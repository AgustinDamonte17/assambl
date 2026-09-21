# assambl.com

Landing page for **Assambl** — _You design. Assambl solves._

Minimal, pre-product landing: the `ASSAMBL()` wordmark with a looping
argument animation (`A()` → `ASSAMBL()` → `ASSAMBL(idea)` → … → `ASSAMBL(r2b)`),
a slogan and a contact line. No CMS, no database yet.

## Stack

- Next.js (App Router) + React
- Tailwind CSS v4
- Fonts: Archivo Black (wordmark), IBM Plex Mono (UI) via `next/font`
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
