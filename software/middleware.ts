// Acceso de prueba en Vercel: nada de la app ni de la API se sirve sin iniciar sesión en /acceso.
// Las credenciales salen de las variables de entorno ACCESO_USUARIO y ACCESO_CLAVE del proyecto en Vercel.
// Sin ellas definidas el sitio queda cerrado, para no publicarlo abierto por olvido.
//
// La sesión es una cookie con una firma HMAC del usuario hecha con la clave: no guarda la contraseña y
// cambiar ACCESO_CLAVE cierra todas las sesiones abiertas.

export const config = { matcher: "/:path*" };

const COOKIE = "assambl_acceso";
const DURACION_S = 60 * 60 * 24 * 30;
// Lo que la portada necesita antes de entrar.
const PUBLICAS = new Set(["/acceso.html", "/icon.svg"]);

function iguales(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diferencia = 0;
  for (let i = 0; i < a.length; i++) diferencia |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diferencia === 0;
}

async function firma(usuario: string, clave: string): Promise<string> {
  const llave = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(clave),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const bytes = new Uint8Array(await crypto.subtle.sign("HMAC", llave, new TextEncoder().encode(usuario)));
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

function leerCookie(request: Request, nombre: string): string {
  for (const parte of (request.headers.get("cookie") ?? "").split(";")) {
    const [k, ...v] = parte.trim().split("=");
    if (k === nombre) return v.join("=");
  }
  return "";
}

// Solo rutas propias: evita que «siguiente» mande a otro sitio.
function destinoSeguro(valor: string | null): string {
  return valor && valor.startsWith("/") && !valor.startsWith("//") && !valor.startsWith("/acceso") ? valor : "/";
}

function redirigir(destino: string, extra: Record<string, string> = {}): Response {
  return new Response(null, { status: 303, headers: { Location: destino, ...extra } });
}

export default async function middleware(request: Request): Promise<Response | undefined> {
  const usuario = process.env.ACCESO_USUARIO;
  const clave = process.env.ACCESO_CLAVE;
  if (!usuario || !clave) {
    return new Response("Acceso no configurado", { status: 503 });
  }

  const url = new URL(request.url);
  const ruta = url.pathname;
  if (PUBLICAS.has(ruta)) return undefined;

  if (ruta === "/acceso" && request.method === "POST") {
    const datos = await request.formData();
    const siguiente = destinoSeguro(datos.get("siguiente")?.toString() ?? null);
    const ok =
      iguales(datos.get("usuario")?.toString() ?? "", usuario) && iguales(datos.get("clave")?.toString() ?? "", clave);
    if (!ok) return redirigir(`/acceso?error=1&siguiente=${encodeURIComponent(siguiente)}`);
    const cookie = `${COOKIE}=${await firma(usuario, clave)}; Path=/; Max-Age=${DURACION_S}; HttpOnly; Secure; SameSite=Lax`;
    return redirigir(siguiente, { "Set-Cookie": cookie });
  }

  if (ruta === "/salir") {
    return redirigir("/acceso", { "Set-Cookie": `${COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax` });
  }

  const sesion = iguales(leerCookie(request, COOKIE), await firma(usuario, clave));
  if (ruta === "/acceso") {
    // Con sesión, la portada no tiene sentido: directo a la app. Sin sesión, vercel.json la sirve.
    return sesion ? redirigir(destinoSeguro(url.searchParams.get("siguiente"))) : undefined;
  }
  if (sesion) return undefined;

  if (ruta.startsWith("/api/")) {
    return Response.json({ detail: "Se necesita iniciar sesión" }, { status: 401 });
  }
  return redirigir(`/acceso?siguiente=${encodeURIComponent(ruta + url.search)}`);
}
