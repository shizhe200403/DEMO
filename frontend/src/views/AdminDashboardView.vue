<template>
  <section class="page admin-dashboard">

    <!-- 顶部控制台状态栏 -->
    <div class="console-topbar">
      <div class="console-topbar-left">
        <span class="console-tag">Admin Console</span>
        <h2>后台总览</h2>
      </div>
      <div class="console-topbar-right">
        <el-button :loading="loading" @click="loadOverview">刷新</el-button>
        <RouterLink class="topbar-link" to="/ops/logs">操作日志</RouterLink>
        <RouterLink class="topbar-link" to="/ops/reports">运营复核</RouterLink>
        <RouterLink class="topbar-link topbar-link-ghost" to="/">回前台</RouterLink>
      </div>
    </div>

    <PageStateBlock
      v-if="auth.isAuthenticated && !auth.user"
      tone="loading"
      title="正在确认管理员身份"
      description="先把当前账号权限拉齐，再展开后台总览。"
      compact
    />
    <PageStateBlock
      v-else-if="!isManagerUser"
      tone="error"
      title="当前账号没有后台权限"
      description="后台总览只对 manager 级账号开放。"
      action-label="回到首页"
      @action="router.push('/')"
    />
    <template v-else>
      <CollectionSkeleton v-if="loading && !overview" variant="dashboard" :card-count="5" />
      <RefreshFrame v-else :active="loading" label="正在同步后台工作台总览">

        <!-- 双栏主体 -->
        <div class="console-layout">

          <!-- 左栏：状态聚合 -->
          <aside class="console-sidebar">

            <!-- 关键指标 -->
            <div class="sidebar-card">
              <span class="sidebar-label">关键指标</span>
              <div class="kpi-list">
                <div class="kpi-item" :class="summary.users_pending > 0 ? 'kpi-warn' : 'kpi-ok'">
                  <div class="kpi-body">
                    <span>待处理账号</span>
                    <strong>{{ summary.users_pending }}</strong>
                  </div>
                  <span class="kpi-badge">{{ summary.users_pending > 0 ? '需处理' : '正常' }}</span>
                </div>
                <div class="kpi-item" :class="moderationBacklog > 0 ? 'kpi-warn' : 'kpi-ok'">
                  <div class="kpi-body">
                    <span>内容待审合计</span>
                    <strong>{{ moderationBacklog }}</strong>
                  </div>
                  <span class="kpi-badge">{{ moderationBacklog > 0 ? '有积压' : '已清空' }}</span>
                </div>
                <div class="kpi-item" :class="summary.report_tasks_failed > 0 ? 'kpi-risk' : 'kpi-ok'">
                  <div class="kpi-body">
                    <span>报表失败任务</span>
                    <strong>{{ summary.report_tasks_failed }}</strong>
                  </div>
                  <span class="kpi-badge">{{ summary.report_tasks_failed > 0 ? '有异常' : '正常' }}</span>
                </div>
                <div class="kpi-item kpi-neutral">
                  <div class="kpi-body">
                    <span>活跃用户数</span>
                    <strong>{{ summary.users_active }}</strong>
                  </div>
                  <span class="kpi-badge">近期</span>
                </div>
              </div>
            </div>

            <!-- 细粒度数据 -->
            <div class="sidebar-card">
              <span class="sidebar-label">分项速览</span>
              <div class="stat-rows">
                <div class="stat-row">
                  <span>总用户</span>
                  <strong>{{ summary.users_total }}</strong>
                </div>
                <div class="stat-row">
                  <span>待审帖子</span>
                  <strong :class="summary.posts_pending > 0 ? 'num-warn' : ''">{{ summary.posts_pending }}</strong>
                </div>
                <div class="stat-row">
                  <span>待审菜谱</span>
                  <strong :class="summary.recipes_pending > 0 ? 'num-warn' : ''">{{ summary.recipes_pending }}</strong>
                </div>
                <div class="stat-row">
                  <span>待处理举报</span>
                  <strong :class="summary.pending_reports > 0 ? 'num-warn' : ''">{{ summary.pending_reports }}</strong>
                </div>
                <div class="stat-row">
                  <span>隐藏评论</span>
                  <strong :class="summary.hidden_comments > 0 ? 'num-warn' : ''">{{ summary.hidden_comments }}</strong>
                </div>
                <div class="stat-row">
                  <span>7日记录用户</span>
                  <strong>{{ summary.active_record_users_last_7_days }}</strong>
                </div>
              </div>
            </div>

            <!-- 快捷跳转 -->
            <div class="sidebar-card">
              <span class="sidebar-label">快捷入口</span>
              <div class="shortcut-links">
                <RouterLink class="shortcut-link shortcut-link-primary" to="/ops/users?preset=pending&status=pending">
                  <strong>待确认账号</strong>
                  <span>{{ summary.users_pending }} 个</span>
                </RouterLink>
                <RouterLink class="shortcut-link" to="/ops/community?preset=pending_reports&report_status=pending">
                  <strong>社区举报</strong>
                  <span>{{ summary.pending_reports }} 条待处理</span>
                </RouterLink>
                <RouterLink class="shortcut-link" to="/ops/recipes?preset=pending&audit_status=pending">
                  <strong>待审菜谱</strong>
                  <span>{{ summary.recipes_pending }} 条待审</span>
                </RouterLink>
                <RouterLink class="shortcut-link" to="/ops/reports">
                  <strong>报表链路</strong>
                  <span>查看失败与近期任务</span>
                </RouterLink>
                <RouterLink class="shortcut-link" to="/ops/logs">
                  <strong>操作日志</strong>
                  <span>确认改动上下文</span>
                </RouterLink>
              </div>
            </div>
          </aside>

          <!-- 右栏：工作区 -->
          <main class="console-main">

            <!-- 值守建议 -->
            <div class="stage-banner">
              <div class="stage-banner-copy">
                <span class="stage-badge">{{ operationsStage.badge }}</span>
                <strong>{{ operationsStage.title }}</strong>
                <p>{{ operationsStage.copy }}</p>
              </div>
              <el-button type="primary" @click="goToWorkbench(operationsStage.link)">{{ operationsStage.cta }}</el-button>
            </div>

            <!-- 三项判断结论 -->
            <div class="conclusion-row">
              <div
                v-for="item in managerConclusions"
                :key="item.label"
                class="conclusion-card"
                :class="`tone-${item.tone}`"
              >
                <div class="conclusion-dot" />
                <div>
                  <span>{{ item.label }}</span>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.copy }}</p>
                </div>
              </div>
            </div>

            <!-- 队列告警横排 -->
            <div v-if="queueSummaries.length" class="queue-strip">
              <div
                v-for="item in queueSummaries"
                :key="item.key"
                class="queue-card"
                :class="`tone-${item.tone}`"
                v-spotlight
              >
                <span>{{ item.label }}</span>
                <strong>{{ item.count }}</strong>
                <p>{{ item.description }}</p>
                <el-button text size="small" @click="goToWorkbench(item.link)">去处理</el-button>
              </div>
            </div>

            <!-- 下方双列：待处理对象 + 报表任务 -->
            <div class="lower-cols">

              <!-- 待处理对象 -->
              <div class="console-panel">
                <div class="panel-hd">
                  <h3>最近待处理对象</h3>
                </div>
                <div v-if="recentWorkItems.length" class="work-list">
                  <div v-for="item in recentWorkItems" :key="item.key" class="work-item">
                    <div class="work-copy">
                      <span>{{ item.label }}</span>
                      <strong>{{ item.title }}</strong>
                      <p>{{ item.description }}</p>
                    </div>
                    <div class="work-meta">
                      <small>{{ formatDateTime(item.created_at || undefined) }}</small>
                      <el-button text type="primary" size="small" @click="goToWorkbench(item.link)">处理</el-button>
                    </div>
                  </div>
                </div>
                <PageStateBlock v-else tone="empty" title="当前没有待处理对象" description="队列已压平，可继续回看日志。" compact />
              </div>

              <!-- 报表任务 -->
              <div class="console-panel">
                <div class="panel-hd">
                  <h3>最近报表任务</h3>
                </div>
                <div v-if="recentTasks.length" class="task-list">
                  <div v-for="task in recentTasks" :key="task.task_id" class="task-item">
                    <div class="task-hd">
                      <div>
                        <strong>{{ task.user.display_name }}</strong>
                        <span>{{ reportTypeLabel(task.report_type) }} · {{ formatDateRange(task.start_date || undefined, task.end_date || undefined) }}</span>
                      </div>
                      <el-tag :type="taskStatusTagType(task.status)" effect="light" size="small">{{ taskStatusLabel(task.status) }}</el-tag>
                    </div>
                    <p>{{ taskInsight(task) }}</p>
                    <div class="task-ft">
                      <span>{{ formatDateTime(task.generated_at || undefined) }}</span>
                      <a v-if="task.file_url" :href="task.file_url" target="_blank" rel="noreferrer">打开文件</a>
                    </div>
                  </div>
                </div>
                <PageStateBlock v-else tone="empty" title="最近还没有报表任务" description="等用户生成周报或月报后才会出现。" compact />
              </div>

            </div>
          </main>
        </div>
      </RefreshFrame>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import type { AdminOperationsOverviewData, AdminOperationsSummary, AdminQueueSummary, AdminRecentReportTask, AdminRecentWorkItem, AdminWorkbenchLink } from "../api/adminReports";
import { getAdminOperationsOverview } from "../api/adminReports";
import { notifyLoadError } from "../lib/feedback";
import { isOpsManager } from "../lib/opsAccess";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const loading = ref(false);
const overview = ref<AdminOperationsOverviewData | null>(null);

const emptySummary: AdminOperationsSummary = {
  users_total: 0,
  users_active: 0,
  users_pending: 0,
  recipes_total: 0,
  recipes_pending: 0,
  recipes_rejected: 0,
  posts_total: 0,
  posts_pending: 0,
  posts_rejected: 0,
  pending_reports: 0,
  hidden_comments: 0,
  meal_records_last_7_days: 0,
  active_record_users_last_7_days: 0,
  report_tasks_total: 0,
  report_tasks_processing: 0,
  report_tasks_failed: 0,
  report_tasks_completed: 0,
};

const isManagerUser = computed(() => isOpsManager(auth.user));
const summary = computed(() => overview.value?.summary ?? emptySummary);
const queueSummaries = computed<AdminQueueSummary[]>(() => overview.value?.queue_summaries ?? []);
const recentWorkItems = computed<AdminRecentWorkItem[]>(() => overview.value?.recent_work_items ?? []);
const recentTasks = computed<AdminRecentReportTask[]>(() => overview.value?.recent_tasks ?? []);
const moderationBacklog = computed(() => summary.value.recipes_pending + summary.value.posts_pending + summary.value.pending_reports);
const operationsStage = computed(() => {
  const pendingUsers = queueSummaries.value.find((item) => item.key === "pending_users");
  if (pendingUsers && pendingUsers.count > 0) {
    return {
      badge: "Account First",
      title: pendingUsers.title,
      copy: "账号待处理是 manager 最该先压平的入口，避免后续内容和权限问题继续外溢。",
      cta: "进入用户队列",
      link: pendingUsers.link,
    };
  }

  if (queueSummaries.value.length > 0) {
    const top = queueSummaries.value[0];
    return {
      badge: top.count > 0 ? "Queue First" : "Stable",
      title: top.title,
      copy: top.description,
      cta: top.count > 0 ? "进入处理队列" : "查看当前值守页",
      link: top.link,
    };
  }

  return {
    badge: "Stable",
    title: "当前后台节奏相对稳定",
    copy: "账号、内容和报表链路都没有明显失衡，适合继续做常规复核而不是紧急救火。",
    cta: "查看操作日志",
    link: { path: "/ops/logs", query: {} },
  };
});
const managerConclusions = computed(() => [
  {
    label: "账号判断",
    title: summary.value.users_pending > 0 ? "账号确认队列仍有积压" : "账号入口当前相对稳定",
    copy: summary.value.users_pending > 0
      ? `当前还有 ${summary.value.users_pending} 个账号待处理，建议 manager 先确认资料缺口、角色边界和状态异常。`
      : "当前没有明显 pending 账号积压，可以更多关注内容处理和日志复盘。",
    tone: summary.value.users_pending > 0 ? "warning" : "good",
  },
  {
    label: "内容判断",
    title: moderationBacklog.value > 0 ? "内容队列还没压平" : "内容处理压力相对可控",
    copy: moderationBacklog.value > 0
      ? `帖子、菜谱和举报合计还有 ${moderationBacklog.value} 条待处理，适合先让后台重新回到清队列节奏。`
      : "当前内容审核没有明显堆积，可以把精力放在账号质量和链路复核上。",
    tone: moderationBacklog.value > 0 ? "warning" : "good",
  },
  {
    label: "复盘判断",
    title: summary.value.report_tasks_failed > 0 ? "报表链路存在失败信号" : "报表链路目前稳定",
    copy: summary.value.report_tasks_failed > 0
      ? `已有 ${summary.value.report_tasks_failed} 条失败任务，建议尽快回运营复核页确认是否是生成链路或数据源异常。`
      : "当前没有明显失败任务，说明复盘能力还在稳定沉淀。",
    tone: summary.value.report_tasks_failed > 0 ? "risk" : "good",
  },
]);

onMounted(() => {
  if (isManagerUser.value) {
    void loadOverview();
  }
});

async function loadOverview() {
  if (!isManagerUser.value) return;
  loading.value = true;
  try {
    const response = await getAdminOperationsOverview();
    overview.value = response?.data ?? null;
  } catch {
    notifyLoadError("后台总览");
  } finally {
    loading.value = false;
  }
}

function goToWorkbench(link: AdminWorkbenchLink) {
  router.push({ path: link.path, query: link.query ?? {} });
}

function reportTypeLabel(value: string) {
  return (
    {
      weekly: "周报",
      monthly: "月报",
    }[value] || value
  );
}

function taskStatusLabel(value: string) {
  return (
    {
      pending: "待处理",
      processing: "生成中",
      completed: "已完成",
      failed: "失败",
    }[value] || value
  );
}

function taskStatusTagType(value: string) {
  return (
    {
      pending: "warning",
      processing: "info",
      completed: "success",
      failed: "danger",
    }[value] || "info"
  );
}

function taskInsight(task: Record<string, any>) {
  if (task.status === "failed") return "这条任务失败了，建议确认是生成链路异常还是数据源问题。";
  if (task.status === "processing") return "任务仍在处理中，适合顺手观察是否存在长时间卡住的情况。";
  if (task.status === "completed") return "任务已经完成，说明最近仍有人在使用复盘能力。";
  return "这条任务还在等待处理。";
}

function formatDateTime(value?: string) {
  if (!value) return "暂无";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "暂无";
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatDateRange(start?: string, end?: string) {
  if (!start || !end) return "时间未填";
  return `${start} 至 ${end}`;
}
</script>

<style scoped>
.admin-dashboard {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 0;
}

/* ── 顶部状态栏 ───────────────────────────────── */
.console-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 24px;
  background: #0f1e29;
  flex-wrap: wrap;
}

.console-topbar-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.console-tag {
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(163, 204, 224, 0.7);
  font-weight: 700;
}

.console-topbar-left h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #f0f7fc;
}

.console-topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.topbar-link {
  display: inline-flex;
  align-items: center;
  height: 34px;
  padding: 0 14px;
  border-radius: 8px;
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  color: rgba(220, 238, 250, 0.85);
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: background 0.2s, border-color 0.2s;
}

.topbar-link:hover {
  background: rgba(255, 255, 255, 0.13);
  border-color: rgba(255, 255, 255, 0.18);
}

.topbar-link-ghost {
  color: #173042;
  background: rgba(240, 247, 252, 0.92);
  border-color: transparent;
}

.topbar-link-ghost:hover {
  background: #fff;
}

/* ── 双栏布局 ─────────────────────────────────── */
.console-layout {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  min-height: calc(100vh - 62px);
  align-items: start;
}

/* ── 左侧栏 ───────────────────────────────────── */
.console-sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 14px 18px 18px;
  border-right: 1px solid rgba(16, 34, 42, 0.08);
  position: sticky;
  top: 0;
  max-height: 100vh;
  overflow-y: auto;
  scrollbar-width: thin;
  background: rgba(248, 251, 254, 0.7);
}

.sidebar-card {
  background: #fff;
  border: 1px solid rgba(16, 34, 42, 0.08);
  border-radius: 16px;
  padding: 14px;
  box-shadow: 0 2px 10px rgba(15, 30, 39, 0.04);
}

.sidebar-label {
  display: block;
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-weight: 700;
  color: #6b8899;
  margin-bottom: 10px;
}

/* KPI 列表 */
.kpi-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kpi-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(16, 34, 42, 0.07);
  background: rgba(247, 251, 255, 0.9);
}

.kpi-body {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.kpi-body span {
  font-size: 11px;
  color: #6b8899;
}

.kpi-body strong {
  font-size: 22px;
  font-weight: 700;
  line-height: 1.1;
  color: #173042;
}

.kpi-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 999px;
  background: #e8f1f7;
  color: #3a6070;
  flex-shrink: 0;
}

.kpi-ok .kpi-badge { background: rgba(220, 247, 232, 0.9); color: #1a6644; }
.kpi-ok { border-color: rgba(34, 197, 94, 0.12); }
.kpi-warn .kpi-badge { background: rgba(255, 237, 200, 0.9); color: #9a6010; }
.kpi-warn { border-color: rgba(245, 158, 11, 0.16); }
.kpi-risk .kpi-badge { background: rgba(255, 225, 225, 0.9); color: #9a2020; }
.kpi-risk { border-color: rgba(239, 68, 68, 0.16); }
.kpi-neutral { border-color: rgba(16, 34, 42, 0.07); }

/* 分项速览 */
.stat-rows {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.stat-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 0;
  border-bottom: 1px solid rgba(16, 34, 42, 0.05);
  font-size: 13px;
}

.stat-row:last-child { border-bottom: none; }

.stat-row span { color: #5b7888; }
.stat-row strong { font-weight: 700; color: #173042; font-size: 15px; }
.num-warn { color: #c0721a !important; }

/* 快捷入口 */
.shortcut-links {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.shortcut-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 10px;
  background: rgba(247, 251, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.07);
  text-decoration: none;
  transition: background 0.2s, border-color 0.2s, transform 0.2s;
}

.shortcut-link:hover {
  background: #fff;
  border-color: rgba(16, 34, 42, 0.14);
  transform: translateX(2px);
}

.shortcut-link strong {
  font-size: 13px;
  font-weight: 600;
  color: #173042;
}

.shortcut-link span {
  font-size: 11px;
  color: #7a96a4;
}

.shortcut-link-primary {
  background: #173042;
  border-color: #173042;
}

.shortcut-link-primary:hover {
  background: #1e3f58;
  border-color: #1e3f58;
}

.shortcut-link-primary strong,
.shortcut-link-primary span {
  color: #e8f4fc;
}

/* ── 右侧主区 ─────────────────────────────────── */
.console-main {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 20px 22px 28px;
}

/* 值守建议横幅 */
.stage-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 18px;
  background: linear-gradient(135deg, #173042 0%, #254f68 100%);
  box-shadow: 0 8px 28px rgba(23, 48, 66, 0.22);
}

.stage-banner-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stage-badge {
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(163, 210, 240, 0.8);
  font-weight: 700;
}

.stage-banner strong {
  font-size: 20px;
  font-weight: 700;
  color: #f0f7fc;
  line-height: 1.2;
}

.stage-banner p {
  margin: 0;
  font-size: 13px;
  color: rgba(220, 238, 250, 0.75);
  line-height: 1.55;
  max-width: 520px;
}

/* 三项判断 */
.conclusion-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.conclusion-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(247, 251, 255, 0.94);
  border: 1px solid rgba(16, 34, 42, 0.07);
}

.conclusion-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #c0d8e4;
  flex-shrink: 0;
  margin-top: 5px;
}

.conclusion-card.tone-good .conclusion-dot { background: #34c97a; }
.conclusion-card.tone-warning .conclusion-dot { background: #f59e0b; }
.conclusion-card.tone-risk .conclusion-dot { background: #ef4444; }
.conclusion-card.tone-good { border-color: rgba(34, 197, 94, 0.14); }
.conclusion-card.tone-warning { border-color: rgba(245, 158, 11, 0.16); }
.conclusion-card.tone-risk { border-color: rgba(239, 68, 68, 0.14); }

.conclusion-card span {
  display: block;
  font-size: 11px;
  color: #6b8899;
  letter-spacing: 0.06em;
  margin-bottom: 2px;
}

.conclusion-card strong {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #173042;
  margin-bottom: 4px;
}

.conclusion-card p {
  margin: 0;
  font-size: 12px;
  color: #5b7888;
  line-height: 1.5;
}

/* 队列告警 */
.queue-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
}

.queue-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(247, 251, 255, 0.94);
  border: 1px solid rgba(16, 34, 42, 0.08);
  transition: transform 0.25s cubic-bezier(0.22, 1.2, 0.36, 1), box-shadow 0.25s ease;
}

.queue-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(15, 30, 39, 0.08);
}

.queue-card span { font-size: 11px; color: #6b8899; }
.queue-card strong { font-size: 26px; font-weight: 700; color: #173042; line-height: 1; }
.queue-card p { margin: 0; font-size: 12px; color: #5b7888; line-height: 1.4; flex: 1; }

/* 下方双列 */
.lower-cols {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.console-panel {
  background: #fff;
  border: 1px solid rgba(16, 34, 42, 0.08);
  border-radius: 18px;
  padding: 18px;
  box-shadow: 0 2px 10px rgba(15, 30, 39, 0.04);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.panel-hd h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #173042;
}

/* 待处理对象 */
.work-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.work-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  padding: 11px 13px;
  border-radius: 12px;
  background: rgba(247, 251, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.work-copy { display: flex; flex-direction: column; gap: 2px; flex: 1; }
.work-copy span { font-size: 11px; color: #6b8899; }
.work-copy strong { font-size: 14px; font-weight: 600; color: #173042; }
.work-copy p { margin: 0; font-size: 12px; color: #5b7888; line-height: 1.4; }

.work-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.work-meta small { font-size: 11px; color: #7a96a4; }

/* 报表任务 */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(247, 251, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.06);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.task-hd {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.task-hd > div { display: flex; flex-direction: column; gap: 2px; }
.task-hd strong { font-size: 14px; font-weight: 600; color: #173042; }
.task-hd span { font-size: 11px; color: #6b8899; }

.task-item p { margin: 0; font-size: 12px; color: #5b7888; line-height: 1.45; }

.task-ft {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.task-ft span { font-size: 11px; color: #7a96a4; }
.task-ft a { font-size: 12px; font-weight: 700; color: #1f4f67; text-decoration: none; }

/* ── 响应式 ───────────────────────────────────── */
@media (max-width: 1100px) {
  .conclusion-row {
    grid-template-columns: 1fr 1fr;
  }

  .lower-cols {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .console-layout {
    grid-template-columns: 1fr;
  }

  .console-sidebar {
    position: static;
    max-height: none;
    border-right: none;
    border-bottom: 1px solid rgba(16, 34, 42, 0.08);
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    padding: 16px;
  }

  .conclusion-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .console-topbar {
    padding: 12px 16px;
  }

  .console-main {
    padding: 14px 16px 20px;
  }

  .console-sidebar {
    grid-template-columns: 1fr;
  }

  .stage-banner {
    flex-direction: column;
    align-items: flex-start;
  }

  .queue-strip {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
