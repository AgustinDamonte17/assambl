"""Proveedores de IA intercambiables.

Todo el producto habla con la IA a través de una sola operación:
`completar_json(sistema, mensajes, imagenes)` → texto JSON. Lo que cambia entre
prestadores es el transporte, no los prompts ni la validación, que viven en
`asistente.py`. Para cambiar de prestador alcanza con el `.env`:

    IA_PROVEEDOR=openai            # openai | anthropic | simulado (vacío: el primero con clave)
    IA_MODELO=gpt-5-mini           # opcional; cada proveedor tiene su valor por defecto
    OPENAI_API_KEY=sk-...
    ANTHROPIC_API_KEY=sk-ant-...

`openai` habla el protocolo de Chat Completions, que también ofrecen OpenRouter,
Groq, DeepSeek, Mistral, Together, Ollama o LM Studio: con `IA_URL_BASE` e
`IA_API_KEY` se apunta a cualquiera de ellos sin tocar código.

`simulado` no sale a internet. Sigue un guion fijo y sirve para desarrollar la
interfaz, correr las pruebas y usar Assambl sin clave; la interfaz lo muestra.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import httpx

from .. import config


class ErrorIA(RuntimeError):
    """Falla del proveedor con un mensaje que se puede mostrar al usuario."""


@dataclass
class Imagen:
    datos_base64: str
    media_type: str = "image/png"

    @classmethod
    def desde_data_url(cls, url: str) -> "Imagen":
        m = re.match(r"data:(image/[\w.+-]+);base64,(.*)", url, re.S)
        if not m:
            raise ErrorIA("La imagen debe llegar como data URL en base64")
        return cls(datos_base64=m.group(2), media_type=m.group(1))


@dataclass
class Mensaje:
    rol: str  # "usuario" | "asistente"
    texto: str


class Proveedor:
    nombre = "base"
    vision = False
    simulado = False

    def __init__(self, modelo: str):
        self.modelo = modelo

    async def completar_json(self, sistema: str, mensajes: list[Mensaje], imagenes: list[Imagen] | None = None,
                             esfuerzo: str = "bajo") -> str:
        raise NotImplementedError

    def describir(self) -> dict:
        return {"proveedor": self.nombre, "modelo": self.modelo, "vision": self.vision, "simulado": self.simulado}


class ProveedorSimulado(Proveedor):
    nombre = "simulado"
    vision = True  # devuelve una lectura de demostración, marcada como tal
    simulado = True

    def __init__(self, motivo: str = ""):
        super().__init__("guion-local")
        self.motivo = motivo

    async def completar_json(self, *a, **k) -> str:  # pragma: no cover - el asistente no lo llama
        raise ErrorIA("El proveedor simulado no completa texto; lo resuelve el guion local")

    def describir(self) -> dict:
        return {**super().describir(), "motivo": self.motivo}


class ProveedorOpenAI(Proveedor):
    """Chat Completions (OpenAI y compatibles) con salida en modo JSON."""

    nombre = "openai"
    vision = True

    def __init__(self, modelo: str, clave: str, url_base: str, timeout_s: float = 120.0):
        super().__init__(modelo)
        self.clave = clave
        self.url_base = url_base.rstrip("/")
        self.timeout_s = timeout_s

    def describir(self) -> dict:
        d = super().describir()
        if "api.openai.com" not in self.url_base:
            d["url_base"] = self.url_base
        return d

    async def completar_json(self, sistema, mensajes, imagenes=None, esfuerzo="bajo") -> str:
        msgs: list[dict] = [{"role": "system", "content": sistema}]
        for i, m in enumerate(mensajes):
            rol = "user" if m.rol == "usuario" else "assistant"
            ultimo = i == len(mensajes) - 1
            if ultimo and imagenes and rol == "user":
                partes: list[dict] = [
                    {"type": "image_url", "image_url": {"url": f"data:{im.media_type};base64,{im.datos_base64}"}}
                    for im in imagenes
                ]
                partes.append({"type": "text", "text": m.texto})
                msgs.append({"role": rol, "content": partes})
            else:
                msgs.append({"role": rol, "content": m.texto})
        cuerpo: dict = {"model": self.modelo, "messages": msgs, "response_format": {"type": "json_object"}}
        if re.match(r"^(gpt-5|o\d)", self.modelo):  # modelos con razonamiento
            cuerpo["reasoning_effort"] = {"bajo": "low", "medio": "medium", "alto": "high"}.get(esfuerzo, "low")
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as c:
                r = await c.post(f"{self.url_base}/chat/completions", json=cuerpo,
                                 headers={"Authorization": f"Bearer {self.clave}"})
        except httpx.HTTPError as e:
            raise ErrorIA(f"No se pudo contactar al proveedor de IA ({self.nombre}): {e}") from e
        if r.status_code == 401:
            raise ErrorIA("La clave de OpenAI no es válida (401). Revisá OPENAI_API_KEY en el .env.")
        if r.status_code == 429:
            raise ErrorIA("El proveedor de IA limitó los pedidos o no tiene crédito (429). Probá en un rato.")
        if r.status_code >= 400:
            raise ErrorIA(f"El proveedor de IA respondió {r.status_code}: {r.text[:300]}")
        datos = r.json()
        try:
            eleccion = datos["choices"][0]
            if eleccion.get("finish_reason") == "content_filter":
                raise ErrorIA("El proveedor de IA rechazó el pedido por su filtro de contenido.")
            return eleccion["message"]["content"] or ""
        except (KeyError, IndexError) as e:
            raise ErrorIA(f"Respuesta inesperada del proveedor de IA: {str(datos)[:300]}") from e


class ProveedorAnthropic(Proveedor):
    """Claude a través del SDK oficial `anthropic`."""

    nombre = "anthropic"
    vision = True

    def __init__(self, modelo: str, clave: str, timeout_s: float = 180.0):
        super().__init__(modelo)
        try:
            import anthropic  # noqa: F401
        except ImportError as e:  # pragma: no cover - depende del entorno
            raise ErrorIA("Falta el paquete `anthropic`: pip install -r requirements.txt") from e
        self.clave = clave
        self.timeout_s = timeout_s

    async def completar_json(self, sistema, mensajes, imagenes=None, esfuerzo="bajo") -> str:
        import anthropic

        msgs: list[dict] = []
        for i, m in enumerate(mensajes):
            rol = "user" if m.rol == "usuario" else "assistant"
            if i == len(mensajes) - 1 and imagenes and rol == "user":
                partes: list[dict] = [
                    {"type": "image", "source": {"type": "base64", "media_type": im.media_type, "data": im.datos_base64}}
                    for im in imagenes
                ]
                partes.append({"type": "text", "text": m.texto})
                msgs.append({"role": rol, "content": partes})
            else:
                msgs.append({"role": rol, "content": m.texto})
        cliente = anthropic.AsyncAnthropic(api_key=self.clave, timeout=self.timeout_s)
        try:
            # Si un clasificador de seguridad rechaza el pedido, la API lo reintenta
            # sola en otro modelo (fallbacks del lado del servidor).
            r = await cliente.beta.messages.create(
                model=self.modelo,
                max_tokens=16000,
                system=sistema,
                messages=msgs,
                betas=["server-side-fallback-2026-07-01"],
                extra_body={
                    "output_config": {"effort": {"bajo": "low", "medio": "medium", "alto": "high"}.get(esfuerzo, "low")},
                    "fallbacks": "default",
                },
            )
        except anthropic.AuthenticationError as e:
            raise ErrorIA("La clave de Anthropic no es válida. Revisá ANTHROPIC_API_KEY en el .env.") from e
        except anthropic.RateLimitError as e:
            raise ErrorIA("Anthropic limitó los pedidos (429). Probá en un rato.") from e
        except anthropic.APIStatusError as e:
            raise ErrorIA(f"Anthropic respondió {e.status_code}: {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise ErrorIA(f"No se pudo contactar a Anthropic: {e}") from e
        if r.stop_reason == "refusal":
            raise ErrorIA("El modelo rechazó el pedido.")
        return "".join(b.text for b in r.content if b.type == "text")


MODELO_POR_DEFECTO = {"openai": "gpt-5-mini", "anthropic": "claude-opus-5-5"}


def obtener() -> Proveedor:
    """Proveedor configurado. Sin clave válida, el simulado (y dice por qué)."""
    elegido = config.variable("IA_PROVEEDOR").strip().lower()
    clave_openai = (config.variable("IA_API_KEY") or config.variable("OPENAI_API_KEY")).strip()
    clave_anthropic = config.variable("ANTHROPIC_API_KEY").strip()
    if not elegido:
        elegido = "openai" if clave_openai else "anthropic" if clave_anthropic else "simulado"
    modelo = config.variable("IA_MODELO").strip()

    if elegido == "openai":
        if not clave_openai:
            return ProveedorSimulado("IA_PROVEEDOR=openai pero falta OPENAI_API_KEY en el .env")
        url = config.variable("IA_URL_BASE").strip() or "https://api.openai.com/v1"
        return ProveedorOpenAI(modelo or MODELO_POR_DEFECTO["openai"], clave_openai, url)
    if elegido == "anthropic":
        if not clave_anthropic:
            return ProveedorSimulado("IA_PROVEEDOR=anthropic pero falta ANTHROPIC_API_KEY en el .env")
        return ProveedorAnthropic(modelo or MODELO_POR_DEFECTO["anthropic"], clave_anthropic)
    if elegido == "simulado":
        return ProveedorSimulado("IA_PROVEEDOR=simulado" if config.variable("IA_PROVEEDOR") else "No hay clave de IA en el .env")
    return ProveedorSimulado(f"Proveedor desconocido «{elegido}»: se usa el simulado")


def extraer_json(texto: str) -> dict:
    """Toma el primer objeto JSON del texto, tolerando cercos de código."""
    t = texto.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        ini, fin = t.find("{"), t.rfind("}")
        if ini >= 0 and fin > ini:
            return json.loads(t[ini:fin + 1])
        raise
