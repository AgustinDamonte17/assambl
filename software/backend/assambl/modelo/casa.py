"""Esquema de la casa (sección `casa` de casa.assambl.json, MVP_01 §4.2).

Describe lo que el usuario decide: muros, aberturas, ambientes, cubiertas,
artefactos, mobiliario e instalaciones. Las piezas (montantes, placas, pernos),
las capas de la envolvente y los cómputos NO se guardan: se derivan con reglas.

Convenciones (ver docs/modelo_de_la_casa.md):
- Metros, X este, Y norte, Z arriba. Origen en la esquina suroeste de la
  planta principal, con Z = 0 en el piso terminado.
- Los ids son estables: otras secciones y las piezas derivadas los referencian.
- Los rectángulos se escriben [x0, y0, x1, y1]; los polígonos, como lista de [x, y].
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .estados import Estado

ESQUEMA_CASA = "assambl/casa@0.1"

Punto = tuple[float, float]
Punto3 = tuple[float, float, float]
Rectangulo = tuple[float, float, float, float]
Medidas = tuple[float, float, float]
Paralela = Literal["x", "y"]


class Estricto(BaseModel):
    """Rechaza campos desconocidos: un error de tipeo no debe perderse en silencio."""

    model_config = ConfigDict(extra="forbid")


# ----------------------------------------------------------------- generales

class Regresion(Estricto):
    piezas_madera: int
    pernos_solera: int
    soleras_con_anclaje_especial: int


class Origen(Estricto):
    fuente: str
    version: str
    regresion: Regresion | None = None
    nota: str = ""


class Ejes(Estricto):
    x: Literal["este"] = "este"
    y: Literal["norte"] = "norte"
    z: Literal["arriba"] = "arriba"
    origen: str


class Implantacion(Estricto):
    """Ubica el sistema de la casa en el sistema local del terreno."""

    origen_en_lote_m: Punto
    giro_deg: float = Field(0.0, description="Giro antihorario de la casa respecto del lote")
    cota_piso_sobre_terreno_m: float = Field(ge=0.15, description="MVP_01 §3.1: platea ≥ 150 mm sobre terreno")


# ----------------------------------------------------------------- sistemas

class Capa(Estricto):
    capa: Literal["terminacion_interior", "entramado", "aislante", "osb", "wrb", "camara_ventilada", "siding"]
    material: str | None = None
    espesor_mm: float | None = None
    seccion_mm: tuple[float, float] | None = None
    modulo_mm: float | None = None
    placa_mm: tuple[float, float] | None = None
    junta_mm: float | None = None
    solape_mm: float | None = None
    retorno_esquina_mm: float | None = None
    liston_mm: tuple[float, float] | None = None
    paso_mm: float | None = None
    esquinero_mm: float | None = None
    junta_esquinero_mm: float | None = None


class Sistema(Estricto):
    """Tipo de muro: el paquete de capas que comparten todos los muros que lo usan."""

    descripcion: str
    espesor_arquitectonico_m: float = Field(gt=0)
    capas: list[Capa]
    terminacion: str | None = None

    @property
    def entramado(self) -> Capa:
        return next(c for c in self.capas if c.capa == "entramado")


class Zocalo(Estricto):
    desde_m: float
    hasta_m: float
    espesor_mm: float
    material: str


class Cielorraso(Estricto):
    cara_inferior_m: float
    espesor_m: float
    material: str
    zonas_m: list[Rectangulo]


class Parametros(Estricto):
    altura_tabiques_m: float = Field(gt=2.0)
    esquinas: str
    zocalo: Zocalo
    cielorraso: Cielorraso
    solado_general: str


# ----------------------------------------------------------------- muros

class Eje(Estricto):
    desde_m: Punto
    hasta_m: Punto

    @property
    def largo_m(self) -> float:
        return math.dist(self.desde_m, self.hasta_m)

    @property
    def paralelo_a(self) -> Paralela | None:
        (x0, y0), (x1, y1) = self.desde_m, self.hasta_m
        if abs(y1 - y0) < 1e-9:
            return "x"
        if abs(x1 - x0) < 1e-9:
            return "y"
        return None


class Altura(Estricto):
    """`tabique`: altura de parametros.altura_tabiques_m.
    `hasta_cubierta`: el muro sube hasta el plano de apoyo de esa cubierta."""

    tipo: Literal["tabique", "hasta_cubierta"]
    cubierta: str | None = None

    @model_validator(mode="after")
    def _cubierta(self):
        if (self.tipo == "hasta_cubierta") != (self.cubierta is not None):
            raise ValueError("`cubierta` va solo, y siempre, con tipo hasta_cubierta")
        return self


class Hoja(Estricto):
    bisagra: Literal["inicio", "fin"] = "inicio"
    apertura_deg: float = 70


class Abertura(Estricto):
    """Vano libre. `posicion_m` se mide sobre el eje, desde `eje.desde_m` hasta la primera jamba."""

    id: str
    tipo: Literal["ventana", "ventana_corrediza", "puerta", "paso"]
    posicion_m: float = Field(ge=0)
    ancho_m: float = Field(gt=0)
    antepecho_m: float = Field(ge=0)
    dintel_m: float = Field(gt=0)
    hoja: Hoja | None = None

    @model_validator(mode="after")
    def _coherente(self):
        if self.dintel_m <= self.antepecho_m:
            raise ValueError(f"{self.id}: el dintel queda por debajo del antepecho")
        if self.hoja is not None and self.tipo != "puerta":
            raise ValueError(f"{self.id}: solo las puertas llevan hoja")
        return self

    @property
    def fin_m(self) -> float:
        return self.posicion_m + self.ancho_m


class Muro(Estricto):
    id: str
    sistema: str
    eje: Eje
    lado_exterior: Literal["norte", "sur", "este", "oeste"] | None = None
    altura: Altura
    aberturas: list[Abertura] = []

    @model_validator(mode="after")
    def _aberturas_en_el_muro(self):
        if self.eje.paralelo_a is None:
            raise ValueError(f"{self.id}: MVP_01 §2 admite solo muros paralelos a X o a Y")
        orden = sorted(self.aberturas, key=lambda a: a.posicion_m)
        for a in orden:
            if a.fin_m > self.eje.largo_m + 1e-6:
                raise ValueError(f"{a.id}: la abertura termina fuera del muro {self.id}")
        for a, b in zip(orden, orden[1:]):
            if b.posicion_m < a.fin_m - 1e-6:
                raise ValueError(f"{a.id} y {b.id} se superponen")
        return self


# ----------------------------------------------------------------- ambientes

class Ambiente(Estricto):
    id: str
    nombre: str
    uso: Literal["dormitorio", "vestidor", "bano", "lavadero", "oficina", "social", "cocina", "circulacion"]
    contorno_m: list[Punto] | None = Field(description="Polígono interior; null si falta dibujarlo")
    solado: str
    estado: Estado = Estado.PROPUESTO
    nota: str = ""

    @model_validator(mode="after")
    def _contorno(self):
        if self.contorno_m is None and self.estado != Estado.PENDIENTE_DATOS:
            raise ValueError(f"{self.id}: sin contorno el ambiente queda pendiente_datos")
        if self.contorno_m is not None and len(self.contorno_m) < 3:
            raise ValueError(f"{self.id}: el contorno necesita al menos tres vértices")
        return self

    @property
    def humedo(self) -> bool:
        """Wet room (MVP_01 §3.13): recibe agua o desagüe."""
        return self.uso in ("bano", "lavadero", "cocina")


# ----------------------------------------------------------------- cubiertas

class PlanoApoyo(Estricto):
    """Cara inferior de los cabios y tope de los muros que llegan a esta cubierta."""

    cota_m: float
    en_m: Punto
    pendiente_pct: float = Field(ge=0)
    sube_hacia_deg: float = Field(description="Azimut hacia donde sube el plano: 0 norte, 90 este")

    def cota(self, x: float, y: float) -> float:
        az = math.radians(self.sube_hacia_deg)
        avance = (x - self.en_m[0]) * math.sin(az) + (y - self.en_m[1]) * math.cos(az)
        return self.cota_m + self.pendiente_pct / 100 * avance


class Chapa(Estricto):
    espesor_mm: float
    junta_alzada_paso_m: float | None = None


class TableroCubierta(Estricto):
    espesor_mm: float
    contorno_m: Rectangulo
    material: str


class Cabios(Estricto):
    seccion_mm: tuple[float, float]
    cantidad: int = Field(ge=2)
    desde_x_m: float
    hasta_x_m: float
    desde_y_m: float
    hasta_y_m: float


class ApoyoIntermedio(Estricto):
    tipo: Literal["viga", "viga_alta"]
    eje_y_m: float
    seccion_mm: tuple[float, float]
    largo_m: float | None = None
    postes_x_m: list[float]
    seccion_poste_mm: tuple[float, float]
    estado: Estado = Estado.PROPUESTO
    nota: str = ""


class Fascias(Estricto):
    altura_m: float
    espesor_mm: float
    material: str


class Cubierta(Estricto):
    id: str
    tipo: Literal["un_agua", "dos_aguas"]
    material: str
    plano_apoyo: PlanoApoyo
    contorno_chapa_m: Rectangulo
    chapa: Chapa
    tablero: TableroCubierta | None = None
    cabios: Cabios
    apoyos_intermedios: list[ApoyoIntermedio] = []
    fascias: Fascias | None = None
    nota: str = ""


# ----------------------------------------------------------------- cimientos

class SoleraInferior(Estricto):
    material: str
    barrera_capilar: bool


class Pernos(Estricto):
    diametro_mm: float
    empotramiento_mm: float
    separacion_max_m: float
    distancia_extremo_objetivo_m: float
    forma: Literal["L", "J"]


class BasesPostes(Estricto):
    dado_m: Medidas
    elevacion_mm: float
    tipo: str


class Cimientos(Estricto):
    tipo: Literal["platea"]
    contorno: Literal["huella"]
    espesor_m: float
    junta_bajo_solera_mm: float
    solera_inferior: SoleraInferior
    pernos: Pernos
    bases_postes: BasesPostes
    estado: Estado
    nota: str = ""


# ----------------------------------------------------------------- carpinterías

class Marco(Estricto):
    seccion_mm: tuple[float, float]
    material: str


class PuertaTipo(Estricto):
    hoja_mm: float
    material: str
    apertura_deg_por_defecto: float


class Alfeizar(Estricto):
    vuelo_m: float
    material: str


class AlturaDintel(Estricto):
    hasta_2_6_m: float
    mayor: float


class Dintel(Estricto):
    tipo: str
    altura_m: AlturaDintel
    separadores: str
    estado: Estado


class Carpinterias(Estricto):
    marco: Marco
    hojas_ventana: str
    puerta: PuertaTipo
    alfeizar: Alfeizar
    dintel: Dintel


# ----------------------------------------------------------------- equipamiento

class Elemento(Estricto):
    """Mueble o equipo apoyado: caja de `medidas_m` [ancho X, fondo Y, alto] antes de girar."""

    id: str
    tipo: str
    ambiente: str | None = None
    centro_m: Punto
    medidas_m: Medidas
    giro_deg: float = 0
    estado: Estado = Estado.PROPUESTO
    nota: str = ""


class Desague(Estricto):
    salida_m: Punto3
    dn_mm: int
    grupo: str


class Agua(Estricto):
    fria: bool
    caliente: bool


class Artefacto(Estricto):
    id: str
    tipo: Literal["inodoro", "bidet", "ducha", "vanitory", "bacha_cocina", "pileta_lavadero", "lavarropas"]
    ambiente: str
    centro_m: Punto
    giro_deg: float = 0
    medidas_m: tuple[float, float] | None = None
    desague: Desague
    agua: Agua


class Deck(Estricto):
    contorno_m: Rectangulo
    tabla_mm: tuple[float, float]
    paso_mm: float
    bastidor_alto_m: float
    material: str


class Volumen(Estricto):
    centro_m: Punto
    medidas_m: tuple[float, ...]
    material: str


class Galeria(Estricto):
    cubierta: str
    deck: Deck
    escalon: Volumen
    equipamiento: list[Elemento]


class Exteriores(Estricto):
    galeria: Galeria | None = None
    sendero_entrada: Volumen | None = None


# ----------------------------------------------------------------- instalaciones

class TableroElectrico(Estricto):
    posicion_m: Punto3
    medidas_m: Medidas
    protecciones: str


class Acometida(Estricto):
    desde_m: Punto3
    estado: Estado
    nota: str = ""


class PuestaATierra(Estricto):
    jabalina_m: Punto
    hasta_cota_m: float
    estado: Estado


class Circuito(Estricto):
    id: str
    uso: str
    seccion_mm2: float


class Toma(Estricto):
    id: str
    ambiente: str
    posicion_m: Punto3
    circuito: str
    paralela_a: Paralela


class BocaLuz(Estricto):
    id: str
    ambiente: str
    posicion_m: Punto3
    circuito: str
    luminaria: Literal["plafon", "colgante"] | None
    llave: str


class Llave(Estricto):
    id: str
    ambiente: str
    posicion_m: Punto3
    paralela_a: Paralela


class Electrica(Estricto):
    tablero: TableroElectrico
    acometida: Acometida
    puesta_a_tierra: PuestaATierra
    altura_distribucion_m: float
    circuitos: list[Circuito]
    tomas: list[Toma]
    bocas_luz: list[BocaLuz]
    llaves: list[Llave]


class Pendiente(Estricto):
    """Algo que el proyecto todavía no decidió."""

    estado: Estado
    nota: str = ""


class Columna(Estricto):
    grupo: str
    x_m: float


class Camara(Estricto):
    id: str
    x_m: float


class Salida(Estricto):
    x_m: float
    estado: Estado
    nota: str = ""


class RedDesague(Estricto):
    pendiente: float = Field(gt=0)
    colector_y_m: float
    cota_eje_inicio_m: float
    columnas: list[Columna]
    camaras_inspeccion: list[Camara]
    salida: Salida
    ventilacion: Pendiente


class Termotanque(Estricto):
    tipo: Literal["electrico", "gas", "solar"]
    capacidad_l: float
    centro_m: Punto3
    medidas_m: Medidas
    circuito: str | None = None


class RedAgua(Estricto):
    entrada_m: Punto3
    colector_m: Punto
    altura_distribucion_m: float
    llave_general_m: Punto3
    abastecimiento: Pendiente
    termotanque: Termotanque


class Sanitaria(Estricto):
    desague: RedDesague
    agua: RedAgua


class Canaleta(Estricto):
    cubierta: str
    borde: Literal["norte", "sur", "este", "oeste"]
    bajada: Literal["norte", "sur", "este", "oeste"]


class Pluvial(Estricto):
    canaletas: list[Canaleta]
    seccion_mm: tuple[float, float]
    pendiente: float
    bajada_dn_mm: int
    material: str
    destino: Pendiente


class Instalaciones(Estricto):
    electrica: Electrica
    sanitaria: Sanitaria
    pluvial: Pluvial


class Material(Estricto):
    nombre: str
    color: str = Field(pattern=r"^#[0-9a-f]{6}$")
    rugosidad: float = Field(ge=0, le=1)
    metalico: float = Field(ge=0, le=1)


# ----------------------------------------------------------------- casa

class Casa(Estricto):
    esquema: Literal["assambl/casa@0.1"] = ESQUEMA_CASA
    nombre: str
    origen: Origen | None = None
    unidades: Literal["m"] = "m"
    ejes: Ejes
    implantacion: Implantacion
    huella_m: list[Punto] = Field(description="Contorno exterior de la planta; también es el de la platea")
    sistemas: dict[str, Sistema]
    parametros: Parametros
    muros: list[Muro]
    ambientes: list[Ambiente]
    cubiertas: list[Cubierta]
    cimientos: Cimientos
    carpinterias: Carpinterias
    exteriores: Exteriores
    artefactos: list[Artefacto]
    mobiliario: list[Elemento]
    instalaciones: Instalaciones
    materiales: dict[str, Material]

    def muro(self, id: str) -> Muro:
        return next(m for m in self.muros if m.id == id)

    def cubierta(self, id: str) -> Cubierta:
        return next(c for c in self.cubiertas if c.id == id)

    def altura_muro(self, muro: Muro, x: float, y: float) -> float:
        """Tope del muro en un punto de su eje."""
        if muro.altura.tipo == "tabique":
            return self.parametros.altura_tabiques_m
        return self.cubierta(muro.altura.cubierta).plano_apoyo.cota(x, y)

    @model_validator(mode="after")
    def _referencias(self):
        """Todo id referenciado existe y todo id es único en su colección."""
        errores: list[str] = []

        def unicos(nombre: str, ids: list[str]) -> set[str]:
            vistos: set[str] = set()
            for i in ids:
                if i in vistos:
                    errores.append(f"{nombre}: id repetido {i!r}")
                vistos.add(i)
            return vistos

        cubiertas = unicos("cubiertas", [c.id for c in self.cubiertas])
        ambientes = unicos("ambientes", [a.id for a in self.ambientes])
        elec = self.instalaciones.electrica
        circuitos = unicos("circuitos", [c.id for c in elec.circuitos])
        llaves = unicos("llaves", [ll.id for ll in elec.llaves])
        unicos("muros", [m.id for m in self.muros])
        unicos("aberturas", [a.id for m in self.muros for a in m.aberturas])
        unicos("artefactos", [a.id for a in self.artefactos])
        unicos("elementos", [e.id for e in self.mobiliario + (self.exteriores.galeria.equipamiento
                                                             if self.exteriores.galeria else [])])
        unicos("bocas eléctricas", [t.id for t in elec.tomas] + [b.id for b in elec.bocas_luz])

        def existe(que: str, valor: str | None, conjunto: set[str] | dict, donde: str):
            if valor is not None and valor not in conjunto:
                errores.append(f"{donde}: {que} {valor!r} no existe")

        for m in self.muros:
            existe("sistema", m.sistema, self.sistemas, m.id)
            existe("cubierta", m.altura.cubierta, cubiertas, m.id)
            if (m.sistema == "exterior") != (m.lado_exterior is not None):
                errores.append(f"{m.id}: lado_exterior va solo, y siempre, en muros exteriores")
        for a in self.ambientes:
            existe("solado", a.solado, self.materiales, a.id)
        for e in self.mobiliario:
            existe("ambiente", e.ambiente, ambientes, e.id)
        for a in self.artefactos:
            existe("ambiente", a.ambiente, ambientes, a.id)
        for t in elec.tomas:
            existe("ambiente", t.ambiente, ambientes, t.id)
            existe("circuito", t.circuito, circuitos, t.id)
        for b in elec.bocas_luz:
            existe("ambiente", b.ambiente, ambientes, b.id)
            existe("circuito", b.circuito, circuitos, b.id)
            existe("llave", b.llave, llaves, b.id)
        for ll in elec.llaves:
            existe("ambiente", ll.ambiente, ambientes, ll.id)
        existe("circuito", self.instalaciones.sanitaria.agua.termotanque.circuito, circuitos, "termotanque")
        for c in self.instalaciones.pluvial.canaletas:
            existe("cubierta", c.cubierta, cubiertas, "canaleta")
        if self.exteriores.galeria:
            existe("cubierta", self.exteriores.galeria.cubierta, cubiertas, "galería")
        grupos = {c.grupo for c in self.instalaciones.sanitaria.desague.columnas}
        for a in self.artefactos:
            existe("grupo de desagüe", a.desague.grupo, grupos, a.id)
        for nombre, s in self.sistemas.items():
            for capa in s.capas:
                existe("material", capa.material, self.materiales, f"sistema {nombre}")
        if errores:
            raise ValueError("; ".join(errores))
        return self
