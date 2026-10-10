"""Lumo en la vista 3D: amoblar, cambiar muebles y proponer ajustes de los espacios.

El usuario pide en lenguaje natural («sumá un escritorio en la oficina», «agrandá el
baño», «armá una galería al norte») y Lumo responde con un mensaje y una lista de
**operaciones** validadas. La IA no ubica muebles por coordenadas: elige qué hacer y
dónde, y `capas/interior.py` busca el lugar con reglas. Las operaciones se aplican a una
copia de la casa que la interfaz muestra como vista previa; el usuario la acepta o la
descarta. Mover un muro lo resuelve la interfaz con la misma operación que el editor
de planta, así arrastra los muros y ambientes conectados igual que a mano.

Sin proveedor de IA, `guion_interior()` interpreta los pedidos más comunes por palabras
clave, con el mismo contrato.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from copy import deepcopy
from typing import Literal

from pydantic import BaseModel, Field

from ..capas import interior as ci
from ..modelo.casa import USOS, MensajeChat
from .asistente import DOMINIO, USUARIO, _pedir_validado
from .proveedores import Mensaje, Proveedor


class Operacion(BaseModel):
    tipo: Literal["agregar", "quitar", "cambiar", "mover", "amoblar", "galeria", "mover_muro", "uso_ambiente"]
    codigo: str | None = Field(default=None, description="Código del catálogo (agregar, cambiar)")
    ambiente: str | None = Field(default=None, description="Id del ambiente")
    pieza: str | None = Field(default=None, description="Id de una pieza existente (quitar, cambiar, mover)")
    cantidad: int = Field(default=1, ge=1, le=8)
    lado: Literal["norte", "sur", "este", "oeste"] | None = None
    fondo_m: float | None = Field(default=None, ge=1.2, le=5)
    muro: str | None = None
    delta_m: float | None = Field(default=None, ge=-2, le=2)
    uso: str | None = None


class RespuestaInterior(BaseModel):
    mensaje: str
    operaciones: list[Operacion] = []


# ---------------------------------------------------------------- aplicar

def _buscar_pieza(casa: dict, op: Operacion) -> dict | None:
    ps = ci.piezas(casa)
    if op.pieza:
        return next((p for p in ps if p["id"] == op.pieza), None)
    if op.codigo:
        grupo = (ci.item(op.codigo) or {}).get("grupo")
        for p in ps:
            if op.ambiente and p.get("ambiente") != op.ambiente:
                continue
            it = ci.item(p.get("tipo", "")) or {}
            if p.get("tipo") == op.codigo or (grupo and it.get("grupo") == grupo):
                return p
    return None


def _sacar(casa: dict, pid: str) -> None:
    for nombre in ci.LISTAS:
        casa[nombre] = [p for p in casa.get(nombre) or [] if p["id"] != pid]


def _cambiar(casa: dict, pieza: dict, codigo: str) -> dict:
    """Cambia el modelo de una pieza conservando su espalda contra el mismo muro."""
    nuevo = ci.item(codigo)
    _, f_viejo, _ = ci.medidas(pieza)
    a, f, h = nuevo["medidas_m"]
    g = math.radians(pieza.get("giro_deg") or 0)
    fx, fy = -math.sin(g), math.cos(g)
    d = (f - f_viejo) / 2
    x, y = pieza["centro_m"]
    _sacar(casa, pieza["id"])
    p = {**pieza, "tipo": codigo, "medidas_m": [a, f, h], "centro_m": [round(x + fx * d, 3), round(y + fy * d, 3)],
         "estado": "propuesto"}
    casa.setdefault(ci.lista_de(codigo), []).append(p)
    return p


def aplicar(casa: dict, operaciones: list[Operacion], lat: float | None = None) -> tuple[dict, list[dict], list[str]]:
    """Aplica las operaciones sobre una copia. Devuelve (casa, operaciones para la interfaz, notas).
    Las de muro quedan como pendientes: la interfaz las ejecuta con su editor de planta."""
    casa = deepcopy(casa)
    pendientes: list[dict] = []
    notas: list[str] = []
    ambientes = {a["id"]: a for a in casa.get("ambientes") or []}
    for op in operaciones:
        if op.ambiente and op.ambiente not in ambientes and op.tipo not in ("galeria",):
            notas.append(f"No encontré el ambiente «{op.ambiente}».")
            continue
        if op.tipo == "agregar" and op.codigo:
            for _ in range(op.cantidad):
                destino = op.ambiente or _ambiente_sugerido(casa, op.codigo)
                if not destino:
                    notas.append(f"No sé en qué ambiente poner {op.codigo}.")
                    break
                casa, pieza, motivo = ci.colocar(casa, op.codigo, destino, origen="asistente")
                if not pieza:
                    notas.append(motivo)
                    break
        elif op.tipo == "quitar":
            p = _buscar_pieza(casa, op)
            if p:
                _sacar(casa, p["id"])
            else:
                notas.append("No encontré esa pieza para quitarla.")
        elif op.tipo == "cambiar" and op.codigo and ci.item(op.codigo):
            p = _buscar_pieza(casa, Operacion(tipo="quitar", pieza=op.pieza, ambiente=op.ambiente,
                                              codigo=op.codigo if not op.pieza else None))
            if p:
                _cambiar(casa, p, op.codigo)
            else:
                notas.append("No encontré la pieza a cambiar.")
        elif op.tipo == "mover" and op.ambiente:
            p = _buscar_pieza(casa, op)
            if not p:
                notas.append("No encontré la pieza a mover.")
                continue
            _sacar(casa, p["id"])
            casa, nueva, motivo = ci.colocar(casa, p["tipo"], op.ambiente, origen="asistente")
            if not nueva:
                notas.append(motivo)
                casa.setdefault(ci.lista_de(p["tipo"]), []).append(p)
        elif op.tipo == "amoblar":
            casa, n = ci.amoblar(casa, [op.ambiente] if op.ambiente else None, reemplazar=bool(op.ambiente))
            notas += n
        elif op.tipo == "galeria":
            casa, gid, n = ci.agregar_galeria(casa, op.lado, op.fondo_m or 3.0, lat=lat)
            notas += n
            if gid:
                casa, n = ci.amoblar(casa, [gid], reemplazar=True)
                notas += n
        elif op.tipo == "mover_muro" and op.muro and op.delta_m:
            if any(m["id"] == op.muro for m in casa.get("muros") or []):
                pendientes.append({"tipo": "mover_muro", "muro": op.muro, "delta_m": round(op.delta_m, 3)})
            else:
                notas.append(f"No encontré el muro «{op.muro}».")
        elif op.tipo == "uso_ambiente" and op.ambiente and op.uso in USOS:
            ambientes[op.ambiente]["uso"] = op.uso
    return casa, pendientes, notas


def _ambiente_sugerido(casa: dict, codigo: str) -> str | None:
    it = ci.item(codigo) or {}
    preferidos = it.get("sugerido_para") or it.get("usos") or []
    ambs = casa.get("ambientes") or []
    for uso in preferidos:
        for a in ambs:
            if a.get("uso") == uso and a.get("contorno_m"):
                return a["id"]
    for a in ambs:
        if a.get("contorno_m") and (a.get("uso") == "galeria") == bool(it.get("exterior") and not it.get("interior", True)):
            return a["id"]
    return None


# ---------------------------------------------------------------- IA

FORMATO = """Respondé SOLO con un objeto JSON:
{
  "mensaje": "qué vas a hacer, para el usuario, en 1 a 3 oraciones",
  "operaciones": [
    {"tipo": "agregar", "codigo": "escritorio", "ambiente": "oficina", "cantidad": 1},
    {"tipo": "quitar", "pieza": "id_de_la_pieza"},
    {"tipo": "cambiar", "pieza": "id_de_la_pieza", "codigo": "cama_queen"},
    {"tipo": "mover", "pieza": "id_de_la_pieza", "ambiente": "otro_ambiente"},
    {"tipo": "amoblar", "ambiente": "dorm_2"},
    {"tipo": "galeria", "lado": "norte", "fondo_m": 3},
    {"tipo": "mover_muro", "muro": "id_del_muro", "delta_m": 0.5},
    {"tipo": "uso_ambiente", "ambiente": "id", "uso": "oficina"}
  ]
}
Reglas:
- Usá solo códigos del catálogo y ids de ambientes, piezas y muros de la casa que te paso.
- No des coordenadas: el software ubica cada pieza donde entra con su espacio de uso.
- "amoblar" reemplaza los muebles del ambiente por una propuesta completa; sin "ambiente", amobla los vacíos.
- Para agrandar o achicar un ambiente, mové UNO de sus muros: delta_m positivo corre el muro hacia +X (este) o +Y (norte).
  En la lista de muros de cada ambiente, "agrandar_signo" es el signo de delta_m que lo agranda. Preferí muros con
  "vecino" interior: un muro exterior cambia la huella de la casa. Avisá qué ambiente vecino se achica.
- Si el pedido no se puede hacer, explicalo en "mensaje" y devolvé "operaciones": [].
- Si es una pregunta («¿entra una mesa para 8?»), respondé en "mensaje" y no hagas operaciones salvo que te lo pida."""


def _catalogo_para_ia() -> str:
    filas = []
    for it in ci.items_catalogo():
        a, f, h = it["medidas_m"]
        lugar = "galería" if not it.get("interior", True) else ("también galería" if it.get("exterior") else "")
        usos = ",".join(it.get("usos") or [])
        filas.append(f"{it['codigo']}: {it['nombre']} ({a:g}×{f:g} m){' · ' + lugar if lugar else ''}{' · solo ' + usos if usos else ''}")
    return "\n".join(filas)


def _sistema() -> str:
    return "\n\n".join([
        "Sos Lumo, el asistente de Assambl: una llamita índigo, simpática y siempre amable. Ahora el usuario ve su casa "
        "en 3D y te pide muebles o cambios en los espacios. Proponés; el usuario ve la vista previa y decide.",
        USUARIO, DOMINIO, "Catálogo de muebles y artefactos (código: nombre, ancho × fondo):\n" + _catalogo_para_ia(),
        FORMATO,
    ])


async def conversar(proveedor: Proveedor, casa: dict, historial: list[MensajeChat], lat: float | None = None) -> dict:
    if proveedor.simulado or not historial:
        r = guion_interior(historial[-1].texto if historial else "", casa)
    else:
        contexto = "Casa actual (JSON): " + json.dumps(ci.describir(casa), ensure_ascii=False)
        mensajes = [Mensaje(m.rol, m.texto) for m in historial]
        mensajes[-1] = Mensaje(mensajes[-1].rol, f"{mensajes[-1].texto}\n\n[{contexto}]")
        r = await _pedir_validado(proveedor, _sistema(), mensajes, RespuestaInterior)
        assert isinstance(r, RespuestaInterior)
    nueva, pendientes, notas = aplicar(casa, r.operaciones, lat)
    return {"mensaje": r.mensaje, "operaciones": [o.model_dump(exclude_none=True) for o in r.operaciones],
            "casa": nueva, "pendientes": pendientes, "notas": notas, "simulado": proveedor.simulado}


# ---------------------------------------------------------------- guion sin IA

def _plano(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t)


SINONIMOS = [
    (("tele", "tv", "televisor"), "mueble_tv"), (("sofa en l", "sillon en l", "esquinero"), "sofa_l"),
    (("sofa", "sillon grande"), "sofa_3"), (("sillon", "butaca"), "sillon"), (("ratona", "mesa baja", "mesita"), "mesa_ratona"),
    (("biblioteca",), "biblioteca"), (("estanteria", "estante"), "estanteria"), (("alfombra",), "alfombra"),
    (("planta", "maceta"), "planta"), (("lampara",), "lampara_pie"), (("mesa para 8", "mesa de 8"), "mesa_8"),
    (("mesa para 6", "mesa de 6"), "mesa_6"), (("mesa redonda",), "mesa_redonda"), (("mesa de galeria", "mesa afuera"), "mesa_exterior"),
    (("mesa", "comedor"), "mesa_4"), (("silla",), "silla"), (("aparador",), "aparador"), (("isla",), "isla"),
    (("banqueta", "taburete"), "banqueta"), (("heladera",), "heladera"), (("lavavajillas",), "lavavajillas"),
    (("alacena",), "alacena_120"), (("anafe", "horno", "cocina electrica"), "cocina_anafe"),
    (("king",), "cama_king"), (("queen",), "cama_queen"), (("cama de 2", "cama doble", "matrimonial"), "cama_2"),
    (("cama de 1", "cama individual", "cama simple"), "cama_1"), (("cama",), "cama_2"), (("mesa de luz", "mesita de luz"), "mesa_luz"),
    (("placard", "ropero", "armario"), "placard_180"), (("comoda",), "comoda"), (("cuna",), "cuna"),
    (("inodoro",), "inodoro"), (("bidet",), "bidet"), (("vanitory", "lavatorio"), "vanitory_60"), (("banera",), "banera"),
    (("ducha",), "ducha_90"), (("lavarropas",), "lavarropas"), (("secarropas",), "secarropas"),
    (("pileta",), "pileta_lavadero"), (("termotanque",), "termotanque"), (("escritorio",), "escritorio"),
    (("reposera",), "reposera"), (("parrilla", "asador"), "parrilla"), (("banco",), "banco_exterior"),
]

USO_PALABRAS = {"dormitorio": "dormitorio", "pieza": "dormitorio", "cuarto": "dormitorio", "habitacion": "dormitorio",
                "bano": "bano", "toilette": "bano", "cocina": "cocina", "estar": "social", "living": "social",
                "comedor": "social", "oficina": "oficina", "escritorio": "oficina", "lavadero": "lavadero",
                "vestidor": "vestidor", "galeria": "galeria", "deposito": "deposito"}


def _pieza_en_texto(t: str) -> str | None:
    for claves, codigo in SINONIMOS:
        if any(re.search(rf"\b{re.escape(k)}", t) for k in claves):
            return codigo
    return None


def _ambiente_en_texto(t: str, casa: dict) -> str | None:
    ambs = [a for a in casa.get("ambientes") or [] if a.get("contorno_m")]
    for a in sorted(ambs, key=lambda a: -len(a.get("nombre", ""))):
        if _plano(a.get("nombre", "")) in t or a["id"].replace("_", " ") in t:
            return a["id"]
    if "principal" in t:
        for a in ambs:
            if "principal" in a["id"] or "principal" in _plano(a.get("nombre", "")):
                return a["id"]
    for palabra, uso in USO_PALABRAS.items():
        if re.search(rf"\b{palabra}", t):
            for a in ambs:
                if a.get("uso") == uso:
                    return a["id"]
    return None


def guion_interior(texto: str, casa: dict) -> RespuestaInterior:
    t = _plano(texto)
    nombres = {a["id"]: a.get("nombre", a["id"]) for a in casa.get("ambientes") or []}
    if not t.strip():
        return RespuestaInterior(mensaje="¡Hola! Soy Lumo. Pedime muebles («sumá un escritorio en la oficina»), "
                                         "que amueble un ambiente, una galería o que agrande un espacio.")
    amb = _ambiente_en_texto(t, casa)
    codigo = _pieza_en_texto(t)

    if re.search(r"\buna galeria|\bla galeria (al|del|hacia)", t) or (
            "galeria" in t and not codigo and re.search(r"\b(arm|hac|sum|agreg|pon|quier|propon)", t)):
        lado = next((l for l in ("norte", "sur", "este", "oeste") if l in t), None)
        return RespuestaInterior(mensaje=f"Armo una galería de 3 m de fondo{' al ' + lado if lado else ' del lado del sol'}, "
                                         "con su mesa y una parrilla.", operaciones=[Operacion(tipo="galeria", lado=lado)])

    if re.search(r"\bamobl|\bamuebl|\bequip", t):
        if amb:
            return RespuestaInterior(mensaje=f"Te propongo un amoblado para «{nombres[amb]}».",
                                     operaciones=[Operacion(tipo="amoblar", ambiente=amb)])
        return RespuestaInterior(mensaje="Amoblo los ambientes que están vacíos.", operaciones=[Operacion(tipo="amoblar")])

    agrandar, achicar = re.search(r"\bagrand|\bampli|mas grande", t), re.search(r"\bachic|\breduc|mas chic", t)
    if (agrandar or achicar) and amb:
        muros = (ci.describir(casa)["ambientes"][[a["id"] for a in casa["ambientes"]].index(amb)]).get("muros") or []
        interiores = [m for m in muros if m["vecino"] not in ("exterior",)]
        m = (interiores or muros or [None])[0]
        if not m:
            return RespuestaInterior(mensaje=f"No encuentro los muros de «{nombres[amb]}».")
        signo = m["agrandar_signo"] * (1 if agrandar else -1)
        vecino = nombres.get(m["vecino"], "el exterior")
        return RespuestaInterior(
            mensaje=f"Corro el muro {m['lado']} de «{nombres[amb]}» 50 cm. "
                    + (f"«{vecino}» se {'achica' if agrandar else 'agranda'} lo mismo." if m["vecino"] != "exterior"
                       else "Cambia la huella de la casa."),
            operaciones=[Operacion(tipo="mover_muro", muro=m["muro"], delta_m=0.5 * signo)])

    if codigo and re.search(r"\b(sac|quit|borr|elimin|saca)", t):
        p = _buscar_pieza(casa, Operacion(tipo="quitar", codigo=codigo, ambiente=amb))
        if not p:
            return RespuestaInterior(mensaje="No encuentro esa pieza en la casa.")
        return RespuestaInterior(mensaje=f"Saco {ci.item(p['tipo'])['nombre'].lower() if ci.item(p['tipo']) else p['id']}.",
                                 operaciones=[Operacion(tipo="quitar", pieza=p["id"])])
    if codigo and re.search(r"\b(cambi|reemplaz)", t):
        p = _buscar_pieza(casa, Operacion(tipo="quitar", codigo=codigo, ambiente=amb))
        if p and p.get("tipo") != codigo:
            return RespuestaInterior(mensaje=f"Cambio {p['id']} por {ci.item(codigo)['nombre'].lower()}.",
                                     operaciones=[Operacion(tipo="cambiar", pieza=p["id"], codigo=codigo)])
    if codigo:
        cantidad = 1
        m = re.search(r"\b(\d|dos|tres|cuatro|cinco|seis)\b", t)
        if m and codigo in ("silla", "banqueta", "silla_exterior", "mesa_luz", "planta"):
            cantidad = {"dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6}.get(m.group(1)) or int(m.group(1))
        destino = amb or _ambiente_sugerido(casa, codigo)
        nombre = ci.item(codigo)["nombre"].lower()
        if not destino:
            return RespuestaInterior(mensaje=f"¿En qué ambiente querés {nombre}?")
        return RespuestaInterior(mensaje=f"Sumo {nombre} en «{nombres[destino]}», donde entre con su espacio de uso.",
                                 operaciones=[Operacion(tipo="agregar", codigo=codigo, ambiente=destino, cantidad=cantidad)])
    return RespuestaInterior(mensaje="En modo demostración entiendo pedidos simples: «sumá una biblioteca en el estar», "
                                     "«sacá la alfombra», «amoblá el dormitorio 2», «armá una galería al norte» o "
                                     "«agrandá el baño».")
