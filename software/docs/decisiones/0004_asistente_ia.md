# 0004 · Asistente de IA con consumo de tokens acotado

Estado: aceptada, por implementar (paso 5 del orden de trabajo). 26/09/2026.

## Objetivo

Un asistente que oriente al usuario durante todo el recorrido y pueda operar el programa por él, con un costo por usuario predecible y bajo. La arquitectura de referencia está en `arq_soft/02_arquitectura_ideal_IA.drawio`.

## Principio

**El asistente es un cliente más de la API de operaciones** (0002), con los mismos permisos que la interfaz y ninguno extra. No escribe geometría ni edita el proyecto: propone operaciones, el backend las simula y las verifica contra las reglas, y el usuario decide si se aplican. El dominio no sabe que existe una IA y se puede probar sin ella.

De ahí salen casi todos los ahorros: si la IA no tiene que razonar sobre geometría ni sobre el proyecto entero, no hace falta mandarle el proyecto entero.

## Cómo se minimizan los tokens

En orden de impacto:

1. **Lo determinístico no pasa por el modelo.** «Falta definir los wet rooms», «la pendiente excede el dominio», «próximo paso sugerido» y los datos faltantes los calculan el motor de reglas y los estados, sin costo. El modelo interviene solo para traducir lenguaje natural a operaciones, conducir la entrevista inicial y explicar en lenguaje llano.
2. **Explicaciones guardadas.** Cada regla tiene su ficha (id, versión, origen, detalle; ver `reglas/`). `explicar_regla` devuelve ese texto. Muchas veces alcanza con mostrarlo y el modelo no se llama.
3. **Contexto mínimo.** Nunca se envía el proyecto entero. Se envía un resumen de unos cientos de tokens: paso actual, selección en el visor, estado de cada capa e ids de las reglas que fallan. Si el modelo necesita más, lo pide con herramientas de lectura (`consultar_modelo(capa, id)`, `consultar_clima`).
4. **Caché de prompt.** El prompt de sistema, las definiciones de herramientas y las fichas de reglas son estables y van primero. La porción cacheada se cobra alrededor de un 10 % del precio normal. Nada variable (fecha, hora, identificadores) puede ir antes del último punto de caché, porque invalida todo lo que sigue. La caché dura minutos y exige un prefijo mínimo que depende del modelo; se verifica en cada respuesta con `usage.cache_read_input_tokens`.
5. **Salida estructurada.** El modelo devuelve operaciones como llamadas a herramientas con esquema estricto, no prosa. La interfaz dibuja el diff. Las respuestas en texto son cortas y con `max_tokens` bajo.
6. **Botones antes que texto libre.** Las sugerencias en contexto («Resolver ahora», «Confirmar lote») disparan operaciones directas sin pasar por el modelo.
7. **Historial corto.** La memoria real es el proyecto y su registro de operaciones, no la conversación. Se envían las últimas vueltas y un resumen de lo anterior.
8. **Modelo y esfuerzo por ruta.** Interpretar un pedido simple («poné el retiro de frente en 5 m») no necesita el mismo modelo ni el mismo esfuerzo de razonamiento que la entrevista inicial o planificar un cambio que toca varias capas. Se elige por ruta y se mide con casos reales antes de fijarlo; a veces el modelo más capaz con poco esfuerzo sale más barato por tarea completada que uno chico que necesita reintentos.
9. **Límites y medición desde el primer día.** Tope de tokens por usuario y por día; cada llamada registra tokens de entrada, de salida y cacheados, junto con el resultado (propuesta aceptada, ajustada o rechazada).

## Herramientas

Salen del catálogo de operaciones (`GET /api/operaciones`), filtrado por `para_asistente`:

- **Lectura** (sin efecto): `consultar_modelo`, `explicar_regla`, `consultar_clima`, `buscar_catalogo`.
- **Escritura**: las operaciones del dominio, siempre en modo **propuesta**. El backend las aplica sobre una copia (`aplicar` es pura), devuelve el diff y las reglas que pasan, fallan o quedan pendientes, y la interfaz muestra *Aplicar · Ajustar · Rechazar*. Al aplicar, el registro queda con `autor: asistente` y quién lo aprobó.

Se ofrecen pocas herramientas por paso, pero el conjunto de cada paso es fijo para que la caché siga sirviendo.

## Guardarraíles

- Los parámetros se validan con el mismo esquema que usa la interfaz: el modelo no puede mandar geometría libre ni campos que no existan.
- Una regla N0 (geometría o física) que falla bloquea la propuesta. El asistente lo explica citando la regla y busca otra alternativa.
- El asistente distingue medición, estimación regional y cálculo local, como ya hace la interfaz. No inventa datos del sitio.
- El proveedor de LLM queda detrás de un adaptador. El dominio no depende de él.

## Primeros pasos

1. Endpoint `POST /api/asistente` en el backend con el adaptador de LLM y la clave en `.env` (como el token de Earthdata; nunca en el código).
2. Constructor de contexto para la capa 01: paso, ubicación, lote resumido, estado, verificaciones de R01 que no pasan.
3. Tres herramientas: `definir_ubicacion`, `definir_lote`, `definir_retiros` (en modo propuesta), más `explicar_regla`.
4. Panel del asistente en la interfaz con la vista de propuesta.
5. Un conjunto de 20 a 30 pedidos reales de la capa 01 («el lote tiene 12 de frente por 30 de fondo, frente al norte») para medir aciertos y tokens por tarea antes de ampliar.

## Descartado

- **Chat libre sin operaciones.** Barato de hacer y caro de sostener: responde con seguridad sobre geometría que nadie verificó y no puede cambiar el proyecto.
- **Enviar el proyecto entero en cada mensaje.** El costo crece con el proyecto y no mejora las respuestas. El modelo lee con herramientas lo que necesita.
