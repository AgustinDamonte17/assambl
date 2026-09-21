# Plan de trabajo — Aplicación a Y Combinator Winter 2027

**Inicio:** sábado 19 de septiembre de 2026 · **Límite:** ~lunes 2 de noviembre (44 días) · **Objetivo interno de envío:** viernes 30 de octubre (buffer de 3 días).

> Confirmar la fecha y hora exactas del cierre en ycombinator.com/apply la semana 1. YC revisa en orden de llegada: enviar antes del límite es una ventaja, no un riesgo.

---

## 0. Cómo leer este plan

- **Un resultado, dos usos.** Aplicar es la meta; el subproducto es una versión 0.2 del plan de negocios con evidencia real. Cada tarea tiene que servir a las dos cosas.
- **Tres frentes en paralelo**, cada uno con un entregable por semana: **Evidencia** (gente real usando y opinando), **Producto** (una demo que muestre el circuito completo), **Aplicación** (respuestas, videos, landing).
- **Criterio YC** que ordena las prioridades: fundadores claros y rápidos → progreso concreto → problema real con usuarios identificables → tamaño de mercado. La aplicación se escribe en inglés, en frases cortas, con números. Nada de adjetivos.
- **Regla de honestidad:** ninguna respuesta afirma algo que no podamos mostrar. Si el 30/10 no hay usuarios, se responde "No" y se explica qué sí hay. La aplicación puede editarse hasta la fecha de cierre incluso después de enviada.

---

## 1. Punto de partida (lo que ya existe y lo que falta)

### Lo que tenemos
| Activo | Estado | Sirve para |
| --- | --- | --- |
| Plan de negocios v0.1 (18/09) | Completo, con hipótesis explícitas | Base de todas las respuestas de texto |
| Presentación `PP_Fable_WF.html` (33 láminas) | Lista | Landing / material para entrevistas |
| Angus Ranch V06 en Blender: 828 piezas con ID estable, 24 headers, 100 pernos, 13 capas, despiece y plan de cortes regenerables desde geometría | Base experimental. Las aberturas son paramétricas: `wall()` deriva kings, trimmers, headers y cripples de cada abertura | Núcleo de la demo |
| `Computo_madera_V06.html` + 6 CSV | Regenerables con `--check` | Mostrar continuidad geometría → cantidades |
| Dos arquitectos contactados | Sin compromiso formal | Primeros usuarios / entrevistas |
| Renders V04/V06 | Listos | Landing y video demo |

### Lo que falta y YC pregunta directamente
| Pregunta YC | Hoy | Meta al 30/10 |
| --- | --- | --- |
| Company name / 50 caracteres | Pendiente | Nombre provisorio elegido, dominio comprado |
| Company URL / product link | No hay | Landing de una página con demo, deck y contacto |
| Demo (≤ 3 min) | No hay | Video mostrando el circuito "cambiar abertura → regenerar → diff de piezas y cantidades" |
| Founder video (1 min) | No hay | Grabado, sin edición, ≤ 100 MB |
| Are people using your product? | No | Sí: 2–3 profesionales usaron el prototipo sobre un proyecto propio, con registro de horas y feedback |
| Do you have revenue? | No | Idealmente un piloto pago (cualquier monto, incluso USD 200) o una carta de intención firmada |
| Who writes code? | Por definir con precisión | Respuesta clara: quién, cuánto, con qué herramientas de IA |
| Are you looking for a cofounder? | Sin decidir | Decisión tomada en semana 2 |
| Legal entity / investment / fundraising | No / No / No | Se responde tal cual. No conviene gastar en sociedad antes de aplicar; YC constituye la C-corp de Delaware durante el batch |
| Location | Por confirmar | Formato exacto "Córdoba, Argentina / San Francisco, USA" + razón |

---

## 2. Cronograma semanal

Semanas de lunes a domingo. Cada viernes: revisión de 30 minutos contra la columna "Criterio de listo". Si algo no está listo, se recorta alcance, no se corre la fecha.

### Semana 0 · sáb 19 – dom 20 sep · Arranque
- Leer la aplicación completa de YC y los consejos oficiales sobre video y demo.
- Definir agenda de entrevistas: lista de 15 nombres (los 2 arquitectos + 13 externos: constructoras woodframe, estudios, fabricantes de paneles, desarrollistas en Córdoba/Argentina).
- Crear carpeta `YC_W27/` con: `respuestas_borrador.md`, `entrevistas.md`, `metricas.md`.
- **Criterio de listo:** lista de contactos con canal y fecha objetivo para cada uno.

### Semana 1 · 21–27 sep · Descubrimiento + decisiones de fondo
**Evidencia**
- Entrevistas con los dos arquitectos sobre un proyecto reciente (guion: las 8 preguntas del plan §10). Registrar horas por tarea, qué se rehizo y por qué.
- Enviar 10 mensajes de contacto externo. Meta: 4 entrevistas agendadas para la semana 2.
**Producto**
- Especificar la demo (ver §3). Fijar el caso: ventana `Norte/O1` (4,15–5,15 m) ampliada 600 mm.
- Medir el estado actual: tiempo de `--check`, tiempo de regeneración en Blender, qué CSV cambian.
**Aplicación**
- Decidir **nombre provisorio** (shortlist de 5 el lunes, decisión el jueves). Comprar dominio.
- Decidir **cofounder**: ¿alguien ya está trabajando con dedicación real? Si no, la respuesta es "Yes, looking for a technical cofounder" y se explica el perfil. No se suma un cofundador nominal en 6 semanas.
- Decidir **ubicación**: dónde vive el fundador hoy y si se muda a San Francisco 3 meses para el batch (YC lo requiere). Escribir la explicación.
- **Criterio de listo:** nombre, dominio, decisión de cofounder y ubicación escritos en `respuestas_borrador.md`. Dos entrevistas hechas y documentadas.

### Semana 2 · 28 sep – 4 oct · Construir el circuito
**Producto**
- Implementar en V06 el operador `modificar_abertura(id, delta)` que edita la tupla de la abertura, regenera la escena y escribe los CSV.
- Implementar `diff_piezas(antes, después)`: piezas modificadas / nuevas / eliminadas por ID, con dimensiones antes → después. Salida: tabla en consola + HTML.
- Marcar en Blender las piezas del diff (material rojo / verde / fantasma), como en la lámina 11 del deck.
**Evidencia**
- 4 entrevistas externas. Al cierre de cada una, pedir: "¿Probarías esto en un proyecto tuyo la semana que viene? ¿Qué proyecto?".
- Seleccionar 2–3 candidatos a usuarios piloto.
**Aplicación**
- Primer borrador completo de todas las respuestas de texto (en español, ver §5). Sin pulir.
- **Criterio de listo:** el comando cambia la ventana y muestra el diff sin intervención manual. 6 entrevistas acumuladas. Borrador v1 completo.

### Semana 3 · 5–11 oct · Demo usable y primeros usuarios
**Producto**
- Panel en Blender (N-panel) con: selector de abertura, campos ancho/alto/posición, botón "Aplicar", lista de piezas afectadas, botón "Exportar paquete" (CSV + render + diff HTML).
- Segundo caso fuera de Angus Ranch: cargar una planta simple de uno de los entrevistados (una planta ortogonal, 4–6 muros) y correr el mismo flujo. Este es el dato que más pesa: "funciona en una casa que no es la nuestra".
- Fallback si el panel no llega: el flujo por línea de comando + video igual demuestra el circuito.
**Evidencia**
- Sesión guiada con el usuario piloto 1: él opera, nosotros observamos. Cronometrar. Registrar toda asistencia.
- Proponer a 1–2 pilotos una **prueba paga pequeña** (USD 200–400 por proyecto delimitado, según plan §9) o, si no, una carta de intención con alcance y precio orientativo.
**Aplicación**
- Landing de una página (Vercel): titular en 50 caracteres, 3 frases, video demo (cuando exista), imagen del entramado, contacto. Subir el deck como enlace secundario.
- **Criterio de listo:** un tercero usó el prototipo. Existe un caso externo a Angus Ranch corriendo. Landing publicada aunque sin video.

### Semana 4 · 12–18 oct · Videos
**Aplicación**
- **Video demo (≤ 3 min):** grabación de pantalla con voz, sin música ni títulos animados. Guion en §4. Tres tomas, elegir la mejor.
- **Founder video (1 min):** celular en horizontal, luz natural, sin guion leído. Nombre, qué hacemos en una frase, por qué nosotros, qué logramos hasta hoy. Grabar 5 veces, quedarse con la más natural.
- Traducir las respuestas al inglés. Cortar cada respuesta al 60 % de su largo.
**Evidencia**
- Usuarios piloto 2 y 3. Cerrar el registro de métricas: horas antes/después en el mismo alcance, correcciones necesarias, asistencia dada.
- Pedir feedback escrito a cada usuario (2–3 frases citables con nombre y rol, con permiso).
**Producto**
- Congelar funcionalidades. Solo corrección de errores encontrados por los pilotos.
- **Criterio de listo:** dos videos grabados y bajo 100 MB. Respuestas en inglés v2. 3 usuarios con datos.

### Semana 5 · 19–25 oct · Revisión externa
- Enviar la aplicación completa (texto + videos) a 3 personas para lectura crítica: un fundador que haya aplicado a YC o programa similar, un profesional del rubro y alguien que no conozca el proyecto. Pregunta única: "¿Qué no entendiste y qué no te creíste?".
- Reescribir según feedback. Regla: cada respuesta debe poder leerse en menos de 20 segundos.
- Actualizar el plan de negocios a v0.2 con los números reales de entrevistas y pilotos (reemplaza hipótesis por respuestas: quién compra, qué trabajo ahorra, cuánto pagaría).
- Cargar todo en el formulario de YC como borrador (guardar sin enviar).
- **Criterio de listo:** tres revisiones incorporadas. Formulario cargado al 100 %.

### Semana 6 · 26 oct – 1 nov · Cierre
- Lunes 26: relectura completa en voz alta. Verificar coherencia de números entre respuestas, landing y deck.
- Martes 27: revisar videos una vez más (audio, duración, tamaño). Probar el enlace del producto desde otro dispositivo.
- **Viernes 30 de octubre: enviar.**
- 31 oct – 2 nov: buffer. Si aparece un dato nuevo relevante (un pago, un usuario más), editar la aplicación enviada.

---

## 3. Especificación de la demo (lo que hay que construir)

**Nombre interno:** "Un cambio, todas las piezas".

**Estado actual que lo hace posible:** en `angus_ranch_V06_casa_y_terreno.py`, `build_walls()` declara cada muro con sus aberturas como tuplas `(inicio, fin, antepecho, dintel, tipo)`. `wall()` genera soleras, montantes comunes, kings, trimmers, doble header (220 o 300 mm según luz), antepecho y cripples a partir de esas tuplas. Los IDs de piezas se derivan del nombre del muro y del índice de abertura (`Norte/O1_Header_0`). `timber_inventory()` y `schedule()` regeneran despiece, cotización y plan de cortes. Por lo tanto el circuito ya existe en forma de script; falta exponerlo como operación y mostrar la diferencia.

**Alcance mínimo (semanas 2–3):**
1. `operaciones.py`: `listar_aberturas()`, `modificar_abertura(id, nuevo_inicio, nuevo_fin, nuevo_antepecho, nuevo_dintel)` con validación (espacio de jamba, solapes, altura bajo cubierta: las mismas aserciones que ya existen en `wall()`).
2. `diff.py`: compara `01_piezas_individuales.csv` antes y después por ID. Clasifica: sin cambio / modificada (dimensión o posición) / nueva / eliminada. Suma m³ y cantidad de tablas afectadas en `03_cotizacion_tablas_stock.csv`.
3. Panel Blender con formulario y botón. Piezas del diff coloreadas. Botón "Exportar paquete" que guarda render + CSV + `diff.html` en una carpeta con fecha.
4. Estados por pieza: `comprobado_por_reglas` / `pendiente_calculo` (por ejemplo, header con luz > 1,8 m marca `pendiente_calculo`, según plan §5).

**Caso externo (semana 3):** una planta de un entrevistado, modelada solo con `wall()` y aberturas. Sin muebles, sin terreno. El objetivo es correr `modificar_abertura` sobre una casa ajena.

**Lo que NO se construye ahora:** interfaz propia fuera de Blender, asistente conversacional con LLM en vivo, cálculo estructural, fundaciones, varias plantas. Si sobra tiempo, el "asistente" se simula con un campo de texto que acepta comandos fijos (`ampliar O1 600`), pero es opcional.

---

## 4. Guiones

### Video demo (≤ 3 minutos)
1. **0:00–0:20** Pantalla: planta de Angus Ranch en Blender con el entramado visible. Voz: "Esto es una casa woodframe. Cada una de sus 828 piezas tiene un identificador y sale de un mismo modelo."
2. **0:20–0:50** Seleccionar la ventana Norte O1. Abrir panel. Cambiar ancho de 1.000 a 1.600 mm. Aplicar.
3. **0:50–1:30** Mostrar la regeneración: header más largo en rojo, montante convertido en cripples en verde, montante eliminado fantasma. Leer el diff: "7 piezas afectadas; el header pasa a 1,89 m y queda marcado para cálculo".
4. **1:30–2:10** Abrir `Computo_madera` regenerado: la cotización cambió; señalar la fila que cambió. "Esto antes eran tres archivos distintos y una tarde de trabajo."
5. **2:10–2:40** Correr el mismo cambio sobre la planta del caso externo. "No depende de nuestra casa."
6. **2:40–3:00** Qué sigue: pilotos con [N] estudios, [X] horas ahorradas medidas. Cerrar con el nombre y la URL.

### Founder video (1 minuto)
- "Soy [nombre], de Córdoba, Argentina. Hago [rol/profesión] hace [N] años."
- "Estoy construyendo [nombre]: una herramienta para que estudios y constructoras woodframe modifiquen una casa y todas sus piezas, planos y cantidades se actualicen solas."
- "Empecé porque [origen personal: diseñando mi propia casa / trabajando en X, perdí semanas rehaciendo información cada vez que cambiaba una ventana]."
- "Hoy tenemos un modelo de 828 piezas identificadas, [N] profesionales probándolo y [dato de progreso]."
- "Aplicamos a YC porque [una razón concreta]."
- Sin editar. Sin música. Mirar a cámara.

---

## 5. Borradores de respuesta (v0, en español; se traducen en semana 4)

Todo lo que está entre corchetes hay que confirmarlo o medirlo. Lo que no está entre corchetes sale del plan v0.1 o del código.

**Describe what your company does in 50 characters or less.**
Opciones a probar en entrevistas (¿cuál entienden a la primera?):
- "Cambia el diseño; la casa woodframe se actualiza." (49)
- "Diseño woodframe que actualiza todas sus piezas." (48)
- "Casas woodframe editables pieza por pieza." (42)

**What is your company going to make?**
Software para estudios y constructoras que diseñan viviendas woodframe de forma recurrente. El usuario edita la planta y las aberturas; el sistema regenera el entramado dentro de reglas constructivas definidas, mantiene un identificador estable por pieza y actualiza vistas, detalles, listados y cantidades. Hoy: prototipo sobre Blender con [N] piezas identificadas, despiece y plan de cortes regenerables, y una operación de cambio de abertura con diferencia de piezas. Después del MVP: más sistemas, documentación más profunda, adaptación por empresa y mercado.

**Who writes code / non-founder work?**
[Nombre] escribe todo el código. Python sobre Blender (bpy), CSV/JSON y HTML. Uso intensivo de herramientas de IA para programar: [Cursor / Codex / Claude / GPT: confirmar cuáles]. Ninguna parte fue hecha por no fundadores. [Si hubo un desarrollador contratado o un arquitecto que aportó reglas: decirlo con nombre de rol y alcance.]

**Are you looking for a cofounder?**
[Decisión de semana 1.] Si es sí: "Sí. Busco un cofundador técnico con experiencia en geometría computacional o herramientas CAD/BIM, idealmente con contacto con construcción en madera. Hoy el desarrollo está a mi cargo con apoyo de IA; la responsabilidad técnica necesita una persona dedicada."

**How far along are you?**
Prototipo funcional sobre una vivienda de 164 m²: 828 piezas con ID, 24 headers, 100 anclajes, 13 vistas por capas, despiece, cotización de tablas y plan de cortes regenerables desde la geometría. Una operación de modificación de abertura que regenera el entramado y muestra la diferencia de piezas y cantidades. [Caso externo: 1 vivienda de un tercero procesada.] [Usuarios: N profesionales, N proyectos, N horas medidas.] [Ingresos: piloto pago de USD X / carta de intención.]

**How long have you been working on this? Full-time?**
[Fecha de inicio del proyecto Angus Ranch y del plan; porcentaje de dedicación real; desde cuándo full-time si aplica.] Ser exacto.

**Tech stack.**
Blender 4.x con Python (bpy) como motor geométrico y de prototipado; modelo del proyecto en Python con IDs estables; salidas CSV/JSON/HTML; GLB para visores web. IA: [herramientas de código]; para el asistente de producto se prevé un LLM que llame operaciones definidas y validadas, sin generar geometría libre. Próximo: visor web (three.js) y servicio de reglas separado de la interfaz.

**Are people using your product? / Revenue?**
Responder con el dato real al 30/10. Si "Yes", una línea: "[N] profesionales en [N] proyectos; [X] horas ahorradas medidas sobre el mismo alcance."

**Why this idea? Domain expertise? How do you know people need it?**
[Origen personal: confirmar. Hipótesis: el fundador diseñó/está construyendo Angus Ranch en Córdoba y vivió el costo de cada cambio.] Evidencia a completar: [N] entrevistas, citas concretas, horas que se pierden por cambio, quién decide comprar. Honestidad: "La hipótesis de problema la estamos probando; hasta hoy [dato]".

**Competitors. What do you understand that they don't?**
Higharc (diseño-configuración-documentación residencial, Serie C de USD 95 M en junio 2026), Chief Architect, hsbcad, ARKANCE Be.Smart, y el flujo actual del cliente (CAD + planillas + revisión manual). Lo que entendemos: [formular con evidencia de entrevistas]. Hipótesis: los equipos pequeños que repiten un sistema no necesitan una suite de fabricación; necesitan que un cambio no rompa el resto, con su propio sistema constructivo configurado. La ventaja se construye en el catálogo de soluciones comprobadas y el modelo de dependencias, no en el acceso a IA.

**How do you make money? How much?**
Suscripción por organización (USD 100–250/mes equipos pequeños; 300–600 mayor volumen) más piloto pago por proyecto (USD 200–600). Escala: 250 organizaciones × USD 250 = USD 750 k anualizados; 3.000 × USD 450 = USD 16 M. Expansión por más sistemas, módulos y mercados. Los números son hipótesis a validar en pilotos.

**Other ideas considered.**
1. Cómputo y cotización de madera como herramienta independiente (ya existe `Computo_madera_V06`). 2. Biblioteca verificada de detalles woodframe con reglas ejecutables, vendida a fabricantes de paneles. 3. Marketplace de aserraderos con pedidos generados desde el modelo. [Agregar las propias.]

**Location.**
"[Ciudad], Argentina / [San Francisco, USA o Ciudad, Argentina]". Explicación: acceso a clientes iniciales en Argentina (woodframe en crecimiento, escasas estadísticas según INTA), disposición a mudarse durante el batch, y [razón para la base posterior].

**Legal entity / investment / fundraising.** No / No / No. (Sin justificar de más.)

**What convinced you to apply? How did you hear?**
[Respuesta personal, corta y verdadera.]

---

## 6. Métricas que tienen que existir el 30 de octubre

| Métrica | Mínimo | Objetivo |
| --- | --- | --- |
| Entrevistas documentadas (externas al círculo cercano) | 8 | 12 |
| Profesionales que operaron el prototipo | 2 | 3 |
| Proyectos reales procesados (además de Angus Ranch) | 1 | 2 |
| Horas medidas: flujo actual vs. prototipo, mismo alcance | 1 comparación | 3 comparaciones |
| Compromiso económico (pago o carta de intención) | 1 carta | 1 pago |
| Citas con nombre y permiso | 2 | 3 |

---

## 7. Riesgos de estas seis semanas y respuesta

| Riesgo | Señal | Respuesta |
| --- | --- | --- |
| La demo se agranda | Semana 3 sin panel funcionando | Congelar en línea de comando + video; el circuito importa más que la interfaz |
| Nadie externo responde | Semana 2 con menos de 3 entrevistas | Pedir presentaciones a los dos arquitectos; ir a obras y aserraderos en persona; ampliar a Buenos Aires/Rosario |
| Los usuarios piloto no aparecen a tiempo | Semana 4 sin sesiones | Responder "No" con honestidad y mostrar el caso externo procesado por nosotros con su planta |
| Perfeccionismo en videos | Más de 5 tomas | Elegir la más natural y seguir; YC prefiere crudo a producido |
| Respuestas largas | Más de 20 segundos de lectura | Cortar al 60 %; una idea por respuesta |
| Decisión de cofounder sin resolver | Semana 2 sin definición | Responder que se busca; describir perfil; no inventar |

---

## 8. Rutina

- **Lunes 9:00:** plan de la semana (30 min), tres entregables máximo.
- **Miércoles:** una demostración a alguien externo, aunque sea de 10 minutos.
- **Viernes 17:00:** revisión contra criterios de listo; actualizar `metricas.md`; decidir recortes.
- **Diario:** una línea en `entrevistas.md` o `metricas.md`. Lo que no se registra no existe el 30/10.

---

## 9. Preguntas abiertas que condicionan respuestas (resolver en semana 1)

1. ¿Sos fundador único hoy? ¿Alguien más tiene dedicación real (horas semanales) al proyecto?
2. ¿Escribís el código vos, con IA? ¿Con qué herramientas exactamente? ¿Hubo aportes de terceros en código o reglas?
3. ¿Dónde vivís hoy y estás dispuesto a estar en San Francisco enero–marzo 2027?
4. ¿Cuál es tu vínculo con la construcción en madera? ¿Angus Ranch es tu propia casa?
5. ¿Desde cuándo trabajás en esto y qué porcentaje de tu tiempo le dedicás?
6. ¿Tenés capacidad de invertir USD 500–1.500 en estas seis semanas (dominio, hosting, algún piloto asistido, traslados a entrevistas)?
7. ¿Los dos arquitectos aceptarían ser usuarios piloto con un proyecto real en octubre?
