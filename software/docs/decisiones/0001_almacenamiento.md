# 0001 · Almacenamiento: el proyecto es un documento

Estado: aceptada, por implementar (paso 2 del orden de trabajo). 26/09/2026.

## Situación

No hay base de datos. El proyecto (`casa.assambl.json`, esquema en `backend/assambl/modelo/proyecto.py`) vive en el `localStorage` del navegador y se exporta e importa a mano. El backend no guarda proyectos: solo una caché en disco (`backend/cache/`) de mosaicos de NASADEM, series de NASA POWER y escenas, identificadas por los parámetros que las produjeron. El catálogo (`catalogo/ar.json`) está vacío.

Alcanza para una persona en una máquina. No alcanza para cuentas de usuario, varios dispositivos, historial que sobreviva al navegador ni proyectos compartidos.

## Decisión

Se separan cuatro tipos de datos, cada uno con su almacenamiento:

| Dato | Qué es | Dónde se guarda |
| --- | --- | --- |
| **Proyecto** | La intención del usuario: ubicación, lote, muros, aberturas, elecciones | Documento JSON validado por el esquema, guardado entero por versión |
| **Operaciones** | Cada cambio aplicado: qué, quién, cuándo, qué campos cambió | Registro de solo agregado, una fila por operación |
| **Catálogo y reglas** | Escuadrías, placas, rollos, artefactos; reglas con ID y versión | JSON y módulos Python versionados en git |
| **Modelo resuelto y salidas** | Piezas, GLB, planos, clima descargado | Caché en disco o almacenamiento de objetos, identificada por hash |

### Proyecto y operaciones en una base documental sobre SQL

El proyecto no se descompone en tablas relacionales (una por muro, una por pieza). Es un documento con esquema versionado (`esquema: assambl/proyecto@0.2`) y se guarda entero, como JSONB. Así el esquema puede crecer capa por capa sin migraciones de tablas, y el mismo archivo sirve para exportar, importar y probar.

Tablas mínimas:

```
usuarios            id, email, creado
proyectos           id, usuario_id, nombre, esquema, creado, modificado, version_actual
versiones_proyecto  proyecto_id, version, documento (JSONB), creada, operacion_id
operaciones         id, proyecto_id, version_resultante, tipo, parametros (JSONB), autor,
                    aprobado_por, fecha, cambios, estado_antes, estado_despues
propuestas_ia       id, proyecto_id, operaciones (JSONB), estado, vence, creada   -- ver 0004
```

- Cada operación aplicada agrega una fila en `operaciones`. El registro ya lo produce `aplicar()` (0002): `RegistroOperacion` tiene exactamente estos campos.
- Se guarda una versión completa del documento cada N operaciones (y siempre al cerrar una sesión de trabajo). Una versión cualquiera se reconstruye con la última versión anterior más las operaciones posteriores. Con proyectos de cientos de KB, guardar versiones completas es barato; no hace falta empezar con diferencias.
- Deshacer, comparar versiones y saber quién cambió qué (usuario o asistente, y quién aprobó) salen de esas dos tablas.

### Catálogo y reglas en git, no en la base

El catálogo lo edita el equipo de Assambl y lo revisa un especialista. MVP_01 §5 exige reproducibilidad: el mismo proyecto con el mismo catálogo y las mismas versiones de reglas produce el mismo modelo, byte a byte. Eso requiere versiones fijas y revisables, que git da sin esfuerzo. El proyecto declara qué versión usa (`catalogo@0.3`).

El catálogo pasa a la base recién cuando aparezca alguna de estas necesidades: catálogos propios de un cliente, precios de proveedores que cambian seguido o búsqueda sobre miles de artículos. Aun entonces, lo que se publica sigue siendo una versión inmutable a la que el proyecto apunta.

### Modelo resuelto y salidas como caché por hash

El modelo resuelto (piezas, estados), los GLB por capa y los planos se derivan del proyecto. Su clave es `hash(proyecto + versión de catálogo + versión de reglas)`, por capa. Se guardan en disco en desarrollo y en almacenamiento de objetos (tipo S3) en producción. La base solo guarda la referencia. Si se pierden, se regeneran.

### Motor: SQLite primero, Postgres al desplegar

- El backend accede a los datos a través de una interfaz `RepositorioProyectos` (guardar versión, agregar operación, leer, listar). La primera implementación es SQLite en un archivo local: no agrega servicios que levantar y alcanza para desarrollo y demos.
- Al desplegar con usuarios reales se cambia a Postgres (Supabase o Neon), que tiene JSONB e índices sobre documentos. Como el proyecto es un solo documento, el cambio queda dentro del repositorio.
- La ruta `POST /api/operaciones/aplicar` no cambia de contrato: hoy recibe el proyecto y devuelve el nuevo; mañana recibirá el identificador y la versión esperada, y guardará el resultado.

## Descartado

- **Modelo relacional completo** (tabla de muros, de aberturas, de piezas). Obliga a migrar tablas en cada capa nueva y duplica el esquema que ya define pydantic. Las consultas que lo justificarían (por ejemplo, todas las piezas de un proveedor en todos los proyectos) son de analítica y se resuelven después con vistas sobre JSONB.
- **Guardar las piezas resueltas como fuente de verdad.** Una casa tiene miles de piezas que salen de decenas de decisiones. Guardarlas agranda el proyecto y abre la puerta a que piezas y decisiones se contradigan (MVP_01 §4.2).
- **Seguir solo con `localStorage`.** No sobrevive a limpiar el navegador, no se comparte y tiene un límite de pocos MB.
