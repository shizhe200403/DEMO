<template>
  <div class="shell">
    <header v-if="showChrome" class="topbar">
      <div>
        <p class="eyebrow">Nutrition OS</p>
        <h1>智能菜谱推荐与营养健康管理系统</h1>
      </div>
      <nav class="nav">
        <RouterLink to="/">首页</RouterLink>
        <RouterLink to="/recipes">菜谱</RouterLink>
        <RouterLink to="/records">记录</RouterLink>
        <RouterLink to="/community">社区</RouterLink>
        <RouterLink to="/reports">报表</RouterLink>
        <RouterLink to="/profile">我的</RouterLink>
      </nav>
      <div class="user-box">
        <span v-if="auth.user">你好，{{ auth.user?.nickname || auth.user?.username }}</span>
        <button v-if="auth.isAuthenticated" class="ghost" @click="logout">退出</button>
      </div>
    </header>

    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "./stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const showChrome = computed(() => route.path !== "/login");

function logout() {
  auth.clearAuth();
  router.push("/login");
}
</script>

<style scoped>
.shell {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(87, 181, 231, 0.18), transparent 35%),
    radial-gradient(circle at top right, rgba(34, 197, 94, 0.14), transparent 28%),
    linear-gradient(180deg, #f7fbff 0%, #eef4f8 100%);
  color: #123;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  padding: 28px 40px 18px;
}

.eyebrow {
  margin: 0 0 6px;
  font-size: 12px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #3e6d7f;
}

h1 {
  margin: 0;
  font-size: clamp(24px, 3vw, 38px);
  line-height: 1.1;
}

.nav {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
}

.nav a {
  color: #234;
  text-decoration: none;
  font-weight: 600;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(16, 34, 42, 0.08);
  backdrop-filter: blur(12px);
}

.nav a.router-link-active {
  background: #173042;
  color: #fff;
}

.user-box {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
}

.ghost {
  border: 1px solid rgba(23, 48, 66, 0.18);
  background: transparent;
  color: #173042;
  padding: 10px 14px;
  border-radius: 999px;
}

.content {
  padding: 12px 40px 40px;
}

@media (max-width: 768px) {
  .topbar,
  .content {
    padding-left: 16px;
    padding-right: 16px;
  }

  .topbar {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
