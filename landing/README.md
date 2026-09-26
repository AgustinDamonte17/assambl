# assambl.com

Landing page for **Assambl** — _Vos diseñás. Assambl resuelve._

Minimal, pre-product landing: the `ASSAMBL()` wordmark with a looping
argument animation (`A()` → `ASSAMBL()` → `ASSAMBL(idea)` → … → `ASSAMBL(r2b)`),
a slogan and a contact line, followed by a scroll-driven 3D explode of the real
Angus Ranch model, layer by layer. No CMS, no database yet.

## Stack

- Next.js (App Router) + React
- Tailwind CSS v4
- Fonts: Archivo Black (wordmark), IBM Plex Mono (UI) via `next/font`
- three.js + @react-three/fiber (explode section only, lazy-loaded)
- Deployed on Vercel → `assambl.com`

## Development

```bash
npm install
npm run dev      # http://localhost:3000
npm run build    # production build
npm run lint
```

## Structure

```
src/
  app/
    layout.tsx     fonts, metadata, theme color
    page.tsx       landing layout (header / logo / slogan / footer)
    globals.css    brand tokens (ink, concrete, signal, rebar, resolved)
    icon.svg       favicon: A()
  components/
    Logo.tsx       animated wordmark (client component)
    usePrefersReducedMotion.ts
    explode/
      ExplodeSection.tsx  sticky section, HUD, scroll progress, poster, lazy 3D
      ExplodeScene.tsx    R3F canvas, fixed ortho camera, framing, smoothing
      model.ts            GLB loading, brand materials, per-node transforms
      config.ts           choreography: steps, part motions, captions
      progress.ts         scroll progress store (refs, no React state)
public/models/            angus-ranch.glb + posters (light/dark, assembled/exploded)
scripts/angus/
  export_glb.py           Angus Ranch V09 → GLB (reproducible, no Blender needed)
  posters.mjs             renders the posters from the real GLB
  angus-ranch.report.json size, triangles, draw calls per node
```

## Brand tokens

| Token     | Light     | Dark      | Use                        |
| --------- | --------- | --------- | -------------------------- |
| ink       | `#111111` | —         | text (light), bg (dark)    |
| concrete  | `#E8E6E1` | —         | bg (light), text (dark)    |
| signal    | `#FF4F1F` | `#FF4F1F` | parentheses, cursor, `//`  |
| rebar     | `#7A7A78` | `#8B8B88` | secondary text             |
| resolved  | `#1FA45A` | `#3DFF7A` | `r2b` state                |

Animation timings live in `src/components/Logo.tsx` (`T` object).
`prefers-reduced-motion` renders a static `ASSAMBL(house)`.

## Angus Ranch explode

Source of truth: `../angus_ranch_V09_11_capas.py` (the Blender script). The
browser never runs it; it loads `public/models/angus-ranch.glb`.

### Regenerate the GLB

```bash
pip install numpy
npm run export:angus   # python3 scripts/angus/export_glb.py [--source ...] [--out ...]
```

The exporter imports the V09 script and rebuilds its geometry in memory, the same
path as its `--check` mode (read-only; nothing is written next to it). It then
merges pieces into one mesh per animation node and writes a Y-up glTF (metres,
house pivot at the origin). Nodes are named `<layer>__<part>[__<facade>]`, e.g.
`L05_Siding__siding__N`; their `extras` carry `layer`, `part`, `size` and, for
envelope parts, the facade direction `dir`. The collection → node mapping lives
in `COLLECTIONS` at the top of `export_glb.py`; pieces smaller than 6 cm (nuts,
washers) are skipped and counted in the report.

### Regenerate the posters

```bash
npm run build && npm start                     # another terminal
CHROMIUM_PATH=/path/to/chrome npm run posters  # defaults to installed Chrome
```

### Tune the choreography

Everything is in `src/components/explode/config.ts`:

- `PART_RULES`: per layer/part, a list of motions with a progress `range`,
  `lift` (in wall heights), `out` (in house widths, along the facade), optional
  `rotate` and an `ease`. Positions are always computed from the rest pose.
- `STEPS`: when each V09 layer name is shown and highlighted with `--signal`.
- `CAPTIONS`: the three short texts.
- Scroll length: `.explode-track` in `globals.css` (280svh mobile, 320svh desktop).

`prefers-reduced-motion` replaces the scroll section with the static exploded
poster and the layer list. Without WebGL, or if the GLB fails, the poster stays.
