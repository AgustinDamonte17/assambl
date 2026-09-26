"""ANGUS RANCH V06 - CASA Y TERRENO + WOODFRAME + INSTALACIONES.
Script autónomo derivado de V05. Ver Angus_Ranch_V06/LEEME_V06.md.
Blender Scripting: Run Script crea una escena nueva. No borra anteriores.
CLI: python archivo.py --check (solo lectura, sin generar archivos).
Se conservan arquitectura, terreno y detalles V06. Nuevas colecciones:
20_Instalacion_electrica, 21_Desagues_sanitarios, 22_Agua_fria_caliente.
Reservas reales en platea V06, solados, cielorraso y revestimientos.
Desagües sanitarios (no pluviales); agua fría/caliente y termotanque.
Cables y cañerías se representan por sus ejes; accesorios y mazos simplificados.
Predimensionado conceptual: confirmar cargas, protecciones, presión, refuerzos
alrededor de reservas y conexiones exteriores antes de desarrollar la obra.
Blender: --save / --render conserva las opciones originales de V06.
"""
"""ANGUS RANCH V05 — CASA V04 + TERRENO V01, un único script autónomo.

Blender > Scripting > Open > abrir este archivo > Run Script (Alt+P).
Crea una escena NUEVA, Angus_Ranch_V05_Casa_y_Terreno. Guardar como .blend.
No requiere los scripts originales ni borra escenas anteriores.

Ubicación aproximada interpretada de la marca roja: sector sureste.
Norte = +Y, este/calle = +X. Una unidad = un metro; casa sin reescalar.
Lote 2500 m², frente este 60.92 m (aprox. 61 m aceptados).
Casa V04: 164.16 m² de huella cerrada y galería de 30 m² al norte.
Piso de referencia elevado 20 cm respecto del terreno; platea parcialmente
enterrada. Es una decisión de representación ajustable, no de cimentación.

AJUSTES: editar IMPLANTACION más abajo y ejecutar de nuevo.
También se puede seleccionar CASA_MOVER_TODO en el Outliner y usar G / R Z.
Es el padre de todas las piezas, muebles y cámaras de detalle de la casa.
No usar S: la escala de la casa debe permanecer en (1,1,1).
Las ediciones manuales del .blend no se incorporan de vuelta al script.

View Layers: se conservan las vistas constructivas, con terreno, y V06 agrega
las capas 14–16 para electricidad, desagües/cimientos y agua.
Inicio: 02_Exterior_completo. 01_Interior_sin_techo permite ver el interior.
Cámaras: lote, planta, campo, detalle de galería y las tres cámaras V04.
Numpad 0: cámara activa. Numpad 7: planta (norte arriba).
Para cambiar cámara: seleccionarla y Ctrl+Numpad 0.

Árboles en conflicto: se conservan en 02b_ARBOLES_INTERFERENCIA_REVISAR,
colección oculta por defecto, con coordenadas originales. No se propone tala
ni traslado real. Revisión aproximada de copas contra techos; no agronómica.
Tras mover la casa manualmente, revisar esas interferencias nuevamente.

Las instalaciones agregan reservas en la platea V06, solados, cielorraso y
revestimientos, conservando los anclajes y las piezas de madera. El suelo
09_Entorno se sustituye por el terreno completo. El sendero se nivela con el
piso porque su cota de la versión aislada quedaría bajo el nuevo terreno.
No se inventa acceso/portón. Contorno, árboles y paisaje siguen aproximados.

Comprobación sin Blender: python angus_ranch_V05_casa_y_terreno.py --check
Comprueba ambos modelos, escala, orientación, implantación e interferencias.
No equivale a una ejecución o un render dentro de Blender.
"""

import math
import json
import sys

IMPLANTACION = {
    'centro_casa_xy_m': (8.0, -18.0),
    # Pivote local: centro de la envolvente 18 x 13.4 m, incluida galería.
    'pivote_local_xy_m': (9.0, 4.3),
    'giro_grados': 0.0,  # 0 = galería hacia +Y/norte.
    'cota_piso_m': 0.20,
    'ocultar_arboles_interferencia': True,
}


def cargar_fuentes():
    casa = {'__name__': 'fuente_casa_v04'}
    terreno = {'__name__': 'fuente_terreno_v01'}
    exec(compile(FUENTE_CASA_V04, '<casa_v04_incluida>', 'exec'), casa)
    exec(compile(FUENTE_TERRENO_V01, '<terreno_v01_incluido>', 'exec'), terreno)
    return casa, terreno


def local_a_lote(x, y):
    a = math.radians(IMPLANTACION['giro_grados'])
    px, py = IMPLANTACION['pivote_local_xy_m']
    cx, cy = IMPLANTACION['centro_casa_xy_m']
    return (cx + math.cos(a)*(x-px)-math.sin(a)*(y-py),
            cy + math.sin(a)*(x-px)+math.cos(a)*(y-py))


def lote_a_local(x, y):
    a = math.radians(IMPLANTACION['giro_grados'])
    px, py = IMPLANTACION['pivote_local_xy_m']
    cx, cy = IMPLANTACION['centro_casa_xy_m']
    return (px+math.cos(a)*(x-cx)+math.sin(a)*(y-cy),
            py-math.sin(a)*(x-cx)+math.cos(a)*(y-cy))


def distancia_segmento(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    t = max(0., min(1., ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)


def preparar_y_comprobar(casa, terreno):
    terreno['validate']()
    casa['build']()
    # Retirar solo el suelo de estudio; el terreno pasa a ser la base común.
    casa['OBJECTS'][:] = [o for o in casa['OBJECTS'] if o['collection'] != '09_Entorno']
    for obj in casa['OBJECTS']:
        if obj['name'] == 'Sendero_entrada':
            # Superficie superior local Z=0 (antes -0.045).
            obj['vertices'] = [(x,y,z+0.045) for x,y,z in obj['vertices']]
    casa['validate']()
    a = math.radians(IMPLANTACION['giro_grados'])
    direccion_galeria = (-math.sin(a), math.cos(a))
    if direccion_galeria[1] <= 0:
        raise ValueError('La galería dejó de orientarse hacia el norte. Revisar giro_grados.')
    puntos = set(local_a_lote(v[0],v[1]) for o in casa['OBJECTS'] for v in o['vertices'])
    fuera = [p for p in puntos if not terreno['contains'](*p)]
    if fuera:
        raise ValueError('La casa sale del lote: revisar centro/giro. Ejemplo: %r' % (fuera[0],))
    lados = [('Norte',range(0,4)),('Este',range(3,12)),
             ('Sur',range(11,16)),('Oeste',[15,16,17,18,19,0])]
    retiros = {}
    for nombre, indices in lados:
        borde = [terreno['POLY'][i] for i in indices]
        retiros[nombre] = round(min(distancia_segmento(p,a,b)
            for p in puntos for a,b in zip(borde,borde[1:])), 2)
    # Rectángulos de cada chapa: evita confundir el vacío de la planta con casa.
    techos = []
    for obj in casa['OBJECTS']:
        if obj['name'] in ('Chapa_principal','Chapa_anexo','Chapa_galeria'):
            v = obj['vertices']
            techos.append((min(p[0] for p in v),min(p[1] for p in v),
                           max(p[0] for p in v),max(p[1] for p in v)))
    conflictos = []
    for i,(px,py,r,h) in enumerate(terreno['ARBOLES_PX'],1):
        x,y = terreno['to_world']((px,py))
        lx,ly = lote_a_local(x,y)
        radio = r*terreno['SCALE']
        if any(math.hypot(lx-max(x0,min(x1,lx)),ly-max(y0,min(y1,ly))) <= radio
               for x0,y0,x1,y1 in techos):
            conflictos.append(i)
    informe = {
        'version_integrada': 'V05',
        'casa_base': 'V04', 'terreno_base': 'V01',
        'escala_casa': [1.,1.,1.],
        'area_lote_m2': terreno['AREA_LOTE_M2'],
        'huella_casa_m2': casa['VALIDATION']['footprint_m2'],
        'galeria_m2': 30.,
        'centro_casa_xy_m': IMPLANTACION['centro_casa_xy_m'],
        'origen_local_en_lote_xy_m': local_a_lote(0,0),
        'cota_piso_referencia_m': IMPLANTACION['cota_piso_m'],
        'direccion_galeria_xy': direccion_galeria,
        'retiros_minimos_aprox_incluidos_aleros_y_sendero_m': retiros,
        'arboles_interferencia_copa_techo': conflictos,
        'piezas_casa': len(casa['OBJECTS']),
        'nota': 'Retiros geométricos aproximados; no son retiros reglamentarios.',
    }
    print(json.dumps(informe, ensure_ascii=False, indent=2))
    return informe


def construir_integrado(casa, terreno, informe):
    import bpy
    from mathutils import Vector
    if bpy.context.window is None:
        raise RuntimeError('Ejecutar desde el editor Scripting de una ventana de Blender.')
    escena_anterior = bpy.context.window.scene
    terreno['build']()
    escena_terreno = bpy.context.window.scene
    casa['blender_scene']()
    escena = bpy.context.window.scene
    escena.name = 'Angus_Ranch_V05_Casa_y_Terreno'
    escena['version'] = 'V05 (Casa V04 + Terreno V01)'
    escena['norte'] = '+Y'
    escena['implantacion_json'] = json.dumps(informe, ensure_ascii=False)
    escena['escena_previa_conservada'] = escena_anterior.name
    escena['area_lote_m2'] = terreno['AREA_LOTE_M2']
    escena['referencia_casa'] = 'CASA_MOVER_TODO controla todas las piezas sin reescalar.'
    objetos_casa = list(escena.objects)
    control_col = bpy.data.collections.new('00_CONTROL_IMPLANTACION')
    escena.collection.children.link(control_col)
    raiz = bpy.data.objects.new('CASA_MOVER_TODO', None)
    control_col.objects.link(raiz)
    raiz.empty_display_type = 'ARROWS'
    raiz.empty_display_size = 2.5
    raiz.show_in_front = True
    raiz.lock_scale = (True, True, True)
    raiz['instrucciones'] = 'G mueve toda la casa; R Z gira. Escala 1:1. Galería local +Y.'
    raiz['pivote_local_xy_m'] = list(IMPLANTACION['pivote_local_xy_m'])
    # Recentrar solo padres raíz; hijos, biseles y jerarquías V04 no cambian.
    px,py = IMPLANTACION['pivote_local_xy_m']
    for obj in objetos_casa:
        if obj.type == 'LIGHT':
            # Usar únicamente el sol y el cielo del terreno.
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        if obj.parent is None:
            obj.parent = raiz
            obj.location -= Vector((px,py,0))
        if obj.type == 'CAMERA':
            obj.data.clip_end = 5000
    cx,cy = IMPLANTACION['centro_casa_xy_m']
    raiz.location = (cx,cy,IMPLANTACION['cota_piso_m'])
    raiz.rotation_euler.z = math.radians(IMPLANTACION['giro_grados'])
    # Integrar las colecciones reales del terreno, sin duplicar geometría.
    colecciones_terreno = list(escena_terreno.collection.children)
    arboles = next(c for c in colecciones_terreno if c.name.startswith('02_ARBOLES_LOTE'))
    for col in colecciones_terreno:
        escena.collection.children.link(col)
    escena.world = escena_terreno.world
    escena.render.engine = escena_terreno.render.engine
    escena.view_settings.view_transform = escena_terreno.view_settings.view_transform
    escena.camera = escena_terreno.camera
    camaras = next(c for c in colecciones_terreno if c.name.startswith('08_CAMARAS_Y_LUZ'))
    bpy.data.scenes.remove(escena_terreno)  # Solo la escena temporal de ESTA ejecución.
    revisar = bpy.data.collections.new('02b_ARBOLES_INTERFERENCIA_REVISAR')
    escena.collection.children.link(revisar)
    for obj in list(arboles.objects):
        # Blender puede añadir .001 al nombre al ejecutar varias veces.
        numero = int(obj.name.split('.')[0].rsplit('_',1)[1])
        if numero in informe['arboles_interferencia_copa_techo']:
            revisar.objects.link(obj)
            arboles.objects.unlink(obj)
            obj['motivo_revision'] = 'Copa aproximada coincide con techo en implantación inicial.'
            obj['posicion_original_m'] = list(obj.location)
    revisar.hide_viewport = IMPLANTACION['ocultar_arboles_interferencia']
    revisar.hide_render = IMPLANTACION['ocultar_arboles_interferencia']
    revisar['instrucciones'] = 'Árboles conservados en su ubicación original; activar colección para revisar.'
    # Guías originales en el espacio libre, fuera de la vivienda.
    guias = next(c for c in colecciones_terreno if c.name.startswith('07_GUIAS'))
    for obj in guias.objects:
        nombre = obj.name.split('.')[0]
        if nombre == 'Area': obj.location = (-5,0,.09)
        elif nombre == 'Nota': obj.location = (-5,-2,.09)
    # Cámara de la galería desde el norte; acompaña a la casa si se mueve.
    data = bpy.data.cameras.new('CAM_Galeria_norte')
    data.type = 'ORTHO'; data.ortho_scale = 32; data.clip_end = 5000
    cam = bpy.data.objects.new('CAM_Galeria_norte',data)
    camaras.objects.link(cam)
    cam.parent = raiz
    cam.location = Vector((26,30,20))-Vector((px,py,0))
    objetivo = Vector((9,5,1.2))-Vector((px,py,0))
    cam.rotation_euler = (objetivo-cam.location).to_track_quat('-Z','Y').to_euler()
    # Conservar las ocho capas constructivas y activar exterior completo.
    for capa in escena.view_layers:
        capa.use = capa.name == '02_Exterior_completo'
    bpy.context.window.view_layer = escena.view_layers['02_Exterior_completo']
    bpy.context.view_layer.update()
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    raiz.select_set(True)
    bpy.context.view_layer.objects.active = raiz
    escena.render.resolution_x = 1600
    escena.render.resolution_y = 1200
    escena.render.resolution_percentage = 100
    for pantalla in bpy.data.screens:
        for area in pantalla.areas:
            if area.type == 'VIEW_3D':
                sp = area.spaces.active
                sp.clip_end = 5000
                sp.shading.type = 'MATERIAL'
                sp.region_3d.view_perspective = 'ORTHO'
                sp.region_3d.view_distance = 105
                sp.region_3d.view_location = (0,0,0)
                sp.region_3d.view_rotation = escena.camera.rotation_euler.to_quaternion()
    texto = bpy.data.texts.new('LEEME_IMPLANTACION_V05')
    texto.write(__doc__+'\n\nCOMPROBACIÓN DE ESTA EJECUCIÓN\n'+
                json.dumps(informe, ensure_ascii=False, indent=2))
    print('V05 LISTA: casa y terreno en una escena. Guardar como .blend.')
    print('Árboles para revisar (conservados):', informe['arboles_interferencia_copa_techo'])


def main():
    casa, terreno = cargar_fuentes()
    informe = preparar_y_comprobar(casa, terreno)
    if '--check' not in sys.argv:
        construir_integrado(casa, terreno, informe)


# ====================================================================
# FUENTES AUTOCONTENIDAS. No hace falta descargar archivos adicionales.
# Se cargan en espacios de nombres separados para evitar que las funciones
# build(), validate() y los materiales de un modelo sobrescriban al otro.
# Sus bloques __main__ originales NO se ejecutan.
# ====================================================================

FUENTE_CASA_V04 = r'''
"""ANGUS RANCH / V04 sobre planta V03 / arquitectura y woodframe de estudio
Python con NumPy: genera GLB y JSON. Blender: crea una escena nueva editable.
Unidades: metros. X este, Y norte, Z arriba. No elimina escenas existentes.
No representa un proyecto ejecutivo ni un cálculo estructural.
"""
import math, json, struct, os, sys
from pathlib import Path
from collections import Counter
W,D,H=15.0,8.0,2.75
OBJECTS=[]; MATERIALS={}; OPENINGS=[]; ROOMS=[]
COLORS={
 'Revoque cálido':('#e4dfd2',.86,0), 'Roble natural':('#ad7950',.62,0),
 'Madera exterior':('#88694c',.8,0), 'Madera estructura':('#c69967',.72,0),
 'Siding oscuro':('#343c3a',.86,0), 'Lana mineral':('#c6ae69',1,0),
 'OSB':('#b99157',.94,0), 'WRB':('#ecece3',.96,0),
 'Cinta WRB':('#507c9a',.9,0), 'Sellado flexible':('#777569',.95,0),
 'Grafito':('#252e31',.38,.6), 'Zinc':('#3e494d',.45,.75),
 'Vidrio':('#a6cbd2',.12,0), 'Piso piedra':('#c4bdae',.78,0),
 'Porcelanato':('#a1aba6',.65,0), 'Cerámica blanca':('#f0eee8',.24,0),
 'Lino':('#d6c9af',.94,0), 'Verde oliva':('#69745c',.95,0),
 'Terracota':('#b97150',.86,0), 'Acero':('#a8b3b7',.25,.9),
 'Pantalla':('#14252b',.3,.15), 'Tierra':('#75816a',1,0),
 'Grava':('#c5c2b5',1,0), 'Follaje':('#516849',1,0),
 'Luz':('#fff0ca',.3,0), 'Negro':('#171c1d',.5,0),
 'Juntas':('#777b71',1,0), 'Agua':('#759da2',.16,0)}
for name,(hx,rough,metal) in COLORS.items():
 MATERIALS[name]={'color':[int(hx[i:i+2],16)/255 for i in (1,3,5)]+[.23 if name=='Vidrio' else 1], 'roughness':rough,'metallic':metal}



def box(name,loc,size,mat,cat='04_Mobiliario',bevel=.008,rz=0):
 x,y,z=loc;a,b,c=[s/2 for s in size];co,si=math.cos(rz),math.sin(rz)
 vs=[]
 for u,v,w in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]:
  vs.append([x+u*co-v*si,y+u*si+v*co,z+w])
 return add(name,cat,vs,[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]],mat,bevel)

def cylinder(name,a,b,r,mat,cat='04_Mobiliario',n=12,r2=None):
 import numpy as np
 a=np.array(a,float);b=np.array(b,float);axis=b-a;axis/=np.linalg.norm(axis)
 ref=np.array([0,0,1]) if abs(axis[2])<.9 else np.array([1,0,0])
 u=np.cross(axis,ref);u/=np.linalg.norm(u);v=np.cross(axis,u);r2=r if r2 is None else r2
 verts=[]
 for p,rr in [(a,r),(b,r2)]:
  for i in range(n):verts.append((p+rr*(u*math.cos(i*2*math.pi/n)+v*math.sin(i*2*math.pi/n))).tolist())
 faces=[list(range(n-1,-1,-1)),list(range(n,2*n))]+[[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)]
 return add(name,cat,verts,faces,mat)

def ellipsoid(name,loc,size,mat,cat='04_Mobiliario'):
 vs=[];n=16;m=8
 for j in range(m+1):
  phi=math.pi*j/m
  for i in range(n):
   th=2*math.pi*i/n;vs.append([loc[0]+size[0]/2*math.sin(phi)*math.cos(th),loc[1]+size[1]/2*math.sin(phi)*math.sin(th),loc[2]+size[2]/2*math.cos(phi)])
 fs=[]
 for j in range(m):
  for i in range(n):fs.append([j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i])
 return add(name,cat,vs,fs,mat)

def opening(name,axis,pos,a,b,z0,z1,kind):
 cat='03_Carpinterias';w=b-a
 def ob(s,u,z,du,dz,mat='Grafito',depth=.065,offset=0):
  loc=(u,pos+offset,z) if axis=='X' else (pos+offset,u,z)
  sz=(du,depth,dz) if axis=='X' else (depth,du,dz)
  return box(name+s,loc,sz,mat,cat,.002)
 for p in [a+.023,b-.023]:ob('_marco_jamba',p,(z0+z1)/2,.046,z1-z0)
 for z in [z0+.02,z1-.023]:ob('_marco_horizontal',(a+b)/2,z,w,.046)
 if kind in ['corrediza','ventana']:
  n=4 if w>3 else (2 if w>1.1 else 1)
  for i in range(n):
   aa=a+.04+i*(w-.08)/n;bb=a+.04+(i+1)*(w-.08)/n;off=.018*(i%2)
   ob('_vidrio_'+str(i),(aa+bb)/2,(z0+z1)/2,bb-aa-.028,z1-z0-.1,'Vidrio',.012,off)
   ob('_parante_'+str(i),aa,(z0+z1)/2,.025,z1-z0-.05,offset=off)
   if kind=='corrediza':ob('_tirador_'+str(i),aa+.04,1.1,.013,.22,'Acero',.023,offset=off+.05)
  if z0>.1:ob('_alféizar',(a+b)/2,z0-.022,w+.08,.035,'Piso piedra',.27)
 elif kind=='paso':pass
 else:
  # Door leaf open 70 degrees around hinge. Keeps circulation visually legible.
  swing=DOOR_SWINGS.get(name, 70)
  angle=math.radians(swing);base=0 if axis=='X' else math.pi/2;ang=base+angle
  hinge=(a+.04,pos) if axis=='X' else (pos,a+.04)
  length=w-.08;cx=hinge[0]+math.cos(ang)*length/2;cy=hinge[1]+math.sin(ang)*length/2
  box(name+'_hoja_abierta',(cx,cy,(z1-.06)/2+.025),(length,.04,z1-.06),'Roble natural',cat,.004,ang)
  hx=hinge[0]+math.cos(ang)*(length-.1);hy=hinge[1]+math.sin(ang)*(length-.1)
  for side in [-1,1]:
   ox=-math.sin(ang)*.035*side;oy=math.cos(ang)*.035*side
   cylinder(name+'_roseta',(hx+ox,hy+oy,1.03),(hx+ox*1.3,hy+oy*1.3,1.03),.025,'Acero',cat)
   cylinder(name+'_manija',(hx+ox,hy+oy,1.03),(hx+ox+math.cos(ang)*.1,hy+oy+math.sin(ang)*.1,1.03),.008,'Acero',cat)

def cabinet(name,x,y,width,depth=.6,height=.88):
 cat='04a_Cocina'
 box(name+'_cuerpo',(x,y,height/2+.06),(width,depth,height-.12),'Roble natural',cat)
 box(name+'_zócalo',(x,y,.055),(width-.06,depth-.08,.11),'Grafito',cat)
 for i in range(max(1,round(width/.6))):
  n=max(1,round(width/.6));xx=x-width/2+(i+.5)*width/n
  for z,h in [(.25,.32),(.64,.43)]:
   box(name+'_frente',(xx,y+depth/2+.013,z),(width/n-.006,.022,h),'Roble natural',cat,.002)
   box(name+'_uñero',(xx,y+depth/2+.026,z+h/2-.025),(width/n-.07,.013,.012),'Grafito',cat,.001)

def chair(name,x,y,rz=0,mat='Roble natural',cat='04_Mobiliario'):
 def b(s,xx,yy,zz,size,ma):
  co,si=math.cos(rz),math.sin(rz);return box(name+s,(x+xx*co-yy*si,y+xx*si+yy*co,zz),size,ma,cat,.014,rz)
 b('_asiento',0,0,.46,(.46,.43,.065),mat)
 b('_respaldo',0,.19,.71,(.46,.045,.43),mat)
 for xx in [-.17,.17]:
  for yy in [-.15,.15]:b('_pata',xx,yy,.23,(.035,.035,.46),'Roble natural')

def bed(name,x,y,w=1.6,rz=0):
 cat='04c_Dormitorios';co,si=math.cos(rz),math.sin(rz)
 def b(s,xx,yy,z,size,ma,bev=.04):return box(name+s,(x+xx*co-yy*si,y+xx*si+yy*co,z),size,ma,cat,bev,rz)
 b('_base',0,0,.19,(w+.08,2.05,.32),'Roble natural')
 b('_colchón',0,0,.44,(w,2,.23),'Cerámica blanca')
 b('_edredón',0,-.25,.57,(w+.04,1.43,.095),'Lino')
 b('_pie_manta',0,-.7,.63,(w+.07,.43,.035),'Verde oliva')
 b('_cabecero',0,1.04,.67,(w+.18,.085,1.1),'Roble natural')
 for xx in ([-w/4,w/4] if w>1.2 else [0]):b('_almohada',xx,.69,.61,(.59,.41,.13),'Cerámica blanca',.07)

def sink(name,x,y,z=.91,cat='04a_Cocina',width=.53,depth=.4):
 box(name+'_fondo',(x,y,z-.1),(width,depth,.035),'Acero',cat,.01)
 for xx in [-width/2,width/2]:box(name+'_lateral',(x+xx,y,z-.05),(.022,depth,.13),'Acero',cat,.005)
 for yy in [-depth/2,depth/2]:box(name+'_borde',(x,y+yy,z-.05),(width,.022,.13),'Acero',cat,.005)
 cylinder(name+'_desagüe',(x,y,z-.079),(x,y,z-.07),.03,'Grafito',cat,20)
 cylinder(name+'_grifo_pie',(x,y-depth/2-.06,z),(x,y-depth/2-.06,z+.27),.015,'Acero',cat)
 cylinder(name+'_grifo_pico',(x,y-depth/2-.06,z+.27),(x,y-.03,z+.27),.014,'Acero',cat)
 cylinder(name+'_grifo_bajada',(x,y-.03,z+.27),(x,y-.03,z+.22),.014,'Acero',cat)

def toilet(name,x,y,rz=0):
 cat='04d_Banos_lavadero';co,si=math.cos(rz),math.sin(rz)
 def p(dx,dy,z):return(x+dx*co-dy*si,y+dx*si+dy*co,z)
 box(name+'_cisterna',p(0,-.22,.65),(.39,.18,.42),'Cerámica blanca',cat,.045,rz)
 ellipsoid(name+'_pie',p(0,.03,.22),(.31,.44,.4),'Cerámica blanca',cat)
 ellipsoid(name+'_taza',p(0,.03,.4),(.4,.59,.2),'Cerámica blanca',cat)
 ellipsoid(name+'_interior',p(0,.07,.487),(.27,.37,.02),'Grafito',cat)
 ellipsoid(name+'_tapa_levantada',p(0,-.17,.7),(.37,.055,.45),'Cerámica blanca',cat)
 box(name+'_pulsador',p(0,-.22,.865),(.07,.04,.006),'Acero',cat,.002)

def shower(name,x,y,w=.85,d=.85):
 cat='04d_Banos_lavadero'
 box(name+'_plato',(x,y,.035),(w,d,.055),'Cerámica blanca',cat,.012)
 box(name+'_rejilla',(x,y-.25,.065),(.35,.055,.008),'Acero',cat,.001)
 box(name+'_mampara',(x+w/2,y,1.02),(.012,d,1.96),'Vidrio',cat,.0)
 cylinder(name+'_columna',(x,y-d/2+.07,.95),(x,y-d/2+.07,2.15),.015,'Acero',cat)
 cylinder(name+'_brazo',(x,y-d/2+.07,2.15),(x,y,2.15),.015,'Acero',cat)
 cylinder(name+'_rociador',(x,y,2.14),(x,y,2.12),.095,'Acero',cat,24)
 box(name+'_mezclador',(x,y-d/2+.07,1.1),(.2,.07,.06),'Acero',cat)

def plant(name,x,y,z=0,scale=1):
 cat='07_Exterior'
 cylinder(name+'_maceta',(x,y,z),(x,y,z+.32*scale),.16*scale,'Terracota',cat,16,r2=.23*scale)
 for i in range(7):
  a=i*2.4;xx=x+math.cos(a)*.18*scale;yy=y+math.sin(a)*.18*scale;zz=z+(.62+(i%3)*.11)*scale
  cylinder(name+'_tallo',(x,y,z+.28*scale),(xx,yy,zz),.01*scale,'Follaje',cat,6)
  ellipsoid(name+'_hoja',(xx,yy,zz),(.27*scale,.15*scale,.32*scale),'Follaje',cat)

# ================================================================
# V03 — FUENTE ÚNICA: coordenadas métricas, componentes y referencias.
# Los helpers anteriores sólo generan piezas; no generan la casa V01.
# ================================================================
import re
CONFIG = {
    'version': 'V04', 'ancho_hasta_lavadero': 15.0, 'fondo_principal': 8.0,
    'ancho_ala_este': 3.0, 'saliente_sur': 2.4, 'inicio_saliente_sur': 9.6,
    'galeria': (5.0, 8.0, 15.0, 11.0),
    'altura_tabiques': 2.80, 'pendiente_techo': 0.06,
    'cota_apoyo_sur': 3.35, 'modulo_montantes': 0.60,
    'montante_ancho': 0.045, 'montante_fondo': 0.140,
    'osb_espesor': .012, 'osb_modulo': 1.2, 'osb_alto': 2.4, 'osb_junta': .0032,
    'wrb_espesor_grafico': .0005, 'wrb_solape': .15,
    'camara_ventilada': .025, 'siding_espesor': .020, 'siding_paso': .18,
    'aislacion_espesor': .140,
    'retorno_wrb_esquina': .30, 'ancho_esquinero': .10, 'junta_siding_esquinero': .003,
    'nota': 'Dimensiones estructurales de estudio, no calculadas. Base: Thallon, 3a ed., detalles 68A-C, 69B, 72 y pp.129-132.',
}
W=CONFIG['ancho_hasta_lavadero']; D=CONFIG['fondo_principal']
E=W+CONFIG['ancho_ala_este']; S=CONFIG['saliente_sur']; XADD=CONFIG['inicio_saliente_sur']
H=CONFIG['altura_tabiques']; T=CONFIG['montante_ancho']; STUD=CONFIG['montante_fondo']
OBJECTS=[]; OPENINGS=[]; ROOMS=[]; WALLS=[]; DOOR_SWINGS={}; SERIAL={}
CURRENT_COMPONENT='General'; CURRENT_REFERENCE=''; VALIDATION={}
CORNER_SPECS=[
    ('SO','Sur_principal','start','Oeste','start',.1,.1,'convexa'),
    ('NO','Norte','start','Oeste','end',.1,7.9,'convexa'),
    ('NE','Norte','end','Este','end',17.9,7.9,'convexa'),
    ('SE','Sur_anexo','end','Este_anexo','start',17.9,-2.3,'convexa'),
    ('SO_anexo','Sur_anexo','start','Oeste_anexo','start',9.7,-2.3,'convexa'),
    ('Entrante','Sur_principal','end','Oeste_anexo','end',9.7,.1,'concava'),
]
CORNER_ENDPOINTS={}
for cid,xwall,xend,ywall,yend,x,y,kind in CORNER_SPECS:
    CORNER_ENDPOINTS[(xwall,xend)]=(cid,xwall,xend,ywall,yend,x,y,kind)
    CORNER_ENDPOINTS[(ywall,yend)]=(cid,xwall,xend,ywall,yend,x,y,kind)
FACES=[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]

def component(name,reference=''):
    global CURRENT_COMPONENT,CURRENT_REFERENCE
    CURRENT_COMPONENT=name; CURRENT_REFERENCE=reference

def add(name,cat,verts,faces,mat,bevel=0,**meta):
    assert all(math.isfinite(c) for v in verts for c in v), name
    assert len(verts)>=3 and mat in MATERIALS
    key=re.sub(r'[^A-Za-z0-9_]+','_',CURRENT_COMPONENT+'_'+name)
    idx=SERIAL.get(key,0); SERIAL[key]=idx+1
    uid=f'{key}_{idx:03d}'
    o={'name':name,'id':uid,'assembly':CURRENT_COMPONENT,'collection':cat,
       'vertices':verts,'faces':faces,'material':mat,'bevel':bevel,
       'meta':{'referencia':CURRENT_REFERENCE,**meta}}
    OBJECTS.append(o); return o

def roof_level(y): return CONFIG['cota_apoyo_sur']+CONFIG['pendiente_techo']*y

def prism(name,x0,x1,y0,y1,bottom,thickness,mat,cat):
    xy=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    vs=[[x,y,bottom(y)+z] for z in [0,thickness] for x,y in xy]
    return add(name,cat,vs,FACES,mat)

def wall_piece(name,axis,pos,a,b,z0,z1,thick,mat,cat):
    if b-a<.0001:return None
    low=(lambda u:z0) if not callable(z0) else z0
    high=(lambda u:z1) if not callable(z1) else z1
    if min(high(a)-low(a),high(b)-low(b))<.0001:return None
    vs=[]
    for top in [False,True]:
        for u,v in [(a,-thick/2),(b,-thick/2),(b,thick/2),(a,thick/2)]:
            z=high(u) if top else low(u)
            vs.append([u,pos+v,z] if axis=='X' else [pos-v,u,z])
    return add(name,cat,vs,FACES,mat,.001)

def wall(name,axis,pos,start,end,th=.15,holes=(),external=False,outside=1,height=None,bearing=False):
    """Complete panel with matched architecture, opening frame and stud assembly.
    Opening tuple = clear modeled (start,end,sill,head,type), in metres.
    King/trimmer positions derive from each opening, never from manual blocks.
    """
    component(name,'Thallon 68A; 68C / 69B para dinteles. Adaptación métrica provisional.')
    # Primary X wall runs through; Y wall butts against its timber face.
    if external:
        for endpoint in ['start','end']:
            c=CORNER_ENDPOINTS.get((name,endpoint))
            if c:
                sg=-1 if endpoint=='start' else 1
                u=(c[5]+sg*STUD/2) if axis=='X' else (c[6]-sg*STUD/2)
                if endpoint=='start':start=u
                else:end=u
    if height is None:height=(lambda u:roof_level(pos if axis=='X' else u)) if external or bearing else (lambda u:H)
    elif not callable(height):
        hh=height; height=lambda u:hh
    holes=sorted(holes)
    for a,b,z0,z1,kind in holes:
        assert start<=a<b<=end and z1<min(height(a),height(b))-2*T,(name,a,b)
    for aa,bb in zip(holes,holes[1:]):assert aa[1]<=bb[0], name
    WALLS.append({'name':name,'axis':axis,'pos':pos,'start':start,'end':end,'external':external,'bearing':bearing,
                  'top_start':height(start),'top_end':height(end),'holes':holes,'outside':outside,'thickness':th})
    cat='01_Muros_exteriores' if external else '02_Tabiques'
    def part(n,a,b,z0,z1,ma='Revoque cálido',ca=cat,t=th,p=pos):
        if external and ca==cat:
            t=.0125;p=pos-outside*(STUD/2+t/2)
        return wall_piece(n,axis,p,a,b,z0,z1,t,ma,ca)
    cuts=sorted(set([start,end]+[c for h in holes for c in h[:2]]))
    for a,b in zip(cuts,cuts[1:]):
        h=next((h for h in holes if h[0]<(a+b)/2<h[1]),None)
        if h:
            part('Antepecho',a,b,0,h[2]);part('Paño sobre abertura',a,b,h[3],height)
        else:part('Paño',a,b,0,height)
        # Baseboard stops at floor-level openings.
        if not h or h[2]>.1:
            for side in ([-outside] if external else [-1,1]):
                part('Zócalo',a,b,.03,.11,'Roble natural','03_Carpinterias',.014,pos+side*(th/2+.007))
    # Metric study frame, 45 x 140 external; 45 x 90 internal.
    fc='08a_Entramado_paredes'; fd=STUD if external or bearing else .09
    def timber(n,a,b,z0,z1,depth=fd,pp=pos):return part(n,a,b,z0,z1,'Madera estructura',fc,depth,pp)
    # Bottom plate is actually interrupted at door openings.
    doors=[h for h in holes if h[2]<.05]
    bounds=sorted(set([start,end]+[c for h in doors for c in h[:2]]))
    for a,b in zip(bounds,bounds[1:]):
        if not any(h[0]<(a+b)/2<h[1] for h in doors):timber('Sole_plate',a,b,0,T)
    timber('Top_plate_1',start,end,lambda u:height(u)-2*T,lambda u:height(u)-T)
    top_start,top_end=start,end
    if external:
        for endpoint in ['start','end']:
            c=CORNER_ENDPOINTS.get((name,endpoint))
            if c:
                if c[7]=='concava':continue # Roof-height step: do not invent a same-level plate lap.
                sg=-1 if endpoint=='start' else 1
                # Alternate direction at second plate; no two overlapping solids.
                u=(c[5]-sg*STUD/2) if axis=='X' else (c[6]+sg*STUD/2)
                if endpoint=='start':top_start=u
                else:top_end=u
    timber('Top_plate_2',top_start,top_end,lambda u:height(u)-T,height)
    # Full-height end studs and grid studs; avoid king/jack envelopes.
    placed=[]
    centers=[start+T/2,end-T/2]
    p=start+CONFIG['modulo_montantes']
    while p<end-T:centers.append(p);p+=CONFIG['modulo_montantes']
    for p in centers:
        if any(abs(p-q)<T+.005 for q in placed):continue
        if any(h[0]-2*T-T/2-.001<p<h[1]+2*T+T/2+.001 for h in holes):continue
        timber('Common_stud',p-T/2,p+T/2,T,lambda u:height(u)-2*T);placed.append(p)
    for i,(a,b,z0,z1,kind) in enumerate(holes):
        assert a-2*T>=start-.001 and b+2*T<=end+.001,(name,'insufficient jamb space')
        # Two separate full-height kings and two trimmers carrying header.
        for side,lo,hi in [('L',a-2*T,a-T),('R',b+T,b+2*T)]:
            timber(f'O{i}_King_stud_{side}',lo,hi,T,lambda u:height(u)-2*T)
        for side,lo,hi in [('L',a-T,a),('R',b,b+T)]:timber(f'O{i}_Trimmer_{side}',lo,hi,T,z1)
        hd=.30 if b-a>2.6 else .22
        # Double header with gap across wall depth, diagram 68C; long openings tagged engineered study.
        for j,s in enumerate([-1,1]):timber(f'O{i}_Header_{j}',a-T,b+T,z1,z1+hd,T,pos+s*(fd/2-T/2))
        if z0>.05:timber(f'O{i}_Rough_sill',a,b,z0-T,z0)
        grid=[];p=start+CONFIG['modulo_montantes']
        while p<end:
            if a+T/2<=p<=b-T/2:grid.append(p)
            p+=CONFIG['modulo_montantes']
        if not grid:grid=[(a+b)/2]
        for j,p in enumerate(grid):
            if z0>T:timber(f'O{i}_Cripple_inferior_{j}',p-T/2,p+T/2,T,z0-T)
            timber(f'O{i}_Cripple_superior_{j}',p-T/2,p+T/2,z1+hd,lambda u:height(u)-2*T)
        OPENINGS.append({'id':f'{name}/O{i}','wall':name,'axis':axis,'pos':pos,'a':a,'b':b,'sill':z0,'head':z1,'kind':kind,'header_depth':hd,'reference':'Thallon 68A, 68C; 69B', 'structural_sizing':'NOT_CALCULATED'})
        opening(name+'_'+kind,axis,pos,a,b,z0,z1,kind)

def build_base():
    component('Base','Platea volumétrica; sistema de cimentación aún no diseñado.')
    for name,x0,y0,x1,y1 in [('Principal',0,0,W,D),('Ala_este',W,0,E,D),('Saliente_sur',XADD,-S,E,0)]:
        box('Platea_'+name,((x0+x1)/2,(y0+y1)/2,-.18),(x1-x0,y1-y0,.36),'Piso piedra','00_Base',.002)
        box('Piso_'+name,((x0+x1)/2,(y0+y1)/2,.006),(x1-x0,y1-y0,.02),'Piso piedra','00_Base',0)
    rooms=[('Principal',(.2,3.45,3.6,7.8),'Roble natural'),('Dormitorio 2',(.2,.2,2.75,2.1),'Roble natural'),
           ('Vestidor',(3.75,3.45,5.6,4.4),'Roble natural'),('Baño suite',(3.75,4.55,5.6,7.8),'Porcelanato'),
           ('Baño',(9.8,-2.2,12.9,0),'Porcelanato'),('Lavadero',(13.05,-2.2,14.8,0),'Porcelanato'),
           ('Dormitorio 3',(15.,-2.2,17.8,1.2),'Roble natural'),('Oficina',(15.,3.2,17.8,7.8),'Piso piedra')]
    for name,bounds,ma in rooms:
        x0,y0,x1,y1=bounds;ROOMS.append({'name':name,'bounds':bounds,'area':(x1-x0)*(y1-y0)})
        box('Solado_'+name,((x0+x1)/2,(y0+y1)/2,.023),(x1-x0,y1-y0,.018),ma,'00_Base',0)
        if ma=='Porcelanato':
            for j in range(1,int((x1-x0)/.6)+1):box('Junta_'+name,(x0+j*.6,(y0+y1)/2,.033),(.003,y1-y0,.001),'Juntas','00_Base',0)
            for j in range(1,int((y1-y0)/.6)+1):box('Junta_'+name,((x0+x1)/2,y0+j*.6,.033),(x1-x0,.003,.001),'Juntas','00_Base',0)

def build_walls():
    DOOR_SWINGS.update({'Dorm2_N_puerta':-70,'Bano_N_puerta':-70,'Lavadero_N_puerta':-70,'Dorm3_N_puerta':-70,'Oficina_S_puerta':70})
    # Exterior outline: north edge office flush at y8; east side straight x18.
    wall('Norte','X',7.9,0,E,.2,[(.7,3.1,.7,2.4,'ventana'),(4.15,5.15,1.7,2.4,'ventana'),(6.0,10.,0,2.5,'corrediza'),(10.4,14.4,0,2.5,'corrediza'),(15.45,17.4,.9,2.35,'ventana')],True,1)
    wall('Oeste','Y',.1,.2,7.8,.2,[(.55,1.65,1,2.25,'ventana'),(4.5,6.9,.7,2.4,'ventana')],True,-1)
    wall('Sur_principal','X',.1,0,XADD,.2,[(.7,2.15,1.,2.25,'ventana'),(3.4,5.,.8,2.3,'ventana'),(6.1,8.7,1.25,2.4,'ventana')],True,-1)
    # Shift the lower office-window jamb 150 mm to clear the existing roof-support post and king.
    wall('Este','Y',E-.1,0,D-.2,.2,[(1.6,2.65,0,2.2,'puerta'),(4.20,6.6,.9,2.35,'ventana')],True,1)
    wall('Este_anexo','Y',E-.1,-S+.2,0,.2,[(-1.8,-.2,.9,2.35,'ventana')],True,1,lambda u:3.0+.10*(u+S-.1))
    south_height=lambda u:3.00
    wall('Sur_anexo','X',-S+.1,XADD,E,.2,[(10.15,11.15,1.65,2.3,'ventana'),(13.4,14.3,1.5,2.3,'ventana'),(15.5,17.2,.9,2.35,'ventana')],True,-1,south_height)
    wall('Oeste_anexo','Y',XADD+.1,-S+.2,0,.2,[],True,-1,lambda u:3.0+.10*(u+S-.1))
    # Bedroom/suite adjusted from V03. Private circulation open to kitchen.
    wall('Dorm2_N','X',2.175,.2,2.75,holes=[(1.7,2.53,0,2.1,'puerta')])
    wall('Dorm2_E','Y',2.825,.2,2.25)
    wall('Principal_S','X',3.375,.2,5.6,holes=[(2.62,3.47,0,2.1,'puerta')])
    wall('Suite_E','Y',5.7,3.45,7.8,.2,bearing=True)
    wall('Principal_E','Y',3.675,3.45,7.8,holes=[(3.55,4.35,0,2.1,'paso'),(5.4,6.2,0,2.1,'puerta')])
    wall('Vestidor_N','X',4.475,3.75,5.6)
    # South service doors at former toilette/laundry positions.
    wall('Bano_N','X',.1,XADD+.1+STUD/2,12.975,.2,[(12.08,12.88,0,2.1,'puerta')],bearing=True)
    wall('Lavadero_N','X',.1,12.975,15.,.2,[(13.48,14.35,0,2.1,'puerta')],bearing=True)
    wall('Bano_Lavadero','Y',12.975,-2.2,0)
    # Open passage to full height, no portal or trim; smooth plaster returns.
    wall('Ala_Este_Oeste_Sur','Y',14.9,0,1.48,.2,bearing=True)
    wall('Ala_Este_Oeste_Norte','Y',14.9,2.83,7.8,.2,bearing=True)
    wall('Lavadero_Dorm3','Y',14.9,-2.2,0,.2,bearing=True,height=lambda u:3.0+.10*(u+S-.1))
    wall('Dorm3_N','X',1.275,15.,17.8,holes=[(15.18,16.04,0,2.1,'puerta')])
    wall('Oficina_S','X',3.125,15.,17.8,holes=[(15.18,16.04,0,2.1,'puerta')])

def bidet(name,x,y):
    cat='04d_Banos_lavadero';component(name)
    ellipsoid(name+'_pedestal',(x,y,.22),(.29,.40,.38),'Cerámica blanca',cat)
    ellipsoid(name+'_taza',(x,y,.42),(.39,.58,.15),'Cerámica blanca',cat)
    ellipsoid(name+'_hueco',(x,y+.04,.491),(.25,.34,.012),'Grafito',cat)
    cylinder(name+'_grifo',(x,y-.20,.49),(x,y-.20,.61),.014,'Acero',cat)
    cylinder(name+'_pico',(x,y-.20,.61),(x,y-.09,.61),.012,'Acero',cat)

def vanity(name,x,y):
    component(name);cat='04d_Banos_lavadero'
    box(name+'_mueble',(x,y,.65),(.62,.54,.44),'Roble natural',cat,.012)
    # Basin sits above vanity, rather than being covered by a solid countertop.
    sink(name+'_bacha',x,y,.99,cat,.49,.40)

def build_furniture():
    component('Cocina_mesada')
    for i in range(7):cabinet('Bajo_mesada',6.1+i*.6,.54,.6)
    # Actual opening in worktop for the sink.
    for x0,x1 in [(5.8,8.05),(8.61,10.0)]:box('Mesada',((x0+x1)/2,.54,.92),(x1-x0,.69,.055),'Cerámica blanca','04a_Cocina',.005)
    for yy in [.255,.825]:box('Borde_mesada',(8.33,yy,.92),(.56,.12,.055),'Cerámica blanca','04a_Cocina',.003)
    sink('Bacha_cocina',8.33,.54,.94)
    box('Anafe',(6.55,.54,.955),(.6,.52,.015),'Negro','04a_Cocina')
    for xx in [6.4,6.7]:
        for yy in [.4,.68]:cylinder('Placa_induccion',(xx,yy,.965),(xx,yy,.969),.095,'Grafito','04a_Cocina',24)
    box('Horno',(6.55,.856,.5),(.52,.025,.49),'Grafito','04a_Cocina')
    box('Horno_vidrio',(6.55,.875,.47),(.44,.012,.3),'Pantalla','04a_Cocina')
    box('Horno_manija',(6.55,.905,.70),(.40,.035,.02),'Acero','04a_Cocina')
    component('Heladera')
    box('Cuerpo',(10.38,.56,1.05),(.72,.72,2.10),'Acero','04a_Cocina',.025)
    for z,h in [(.45,.81),(1.5,1.22)]:box('Puerta',(10.38,.931,z),(.70,.025,h),'Cerámica blanca','04a_Cocina',.01)
    box('Tirador',(10.67,.96,1.52),(.02,.025,.38),'Acero','04a_Cocina')
    component('Isla')
    cabinet('Isla',8.15,2.63,2.10,.85)
    box('Isla_tapa',(8.15,2.70,.93),(2.3,1.02,.055),'Cerámica blanca','04a_Cocina',.014)
    for x in [7.45,8.15,8.85]:
        component('Taburete_'+str(x));cylinder('Asiento',(x,3.40,.65),(x,3.40,.7),.20,'Roble natural','04a_Cocina',24)
        for dx in [-.13,.13]:
            for dy in [-.13,.13]:cylinder('Pata',(x+dx,3.4+dy,.03),(x+dx,3.4+dy,.65),.015,'Grafito','04a_Cocina')
    component('Mesa_comedor');cat='04b_Social'
    box('Tapa',(8.2,5.65,.765),(1.05,2.8,.065),'Roble natural',cat,.025)
    for y in [4.65,6.65]:box('Base',(8.2,y,.37),(.65,.12,.74),'Grafito',cat)
    for s in [-1,1]:
        for i in range(4):
            component(f'Silla_comedor_{s}_{i}');chair('Silla',8.2+s*.85,4.6+i*.7,-s*math.pi/2,cat=cat)
    for y,rot in [(3.96,math.pi),(7.34,0)]:
        component('Cabecera_'+str(y));chair('Silla',8.2,y,rot,cat=cat)
    component('Sofa');cat='04b_Social'
    box('Alfombra',(12.1,5.75,.045),(3.4,3.1,.018),'Lino',cat,.03)
    box('Base',(11.13,5.95,.27),(.92,2.75,.34),'Verde oliva',cat,.06)
    box('Respaldo',(10.76,5.95,.65),(.19,2.75,.67),'Verde oliva',cat,.055)
    for y in [5.07,5.95,6.83]:box('Almohadon',(11.17,y,.51),(.73,.82,.18),'Verde oliva',cat,.06)
    box('Chaise',(11.85,6.83,.40),(.7,.82,.48),'Verde oliva',cat,.06)
    component('Mesa_living');box('Tapa',(12.55,5.85,.4),(.65,1.15,.055),'Roble natural',cat,.04)
    for y in [5.42,6.28]:box('Pata',(12.55,y,.2),(.4,.03,.4),'Grafito',cat)
    component('Biblioteca_TV')
    box('Mueble_bajo',(14.53,5.80,.34),(.46,2.8,.62),'Roble natural',cat,.012)
    box('TV_marco',(14.45,5.80,1.22),(.075,1.36,.79),'Grafito',cat)
    box('TV_pantalla',(14.407,5.80,1.22),(.009,1.30,.73),'Pantalla',cat)
    for y in [4.6,7.0]:
        for z in [.85,1.3,1.75,2.2]:box('Estante',(14.60,y,z),(.32,.52,.035),'Roble natural',cat)
        for i in range(5):box('Libro',(14.56,y-.2+i*.085,1.47),(.22,.05,.28),['Lino','Terracota','Verde oliva'][i%3],cat,.002)
    component('Principal_cama');bed('Cama',1.85,6.60,1.60)
    for x in [.69,3.0]:
        component('Mesa_luz_'+str(x));box('Cajon',(x,7.22,.35),(.44,.44,.60),'Roble natural','04c_Dormitorios',.016)
        cylinder('Lampara',(x,7.22,.65),(x,7.22,.93),.04,'Grafito','04c_Dormitorios')
        ellipsoid('Pantalla',(x,7.22,1.),(.25,.25,.2),'Lino','04c_Dormitorios')
    component('Dorm2_cama');bed('Cama',1.47,.92,.90,math.pi/2)
    # Narrow wall-mounted shelf: no wardrobe blocking the only clearance in compact room.
    component('Dorm2_estante');box('Estante',(1.2,.25,1.35),(1.3,.16,.03),'Roble natural','04c_Dormitorios')
    component('Dorm3_cama');bed('Cama',16.7,-.72,1.0)
    component('Dorm3_placard');box('Cuerpo',(15.30,-1.325,1.16),(.55,1.55,2.30),'Roble natural','04c_Dormitorios',.008)
    for y in [-1.71,-.94]:box('Puerta',(15.58,y,1.16),(.025,.755,2.26),'Lino','04c_Dormitorios',.002)
    component('Vestidor_mueble')
    for z in [.15,.65,1.1,2.2]:box('Estante',(5.33,3.92,z),(.53,.9,.035),'Roble natural','04c_Dormitorios')
    for y in [3.48,4.36]:box('Costado',(5.33,y,1.16),(.53,.035,2.25),'Roble natural','04c_Dormitorios')
    cylinder('Barral',(5.20,3.51,1.95),(5.20,4.33,1.95),.015,'Acero','04c_Dormitorios')
    component('Oficina_escritorio');cat='04e_Oficina'
    box('Tapa',(16.35,6.64,.75),(1.75,.75,.065),'Roble natural',cat,.016)
    for x in [15.65,17.05]:box('Pata',(x,6.64,.37),(.04,.62,.74),'Grafito',cat)
    box('Monitor',(16.35,6.84,1.1),(.62,.06,.36),'Grafito',cat)
    box('Monitor_base',(16.35,6.84,.84),(.23,.21,.1),'Grafito',cat)
    box('Teclado',(16.35,6.37,.799),(.43,.15,.02),'Cerámica blanca',cat)
    component('Oficina_silla');chair('Silla',16.35,5.92,math.pi,'Grafito',cat)
    component('Oficina_biblioteca')
    for z in [.25,.75,1.25,1.75,2.25]:box('Estante',(17.59,4.83,z),(.36,1.4,.035),'Roble natural',cat)
    # All fixtures grouped independently; precisely two WC and two bidets.
    component('Suite_ducha');shower('Ducha',4.27,7.15,.95,1.15)
    component('Suite_WC');toilet('Inodoro',4.24,4.96)
    bidet('Suite_bidet',5.14,4.96);vanity('Suite_vanitory',5.19,7.33)
    component('Bano_ducha');shower('Ducha',10.35,-1.39,.97,1.52)
    component('Bano_WC');toilet('Inodoro',11.54,-1.89)
    bidet('Bano_bidet',12.36,-1.89);vanity('Bano_vanitory',11.29,-.39)
    component('Lavadero_lavarropas');cat='04d_Banos_lavadero'
    box('Cuerpo',(14.34,-1.87,.47),(.64,.62,.9),'Cerámica blanca',cat,.024)
    cylinder('Aro',(14.34,-1.55,.46),(14.34,-1.515,.46),.23,'Acero',cat,28)
    cylinder('Vidrio',(14.34,-1.514,.46),(14.34,-1.51,.46),.18,'Pantalla',cat,28)
    component('Lavadero_pileta');vanity('Lavadero_pileta',13.52,-1.84)
    # No console or furniture in front of the laundry entrance.
    component('Iluminacion');cat='05_Iluminacion'
    for x,y in [(1.8,5.5),(1.4,1.1),(4.65,6.3),(11.6,-.8),(14,-1),(16.5,-.4),(16.4,5.5),(12.4,5.8),(8.2,2.7)]:
        cylinder('Plafon',(x,y,2.70),(x,y,2.735),.14,'Luz',cat,20)
    for y in [4.9,5.65,6.4]:
        cylinder('Cable',(8.2,y,2.05),(8.2,y,2.75),.006,'Grafito',cat,8)
        cylinder('Colgante',(8.2,y,1.97),(8.2,y,2.13),.14,'Terracota',cat,24,r2=.07)

def build_roof():
    component('Techo_principal','Thallon 129A, p.130: cabios apoyados y apoyo intermedio. Secciones pendientes de cálculo.')
    # Actual inclined rafters supported at north/south walls AND purlin y4.
    for i in range(31):
        x=.08+i*(E-.16)/30
        prism('Cabio_inclinado',x-.0315,x+.0315,-.35,8.35,roof_level,.24,'Madera estructura','08b_Estructura_techo')
    support_x=[.1,5.7,14.9,E-.1]
    z=roof_level(4.)
    for i,(a,b) in enumerate(zip(support_x,support_x[1:])):
        o=box('Viga_intermedia_'+str(i),((a+b)/2,4.,z-.31),(b-a,.20,.62),'Madera estructura','08b_Estructura_techo',.003)
        o['meta'].update({'luz_entre_ejes_m':b-a,'dimensionamiento':'Pendiente; viga central de gran luz, verificar solución de madera laminada/ingeniería.'})
    for x in support_x:
        box('Poste_apoyo_viga',(x,4.,(z-.62)/2),(.20,.20,z-.62),'Madera estructura','08b_Estructura_techo',.002)
    # Roof deck in a distinct collection for later layers.
    prism('Tablero_cubierta',-.35,E+.35,-.35,8.35,lambda y:roof_level(y)+.24,.018,'Roble natural','08c_Tablero_techo')
    prism('Chapa_principal',-.40,E+.40,-.40,8.40,lambda y:roof_level(y)+.258,.035,'Zinc','06b_Cubiertas')
    for i in range(38):
        x=-.35+i*.5
        cylinder('Junta_alzada',(x,-.39,roof_level(-.39)+.301),(x,8.39,roof_level(8.39)+.301),.01,'Zinc','06b_Cubiertas',6)
    for x in [-.4,E+.4]:prism('Fascia_lateral',x-.025,x+.025,-.42,8.42,lambda y:roof_level(y)-.02,.33,'Grafito','06b_Cubiertas')
    for y in [-.41,8.41]:box('Fascia_borde',(E/2,y,roof_level(y)+.13),(E+.85,.05,.34),'Grafito','06b_Cubiertas',.002)
    # Lean-to south extension: slopes downward away from main wall.
    component('Techo_anexo_sur','Thallon p.130: simple-span shed roof. Encuentro e impermeabilización por desarrollar.')
    low=lambda y:3.0+.10*(y+S-.1)
    for i in range(15):
        x=XADD+.07+i*(E-XADD-.14)/14
        prism('Cabio_anexo',x-.0315,x+.0315,-S-.3,.15,low,.18,'Madera estructura','08b_Estructura_techo')
    # High support sill under south annex rafters, carried by frame at main south boundary.
    box('Viga_alta_anexo',((XADD+E)/2,.08,low(.08)-.14),(E-XADD,.14,.28),'Madera estructura','08b_Estructura_techo')
    for x in [XADD+.1,12.975,14.9,E-.1]:
        box('Poste_anexo',(x,.08,(low(.08)-.28)/2),(.14,.14,low(.08)-.28),'Madera estructura','08b_Estructura_techo')
    prism('Tablero_anexo',XADD-.2,E+.35,-S-.35,.15,lambda y:low(y)+.18,.018,'Roble natural','08c_Tablero_techo')
    prism('Chapa_anexo',XADD-.25,E+.4,-S-.4,.17,lambda y:low(y)+.198,.035,'Zinc','06b_Cubiertas')
    # Flat ceiling is independently removable, not confused with roof rafters.
    component('Cielorraso')
    for x0,y0,x1,y1 in [(0,0,E,D),(XADD,-S,E,0)]:box('Panel',((x0+x1)/2,(y0+y1)/2,2.795),(x1-x0,y1-y0,.07),'Revoque cálido','06a_Cielorraso',0)

def build_exterior():
    component('Galeria_deck');cat='07_Exterior'
    box('Bastidor',(10,9.5,-.11),(10,3,.18),'Madera exterior',cat)
    for i in range(72):box('Tabla',(5.068+i*.139,9.5,.004),(.132,3,.03),'Madera exterior',cat,.002)
    component('Galeria_estructura','Esquema de apoyo; cimentación y uniones pendientes.')
    level=lambda y:3.03-.06*(y-8.)
    for y in [8.15,10.85]:
        for x in [5.1,10.,14.9]:box('Poste',(x,y,(level(y)-.2)/2),(.14,.14,level(y)-.2),'Madera estructura','08b_Estructura_techo')
        box('Viga',(10,y,level(y)-.1),(10.2,.14,.2),'Madera estructura','08b_Estructura_techo')
    for i in range(21):
        x=5.+i*.5;prism('Cabio_galeria',x-.03,x+.03,8.,11.1,level,.14,'Madera estructura','08b_Estructura_techo')
    prism('Chapa_galeria',4.9,15.1,7.98,11.15,lambda y:level(y)+.14,.03,'Zinc','06c_Cubierta_galeria')
    component('Galeria_muebles')
    box('Banco',(6.7,10.50,.46),(2.3,.6,.13),'Roble natural',cat,.016)
    for x in [5.8,7.6]:box('Pata_banco',(x,10.5,.23),(.1,.46,.46),'Grafito',cat)
    box('Mesa',(9.2,10.0,.43),(1.2,.7,.06),'Roble natural',cat,.02)
    chair('Silla',8.85,10.65,cat=cat);chair('Silla',9.55,10.65,cat=cat)
    component('Parrilla','Volumetría arquitectónica. Resolver aislación térmica, distancias y salida de humos antes de construcción.')
    box('Base',(14.40,9.50,.44),(.80,1.40,.87),'Revoque cálido',cat)
    box('Fondo',(14.79,9.5,1.3),(.08,1.4,.87),'Grafito',cat)
    for y in [8.84,10.16]:box('Lateral',(14.40,y,1.3),(.8,.08,.87),'Grafito',cat)
    box('Campana',(14.4,9.5,1.92),(.85,1.43,.35),'Grafito',cat)
    box('Chimenea',(14.55,9.5,2.78),(.33,.40,1.4),'Grafito',cat)
    for i in range(18):cylinder('Rejilla',(14.04,8.94+i*.064,.99),(14.75,8.94+i*.064,.99),.005,'Acero',cat,6)
    component('Vegetacion');plant('Maceta_galeria',5.5,8.7);plant('Maceta_living',14.0,3.8)
    component('Entorno')
    box('Terreno_sin_mensura',(9,4,-.48),(27,22,.15),'Tierra','09_Entorno',0)
    box('Sendero_entrada',(E+1,2.1,-.12),(2,1.3,.15),'Piso piedra',cat)
    box('Escalon_deck',(10,11.24,-.11),(4,.45,.13),'Piso piedra',cat)

LAYER_CATS=['10_05_Insulation','11_06_OSB','12_07_WRB','13_08_Camara_listones','14_08_Siding']
LAYER_MODES=[('05_Insulation','insulation'),('06_Sheathing_OSB','osb'),('07_WRB_Tyvek','wrb'),('08_Siding_oscuro','siding')]

def wall_top(w,u):
    return w['top_start']+(w['top_end']-w['top_start'])*(u-w['start'])/(w['end']-w['start'])

def layer_wall(w,layer):
    """Layer-specific corner extent: OSB butt/lap and siding corner-board clearance."""
    p=dict(w);byname={q['name']:q for q in WALLS}
    r=STUD/2;osb=CONFIG['osb_espesor'];j=CONFIG['osb_junta']
    outer=r+osb+2*CONFIG['wrb_espesor_grafico']+.0005
    for endpoint in ['start','end']:
        c=CORNER_ENDPOINTS.get((w['name'],endpoint))
        if not c:continue
        cid,xwall,xe,ywall,ye,cx,cy,kind=c
        sx=byname[ywall]['outside'];sy=byname[xwall]['outside'];sg=-1 if endpoint=='start' else 1
        if layer=='osb':
            if w['axis']=='X':u=cx+sx*(r+(osb if kind=='convexa' else 0))
            else:u=cy+sy*(r+(osb if kind=='concava' else 0))-sg*j
        elif layer=='siding':
            radial=outer+CONFIG['camara_ventilada']+CONFIG['siding_espesor']
            u=(cx+sx*radial if w['axis']=='X' else cy+sy*radial)-sg*(CONFIG['ancho_esquinero']+CONFIG['junta_siding_esquinero'])
        else:
            radial=r+osb+2*CONFIG['wrb_espesor_grafico']
            u=cx+sx*radial if w['axis']=='X' else cy+sy*radial
        p[endpoint]=u
    p['top_start']=wall_top(w,p['start']);p['top_end']=wall_top(w,p['end'])
    return p

def build_corner_frame():
    byname={w['name']:w for w in WALLS}
    for cid,xname,xe,yname,ye,cx,cy,kind in CORNER_SPECS:
        w=byname[xname];sg=-1 if xe=='start' else 1
        component(xname,'Thallon 71A/C: montante perpendicular de respaldo, cavidad aislable y soleras alternadas. Adaptación 45x140 mm.')
        edge=w[xe]
        if kind=='convexa':
            a,b=sorted([edge-sg*T,edge-sg*(T+STUD)])
            pp=w['pos']-w['outside']*(STUD/2-T/2)
            o=wall_piece('Esquina_'+cid+'_Backer_perpendicular',w['axis'],pp,a,b,T,lambda u:wall_top(w,u)-2*T,T,'Madera estructura','08a_Entramado_paredes')
            if o:o['meta'].update(corner_id=cid,funcion='respaldo interior sin cerrar la cavidad aislable')
            o=wall_piece('Esquina_'+cid+'_Aislacion_respaldo',w['axis'],w['pos']+w['outside']*T/2,a,b,T,lambda u:wall_top(w,u)-2*T,STUD-T,'Lana mineral','10_05_Insulation')
            if o:o['bevel']=0;o['meta'].update(corner_id=cid,wall_id=xname)
        else:
            # Back the structural board edge at the inside/re-entrant corner.
            edge=cx+byname[yname]['outside']*STUD/2
            a,b=edge-T,edge
            o=wall_piece('Esquina_'+cid+'_Respaldo_OSB',w['axis'],w['pos'],a,b,T,lambda u:wall_top(w,u)-2*T,STUD,'Madera estructura','08a_Entramado_paredes')
            if o:o['meta'].update(corner_id=cid,funcion='apoyo del canto OSB del rincón entrante')

def folded_corner(name,c,radial,width,thick,mat,cat,z0=0):
    """One watertight L-shaped mesh, not two disconnected planes or an opaque box."""
    cid,xname,xe,yname,ye,cx,cy,kind=c;byname={w['name']:w for w in WALLS}
    xw,yw=byname[xname],byname[yname];sx=yw['outside'];sy=xw['outside']
    dx=1 if xe=='start' else -1;dy=1 if ye=='start' else -1
    px,py=cx+sx*radial,cy+sy*radial
    poly=[(px+dx*width,py),(px,py),(px,py+dy*width),(px-sx*thick,py+dy*width),
          (px-sx*thick,py-sy*thick),(px+dx*width,py-sy*thick)]
    area=sum(poly[i][0]*poly[(i+1)%6][1]-poly[(i+1)%6][0]*poly[i][1] for i in range(6))
    if area<0:poly.reverse()
    # Shared corner height; secondary wall leg follows its own rake away from the vertex.
    corner_h=max(wall_top(xw,cx),wall_top(yw,cy))
    def height(x,y):
        along=abs(y-py)
        return max(wall_top(xw,x),wall_top(yw,y)) if along<.001 else wall_top(yw,y)+(corner_h-wall_top(yw,cy))*max(0,1-along/width)
    vertices=[[x,y,z0] for x,y in poly]+[[x,y,height(x,y)] for x,y in poly]
    # Ear clipping is needed for a concave L; a fan would fill the ventilation void.
    remaining=list(range(6));tris=[]
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    while len(remaining)>3:
        for k,b in enumerate(remaining):
            a=remaining[k-1];cc=remaining[(k+1)%len(remaining)]
            if cross(poly[a],poly[b],poly[cc])<=1e-12:continue
            if any(all(cross(poly[u],poly[v],poly[q])>=-1e-12 for u,v in [(a,b),(b,cc),(cc,a)]) for q in remaining if q not in [a,b,cc]):continue
            tris.append([a,b,cc]);remaining.pop(k);break
        else:raise ValueError('Invalid corner polygon '+cid)
    tris.append(remaining)
    faces=[list(reversed(t)) for t in tris]+[[i+6 for i in t] for t in tris]+[[i,(i+1)%6,(i+1)%6+6,i+6] for i in range(6)]
    component('Esquina_'+cid,'Thallon 71A/C,78: unión y apoyo. DuPont Housewrap: retorno mínimo 300 mm; ver LEEME_V04.md.')
    o=add(name,cat,vertices,faces,mat,0,corner_id=cid,tipo=kind,retorno_m=width,espesor_m=thick)
    return o

def build_corner_finishes():
    r=STUD/2;osb=CONFIG['osb_espesor'];wrb=CONFIG['wrb_espesor_grafico'];gap=CONFIG['camara_ventilada'];sid=CONFIG['siding_espesor']
    outer=r+osb+2*wrb+.0005
    byname={w['name']:w for w in WALLS}
    for c in CORNER_SPECS:
        cid,xname,xe,yname,ye,cx,cy,kind=c
        folded_corner('WRB_plegada_continua',c,outer,CONFIG['retorno_wrb_esquina'],.0005,'WRB','12_07_WRB')
        folded_corner('Esquinero_siding_L',c,outer+gap+sid,CONFIG['ancho_esquinero'],sid,'Siding oscuro','14_08_Siding',.03)
        # Narrow seals at trim/siding joints, at the exposed surface only; drainage cavity stays open.
        for name,endpoint in [(xname,xe),(yname,ye)]:
            w=byname[name];p=layer_wall(w,'siding');sg=-1 if endpoint=='start' else 1
            edge=p[endpoint];a,b=sorted([edge,edge+sg*CONFIG['junta_siding_esquinero']])
            component('Esquina_'+cid,'Esquinero propuesto; perfil, sellador y fijación por confirmar con fabricante de siding.')
            o=wall_piece('Junta_siding_esquinero',w['axis'],w['pos']+w['outside']*(outer+gap+sid-.0025),a,b,.03,
                         lambda u:wall_top(w,u),.005,'Sellado flexible','14_08_Siding')
            if o:o['bevel']=0;o['meta']['corner_id']=cid
            # Two vertical supports, one on each face, leave open vertical drainage channels.
            inside=-sg;u=edge+sg*.03
            o=wall_piece('Liston_apoyo_esquinero',w['axis'],w['pos']+w['outside']*(outer+gap/2),u-.0225,u+.0225,.03,
                         lambda u:wall_top(w,u)-.03,gap,'Madera estructura','13_08_Camara_listones')
            if o:o['meta']['corner_id']=cid

def skin(w,name,a,b,z0,z1,offset,thick,mat,cat):
    """Clip each surface to the actual openings and sloping wall outline."""
    a=max(a,w['start']);b=min(b,w['end'])
    cuts=[a,b]+[u for h in w['holes'] for u in h[:2] if a<u<b]
    slope=(w['top_end']-w['top_start'])/(w['end']-w['start'])
    if abs(slope)>1e-9:
        for z in [z0,z1]:
            u=w['start']+(z-w['top_start'])/slope
            if a<u<b:cuts.append(u)
    cuts=sorted(set(cuts))
    for lo,hi in zip(cuts,cuts[1:]):
        if hi-lo<1e-5:continue
        middle=(lo+hi)/2
        hole=next((h for h in w['holes'] if h[0]<middle<h[1]),None)
        spans=[(z0,z1)] if hole is None else [(z0,min(z1,hole[2])),(max(z0,hole[3]),z1)]
        for bot,top in spans:
            if min(top,wall_top(w,middle))-bot<.0001:continue
            o=wall_piece(name,w['axis'],w['pos']+w['outside']*offset,lo,hi,bot,
                         lambda u,t=top:min(t,wall_top(w,u)),thick,mat,cat)
            if o:
                o['bevel']=0
                o['meta'].update(wall_id=w['name'],capa=cat,espesor_m=thick)

def fill_cavities(w):
    """Sweep exact timber boundaries; insulation occupies free bays, never wood."""
    import numpy as np
    axis=0 if w['axis']=='X' else 1;cross=1-axis
    members=[o for o in OBJECTS if o['collection']=='08a_Entramado_paredes' and o['assembly']==w['name']]
    # Crossing cap plates belong to the other wall but occupy this corner too.
    for o in OBJECTS:
        if o['collection']=='08a_Entramado_paredes' and o['assembly']!=w['name'] and o['name']=='Top_plate_2':
            v=np.array(o['vertices'])
            if min(v[:,cross].max(),w['pos']+STUD/2)-max(v[:,cross].min(),w['pos']-STUD/2)>1e-5:
                if min(v[:,axis].max(),w['end'])-max(v[:,axis].min(),w['start'])>1e-5:members.append(o)
    # Include roof support posts embedded in the exterior wall.
    for o in OBJECTS:
        if o['collection']=='08b_Estructura_techo' and o['name'].startswith('Poste'):
            v=np.array(o['vertices'])
            if v[:,cross].min()<w['pos']+STUD/2 and v[:,cross].max()>w['pos']-STUD/2:members.append(o)
    blockers=[];cuts={w['start'],w['end']}
    for o in members:
        v=np.array(o['vertices']);a=max(w['start'],float(v[:,axis].min()));b=min(w['end'],float(v[:,axis].max()))
        if a>=b:continue
        # Headers fill depth only partly; reserve the entire rectangle here and fill their core separately.
        def edge(top,v=v):
            vv=v[4:8] if top else v[:4]
            plane=np.linalg.lstsq(np.column_stack((vv[:,:2],np.ones(4))),vv[:,2],rcond=None)[0]
            return lambda u:float(plane[axis]*u+plane[cross]*w['pos']+plane[2])
        blockers.append((a,b,edge(False),edge(True)));cuts.update([a,b])
    for a,b,sill,head,kind in w['holes']:
        blockers.append((a,b,lambda u,z=sill:z,lambda u,z=head:z));cuts.update([a,b])
    component(w['name'],'Thallon 68A-C: conservar cavidades accesibles; relleno térmico propuesto, sin cálculo higrotérmico.')
    cuts=sorted(cuts)
    for a,b in zip(cuts,cuts[1:]):
        mid=(a+b)/2
        active=sorted([q for q in blockers if q[0]<mid<q[1]],key=lambda q:q[2](mid))
        cursor=lambda u:0.
        free=[]
        for _,_,low,high in active:
            if low(mid)>cursor(mid)+1e-5:free.append((cursor,low))
            if high(mid)>cursor(mid):cursor=high
        if cursor(mid)<wall_top(w,mid)-1e-5:free.append((cursor,lambda u:wall_top(w,u)))
        for low,high in free:
            # Blocking at the horizontal OSB joint, cut exactly between existing timbers.
            z=CONFIG['osb_alto'];ranges=[(low,high)]
            if low(mid)<z-T/2 and high(mid)>z+T/2:
                wall_piece('Blocking_junta_OSB',w['axis'],w['pos'],a,b,z-T/2,z+T/2,STUD,'Madera estructura','08a_Entramado_paredes')
                ranges=[(low,lambda u:z-T/2),(lambda u:z+T/2,high)]
            for lo,hi in ranges:
                o=wall_piece('Aislacion_cavidad',w['axis'],w['pos'],a,b,lo,hi,CONFIG['aislacion_espesor'],'Lana mineral','10_05_Insulation')
                if o:o['bevel']=0;o['meta'].update(wall_id=w['name'],tipo='cavidad entre madera, incluidos paños bajo/sobre vanos')
    for i,(a,b,z0,z1,kind) in enumerate(w['holes']):
        hd=.30 if b-a>2.6 else .22
        o=wall_piece(f'O{i}_Aislacion_nucleo_dintel',w['axis'],w['pos'],a-T,b+T,z1,z1+hd,STUD-2*T,'Lana mineral','10_05_Insulation')
        if o:o['bevel']=0;o['meta'].update(wall_id=w['name'],tipo='núcleo entre las dos hojas del dintel; revisar solución resistente')

def build_envelope():
    """Exterior only. Layer offsets are measured from the frame centerline."""
    osb=CONFIG['osb_espesor'];wrb=CONFIG['wrb_espesor_grafico'];gap=CONFIG['camara_ventilada'];sid=CONFIG['siding_espesor']
    for w in [w for w in WALLS if w['external']]:
        fill_cavities(w)
        component(w['name'],'Thallon 71A/C,78. APA panel spacing; DuPont WRB/furring guidance. Ver LEEME_V04.md.')
        ow=layer_wall(w,'osb');mw=layer_wall(w,'wrb');sw=layer_wall(w,'siding')
        a=ow['start'];j=CONFIG['osb_junta'];row=0
        while a<ow['end']-.001:
            # Keep vertical panel joints on the existing stud grid despite extended corners.
            grid=w['start']+math.floor((a+CONFIG['osb_modulo']-w['start']+1e-6)/CONFIG['modulo_montantes'])*CONFIG['modulo_montantes']
            b=min(max(grid,a+.05),ow['end'])
            if ow['end']-a<=CONFIG['osb_modulo']:b=ow['end']
            for k,z in enumerate([0,CONFIG['osb_alto']]):
                skin(ow,f'OSB_panel_{row:02d}_{k}',a+(j/2 if row else 0),b-(j/2 if b<ow['end'] else 0),
                     z+(j/2 if k else 0),z+CONFIG['osb_alto']-j/2,STUD/2+osb/2,osb,'OSB','11_06_OSB')
            a=b;row+=1
        # Upper membrane sheet overlaps the lower by 150 mm, visibly outside it.
        for k,z in enumerate([0,CONFIG['osb_alto']-CONFIG['wrb_solape']]):
            skin(mw,f'WRB_faja_{k}',mw['start'],mw['end'],z,z+CONFIG['osb_alto'],STUD/2+osb+wrb/2+k*wrb,wrb,'WRB','12_07_WRB')
        outer=STUD/2+osb+2*wrb
        for i,(a,b,sill,head,kind) in enumerate(w['holes']):
            # Graphic flashing zones outside clear openings; sill-pan folding remains a future detail.
            for side,u0,u1,z0,z1 in [('Jamba_L',a-.06,a,sill,head+.06),('Jamba_R',b,b+.06,sill,head+.06),('Cabezal',a-.06,b+.06,head,head+.06)]:
                skin(w,f'O{i}_Flashing_{side}',u0,u1,z0,z1,outer+.00025,.0005,'Cinta WRB','12_07_WRB')
            if sill>0:skin(w,f'O{i}_Flashing_antepecho',a-.06,b+.06,sill-.06,sill,outer+.00025,.0005,'Cinta WRB','12_07_WRB')
        # Vertical battens give a continuous drainage route behind horizontal siding.
        # Align to actual stud centers, including the sides of openings.
        members=[o for o in OBJECTS if o['assembly']==w['name'] and o['collection']=='08a_Entramado_paredes' and ('Common_stud' in o['name'] or 'King_stud' in o['name'])]
        axis=0 if w['axis']=='X' else 1
        for i,o in enumerate(members):
            u=(min(v[axis] for v in o['vertices'])+max(v[axis] for v in o['vertices']))/2
            skin(w,f'Liston_vertical_{i:02d}',u-.0225,u+.0225,.03,max(w['top_start'],w['top_end'])-.03,
                 outer+.0005+gap/2,gap,'Madera estructura','13_08_Camara_listones')
        z=.03;k=0
        while z<max(w['top_start'],w['top_end'])-.03:
            skin(sw,f'Siding_horizontal_{k:02d}',sw['start'],sw['end'],z,min(z+CONFIG['siding_paso']-.002,max(w['top_start'],w['top_end'])-.03),
                 outer+.0005+gap+sid/2,sid,'Siding oscuro','14_08_Siding')
            z+=CONFIG['siding_paso'];k+=1
    build_corner_finishes()

def conform_corner_plate_planes():
    """Fit primary-wall top cuts to the same roof plane as the perpendicular wall."""
    byname={w['name']:w for w in WALLS if w['external'] and w['axis']=='X'}
    for o in OBJECTS:
        w=byname.get(o['assembly'])
        if not w:continue
        slope=.10 if w['name']=='Sur_anexo' else CONFIG['pendiente_techo']
        for v in o['vertices']:
            h=wall_top(w,v[0])
            if any(abs(v[2]-(h-k*T))<1e-6 for k in [0,1,2]):v[2]+=slope*(v[1]-w['pos'])

def selected(mode):
    def keep(o):
        c=o['collection']
        if mode in ['insulation','osb','wrb','siding']:
            level={'insulation':1,'osb':2,'wrb':3,'siding':5}[mode]
            return c in ['00_Base','08a_Entramado_paredes','08d_Postes_en_muros'] or c in LAYER_CATS[:level]
        if mode=='estructura':return c=='00_Base' or c in ['08a_Entramado_paredes','08b_Estructura_techo','08d_Postes_en_muros']
        if mode=='paredes':return c in ['00_Base','08a_Entramado_paredes','08d_Postes_en_muros']
        if c.startswith('08'):
            return mode=='completo'
        if mode=='sin_techo':return not c.startswith('06') and c!='09_Entorno'
        return True
    return [o for o in OBJECTS if keep(o)]

def export_glb(path,mode='completo'):
    import numpy as np
    buf=bytearray();views=[];access=[];meshes=[];nodes=[];groups={};assemblies={}
    doc={'asset':{'version':'2.0','generator':'Angus Ranch V04'},'scene':0,'scenes':[{'nodes':[]}],
         'nodes':nodes,'meshes':meshes,'bufferViews':views,'accessors':access,'materials':[]}
    mids={}
    def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    for name,p in MATERIALS.items():
        mids[name]=len(doc['materials'])
        m={'name':name,'pbrMetallicRoughness':{'baseColorFactor':[linear(v) for v in p['color'][:3]]+[p['color'][3]],'roughnessFactor':p['roughness'],'metallicFactor':p['metallic']}}
        if p['color'][3]<1:m.update(alphaMode='BLEND',doubleSided=True)
        if name=='Luz':m['emissiveFactor']=[.7,.58,.4]
        doc['materials'].append(m)
    def arr(data):
        while len(buf)%4:buf.append(0)
        start=len(buf);buf.extend(data.tobytes());views.append({'buffer':0,'byteOffset':start,'byteLength':data.nbytes,'target':34962})
        access.append({'bufferView':len(views)-1,'componentType':5126,'count':len(data),'type':'VEC3','min':data.min(0).tolist(),'max':data.max(0).tolist()})
        return len(access)-1
    chosen=selected(mode)
    assembly_centers={}
    for o in chosen:
        ak=(o['collection'],o['assembly'])
        if ak not in assembly_centers:
            vv=np.array([v for other in chosen if (other['collection'],other['assembly'])==ak for v in other['vertices']])
            assembly_centers[ak]=(vv.min(0)+vv.max(0))/2
    for o in chosen:
        cat=o['collection'];ak=(cat,o['assembly'])
        if cat not in groups:
            groups[cat]=len(nodes);doc['scenes'][0]['nodes'].append(len(nodes));nodes.append({'name':cat,'children':[]})
        if ak not in assemblies:
            ac=assembly_centers[ak]
            assemblies[ak]=len(nodes);nodes[groups[cat]]['children'].append(len(nodes));nodes.append({'name':o['assembly'],'children':[], 'translation':[float(ac[0]),float(ac[2]),float(-ac[1])]})
        vv=np.array(o['vertices']);center=(vv.min(0)+vv.max(0))/2;pos=[];norm=[]
        for face in o['faces']:
            for j in range(1,len(face)-1):
                tri=vv[[face[0],face[j],face[j+1]]];nn=np.cross(tri[1]-tri[0],tri[2]-tri[0]);ln=np.linalg.norm(nn)
                if ln<1e-10:continue
                nn/=ln
                for v in tri-center:pos.append([v[0],v[2],-v[1]]);norm.append([nn[0],nn[2],-nn[1]])
        pa=arr(np.array(pos,dtype='<f4'));na=arr(np.array(norm,dtype='<f4'))
        meshes.append({'name':o['id'],'primitives':[{'attributes':{'POSITION':pa,'NORMAL':na},'material':mids[o['material']]}]})
        nodes[assemblies[ak]]['children'].append(len(nodes))
        relative=center-assembly_centers[ak]
        nodes.append({'name':o['id'],'mesh':len(meshes)-1,'translation':[float(relative[0]),float(relative[2]),float(-relative[1])],
                      'extras':{'nombre':o['name'],'collection':cat,'assembly':o['assembly'],**o['meta']}})
    doc['buffers']=[{'byteLength':len(buf)}];js=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();js+=b' '*((-len(js))%4);buf+=b'\0'*((-len(buf))%4)
    with open(path,'wb') as f:f.write(struct.pack('<III',0x46546c67,2,28+len(js)+len(buf))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(buf),0x004e4942)+buf)

def validate():
    import numpy as np
    assert len({o['id'] for o in OBJECTS})==len(OBJECTS)
    assert W==15 and D==8 and E==18
    assert not any('toilette' in o['id'].lower() for o in OBJECTS)
    # Each raised opening has sill, two kings, two trimmers and two header leaves.
    for op in OPENINGS:
        i=int(op['id'].rsplit('O',1)[1]);obs=[o for o in OBJECTS if o['assembly']==op['wall']]
        names=[o['name'] for o in obs]
        for k in ['King_stud_L','King_stud_R','Trimmer_L','Trimmer_R','Header_0','Header_1']:assert f'O{i}_{k}' in names,op
        if op['sill']>.05:assert f'O{i}_Rough_sill' in names,op
        # No frame piece intersects the modeled clear aperture.
        for o in obs:
            if o['collection']!='08a_Entramado_paredes':continue
            v=np.array(o['vertices']);u=v[:,0] if op['axis']=='X' else v[:,1]
            overlap=min(u.max(),op['b'])-max(u.min(),op['a'])
            z_overlap=min(v[:,2].max(),op['head'])-max(v[:,2].min(),op['sill'])
            assert not(overlap>1e-6 and z_overlap>1e-6),(op['id'],o['name'],'frame in aperture')
    for o in OBJECTS:
        a=np.array(o['vertices']);assert np.isfinite(a).all()
        assert all(max(f)<len(a) and min(f)>=0 for f in o['faces'])
    # Verify roof support levels rather than an unqualified structural claim.
    assert abs((roof_level(8)-roof_level(0))-.48)<1e-8
    assert roof_level(4)-.62>2.83
    global VALIDATION
    VALIDATION={'geometry_checks':'passed','object_count':len(OBJECTS),'opening_count':len(OPENINGS),
                'footprint_m2':E*D+(E-XADD)*S,'gallery_m2':30.,'max_main_beam_span_m':9.2,
                'blender_runtime_tested':False,'structural_analysis':False,'main_roof_rise_m':.48,
                'collections':dict(Counter(o['collection'] for o in OBJECTS))}
    return VALIDATION

def blender_scene():
    import bpy
    from mathutils import Vector
    scene=bpy.data.scenes.new('Angus Ranch V04');bpy.context.window.scene=scene
    scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='METERS';scene.unit_settings.scale_length=1
    scene['version']='V04';scene['huella_cubierta_m2']=VALIDATION['footprint_m2'];scene['galeria_m2']=30.
    scene['fuente']='Rob Thallon, Graphic Guide to Frame Construction, tercera edición revisada; referencias en cada objeto.'
    scene['limite']='Modelo conceptual, secciones y uniones no calculadas.'
    mats={}
    for name,p in MATERIALS.items():
        m=bpy.data.materials.new(name);m.diffuse_color=p['color'];m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF')
        rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in p['color'][:3]]
        bs.inputs['Base Color'].default_value=rgb+[1.];bs.inputs['Roughness'].default_value=p['roughness'];bs.inputs['Metallic'].default_value=p['metallic']
        if name=='Vidrio':
            if 'Transmission Weight' in bs.inputs:bs.inputs['Transmission Weight'].default_value=.9
            bs.inputs['IOR'].default_value=1.45;bs.inputs['Alpha'].default_value=.25
            if hasattr(m,'surface_render_method'):m.surface_render_method='DITHERED'
        if name=='Luz' and 'Emission Color' in bs.inputs:bs.inputs['Emission Color'].default_value=(1,.8,.55,1);bs.inputs['Emission Strength'].default_value=2
        if 'Madera' in name or name=='Roble natural':
            nd=m.node_tree.nodes;lk=m.node_tree.links;tc=nd.new('ShaderNodeTexCoord');ns=nd.new('ShaderNodeTexNoise');ns.inputs['Scale'].default_value=6
            mp=nd.new('ShaderNodeVectorMath');mp.operation='MULTIPLY';mp.inputs[1].default_value=(2,28,2);lk.new(tc.outputs['Generated'],mp.inputs[0]);lk.new(mp.outputs[0],ns.inputs['Vector'])
            bu=nd.new('ShaderNodeBump');bu.inputs['Strength'].default_value=.10;bu.inputs['Distance'].default_value=.015;lk.new(ns.outputs['Fac'],bu.inputs['Height']);lk.new(bu.outputs[0],bs.inputs['Normal'])
        mats[name]=m
    cols={};parents={}
    for cat in sorted({o['collection'] for o in OBJECTS}):
        c=bpy.data.collections.new(cat);c['category_id']=cat;scene.collection.children.link(c);cols[cat]=c
    for o in OBJECTS:
        cat=o['collection'];key=(cat,o['assembly'])
        if key not in parents:
            av=[v for other in OBJECTS if (other['collection'],other['assembly'])==key for v in other['vertices']]
            ac=[(min(v[i] for v in av)+max(v[i] for v in av))/2 for i in range(3)]
            em=bpy.data.objects.new(o['assembly'],None);em.location=ac;em.empty_display_type='PLAIN_AXES';em.empty_display_size=.07;cols[cat].objects.link(em);parents[key]=em
        vs=o['vertices'];center=[(min(v[i] for v in vs)+max(v[i] for v in vs))/2 for i in range(3)]
        me=bpy.data.meshes.new(o['id']);me.from_pydata([[v[i]-center[i] for i in range(3)] for v in vs],[],o['faces']);me.update()
        ob=bpy.data.objects.new(o['id'],me);cols[cat].objects.link(ob);ob.parent=parents[key];ob.location=Vector(center)-parents[key].location;ob.data.materials.append(mats[o['material']])
        ob['nombre']=o['name'];ob['id_estable']=o['id'];ob['referencia']=o['meta']['referencia'];ob['dimensionamiento']='De estudio; no calculado'
        for k,v in o['meta'].items():ob[k]=v
        if o['bevel']:
            mod=ob.modifiers.new('Bisel editable','BEVEL');mod.width=o['bevel'];mod.segments=2
            mod=ob.modifiers.new('Normales','WEIGHTED_NORMAL')
    manual=bpy.data.collections.new('90_Mis_cambios');scene.collection.children.link(manual)
    env=bpy.data.collections.new('99_Camaras_luces');scene.collection.children.link(env)
    # Compare category metadata, not actual collection names which Blender may suffix.
    modes=[('01_Interior_sin_techo','sin_techo'),('02_Exterior_completo','completo'),('03_Estructura_woodframe','estructura'),('04_Entramado_paredes','paredes')]+LAYER_MODES
    for j,(name,mode) in enumerate(modes):
        layer=scene.view_layers[0] if j==0 else scene.view_layers.new(name);layer.name=name
        visible={o['collection'] for o in selected(mode)}
        for lc in layer.layer_collection.children:
            category=lc.collection.get('category_id')
            if category:lc.exclude=category not in visible
        layer.use=(j==0)
    def camera(name,loc,target,scale):
        data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);env.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale;data.clip_end=300;return ob
    cam=camera('CAM_Interior',(25,26,24),(9,4,.8),25)
    camera('CAM_Planta',(9,4,30),(9,4,0),23)
    camera('CAM_Exterior',(25,-17,17),(9,4,1),26)
    scene.camera=cam
    sun=bpy.data.lights.new('Sol_de_estudio','SUN');sun.energy=2;sun.angle=.15;ob=bpy.data.objects.new('Sol_de_estudio',sun);env.objects.link(ob);ob.rotation_euler=(.5,-.4,2.4)
    light=bpy.data.lights.new('Relleno','AREA');light.energy=1900;light.size=12;ob=bpy.data.objects.new('Relleno',light);env.objects.link(ob);ob.location=(9,4,12)
    world=bpy.data.worlds.new('Cielo_estudio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.72,.8,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
    scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.render.resolution_x=1800;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
    bpy.context.window.view_layer=scene.view_layers[0]
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                sp=area.spaces.active;sp.region_3d.view_perspective='ORTHO';sp.region_3d.view_distance=25;sp.region_3d.view_location=(9,4,1);sp.region_3d.view_rotation=cam.rotation_euler.to_quaternion();sp.shading.type='MATERIAL';sp.clip_end=300
    tx=bpy.data.texts.new('LEEME_V04');tx.write('V04 sobre planta V03. View Layers 01–04 arquitectura/estructura; 05 Insulation, 06 OSB, 07 WRB, 08 Siding.\nCapas 05–08 acumulativas de las paredes exteriores. Camara de drenaje de 25 mm, vacia entre listones.\nPaso living abierto hasta arriba sin marco. Secciones, encuentros y sistema de apoyos pendientes de revisión.\nCada ejecución crea una escena NUEVA. Las ediciones manuales no vuelven al Python.\nGuardar como .blend desde Archivo. Ver LEEME_V04.md.\n')
    print('V04 LISTA. Guardar como .blend. No se borraron escenas anteriores.')

def build():
    OBJECTS.clear();OPENINGS.clear();ROOMS.clear();WALLS.clear();SERIAL.clear()
    build_base();build_walls();build_furniture();build_roof();build_corner_frame();build_envelope();conform_corner_plate_planes()
    for o in OBJECTS:
        if o['collection']=='08b_Estructura_techo' and o['name'].startswith('Poste'):o['collection']='08d_Postes_en_muros'
    build_exterior();validate()

if __name__=='__main__':
    build()
    try:import bpy
    except ImportError:
        out=Path(__file__).resolve().parent
        for mode,suffix in [('completo','Completo'),('sin_techo','Sin_techo'),('estructura','Woodframe')]+[(m,n) for n,m in LAYER_MODES]:export_glb(out/f'Angus_Ranch_V04_{suffix}.glb',mode)
        (out/'modelo_geometria.json').write_text(json.dumps({'objects':OBJECTS,'materials':MATERIALS,'rooms':ROOMS,'openings':OPENINGS,'config':CONFIG,'validation':VALIDATION},ensure_ascii=False))
        (out/'verificacion_geometria.json').write_text(json.dumps(VALIDATION,ensure_ascii=False,indent=2))
        print(json.dumps(VALIDATION,ensure_ascii=False,indent=2))
    else:blender_scene()

'''

FUENTE_TERRENO_V01 = r'''
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

'''


"""Extensión reproducible V06; se incorpora al script autónomo final."""
from pathlib import Path
from collections import defaultdict, Counter
import csv
import copy
import html

V06 = {
    'perno_diametro_m': .0127,
    'empotramiento_m': .18,
    'separacion_pernos_max_m': 1.20,
    'distancia_extremo_objetivo_m': .20,
    'junta_solera_m': .003,
    'largos_stock_mm': [2400, 3000, 3600, 4200, 4800, 6000],
    'sobrelargo_por_pieza_mm': 10,
    'corte_sierra_mm': 3,
    'reserva_compra': .10,
}
CAT_HEADER = '15a_V06_Headers_dos_tablas'
CAT_CORE = '15b_V06_Separadores_headers'
CAT_SILL = '16a_V06_Soleras_tratadas'
CAT_GASKET = '16b_V06_Barrera_capilar'
CAT_ANCHOR = '16c_V06_Pernos_arandelas_tuercas'
CAT_SHOE = '16d_V06_Bases_postes'
CAT_CONCRETE = '16e_V06_Hormigon'
CAT_GALLERY_POST = '16f_V06_Postes_galeria'
NEW_CATS = {CAT_HEADER,CAT_CORE,CAT_SILL,CAT_GASKET,CAT_ANCHOR,CAT_SHOE,CAT_CONCRETE,CAT_GALLERY_POST}


def bounds(o):
    return ([min(v[i] for v in o['vertices']) for i in range(3)],
            [max(v[i] for v in o['vertices']) for i in range(3)])


def material_v06(c, name, color, metal=0):
    c['MATERIALS'][name] = {'color':list(color)+[1.], 'roughness':.55, 'metallic':metal}


def ring(c, name, x,y,z,outer,inner,height, cat=CAT_ANCHOR,n=32,mat='Acero galvanizado V06'):
    vs=[]
    for zz in [z,z+height]:
        for radius in [outer,inner]:
            vs += [[x+radius*math.cos(2*math.pi*i/n),y+radius*math.sin(2*math.pi*i/n),zz] for i in range(n)]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces += [[i,j,n+j,n+i], [2*n+i,3*n+i,3*n+j,2*n+j],
                  [i,2*n+i,2*n+j,j], [n+i,n+j,3*n+j,3*n+i]]
    return c['add'](name,cat,vs,faces,mat)


def augment_v06(c):
    material_v06(c,'Madera header A V06',(.73,.43,.20))
    material_v06(c,'Madera header B V06',(.95,.68,.35))
    material_v06(c,'Contrachapado V06',(.55,.36,.20))
    material_v06(c,'Madera tratada V06',(.40,.53,.32))
    material_v06(c,'Barrera capilar V06',(.11,.16,.18))
    material_v06(c,'Acero galvanizado V06',(.38,.57,.67),.75)
    material_v06(c,'Hormigon V06',(.60,.62,.61))
    walls={w['name']:w for w in c['WALLS']}
    c['OBJECTS'][:]=[o for o in c['OBJECTS'] if 'Aislacion_nucleo_dintel' not in o['name']]
    for o in c['OBJECTS']:
        if '_Header_' in o['name']:
            o['collection']=CAT_HEADER
            o['material']='Madera header A V06' if o['name'].endswith('_0') else 'Madera header B V06'
            o['meta'].update(sistema='Doble tabla; adaptación métrica de Thallon 68C',
                             espesor_tabla_mm=45, verificacion_resistente='PENDIENTE',
                             referencia='Thallon 68C, PDF 81. NO es la alternativa LVL/LSL de 69B.')
        if o['name']=='Sole_plate':
            o['collection']=CAT_SILL;o['material']='Madera tratada V06'
            o['meta'].update(tratamiento='Preservada para contacto con hormigón; especie y clase por definir')
        if o['name'].startswith('Platea_'):
            o['collection']=CAT_CONCRETE;o['material']='Hormigon V06'
            for v in o['vertices']:
                if abs(v[2])<1e-8:v[2]=-.003
            o['meta']['alcance']='Volumen V05, cara superior rebajada 3 mm para junta. Sin armadura ni cálculo de suelo.'
    for op in c['OPENINGS']:
        w=walls[op['wall']];depth=c['STUD'] if w['external'] or w['bearing'] else .09
        gap=round(depth-.09,6)
        if gap<=0:continue
        c['component'](w['name'],'Thallon 68C; adaptación 45+50+45 mm, cuatro separadores de contrachapado 12.5 mm. Por verificar.')
        for j in range(4):
            o=c['wall_piece'](op['id'].split('/')[-1]+'_Separador_'+str(j+1),w['axis'],
                              w['pos']-gap/2+(j+.5)*gap/4,op['a']-.045,op['b']+.045,
                              op['head'],op['head']+op['header_depth'],gap/4,'Contrachapado V06',CAT_CORE)
            o['meta'].update(abertura=op['id'],espesor_mm=12.5,
                            nota='Relleno continuo de estudio, no homologación estructural; sustituye núcleo aislado V05.')
        op['reference']='Thallon 68C (PDF 81), adaptación métrica 45+50+45 mm'
    # Anchors are located on real sill segments, outside jambs/studs/posts and door voids.
    anchors=[]; unresolved=[]
    for sill in [o for o in c['OBJECTS'] if o['collection']==CAT_SILL]:
        w=walls[sill['assembly']];ax=0 if w['axis']=='X' else 1;cross=1-ax
        lo,hi=bounds(sill);a,b=lo[ax],hi[ax];p=w['pos']
        c['component'](sill['assembly'],'Thallon 12A (PDF 25); geometría preliminar de anclajes, NO especificación de obra.')
        gasket=c['wall_piece']('Junta_bajo_'+sill['id'],w['axis'],p,a,b,-.003,0,hi[cross]-lo[cross],
                               'Barrera capilar V06',CAT_GASKET)
        gasket['meta']['solera_id']=sill['id']
        blocked=[]
        for o in c['OBJECTS']:
            if o['collection'] not in {'08a_Entramado_paredes','08d_Postes_en_muros'}:continue
            ol,oh=bounds(o)
            if ol[2]>.065 or oh[2]<.06:continue
            if min(oh[cross],p+.031)-max(ol[cross],p-.031)>1e-6:
                blocked.append((ol[ax]-.036,oh[ax]+.036))
        candidates=[round(a+.09+j*.005,6) for j in range(max(0,int((b-a-.18)/.005)+1))]
        candidates=[u for u in candidates if not any(l<u<h for l,h in blocked)]
        selected=[]
        if candidates:
            left=[u for u in candidates if u<=a+.30]
            right=[u for u in candidates if u>=b-.30]
            if left and right:
                first=min(left,key=lambda u:abs(u-(a+.20)))
                last=min(right,key=lambda u:abs(u-(b-.20)))
                if last<first:first,last=left[0],right[-1]
                selected=[first]
                while last-selected[-1]>1.20+1e-6:
                    opts=[u for u in candidates if selected[-1]+.10<u<=selected[-1]+1.20]
                    if not opts:break
                    selected.append(max(opts))
                if last-selected[-1]>.06:selected.append(last)
        valid=len(selected)>=2 and selected[0]-a<=.30 and b-selected[-1]<=.30 and max(y-x for x,y in zip(selected,selected[1:]))<=1.200001
        if not valid:
            unresolved.append({'solera':sill['id'],'largo_m':b-a,'motivo':'No caben dos pernos con las separaciones gráficas; conexión especial pendiente'})
        for u in selected:
            x,y=(u,p) if ax==0 else (p,u)
            aid='A%03d'%(len(anchors)+1)
            c['component'](aid,'Thallon 12A; diámetro 12.7 mm, empotramiento 180 mm, paso objetivo <=1200 mm: hipótesis geométrica.')
            rod=c['cylinder']('Perno_vertical',(x,y,-.183),(x,y,.071),.00635,'Acero galvanizado V06',CAT_ANCHOR,16)
            # L-shaped cast-in tail remains inside concrete and parallel to wall.
            tx,ty=(x+.065,y) if ax==0 else (x,y+.065)
            c['cylinder']('Pata_L',(x,y,-.183),(tx,ty,-.183),.00635,'Acero galvanizado V06',CAT_ANCHOR,16)
            ring(c,'Arandela_perforada',x,y,.045,.030,.0075,.004)
            ring(c,'Tuerca_hexagonal',x,y,.049,.012,.007,.011,n=6)
            rod['meta'].update(solera_id=sill['id'],anclaje_id=aid,diametro_mm=12.7,empotramiento_mm=180,
                               rosca='Representación lisa; rosca nominal pendiente de producto')
            anchors.append({'id':aid,'solera':sill['id'],'pared':w['name'],'x':x,'y':y,'u':u,'a':a,'b':b})
    # Post bases are separate from sill anchors. No assumed capacities or product model.
    posts=[o for o in c['OBJECTS'] if o['name'].startswith('Poste') and o['collection'] in {'08b_Estructura_techo','08d_Postes_en_muros'}]
    for pi,post in enumerate(posts):
        if post['assembly']=='Galeria_estructura':post['collection']=CAT_GALLERY_POST
        lo,hi=bounds(post);x,y=(lo[0]+hi[0])/2,(lo[1]+hi[1])/2;sx,sy=hi[0]-lo[0],hi[1]-lo[1]
        for v in post['vertices']:
            if abs(v[2]-lo[2])<1e-7:v[2]=.05
        c['component']('BP%02d'%(pi+1),'Base U ilustrativa: elevación 50 mm. Producto, tornillos y anclaje por dimensionar.')
        c['box']('Dado_galeria' if post['assembly']=='Galeria_estructura' else 'Refuerzo_local_poste',
                 (x,y,-.30),(.45,.45,.594),'Hormigon V06',CAT_CONCRETE,0)
        c['box']('Placa_base',(x,y,.019),(sx+.09,sy+.09,.010),'Acero galvanizado V06',CAT_SHOE,.001)
        c['box']('Asiento_poste',(x,y,.045),(sx,sy,.010),'Acero galvanizado V06',CAT_SHOE,.001)
        for sg in [-1,1]:
            yy=y+sg*(sy/2+.003)
            c['box']('Ala_U',(x,yy,.135),(sx,.006,.222),'Acero galvanizado V06',CAT_SHOE,.001)
            for zz in [.105,.185]:
                c['cylinder']('Tornillo_ilustrativo',(x,yy+sg*.009,zz),(x,yy-sg*.05,zz),.004,'Acero galvanizado V06',CAT_SHOE,12)
        for sg in [-1,1]:
            xx=x+sg*(sx/2+.023)
            c['cylinder']('Anclaje_base',(xx,y,-.183),(xx,y,.04),.00635,'Acero galvanizado V06',CAT_SHOE,16)
            ring(c,'Tuerca_base',xx,y,.027,.012,.007,.010,CAT_SHOE,6)
            ring(c,'Arandela_base',xx,y,.024,.019,.0075,.003,CAT_SHOE)
        post['meta']['base_v06']='BP%02d; cortar poste por abajo a cota local 0.05 m, conservar apoyo superior'%(pi+1)
    return anchors,unresolved


def timber_inventory(c):
    """Grain-aware rectangular blank dimensions; never use roof world AABB as section."""
    import numpy as np
    rows=[]
    for o in c['OBJECTS']:
        cat=o['collection'];name=o['name']
        if cat not in {'08a_Entramado_paredes','08b_Estructura_techo','08d_Postes_en_muros',
                       '13_08_Camara_listones',CAT_HEADER,CAT_SILL,CAT_CORE,CAT_GALLERY_POST} and not (o['assembly']=='Galeria_deck' and name=='Tabla'):continue
        v=np.array(o['vertices'],float);lo,hi=bounds(o)
        if cat==CAT_CORE:section='Separadores contrachapado';kind='tablero'
        elif cat==CAT_HEADER:section='Headers';kind='madera'
        elif cat==CAT_SILL:section='Soleras tratadas';kind='madera tratada'
        elif cat=='13_08_Camara_listones':section='Listones fachada';kind='madera'
        elif o['assembly']=='Galeria_deck':section='Tablas deck';kind='madera exterior'
        elif name.startswith('Viga'):section='Vigas';kind='madera ingenieria por definir'
        elif name.startswith('Poste'):section='Postes';kind='madera'
        elif name.startswith('Cabio'):section='Cabios';kind='madera'
        elif 'Top_plate' in name:section='Soleras superiores';kind='madera'
        elif 'Blocking' in name or 'Respaldo' in name or 'Backer' in name:section='Bloqueos y esquinas';kind='madera'
        else:section='Montantes y antepechos';kind='madera'
        # Vertical pieces need the longest point of a sloping top cut.
        vertical=any(k in name for k in ['stud','Trimmer','Cripple','Poste','Backer','Respaldo','Liston'])
        if vertical:
            grain=np.array([0.,0.,1.]);across=np.array([1.,0.,0.]);other=np.array([0.,1.,0.])
        else:
            # Box/prism/wall_piece all use 0-1 and 0-3 as longitudinal candidates.
            e1=v[1]-v[0];e2=v[3]-v[0]
            wall_part=o['assembly'] in {w['name'] for w in c['WALLS']}
            e=e1 if wall_part or np.linalg.norm(e1)>=np.linalg.norm(e2) else e2
            grain=e/np.linalg.norm(e)
            across=np.array([-grain[1],grain[0],0.]);across/=np.linalg.norm(across)
            other=np.cross(grain,across)
        spans=[float(np.ptp(v@axis)) for axis in [grain,across,other]]
        thickness,width=sorted(spans[1:])
        # Purchase blank rounds UP to 1 mm; plywood preserves 12.5 mm thickness.
        t=round(thickness*1000,3) if cat==CAT_CORE else math.ceil(thickness*1000-1e-6)
        b=math.ceil(width*1000-1e-6);length=math.ceil(spans[0]*1000-1e-6)
        pending='REVISAR dimensionamiento'
        if length>max(V06['largos_stock_mm']):pending='ESPECIAL: largo continuo >6 m; resolver suministro/empalmes'
        if section=='Vigas':pending='INGENIERIA: seccion y continuidad pendientes'
        row={'id':o['id'],'seccion':section,'sector':o['assembly'],'pieza':name,'material':kind,
             'espesor_mm':t,'ancho_mm':b,'largo_corte_mm':length,'cantidad':1,
             'volumen_bruto_m3':round(t*b*length/1e9,8),'estado':pending}
        o['meta'].update(computo_id=row['id'],seccion_computo=section,espesor_compra_mm=t,ancho_compra_mm=b,
                         largo_corte_mm=length,computable=True,grano_direccion=[float(x) for x in grain],
                         dimensiones_nota='Envolvente rectangular según fibra. Largo al punto máximo, antes del margen de corte.')
        rows.append(row)
    assert len(rows)==len({r['id'] for r in rows})
    return rows


def schedule(rows):
    groups=defaultdict(list)
    for r in rows:groups[(r['seccion'],r['sector'],r['espesor_mm'],r['ancho_mm'],r['largo_corte_mm'])].append(r)
    grouped=[]
    for i,(key,rr) in enumerate(sorted(groups.items()),1):
        sec,zone,t,w,l=key
        grouped.append({'grupo':'G%03d'%i,'seccion':sec,'sector':zone,'espesor_mm':t,'ancho_mm':w,
                        'largo_corte_mm':l,'cantidad':len(rr),'metros_lineales':round(l*len(rr)/1000,3),
                        'volumen_bruto_m3':round(sum(r['volumen_bruto_m3'] for r in rr),6),
                        'estado':rr[0]['estado'],'ids':' | '.join(r['id'] for r in rr)})
    stockgroups=defaultdict(list);special=[]
    for r in rows:
        if r['seccion']=='Separadores contrachapado' or r['seccion']=='Vigas' or r['largo_corte_mm']+13>6000:
            special.append(r);continue
        stockgroups[(r['seccion'],r['espesor_mm'],r['ancho_mm'],r['material'])].append(r)
    bins=[]
    for key,rr in sorted(stockgroups.items()):
        local=[]
        for r in sorted(rr,key=lambda r:-r['largo_corte_mm']):
            need=r['largo_corte_mm']+V06['sobrelargo_por_pieza_mm']+V06['corte_sierra_mm']
            available=[b for b in local if b['usado_mm']+need<=6000]
            bn=min(available,key=lambda b:6000-b['usado_mm']-need) if available else None
            if bn is None:bn={'usado_mm':0,'piezas':[]};local.append(bn)
            bn['usado_mm']+=need;bn['piezas'].append(r)
        for bn in local:
            stock=next(l for l in V06['largos_stock_mm'] if l>=bn['usado_mm'])
            bins.append({'tabla':'T%04d'%(len(bins)+1),'seccion':key[0],'espesor_mm':key[1],'ancho_mm':key[2],
                         'material':key[3],'largo_stock_mm':stock,'usado_mm':bn['usado_mm'],'sobrante_mm':stock-bn['usado_mm'],
                         'cortes':' + '.join(str(r['largo_corte_mm']) for r in bn['piezas']),
                         'ids':' | '.join(r['id'] for r in bn['piezas'])})
    purchase=[]
    counts=Counter((b['seccion'],b['espesor_mm'],b['ancho_mm'],b['material'],b['largo_stock_mm']) for b in bins)
    for key,n in sorted(counts.items()):
        s,t,w,m,l=key;reserve=math.ceil(n*V06['reserva_compra'])
        purchase.append({'seccion':s,'espesor_mm':t,'ancho_mm':w,'material':m,'largo_stock_mm':l,
                         'tablas_base':n,'reserva_10pct_redondeada':reserve,'tablas_cotizar':n+reserve,
                         'nota':'Largos supuestos; confirmar aserradero, especie, grado, humedad y tratamiento'})
    assigned=[pid for b in bins for pid in b['ids'].split(' | ')]+[r['id'] for r in special]
    assert Counter(assigned)==Counter(r['id'] for r in rows)
    return grouped,bins,purchase,special


def write_outputs(out,c,rows,anchors,unresolved,report):
    out.mkdir(exist_ok=True,parents=True)
    grouped,bins,purchase,special=schedule(rows)
    def export(name,data):
        if not data:return
        with (out/name).open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]),delimiter=';');writer.writeheader();writer.writerows(data)
    export('01_piezas_individuales.csv',rows);export('02_despiece_por_sector.csv',grouped)
    export('03_cotizacion_tablas_stock.csv',purchase);export('04_plan_cortes.csv',bins)
    export('05_piezas_especiales_y_tableros.csv',special);export('06_anclajes_solera.csv',anchors)
    report.update(version_integrada='V06',piezas_casa=len(c['OBJECTS']),piezas_computadas=len(rows),grupos_despiece=len(grouped),
                  pernos_solera=len(anchors),soleras_anclaje_especial=unresolved,
                  headers_dobles=len(c['OPENINGS']),tablas_stock_sin_reserva=len(bins),
                  tablas_stock_con_reserva=sum(r['tablas_cotizar'] for r in purchase),
                  piezas_fuera_stock=len(special),volumen_bruto_total_m3=round(sum(r['volumen_bruto_m3'] for r in rows),4),
                  calculo_estructural=False,blender_ejecutado=False,hipotesis=V06)
    (out/'verificacion_V06.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'datos_computo.json').write_text(json.dumps({'piezas':rows,'agrupado':grouped,'compra':purchase,'especiales':special,'informe':report},ensure_ascii=False),encoding='utf-8')
    def table(data,cols):
        return '<table><thead><tr>'+''.join('<th>'+html.escape(k.replace('_',' '))+'</th>' for k in cols)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in cols)+'</tr>' for r in data)+'</tbody></table>'
    totals=[]
    for s in sorted({r['seccion'] for r in rows}):
        rr=[r for r in rows if r['seccion']==s]
        totals.append({'seccion':s,'piezas':len(rr),'m3_brutos':round(sum(r['volumen_bruto_m3'] for r in rr),3)})
    page='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Angus Ranch · V06 · Cómputo</title>
<style>body{font:15px/1.5 system-ui;background:#f5f1e8;color:#263b35;max-width:1250px;margin:40px auto;padding:24px}h1{font-size:42px;line-height:1.1}h2{margin-top:44px}p{max-width:950px}table{border-collapse:collapse;width:100%;background:white;margin:20px 0;font-size:13px}th,td{padding:10px;text-align:left;border-bottom:1px solid #deded3}th{background:#23483b;color:white;position:sticky;top:0}.note{background:#e9dcc4;padding:20px;border-left:5px solid #a87432}.metrics{display:flex;gap:18px;flex-wrap:wrap}.metric{background:#fff;padding:20px;min-width:175px}.metric strong{font-size:32px;display:block}a{color:#205a4b}input{padding:12px;width:90%;margin:16px 0}@media print{th{position:static}body{margin:0}input{display:none}}</style>
<p>ANGUS RANCH / CASA + TERRENO / V06</p><h1>Madera, pieza por pieza.</h1><p>Despiece vinculado a los IDs del modelo Blender. Dimensiones en milímetros reales; no equivalen automáticamente a medidas nominales en pulgadas.</p>'''
    page+='<div class="metrics">'+''.join('<div class="metric"><strong>'+str(v)+'</strong>'+k+'</div>' for k,v in [('piezas modeladas',len(rows)),('headers dobles',len(c['OPENINGS'])),('pernos de solera',len(anchors)),('m³ brutos modelados',report['volumen_bruto_total_m3'])])+'</div>'
    page+='''<p class="note"><b>Base para cotización preliminar.</b> Las secciones existentes no están calculadas. No comprar como lista ejecutiva. Los largos de stock 2.4 / 3 / 3.6 / 4.2 / 4.8 / 6 m son hipótesis, con 10 mm de sobrelargo por pieza y 3 mm de sierra. Se reutilizan recortes dentro de la misma sección/uso mediante empaquetado heurístico; no se promete optimización global. Reserva adicional 10%, redondeada hacia arriba por renglón de compra.</p>
<p>Las piezas de más de 6 m, todas las vigas y los separadores de contrachapado se cotizan aparte. No se cortan vigas ni soleras largas en la geometría para simular empalmes todavía no resueltos. El cómputo incluye entramado, cabios, vigas, postes, listones y tablas del deck; excluye muebles, OSB de muros, tableros del techo y siding. El bastidor macizo del deck en V05 es una envolvente, no un despiece: sus viguetas y apoyos intermedios siguen pendientes. También faltan bloqueos/conectores del techo que no estaban modelados.</p>'''
    page+='<h2>Resumen por uso</h2>'+table(totals,['seccion','piezas','m3_brutos'])
    page+='<h2>Tablas de stock: presupuesto parcial</h2><p>Incluye reserva. Especie, grado resistente, secado y preservación a confirmar. No incluye las piezas especiales de abajo.</p>'+table(purchase,list(purchase[0]))
    page+='<h2>Despiece del modelo por sector</h2><input id="q" placeholder="Filtrar: Norte, Cabios, Headers, 140…" oninput="document.querySelectorAll(\'#despiece tbody tr\').forEach(r=>r.hidden=!r.innerText.toLowerCase().includes(this.value.toLowerCase()))"><div id="despiece">'+table(grouped,[k for k in grouped[0] if k!='ids'])+'</div>'
    page+='<h2>Piezas especiales / tableros</h2>'+table(special,['id','seccion','espesor_mm','ancho_mm','largo_corte_mm','estado'])
    page+='<h2>Anclajes y alcance</h2><p>Pernos de solera de estudio: diámetro 12.7 mm, penetración 180 mm, paso máximo buscado 1.20 m y extremos a no más de 300 mm. Arandelas perforadas y tuercas independientes. Estas medidas interpretan Thallon 12A, no una verificación normativa argentina. '+str(len(unresolved))+' soleras requieren una conexión especial por falta de espacio. Catorce bases de postes ilustrativas; seis dados de galería sin cálculo de suelo ni armaduras. El hold-down mostrado en la capa 13 es un detalle didáctico: no define ubicación ni cantidad para la vivienda.</p>'
    if unresolved:page+=table(unresolved,['solera','largo_m','motivo'])
    page+='''<p>El header exterior representa 45 + 4 × 12.5 + 45 = 140 mm; el interior, dos tablas de 45 mm sin separador. La solución de 68C se adapta a las medidas existentes; la composición de 50 mm de contrachapado requiere revisión estructural y térmica. No se afirma equivalencia con doble LVL ni con LSL. Alturas heredadas 220/300 mm y vanos de 4 m requieren cálculo, al igual que la viga central de 9.20 m.</p>
<h2>Fuentes</h2><p>Modelo: angus_ranch_V05_casa_y_terreno.py. Libro local Woodframe fundamentals.pdf: Rob Thallon, <i>Graphic Guide to Frame Construction</i>, detalles 68A/C (PDF 81), 69B (PDF 82), 12A (PDF 25), 83A y 85A/B (PDF 96 y 98). Contexto consultado: “Modelar casa en Blender” y “Modelar terreno 3D”, proyecto Angus Ranch Cba. <a href="https://www.strongtie.com/products/connectors/wood-construction-connectors/technical-notes/general-notes-for-holdowns-and-tensionties">Notas de fabricante para hold-downs</a>: la selección y montaje deben responder al producto y a las cargas.</p></html>'''
    (out/'Computo_madera_V06.html').write_text(page,encoding='utf-8')
    return grouped


def setup_blender_v06(c,rows,grouped,report,out):
    import bpy
    from mathutils import Vector, Matrix
    scene=bpy.context.scene
    scene.name='Angus_Ranch_V06_Casa_y_Terreno'
    scene['version']='V06';scene['estado']='Estudio constructivo y cómputo preliminar; no calculado'
    scene['computo_json']=json.dumps(report,ensure_ascii=False)
    root=next(o for o in scene.objects if o.name.startswith('CASA_MOVER_TODO'))
    byid={o.get('id_estable'):o for o in scene.objects if o.get('id_estable')}
    cols={co.get('category_id'):co for co in scene.collection.children if co.get('category_id')}
    env=next(co for co in scene.collection.children if co.name.startswith('99_Camaras_luces'))
    def newcol(name,parent=None):
        co=bpy.data.collections.new(name);(parent or scene.collection).children.link(co);return co
    despiece=newcol('17_V06_DESPIECE_NO_SUMAR_COPIAS')
    detheader=newcol('18_V06_DETALLE_HEADER_NO_COMPUTAR')
    detanchor=newcol('19_V06_DETALLE_ANCLAJES_NO_COMPUTAR')
    def label(co,name,body,loc,size=.18):
        tx=bpy.data.curves.new(name,'FONT');tx.body=body;tx.size=size;tx.extrude=0
        ob=bpy.data.objects.new(name,tx);co.objects.link(ob);ob.location=loc
        ob['computable']=False;ob['solo_demostracion']=True
        mat=bpy.data.materials.get('Rotulos V06')
        if not mat:
            mat=bpy.data.materials.new('Rotulos V06');mat.diffuse_color=(.06,.13,.11,1)
        tx.materials.append(mat);return ob
    def mesh(co,name,vs,faces,matname):
        me=bpy.data.meshes.new(name);me.from_pydata(vs,[],faces);me.update()
        ob=bpy.data.objects.new(name,me);co.objects.link(ob)
        mat=next((m for m in bpy.data.materials if m.name==matname),None)
        if mat:me.materials.append(mat)
        ob['computable']=False;ob['solo_demostracion']=True
        return ob
    def block(co,name,loc,size,mat):
        x,y,z=loc;dx,dy,dz=[s/2 for s in size]
        vs=[[x+a*dx,y+b*dy,z+d*dz] for a,b,d in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        return mesh(co,name,vs,c['FACES'],mat)
    def camera(name,loc,target,scale,house=False):
        data=bpy.data.cameras.new(name);data.type='ORTHO';data.ortho_scale=scale;data.clip_end=5000
        ob=bpy.data.objects.new(name,data);env.objects.link(ob)
        if house:
            ob.parent=root
            pivot=Vector((*IMPLANTACION['pivote_local_xy_m'],0))
            ob.location=Vector(loc)-pivot;target=Vector(target)-pivot
        else:ob.location=loc;target=Vector(target)
        ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
        return ob
    cameras={}
    cameras['09_Headers_dobles']=camera('CAM_V06_09_Headers',(23,24,20),(9,3,1.7),24,True)
    cameras['10_Anclajes_y_cimientos']=camera('CAM_V06_10_Cimientos',(23,24,19),(9,3.8,1.4),27,True)
    # Display one physical copy for every inventory ID, sorted by usage, sector and dimensions.
    # Display geometry is the rectangular cut blank, not an extra part of the building.
    categories={};group_lookup={}
    for i,g in enumerate(grouped):
        sec=g['seccion']
        if sec not in categories:categories[sec]=newcol(sec,despiece)
        title=f"{g['grupo']} {g['sector']} | {g['espesor_mm']} x {g['ancho_mm']} x {g['largo_corte_mm']} mm | {g['cantidad']} piezas"
        gc=newcol(title,categories[sec]);gc['cantidad_real']=g['cantidad'];gc['solo_demostracion']=True
        x=45+(i%8)*21;y=(i//8)*2.8
        label(gc,g['grupo'],f"{g['grupo']}  {sec} / {g['sector']}\n{g['espesor_mm']:g} x {g['ancho_mm']} x {g['largo_corte_mm']} mm  |  x{g['cantidad']}",(x,y-.55,0),.18)
        t=g['espesor_mm']/1000;w=g['ancho_mm']/1000;l=g['largo_corte_mm']/1000
        for j,pid in enumerate(g['ids'].split(' | ')):
            source=byid[pid]
            ob=block(gc,'DESPIECE__'+pid,(x+l/2,y+(j%5)*(w+.04),t/2+(j//5)*(t+.025)),(l,w,t),source.data.materials[0].name)
            ob['pieza_origen']=pid;ob['grupo']=g['grupo'];ob['cantidad']=1
        group_lookup[g['grupo']]=gc
    depth=(math.ceil(len(grouped)/8))*2.8
    label(despiece,'Titulo_despiece','V06 / DESPIECE DE MADERA\nCopias de presentacion: NO sumar al edificio. Seleccionar grupo y Numpad . para acercar.',(45,-3,0),.5)
    cameras['11_Despiece_madera']=camera('CAM_V06_11_Despiece',(128,depth/2,200),(128,depth/2,0),max(175,depth*1.4))
    # Header example: actual north window, exploded across depth for readability.
    src=[o for o in c['OBJECTS'] if o['assembly']=='Norte' and o['name'].startswith('O0_') and o['collection'] in {'08a_Entramado_paredes',CAT_HEADER,CAT_CORE}]
    for o in src:
        vs=copy.deepcopy(o['vertices']);delta=0
        if o['collection']==CAT_HEADER:delta=-.40 if o['name'].endswith('_0') else .40
        if o['collection']==CAT_CORE:delta=(int(o['name'].rsplit('_',1)[1])-2.5)*.085
        vs=[[v[0]+45,v[1]-7.9-12+delta,v[2]] for v in vs]
        ob=mesh(detheader,'DET_HEADER__'+o['id'],vs,o['faces'],o['material']);ob['pieza_origen']=o['id']
    for o in c['OBJECTS']:
        if o['assembly']=='Norte' and o['name'] in {'Top_plate_1','Top_plate_2'}:
            lo,hi=bounds(o)
            vs=[[45+(.61 if abs(v[0]-lo[0])<1e-6 else 3.19),v[1]-7.9-12,v[2]] for v in o['vertices']]
            mesh(detheader,'DET_'+o['name'],vs,o['faces'],o['material'])
    label(detheader,'Titulo_header','HEADER DOBLE / NORTE O0\nVista explotada; separaciones aumentadas solo aqui',(45,-14.0,0),.20)
    label(detheader,'Medidas_header','2 tablas: 45 x 220 x 2490 mm\nNucleo: 4 laminas de contrachapado de 12.5 mm\n45 + 50 + 45 = 140 mm / composicion por verificar',(45,-14.9,0),.16)
    cameras['12_Detalle_header_explotado']=camera('CAM_V06_12_Header',(50,-18,6),(46.7,-12.7,1.35),8.2)
    # Actual sill anchor rendered as a cutaway. Copy -> not part of takeoff.
    sample=next(a for a in report['_anchors'] if a['pared']=='Sur_principal')
    xx,yy=sample['x'],sample['y'];origin=(54,-12,0)
    for o in c['OBJECTS']:
        if o['assembly']==sample['id']:
            mesh(detanchor,'DET_ANCLAJE__'+o['id'],[[v[0]-xx+origin[0],v[1]-yy+origin[1],v[2]] for v in o['vertices']],o['faces'],o['material'])
    # Half solids expose the embedment and the bore line instead of a transparent mesh.
    block(detanchor,'Hormigon_cortado',(54,-11.87,-.1815),(.90,.26,.357),'Hormigon V06')
    block(detanchor,'Solera_PT_cortada',(54,-11.965,.0225),(.85,.07,.045),'Madera tratada V06')
    block(detanchor,'Junta_3mm',(54,-11.965,-.0015),(.85,.07,.003),'Barrera capilar V06')
    block(detanchor,'Stud',(54.30,-12,.4475),(.045,.14,.805),'Madera estructura')
    label(detanchor,'Leyenda_perno','ANCLAJE DE SOLERA / CORTE\nPerno 12.7 mm; empotramiento 180 mm\nArandela + tuerca + solera tratada + junta 3 mm\nMedidas de estudio, no especificacion de obra',(53.4,-12.8,-.36),.085)
    # Separate demonstrative hold-down: two studs, plate, fasteners and dedicated anchor.
    hx,hy=55.7,-12
    block(detanchor,'HD_Hormigon_seccion',(hx,hy+.13,-.1815),(.85,.26,.357),'Hormigon V06')
    block(detanchor,'HD_Solera_PT',(hx,hy,.0225),(.80,.14,.045),'Madera tratada V06')
    block(detanchor,'HD_Junta',(hx,hy,-.0015),(.80,.14,.003),'Barrera capilar V06')
    for sg in [-1,1]:block(detanchor,'HD_Montante_doble',(hx+sg*.0225,hy,.50),(.045,.14,.91),'Madera estructura')
    block(detanchor,'HD_Placa_vertical',(hx,hy-.074,.27),(.095,.008,.36),'Acero galvanizado V06')
    block(detanchor,'HD_Asiento',(hx,hy-.126,.102),(.11,.11,.014),'Acero galvanizado V06')
    # Reuse mesh primitives in a scratch object list; never add sample hardware to inventory.
    start=len(c['OBJECTS']);c['component']('DET_HD','Thallon 83/85. Ejemplo didáctico; NO distribución de hold-downs de la casa.')
    c['cylinder']('Varilla_M16',(hx,hy-.145,-.20),(hx,hy-.145,.14),.008,'Acero galvanizado V06',CAT_ANCHOR,20)
    c['cylinder']('Cabeza_embebida',(hx,hy-.145,-.208),(hx,hy-.145,-.198),.017,'Acero galvanizado V06',CAT_ANCHOR,16)
    ring(c,'Tuerca_HD',hx,hy-.145,.116,.015,.0085,.014,n=6)
    ring(c,'Arandela_HD',hx,hy-.145,.109,.025,.009,.007)
    for xoff in [-.023,.023]:
        for z in [.17,.25,.33,.41]:
            c['cylinder']('Tornillo_HD',(hx+xoff,hy-.090,z),(hx+xoff,hy-.025,z),.003,'Acero galvanizado V06',CAT_ANCHOR,12)
    for o in c['OBJECTS'][start:]:mesh(detanchor,o['id'],o['vertices'],o['faces'],o['material'])
    del c['OBJECTS'][start:]
    label(detanchor,'Leyenda_HD','HOLD-DOWN / EJEMPLO\nMontante doble + conector + anclaje dedicado\nNo define ubicacion, cantidad ni capacidad\nTornillos y varilla: representacion ilustrativa',(55.15,-12.8,-.36),.085)
    cameras['13_Detalle_anclajes']=camera('CAM_V06_13_Anclajes',(57.6,-16.2,3.3),(54.9,-12,.05),3.9)
    # Each view layer has a dedicated camera marker. Blender cameras are scene-wide;
    # render launcher below switches both together, as documented in LEEME.
    old_layers=list(scene.view_layers)
    for layer in old_layers:
        for lc in layer.layer_collection.children:
            cat=lc.collection.get('category_id')
            if lc.collection in {despiece,detheader,detanchor}:lc.exclude=True
            elif cat in NEW_CATS:
                lc.exclude=layer.name=='01_Interior_sin_techo' and cat not in {CAT_CONCRETE,CAT_SILL}
    rules={
        '09_Headers_dobles':{'08a_Entramado_paredes',CAT_HEADER,CAT_CORE,CAT_SILL},
        '10_Anclajes_y_cimientos':{'08a_Entramado_paredes','08d_Postes_en_muros',CAT_HEADER,CAT_CORE,CAT_SILL,CAT_GASKET,CAT_ANCHOR,CAT_SHOE,CAT_CONCRETE,CAT_GALLERY_POST},
        '11_Despiece_madera':set(), '12_Detalle_header_explotado':set(), '13_Detalle_anclajes':set()}
    for name,visible in rules.items():
        layer=scene.view_layers.new(name)
        for lc in layer.layer_collection.children:
            co=lc.collection;cat=co.get('category_id')
            lc.exclude=not(cat in visible or co==env or co.name.startswith('00_CONTROL') or
                           (name=='11_Despiece_madera' and co==despiece) or
                           (name=='12_Detalle_header_explotado' and co==detheader) or
                           (name=='13_Detalle_anclajes' and co==detanchor))
        layer['camara_recomendada']=cameras[name].name
    # Tres capas de inspección, sin nuevas cámaras ni renders automáticos.
    bases={'00_Base',CAT_CONCRETE}
    estructura={'08a_Entramado_paredes','08d_Postes_en_muros',CAT_HEADER,CAT_CORE,CAT_SILL}
    for name,visible in [
            ('14_Instalacion_electrica',bases|estructura|{INSTALACIONES['electrico']}),
            ('15_Desagues_y_cimientos',bases|{CAT_ANCHOR,CAT_SHOE,INSTALACIONES['desagues']}),
            ('16_Agua_fria_y_caliente',bases|estructura|{INSTALACIONES['agua']})]:
        layer=scene.view_layers.new(name)
        for lc in layer.layer_collection.children:
            co=lc.collection
            lc.exclude=not(co.get('category_id') in visible or co==env or co.name.startswith('00_CONTROL'))
        layer['camara_recomendada']=cameras['09_Headers_dobles'].name
        layer.use=False
    # Camera switching via timeline markers, without auto-run handlers/add-ons.
    frame_map=[(1,'09_Headers_dobles'),(10,'10_Anclajes_y_cimientos'),(20,'11_Despiece_madera'),
               (30,'12_Detalle_header_explotado'),(40,'13_Detalle_anclajes')]
    for frame,name in frame_map:
        marker=scene.timeline_markers.new(name,frame=frame);marker.camera=cameras[name]
    scene.frame_end=40;scene.frame_set(1);scene.camera=cameras['09_Headers_dobles']
    for layer in scene.view_layers:layer.use=layer.name=='09_Headers_dobles'
    bpy.context.window.view_layer=scene.view_layers['09_Headers_dobles']
    # Good modelling view independent from render cameras.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                sp=area.spaces.active;sp.shading.type='SOLID';sp.shading.color_type='MATERIAL'
                sp.region_3d.view_distance=26;sp.region_3d.view_location=root.matrix_world@Vector((0,0,1))
                sp.region_3d.view_rotation=cameras['09_Headers_dobles'].matrix_world.to_quaternion()
    for o in scene.objects:
        if o.type=='MESH' and o.get('computo_id'):o['computable']=True
    readme=bpy.data.texts.new('LEEME_V06');readme.write((out/'LEEME_V06.md').read_text(encoding='utf-8'))
    scene['camara_por_layer']=json.dumps({n:ca.name for n,ca in cameras.items()})
    report.pop('_anchors',None)
    report['blender_ejecutado']=True
    report['objetos_escena']=len(scene.objects)
    report['view_layers']=[v.name for v in scene.view_layers]
    assert len([o for o in despiece.all_objects if o.get('pieza_origen')])==len(rows)
    assert len([o for o in scene.objects if o.get('computable')])==len(rows)
    report['copias_despiece_verificadas']=len(rows)
    (out/'verificacion_V06.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return cameras


# Instalaciones en coordenadas LOCALES de la casa, en metros.
# Son hipótesis de anteproyecto, no un dimensionamiento para ejecutar obra.
INSTALACIONES = {
    'electrico': '20_Instalacion_electrica', 'desagues': '21_Desagues_sanitarios', 'agua': '22_Agua_fria_caliente',
    'altura_distribucion_electrica_m': 2.86,  # entre cielorraso y vigas
    'altura_distribucion_agua_m': 2.94,
    'pendiente_desague': .02,
    'y_colector_cloacal_m': -3.3,
    'cota_eje_inicio_colectores_m': -.56,
    'tablero_xyz_m': (17.70, 2.95, 1.50),
    'nota': 'Revisar cargas, selectividad, caída de tensión, presión, ventilación '
            'y refuerzos de reservas con los profesionales de cada especialidad.',
    'referencias': [
        'https://www.argentina.gob.ar/sites/default/files/02_guia_prevencion_riesgo_electrico_ok_.pdf',
        'https://www.argentina.gob.ar/sites/default/files/2018/03/reglamento_conexion_nuevos_suministros_domiciliarios.pdf',
    ],
}


def agregar_instalaciones(casa):
    """Agrega redes conectadas y recorta las reservas en la propia malla base.

    No usa bpy: también se construye y verifica todo con --check.
    Tres colecciones nuevas; ninguna cámara, plano ni exportación adicional.
    Recorridos interiores superficiales/sobre cielorraso: no se taladra madera.
    DN y secciones son nominales orientativos, sujetos al cálculo del proyecto.
    """
    cfg = INSTALACIONES
    electrico, desagues, agua = (cfg[k] for k in ('electrico', 'desagues', 'agua'))
    box, cylinder = casa['box'], casa['cylinder']
    objects = casa['OBJECTS']
    for name, rgb in {
        'INST_Canalizacion': (.42, .44, .48), 'INST_Fase': (.46, .22, .08),
        'INST_Neutro': (.12, .48, .95), 'INST_Tierra': (.22, .72, .12),
        'INST_Cloacal': (.65, .28, .10), 'INST_Fria': (.05, .40, .90),
        'INST_Caliente': (.90, .12, .08), 'INST_Reserva': (.95, .70, .10),
    }.items():
        casa['MATERIALS'][name] = {'color': [*rgb, 1.], 'roughness': .6, 'metallic': 0.}
    segmentos, reservas, terminales = [], [], []

    def grupo(name):
        casa['component']('INST_' + name, 'Anteproyecto coordinado con V06, anclajes y hormigón; unidades m.')

    def pieza(name, p, size, mat, cat, **meta):
        obj = box(name, p, size, mat, cat, 0)
        obj['meta'].update(meta)
        return obj

    def tubo(name, a, b, diametro, mat, cat, **meta):
        # Tubo anular: deja visible la luz interior y permite alojar conductores.
        import numpy as np
        a, b = np.array(a, float), np.array(b, float)
        axis = b-a
        if np.linalg.norm(axis) < 1e-8:
            return
        axis /= np.linalg.norm(axis)
        ref = np.array((0., 0., 1.) if abs(axis[2]) < .9 else (1., 0., 0.))
        u = np.cross(axis, ref); u /= np.linalg.norm(u); v = np.cross(axis, u)
        ro = diametro/2; ri = ro-min(.004, diametro*.10)
        n = 12
        verts = [(p+r*(u*math.cos(i*2*math.pi/n)+v*math.sin(i*2*math.pi/n))).tolist()
                 for p, r in [(a, ro), (b, ro), (a, ri), (b, ri)] for i in range(n)]
        faces = []
        for i in range(n):
            j = (i+1) % n
            faces += [[i,j,n+j,n+i], [2*n+i,3*n+i,3*n+j,2*n+j],
                      [i,2*n+i,2*n+j,j], [n+i,n+j,3*n+j,3*n+i]]
        obj = casa['add'](name, cat, verts, faces, mat)
        obj['meta'].update({'diametro_exterior_representado_m': diametro, **meta})
        segmentos.append({'nombre': name, 'a': a.tolist(), 'b': b.tolist(),
                           'diametro': diametro, 'capa': cat, **meta})
        return obj

    def ruta(name, points, d, mat, cat, **meta):
        # El muro norte del anexo llega al techo (no termina en el cielorraso).
        # Reencaminar sus cruces por huecos ENTRE montantes, a cota de servicio.
        # No se cortan dinteles, montantes ni vigas. La reserva corta revestimiento.
        coordinados=[points[0]]
        for a,b in zip(points,points[1:]):
            if (cat in (electrico,agua) and abs(a[2]-b[2])<1e-8 and 2.84<a[2]<2.97
                    and abs(a[0]-b[0])<1e-8 and min(a[1],b[1])<.03
                    and max(a[1],b[1])>.17 and 9.77<a[0]<15.):
                # Desplazamientos mínimos para cada conductor, preservando su orden.
                xc=(12.50 if a[0]<12.98 else 14.55)
                if cat==electrico:
                    xc-=.08
                elif mat=='INST_Caliente':
                    xc+=.08
                sentido=1 if b[1]>a[1] else -1
                y0=-.25 if sentido==1 else .45
                y1=.45 if sentido==1 else -.25
                coordinados.extend([(a[0],y0,a[2]),(xc,y0,a[2]),
                                    (xc,y1,a[2]),(b[0],y1,b[2])])
                rn='Paso_muro_%s_%.3f'%(cat,a[2])+'_'+str(xc)
                if not any(r['nombre']==rn for r in reservas):
                    reservas.append({'nombre':rn,'min':(xc-.025,-.02,a[2]-.023),
                                     'max':(xc+.025,.22,a[2]+.023)})
                    tubo('Camisa_'+rn,(xc,-.02,a[2]),(xc,.22,a[2]),.032,
                         'INST_Reserva',cat,funcion='Paso protegido entre montantes; sellar revestimiento')
            coordinados.append(b)
        for i, (a,b) in enumerate(zip(coordinados, coordinados[1:])):
            tubo(name+'_%02d' % i, a, b, d, mat, cat, **meta)

    def reserva(name, x, y, lado, z0=-.37, z1=.06):
        reservas.append({'nombre': name, 'min': (x-lado/2, y-lado/2, z0),
                         'max': (x+lado/2, y+lado/2, z1)})

    # Nombre, salida real del artefacto (x,y,z), grupo, DN, agua caliente.
    artefactos = [
        ('Suite_WC',4.24,4.99,.05,'suite',.110,False),
        ('Suite_bidet',5.14,5.00,.28,'suite',.050,True),
        ('Suite_ducha',4.27,7.15,.035,'suite',.050,True),
        ('Suite_lavatorio',5.19,7.33,.90,'suite',.050,True),
        ('Cocina_bacha',8.33,.54,.85,'cocina',.050,True),
        ('Bano_WC',11.54,-1.86,.05,'bano',.110,False),
        ('Bano_bidet',12.36,-1.85,.28,'bano',.050,True),
        ('Bano_ducha',10.35,-1.39,.035,'bano',.050,True),
        ('Bano_lavatorio',11.29,-.39,.90,'bano',.050,True),
        ('Lavadero_pileta',13.52,-1.84,.90,'lavadero',.050,True),
        ('Lavadero_lavarropas',14.34,-1.87,.70,'lavadero',.050,False),
    ]
    # Colectores bajo platea; la generatriz superior más alta queda bajo Z=-.36.
    # Pendiente constante aguas abajo; todas las uniones comparten cota de eje.
    pendiente = cfg['pendiente_desague']; yc = cfg['y_colector_cloacal_m']
    zcab = cfg['cota_eje_inicio_colectores_m']
    columnas = {'suite': 6.15, 'cocina': 9.15, 'bano': 12.70, 'lavadero': 14.65}

    def ztroncal(x):
        return zcab-pendiente*(7.6-yc)-pendiente*(x-columnas['suite'])

    def zramal(g, y):
        return ztroncal(columnas[g])+pendiente*(y-yc)

    grupo('Desagues')
    for g, xc in columnas.items():
        ys = sorted({y+(0 if 'WC' in name else .14)
                     for name,_,y,_,gg,_,_ in artefactos if gg == g}, reverse=True)
        ruta('Colector_'+g, [(xc,y,zramal(g,y)) for y in ys]+[(xc,yc,ztroncal(xc))],
             .110, 'INST_Cloacal', desagues, flujo='a_hacia_b', pendiente=pendiente)
    xs = list(columnas.values())+[19.2,20.2]
    ruta('Troncal_a_destino_pendiente', [(x,yc,ztroncal(x)) for x in xs], .110,
         'INST_Cloacal', desagues, flujo='a_hacia_b', pendiente=pendiente,
         destino='Extremo ciego de anteproyecto: red o tratamiento a definir; no hay descarga libre.')
    for name,x,y,z,g,d,caliente in artefactos:
        grupo('Desague_'+name)
        # El sifón queda EN SERIE: no existe una bajada directa que lo puentee.
        rx,ry,rz=x,y,z
        if 'WC' not in name:
            fondo=z-.22; salida=z-.10
            rx,ry,rz=x+.16,y+.14,salida
            ruta('Sifon_'+name,[(x,y,z),(x,y,fondo),(x,y+.14,fondo),
                 (x,y+.14,salida),(rx,ry,rz)],d,'INST_Cloacal',desagues,
                 funcion='Cierre hidráulico en serie; WC con sifón propio del artefacto')
            if 'ducha' in name:
                reserva('Caja_sifon_'+name,x+.08,y+.07,.40)
        xc = columnas[g]; zj = zramal(g,ry); zi = zj+pendiente*abs(xc-rx)
        # Bajada y transición con dos tramos a 45 grados, no codo enterrado a 90.
        # Transición íntegramente bajo la platea: evita tocar el borde de la reserva.
        giro = min(.16, abs(xc-rx)/3, -.38-zi-d/2)
        assert giro > .01, ('Falta profundidad para el codo',name)
        paso = 1 if xc>rx else -1
        ruta(name, [(rx,ry,rz), (rx,ry,zi+giro), (rx+paso*giro,ry,zi), (xc,ry,zj)],
             d, 'INST_Cloacal', desagues, flujo='a_hacia_b', artefacto=name)
        reserva('Paso_'+name,rx,ry,d+.07)
        tubo('Camisa_'+name,(rx,ry,-.37),(rx,ry,.045),d+.04,'INST_Reserva',desagues,
             funcion='Camisa sin adherencia rígida; sellado flexible y refuerzo de borde a calcular')
        terminales.append({'nombre':name, 'tipo':'sanitario', 'posicion':(x,y,z)})
        if 'ducha' in name:
            pieza('Rejilla_'+name,(x,y,.043),(.12,.12,.012),'Acero',desagues)
    # Cámaras abiertas con tapa removible, fuera de la huella de la vivienda.
    for name,x in [('CI_suite',6.15),('CI_servicios',14.65),('CI_salida',19.2)]:
        grupo(name); zb=ztroncal(x)-.16; top=-.20
        pieza('Solera',(x,yc,zb),(.70,.70,.08),'Piso piedra',desagues)
        for yy in [yc-.31,yc+.31]:
            for xx in [x-.22,x+.22]:
                pieza('Jamba_NS',(xx,yy,(zb+top)/2),(.18,.08,top-zb),'Piso piedra',desagues)
            zpuente=ztroncal(x)+.10
            pieza('Dintel_NS',(x,yy,(zpuente+top)/2),(.26,.08,top-zpuente),'Piso piedra',desagues)
        # Aberturas inferiores para el paso del troncal en las dos paredes E/O.
        for xx in [x-.31,x+.31]:
            for yy in [yc-.22,yc+.22]:
                pieza('Jamba',(xx,yy,(zb+top)/2),(.08,.18,top-zb),'Piso piedra',desagues)
            zpuente=ztroncal(x)+.09
            pieza('Dintel_paso',(xx,yc,(zpuente+top)/2),(.08,.26,top-zpuente),'Piso piedra',desagues)
        pieza('Tapa_registro',(x,yc,top+.025),(.70,.70,.05),'Grafito',desagues,
              mantenimiento='Tapa accesible; no cubrir con construcciones')
    # Ventilaciones independientes al aire exterior, fuera del alero.
    for name,g,x,y in [('Suite','suite',3.8,8.65),('Sur','bano',9.2,-3.3)]:
        grupo('Ventilacion_'+name)
        xc=columnas[g]; origen=(xc,yc,ztroncal(xc))
        # La conexión asciende desde el colector: no es un ramal de efluentes.
        ruta('Ventilacion_'+name,[origen,(x,yc,origen[2]+.08),(x,y,origen[2]+.12),(x,y,4.7)],
             .075,'INST_Cloacal',desagues,funcion='Ventilación primaria; verificar distancia a aberturas')

    # Agua: punto exterior independiente al sur; AF y AC sobre cielorraso.
    grupo('Agua_cabecera')
    za=cfg['altura_distribucion_agua_m']; colector=(14.45,-.65,za)
    ruta('Entrada_AF_a_llave',[(14.45,-3.85,-.48),(14.45,-.65,-.48),colector],
         .032,'INST_Fria',agua,funcion='Abastecimiento exterior a definir: tanque/bomba/red')
    reserva('Entrada_agua',14.45,-.65,.10)
    reserva('Cielorraso_cabecera_AF',14.45,-.65,.06,2.75,2.84)
    tubo('Camisa_agua',(14.45,-.65,-.37),(14.45,-.65,.045),.06,'INST_Reserva',agua)
    pieza('Llave_general_AF',(14.45,-.65,1.25),(.10,.10,.14),'Acero',agua)
    pieza('Filtro_AF',(14.45,-.65,1.00),(.13,.13,.20),'INST_Fria',agua)
    # Equipo eléctrico mural, sobre lavarropas; las bocas coinciden con los tubos.
    equipo=(14.30,-1.87,1.91)
    pieza('Termotanque_electrico',equipo,(.48,.48,.68),'Cerámica blanca',agua,
          capacidad_orientativa_litros=60,funcion='Agua caliente; revisar capacidad y fijaciones')
    fria=(14.42,-1.87,1.57); caliente=(14.18,-1.87,1.57)
    ruta('AF_termotanque',[colector,(14.42,-.65,za),(14.42,-1.54,za),
         (14.42,-1.54,1.57),fria],
         .025,'INST_Fria',agua)
    cab_ac=(14.18,-.65,za)
    ruta('AC_termotanque',[caliente,(14.18,-1.54,1.57),(14.18,-1.54,za),cab_ac],.025,'INST_Caliente',agua,
         aislamiento='Aislación térmica a especificar')
    for xx in [14.42,14.18]:
        reserva('Cielorraso_termotanque_'+str(xx),xx,-1.54,.06,2.75,2.84)
    pieza('Valvula_seguridad',fria,(.08,.08,.08),'Acero',agua)
    ruta('Descarga_seguridad',[fria,(14.55,-1.87,1.57),(14.55,-1.87,.82)],.020,'INST_Fria',agua,
         funcion='Descarga visible con ruptura de carga hacia embudo sifonado')
    pieza('Embudo_descarga',(14.55,-1.87,.76),(.10,.10,.06),'INST_Cloacal',desagues)
    ruta('Embudo_a_sifon_lavarropas',[(14.55,-1.87,.73),(14.34,-1.87,.70)],
         .032,'INST_Cloacal',desagues)
    # Alimentaciones terminales derivadas de cabeceras comunes. AC separada 8 cm.
    for name,x,y,z,g,d,hay_ac in artefactos:
        grupo('Agua_'+name)
        if 'ducha' in name:
            py=7.68 if g=='suite' else -2.10; altura=1.10
        elif 'WC' in name:
            py=y-.22; altura=.62
        elif 'bidet' in name:
            py=y-.20; altura=.50
        elif 'lavarropas' in name:
            py=-2.10; altura=.95
        else:
            py=y-.26; altura=.94 if g=='cocina' else .99
        for hot in ([False,True] if hay_ac else [False]):
            xx=x+(.08 if hot else 0); color='INST_Caliente' if hot else 'INST_Fria'
            origen=cab_ac if hot else colector; tag=('AC_' if hot else 'AF_')+name
            # Separación de redes horizontal; ramales registrables sobre cielorraso.
            yy=2.35 if hot else 2.15
            ruta(tag,[origen,(origen[0],yy,za),(xx,yy,za),(xx,py,za),(xx,py,altura)],
                 .020,color,agua,artefacto=name,funcion='Derivación individual con llave de corte')
            pieza('Llave_'+tag,(xx,py,altura+.08),(.05,.05,.07),'Acero',agua)
            reserva('Cielorraso_'+tag,xx,py,.055,2.75,2.84)
        if hay_ac:
            ruta('Mezcladora_'+name,[(x,py,altura),(x+.08,py,altura)],.020,'Acero',agua)
        if 'ducha' in name:
            ruta('Ducha_cabezal_'+name,[(x,py,altura),(x,py,2.05),(x,py+(.20 if g=='bano' else -.20),2.05)],
                 .020,'Acero',agua)

    # Tablero cercano al acceso este, fuera de baños y lavadero.
    grupo('Tablero')
    panel=cfg['tablero_xyz_m']; ze=cfg['altura_distribucion_electrica_m']
    reserva('Cielorraso_tablero',panel[0],panel[1],.05,2.75,2.84)
    pieza('Tablero_principal',panel,(.18,.48,.62),'Grafito',electrico,
          proteccion='Seccionador general, DPS, diferenciales 30 mA y termomagnéticas por circuito; calibres a calcular')
    circuitos={
        'IUG': ('Iluminación',1.5), 'TUG_D':('Tomas dormitorios',2.5),
        'TUG_E':('Tomas estar y oficina',2.5), 'TUG_C':('Tomas de mesada',2.5),
        'TUG_B':('Tomas baños',2.5), 'HEL':('Heladera',2.5),
        'LAV':('Lavarropas',2.5), 'HOR':('Horno',4.),
        'ANA':('Anafe',6.), 'TER':('Termotanque',2.5),
    }
    for i,(cod,(uso,seccion)) in enumerate(circuitos.items()):
        pieza('Proteccion_'+cod,(17.59,2.77+(i%5)*.085,1.60-(i//5)*.20),(.04,.065,.12),
              'Cerámica blanca',electrico,circuito=cod,uso=uso,
              seccion_orientativa_mm2=seccion,calibre='Pendiente de cálculo de carga y tendido')
    # Tomas sobre caras interiores, fuera de vanos y de las duchas.
    # Normal: altura .30; mesada: 1.10; baño: 1.20 (fuera de ducha).
    tomas=[
        ('Dorm_principal_1',.25,3.95,.30,'TUG_D','Y'),
        ('Dorm_principal_2',3.50,7.20,.30,'TUG_D','Y'),
        ('Dorm_principal_3',2.40,3.51,.30,'TUG_D','X'),
        ('Dorm2_1',.25,.35,.30,'TUG_D','Y'),('Dorm2_2',2.64,1.65,.30,'TUG_D','Y'),
        ('Dorm3_1',15.05,-1.30,.30,'TUG_D','Y'),('Dorm3_2',17.72,.65,.30,'TUG_D','Y'),
        ('Estar_TV',14.72,5.55,.30,'TUG_E','Y'),('Estar_aux',14.72,7.10,.30,'TUG_E','Y'),
        ('Comedor',5.88,5.90,.30,'TUG_E','Y'),
        ('Oficina_1',16.10,7.70,.30,'TUG_E','X'),('Oficina_2',17.72,6.90,.30,'TUG_E','Y'),
        ('Oficina_3',15.07,4.80,.30,'TUG_E','Y'),
        ('Mesada_1',7.30,.28,1.10,'TUG_C','X'),('Mesada_2',9.45,.28,1.10,'TUG_C','X'),
        ('Heladera',10.85,.28,.40,'HEL','X'),('Horno',6.00,.28,.45,'HOR','X'),
        ('Anafe',6.80,.28,.65,'ANA','X'),('Lavarropas',14.67,-2.09,1.10,'LAV','X'),
        ('Termotanque',14.67,-2.09,1.90,'TER','X'),
        ('Bano',12.83,-.48,1.20,'TUG_B','Y'),('Suite',5.50,5.70,1.20,'TUG_B','Y'),
    ]

    desvios_ventanas=[]

    def bajada_electrica(name,p):
        """Desciende por paño ciego y retorna bajo el antepecho, sin mover la toma.

        Se considera también la proyección de la ventana sobre la cara interior:
        un tubo superficial no debe pasar por delante del vidrio aunque no lo toque.
        """
        x,y,z=p
        for w in casa['WALLS']:
            u=0 if w['axis']=='X' else 1; normal=1-u
            if abs(p[normal]-w['pos'])>w['thickness']/2+.20:
                continue
            vanos=[h for h in w['holes'] if h[4] in ('ventana','corrediza')]
            obstaculos=[h for h in vanos if h[0]-.08<=p[u]<=h[1]+.08
                        and z<h[3]+.08 and ze>h[2]-.08]
            if not obstaculos:
                continue
            # Una toma situada en el vidrio requiere relocalización explícita.
            assert all(z+.08<h[2] for h in obstaculos), ('Terminal dentro de ventana',name)
            candidatos=sorted({q for h in vanos for q in (h[0]-.18,h[1]+.18)},
                               key=lambda q:(abs(q-p[u]),q))
            destino=None
            for q in candidatos:
                if not w['start']+.12<q<w['end']-.12:
                    continue
                if any(h[0]-.12<q<h[1]+.12 and z<h[3]+.08 for h in w['holes']):
                    continue
                # El tramo de retorno tampoco puede atravesar otro vano bajo.
                if any(min(q,p[u])<h[1]+.08 and max(q,p[u])>h[0]-.08
                       and h[2]-.08<z<h[3]+.08 for h in w['holes']):
                    continue
                destino=q;break
            assert destino is not None, ('No hay paño ciego para la bajada',name)
            pie=list(p);pie[u]=destino;alto=pie.copy();alto[2]=ze
            desvios_ventanas.append({'terminal':name,'pared':w['name'],
                                     'bajada_xy_m':alto[:2],'retorno_z_m':z})
            return [tuple(alto),tuple(pie),p]
        return [(x,y,ze),p]

    def electrificar(name,p,circuito,tipo='toma',axis='X',switch=None):
        grupo('Electrico_'+name)
        x,y,z=p
        size=(.13,.05,.09) if axis=='X' else (.05,.13,.09)
        pieza(tipo+'_'+name,p,size,'Cerámica blanca',electrico,circuito=circuito,
              funcion=tipo,altura_m=z,puesta_a_tierra=True)
        top=(panel[0],panel[1],ze)
        bajada=bajada_electrica(name,p)
        bx,by,_=bajada[0]
        puntos=[panel,top,(panel[0],2.60,ze),(bx,2.60,ze)]+bajada
        ruta('Canalizacion_'+name,puntos,.025,'INST_Canalizacion',electrico,
             circuito=circuito,funcion='Pasacables sobre cielorraso y bajada superficial sin corte de madera')
        # Conductores explícitos dentro del conducto, con PE en todas las bocas.
        for j,(conductor,mat) in enumerate([('L','INST_Fase'),('N','INST_Neutro'),('PE','INST_Tierra')]):
            pts=[(px+(j-1)*.004,py,pz) for px,py,pz in puntos]
            ruta('Cable_'+conductor+'_'+name,pts,.0025,mat,electrico,
                 circuito=circuito,conductor=conductor,
                 seccion_orientativa_mm2=circuitos[circuito][1],
                 diametro_grafico=True,interruptor=switch or '')
        reserva('Paso_cielorraso_'+name,bx,by,.045,2.75,2.84)
        tubo('Pasacable_'+name,(bx,by,2.75),(bx,by,2.84),.034,'INST_Reserva',electrico)
        terminales.append({'nombre':name,'tipo':tipo,'circuito':circuito,'posicion':p})

    for name,x,y,z,c,axis in tomas:
        electrificar(name,(x,y,z),c,axis=axis)
    # Una llave por ambiente, al lado de los accesos. Bocas en las luminarias V04.
    luces=[
        ('Dorm_principal',(1.8,5.5,2.735),(2.42,3.51,1.10),'X'),
        ('Dorm2',(1.4,1.1,2.735),(1.50,2.04,1.10),'X'),
        ('Suite',(4.65,6.3,2.735),(3.85,6.42,1.10),'Y'),
        ('Bano',(11.6,-.8,2.735),(11.86,-.08,1.10),'X'),
        ('Lavadero',(14.,-1.,2.735),(13.26,-.08,1.10),'X'),
        ('Dorm3',(16.5,-.4,2.735),(16.25,1.10,1.10),'X'),
        ('Oficina',(16.4,5.5,2.735),(16.25,3.30,1.10),'X'),
        ('Estar',(12.4,5.8,2.735),(17.70,2.80,1.10),'Y'),
        ('Cocina',(8.2,2.7,2.735),(5.88,3.70,1.10),'Y'),
        ('Vestidor',(4.65,3.95,2.735),(5.48,4.30,1.10),'X'),
    ]
    for name,p,sw,axis in luces:
        electrificar(name,p,'IUG','boca_luz',switch='Llave_'+name)
        grupo('Llave_'+name)
        pieza('Llave_'+name,sw,(.08,.05,.10) if axis=='X' else (.05,.08,.10),
              'Cerámica blanca',electrico,circuito='IUG',controla=name)
        bajada_sw=bajada_electrica('Llave_'+name,sw)
        sx,sy,_=bajada_sw[0]
        puntos_sw=list(reversed(bajada_sw))+[(p[0],sy,ze),(p[0],p[1],ze)]
        ruta('Llave_canalizacion_'+name,puntos_sw,
             .020,'INST_Canalizacion',electrico,circuito='IUG')
        for j,(tag,mat) in enumerate([('Fase','INST_Fase'),('Retorno','INST_Fase'),('PE','INST_Tierra')]):
            off=(j-1)*.003
            ruta('Llave_'+tag+'_'+name,[(px+off,py,pz) for px,py,pz in puntos_sw],.0025,mat,electrico,
                  circuito='IUG',funcion=tag)
        reserva('Paso_llave_'+name,sx,sy,.04,2.75,2.84)
    for i,y in enumerate([4.9,5.65,6.4]):
        electrificar('Colgante_'+str(i),(8.2,y,2.75),'IUG','boca_luz',switch='Llave_Estar')
    grupo('Alimentacion_y_tierra')
    ruta('Reserva_acometida',[(18.60,3.05,-.48),(17.70,2.95,-.48),panel],
         .040,'INST_Canalizacion',electrico,funcion='Acometida desde medidor a definir')
    ruta('PE_principal',[panel,(17.70,2.95,-.48),(18.65,2.95,-.48),(18.65,2.95,-1.95)],
         .006,'INST_Tierra',electrico,funcion='Puesta a tierra: sección y electrodo a verificar por medición')
    reserva('Paso_tierra_y_acometida',17.70,2.95,.10)
    cylinder('Jabalina',(18.65,2.95,-.35),(18.65,2.95,-1.95),.008,'Acero',electrico)
    pieza('Registro_tierra',(18.65,2.95,-.17),(.25,.25,.06),'Grafito',electrico)

    # V06: las reservas no pueden cortar pernos, soleras, bases ni sus dados.
    protegidas=[o for o in objects if o['collection'] in
                (CAT_ANCHOR,CAT_SHOE,CAT_GASKET,CAT_SILL) or
                (o['collection']==CAT_CONCRETE and not o['name'].startswith('Platea_'))]
    for o in protegidas:
        lo,hi=bounds(o)
        for r in reservas:
            assert not all(min(hi[i],r['max'][i])-max(lo[i],r['min'][i])>1e-8 for i in range(3)), (
                'Reserva contra anclaje o refuerzo V06',r['nombre'],o['id'])
    recortes = recortar_reservas_instalaciones(casa, reservas)
    # Comprobaciones geométricas y de continuidad por los datos de la red.
    escurrimientos=[s for s in segmentos if s.get('flujo')=='a_hacia_b']
    def punto_en_tramo(p,s):
        a,b=s['a'],s['b'];v=[b[i]-a[i] for i in range(3)]
        t=sum((p[i]-a[i])*v[i] for i in range(3))/sum(k*k for k in v)
        return -1e-7<=t<=1+1e-7 and math.dist(p,[a[i]+t*v[i] for i in range(3)])<1e-7
    salida_final=(20.2,yc,ztroncal(20.2))
    for s in escurrimientos:
        assert (math.dist(s['b'],salida_final)<1e-7 or
                any(q is not s and q['b'][2]<s['b'][2]-1e-8 and punto_en_tramo(s['b'],q)
                    for q in escurrimientos)), ('Ramal desconectado',s['nombre'])
    for s in segmentos:
        if s.get('flujo') == 'a_hacia_b':
            a,b=s['a'],s['b']; largo=math.hypot(b[0]-a[0],b[1]-a[1])
            assert a[2] > b[2], ('Contrapendiente',s['nombre'])
            if largo > 1e-8:
                assert (a[2]-b[2])/largo >= pendiente-1e-8, s['nombre']
    assert all(any(r['nombre']=='Paso_'+a[0] for r in reservas) for a in artefactos)
    for s in segmentos:
        if s['nombre'].startswith(('Colector_', 'Troncal_')):
            assert max(s['a'][2],s['b'][2])+s['diametro']/2 < -.36
    # Prueba conservadora por envolventes: ninguna canalización atraviesa madera.
    # Las piezas inclinadas usan su caja envolvente, nunca se descuenta madera.
    def limites(o):
        return ([min(v[i] for v in o['vertices']) for i in range(3)],
                [max(v[i] for v in o['vertices']) for i in range(3)])
    madera=[(o,limites(o)) for o in objects if o['collection'] in
            ('08a_Entramado_paredes','08b_Estructura_techo','08d_Postes_en_muros',
             CAT_HEADER,CAT_CORE,CAT_SILL,CAT_GALLERY_POST)]
    for obj in objects:
        if obj['collection'] not in (electrico,agua) or 'diametro_exterior_representado_m' not in obj['meta']:
            continue
        if obj['meta']['diametro_exterior_representado_m']<.010:
            continue
        lo,hi=limites(obj)
        for w,(a,b) in madera:
            assert not all(min(hi[i],b[i])-max(lo[i],a[i])>1e-5 for i in range(3)), (
                'Canalización contra madera; reencaminar',obj['name'],w['id'])
    apoyos=[(o,limites(o)) for o in objects if o['collection'] in
            (CAT_CONCRETE,CAT_ANCHOR,CAT_SHOE,CAT_GASKET)]
    for obj in objects:
        if obj['collection'] not in (electrico,desagues,agua) or obj['meta'].get('diametro_exterior_representado_m',0)<.010:
            continue
        lo,hi=limites(obj)
        for apoyo,(a,b) in apoyos:
            assert not all(min(hi[i],b[i])-max(lo[i],a[i])>1e-5 for i in range(3)), (
                'Instalación contra hormigón o anclaje V06',obj['name'],apoyo['id'])
    ventanas_verificadas=verificar_electricidad_ventanas(casa)
    return {'capas': [electrico,desagues,agua], 'artefactos_sanitarios':len(artefactos),
            'desvios_electricos_por_ventanas':desvios_ventanas,
            'ventanas_verificadas':ventanas_verificadas,
            'tomas':len(tomas),'circuitos':{k:{'uso':v[0],'seccion_orientativa_mm2':v[1]} for k,v in circuitos.items()},
            'reservas':reservas,'piezas_recortadas':recortes,'tramos':len(segmentos),
            'pendiente_cloacal':pendiente,'tablero_xyz_local_m':panel,
            'verificacion':'Geometría, reservas, continuidad cloacal, pendientes, madera, hormigón, anclajes V06 y electricidad fuera de ventanas; no cálculo reglamentario.',
            'criterios':cfg,'terminales':terminales,
            'pendientes_de_proyecto':['Origen de agua y presión disponible','Medidor y potencia eléctrica',
                'Destino cloacal y cotas exteriores','Refuerzo de platea alrededor de reservas',
                'Accesorios, soportes, sellados, dimensionamiento y coordinación final en obra']}


def verificar_electricidad_ventanas(casa):
    """Audita toda la geometría eléctrica, incluyendo cables, cajas y pasacables.

    El volumen protegido incluye 6 cm de margen alrededor del vano y la franja
    de servicio interior. Las envolventes son conservadoras para tramos oblicuos.
    """
    electricos=[(o,bounds(o)) for o in casa['OBJECTS']
                if o['collection']==INSTALACIONES['electrico']]
    cantidad=0
    for w in casa['WALLS']:
        u=0 if w['axis']=='X' else 1;normal=1-u
        for a,b,z0,z1,kind in w['holes']:
            if kind not in ('ventana','corrediza'):
                continue
            cantidad+=1
            lo=[0.,0.,z0-.06];hi=[0.,0.,z1+.06]
            lo[u]=a-.06;hi[u]=b+.06
            franja=w['thickness']/2+.20
            lo[normal]=w['pos']-franja;hi[normal]=w['pos']+franja
            for obj,(ol,oh) in electricos:
                assert not all(min(oh[i],hi[i])-max(ol[i],lo[i])>1e-8 for i in range(3)), (
                    'Electricidad atraviesa ventana o su proyección interior',w['name'],(a,b),obj['name'])
    return cantidad


def recortar_reservas_instalaciones(casa, reservas):
    """Resta prismas de reserva a cajas de platea, solados y cielorraso.

    Descompone cada caja en hasta seis cajas sin superposición por cada corte.
    El vacío es geometría real, también en --check; no un marcador superpuesto.
    Conserva material, colección y metadatos. No recorta piezas estructurales de madera.
    """
    def bounds(o):
        return ([min(v[i] for v in o['vertices']) for i in range(3)],
                [max(v[i] for v in o['vertices']) for i in range(3)])

    def restar(lo, hi, r):
        a=[max(lo[i],r['min'][i]) for i in range(3)]
        b=[min(hi[i],r['max'][i]) for i in range(3)]
        if any(b[i]-a[i]<=1e-9 for i in range(3)):
            return [(lo,hi)],False
        partes=[]; low=list(lo); high=list(hi)
        for i in range(3):
            if a[i]-low[i]>1e-9:
                h=high.copy();h[i]=a[i];partes.append((low.copy(),h));low[i]=a[i]
            if high[i]-b[i]>1e-9:
                l=low.copy();l[i]=b[i];partes.append((l,high.copy()));high[i]=b[i]
        return partes,True

    categorias=('00_Base','06a_Cielorraso','02_Tabiques',CAT_CONCRETE)
    originales=list(casa['OBJECTS']); cambios=0; usados=set()
    for obj in originales:
        if obj['collection'] not in categorias:
            continue
        partes=[bounds(obj)]; afectadas=[]
        for r in reservas:
            original_lo,original_hi=bounds(obj)
            if all(min(original_hi[i],r['max'][i])-max(original_lo[i],r['min'][i])>1e-9 for i in range(3)):
                usados.add(r['nombre'])
            nuevas=[]
            for lo,hi in partes:
                resultado,corto=restar(lo,hi,r);nuevas.extend(resultado)
                if corto:
                    afectadas.append(r['nombre']);usados.add(r['nombre'])
            partes=nuevas
        if not afectadas:
            continue
        cambios+=1;casa['OBJECTS'].remove(obj)
        casa['component'](obj['assembly'],obj['meta']['referencia'])
        for i,(lo,hi) in enumerate(partes):
            nuevo=casa['box'](obj['name']+'_Reserva_%03d'%i,
                    [(lo[j]+hi[j])/2 for j in range(3)], [hi[j]-lo[j] for j in range(3)],
                    obj['material'],obj['collection'],0)
            nuevo['meta'].update(obj['meta'])
            nuevo['meta'].update({'original':obj['id'],'reservas_json':json.dumps(sorted(set(afectadas)))})
    # Todas las reservas solicitadas deben alcanzar una pieza: evita agujeros ficticios.
    assert usados == {r['nombre'] for r in reservas}, ('Reservas sin pieza',set(r['nombre'] for r in reservas)-usados)
    for obj in casa['OBJECTS']:
        if obj['collection'] in categorias:
            lo,hi=bounds(obj)
            for r in reservas:
                assert not all(min(hi[i],r['max'][i])-max(lo[i],r['min'][i])>1e-8 for i in range(3)), obj['id']
    return cambios


def main_v06():
    c,t=cargar_fuentes()
    report=preparar_y_comprobar(c,t)
    anchors,unresolved=augment_v06(c)
    report['instalaciones']=agregar_instalaciones(c)
    # The old validation checks names and opening clearance; extend for new collections.
    c['validate']()
    for op in c['OPENINGS']:
        prefix=op['id'].rsplit('/',1)[1]
        leaves=[o for o in c['OBJECTS'] if o['assembly']==op['wall'] and o['name'] in [prefix+'_Header_0',prefix+'_Header_1']]
        assert len(leaves)==2
        for o in leaves:
            lo,hi=bounds(o);axis=0 if op['axis']=='X' else 1
            assert abs(lo[axis]-(op['a']-.045))<1e-6 and abs(hi[axis]-(op['b']+.045))<1e-6
            assert abs(lo[2]-op['head'])<1e-6
    rows=timber_inventory(c)
    base=Path(__file__).resolve().parent
    out=base/'Angus_Ranch_V06'
    # --check es de solo lectura: no produce cómputos, planos, renders ni .blend.
    if '--check' in sys.argv:
        report.update(version_integrada='V06 + instalaciones',piezas_casa=len(c['OBJECTS']),
                      piezas_computadas=len(rows),pernos_solera=len(anchors),
                      soleras_anclaje_especial=unresolved,blender_ejecutado=False)
        print(json.dumps(report,ensure_ascii=False,indent=2));return
    grouped=write_outputs(out,c,rows,anchors,unresolved,report)
    (out/'LEEME_V06.md').write_text(README_V06,encoding='utf-8')
    construir_integrado(c,t,report)
    report['_anchors']=anchors
    cameras=setup_blender_v06(c,rows,grouped,report,out)
    import bpy
    scene=bpy.context.scene
    if '--save' in sys.argv or '--render' in sys.argv:
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'angus_ranch_V06_casa_y_terreno.blend'))
    if '--render' in sys.argv:
        scene.render.engine='BLENDER_WORKBENCH'
        scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
        scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
        scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=True
        scene.display.shading.background_type='WORLD';scene.world.color=(.83,.84,.81)
        scene.view_settings.view_transform='Standard'
        scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
        for frame,name in [(1,'09_Headers_dobles'),(10,'10_Anclajes_y_cimientos'),(20,'11_Despiece_madera'),(30,'12_Detalle_header_explotado'),(40,'13_Detalle_anclajes')]:
            for layer in scene.view_layers:layer.use=layer.name==name
            bpy.context.window.view_layer=scene.view_layers[name];scene.frame_set(frame);scene.camera=cameras[name]
            scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
        for layer in scene.view_layers:layer.use=layer.name=='09_Headers_dobles'
        bpy.context.window.view_layer=scene.view_layers['09_Headers_dobles'];scene.frame_set(1);scene.camera=cameras['09_Headers_dobles']
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'angus_ranch_V06_casa_y_terreno.blend'))
    print('V06 LISTA:',out)


README_V06='''# Angus Ranch V06 - Woodframe y anclajes

## Instalaciones incorporadas

Colecciones 20_Instalacion_electrica, 21_Desagues_sanitarios y 22_Agua_fria_caliente.
View Layers 14_Instalacion_electrica, 15_Desagues_y_cimientos y 16_Agua_fria_y_caliente.
Tablero junto al acceso este; tomas, llaves, circuitos y pasacables.
Las bajadas eléctricas evitan ventanas: descienden por paños ciegos laterales
y retornan bajo el antepecho hacia las tomas. --check verifica todos los vanos
vidriados contra canalizaciones, conductores y cajas, incluso sobre la cara interior.
AF/AC desde lavadero con llaves y termotanque. Desagües sanitarios bajo la platea, con sifones,
ventilaciones y registros exteriores. Las reservas recortan el hormigón V06;
se mantienen la junta de 3 mm, los pernos, dados y bases de postes. Los recorridos
se coordinan con esas piezas sin perforar madera. Dimensiones de anteproyecto:
verificar cargas, diámetros, soportes, refuerzos y acometidas exteriores.
--check comprueba el modelo en memoria y no escribe archivos de salida.

Abrir angus_ranch_V06_casa_y_terreno.blend. La V05 original no se modifica.
El archivo central es ../angus_ranch_V06_casa_y_terreno.py: autónomo, incluye la V05 y la extensión V06.
Ejecutarlo en Scripting crea una escena nueva; las ediciones manuales del .blend no vuelven al Python.

## Vistas en Blender

Las ocho capas anteriores permanecen. Selector View Layer, arriba a la derecha:

| Capa | Contenido | Fotograma para cámara |
| --- | --- | --- |
| 09_Headers_dobles | Entramado + headers, hojas con colores diferentes | 1 |
| 10_Anclajes_y_cimientos | Estructura de paredes, soleras, junta, pernos, bases y hormigón | 10 |
| 11_Despiece_madera | Una copia por pieza, agrupada por uso, sector y dimensiones | 20 |
| 12_Detalle_header_explotado | Ventana Norte O0; separación didáctica de tablas y núcleo | 30 |
| 13_Detalle_anclajes | Corte del perno de solera y ejemplo de hold-down | 40 |

Elegir la capa y el fotograma indicado, luego Numpad 0. Blender usa cámara por escena, no por View Layer: cambiar capa solo NO cambia la cámara. También se puede seleccionar la cámara CAM_V06 correspondiente y Ctrl+Numpad 0. Para explorar el despiece, desplegar colección 17, elegir un grupo o pieza y Numpad . (Frame Selected). La vista general es un índice; los rótulos se leen acercándose.

Las copias de despiece y los detalles tienen computable=False y pieza_origen cuando corresponde. No se suman al edificio. Sus geometrías están en mesas de presentación separadas y ocultas en las ocho capas originales. Se muestran blancos de corte rectangulares, no siempre el corte oblicuo terminado. El resto de la casa conserva su implantación, orientación y escala.

## Headers

La V05 ya incluía dos hojas. La V06 las identifica como A/B, agrega el núcleo separado y ofrece vista explotada. Referencia real: Thallon 68C, PDF 81. La captura adjunta mezcla el título 68C con la leyenda LVL/LSL de 69B, PDF 82; no son sistemas intercambiables.
Se conservan las medidas del proyecto: tablas de 45 mm, no equivalencia literal con 2x cepillado estadounidense. Muros de 140 mm: 45 + 4x12.5 contrachapado + 45 mm. Tabiques de 90 mm: 45+45 mm. Alturas 220/300 mm heredadas. El núcleo continuo sustituye el aislamiento de dintel de V05; revisar su efecto térmico y su composición resistente. Uniones entre hojas, especie, grado, apoyos, cantidad de trimmers y secciones requieren cálculo, especialmente en los dos vanos de 4 m. La vista explotada no altera las dimensiones del edificio.

## Cimientos / anclajes

Se conserva la platea volumétrica de V05, con su cara superior 3 mm más baja para representar la junta bajo la solera existente. La solera no cambia de cota ni de sección; queda tratada y en una colección propia. Pernos con pata L, diámetro gráfico 12.7 mm, empotramiento 180 mm, arandelas con agujero y tuercas hexagonales separadas. Paso objetivo <=1.20 m y anclajes próximos a extremos de cada solera, evitando montantes y aberturas. Las excepciones geométricas se enumeran en el informe y necesitan una conexión especial.
Los postes tienen bases U ilustrativas y madera elevada 50 mm: su extremo superior se conserva. Hay seis dados de galería y ocho refuerzos locales bajo postes, todos de estudio, sin armaduras ni cálculo geotécnico. La capa 13 muestra el interior mediante medias secciones; los cuerpos completos ocultan el empotramiento en la capa 10. Los taladros de soleras y hormigón se indican por el recorrido del perno (sin booleanos); la rosca no está modelada. Las placas U, tornillos y anclajes no son un producto homologado.
El hold-down de capa 13 explica una conexión distinta al perno de solera, con montante doble, placa y anclaje dedicado. NO es una distribución ejecutiva de hold-downs ni un cómputo de esas fijaciones: faltan cálculo lateral, paños resistentes y selección de producto. Libro: 12A, 83A y 85A/B. Las medidas del libro no se presentan como reglamento argentino.

## Cómputo y cotización

Abrir Computo_madera_V06.html para resumen, filtros y tablas. Los CSV usan UTF-8 y separador punto y coma; al importar elegir punto decimal. Todos se regeneran desde la geometría:
- 01_piezas_individuales: ID estable y dimensiones del blanco de corte.
- 02_despiece_por_sector: cantidad por uso, pared/techo y medidas.
- 03_cotizacion_tablas_stock: tablas de largos hipotéticos con reserva 10% por renglón.
- 04_plan_cortes: IDs y cortes asignados a cada tabla, 10 mm de sobrelargo y 3 mm de sierra por corte.
- 05_piezas_especiales_y_tableros: vigas, largos >6 m y contrachapado aparte.
- 06_anclajes_solera: coordenadas locales y solera asociada, no listado homologado de fijaciones.

Las dimensiones se toman según la dirección de la fibra; un cabio inclinado no se mide con la altura total de su caja global. Se redondea hacia arriba al mm para madera y se mantiene 12.5 mm para contrachapado. El volumen es del blanco de corte, no volumen neto instalado. Largos comerciales supuestos 2.4/3/3.6/4.2/4.8/6 m. Empaquetado heurístico con reutilización dentro de igual sección y uso; verificar contra oferta real del aserradero. No se simulan empalmes para convertir largos continuos en piezas comerciales. Todas las vigas quedan aparte, incluso las cortas.
Incluye madera estructural modelada, listones de fachada, tablas del deck y separadores. No incluye muebles, placas OSB, tableros de cubierta ni siding en el pedido de tablas. El bastidor del deck sigue siendo un volumen de V05, no viguetas desglosadas. Faltan detalles de empalmes, arriostramiento, bloqueos y conectores de cubierta; enlace superior del rincón del anexo y encuentros heredados requieren desarrollo. Por ello es una estimación del modelo, no el pedido completo definitivo de la casa.

## Regeneración

python angus_ranch_V06_casa_y_terreno.py --check
blender --background --python angus_ranch_V06_casa_y_terreno.py -- --save --render

La primera opción verifica geometría y genera los cómputos; la segunda además construye Blender, guarda .blend y renderiza cuatro vistas. verificacion_V06.json registra lo realmente ejecutado. No sobrescribe V05 ni borra escenas preexistentes al ejecutarse desde Blender abierto.
'''


if __name__=='__main__':
    main_v06()
