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
make pack               # ZIP de entrega en dist/
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
- **Nombres.** El archivo concatena la jerarquía de secciones del notebook, ignorando el `#` del título: `## Ejercicio 1` → `### Resolución` → `#### Inciso 1` produce `ejercicio_1-resolucion-inciso_1.svg`. Los espacios dentro de cada sección se vuelven `_` y los niveles se unen con `-`. Si el nombre supera los 100 caracteres se descartan las secciones menos específicas. Varias figuras dentro de la misma sección se numeran `-2`, `-3`, etc. El manifiesto muestra la ruta completa (`Ejercicio 1 › Resolución › Inciso 1`) y avisa cuando una figura cambia de nombre.
- **Caché.** Si el notebook no cambió, no se vuelve a ejecutar. Para forzar: `.venv/bin/python reports/_scripts/reports.py figures --force`.
- **Sin Qiskit instalado.** Si el notebook no se puede ejecutar, se usan las salidas ya guardadas en el `.ipynb`, así el PDF igual se compila.
- **Rutas.** `notebooks:` se resuelve respecto de la carpeta del informe; `make report-new` convierte automáticamente `practicos/x.ipynb` a `../../practicos/x.ipynb`.

Dependencias necesarias (ya incluidas en `requirements.txt`): `nbclient`, `nbformat` y `PyYAML`.

## Tamaño de las figuras

Se puede indicar `width`, `height` o ambos:

```markdown
![Solo ancho.](assets/figura.svg){width=60%}
![Solo alto.](assets/figura.svg){height=5cm}
![Caja máxima.](assets/figura.svg){width=90% height=5cm}
```

- **Una dimensión:** la imagen se escala proporcionalmente.
- **Ambas:** funcionan como una caja. La imagen se escala proporcionalmente hasta entrar en ella, sin deformarse; manda la restricción más ajustada. La caja se ajusta al tamaño real de la imagen, así que no queda espacio en blanco antes del epígrafe.
- Acepta unidades de Typst: `cm`, `mm`, `in`, `pt` y porcentajes (`width=50%`).
- El epígrafe mantiene siempre el ancho del texto (92 %), independientemente del tamaño de la imagen.

## Espaciado

El espacio antes y después de los títulos lo define la plantilla, no el Markdown: dejar una línea en blanco en el `.qmd` no agrega altura. Para cambiar la separación se ajustan los valores `below` (después del título) y `above` (antes) de los `show heading.where(level: ...)` en `_shared/_template/typst-template.typ` y se corre `make report-sync REPORT=`.

## Empaquetar la entrega

```bash
make pack
```

Genera `dist/<informe>.zip` con:

```text
qpe-grover/
├── Informe.pdf
├── practicos/qpe.ipynb
├── practicos/grover.ipynb
└── requirements.txt
```

Los notebooks son los declarados en `notebooks:` del front matter, y el PDF tiene que existir (`make report` primero). Se puede cambiar la salida con `DIST=...` y elegir otro informe con `REPORT=...`.

## Notas de diseño y trampas (para mantenimiento)

Estas son las decisiones y los errores que costó descubrir; están resumidas también como comentarios en `reports/_scripts/reports.py` y en `_shared/_template/typst-template.typ`.

- **Sandbox de Typst.** La plantilla y los logos tienen que estar dentro de la carpeta del informe: Typst no puede leer fuera de su raíz (“path would escape the project root”). Por eso `_template/` y los logos se copian con `sync`. Los parciales sí se comparten porque los inserta Pandoc (`{{< include ../_shared/... >}}`) antes de llamar a Typst.
- **El guion bajo no es decorativo.** Quarto ignora archivos y carpetas que empiezan con `_`: así `_shared` y `_scripts` no se renderizan. Cuidado al probar: un `.qmd` de prueba llamado `_prueba.qmd` se compila **con el formato por defecto e ignora el `_quarto.yml` del informe**. Usá un nombre sin `_` (`tmp-prueba.qmd`) y borralo después.
- **`width` + `height` en imágenes.** Typst reserva una caja de ese tamaño y centra la imagen escalada adentro; el espacio sobrante empuja el epígrafe hacia abajo. La plantilla reescribe la imagen a su tamaño proporcional exacto (ver `figure-image-size` y el `show figure`).
- **`measure()` y los porcentajes.** Devuelve ancho 0 para `width: 45%`. Para resolver un relativo se lee el campo de la imagen (`content.at("width")`) y se combina `length.ratio` con el tamaño disponible de `layout(...)`.
- **Campos de contenido.** En una función genérica no sirve `content.width`: hay que ir por `content.at("width", default: auto)`. Para inspeccionar qué trae un contenido, `content.fields()`.
- **Show rules y recursión.** Una regla no se reaplica al elemento que devuelve, pero sí a los elementos nuevos que construye. El `show image` interno necesita comparar `source` y dimensiones para cortar (“maximum show rule depth exceeded”).
- **Ancho del epígrafe.** Es fijo (92 % del texto) a propósito. No envolver la figura en un `block(width: 45%)` para “acompañar” la imagen: ese porcentaje se resolvería dos veces y la imagen se achicaría.
- **Espaciado.** Los espacios alrededor de títulos y figuras los define la plantilla; las líneas en blanco del Markdown no agregan altura. Ver los `show heading.where(level: ...)`.
- **Agregar una variable YAML.** Hay que tocar tres lugares: el front matter (o `_quarto.yml`), `_template/typst-show.typ` (mapearla a un parámetro) y la firma de `article()` en `typst-template.typ`. Si falta el tercero, Typst falla con “unexpected argument”.
- **`_quarto.yml` no se sincroniza.** `make report-new` copia `_shared/_quarto.yml.template`, pero `sync` no lo actualiza en informes existentes para no pisar configuraciones propias.
- **Nombres de figuras.** Salen de la pila de encabezados (se ignora el `#`). Renombrar figuras **rompe las referencias del `.qmd`**: el script avisa `viejo → nuevo`, pero no las reescribe. Si se cambia el criterio, subir `EXTRACTOR_VERSION` para invalidar la caché.
- **SVG vs PNG.** Las figuras de matplotlib salen SVG. Las celdas que arman la imagen con `fig.savefig(..., format="png")` o `display(Image(...))` quedan PNG: matplotlib no compone SVG (tablas y mosaicos de `qpe.ipynb`).
- **Referencias a imágenes.** El script no valida el `.qmd`; si falta una imagen, Typst falla con “file not found”. Revisar que cada `![](assets/...)` exista antes de empacar.
- **Errores que no son errores.** El aviso de IPKernelApp sobre TCP sin cifrado es normal. `pdfinfo` puede imprimir “Suspects object is wrong type” con PDFs de Typst; es un detalle de poppler.
- **ZIP de entrega.** `make pack` no compila: exige `informe.pdf`. Conserva la ruta de los notebooks dentro del repo (`practicos/...`) porque es la que menciona el informe.

## Guía de escritura

- **Figura con epígrafe automático:** `![Descripción.](assets/figura.svg){#fig-x width=85%}` genera *Imagen N: Descripción.* y se referencia con `@fig-x`.
- **Consigna:** un blockquote (`>`) se centra y se pone en cursiva.
- **Tabla con epígrafe:** agregar `: Descripción. {#tbl-x}` debajo de la tabla.
- **Salto de página:** `{{< pagebreak >}}`.
- **Ecuaciones:** `$...$` en línea y `$$...$$` en bloque.
- **Secciones comunes:** `{{< include ../_shared/_partials/transparencia.md >}}` y `{{< include ../_shared/_partials/referencias.md >}}`.
