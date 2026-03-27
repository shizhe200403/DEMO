<template>
  <div class="shell">
    <template v-if="showChrome">
      <header class="topbar desktop-only">
        <div class="brand">
          <p class="eyebrow">每日饮食</p>
          <h1>饮食管理助手</h1>
          <p class="subtitle">记录饮食、查看推荐、追踪趋势，让每天吃什么更轻松、更有方向。</p>
        </div>
        <nav class="nav" aria-label="主导航">
          <RouterLink v-for="item in primaryNavItems" :key="item.to" :to="item.to">{{ item.label }}</RouterLink>
        </nav>
        <div class="user-box">
          <span v-if="auth.user">你好，{{ auth.user?.nickname || auth.user?.username }}</span>
          <button v-if="auth.isAuthenticated" class="ghost" @click="logout">退出</button>
        </div>
      </header>

      <header class="mobile-topbar mobile-only">
        <div>
          <p class="mobile-eyebrow">每日饮食</p>
          <strong>{{ currentTitle }}</strong>
        </div>
        <button class="ghost" type="button" @click="mobileMoreOpen = true">{{ auth.user?.nickname || "菜单" }}</button>
      </header>
    </template>

    <main class="content" :class="{ 'with-mobile-nav': showChrome }">
      <div class="content-inner">
        <RouterView v-slot="{ Component, route: currentRoute }">
          <Transition name="route-shell" mode="out-in">
            <component :is="Component" :key="currentRoute.path" />
          </Transition>
        </RouterView>
      </div>
    </main>

    <nav v-if="showChrome" class="mobile-bottom-nav mobile-only" aria-label="移动端快捷导航">
      <RouterLink v-for="item in mobileNavItems" :key="item.to" :to="item.to" class="mobile-nav-link">
        <span class="mobile-nav-icon">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </RouterLink>
      <button class="mobile-nav-link more-link" :class="{ active: moreLinkActive }" type="button" @click="mobileMoreOpen = true">
        <span class="mobile-nav-icon">···</span>
        <span>更多</span>
      </button>
    </nav>

    <div v-if="showChrome && mobileMoreOpen" class="mobile-sheet-mask mobile-only" @click="mobileMoreOpen = false" />
    <aside v-if="showChrome" class="mobile-sheet mobile-only" :class="{ open: mobileMoreOpen }" aria-label="更多导航">
      <div class="sheet-head">
        <div>
          <p class="mobile-eyebrow">快捷入口</p>
          <strong>{{ auth.user?.nickname || auth.user?.username || "当前账号" }}</strong>
        </div>
        <button class="ghost" type="button" @click="mobileMoreOpen = false">关闭</button>
      </div>
      <div class="sheet-links">
        <RouterLink v-for="item in secondaryNavItems" :key="item.to" :to="item.to" @click="mobileMoreOpen = false">
          <span>{{ item.label }}</span>
          <small>{{ item.copy }}</small>
        </RouterLink>
      </div>
      <button v-if="auth.isAuthenticated" class="sheet-logout" type="button" @click="handleMobileLogout">退出登录</button>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "./stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const mobileMoreOpen = ref(false);

const navItems = [
  { to: "/", label: "首页", icon: "首", copy: "查看今天的进度与下一步" },
  { to: "/recipes", label: "菜谱", icon: "谱", copy: "按场景快速挑选可执行菜谱" },
  { to: "/favorites", label: "收藏", icon: "藏", copy: "回到已经沉淀下来的常用选择" },
  { to: "/records", label: "记录", icon: "记", copy: "记录今天这一餐并追踪趋势" },
  { to: "/goals", label: "目标", icon: "标", copy: "管理重点目标与阶段进展" },
  { to: "/community", label: "社区", icon: "社", copy: "查看经验内容与互动反馈" },
  { to: "/reports", label: "报表", icon: "报", copy: "生成周报和月报并做复盘" },
  { to: "/profile", label: "我的", icon: "我", copy: "维护账号资料与健康档案" },
];

const showChrome = computed(() => route.path !== "/login");
const primaryNavItems = computed(() => navItems);
const mobileNavItems = computed(() => navItems.filter((item) => ["/", "/records", "/reports"].includes(item.to)));
const secondaryNavItems = computed(() => navItems.filter((item) => !mobileNavItems.value.some((nav) => nav.to === item.to)));
const moreLinkActive = computed(() => secondaryNavItems.value.some((item) => item.to === route.path));
const currentTitle = computed(() => navItems.find((item) => item.to === route.path)?.label || "营养饮食助手");

watch(
  () => route.fullPath,
  () => {
    mobileMoreOpen.value = false;
  },
);

function logout() {
  auth.clearAuth();
  router.push("/login");
}

function handleMobileLogout() {
  mobileMoreOpen.value = false;
  logout();
}
</script>

<style scoped>
.shell {
  min-height: 100vh;
  overflow-x: clip;
  background:
    radial-gradient(circle at top left, rgba(87, 181, 231, 0.18), transparent 35%),
    radial-gradient(circle at top right, rgba(34, 197, 94, 0.14), transparent 28%),
    linear-gradient(180deg, #f7fbff 0%, #eef4f8 100%);
  color: #123;
}

.topbar,
.mobile-topbar,
.nav,
.user-box,
.sheet-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}

.topbar {
  padding: 28px 40px 18px;
}

.mobile-topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  padding: calc(12px + env(safe-area-inset-top)) 16px 10px;
  backdrop-filter: blur(12px);
  background: rgba(247, 251, 255, 0.88);
  border-bottom: 1px solid rgba(16, 34, 42, 0.08);
}

.eyebrow,
.mobile-eyebrow {
  margin: 0 0 6px;
  font-size: 12px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #3e6d7f;
}

h1 {
  margin: 0;
  font-size: clamp(24px, 3vw, 34px);
  line-height: 1.1;
}

.subtitle {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.6;
  max-width: 620px;
}

.nav {
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

.ghost,
.sheet-logout {
  cursor: pointer;
}

.user-box {
  font-weight: 600;
}

.ghost,
.sheet-logout {
  border: 1px solid rgba(23, 48, 66, 0.18);
  background: transparent;
  color: #173042;
  padding: 10px 14px;
  border-radius: 999px;
}

.content {
  padding: 12px 24px 40px;
}

.content.with-mobile-nav {
  padding-bottom: calc(82px + env(safe-area-inset-bottom));
}

.content-inner {
  width: min(100%, 1360px);
  margin: 0 auto;
  min-width: 0;
}

.mobile-bottom-nav {
  position: fixed;
  left: 10px;
  right: 10px;
  bottom: calc(10px + env(safe-area-inset-bottom));
  z-index: 30;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
  padding: 8px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 40px rgba(15, 30, 39, 0.16);
  backdrop-filter: blur(16px);
}

.mobile-nav-link {
  display: grid;
  justify-items: center;
  gap: 3px;
  padding: 6px 4px;
  border-radius: 14px;
  color: #476072;
  text-decoration: none;
  font-size: 10px;
  font-weight: 700;
  border: 0;
  background: transparent;
}

.mobile-nav-link.router-link-active,
.mobile-nav-link.active {
  background: #173042;
  color: #fff;
}

.mobile-nav-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: rgba(23, 48, 66, 0.08);
  font-size: 11px;
}

.mobile-nav-link.router-link-active .mobile-nav-icon,
.mobile-nav-link.active .mobile-nav-icon,
.more-link .mobile-nav-icon {
  background: rgba(255, 255, 255, 0.18);
}

.mobile-sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 39;
  background: rgba(16, 34, 42, 0.32);
}

.mobile-sheet {
  position: fixed;
  left: 12px;
  right: 12px;
  bottom: calc(76px + env(safe-area-inset-bottom));
  z-index: 40;
  padding: 18px;
  max-height: min(72vh, 560px);
  overflow-y: auto;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.18);
  backdrop-filter: blur(16px);
  opacity: 0;
  pointer-events: none;
  transform: translateY(12px);
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.mobile-sheet.open {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0);
}

.sheet-links {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}

.sheet-links a {
  display: grid;
  gap: 4px;
  padding: 14px 16px;
  border-radius: 18px;
  text-decoration: none;
  background: rgba(247, 251, 255, 0.94);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.sheet-links small {
  color: #5a7a8a;
  line-height: 1.5;
}

.sheet-logout {
  width: 100%;
  margin-top: 16px;
}

.desktop-only {
  display: flex;
}

.mobile-only {
  display: none;
}

@media (max-width: 960px) {
  .desktop-only {
    display: none;
  }

  .mobile-only {
    display: block;
  }

  .content {
    padding: 12px 16px calc(86px + env(safe-area-inset-bottom));
  }

  .mobile-topbar strong {
    display: -webkit-box;
    overflow: hidden;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
  }
}
</style>
