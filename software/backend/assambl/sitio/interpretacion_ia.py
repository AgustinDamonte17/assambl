"""Interpretación de la imagen del lote con un modelo de visión (Claude). Opcional.

La detección por color (`vegetacion.py`) encuentra copas, pero confunde un cerco
vivo con árboles sueltos, no ve construcciones sin mapear y no distingue un
árbol de un arbusto. Un modelo de visión sí, que es lo que hace a mano quien mira
la foto. Se usa solo sobre el recorte del lote, donde importa la definición, y
con estas reglas para gastar pocos tokens (docs/decisiones/0004 y 0005):

- una imagen por lote y ningún texto de proyecto más que el necesario;
- salida estructurada (JSON validado), sin prosa;
- resultado guardado por el hash de la imagen: la misma foto no se paga dos veces.

Si no hay ANTHROPIC_API_KEY, si se desactiva con ASSAMBL_IA=0 o si la llamada
falla, se devuelve None y el modelo del sitio usa la detección por color.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
from dataclasses import dataclass

from PIL import Image, ImageDraw
from pydantic import BaseModel

from ..config import carpeta_cache, variable
from ..fuentes.imagen_satelital import Ortofoto
from .vegetacion import Arbol

MODELO_POR_DEFECTO = "claude-opus-5"
VERSION_PROMPT = "sitio-ia@1"
LADO_MAX_PX = 1568
FUENTE = "interpretación de la imagen con IA"

INSTRUCCIONES = """Sos un asistente que interpreta imágenes satelitales para un software de arquitectura.
La imagen es una vista cenital, norte arriba, de un lote y su borde inmediato. El contorno del lote está
dibujado con una línea magenta fina. Cada píxel mide {m_px:.3f} m.

Identificá, en coordenadas de píxel de ESTA imagen (origen arriba a la izquierda):
1. Cada árbol: el centro de la copa y su radio. No confundas la sombra de un árbol con otra copa: la sombra es
   oscura y sin textura de follaje. Un grupo de copas que se tocan son varios árboles si se distinguen centros.
   Estimá la altura en metros por el tamaño de la copa y el largo de la sombra, si se ve.
2. Cada construcción (casa, galpón, tinglado, pileta): su contorno como polígono y una altura estimada.
No incluyas calles, caminos ni cercos. Si algo es dudoso, no lo incluyas."""


class PuntoIA(BaseModel):
    x_px: float
    y_px: float


class ArbolIA(BaseModel):
    x_px: float
    y_px: float
    radio_px: float
    altura_m: float


class ConstruccionIA(BaseModel):
    tipo: str
    contorno: list[PuntoIA]
    altura_m: float


class InterpretacionIA(BaseModel):
    arboles: list[ArbolIA]
    construcciones: list[ConstruccionIA]
    observaciones: str


@dataclass
class ConstruccionDetectada:
    contorno: list[tuple[float, float]]
    altura_m: float
    tipo: str


@dataclass
class ResultadoIA:
    arboles: list[Arbol]
    construcciones: list[ConstruccionDetectada]
    observaciones: str
    modelo: str
    desde_cache: bool


def disponible() -> bool:
    return bool(variable("ANTHROPIC_API_KEY")) and variable("ASSAMBL_IA", "1") not in ("0", "false", "no")


def _imagen_para_enviar(orto: Ortofoto, lote: list[tuple[float, float]]) -> tuple[bytes, float]:
    """JPEG con el contorno del lote dibujado. Devuelve también la escala aplicada."""
    img = Image.fromarray(orto.rgb)
    escala = min(1.0, LADO_MAX_PX / max(img.size))
    if escala < 1.0:
        img = img.resize((round(img.width * escala), round(img.height * escala)), Image.LANCZOS)
    if len(lote) >= 3:
        cols, filas = orto.a_pixel([p[0] for p in lote], [p[1] for p in lote])
        puntos = [(float(c) * escala, float(f) * escala) for c, f in zip(cols, filas)]
        ImageDraw.Draw(img).line(puntos + puntos[:1], fill=(255, 0, 255), width=2)
    salida = io.BytesIO()
    img.save(salida, format="JPEG", quality=88)
    return salida.getvalue(), escala


async def interpretar(orto: Ortofoto, lote: list[tuple[float, float]]) -> ResultadoIA | None:
    if not disponible():
        return None
    modelo = variable("ASSAMBL_MODELO_IA", MODELO_POR_DEFECTO)
    jpeg, escala = _imagen_para_enviar(orto, lote)
    m_px = orto.m_px / escala
    clave = hashlib.sha256(jpeg + VERSION_PROMPT.encode() + modelo.encode()).hexdigest()[:24]
    ruta = carpeta_cache("ia") / f"{clave}.json"

    desde_cache = ruta.exists()
    if desde_cache:
        datos = InterpretacionIA.model_validate_json(ruta.read_text(encoding="utf-8"))
    else:
        try:
            import anthropic

            cliente = anthropic.AsyncAnthropic(api_key=variable("ANTHROPIC_API_KEY"))
            respuesta = await cliente.messages.parse(
                model=modelo,
                max_tokens=16000,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                     "data": base64.standard_b64encode(jpeg).decode()}},
                        {"type": "text", "text": INSTRUCCIONES.format(m_px=m_px)},
                    ],
                }],
                output_format=InterpretacionIA,
            )
        except Exception:  # sin red, clave inválida, límite de uso: se sigue sin IA
            return None
        if respuesta.stop_reason == "refusal" or respuesta.parsed_output is None:
            return None
        datos = respuesta.parsed_output
        ruta.write_text(datos.model_dump_json(), encoding="utf-8")

    def a_local(px: float, py: float) -> tuple[float, float]:
        x, y = orto.a_local(px / escala, py / escala)
        return float(x), float(y)

    arboles = []
    for a in datos.arboles:
        if a.radio_px <= 0:
            continue
        x, y = a_local(a.x_px, a.y_px)
        radio = a.radio_px * m_px
        altura = a.altura_m if 1.0 <= a.altura_m <= 40.0 else None
        arboles.append(Arbol(x, y, radio, altura or 1.6 * radio + 2.0, FUENTE, altura_supuesta=altura is None))
    construcciones = [
        ConstruccionDetectada([a_local(p.x_px, p.y_px) for p in c.contorno], c.altura_m if c.altura_m > 0 else 3.0,
                              c.tipo)
        for c in datos.construcciones if len(c.contorno) >= 3
    ]
    return ResultadoIA(arboles, construcciones, datos.observaciones, modelo, desde_cache)


def guardar_para_prueba(orto: Ortofoto, lote: list[tuple[float, float]], datos: InterpretacionIA) -> None:
    """Deja en la caché una respuesta como si la hubiera dado el modelo (solo pruebas)."""
    modelo = variable("ASSAMBL_MODELO_IA", MODELO_POR_DEFECTO)
    jpeg, _ = _imagen_para_enviar(orto, lote)
    clave = hashlib.sha256(jpeg + VERSION_PROMPT.encode() + modelo.encode()).hexdigest()[:24]
    (carpeta_cache("ia") / f"{clave}.json").write_text(json.dumps(datos.model_dump()), encoding="utf-8")
