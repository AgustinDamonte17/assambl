// Acceso de prueba en Vercel: pide usuario y contraseña (Basic Auth) antes de servir la app o la API.
// Las credenciales salen de las variables de entorno ACCESO_USUARIO y ACCESO_CLAVE del proyecto en Vercel.
// Sin ellas definidas el sitio queda cerrado, para no publicarlo abierto por olvido.

export const config = { matcher: "/:path*" };

function iguales(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diferencia = 0;
  for (let i = 0; i < a.length; i++) diferencia |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diferencia === 0;
}

export default function middleware(request: Request): Response | undefined {
  const usuario = process.env.ACCESO_USUARIO;
  const clave = process.env.ACCESO_CLAVE;
  if (!usuario || !clave) {
    return new Response("Acceso no configurado", { status: 503 });
  }

  const encabezado = request.headers.get("authorization") ?? "";
  const [esquema, codificado] = encabezado.split(" ");
  if (esquema === "Basic" && codificado) {
    try {
      const [u, ...resto] = atob(codificado).split(":");
      if (iguales(u, usuario) && iguales(resto.join(":"), clave)) return undefined;
    } catch {
      // Encabezado mal formado: se trata como credencial inválida.
    }
  }

  return new Response("Se necesita usuario y contraseña", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Assambl", charset="UTF-8"' },
  });
}
