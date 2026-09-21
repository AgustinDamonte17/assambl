import type { Metadata, Viewport } from "next";
import { Archivo_Black, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const archivoBlack = Archivo_Black({
  variable: "--font-archivo-black",
  weight: "400",
  subsets: ["latin"],
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  weight: ["400", "500"],
  subsets: ["latin"],
  display: "swap",
});

const SLOGAN = "You design. Assambl solves.";

export const metadata: Metadata = {
  metadataBase: new URL("https://assambl.com"),
  title: "Assambl",
  description: SLOGAN,
  openGraph: {
    title: "Assambl",
    description: SLOGAN,
    url: "https://assambl.com",
    siteName: "Assambl",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "Assambl",
    description: SLOGAN,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#e8e6e1" },
    { media: "(prefers-color-scheme: dark)", color: "#111111" },
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${archivoBlack.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
