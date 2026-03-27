import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import RecipesView from "../views/RecipesView.vue";
import RecordsView from "../views/RecordsView.vue";
import ProfileView from "../views/ProfileView.vue";
import CommunityView from "../views/CommunityView.vue";
import ReportsView from "../views/ReportsView.vue";
import LoginView from "../views/LoginView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: LoginView },
    { path: "/", component: HomeView },
    { path: "/recipes", component: RecipesView },
    { path: "/records", component: RecordsView },
    { path: "/community", component: CommunityView },
    { path: "/reports", component: ReportsView },
    { path: "/profile", component: ProfileView },
  ],
});

router.beforeEach((to) => {
  const token = localStorage.getItem("access_token");
  if (!token && to.path !== "/login") {
    return "/login";
  }
  if (token && to.path === "/login") {
    return "/";
  }
  return true;
});

export default router;
