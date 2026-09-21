# Plan de negocios — Plataforma de diseño y desarrollo woodframe

**Versión 0.1 · 18 de septiembre de 2026 · Documento de trabajo**

**Nombre comercial: pendiente.** Angus Ranch es el caso de desarrollo inicial; no se presupone que sea la marca del producto.

Este plan propone decisiones para comenzar y explicita las hipótesis que necesitan evidencia. No existe todavía validación comercial, una estimación comprobada del mercado ni un presupuesto contratado. Los importes se expresan en USD de referencia para comparar escenarios; no son cotizaciones ni recomendaciones de inversión.

## 1. Tesis del negocio

Crear una plataforma que permita a profesionales y constructores diseñar viviendas woodframe y desarrollar su definición constructiva con asistencia de IA, automatización y un modelo único del proyecto.

La promesa inicial es **reducir las horas necesarias para transformar y modificar un diseño dentro de un sistema constructivo definido**, manteniendo consistentes sus vistas, componentes y documentación. La promesa de largo plazo es representar la vivienda completa como un conjunto coordinado de piezas y sistemas individualizables, verificables y cuantificables.

La oportunidad comercial depende de comprobar tres cosas: que el trabajo repetitivo sea suficientemente costoso, que el sistema lo reduzca sin trasladar ese esfuerzo a correcciones y que los clientes vuelvan a usarlo en proyectos posteriores.

**Misión propuesta:** permitir que más equipos desarrollen viviendas woodframe bien resueltas, dedicando más tiempo al diseño y menos a reconstruir información técnica en cada proyecto.

**Visión a cinco años:** una plataforma utilizada de manera recurrente para diseñar, coordinar y documentar viviendas, con paquetes constructivos adaptables a distintos mercados y empresas. Este horizonte expresa dirección, no un calendario comprometido de funcionalidades.

**Decisiones adoptadas para esta versión:**

- Empezar con un MVP de alcance técnico explícito.
- Concentrar el valor en diseño y desarrollo constructivo.
- Mantener identificación y cantidades de componentes en la base del modelo.
- Posponer proveedores, precios, compras y órdenes de pedido.
- Incorporar conocimiento de literatura al trabajo técnico; la interfaz no necesita presentar bibliografía. Conservar internamente el origen y la versión de las reglas facilitará su mantenimiento. La gestión de licencias no se incorpora como frente de trabajo de esta etapa.
- Aprovechar el contacto ya iniciado con dos arquitectos; su participación y disponibilidad todavía deben acordarse.
- Evaluar inversión externa después de obtener evidencia del producto y del negocio.

## 2. Problema, usuario y comprador

La hipótesis de problema es que, en proyectos woodframe pequeños y medianos, una parte significativa del trabajo se dedica a trasladar decisiones entre planos, modelos, detalles y listados, y a revisar sus consecuencias después de cada cambio.

Necesitamos comprobar dónde ocurre ese trabajo: diseño inicial, adaptación de modelos repetidos, definición de paneles, documentación, coordinación o revisiones. La primera versión debe atacar el punto donde confluyan frecuencia, costo y posibilidad real de automatización.

**Cliente inicial propuesto:** constructoras y estudios que desarrollan viviendas woodframe de manera recurrente y tienen un sistema de trabajo relativamente repetible. Argentina se adopta como hipótesis de entrada por cercanía y acceso a contactos; el mercado específico se decidirá con evidencia.

| Segmento | Usuario cotidiano | Comprador probable | Encaje inicial |
| --- | --- | --- | --- |
| Constructora woodframe con equipo técnico pequeño | Proyectista o arquitecto | Dueño o responsable técnico | Prioridad alta si adapta modelos con frecuencia |
| Estudio especializado en woodframe | Arquitecto o dibujante técnico | Socio del estudio | Prioridad alta si produce documentación recurrente |
| Fabricante de paneles | Diseñador de producción | Responsable industrial | Etapa posterior: requiere más detalle de fabricación |
| Desarrollista que terceriza proyecto | Coordinador de proyectos | Dueño o director | Puede comprar, pero necesita participación de sus proyectistas |
| Particular que diseña su propia vivienda | Propietario | Propietario | No es el segmento inicial: menor recurrencia y mayor necesidad de acompañamiento |

Como filtro de entrevistas se explorarán organizaciones que desarrollen aproximadamente 5–30 viviendas por año. Es un rango de selección propuesto, no un dato observado del mercado. La frecuencia y similitud entre proyectos importan más que el tamaño de la empresa.

El cliente compra productividad y continuidad de información. La IA es parte de cómo se entrega ese beneficio; no basta como argumento de compra.

## 3. Propuesta de valor y evidencia necesaria

**Propuesta comercial inicial:** “Diseñá y modificá viviendas woodframe dentro de tu sistema constructivo, con un modelo por capas que actualiza componentes y documentación y te guía sobre las definiciones pendientes”.

La aplicación debería permitir que un profesional:

1. Inicie una vivienda desde una configuración compatible con el sistema.
2. Ajuste distribución, dimensiones y aberturas.
3. Observe las consecuencias constructivas de cada cambio.
4. Revise entramados y detalles recurrentes por capas.
5. Obtenga un paquete consistente para continuar el trabajo profesional.

La meta del piloto es reducir al menos un 30% las horas totales del flujo elegido, incluyendo preparación, operación, revisión y corrección. Es un umbral propuesto para decidir si continuar; no una prestación demostrada.

La comparación se hará con el mismo alcance y nivel de calidad. No se comparará un anteproyecto simplificado producido por la app con un proyecto ejecutivo completo realizado manualmente.

Los beneficios secundarios a medir son menos discrepancias entre versiones, incorporación más rápida de cambios y menor tiempo hasta una primera alternativa útil.

## 4. MVP: alcance comercial y técnico

El MVP es una herramienta de desarrollo de proyecto para profesionales. Su salida será un **paquete de definición arquitectónica y constructiva parcial, con alcance y pendientes explícitos**. La casa completa es la dirección del producto, no el entregable de la primera versión.

**Dominio de partida propuesto:** vivienda unifamiliar de una planta; planta ortogonal; terreno modelado con condiciones simples; una familia de muros y un tipo inicial de cubierta; catálogo acotado de aberturas y encuentros. Los límites de dimensiones y soluciones se fijarán con especialistas antes de automatizar decisiones técnicas.

| Incluido | Resultado esperado |
| --- | --- |
| Inicio guiado del proyecto | Datos básicos, configuración y decisiones pendientes |
| Edición de planta acotada | Cambios de dimensiones, muros y aberturas admitidos |
| Visor 3D por capas | Relación clara entre diseño y solución constructiva |
| Generación de entramado dentro de reglas definidas | Componentes y relaciones reproducibles |
| Biblioteca pequeña de encuentros | Detalles aplicables a los casos soportados |
| Historial y deshacer | Comparación y recuperación de versiones |
| Asistente contextual | Orientación sobre la próxima decisión y efectos del cambio |
| Identificación de piezas | Tipo, dimensiones, ubicación y pertenencia |
| Cantidades del alcance modelado | Control de consistencia, sin circuito de compras |
| Exportación básica | Vistas, detalles seleccionados, listado de componentes y pendientes |

Quedan para etapas posteriores: varias plantas, geometrías libres, resolución integral de fundaciones, cálculo estructural general, instalaciones completas, documentación de fabricación industrial, aprobación automática, importación universal de planos y compras.

Las fundaciones pueden aparecer como referencia geométrica y las instalaciones como zonas reservadas si eso mejora el flujo. No se presentarán como disciplinas resueltas. Los elementos que requieran dimensionamiento podrán utilizar parámetros revisados o permanecer pendientes, según el alcance pactado.

**Criterios propuestos de aceptación del MVP:**

- Completar al menos tres viviendas distintas dentro del dominio soportado, incluyendo casos externos a Angus Ranch.
- Ejecutar cambios de abertura, ambiente y dimensión exterior sin reconstrucción manual del proyecto por el desarrollador.
- Mantener coincidencia entre piezas únicas y listados del alcance modelado; excluir copias de presentación.
- Guardar, reabrir y recuperar una versión previa.
- Señalar entradas fuera de alcance y verificaciones desactualizadas.
- Permitir que un usuario complete el flujo con capacitación acotada; registrar toda asistencia necesaria.
- Exportar un paquete que el profesional pueda revisar y utilizar para continuar su trabajo.

No es necesario que la primera versión automatice todo para que sea útil. Sí debe completar un trabajo delimitado de principio a fin.

## 5. Experiencia de uso

La interfaz combinará planta editable, vista 3D por capas y asistente. La conversación permite expresar intención; los controles visuales permiten precisión.

Ejemplo: el usuario selecciona una ventana y pide ampliarla. El sistema prepara el cambio, muestra qué elementos se modifican, aplica las reglas disponibles y señala qué necesita revisión. La aceptación del cambio produce una nueva versión coherente del proyecto.

La secuencia de preguntas será contextual. No debe exigir resolver todos los detalles antes de explorar una distribución, ni ocultar decisiones que condicionan el desarrollo posterior.

Cada elemento o sistema tendrá un estado entendible: propuesto, pendiente de datos, comprobado por las reglas disponibles o revisado por una persona identificada. Una modificación relevante invalida los estados afectados.

La prueba de usabilidad debe medir si el usuario entiende qué cambió, qué puede seguir haciendo y qué falta resolver, sin depender de una explicación del equipo fundador.

## 6. Estrategia tecnológica y activos existentes

La revisión de Angus Ranch V06 muestra una base experimental: generación geométrica, organización por capas, identificadores, despiece y cómputos. Su documentación también identifica pendientes y advierte que los cambios manuales en Blender no regresan al script. Es evidencia de factibilidad parcial, no evidencia de un MVP terminado.

La arquitectura propuesta separa cinco responsabilidades:

1. **Modelo del proyecto:** muros, ambientes, aberturas, piezas, sistemas y relaciones, con identificadores estables.
2. **Reglas constructivas:** condiciones, parámetros, alcance y resultados verificables.
3. **Generación geométrica y documental:** representaciones que salen del mismo modelo.
4. **Interfaz:** edición, visualización, historial y revisión.
5. **Asistente:** interpretación de intenciones y ejecución de operaciones permitidas.

El asistente no debe modificar arbitrariamente la geometría mediante código improvisado en cada conversación. Debe llamar operaciones definidas, validar parámetros y devolver cambios revisables.

**Decisión provisional sobre Blender:** aprovecharlo como entorno de prototipado y generación visual. Evaluar con una prueba corta si el piloto usa una interfaz simplificada dentro de Blender o una interfaz propia. Evitar invertir meses en un editor completo antes de comprobar el flujo de valor.

Comparar las opciones usando el mismo ejercicio: abrir una casa, modificar una abertura, inspeccionar el entramado, deshacer y exportar. Medir tiempo de aprendizaje, precisión, esfuerzo de desarrollo y continuidad de datos. La decisión debe tomarse al final de la etapa inicial, no convertirse en una investigación permanente.

El modelo del proyecto y las reglas deben poder sobrevivir a un cambio de interfaz. La interoperabilidad se desarrollará según los formatos que realmente necesiten los pilotos, evitando prometer compatibilidad total desde el inicio.

## 7. Competencia y diferenciación

La investigación de sitios oficiales confirma que ya existen soluciones relevantes. Las capacidades comerciales publicadas no se han verificado mediante pruebas propias.

| Referencia | Oferta relevante | Implicación estratégica |
| --- | --- | --- |
| [Higharc](https://www.higharc.com/) | Conecta diseño residencial, configuración, estimación y documentación | La visión integral ya tiene competencia directa |
| [Chief Architect](https://www.chiefarchitect.com/products/home-design/premier/) | Modelado residencial, materiales y documentación constructiva | Modelar una casa y producir listados no basta como diferenciación |
| [hsbcad](https://www.hsbcad.com/) | Herramientas para diseño, fabricación y montaje de construcción industrializada | La profundidad de producción es un terreno especializado |
| [ARKANCE Be.Smart](https://arkance.world/global/products/be-smart?showpopup=true) | Ecosistema de herramientas BIM; la oferta de wood framing de Agacad remite a esta plataforma | Debe evaluarse como alternativa de automatización en flujos BIM |
| Flujo actual del cliente | Herramientas conocidas, planillas, detalles propios y revisión manual | El costo de cambiar de hábito puede superar el ahorro percibido |

La hipótesis de diferenciación combina acompañamiento paso a paso, alcance constructivo claro, configuración del sistema del cliente y continuidad entre modificaciones y entregables. Cada una debe probarse frente a alternativas reales. No se presume que los competidores carezcan de estas capacidades.

El activo defendible crecería en el catálogo de soluciones comprobadas, el modelo de dependencias, los casos de prueba, la experiencia de edición y la integración en el trabajo recurrente. Tener acceso a un modelo de IA o a libros no constituye por sí solo una ventaja sostenible.

Higharc anunció una ronda Serie C de USD 95 millones en junio de 2026. Es evidencia de que inversores financian esta categoría, no una valoración comparable para este proyecto ni una prueba de demanda local. [Anuncio oficial](https://www.higharc.com/newsroom/higharc-95m-series-c-for-homebuilding-ai).

## 8. Mercado y ambición de escala

No se asigna un tamaño de mercado sin identificar compradores. El gasto total en construcción no es el mercado accesible de este software.

Se construirá una estimación de abajo hacia arriba: cantidad de organizaciones con actividad compatible × proporción alcanzable × ingreso anual plausible por organización. Los contactos deben deduplicarse por empresa; varios arquitectos de la misma organización no son varios clientes.

Una publicación de INTA señala la escasez de estadísticas sobre construcción en madera en Argentina. Esto refuerza la necesidad de elaborar una base propia y contrastar fuentes, sin convertir una estimación de participación constructiva en cantidad de compradores de software. [INTA](https://www.argentina.gob.ar/inta/tecnologias/aplicacion-en-madera-de-eucalipto-para-la-construccion).

**Trabajo inicial:** construir una lista de 50 organizaciones identificadas, segmentarlas y registrar frecuencia de proyectos, sistema constructivo, responsable técnico y herramientas. La lista servirá para prospección y aprendizaje; no se extrapolará automáticamente a todo el mercado.

Los siguientes escenarios muestran la escala de ingresos necesaria, no el tamaño observado del mercado ni una previsión de captación:

| Organizaciones pagas | Ingreso mensual medio | Ingreso recurrente anualizado |
| ---: | ---: | ---: |
| 50 | USD 150 | USD 90.000 |
| 250 | USD 250 | USD 750.000 |
| 1.000 | USD 350 | USD 4.200.000 |
| 3.000 | USD 450 | USD 16.200.000 |

El ingreso recurrente anualizado se calcula como clientes activos × ingreso mensual medio × 12. No equivale al ingreso efectivamente cobrado durante un año de crecimiento.

A USD 250 mensuales, superar USD 1 millón anualizado requiere 334 organizaciones; superar USD 10 millones requiere 3.334. Esto obliga a evaluar pronto si el segmento inicial puede sostener el negocio y qué expansión haría falta para una empresa de mayor escala.

La expansión puede ocurrir por más organizaciones, mayor uso por organización, módulos adicionales y nuevos mercados. Cada nuevo mercado exige validar su propio paquete constructivo, distribución y soporte. Traducir la interfaz no basta.

## 9. Modelo de ingresos y prueba de precios

La propuesta inicial es cobrar por organización, con límites claros de proyectos activos y colaboradores. La suscripción ofrece continuidad; una modalidad por proyecto puede servir a clientes con trabajo esporádico.

**Hipótesis de precios para investigar, no tarifas de lanzamiento:**

| Modalidad | Rango experimental | Qué permite aprender |
| --- | --- | --- |
| Piloto pago y acompañado | USD 200–600 por proyecto delimitado | Si existe compromiso económico por el resultado |
| Suscripción de equipo pequeño | USD 100–250 mensuales | Si el uso recurrente sostiene una cuota |
| Equipo con mayor volumen | USD 300–600 mensuales | Si colaboración y reutilización justifican mayor ingreso |
| Configuración específica | Presupuesto separado | Cuánto trabajo de incorporación exige cada sistema |

No se lanzarán todos los planes simultáneamente. Se probará una oferta sencilla y se revisará según uso y objeciones. Los importes deben contrastarse con capacidad de pago local y ahorro observado.

Ejemplo de valor: si un equipo reduce 20 horas mensuales y valora internamente esas horas a USD 15, el ahorro de capacidad es USD 300. Una cuota de USD 150 consumiría la mitad de ese beneficio. Estas cifras son hipotéticas; además, liberar horas no siempre reduce gastos en efectivo. Hay que preguntar si permite producir más, entregar antes o evitar tercerización.

Durante los pilotos se registrará cuánto del precio paga software y cuánto acompañamiento. Los ingresos por servicios no se contarán como ingresos recurrentes del producto.

## 10. Validación con los dos arquitectos y clientes externos

Los dos arquitectos ya contactados son el primer acceso al rubro. Se propondrá que ayuden a reconstruir el flujo profesional, revisar entregables y detectar casos representativos. No se asume que ya aceptaron ser asesores, socios ni revisores habituales.

Preguntas para trabajar sobre un proyecto reciente:

1. ¿Qué entregables producen y quién los utiliza?
2. ¿Qué tareas consumieron más horas y cuáles se repitieron?
3. ¿Qué cambió después de la primera versión y qué hubo que rehacer?
4. ¿Qué resuelven con bibliotecas o plantillas y qué requiere criterio nuevo?
5. ¿Qué información debería conservar una herramienta para resultar confiable?
6. ¿Qué resultado parcial usarían en un proyecto real?
7. ¿Quién decide comprar software y con qué presupuesto?
8. ¿Qué proyecto próximo permitiría una prueba y quién revisaría el resultado?

La opinión favorable de amigos no se contará como validación comercial. Se buscarán entre 8 y 12 entrevistas totales, con participantes externos al círculo cercano y representación de constructoras o responsables de compra.

**Diseño del piloto:** seleccionar un caso soportado; medir el flujo actual; procesar el mismo trabajo con el producto; revisar con un profesional; registrar correcciones y asistencia; ofrecer continuidad paga. En las pruebas sucesivas se alternarán tareas o usarán casos equivalentes para reducir el efecto de aprendizaje.

Objetivo inicial: tres organizaciones piloto independientes, cinco proyectos completados entre ellas y al menos dos decisiones de pago o renovación. Son metas de aprendizaje, no tracción existente. Esta muestra permite decidir el siguiente paso, pero no demuestra retención de mercado.

## 11. Captación y ventas

La venta inicial será conducida por el fundador. Los contactos de los arquitectos pueden facilitar presentaciones; no se enviarán comunicaciones en su nombre sin acuerdo.

Secuencia propuesta: entrevista sobre un proyecto real → demostración sobre un caso compatible → piloto de alcance y precio acordados → revisión del resultado → suscripción o segundo proyecto pago.

El mensaje comercial debe mostrar una modificación concreta y su efecto sobre los entregables. “Ampliamos esta abertura y actualizamos el conjunto afectado” es más verificable que “IA que diseña casas”.

Los primeros canales serán referencias profesionales, contacto directo con organizaciones identificadas y demostraciones en ámbitos especializados. La publicidad paga se evaluará después de conocer conversión y permanencia.

Como embudo de trabajo, se puede planificar contactar 40 organizaciones calificadas, lograr 12 conversaciones, seleccionar cinco candidatas y activar tres pilotos. Son objetivos operativos, no tasas históricas. Se registrará cada abandono y su causa.

La primera incorporación puede ser asistida. Sin embargo, el tiempo del fundador y del soporte debe disminuir con cada nueva organización. Si cada cliente requiere desarrollo distinto, habrá que revisar el segmento o reconocer un modelo de servicios.

## 12. Equipo y forma de operar

| Responsabilidad | Cobertura inicial propuesta |
| --- | --- |
| Producto, entrevistas y ventas | Fundador, con dedicación semanal explícita |
| Modelo de datos, geometría y aplicación | Un responsable técnico con experiencia pertinente |
| Flujo profesional y revisión de entregables | Arquitecto asesor con dedicación acordada |
| Reglas estructurales y límites de aplicación | Especialista en estructuras de madera por alcance |
| Interfaz y pruebas de uso | Apoyo puntual de diseño de producto |

Los roles pueden combinarse, pero no conviene diluir la responsabilidad técnica ni asumir que un único desarrollador domina construcción, geometría e interfaz por igual.

Antes de sumar socios o colaboradores permanentes, definir dedicación, remuneración, entregables, decisiones y continuidad del trabajo. No se propone una distribución societaria sin conocer aportes y compromisos.

Rutina recomendada: revisión semanal de producto y aprendizaje; demostración quincenal con un usuario; evaluación mensual de horas, caja y avance frente a criterios. Mantener una lista corta de decisiones y evitar acumular funcionalidades sin una hipótesis comercial.

## 13. Hoja de ruta y presupuesto inicial

Los plazos son hipótesis de planificación condicionadas a disponibilidad del equipo y complejidad encontrada. El MVP utilizable se estima inicialmente en 4–6 meses con dedicación técnica sostenida. Los primeros 90 días buscan demostrar el flujo y activar pruebas, no prometer el producto completo.

| Etapa | Plazo orientativo | Entregable | Condición para avanzar |
| --- | --- | --- | --- |
| Descubrimiento y especificación | Semanas 1–4 | Entrevistas, flujo elegido, alcance y comparación de interfaces | Dolor repetido, casos disponibles y compradores identificados |
| Prototipo funcional | Semanas 5–8 | Modelo editable y una modificación propagada | Funciona también en un caso externo a Angus Ranch |
| Prueba acompañada | Semanas 9–12 | Exportación, revisión y medición inicial | Usuarios completan el trabajo y reconocen valor concreto |
| MVP y pilotos pagos | Meses 4–6 | Guardado, historial, controles y flujo delimitado estable | Ahorro medido, calidad aceptable y primeros pagos |
| Repetición comercial | Meses 7–12 | Incorporación repetible y clientes que regresan | Menos asistencia por cliente y uso en proyectos nuevos |
| Expansión seleccionada | Después de esos hitos | Un módulo o mercado adicional | Núcleo estable y demanda demostrada |

**Presupuesto de caja propuesto para los primeros 90 días:**

| Rubro | Rango orientativo |
| --- | ---: |
| Desarrollo contratado o dedicación técnica remunerada | USD 9.000–18.000 |
| Arquitectura y revisión especializada | USD 2.000–5.000 |
| Diseño de interfaz y pruebas | USD 1.000–3.000 |
| Infraestructura y herramientas | USD 300–1.000 |
| Entrevistas, traslados y administración | USD 500–1.500 |
| Subtotal | USD 12.800–28.500 |
| Reserva del 20% | USD 2.560–5.700 |
| **Total orientativo** | **USD 15.360–34.200** |

Son asignaciones de planificación, no tarifas salariales verificadas. Excluyen sueldo del fundador, equipamiento nuevo y eventuales impuestos adicionales. Si el fundador programa o hay trabajo aportado, puede disminuir el desembolso, pero debe registrarse el costo económico de esas horas.

No se presupone que esta suma financie todo el MVP ni que haya fondos disponibles. Se propone autorizar internamente cada etapa por separado. Al final de la cuarta semana debe existir un presupuesto revisado con personas, horas y cotizaciones reales antes de comprometer la siguiente etapa.

## 14. Escenario financiero ilustrativo a tres años

Este escenario sirve para entender órdenes de magnitud. No es un pronóstico. Supone que se valida el producto, que se logra captar y retener organizaciones y que el equipo puede ampliar el alcance gradualmente. El año 1 comienza con el proyecto empresarial, no después del lanzamiento.

| Variable | Año 1 | Año 2 | Año 3 |
| --- | ---: | ---: | ---: |
| Organizaciones pagas promedio durante el año | 10 | 60 | 180 |
| Organizaciones pagas al cierre | 25 | 100 | 260 |
| Ingreso mensual medio por organización | USD 150 | USD 200 | USD 250 |
| Ingresos anuales de suscripción | USD 18.000 | USD 144.000 | USD 540.000 |
| Costos directos de prestación | 25% | 20% | 18% |
| Costos directos en USD | USD 4.500 | USD 28.800 | USD 97.200 |
| Margen bruto en USD | USD 13.500 | USD 115.200 | USD 442.800 |
| Gastos operativos fijos | USD 120.000 | USD 240.000 | USD 360.000 |
| **Resultado operativo simplificado** | **–USD 106.500** | **–USD 124.800** | **USD 82.800** |

Ingresos = organizaciones promedio × ingreso mensual medio × 12. Los promedios presuponen meses iniciales sin facturación y una trayectoria de crecimiento compatible; no se calculan a partir del número al cierre. Los ingresos recurrentes anualizados al cierre serían USD 45.000, USD 240.000 y USD 780.000 respectivamente, si se mantiene el ingreso mensual indicado.

Los costos directos incluyen infraestructura, IA y prestación o soporte atribuible al cliente. Los gastos fijos incluyen desarrollo, remuneración del fundador, gestión, ventas y administración, sin duplicar soporte incluido en costos directos. Los servicios de configuración y pilotos no recurrentes se excluyen de los ingresos de esta tabla. El presupuesto de 90 días forma parte del gasto del año 1; no se suma otra vez.

El modelo omite impuestos, financiación, inversiones en activos, diferencias de cambio y plazos de cobro. Por eso, el resultado operativo no equivale a flujo de caja. La pérdida operativa acumulada de los primeros dos años sería USD 231.300; con una reserva del 20%, USD 277.560 sería una referencia parcial de recursos, todavía insuficiente para fijar una necesidad exacta de financiación. Hace falta un flujo mensual y ajustar los rubros omitidos.

**Sensibilidad del año 3**, manteniendo USD 360.000 de gastos fijos y un margen bruto del 82%:

| Cambio | Resultado operativo anual |
| --- | ---: |
| 180 organizaciones promedio a USD 250 | USD 82.800 |
| 120 organizaciones promedio a USD 250 | –USD 64.800 |
| 180 organizaciones promedio a USD 175 | –USD 50.040 |

Con USD 30.000 mensuales de gastos fijos, USD 250 por organización y margen bruto del 82%, se necesitan aproximadamente **147 organizaciones activas** para cubrir la operación mensual. Es una relación aritmética bajo esos supuestos; no contempla costos nuevos al crecer.

La sensibilidad muestra dos riesgos centrales: un precio bajo puede impedir sostener el equipo y un servicio demasiado intensivo puede reducir el margen. Ambos deben medirse durante los pilotos.

## 15. Indicadores y criterios de decisión

La métrica principal propuesta es **cantidad de proyectos útiles completados y revisados por organizaciones que vuelven a utilizar el producto**. Las sesiones de chat o las imágenes generadas pueden ayudar a diagnosticar uso, pero no prueban valor comercial.

| Dimensión | Indicador | Señal inicial buscada |
| --- | --- | --- |
| Productividad | Horas totales frente al flujo actual | Reducción de al menos 30% en el alcance probado |
| Calidad | Correcciones e incidencias por proyecto | Sin inconsistencias críticas pendientes en la entrega del piloto |
| Activación | Tiempo hasta primer proyecto útil | Disminuye después de cada incorporación |
| Autonomía | Horas de asistencia por proyecto | Tendencia descendente sin deterioro de calidad |
| Compra | Pilotos que pagan o continúan pagando | Al menos dos decisiones económicas independientes |
| Recurrencia | Uso en un segundo proyecto disponible | Uso real más allá de la demostración |
| Economía | Margen después de prestación y soporte | Mejora al repetir el flujo |

La recurrencia se evaluará según el calendario de proyectos del cliente. Un mes sin un nuevo proyecto no implica automáticamente abandono. Se distinguirán organizaciones sin oportunidad de uso de aquellas que eligen otra herramienta.

Se registrará costo de adquisición incluyendo tiempo comercial del fundador. No se estimará valor de vida del cliente con pocas observaciones. Como ejemplo aritmético, a USD 250 mensuales y 82% de margen bruto, cada organización aporta USD 205 mensuales antes de gastos fijos; un costo de adquisición de USD 900 se recuperaría en unos 4,4 meses si permanece y paga. Ninguno de esos parámetros está validado.

**Reorientar o reducir alcance si:** el ahorro desaparece al revisar; el comprador valora solamente renders; cada proyecto requiere cambios de código; los clientes no regresan teniendo proyectos compatibles; o la personalización consume la mayor parte del ingreso. Una buena salida puede ser un complemento especializado o un servicio apoyado en software, si la evidencia favorece ese negocio.

## 16. Riesgos y respuesta operativa

| Riesgo | Señal temprana | Respuesta |
| --- | --- | --- |
| Intentar resolver la casa completa demasiado pronto | Módulos abiertos sin flujos terminados | Congelar el dominio y cerrar un entregable |
| Modelo visual convincente pero inconsistente | Cambios que dejan piezas o documentos desactualizados | Reglas reproducibles y pruebas de propagación |
| Dependencia de una única casa | Angus Ranch funciona y los casos externos fallan | Incorporar casos externos desde el prototipo |
| Error en la interpretación técnica | Salidas plausibles que no pasan revisión | Revisión especializada y límites explícitos |
| Mala experiencia de edición | Todo requiere chat o asistencia del desarrollador | Selección visual, cotas, historial y pruebas observadas |
| Demanda local insuficiente | Pocos compradores con recurrencia y presupuesto | Revisar segmento y expansión antes de escalar costos |
| Consultoría difícil de repetir | Trabajo específico creciente por cliente | Separar configuración reutilizable de desarrollo a medida |
| Dependencia de personas clave | Conocimiento sin registrar | Documentación, pruebas y responsabilidades claras |
| Baja continuidad de proyectos | Suscripciones interrumpidas entre trabajos | Evaluar cobro por proyecto o planes anuales según evidencia |
| Pérdida de trabajo o exposición de proyectos | Fallas de guardado o permisos | Historial, recuperación y control de acceso desde los pilotos externos |

## 17. Estrategia de financiación y crecimiento

La etapa actual busca comprar aprendizaje con un compromiso de caja controlado. No se propone iniciar una ronda ahora.

Una ronda posterior tendría sentido si existen: clientes que pagan y repiten; ahorro documentado; incorporación cada vez menos dependiente del fundador; claridad sobre alcance y limitaciones; y un conjunto identificable de clientes a captar.

Como referencia de madurez para evaluar inversión, se propone aspirar a 10–20 organizaciones pagas, varias cohortes con uso repetido y casos medidos fuera de la red personal. No es un requisito universal de inversores ni una garantía de financiación. Una solución industrial con contratos mayores podría justificar otro recorrido.

El capital debería financiar un hito concreto, como ampliar cobertura técnica y lograr captación repetible en un segmento. El monto se calculará con el presupuesto mensual del equipo, 18–24 meses de operación prevista, ingresos prudentes y contingencias. No se fija una valoración ni una dilución en esta versión.

Si la evidencia muestra un negocio rentable de nicho, puede crecer con ingresos y capital acotado. Si demuestra demanda más amplia y una vía creíble hacia miles de organizaciones o contratos mayores, puede ser candidato a capital de riesgo. La elección depende del tamaño alcanzable y del ritmo de expansión, además de la ambición del fundador.

La visión completa seguirá una secuencia condicionada por demanda: núcleo de diseño y entramado → coordinación de más sistemas → documentación más profunda → adaptación a empresas y mercados → cuantificación integral y, eventualmente, abastecimiento. Las compras no condicionan el éxito del MVP.

## 18. Agenda de las próximas cuatro semanas

| Semana | Trabajo | Responsable propuesto | Evidencia que debe quedar |
| --- | --- | --- | --- |
| 1 | Conversaciones con los dos arquitectos; reconstruir un proyecto reciente; registrar dedicación y caja disponibles | Fundador; arquitectos si aceptan | Flujo, entregables, tiempos aproximados y límites de inversión |
| 2 | Entrevistas externas; base inicial de organizaciones; selección del trabajo a automatizar | Fundador con apoyo profesional | Problema repetido, comprador y casos candidatos |
| 3 | Especificación del dominio y prueba comparativa de interfaz; análisis de reutilización de V06 | Responsable técnico y asesores | Alcance, riesgos técnicos y decisión provisional sobre Blender |
| 4 | Demostración de un cambio coherente si la factibilidad lo permite; propuesta de pilotos y presupuesto contratado | Fundador y responsable técnico | Decisión de avanzar, ajustar o reformular la siguiente etapa |

La versión 0.2 del plan debe reemplazar supuestos por respuestas: quién compra, qué trabajo necesita, cuánto tarda hoy, qué acepta pagar, qué datos aporta, qué entregable considera útil y cuánto cuesta desarrollar el primer alcance.

**Decisión recomendada:** comenzar un período de descubrimiento y factibilidad de cuatro semanas, con gasto limitado y entregables definidos. Su resultado debe permitir decidir el desarrollo del MVP con evidencia y preservar la ambición de construir una plataforma de largo plazo.

---

**Base documental de esta versión:** revisión del script y del LEEME de Angus Ranch V06; instrucciones del fundador en esta conversación; consulta de las páginas oficiales enlazadas el 18/09/2026. No se realizó una auditoría técnica de la vivienda, una lectura completa de la literatura, entrevistas a terceros ni una prueba práctica de productos competidores. Los hechos externos están enlazados junto a las afirmaciones; metas, precios, cronogramas y finanzas son propuestas explícitas para validar.
