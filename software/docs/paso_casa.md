# Capa 02 · Casa — planta, volumen e interior

**Versión 0.2 · 10 de octubre de 2026 · Documento de trabajo**

Este documento fija cómo el usuario llega a la planta de su casa, cómo la edita y cómo la ve levantada y
amoblada antes de pasar a la estructura. El código vive en `frontend/src/pasos/casa/` (interfaz),
`backend/assambl/capas/casa.py` (generador de plantas), `backend/assambl/capas/interior.py` (muebles y
galería), `backend/assambl/reglas/` (reglas R03 y RI) y `backend/assambl/ia/` (Lumo y proveedores de IA).

**Orden de las capas.** La secuencia no sigue al pie de la letra la numeración del MVP_01: se ajusta a medida
que se construye. Hoy va Terreno → Casa (planta, volumen e interior) → Estructura → … → Plomería → Eléctrico →
Cimientos. Las instalaciones y los cimientos van al final porque resultan de las decisiones de la casa. Los ids
de las capas son estables (`frontend/src/componentes/capas.ts`); el número que se ve es la posición. Las reglas
de la planta conservan su prefijo R03 porque verifican lo que después levanta la estructura woodframe.
Las capturas de `docs/paso_casa/` son el boceto: se decidió prototipar directamente en la aplicación, con
datos reales (Angus Ranch), en lugar de hacerlo en Figma. Así el prototipo que se prueba con usuarios es el
producto mismo.

| | |
| --- | --- |
| ![Inicio](paso_casa/1_inicio.png) Cómo empezar | ![Lumo](paso_casa/2_lumo.png) Charla con Lumo |
| ![Alternativas](paso_casa/3_alternativas.png) Elegir un partido | ![Editor](paso_casa/4_editor.png) Editor de planta |
| ![Estados](paso_casa/5_estados_angus.png) Estados en Angus Ranch | ![Imagen](paso_casa/6_imagen_revisar.png) Planta leída de un bosquejo, a revisar |
| ![Vista 3D](paso_casa/7_vista3d.png) Vista 3D amoblada, muros cortados | ![Propuesta](paso_casa/8_lumo_propuesta.png) Propuesta de Lumo en vista previa |

## 1. Para quién

El usuario **no** es arquitecto ni modelador 3D. Es alguien entusiasmado con construir su casa en woodframe
que nunca usó un programa de dibujo. De ahí salen cinco principios que atraviesan el paso:

1. **Nunca un lienzo en blanco sin ayuda.** La primera pantalla ofrece maneras de empezar, no herramientas.
2. **La IA entiende; las reglas construyen.** El asistente conversa y lee imágenes, pero no escribe muros:
   produce un *programa* (qué ambientes, qué tamaño) o *rectángulos aproximados*, y la geometría la arma
   `capas/casa.py` con reglas deterministas. Es lo que pide MVP_01 §4.4: la interfaz y el asistente llaman
   las mismas operaciones y ninguno escribe geometría por su cuenta.
3. **Todo es un punto de partida.** Lo que sale de cualquier entrada se abre en el mismo editor.
4. **Se ve qué está verificado y qué no.** Cada pieza muestra su estado sobre el plano (§5).
5. **Español rioplatense, sin jerga.** Si hay un término técnico, se explica en una línea.

## 2. El recorrido

```
                    ┌──────────────────────────────┐
                    │  ¿Cómo querés empezar tu casa?│  ← Inicio.tsx
                    └──────────────┬───────────────┘
      ┌──────────────┬─────────────┼───────────────┬─────────────────┐
      ▼              ▼             ▼               ▼                 ▼
 1 Contala con   2 Armala con   3 Subí un       Dibujar desde     Ver un ejemplo
 tus palabras    Lumo           bosquejo        cero (básico)     (Angus Ranch)
 (IA, texto)     (IA, guiado)   (IA, imagen)
      │              │             │               │                 │
      └──────┬───────┘             │               │                 │
             ▼                     ▼               │                 │
        Charla.tsx          ImportarImagen.tsx     │                 │
   pregunta solo lo que   lectura + planta encima  │                 │
   falta · opciones con   de la imagen · dudas     │                 │
   su consecuencia        con opciones             │                 │
             │                     │               │                 │
             ▼                     │               │                 │
     Alternativas.tsx              │               │                 │
   2–3 partidos del mismo          │               │                 │
   programa: elegir uno            │               │                 │
             │                     │               │                 │
             └─────────────────────┴───────┬───────┴─────────────────┘
                                           ▼
                              Editor de planta 2D (EditorPlanta + PanelEditor)
                              verificación en vivo con R03 · deshacer · estados
                                           ▲
                                           │  misma casa, misma selección, mismo deshacer
                                           ▼
                              Vista 3D (VistaCasa3D + PanelInterior)
                              casa levantada y amoblada · galería · Lumo
```

**Prioridades** (como se acordó): las entradas 1 y 2 están completas; la 3 (dibujo libre) existe en su
versión básica —el mismo editor con la planta vacía— y no tiene asistencia propia todavía.

### 2.1 Entrada 1a · «Contala con tus palabras» (prompt libre)

- Un cuadro de texto con tres ejemplos que se pueden tocar para completarlo.
- El asistente extrae el programa y **solo pregunta si falta algo que cambia la forma de la casa**
  (cantidad de dormitorios, tamaño aproximado). Si alcanza, salta directo a las alternativas.
- Siempre se puede seguir charlando para ajustar («sumá un lavadero», «que el baño sea más grande»).

### 2.2 Entrada 1b · «Armala con Lumo» (orientador)

**Lumo** es el asistente de Assambl en toda la aplicación: una llama índigo con ojos ovalados y sonrisa fija.
Su definición de diseño es `software/lumo/lumo-final.html` (forma, paleta, los diez estados y cuándo se usa
cada uno); el componente es `frontend/src/componentes/lumo/Lumo.tsx` con `lumo.css`. El estado es un atributo
del mismo dibujo, así que nunca cambia la forma:

| Estado | Cuándo aparece en la app |
| --- | --- |
| `idle` | En la barra superior y en la charla sin actividad |
| `wave` | Tarjeta «Armala con Lumo» del inicio |
| `listen` | Mientras el usuario escribe |
| `think` | Entre el envío y la respuesta; leyendo un bosquejo |
| `build` | Armando plantas o amoblando la casa |
| `reply` | Último mensaje de la charla |
| `success` | Alternativas listas, propuesta de muebles lista para aplicar |
| `oops` | Error recuperable |
| `sleep` | Sin conexión con la API |

Respeta `prefers-reduced-motion`.

Reglas de conversación (están en el prompt de sistema, `ia/asistente.py`):

- **Una pregunta por vez**, siempre con **2 a 4 opciones** y la **consecuencia** de cada una en pocas
  palabras («Integrada · un solo ambiente, más luz y menos muros»). Siempre se puede escribir en vez de elegir.
- Primero lo que más cambia la casa: dormitorios → tamaño → baños → cocina integrada o separada → extras.
- Si el usuario no sabe, se sugiere la opción más común y se sigue. En 5 a 7 preguntas debe estar listo.
- Fuera del dominio (dos plantas, curvas, más de 200 m²) se explica por qué y se ofrece lo más parecido.
- A la derecha, «Lo que va anotando Lumo» muestra el programa en vivo: ambientes, superficies y total.
- Si el programa pide galería, las tres alternativas la traen dibujada del lado del sol (§4.4).

### 2.3 Momento de decisión · alternativas

Cuando el programa alcanza, se muestran **tres partidos** del mismo pedido (`capas/casa.py → alternativas`):

| Partido | Qué es | A cambio de |
| --- | --- | --- |
| Compacta en dos franjas | Estar a un lado; pasillo corto; dormitorios al sol, baños y lavadero del lado opuesto | — (menos muro exterior) |
| Lineal, todo al sol | Una tira de ambientes, pasillo del lado frío | Más fachada y más muro exterior |
| Compacta, estar al este | La compacta espejada: estar con sol de mañana | — |

Cada tarjeta muestra la planta en miniatura con estados, superficie cubierta, frente × fondo y **metros de
muro exterior** (el dato que un entusiasta no mira y que más pesa en costo y en pérdida de calor). «Al sol»
significa norte en el hemisferio sur y sur en el norte: se usa la latitud de la capa 01 si existe.

### 2.4 Entrada 2 · «Subí un bosquejo o un plano»

1. Se arrastra una imagen (PNG/JPG). El navegador la achica a 1600 px antes de enviarla.
2. Opcionales: **ancho total del frente** (para escalar si el dibujo no tiene cotas) y aclaraciones.
3. La IA devuelve ambientes como rectángulos en metros, **la escala que usó** (cotas del dibujo, medida del
   usuario o estimada), su **confianza**, advertencias y **preguntas con opciones** para lo ambiguo. Tocar una
   opción vuelve a interpretar con esa aclaración.
4. `normalizar_rectangulos()` alinea bordes casi coincidentes y lleva todo a la grilla de 5 cm; el generador
   arma muros, aberturas y ambientes.
5. La planta se muestra **encima de la imagen** para compararla, y en el editor la imagen queda de fondo
   (calco) con opacidad regulable.
6. **Todas las piezas nacen `pendiente_revision`.** El usuario corrige y confirma, pieza por pieza
   («✓ Revisado») o en bloque («Ya revisé todo»).

Un ambiente en L se lee como dos rectángulos «Estar (a)» y «Estar (b)»; entre ellos no se pone muro.

### 2.5 Dibujo libre y ejemplo

- **Dibujar desde cero** abre el editor vacío con una indicación para empezar con la herramienta Muro.
- **Ver un ejemplo** carga `casos/angus_ranch.assambl.json` (el caso de regresión de V11). Sirve para
  mostrar el editor con una casa real y con estados no triviales: sus corredizas de 4 m «requieren cálculo» y
  el estar-comedor «faltan datos» porque V11 no lo delimita.

## 3. El editor de planta 2D

Lienzo SVG en metros, con X al este e Y al norte (convención de Angus Ranch). Muestra grilla de 1 m / 5 m,
norte, barra de escala, coordenadas del cursor, el lote de la capa 01 (línea verde) y el calco si lo hay.

| Herramienta | Tecla | Qué hace |
| --- | --- | --- |
| Elegir y mover | V | Clic elige. Arrastrar un muro lo corre en perpendicular y **arrastra lo conectado**: los extremos de los muros que apoyan contra él, los bordes de los ambientes y la posición de sus aberturas. Arrastrar una abertura la desliza por su muro sin dejarla pisar otra. |
| Muro | M | Clic en cada quiebre. **Siempre a 90°** (gana el eje con más recorrido). Imanes a extremos existentes, alineación con extremos a 10 px y grilla de 5/10/25 cm según el zoom. Muestra el largo mientras se dibuja. Al cerrar sobre un extremo termina la cadena; doble clic o Esc también. Se elige el sistema: exterior 45 × 140, interior portante o tabique 45 × 90. |
| Puerta / ventana | A | Se elige un ítem del **catálogo** (`catalogo/ar.json`, familia `aberturas`) y se hace clic sobre un muro. Una sombra muestra dónde queda y avisa «no entra» antes de hacer clic. |
| Ambiente | R | Se arrastra un rectángulo; al soltar se elige el ambiente y el foco va al nombre. |

Además: rueda para acercar, espacio + arrastrar o botón derecho para desplazarse, Supr para borrar, Esc para
soltar, Ctrl+Z / Ctrl+Shift+Z para deshacer y rehacer (80 pasos).

El panel derecho tiene las propiedades de lo elegido (sistema y largo del muro; catálogo, posición, ancho,
antepecho, dintel, bisagra y sentido de la puerta; nombre y uso del ambiente), la lista **«Para resolver»**
(cada ítem lleva a su pieza y la resalta al pasar el mouse), la leyenda de estados con cantidades y un resumen
(superficie cubierta, muro exterior, piezas).

Todas las ediciones son operaciones puras en `operaciones.ts` (`agregarMuro`, `moverMuro`,
`agregarAbertura`, `modificarAbertura`, `agregarAmbiente`, `marcarRevisado`…) que devuelven una casa nueva.
La huella se recalcula encadenando los muros exteriores. Lo que la casa trae de otras capas (cubiertas,
instalaciones, mobiliario) se conserva sin tocar.

## 4. La vista 3D y el interior

Con la planta resuelta, el usuario necesita ver la casa antes de pasar a la estructura: si el living entra, si
el dormitorio queda chico con la cama, si la galería mira al sol. La vista 3D es **la misma casa** que la
planta, no un paso aparte: un selector «Planta 2D | Vista 3D» en la barra del editor cambia de vista y
conserva la selección, el deshacer y las reglas. Se puede abrir en cualquier momento; lo que falte resolver
sigue en la lista.

### 4.1 Lo que se ve

`escena3d.ts` levanta la casa en el navegador a partir de la planta, sin backend:

- **Muros** con su espesor, cortados a la altura elegida (por defecto 1,35 m, como una maqueta seccionada;
  el control «Muros» llega hasta la altura completa). La cara exterior de los muros exteriores va oscura, la
  interior en revoque y el corte en tono madera. Ventanas con antepecho, dintel y vidrio; puertas con la hoja
  abierta como en la planta.
- **Pisos** por ambiente según su solado o su uso (madera en dormitorios, porcelanato en baños), sobre la platea.
- **Galería** con deck de tablas y postes en las esquinas libres.
- **Muebles y artefactos** del catálogo, con medidas reales y las mismas formas que se ven en la planta.

Cámara isométrica desde las cuatro esquinas, vista desde arriba y «Recorrer» a la altura de los ojos dentro
del ambiente elegido. «Exportar imagen» arma una lámina PNG con título, la vista y las superficies.

### 4.2 Muebles

El catálogo es la familia `mobiliario` de `catalogo/ar.json` (55 piezas: estar, comedor, cocina, dormitorio,
baño, lavadero, oficina, galería y deco). El frontend lo importa del mismo archivo que usan las reglas y el
amoblado, así no hay dos listas. Cada ítem trae medidas, apoyo (muro, esquina o libre), espacio de uso
delante, ambientes donde puede ir y, en los artefactos, agua y desagüe para la plomería. Las variantes de un
mismo mueble (camas de 1 plaza a king, placards, duchas) comparten `grupo` y se cambian desde el panel.

Convención de las piezas: `centro_m`, `medidas_m` = [ancho, fondo, alto] y `giro_deg` antihorario, con la
espalda al sur y el frente al norte en 0°. La planta 2D dibuja las piezas desde arriba con las mismas cajas y
cilindros que la vista 3D (`modelo/muebles.ts → primitivas`).

- **Al entrar a la vista 3D por primera vez la casa aparece amoblada** (`capas/interior.py → amoblar`), con
  reglas por uso: la cama contra el muro sin ventana con paso a los costados, mesas de luz y placard en otro
  muro; en el baño la ducha en la esquina lejos de la puerta, inodoro, bidet y vanitory; la cocina como mesada
  corrida con heladera, anafe, bacha y alacenas; el estar con sofá y tele enfrentados, mesa ratona y alfombra, y
  el comedor con su mesa y sillas. Se deshace con Ctrl+Z.
- En 3D se toca un mueble para elegirlo y se arrastra sobre el piso; se pega a los muros cercanos. En la planta
  también se arrastra. **R** gira 90° (Mayúsculas + R al revés), **Ctrl+D** duplica, **Supr** borra.
- «Agregar» ubica la pieza en el ambiente elegido (o en el que le corresponde) contra un muro y con su
  espacio de uso libre (`POST /api/casa/colocar`).
- Mover un muro en la planta arrastra los muebles que tienen la espalda contra él.

### 4.3 Lumo en la vista 3D

Lumo atiende pedidos de muebles y de espacios: «sumá un escritorio en la oficina», «cambiá la cama por una
queen», «sacá la alfombra», «amoblá el dormitorio 2», «armá una galería al norte», «agrandá el baño». Responde
con **operaciones** validadas (`ia/interior.py`): agregar, quitar, cambiar, mover, amoblar, galería, mover un
muro o cambiar el uso de un ambiente. La IA no da coordenadas: elige qué hacer y dónde, y las reglas buscan el
lugar. El resultado se muestra como **vista previa** con las piezas nuevas marcadas en índigo; el usuario la
aplica o la descarta. Los cambios de muros los ejecuta la interfaz con la misma operación del editor, así
arrastran lo conectado igual que a mano. Sin proveedor de IA, un guion por palabras clave resuelve los pedidos
más comunes.

### 4.4 Galería

La galería es un ambiente de uso `galeria`: exterior, techado y sin muros. No suma a la superficie cubierta
cerrada (la huella) y se informa aparte. Se agrega desde el panel eligiendo lado y fondo (2 a 4 m); por defecto
va del lado del sol de invierno (norte en el hemisferio sur), sobre el muro del estar y centrada en él. Si ese
muro no tiene salida, se propone una puerta-ventana corrediza. También se puede dibujar a mano con la
herramienta Ambiente y uso «Galería».

## 5. Formato

La planta se guarda en `proyecto.casa` con el esquema `assambl/casa@0.1` de Angus Ranch: muros por eje con sus
aberturas (`posicion_m` desde el inicio del eje), ambientes con contorno en la cara interior del muro,
sistemas constructivos y huella. Se agregan tres campos opcionales por pieza:

- `estado`: el declarado (ver §6).
- `revision: {fecha}`: cuándo lo aprobó el usuario.
- `catalogo`: código del ítem de catálogo de una abertura.

El interior usa las secciones que ya traía Angus Ranch: `mobiliario` (muebles) y `artefactos` (lo que lleva
agua o desagüe), con `id`, `tipo` (código del catálogo), `ambiente`, `centro_m`, `medidas_m`, `giro_deg` y
`estado`. La galería es un ambiente más, con `uso: "galeria"`. `interior.amoblado_automatico` recuerda que ya
se propuso un amoblado, para no repetirlo.

## 6. Estados sobre cada pieza

Cada muro, abertura y ambiente muestra un estado de MVP_01 §4.4 con **tres canales redundantes** (relleno,
trama, insignia con glifo), para que se lea sin depender del color. La idea visual: lo resuelto se ve «como un
plano» (negro sólido); lo que pide atención se destaca; lo que no se sabe se ve hueco.

| Estado | Muro | Ambiente | Insignia | Significado para el usuario |
| --- | --- | --- | --- | --- |
| `comprobado_por_reglas` | Negro sólido | Claro | — | Cumple todas las reglas que se le aplican. |
| `propuesto` | Gris | Claro | — | Recién creado; todavía no se verificó. |
| `pendiente_datos` | Hueco punteado | Rayado gris | … | Le falta algo: una ventana, una puerta, un contorno. |
| `pendiente_calculo` | Ámbar sólido | Tinte ámbar | ∑ | Excede las reglas (vano muy ancho): lo calcula un profesional. |
| `pendiente_revision` | Ámbar rayado | Tinte ámbar | ! (solo en ambientes) | Lo propuso la IA o una heurística: miralo y confirmalo. |
| `revisado` | Negro sólido | Tinte verde | ✓ | Lo aprobaste vos. |
| `desactualizado` | Naranja señal | Tinte naranja | ↻ | Estaba revisado y un cambio lo invalidó. |

**Cómo se combinan** (`estados.ts → estadoPieza`):

1. Lo que una regla marca `pendiente_calculo` **gana siempre**: no se puede tapar con «Revisado».
2. Si no, manda el estado declarado cuando es `revisado`, `desactualizado` o `pendiente_revision`.
3. Si no, el que dan las reglas R03; sin API, el guardado.

**Transiciones:** crear o editar una pieza la deja `propuesto` (es una propuesta nueva del usuario y las
reglas la vuelven a verificar); si estaba `revisado`, pasa a `desactualizado`. Lo leído de una imagen nace
`pendiente_revision`. «✓ Revisado» la pasa a `revisado`. El estado de la planta en el encabezado es el más
grave de los que se ven. «Ver sobre la planta» apaga los colores y deja el plano limpio.

`pendiente_revision` suele abarcar toda una planta leída por IA; por eso en muros y aberturas lo dice la trama
y la insignia «!» queda solo en los ambientes, para no llenar el plano de signos.

## 7. Reglas de la planta y del interior

`reglas/r03_planta.py` (versión 0.1). Cada verificación nombra las piezas a las que se aplica y el estado de la
pieza es el peor que recibe. Se ejecutan en el backend a cada cambio (250 ms de espera).

| ID | Verifica | Si falla |
| --- | --- | --- |
| R03.01 | Muros a 90° (dominio del MVP_01) | `pendiente_revision` |
| R03.02 | Superficie cubierta entre 40 y 200 m² | `pendiente_revision` |
| R03.03 | Ningún muro menor a 30 cm | `pendiente_revision` |
| R03.04 | La abertura entra en su muro con lugar para el king (10 cm al extremo) y no pisa otra | `pendiente_revision` |
| R03.05 | Header por tabla según la luz del vano en bruto (nominal + 2 × 15 mm): 2 × 6 hasta 1,20 m; 2 × 8 hasta 1,80 m; 2 × 10 hasta 2,40 m | `pendiente_calculo` |
| R03.06 | Puertas de al menos 2,00 m de alto | `pendiente_revision` |
| R03.07 | El ambiente tiene contorno | `pendiente_datos` |
| R03.08 | Dormitorio ≥ 7,5 m² y 2,4 m de lado; baño ≥ 2,4 m² | `pendiente_revision` |
| R03.09 | Dormitorios, estar y oficina tienen ventana en un muro exterior | `pendiente_datos` |
| R03.10 | Cada ambiente tiene puerta o paso (o está abierto a otro) | `pendiente_datos` |

Los umbrales son de partida (MVP_01 §3.3: deben ratificarse con el especialista). Nota: medida en vano bruto,
una corrediza de 2,40 m ya pide cálculo; por eso el generador propone corredizas de 2,00 m.

`reglas/r_interior.py` (versión 0.1) se ejecuta junto con las R03 y nombra el mueble que tiene el problema.

| ID | Verifica | Si falla |
| --- | --- | --- |
| RI.01 | Cada pieza queda dentro de su ambiente (no atraviesa muros) | `pendiente_revision` |
| RI.02 | Las piezas no se superponen (salvo alfombra, sillas bajo la mesa, piezas colgadas) | `pendiente_revision` |
| RI.03 | Cada pieza contra muro tiene libre su espacio de uso (70 cm delante del inodoro, 60 cm de los demás artefactos, 1 m de la mesada) | `pendiente_revision` |
| RI.04 | Ninguna pieza queda en el barrido de una puerta o en un paso | `pendiente_revision` |
| RI.05 | Cada pieza va en un ambiente adecuado (sanitarios en baños, muebles de galería afuera) | `pendiente_revision` |
| RI.06 | Los pasillos dejan 90 cm de paso | `pendiente_revision` |
| RI.07 | La galería tiene al menos 1,8 m de fondo y está junto a la casa | `pendiente_revision` |

## 8. Inteligencia artificial

### 8.1 Proveedor intercambiable

Todo el producto habla con la IA por una sola operación, `completar_json(sistema, mensajes, imagenes)`
(`ia/proveedores.py`). Los prompts y la validación viven en `ia/asistente.py` y no dependen del prestador.
Se cambia de prestador **solo desde el `.env`**:

| Variable | Para qué |
| --- | --- |
| `IA_PROVEEDOR` | `openai`, `anthropic` o `simulado`. Vacío: el primero que tenga clave. |
| `IA_MODELO` | Modelo; por defecto `gpt-5-mini` (OpenAI) o `claude-opus-5-5` (Anthropic). |
| `OPENAI_API_KEY` | Clave de OpenAI. |
| `ANTHROPIC_API_KEY` | Clave de Anthropic. |
| `IA_URL_BASE`, `IA_API_KEY` | Cualquier servicio compatible con Chat Completions (OpenRouter, Groq, DeepSeek, Mistral, Together, Ollama, LM Studio…). |

- `openai` usa Chat Completions por HTTP con salida en modo JSON; `anthropic` usa el SDK oficial.
- `simulado` no sale a internet: sigue un guion fijo (preguntas del orientador y lectura del texto por
  palabras clave) y, para imágenes, devuelve una planta de demostración **marcada como tal**. Es lo que se usa
  sin clave, en las pruebas y para desarrollar la interfaz. La interfaz avisa «IA en demostración».
- La respuesta se valida con pydantic; si no valida, se le devuelve el error al modelo **una vez** para que la
  corrija. Después se normaliza: ids únicos y superficies que cierran con la superficie objetivo.
- `GET /api/casa/ia` informa proveedor y modelo activos (sin exponer la clave).

Agregar otro prestador es escribir una subclase de `Proveedor` con `completar_json` y sumarla en
`obtener()`.

### 8.2 Privacidad

Las imágenes y el texto que el usuario escribe se envían al prestador configurado. Conviene decirlo en la
interfaz antes de la prueba con usuarios y revisar la política de retención del prestador elegido.

## 9. Rutas

```
GET  /api/casa/ia                    proveedor de IA activo
GET  /api/casa/catalogo              catálogo del mercado (aberturas)
POST /api/casa/conversar             un turno de charla → mensaje, pregunta con opciones, programa, listo
POST /api/casa/alternativas          programa → 3 partidos con su casa y su análisis R03
POST /api/casa/interpretar-imagen    imagen (data URL) → lectura, planta a revisar, análisis
POST /api/casa/analizar              casa → estado por pieza y verificaciones R03 y RI
POST /api/casa/amoblar               casa (+ ambientes, reemplazar) → casa amoblada y notas
POST /api/casa/colocar               casa + código + ambiente → la pieza ubicada o el motivo
POST /api/casa/galeria               casa + lado + fondo → galería amoblada (y su salida si falta)
POST /api/casa/interior/conversar    pedido a Lumo → mensaje, operaciones, casa propuesta, muros a mover
```

## 10. Pendientes

- **Probar con la clave real de OpenAI** el orientador, el texto libre y la lectura de bosquejos (hasta ahora
  se probó el recorrido completo con el proveedor simulado y el contrato con un proveedor falso en las pruebas).
  Armar un set de 10–15 bosquejos reales para medir la lectura de imágenes.
- **Lumo en la planta 2D:** hoy Lumo cambia muebles y mueve muros desde la vista 3D; falta llevar la misma
  charla al editor de planta (abrir vanos, partir ambientes).
- **Amoblado:** afinar las plantas chicas con cocina integrada (a veces no entran a la vez estar y comedor) y
  sumar más variantes de distribución por ambiente.
- **Techo y alturas en 3D:** cubierta y cielorraso cuando se construya la estructura.
- **Implantación:** mover y girar la casa sobre el lote, con retiros dibujados (hoy se centra en el lote).
- **Dibujo libre asistido:** detectar ambientes cerrados por muros y proponer nombres.
- Partidos en L y en U.
- Prueba de usabilidad con 5 entusiastas: ¿entienden los estados sin la leyenda? ¿qué entrada eligen?
