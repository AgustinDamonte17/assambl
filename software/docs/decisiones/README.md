# Decisiones de arquitectura

Estado al 26/09/2026.

Cada documento fija una decisión: el problema, lo que se eligió, lo que se descartó y por qué. Una decisión se reemplaza con un documento nuevo que la cita; no se reescribe la historia.

| # | Decisión | Estado |
| --- | --- | --- |
| [0001](0001_almacenamiento.md) | Almacenamiento: el proyecto es un documento; la base guarda versiones y operaciones | Aceptada · por implementar |
| [0002](0002_operaciones_e_historial.md) | Toda modificación pasa por operaciones validadas en el backend | Aceptada · implementada en la capa 01 |
| [0003](0003_escala_y_visor_3d.md) | Escala: guardar la intención, derivar las piezas; visor sobre three.js | Aceptada · parcialmente implementada |
| [0004](0004_asistente_ia.md) | Asistente de IA: cliente de las operaciones, con consumo de tokens acotado | Aceptada · por implementar |

## Orden de trabajo

El orden sale de las dependencias, no de la preferencia: el asistente necesita operaciones para tener qué llamar, la base necesita operaciones para tener qué versionar y el visor por capas necesita capas resueltas para tener qué mostrar.

1. **API de operaciones e historial sobre la capa 01** (0002). Hecho: `assambl/modelo/operaciones.py`, `POST /api/operaciones/aplicar`, deshacer en la interfaz.
2. **Persistencia mínima** (0001): repositorio de proyectos con SQLite que guarda versiones y el registro de operaciones. Postgres y cuentas de usuario cuando haya una beta con usuarios reales.
3. **Modelo declarativo de la casa, capas 02 y 03** (MVP_01 §4.2): muros, aberturas y entramado como operaciones; Angus Ranch como caso de regresión; catálogo real en `catalogo/ar.json`. Es donde está el valor del producto.
4. **Visor por capas en la aplicación** (0003): GLB por capa con instancias, encender y apagar capas, explosión, selección de piezas.
5. **Asistente sobre la capa 01** (0004), con tres o cuatro herramientas y el costo medido desde el primer día. Se amplía a medida que aparecen operaciones.

Ni el asistente ni la base van primero. Sin operaciones, el asistente sería un chat que describe geometría que nadie verifica, lo contrario de lo que pide MVP_01 §4.4. La base primero adelantaría cuentas y despliegue antes de que el producto tenga algo que guardar.
