# Informes en Quarto (`reports/`)

Informes académicos en PDF con la estética de la cátedra (portada con logos, encabezados, numeración de páginas, texto justificado, epígrafes de figuras y tablas), generados con **Quarto + Typst**.

```text
reports/
├── _shared/                      # fuente única de verdad (no es un informe)
│   ├── _quarto.yml.template      # configuración base para informes nuevos
│   ├── _template/                # diseño visual en Typst + esqueleto
│   ├── _partials/                # transparencia y referencias (se incluyen)
│   └── assets/logos/             # logos institucionales
├── _scripts/
│   └── reports.py                # extracción de figuras y andamiaje
├── qpe-grover/                   # un informe
│   ├── _quarto.yml               # configuración propia (copiada al crearlo)
│   ├── _template/                # copia de la plantilla (la actualiza sync)
│   ├── assets/
│   │   ├── logos/
│   │   └── figures/              # figuras extraídas de los notebooks
│   │       ├── qpe/              # + README.md con el manifiesto
│   │       └── grover/
│   ├── informe.qmd
│   └── informe.pdf
└── README.md
```

### Convención del guion bajo

Las carpetas que empiezan con `_` (`_shared/`, `_scripts/`) son **infraestructura, no informes**: no se compilan, no aparecen en `make reports-list` ni se tocan al crear un informe. El prefijo lo entiende Quarto —ignora todo lo que empiece con `_`— y además lo entiende cualquiera que mire el árbol: un directorio con `informe.qmd` es un informe, uno con `_` no.

Por eso también llevan `_` las subcarpetas internas `_template/` y `_partials/`, y la configuración base se llama `_quarto.yml.template` en vez de `_quarto.yml`: así Quarto no la confunde con la configuración de un proyecto.


## Comandos

```bash
make reports            # extrae figuras y compila todos los informes
make report             # extrae figuras y compila $(REPORT)
make figures            # solo extrae figuras de $(REPORT)
make reports-list       # lista informes, notebooks y cantidad de figuras
make report-new NAME=qft TITLE="Práctica: QFT" NOTEBOOKS="practicos/qft.ipynb"
make report-sync        # actualiza plantilla y logos de $(REPORT)
make report-sync REPORT=   # ídem para todos los informes
```

`REPORT` vale `reports/qpe-grover/informe.qmd` por defecto; se puede pasar otro:

```bash
make report REPORT=reports/qft/informe.qmd
```

## Qué es compartido y qué se copia

- **Se incluyen (compartido de verdad):** `_shared/_partials/transparencia.md` y `_shared/_partials/referencias.md`. Cada informe los trae con

  ```markdown
  {{< include ../_shared/_partials/transparencia.md >}}
  ```

  Si editás esos archivos, el cambio aparece en todos los informes al recompilar. Para agregar referencias propias del práctico, se agregan en el informe después del include (por ejemplo, una sección `## Recursos específicos`).

- **Se copian:** `_shared/_template/` (Quarto exige que la plantilla Typst viva dentro del proyecto del informe, porque Typst no puede leer fuera de su raíz) y los logos. `make report-sync` los actualiza; `_quarto.yml` e `informe.qmd` nunca se tocan.

- **Cambiar un logo:** reemplazá el archivo en `_shared/assets/logos/` y corré `make report-sync REPORT=` para propagarlo a todos los informes. Los logos se sobrescriben en cada sincronización, a diferencia de `_quarto.yml`. Los que usa la plantilla son `unicen-logo.png` (arriba a la izquierda), `exa-logo.png` (arriba a la derecha y encabezados), `qc-logo-cover.png` (ilustración de la portada) y `quantum-banner.png` (franjas superior e inferior).

- **Logo de portada desde `images/`:** el logo del curso se importa con

  ```bash
  make logos
  ```

  Toma `images/logo-no-background.png`, le recorta el margen transparente y lo guarda como `_shared/assets/logos/qc-logo-cover.png`, propagándolo a todos los informes. Para usar otra imagen: `make logos SOURCE=images/otro-logo.png`.

## Crear un informe nuevo

```bash
make report-new NAME=qft TITLE="Práctica: QFT" NOTEBOOKS="practicos/qft.ipynb practicos/qft-extra.ipynb"
```

Crea `reports/qft/` con la plantilla, los logos y el `informe.qmd` armado con los notebooks declarados. Después:

```bash
make report REPORT=reports/qft/informe.qmd
```

## Figuras automáticas desde notebooks

En el front matter de `informe.qmd` se declaran los notebooks:

```yaml
---
title: "Práctica: QFT"
notebooks:
  - ../../practicos/qft.ipynb
  - ../../practicos/qft-extra.ipynb
---
```

`make figures` los **ejecuta en memoria** (el `.ipynb` original no se modifica) pidiéndole a IPython salida SVG, y escribe cada figura en `assets/figures/<notebook>/`. También genera un manifiesto:

```text
assets/figures/qft/README.md
```

con la tabla de figuras (archivo, sección del notebook, celda) y la línea lista para copiar y pegar:

```markdown
![DESCRIPCIÓN](assets/figures/qft/ejercicio-1.svg){#fig-qft-ejercicio-1 width=90%}
```

Detalles:

- **SVG vs PNG.** Las figuras de matplotlib (circuitos, histogramas) salen como SVG vectorial. Las celdas que arman la imagen a mano con `fig.savefig(..., format="png")` o `display(Image(...))` salen como PNG a la resolución original; es el caso de las tablas y de los mosaicos de circuitos de `qpe.ipynb`. El manifiesto indica el formato de cada una.
- **Nombres.** El archivo se nombra con la última sección markdown previa (`inciso-ii.svg`). Si se agrega una figura dentro de la misma sección, las posteriores de esa sección se renumeran (`inciso-ii-2.svg`). El script avisa cuando una figura cambia de nombre.
- **Caché.** Si el notebook no cambió, no se vuelve a ejecutar. Para forzar: `.venv/bin/python reports/_scripts/reports.py figures --force`.
- **Sin Qiskit instalado.** Si el notebook no se puede ejecutar, se usan las salidas ya guardadas en el `.ipynb`, así el PDF igual se compila.
- **Rutas.** `notebooks:` se resuelve respecto de la carpeta del informe; `make report-new` convierte automáticamente `practicos/x.ipynb` a `../../practicos/x.ipynb`.

Dependencias necesarias (ya incluidas en `requirements.txt`): `nbclient`, `nbformat` y `PyYAML`.

## Guía de escritura

- **Figura con epígrafe automático:** `![Descripción.](assets/figura.svg){#fig-x width=85%}` genera *Imagen N: Descripción.* y se referencia con `@fig-x`.
- **Consigna:** un blockquote (`>`) se centra y se pone en cursiva.
- **Tabla con epígrafe:** agregar `: Descripción. {#tbl-x}` debajo de la tabla.
- **Salto de página:** `{{< pagebreak >}}`.
- **Ecuaciones:** `$...$` en línea y `$$...$$` en bloque.
- **Secciones comunes:** `{{< include ../_shared/_partials/transparencia.md >}}` y `{{< include ../_shared/_partials/referencias.md >}}`.
