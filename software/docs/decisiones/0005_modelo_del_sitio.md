# 0005 · Modelo del sitio desde la imagen satelital, con terreno plano

Estado: aceptada, implementada. 27/09/2026. Deja en pausa el relieve de NASADEM (capa 01 de `fuentes_de_datos_terreno.md`) y reemplaza la regla «la NASA es la única fuente externa de datos del modelo».

## Situación

El relieve de NASADEM traía más problemas que valor en esta etapa. Pide un token de Earthdata que vence cada 60 días y descargas de ~26 MB por grado. Su resolución es de ~30 m, así que un lote urbano cae entre dos puntos de medición y la pendiente que da es la de la ladera, no la del lote. Además, la escena plana y gris no le decía al usuario nada de su terreno: ni árboles, ni calles, ni vecinos.

## Decisión

1. **Todo terreno se modela plano** (Z = 0). La pendiente queda como `pendiente_datos` en R01.05 y viaja como aviso hasta que haya relevamiento. El código de NASADEM y de las curvas de nivel queda en el repositorio, sin uso, para cuando se retome.
2. **El paso 3 reconstruye el sitio a partir de la imagen satelital**, sin pedirle nada al usuario:

| Capa | De dónde sale | Definición |
| --- | --- | --- |
| Suelo del entorno | Ortofoto Esri World Imagery apoyada sobre el plano | 0,6–1 m/píxel (±margen, máx. 1000 m) |
| Suelo del lote y su borde | Misma fuente, recorte aparte | 0,3 m/píxel (zoom 19; si falta, 18 o 17 ampliado) |
| Calles y caminos | OpenStreetMap (Overpass) | geometría mapeada; ancho típico por tipo si falta |
| Construcciones | OpenStreetMap; en el lote también IA | contorno mapeado; altura por plantas o 4,5 m supuestos |
| Árboles del lote | Detección en la imagen, o IA si está configurada | posición y copa medidas; altura supuesta |
| Árboles del entorno | Detección en la imagen de baja definición, más los árboles de OSM | hasta 1500, forma genérica |

La geometría se arma una sola vez en Python (`assambl/sitio/`) y se publica como un `.glb` con las dos imágenes embebidas. El visor y el diseño de la casa cargan el mismo archivo.

3. **Los árboles del lote tienen identidad** (`A01`, `A02`…), posición, diámetro de copa, altura y fuente, en el `.glb` y en la respuesta de la API. Son los que el diseño va a tener que respetar, mover o talar.

## ¿Hace falta IA para interpretar la imagen?

Para el lote, sí conviene. Para el entorno, no.

- **Detección por color, sin IA** (`sitio/vegetacion.py`). Una copa es una mancha más verde y más oscura que el suelo. Se marca con el índice de exceso de verde y el brillo; cada copa es un máximo de la distancia al borde de la mancha. Es gratis, determinística y rápida. En el mundo sintético de prueba encuentra todas las copas del lote, con 0,1–0,3 m de error de posición y radio. Con fotos reales falla donde un humano no fallaría: un cerco vivo sale como fila de árboles, un pasto muy oscuro puede parecer copa, y una construcción que no está en OSM no aparece.
- **Interpretación con un modelo de visión** (`sitio/interpretacion_ia.py`, Claude). Es lo que hiciste a mano con Astra: mirar la foto, distinguir la copa de su sombra, ver el galpón que nadie mapeó. Se usa solo sobre el recorte del lote, donde importa la definición. Si no hay clave o la llamada falla, se usa la detección por color.

### Cómo se mantiene bajo el consumo (0004)

- Una sola imagen por lote, el recorte de alta definición, con el contorno dibujado encima. Un lote de 50 × 80 m con su borde son ~350 × 450 px, unos pocos cientos de tokens de entrada.
- Salida estructurada con esquema (`messages.parse` + pydantic): el modelo devuelve píxeles y alturas, no prosa.
- El resultado se guarda por hash de la imagen, del prompt y del modelo en `backend/cache/ia/`. El mismo lote no se paga dos veces, ni siquiera tras reiniciar el backend.
- Orden de magnitud con el modelo por defecto: centavos de dólar por lote, una vez. Hay que medirlo con lotes reales antes de fijar el modelo (`ASSAMBL_MODELO_IA`).

### Cómo se activa

En `backend/.env` (nunca en el código):

```
ANTHROPIC_API_KEY=sk-ant-...
# opcionales
ASSAMBL_MODELO_IA=claude-opus-5
ASSAMBL_IA=0            # desactiva la IA aunque haya clave
```

## Límites que se muestran al usuario

- El terreno es plano por supuesto, no por medición.
- La fecha de la imagen es desconocida: un árbol talado puede seguir apareciendo.
- Las alturas de árboles y construcciones son supuestas salvo que la fuente las traiga.
- Donde Esri no tiene imagen de alta definición se usa una de menor zoom, ampliada, y se avisa.

## Riesgos y alternativas

- **Licencia de la imagen.** Los términos de Esri World Imagery restringen su uso fuera de sus productos. Sirve para el prototipo, pero antes de un lanzamiento hay que resolverlo:
  - cuenta de Esri;
  - Mapbox Satellite o Google Map Tiles, con licencia comercial;
  - ortofotos nacionales (IGN / provincias), donde existan.
  El módulo `fuentes/imagen_satelital.py` está pensado para cambiar de proveedor sin tocar el resto.
- **Google Photorealistic 3D Tiles** daría volumetría real (árboles y casas con altura medida) en ciudades. Es una alternativa a evaluar cuando se retome el relieve.
- **Cobertura de OSM en zonas rurales**: suele ser pobre. Ahí la IA sobre el lote es lo que encuentra construcciones.

## Desarrollo sin red

`ASSAMBL_IMAGEN_SINTETICA=1` reemplaza la imagen y OpenStreetMap por un mundo sintético (campo, camino, calle, casas y árboles con sombra) que la interfaz marca como «imagen sintética de prueba». Las pruebas lo usan para verificar georreferencia, detección de árboles, calles y construcciones.
