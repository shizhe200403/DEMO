<template>
  <div class="shell">
    <template v-if="showChrome">
      <header class="topbar desktop-only">
        <div class="brand">
          <p class="eyebrow">每日饮食</p>
          <h1>饮食管理助手</h1>
          <p class="subtitle">先看今天还差什么，再决定下一餐怎么吃、怎么记。</p>
        </div>
        <nav class="nav" aria-label="主导航">
          <RouterLink v-for="item in primaryNavItems" :key="item.to" :to="item.to">{{ item.label }}</RouterLink>
        </nav>
        <div class="user-box">
          <div class="more-menu-wrap">
            <button class="ghost more-trigger" type="button" :aria-expanded="moreMenuOpen" @click="moreMenuOpen = !moreMenuOpen">
              更多
            </button>
            <div v-if="moreMenuOpen" class="more-menu">
              <RouterLink v-for="item in secondaryNavItems" :key="item.to" :to="item.to" @click="moreMenuOpen = false">
                <strong>{{ item.label }}</strong>
                <span>{{ item.copy }}</span>
              </RouterLink>
            </div>
          </div>
          <span v-if="auth.user">你好，{{ auth.user?.nickname || auth.user?.username }}</span>
          <button v-if="auth.isAuthenticated" class="ghost" @click="logout">退出</button>
        </div>
      </header>

      <header class="mobile-topbar mobile-only">
        <div>
          <p class="mobile-eyebrow">每日饮食</p>
          <strong>{{ currentTitle }}</strong>
        </div>
        <button class="ghost mobile-nav-trigger" type="button" :aria-expanded="mobileNavOpen" @click="mobileNavOpen = !mobileNavOpen">
          <span class="hamburger-mark" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span>{{ mobileNavOpen ? "收起" : "导航" }}</span>
        </button>
      </header>
    </template>

    <main class="content" :class="{ 'with-mobile-nav': showChrome, 'with-mobile-nav-open': showChrome && mobileNavOpen }">
      <div class="content-inner">
        <RouterView v-slot="{ Component, route: currentRoute }">
          <Transition name="route-shell" mode="out-in">
            <component :is="Component" :key="currentRoute.path" />
          </Transition>
        </RouterView>
      </div>
    </main>

    <nav v-if="showChrome" class="mobile-rail mobile-only" :class="{ open: mobileNavOpen }" aria-label="移动端快捷导航">
      <button class="mobile-rail-toggle" type="button" :aria-expanded="mobileNavOpen" @click="mobileNavOpen = !mobileNavOpen">
        <span class="hamburger-mark" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
        <span>{{ mobileNavOpen ? "隐藏导航" : "展开导航" }}</span>
      </button>
      <div v-if="mobileNavOpen" class="mobile-rail-scroll">
        <div class="mobile-rail-group">
          <span class="mobile-rail-label">常用</span>
          <RouterLink
            v-for="item in primaryNavItems"
            :key="item.to"
            :to="item.to"
            class="mobile-rail-link"
            @click="mobileNavOpen = false"
          >
            <span class="mobile-rail-icon">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </RouterLink>
        </div>
        <div class="mobile-rail-group">
          <span class="mobile-rail-label">更多</span>
          <RouterLink
            v-for="item in secondaryNavItems"
            :key="item.to"
            :to="item.to"
            class="mobile-rail-link"
            @click="mobileNavOpen = false"
          >
            <span class="mobile-rail-icon">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </RouterLink>
        </div>
        <button v-if="auth.isAuthenticated" class="mobile-rail-link mobile-rail-logout" type="button" @click="handleMobileLogout">
          <span class="mobile-rail-icon">退</span>
          <span>退出</span>
        </button>
      </div>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "./stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const mobileNavOpen = ref(false);
const moreMenuOpen = ref(false);

const navItems = [
  { to: "/", label: "首页", icon: "首", copy: "查看今天的进度与下一步" },
  { to: "/records", label: "记录", icon: "记", copy: "记录今天这一餐并追踪趋势" },
  { to: "/recipes", label: "菜谱", icon: "谱", copy: "按场景快速挑选可执行菜谱" },
  { to: "/favorites", label: "收藏", icon: "藏", copy: "回到已经沉淀下来的常用选择" },
  { to: "/goals", label: "目标", icon: "标", copy: "管理重点目标与阶段进展" },
  { to: "/reports", label: "报表", icon: "报", copy: "生成周报和月报并做复盘" },
  { to: "/assistant", label: "AI助手", icon: "智", copy: "和AI营养师对话，获取个性化建议" },
  { to: "/community", label: "社区", icon: "社", copy: "查看经验内容与互动反馈" },
  { to: "/profile", label: "我的", icon: "我", copy: "维护账号资料与健康档案" },
];
const primaryNavPaths = ["/", "/records", "/recipes", "/favorites"];

const showChrome = computed(() => route.path !== "/login");
const primaryNavItems = computed(() => navItems.filter((item) => primaryNavPaths.includes(item.to)));
const secondaryNavItems = computed(() => navItems.filter((item) => !primaryNavPaths.includes(item.to)));
const currentTitle = computed(() => navItems.find((item) => item.to === route.path)?.label || "营养饮食助手");

watch(
  () => route.fullPath,
  () => {
    mobileNavOpen.value = false;
    moreMenuOpen.value = false;
  },
);

function logout() {
  auth.clearAuth();
  router.push("/login");
}

function handleMobileLogout() {
  mobileNavOpen.value = false;
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
.user-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  padding: 28px 40px 18px;
  background: rgba(247, 251, 255, 0.9);
  backdrop-filter: blur(14px);
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

.more-menu-wrap {
  position: relative;
  z-index: 50;
}

.more-menu {
  position: absolute;
  right: 0;
  top: calc(100% + 12px);
  z-index: 60;
  min-width: 280px;
  display: grid;
  gap: 8px;
  padding: 10px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 22px 44px rgba(15, 30, 39, 0.14);
  backdrop-filter: blur(18px);
}

.more-menu a {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  text-decoration: none;
  border-radius: 16px;
  background: rgba(247, 251, 255, 0.96);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.more-menu a strong {
  font-size: 14px;
  color: #173042;
}

.more-menu a span {
  font-size: 12px;
  line-height: 1.5;
  color: #5a7a8a;
}

.more-menu a.router-link-active {
  background: rgba(23, 48, 66, 0.08);
  border-color: rgba(23, 48, 66, 0.12);
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
  padding-bottom: calc(64px + env(safe-area-inset-bottom));
}

.content.with-mobile-nav-open {
  padding-bottom: calc(126px + env(safe-area-inset-bottom));
}

.content-inner {
  width: min(100%, 1360px);
  margin: 0 auto;
  min-width: 0;
}

.mobile-nav-trigger,
.mobile-rail-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.hamburger-mark {
  display: inline-flex;
  width: 14px;
  flex-direction: column;
  gap: 3px;
}

.hamburger-mark span {
  width: 14px;
  height: 2px;
  border-radius: 999px;
  background: currentColor;
}

.mobile-rail {
  position: fixed;
  left: 8px;
  right: 8px;
  bottom: calc(8px + env(safe-area-inset-bottom));
  z-index: 30;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  pointer-events: none;
}

.mobile-rail.open {
  pointer-events: auto;
}

.mobile-rail-toggle,
.mobile-rail-scroll {
  pointer-events: auto;
}

.mobile-rail-toggle {
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(255, 255, 255, 0.92);
  color: #173042;
  padding: 10px 14px;
  border-radius: 999px;
  box-shadow: 0 12px 28px rgba(15, 30, 39, 0.14);
  backdrop-filter: blur(16px);
  font-size: 13px;
  font-weight: 700;
}

.mobile-rail-scroll {
  display: grid;
  gap: 10px;
  width: 100%;
  padding: 8px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 12px 28px rgba(15, 30, 39, 0.14);
  backdrop-filter: blur(16px);
}

.mobile-rail-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mobile-rail-label {
  display: block;
  width: 100%;
  padding: 2px 4px 0;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #5a7a8a;
}

.mobile-rail-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 999px;
  color: #476072;
  text-decoration: none;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(247, 251, 255, 0.94);
  white-space: nowrap;
}

.mobile-rail-link.router-link-active,
.mobile-rail-link.active {
  background: #173042;
  color: #fff;
  border-color: #173042;
}

.mobile-rail-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  background: rgba(23, 48, 66, 0.08);
  font-size: 10px;
}

.mobile-rail-link.router-link-active .mobile-rail-icon,
.mobile-rail-link.active .mobile-rail-icon,
.mobile-rail-logout .mobile-rail-icon {
  background: rgba(255, 255, 255, 0.18);
}

.mobile-rail-logout {
  cursor: pointer;
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
    padding: 10px 12px calc(64px + env(safe-area-inset-bottom));
  }

  .content.with-mobile-nav {
    padding-bottom: calc(64px + env(safe-area-inset-bottom));
  }

  .content.with-mobile-nav-open {
    padding-bottom: calc(120px + env(safe-area-inset-bottom));
  }

  .mobile-topbar {
    gap: 12px;
    padding: calc(10px + env(safe-area-inset-top)) 12px 8px;
  }

  .mobile-topbar strong {
    font-size: 18px;
    line-height: 1.2;
    display: -webkit-box;
    overflow: hidden;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
  }

  .mobile-eyebrow {
    margin-bottom: 3px;
    font-size: 10px;
    letter-spacing: 0.14em;
  }

  .ghost,
  .mobile-rail-toggle {
    padding: 8px 12px;
    font-size: 13px;
  }

  .mobile-rail-scroll {
    padding: 6px;
    border-radius: 16px;
  }

  .mobile-rail-link {
    padding: 8px 10px;
    font-size: 11px;
  }
}
</style>
