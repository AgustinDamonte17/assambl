# Assambl · software

Aplicación de modelado de residencias en woodframe. Este directorio contiene todo el código del producto; la especificación funcional vive en [`../MVP/MVP_01.md`](../MVP/MVP_01.md).

## Organización

```
software/
  frontend/          Interfaz web (Vite + React + TypeScript + Tailwind 4)
    src/
      modelo/        Tipos del proyecto (espejo TS del esquema casa.assambl.json) y geometría plana
      estado/        Estado del proyecto, cola de operaciones, deshacer, autosave y guardar/abrir
      api/           Cliente HTTP hacia el backend
      componentes/   Shell, barra de pasos, controles reutilizables
      pasos/         Un directorio por capa del MVP; la interfaz es secuencial y guiada
        terreno/     Capa 01: ubicación, lote, visor 3D, clima
  backend/
    api/             FastAPI: rutas HTTP finas que llaman al paquete assambl
    assambl/         Paquete Python del producto (estructura de MVP_01 §4.6)
      modelo/        Esquema del proyecto y del sitio (pydantic), estados y operaciones
      geometria/     Polígonos, coordenadas locales, malla del terreno
      fuentes/       Datos externos: nasadem.py, power.py (y nominatim.py solo para buscar)
      clima/         sol.py (posición solar) y resumen.py (temperaturas, vientos, radiación)
      generadores/   glb.py (escritor glTF) y blender.py (script .py de la escena)
      capas/         Composición por capa (hoy: terreno)
      reglas/        r01_terreno.py … r14_electrico.py, cada regla con ID, versión y origen
      catalogo/      ar.json (perfil Argentina) — se completa a partir de la capa 03
    tests/           pytest (test_*.py) y sondas manuales (probar_*.py)
    cache/           Mosaicos, clima y salidas; regenerable, ignorada por git
  docs/              Fuentes de datos y decisiones de arquitectura (docs/decisiones/)
  scripts/           Utilidades de desarrollo
```

Tres reglas de oro:

- **El proyecto (`casa.assambl.json`) es la única fuente de verdad** (MVP_01 §4.2). Todo lo descargado o calculado es caché regenerable y se identifica por los parámetros que lo produjeron.
- **El proyecto solo cambia por operaciones** (MVP_01 §4.4). La interfaz no edita el documento: manda una operación validada al backend (`POST /api/operaciones/aplicar`) y recibe el proyecto nuevo con su registro para el historial. El asistente de IA usará el mismo contrato. Ver [`docs/decisiones/0002_operaciones_e_historial.md`](docs/decisiones/0002_operaciones_e_historial.md).
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

## Flujo actual (capa 01 · Terreno)

1. **Ubicación y relieve.** Buscar una dirección, escribir coordenadas o hacer clic en el mapa. Elegir la extensión del entorno (100–1000 m, 500 por defecto) y generar la escena: se descarga el mosaico de NASADEM que cubre el área, se recorta a los posts nativos y se arma la malla. Cada capa informa su fuente, su resolución y su naturaleza (medición satelital, reanálisis regional o cálculo local).
2. **Lote.** Dibujar los vértices sobre el mapa, crear un rectángulo rápido o cargar el lote lado por lado (longitud y rumbo; el último lado cierra). Sobre el mapa se ven las curvas de nivel del relieve reconstruido, así el lote se dibuja sobre el mismo terreno que después aparece en 3D. Área, perímetro, pendiente y verificaciones de la regla R01 en tiempo real.
3. **Modelo 3D y sol.** Muestra el resultado de la reconstrucción; no pide decisiones. Visor con relieve, lote apoyado sobre la malla, norte y origen, recorrido solar y sombras. Los atajos a equinoccios y solsticios y la hora del visor son solo para mirar.
4. **Clima.** Temperaturas por mes con grados-día, perfil horario, radiación mensual y rosa de vientos de 16 sectores, calculados sobre 5 años de series horarias de NASA POWER. Tampoco pide decisiones.
5. **Avanzar.** El cierre del paso 4 (y el botón **Avanzar** de la barra de pasos) lista lo que falta: ubicación, relieve reconstruido para el origen y el entorno actuales, lote cerrado, dentro del entorno y confirmado. Lo que R01 deja pendiente sin impedir el diseño (pendiente fuera del dominio, relieve más grueso que el lote) viaja como aviso. Los requisitos los decide el backend (`assambl/guia/terreno.py`).

Avanzar lleva a **Diseño de la casa**, que arranca sobre el terreno reconstruido: el visor muestra el relieve y el lote, y el panel reúne los datos de partida y los pendientes. Las herramientas de diseño (huella, ambientes, muros, aberturas) son el próximo desarrollo.

Cada cambio de diseño es una operación que aplica el backend; **Deshacer** (o Ctrl+Z) vuelve atrás la última. El proyecto se guarda automáticamente en el navegador y se exporta/importa como `casa.assambl.json`; el registro de operaciones queda aparte, también en el navegador, hasta que exista la base de datos ([`docs/decisiones/0001_almacenamiento.md`](docs/decisiones/0001_almacenamiento.md)).

### Salida de la fase de terreno

La geometría se construye **una sola vez, en Python**, y se publica como GLB por capa (MVP_01 §4.5). El mismo generador produce el script de Blender, así que no hay dos implementaciones que puedan desincronizarse:

```
POST /api/terreno/escena          arma la escena y devuelve una referencia
GET  /api/terreno/escena/{ref}.glb   el modelo 3D (visor web y Blender)
GET  /api/terreno/escena/{ref}.py    script de Blender que reconstruye la escena
GET  /api/terreno/escena/{ref}/curvas  curvas de nivel de la escena, en coordenadas locales
POST /api/terreno/requisitos         qué falta para cerrar el terreno y pasar al diseño
GET  /api/terreno/sol                trayectoria del día, muestreada cada 5 minutos
GET  /api/clima                      resúmenes de NASA POWER con su procedencia
GET  /api/operaciones                catálogo de operaciones con el esquema de sus parámetros
POST /api/operaciones/aplicar        aplica una operación al proyecto y devuelve el registro
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
cd backend; .venv\Scripts\python -m pytest -q         # 98 pruebas, sin red
.venv\Scripts\python tests\probar_nasa.py --cotas     # coteja NASADEM contra cotas conocidas
cd ..; npm install --no-save puppeteer gltf-validator
node scripts/probar_ui.cjs                            # recorrido en navegador headless con capturas
```

El recorrido en navegador necesita la aplicación levantada (`npm run dev`) y deja las capturas en `backend/cache/salidas/ui/`. Las dos herramientas de `--no-save` se instalan juntas a propósito: instalar una sola purga la otra, porque no están en `package.json`.

Las sondas `backend/tests/probar_*.py` sí salen a internet y sirven para verificar las fuentes a mano. `tests/tesela_de_prueba.py` permite probar la cadena completa del relieve sin credencial, con un mosaico sintético que hay que borrar después (ver la documentación de fuentes).

## Pendientes inmediatos de la capa 01

- Fuente de relieve: evaluar alternativas a NASADEM (resolución de ~30 m, token de Earthdata, disponibilidad) antes de seguir invirtiendo en el paso Lote.
- Retiros de frente, fondo y laterales dibujados como zona edificable (ya están en el esquema del proyecto).
- Visor HTML autocontenido con el GLB embebido en base64 (MVP_01 §4.5).
- Plano de implantación SVG (entregable 6.1).
