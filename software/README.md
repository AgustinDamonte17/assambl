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
        terreno/     Capa 01: ubicación, lote y modelo 3D del sitio (con sol y clima)
        diseno/      Diseño de la casa sobre el sitio reconstruido
  backend/
    api/             FastAPI: rutas HTTP finas que llaman al paquete assambl
    assambl/         Paquete Python del producto (estructura de MVP_01 §4.6)
      modelo/        Esquema del proyecto y del sitio (pydantic), estados y operaciones
      geometria/     Polígonos, coordenadas locales, malla del terreno
      fuentes/       Datos externos: imagen_satelital.py, osm.py, power.py (nominatim.py solo para buscar;
                     nasadem.py en pausa)
      sitio/         Modelo 3D del sitio: detección de árboles, interpretación con IA (opcional), composición
      clima/         sol.py (posición solar) y resumen.py (temperaturas, vientos, radiación)
      generadores/   glb.py (escritor glTF con texturas) y blender.py (script .py de la escena con relieve, en pausa)
      capas/         Composición por capa (terreno con relieve, en pausa)
      guia/          Qué falta para avanzar en cada etapa (determinístico, sin IA)
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
- **Cada dato declara de dónde sale y cuánto vale.** El sitio se reconstruye desde la imagen satelital (Esri World Imagery) y OpenStreetMap, con el terreno supuesto plano; el clima viene de NASA POWER; sol y sombras se calculan acá. Cada capa informa su fuente, su resolución y su naturaleza (medición, estimación regional, cálculo local o interpretación de imagen). Ver [`docs/decisiones/0005_modelo_del_sitio.md`](docs/decisiones/0005_modelo_del_sitio.md).

## Requisitos

- Node.js ≥ 20 y npm
- Python ≥ 3.11
- Conexión a internet (imagen satelital, OpenStreetMap y NASA POWER). Sin red, `ASSAMBL_IMAGEN_SINTETICA=1` usa un mundo sintético de prueba.
- Opcional: una clave de la API de Anthropic para que la IA interprete la imagen del lote (ver abajo). Sin clave, los árboles se detectan por color.

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

## Variables de entorno

Se leen de `backend/.env`, `software/.env` o la raíz del repositorio, en ese orden. Los `.env` están en `.gitignore`: **las claves no van en el código ni se commitean.**

```
ANTHROPIC_API_KEY=sk-ant-...        # opcional: interpretación del lote con IA
ASSAMBL_MODELO_IA=claude-opus-5     # opcional: modelo de visión
ASSAMBL_IA=0                        # opcional: desactiva la IA aunque haya clave
ASSAMBL_IMAGEN_SINTETICA=1          # desarrollo sin red: mundo sintético, marcado en la interfaz
ASSAMBL_OVERPASS_URL=...            # opcional: otro servidor de Overpass
```

El relieve de NASADEM (y su `EARTHDATA_TOKEN`) está en pausa; ver [`docs/fuentes_de_datos_terreno.md`](docs/fuentes_de_datos_terreno.md).

## Flujo actual (capa 01 · Terreno)

1. **Ubicación.** Buscar una dirección, escribir coordenadas o hacer clic en el mapa, y elegir la extensión del entorno (100–1000 m, 500 por defecto).
2. **Lote.** Dibujar los vértices sobre la imagen satelital, crear un rectángulo rápido o cargar el lote lado por lado (longitud y rumbo; el último lado cierra). Área, perímetro y verificaciones de la regla R01 en tiempo real.
3. **Modelo 3D.** Al entrar, el software reconstruye el sitio sin pedir nada: suelo con la imagen satelital (el lote en alta definición, el entorno en baja), calles y construcciones de OpenStreetMap, y árboles detectados en la imagen. Los del lote salen con identificador, copa y altura, y se interpretan con IA si hay clave. El terreno se supone plano. En el mismo panel están el recorrido del sol (solo para mirar), el clima de NASA POWER y la procedencia de cada capa. Abajo, **← Ubicación**, **← Lote** y **Confirmar**. Confirmar se habilita cuando están la ubicación, un lote cerrado y confirmado dentro del entorno, y el modelo generado para ese lote; los pendientes que no bloquean (pendiente no relevada, superficie chica) viajan como aviso. Los requisitos los decide el backend (`assambl/guia/terreno.py`).

Confirmar lleva a **Diseño de la casa**, que arranca sobre el sitio reconstruido: el visor muestra el lote, sus árboles y el entorno, y el panel reúne los datos de partida y los pendientes. Las herramientas de diseño (huella, ambientes, muros, aberturas) son el próximo desarrollo.

Cada cambio de diseño es una operación que aplica el backend; **Deshacer** (o Ctrl+Z) vuelve atrás la última. El proyecto se guarda automáticamente en el navegador y se exporta/importa como `casa.assambl.json`; el registro de operaciones queda aparte, también en el navegador, hasta que exista la base de datos ([`docs/decisiones/0001_almacenamiento.md`](docs/decisiones/0001_almacenamiento.md)).

### Salida de la fase de terreno

La geometría se construye **una sola vez, en Python**, y se publica como un GLB con un nodo por capa y las imágenes embebidas (MVP_01 §4.5). El visor y el diseño cargan el mismo archivo, que también abre Blender:

```
POST /api/terreno/escena             reconstruye el sitio y devuelve una referencia, el resumen y los árboles del lote
GET  /api/terreno/escena/{ref}.glb   el modelo 3D del sitio
POST /api/terreno/requisitos         qué falta para confirmar el terreno y pasar al diseño
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

- **El terreno plano es un supuesto.** No se releva la pendiente: para fundaciones hace falta un relevamiento topográfico, y R01.05 queda pendiente hasta tenerlo.
- **El sitio es una interpretación de una foto.** La fecha de la imagen es desconocida; posición y copa de los árboles se miden en la imagen, pero la altura de árboles y construcciones es supuesta salvo que la fuente la informe. Calles y construcciones son las mapeadas en OpenStreetMap.
- **El clima es una estimación regional.** Una celda de NASA POWER mide unos 50 × 60 km. El viento está dado a 10 m de altura y sin obstáculos: sirve para elegir orientaciones, no para dimensionar una abertura.
- **Sol, radiación y sombra son tres datos distintos.** La posición del sol es un cálculo astronómico exacto; la radiación es un histórico promediado de la NASA; la sombra sale de los árboles y construcciones del modelo, con sus alturas supuestas.

## Problemas conocidos y soluciones

- **La API no conecta («api sin conexión»).** Verificar que `npm run dev:api` esté corriendo y que nadie más use el 8765 (`Get-NetTCPConnection -LocalPort 8765`).
- **El suelo sale gris y sin árboles.** No hubo imagen satelital (sin red o sin cobertura); el panel del paso 3 lo avisa.
- **«Map data not yet available».** Es el mosaico de relleno de Esri; el backend lo reconoce y usa uno de menor zoom ampliado.
- **La primera reconstrucción tarda.** Descarga unos 60–130 mosaicos de imagen, consulta OpenStreetMap y, si hay clave, la IA. Los 5 años horarios de POWER pueden llevar varios minutos. Después todo sale de `backend/cache/`. Para empezar de cero, borrar esa carpeta.
- **`getaddrinfo failed`.** Corte de DNS transitorio; se reintenta. Si persiste, volver a generar la escena.
- **Recarga automática del backend.** `dev:api` usa `uvicorn --reload`; `API_RELOAD=0 npm run dev:api` lo desactiva.

## Pruebas

```powershell
cd backend; .venv\Scripts\python -m pytest -q         # 108 pruebas, sin red
.venv\Scripts\python tests\probar_nasa.py --cotas     # coteja NASADEM contra cotas conocidas
cd ..; npm install --no-save puppeteer gltf-validator
node scripts/probar_ui.cjs                            # recorrido en navegador headless con capturas
```

El recorrido en navegador necesita la aplicación levantada (`npm run dev`) y deja las capturas en `backend/cache/salidas/ui/`. Las dos herramientas de `--no-save` se instalan juntas a propósito: instalar una sola purga la otra, porque no están en `package.json`.

Las sondas `backend/tests/probar_*.py` sí salen a internet y sirven para verificar las fuentes a mano. `tests/tesela_de_prueba.py` permite probar la cadena completa del relieve sin credencial, con un mosaico sintético que hay que borrar después (ver la documentación de fuentes).

## Pendientes inmediatos de la capa 01

- Probar la reconstrucción con lotes reales y ajustar la detección de árboles; medir el costo de la IA por lote.
- Licencia de la imagen satelital para producción (0005).
- Relieve: retomar con una fuente mejor que NASADEM (en pausa).
- Retiros de frente, fondo y laterales dibujados como zona edificable (ya están en el esquema del proyecto).
- Visor HTML autocontenido con el GLB embebido en base64 (MVP_01 §4.5).
- Plano de implantación SVG (entregable 6.1).
