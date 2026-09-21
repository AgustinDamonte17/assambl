"""ANGUS RANCH · TERRENO V01 · Blender 3.6 / 4.x / 5.x

USO
1. Blender > Scripting > New / Open > abrir este archivo > Run Script.
2. Se crea una escena NUEVA: Terreno_Angus_V01. Las escenas existentes,
   incluida la casa, se conservan. Cada ejecución crea otra escena.
3. Numpad 0: cámara de perspectiva. Numpad 7: vista superior.
   Para moverse cómodamente: seleccionar Lote_2500m2 y Numpad .
4. Guardar el resultado como .blend desde Blender. No se guarda automáticamente.
5. Colecciones separadas para lote, árboles, alambrado, calle, campo,
   vecinos y guías. Cada árbol es UN objeto completo, fácil de mover.

ESCALA Y FIDELIDAD
Una unidad Blender = un metro. Lote plano, superficie superior en Z=0.
X positivo = este; Y positivo = norte; Z positivo = arriba.
Origen = centroide del lote. La casa se incorporará después, sin escalarla.
El contorno se trazó visualmente sobre la captura de 484 x 493 px.
Escala uniforme ajustada para que el polígono tenga EXACTAMENTE 2500 m².
Las medidas de lados y los quiebres son estimados: el trazo de Paint no
es un plano catastral. La flecha norte se interpreta paralela a la imagen.
Árboles: posición y diámetro de copa aproximados; altura y especie desconocidas.
La altura del alambrado, postes, ancho de calle y paisaje lejano son supuestos.
Campo: al menos 1000 m hacia el oeste, con ondulación ilustrativa y monte
disperso. No representa una topografía medida ni inventario forestal real.
Vecinos norte/sur: suelo de contexto sin edificios ni divisiones inventadas.
No se abre un portón: su posición todavía no está definida.

PARÁMETROS: editar el bloque CONFIGURACIÓN y volver a ejecutar.
Sin Blender, ejecutar `python terreno_angus_ranch_V01.py --check`
para verificar escala, superficie, orientación y posiciones de árboles.
"""

import math
import random
import sys
from numbers import Integral

# -------------------------- CONFIGURACIÓN --------------------------
AREA_LOTE_M2 = 2500.0
EXTENSION_OESTE_M = 1000.0
EXTENSION_CAMPO_NS_M = 700.0
ALTURA_RELIEVE_M = 12.0  # ilustrativa; 0 para todo el campo plano
ANCHO_CALLE_M = 6.0     # estimado, sin medición
# Frente este trazado: 60.92 m, aceptado como aproximadamente 61 m.
ALTURA_POSTE_M = 1.20
SEPARACION_POSTES_M = 3.0
ALTURAS_ALAMBRES_M = (0.55, 1.05)
ARBOLES_ENTORNO = 180
SEMILLA = 26
MOSTRAR_GUIAS = True

# Puntos en la imagen: recorrido horario desde la esquina noroeste.
CONTORNO_PX = [
    (56,56),(118,39),(230,25),(313,13),(319,33),(322,108),
    (332,174),(350,244),(367,299),(369,345),(381,380),(380,408),
    (328,430),(269,446),(208,459),(132,459),(110,384),(94,313),
    (76,214),(65,143),
]

# x, y, radio de copa en píxeles, altura supuesta en metros.
# Se intenta identificar la copa, evitando interpretar su sombra como otra copa.
ARBOLES_PX = [
    (157,48,19,6.5),(247,41,24,8.0),(300,77,10,3.0),
    (91,145,21,6.0),(165,105,17,5.0),(222,107,23,8.0),
    (181,146,13,4.5),(316,130,14,4.5),(270,185,32,8.5),
    (319,176,10,3.5),(310,201,7,2.5),(103,223,20,5.5),
    (158,282,13,4.0),(137,322,9,3.0),(153,349,22,5.5),
    (243,305,7,2.3),(284,303,11,3.5),(300,327,10,3.8),
    (349,386,12,3.7),(143,428,15,4.0),(201,439,8,2.7),
]


def signed_area(points):
    return sum(x*v-u*y for (x,y),(u,v) in
               zip(points, points[1:]+points[:1])) / 2.0


def triangle_indices(triangles, vertices):
    """Admite tessellate_polygon con índices o con vectores según Blender."""
    lookup = {tuple(vertex): i for i, vertex in enumerate(vertices)}
    faces = []
    for triangle in triangles:
        face = tuple(int(vertex) if isinstance(vertex, Integral)
                     else lookup[tuple(vertex)] for vertex in triangle)
        if len(face) != 3 or any(i < 0 or i >= len(vertices) for i in face):
            raise ValueError('Triangulación del lote inválida: %r' % (face,))
        faces.append(face)
    return faces


def centroid(points):
    area = signed_area(points)
    cx = cy = 0.0
    for (x,y),(u,v) in zip(points, points[1:]+points[:1]):
        cross = x*v-u*y
        cx += (x+u)*cross
        cy += (y+v)*cross
    return cx/(6*area), cy/(6*area)


SCALE = math.sqrt(AREA_LOTE_M2 / abs(signed_area(CONTORNO_PX)))
CX, CY = centroid(CONTORNO_PX)


def to_world(point):
    return ((point[0]-CX)*SCALE, (CY-point[1])*SCALE)


POLY = [to_world(p) for p in CONTORNO_PX]
XMIN = min(x for x,y in POLY)
XMAX = max(x for x,y in POLY)
YMIN = min(y for x,y in POLY)
YMAX = max(y for x,y in POLY)
WEST_LIMIT = XMIN-EXTENSION_OESTE_M


def contains(x, y):
    inside = False
    for (ax,ay),(bx,by) in zip(POLY, POLY[1:]+POLY[:1]):
        if (ay > y) != (by > y):
            if x < ax+(y-ay)*(bx-ax)/(by-ay):
                inside = not inside
    return inside


def boundary_x(y, indices):
    pts = sorted([POLY[i] for i in indices], key=lambda p:p[1])
    if y <= pts[0][1]:
        a,b = pts[:2]
    elif y >= pts[-1][1]:
        a,b = pts[-2:]
    else:
        for a,b in zip(pts,pts[1:]):
            if a[1] <= y <= b[1]:
                break
    return a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1])


def west_x(y):
    return boundary_x(max(YMIN,min(YMAX,y)), [0,19,18,17,16,15])


def road_inner_x(y):
    return boundary_x(y, list(range(3,12)))+1.8


def ground_z(x,y):
    distance = max(0.0,west_x(y)-x-12.0)
    fade = min(1.0,distance/100.0)
    fade = fade*fade*(3-2*fade)
    waves = (0.50+0.24*math.sin(x/95+y/130)
             +0.17*math.cos(x/47-y/87)+0.09*math.sin(y/32))
    return -0.06+ALTURA_RELIEVE_M*fade*waves


def validate():
    assert AREA_LOTE_M2 > 0 and EXTENSION_OESTE_M >= 1000
    assert ANCHO_CALLE_M > 0 and SEPARACION_POSTES_M > 0
    assert max(ALTURAS_ALAMBRES_M) < ALTURA_POSTE_M
    assert abs(abs(signed_area(POLY))-AREA_LOTE_M2) < 1e-7
    assert abs(centroid(POLY)[0]) < 1e-8
    assert abs(centroid(POLY)[1]) < 1e-8
    assert to_world((0,0))[1] > to_world((0,493))[1]
    for x,y,r,h in ARBOLES_PX:
        assert contains(*to_world((x,y))), (x,y)
    print('Superficie: %.2f m²; escala: %.6f m/pixel' % (AREA_LOTE_M2,SCALE))
    for name,indices in [('Norte',range(0,4)),('Este',range(3,12)),
                         ('Sur',range(11,16)),('Oeste',[15,16,17,18,19,0])]:
        pts = [POLY[i] for i in indices]
        length = sum(math.dist(a,b) for a,b in zip(pts,pts[1:]))
        print('%s: %.2f m (trazado aproximado)' % (name,length))
    print('Árboles del lote: %d; extensión oeste: %.0f m' %
          (len(ARBOLES_PX),EXTENSION_OESTE_M))


def build():
    import bpy
    from mathutils import Vector

    rng = random.Random(SEMILLA)
    scene = bpy.data.scenes.new('Terreno_Angus_V01')
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    scene.unit_settings.length_unit = 'METERS'
    scene['alcance'] = 'Lote aproximado desde imagen; 2500 m2. Entorno ilustrativo.'
    scene['norte'] = '+Y'
    scene['escala_m_por_pixel'] = SCALE
    scene['referencia_casa'] = 'Centroide en (0,0); suelo Z=0; unidades metros.'
    if bpy.context.window:
        bpy.context.window.scene = scene

    def collection(name):
        c = bpy.data.collections.new(name)
        scene.collection.children.link(c)
        return c

    lot = collection('01_LOTE_2500m2')
    trees = collection('02_ARBOLES_LOTE_mover_objeto_completo')
    fence = collection('03_ALAMBRADO_dos_hilos')
    road = collection('04_CALLE_ESTE')
    field = collection('05_CAMPO_OESTE_1000m_ilustrativo')
    neighbors = collection('06_VECINOS_contexto')
    guides = collection('07_GUIAS_ocultables')
    cameras = collection('08_CAMARAS_Y_LUZ')

    def material(name, color, texture=False):
        m = bpy.data.materials.new('TER_V01_'+name)
        m.diffuse_color = (*color,1)
        m.use_nodes = True
        shader = m.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (*color,1)
        shader.inputs['Roughness'].default_value = 0.92
        if texture:
            nodes,links = m.node_tree.nodes,m.node_tree.links
            coord = nodes.new('ShaderNodeTexCoord')
            noise = nodes.new('ShaderNodeTexNoise')
            noise.inputs['Scale'].default_value = 0.7
            noise.inputs['Detail'].default_value = 3.0
            ramp = nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.elements[0].color = (*(c*0.62 for c in color),1)
            ramp.color_ramp.elements[1].color = (*(min(1,c*1.25) for c in color),1)
            links.new(coord.outputs['Object'],noise.inputs['Vector'])
            links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
            links.new(ramp.outputs['Color'],shader.inputs['Base Color'])
        return m

    grass = material('pasto_ralo',(0.30,0.32,0.16),True)
    wild = material('campo_seco',(0.34,0.32,0.18),True)
    soil = material('tierra_calle',(0.58,0.43,0.28),True)
    track = material('huellas_sutiles',(0.46,0.34,0.22),True)
    bark = material('troncos_postes',(0.22,0.15,0.08))
    leaves = [material('follaje_'+str(i),c) for i,c in enumerate([
        (0.13,0.23,0.13),(0.19,0.28,0.15),(0.24,0.31,0.19),
        (0.16,0.25,0.21),(0.27,0.32,0.17)])]
    wire_mat = material('alambre',(0.28,0.30,0.28))
    guide_mat = material('guias',(0.95,0.55,0.12))
    text_mat = material('texto',(0.85,0.88,0.78))

    def mesh_obj(name, verts, faces, coll, mats, ids=None):
        mesh = bpy.data.meshes.new(name+'_mesh')
        mesh.from_pydata(verts,[],faces)
        mesh.update()
        obj = bpy.data.objects.new(name,mesh)
        coll.objects.link(obj)
        for mat in mats:
            mesh.materials.append(mat)
        if ids is not None:
            for face,index in zip(mesh.polygons,ids):
                face.material_index = index
        return obj

    # Polígono plano triangulado para conservar quiebres del trazo.
    from mathutils.geometry import tessellate_polygon
    boundary = list(reversed(POLY)) if signed_area(POLY)<0 else POLY[:]
    vectors = [Vector((x,y,0)) for x,y in boundary]
    faces = triangle_indices(tessellate_polygon([vectors]), vectors)
    obj = mesh_obj('Lote_2500m2',vectors,faces,lot,[grass])
    obj['area_m2'] = AREA_LOTE_M2
    obj['precision'] = 'Área ajustada; lados aproximados desde imagen.'

    # Malla continua bajo todo el entorno; más detalle cerca del lote.
    xs = sorted(set([WEST_LIMIT+i*(XMIN-40-WEST_LIMIT)/80 for i in range(81)]
                    +[XMIN-40+i*2 for i in range(math.ceil((XMAX+85-XMIN)/2)+1)]))
    ys = sorted(set([-EXTENSION_CAMPO_NS_M/2+i*10
                     for i in range(int(EXTENSION_CAMPO_NS_M/10)+1)]
                    +[YMIN-20+i*2 for i in range(int((YMAX-YMIN+40)/2)+1)]))
    verts = [(x,y,ground_z(x,y)) for y in ys for x in xs]
    nx = len(xs)
    faces = [(j*nx+i,j*nx+i+1,(j+1)*nx+i+1,(j+1)*nx+i)
             for j in range(len(ys)-1) for i in range(nx-1)]
    mesh_obj('Campo_continuo_1000m_oeste',verts,faces,field,[wild])

    # Suelo plano de las parcelas colindantes, sin asumir límites exteriores.
    for name,edge,dy in [('Norte',[0,1,2,3],50),('Sur',[11,12,13,14,15],-50)]:
        pts = [POLY[i] for i in edge]
        verts = [(x,y,-0.025) for x,y in pts]
        verts += [(x,y+dy,-0.025) for x,y in pts]
        n = len(pts)
        faces = [(i,i+1,n+i+1,n+i) for i in range(n-1)]
        mesh_obj('Vecino_'+name,verts,faces,neighbors,[grass])

    def ribbon(name, offset, width, mat):
        y0,y1 = YMIN-75,YMAX+75
        verts = []
        for i in range(101):
            y = y0+(y1-y0)*i/100
            x = road_inner_x(y)+offset
            verts += [(x,y,-0.01 if offset==0 else -0.006),
                      (x+width,y,-0.01 if offset==0 else -0.006)]
        faces = [(2*i,2*i+1,2*i+3,2*i+2) for i in range(100)]
        return mesh_obj(name,verts,faces,road,[mat])
    ribbon('Calle_tierra_ancho_estimado_6m',0,ANCHO_CALLE_M,soil)
    for index,fraction in enumerate((0.30,0.70)):
        ribbon('Huella_'+str(index+1),ANCHO_CALLE_M*fraction,0.28,track)

    # Constructor de geometría: cada árbol incluye tronco, ramas y copa
    # en un solo mesh. No hay piezas sueltas que se desarmen al moverlo.
    class Geometry:
        def __init__(self):
            self.v,self.f,self.ids = [],[],[]

        def cylinder(self,a,b,r,mat=0,sides=8,top_ratio=0.7):
            a,b = Vector(a),Vector(b)
            axis = (b-a).normalized()
            helper = Vector((0,0,1)) if abs(axis.z)<0.95 else Vector((1,0,0))
            u = axis.cross(helper).normalized()
            v = axis.cross(u)
            start = len(self.v)
            for center,radius in [(a,r),(b,r*top_ratio)]:
                for k in range(sides):
                    d = u*math.cos(k*math.tau/sides)+v*math.sin(k*math.tau/sides)
                    self.v.append(tuple(center+d*radius))
            faces = [tuple(start+k for k in reversed(range(sides))),
                     tuple(start+sides+k for k in range(sides))]
            faces += [(start+k,start+(k+1)%sides,start+sides+(k+1)%sides,
                       start+sides+k) for k in range(sides)]
            self.f.extend(faces)
            self.ids.extend([mat]*len(faces))

        def crown(self,center,scale,mat):
            start = len(self.v)
            sides,rings = 10,5
            self.v.append((center[0],center[1],center[2]+scale[2]))
            for j in range(1,rings):
                phi = math.pi*j/rings
                for k in range(sides):
                    theta = math.tau*k/sides
                    irregular = rng.uniform(0.88,1.12)
                    self.v.append((center[0]+scale[0]*math.sin(phi)*math.cos(theta)*irregular,
                                   center[1]+scale[1]*math.sin(phi)*math.sin(theta)*irregular,
                                   center[2]+scale[2]*math.cos(phi)))
            bottom = len(self.v)
            self.v.append((center[0],center[1],center[2]-scale[2]))
            faces = [(start,start+1+k,start+1+(k+1)%sides) for k in range(sides)]
            for j in range(rings-2):
                a = start+1+j*sides
                b = a+sides
                faces += [(a+k,b+k,b+(k+1)%sides,a+(k+1)%sides) for k in range(sides)]
            a = start+1+(rings-2)*sides
            faces += [(bottom,a+(k+1)%sides,a+k) for k in range(sides)]
            self.f.extend(faces)
            self.ids.extend([mat]*len(faces))

    def tree(name,x,y,r,h,coll,z=0):
        geo = Geometry()
        geo.cylinder((0,0,0),(0,0,h*0.66),max(0.07,r*0.08))
        mat = rng.randrange(len(leaves))+1
        geo.crown((0,0,h*0.72),(r*0.72,r*0.72,h*0.28),mat)
        for k in range(5):
            angle = math.tau*k/5+rng.uniform(-0.25,0.25)
            dx,dy = math.cos(angle)*r*0.45,math.sin(angle)*r*0.45
            cz = h*rng.uniform(0.53,0.70)
            geo.cylinder((0,0,h*0.36),(dx,dy,cz),max(0.045,r*0.035))
            geo.crown((dx,dy,cz),(r*0.56,r*0.56,h*0.25),mat)
        obj = mesh_obj(name,geo.v,geo.f,coll,[bark]+leaves,geo.ids)
        obj.location = (x,y,z)
        obj['altura_aproximada_m'] = h
        obj['diametro_copa_aproximado_m'] = 2*r
        return obj

    for i,(px,py,r,h) in enumerate(ARBOLES_PX,1):
        x,y = to_world((px,py))
        obj = tree('Arbol_lote_%02d'%i,x,y,r*SCALE,h,trees)
        obj['origen_posicion'] = 'Copa identificada visualmente en captura.'

    # Franja boscosa visible junto al oeste: distribución ilustrativa.
    for i in range(45):
        y = rng.uniform(YMIN-20,YMAX+25)
        x = west_x(y)-rng.uniform(2.5,17)
        tree('Monte_lindero_%02d'%i,x,y,rng.uniform(1.4,3.5),
             rng.uniform(4,8),field,ground_z(x,y))
    for i in range(ARBOLES_ENTORNO):
        x = rng.uniform(WEST_LIMIT+15,XMIN-35)
        y = rng.uniform(-EXTENSION_CAMPO_NS_M/2+10,EXTENSION_CAMPO_NS_M/2-10)
        tree('Monte_distante_%03d'%i,x,y,rng.uniform(1,3.5),
             rng.uniform(2.5,6),field,ground_z(x,y))
    # Copas principales visibles al otro lado de la calle.
    for i,(px,py,r,h) in enumerate([(404,77,33,9),(429,29,20,6),
                                   (470,90,15,5),(387,190,10,4),
                                   (392,225,11,4),(403,294,15,5),
                                   (471,338,24,7),(369,438,25,7)]):
        x,y = to_world((px,py))
        tree('Arbol_entorno_visible_%02d'%i,x,y,r*SCALE,h,neighbors,-0.02)

    def curve(name,points,thickness,coll,mat):
        data = bpy.data.curves.new(name,'CURVE')
        data.dimensions = '3D'
        data.resolution_u = 1
        data.bevel_depth = thickness
        data.bevel_resolution = 0
        spline = data.splines.new('POLY')
        spline.points.add(len(points)-1)
        for p,co in zip(spline.points,points):
            p.co = (*co,1)
        obj = bpy.data.objects.new(name,data)
        coll.objects.link(obj)
        data.materials.append(mat)
        return obj

    posts = Geometry()
    for i,(a,b) in enumerate(zip(POLY,POLY[1:]+POLY[:1])):
        count = max(1,math.ceil(math.dist(a,b)/SEPARACION_POSTES_M))
        for j in range(count):
            t = j/count
            x,y = a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t
            posts.cylinder((x,y,-0.15),(x,y,ALTURA_POSTE_M),0.055,top_ratio=1)
    mesh_obj('Postes_perimetrales',posts.v,posts.f,fence,[bark],posts.ids)
    for i,h in enumerate(ALTURAS_ALAMBRES_M,1):
        curve('Alambre_continuo_hilo_'+str(i),[(x,y,h) for x,y in POLY+POLY[:1]],
              0.002,fence,wire_mat)

    def label(name,text,pos,size=1.5):
        data = bpy.data.curves.new(name,'FONT')
        data.body = text
        data.size = size
        data.align_x = 'CENTER'
        obj = bpy.data.objects.new(name,data)
        guides.objects.link(obj)
        obj.location = pos  # texto en XY, legible desde vista superior
        data.materials.append(text_mat)
        return obj

    curve('Contorno_guia',[(x,y,0.07) for x,y in POLY+POLY[:1]],0.055,guides,guide_mat)
    nx,ny = XMAX+16,YMAX-12
    curve('Norte',[(nx,ny,0.10),(nx,ny+10,0.10)],0.12,guides,guide_mat)
    curve('Flecha_N',[(nx-1.4,ny+7.5,0.10),(nx,ny+10,0.10),
                      (nx+1.4,ny+7.5,0.10)],0.12,guides,guide_mat)
    label('N','N',(nx,ny+11,0.12),2.5)
    label('Area','2.500 m² | LOTE PLANO',(0,-7,0.09),1.5)
    label('Nota','CONTORNO Y ÁRBOLES APROXIMADOS',(0,-10,0.09),0.75)
    label('Vecino_N','VECINO NORTE',(0,YMAX+12,0.12))
    label('Vecino_S','VECINO SUR',(0,YMIN-14,0.12))
    label('Campo','CAMPO OESTE | 1.000 m',(XMIN-37,0,0.15),1.4)
    bx,by = 0,YMIN-7
    curve('Escala_10m',[(bx-5,by,0.12),(bx+5,by,0.12)],0.10,guides,guide_mat)
    for x in (bx-5,bx+5):
        curve('Marca_escala',[(x,by-0.5,0.12),(x,by+0.5,0.12)],0.08,guides,guide_mat)
    label('Escala','10 m',(bx,by+1,0.12),1.0)
    guides.hide_viewport = not MOSTRAR_GUIAS
    guides.hide_render = not MOSTRAR_GUIAS

    anchor = bpy.data.objects.new('REFERENCIA_CASA_suelo_Z0_unidades_metros',None)
    lot.objects.link(anchor)
    anchor.empty_display_type = 'PLAIN_AXES'
    anchor.empty_display_size = 2
    anchor.hide_render = True

    def camera(name,pos,target,ortho):
        data = bpy.data.cameras.new(name)
        data.type = 'ORTHO'
        data.ortho_scale = ortho
        data.clip_end = 5000
        obj = bpy.data.objects.new(name,data)
        cameras.objects.link(obj)
        obj.location = pos
        obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
        return obj

    scene.camera = camera('Camara_01_lote_perspectiva',(95,-115,125),(0,0,0),135)
    top = camera('Camara_02_planta',(0,0,150),(0,0,0),105)
    top.rotation_euler = (0,0,0)  # -Z hacia abajo; +Y norte arriba
    camera('Camara_03_campo_completo',(-390,-800,850),(-440,0,0),1300)
    light_data = bpy.data.lights.new('Sol','SUN')
    light_data.energy = 2.5
    light_data.angle = math.radians(15)
    light = bpy.data.objects.new('Sol',light_data)
    cameras.objects.link(light)
    light.rotation_euler = (math.radians(28),math.radians(-22),math.radians(-35))
    world = bpy.data.worlds.new('Cielo_Terreno_V01')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.65,0.76,0.90,1)
    world.node_tree.nodes['Background'].inputs[1].default_value = 0.65
    scene.world = world
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    try:
        scene.view_settings.view_transform = 'AgX'
    except TypeError:
        scene.view_settings.view_transform = 'Standard'

    if bpy.context.window:
        for obj in scene.objects:
            obj.select_set(False)
        target = next(o for o in lot.objects if o.type=='MESH')
        target.select_set(True)
        bpy.context.view_layer.objects.active = target
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    space = area.spaces.active
                    space.clip_end = 5000
                    space.shading.type = 'MATERIAL'
                    space.region_3d.view_distance = 105
                    space.region_3d.view_location = Vector((0,0,0))
                    space.region_3d.view_rotation = scene.camera.rotation_euler.to_quaternion()
    print('Listo: '+scene.name+' · seleccionar Lote_2500m2 y Numpad . para enfocar.')


if __name__ == '__main__':
    validate()
    if '--check' not in sys.argv:
        build()
