# assambl
Assambl

## gstack

Usamos [gstack](https://github.com/garrytan/gstack) como skills de Cursor. La regla `.cursor/rules/gstack.mdc` le indica al agente cómo usarlos.

Requisitos: git, [bun](https://bun.sh) y Node.js. En Windows, además, Git Bash.

Instalar bun:

```powershell
# Windows (PowerShell)
irm bun.sh/install.ps1 | iex
```

```bash
# macOS / Linux
curl -fsSL https://bun.sh/install | bash
```

Instalar gstack para Cursor (en Windows, desde Git Bash):

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
cd ~/.claude/skills/gstack && ./setup --host cursor
```

Los skills quedan en `~/.cursor/skills` con prefijo `gstack-` (ej. `/gstack-office-hours`, `/gstack-review`, `/gstack-qa`). Para actualizar: `/gstack-upgrade`, o `git pull` y volver a correr `./setup --host cursor`.

En Windows, `/gstack-cso` requiere Visual Studio 2022 Build Tools con "Desktop development with C++".
