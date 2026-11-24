# Plantilla de Informes en Quarto (`reports/`)

Esta carpeta contiene la plantilla y configuración de **Quarto + Typst** para compilar informes académicos en PDF con la estética de la cátedra **Fundamentos de la Computación Cuántica** (Facultad de Ciencias Exactas - UNICEN).

## Estructura de Archivos

```text
reports/
├── _quarto.yml                 # Configuración general (logos, autor, docentes, formato)
├── _template/
│   ├── typst-template.typ      # Diseño visual (portada, barras cuánticas, tipografía, tablas)
│   └── typst-show.typ          # Puente de variables YAML entre Quarto y Typst
├── assets/
│   └── logos/                  # Logos extraídos (UNICEN, EXA, logo cuántico, barra reticulada)
├── informe.qmd                 # Documento fuente del informe (Grover y QPE)
└── informe.pdf                 # PDF compilado listo para entregar
```

## Cómo Compilar el Informe

Para generar el archivo `informe.pdf`, ejecutá desde la raíz del repositorio (o dentro de `reports/`):

```bash
quarto render reports/informe.qmd
```

Si querés previsualizar los cambios en tiempo real mientras escribís:

```bash
quarto preview reports/informe.qmd
```

## Guía Rápida de Uso y Estética

### 1. Imágenes con Descripción y Referencias Cruzadas
Para insertar una imagen centrada con epígrafe automático (`Imagen 1: ...`):

```markdown
![Circuito correspondiente al oráculo de Grover.](assets/mi_circuito.png){#fig-oraculo width=85%}
```

- El prefijo `Imagen X:` en cursiva gris se agrega automáticamente.
- Podés referenciarla en el texto escribiendo `@fig-oraculo` (se renderiza como `Imagen 1`).

### 2. Citas o Consignas Centradas
Tal como en tus informes anteriores, cualquier bloque de cita (`>`) se formatea centrado y en cursiva, ideal para colocar las consignas de los ejercicios:

```markdown
> Implementar el algoritmo de Grover para la función booleana $x_2' x_1 x_0$.
```

### 3. Tablas Académicas
Las tablas en Markdown toman automáticamente el encabezado negro con texto blanco y filas cebradas grises/blancas:

```markdown
| Qubits | Estado | Frecuencia | ¿Correcto? |
|:------:|:------:|:----------:|:----------:|
| 011    | 3      | 968        | SÍ         |

: Resultados obtenidos en la simulación. {#tbl-resultados}
```

### 4. Saltos de Página y Ecuaciones
- **Salto de página:** `{{< pagebreak >}}`
- **Ecuaciones en línea:** `$|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$`
- **Ecuaciones en bloque:**
  ```markdown
  $$U|\psi\rangle = e^{2\pi i \theta}|\psi\rangle$$
  ```
