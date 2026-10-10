---
name: assambl-ui
description: Reglas de interfaz de la app de Assambl (software/frontend, el configurador de casas por capas en localhost:5173) — tipografía en tres roles (head, body, label), cuándo va mono y cuándo no, tokens, pesos y componentes base. Usala antes de crear o modificar cualquier pantalla, panel, componente, texto SVG o estilo de la app, y siempre que haya que decidir en qué fuente va un texto.
---

# Interfaz de Assambl

La app vive en `software/frontend/` (Vite + React + Tailwind 4). Los tokens están en
`software/frontend/src/estilos.css`; los componentes base, en `software/frontend/src/componentes/ui.tsx`.

## Tipografía: tres roles

Familia **Chivo + Chivo Mono**. La mono no es la voz de la interfaz: queda solo para rótulos y datos, donde
aporta carácter técnico y columnas alineadas. Leer texto corrido en monoespaciada cansa.

| Token | Valor | Clase Tailwind | Pesos | Para qué |
| --- | --- | --- | --- | --- |
| `--font-head` | `"Chivo", system-ui, sans-serif` | `font-head` | 800 (`font-extrabold`) en h1 · 700 (`font-bold`) en títulos de tarjeta o sección | Títulos de pantalla y de tarjeta/sección |
| `--font-body` | `"Chivo", system-ui, sans-serif` | `font-body` (es la fuente base: no hace falta ponerla) | 400 · 500 (`font-medium`) para énfasis | Todo lo que se lee |
| `--font-label` | `"Chivo Mono", ui-monospace, monospace` | `font-label` | 400 · 500 (`font-medium`) | **Solo** rótulos cortos y datos |

`--font-display` (Archivo Black) queda **únicamente** para el logo `ASSAMBL()`. No se usa en títulos.

### Qué va en cada rol

**`--font-head`**
- h1 de pantalla: `font-head font-extrabold text-3xl tracking-tight` (p. ej. «¿Cómo querés empezar tu casa?»).
- Título de tarjeta o de pieza seleccionada: `font-head font-bold` (p. ej. «Contala con tus palabras», «Dormitorio principal»).

**`--font-body`** — todo lo que se lee:
- párrafos, introducciones y descripciones de tarjetas;
- botones (incluido `Boton`, aunque vaya en mayúsculas) y links;
- chips y ejemplos de prompt;
- placeholder y texto de `textarea` e `input` de texto;
- nombres de capa en la barra lateral;
- diálogo de Monti, preguntas y opciones de la charla;
- texto de ayuda, avisos y metadatos en prosa («Se guarda solo en este navegador…»);
- nombres de ambientes en la planta (SVG, peso 700).

**`--font-label`** — solo rótulos cortos y datos:
- números de capa y de paso (`01`, `02`, `03`…; el `1` `2` `3` de las tarjetas);
- tags `NÚCLEO` / `HOOK` y etiquetas de estado (`Etiqueta`, `EtiquetaFuente`, `EtiquetaNaturaleza`);
- eyebrows y rótulos de sección en mayúsculas: «CAPA 03 · CASA», «SECUENCIA», «PLANTA 2D», los títulos de `Seccion`, los rótulos de `Campo`;
- medidas y cotas: `164 m²`, `2,40 m`, `38×89 mm`, superficies en la planta, cotas de arrastre, barra de escala, coordenadas del cursor;
- valores de `Dato`, celdas de tablas numéricas y campos numéricos (`type="number"`, `type="date"`, `inputMode="decimal"`);
- IDs y timestamps: «Proyecto a5406309», «2026-10-10 15:46», `dorm_principal`, `R03.05`;
- badge de modelo IA («IA: openai · gpt-5-mini») y estado «API CONECTADA»;
- atajos de teclado (`<kbd>`);
- firmas de código tipo `assambl(intent) → building` y la palabra dentro del logo (`ASSAMBL(casa)`).

### Prueba rápida para casos dudosos

> Si el texto tiene **más de ~6 palabras** o se lee como **una oración**, va en `--font-body`.
> Si es un **código, número, unidad o etiqueta**, va en `--font-label`.

Cuando una misma línea mezcla las dos cosas, se parte: la prosa en body y el dato en un `<span className="font-label">`.
Ejemplo: `<span className="font-label">{v.id}</span> · {v.descripcion}`.

Ningún párrafo, botón ni texto de más de una línea se renderiza en mono.

## Cómo aplicarlo en el código

- La fuente base (`html, body`) ya es `--font-body`. No hace falta poner `font-body` salvo para devolver a body
  un texto que está dentro de algo en `font-label` (p. ej. un valor en prosa dentro de `Dato`).
- `.font-label` ya activa `font-variant-numeric: tabular-nums`; no hace falta agregar `tabular-nums`.
- `font-mono` y `<kbd>` apuntan a `--font-label` por compatibilidad, pero en código nuevo se escribe `font-label`.
- Texto SVG: se le pone `className="font-label"` a cotas, áreas, escala, norte y coordenadas. Los nombres van
  sin clase (heredan body).
- Pesos cargados: Chivo 400, 500, 700, 800; Chivo Mono 400, 500. No usar `font-semibold` (600) ni `font-bold` en
  mono: el navegador los sintetiza y se ven mal. Para resaltar un dato en mono, `font-medium`.
- No hacer reemplazos globales de fuente: decidir elemento por elemento con la prueba rápida.
- Cualquier fuente de UI que no sea Chivo / Chivo Mono (y Archivo Black en el logo) es un error.

## Tamaños y layout

- Prosa: mínimo 11px (`text-[11px]`); lo normal es `text-xs` (12px) a `text-[13px]` en paneles y 15px en la
  introducción de una pantalla. La proporcional ocupa menos ancho que la mono, así que el mismo tamaño se lee más
  chico: no bajar de 11px en texto corrido.
- Rótulos en mono: 9–11px, en mayúsculas con `tracking-wide` o `tracking-widest`.
- Tags y etiquetas de estado llevan `whitespace-nowrap`: no se parten en dos renglones.
- Chips truncados: con CSS (`max-w-full truncate`) y el texto completo en `title`, nunca cortando el string por
  cantidad de caracteres (eso dependía del ancho fijo de la mono).
- Barra lateral (220px): nombre de capa en `text-xs leading-snug`, número y tag en mono a los costados.

## Cómo se cargan las fuentes

`software/frontend/index.html` las pide a Google Fonts en un solo `<link>`:
`Archivo+Black`, `Chivo:wght@400;500;700;800`, `Chivo+Mono:wght@400;500`. Si se agrega un peso, se agrega ahí.

## Componentes base (`componentes/ui.tsx`)

- `Boton` — body, mayúsculas, `text-xs`. `primario` en `signal`.
- `Seccion` — rótulo en label (mayúsculas, `tracking-widest`, `text-rebar`).
- `Campo` — rótulo en label; el input numérico sale en label por CSS.
- `Dato` — etiqueta en body, valor y sufijo en label.
- `Etiqueta`, `EtiquetaFuente`, `EtiquetaNaturaleza` — tags en label.
- `Aviso`, `FichaFuente` — prosa en body, 11px.

## Paleta

Tokens en `:root` de `estilos.css`: `--ink`, `--concrete`, `--concrete-2`, `--concrete-3`, `--signal` (acento),
`--rebar` (texto secundario), `--resolved`, `--warn`, `--line`. Se usan con las clases `text-ink`, `bg-concrete`,
`border-line`, etc. Sin bordes redondeados.
