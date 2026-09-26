# 0002 · Operaciones e historial

Estado: aceptada, implementada en la capa 01. 26/09/2026.

## Situación anterior

El frontend modificaba el proyecto con un reductor local (`ProyectoContext.tsx`): cada panel despachaba acciones como `lote_vertices` o `margen` y el navegador aplicaba el cambio sin pasar por el backend. El estado del terreno lo calculaba R01 en el backend, pero lo escribía el frontend con una acción aparte (`lote_estado`). Había dos implementaciones de la misma lógica (reductor TS y paquete Python) que podían desincronizarse, y ya lo habían hecho: el esquema Python seguía en `proyecto@0.1` con campos que el frontend ya no usaba.

MVP_01 §4.4 pide lo contrario: la interfaz y el asistente llaman las mismas operaciones y ninguno escribe el proyecto directamente.

## Decisión

Toda modificación del diseño es una **operación**: un objeto con `tipo` y parámetros validados por pydantic, aplicado por el backend.

- Módulo: `backend/assambl/modelo/operaciones.py`. `aplicar(proyecto, operacion, autor, contexto)` es una función pura: no guarda, no sale a la red y no modifica el proyecto que recibe. Devuelve el proyecto nuevo, un `RegistroOperacion` y, si corresponde, el resultado de R01.
- Ruta: `POST /api/operaciones/aplicar` con `{proyecto, operacion, autor}`. Parámetros fuera de rango devuelven 422; una operación válida que no se puede aplicar a ese proyecto (escena inexistente o de otro origen) devuelve 409.
- Catálogo: `GET /api/operaciones` lista cada operación con su descripción y el esquema JSON de sus parámetros. De ese catálogo saldrán las definiciones de herramientas del asistente (0004), sin escribirlas dos veces.
- Espejo TS de los tipos: `frontend/src/modelo/operaciones.ts`.

### Operaciones de la capa 01

| Operación | Qué hace | Efectos derivados |
| --- | --- | --- |
| `renombrar_proyecto` | Cambia el nombre | — |
| `definir_ubicacion` | Fija el origen (0, 0) | Si el origen se mueve y hay lote: terreno `desactualizado`, se borran pendiente y cota |
| `definir_margen` | Metros de relieve alrededor del origen (100–2000) | Recalcula R01 |
| `definir_lote` | Reemplaza la poligonal | Lados, área, perímetro; recalcula R01; saca al terreno de `desactualizado` |
| `definir_retiros` | Frente, fondo y laterales | — |
| `vincular_escena` | Asocia una escena ya generada | Cota del origen y pendiente salen de la escena; recalcula R01. No la ofrece el asistente |

Lo que la operación necesita leer y no está en el proyecto (hoy, la malla de la escena generada) llega por un `Contexto`. Una escena solo se usa si coincide con el origen y el margen del proyecto.

### Qué no es una operación

- **Preferencias de estudio**: fecha, hora y huso del asoleamiento (`fecha_sol`, `hora_sol`, `huso_h`). Se guardan en el proyecto para reabrirlo como se dejó, pero no cambian el diseño, no pasan por el historial y el frontend las cambia localmente.
- **Cargar y crear proyecto.** Reemplazan el documento entero y vacían el historial en memoria.

### Estados

Una operación nunca deja un estado optimista. `definir_lote` corre R01 y fija el estado que dan las reglas. Mover el origen deja el terreno `desactualizado`, y así queda aunque otras operaciones vuelvan a correr las reglas: que R01 pase no confirma que el lote siga en su lugar. Solo redefinir el lote lo confirma. La interfaz ofrece un botón **Confirmar lote** para hacerlo sin redibujar.

### Historial y deshacer (mientras no haya base)

- Cada respuesta trae un `RegistroOperacion`: id, operación, autor (`usuario`, `asistente` o `sistema`), fecha, campos cambiados, estado antes y después, y avisos. Una operación sin efecto devuelve `cambios: []` y no toca `modificado`.
- El frontend guarda los últimos 200 registros en `localStorage` (`assambl.historial`), fuera de `casa.assambl.json` para que el proyecto siga liviano. Con la base de 0001 pasan a la tabla `operaciones`.
- Deshacer (botón y Ctrl+Z) restaura el proyecto anterior a la última operación del usuario. Operaciones seguidas del mismo tipo dentro de 1,5 s se deshacen juntas (tipear, arrastrar el margen). Lo que registra el sistema (`vincular_escena`) no se deshace por separado. La escena es caché: deshacer conserva la vigente y la interfaz la regenera si el lote o el origen restaurados lo piden.
- Las operaciones se aplican de a una, siempre sobre el último proyecto. Si mientras viaja una se carga otro proyecto o se deshace, su respuesta se descarta.

## Consecuencias

- El backend es la única implementación de la lógica de cambio. El reductor del frontend solo carga, crea y ajusta preferencias de vista.
- Cada cambio de diseño cuesta un viaje al backend. En local es imperceptible. Los controles continuos (deslizador del margen) envían la operación cuando el valor se detiene, y los arrastres del mapa, al soltar.
- Sin la API no se puede editar el diseño. Antes tampoco se podía generar la escena ni correr R01.
- El esquema Python pasó a `proyecto@0.2` y coincide con el TS. Una prueba valida contra el esquema Python un proyecto con la forma exacta que crea `proyectoNuevo()`.

## Próximos pasos

- Pasar el historial a la base (0001) y registrar quién aprobó cada operación propuesta por el asistente.
- Agregar las operaciones de las capas 02 y 03 (`crear_muro`, `agregar_abertura`…) con el mismo contrato.
- Propuestas: aplicar una operación sobre una copia, devolver el diff y confirmarla después (el motor de transacciones del diagrama `arq_soft/02_arquitectura_ideal_IA.drawio`). `aplicar` ya es pura, así que simular es llamarla sin guardar el resultado.
