<template>
  <div
    class="shell"
    :class="{ 'admin-shell-root': isAdminRoute }"
    :style="shellStyle"
    @pointermove="handleShellPointerMove"
    @pointerleave="resetShellPointer"
  >
    <template v-if="showChrome && !isAdminRoute">
      <header class="topbar desktop-only shell-surface">
        <div class="brand">
          <div class="brand-topline">
            <p class="eyebrow">每日饮食</p>
            <span class="brand-date">{{ todayStamp }}</span>
          </div>
          <h1>饮食执行助手</h1>
          <p class="subtitle">今天先看缺口，再把下一餐顺手记上。</p>
        </div>
        <nav class="nav shell-surface" aria-label="主导航">
          <RouterLink v-for="item in primaryNavItems" :key="item.to" :to="item.to">
            <span>{{ item.label }}</span>
          </RouterLink>
        </nav>
        <div class="user-box">
          <RouterLink v-if="hasOpsUser" class="ghost admin-entry" :to="opsHomeRoute">后台</RouterLink>
          <div ref="notificationWrapRef" class="notification-wrap">
            <button class="ghost notification-trigger" type="button" :aria-expanded="notificationOpen" @click="toggleNotifications">
              提醒
              <span v-if="notificationUnreadCount" class="notification-badge">{{ notificationUnreadCount }}</span>
            </button>
          </div>
          <div ref="moreMenuWrapRef" class="more-menu-wrap">
            <button ref="moreTriggerRef" class="ghost more-trigger" type="button" :aria-expanded="moreMenuOpen" @click="toggleMoreMenu">
              更多
            </button>
          </div>
          <span v-if="auth.user">你好，{{ auth.user?.nickname || auth.user?.username }}</span>
          <button v-if="auth.isAuthenticated" class="ghost" @click="logout">退出</button>
        </div>
      </header>

      <header class="mobile-topbar mobile-only">
        <div>
          <p class="mobile-eyebrow">每日饮食</p>
          <strong>{{ currentFrontTitle }}</strong>
          <p class="mobile-subtitle">{{ currentFrontMoment.copy }}</p>
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

      <Teleport to="body">
        <Transition name="menu-float">
          <div v-if="moreMenuOpen" ref="moreMenuRef" class="more-menu more-menu-portal" :style="moreMenuStyle">
            <div class="more-menu-intro">
              <span>低频管理</span>
              <strong>把需要偶尔处理的功能收在这里，主线就不会被打断。</strong>
            </div>
            <RouterLink v-for="item in secondaryNavItems" :key="item.to" :to="item.to" @click="moreMenuOpen = false">
              <strong>{{ item.label }}</strong>
              <span>{{ item.copy }}</span>
            </RouterLink>
          </div>
        </Transition>
      </Teleport>

      <Teleport to="body">
        <Transition name="menu-float">
          <div v-if="notificationOpen" ref="notificationPanelRef" class="notification-panel" :style="notificationPanelStyle">
            <div class="notification-panel-head">
              <strong>站内提醒</strong>
              <div class="notification-head-actions">
                <span>{{ notificationUnreadCount ? `${notificationUnreadCount} 条未读` : "已读完" }}</span>
                <button v-if="notificationUnreadCount" type="button" class="notification-mark-all" @click="markAllAsRead">
                  全部已读
                </button>
              </div>
            </div>
            <div v-if="notifications.length" class="notification-list">
              <button
                v-for="item in notifications"
                :key="item.id"
                type="button"
                class="notification-item"
                :class="{ unread: !item.read_at }"
                @click="openNotification(item)"
              >
                <div class="notification-item-head">
                  <strong>{{ item.title }}</strong>
                  <span>{{ formatNotificationTime(item.created_at) }}</span>
                </div>
                <p>{{ item.body || "有一条新的站内提醒。" }}</p>
              </button>
            </div>
            <div v-else class="notification-empty">当前还没有新的站内提醒</div>
          </div>
        </Transition>
      </Teleport>

      <main class="content" :class="{ 'with-mobile-nav': true, 'with-mobile-nav-open': mobileNavOpen }">
        <div class="content-inner">
          <Transition name="ribbon-float" mode="out-in">
            <article :key="route.path" class="floating-ribbon news-ticker">
              <div class="ticker-label">
                <span class="ribbon-status-dot" aria-hidden="true" />
                <strong>今日建议</strong>
              </div>
              <div class="ticker-viewport" aria-label="今日建议播报">
                <div class="ticker-track">
                  <span v-for="(message, index) in tickerLoopMessages" :key="`${route.path}-${index}-${message}`" class="ticker-item">
                    {{ message }}
                  </span>
                </div>
              </div>
              <RouterLink class="ticker-action" :to="currentFrontMoment.to">{{ currentFrontMoment.cta }}</RouterLink>
            </article>
          </Transition>
          <RouterView v-slot="{ Component, route: currentRoute }">
            <Transition name="route-shell" mode="out-in">
              <component :is="Component" :key="currentRoute.path" />
            </Transition>
          </RouterView>
        </div>
      </main>

      <nav class="mobile-rail mobile-only" :class="{ open: mobileNavOpen }" aria-label="移动端快捷导航">
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
                v-if="hasOpsUser"
                :to="opsHomeRoute"
                class="mobile-rail-link"
                @click="mobileNavOpen = false"
              >
                <span class="mobile-rail-icon">管</span>
                <span>后台</span>
              </RouterLink>
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
    </template>

    <template v-else-if="showChrome && isAdminRoute">
      <header class="admin-topnav desktop-only shell-surface">
        <div class="admin-topnav-brand">
          <div class="brand-topline">
            <p class="eyebrow">Admin Console</p>
            <span class="brand-date admin-brand-date">{{ todayStamp }}</span>
          </div>
          <div class="admin-brand-copy">
            <span class="admin-topnav-name">饮食管理台</span>
            <p class="subtitle admin-topnav-subtitle">{{ currentAdminMoment.copy }}</p>
          </div>
        </div>
        <nav class="admin-topnav-links shell-surface" aria-label="后台导航">
          <RouterLink
            v-for="item in filteredAdminNavItems"
            :key="item.to"
            :to="item.to"
            class="admin-topnav-link"
            :exact-active-class="item.to === '/ops' ? 'router-link-exact-active' : 'router-link-active'"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
        <div class="admin-topnav-end">
          <div ref="notificationWrapRef" class="notification-wrap">
            <button class="ghost notification-trigger" type="button" :aria-expanded="notificationOpen" @click="toggleNotifications">
              提醒
              <span v-if="notificationUnreadCount" class="notification-badge">{{ notificationUnreadCount }}</span>
            </button>
          </div>
          <RouterLink class="ghost admin-return-soft" to="/">回到前台</RouterLink>
          <span class="admin-topnav-user">{{ auth.user?.nickname || auth.user?.username }}</span>
          <span class="admin-topnav-role">{{ adminRoleLabel }}</span>
          <button v-if="auth.isAuthenticated" class="ghost" @click="logout">退出</button>
        </div>
      </header>

      <header class="admin-mobile-topbar mobile-only">
        <div class="admin-mobile-copy">
          <p class="mobile-eyebrow">Admin Console</p>
          <strong>{{ currentAdminMoment.label }}</strong>
          <p class="mobile-subtitle">{{ currentAdminMoment.title }}</p>
        </div>
        <button class="ghost mobile-nav-trigger" type="button" :aria-expanded="adminMobileNavOpen" @click="adminMobileNavOpen = !adminMobileNavOpen">
          <span class="hamburger-mark" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span>{{ adminMobileNavOpen ? "收起" : "导航" }}</span>
        </button>
      </header>

      <main class="admin-content">
        <div class="admin-content-inner">
          <Transition name="ribbon-float" mode="out-in">
            <article :key="route.path" class="floating-ribbon news-ticker admin-pulse">
              <div class="ticker-label">
                <span class="ribbon-status-dot" aria-hidden="true" />
                <strong>后台建议</strong>
              </div>
              <div class="ticker-viewport" aria-label="后台建议播报">
                <div class="ticker-track">
                  <span
                    v-for="(message, index) in adminTickerLoopMessages"
                    :key="`${route.path}-admin-${index}-${message}`"
                    class="ticker-item"
                  >
                    {{ message }}
                  </span>
                </div>
              </div>
              <RouterLink class="ticker-action" :to="currentAdminAction.to">{{ currentAdminAction.label }}</RouterLink>
            </article>
          </Transition>
          <RouterView v-slot="{ Component, route: currentRoute }">
            <Transition name="route-shell" mode="out-in">
              <component :is="Component" :key="currentRoute.path" />
            </Transition>
          </RouterView>
        </div>
      </main>

      <nav class="mobile-rail mobile-only admin-mobile-rail" :class="{ open: adminMobileNavOpen }" aria-label="后台移动端快捷导航">
        <button class="mobile-rail-toggle" type="button" :aria-expanded="adminMobileNavOpen" @click="adminMobileNavOpen = !adminMobileNavOpen">
          <span class="hamburger-mark" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span>{{ adminMobileNavOpen ? "隐藏导航" : "展开导航" }}</span>
        </button>
        <Transition name="rail-float">
          <div v-if="adminMobileNavOpen" class="mobile-rail-scroll admin-mobile-scroll">
            <div class="mobile-rail-group">
              <span class="mobile-rail-label">后台主线</span>
              <RouterLink
                v-for="item in filteredAdminNavItems"
                :key="item.to"
                :to="item.to"
                class="mobile-rail-link admin-mobile-link"
                @click="adminMobileNavOpen = false"
              >
                <span class="mobile-rail-icon">{{ item.icon }}</span>
                <span>{{ item.label }}</span>
              </RouterLink>
            </div>
            <div class="mobile-rail-group">
              <span class="mobile-rail-label">前台入口</span>
              <RouterLink
                v-for="item in primaryNavItems"
                :key="item.to"
                :to="item.to"
                class="mobile-rail-link"
                @click="adminMobileNavOpen = false"
              >
                <span class="mobile-rail-icon">{{ item.icon }}</span>
                <span>{{ item.label }}</span>
              </RouterLink>
            </div>
            <button v-if="auth.isAuthenticated" class="mobile-rail-link mobile-rail-logout" type="button" @click="handleAdminMobileLogout">
              <span class="mobile-rail-icon">退</span>
              <span>退出</span>
            </button>
          </div>
        </Transition>
      </nav>
    </template>

    <RouterView v-else v-slot="{ Component, route: currentRoute }">
      <Transition name="route-shell" mode="out-in">
        <component :is="Component" :key="currentRoute.path" />
      </Transition>
    </RouterView>

    <GlobalAssistantFloat v-if="showChrome && auth.isAuthenticated" />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import GlobalAssistantFloat from "./components/GlobalAssistantFloat.vue";
import { listHealthGoals } from "./api/goals";
import { listNotifications, markAllNotificationsRead, markNotificationRead } from "./api/notifications";
import { listMealRecords } from "./api/tracking";
import { useAuthStore } from "./stores/auth";
import { canAccessOpsScope, hasOpsAccess, isOpsManager, resolveOpsHome } from "./lib/opsAccess";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const mobileNavOpen = ref(false);
const adminMobileNavOpen = ref(false);
const moreMenuOpen = ref(false);
const moreMenuWrapRef = ref<HTMLElement | null>(null);
const moreTriggerRef = ref<HTMLElement | null>(null);
const moreMenuRef = ref<HTMLElement | null>(null);
const moreMenuStyle = ref<Record<string, string>>({});
const notificationWrapRef = ref<HTMLElement | null>(null);
const notificationPanelRef = ref<HTMLElement | null>(null);
const notificationOpen = ref(false);
const notificationPanelStyle = ref<Record<string, string>>({});
const notifications = ref<any[]>([]);
const shellPointer = reactive({ x: 16, y: 10 });
const personalizedTickerTips = ref<string[]>([]);
let tickerRequestId = 0;

const navItems = [
  { to: "/", label: "首页", icon: "首", copy: "查看今天的进度与下一步" },
  { to: "/records", label: "记录", icon: "记", copy: "记录今天这一餐并追踪趋势" },
  { to: "/recipes", label: "菜谱", icon: "谱", copy: "按场景快速挑选可执行菜谱" },
  { to: "/favorites", label: "收藏", icon: "藏", copy: "回到已经沉淀下来的常用选择" },
  { to: "/goals", label: "目标", icon: "标", copy: "管理重点目标与阶段进展" },
  { to: "/reports", label: "报表", icon: "报", copy: "生成周报和月报并做复盘" },
  { to: "/assistant", label: "AI助手", icon: "智", copy: "和 AI 营养师对话，获取个性化建议" },
  { to: "/community", label: "社区", icon: "社", copy: "查看经验内容与互动反馈" },
  { to: "/profile", label: "我的", icon: "我", copy: "维护账号资料与健康档案" },
];

const adminNavItems = [
  { to: "/ops", label: "后台总览", icon: "览", copy: "先看今天的值守主线和后台建议", scope: "manager" as const },
  { to: "/ops/logs", label: "操作日志", icon: "迹", copy: "回看是谁改了什么、改完是否把后台主线拉稳", scope: "operator" as const },
  { to: "/ops/reports", label: "运营复核", icon: "报", copy: "集中看后台运营指标、报表任务和记录覆盖情况", scope: "operator" as const },
  { to: "/ops/community", label: "社区审核", icon: "社", copy: "集中处理帖子审核、举报和评论隐藏", scope: "operator" as const },
  { to: "/ops/recipes", label: "菜谱管理", icon: "谱", copy: "集中处理菜谱状态、审核结论和内容质量", scope: "operator" as const },
  { to: "/ops/users", label: "用户管理", icon: "户", copy: "集中管理账号状态、角色边界和资料质量", scope: "manager" as const },
];

const primaryNavPaths = ["/", "/records", "/recipes", "/favorites"];
const frontRouteMoments = [
  { path: "/", label: "首页", badge: "Today Flow", title: "先把今天最值得做的动作点出来", copy: "首页应该像晨间工作台，而不是总览页。先看缺口，再定下一餐。", hint: "先看缺口，再动手", cta: "去记下一餐", to: "/records" },
  { path: "/records", label: "记录", badge: "Quick Capture", title: "把记录动作压到最顺手", copy: "现在适合直接完成一餐，而不是继续找入口。先记上，再决定要不要细化。", hint: "先记上，细化可以稍后", cta: "看看收藏选餐", to: "/favorites" },
  { path: "/recipes", label: "菜谱", badge: "Meal Library", title: "把下一餐选得更轻松", copy: "菜谱页不只是看内容，更应该帮你更快决定这顿吃什么。", hint: "别选太久，先锁定一份", cta: "去记录页带入", to: "/records" },
  { path: "/favorites", label: "收藏", badge: "Fast Return", title: "常吃内容应该越用越快", copy: "收藏不是终点，它更像你日常执行时最快回来的那条路。", hint: "常吃内容要越点越顺手", cta: "继续去记录", to: "/records" },
  { path: "/reports", label: "报表", badge: "Weekly Review", title: "先看结论，再把下周动作收紧", copy: "报表页不该只给数字，更该把下一步讲清楚。", hint: "结论要比数字更先到位", cta: "打开 AI 行动版", to: "/assistant" },
  { path: "/assistant", label: "AI助手", badge: "Task Co-Pilot", title: "把 AI 放到你刚好卡住的那一步", copy: "AI 最有用的时候，不是闲聊，而是帮你把当前动作做完。", hint: "卡住时再叫它最值", cta: "回首页继续", to: "/" },
  { path: "/goals", label: "目标", badge: "Goal Focus", title: "目标页更适合做节奏校准", copy: "阶段目标不需要天天改，但需要在你偏离时把主线拉回来。", hint: "目标负责校准，不负责打断", cta: "回首页看今天", to: "/" },
  { path: "/community", label: "社区", badge: "Shared Notes", title: "社区更像灵感补给，不该盖过主线", copy: "看看别人怎么做可以，但别让今天的执行动作被内容流打断。", hint: "逛一会儿就够，主线更重要", cta: "回到记录页", to: "/records" },
  { path: "/profile", label: "我的", badge: "Profile Ready", title: "资料越完整，系统建议越像真的懂你", copy: "健康档案是系统判断下一步的底层信息，不需要花哨，但需要清楚。", hint: "底层信息补齐，建议才会更准", cta: "回首页继续", to: "/" },
];
const adminRouteMoments = [
  { path: "/ops", label: "后台总览", badge: "Ops Overview", title: "先把后台今天最该处理的动作排清楚", copy: "后台先定优先级，再进入具体模块，避免一开始就散到每个角落。", hint: "先定优先级，再展开处理", cta: "去用户管理", to: "/ops/users", scope: "manager" as const },
  { path: "/ops/logs", label: "操作日志", badge: "Action Trail", title: "先把最近到底改了什么看清楚", copy: "操作日志不是为了堆记录，而是为了让后台动作可回看、可追责、可复盘。", hint: "先看动作轨迹，再判断问题出在哪一步", cta: "回后台总览", to: "/ops", scope: "operator" as const },
  { path: "/ops/reports", label: "运营复核", badge: "Operations Review", title: "先把运营指标和报表任务看清楚", copy: "这页更适合从整体活跃度、内容处理节奏和报表任务状态判断后台下一步。", hint: "先看指标，再判断要补数据、补内容还是补处理节奏", cta: "回后台总览", to: "/ops", scope: "operator" as const },
  { path: "/ops/community", label: "社区审核", badge: "Community Moderation", title: "先把帖子审核和举报处理收紧", copy: "社区后台先看待审核内容、待处理举报和评论隐藏动作，别让风险内容继续外露。", hint: "优先看待审核帖子和待处理举报", cta: "回后台总览", to: "/ops", scope: "operator" as const },
  { path: "/ops/recipes", label: "菜谱管理", badge: "Recipe Operations", title: "先把菜谱状态和审核结论收紧", copy: "菜谱管理先盯状态、审核和信息质量，别让无效内容混进用户决策链路。", hint: "优先看待审核和信息不完整的菜谱", cta: "回后台总览", to: "/ops", scope: "operator" as const },
  { path: "/ops/users", label: "用户管理", badge: "User Operations", title: "先把账号、角色和资料边界看清楚", copy: "用户管理是后台最核心的第一块，先把角色边界、状态和资料质量稳住。", hint: "优先检查权限、停用状态和资料完整度", cta: "回后台总览", to: "/ops", scope: "manager" as const },
];

const showChrome = computed(() => route.path !== "/login");
const isAdminRoute = computed(() => route.path.startsWith("/ops"));
const notificationUnreadCount = computed(() => notifications.value.filter((item) => !item.read_at).length);
const primaryNavItems = computed(() => navItems.filter((item) => primaryNavPaths.includes(item.to)));
const secondaryNavItems = computed(() => navItems.filter((item) => !primaryNavPaths.includes(item.to)));
const hasOpsUser = computed(() => hasOpsAccess(auth.user));
const isManagerUser = computed(() => isOpsManager(auth.user));
const opsHomeRoute = computed(() => resolveOpsHome(auth.user));
const filteredAdminNavItems = computed(() => adminNavItems.filter((item) => !item.scope || canAccessOpsScope(auth.user, item.scope)));
const adminRoleLabel = computed(() => (isManagerUser.value ? "管理员" : hasOpsUser.value ? "审核员" : "后台用户"));
const currentFrontMoment = computed(() => matchRouteMoment(route.path, frontRouteMoments) ?? frontRouteMoments[0]);
const currentAdminMoment = computed(() => matchRouteMoment(route.path, adminRouteMoments) ?? adminRouteMoments[0]);
const currentAdminAction = computed(() => {
  if (currentAdminMoment.value.scope === "manager" || isManagerUser.value) {
    return { to: currentAdminMoment.value.to, label: currentAdminMoment.value.cta };
  }
  return { to: opsHomeRoute.value, label: route.path === "/ops/reports" ? "回运营复核首页" : "回到运营复核" };
});
const currentFrontTitle = computed(() => currentFrontMoment.value.label || "营养饮食助手");
const fallbackTickerTips = computed(() => [
  currentFrontMoment.value.hint,
  `当前页：${currentFrontTitle.value}，${currentFrontMoment.value.copy}`,
  auth.user ? `继续保持，${auth.user?.nickname || auth.user?.username}，先完成一个最小动作就够了` : "先完成一个最小动作，今天就会更顺一点",
]);
const tickerMessages = computed(() => [
  ...(personalizedTickerTips.value.length ? personalizedTickerTips.value : fallbackTickerTips.value),
  `当前动作：${currentFrontMoment.value.title}`,
]);
const tickerLoopMessages = computed(() => [...tickerMessages.value, ...tickerMessages.value]);
const adminTickerMessages = computed(() => [
  currentAdminMoment.value.hint,
  "后台先解决最影响真实用户体验的问题，再扩展模块深度。",
  hasOpsUser.value
    ? `当前值守：${auth.user?.nickname || auth.user?.username}，先完成一个明确动作，比同时盯多块更有效。`
    : "先确认后台权限，再开始处理后台事项。",
  route.path === "/ops/users"
    ? "用户管理里先看账号状态、角色边界和资料完整度，再处理个别字段。"
    : route.path === "/ops/logs"
      ? "操作日志里先看最近动作轨迹和字段前后变化，再判断是误改、漏改还是流程本身有问题。"
    : route.path === "/ops/reports"
      ? "运营复核里先看整体活跃、内容处理节奏和报表任务状态，再决定下一步补哪里。"
    : route.path === "/ops/community"
      ? "社区审核里先处理待审核帖子、待处理举报和需要隐藏的评论。"
    : route.path === "/ops/recipes"
      ? "菜谱管理里先看待审核、草稿和信息缺口，再决定是否发布或驳回。"
    : "先看后台总览，把今天的主线排清楚，再进入具体列表。",
]);
const adminTickerLoopMessages = computed(() => [...adminTickerMessages.value, ...adminTickerMessages.value]);
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
    adminMobileNavOpen.value = false;
    moreMenuOpen.value = false;
    if (!isAdminRoute.value) {
      void refreshTickerTips();
    }
  },
);

watch(
  () => auth.user?.id,
  () => {
    if (!isAdminRoute.value) {
      void refreshTickerTips();
    } else {
      personalizedTickerTips.value = [];
    }
    void loadNotificationsList();
  },
  { immediate: true },
);

onMounted(() => {
  document.addEventListener("pointerdown", handleDocumentPointerDown);
  document.addEventListener("keydown", handleDocumentKeydown);
  window.addEventListener("resize", handleViewportChange);
  window.addEventListener("scroll", handleViewportChange, true);
});

onBeforeUnmount(() => {
  document.removeEventListener("pointerdown", handleDocumentPointerDown);
  document.removeEventListener("keydown", handleDocumentKeydown);
  window.removeEventListener("resize", handleViewportChange);
  window.removeEventListener("scroll", handleViewportChange, true);
});

function matchRouteMoment(routePath: string, moments: Array<{ path: string }>) {
  const matched = [...moments].sort((a, b) => b.path.length - a.path.length).find((item) => routePath.startsWith(item.path));
  return matched ?? moments[0];
}

function logout() {
  auth.clearAuth();
  router.push("/login");
}

function toggleMoreMenu() {
  if (moreMenuOpen.value) {
    moreMenuOpen.value = false;
    return;
  }

  moreMenuOpen.value = true;
  void nextTick(() => {
    updateMoreMenuPosition();
  });
}

function handleMobileLogout() {
  mobileNavOpen.value = false;
  logout();
}

function handleAdminMobileLogout() {
  adminMobileNavOpen.value = false;
  logout();
}

function handleDocumentPointerDown(event: PointerEvent) {
  if (moreMenuOpen.value) {
    const wrap = moreMenuWrapRef.value;
    const menu = moreMenuRef.value;
    if (event.target instanceof Node && !wrap?.contains(event.target) && !menu?.contains(event.target)) {
      moreMenuOpen.value = false;
    }
  }

  if (notificationOpen.value) {
    const wrap = notificationWrapRef.value;
    const panel = notificationPanelRef.value;
    if (event.target instanceof Node && !wrap?.contains(event.target) && !panel?.contains(event.target)) {
      notificationOpen.value = false;
    }
  }
}

function handleDocumentKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") {
    moreMenuOpen.value = false;
    notificationOpen.value = false;
  }
}

function handleViewportChange() {
  if (moreMenuOpen.value) {
    updateMoreMenuPosition();
  }
  if (notificationOpen.value) {
    updateNotificationPosition();
  }
}

function updateMoreMenuPosition() {
  const trigger = moreTriggerRef.value;
  if (!trigger) {
    return;
  }

  const bounds = trigger.getBoundingClientRect();
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  const menuWidth = Math.min(320, viewportWidth - 32);
  const left = Math.min(Math.max(16, bounds.right - menuWidth), Math.max(16, viewportWidth - menuWidth - 16));
  const top = Math.max(16, bounds.bottom + 12);
  const maxHeight = Math.max(180, viewportHeight - top - 16);

  moreMenuStyle.value = {
    left: `${left}px`,
    top: `${top}px`,
    width: `${menuWidth}px`,
    maxHeight: `${maxHeight}px`,
  };
}

function updateNotificationPosition() {
  const trigger = notificationWrapRef.value;
  if (!trigger) {
    return;
  }
  const bounds = trigger.getBoundingClientRect();
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  const panelWidth = Math.min(340, viewportWidth - 32);
  const left = Math.min(Math.max(16, bounds.right - panelWidth), Math.max(16, viewportWidth - panelWidth - 16));
  const top = Math.max(16, bounds.bottom + 12);
  notificationPanelStyle.value = {
    left: `${left}px`,
    top: `${top}px`,
    width: `${panelWidth}px`,
    maxHeight: `${Math.max(220, viewportHeight - top - 16)}px`,
  };
}

async function loadNotificationsList() {
  if (!auth.isAuthenticated) {
    notifications.value = [];
    return;
  }
  try {
    const response = await listNotifications();
    notifications.value = response.data?.items ?? [];
  } catch {
    notifications.value = [];
  }
}

function toggleNotifications() {
  notificationOpen.value = !notificationOpen.value;
  if (notificationOpen.value) {
    void loadNotificationsList();
    void nextTick(() => updateNotificationPosition());
  }
}

async function openNotification(item: any) {
  if (!item.read_at) {
    await markNotificationRead(item.id).catch(() => undefined);
    item.read_at = new Date().toISOString();
  }
  notificationOpen.value = false;
  if (item.link_path) {
    router.push(item.link_path);
  }
}

function formatNotificationTime(value?: string) {
  if (!value) {
    return "刚刚";
  }
  return value.replace("T", " ").slice(5, 16);
}

async function markAllAsRead() {
  await markAllNotificationsRead().catch(() => undefined);
  notifications.value = notifications.value.map((item) => ({ ...item, read_at: item.read_at || new Date().toISOString() }));
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

function unwrapListPayload(payload: any) {
  if (Array.isArray(payload?.data?.items)) return payload.data.items;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload)) return payload;
  return [];
}

function todayString() {
  const today = new Date();
  const year = today.getFullYear();
  const month = `${today.getMonth() + 1}`.padStart(2, "0");
  const day = `${today.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function goalTypeLabel(value?: string) {
  const labels: Record<string, string> = {
    weight_loss: "减重",
    muscle_gain: "增肌",
    blood_sugar_control: "控糖",
    fat_control: "控脂",
    protein_up: "补蛋白",
    diet_balance: "饮食均衡",
  };
  return value ? labels[value] || value : "";
}

function dietTypeHint(value?: string) {
  const labels: Record<string, string> = {
    balanced: "今天继续把饮食均衡放在第一位",
    high_protein: "今天优先保证每餐都有更扎实的蛋白来源",
    low_fat: "今天先把油脂感重的选择往后放一放",
    low_sugar: "今天先把精制糖和甜饮压下来",
    vegetarian: "今天优先选更稳妥的植物蛋白组合",
    low_sodium: "今天外食时先看盐分和汤汁",
  };
  return value ? labels[value] || "" : "";
}

function mealPreferenceHint(value?: string) {
  const labels: Record<string, string> = {
    quick_easy: "今天先选准备时间短的菜，别把决定拖太久",
    light_home: "今天更适合走清爽家常路线",
    prep_friendly: "今天顺手多做一份，后面记录会更轻松",
    family_style: "今天优先挑一家人都容易接受的做法",
    eating_out: "今天外食时优先选配料清楚、分量好判断的餐",
  };
  return value ? labels[value] || "" : "";
}

function healthHint(health: Record<string, any> | null | undefined) {
  if (health?.has_diabetes) return "今天先把碳水和添加糖压稳一点";
  if (health?.has_hypertension) return "今天先把重口和高钠食物往后放";
  if (health?.has_hyperlipidemia) return "今天先避开明显高油高脂的搭配";
  return "";
}

async function refreshTickerTips() {
  if (!auth.isAuthenticated || isAdminRoute.value) {
    personalizedTickerTips.value = [];
    return;
  }

  const requestId = ++tickerRequestId;

  try {
    const [goalResult, recordResult] = await Promise.allSettled([listHealthGoals(), listMealRecords()]);
    if (requestId !== tickerRequestId) {
      return;
    }

    const user = auth.user;
    const profile = user?.profile ?? null;
    const health = user?.health_condition ?? null;
    const goals = goalResult.status === "fulfilled" ? unwrapListPayload(goalResult.value) : [];
    const records = recordResult.status === "fulfilled" ? unwrapListPayload(recordResult.value) : [];
    const activeGoal = goals.find((item: Record<string, any>) => item.status === "active") ?? null;
    const today = todayString();
    const todayRecords = records.filter((item: Record<string, any>) => item.record_date === today);
    const mealNames: Record<string, string> = { breakfast: "早餐", lunch: "午餐", dinner: "晚餐", snack: "加餐" };
    const todayMealSet = new Set(todayRecords.map((item: Record<string, any>) => String(item.meal_type || "")));
    const missingMeals = ["breakfast", "lunch", "dinner"].filter((item) => !todayMealSet.has(item));

    const tips = [
      activeGoal ? `今天先围绕${goalTypeLabel(activeGoal.goal_type)}主线做决定，别同时改太多件事` : "今天先完成一餐记录，系统才更容易给准建议",
      todayRecords.length === 0 ? "今天还没开始记录，先补一餐，后面的建议才会更像真的懂你" : `今天已经记了${todayRecords.length}餐，接下来优先补${missingMeals.length ? missingMeals.map((item) => mealNames[item]).join("、") : "下一餐的质量"}`,
      healthHint(health),
      dietTypeHint(profile?.diet_type),
      mealPreferenceHint(profile?.meal_preference),
      profile?.is_outdoor_eating_frequent ? "今天如果在外面吃，优先选配料简单、分量清楚的餐" : "今天如果在家吃，尽量把常吃菜谱沉淀成可复用选择",
      currentFrontMoment.value.hint,
    ]
      .filter((item, index, list): item is string => Boolean(item && item.trim()) && list.indexOf(item) === index)
      .slice(0, 4);

    personalizedTickerTips.value = tips;
  } catch {
    if (requestId === tickerRequestId) {
      personalizedTickerTips.value = [];
    }
  }
}
</script>

<style scoped>
.shell {
  min-height: 100vh;
  overflow-x: clip;
  background:
    radial-gradient(circle at var(--pointer-x) var(--pointer-y), rgba(87, 181, 231, 0.14), transparent 0, transparent 24%),
    radial-gradient(circle at top left, rgba(87, 181, 231, 0.14), transparent 32%),
    linear-gradient(180deg, #f8fbfe 0%, #eef4f8 100%);
  color: #123;
  transition: background 0.26s ease;
}

.shell.admin-shell-root {
  background:
    radial-gradient(circle at var(--pointer-x) var(--pointer-y), rgba(255, 191, 105, 0.12), transparent 0, transparent 26%),
    radial-gradient(circle at top right, rgba(87, 181, 231, 0.12), transparent 28%),
    linear-gradient(180deg, #fbfcff 0%, #eef4f8 100%);
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
  overflow: visible;
  isolation: isolate;
  padding: 14px 20px 10px;
  background: rgba(247, 251, 255, 0.7);
  border-bottom: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 14px 40px rgba(18, 32, 44, 0.06);
  backdrop-filter: blur(18px);
}

.shell-surface {
  position: relative;
  overflow: hidden;
}

.shell-surface::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.16), transparent 32%);
  opacity: 0.56;
  pointer-events: none;
}

.mobile-topbar,
.admin-mobile-topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  padding: calc(12px + env(safe-area-inset-top)) 16px 10px;
  backdrop-filter: blur(16px);
}

.mobile-topbar {
  background: rgba(247, 251, 255, 0.82);
  border-bottom: 1px solid rgba(16, 34, 42, 0.08);
}

.admin-mobile-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  background: rgba(249, 252, 255, 0.86);
  border-bottom: 1px solid rgba(16, 34, 42, 0.08);
}

.brand {
  display: grid;
  flex: 0 0 248px;
  gap: 4px;
  min-width: 0;
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

.admin-shell-root .eyebrow,
.admin-shell-root .mobile-eyebrow {
  color: #7d5e2f;
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

h1,
.admin-title {
  margin: 0;
  font-size: clamp(21px, 2vw, 26px);
  line-height: 1.1;
}

.subtitle,
.mobile-subtitle,
.admin-subtitle {
  margin: 4px 0 0;
  color: #476072;
  line-height: 1.5;
  font-size: 13px;
}

.subtitle {
  max-width: 280px;
}

.admin-subtitle,
.admin-mobile-copy .mobile-subtitle {
  color: #5f7684;
}

.nav {
  flex: 1 1 auto;
  min-width: 0;
  flex-wrap: nowrap;
  justify-content: center;
  gap: 8px;
  padding: 6px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(16, 34, 42, 0.05);
  backdrop-filter: blur(14px);
}

.nav a {
  flex: 1 1 0;
  min-width: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #234;
  text-decoration: none;
  font-weight: 700;
  white-space: nowrap;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid transparent;
  backdrop-filter: blur(12px);
  transition: transform 0.24s ease, background 0.24s ease, border-color 0.24s ease, box-shadow 0.24s ease;
}

.nav a span {
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
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

.more-menu-wrap {
  position: relative;
  z-index: 50;
}

.more-menu {
  min-width: 280px;
  display: grid;
  gap: 8px;
  padding: 10px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 28px 48px rgba(15, 30, 39, 0.16);
  backdrop-filter: blur(22px);
  overflow: auto;
}

.more-menu-portal {
  position: fixed;
  z-index: 2000;
}

.more-menu-intro {
  display: grid;
  gap: 6px;
  padding: 16px;
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(23, 48, 66, 0.96), rgba(35, 75, 96, 0.92)),
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.18), transparent 38%);
  box-shadow: 0 16px 28px rgba(15, 30, 39, 0.18);
}

.more-menu-intro span {
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.64);
}

.more-menu-intro strong {
  font-size: 14px;
  line-height: 1.55;
  color: #fff;
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
  border: 1px solid rgba(23, 48, 66, 0.18);
  background: rgba(255, 255, 255, 0.55);
  color: #173042;
  padding: 8px 12px;
  border-radius: 999px;
  transition: transform 0.22s ease, background 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
}

.shell.admin-shell-root .ghost {
  border-color: rgba(16, 34, 42, 0.12);
  background: rgba(255, 255, 255, 0.7);
  color: #173042;
}

.ghost:hover,
.sheet-logout:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.86);
  border-color: rgba(23, 48, 66, 0.24);
  box-shadow: 0 10px 22px rgba(15, 30, 39, 0.08);
}

.shell.admin-shell-root .ghost:hover {
  background: rgba(255, 255, 255, 0.94);
  border-color: rgba(16, 34, 42, 0.18);
}

.user-box {
  flex: 0 0 auto;
  position: relative;
  z-index: 1;
  font-weight: 600;
  gap: 10px;
  white-space: nowrap;
  font-size: 13px;
}

.notification-wrap {
  position: relative;
}

.notification-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.notification-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: #ff6b5f;
  color: #fff;
  font-size: 11px;
  font-weight: 800;
}

.notification-panel {
  position: fixed;
  z-index: 2100;
  display: grid;
  gap: 10px;
  padding: 12px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 28px 48px rgba(15, 30, 39, 0.16);
  backdrop-filter: blur(22px);
  overflow: auto;
}

.notification-panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 4px 4px 0;
}

.notification-panel-head strong {
  color: #173042;
  font-size: 15px;
}

.notification-panel-head span {
  color: #5a7a8a;
  font-size: 12px;
}

.notification-head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notification-mark-all {
  border: 0;
  padding: 0;
  background: transparent;
  color: #1f4f67;
  font-size: 12px;
  font-weight: 700;
}

.notification-list {
  display: grid;
  gap: 8px;
}

.notification-item {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 18px;
  border: 1px solid rgba(16, 34, 42, 0.06);
  background: rgba(247, 251, 255, 0.94);
  text-align: left;
}

.notification-item.unread {
  border-color: rgba(255, 138, 28, 0.2);
  background: linear-gradient(135deg, rgba(255, 248, 239, 0.98), rgba(247, 251, 255, 0.94));
}

.notification-item-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.notification-item-head strong {
  color: #173042;
  font-size: 14px;
  line-height: 1.4;
}

.notification-item-head span,
.notification-item p,
.notification-empty {
  color: #5a7a8a;
  font-size: 12px;
}

.notification-item p {
  margin: 0;
  line-height: 1.55;
}

.notification-empty {
  padding: 18px 14px;
  text-align: center;
}

.content {
  padding: 10px 18px 44px;
}

.content.with-mobile-nav {
  padding-bottom: calc(64px + env(safe-area-inset-bottom));
}

.content.with-mobile-nav-open {
  padding-bottom: calc(126px + env(safe-area-inset-bottom));
}

.content-inner {
  width: min(100%, 1440px);
  margin: 0 auto;
  min-width: 0;
}

.admin-topnav {
  position: sticky;
  top: 0;
  z-index: 40;
  display: flex;
  align-items: center;
  min-height: 80px;
  padding: 14px 20px 10px;
  background: rgba(247, 251, 255, 0.74);
  border-bottom: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 14px 40px rgba(18, 32, 44, 0.06);
  backdrop-filter: blur(20px);
}

.admin-topnav-brand {
  display: grid;
  gap: 6px;
  flex: 0 0 250px;
  min-width: 0;
}

.admin-brand-date {
  background: rgba(255, 244, 231, 0.92);
  color: #7b5924;
  border-color: rgba(198, 143, 73, 0.18);
}

.admin-topnav-name {
  font-size: clamp(21px, 2vw, 26px);
  font-weight: 700;
  color: #173042;
  white-space: normal;
}

.admin-brand-copy {
  display: grid;
  gap: 4px;
}

.admin-topnav-subtitle {
  max-width: 320px;
}

.admin-topnav-links {
  display: flex;
  align-items: center;
  flex: 1 1 auto;
  min-width: 0;
  gap: 8px;
  padding: 6px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(16, 34, 42, 0.05);
  backdrop-filter: blur(14px);
}

.admin-topnav-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  padding: 0 12px;
  border-radius: 14px;
  font-size: 13px;
  font-weight: 700;
  color: #234;
  text-decoration: none;
  white-space: nowrap;
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid transparent;
  transition: transform 0.24s ease, background 0.24s ease, border-color 0.24s ease, box-shadow 0.24s ease;
}

.admin-topnav-link:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.9);
  color: #173042;
  border-color: rgba(16, 34, 42, 0.08);
  box-shadow: 0 14px 26px rgba(15, 30, 39, 0.08);
}

.admin-topnav-link.router-link-active,
.admin-topnav-link.router-link-exact-active {
  background: #173042;
  color: #fff;
  font-weight: 700;
  box-shadow: 0 16px 30px rgba(23, 48, 66, 0.22);
}

.admin-topnav-end {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 0 0 auto;
  margin-left: 16px;
  white-space: nowrap;
}

.admin-return-soft {
  opacity: 0.88;
}

.admin-topnav-user {
  font-size: 13px;
  font-weight: 600;
  color: #173042;
  white-space: nowrap;
}

.admin-topnav-role {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 9px;
  border-radius: 999px;
  background: rgba(255, 191, 105, 0.16);
  border: 1px solid rgba(198, 143, 73, 0.22);
  color: #7b5924;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.admin-workspace {
  min-width: 0;
  min-height: calc(100vh - 52px);
}

.admin-content {
  min-width: 0;
  padding: 10px 18px 44px;
}

.admin-content-inner {
  width: min(100%, 1440px);
  margin: 0 auto;
  min-width: 0;
}

.admin-content-inner > * + * {
  margin-top: 14px;
}

.ticker-label {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding-right: 4px;
}

.ticker-label strong {
  font-size: 12px;
  color: #284c5d;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.ticker-viewport {
  position: relative;
  min-width: 0;
  overflow: hidden;
  mask-image: linear-gradient(90deg, transparent 0, #000 5%, #000 95%, transparent 100%);
}

.ticker-track {
  display: inline-flex;
  align-items: center;
  gap: 28px;
  min-width: max-content;
  animation: ticker-scroll 34s linear infinite;
}

.ticker-item {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
  color: #476072;
  font-size: 13px;
  line-height: 1.35;
}

.ticker-item::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: rgba(23, 48, 66, 0.22);
}

.ticker-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: #173042;
  color: #fff;
  text-decoration: none;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  box-shadow: 0 10px 20px rgba(23, 48, 66, 0.2);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.admin-pulse .ticker-action {
  background: linear-gradient(135deg, #ffb25b, #e98a2f);
  color: #fff;
  box-shadow: 0 12px 22px rgba(178, 116, 36, 0.22);
}

.admin-pulse .ticker-label strong {
  color: #7b5924;
}

.admin-pulse .ticker-item {
  color: #516d7b;
}

.ribbon-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: linear-gradient(135deg, #57b5e7, #22c55e);
  box-shadow: 0 0 0 5px rgba(87, 181, 231, 0.14);
  animation: ribbon-status-pulse 2.4s ease-in-out infinite;
}

.ticker-action:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 24px rgba(23, 48, 66, 0.24);
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

@keyframes ticker-scroll {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(calc(-50% - 14px));
  }
}

@keyframes ribbon-status-pulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 6px rgba(87, 181, 231, 0.14);
  }
  50% {
    transform: scale(1.12);
    box-shadow: 0 0 0 9px rgba(87, 181, 231, 0.08);
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

.admin-mobile-rail .mobile-rail-toggle {
  border-color: rgba(16, 34, 42, 0.08);
  background: rgba(255, 255, 255, 0.92);
  color: #173042;
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

.admin-mobile-scroll {
  background: rgba(255, 255, 255, 0.94);
  border-color: rgba(16, 34, 42, 0.08);
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

.admin-mobile-scroll .mobile-rail-label {
  color: #7b5924;
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

.admin-mobile-link,
.admin-mobile-scroll .mobile-rail-link {
  border-color: rgba(16, 34, 42, 0.08);
  background: rgba(247, 251, 255, 0.94);
  color: #234;
}

.mobile-rail-link.router-link-active,
.mobile-rail-link.active {
  background: #173042;
  color: #fff;
  border-color: #173042;
}

.admin-mobile-scroll .mobile-rail-link.router-link-active {
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

.admin-mobile-scroll .mobile-rail-icon {
  background: rgba(23, 48, 66, 0.08);
}

.mobile-rail-link.router-link-active .mobile-rail-icon,
.mobile-rail-link.active .mobile-rail-icon,
.mobile-rail-logout .mobile-rail-icon {
  background: rgba(255, 255, 255, 0.18);
}

.admin-mobile-scroll .mobile-rail-link.router-link-active .mobile-rail-icon,
.admin-mobile-scroll .mobile-rail-logout .mobile-rail-icon {
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

@media (max-width: 1100px) {
  .admin-topnav {
    padding: 14px 16px 10px;
  }

  .admin-topnav-link {
    padding: 0 9px;
    font-size: 12px;
  }

  .admin-topnav-end {
    gap: 8px;
    margin-left: 8px;
  }
}

@media (max-width: 980px) {
  .desktop-only {
    display: none;
  }

  .mobile-only {
    display: block;
  }

  .mobile-topbar.mobile-only,
  .mobile-rail.mobile-only,
  .admin-mobile-topbar.mobile-only {
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

  .admin-content {
    padding: 12px 12px calc(64px + env(safe-area-inset-bottom));
  }

  .mobile-topbar,
  .admin-mobile-topbar {
    gap: 12px;
    padding: calc(10px + env(safe-area-inset-top)) 12px 8px;
  }

  .mobile-topbar strong,
  .admin-mobile-topbar strong {
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
    grid-template-columns: 1fr;
    gap: 10px;
    margin-bottom: 14px;
    padding: 12px;
    border-radius: 16px;
  }

  .ticker-label {
    padding-right: 0;
  }

  .ticker-viewport {
    mask-image: none;
  }

  .ticker-track {
    gap: 24px;
    animation-duration: 26s;
  }

  .ticker-item {
    font-size: 12px;
  }

  .ticker-action {
    width: 100%;
    min-height: 36px;
  }

  .admin-ribbon-side {
    justify-items: start;
    text-align: left;
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
