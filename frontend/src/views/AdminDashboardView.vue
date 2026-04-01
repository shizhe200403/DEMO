<template>
  <section class="page admin-dashboard">
    <div class="head">
      <div>
        <p class="tag">Admin Console</p>
        <h2>后台总览</h2>
      </div>
      <div class="head-actions">
        <el-button type="primary" :loading="loading" @click="loadOverview">刷新总览</el-button>
        <RouterLink class="ghost-link" to="/ops/logs">进入操作日志</RouterLink>
        <RouterLink class="ghost-link" to="/ops/reports">进入运营复核</RouterLink>
        <RouterLink class="ghost-link ghost-link-soft" to="/">回前台首页</RouterLink>
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
      description="后台总览只对 manager 级账号开放，普通账号和 auditor 不会进入这里。"
      action-label="回到首页"
      @action="router.push('/')"
    />
    <template v-else>
      <CollectionSkeleton v-if="loading && !overview" variant="dashboard" :card-count="5" />
      <RefreshFrame v-else :active="loading" label="正在同步后台工作台总览">
        <div class="summary-grid">
          <article v-spotlight>
            <span>待处理账号</span>
            <strong>{{ summary.users_pending }}</strong>
            <p>manager 最值得优先看的入口，直接决定是否有人卡在账号确认链路里。</p>
          </article>
          <article v-spotlight>
            <span>当前活跃用户</span>
            <strong>{{ summary.users_active }}</strong>
            <p>和最近真实记录量一起看，能更快判断问题偏增长、留存还是链路摩擦。</p>
          </article>
          <article v-spotlight>
            <span>内容待处理总量</span>
            <strong>{{ moderationBacklog }}</strong>
            <p>帖子、菜谱和举报如果同时堆积，说明后台已经偏离日常维护节奏。</p>
          </article>
          <article v-spotlight>
            <span>报表失败任务</span>
            <strong>{{ summary.report_tasks_failed }}</strong>
            <p>失败任务会直接影响复盘稳定性，manager 也需要及时感知这条链路是否失衡。</p>
          </article>
        </div>

        <div class="ops-alert-strip">
          <article v-for="item in queueSummaries" :key="item.key" class="ops-alert-card" :class="`tone-${item.tone}`" v-spotlight>
            <span>{{ item.label }}</span>
            <strong>{{ item.count }}</strong>
            <p>{{ item.description }}</p>
            <el-button text type="primary" @click="goToWorkbench(item.link)">{{ item.title }}</el-button>
          </article>
        </div>

        <div class="admin-grid">
          <article class="card console-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>今日值守建议</h3>
                <p>先把最影响后台处理效率的入口选出来，再落到具体队列，不在首页停留太久。</p>
              </div>
            </div>
            <article class="review-stage-card">
              <div>
                <span>{{ operationsStage.badge }}</span>
                <strong>{{ operationsStage.title }}</strong>
                <p>{{ operationsStage.copy }}</p>
              </div>
              <el-button type="primary" @click="goToWorkbench(operationsStage.link)">{{ operationsStage.cta }}</el-button>
            </article>

            <div class="conclusion-list">
              <article v-for="item in managerConclusions" :key="item.label" class="conclusion-item" :class="`tone-${item.tone}`">
                <span>{{ item.label }}</span>
                <strong>{{ item.title }}</strong>
                <p>{{ item.copy }}</p>
              </article>
            </div>
          </article>

          <article class="card console-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>最近待处理对象</h3>
                <p>从首页直接落到对象级处理，不再只停在抽象指标上。</p>
              </div>
            </div>
            <div v-if="recentWorkItems.length" class="sample-list">
              <article v-for="item in recentWorkItems" :key="item.key" class="sample-item">
                <div class="sample-copy">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.description }}</p>
                </div>
                <div class="sample-meta sample-meta-stack">
                  <small>{{ formatDateTime(item.created_at || undefined) }}</small>
                  <el-button text type="primary" @click="goToWorkbench(item.link)">直接处理</el-button>
                </div>
              </article>
            </div>
            <PageStateBlock
              v-else
              tone="empty"
              title="当前没有额外待处理对象"
              description="如果队列已经压平，可以继续回看日志或切到运营复核页。"
              compact
            />
          </article>

          <article class="card console-card quick-actions" v-spotlight>
            <div class="card-head">
              <div>
                <h3>后台快捷动作</h3>
                <p>manager 高频动作继续收口在这里，但都直接落到可处理页面。</p>
              </div>
            </div>
            <RouterLink class="action-link action-link-primary" to="/ops/users?preset=pending&status=pending">
              <strong>处理待确认账号</strong>
              <span>直接进入用户队列，优先看 pending 账号和状态异常。</span>
            </RouterLink>
            <RouterLink class="action-link" to="/ops/community?preset=pending_reports&report_status=pending">
              <strong>处理社区举报</strong>
              <span>直接落到待处理举报视角，不再从总览页二次筛选。</span>
            </RouterLink>
            <RouterLink class="action-link" to="/ops/recipes?preset=pending&audit_status=pending">
              <strong>处理待审核菜谱</strong>
              <span>直接看 audit pending 的菜谱队列，压平内容处理积压。</span>
            </RouterLink>
            <RouterLink class="action-link" to="/ops/reports">
              <strong>查看报表链路</strong>
              <span>回到运营复核页确认失败任务、近期报表和活跃记录信号。</span>
            </RouterLink>
            <RouterLink class="action-link" to="/ops/logs">
              <strong>回看最近操作</strong>
              <span>先确认后台是谁改了什么，避免处理结果和上下文断开。</span>
            </RouterLink>
          </article>
        </div>

        <div class="admin-lower-grid">
          <article class="card console-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>最近报表任务</h3>
                <p>manager 需要知道复盘链路是不是仍有人在用，以及失败是否已经开始积压。</p>
              </div>
            </div>
            <div v-if="recentTasks.length" class="task-list">
              <article v-for="task in recentTasks" :key="task.task_id" class="task-item">
                <div class="task-head">
                  <div>
                    <strong>{{ task.user.display_name }}</strong>
                    <span>{{ reportTypeLabel(task.report_type) }} · {{ formatDateRange(task.start_date || undefined, task.end_date || undefined) }}</span>
                  </div>
                  <el-tag :type="taskStatusTagType(task.status)" effect="light">{{ taskStatusLabel(task.status) }}</el-tag>
                </div>
                <p>{{ taskInsight(task) }}</p>
                <div class="task-meta">
                  <span>生成时间：{{ formatDateTime(task.generated_at || undefined) }}</span>
                  <a v-if="task.file_url" :href="task.file_url" target="_blank" rel="noreferrer">打开文件</a>
                </div>
              </article>
            </div>
            <PageStateBlock
              v-else
              tone="empty"
              title="最近还没有报表任务"
              description="等用户持续生成周报或月报后，这里才会积累 manager 可用的复盘线索。"
              compact
            />
          </article>

          <article class="card console-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>后台管理速览</h3>
                <p>把 manager 最常需要一起看的几个指标压成一眼可判断的板块。</p>
              </div>
            </div>
            <div class="stats-grid">
              <article>
                <span>总用户</span>
                <strong>{{ summary.users_total }}</strong>
                <p>和待处理账号一起看，能更快区分是新增流入问题还是审核处理问题。</p>
              </article>
              <article>
                <span>待审核帖子</span>
                <strong>{{ summary.posts_pending }}</strong>
                <p>帖子积压会让社区停在半开放状态，适合和举报一起联动看。</p>
              </article>
              <article>
                <span>待审核菜谱</span>
                <strong>{{ summary.recipes_pending }}</strong>
                <p>菜谱审核会直接影响推荐和前台可见内容质量。</p>
              </article>
              <article>
                <span>已隐藏评论</span>
                <strong>{{ summary.hidden_comments }}</strong>
                <p>{{ summary.hidden_comments ? "隐藏评论已经开始积累，建议顺手回社区页复核评论风险。" : "当前隐藏评论压力不大，可以把注意力先放在账号和待审队列。" }}</p>
              </article>
            </div>
          </article>
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
  gap: 18px;
}

.head-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.ops-alert-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.ops-alert-card {
  display: grid;
  gap: 6px;
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background:
    linear-gradient(135deg, rgba(252, 254, 255, 0.96), rgba(242, 248, 252, 0.94)),
    radial-gradient(circle at top right, rgba(87, 181, 231, 0.12), transparent 34%);
}

.ops-alert-card span {
  color: #638295;
  font-size: 12px;
}

.ops-alert-card strong {
  color: #173042;
  font-size: 28px;
}

.ops-alert-card p {
  margin: 0;
  color: #557383;
  line-height: 1.6;
}

.ghost-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  padding: 0 16px;
  border-radius: 999px;
  text-decoration: none;
  font-weight: 700;
  color: #f3f7fb;
  background: linear-gradient(135deg, #173042, #28546b);
  box-shadow: 0 16px 28px rgba(11, 22, 35, 0.18);
}

.ghost-link-soft {
  color: #173042;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: none;
}

.admin-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr 0.95fr;
  gap: 16px;
}

.admin-lower-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 16px;
}

.console-card {
  display: grid;
  gap: 16px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.card-head h3 {
  margin: 0;
  font-size: 20px;
  color: #173042;
}

.card-head p {
  margin: 6px 0 0;
  color: #5b7888;
  line-height: 1.65;
}

.review-stage-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  padding: 18px;
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(23, 48, 66, 0.96), rgba(40, 84, 107, 0.92)),
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.12), transparent 38%);
}

.review-stage-card span,
.review-stage-card strong,
.review-stage-card p {
  color: #f7fbff;
}

.review-stage-card span {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.review-stage-card strong {
  display: block;
  margin-top: 4px;
  font-size: 20px;
}

.review-stage-card p {
  margin: 8px 0 0;
  line-height: 1.7;
  color: rgba(242, 247, 251, 0.84);
}

.conclusion-list,
.sample-list,
.quick-actions,
.task-list {
  display: grid;
  gap: 12px;
}

.conclusion-item,
.sample-item,
.action-link,
.task-item,
.stats-grid article {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(247, 251, 255, 0.92);
}

.conclusion-item span,
.sample-copy span,
.task-head span,
.stats-grid span {
  color: #638295;
  font-size: 12px;
}

.conclusion-item strong,
.sample-copy strong,
.task-head strong,
.stats-grid strong,
.action-link strong {
  color: #173042;
  font-size: 15px;
}

.conclusion-item p,
.sample-copy p,
.task-item p,
.stats-grid p,
.action-link span {
  margin: 0;
  color: #557383;
  line-height: 1.65;
}

.tone-good {
  border-color: rgba(34, 197, 94, 0.16);
}

.tone-warning {
  border-color: rgba(245, 158, 11, 0.18);
}

.tone-risk {
  border-color: rgba(239, 68, 68, 0.16);
}

.sample-item {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.sample-copy {
  display: grid;
  gap: 4px;
}

.sample-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  align-items: center;
}

.sample-meta-stack {
  display: grid;
  justify-items: end;
}

.sample-meta small,
.task-meta span {
  color: #5b7888;
  font-size: 12px;
}

.action-link,
.task-meta a {
  color: inherit;
  text-decoration: none;
}

.action-link-primary {
  background: linear-gradient(135deg, rgba(23, 48, 66, 0.96), rgba(43, 83, 105, 0.92));
}

.action-link-primary strong,
.action-link-primary span {
  color: #f7fbff;
}

.task-head,
.task-meta {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.task-head > div {
  display: grid;
  gap: 4px;
}

.task-meta a {
  color: #1f4f67;
  font-weight: 700;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 1240px) {
  .ops-alert-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .admin-grid,
  .admin-lower-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .ops-alert-strip,
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .review-stage-card,
  .sample-item {
    grid-template-columns: 1fr;
  }

  .sample-meta,
  .sample-meta-stack {
    justify-items: start;
    justify-content: flex-start;
  }
}

@media (max-width: 720px) {
  .ghost-link {
    width: 100%;
  }
}
</style>
