/** «Resolver»: qué hace Lumo con cada problema de la lista.
 *
 *  Para lo que tiene una salida clara, Lumo actúa (agrega la ventana que falta, cambia la abertura que pide
 *  cálculo). Cuando hay más de una salida razonable, pregunta con opciones que ya traen sus acciones. Y lo
 *  que no se puede decidir con reglas vuelve como `null`: se le pasa al modelo de lenguaje, como cualquier
 *  otro pedido. */

import type { Punto } from "../../modelo/proyecto";
import { buscarAbertura, esHorizontal, esVertical, espesor, type Casa, type ItemCatalogo, type VerificacionPlanta } from "../../modelo/casa";
import { murosDe, vecinosDe, type Accion } from "./acciones";

export interface OpcionLumo {
  etiqueta: string;
  detalle?: string;
  /** Lo que se ejecuta al elegirla. Sin acciones, la etiqueta se manda como texto. */
  acciones?: Accion[];
  /** Lo que dice Lumo al ejecutarla. */
  mensaje?: string;
}

export interface TurnoLumo {
  mensaje: string;
  pregunta?: { texto: string; opciones: OpcionLumo[] } | null;
  acciones?: Accion[];
}

const LUZ_MAXIMA_M = 2.4; // hasta acá el dintel sale de tabla (R03.05)
const HOLGURA_M = 0.03;

interface Zona {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  area_m2: number;
  rectangular?: boolean;
}

/** `todas` son las verificaciones del momento: un problema a veces se resuelve con lo que señala otro
 *  (el baño que falta puede ir en el espacio que quedó sin uso). */
export function resolver(casa: Casa, v: VerificacionPlanta, catalogo: ItemCatalogo[], todas: VerificacionPlanta[] = []): TurnoLumo | null {
  const amb = casa.ambientes.find((a) => v.piezas.includes(a.id));
  const libres = todas.filter((x) => x.id === "R03.15").map((x) => x.parametros as unknown as Zona).filter((z) => z.rectangular);
  switch (v.id) {
    case "R03.09":
      if (!amb) return null;
      return { mensaje: `Le agrego una ventana a «${amb.nombre}» en un muro que dé al exterior.`, acciones: [{ tipo: "agregar_abertura", ambiente: amb.id, clase: "ventana" }] };

    case "R03.10":
      if (!amb) return null;
      return { mensaje: `Le pongo una puerta a «${amb.nombre}» hacia el ambiente de paso más cercano.`, acciones: [{ tipo: "agregar_abertura", ambiente: amb.id, clase: "puerta" }] };

    case "R03.05": {
      const h = v.piezas[0] ? buscarAbertura(casa, v.piezas[0]) : null;
      if (!h) return null;
      const mejor = catalogo
        .filter((i) => i.tipo === h.abertura.tipo && i.ancho_m + HOLGURA_M <= LUZ_MAXIMA_M && i.ancho_m < h.abertura.ancho_m)
        .sort((a, b) => b.ancho_m - a.ancho_m)[0];
      if (!mejor) return null;
      return {
        mensaje: `Ese vano es más ancho de lo que resuelve la tabla de dinteles. Lo cambio por una ${mejor.nombre.toLowerCase()}, la más ancha que no necesita cálculo.`,
        acciones: [{ tipo: "cambiar_abertura", abertura: h.abertura.id, catalogo: mejor.codigo }],
      };
    }

    case "R03.04": {
      const id = v.piezas[v.piezas.length - 1];
      if (!id) return null;
      return { mensaje: "Corro la abertura hasta donde entra en su muro, sin pisar a las demás.", acciones: [{ tipo: "acomodar_abertura", abertura: id }] };
    }

    case "R03.11": {
      const opciones: OpcionLumo[] = libres
        .filter((z) => z.area_m2 <= 12)
        .slice(0, 1)
        .map((z) => ({
          etiqueta: `Hacer un baño en el espacio libre de ${z.area_m2.toFixed(0)} m²`,
          detalle: "Lo marco como baño; después le reviso la puerta y la ventana",
          acciones: [
            { tipo: "crear_ambiente" as const, contorno: hastaLasCaras(casa, z), nombre: "Baño", uso: "bano" as const },
          ],
          mensaje: "Marco ese espacio como el baño de la casa.",
        }));
      for (const bano of casa.ambientes.filter((a) => a.uso === "bano" && a.contorno_m)) {
        const destinos = new Map(vecinosDe(casa, bano).filter((x) => !["dormitorio", "vestidor", "bano"].includes(x.ambiente.uso)).map((x) => [x.ambiente.id, x.ambiente]));
        for (const d of destinos.values()) {
          opciones.push({
            etiqueta: `Abrir «${bano.nombre}» hacia «${d.nombre}»`,
            detalle: "Le sumo una puerta: lo usan el dormitorio y el resto de la casa",
            acciones: [{ tipo: "agregar_abertura", ambiente: bano.id, clase: "puerta", destino: d.id }],
            mensaje: `Le abro a «${bano.nombre}» una segunda puerta hacia «${d.nombre}».`,
          });
        }
      }
      for (const c of casa.ambientes.filter((a) => ["lavadero", "deposito", "otro"].includes(a.uso) && a.contorno_m).slice(0, 2)) {
        opciones.push({
          etiqueta: `Convertir «${c.nombre}» en baño`,
          detalle: "Cambia su nombre y su uso; después revisá su puerta y su ventana",
          acciones: [{ tipo: "renombrar", ambiente: c.id, nombre: "Baño", uso: "bano" }],
          mensaje: `Convierto «${c.nombre}» en el baño de la casa.`,
        });
      }
      if (!opciones.length) {
        return { mensaje: "A la casa le falta un baño al que se llegue sin pasar por un dormitorio, y no encuentro un ambiente para convertir. Marcá uno con la herramienta Ambiente (tecla R) y elegí el uso Baño, o deshacé el cambio que lo sacó." };
      }
      return { mensaje: "A la casa le falta un baño para todos: hoy para usarlo hay que pasar por un dormitorio.", pregunta: { texto: "¿Cómo lo resolvemos?", opciones: opciones.slice(0, 4) } };
    }

    case "R03.12": {
      const candidatos = casa.ambientes.filter((a) => ["oficina", "otro"].includes(a.uso) && a.contorno_m).slice(0, 3);
      if (!candidatos.length) return { mensaje: "La casa no tiene dormitorio y no veo un ambiente para convertir. Marcá uno con la herramienta Ambiente (tecla R) y elegí el uso Dormitorio." };
      return {
        mensaje: "La casa no tiene ningún dormitorio.",
        pregunta: {
          texto: "¿Cuál de estos ambientes pasa a ser dormitorio?",
          opciones: candidatos.map((c) => ({
            etiqueta: `«${c.nombre}»`,
            acciones: [{ tipo: "renombrar" as const, ambiente: c.id, nombre: "Dormitorio", uso: "dormitorio" as const }],
            mensaje: `«${c.nombre}» pasa a ser un dormitorio.`,
          })),
        },
      };
    }

    case "R03.13": {
      const estar = casa.ambientes.find((a) => a.uso === "social");
      if (!estar) return { mensaje: "La casa no tiene estar. Elegí el ambiente más grande y cambiale el uso a «Estar / comedor»." };
      return {
        mensaje: "No encuentro la cocina.",
        pregunta: {
          texto: "¿Dónde está?",
          opciones: [
            {
              etiqueta: `Integrada a «${estar.nombre}»`,
              detalle: "Lo renombro para que quede dicho",
              acciones: [{ tipo: "renombrar", ambiente: estar.id, nombre: `${estar.nombre} y cocina` }],
              mensaje: `Anoto que la cocina está integrada a «${estar.nombre}».`,
            },
            ...casa.ambientes
              .filter((a) => ["otro", "lavadero", "deposito"].includes(a.uso))
              .slice(0, 2)
              .map((c) => ({
                etiqueta: `Es «${c.nombre}»`,
                acciones: [{ tipo: "renombrar" as const, ambiente: c.id, nombre: "Cocina", uso: "cocina" as const }],
                mensaje: `«${c.nombre}» pasa a ser la cocina.`,
              })),
          ],
        },
      };
    }

    case "R03.14": {
      const estar = casa.ambientes.find((a) => a.uso === "social" && a.contorno_m);
      if (!estar) return null;
      const lados = [...new Set(murosDe(casa, estar).filter((t) => t.muro.sistema === "exterior").map((t) => t.lado))];
      if (!lados.length) return { mensaje: `«${estar.nombre}» no da al exterior por ningún lado: no tengo dónde poner la entrada. Agregala con la herramienta Puerta / ventana (tecla A).` };
      return {
        mensaje: "La casa no tiene puerta de entrada.",
        pregunta: {
          texto: `¿Por qué lado de «${estar.nombre}» se entra?`,
          opciones: lados.map((lado) => ({
            etiqueta: `Por el ${lado}`,
            acciones: [{ tipo: "mover_entrada" as const, lado, ambiente: estar.id }],
            mensaje: `Pongo la entrada del lado ${lado}.`,
          })),
        },
      };
    }

    case "R03.15": {
      const z = v.parametros as unknown as Zona;
      if (!z.rectangular) return { mensaje: "Ese espacio no es un rectángulo, así que no lo puedo marcar yo. Usá la herramienta Ambiente (tecla R) para marcarlo y darle un uso." };
      return {
        mensaje: `Marco ese espacio de ${z.area_m2.toFixed(0)} m² como un ambiente para que le des un uso. Si preferís sumarlo a un vecino, elegilo y usá «Integrar con».`,
        acciones: [{ tipo: "crear_ambiente", contorno: hastaLasCaras(casa, z), nombre: "Ambiente nuevo", uso: "otro" }],
      };
    }
  }
  return null;
}

/** La zona libre llega hasta el contorno de los vecinos, del otro lado de los muros: se la trae a la cara
 *  interior de los muros que la rodean. */
function hastaLasCaras(casa: Casa, z: Zona): Punto[] {
  const cara = (vertical: boolean, borde: number, a: number, b: number, haciaAdentro: number): number => {
    let mejor = borde;
    let distancia = 0.3;
    for (const m of casa.muros) {
      if (vertical ? !esVertical(m) : !esHorizontal(m)) continue;
      const fijo = vertical ? m.eje.desde_m[0] : m.eje.desde_m[1];
      const ini = vertical ? m.eje.desde_m[1] : m.eje.desde_m[0];
      const fin = vertical ? m.eje.hasta_m[1] : m.eje.hasta_m[0];
      if (Math.min(b, Math.max(ini, fin)) - Math.max(a, Math.min(ini, fin)) <= 0.3) continue;
      const d = Math.abs(fijo - borde);
      if (d < distancia) {
        distancia = d;
        mejor = fijo + (haciaAdentro * espesor(casa, m.sistema)) / 2;
      }
    }
    return Math.round(mejor * 200) / 200;
  };
  const x0 = cara(true, z.x0, z.y0, z.y1, 1);
  const x1 = cara(true, z.x1, z.y0, z.y1, -1);
  const y0 = cara(false, z.y0, z.x0, z.x1, 1);
  const y1 = cara(false, z.y1, z.x0, z.x1, -1);
  return [
    [x0, y0],
    [x1, y0],
    [x1, y1],
    [x0, y1],
  ];
}
