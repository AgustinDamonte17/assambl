# 0006 · La casa es independiente del terreno

Estado: aceptada, por implementar. Es la base del diseño de la casa: se aplica antes de escribir sus primeras operaciones (huella, muros). 27/09/2026.

## Problema

Hoy todo lo del proyecto se mide en metros desde un origen que es la ubicación elegida en el mapa, con +Y hacia el norte. Si la casa se diseñara en esas coordenadas, cada pieza quedaría atada a ese lote: cambiar de terreno, mover la casa dentro del lote o reutilizarla en otro proyecto obligaría a mover todas las piezas. **Esto no debe pasar.**

## Decisión

1. **La casa tiene su propio sistema de coordenadas.** Metros, Z arriba, origen en un punto de la casa (por ejemplo, la esquina de referencia de la platea) y ejes propios de la casa, sin norte. Muros, aberturas, ambientes y piezas se guardan en ese sistema. En el proyecto, `casa` es una sección aparte de `terreno`.
2. **La implantación es el único vínculo entre casa y sitio.** Es un dato pequeño, `implantacion = {x, y, rumbo_deg}`: dónde cae el origen de la casa en el sistema del sitio y cuánto está girada respecto del norte. Tiene sus propias operaciones (`implantar_casa`, `mover_implantacion`). Se agrega `nivel_m = 0`, reservado para cuando vuelva el relieve.
3. **Terreno plano.** Mientras el terreno se modele plano (0005), el suelo de la casa está en Z = 0 del sitio y el relieve no interviene en la implantación.
4. **Cambiar de terreno no toca la casa.** Cambiar de lote, de ubicación o de modelo del sitio solo afecta la implantación y las reglas que miran el sitio. Una casa se puede copiar a otro proyecto (y en el futuro, guardarse como tipología) con solo su sección `casa`.
5. **Las reglas que dependen del sitio leen la casa a través de la implantación**: retiros y si entra en el lote, árboles debajo de la huella, orientación al sol y al viento, clima. Sin implantación no fallan: quedan en `pendiente_datos`, como cualquier dato faltante (MVP_01 §4.4). Al implantar o mover la casa se recalculan (§4.3).
6. **Orientación relativa a la casa.** Lo que la casa sabe de sí misma se nombra respecto de sus propios ejes: frente, contrafrente, laterales. El norte y los puntos cardinales se derivan del `rumbo_deg` de la implantación. Una fachada deja de estar al norte si se gira la casa, pero sigue siendo la misma fachada.
7. **Geometría y visor.** La casa se publica en su propio `.glb`, separado del sitio. El visor los compone aplicando la implantación como transformación del nodo de la casa: mover o girar la casa no regenera su geometría.
8. **El orden de las etapas deja de ser obligatorio.** Se puede empezar por el diseño de la casa (el visor muestra un suelo neutro sin sitio) o por el terreno. Queda pendiente una decisión de producto: si el terreno es obligatorio antes de emitir planos o solo antes de ciertos entregables.

## Criterios de aceptación

- Cambiar la implantación (posición o rumbo) no modifica ninguna coordenada guardada en `casa`.
- Cambiar el lote, la ubicación o el modelo del sitio no modifica `casa`; solo cambian estados de reglas que miran el sitio.
- Una casa diseñada sin terreno se implanta después y las reglas del sitio pasan de `pendiente_datos` a su resultado.
- La misma sección `casa` implantada en dos lotes distintos da la misma geometría de casa.
