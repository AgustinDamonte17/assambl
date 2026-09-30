# Fundamentos de diseño de la planta

> Capa 03 · Casa. Código: `backend/assambl/fundamentos/`. Material de estudio: `docs/interior_fundamentals/`.

Las alternativas que propone Monti no son aleatorias: salen de **plantas de referencia** que ya funcionan y se
evalúan con **fundamentos de diseño** tomados de la teoría de planificación de interiores. Este documento resume esa
teoría, explica cómo la mide Assambl y qué muestra de cada una de las diez plantas de referencia.

## Qué son y qué no son

Las reglas R03 (`reglas/r03_planta.py`) son como la física de una viga: un header tapa la luz o no la tapa, un
dormitorio tiene la superficie mínima o no la tiene. Producen **estados** por pieza.

Los fundamentos son otra cosa: **buenas prácticas que se contraponen entre sí**. Un pasillo da privacidad y cuesta
metros; una planta en L gana luz y cuesta muro; un recibidor da sensación de llegada y ocupa superficie que se podría
vivir. Por eso:

- no producen estados ni bloquean nada;
- cada observación es **a favor**, **a considerar** o **para saber**, con los ambientes a los que se refiere;
- cada fundamento dice **qué se resigna** si se lo sigue (su tensión con otros);
- los puntajes (0–100 por criterio) solo sirven para **comparar alternativas entre sí**, no para calificar una casa.

La decisión es siempre del usuario: la herramienta le muestra qué gana y qué resigna con cada partido.

## Fuente

M. Mitton y C. Nystuen, *Residential Interior Design: A Guide to Planning Spaces*, 3.ª ed., Wiley, 2016 (citado
**RID**, con capítulo y página del libro). El libro reúne a su vez a C. Alexander (*A Pattern Language*), O. Newman
(espacio defendible), E. T. Hall (proxémica), S. Susanka (*The Not So Big House*) y el International Residential
Code 2015 (IRC). Los umbrales del libro están en pies y pulgadas; acá están convertidos y redondeados, y deben
leerse como orientativos. Las páginas se refieren al libro, no al PDF (en el PDF de estudio, página del libro + 8).

## Ideas centrales del libro

1. **Privacidad y territorio** (cap. 1). La casa ofrece una jerarquía de territorios de lo público a lo privado
   (Newman: público, semipúblico, semiprivado, privado, con zonas colchón entre ellos). Alexander lo llama
   *gradiente de intimidad*: entrada y estar adelante, dormitorios y baños al fondo. Si los ambientes no siguen ese
   orden, las visitas —de extraños, de amigos o de la propia familia— siempre resultan un poco incómodas.
2. **Calidad antes que cantidad** (cap. 1, Susanka). Una casa más chica y bien pensada rinde más que una grande con
   ambientes que no se usan. En Assambl se traduce en mirar la circulación y la superficie aprovechada.
3. **La entrada como transición** (cap. 2). Entre la calle y el interior hace falta un lugar de llegada; si la
   transición es brusca no hay sensación de llegar. El recibidor ocupa entre 2,5 % y 5 % de la casa, idealmente es
   tan ancho como profundo, está a resguardo del viento dominante, cerca del estar y del toilette, y tiene placar.
   El garage y el lavadero-mudroom funcionan como colchón en la entrada de servicio.
4. **La circulación no produce** (cap. 2). Los pasillos son superficie que se paga y no se vive: conviene
   minimizarlos. Un pasillo con puertas a ambos lados (doble carga) sirve el doble que uno con puertas de un solo
   lado. Pasillos de 0,90 m como mínimo, mejor 1,05–1,20 m; puertas de 0,90 m; 1,50 m de giro para silla de ruedas.
5. **El estar se organiza en grupos de conversación** (cap. 3): de hasta seis personas, en un círculo de unos 3,7–4 m.
   El tránsito no debe cruzar el grupo; el paso de punta a punta de un ambiente rectangular es el que más limita
   cómo se lo amuebla.
6. **La cocina es el centro** (cap. 4): abierta al comedor, con el triángulo de trabajo (heladera, pileta, cocina)
   fuera del paso, cerca de una entrada de servicio y del lavadero.
7. **Dormitorios** (cap. 5): ubicados según la circulación de la familia y el ruido; 12–13,5 m² casi cuadrados para
   una cama de dos plazas con muebles en dos paredes, 14 m² o más para tres; placar cerca de la puerta; la posición
   de la puerta respecto de las ventanas define cómo se amuebla. Planta *dividida* (principal lejos de los demás)
   o *agrupada*: ninguna es mejor, depende de la familia.
8. **Baños** (cap. 6): menos y mejores, compartimentados; muros húmedos compartidos; mejor no en muros exteriores
   en climas fríos; que la puerta no mire al inodoro; baño completo mínimo 1,50 × 2,25 m, toilette 1,3–1,7 m².
9. **Programa, diagramas y superficie** (cap. 8): del programa a un diagrama de burbujas (adyacencias), después a un
   diagrama de bloques orientado al sitio y recién ahí a la planta. Lo programado es el 80–85 % de la superficie
   bruta; el resto son muros y circulación (Assambl usa 82 % en `ia/guion.py`).
10. **Evaluar varias soluciones distintas** (cap. 10): generar partidos bien diferentes y compararlos contra los
    requisitos, en lugar de pulir la primera idea. El entramado es el 45–55 % del costo de la obra y mover
    cañerías es de lo más caro: la compacidad y el núcleo húmedo pesan en la economía.

## Los fundamentos que mide Assambl

Agrupados en seis criterios. La implementación está en `fundamentos/evaluar.py` y se apoya en el grafo de la planta
(`fundamentos/grafo.py`): qué ambiente linda con cuál, si entre ellos hay muro, puerta o nada, qué fachadas tiene
cada uno, por dónde se entra y cómo se llega de un ambiente a otro.

| Criterio | Id | Fundamento | Qué mide | Referencia | Fuente |
|---|---|---|---|---|---|
| Privacidad y zonas | F01 | Gradiente de intimidad | A qué ambiente se abre cada dormitorio | Pasillo o recibidor, no el estar | RID 1, pp. 2–4 |
| | F02 | Dormitorios lejos del ruido | Muro compartido entre dormitorios y estar o cocina | Menos de 15 % del perímetro | RID 5, p. 126 |
| | F03 | Entrada como transición | A qué ambiente da la puerta de acceso | Un recibidor | RID 2, pp. 29–31 |
| | F06 | Baño para las visitas | Recorrido de la entrada a un baño sin cruzar dormitorios | Que exista | RID 1, p. 7; 2, p. 31 |
| Recorridos | F04 | Circulación justa | Pasillos y recibidores / superficie útil | ≤ 10 % muy eficiente; > 18 % mucho | RID 2, p. 42 |
| | F16 | Anchos para todos | Pasillo más angosto y puerta interior más angosta | ≥ 1,05 m y ≥ 0,80 m | RID 2, pp. 38–46 |
| Luz y sol | F08 | Luz natural suficiente | Vidrio / superficie de cada ambiente habitable | ≥ 8 % (IRC), ideal 10 % | RID 1, p. 17; 3, p. 62 |
| | F09 | Orientación al sol | Ventanas del estar (doble peso) y dormitorios hacia el sol | Norte en el hemisferio sur | RID 9, p. 229 |
| Ambientes cómodos | F10 | Estar para reunirse | Lado menor del estar y puertas que desembocan | ≥ 3,6 m; ≤ 4 accesos | RID 3, pp. 52–59 |
| | F07 | Dormitorios con lugar para amoblar | Superficie, lado menor y proporción | Principal ≥ 12 m² y 3 m; otros ≥ 9 m² y 2,7 m | RID 5, pp. 126–136 |
| | F11 | Cocina conectada | Abierta o comunicada con el comedor; junto a lavadero, garage o salida | Las dos cosas | RID 4, pp. 66–71; 7, p. 188 |
| Instalaciones agrupadas | F05 | Núcleo húmedo | Grupos de ambientes con agua que se tocan | Un solo grupo | RID 6, pp. 176–178; 10, p. 241 |
| Economía de obra | F12 | Compacidad | Perímetro / perímetro del cuadrado de igual área; esquinas | ≤ 1,08 | RID 10, p. 243 |
| | F13 | Superficie que se aprovecha | Ambientes / superficie cubierta | 80–85 % | RID 8, p. 203 |

Cada fundamento lleva en el código su principio, el porqué, lo que mide, la tensión con otros y la fuente; la API
los expone en `GET /api/casa/fundamentos` y la pestaña *Fundamentos de diseño* los muestra al usuario.

Cuando una planta tiene ambientes sin contorno (el estar de Angus Ranch es «lo que queda»), no se sabe por dónde se
circula: la evaluación lo avisa y omite los fundamentos que dependen de eso.

### Del libro, todavía no medidos

Quedan para cuando el editor tenga muebles e instalaciones (capas 12 y 13): el triángulo de trabajo de la cocina
(lados de 1,2 a 2,7 m, total 3,6 a 7,9 m), los grupos de conversación con muebles reales, las distancias de paso
alrededor de la cama (0,90–1,20 m el principal, 0,60 m el secundario), la ubicación de artefactos en el baño y la
visual desde la puerta al inodoro, las puertas cerca de las esquinas y abriendo contra un muro ciego, la ventilación
por aberturas practicables (4 %), la visitabilidad completa (entrada sin escalones) y la previsión de ampliaciones.

## Plantas de referencia

Las diez plantas de `docs/interior_fundamentals/` están transcriptas en `fundamentos/plantas_referencia.json` como
rectángulos de ejes en metros, con los rasgos que las caracterizan y una lectura en palabras. Se leyeron
superponiendo una grilla métrica a cada dibujo y se validaron regenerándolas con `capas/casa.py` y las reglas R03.
Simplificaciones: sin retranqueos menores a unos 30 cm, sin bay windows ni muros en diagonal, placares dentro del
dormitorio. La orientación del dibujo no es la del sol: Assambl gira y espeja cada planta.

Evaluación de cada una tal como está dibujada, en el hemisferio sur (−31,4°) y orientada como el dibujo
(la pestaña de referencias las muestra ya orientadas al sol, por eso ahí la luz puede puntuar más):

| Planta | m² | Privacidad | Recorridos | Luz y sol | Ambientes | Instalaciones | Economía | Circulación | Compacidad |
|---|---|---|---|---|---|---|---|---|---|
| 060 · Compacta de 2 dormitorios sin pasillo | 60 | 80 | 68 | 94 | 96 | 100 | 100 | 2 % | 1,02 |
| 082 · Dos franjas con hall central | 82 | 76 | 80 | 100 | 97 | 100 | 100 | 7 % | 1,03 |
| 096 · Tres dormitorios alrededor de un hall | 96 | 80 | 80 | 90 | 98 | 55 | 90 | 8 % | 1,12 |
| 101 · Nórdica con galería y sin pasillo | 101 | 84 | 80 | 90 | 78 | 100 | 100 | 4 % | 1,00 |
| 106 · Dormitorios divididos, social al centro | 106 | 90 | 80 | 90 | 100 | 100 | 89 | 5 % | 1,13 |
| 120 · Lineal de 4 dormitorios, principal en un extremo | 120 | 80 | 68 | 92 | 91 | 55 | 92 | 7 % | 1,13 |
| 160 · Garage como colchón, suite junto a la entrada | 160 | 95 | 52 | 90 | 83 | 35 | 59 | 19 % | 1,12 |
| 172 · En L con garage y entrada en el ángulo | 172 | 94 | 67 | 78 | 87 | 55 | 47 | 14 % | 1,17 |
| 180 · Estar como pabellón, garage al frente | 180 | 85 | 68 | 82 | 100 | 35 | 43 | 4 % | 1,21 |
| 204 · Dos alas con oficina de bisagra | 204 | 100 | 59 | 90 | 87 | 35 | 39 | 17 % | 1,33 |

Lo que muestran, leído con la teoría:

- **Las chicas son compactas y agrupan el agua** (060, 082, 101): compacidad cercana a 1, un solo núcleo húmedo y
  casi nada de pasillo. El precio es la privacidad: en 060 y 101 los dormitorios se reparten desde el estar o un
  recibidor mínimo, y se entra directo al estar. Son buenas para una pareja, una casa de fin de semana o un
  presupuesto ajustado.
- **El hall central es el término medio** (082, 096): un hall corto de doble carga reparte a dormitorios y baños
  con 7–8 % de circulación, y el gradiente de intimidad aparece sin gastar en pasillos largos.
- **La planta dividida compra privacidad** (106, 120): la suite queda del otro lado del estar. 106 lo logra sin
  perder el núcleo húmedo porque la suite se apoya en la cocina; 120 separa el agua en dos grupos.
- **Las grandes ganan privacidad y la pagan en muro** (160 a 204): recibidor, toilette de visitas, garage como
  colchón y alas separadas les dan los mejores valores de privacidad, a cambio de más circulación, varios grupos
  húmedos y más muro exterior por metro cuadrado. La L de 172 y las alas de 204 arman patios y fachadas al sol.
- **Casi todas ponen el estar y los dormitorios en fachadas distintas del agua**: la orientación del lado húmedo
  hacia la fachada fría es un rasgo común que Assambl usa al orientarlas.

## Cómo se convierten en alternativas

`fundamentos/referencias.py`, llamado desde `capas/casa.alternativas()`:

1. **Elegir.** Sirven las plantas con los dormitorios pedidos o uno más, que pasa a ser la oficina pedida o queda
   como «oficina o cuarto de huéspedes».
2. **Adaptar.** Se quita el garage o la galería si no se pidieron; se renombran los ambientes con los del programa
   (el principal al principal); se agranda hasta 12 % hacia la superficie buscada. No se achica: achicar angosta
   pasillos y puertas por debajo de lo usable, así que se avisa que es más grande y se ajusta en el editor.
3. **Orientar.** Se prueban los ocho giros y espejados y se queda el que mejor evalúa, sobre todo en luz y sol.
   Sin ubicación en el paso Terreno se supone el hemisferio sur y se avisa.
4. **Ordenar.** Por parecido al programa (dormitorios, baños, garage, galería, superficie y las preferencias
   *dormitorios juntos o divididos* y *entrada con recibidor o directa*) y por la evaluación de fundamentos.
5. **Explicar.** Cada alternativa dice de qué planta sale, qué se le cambió y qué gana y resigna. Si ninguna
   referencia sirve (por ejemplo, cinco dormitorios), se usan los partidos del generador, también evaluados.

Monti pregunta por esas preferencias en el modo orientador (`ia/guion.py`) y el asistente con IA recibe el resumen
de fundamentos en su prompt (`ia/asistente.py`) para explicar las opciones con el mismo criterio.

## Dónde se ve

- **Formas de empezar → Partí de una casa que funciona**: la galería de las diez plantas (dibujo original y versión
  Assambl), con sus rasgos, su evaluación y un botón para empezar desde cualquiera. Otra pestaña muestra los
  fundamentos completos con su fuente.
- **Alternativas**: cada tarjeta suma el origen, las barras de los seis criterios, lo más destacado a favor y a
  considerar, qué se adaptó y todas las observaciones.
- **Editor**: la sección *Fundamentos de diseño* se recalcula con cada cambio (`POST /api/casa/analizar`); al pasar
  el mouse por una observación se resaltan los ambientes a los que se refiere.
