import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import AutoImport from "unplugin-auto-import/vite";
import Components from "unplugin-vue-components/vite";
import { ElementPlusResolver } from "unplugin-vue-components/resolvers";

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      dts: false,
      imports: ["vue", "vue-router", "pinia"],
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      dts: false,
      resolvers: [ElementPlusResolver({ importStyle: "css" })],
    }),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return;
          }
          if (id.includes("element-plus/es/components/")) {
            const chunkName = id.split("element-plus/es/components/")[1]?.split("/")[0];
            if (chunkName) {
              return `ep-${chunkName}`;
            }
          }
          if (id.includes("element-plus")) {
            return "ep-shared";
          }
          if (id.includes("vue") || id.includes("pinia") || id.includes("vue-router")) {
            return "vue-core";
          }
          if (id.includes("axios")) {
            return "network";
          }
          return "vendor";
        },
      },
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
  },
});
