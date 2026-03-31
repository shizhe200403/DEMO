<template>
  <div class="shell" :style="shellStyle" @pointermove="handleShellPointerMove" @pointerleave="resetShellPointer">
    <template v-if="showChrome">
      <header class="topbar desktop-only">
        <div class="brand">
          <div class="brand-topline">
            <p class="eyebrow">每日饮食</p>
            <span class="brand-date">{{ todayStamp }}</span>
          </div>
          <h1>饮食执行助手</h1>
          <p class="subtitle">把“今天还差什么、下一餐吃什么、顺手怎么记”压成一条更轻、更快的执行链路。</p>
        </div>
        <nav class="nav" aria-label="主导航">
          <RouterLink v-for="item in primaryNavItems" :key="item.to" :to="item.to">
            <span>{{ item.label }}</span>
            <small>{{ item.copy }}</small>
          </RouterLink>
        </nav>
        <div class="user-box">
          <div class="more-menu-wrap">
            <button class="ghost more-trigger" type="button" :aria-expanded="moreMenuOpen" @click="moreMenuOpen = !moreMenuOpen">
              更多
            </button>
            <Transition name="menu-float">
              <div v-if="moreMenuOpen" class="more-menu">
                <RouterLink v-for="item in secondaryNavItems" :key="item.to" :to="item.to" @click="moreMenuOpen = false">
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.copy }}</span>
                </RouterLink>
              </div>
            </Transition>
          </div>
          <span v-if="auth.user">你好，{{ auth.user?.nickname || auth.user?.username }}</span>
          <button v-if="auth.isAuthenticated" class="ghost" @click="logout">退出</button>
        </div>
      </header>

      <header class="mobile-topbar mobile-only">
        <div>
          <p class="mobile-eyebrow">每日饮食</p>
          <strong>{{ currentTitle }}</strong>
          <p class="mobile-subtitle">{{ currentRouteMoment.copy }}</p>
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
        <Transition name="ribbon-float" mode="out-in">
          <article v-if="showChrome" :key="route.path" class="floating-ribbon">
            <div class="floating-ribbon-copy">
              <span>{{ currentRouteMoment.badge }}</span>
              <strong>{{ currentRouteMoment.title }}</strong>
              <p>{{ currentRouteMoment.copy }}</p>
            </div>
            <div class="floating-ribbon-actions">
              <RouterLink class="ribbon-link" :to="currentRouteMoment.to">{{ currentRouteMoment.cta }}</RouterLink>
              <p class="ribbon-meta">{{ auth.user ? `继续中：${auth.user?.nickname || auth.user?.username}` : "欢迎回来，继续把今天推进一点点" }}</p>
            </div>
          </article>
        </Transition>
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
      <Transition name="rail-float">
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
      </Transition>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "./stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const mobileNavOpen = ref(false);
const moreMenuOpen = ref(false);
const shellPointer = reactive({ x: 16, y: 10 });

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
const routeMoments = [
  { path: "/", badge: "Today Flow", title: "先把今天最值得做的动作点出来", copy: "首页应该像晨间工作台，而不是总览页。先看缺口，再定下一餐。", cta: "去记下一餐", to: "/records" },
  { path: "/records", badge: "Quick Capture", title: "把记录动作压到最顺手", copy: "现在适合直接完成一餐，而不是继续找入口。先记上，再决定要不要细化。", cta: "看看收藏选餐", to: "/favorites" },
  { path: "/recipes", badge: "Meal Library", title: "把下一餐选得更轻松", copy: "菜谱页不只是看内容，更应该帮你更快决定这顿吃什么。", cta: "去记录页带入", to: "/records" },
  { path: "/favorites", badge: "Fast Return", title: "常吃内容应该越用越快", copy: "收藏不是终点，它更像你日常执行时最快回来的那条路。", cta: "继续去记录", to: "/records" },
  { path: "/reports", badge: "Weekly Review", title: "先看结论，再把下周动作收紧", copy: "报表页不该只给数字，更该把下一步讲清楚。", cta: "打开 AI 行动版", to: "/assistant" },
  { path: "/assistant", badge: "Task Co-Pilot", title: "把 AI 放到你刚好卡住的那一步", copy: "AI 最有用的时候，不是闲聊，而是帮你把当前动作做完。", cta: "回首页继续", to: "/" },
  { path: "/goals", badge: "Goal Focus", title: "目标页更适合做节奏校准", copy: "阶段目标不需要天天改，但需要在你偏离时把主线拉回来。", cta: "回首页看今天", to: "/" },
  { path: "/community", badge: "Shared Notes", title: "社区更像灵感补给，不该盖过主线", copy: "看看别人怎么做可以，但别让今天的执行动作被内容流打断。", cta: "回到记录页", to: "/records" },
  { path: "/profile", badge: "Profile Ready", title: "资料越完整，系统建议越像真的懂你", copy: "健康档案是系统判断下一步的底层信息，不需要花哨，但需要清楚。", cta: "回首页继续", to: "/" },
];

const showChrome = computed(() => route.path !== "/login");
const primaryNavItems = computed(() => navItems.filter((item) => primaryNavPaths.includes(item.to)));
const secondaryNavItems = computed(() => navItems.filter((item) => !primaryNavPaths.includes(item.to)));
const currentTitle = computed(() => navItems.find((item) => item.to === route.path)?.label || "营养饮食助手");
const currentRouteMoment = computed(() => routeMoments.find((item) => item.path === route.path) ?? routeMoments[0]);
const todayStamp = computed(() =>
  new Intl.DateTimeFormat("zh-CN", {
    month: "long",
    day: "numeric",
    weekday: "short",
  }).format(new Date()),
);
const shellStyle = computed(() => ({
  "--pointer-x": `${shellPointer.x}%`,
  "--pointer-y": `${shellPointer.y}%`,
}));

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

function handleShellPointerMove(event: PointerEvent) {
  const currentTarget = event.currentTarget as HTMLElement | null;
  if (!currentTarget) {
    return;
  }
  const bounds = currentTarget.getBoundingClientRect();
  shellPointer.x = ((event.clientX - bounds.left) / bounds.width) * 100;
  shellPointer.y = ((event.clientY - bounds.top) / bounds.height) * 100;
}

function resetShellPointer() {
  shellPointer.x = 16;
  shellPointer.y = 10;
}
</script>

<style scoped>
.shell {
  min-height: 100vh;
  overflow-x: clip;
  background:
    radial-gradient(circle at var(--pointer-x) var(--pointer-y), rgba(87, 181, 231, 0.2), transparent 0, transparent 26%),
    radial-gradient(circle at top left, rgba(87, 181, 231, 0.18), transparent 35%),
    radial-gradient(circle at top right, rgba(34, 197, 94, 0.14), transparent 28%),
    linear-gradient(180deg, #f7fbff 0%, #eef4f8 100%);
  color: #123;
  transition: background 0.26s ease;
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
  padding: 24px 32px 16px;
  background: rgba(247, 251, 255, 0.7);
  border-bottom: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 14px 40px rgba(18, 32, 44, 0.06);
  backdrop-filter: blur(18px);
}

.mobile-topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  padding: calc(12px + env(safe-area-inset-top)) 16px 10px;
  backdrop-filter: blur(16px);
  background: rgba(247, 251, 255, 0.82);
  border-bottom: 1px solid rgba(16, 34, 42, 0.08);
}

.brand {
  display: grid;
  gap: 6px;
}

.brand-topline {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.eyebrow,
.mobile-eyebrow {
  margin: 0 0 6px;
  font-size: 12px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #3e6d7f;
}

.brand-date {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(16, 34, 42, 0.08);
  color: #31586a;
  font-size: 12px;
  font-weight: 700;
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
  padding: 8px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(16, 34, 42, 0.05);
  backdrop-filter: blur(14px);
}

.nav a {
  display: grid;
  gap: 2px;
  color: #234;
  text-decoration: none;
  font-weight: 600;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid transparent;
  backdrop-filter: blur(12px);
  transition: transform 0.24s ease, background 0.24s ease, border-color 0.24s ease, box-shadow 0.24s ease;
}

.nav a span {
  font-size: 14px;
}

.nav a small {
  color: #6b8694;
  font-size: 11px;
  font-weight: 600;
}

.nav a:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.86);
  border-color: rgba(16, 34, 42, 0.08);
  box-shadow: 0 14px 26px rgba(15, 30, 39, 0.08);
}

.nav a.router-link-active {
  background: #173042;
  color: #fff;
  box-shadow: 0 16px 30px rgba(23, 48, 66, 0.22);
}

.nav a.router-link-active small {
  color: rgba(255, 255, 255, 0.72);
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
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 28px 48px rgba(15, 30, 39, 0.16);
  backdrop-filter: blur(22px);
}

.more-menu a {
  display: grid;
  gap: 4px;
  padding: 14px 15px;
  text-decoration: none;
  border-radius: 16px;
  background: rgba(247, 251, 255, 0.96);
  border: 1px solid rgba(16, 34, 42, 0.06);
  transition: transform 0.22s ease, border-color 0.22s ease, background 0.22s ease;
}

.more-menu a:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.98);
  border-color: rgba(16, 34, 42, 0.1);
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
  background: rgba(255, 255, 255, 0.55);
  color: #173042;
  padding: 10px 14px;
  border-radius: 999px;
  transition: transform 0.22s ease, background 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
}

.ghost:hover,
.sheet-logout:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.86);
  border-color: rgba(23, 48, 66, 0.24);
  box-shadow: 0 10px 22px rgba(15, 30, 39, 0.08);
}

.content {
  padding: 18px 24px 44px;
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

.floating-ribbon {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin: 0 0 18px;
  padding: 18px 20px;
  border-radius: 24px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.82), rgba(244, 249, 252, 0.9)),
    radial-gradient(circle at top right, rgba(87, 181, 231, 0.14), transparent 34%);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 20px 42px rgba(15, 30, 39, 0.08);
  backdrop-filter: blur(18px);
  animation: shell-soft-in 0.5s cubic-bezier(0.22, 1.2, 0.36, 1);
}

.floating-ribbon-copy {
  display: grid;
  gap: 8px;
}

.floating-ribbon-copy span,
.ribbon-meta {
  color: #5b7888;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.floating-ribbon-copy strong {
  font-size: clamp(18px, 2.2vw, 24px);
  line-height: 1.2;
  color: #10202c;
}

.floating-ribbon-copy p,
.ribbon-meta {
  margin: 0;
  line-height: 1.65;
}

.floating-ribbon-copy p {
  color: #476072;
  max-width: 760px;
}

.floating-ribbon-actions {
  display: grid;
  justify-items: end;
  gap: 12px;
  min-width: 220px;
}

.ribbon-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  padding: 0 16px;
  border-radius: 999px;
  background: #173042;
  color: #fff;
  text-decoration: none;
  font-weight: 700;
  box-shadow: 0 14px 26px rgba(23, 48, 66, 0.24);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.ribbon-link:hover {
  transform: translateY(-1px);
  box-shadow: 0 18px 30px rgba(23, 48, 66, 0.28);
}

.mobile-subtitle {
  margin: 4px 0 0;
  color: #5a7a8a;
  font-size: 12px;
  line-height: 1.5;
}

.menu-float-enter-active,
.menu-float-leave-active,
.ribbon-float-enter-active,
.ribbon-float-leave-active,
.rail-float-enter-active,
.rail-float-leave-active {
  transition: opacity 0.28s ease, transform 0.32s cubic-bezier(0.22, 1.2, 0.36, 1), filter 0.28s ease;
}

.menu-float-enter-from,
.menu-float-leave-to,
.rail-float-enter-from,
.rail-float-leave-to {
  opacity: 0;
  filter: blur(6px);
  transform: translateY(8px) scale(0.98);
}

.ribbon-float-enter-from,
.ribbon-float-leave-to {
  opacity: 0;
  filter: blur(8px);
  transform: translateY(12px) scale(0.985);
}

@keyframes shell-soft-in {
  0% {
    opacity: 0;
    transform: translateY(12px) scale(0.985);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
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

  .mobile-topbar.mobile-only,
  .mobile-rail.mobile-only {
    display: flex;
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

  .floating-ribbon {
    flex-direction: column;
    gap: 12px;
    margin-bottom: 14px;
    padding: 16px;
    border-radius: 20px;
  }

  .floating-ribbon-actions {
    min-width: 0;
    justify-items: stretch;
  }

  .ribbon-link {
    width: 100%;
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
