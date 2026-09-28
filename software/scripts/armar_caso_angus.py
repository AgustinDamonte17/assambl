"""Arma software/casos/angus_ranch.assambl.json a partir de angus_ranch_V11_11_capas.py.

Muros, aberturas, ambientes y lote salen del script ejecutado; el resto se
transcribe de las llamadas de build_furniture/build_roof/agregar_instalaciones.
"""
import contextlib, importlib.util, io, json, math
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("v11", RAIZ / "angus_ranch_V11_11_capas.py")
v11 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v11)
c, t = v11.cargar_fuentes()
with contextlib.redirect_stdout(io.StringIO()):
    v11.preparar_y_comprobar(c, t)
anclajes, especiales = v11.augment_v06(c)
inst = v11.agregar_instalaciones(c)
filas = v11.timber_inventory(c)


def r(v, n=4):
    if isinstance(v, (list, tuple)):
        return [r(x, n) for x in v]
    x = round(float(v), n)
    return 0.0 if x == 0 else x


# ---------------------------------------------------------------- terreno
poly = [r(p, 2) for p in t["POLY"]]
lados = []
for i, a in enumerate(poly):
    b = poly[(i + 1) % len(poly)]
    lados.append({"longitud_m": r(math.dist(a, b), 3),
                  "rumbo_deg": r((math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) + 360) % 360, 2)})
area = abs(sum(x * v - u * y for (x, y), (u, v) in zip(poly, poly[1:] + poly[:1]))) / 2
perim = sum(math.dist(a, b) for a, b in zip(poly, poly[1:] + poly[:1]))

# ---------------------------------------------------------------- muros
STUD = c["STUD"]
esquinas = {}
for cid, xw, xe, yw, ye, x, y, tipo in c["CORNER_SPECS"]:
    esquinas[(xw, xe)] = (x, y)
    esquinas[(yw, ye)] = (x, y)
LADO = {("X", 1): "norte", ("X", -1): "sur", ("Y", 1): "este", ("Y", -1): "oeste"}
ANEXO = {"Este_anexo", "Sur_anexo", "Oeste_anexo", "Lavadero_Dorm3"}
TIPO_ABERTURA = {"ventana": "ventana", "corrediza": "ventana_corrediza", "puerta": "puerta", "paso": "paso"}

muros = []
for w in c["WALLS"]:
    def punto(extremo):
        if w["external"] and (w["name"], extremo) in esquinas:
            return esquinas[(w["name"], extremo)]
        u = w[extremo]
        return (u, w["pos"]) if w["axis"] == "X" else (w["pos"], u)
    desde, hasta = punto("start"), punto("end")
    u0 = desde[0] if w["axis"] == "X" else desde[1]
    sistema = "exterior" if w["external"] else ("interior_portante" if w["bearing"] else "tabique")
    muro = {"id": w["name"], "sistema": sistema,
            "eje": {"desde_m": r(desde), "hasta_m": r(hasta)}}
    if w["external"]:
        muro["lado_exterior"] = LADO[(w["axis"], w["outside"])]
    muro["altura"] = ({"tipo": "hasta_cubierta", "cubierta": "anexo_sur" if w["name"] in ANEXO else "principal"}
                      if sistema != "tabique" else {"tipo": "tabique"})
    aberturas = []
    for i, (a, b, z0, z1, kind) in enumerate(w["holes"]):
        ab = {"id": f"{w['name']}/O{i}", "tipo": TIPO_ABERTURA[kind],
              "posicion_m": r(a - u0), "ancho_m": r(b - a),
              "antepecho_m": r(z0), "dintel_m": r(z1)}
        if kind == "puerta":
            ab["hoja"] = {"bisagra": "inicio", "apertura_deg": c["DOOR_SWINGS"].get(f"{w['name']}_puerta", 70)}
        aberturas.append(ab)
    muro["aberturas"] = aberturas
    muros.append(muro)

# ---------------------------------------------------------------- ambientes
USO = {"Principal": ("dorm_principal", "Dormitorio principal", "dormitorio"),
       "Dormitorio 2": ("dorm_2", "Dormitorio 2", "dormitorio"),
       "Vestidor": ("vestidor", "Vestidor", "vestidor"),
       "Baño suite": ("bano_suite", "Baño suite", "bano"),
       "Baño": ("bano", "Baño", "bano"),
       "Lavadero": ("lavadero", "Lavadero", "lavadero"),
       "Dormitorio 3": ("dorm_3", "Dormitorio 3", "dormitorio"),
       "Oficina": ("oficina", "Oficina", "oficina")}
SOLADO = {"Roble natural": "roble_natural", "Porcelanato": "porcelanato", "Piso piedra": "piso_piedra"}
solados_v11 = {"Principal": "Roble natural", "Dormitorio 2": "Roble natural", "Vestidor": "Roble natural",
               "Baño suite": "Porcelanato", "Baño": "Porcelanato", "Lavadero": "Porcelanato",
               "Dormitorio 3": "Roble natural", "Oficina": "Piso piedra"}
ambientes = []
for room in c["ROOMS"]:
    aid, nombre, uso = USO[room["name"]]
    x0, y0, x1, y1 = room["bounds"]
    ambientes.append({"id": aid, "nombre": nombre, "uso": uso,
                      "contorno_m": r([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]),
                      "solado": SOLADO[solados_v11[room["name"]]],
                      "estado": "propuesto"})
ambientes.append({"id": "estar_comedor_cocina", "nombre": "Estar, comedor y cocina", "uso": "social",
                  "contorno_m": None, "solado": "piso_piedra", "estado": "pendiente_datos",
                  "nota": "V11 no delimita el espacio social: es el resto de la planta principal "
                          "(incluye el acceso y la circulación del ala este). Falta dibujar su contorno."})

# ---------------------------------------------------------------- artefactos sanitarios
# (id, tipo, ambiente, centro del artefacto, giro, medidas, salida de desagüe, DN, agua caliente, grupo)
ART = [
    ("Suite_WC", "inodoro", "bano_suite", (4.24, 4.96), None, (4.24, 4.99, .05), 110, False, "suite"),
    ("Suite_bidet", "bidet", "bano_suite", (5.14, 4.96), None, (5.14, 5.00, .28), 50, True, "suite"),
    ("Suite_ducha", "ducha", "bano_suite", (4.27, 7.15), (.95, 1.15), (4.27, 7.15, .035), 50, True, "suite"),
    ("Suite_lavatorio", "vanitory", "bano_suite", (5.19, 7.33), (.62, .54), (5.19, 7.33, .90), 50, True, "suite"),
    ("Cocina_bacha", "bacha_cocina", "estar_comedor_cocina", (8.33, .54), (.53, .40), (8.33, .54, .85), 50, True, "cocina"),
    ("Bano_WC", "inodoro", "bano", (11.54, -1.89), None, (11.54, -1.86, .05), 110, False, "bano"),
    ("Bano_bidet", "bidet", "bano", (12.36, -1.89), None, (12.36, -1.85, .28), 50, True, "bano"),
    ("Bano_ducha", "ducha", "bano", (10.35, -1.39), (.97, 1.52), (10.35, -1.39, .035), 50, True, "bano"),
    ("Bano_lavatorio", "vanitory", "bano", (11.29, -.39), (.62, .54), (11.29, -.39, .90), 50, True, "bano"),
    ("Lavadero_pileta", "pileta_lavadero", "lavadero", (13.52, -1.84), (.62, .54), (13.52, -1.84, .90), 50, True, "lavadero"),
    ("Lavadero_lavarropas", "lavarropas", "lavadero", (14.34, -1.87), (.64, .62), (14.34, -1.87, .70), 50, False, "lavadero"),
]
artefactos = []
for aid, tipo, amb, centro, medidas, salida, dn, ac, grupo in ART:
    a = {"id": aid, "tipo": tipo, "ambiente": amb, "centro_m": r(centro), "giro_deg": 0}
    if medidas:
        a["medidas_m"] = r(medidas)
    a["desague"] = {"salida_m": r(salida), "dn_mm": dn, "grupo": grupo}
    a["agua"] = {"fria": True, "caliente": ac}
    artefactos.append(a)

# ---------------------------------------------------------------- mobiliario
# (id, tipo, ambiente, centro xy, medidas [ancho x, fondo y, alto], giro_deg)
MOB = [
    ("Cocina_bajo_mesada", "bajo_mesada", "estar_comedor_cocina", (7.9, .54), (4.2, .6, .88), 0),
    ("Cocina_mesada", "mesada", "estar_comedor_cocina", (7.9, .54), (4.2, .69, .9475), 0),
    ("Cocina_anafe", "anafe_induccion", "estar_comedor_cocina", (6.55, .54), (.6, .52, .015), 0),
    ("Cocina_horno", "horno_empotrado", "estar_comedor_cocina", (6.55, .856), (.52, .025, .49), 0),
    ("Heladera", "heladera", "estar_comedor_cocina", (10.38, .56), (.72, .72, 2.10), 0),
    ("Isla", "isla", "estar_comedor_cocina", (8.15, 2.70), (2.3, 1.02, .9575), 0),
    ("Taburete_1", "taburete", "estar_comedor_cocina", (7.45, 3.40), (.40, .40, .70), 0),
    ("Taburete_2", "taburete", "estar_comedor_cocina", (8.15, 3.40), (.40, .40, .70), 0),
    ("Taburete_3", "taburete", "estar_comedor_cocina", (8.85, 3.40), (.40, .40, .70), 0),
    ("Mesa_comedor", "mesa", "estar_comedor_cocina", (8.2, 5.65), (1.05, 2.8, .7975), 0),
]
for s in (-1, 1):
    for i in range(4):
        MOB.append((f"Silla_comedor_{'O' if s < 0 else 'E'}{i + 1}", "silla", "estar_comedor_cocina",
                    (8.2 + s * .85, 4.6 + i * .7), (.46, .43, .925), -s * 90))
MOB += [
    ("Silla_cabecera_S", "silla", "estar_comedor_cocina", (8.2, 3.96), (.46, .43, .925), 180),
    ("Silla_cabecera_N", "silla", "estar_comedor_cocina", (8.2, 7.34), (.46, .43, .925), 0),
    ("Sofa", "sofa", "estar_comedor_cocina", (11.13, 5.95), (.92, 2.75, .985), 0),
    ("Sofa_chaise", "sofa_chaise", "estar_comedor_cocina", (11.85, 6.83), (.70, .82, .64), 0),
    ("Alfombra_living", "alfombra", "estar_comedor_cocina", (12.1, 5.75), (3.4, 3.1, .018), 0),
    ("Mesa_living", "mesa_baja", "estar_comedor_cocina", (12.55, 5.85), (.65, 1.15, .4275), 0),
    ("Mueble_TV", "mueble_bajo", "estar_comedor_cocina", (14.53, 5.80), (.46, 2.8, .65), 0),
    ("TV", "televisor", "estar_comedor_cocina", (14.45, 5.80), (.075, 1.36, .79), 0),
    ("Biblioteca_estar_S", "estanteria", "estar_comedor_cocina", (14.60, 4.6), (.32, .52, 2.2175), 0),
    ("Biblioteca_estar_N", "estanteria", "estar_comedor_cocina", (14.60, 7.0), (.32, .52, 2.2175), 0),
    ("Cama_principal", "cama", "dorm_principal", (1.85, 6.60), (1.68, 2.05, 1.22), 0),
    ("Mesa_luz_O", "mesa_luz", "dorm_principal", (.69, 7.22), (.44, .44, .65), 0),
    ("Mesa_luz_E", "mesa_luz", "dorm_principal", (3.0, 7.22), (.44, .44, .65), 0),
    ("Cama_dorm2", "cama", "dorm_2", (1.47, .92), (.98, 2.05, 1.22), 90),
    ("Estante_dorm2", "estante_mural", "dorm_2", (1.2, .25), (1.3, .16, .03), 0),
    ("Cama_dorm3", "cama", "dorm_3", (16.7, -.72), (1.08, 2.05, 1.22), 0),
    ("Placard_dorm3", "placard", "dorm_3", (15.30, -1.325), (.55, 1.55, 2.30), 0),
    ("Vestidor_mueble", "estanteria", "vestidor", (5.33, 3.92), (.53, .9, 2.25), 0),
    ("Escritorio", "escritorio", "oficina", (16.35, 6.64), (1.75, .75, .7825), 0),
    ("Silla_oficina", "silla", "oficina", (16.35, 5.92), (.46, .43, .925), 180),
    ("Biblioteca_oficina", "estanteria", "oficina", (16.95, 3.40), (1.4, .36, 2.2675), 0),
    ("Maceta_living", "planta", "estar_comedor_cocina", (14.0, 3.8), (.46, .46, 1.0), 0),
]
mobiliario = [{"id": i, "tipo": tp, "ambiente": a, "centro_m": r(ce), "medidas_m": r(me), "giro_deg": g}
              for i, tp, a, ce, me, g in MOB]

# ---------------------------------------------------------------- eléctrico
# V11 repite nombres entre tomas y bocas de luz ("Bano", "Suite"): separar por tipo.
por_tipo = {tipo: {x["nombre"]: x for x in inst["terminales"] if x["tipo"] == tipo}
            for tipo in ("toma", "boca_luz")}
CIRC = [("IUG", "Iluminación", 1.5), ("TUG_D", "Tomas dormitorios", 2.5), ("TUG_E", "Tomas estar y oficina", 2.5),
        ("TUG_C", "Tomas de mesada", 2.5), ("TUG_B", "Tomas baños", 2.5), ("HEL", "Heladera", 2.5),
        ("LAV", "Lavarropas", 2.5), ("HOR", "Horno", 4.0), ("ANA", "Anafe", 6.0), ("TER", "Termotanque", 2.5)]
TOMAS = [
    ('Dorm_principal_1', 'dorm_principal', 'y'), ('Dorm_principal_2', 'dorm_principal', 'y'),
    ('Dorm_principal_3', 'dorm_principal', 'x'), ('Dorm2_1', 'dorm_2', 'y'), ('Dorm2_2', 'dorm_2', 'y'),
    ('Dorm3_1', 'dorm_3', 'y'), ('Dorm3_2', 'dorm_3', 'y'), ('Estar_TV', 'estar_comedor_cocina', 'y'),
    ('Estar_aux', 'estar_comedor_cocina', 'y'), ('Comedor', 'estar_comedor_cocina', 'y'),
    ('Oficina_1', 'oficina', 'x'), ('Oficina_2', 'oficina', 'y'), ('Oficina_3', 'oficina', 'y'),
    ('Mesada_1', 'estar_comedor_cocina', 'x'), ('Mesada_2', 'estar_comedor_cocina', 'x'),
    ('Heladera', 'estar_comedor_cocina', 'x'), ('Horno', 'estar_comedor_cocina', 'x'),
    ('Anafe', 'estar_comedor_cocina', 'x'), ('Lavarropas', 'lavadero', 'x'), ('Termotanque', 'lavadero', 'x'),
    ('Bano', 'bano', 'y'), ('Suite', 'bano_suite', 'y')]
tomas = [{"id": "Toma_" + n, "ambiente": a, "posicion_m": r(por_tipo["toma"][n]["posicion"]), "circuito": por_tipo["toma"][n]["circuito"],
          "paralela_a": o} for n, a, o in TOMAS]
LUCES = [  # id, ambiente, luminaria V04, llave (posición), orientación de la llave
    ('Dorm_principal', 'dorm_principal', 'plafon', (2.42, 3.51, 1.10), 'x'),
    ('Dorm2', 'dorm_2', 'plafon', (1.50, 2.04, 1.10), 'x'),
    ('Suite', 'bano_suite', 'plafon', (3.85, 6.42, 1.10), 'y'),
    ('Bano', 'bano', 'plafon', (11.86, -.08, 1.10), 'x'),
    ('Lavadero', 'lavadero', 'plafon', (13.26, -.08, 1.10), 'x'),
    ('Dorm3', 'dorm_3', 'plafon', (16.25, 1.10, 1.10), 'x'),
    ('Oficina', 'oficina', 'plafon', (16.25, 3.30, 1.10), 'x'),
    ('Estar', 'estar_comedor_cocina', 'plafon', (17.70, 2.80, 1.10), 'y'),
    ('Cocina', 'estar_comedor_cocina', 'plafon', (5.88, 3.70, 1.10), 'y'),
    ('Vestidor', 'vestidor', None, (5.48, 4.30, 1.10), 'x'),
]
llaves = [{"id": "Llave_" + n, "ambiente": a, "posicion_m": r(p), "paralela_a": o} for n, a, _, p, o in LUCES]
bocas = [{"id": "Luz_" + n, "ambiente": a, "posicion_m": r(por_tipo["boca_luz"][n]["posicion"]), "circuito": "IUG",
          "luminaria": lum, "llave": "Llave_" + n} for n, a, lum, _, _ in LUCES]
bocas += [{"id": f"Luz_Colgante_{i}", "ambiente": "estar_comedor_cocina", "posicion_m": r(por_tipo["boca_luz"][f"Colgante_{i}"]["posicion"]),
           "circuito": "IUG", "luminaria": "colgante", "llave": "Llave_Estar"} for i in range(3)]
assert len(tomas) + len(bocas) + len(ART) == len(inst["terminales"])

def clave(nombre):
    k = nombre.replace(" V06", "").lower()
    for a, b in zip("áéíóú ", "aeiou_"):
        k = k.replace(a, b)
    return k


materiales = {}
for nombre, m in c["MATERIALS"].items():
    if nombre.startswith("Madera header"):
        continue  # variantes de color de estudio para distinguir las dos hojas del dintel
    materiales[clave(nombre)] = {"nombre": nombre.replace(" V06", ""),
                                 "color": "#" + "".join("%02x" % round(v * 255) for v in m["color"][:3]),
                                 "rugosidad": m["roughness"], "metalico": m["metallic"]}

casa = {
    "esquema": "assambl/casa@0.1",
    "nombre": "Angus Ranch",
    "origen": {
        "fuente": "angus_ranch_V11_11_capas.py",
        "version": "V11",
        "regresion": {"piezas_madera": len(filas), "pernos_solera": len(anclajes),
                      "soleras_con_anclaje_especial": len(especiales)},
        "nota": "Transcripción declarativa de V11. Las piezas, capas y cómputos se derivan con reglas; no se guardan acá.",
    },
    "unidades": "m",
    "ejes": {"x": "este", "y": "norte", "z": "arriba", "origen": "esquina suroeste de la planta principal, sobre el piso terminado"},
    "implantacion": {
        "origen_en_lote_m": r(v11.local_a_lote(0, 0)),
        "giro_deg": v11.IMPLANTACION["giro_grados"],
        "cota_piso_sobre_terreno_m": v11.IMPLANTACION["cota_piso_m"],
    },
    "huella_m": [[0.0, 0.0], [9.6, 0.0], [9.6, -2.4], [18.0, -2.4], [18.0, 8.0], [0.0, 8.0]],
    "sistemas": {
        "exterior": {
            "descripcion": "Muro exterior woodframe 45 × 140 con OSB, WRB, cámara ventilada y siding",
            "espesor_arquitectonico_m": 0.20,
            "capas": [
                {"capa": "terminacion_interior", "material": "revoque_calido", "espesor_mm": 12.5},
                {"capa": "entramado", "seccion_mm": [45, 140], "modulo_mm": 600, "material": "madera_estructura"},
                {"capa": "aislante", "material": "lana_mineral", "espesor_mm": 140},
                {"capa": "osb", "material": "osb", "espesor_mm": 12, "placa_mm": [1200, 2400], "junta_mm": 3.2},
                {"capa": "wrb", "material": "wrb", "solape_mm": 150, "retorno_esquina_mm": 300},
                {"capa": "camara_ventilada", "espesor_mm": 25, "liston_mm": [45, 25], "material": "madera_estructura"},
                {"capa": "siding", "material": "siding_oscuro", "espesor_mm": 20, "paso_mm": 180,
                 "esquinero_mm": 100, "junta_esquinero_mm": 3},
            ],
        },
        "interior_portante": {
            "descripcion": "Tabique portante 45 × 140, revoque en ambas caras",
            "espesor_arquitectonico_m": 0.20,
            "capas": [{"capa": "entramado", "seccion_mm": [45, 140], "modulo_mm": 600, "material": "madera_estructura"}],
            "terminacion": "revoque_calido",
        },
        "tabique": {
            "descripcion": "Tabique no portante 45 × 90, revoque en ambas caras",
            "espesor_arquitectonico_m": 0.15,
            "capas": [{"capa": "entramado", "seccion_mm": [45, 90], "modulo_mm": 600, "material": "madera_estructura"}],
            "terminacion": "revoque_calido",
        },
    },
    "parametros": {
        "altura_tabiques_m": 2.80,
        "esquinas": "el muro paralelo a X pasa de largo; el paralelo a Y apoya contra su cara",
        "zocalo": {"desde_m": 0.03, "hasta_m": 0.11, "espesor_mm": 14, "material": "roble_natural"},
        "cielorraso": {"cara_inferior_m": 2.76, "espesor_m": 0.07, "material": "revoque_calido",
                       "zonas_m": [[0, 0, 18, 8], [9.6, -2.4, 18, 0]]},
        "solado_general": "piso_piedra",
    },
    "muros": muros,
    "ambientes": ambientes,
    "cubiertas": [
        {"id": "principal", "tipo": "un_agua", "material": "zinc",
         "plano_apoyo": {"cota_m": 3.35, "en_m": [0, 0], "pendiente_pct": 6.0, "sube_hacia_deg": 0},
         "contorno_chapa_m": [-0.40, -0.40, 18.40, 8.40],
         "chapa": {"espesor_mm": 35, "junta_alzada_paso_m": 0.5},
         "tablero": {"espesor_mm": 18, "contorno_m": [-0.35, -0.35, 18.35, 8.35], "material": "roble_natural"},
         "cabios": {"seccion_mm": [63, 240], "cantidad": 31, "desde_x_m": 0.08, "hasta_x_m": 17.92,
                    "desde_y_m": -0.35, "hasta_y_m": 8.35},
         "apoyos_intermedios": [{"tipo": "viga", "eje_y_m": 4.0, "seccion_mm": [200, 620],
                                 "postes_x_m": [0.1, 5.7, 14.9, 17.9], "seccion_poste_mm": [200, 200],
                                 "estado": "pendiente_calculo",
                                 "nota": "Viga de 9,2 m entre postes: madera laminada o ingeniería a definir."}],
         "fascias": {"altura_m": 0.34, "espesor_mm": 50, "material": "grafito"}},
        {"id": "anexo_sur", "tipo": "un_agua", "material": "zinc",
         "plano_apoyo": {"cota_m": 3.0, "en_m": [0, -2.3], "pendiente_pct": 10.0, "sube_hacia_deg": 0},
         "contorno_chapa_m": [9.35, -2.80, 18.40, 0.17],
         "chapa": {"espesor_mm": 35},
         "tablero": {"espesor_mm": 18, "contorno_m": [9.40, -2.75, 18.35, 0.15], "material": "roble_natural"},
         "cabios": {"seccion_mm": [63, 180], "cantidad": 15, "desde_x_m": 9.67, "hasta_x_m": 17.93,
                    "desde_y_m": -2.70, "hasta_y_m": 0.15},
         "apoyos_intermedios": [{"tipo": "viga_alta", "eje_y_m": 0.08, "seccion_mm": [140, 280],
                                 "postes_x_m": [9.7, 12.975, 14.9, 17.9], "seccion_poste_mm": [140, 140],
                                 "estado": "pendiente_calculo"}],
         "nota": "Encuentro con la cubierta principal e impermeabilización por desarrollar."},
        {"id": "galeria", "tipo": "un_agua", "material": "zinc",
         "plano_apoyo": {"cota_m": 3.03, "en_m": [0, 8.0], "pendiente_pct": 6.0, "sube_hacia_deg": 180},
         "contorno_chapa_m": [4.90, 7.98, 15.10, 11.15],
         "chapa": {"espesor_mm": 30},
         "cabios": {"seccion_mm": [60, 140], "cantidad": 21, "desde_x_m": 5.0, "hasta_x_m": 15.0,
                    "desde_y_m": 8.0, "hasta_y_m": 11.1},
         "apoyos_intermedios": [{"tipo": "viga", "eje_y_m": y, "seccion_mm": [140, 200], "largo_m": 10.2,
                                 "postes_x_m": [5.1, 10.0, 14.9], "seccion_poste_mm": [140, 140],
                                 "estado": "pendiente_calculo"} for y in (8.15, 10.85)]},
    ],
    "cimientos": {
        "tipo": "platea",
        "contorno": "huella",
        "espesor_m": 0.36,
        "junta_bajo_solera_mm": 3,
        "solera_inferior": {"material": "madera_tratada", "barrera_capilar": True},
        "pernos": {"diametro_mm": 12.7, "empotramiento_mm": 180, "separacion_max_m": 1.20,
                   "distancia_extremo_objetivo_m": 0.20, "forma": "L"},
        "bases_postes": {"dado_m": [0.45, 0.45, 0.594], "elevacion_mm": 50, "tipo": "base_U"},
        "estado": "pendiente_calculo",
        "nota": "Volumen de estudio: sin armadura ni estudio de suelo.",
    },
    "carpinterias": {
        "marco": {"seccion_mm": [46, 65], "material": "grafito"},
        "hojas_ventana": "1 hasta 1,10 m de ancho, 2 hasta 3 m, 4 por encima",
        "puerta": {"hoja_mm": 40, "material": "roble_natural", "apertura_deg_por_defecto": 70},
        "alfeizar": {"vuelo_m": 0.04, "material": "piso_piedra"},
        "dintel": {"tipo": "doble_tabla_con_separadores", "altura_m": {"hasta_2_6_m": 0.22, "mayor": 0.30},
                   "separadores": "4 de contrachapado 12,5 mm", "estado": "pendiente_calculo"},
    },
    "exteriores": {
        "galeria": {"cubierta": "galeria",
                    "deck": {"contorno_m": [5.0, 8.0, 15.0, 11.0], "tabla_mm": [132, 30], "paso_mm": 139,
                             "bastidor_alto_m": 0.18, "material": "madera_exterior"},
                    "escalon": {"centro_m": [10.0, 11.24], "medidas_m": [4.0, 0.45, 0.13], "material": "piso_piedra"},
                    "equipamiento": [
                        {"id": "Banco_galeria", "tipo": "banco", "centro_m": [6.7, 10.5], "medidas_m": [2.3, 0.6, 0.525], "giro_deg": 0},
                        {"id": "Mesa_galeria", "tipo": "mesa", "centro_m": [9.2, 10.0], "medidas_m": [1.2, 0.7, 0.46], "giro_deg": 0},
                        {"id": "Silla_galeria_1", "tipo": "silla", "centro_m": [8.85, 10.65], "medidas_m": [0.46, 0.43, 0.925], "giro_deg": 0},
                        {"id": "Silla_galeria_2", "tipo": "silla", "centro_m": [9.55, 10.65], "medidas_m": [0.46, 0.43, 0.925], "giro_deg": 0},
                        {"id": "Parrilla", "tipo": "parrilla", "centro_m": [14.4, 9.5], "medidas_m": [0.8, 1.4, 3.48], "giro_deg": 0,
                         "estado": "pendiente_revision",
                         "nota": "Volumetría. Resolver aislación, distancias y salida de humos."},
                        {"id": "Maceta_galeria", "tipo": "planta", "centro_m": [5.5, 8.7], "medidas_m": [0.46, 0.46, 1.0], "giro_deg": 0}]},
        "sendero_entrada": {"centro_m": [19.0, 2.1], "medidas_m": [2.0, 1.3], "material": "piso_piedra"},
    },
    "artefactos": artefactos,
    "mobiliario": mobiliario,
    "instalaciones": {
        "electrica": {
            "tablero": {"posicion_m": r(inst["tablero_xyz_local_m"]), "medidas_m": [0.18, 0.48, 0.62],
                        "protecciones": "Seccionador general, DPS, diferenciales 30 mA y termomagnéticas por circuito"},
            "acometida": {"desde_m": [18.60, 3.05, -0.48], "estado": "pendiente_datos",
                          "nota": "Medidor y potencia a definir"},
            "puesta_a_tierra": {"jabalina_m": [18.65, 2.95], "hasta_cota_m": -1.95, "estado": "pendiente_datos"},
            "altura_distribucion_m": v11.INSTALACIONES["altura_distribucion_electrica_m"],
            "circuitos": [{"id": i, "uso": u, "seccion_mm2": s} for i, u, s in CIRC],
            "tomas": tomas,
            "bocas_luz": bocas,
            "llaves": llaves,
        },
        "sanitaria": {
            "desague": {"pendiente": v11.INSTALACIONES["pendiente_desague"],
                        "colector_y_m": v11.INSTALACIONES["y_colector_cloacal_m"],
                        "cota_eje_inicio_m": v11.INSTALACIONES["cota_eje_inicio_colectores_m"],
                        "columnas": [{"grupo": g, "x_m": x} for g, x in
                                     [("suite", 6.15), ("cocina", 9.15), ("bano", 12.70), ("lavadero", 14.65)]],
                        "camaras_inspeccion": [{"id": "CI_suite", "x_m": 6.15}, {"id": "CI_servicios", "x_m": 14.65},
                                               {"id": "CI_salida", "x_m": 19.2}],
                        "salida": {"x_m": 20.2, "estado": "pendiente_datos",
                                   "nota": "Red cloacal o tratamiento a definir"},
                        "ventilacion": {"estado": "pendiente_datos",
                                        "nota": "V11 retiró los dos ramales de ventilación; falta redefinirla"}},
            "agua": {"entrada_m": [14.45, -3.85, -0.48], "colector_m": [14.45, -0.65],
                     "altura_distribucion_m": v11.INSTALACIONES["altura_distribucion_agua_m"],
                     "llave_general_m": [14.45, -0.65, 1.25],
                     "abastecimiento": {"estado": "pendiente_datos", "nota": "Tanque, bomba o red a definir"},
                     "termotanque": {"tipo": "electrico", "capacidad_l": 60, "centro_m": [14.30, -1.87, 1.91],
                                     "medidas_m": [0.48, 0.48, 0.68], "circuito": "TER"}},
        },
        "pluvial": {
            "canaletas": [{"cubierta": "principal", "borde": "sur", "bajada": "oeste"},
                          {"cubierta": "anexo_sur", "borde": "sur", "bajada": "este"},
                          {"cubierta": "galeria", "borde": "norte", "bajada": "este"}],
            "seccion_mm": [160, 120], "pendiente": 0.003, "bajada_dn_mm": 90, "material": "zinc",
            "destino": {"estado": "pendiente_datos", "nota": "Separado del cloacal; destino a definir"},
        },
    },
    "materiales": materiales,
}

proyecto = {
    "esquema": "assambl/proyecto@0.2",
    "id": "caso-angus-ranch",
    "nombre": "Angus Ranch",
    "mercado": "AR",
    "creado": "2026-09-28T00:00:00Z",
    "modificado": "2026-09-28T00:00:00Z",
    "terreno": {
        "estado": "propuesto",
        "ubicacion": None,
        "margen_m": 500,
        "sistema_local": None,
        "escena_ref": None,
        "lote": {"origen": poly[0], "lados": lados, "vertices": poly,
                 "area_m2": r(area, 1), "perimetro_m": r(perim, 2),
                 "fuente": "trazado sobre imagen (terreno_angus_ranch_V01.py), escalado a 2500 m²; no es una mensura"},
        "retiros": {"frente_m": 3, "fondo_m": 3, "laterales_m": 0},
        "pendiente": None,
        "fecha_sol": "2026-09-28",
        "hora_sol": 12,
        "huso_h": None,
    },
    "casa": casa,
}
destino = RAIZ / "software/casos/angus_ranch.assambl.json"
destino.parent.mkdir(exist_ok=True)
import re
texto = json.dumps(proyecto, ensure_ascii=False, indent=2)
# Listas de números en una sola línea: coordenadas y medidas legibles a mano.
texto = re.sub(r"\[\s*((?:-?[\d.]+|null)(?:,\s*(?:-?[\d.]+|null))*)\s*\]",
               lambda m: "[" + ", ".join(x.strip() for x in m.group(1).split(",")) + "]", texto)
texto = re.sub(r"\[\s*(\[[^\[\]]*\](?:,\s*\[[^\[\]]*\])*)\s*\]",
               lambda m: "[" + re.sub(r",\s*\[", ", [", m.group(1)) + "]", texto)
destino.write_text(texto + "\n", encoding="utf-8")
print("ok", destino, destino.stat().st_size)
