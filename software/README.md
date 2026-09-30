# Assambl · software

Aplicación de modelado de residencias en woodframe. Este directorio contiene todo el código del producto; la especificación funcional vive en [`../MVP/MVP_01.md`](../MVP/MVP_01.md).

## Organización

```
software/
  frontend/          Interfaz web (Vite + React + TypeScript + Tailwind 4)
    src/
      modelo/        Tipos del proyecto (espejo TS del esquema casa.assambl.json) y geometría plana
      estado/        Estado del proyecto en memoria, autosave y guardar/abrir
      api/           Cliente HTTP hacia el backend
      componentes/   Shell, barra de pasos, controles reutilizables
      pasos/         Un directorio por capa del MVP; la interfaz es secuencial y guiada
        terreno/     Capa 01: ubicación, lote, visor 3D, clima
        casa/        Capa 03: cómo empezar (IA, imagen, dibujo), alternativas y editor de planta 2D
  backend/
    api/             FastAPI: rutas HTTP finas que llaman al paquete assambl
    assambl/         Paquete Python del producto (estructura de MVP_01 §4.6)
      modelo/        Esquema del proyecto y del sitio (pydantic), estados
      geometria/     Polígonos, coordenadas locales, malla del terreno
      fuentes/       Datos externos: nasadem.py, power.py (y nominatim.py solo para buscar)
      clima/         sol.py (posición solar) y resumen.py (temperaturas, vientos, radiación)
      generadores/   glb.py (escritor glTF) y blender.py (script .py de la escena)
      capas/         Composición por capa: terreno.py, casa.py (plantas desde ambientes)
      reglas/        r01_terreno.py … r14_electrico.py, cada regla con ID, versión y origen (hoy r01 y r03)
      ia/            Asistente de diseño y proveedores de IA intercambiables (OpenAI, Anthropic, simulado)
      catalogo/      ar.json (perfil Argentina): aberturas; se completa con el resto de la capa 03
    tests/           pytest (test_*.py) y sondas manuales (probar_*.py)
    cache/           Mosaicos, clima y salidas; regenerable, ignorada por git
  docs/              Decisiones técnicas y fuentes de datos
  scripts/           Utilidades de desarrollo
```

Dos reglas de oro:

- **El proyecto (`casa.assambl.json`) es la única fuente de verdad** (MVP_01 §4.2). Todo lo descargado o calculado es caché regenerable y se identifica por los parámetros que lo produjeron.
- **La NASA es la única fuente externa de datos del modelo.** Relieve de NASADEM, clima de NASA POWER; proyección, malla, sol y sombras se calculan acá. El buscador de direcciones y el mapa base son ayudas de navegación y no aportan geometría. El detalle está en [`docs/fuentes_de_datos_terreno.md`](docs/fuentes_de_datos_terreno.md).

## Requisitos

- Node.js ≥ 20 y npm
- Python ≥ 3.11
- Conexión a internet
- Un token de **NASA Earthdata** para descargar relieve (ver abajo). Sin token la aplicación funciona, pero la escena sale plana y marcada como provisional.

## Puesta en marcha

Desde `software/`:

```powershell
npm run setup      # instala dependencias del frontend y crea backend/.venv con las suyas
npm run dev        # levanta API (http://localhost:8765) y web (http://localhost:5173) juntas
```

Abrir <http://localhost:5173>. La API documenta sus rutas en <http://localhost:8765/docs>. El puerto se cambia con `API_PORT` (el frontend lo lee en `vite.config.ts`); se eligió 8765 porque el 8000 suele estar ocupado por otros servidores de desarrollo.

Comandos separados:

```powershell
npm run dev:web    # solo frontend
npm run dev:api    # solo backend (usa backend/.venv si existe)
npm run check      # tsc + compilación del frontend y pruebas del backend
```

## Token de Earthdata

1. Crear una cuenta gratuita en <https://urs.earthdata.nasa.gov>.
2. En el perfil, pestaña **Generate Token**, generar y copiar el token (vale 60 días).
3. Crear un archivo `.env` con una línea:

```
EARTHDATA_TOKEN=eyJ0eXAiOi…
```

Se busca en `backend/.env`, `software/.env` y la raíz del repositorio, en ese orden. Los `.env` están en `.gitignore`: **el token no va en el código ni se commitea.** `GET /api/terreno/credencial` informa si está presente y válido, y el panel de ubicación lo muestra.

NASA POWER no necesita credencial, así que el clima funciona siempre.

## Asistente de IA (capa 03)

El paso Casa usa IA para conversar con el usuario y leer bosquejos. El prestador se elige en el mismo `.env`
y se cambia sin tocar código:

```
IA_PROVEEDOR=openai          # openai | anthropic | simulado (vacío: el primero con clave)
OPENAI_API_KEY=sk-...
# IA_MODELO=gpt-5-mini       # opcional
# ANTHROPIC_API_KEY=...      # para IA_PROVEEDOR=anthropic
# IA_URL_BASE=...            # cualquier servicio compatible con Chat Completions (Ollama, OpenRouter, Groq…)
```

Sin clave funciona igual en **modo demostración** (guion fijo, avisado en la interfaz). `GET /api/casa/ia`
dice qué proveedor está activo. El diseño completo del paso está en [`docs/paso_casa.md`](docs/paso_casa.md).

## Flujo actual (capa 01 · Terreno)

1. **Ubicación y relieve.** Buscar una dirección, escribir coordenadas o hacer clic en el mapa. Elegir la extensión del entorno (100–2000 m, 500 por defecto) y generar la escena: se descarga el mosaico de NASADEM que cubre el área, se recorta a los posts nativos y se arma la malla. Cada capa informa su fuente, su resolución y su naturaleza (medición satelital, reanálisis regional o cálculo local).
2. **Lote.** Dibujar los vértices sobre el mapa, crear un rectángulo rápido o cargar el lote lado por lado (longitud y rumbo; el último lado cierra). Área, perímetro, pendiente y verificaciones de la regla R01 en tiempo real.
3. **Modelo 3D y sol.** Visor que carga el `.glb` del backend: relieve, lote apoyado sobre la malla, norte y origen, recorrido solar del día y sombras. Fecha, hora y huso son editables, con atajos a equinoccios y solsticios. Desde el panel se descargan el `.glb` y el script `.py` de Blender.
4. **Clima.** Temperaturas por mes con grados-día, perfil horario, radiación mensual y rosa de vientos de 16 sectores, calculados sobre 5 años de series horarias de NASA POWER.

El proyecto se guarda automáticamente en el navegador y se exporta/importa como `casa.assambl.json`.

### Capa 03 · Casa (planta)

1. **Cómo empezar.** Contarla con palabras (IA), armarla paso a paso con Monti (IA con preguntas y opciones),
   subir un bosquejo o un plano (IA con visión), dibujar desde cero o abrir el ejemplo Angus Ranch.
2. **Alternativas fundamentadas.** El programa armado en la charla se resuelve en tres partidos de planta que
   parten de diez plantas de referencia y explican qué ganan y qué resignan según fundamentos de diseño
   ([`docs/fundamentos_diseno.md`](docs/fundamentos_diseno.md)). También se puede partir directamente de una
   de esas plantas.
3. **Editor 2D.** Muros a 90° con imanes, puertas y ventanas del catálogo, ambientes con nombre, arrastre de
   muros que arrastra lo conectado, deshacer, y el estado de cada pieza verificado en vivo con las reglas R03.

### Salida de la fase de terreno

La geometría se construye **una sola vez, en Python**, y se publica como GLB por capa (MVP_01 §4.5). El mismo generador produce el script de Blender, así que no hay dos implementaciones que puedan desincronizarse:

```
POST /api/terreno/escena          arma la escena y devuelve una referencia
GET  /api/terreno/escena/{ref}.glb   el modelo 3D (visor web y Blender)
GET  /api/terreno/escena/{ref}.py    script de Blender que reconstruye la escena
GET  /api/terreno/sol                trayectoria del día, muestreada cada 5 minutos
GET  /api/clima                      resúmenes de NASA POWER con su procedencia
```

El `.glb` se valida con el validador oficial de Khronos:

```powershell
npm install --no-save gltf-validator
node scripts/validar_glb.cjs ruta\al\archivo.glb
```

## Qué dicen y qué no dicen los datos

La interfaz lo repite en cada panel, y vale repetirlo acá:

- **El relieve no es una mensura.** NASADEM tiene posts cada ~30 m: un lote urbano cae entre dos posts. La pendiente que se informa es la de la ladera, no la del interior del lote. Para fundaciones hace falta un relevamiento topográfico. Por eso el código no interpola ni agrega ruido para «mejorar» el aspecto: las facetas que se ven son la resolución real del dato.
- **El clima es una estimación regional.** Una celda de NASA POWER mide unos 50 × 60 km. El viento está dado a 10 m de altura y sin obstáculos: sirve para elegir orientaciones, no para dimensionar una abertura.
- **Sol, radiación y sombra son tres datos distintos.** La posición del sol es un cálculo astronómico exacto; la radiación es un histórico promediado de la NASA; la sombra sale del modelo 3D y tiene la resolución del relieve.

## Problemas conocidos y soluciones

- **La API no conecta («api sin conexión»).** Verificar que `npm run dev:api` esté corriendo y que nadie más use el 8765 (`Get-NetTCPConnection -LocalPort 8765`).
- **La escena sale plana y provisional.** Falta el `EARTHDATA_TOKEN`, está vencido, o el punto está fuera de la cobertura de NASADEM (60° N a 56° S). El aviso del panel dice cuál de los tres es. Para verificar el token solo: `.venv\Scripts\python tests\probar_nasa.py`.
- **La primera descarga tarda.** Un mosaico de NASADEM son ~26 MB por grado y los 5 años horarios de POWER son cinco pedidos que pueden llevar varios minutos. Después todo sale de `backend/cache/` en menos de un segundo. Para empezar de cero, borrar esa carpeta.
- **`getaddrinfo failed`.** Corte de DNS transitorio; se reintenta. Si persiste, volver a generar la escena.
- **Recarga automática del backend.** `dev:api` usa `uvicorn --reload`; `API_RELOAD=0 npm run dev:api` lo desactiva.

## Pruebas

```powershell
cd backend; .venv\Scripts\python -m pytest -q         # 73 pruebas, sin red
.venv\Scripts\python tests\probar_nasa.py --cotas     # coteja NASADEM contra cotas conocidas
cd ..; npm install --no-save puppeteer gltf-validator
node scripts/probar_ui.cjs                            # recorrido en navegador headless con capturas
```

El recorrido en navegador necesita la aplicación levantada (`npm run dev`) y deja las capturas en `backend/cache/salidas/ui/`. Las dos herramientas de `--no-save` se instalan juntas a propósito: instalar una sola purga la otra, porque no están en `package.json`.

Las sondas `backend/tests/probar_*.py` sí salen a internet y sirven para verificar las fuentes a mano. `tests/tesela_de_prueba.py` permite probar la cadena completa del relieve sin credencial, con un mosaico sintético que hay que borrar después (ver la documentación de fuentes).

## Pendientes inmediatos de la capa 01

- Retiros de frente, fondo y laterales dibujados como zona edificable (ya están en el esquema del proyecto).
- Visor HTML autocontenido con el GLB embebido en base64 (MVP_01 §4.5).
- Plano de implantación SVG (entregable 6.1).
