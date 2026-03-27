import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import "./styles/main.css";
import App from "./App.vue";
import router from "./router";
import { useAuthStore } from "./stores/auth";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);
app.use(ElementPlus);

const auth = useAuthStore(pinia);
if (localStorage.getItem("access_token")) {
  auth.fetchMe().catch(() => {
    auth.clearAuth();
    router.push("/login");
  });
}

app.mount("#app");
