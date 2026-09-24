# Fuentes de datos de la capa 01 · Terreno

Estado al 23/09/2026.

**Regla de la capa: la NASA es la única fuente externa de datos del modelo.** El relieve viene de NASADEM y el clima de NASA POWER. Todo lo demás —proyección local, malla, apoyo del lote, posición del sol, sombras— se calcula en este repositorio, sin consultar a ningún otro proveedor.

Dos servicios quedan fuera de esa regla porque no aportan ningún dato al modelo:

- **Nominatim (OpenStreetMap)** traduce una dirección a coordenadas. Es un buscador; lo que entra al proyecto son las coordenadas, que el usuario puede escribir a mano.
- **Las teselas del mapa base** (calles y satélite) son el fondo sobre el que se dibuja el lote. La interfaz lo dice explícitamente y esas imágenes nunca se convierten en geometría ni en textura del modelo 3D.

Si alguno de los dos deja de funcionar, la capa 01 sigue completa: se escriben las coordenadas y se dibuja el lote por lados.

## Qué produce cada fuente

| Dato | Fuente | Resolución informada | Naturaleza |
| --- | --- | --- | --- |
| Alturas del terreno | NASADEM HGT v001 | 1 arcosegundo (≈ 30 m) | medición satelital |
| Temperatura, viento, radiación | NASA POWER | 0,5° × 0,625° (≈ 50–60 km) MERRA-2; 1° CERES/SYN1deg para radiación | reanálisis regional |
| Azimut y elevación del sol | cálculo propio (`assambl/clima/sol.py`) | exacta para el punto | cálculo local |
| Contorno del lote | el usuario | exacta | cálculo local |
| Sombras | modelo 3D de la escena | la del relieve (≈ 30 m) | cálculo local |

Esa clasificación no es decorativa: viaja en el campo `naturaleza` de cada `Fuente` y la interfaz la muestra como etiqueta al lado de cada capa. El objetivo es que nunca se confunda una medición con una estimación regional.

## Relieve · NASADEM

- Producto: `NASADEM_HGT` v001, DOI `10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001`. Es el reprocesamiento de SRTM (2000) hecho por JPL con mejor control de huecos y georreferenciación; se distribuye por el LP DAAC.
- Cobertura: entre 60° N y 56° S. Fuera de esa banda no hay dato y la escena sale provisional.
- Descarga: se arma la URL directamente, porque el nombre del objeto es previsible:

  ```
  https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/NASADEM_HGT.001/NASADEM_HGT_<tesela>/NASADEM_HGT_<tesela>.zip
  ```

  El LP DAAC exige Earthdata Login: se manda `Authorization: Bearer <EARTHDATA_TOKEN>`. Ojo que redirige a la pantalla de login **antes** de verificar si el objeto existe, así que sin token un 302 no dice nada sobre la cobertura.
- Búsqueda por catálogo (CMR), solo como respaldo si la ruta directa da 404. Antes era el camino principal y se cambió el 23/09/2026: la búsqueda de gránulos estaba devolviendo timeouts y HTTP 500 mientras el resto de Earthdata respondía en un segundo. Es un punto único de falla evitable, y agregaba un viaje de ida y vuelta a cada descarga.
- Si la ruta directa da 404 **y** el catálogo tampoco responde, el código levanta `CatalogoCaido` en vez de informar «sin cobertura»: no se puede distinguir un mosaico inexistente de una reorganización del depósito sin preguntarle a alguien.
- La colección vive hoy en el proveedor **LPCLOUD** (`C2763264762-LPCLOUD`), no en el viejo `LPDAAC_ECS`. Consultar por `provider=LPDAAC_ECS` devuelve vacío, y el espejo histórico `e4ftl01.cr.usgs.gov` responde 404 para este producto.
- Formato: `.hgt` dentro de un `.zip`. Cada mosaico cubre 1° × 1° con 3601 × 3601 posts `int16` big-endian, sin encabezado. La fila 0 del archivo es el **borde norte**, así que al leerlo se invierte verticalmente. El valor `-32768` marca ausencia de dato.
- Nombre del mosaico: esquina **suroeste**, p. ej. `s32w065` para el cuadrado entre 32° S y 31° S, 65° O y 64° O.
- Recorte: se indexa en arcosegundos enteros y se toma el post inmediatamente exterior a cada borde, de modo que el área pedida quede contenida. El límite es 9 mosaicos por escena; con el margen máximo (2000 m) nunca se pasa de 4.
- Huecos: se rellenan con la mediana del recorte y la cantidad se informa en el campo `huecos` de la malla. Si no queda ningún post con dato, la escena pasa a provisional.
- Caché: `backend/cache/nasadem/<tesela>.hgt` (unos 26 MB por mosaico, sin comprimir). Se descarga una vez por grado, no una vez por escena.
- Reintentos: tres, solo ante fallos de conexión. Los cortes de DNS momentáneos aparecieron dos veces durante el desarrollo y no vale la pena perder una descarga de minutos por uno.

### Cotejo de la georreferenciación

Un error de indexado —filas o columnas invertidas— produce una malla perfectamente verosímil en el visor, pero con la ladera del lado equivocado. La única manera de detectarlo es comparar contra cotas conocidas:

```powershell
.venv\Scripts\python tests\probar_nasa.py --cotas
```

Resultado del 23/09/2026 sobre `s32w065`: plaza San Martín 410 m (esperado ~400), aeropuerto de Córdoba 475 m (~474), Villa Carlos Paz 662 m (~640), Alta Gracia 553 m (~580). Además el punto más alto del mosaico cae en −31,9878 / −64,9364 a 2773 m, que es el cerro Champaquí (−31,978 / −64,933, 2790 m).

Las referencias son lugares llanos a propósito. Sobre una ladera empinada, cien metros de imprecisión en la coordenada mueven la cota lo suficiente como para que la comparación no signifique nada: la primera versión de esta prueba usaba un pico y daba 442 m de diferencia sin que hubiera ningún error.

### Lo que NASADEM no puede decir

- 30 m entre posts significa que **un lote urbano típico cae entre dos posts**. La pendiente que informa la aplicación es la de la ladera, no la del interior del lote. La regla `R01.06` marca el proyecto como «requiere revisión» cuando el lote mide menos de dos pasos del DEM.
- Es un modelo de superficie derivado de radar: en zonas arboladas o densas la altura incluye copas y techos.
- La exactitud vertical publicada de SRTM/NASADEM es del orden de varios metros. **No sirve para definir cotas de fundación ni de platea; eso requiere una mensura.**
- Por eso el código **no interpola ni agrega ruido** para «mejorar» el aspecto. La malla usa los posts nativos y sombreado plano: las facetas que se ven en el visor son la resolución real del dato.

## Clima · NASA POWER

- Endpoints (sin credencial, sin clave):
  - `https://power.larc.nasa.gov/api/temporal/climatology/point` — medias mensuales multianuales.
  - `https://power.larc.nasa.gov/api/temporal/hourly/point` — series horarias, un año por pedido.
- `community=RE` (Renewable Energy).
- Parámetros de la climatología: `T2M`, `T2M_MAX`, `T2M_MIN`, `WS10M`, `WD10M`, `ALLSKY_SFC_SW_DWN`, `RH2M`, `PRECTOTCORR`.
- Parámetros horarios: `T2M`, `WS10M`, `WD10M`, `ALLSKY_SFC_SW_DWN`.
- Período horario: los últimos 5 años **cerrados**. POWER publica con meses de retraso, así que el año en curso y el anterior incompleto se excluyen. Son ~43 800 horas.
- `time-standard=LST` es obligatorio en el pedido horario. Sin ese parámetro POWER responde en UTC y el perfil horario de temperatura queda corrido respecto del sol (en Argentina, 3 horas).
- Valor faltante: `-999`. Se descarta antes de promediar.
- Caché: `backend/cache/power/`, un archivo para la climatología y uno por año horario. La primera descarga tarda varios minutos; después el endpoint responde desde disco en menos de un segundo.

### Unidades, y por qué están separadas

La radiación aparece con **dos unidades distintas** según el producto: `kW-hr/m^2/day` en la climatología y `Wh/m^2` en las series horarias. El modelo guarda `parametros_climatologia` y `parametros_horarios` en campos separados justamente para que una no sobreescriba a la otra.

`T2M_MAX` y `T2M_MIN` son los **extremos del período**, no el promedio de las máximas diarias. En el modelo se llaman `t_max_c` y `t_min_c` y la interfaz lo aclara al pie de la tabla.

### Lo que POWER no puede decir

- Una celda de MERRA-2 mide unos 50 × 60 km. El dato es el promedio de un área que incluye sierra y llano, ciudad y campo. **Es una estimación regional, no una medición del sitio.**
- El viento está dado a **10 m de altura y sin obstáculos**. Junto a una ventana, a 1,5 m del piso y detrás de una tapia, la velocidad real es una fracción de ésa. Sirve para elegir orientaciones y decidir dónde conviene ventilar cruzado; no para dimensionar una abertura.
- La radiación es histórica y promediada: dice cuánta energía llega en promedio a un plano horizontal en la zona. No es lo mismo que la posición del sol (cálculo exacto) ni que la sombra (que sale del modelo 3D).

### Resúmenes que se calculan acá

- **Temperaturas por mes:** media, extremos del período y amplitud, más grados-día de calefacción y refrigeración con base 18 °C.
- **Perfil horario:** media de cada hora solar local sobre las 5 años, y la amplitud diaria que surge de ahí.
- **Rosa de vientos:** 16 sectores de 22,5°, con bins de velocidad en 0,5 / 2 / 4 / 6 / 8 / 10 m/s y porcentaje de calmas. La dirección predominante es el **sector más frecuente**, no un promedio de ángulos: promediar rumbos alrededor del norte da un resultado sin sentido físico.
- **Radiación por mes**, en la unidad que informa la fuente.

## Sol · cálculo local

- Algoritmo: NOAA Solar Calculator, que implementa las series de Meeus (*Astronomical Algorithms*, 2ª ed.). Está en `assambl/clima/sol.py`, sin dependencias externas.
- Entrada: latitud, longitud, fecha, hora y huso. Si no se da huso, se estima por longitud.
- Salida: azimut (desde el norte, hacia el este), elevación con refracción atmosférica, y un vector unitario `[x, y, z]` en el sistema del proyecto.
- Orto y ocaso se toman con el centro del sol a **−0,833°** sobre el horizonte, que es la convención habitual (semidiámetro solar más refracción).
- Verificación: `tests/cotejar_sol.py` compara contra la biblioteca `astral` para varias fechas y latitudes. Coincide dentro de 1 minuto en amanecer y atardecer y de 0,02° en azimut. Los valores verificados quedaron fijos en `tests/test_sol.py`.
- **El algoritmo existe una sola vez, en el backend.** El visor recibe la trayectoria del día muestreada cada 5 minutos e interpola entre muestras al mover el control horario. No hay una segunda implementación en TypeScript que pueda desincronizarse.

## Sistema de coordenadas y proyección

- Origen: el punto que elige el usuario (lat₀, lon₀). Unidades: **metros**. `+X` este, `+Y` norte, `+Z` arriba.
- Proyección equirrectangular local: `x = Δlon · cos lat₀ · R · π/180`, `y = Δlat · R · π/180`, con `R = 6 371 008,8 m`. Para escenas de pocos kilómetros el error en distancias es inferior al 0,1 %.
- `z = 0` es la cota de NASADEM en el origen. El desplazamiento absoluto se guarda como `cota_origen_msnm`.
- Para trámites catastrales habría que convertir a POSGAR 2007 / Gauss-Krüger; no está implementado.

## Una sola geometría, tres destinos

El backend arma la malla una vez y la publica como **GLB por capa** (MVP_01 §4.5). De ese mismo generador salen:

1. El `.glb` que carga el visor web con `GLTFLoader`.
2. El `.glb` que se puede importar en Blender directamente.
3. Un script `.py` de Blender que reconstruye la escena con `bmesh`, para quien prefiera código editable.

Así no hay dos implementaciones de la geometría. El `.glb` se valida contra el validador oficial de Khronos con `node scripts/validar_glb.cjs` (0 errores, 0 advertencias).

Detalle del contenedor: glTF define `+Y` arriba, así que el nodo raíz lleva una rotación de −90° sobre X que convierte el sistema del proyecto. Blender la cancela al importar, de modo que en ambos lados el norte queda en `+Y` y las alturas en `+Z`.

El lote se **apoya** sobre la malla: cada vértice del contorno toma la altura del triángulo del relieve que le corresponde, con la misma triangulación que se dibuja (diagonal SO–NE). Es un apoyo geométrico, no relieve inventado. Se aplica una separación de 0,25 m en la superficie y 0,45 m en la línea, porque a más de 1 km de escena el búfer de profundidad no distingue diferencias de pocos centímetros y el lote parpadearía contra el terreno.

## Credencial de Earthdata

1. Crear una cuenta gratuita en <https://urs.earthdata.nasa.gov>.
2. Entrar al perfil, pestaña **Generate Token**, y copiar el token (dura 60 días).
3. Guardarlo en un archivo `.env`, como `EARTHDATA_TOKEN=eyJ0eXAi…`.

`assambl/config.py` busca el `.env` en `backend/`, en `software/` y en la raíz del repositorio, en ese orden, y no sobreescribe variables de entorno ya definidas. Los `.env` están en `.gitignore`: **el token no se escribe en el código ni se commitea**.

Sin token la aplicación no se rompe: `GET /api/terreno/credencial` informa que falta, el panel de ubicación lo avisa y la escena se genera **plana y marcada como provisional**, con un cartel en el visor y la fuente en estado `provisional`. La búsqueda en CMR y todo NASA POWER funcionan igual, porque no piden credencial.

Si el token venció, el LP DAAC responde 401 o 403 y el mensaje de error lo dice explícitamente.

## Cómo probar el relieve sin credencial

`backend/tests/tesela_de_prueba.py` escribe un mosaico `.hgt` **sintético** en la caché y lo borra cuando se lo pide:

```powershell
.venv\Scripts\python tests\tesela_de_prueba.py poner
.venv\Scripts\python tests\tesela_de_prueba.py quitar
```

Sirve para verificar la lectura del formato, el armado de la malla, el `.glb` y las sombras del visor. **El relieve que genera es inventado**: no es un sustituto de NASADEM y hay que borrarlo antes de mirar datos reales.

## Fuentes que se descartaron

Se probaron y se quitaron al fijar la regla de una sola fuente externa:

- **AWS Terrain Tiles (Terrarium)**: DEM en PNG, sin clave. Ventaja: no pide credencial. Desventaja: es SRTM remuestreado a teselas web, así que obliga a interpolar para volver a metros y el dato que sale ya no es el original.
- **Overpass (OpenStreetMap)** para calles y edificios vecinos: quitado por pedido explícito. Además el servidor público daba 504 con radios mayores a 1 km y la cobertura de alturas de edificios en Argentina es muy baja (la mayoría salían con altura supuesta).
- **Esri World Imagery** como textura del terreno 3D: quitado del modelo. Sobrevive únicamente como fondo del mapa 2D para dibujar.
- **Topoexport**: no tiene API pública documentada (en 2026 sigue siendo una calculadora de precios con formulario de contacto) y fuera de Alemania y Suiza sus edificios vienen de OpenStreetMap.

Candidatos para más adelante, si hiciera falta mejorar el relieve: **IGN MDE-Ar** (30 m nacional y 5 m en zonas relevadas, mejor exactitud vertical que SRTM en Argentina) y **Copernicus DEM GLO-30** (TanDEM-X, más reciente). Ambos son GeoTIFF y requerirían `rasterio`, y ninguno es de la NASA: entrarían solo con una decisión explícita de cambiar la regla.

## Cómo agregar o cambiar una fuente

Cada proveedor es un módulo en `backend/assambl/fuentes/` con funciones puras que devuelven las estructuras de `assambl/modelo/sitio.py`. `assambl/capas/terreno.py` los orquesta y arma la lista `fuentes`, donde cada entrada declara nombre, URL, licencia, fecha, estado, **resolución** y **naturaleza**. Esos dos últimos campos son obligatorios: la interfaz los muestra y sin ellos no se puede distinguir una medición de una estimación.
