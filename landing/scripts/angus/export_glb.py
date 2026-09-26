"""Exporta Angus Ranch V11 a un GLB web con nodos explícitos para el explode.

Uso (desde landing/):
    python3 scripts/angus/export_glb.py            # usa ../angus_ranch_V11_11_capas.py
    python3 scripts/angus/export_glb.py --source RUTA --out public/models/angus-ranch.glb

Requiere Python 3.10+ y numpy. No requiere Blender: reutiliza la geometría que el
script V11 construye en memoria (las mismas funciones que usa su modo --check) y
no modifica el script fuente ni genera archivos a su lado.

Sistema de coordenadas
    Fuente: metros, X este, Y norte, Z arriba. Casa en coordenadas locales V04,
    terreno en coordenadas de lote. Se convierte todo a coordenadas locales de la
    casa con el pivote de IMPLANTACION en el origen y la cota de piso aplicada.
    glTF: Y arriba, -Z norte  ->  (x, y, z)_gltf = (x, z, -y)_blender.

Jerarquía exportada (el nombre de cada nodo es el identificador estable)
    AngusRanch
      L01_Terreno ... L10_Electrico       nodos de capa, identidad, no se animan
        <capa>__<parte>[__<fachada>]      nodos animables, pivote = centro de su caja
    Solo se animan las hojas. extras (userData en three.js): layer, part, facade,
    dir (dirección de fachada en planta, glTF XZ), size (caja en metros).

Cada hoja lleva una sola malla con COLOR_0 (color lineal del material original) y,
si corresponde, una segunda primitiva para vidrio. Se fusionan todas las piezas que
comparten capa, parte y fachada: el explode no necesita más independencia.
"""

import argparse
import contextlib
import importlib.util
import io
import json
import math
import random
import struct
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True  # no dejar __pycache__ junto al script fuente

HERE = Path(__file__).resolve().parent
LANDING = HERE.parent.parent
DEFAULT_SOURCE = LANDING.parent / 'angus_ranch_V11_11_capas.py'
DEFAULT_OUT = LANDING / 'public' / 'models' / 'angus-ranch.glb'
# El reporte no se publica: queda junto al exportador.
REPORT = HERE / 'angus-ranch.report.json'

# Piezas cuya caja es menor que esto (m) no se ven a la escala del landing
# (tuercas, arandelas, tornillos). Se informan en el reporte.
MIN_DIAGONAL_M = 0.06

# ---------------------------------------------------------------------------
# Unidades de animación. Colección V11 -> (capa, parte, ¿separar por fachada?)
# Las capas son las View Layers de V11; las partes, subdivisiones del explode.
# ---------------------------------------------------------------------------
LAYERS = [
    ('L01_Terreno', '01_Terreno'),
    ('L02_Cimientos', '02_Cimientos'),
    ('L03_Estructura', '03_Estructura'),
    ('L04_Aislante', '04_Aislante'),
    ('L05_Siding', '05_Siding'),
    ('L06_Techo', '06_Techo'),
    ('L07_Interior', '07_Interior'),
    ('L08_Terminaciones', '08_Terminaciones'),
    ('L09_Plomeria', '09_Plomeria'),
    ('L10_Electrico', '10_Electrico'),
]

COLLECTIONS = {
    '16e_V06_Hormigon': ('L02_Cimientos', 'platea', False),
    '16a_V06_Soleras_tratadas': ('L02_Cimientos', 'soleras', False),
    '16b_V06_Barrera_capilar': ('L02_Cimientos', 'soleras', False),
    '16c_V06_Pernos_arandelas_tuercas': ('L02_Cimientos', 'soleras', False),
    '16d_V06_Bases_postes': ('L02_Cimientos', 'platea', False),
    '08a_Entramado_paredes': ('L03_Estructura', 'entramado', False),
    '08d_Postes_en_muros': ('L03_Estructura', 'entramado', False),
    '15a_V06_Headers_dos_tablas': ('L03_Estructura', 'entramado', False),
    '15b_V06_Separadores_headers': ('L03_Estructura', 'entramado', False),
    '16f_V06_Postes_galeria': ('L03_Estructura', 'galeria', False),
    '10_05_Insulation': ('L04_Aislante', 'lana', True),
    '13_08_Camara_listones': ('L05_Siding', 'listones', True),
    '14_08_Siding': ('L05_Siding', 'siding', True),
    '08b_Estructura_techo': ('L06_Techo', 'estructura', False),
    '08c_Tablero_techo': ('L06_Techo', 'tablero', False),
    '06b_Cubiertas': ('L06_Techo', 'cubierta', False),
    '06c_Cubierta_galeria': ('L06_Techo', 'cubierta', False),
    '00_Base': ('L07_Interior', 'pisos', False),
    '02_Tabiques': ('L07_Interior', 'tabiques', False),
    '04a_Cocina': ('L07_Interior', 'equipamiento', False),
    '04b_Social': ('L07_Interior', 'equipamiento', False),
    '04c_Dormitorios': ('L07_Interior', 'equipamiento', False),
    '04d_Banos_lavadero': ('L07_Interior', 'equipamiento', False),
    '04e_Oficina': ('L07_Interior', 'equipamiento', False),
    '01_Muros_exteriores': ('L08_Terminaciones', 'revestimiento_interior', False),
    '03_Carpinterias': ('L08_Terminaciones', 'carpinterias', True),
    '06a_Cielorraso': ('L08_Terminaciones', 'cielorraso', False),
    '07_Exterior': ('L08_Terminaciones', 'galeria', False),
    '11_06_OSB': ('L08_Terminaciones', 'osb', True),
    '12_07_WRB': ('L08_Terminaciones', 'wrb', True),
    '21_Desagues_sanitarios': ('L09_Plomeria', 'redes', False),
    '22_Agua_fria_caliente': ('L09_Plomeria', 'redes', False),
    # V11: canaletas, babetas y bajadas. Cuelgan del alero y bajan al terreno:
    # quedan en su lugar (no suben con la cubierta) y se nombran en 09_Plomeria.
    '23_Pluviales_canaletas': ('L09_Plomeria', 'pluviales', False),
    '20_Instalacion_electrica': ('L10_Electrico', 'redes', False),
    '05_Iluminacion': ('L10_Electrico', 'luminarias', False),
}

# Fachadas: dirección hacia afuera en planta (Blender XY). Las esquinas se mueven
# en diagonal para seguir a las dos caras que unen. Oeste_anexo lleva una leve
# componente sur para no cruzarse con Sur_principal en el encuentro entrante.
FACADES = {
    'Norte': ('N', (0, 1)), 'Sur_principal': ('S', (0, -1)), 'Sur_anexo': ('S', (0, -1)),
    'Este': ('E', (1, 0)), 'Este_anexo': ('E', (1, 0)), 'Oeste': ('O', (-1, 0)),
    'Oeste_anexo': ('OA', (-1, -1.15)),
    'Esquina_NO': ('NO', (-1, 1)), 'Esquina_NE': ('NE', (1, 1)),
    'Esquina_SE': ('SE', (1, -1)), 'Esquina_SO': ('SO', (-1, -1)),
    'Esquina_SO_anexo': ('SO', (-1, -1)), 'Esquina_Entrante': ('SO', (-1, -1)),
}

GLASS = 'Vidrio'


def srgb_to_linear(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def load_source(path):
    spec = importlib.util.spec_from_file_location('angus_v09', path)
    mod = importlib.util.module_from_spec(spec)
    argv = sys.argv
    sys.argv = [str(path), '--check']
    try:
        spec.loader.exec_module(mod)
        # Mismo recorrido que main_v06() en modo --check (solo lectura).
        with contextlib.redirect_stdout(io.StringIO()):
            casa, terreno = mod.cargar_fuentes()
            informe = mod.preparar_y_comprobar(casa, terreno)
            mod.augment_v06(casa)
            mod.agregar_instalaciones(casa)
            casa['validate']()
    finally:
        sys.argv = argv
    return mod, casa, terreno, informe


class Part:
    """Geometría fusionada de una hoja animable, en coordenadas locales Blender."""

    def __init__(self):
        self.prims = {False: ([], [], []), True: ([], [], [])}  # glass? -> (verts, cols, tris)
        self.pieces = 0

    def add(self, verts, faces, color):
        v = np.asarray(verts, dtype=np.float64)
        verts_l, cols_l, tris_l = self.prims[color[3] < 1]
        base = sum(len(a) for a in verts_l)
        tris = [(f[0], f[j], f[j + 1]) for f in faces for j in range(1, len(f) - 1)]
        if not tris:
            return
        verts_l.append(v)
        cols_l.append(np.tile(np.asarray(color, dtype=np.float64), (len(v), 1)))
        tris_l.append(np.asarray(tris, dtype=np.int64) + base)
        self.pieces += 1

    def bounds(self):
        allv = [a for glass in (False, True) for a in self.prims[glass][0]]
        v = np.concatenate(allv)
        return v.min(0), v.max(0)


def triangulate_polygon(poly):
    """Ear clipping para el contorno del lote (simple, sin huecos)."""
    pts = list(poly)
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))
    idx = list(range(len(pts)))
    if area < 0:
        idx.reverse()

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def inside(p, a, b, c):
        return cross(a, b, p) >= 0 and cross(b, c, p) >= 0 and cross(c, a, p) >= 0

    tris = []
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = pts[i0], pts[i1], pts[i2]
            if cross(a, b, c) <= 0:
                continue
            if any(inside(pts[j], a, b, c) for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append((i0, i1, i2))
            del idx[k]
            break
    tris.append(tuple(idx))
    return tris


def terrain_geometry(mod, terreno, informe, add):
    """Lote V01 (maqueta con canto), postes del alambrado y árboles del lote.

    Replica la generación de terreno V01 sin bpy: mismo contorno, misma semilla y
    mismo orden de llamadas al generador aleatorio para las copas.
    """
    T = terreno
    to_local = mod.lote_a_local
    poly = [to_local(x, y) for x, y in T['POLY']]
    depth = 0.8  # canto de la maqueta; solo representación
    top = [(x, y, 0.0) for x, y in poly]
    bot = [(x, y, -depth) for x, y in poly]
    n = len(poly)
    faces = [list(t) for t in triangulate_polygon(poly)]
    faces += [[n + c, n + b, n + a] for a, b, c in faces]
    faces += [[i, n + i, n + (i + 1) % n, (i + 1) % n] for i in range(n)]
    grass = (0.30, 0.32, 0.16, 1)  # TER_V01_pasto_ralo (lineal)
    add('L01_Terreno', 'lote', None, top + bot, faces, grass)

    rng = random.Random(T['SEMILLA'])
    bark = (0.22, 0.15, 0.08, 1)
    leaves = [(0.13, 0.23, 0.13, 1), (0.19, 0.28, 0.15, 1), (0.24, 0.31, 0.19, 1),
              (0.16, 0.25, 0.21, 1), (0.27, 0.32, 0.17, 1)]

    def cylinder(out, a, b, r, sides=8, top_ratio=0.7):
        a, b = np.array(a, float), np.array(b, float)
        axis = (b - a) / np.linalg.norm(b - a)
        helper = np.array([0, 0, 1.]) if abs(axis[2]) < 0.95 else np.array([1., 0, 0])
        u = np.cross(axis, helper); u /= np.linalg.norm(u)
        v = np.cross(axis, u)
        vs = []
        for center, radius in [(a, r), (b, r * top_ratio)]:
            for k in range(sides):
                d = u * math.cos(k * math.tau / sides) + v * math.sin(k * math.tau / sides)
                vs.append(tuple(center + d * radius))
        fs = [list(reversed(range(sides))), [sides + k for k in range(sides)]]
        fs += [[k, (k + 1) % sides, sides + (k + 1) % sides, sides + k] for k in range(sides)]
        out.append((vs, fs))

    def crown(out, center, scale):
        sides, rings = 10, 5
        vs = [(center[0], center[1], center[2] + scale[2])]
        for j in range(1, rings):
            phi = math.pi * j / rings
            for k in range(sides):
                theta = math.tau * k / sides
                irr = rng.uniform(0.88, 1.12)
                vs.append((center[0] + scale[0] * math.sin(phi) * math.cos(theta) * irr,
                           center[1] + scale[1] * math.sin(phi) * math.sin(theta) * irr,
                           center[2] + scale[2] * math.cos(phi)))
        bottom = len(vs)
        vs.append((center[0], center[1], center[2] - scale[2]))
        fs = [[0, 1 + k, 1 + (k + 1) % sides] for k in range(sides)]
        for j in range(rings - 2):
            a = 1 + j * sides
            b = a + sides
            fs += [[a + k, b + k, b + (k + 1) % sides, a + (k + 1) % sides] for k in range(sides)]
        a = 1 + (rings - 2) * sides
        fs += [[bottom, a + (k + 1) % sides, a + k] for k in range(sides)]
        out.append((vs, fs))

    hidden = set(informe['arboles_interferencia_copa_techo'])
    for i, (px, py, r, h) in enumerate(T['ARBOLES_PX'], 1):
        r = r * T['SCALE']
        trunks, crowns = [], []
        cylinder(trunks, (0, 0, 0), (0, 0, h * 0.66), max(0.07, r * 0.08))
        mat = rng.randrange(len(leaves))
        crown(crowns, (0, 0, h * 0.72), (r * 0.72, r * 0.72, h * 0.28))
        for k in range(5):
            angle = math.tau * k / 5 + rng.uniform(-0.25, 0.25)
            dx, dy = math.cos(angle) * r * 0.45, math.sin(angle) * r * 0.45
            cz = h * rng.uniform(0.53, 0.70)
            cylinder(trunks, (0, 0, h * 0.36), (dx, dy, cz), max(0.045, r * 0.035))
            crown(crowns, (dx, dy, cz), (r * 0.56, r * 0.56, h * 0.25))
        if i in hidden:  # V05 los oculta por interferir con el techo; se respeta
            continue
        x, y = to_local(*T['to_world']((px, py)))
        for parts, color in [(trunks, bark), (crowns, leaves[mat])]:
            for vs, fs in parts:
                add('L01_Terreno', 'arboles', None, [(vx + x, vy + y, vz) for vx, vy, vz in vs], fs, color)

    for a, b in zip(T['POLY'], T['POLY'][1:] + T['POLY'][:1]):
        count = max(1, math.ceil(math.dist(a, b) / T['SEPARACION_POSTES_M']))
        for j in range(count):
            t = j / count
            x, y = to_local(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            posts = []
            cylinder(posts, (x, y, -0.15), (x, y, T['ALTURA_POSTE_M']), 0.055, top_ratio=1)
            for vs, fs in posts:
                add('L01_Terreno', 'alambrado', None, vs, fs, bark)


def build(source):
    mod, casa, terreno, informe = load_source(source)
    px, py = mod.IMPLANTACION['pivote_local_xy_m']
    floor = mod.IMPLANTACION['cota_piso_m']
    if mod.IMPLANTACION['giro_grados'] != 0:
        raise SystemExit('giro_grados != 0: revisar la conversión de fachadas antes de exportar.')

    parts = defaultdict(Part)
    meta = {}
    report = {'fuente': Path(source).name, 'piezas_fuente': len(casa['OBJECTS']),
              'piezas_omitidas_por_tamano': defaultdict(int), 'colecciones_sin_grupo': []}

    def add(layer, part, facade, verts, faces, color):
        key = (layer, part, facade)
        parts[key].add(verts, faces, color)
        meta.setdefault(key, facade)

    internal_walls = {w['name'] for w in casa['WALLS'] if not w['external']}
    materials = casa['MATERIALS']
    for o in casa['OBJECTS']:
        col = o['collection']
        if col not in COLLECTIONS:
            report['colecciones_sin_grupo'].append(col)
            continue
        layer, part, split = COLLECTIONS[col]
        if col == '03_Carpinterias' and o['assembly'] in internal_walls:
            layer, part, split = 'L07_Interior', 'carpinterias', False
        if o['assembly'] == 'INST_Alimentacion_y_tierra':
            # Acometida y jabalina: exteriores y enterradas, no viajan con los muros.
            part = 'acometida'
        v = np.asarray(o['vertices'], dtype=np.float64)
        if np.linalg.norm(v.max(0) - v.min(0)) < MIN_DIAGONAL_M:
            report['piezas_omitidas_por_tamano'][col] += 1
            continue
        facade = None
        if split:
            if o['assembly'] not in FACADES:
                raise SystemExit(f'Pieza de envolvente sin fachada: {o["id"]} ({o["assembly"]})')
            facade = FACADES[o['assembly']][0]
        p = materials[o['material']]['color']
        color = [srgb_to_linear(c) for c in p[:3]] + [p[3]]
        verts = [(x - px, y - py, z + floor) for x, y, z in o['vertices']]
        add(layer, part, facade, verts, o['faces'], color)

    report['colecciones_sin_grupo'] = sorted(set(report['colecciones_sin_grupo']))

    def add_terrain(layer, part, facade, verts, faces, color):
        # El terreno ya está en coordenadas locales de la casa (sin pivote restado).
        add(layer, part, facade, [(x - px, y - py, z) for x, y, z in verts], faces, color)

    terrain_geometry(mod, terreno, informe, add_terrain)
    facade_dirs = {code: d for code, d in FACADES.values()}
    return parts, facade_dirs, report


def write_glb(parts, facade_dirs, out):
    buf = bytearray()
    views, accessors, meshes, nodes = [], [], [], []
    materials = [
        {'name': 'modelo', 'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1],
                                                    'metallicFactor': 0, 'roughnessFactor': 0.9}},
        {'name': 'vidrio', 'alphaMode': 'BLEND', 'doubleSided': True,
         'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 0.3],
                                  'metallicFactor': 0, 'roughnessFactor': 0.2}},
    ]

    def view(data, target):
        while len(buf) % 4:
            buf.append(0)
        views.append({'buffer': 0, 'byteOffset': len(buf), 'byteLength': data.nbytes, 'target': target})
        buf.extend(data.tobytes())
        return len(views) - 1

    def accessor(data, ctype, atype, target, normalized=False, minmax=False):
        a = {'bufferView': view(data, target), 'componentType': ctype,
             'count': len(data), 'type': atype}
        if normalized:
            a['normalized'] = True
        if minmax:
            a['min'] = data.min(0).tolist()
            a['max'] = data.max(0).tolist()
        accessors.append(a)
        return len(accessors) - 1

    root = {'name': 'AngusRanch', 'children': []}
    nodes.append(root)
    layer_nodes = {}
    for layer_id, label in LAYERS:
        layer_nodes[layer_id] = len(nodes)
        root['children'].append(len(nodes))
        nodes.append({'name': layer_id, 'children': [], 'extras': {'label': label}})

    stats = []
    tri_total = 0
    for (layer, part, facade) in sorted(parts, key=lambda k: (k[0], k[1], k[2] or '')):
        pt = parts[(layer, part, facade)]
        lo, hi = pt.bounds()
        center = (lo + hi) / 2
        prims = []
        tris_part = 0
        for glass in (False, True):
            verts_l, cols_l, tris_l = pt.prims[glass]
            if not verts_l:
                continue
            v = np.concatenate(verts_l) - center
            pos = np.stack([v[:, 0], v[:, 2], -v[:, 1]], 1).astype('<f4')
            col = np.clip(np.round(np.concatenate(cols_l) * 255), 0, 255).astype(np.uint8)
            idx = np.concatenate(tris_l)
            tris_part += len(idx)
            idx = idx.astype('<u2' if len(pos) < 65536 else '<u4').reshape(-1)
            prims.append({'attributes': {
                'POSITION': accessor(pos, 5126, 'VEC3', 34962, minmax=True),
                'COLOR_0': accessor(col, 5121, 'VEC4', 34962, normalized=True)},
                'indices': accessor(idx, 5123 if idx.dtype == np.dtype('<u2') else 5125, 'SCALAR', 34963),
                'material': 1 if glass else 0})
        name = f'{layer}__{part}' + (f'__{facade}' if facade else '')
        meshes.append({'name': name, 'primitives': prims})
        size = hi - lo
        extras = {'layer': layer, 'part': part,
                  'size': [round(float(size[0]), 3), round(float(size[2]), 3), round(float(size[1]), 3)]}
        if facade:
            dx, dy = facade_dirs[facade]
            extras['facade'] = facade
            extras['dir'] = [dx, -dy]  # dirección en el plano glTF XZ
        layer_nodes_idx = layer_nodes[layer]
        nodes[layer_nodes_idx]['children'].append(len(nodes))
        nodes.append({'name': name, 'mesh': len(meshes) - 1,
                      'translation': [float(center[0]), float(center[2]), float(-center[1])],
                      'extras': extras})
        tri_total += tris_part
        stats.append({'nodo': name, 'piezas': pt.pieces, 'triangulos': tris_part,
                      'primitivas': len(prims)})

    for layer_id, idx in layer_nodes.items():
        if not nodes[idx]['children']:
            del nodes[idx]['children']

    doc = {'asset': {'version': '2.0', 'generator': 'assambl landing/scripts/angus/export_glb.py'},
           'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': nodes, 'meshes': meshes,
           'materials': materials, 'accessors': accessors, 'bufferViews': views,
           'buffers': [{'byteLength': 0}]}
    while len(buf) % 4:
        buf.append(0)
    doc['buffers'][0]['byteLength'] = len(buf)
    js = json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode()
    js += b' ' * ((-len(js)) % 4)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(buf)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A) + js)
        f.write(struct.pack('<II', len(buf), 0x004E4942) + bytes(buf))
    return stats, tri_total, sum(len(m['primitives']) for m in meshes)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    ap.add_argument('--out', type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    if not args.source.exists():
        raise SystemExit(f'No se encontró el script fuente: {args.source}')
    parts, facade_dirs, report = build(args.source)
    stats, tris, draws = write_glb(parts, facade_dirs, args.out)
    report['piezas_omitidas_por_tamano'] = dict(report['piezas_omitidas_por_tamano'])
    report.update(glb=str(args.out.relative_to(LANDING)) if args.out.is_relative_to(LANDING) else str(args.out),
                  bytes=args.out.stat().st_size, triangulos=tris, nodos_animables=len(stats),
                  primitivas_draw_calls=draws, nodos=stats)
    report_path = REPORT
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{args.out}: {report["bytes"] / 1e6:.2f} MB, {tris} triángulos, '
          f'{len(stats)} nodos animables, {draws} primitivas')
    print(f'Reporte: {report_path}')


if __name__ == '__main__':
    main()
