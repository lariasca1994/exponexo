import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: [
        "offline.html",
        "icono.svg",
        "icono-192.png",
        "icono-512.png",
        "apple-touch-icon.png"
      ],
      manifest: {
        name: "ExpoNexo · Plataforma de Ferias y Eventos",
        short_name: "ExpoNexo",
        description: "Reserva de stands, entradas con QR, agenda de negocios y mesa de ayuda.",
        theme_color: "#0f172a",
        background_color: "#0f172a",
        display: "standalone",
        orientation: "any",
        scope: "/",
        start_url: "/",
        categories: ["business", "events", "productivity"],
        icons: [
          {
            src: "/icono.svg",
            sizes: "any",
            type: "image/svg+xml",
            purpose: "any maskable"
          },
          {
            src: "/icono-192.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "any"
          },
          {
            src: "/icono-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any maskable"
          },
          {
            src: "/apple-touch-icon.png",
            sizes: "180x180",
            type: "image/png",
            purpose: "any"
          }
        ]
      },
      workbox: {
        // Never cache API responses with personal data; only static UI assets
        globPatterns: ["**/*.{js,css,html,svg,png,woff2}"],
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/v1\//]
      }
    })
  ],
  server: {
    port: 5173
  }
});
