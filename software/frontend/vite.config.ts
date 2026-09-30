import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const apiPort = process.env.API_PORT || "8765";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    strictPort: true,
    // El caso Angus Ranch vive en software/casos y se importa como assambl-software/casos/…
    fs: { allow: [".."] },
    proxy: {
      "/api": { target: `http://127.0.0.1:${apiPort}`, changeOrigin: true },
    },
  },
});
