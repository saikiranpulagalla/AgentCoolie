import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const configuredApiUrl = env.VITE_API_URL?.trim();
  if (command === "build" && mode === "production" && !configuredApiUrl) {
    throw new Error("VITE_API_URL must be set for a production frontend build.");
  }
  if (command === "build" && mode === "production" && configuredApiUrl && !configuredApiUrl.startsWith("https://")) {
    throw new Error("VITE_API_URL must use https:// for a production frontend build.");
  }
  const apiUrl = configuredApiUrl || "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    define: {
      __API_URL__: JSON.stringify(apiUrl),
    },
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "client", "src"),
        "@shared": path.resolve(__dirname, "shared"),
        "@assets": path.resolve(__dirname, "attached_assets"),
      },
    },
    root: path.resolve(__dirname, "client"),
    envDir: path.resolve(__dirname),
    build: {
      outDir: path.resolve(__dirname, "dist/public"),
      emptyOutDir: true,
    },
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: apiUrl,
          changeOrigin: true,
          secure: false,
        },
      },
      fs: {
        strict: true,
        deny: ["**/.*"],
      },
    },
  };
});
