import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
// Dev: `npm run dev` proxies /api to `wrangler pages dev` on :8788.
export default defineConfig({ plugins: [svelte()], server: { proxy: { "/api": "http://127.0.0.1:8788" } } });
