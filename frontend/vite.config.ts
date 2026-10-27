import { readdirSync } from "node:fs";
import { resolve } from "node:path";
import { defineConfig } from "vite";

const root = resolve(__dirname, "src");
const templates = resolve(root, "templates");

// Cada .html de templates/ vira uma pagina do build (site multi-pagina, sem SPA)
const paginas = Object.fromEntries(
    readdirSync(templates)
        .filter((arquivo) => arquivo.endsWith(".html"))
        .map((arquivo) => [arquivo.replace(".html", ""), resolve(templates, arquivo)]),
);

export default defineConfig({
    root,
    server: {
        port: 5173,
        open: "/templates/index.html",
        // O front chama /api/...; o proxy repassa ao FastAPI sem precisar de CORS
        proxy: {
            "/api": {
                target: process.env.API_TARGET ?? "http://localhost:8000",
                changeOrigin: true,
                rewrite: (caminho) => caminho.replace(/^\/api/, ""),
            },
        },
    },
    build: {
        outDir: resolve(__dirname, "dist"),
        emptyOutDir: true,
        rollupOptions: { input: paginas },
    },
});
