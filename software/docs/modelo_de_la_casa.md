# Modelo de la casa · `casa@0.1`

Estado al 28/09/2026.

Este documento explica la sección `casa` de `casa.assambl.json`: qué decide el usuario sobre la vivienda y cómo se escribe. Es el contrato entre la interfaz y el motor de reglas: la interfaz edita estos datos y el backend los convierte en piezas, capas, planos y cómputos.

| Qué | Dónde |
| --- | --- |
| Modelo de referencia (valida tipos y referencias cruzadas) | [`backend/assambl/modelo/casa.py`](../backend/assambl/modelo/casa.py) |
| Espejo TypeScript para la interfaz | [`frontend/src/modelo/casa.ts`](../frontend/src/modelo/casa.ts) |
| Caso de ejemplo completo: Angus Ranch V11 | [`casos/angus_ranch.assambl.json`](../casos/angus_ranch.assambl.json) |
| Generador del caso a partir del script V11 | [`scripts/armar_caso_angus.py`](../scripts/armar_caso_angus.py) |
| Pruebas del caso contra V11 | [`backend/tests/test_caso_angus.py`](../backend/tests/test_caso_angus.py) |

## Principio: se guardan decisiones, no piezas

El JSON guarda lo que una persona decide: dónde va un muro, qué ancho tiene una ventana, qué pendiente tiene el techo. **No guarda** montantes, placas de OSB, pernos, listones ni cantidades. Todo eso se deriva con reglas (MVP_01 §4.2) y es caché regenerable.

La prueba de que el formato alcanza es Angus Ranch: con estos datos, el generador de la capa 03 tiene que reproducir las **828 piezas de madera** y los **100 pernos de solera** que produce V11. Esos números están en `casa.origen.regresion` y la prueba `test_objetivo_de_regresion` los verifica contra el script.

Cuando un dato todavía no está decidido, se marca con `estado: "pendiente_datos"` y una `nota`, en vez de inventarlo. En Angus Ranch quedan pendientes el contorno del estar-comedor-cocina, la ubicación real del terreno, el destino cloacal y pluvial, la ventilación sanitaria, el abastecimiento de agua y el medidor.

## Convenciones

- **Unidades:** metros en todo campo terminado en `_m`; milímetros en `_mm`; grados en `_deg`; porcentaje en `_pct`.
- **Ejes:** X este, Y norte, Z arriba. Mismo criterio que el terreno (`norte: "+Y"`).
- **Origen de la casa:** esquina suroeste de la planta principal, con Z = 0 en el piso terminado. La implantación ubica ese origen dentro del lote.
- **Rectángulo:** `[x0, y0, x1, y1]`. **Polígono:** lista de `[x, y]` sin repetir el primer vértice.
- **Medidas de un objeto:** `[ancho en X, fondo en Y, alto]`, antes de aplicar `giro_deg` (antihorario, visto desde arriba).
- **Ids:** estables y únicos dentro de su colección. Otras secciones y las piezas derivadas los referencian (`"ambiente": "bano_suite"`, `"circuito": "TUG_D"`). Cambiar un id rompe referencias; el validador lo detecta.
- **Estados:** los de MVP_01 §4.4 (`propuesto`, `pendiente_datos`, `pendiente_calculo`, …), los mismos que ya usa el terreno.

## Encaje en el proyecto

`casa` es una sección opcional del proyecto. El proyecto sigue en `assambl/proyecto@0.2`, así que la aplicación actual abre el caso de Angus Ranch sin cambios (todavía no muestra la casa). La sección tiene su propio número de versión, `casa.esquema = "assambl/casa@0.1"`, para poder evolucionar sin romper el terreno.

```jsonc
{
  "esquema": "assambl/proyecto@0.2",
  "terreno": { … },          // capa 01, ya existente
  "casa": {
    "esquema": "assambl/casa@0.1",
    "nombre", "origen", "unidades", "ejes",
    "implantacion", "huella_m",
    "sistemas", "parametros",
    "muros", "ambientes", "cubiertas",
    "cimientos", "carpinterias", "exteriores",
    "artefactos", "mobiliario", "instalaciones",
    "materiales"
  }
}
```

## Campos

### Generales

| Campo | Qué es |
| --- | --- |
| `nombre` | Nombre de la casa. |
| `origen` | De dónde sale el diseño. En un caso migrado: script, versión y los números de regresión. En una casa hecha en la app puede faltar. |
| `unidades`, `ejes` | Fijos (`"m"`, este/norte/arriba). Están escritos para que el archivo se explique solo. |
| `implantacion.origen_en_lote_m` | Dónde cae el origen de la casa en el sistema local del terreno (`terreno.lote.vertices`). |
| `implantacion.giro_deg` | Giro antihorario de la casa respecto del lote. En Angus Ranch es 0: la galería mira al norte. |
| `implantacion.cota_piso_sobre_terreno_m` | Altura del piso terminado sobre el terreno natural. Mínimo 0,15 (MVP_01 §3.1). |
| `huella_m` | Contorno exterior de la planta, sin galería ni aleros. También es el contorno de la platea. Angus Ranch: 164,16 m². |

### `sistemas`: tipos de muro

Cada muro dice qué sistema usa, y el sistema define el paquete de capas. Cambiar el aislante de todos los muros exteriores es cambiar una línea acá, no veinte muros.

| Campo | Qué es |
| --- | --- |
| clave (`exterior`, `interior_portante`, `tabique`) | Nombre del sistema al que apuntan los muros. |
| `espesor_arquitectonico_m` | Espesor del muro en planta (0,20 exterior y portante; 0,15 tabique). |
| `capas` | Capas de adentro hacia afuera. `capa` es uno de `terminacion_interior`, `entramado`, `aislante`, `osb`, `wrb`, `camara_ventilada`, `siding`; el resto de los campos son los que esa capa necesita (espesor, escuadría, módulo, solapes, etc.). |
| `terminacion` | Terminación de ambas caras en muros interiores. |

La capa `entramado` es la que usan las reglas estructurales: `seccion_mm` [ancho, fondo] (45 × 140 exterior y portante; 45 × 90 tabique) y `modulo_mm` (600 entre ejes de montantes).

### `parametros`

Valores comunes a toda la casa.

| Campo | Qué es |
| --- | --- |
| `altura_tabiques_m` | Altura de los muros con `altura.tipo = "tabique"` (2,80). |
| `esquinas` | Regla de encuentro en esquinas exteriores. En V11, el muro paralelo a X pasa de largo y el paralelo a Y apoya contra su cara. |
| `zocalo` | Franja de zócalo: cotas, espesor y material. |
| `cielorraso` | Cara inferior, espesor, material y zonas (rectángulos) que cubre. |
| `solado_general` | Solado de lo que no está dentro de un ambiente con solado propio. |

### `muros`

Un muro es un eje recto con un sistema, una altura y sus aberturas. MVP_01 §2 admite solo muros paralelos a X o a Y; el validador rechaza los oblicuos.

| Campo | Qué es |
| --- | --- |
| `id` | Nombre estable (`"Norte"`, `"Dorm2_N"`). Es el prefijo del id de sus aberturas y de sus piezas. |
| `sistema` | Clave en `sistemas`. |
| `eje.desde_m`, `eje.hasta_m` | Extremos del eje en planta, siempre con la coordenada creciente. **En muros exteriores el eje va de esquina a esquina** (el punto donde se cruzan los ejes de dos muros exteriores); la regla de esquina decide después cuánto se extiende o se retrae el entramado. En muros interiores, el eje es el largo real del muro. |
| `lado_exterior` | Solo muros exteriores: hacia dónde queda afuera (`norte`, `sur`, `este`, `oeste`). Define de qué lado van OSB, WRB y siding. |
| `altura.tipo` | `"tabique"`: toma `parametros.altura_tabiques_m`. `"hasta_cubierta"`: el muro sube hasta el plano de apoyo de la cubierta indicada, así que puede tener el tope inclinado. |
| `altura.cubierta` | Solo con `hasta_cubierta`: id de la cubierta. |
| `aberturas` | Ver abajo. |

Qué se deriva y no se guarda: extremos reales del entramado en esquinas, soleras, montantes, kings, jacks, dinteles, antepechos y cripples, bloqueos, capas de la envolvente y zócalos.

#### Aberturas

Cada abertura es el **vano libre** (la luz que queda entre el marco estructural), no la medida del marco ni de la carpintería.

| Campo | Qué es |
| --- | --- |
| `id` | `"<muro>/O<n>"`, numeradas en orden a lo largo del eje, igual que en V11. |
| `tipo` | `ventana`, `ventana_corrediza`, `puerta` o `paso` (vano sin hoja ni marco). |
| `posicion_m` | Distancia sobre el eje desde `eje.desde_m` hasta la primera jamba. |
| `ancho_m` | Ancho del vano libre. |
| `antepecho_m` | Cota inferior del vano (0 en puertas y ventanas a piso). |
| `dintel_m` | Cota superior del vano. |
| `hoja` | Solo puertas: `bisagra` (`inicio` o `fin`, según el extremo del vano más cercano a `eje.desde_m`) y `apertura_deg` con la que se dibuja la hoja (positivo o negativo según el lado). |

El validador exige que la abertura quede dentro del eje, que no se superponga con otra y que el dintel esté por encima del antepecho. La altura del dintel estructural no se guarda: sale de `carpinterias.dintel`.

### `ambientes`

| Campo | Qué es |
| --- | --- |
| `id`, `nombre` | Id estable y nombre para mostrar. |
| `uso` | `dormitorio`, `vestidor`, `bano`, `lavadero`, `oficina`, `social`, `cocina` o `circulacion`. Baño, lavadero y cocina son locales húmedos (MVP_01 §3.13), lo que dispara reglas de plomería. |
| `contorno_m` | Polígono interior (caras de muro), o `null` si todavía no se dibujó. |
| `solado` | Clave en `materiales`. |
| `estado` | `propuesto`, o `pendiente_datos` si falta el contorno. |

### `cubiertas`

Cada cubierta es un plano inclinado con su estructura. El **plano de apoyo** es la cara inferior de los cabios y, a la vez, el tope de los muros que llegan hasta esa cubierta.

| Campo | Qué es |
| --- | --- |
| `id` | `principal`, `anexo_sur`, `galeria`. Los muros y las canaletas lo referencian. |
| `tipo` | `un_agua` (las tres de Angus Ranch) o `dos_aguas`. |
| `plano_apoyo` | `cota_m` en el punto `en_m`, `pendiente_pct` y `sube_hacia_deg` (azimut: 0 norte, 180 sur). La cota en cualquier punto es `cota_m + pendiente × avance en esa dirección`. |
| `contorno_chapa_m` | Rectángulo de la chapa, aleros incluidos. |
| `chapa` | Espesor y, si corresponde, paso de la junta alzada. |
| `tablero` | Tablero de cubierta: espesor, contorno y material. |
| `cabios` | Escuadría [ancho, alto], cantidad y el rango en X (primer y último eje) y en Y. |
| `apoyos_intermedios` | Vigas con sus postes: eje en Y, escuadrías, posiciones de postes. Las vigas largas van en `pendiente_calculo`. |
| `fascias` | Fascias perimetrales. |

### `cimientos`

Platea de hormigón con la huella de la casa (`contorno: "huella"`), espesor, junta bajo solera, solera inferior tratada con barrera capilar, pernos de anclaje (diámetro, empotramiento, separación máxima y distancia objetivo al extremo, criterio V06) y bases de postes. Estado `pendiente_calculo`: es un volumen de estudio sin armadura ni estudio de suelo.

Qué se deriva: la posición de cada perno sobre cada tramo de solera, los dados bajo postes y las soleras que necesitan una conexión especial.

### `carpinterias`

Criterios comunes a todas las aberturas: sección y material del marco, cantidad de hojas de ventana según el ancho, espesor y material de la hoja de puerta con su apertura por defecto, vuelo del alféizar y la regla del **dintel** (0,22 m hasta 2,6 m de vano; 0,30 m por encima; dos tablas con separadores de contrachapado; `pendiente_calculo`).

### `exteriores`

`galeria`: la cubierta que usa, el deck (contorno, tabla, paso, bastidor), el escalón y su equipamiento (banco, mesa, sillas, parrilla, maceta). `sendero_entrada`: volumen de acceso.

### `artefactos`

Artefactos sanitarios: los que tienen desagüe o agua (capas 12 y 13).

| Campo | Qué es |
| --- | --- |
| `tipo` | `inodoro`, `bidet`, `ducha`, `vanitory`, `bacha_cocina`, `pileta_lavadero`, `lavarropas`. |
| `ambiente` | Id del ambiente. |
| `centro_m`, `giro_deg`, `medidas_m` | Ubicación en planta; `medidas_m` [ancho, fondo] cuando el tipo no la fija (duchas, vanitories). |
| `desague.salida_m` | Punto de descarga del artefacto (x, y, z). De acá parte el ramal. |
| `desague.dn_mm` | Diámetro nominal: 110 inodoros, 50 el resto. |
| `desague.grupo` | Columna de desagüe a la que descarga (ver `instalaciones.sanitaria.desague.columnas`). |
| `agua.fria`, `agua.caliente` | Qué alimentaciones necesita. |

### `mobiliario`

Muebles y equipos sin instalación propia, como cajas con `centro_m`, `medidas_m` y `giro_deg`, más su `tipo` (cama, mesa, silla, bajo_mesada, heladera…) y `ambiente`. Es capa hook (MVP_01 §3.12): alcanza para dibujar la planta, verificar pasos y ubicar tomas, no para fabricar el mueble.

### `instalaciones`

**`electrica`**

| Campo | Qué es |
| --- | --- |
| `tablero` | Posición (x, y, z del centro), medidas y protecciones previstas. |
| `acometida`, `puesta_a_tierra` | Punto de llegada y jabalina. Ambos `pendiente_datos`. |
| `altura_distribucion_m` | Cota de las canalizaciones sobre el cielorraso. |
| `circuitos` | Id, uso y sección orientativa en mm². |
| `tomas` | Id (`Toma_…`), ambiente, posición del centro de la caja, circuito y `paralela_a` (la caja es paralela al eje X o al Y, según la pared). |
| `bocas_luz` | Id (`Luz_…`), ambiente, posición, circuito, `luminaria` (`plafon`, `colgante` o `null` si es solo la boca) y la `llave` que la comanda. |
| `llaves` | Id (`Llave_…`), ambiente, posición y orientación. |

Qué se deriva: recorridos de caños, conductores, desvíos para no pasar frente a ventanas y reservas en el cielorraso.

**`sanitaria`**

- `desague`: pendiente, línea del colector (`colector_y_m`), cota de eje al inicio, una columna por grupo de artefactos, cámaras de inspección, salida (`pendiente_datos`) y ventilación (`pendiente_datos`; V11 retiró los ramales).
- `agua`: entrada exterior, colector, cota de distribución, llave general, abastecimiento (`pendiente_datos`) y termotanque (tipo, capacidad, ubicación, circuito).

Qué se deriva: ramales, sifones, camisas y reservas en platea, y alimentaciones individuales con sus llaves de corte.

**`pluvial`**: una canaleta por cubierta con el borde donde va y hacia dónde baja; sección, pendiente, diámetro de la bajada y destino (`pendiente_datos`). Separado del cloacal.

### `materiales`

Paleta de materiales por clave: `nombre`, `color` (`#rrggbb`), `rugosidad` y `metalico` (0–1). Incluye los colores de V11 para el visor, y los de las instalaciones para distinguir fase, neutro, tierra, fría, caliente y cloacal. Cualquier campo `material` o `solado` de la casa apunta a una clave de acá.

## Validación

`Casa.model_validate(...)` (backend) rechaza:

- campos desconocidos (un error de tipeo no se pierde en silencio);
- ids repetidos en muros, aberturas, ambientes, cubiertas, circuitos, llaves, tomas y bocas de luz, artefactos y elementos;
- referencias rotas: sistema, cubierta, ambiente, circuito, llave, grupo de desagüe, solado o material inexistentes;
- muros oblicuos, aberturas fuera del muro o superpuestas, dinteles por debajo del antepecho;
- `lado_exterior` en un muro interior, o faltante en uno exterior;
- un ambiente sin contorno que no esté en `pendiente_datos`.

`test_caso_angus.py` compara además el caso con V11 ejecutado en memoria: ejes y extremos reales de cada muro, alturas con techo inclinado, cada abertura, dinteles, planos de las tres cubiertas, cabios, ambientes, artefactos, tomas, bocas de luz, circuitos, implantación, lote y los números de regresión.

```powershell
cd backend; .venv\Scripts\python -m pytest -q tests\test_caso_angus.py
```

La prueba necesita `angus_ranch_V11_11_capas.py` en la raíz del repositorio; si no está, se saltea.

## Regenerar el caso

Si cambia el script V11:

```powershell
python scripts\armar_caso_angus.py      # desde software/, con numpy instalado
```

Muros, aberturas, ambientes, lote y posiciones de tomas, bocas y artefactos se leen del script ejecutado. Mobiliario, cubiertas y parámetros de instalaciones están transcriptos en el generador: si V11 cambia alguno de esos, hay que actualizarlo ahí. Después, correr las pruebas.

## Preguntas abiertas del formato

1. **Espacios sin contorno.** El estar-comedor-cocina de Angus Ranch es el resto de la planta. ¿Lo dibuja el usuario, o se deriva como "lo que queda entre muros"?
2. **Eje de muros exteriores de esquina a esquina.** Es cómodo para la regla y para dibujar, pero en la interfaz puede convenir mostrar la cara exterior. Decidirlo al diseñar el editor de planta.
3. **Carpinterías de catálogo.** Hoy cada abertura guarda su vano libre. Cuando exista el catálogo AR (MVP_01 §3.3), la abertura debería apuntar a un producto y derivar el vano.
4. **Mobiliario.** ¿Biblioteca de tipos con medidas por defecto, o cajas libres como ahora?
5. **Dos aguas.** El tipo existe, pero ningún caso lo usa todavía: falta definir cumbrera y limatesas.
