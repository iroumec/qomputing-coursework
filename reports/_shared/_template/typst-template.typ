// ============================================================================
// typst-template.typ
// Plantilla académica con estética cuántica para informes de
// Algoritmos Avanzados de Computación Cuántica (EXA - UNICEN)
//
// NOTAS DE DISEÑO (leer antes de tocar)
// ----------------------------------------------------------------------------
// * Sandbox de Typst: la plantilla debe vivir DENTRO del proyecto de cada
//   informe. Typst no puede leer archivos fuera de su raíz ("path would escape
//   the project root"). Por eso `_template/` y los logos se copian a cada
//   informe con `make report-sync`. Las secciones comunes (`_partials/`) sí se
//   comparten: se incluyen con `{{< include ../_shared/_partials/... >}}` y
//   Pandoc las inserta antes de invocar a Typst, así que no pasan por el
//   sandbox.
//
// * `width` + `height` en una imagen: Typst reserva una caja de ese tamaño y
//   dibuja la imagen escalada y centrada adentro. El espacio que sobra dentro
//   de la caja separa el epígrafe de la imagen. Lo resuelve
//   `figure-image-size` + el `show figure` de más abajo, que reescriben la
//   imagen a su tamaño proporcional exacto.
//
// * `measure()` devuelve ancho 0 para tamaños relativos (`45%`). Para resolver
//   un relativo hay que leer el campo de la imagen (`fields()` / `at`) y
//   combinar `length.ratio` con el tamaño disponible que da `layout(...)`.
//
// * Los campos de un elemento `image` no se leen como `content.width` cuando
//   el contenido es genérico: hay que usar `content.at("width", default: auto)`.
//
// * El espaciado vertical de títulos, párrafos y figuras se define acá. Las
//   líneas en blanco del Markdown NO agregan altura.
//
// * Un show rule no se reaplica al elemento que devuelve, pero sí a los
//   elementos nuevos que construye: el `show image` interno necesita un guard
//   (compara source y dimensiones) para no recursar infinito.
// ============================================================================

#let quantum-banner(height: 15pt) = {
  block(
    width: 100%,
    height: height,
    fill: rgb("#040908"),
    clip: true,
    {
      // Sutil grilla cuántica verde/cian sobre fondo oscuro
      let cols = 90
      let rows = 5
      place(top + left,
        grid(
          columns: (1fr,) * cols,
          rows: (height / rows,) * rows,
          stroke: 0.25pt + rgb("#0d3b2e"),
        )
      )
      // Líneas de acento luminosas sutiles en los bordes
      place(top, line(length: 100%, stroke: 0.6pt + rgb("#155e4b")))
      place(bottom, line(length: 100%, stroke: 0.6pt + rgb("#155e4b")))
    }
  )
}

// Devuelve la primera imagen que haya dentro de un contenido (la figura que
// genera Quarto es `[#box(image(...))]`): (source, width, height) o `none`.
//
// Recorre `body`, `child` y `children` porque el cuerpo puede venir envuelto en
// cajas o secuencias. Ojo: los campos de una imagen no se leen como
// `content.width` cuando el contenido es genérico; van por `at()`.
#let image-info(content) = {
  if content == none {
    return none
  }
  if content.func() == image {
    return (
      source: content.at("source"),
      width: content.at("width", default: auto),
      height: content.at("height", default: auto),
    )
  }
  if content.has("body") {
    let found = image-info(content.body)
    if found != none {
      return found
    }
  }
  if content.has("child") {
    let found = image-info(content.child)
    if found != none {
      return found
    }
  }
  if content.has("children") {
    for child in content.children {
      let found = image-info(child)
      if found != none {
        return found
      }
    }
  }
  none
}

// Resuelve un largo relativo (`45%`) contra una base; los absolutos quedan
// igual. `length.ratio` da la parte porcentual (0% si es absoluto) y el resto
// (`length - length.ratio`) es la parte absoluta. No sirve `measure()` para
// esto: devuelve 0 cuando el ancho es relativo.
#let resolve-length(length, base) = {
  if length.ratio == 0% {
    length
  } else {
    (length - length.ratio) + base * length.ratio
  }
}

// Tamaño que debe ocupar la imagen cuando fija `width` y `height` a la vez.
// Typst, con las dos dimensiones, reserva una CAJA de ese tamaño y centra la
// imagen escalada adentro (`fit: contain`), dejando espacio en blanco que
// empuja el epígrafe hacia abajo. Acá se calcula el tamaño proporcional que
// realmente entra en la caja (manda la restricción más ajustada) para
// reescribir la imagen sin sobrante.
// Devuelve `none` si falta alguna dimensión o no hay imagen: en ese caso Typst
// ya escala proporcionalmente y no hay nada que corregir.
#let figure-image-size(content, available) = {
  let info = image-info(content)
  if info == none {
    return none
  }
  if info.width == auto or info.height == auto {
    return none
  }
  let natural = measure(image(info.source))
  let box-width = resolve-length(info.width, available.width)
  let box-height = resolve-length(info.height, available.height)
  let scale = calc.min(box-width / natural.width, box-height / natural.height)
  (
    source: info.source,
    width: natural.width * scale,
    height: natural.height * scale,
  )
}

#let article(
  title: none,
  subtitle: none,
  cursada: "Cursada 2025",
  materia: "Fundamentos de la Computación Cuántica",
  running-header: none,
  authors: none,
  profesores: (),
  logo-left: none,
  logo-right: none,
  logo-cover: none,
  banner-image: none,
  keywords: (),
  date: none,
  abstract-title: none,
  abstract: none,
  thanks: none,
  cols: 1,
  lang: "es",
  region: "AR",
  font: ("Liberation Serif", "Nimbus Roman", "Libertinus Serif"),
  fontsize: 12pt,
  title-size: 22pt,
  subtitle-size: 18pt,
  heading-family: ("Liberation Serif", "Nimbus Roman", "Libertinus Serif"),
  heading-weight: "bold",
  heading-style: "normal",
  heading-color: black,
  heading-line-height: 0.65em,
  mathfont: none,
  codefont: ("Liberation Mono", "DejaVu Sans Mono"),
  linestretch: 1.15,
  sectionnumbering: none,
  linkcolor: "#1155cc",
  citecolor: "#1155cc",
  filecolor: "#1155cc",
  toc: true,
  toc_title: none,
  toc_depth: 3,
  toc_indent: 1.5em,
  doc,
) = {
  // Metadatos del PDF
  set document(title: title, keywords: keywords)
  set document(
    author: authors.map(author => content-to-string(author.name)).join(", ", last: " & "),
  ) if authors != none and authors != ()

  // Tipografía base
  set text(
    lang: lang,
    region: region,
    font: font,
    size: fontsize,
    fill: rgb("#111111"),
  )
  show math.equation: set text(font: mathfont) if mathfont != none
  show raw: set text(font: codefont, size: 0.92em) if codefont != none

  // Código inline con estilo sutil
  show raw.where(block: false): box.with(
    fill: rgb("#f3f4f6"),
    inset: (x: 3pt, y: 0pt),
    outset: (y: 2pt),
    radius: 2pt,
  )

  // Bloques de código con estética limpia y borde izquierdo cuántico
  show raw.where(block: true): set block(
    fill: rgb("#f8fafc"),
    stroke: (
      left: 2.5pt + rgb("#155e4b"),
      rest: 0.5pt + rgb("#e2e8f0"),
    ),
    width: 100%,
    inset: 10pt,
    radius: 3pt,
  )

  // Enlaces con estilo académico (azul y subrayado como en las entregas)
  show link: it => {
    set text(fill: rgb("#1155cc"))
    underline(it)
  }
  show ref: set text(fill: rgb("#1155cc"))

  // Numeración de secciones
  set heading(numbering: sectionnumbering)

  // Jerarquía visual de encabezados (fiel a los informes en entregas/).
  // `below` controla la separación entre el título y el texto que le sigue;
  // `above`, la separación con el contenido anterior. Las líneas en blanco del
  // Markdown no agregan espacio: si hace falta más aire, se cambian estos
  // valores y se corre `make report-sync REPORT=` para propagarlos.
  show heading.where(level: 1): it => block(above: 1.6em, below: 1.3em)[
    #set text(font: heading-family, size: 20pt, weight: "regular", fill: rgb("#000000"))
    #it
  ]
  show heading.where(level: 2): it => block(above: 1.5em, below: 1.15em)[
    #set text(font: heading-family, size: 15pt, weight: "regular", fill: rgb("#111111"))
    #it
  ]
  show heading.where(level: 3): it => block(above: 1.4em, below: 1em)[
    #set text(font: heading-family, size: 13pt, weight: "regular", fill: rgb("#555555"))
    #it
  ]
  show heading.where(level: 4): it => block(above: 1.3em, below: 0.9em)[
    #set text(font: heading-family, size: 12pt, weight: "bold", fill: rgb("#333333"))
    #it
  ]

  // Citas / Consignas (blockquotes) centradas y en cursiva como en las entregas
  show quote.where(block: true): it => block(
    width: 100%,
    inset: (x: 2.2em, y: 0.6em),
    align(center, emph(it.body))
  )

  // Configuración de figuras e imágenes ("Imagen X: descripción" en cursiva gris)
  set figure(
    supplement: [Imagen],
    gap: 0.85em,
  )
  // Si una imagen fija `width` y `height`, Typst deja una caja del tamaño pedido
  // con la imagen centrada adentro: el espacio sobrante empuja el epígrafe
  // lejos. Acá se reescribe la imagen a su tamaño proporcional exacto para que
  // la caja coincida con lo dibujado. El `show image` interno necesita el guard
  // de dimensiones: si no, la imagen nueva vuelve a entrar en la regla y
  // recursa hasta "maximum show rule depth exceeded".
  show figure: set block(above: 1.4em, below: 1.4em)
  show figure: it => {
    context layout(size => {
      let target = figure-image-size(it.body, size)
      if target == none {
        return it
      }
      show image: img => {
        if img.at("source") != target.source {
          return img
        }
        if img.at("width", default: auto) == target.width and img.at("height", default: auto) == target.height {
          return img
        }
        image(target.source, width: target.width, height: target.height)
      }
      it
    })
  }
  // El epígrafe tiene ancho fijo (92 % del texto) a propósito, sin importar el
  // tamaño de la imagen. No envolver la figura en un `block(width: ...)` para
  // "ajustarlo": un ancho relativo de la imagen (`45%`) se resolvería dos veces
  // y la imagen terminaría más chica.
  show figure.caption: it => context [
    #set par(justify: false, leading: 0.6em)
    #set align(center)
    #block(width: 92%)[
      #text(style: "italic", size: 10.5pt, fill: rgb("#444444"))[
        #it.supplement #it.counter.display(it.numbering): #it.body
      ]
    ]
  ]

  // Red de seguridad: si alguna imagen fija ambas dimensiones y no pasa por el
  // ajuste de `show figure`, se escala proporcionalmente en lugar de deformarse
  // (Typst, por defecto, estira cuando recibe width y height). La franja de la
  // portada usa `fit: "stretch"` explícito y no se ve afectada.
  set image(fit: "contain")

  // Estilo de tablas (encabezado oscuro y filas alternadas o limpias)
  set table(
    inset: (x: 8pt, y: 6pt),
    stroke: 0.5pt + rgb("#d1d5db"),
    align: center + horizon,
    fill: (x, y) => if y == 0 {
      rgb("#0a0a0a")
    } else if calc.even(y) {
      rgb("#f3f4f6")
    } else {
      white
    },
  )
  show table.cell.where(y: 0): set text(
    fill: white,
    weight: "bold",
    font: ("Liberation Sans", "Nimbus Sans", "DejaVu Sans"),
    size: 10pt,
  )

  // Franja cuántica superior e inferior (usa la imagen extraída o el banner vectorial)
  let render-banner() = {
    if banner-image != none {
      image(banner-image, width: 100%, height: 15pt, fit: "stretch")
    } else {
      quantum-banner(height: 15pt)
    }
  }

  // Texto del encabezado en páginas interiores
  let header-text = if running-header != none {
    running-header
  } else if materia != none {
    materia
  } else {
    title
  }

  // Configuración de página (A4, encabezado con logo EXA, pie con barra cuántica y nro de página)
  set page(
    paper: "a4",
    margin: (top: 3.1cm, bottom: 2.6cm, left: 2.54cm, right: 2.54cm),
    header-ascent: 25%,
    footer-descent: 20%,
    header: context {
      if counter(page).get().first() > 1 {
        align(right + horizon)[
          #box(width: 100%)[
            #align(right + horizon)[
              #stack(
                dir: ltr,
                spacing: 10pt,
                align(horizon, text(style: "italic", size: 11.5pt, fill: rgb("#1a1a1a"))[#header-text]),
                if logo-right != none {
                  align(horizon, image(logo-right, height: 1.25cm))
                }
              )
            ]
          ]
        ]
      }
    },
    footer: context {
      let pg = counter(page).get().first()
      if pg > 1 {
        align(right)[
          #pad(bottom: 4pt)[
            #text(size: 11.5pt, fill: rgb("#111111"))[#pg]
          ]
        ]
      }
    },
    background: context {
      let pg = counter(page).get().first()
      if pg == 1 {
        place(top + left, render-banner())
      }
      place(bottom + left, render-banner())
    }
  )

  // ==========================================================================
  // PORTADA (Página 1)
  // ==========================================================================
  page(
    margin: (top: 1.1cm, bottom: 1.5cm, left: 1.5cm, right: 1.5cm),
    header: none,
    footer: none,
  )[
    #set par(justify: false)

    // Logos superiores en las esquinas
    #grid(
      columns: (1fr, 1fr),
      align: (left + horizon, right + horizon),
      if logo-left != none {
        image(logo-left, height: 1.4cm)
      } else { [] },
      if logo-right != none {
        image(logo-right, height: 1.35cm)
      } else { [] },
    )

    #v(0.8cm)

    // Títulos principales de la portada
    #align(center)[
      #set par(leading: 0.75em)
      #if cursada != none [
        #text(size: 21pt, weight: "bold")[#cursada] \
        #v(0.15cm)
      ]
      #if materia != none [
        #text(size: 21pt, weight: "bold")[#materia] \
        #v(0.15cm)
      ]
      #if title != none [
        #text(size: 21pt, weight: "bold")[#title] \
      ]
      #if subtitle != none [
        #v(0.15cm)
        #text(size: 15pt, weight: "regular", fill: rgb("#333333"))[#subtitle]
      ]
    ]

    #v(1fr)

    // Ilustración central cuántica
    #if logo-cover != none [
      #align(center)[
        #image(logo-cover, width: 9.2cm)
      ]
    ]

    #v(1fr)

    // Bloque de Alumno y Profesores en la parte inferior
    #align(center)[
      #set text(size: 12pt)
      #set par(leading: 0.7em)

      #if authors != none and authors != () [
        #let label-alumno = if authors.len() > 1 { "Alumnos" } else { "Alumno" }
        #text(weight: "bold", underline[#label-alumno]) \
        #v(2pt)
        #for author in authors [
          #author.name#if author.email != none and author.email != [] [: #link("mailto:" + content-to-string(author.email))[#author.email].] \
        ]
      ]

      #if profesores != none and profesores != () [
        #v(0.45cm)
        #let label-prof = if profesores.len() > 1 { "Profesores" } else { "Profesor" }
        #text(weight: "bold", underline[#label-prof]) \
        #v(2pt)
        #for prof in profesores [
          #prof.name#if prof.email != none and prof.email != [] [: #link("mailto:" + content-to-string(prof.email))[#prof.email].] \
        ]
      ]
    ]

    #v(0.6cm)
  ]

  // ==========================================================================
  // ÍNDICE / TABLA DE CONTENIDOS (Página 2)
  // ==========================================================================
  if toc {
    // Estilo de las entradas de primer nivel en negrita (como en entregas/)
    show outline.entry.where(level: 1): it => {
      set text(weight: "bold")
      it
    }
    let clean-toc-title = if toc_title == none or empty(toc_title) or content-to-string(toc_title) == "Tabla de contenidos" {
      none
    } else {
      toc_title
    }
    block(above: 0.5em, below: 1.5em)[
      #outline(
        title: clean-toc-title,
        depth: toc_depth,
        indent: 1.4em,
      )
    ]
    pagebreak()
  }

  // ==========================================================================
  // CUERPO DEL INFORME (Texto justificado académico)
  // ==========================================================================
  set par(
    justify: true,
    leading: linestretch * 0.65em,
    spacing: 1.25em,
  )

  doc
}
