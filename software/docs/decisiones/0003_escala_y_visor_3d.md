# 0003 · Escala del proyecto y visor 3D

Estado: aceptada. Los puntos 1 y 3 ya están en la base del diseño; 2, 4 y 5 están por implementar. 26/09/2026.

## Pregunta

¿Cómo evitar que el software se vuelva pesado a medida que crece el proyecto? ¿Hace falta un motor 3D propio para que el usuario no tenga que abrir otros programas?

## Referencia: cómo lo resuelve Revit

- Un `.rvt` es un archivo binario propietario. Por fuera es un contenedor OLE (el formato de almacenamiento estructurado de los viejos `.doc`) con flujos internos comprimidos. Por dentro funciona como una base de datos de objetos: cada elemento tiene un identificador, parámetros y referencias a otros elementos. No es código ni texto.
- **Familias, tipos e instancias.** Una ventana se define una vez en su familia (`.rfa`). Cada ventana colocada guarda su tipo, su posición y los parámetros que difieren. Buena parte de la geometría se regenera desde esas definiciones en lugar de guardarse pieza por pieza.
- **Un hotel no es un archivo.** Los proyectos grandes se parten en modelos vinculados (arquitectura, estructura e instalaciones por separado, a menudo uno por edificio o torre). Dentro de cada modelo hay *worksets* que se pueden dejar sin abrir, vistas que solo procesan lo visible y niveles de detalle (grueso, medio, fino). En trabajo colaborativo hay un modelo central y copias locales que se sincronizan.
- Aun así, los archivos de cientos de MB y la lentitud son una queja habitual de Revit.

Otras referencias: IFC es el estándar abierto (texto STEP, muy verboso). Herramientas recientes como Speckle guardan un grafo de objetos identificados por hash de su contenido: lo repetido se guarda una vez y se carga por partes.

## Decisión

1. **Se guarda la intención, no las piezas** (MVP_01 §4.2). El proyecto contiene decisiones: lote, muros, aberturas, elecciones de catálogo. Las piezas salen de las reglas de forma determinística. Angus Ranch V11 tiene 5.423 piezas que salen de unas decenas de decisiones: el documento pesa decenas o cientos de KB y el modelo resuelto es caché. Es la decisión de mayor impacto.
2. **Tipos e instancias.** Cada pieza del modelo resuelto guarda `id + ítem de catálogo + transformación + parámetros propios`. La geometría de un ítem (un montante de 45 × 95 × 2.440) se genera una vez. En el visor, `THREE.InstancedMesh` dibuja miles de instancias con una sola geometría, y en el GLB se usa la extensión `EXT_mesh_gpu_instancing`. El GLB de la landing hoy fusiona piezas por capa (3,5 MB, 234.648 triángulos, 69 llamadas de dibujo): rinde bien, pero pierde la selección pieza por pieza. Se recupera con un atributo de identificador por vértice o con instancias.
3. **Partición por capa y, después, por zona**, cada parte con su propio hash. Ya se genera un GLB por capa (MVP_01 §4.5). La propagación selectiva (§4.3) recalcula solo las capas alcanzables desde el cambio; el resto sale de caché. Para proyectos grandes se agrega una partición espacial (nivel, módulo, edificio) y el visor carga lo que se está mirando.
4. **Niveles de detalle.** La vista general muestra volúmenes (muro como caja, techo como faldón). Al entrar en una capa o en un muro se carga el detalle pieza por pieza.
5. **Datos separados de la geometría.** Los atributos de cada pieza (id, ítem, estado, regla que la generó) van en JSON o en la base, donde se pueden consultar. Los triángulos van en GLB binario.

Orden de magnitud: una casa tiene entre 5 y 10 mil piezas. Con los puntos 1 y 2, un navegador la maneja sin problema. Un hotel (del orden del millón de piezas) necesita además los puntos 3 y 4. No se construye ahora, pero nada de lo decidido le cierra la puerta.

## Visor: three.js, no un motor propio

El objetivo es que el usuario no abra otros programas y pueda recorrer el proyecto por capas. three.js ya está en `Visor3D.tsx` y en la landing, y alcanza para eso. El motor que hace falta construir es el del **dominio** (operaciones, grafo de capas, reglas, estados); el visor muestra lo que ese motor produce.

Lo que se suma al visor de la aplicación, en este orden:

1. Encender y apagar capas.
2. Explosión por capas, reutilizando `landing/src/components/explode/`.
3. Seleccionar una pieza y ver su ficha (id, ítem, estado, regla).
4. Capas «fantasma» para mostrar una propuesta antes de aplicarla (0004).

Blender queda como generador opcional para renders y verificación visual (MVP_01 §4.5). La edición directa en 3D (arrastrar un muro) viene después de la edición en planta 2D, que es más precisa y más simple.

## Descartado

- **Motor 3D propio** (WebGPU a mano, o un motor de juegos). Meses de trabajo en algo que no diferencia al producto.
- **Guardar la escena como fuente de verdad** (el enfoque de un `.blend` o de un `.rvt` sin reglas). Cualquier cambio exigiría editar la geometría a mano y se perdería la propagación entre capas.
