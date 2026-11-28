#!/usr/bin/env python3
"""Herramientas para construir los informes de `reports/`.

Cada informe es una carpeta autocontenida:

    reports/
    ├── _shared/              plantilla, logos y parciales compartidos
    ├── _scripts/             estas herramientas
    └── qpe-grover/
        ├── _quarto.yml
        ├── _template/        copia de la plantilla común
        ├── assets/logos/     logos institucionales
        ├── assets/figures/   figuras extraídas de los notebooks
        ├── informe.qmd
        └── informe.pdf

Las secciones comunes (`_shared/_partials/`) no se copian: cada informe las
incluye desde `_shared/` con `{{< include ../_shared/_partials/... >}}`.

Subcomandos
-----------
figures [INFORME ...]
    Ejecuta los notebooks declarados en el front matter de `informe.qmd` y
    extrae sus figuras como SVG (o PNG si la celda las genera como raster).
    Deja un manifiesto para copiar y pegar en `assets/figures/<notebook>/README.md`.
    Sin argumentos procesa todos los informes.

new NOMBRE
    Crea `reports/NOMBRE/` a partir de `reports/_shared/`.

sync [INFORME ...]
    Actualiza la plantilla y los logos de cada informe con lo que haya en
    `reports/_shared/`. No toca `_quarto.yml` ni `informe.qmd`.

logos [--source RUTA] [--name NOMBRE]
    Recorta el logo indicado (por defecto `images/logo-no-background.png`),
    lo guarda como logo de portada en `_shared/assets/logos/` y lo propaga
    a todos los informes.

pack [INFORME ...] [--out DIR]
    Arma un ZIP por informe con el PDF compilado, los notebooks declarados en
    el front matter y `requirements.txt`. Por defecto lo deja en `dist/`.

list
    Lista los informes, sus notebooks y las figuras extraídas.

Ejemplos
--------
    make figures REPORT=reports/qpe-grover/informe.qmd
    .venv/bin/python reports/_scripts/reports.py figures
    .venv/bin/python reports/_scripts/reports.py new qft --title "Práctica: QFT" \\
        --notebook practicos/qft.ipynb

Notas de mantenimiento
----------------------
* Este archivo y `reports/README.md` documentan las decisiones y las trampas
  encontradas, para no depender del historial de la conversación.
* `EXTRACTOR_VERSION` forma parte de la clave de caché: subilo cuando cambie el
  criterio de nombres o la forma de extraer figuras.
* Los notebooks se ejecutan en memoria: el `.ipynb` original nunca se modifica.
  La salida SVG se logra con un profile temporal de IPython
  (`c.InlineBackend.figure_formats = {'svg'}`). Las celdas que arman la imagen a
  mano con `fig.savefig(..., format="png")` o `display(Image(...))` quedan como
  PNG, porque matplotlib no puede componer SVG (es el caso de las tablas y los
  mosaicos de `qpe.ipynb`).
* El nombre de cada figura sale de la pila de encabezados: se ignora el `#` y se
  concatenan los niveles con `-`, usando `_` en lugar de espacios
  (`ejercicio_1-resolucion-inciso_i.svg`). Si un nombre cambia, las referencias
  del `.qmd` se rompen: el script avisa `viejo → nuevo`, pero no las reescribe.
* `sync` copia y SOBRESCRIBE plantilla y logos, pero nunca `_quarto.yml` ni
  `informe.qmd`. Los parciales no se copian: se incluyen desde `_shared`.
* `pack` no compila: exige el PDF ya generado (`make report`).
* Si Typst falla con "file not found", hay una imagen referenciada en el `.qmd`
  que no existe. Este script no valida las referencias del documento.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS = ROOT / "reports"
SHARED = REPORTS / "_shared"
CACHE = REPORTS / ".figures-cache"
REPORT_FILE = "informe.qmd"
DEFAULT_FIGURES_DIR = "assets/figures"
EXTRACTOR_VERSION = 5

# Configuración que se inyecta en el kernel para que IPython entregue SVG.
IPYTHON_SVG_CONFIG = "c = get_config()\nc.InlineBackend.figure_formats = {'svg'}\n"


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def slugify(text: str, maxlen: int = 48, separator: str = "-") -> str:
    """Convierte un título en un nombre de archivo legible."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\$[^$]*\$", "", text)                 # quita math inline
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # links -> texto
    text = re.sub(r"[`*_#{}]", "", text)
    text = re.sub(r"[^0-9A-Za-z]+", separator, text)
    text = text.strip(separator).lower()[:maxlen]
    return text.strip(separator) or "figura"


def heading_slug(
    chain: tuple[str, ...], max_component: int = 48, max_total: int = 100
) -> str:
    """Concatena la jerarquía de secciones: `ejercicio_1-resolucion-inciso_1`.

    Convención acordada: `_` reemplaza los espacios dentro de una sección y los
    niveles se unen con `-`. Si el total supera `max_total`, se descartan las
    secciones de más arriba (se conserva la parte más específica).
    """
    parts = [slugify(title, max_component, separator="_") for title in chain if title]
    while len(parts) > 1 and len("-".join(parts)) > max_total:
        parts.pop(0)  # conserva las secciones más específicas
    return "-".join(parts)[:max_total].strip("-_") or "figura"


def front_matter(qmd: Path) -> dict:
    """Lee el bloque YAML inicial de un .qmd (sin depender de Quarto)."""
    try:
        import yaml
    except ImportError:  # pragma: no cover
        sys.exit("Falta PyYAML: .venv/bin/pip install pyyaml")

    lines = qmd.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            return yaml.safe_load("\n".join(lines[1:i])) or {}
    return {}


def report_dirs() -> list[Path]:
    return [
        d
        for d in sorted(REPORTS.iterdir())
        if d.is_dir() and not d.name.startswith(("_", ".")) and (d / REPORT_FILE).is_file()
    ]


def resolve_report(value: str) -> Path:
    """Acepta una carpeta de informe o la ruta de su informe.qmd."""
    path = Path(value)
    if not path.is_absolute():
        candidates = [path, ROOT / path, REPORTS / path]
        path = next((c for c in candidates if c.exists()), path)
    if path.is_dir():
        path = path / REPORT_FILE
    return path


def find_reports(args: list[str]) -> list[Path]:
    if args:
        paths = [resolve_report(a) for a in args]
    else:
        paths = [d / REPORT_FILE for d in report_dirs()]
    missing = [p for p in paths if not p.is_file()]
    if missing:
        sys.exit("No existe: " + ", ".join(str(p) for p in missing))
    return paths


# --------------------------------------------------------------------------- #
# Plantilla compartida
# --------------------------------------------------------------------------- #
def copy_tree(
    source: Path, target: Path, only_missing: bool = False, exclude: tuple[str, ...] = ()
) -> list[Path]:
    """Copia archivos de `source` a `target` y devuelve los que cambió."""
    changed: list[Path] = []
    target.mkdir(parents=True, exist_ok=True)
    for item in source.rglob("*"):
        if not item.is_file():
            continue
        if any(item.match(pattern) for pattern in exclude):
            continue
        destination = target / item.relative_to(source)
        if only_missing and destination.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and destination.read_bytes() == item.read_bytes():
            continue
        shutil.copy2(item, destination)
        changed.append(destination)
    return changed


def sync_report(report_dir: Path) -> list[Path]:
    """Copia plantilla y logos; nunca toca `_quarto.yml` ni `informe.qmd`.

    - `_template/` se SOBRESCRIBE: la fuente de verdad es `_shared`.
    - los logos también se sobrescriben (para poder reemplazarlos con
      `make logos`), salvo los que no estén en `_shared`.
    - `.gitignore` solo se crea si falta.
    - los parciales NO se copian: se incluyen desde `_shared` en el `.qmd`.
    """
    changed: list[Path] = []
    changed += copy_tree(
        SHARED / "_template", report_dir / "_template", exclude=("*.template",)
    )
    changed += copy_tree(SHARED / "assets" / "logos", report_dir / "assets" / "logos")
    for name in (".gitignore",):
        source = SHARED / name
        destination = report_dir / name
        if source.is_file() and not destination.exists():
            shutil.copy2(source, destination)
            changed.append(destination)
    return changed


def notebook_arg(value: str, report_dir: Path) -> str:
    """Normaliza un notebook a una ruta relativa a la carpeta del informe."""
    path = Path(value)
    candidate = path if path.is_absolute() else ROOT / path
    if "*" in value or not candidate.exists():
        return value
    return os.path.relpath(candidate.resolve(), report_dir)


def new_report(args) -> None:
    report_dir = REPORTS / args.name
    if report_dir.exists():
        sys.exit(f"Ya existe {rel(report_dir)}")

    report_dir.mkdir(parents=True)
    sync_report(report_dir)

    config = SHARED / "_quarto.yml.template"
    if config.is_file():
        shutil.copy2(config, report_dir / "_quarto.yml")

    notebooks = "".join(
        f"  - {notebook_arg(nb, report_dir)}\n" for nb in args.notebook
    ) or "  # - ../../practicos/qft.ipynb\n"

    template = SHARED / "_template" / "report.qmd.template"
    if not template.is_file():
        sys.exit(f"Falta la plantilla {rel(template)}")
    body = (
        template.read_text(encoding="utf-8")
        .replace("{{title}}", args.title)
        .replace("{{subtitle}}", args.subtitle)
        .replace("{{running_header}}", args.running_header or args.title)
        .replace("{{notebooks}}", notebooks.rstrip("\n"))
    )
    (report_dir / REPORT_FILE).write_text(body, encoding="utf-8")

    print(f"+ Creado {rel(report_dir / REPORT_FILE)}")
    print(f"  Siguiente paso: make figures REPORT={rel(report_dir / REPORT_FILE)}")


def sync_reports(args) -> None:
    if not SHARED.is_dir():
        sys.exit(f"Falta {rel(SHARED)}")
    if args:
        targets = [resolve_report(a).parent for a in args]
    else:
        targets = report_dirs()

    for report_dir in targets:
        changed = sync_report(report_dir)
        detail = f"{len(changed)} archivo(s) actualizado(s)" if changed else "sin cambios"
        print(f"= {rel(report_dir)}: {detail}")


def import_logo(source: Path, name: str, margin: float = 0.02) -> Path:
    """Recorta un logo con transparencia y lo deja en `_shared/assets/logos/`.

    El archivo de origen suele venir con mucho margen transparente (el logo
    original de `images/`). Se recorta el bounding box del canal alfa y se deja
    un margen mínimo (2 %) para que no quede pegado al borde. Después se
    propaga a todos los informes con `sync_report`.
    """
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover
        sys.exit("Falta Pillow: .venv/bin/pip install pillow")

    if not source.is_file():
        sys.exit(f"No existe el logo {source}")

    image = Image.open(source).convert("RGBA")
    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)

    pad = int(max(image.size) * margin)
    canvas = Image.new("RGBA", (image.width + 2 * pad, image.height + 2 * pad), (0, 0, 0, 0))
    canvas.paste(image, (pad, pad))

    target = SHARED / "assets" / "logos" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target)

    # Propaga el logo a todos los informes.
    for report_dir in report_dirs():
        sync_report(report_dir)

    print(f"+ Logo importado: {rel(target)} ({canvas.width}×{canvas.height})")
    print("  Sincronizado en: " + ", ".join(rel(d) for d in report_dirs()))
    return target


# --------------------------------------------------------------------------- #
# Ejecución de notebooks
# --------------------------------------------------------------------------- #
def execute_notebook(nb, nb_path: Path, timeout: int) -> None:
    """Ejecuta el notebook en memoria con salida SVG de IPython.

    El archivo .ipynb original nunca se modifica: nbclient trabaja sobre una
    copia en memoria.

    El formato SVG no se puede pedir por parámetro al kernel: se configura con
    un profile temporal de IPython (`IPYTHONDIR` + `figure_formats`). Por eso se
    crea un directorio temporal y se restaura la variable de entorno al salir.
    El aviso de IPKernelApp sobre TCP sin cifrado es normal y no afecta nada.

    `resources.metadata.path` fija el cwd del kernel a la carpeta del notebook
    para que sus rutas relativas (por ejemplo `images/foo.png`) funcionen.
    `allow_errors=True` permite seguir extrayendo el resto de las figuras aunque
    una celda falle; los errores se listan en el manifiesto.
    """
    from nbclient import NotebookClient

    ipython_dir = Path(tempfile.mkdtemp(prefix="ipython-svg-"))
    profile = ipython_dir / "profile_default"
    profile.mkdir(parents=True, exist_ok=True)
    (profile / "ipython_config.py").write_text(IPYTHON_SVG_CONFIG, encoding="utf-8")

    previous = os.environ.get("IPYTHONDIR")
    os.environ["IPYTHONDIR"] = str(ipython_dir)
    try:
        client = NotebookClient(
            nb,
            timeout=timeout,
            kernel_name="python3",
            allow_errors=True,
            resources={"metadata": {"path": str(nb_path.parent)}},
        )
        client.execute()
    finally:
        if previous is None:
            os.environ.pop("IPYTHONDIR", None)
        else:
            os.environ["IPYTHONDIR"] = previous
        shutil.rmtree(ipython_dir, ignore_errors=True)


def heading_map(nb) -> dict[int, tuple[str, ...]]:
    """Asocia cada celda de código con la jerarquía de encabezados previos.

    Se mantiene una pila de secciones: un encabezado de nivel n descarta las
    secciones de nivel >= n antes de apilarse. El encabezado de nivel 1 se
    ignora (es el título del notebook) y reinicia la jerarquía.
    """
    headings: dict[int, tuple[str, ...]] = {}
    stack: list[tuple[int, str]] = []
    title_re = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$", re.M)

    for index, cell in enumerate(nb.cells):
        if cell.cell_type == "markdown":
            for match in title_re.finditer(cell.source):
                level = len(match.group(1))
                title = match.group(2).strip()
                if level == 1:
                    stack.clear()
                    continue
                while stack and stack[-1][0] >= level:
                    stack.pop()
                stack.append((level, title))
        elif cell.cell_type == "code":
            headings[index] = tuple(title for _, title in stack)
    return headings


def cell_figures(cell):
    """Devuelve (formato, payload) por cada imagen de una celda."""
    for output in cell.get("outputs", []):
        data = output.get("data") or {}
        for mime, fmt in (("image/svg+xml", "svg"), ("image/png", "png")):
            if mime in data:
                payload = data[mime]
                if isinstance(payload, list):
                    payload = "".join(payload)
                yield fmt, payload
                break  # si hay SVG, se prefiere sobre el PNG espejo


def extract(nb, out_dir: Path, name: str, figures_dir_rel: str) -> list[dict]:
    """Escribe las figuras de un notebook y devuelve sus metadatos."""
    headings = heading_map(nb)
    used: dict[str, int] = {}
    entries: list[dict] = []

    for index, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        for out_index, (fmt, payload) in enumerate(cell_figures(cell)):
            chain = headings.get(index) or ()
            base = heading_slug(chain)
            used[base] = used.get(base, 0) + 1
            suffix = "" if used[base] == 1 else f"-{used[base]}"
            filename = f"{base}{suffix}.{fmt}"
            target = out_dir / filename

            if fmt == "svg":
                target.write_text(payload, encoding="utf-8")
            else:
                target.write_bytes(base64.b64decode(payload))

            entries.append(
                {
                    "file": filename,
                    "path": f"{figures_dir_rel}/{name}/{filename}",
                    "heading": " › ".join(chain) or "(sin sección)",
                    "cell": index,
                    "output": out_index,
                    "cell_id": cell.get("id", ""),
                    "format": fmt,
                    "label": f"fig-{name}-{slugify(' '.join(chain) or 'figura', 120)}{suffix}",
                }
            )
    return entries


def write_manifest(nb_path: Path, out_dir: Path, entries: list[dict], errors: list[str]) -> None:
    lines = [
        f"# Figuras de `{rel(nb_path)}`",
        "",
        "Generado automáticamente por `reports/_scripts/reports.py`. No editar a mano.",
        "",
        "| # | Archivo | Sección | Celda | Formato |",
        "|---|---------|---------|-------|---------|",
    ]
    for n, entry in enumerate(entries, start=1):
        lines.append(
            f"| {n} | `{entry['file']}` | {entry['heading']} | {entry['cell']} | "
            f"{entry['format'].upper()} |"
        )

    if errors:
        lines += ["", "## Errores durante la ejecución", ""]
        lines += [f"- {error}" for error in errors]

    lines += ["", "## Copiar y pegar", ""]
    for entry in entries:
        lines += [
            f"### {entry['heading']} (celda {entry['cell']})",
            "",
            "```markdown",
            f"![DESCRIPCIÓN]({entry['path']}){{#{entry['label']} width=90%}}",
            "```",
            "",
        ]

    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Extracción
# --------------------------------------------------------------------------- #
def notebook_specs(meta: dict, qmd: Path) -> list[dict]:
    raw = meta.get("notebooks") or []
    if isinstance(raw, (str, Path)):
        raw = [raw]

    specs: list[dict] = []
    seen: dict[str, int] = {}
    for item in raw:
        if isinstance(item, str):
            spec = {"path": item}
        elif isinstance(item, dict):
            spec = dict(item)
        else:
            continue

        path_value = spec.get("path") or spec.get("notebook")
        if not path_value:
            continue

        base = qmd.parent
        matches = sorted(base.glob(path_value)) if not Path(path_value).is_absolute() else [Path(path_value)]
        for match in matches or [base / path_value]:
            if not match.is_file():
                print(f"! Aviso: no se encontró el notebook {match}")
                continue
            name = spec.get("name") or match.stem
            seen[name] = seen.get(name, 0) + 1
            if seen[name] > 1:
                name = f"{name}-{seen[name]}"
            specs.append({"path": match, "name": slugify(name)})
    return specs


def process_notebook(
    spec: dict, qmd: Path, figures_dir_rel: str, force: bool, timeout: int
) -> int:
    """Extrae las figuras de un notebook y actualiza el manifiesto y la caché.

    Caché: la clave combina EXTRACTOR_VERSION + hash del notebook + carpeta de
    salida. Si no cambió nada, no se vuelve a ejecutar (19 s por notebook en
    este repo). `--force` la ignora.

    Si la ejecución falla (kernel ausente, sin Qiskit, timeout), se usan las
    salidas ya guardadas en el `.ipynb`, así el informe se puede compilar igual.

    La carpeta de figuras se borra antes de reescribirla: es material generado y
    así no quedan archivos viejos con nombres anteriores.
    """
    import nbformat

    nb_path: Path = spec["path"]
    name: str = spec["name"]
    out_dir = qmd.parent / figures_dir_rel / name
    cache_file = CACHE / f"{slugify(qmd.parent.name)}-{name}.json"

    cache_key = sha256(
        f"{EXTRACTOR_VERSION}:{sha256(nb_path.read_bytes())}:{rel(out_dir)}".encode()
    )
    cached = None
    if cache_file.is_file():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cached = None

    if (
        not force
        and cached
        and cached.get("key") == cache_key
        and all((out_dir / e["file"]).is_file() for e in cached.get("figures", []))
    ):
        print(f"= {rel(nb_path)}: sin cambios ({len(cached['figures'])} figuras)")
        return len(cached["figures"])

    nb = nbformat.read(nb_path, as_version=4)
    errors: list[str] = []
    try:
        execute_notebook(nb, nb_path, timeout)
    except Exception as exc:  # kernel ausente, timeout global, etc.
        print(f"! No se pudo ejecutar {rel(nb_path)} ({exc}).")
        print("  Se usan las salidas ya guardadas en el notebook.")
        nb = nbformat.read(nb_path, as_version=4)

    for index, cell in enumerate(nb.cells):
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                errors.append(
                    f"celda {index}: {output.get('ename')}: {output.get('evalue')}"
                )

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    entries = extract(nb, out_dir, name, figures_dir_rel)
    write_manifest(nb_path, out_dir, entries, errors)

    # Avisa si alguna figura cambió de nombre respecto de la extracción previa.
    if cached:
        old = {
            (e.get("cell_id") or e.get("cell"), e.get("output", 0)): e["path"]
            for e in cached.get("figures", [])
        }
        for entry in entries:
            key = (entry["cell_id"] or entry["cell"], entry["output"])
            if key in old and old[key] != entry["path"]:
                print(f"! La figura {old[key]} pasó a llamarse {entry['path']}")

    CACHE.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(
        json.dumps(
            {
                "key": cache_key,
                "source": rel(nb_path),
                "generated": datetime.now().isoformat(timespec="seconds"),
                "figures": entries,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    svg = sum(1 for e in entries if e["format"] == "svg")
    png = len(entries) - svg
    detail = f"{svg} SVG" + (f", {png} PNG" if png else "")
    print(f"+ {rel(nb_path)}: {len(entries)} figuras ({detail}) en {rel(out_dir)}")
    if errors:
        print(f"! {len(errors)} celdas con error; ver el manifiesto.")
    return len(entries)


def run_figures(qmd: Path, force: bool, timeout: int) -> int:
    meta = front_matter(qmd)
    specs = notebook_specs(meta, qmd)
    if not specs:
        print(f"- {rel(qmd)}: no declara 'notebooks:' en el front matter")
        return 0

    figures_dir_rel = meta.get("figures-dir") or DEFAULT_FIGURES_DIR
    total = 0
    for spec in specs:
        total += process_notebook(spec, qmd, figures_dir_rel, force, timeout)
    return total


def pack_report(qmd: Path, out_dir: Path) -> Path:
    """Arma el ZIP de entrega: informe PDF, notebooks declarados y requirements.

    Estructura del ZIP (una carpeta con el nombre del informe):

        <informe>/Informe.pdf
        <informe>/practicos/qpe.ipynb      (ruta relativa al repo)
        <informe>/requirements.txt

    Se conserva la ruta de los notebooks dentro del repo para que coincida con
    la que menciona el informe. No compila: exige el PDF ya generado.
    """
    meta = front_matter(qmd)
    pdf = qmd.parent / "informe.pdf"
    if not pdf.is_file():
        sys.exit(
            f"Falta {rel(pdf)}. Compilá el informe primero: "
            f"make report REPORT={rel(qmd)}"
        )

    specs = notebook_specs(meta, qmd)
    folder = qmd.parent.name
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{folder}.zip"

    added: list[str] = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(pdf, f"{folder}/Informe.pdf")
        added.append(f"{folder}/Informe.pdf")

        seen: set[Path] = set()
        for spec in specs:
            notebook = spec["path"].resolve()
            if notebook in seen:
                continue
            seen.add(notebook)
            try:
                arcname = notebook.relative_to(ROOT)
            except ValueError:
                arcname = Path(notebook.name)
            archive.write(notebook, f"{folder}/{arcname}")
            added.append(f"{folder}/{arcname}")

        requirements = ROOT / "requirements.txt"
        if requirements.is_file():
            archive.write(requirements, f"{folder}/requirements.txt")
            added.append(f"{folder}/requirements.txt")

    size = zip_path.stat().st_size / 1024
    print(f"+ {rel(zip_path)} ({size:.0f} KB)")
    for name in added:
        print(f"    {name}")
    if not specs:
        print("! El informe no declara notebooks: el ZIP solo tiene el PDF.")
    return zip_path


def list_reports() -> None:
    reports = find_reports([])
    if not reports:
        print("No hay informes en reports/")
        return
    for qmd in reports:
        meta = front_matter(qmd)
        specs = notebook_specs(meta, qmd)
        figures_dir_rel = meta.get("figures-dir") or DEFAULT_FIGURES_DIR
        print(f"{rel(qmd)}  —  {meta.get('title', '(sin título)')}")
        if not specs:
            print("    sin notebooks declarados")
        for spec in specs:
            out_dir = qmd.parent / figures_dir_rel / spec["name"]
            files = [p for p in out_dir.glob("*") if p.name != "README.md"] if out_dir.is_dir() else []
            print(f"    {rel(spec['path'])}  →  {len(files)} figuras")
        print()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extracción de figuras y creación de informes en reports/"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    figures = sub.add_parser("figures", help="Extrae las figuras de los notebooks")
    figures.add_argument("reports", nargs="*", help="Carpetas de informe (por defecto: todas)")
    figures.add_argument("--force", action="store_true", help="Reejecuta aunque no haya cambios")
    figures.add_argument("--timeout", type=int, default=900, help="Timeout por celda (s)")

    new = sub.add_parser("new", help="Crea un informe nuevo")
    new.add_argument("name", help="Nombre de la carpeta del informe")
    new.add_argument("--title", required=True)
    new.add_argument("--subtitle", default="")
    new.add_argument("--running-header", default="")
    new.add_argument("--notebook", action="append", default=[], help="Repetible")

    sync = sub.add_parser("sync", help="Actualiza plantilla y logos")
    sync.add_argument("reports", nargs="*", help="Carpetas de informe (por defecto: todas)")

    logos = sub.add_parser("logos", help="Importa y propaga el logo de portada")
    logos.add_argument(
        "--source",
        default="images/logo-no-background.png",
        help="Imagen de origen (por defecto: images/logo-no-background.png)",
    )
    logos.add_argument(
        "--name",
        default="qc-logo-cover.png",
        help="Nombre del destino en _shared/assets/logos/",
    )

    pack = sub.add_parser("pack", help="Arma el ZIP de entrega")
    pack.add_argument("reports", nargs="*", help="Carpetas de informe (por defecto: todas)")
    pack.add_argument("--out", default="dist", help="Carpeta de salida (por defecto: dist/)")

    sub.add_parser("list", help="Lista informes y figuras")

    args = parser.parse_args()

    if args.command == "figures":
        total = 0
        for qmd in find_reports(args.reports):
            total += run_figures(qmd.resolve(), args.force, args.timeout)
        print(f"\nTotal: {total} figuras")
    elif args.command == "new":
        new_report(args)
    elif args.command == "sync":
        sync_reports(args.reports)
    elif args.command == "pack":
        out_dir = Path(args.out)
        if not out_dir.is_absolute():
            out_dir = ROOT / out_dir
        for qmd in find_reports(args.reports):
            pack_report(qmd.resolve(), out_dir)
    elif args.command == "logos":
        import_logo(ROOT / args.source, args.name)
    else:
        list_reports()


if __name__ == "__main__":
    main()
