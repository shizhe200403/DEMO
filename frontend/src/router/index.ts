import { createRouter, createWebHistory } from "vue-router";
import { canAccessOpsScope, hasOpsAccess, readStoredOpsIdentity, resolveOpsHome, type OpsScope } from "../lib/opsAccess";

function resolveDefaultRoute() {
  return resolveOpsHome(readStoredOpsIdentity());
}

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
    { path: "/users/:userId", component: () => import("../views/PublicUserProfileView.vue") },
    { path: "/assistant", component: () => import("../views/AssistantView.vue") },
    { path: "/pricing", component: () => import("../views/PricingView.vue") },
    { path: "/payment/result", component: () => import("../views/PaymentResultView.vue") },
    { path: "/ops", component: () => import("../views/AdminDashboardView.vue"), meta: { opsScope: "manager" } },
    { path: "/ops/community", component: () => import("../views/AdminCommunityView.vue"), meta: { opsScope: "operator" } },
    { path: "/ops/logs", component: () => import("../views/AdminOperationLogsView.vue"), meta: { opsScope: "operator" } },
    { path: "/ops/reports", component: () => import("../views/AdminOpsReportsView.vue"), meta: { opsScope: "operator" } },
    { path: "/ops/recipes", component: () => import("../views/AdminRecipesView.vue"), meta: { opsScope: "operator" } },
    { path: "/ops/users", component: () => import("../views/AdminUsersView.vue"), meta: { opsScope: "manager" } },
  ],
});

router.beforeEach((to) => {
  const token = localStorage.getItem("access_token");
  if (!token && to.path !== "/login") {
    return "/login";
  }
  if (token && to.path === "/login") {
    return resolveDefaultRoute();
  }

  const requiredScope = to.meta.opsScope as OpsScope | undefined;
  if (requiredScope) {
    const identity = readStoredOpsIdentity();
    if (!hasOpsAccess(identity)) {
      return "/";
    }
    if (!canAccessOpsScope(identity, requiredScope)) {
      return resolveOpsHome(identity);
    }
  }

  return true;
});

export default router;
