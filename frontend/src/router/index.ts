import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: () => import("../views/LoginView.vue") },
    { path: "/", component: () => import("../views/HomeView.vue") },
    { path: "/recipes", component: () => import("../views/RecipesView.vue") },
    { path: "/favorites", component: () => import("../views/FavoritesView.vue") },
    { path: "/records", component: () => import("../views/RecordsView.vue") },
    { path: "/goals", component: () => import("../views/GoalsView.vue") },
    { path: "/community", component: () => import("../views/CommunityView.vue") },
    { path: "/reports", component: () => import("../views/ReportsView.vue") },
    { path: "/profile", component: () => import("../views/ProfileView.vue") },
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
