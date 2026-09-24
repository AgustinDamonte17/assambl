# Assambl · MVP_01 — Especificación de la primera versión

**Versión 0.1 · 22 de septiembre de 2026 · Documento de trabajo**

Assambl es un software para modelar residencias en woodframe *from the ground up*: desde el terreno hasta el circuito eléctrico, con un solo modelo del proyecto del que salen todas las vistas, planos, cantidades e instructivos. Este documento fija qué construye la primera versión (MVP_01), cómo se almacena el diseño, qué reglas lo hacen realista y qué entrega al usuario.

Se apoya en el [Plan de negocios v0.1](../Plan_de_negocios_Woodframe_v0.1.md) y en la base experimental de Angus Ranch V06 (828 piezas con ID estable, 13 capas de vista, despiece y plan de cortes regenerables). No presupone que exista validación comercial; las dimensiones comerciales de materiales son un perfil por defecto que debe verificarse con proveedores locales antes de usarse en un pedido real.

**Decisiones adoptadas en esta versión:**

- Las 14 capas de la casa forman el modelo desde el primer día, pero con dos niveles de compromiso: un **núcleo construible** (capas 01–05 y 09) y **capas con hooks** (06–08 y 10–14) que reservan geometría, dependencias y estados sin resolver la disciplina completa.
- El diseño deja de vivir en un script de Blender. Vive en un **modelo declarativo versionado** con catálogo, reglas y generadores; Blender pasa a ser un generador más.
- Mercado de referencia: **Argentina**. Madera en escuadrías nominales en pulgadas con espesor real de 45 mm (criterio ya adoptado en V06); placas de 1,22 × 2,44 m; Durlock de 1,20 × 2,40 m; rollos de membrana de 1,5 / 2,7 / 3,0 m de ancho.
- Los fundamentos constructivos siguen tomándose de *Woodframe fundamentals* y de la bibliografía ya citada en V06 (Thallon). Cada regla conserva origen y versión; la interfaz no necesita mostrarlos.
- El entregable interactivo (HTML autocontenido) replica el lenguaje visual de las presentaciones Assambl (`pp_shell.cjs`) y agrega un visor 3D por capas.

---

## 1. Tesis del MVP_01

La promesa: **un profesional describe la casa una vez y Assambl devuelve una casa coherente, pieza por pieza, en las 14 capas, con planos listos para construir y la secuencia para hacerlo.** Cada cambio posterior (mover un muro, ampliar una ventana, mover un baño) se propaga a las capas afectadas y marca qué dejó de estar verificado.

Lo que diferencia al MVP_01 de un modelador 3D genérico:

1. **Realismo material.** Las piezas tienen las dimensiones que se compran en una maderera o corralón argentino. Un montante no mide "lo que haga falta": mide 45 × 95 mm y sale de una tabla de 3,05 / 3,66 / 4,27 m con sobrelargo y sierra descontados.
2. **Coherencia física.** La platea sabe cuánto peso baja de cada muro; el header sabe cuánta luz cubre; la canaleta sabe cuántos m² de techo drena. Cuando el modelo no puede verificarlo, lo dice.
3. **Un modelo, muchas salidas.** Planos, detalles, visor HTML, secuencia de ensamble, perspectivas y cantidades salen del mismo archivo de proyecto. No hay copias que se desincronicen.
4. **Orden de construcción.** El modelo conoce las dependencias temporales: la plomería se decide antes de hormigonar, el cableado se pasa después del cierre exterior y antes de aislar. Ese conocimiento se convierte en instructivo.

La medida de éxito del MVP_01 no es la cantidad de capas: es completar **tres casas distintas** dentro del dominio, con planos que un constructor woodframe reconozca como ejecutables y un listado de materiales que coincida con lo modelado.

---

## 2. Dominio de partida

| Dimensión | MVP_01 admite | Fuera de MVP_01 |
| --- | --- | --- |
| Plantas | Una planta sobre platea, altura de muro 2,44–2,75 m | Dos plantas, entrepisos, subsuelos |
| Geometría | Planta ortogonal, quiebres a 90°, hasta 3 volúmenes adosados | Ángulos libres, curvas, muros inclinados |
| Superficie | 40–200 m² cubiertos | Mayor superficie sin revisión estructural |
| Terreno | Lote poligonal, pendiente uniforme ≤ 5 %, sin napa conocida | Laderas, terrenos con desnivel escalonado, suelos problemáticos |
| Cimientos | Platea de hormigón armado con vigas de borde y refuerzos bajo muros portantes | Pilotes, plateas post-tensadas, sótanos |
| Muros | Una familia exterior (45 × 140 o 45 × 95 con cámara) y una interior (45 × 70 / 45 × 95) | Muros dobles acústicos, SIP, CLT |
| Aberturas | Catálogo acotado de ventanas y puertas con medidas comerciales | Aberturas a medida no rectangulares, curtain wall |
| Cubierta | Dos aguas o un agua con cabios; pendiente 15–45 % | Cerchas industriales, cubiertas planas, mansardas |
| Instalaciones | Trazado geométrico y reservas; sin cálculo hidráulico ni eléctrico completo | Dimensionamiento normativo completo, gas, climatización |

Angus Ranch (164 m², una planta, galería) es el primer caso; el segundo y el tercero deben venir de proyectos externos, como exige el plan v0.1.

---

## 3. Las 14 capas

Cada capa es a la vez una **vista** del modelo 3D, un **conjunto de piezas** con ID y un **nodo del grafo de dependencias**. La tabla resume el compromiso en MVP_01; las secciones siguientes detallan cada capa.

| # | Capa | Nivel MVP_01 | Depende de | Afecta a | Salida principal |
| --- | --- | --- | --- | --- | --- |
| 01 | Terreno | Núcleo (simple) | — | 02, 03, 09 | Lote, vecinos, calles, orientación, clima |
| 02 | Cimientos | Núcleo | 01, 03, 13 | 03 | Platea, vigas, refuerzos, pases, anclajes |
| 03 | Estructura woodframe | Núcleo | 02, 13, 14 | 04–12, 14 | Piso, muros, aberturas, techo; uniones |
| 04 | OSB | Núcleo | 03 | 05, 06, 09 | Layout de placas, cantidad, cortes |
| 05 | Membrana exterior (WRB) | Núcleo | 04 | 06 | Rollos, solapes, retornos |
| 06 | Rastreles de siding | Hook | 05 | 07 | Listones, separación, cámara |
| 07 | Siding | Hook | 06 | — | Tipo, color, tablas, cantidad |
| 08 | Aislante de paredes | Hook | 03, 13, 14 | 11 | Tipo, espesor, m², rollos |
| 09 | Roofing | Núcleo | 03 | 10 | Placas, membrana, tejas o chapa |
| 10 | Canaletas | Hook | 09 | 01 | Tramos, bajadas, pendientes |
| 11 | Durlock | Hook | 03, 08, 13, 14 | 12 | Placas, layout, tornillería |
| 12 | Mobiliario y terminaciones | Hook | 11, 13 | — | Biblioteca básica, pisos, cantidades |
| 13 | Plomería | Hook | 03 (wet rooms) | 02, 03, 08, 11 | Trazado, pases, perforaciones |
| 14 | Eléctrico | Hook | 03 | 03, 08, 11 | Tablero, circuitos, cajas, cañerías |

**Núcleo** significa: geometría completa, catálogo real, reglas verificables, planos y cantidades. **Hook** significa: la capa existe en el modelo con su geometría reservada, su catálogo inicial y sus dependencias declaradas; sus reglas pueden ser parciales y sus resultados llevan estado `pendiente` cuando la regla no alcanza. Ninguna capa se omite del visor ni de la secuencia de ensamble.

### 3.1 Terreno

**Objetivo.** Ubicar la casa en un lote real con su contexto inmediato y sus condiciones ambientales, para que orientación, retiros y escurrimiento sean decisiones informadas.

**Entradas.**
- Ubicación (dirección o coordenadas) y polígono del lote.
- Importación desde [Topoexport](https://topoexport.com/) si es viable: límites, edificaciones vecinas, calles y, cuando esté disponible, relieve. Formato objetivo: DXF u OBJ. Debe verificarse licencia, costo y cobertura en Argentina antes de comprometerlo.
- Alternativa manual: dibujar el polígono y cargar vecinos como cajas.
- Datos ambientales: recorrido solar por cálculo astronómico (no requiere descarga: latitud, longitud, fecha); temperaturas medias y extremas mensuales y vientos dominantes desde una fuente abierta (Open-Meteo, NASA POWER o SMN). Se guardan como parámetros del proyecto con su fuente y fecha.

**Reglas.** Retiros mínimos de frente, fondo y laterales como parámetros del proyecto (no se codifica normativa municipal); ubicación de la casa dentro del lote; cota 0 en el nivel de platea, ≥ 150 mm sobre el terreno natural; pendiente mínima de escurrimiento alrededor de la casa 2 %.

**Salidas.** Plano de implantación con norte, retiros y cotas; diagrama de asoleamiento de solsticios y equinoccios; ficha climática del sitio. V06 ya modela lote, calle y terreno para Angus Ranch (`terreno_angus_ranch_V01.py`), lo que sirve de referencia para el formato.

**Estado y pendientes.** Núcleo en versión simple. Pendiente: pruebas con Topoexport en tres lotes reales; decidir si el relieve entra en MVP_01 o queda plano con pendiente uniforme.

### 3.2 Cimientos

**Objetivo.** Platea de hormigón armado que recibe la casa, con refuerzos donde la carga lo pide y con los pases de instalaciones previstos antes de hormigonar.

**Catálogo por defecto (Argentina).** Hormigón H-21 o H-25; platea 120–150 mm; vigas de borde y bajo muros portantes 300–400 mm de altura × 250–300 mm; malla Q188 (150 × 150 × 6 mm); barras Ø 8/10/12 mm en vigas; film de polietileno 200 µ; base de tosca o RDC compactada 150–200 mm; pernos de anclaje J o L de Ø 12,7 mm con empotramiento 180 mm y paso ≤ 1,20 m (criterio V06).

**Reglas.**
- La platea toma la huella de los muros de capa 03 más un voladizo configurable (100–150 mm).
- Cada tramo de muro exterior o portante genera una viga bajo solera. Su altura se marca `pendiente_calculo` si la carga lineal supera un umbral parametrizable; el modelo no dimensiona hormigón, pero acumula la carga que baja de las capas 03, 04, 08, 09 y 11 (pesos propios por m² de referencia) para orientar al profesional.
- Pases de plomería (capa 13): camisas de PVC de Ø 110 / 63 / 50 mm en las posiciones de desagüe, alimentaciones de agua y ventilación, generadas antes de la geometría de hormigón. Sin capa 13 definida, la platea se marca `incompleta: pases pendientes`.
- Anclajes: distribuidos según la regla de V06; excepciones (distancia a montantes y aberturas) listadas en el informe.

**Salidas.** Planta de platea con vigas, refuerzos y pases; corte típico platea–solera–anclaje; listado de hormigón, malla, barras y pernos; posición de cada pase con su ID de origen en plomería.

**Estado y pendientes.** Núcleo. Pendiente: definir con especialista los umbrales de carga que disparan `pendiente_calculo` y las secciones por defecto.

### 3.3 Estructura woodframe

**Objetivo.** El corazón del sistema: piso (cuando el proyecto no apoye directamente en platea), muros, aberturas y techo, con uniones resueltas según *Woodframe fundamentals* y con escuadrías que se consiguen en madereras argentinas.

**Catálogo por defecto (Argentina).** Pino elliottii/taeda cepillado, nominal en pulgadas y real en mm:

| Nominal | Sección real (mm) | Uso principal |
| --- | --- | --- |
| 1" × 2" | 19 × 45 | Rastreles, listones, separadores |
| 1" × 4" | 19 × 95 | Tablas de terminación, tapajuntas |
| 2" × 2" | 45 × 45 | Rastreles de siding, bloqueos menores |
| 2" × 3" | 45 × 70 | Tabiques interiores no portantes |
| 2" × 4" | 45 × 95 | Montantes, soleras, tabiques interiores |
| 2" × 6" | 45 × 145 | Montantes exteriores, cabios, viguetas cortas |
| 2" × 8" | 45 × 195 | Viguetas de piso, cabios, headers |
| 2" × 10" | 45 × 245 | Viguetas, cabios de mayor luz, headers |
| 2" × 12" | 45 × 295 | Vigas cumbrera, headers de vanos grandes |

Largos comerciales: 2,44 · 3,05 · 3,66 · 4,27 · 4,88 · 6,10 m. Multilaminado (LVL) y vigas compuestas sólo como piezas especiales con estado `pendiente_calculo`. El catálogo es editable por proyecto; los valores anteriores son el perfil por defecto y deben verificarse con al menos dos madereras.

**Reglas de entramado (heredadas de V06 y ampliadas).**
- Muros: solera inferior simple, solera superior doble con solapes ≥ 1,20 m y desfasados en esquinas; montantes a 400 o 600 mm entre ejes; montante extra en cada esquina y en cada encuentro en T (esquina de tres montantes o *California corner*, bloqueo tipo escalera para el encuentro T).
- Aberturas: *rough opening* = medida nominal de la abertura + holgura de 10–20 mm por lado; king, jack, header doble (dos hojas de 45 mm con alma de contrachapado 12,5 mm para muros de 140 mm, criterio V06), antepecho y cripples derivados de cada abertura. Header 2 × 6 hasta 1,20 m de luz; 2 × 8 hasta 1,80 m; 2 × 10 hasta 2,40 m; más allá, `pendiente_calculo`. Estos límites son de partida y deben ratificarse con el especialista.
- Piso sobre viguetas (opcional en MVP_01): viguetas 2 × 8 / 2 × 10 a 400 mm con *rim joist*, bloqueos a mitad de luz cuando la luz supera 2,40 m, apoyo mínimo 45 mm.
- Techo: cabios 2 × 6 / 2 × 8 a 600 mm, viga cumbrera, corte *birdsmouth* con asiento ≥ 45 mm, *rafter ties* o cielorraso estructural cada tres cabios, alero 300–600 mm, bloqueos de alero, tabla de frontis 1 × 8 nominal. Cerchas quedan fuera.
- Uniones: clavos 3" (75 mm) y 3½" (90 mm) para entramado, 2½" (63 mm) para placas; conectores metálicos (*joist hangers*, hurricane ties, hold-downs) sólo como piezas catalogadas con estado, no como cálculo lateral.
- Cada pieza recibe un ID estable derivado de su pertenencia (`Muro_Norte/O1/Header_A`), su blanco de corte y la regla que la generó.

**Interacción con otras capas.** Recibe reservas de plomería (13) y eléctrico (14) que se convierten en perforaciones, bloqueos o desplazamientos de montantes; entrega a 04, 05, 08, 09 y 11 las superficies y cavidades sobre las que se calculan placas, membranas y aislantes.

**Salidas.** Plano de entramado por muro (vista frontal con cada pieza acotada e identificada); planta estructural; plano de cabios; despiece, cotización por tablas comerciales y plan de cortes (heredados de V06); detalles de esquina, encuentro T, abertura y apoyo de cabio.

**Estado y pendientes.** Núcleo. Pendiente: revisar con el especialista los límites de header y la conveniencia de muros de 45 × 140 frente a 45 × 145 (2 × 6); definir el conjunto de encuentros de la biblioteca inicial.

### 3.4 OSB

**Objetivo.** Cerrar y arriostrar muros y techo con placas de medidas comerciales, y saber cuántas placas de qué espesor se compran.

**Catálogo por defecto.** Placas de 1,22 × 2,44 m en 9,5 · 11,1 · 15,1 · 18,3 mm. Muros: 11,1 mm. Techo: 15,1 mm (o 11,1 con cabios a 400 mm). Piso sobre viguetas: 18,3 mm.

**Reglas.** Orientación vertical en muros, con juntas sobre montantes; horizontal en techo, con juntas alternadas y separación de 3 mm; clavado a 150 mm en bordes y 300 mm en campo; las placas cubren las aberturas y se recortan (el recorte se contabiliza como desperdicio recuperable si supera 300 × 600 mm). Algoritmo de layout por muro con objetivo de mínimo de placas y máximo de piezas enteras.

**Salidas.** Mapa de placas por muro y faldón con cada placa identificada y sus cortes; tabla por espesor: placas enteras, placas cortadas, desperdicio estimado.

**Estado.** Núcleo.

### 3.5 Membrana exterior (WRB, tipo Tyvek)

**Objetivo.** Capa de control de agua y aire sobre el OSB, con solapes, retornos y cinta contabilizados.

**Catálogo por defecto.** Rollos de 1,5 × 30 m, 2,7 × 30 m y 3,0 × 30 m; cinta de sellado de 60 mm × 25 m; membrana autoadhesiva para antepechos de 150 / 230 mm de ancho.

**Reglas.** Colocación horizontal de abajo hacia arriba, solape horizontal ≥ 150 mm y vertical ≥ 300 mm; continuidad en esquinas ≥ 300 mm; retornos hacia el interior del *rough opening*; antepecho con membrana autoadhesiva antes de la carpintería; cinta en todas las juntas.

**Salidas.** Esquema de tendido por fachada con orden de colocación; cantidad de rollos por ancho, metros de cinta y membrana de antepecho.

**Estado.** Núcleo.

### 3.6 Rastreles de siding

**Objetivo.** Los "rieles" sobre los que se clava el siding, generando la cámara de aire ventilada.

**Catálogo por defecto.** Listones 1 × 2 (19 × 45) o 2 × 2 (45 × 45), tratados o de pino impregnado; malla mosquitera perforada para aberturas de ventilación inferior y superior.

**Reglas.** Alineados sobre cada montante (400 / 600 mm); orientación perpendicular al siding (verticales para siding horizontal; doble rastrelado para siding vertical); cámara mínima 20 mm; ventilación abierta y protegida en base y remate; rastreles perimetrales en aberturas.

**Salidas.** Esquema de rastrelado por fachada; metros lineales por sección; metros de malla.

**Estado.** Hook. Geometría y cantidades completas; la regla de doble rastrelado para siding vertical es la única que puede quedar `pendiente` en la primera iteración.

### 3.7 Siding

**Objetivo.** Ofrecer una selección inicial de tipos y colores, calcular tablas o paneles con desperdicio y mostrar el resultado en el visor.

**Catálogo inicial (5 tipos, 6 colores cada uno).**
- Madera horizontal solapada (*lap*), tablas 1 × 6 y 1 × 8 nominal, largos 3,05 / 3,66 m.
- Madera vertical con junta cubierta (*board & batten*), tablas 1 × 8 + listón 1 × 2.
- Fibrocemento tipo Superboard Siding: 200 × 3.600 × 8 mm, textura madera y lisa.
- Chapa acanalada o lisa prepintada, ancho útil 1,10 m, largos a medida.
- Vinilo doble ranura, paneles de 3,66 m.

**Reglas.** Solape 25–30 mm en horizontal; arranque con tabla de nivel; tapajuntas en esquinas (1 × 4) y perimetrales en aberturas; corte y desperdicio por fachada; el color afecta al visor y a la ficha de materiales, no a la geometría.

**Salidas.** Fachadas con siding y color elegido; tabla de materiales por fachada; alzado de tapajuntas.

**Estado.** Hook. Catálogo y cantidades sí; detalles de encuentro con cubierta y con carpinterías sólo para madera horizontal en la primera iteración.

### 3.8 Aislante de paredes

**Objetivo.** Rellenar cavidades con aislante comercial y saber cuánto material entra.

**Catálogo por defecto.** Lana de vidrio en rollo 1,20 × 18 m × 50 mm (con o sin foil), paneles 0,40 × 1,20 m en 70 / 100 mm; lana de roca 50 / 100 mm; celulosa proyectada como opción `pendiente`; barrera de vapor de polietileno 200 µ del lado caliente (interior en clima templado).

**Reglas.** El espesor de aislante ≤ profundidad de cavidad (95 o 140 mm); cavidades se calculan descontando montantes, bloqueos, cajas eléctricas (14) y pasajes de plomería (13); barrera de vapor continua con solape 150 mm y sellada en cajas; R de referencia por composición (informativo, sin cálculo higrotérmico).

**Salidas.** m² netos de cavidad por muro; rollos y paneles por espesor; m² de barrera de vapor.

**Estado.** Hook. Cantidades completas; la selección automática de espesor según clima (capa 01) queda `pendiente`.

### 3.9 Roofing

**Objetivo.** Cubierta terminada con dos opciones: tejas asfálticas sobre OSB con membrana, o chapa sobre clavaderas.

**Catálogo por defecto.**
- Opción tejas: OSB 15,1 mm (capa 04), membrana asfáltica o sintética de 1 × 20 m, tejas asfálticas de 3 pestañas o arquitectónicas en paquetes de ≈ 3,1 m², faja de arranque, cumbrera ventilada, gotero metálico, babetas.
- Opción chapa: clavaderas 2 × 3 a 600–900 mm o OSB + membrana, chapa acanalada o trapezoidal T-101 calibre 25, ancho útil 1,10 m, largos a medida hasta 12 m, cumbrera, cenefas, tornillos autoperforantes con arandela, aislante bajo chapa (foil + lana).

**Reglas.** Pendiente mínima 17 % (2:12) para tejas con membrana doble, 34 % (4:12) recomendada; chapa ≥ 10 % con largos continuos; sentido de colocación contra viento dominante (capa 01); solape de chapa 150–200 mm; membrana de abajo hacia arriba con solape 100 mm horizontal; cumbrera y aleros con ventilación cuando la cubierta lleva aislante en cabios.

**Salidas.** Planta de techos con faldones, pendientes, cumbreras y bajadas; layout de placas y chapas; cantidades por opción; detalle de alero, cumbrera y encuentro con muro.

**Estado.** Núcleo.

### 3.10 Canaletas

**Objetivo.** Recoger y bajar el agua de cada faldón con pendiente y bajadas suficientes.

**Catálogo por defecto.** Canaleta de chapa galvanizada o prepintada semicircular o rectangular de 100–125 mm; PVC 125 mm; bajadas Ø 75–100 mm; soportes cada 600 mm; boquillas, tapas y codos.

**Reglas.** Pendiente 0,5–1 % hacia la bajada; una bajada por cada ≤ 12 m de canaleta o ≤ 60 m² de faldón; bajadas alejadas de aberturas y descargando a ≥ 1 m de la platea (o a pozo/red si el proyecto lo indica); el lado de descarga se elige con la pendiente del terreno (capa 01).

**Salidas.** Esquema de canaletas y bajadas sobre la planta de techos; metros de canaleta por sección, cantidad de bajadas y accesorios.

**Estado.** Hook. Geometría y cantidades completas; el chequeo de capacidad frente a lluvia de diseño queda `pendiente` hasta contar con datos de la capa 01.

### 3.11 Durlock

**Objetivo.** Revestir interiormente muros y cielorrasos con placas de yeso, con layout y cantidades.

**Catálogo por defecto.** Placa estándar 1,20 × 2,40 m × 12,5 mm; 9,5 mm para cielorrasos; placa RH (verde) 12,5 mm en wet rooms; placa RF (rosa) como opción; tornillos T2 25 mm a 250 mm en bordes y 300 mm en campo; cinta de papel; masilla; cantoneras; perfiles omega 35 mm para cielorraso cuando no se usa aplicación directa.

**Reglas.** Orientación vertical en muros de altura ≤ 2,44 m, horizontal en mayores, con juntas desfasadas; en wet rooms RH obligatoria hasta 1,80 m como mínimo y en todo el muro de ducha; aberturas de cajas eléctricas y salidas de plomería recortadas y contabilizadas; cielorraso con placa 9,5 sobre cabios o cielorraso estructural.

**Salidas.** Mapa de placas por muro y cielorraso; tabla por tipo de placa; tornillos, cinta, masilla y perfiles.

**Estado.** Hook. Cantidades completas; detalles de encuentro con carpinterías y zócalos en la segunda iteración.

### 3.12 Mobiliario y terminaciones interiores

**Objetivo.** Poblar la casa con una biblioteca básica de muebles, artefactos y materiales de terminación para que el usuario "vea su casa" y para contabilizar pisos, revestimientos y pintura.

**Biblioteca inicial (migrada de V06).** Cocina (bajo mesada, alacena, mesada, bacha, anafe, heladera), baño (inodoro, bidet, vanitory, ducha, bañera), dormitorio (cama 1 / 1,5 / 2 plazas, mesas de luz, placard), estar y comedor (sofá, sillón, mesa, sillas, TV, biblioteca), lavadero, exteriores (mesa de galería, sillas, plantas). Cada objeto tiene dimensiones reales, huella, zona de uso y, para artefactos sanitarios, puntos de conexión que alimentan la capa 13.

**Materiales de terminación.** Pisos: porcelanato 60 × 60, cerámico 45 × 45, piso flotante 1,20 × 0,19, madera 1 × 4; revestimiento de baño 30 × 60; pintura látex interior por m²; zócalos MDF 70 mm.

**Reglas.** Huellas de circulación mínimas (900 mm en pasillos, 600 mm frente a artefactos, 700 mm frente a inodoro); artefactos sanitarios sólo en ambientes marcados como wet room; cantidades de piso por ambiente con 10 % de desperdicio.

**Salidas.** Planta amoblada; visor con mobiliario; tabla de terminaciones por ambiente.

**Estado.** Hook. Biblioteca acotada, se amplía después.

### 3.13 Plomería

**Objetivo.** Una vez definidos los wet rooms (baños, cocina, lavadero), trazar alimentación de agua fría y caliente, desagües cloacales y ventilaciones, y volcar sus efectos en cimientos y estructura.

**Catálogo por defecto.** Agua: polipropileno termofusión o PEX Ø 20 / 25 mm; llaves de paso; termotanque eléctrico o a gas (ubicación como reserva). Desagües: PVC Ø 40 (lavatorio, bidet), Ø 50 (ducha, pileta de cocina, lavadero), Ø 63 (colector), Ø 110 (inodoro y colector principal); piletas de patio 15 × 15 y 20 × 20; cámara de inspección 60 × 60; ventilación Ø 63/110 sobre techo.

**Reglas.**
- Cada artefacto de la capa 12 con punto de conexión genera una salida de desagüe y una o dos alimentaciones.
- Desagües con pendiente 1–2 % hacia la cámara; recorrido bajo platea; cada cruce de platea produce un pase en la capa 02 (camisa Ø nominal + 20 mm).
- Alimentaciones por dentro de muros: cada cruce de montante produce una perforación centrada de Ø ≤ 40 % del ancho del montante en tabiques no portantes y ≤ 25 % en portantes; si excede, la regla propone bloqueo, muro húmedo de 2 × 6 o desplazamiento del artefacto y marca `pendiente_revision`.
- Ventilación del colector principal hasta 300 mm sobre la cubierta, con babeta en la capa 09.
- El termotanque se ubica a ≤ 8 m de recorrido del punto de agua caliente más lejano (regla de confort, parametrizable).

**Salidas.** Planta de instalación sanitaria (agua y desagüe) con diámetros; isométrico esquemático; listado de tubos, accesorios y artefactos; tabla de pases (a 02) y perforaciones (a 03).

**Estado.** Hook. Trazado geométrico y dependencias completas; no hay cálculo hidráulico ni verificación normativa. Las dimensiones son de práctica habitual, no de reglamento.

### 3.14 Circuito eléctrico

**Objetivo.** Ubicar el tablero principal, definir circuitos y bocas, y trazar cañerías por la estructura con sus perforaciones.

**Catálogo por defecto.** Tablero de embutir 12–24 módulos; interruptor general, diferencial 30 mA, termomagnéticas 10 / 16 / 20 A; caño corrugado 20 / 25 mm; cajas rectangulares 5 × 10 y octogonales 10 × 10 para embutir en Durlock con soporte a montante; cable unipolar 1,5 / 2,5 / 4 / 6 mm²; tomas, llaves y bocas de iluminación.

**Reglas (referencia AEA 90364-7-771, parametrizables).**
- Tablero principal cerca de la acometida y del acceso, a 1,20–1,60 m del piso, nunca en wet rooms.
- Circuitos: iluminación (IUG) hasta 15 bocas y 10 A; tomas (TUG) hasta 15 bocas y 16 A; circuitos especiales (ACU) para termotanque, anafe eléctrico, aire acondicionado; mínimo dos circuitos por vivienda.
- Bocas por ambiente según superficie (por ejemplo, un toma cada 6 m² o fracción y al menos uno por pared en dormitorios y estar; tomas de cocina y baño sobre mesada y a ≥ 600 mm de duchas y bachas).
- Recorrido: horizontal por la cavidad entre montantes con perforaciones centradas de Ø ≤ 25 mm; vertical dentro de la cavidad; cruce de soleras superiores por perforación; protección con chapa cuando la perforación queda a < 32 mm del borde del montante.
- Las cajas ocupan volumen en la cavidad y lo descuentan del aislante (08); su cara frontal define el recorte de la placa (11).

**Salidas.** Planta eléctrica con bocas, llaves y tablero; esquema unifilar básico; listado de bocas por circuito, metros de caño y cable por sección, cajas; tabla de perforaciones (a 03).

**Estado.** Hook. Distribución y trazado completos; el cálculo de caída de tensión y la verificación normativa completa quedan fuera.

---

## 4. Dónde vive el diseño

### 4.1 Diagnóstico de Angus Ranch V06

El diseño de Angus Ranch vive en `angus_ranch_V06_casa_y_terreno.py` (2.200 líneas): un script que declara muros con aberturas como tuplas, genera piezas con `wall()`, construye la envolvente, muebles, techo, terreno y anclajes, produce el inventario de madera y arma la escena de Blender. Funciona y prueba que la generación paramétrica es viable. Sus límites para un producto:

- Datos y lógica mezclados: cambiar la casa exige editar código.
- Sin grafo de dependencias explícito: el orden de las funciones es el orden de dependencia; un cambio regenera todo y no se sabe qué se vio afectado sin comparar salidas.
- Blender como única salida: las ediciones manuales en Blender no vuelven al script; los planos y el HTML se hacen aparte.
- Sin estados por pieza ni por regla: la advertencia "requiere cálculo" vive en el LEEME, no en el modelo.
- Una sola casa: cada nuevo proyecto es una copia del script.

### 4.2 Decisión: modelo declarativo + reglas + generadores

Assambl separa lo que hoy está en un solo archivo en cuatro partes con contratos claros:

| Parte | Qué contiene | Formato | Quién lo edita |
| --- | --- | --- | --- |
| **Proyecto** | Terreno, ambientes, muros, aberturas, wet rooms, elecciones de materiales, parámetros, historial | JSON versionado (`casa.assambl.json`) con esquema | El usuario, a través de la interfaz y de operaciones |
| **Catálogo** | Escuadrías, placas, rollos, artefactos, muebles, con dimensiones comerciales y perfil por mercado | JSON por mercado (`catalogo/ar.json`) | El equipo Assambl; el cliente puede extender su perfil |
| **Reglas** | Fundamentos: condiciones, parámetros, resultado, origen y versión | Módulos Python puros, un archivo por familia de reglas, registrados con ID | El equipo Assambl con revisión de especialistas |
| **Generadores** | Convierten proyecto + catálogo + reglas en piezas y salidas | Python: geometría pura (sin Blender) → exportadores Blender, GLB, SVG, CSV, HTML | El equipo Assambl |

Flujo: `proyecto + catálogo → motor de capas (aplica reglas en orden del grafo) → modelo resuelto (piezas con ID, estados, relaciones) → generadores`. El modelo resuelto se guarda junto al proyecto como caché regenerable; nunca es la fuente de verdad.

**Por qué no seguir con el script único.** Un script seccionado (una función por capa) resolvería la legibilidad pero no la edición sin código, ni los estados, ni la propagación selectiva, ni la independencia de Blender. Todas esas capacidades son las que el plan v0.1 identifica como críticas ("cambios coherentes", "el modelo debe sobrevivir a la interfaz").

**Qué se reutiliza de V06.** La lógica de `wall()` (kings, jacks, headers, cripples), `timber_inventory()` y `schedule()` (despiece, tablas comerciales, plan de cortes), la distribución de anclajes de `augment_v06()`, y la biblioteca de muebles. Se migran a módulos de reglas y catálogo; el script queda como caso de prueba de regresión: el modelo declarativo de Angus Ranch debe reproducir sus 828 piezas.

### 4.3 Grafo de capas y propagación

Cada capa declara sus entradas (qué lee de otras capas) y sus salidas (qué produce). El motor construye el grafo, detecta ciclos (cimientos ↔ plomería ↔ estructura se resuelven en dos pasadas: reservas primero, geometría después) y, ante una operación, recalcula sólo las capas alcanzables desde el cambio.

Ejemplo: mover el inodoro del baño 300 mm hacia el este.

1. Capa 12 actualiza la posición del artefacto y su punto de conexión.
2. Capa 13 rehace el ramal de desagüe: nuevo pase de platea, nueva perforación de solera.
3. Capa 02 mueve la camisa; si la platea ya está en estado `revisado`, marca `desactualizado`.
4. Capa 03 revisa si la perforación cae sobre un montante; si sí, aplica la regla de bloqueo y marca la pieza `modificada`.
5. Capas 08 y 11 recalculan cavidad y recorte de placa.
6. Capas 04–07, 09, 10 y 14 no se tocan.
7. El historial registra la operación, el diff de piezas y los estados invalidados.

### 4.4 Operaciones y estados

Toda modificación pasa por operaciones con parámetros validados: `crear_muro`, `mover_muro`, `definir_ambiente`, `agregar_abertura`, `modificar_abertura`, `marcar_wet_room`, `ubicar_artefacto`, `elegir_material`, `ubicar_tablero`, `agregar_boca`. La interfaz y el asistente llaman las mismas operaciones; ninguno escribe geometría directamente.

Estados por pieza, por regla y por capa:

| Estado | Significado |
| --- | --- |
| `propuesto` | Generado por reglas, sin verificación específica |
| `comprobado_por_reglas` | Todas las reglas aplicables se cumplieron |
| `pendiente_datos` | Falta una entrada (por ejemplo, wet rooms sin definir) |
| `pendiente_calculo` | La regla reconoce que excede su alcance (header largo, viga alta) |
| `pendiente_revision` | Conflicto resuelto por heurística que debe mirar una persona |
| `revisado` | Aprobado por un usuario identificado en una versión determinada |
| `desactualizado` | Estaba revisado y un cambio posterior lo invalidó |

### 4.5 Blender y visor web

Blender sigue siendo el entorno de prototipado, render de perspectivas y verificación visual: el generador `bpy` construye la escena por capas como hace V06. El visor HTML autocontenido usa un GLB por capa embebido en base64 y three.js, y no depende de Blender en el navegador. La decisión sobre la interfaz de edición (panel en Blender o interfaz propia) se toma como indica el plan v0.1, con el mismo ejercicio comparativo; el modelo declarativo hace que esa decisión sea reversible.

### 4.6 Organización propuesta del código

```
assambl/
  modelo/        esquema del proyecto, operaciones, historial, estados
  catalogo/      ar.json (perfil Argentina), esquema de catálogo
  reglas/        r01_terreno.py … r14_electrico.py, registro con ID y versión
  capas/         motor del grafo, resolución por capa, diff
  geometria/     primitivas, layout de placas, empaquetado de tablas
  generadores/   blender.py, glb.py, planos_svg.py, csv.py, html_visor.py, secuencia.py
  casos/         angus_ranch.assambl.json + pruebas de regresión (828 piezas)
```

---

## 5. Fundamentos: las reglas del realismo

Los fundamentos son las verdades sobre las que Assambl produce resultados consistentes. Se organizan en seis familias; cada regla se registra con ID, versión, origen, condiciones de aplicación, parámetros, resultado y estado que otorga.

| Familia | Qué garantiza | Ejemplos |
| --- | --- | --- |
| **Geométricas** | Que las piezas ocupen espacio real y no se superpongan | Montantes centrados en su módulo; placas no se solapan; aberturas dentro del muro con jambas mínimas |
| **De catálogo** | Que todo lo modelado se pueda comprar | Toda pieza referencia un ítem del catálogo; largos ≤ largo comercial máximo o se marca empalme; placas cortadas de 1,22 × 2,44 |
| **Constructivas** | Que las uniones sean las del sistema woodframe | Solera doble con solape; esquinas de tres montantes; header doble sobre abertura; solape de membrana; clavado de placas |
| **Físicas simplificadas** | Que la casa responda a gravedad y agua | Carga acumulada por muro hacia la platea; pendiente mínima de techo y desagüe; agua siempre hacia abajo y hacia afuera (solapes tipo teja) |
| **Normativas de referencia** | Que las instalaciones no contradigan práctica y normas conocidas | AEA 90364 para circuitos y bocas; diámetros de desagüe por artefacto; RH en wet rooms; distancias tablero–agua |
| **De secuencia** | Que el orden de construcción sea posible | Pases antes de hormigonar; cableado después del cierre exterior y antes del aislante; Durlock después de instalaciones aprobadas |

Principios de implementación:

- **Alcance explícito.** Cada regla dice qué cubre y qué no. Fuera de alcance no falla en silencio: emite `pendiente_calculo` o `pendiente_revision`.
- **Reproducibilidad.** Mismo proyecto + mismo catálogo + mismas versiones de reglas = mismo modelo resuelto, byte a byte. Es la base de las pruebas de regresión y del diff entre versiones.
- **Parámetros, no constantes.** Separaciones, solapes, umbrales y diámetros son parámetros con valor por defecto y rango admitido; el cliente puede ajustarlos dentro del rango.
- **Origen conservado.** *Woodframe fundamentals*, Thallon, manuales de fabricantes (Durlock, Superboard, Isover) y normas (AEA) se registran como origen de cada regla, con la aclaración de que las medidas de libros extranjeros no se presentan como reglamento argentino.
- **Revisión especializada antes de automatizar.** Ninguna regla estructural (headers, vigas, plateas) pasa a `comprobado_por_reglas` sin haber sido revisada por el especialista en estructuras de madera del equipo.

---

## 6. Entregables del MVP_01

Todos se generan desde el modelo resuelto con un solo comando (`assambl exportar casa.assambl.json --paquete`), en una carpeta con fecha y versión.

### 6.1 Planos listos para construir

Formato SVG con exportación a PDF, escala declarada, cotas en mm, norte y rótulo con versión del proyecto y estado de revisión.

| Plano | Contenido | Capas |
| --- | --- | --- |
| Implantación | Lote, retiros, casa, norte, cotas, vecinos | 01 |
| Planta de platea | Contorno, vigas, refuerzos, pases con ID, anclajes | 02, 13 |
| Planta arquitectónica | Muros, aberturas con código, ambientes con superficie, mobiliario | 03, 12 |
| Planta estructural | Ejes de muros, montantes, headers identificados | 03 |
| Entramado por muro | Alzado de cada muro con cada pieza acotada e identificada | 03 |
| Planta de cabios y techos | Cabios, cumbrera, aleros, faldones, pendientes, canaletas y bajadas | 03, 09, 10 |
| Mapas de placas | OSB por muro y faldón; Durlock por muro y cielorraso | 04, 11 |
| Fachadas | Cuatro fachadas con siding, aberturas y niveles | 07 |
| Cortes | Dos cortes con platea, muro completo por capas, cubierta | 02–11 |
| Sanitaria | Agua y desagüe con diámetros; isométrico esquemático | 13 |
| Eléctrica | Bocas, llaves, tablero, circuitos; unifilar básico | 14 |

### 6.2 Detalles de partes clave

Biblioteca inicial de detalles paramétricos (se dibujan con las dimensiones reales del proyecto, no como láminas fijas):

1. Anclaje solera–platea con perno y junta (heredado de V06, capa 13 de Blender).
2. Header doble con alma, king, jack y cripples (heredado de V06, vista explotada).
3. Esquina exterior de tres montantes con OSB, membrana, rastrel y siding.
4. Encuentro T interior con bloqueo escalera.
5. Solape de solera superior doble.
6. Apoyo de cabio con *birdsmouth*, bloqueo de alero y frontis.
7. Corte completo de pared: Durlock – barrera de vapor – aislante – montante – OSB – membrana – rastrel – cámara – siding, con espesores acotados (el "sistema de aislación completo").
8. Antepecho de ventana: membrana autoadhesiva, retornos, gotero.
9. Pase de desagüe en platea con camisa.
10. Perforación de montante para cañería eléctrica con protección.

### 6.3 HTML interactivo autocontenido

Un solo archivo `.html`, sin dependencias externas salvo tipografías opcionales, que replica el formato de las presentaciones Assambl (`pp_shell.cjs`): navegación por láminas, índice, modo lectura, documento completo embebido. Se agrega:

- **Lámina "capa por capa"**: visor three.js con las 14 capas como GLB embebidos; el usuario activa o apaga capas, las recorre en secuencia con animación de apilado y orbita la casa. Cada capa muestra su ficha (piezas, m², cantidades, estado).
- **Lámina de cambios**: si el proyecto tiene historial, muestra el último diff (piezas nuevas, modificadas, eliminadas) sobre el modelo.
- **Láminas de entregables**: planos y detalles embebidos como SVG navegables.
- **Lámina de secuencia**: la línea de tiempo de ensamble (6.4) sincronizada con el visor.

Restricción de tamaño: ≤ 40 MB para que se comparta por correo o link directo; el GLB se simplifica por capa (sin muebles de alta densidad) si hace falta.

### 6.4 Secuencia de ensamble

Un instructivo generado desde el grafo de dependencias y las reglas de secuencia, ordenado por fases, con lo que se necesita tener resuelto antes de cada una y las decisiones que no pueden postergarse.

| Fase | Trabajo | Condición previa | Advertencia que el sistema emite |
| --- | --- | --- | --- |
| 0 | Replanteo del lote y nivelación | Capa 01 revisada | Verificar retiros con el municipio |
| 1 | Excavación, base compactada, film | Capa 02 en estado revisado | — |
| 2 | Tendido de desagües y camisas de pases | Capa 13 revisada | **La plomería bajo platea se decide ahora: después no se cambia sin romper** |
| 3 | Armado, pernos de anclaje posicionados, hormigonado | Capas 02 y 13 | Pernos según plano de anclajes; curado ≥ 7 días antes de cargar |
| 4 | Soleras tratadas, junta, montaje de muros por paneles, solera doble | Capa 03 | Orden de muros sugerido: exteriores largos → exteriores cortos → interiores |
| 5 | Cabios, cumbrera, bloqueos, OSB de techo, membrana | Capas 03, 04, 09 | Techo estanco antes de seguir con interiores |
| 6 | OSB de muros, membrana exterior, carpinterías, antepechos | Capas 04, 05 | Membrana antes de las carpinterías; retornos y cinta |
| 7 | Rastreles y siding; canaletas y bajadas | Capas 06, 07, 10 | Ventilación de cámara abierta arriba y abajo |
| 8 | Cañerías de agua interiores y ventilación cloacal | Capa 13 | Prueba hidráulica antes de cerrar |
| 9 | Cañerías eléctricas, cajas y tablero (sin cablear si hay humedad) | Capa 14 | **Cablear después del cierre exterior y antes del aislante** |
| 10 | Aislante, barrera de vapor | Capa 08 | Sellar cajas y perforaciones |
| 11 | Durlock, masillado, cielorrasos | Capa 11 | Sólo con instalaciones aprobadas |
| 12 | Terminación de cubierta (tejas o chapa si se postergó), pintura, pisos | Capas 09, 12 | — |
| 13 | Cableado, artefactos, mobiliario | Capas 12, 14 | Prueba eléctrica antes de habilitar |

Cada fase enlaza los planos y detalles que se usan y la lista de materiales que hay que tener en obra. Se exporta como parte del HTML y como PDF.

### 6.5 Vistas de perspectiva

Cuatro perspectivas exteriores (una por esquina), dos interiores (estar y cocina), una axonométrica explotada por capas y una aérea con contexto del lote. Se renderizan en Blender (Eevee) desde cámaras fijadas por regla (altura de ojo 1,60 m, distancia proporcional al ancho de la casa) para que todas las casas se presenten igual. El HTML las incluye comprimidas.

### 6.6 Render animado

No es prioridad del MVP_01. Opciones a evaluar cuando llegue el momento, ordenadas por costo:

1. **Órbita automática en el visor three.js** del HTML (ya disponible con el visor; costo nulo).
2. **Animación de apilado por capas** en el visor (aparecen las 14 capas en orden de ensamble; costo bajo, misma tecnología).
3. **Video MP4 desde Blender**: órbita de 15–20 s en Eevee con las cámaras del 6.5, exportado con ffmpeg (costo medio, dependencia de tiempo de render).
4. **Recorrido interior** con cámara animada (costo alto; segunda etapa).

---

## 7. Criterios de aceptación del MVP_01

1. Tres casas distintas dentro del dominio (Angus Ranch y dos externas) completan las 14 capas con estados visibles y exportan el paquete completo sin intervención del desarrollador.
2. El modelo declarativo de Angus Ranch reproduce las 828 piezas de V06 con los mismos IDs, dimensiones y cotización de tablas (prueba de regresión).
3. Cada pieza de madera, placa, rollo y artefacto referencia un ítem del catálogo argentino; ningún largo supera el comercial sin empalme declarado.
4. Las operaciones `modificar_abertura`, `mover_muro` y `ubicar_artefacto` propagan el cambio a las capas afectadas, dejan intactas las demás y producen un diff legible.
5. Los planos de entramado por muro son reconocidos como ejecutables por al menos un constructor woodframe externo en una revisión documentada.
6. La secuencia de ensamble incluye las advertencias de plomería en cimientos y de cableado antes de aislar, y cada fase enlaza planos y materiales.
7. El HTML interactivo abre en un navegador de escritorio sin conexión, muestra las 14 capas y pesa ≤ 40 MB.
8. Las cantidades exportadas coinciden con las piezas únicas del modelo; las copias de presentación (despiece, detalles) no se suman.
9. Todo elemento fuera de alcance queda marcado con un estado `pendiente_*` visible en el visor y en el paquete; no hay salidas silenciosas.

---

## 8. Riesgos específicos del MVP_01

| Riesgo | Señal temprana | Respuesta |
| --- | --- | --- |
| Catorce capas dispersan el esfuerzo | Ninguna capa termina en estado exportable | Congelar hooks en versión mínima (geometría + cantidades) y cerrar núcleo primero |
| Catálogo argentino no coincide con la oferta real | Madereras no tienen 2 × 8 en 6,10 m o largos difieren | Verificar con dos proveedores en la semana 2; el catálogo es dato, no código |
| Topoexport no cubre o no licencia | Sin lote real importable en las pruebas | Carga manual del polígono desde el inicio; Topoexport como mejora |
| Reglas estructurales plausibles pero equivocadas | Especialista rechaza headers o vigas por defecto | Estados `pendiente_calculo` amplios hasta revisión; nunca `comprobado` sin especialista |
| El grafo de dependencias se vuelve inmanejable | Cambios menores regeneran todo o dejan capas inconsistentes | Dependencias declaradas por capa, pruebas de propagación por operación |
| GLB de 14 capas demasiado pesado | HTML > 40 MB | Simplificación por capa, muebles en baja densidad, texturas procedurales |
| Migrar V06 consume el tiempo del producto | Semana 6 sin caso externo | La regresión de 828 piezas se acepta con tolerancia y se completa después del caso externo |

---

## 9. Hoja de ruta del MVP_01

Plazos orientativos con dedicación técnica sostenida, alineados con los 4–6 meses del plan v0.1. Cada hito cierra con una casa exportable, no con una lista de funciones.

| Hito | Plazo | Contenido | Condición para avanzar |
| --- | --- | --- | --- |
| H0 · Modelo y motor | Semanas 1–4 | Esquema del proyecto, catálogo AR v0, registro de reglas, motor del grafo, migración de `wall()` y despiece; Angus Ranch declarativa | Regresión de 828 piezas dentro de tolerancia; `modificar_abertura` con diff |
| H1 · Núcleo de la envolvente | Semanas 5–10 | Capas 01 (simple), 02, 03, 04, 05, 09 completas; planos de entramado, platea y techo; detalles 1–8 | Segunda casa (externa) exporta planos revisables |
| H2 · Hooks y visor | Semanas 11–16 | Capas 06, 07, 08, 10, 11, 12 en versión hook; visor three.js con 14 capas; perspectivas | Tercera casa; HTML ≤ 40 MB; revisión de un constructor |
| H3 · Instalaciones y secuencia | Semanas 17–22 | Capas 13 y 14 con propagación a 02, 03, 08, 11; secuencia de ensamble; detalles 9–10 | Mover un baño propaga a platea y estructura con diff correcto |
| H4 · Cierre del MVP_01 | Semanas 23–26 | Historial y deshacer, estados de revisión, paquete completo, correcciones de pilotos | Criterios de aceptación de la sección 7 cumplidos |

---

## 10. Preguntas abiertas

1. **Espesor de muro exterior:** ¿45 × 140 con alma de contrachapado como V06, o 2 × 6 real (45 × 145) para simplificar catálogo y aislante de 140 mm? Decidir con el especialista y con dos madereras.
2. **Piso:** ¿MVP_01 admite piso sobre viguetas además de platea directa, o se posterga?
3. **Topoexport:** confirmar licencia, formatos y cobertura en Córdoba; probar en tres lotes.
4. **Cubierta:** ¿ambas opciones (tejas y chapa) en H1, o chapa primero por ser la más frecuente en el mercado local?
5. **Perfil de catálogo por cliente:** ¿el cliente edita su catálogo desde el inicio o sólo elige entre perfiles?
6. **Interfaz de edición:** panel en Blender o interfaz propia; el ejercicio comparativo del plan v0.1 sigue pendiente y no bloquea H0–H1.
7. **Alcance de las 14 capas en el visor:** ¿se muestran las capas hook con estado `pendiente` al usuario final del piloto, o sólo al equipo?
8. **Unidades del catálogo:** ¿se conservan las nominales en pulgadas en la interfaz (como habla el mercado) mostrando mm en planos?

---

**Base documental:** Plan de negocios v0.1 (18/09/2026); LEEME y script de Angus Ranch V06; *Woodframe fundamentals* y Thallon como origen de reglas constructivas; catálogos públicos de fabricantes (Durlock, Superboard, Isover) y AEA 90364-7-771 como referencia de instalaciones; instrucciones del fundador del 22/09/2026. Las dimensiones comerciales y umbrales indicados son valores de partida para el perfil Argentina y deben verificarse con proveedores y especialistas antes de usarse en obra.
