<template>
  <section class="page admin-ops-reports">
    <div class="head">
      <div>
        <p class="tag">Operations Review</p>
        <h2>运营复核</h2>
      </div>
      <div class="head-actions">
        <el-button type="primary" :loading="loading" @click="loadOverview">刷新总览</el-button>
        <el-button plain @click="router.push('/reports')">去前台报表页</el-button>
      </div>
    </div>

    <PageStateBlock
      v-if="auth.isAuthenticated && !auth.user"
      tone="loading"
      title="正在确认后台身份"
      description="先把当前账号权限拉齐，再展开后台运营复核。"
      compact
    />
    <PageStateBlock
      v-else-if="!hasOpsUser"
      tone="error"
      title="当前账号没有后台权限"
      description="运营复核只对后台值守账号开放，普通账号不会显示这里。"
      action-label="回到首页"
      @action="router.push('/')"
    />
    <template v-else>
      <CollectionSkeleton v-if="loading && !overview" variant="dashboard" :card-count="5" />
      <RefreshFrame v-else :active="loading" label="正在同步后台运营概况">
        <div class="summary-grid">
          <article v-spotlight>
            <span>活跃用户</span>
            <strong>{{ summary.users_active }}</strong>
            <p>当前处于正常状态的用户总量。</p>
          </article>
          <article v-spotlight>
            <span>最近 7 天记录用户</span>
            <strong>{{ summary.active_record_users_last_7_days }}</strong>
            <p>这能更直接反映系统最近有没有被真实持续使用。</p>
          </article>
          <article v-spotlight>
            <span>待处理内容</span>
            <strong>{{ moderationBacklog }}</strong>
            <p>帖子、菜谱和举报的待处理总量，决定后台现在更偏审核还是偏维护。</p>
          </article>
          <article v-spotlight>
            <span>报表失败任务</span>
            <strong>{{ summary.report_tasks_failed }}</strong>
            <p>失败任务过多时，用户会明显感觉复盘能力不稳定。</p>
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
                <h3>当前后台判断</h3>
                <p>先把后台今天最值得值守的入口选出来，再进入具体处理页面。</p>
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
              <article v-for="item in operationConclusions" :key="item.label" class="conclusion-item" :class="`tone-${item.tone}`">
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
                <p>从这里直接落到具体队列，而不是停在说明性总览里。</p>
              </div>
            </div>
            <div v-if="recentWorkItems.length" class="health-list">
              <article v-for="item in recentWorkItems" :key="item.key" class="health-item">
                <div class="health-copy">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.description }}</p>
                </div>
                <div class="health-actions">
                  <small>{{ formatDateTime(item.created_at || undefined) }}</small>
                  <el-button text type="primary" @click="goToWorkbench(item.link)">直接处理</el-button>
                </div>
              </article>
            </div>
            <PageStateBlock
              v-else
              tone="empty"
              title="当前没有额外待处理对象"
              description="如果队列已经压平，可以继续看最近报表任务或回到其他模块复核。"
              compact
            />
          </article>
        </div>

        <div class="admin-grid lower-grid">
          <article class="card console-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>最近报表任务</h3>
                <p>这块用来确认最近有没有失败堆积，以及哪些用户仍在持续生成报表。</p>
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
              description="等用户生成周报或月报后，这里才会沉淀后台复核线索。"
              compact
            />
          </article>

          <article class="card console-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>运营速览</h3>
                <p>把最容易影响“系统像不像有人在用”的几个指标压成一眼可判断的板块。</p>
              </div>
            </div>
            <div class="stats-grid">
              <article>
                <span>总用户</span>
                <strong>{{ summary.users_total }}</strong>
                <p>和活跃用户一起看，能更快判断当前是增长问题还是留存问题。</p>
              </article>
              <article>
                <span>最近 7 天记录餐次</span>
                <strong>{{ summary.meal_records_last_7_days }}</strong>
                <p>这是比“打开过页面”更真实的活跃信号。</p>
              </article>
              <article>
                <span>累计报表任务</span>
                <strong>{{ summary.report_tasks_total }}</strong>
                <p>报表任务越稳定，系统的复盘资产就越像真的在沉淀。</p>
              </article>
              <article>
                <span>处理中任务</span>
                <strong>{{ summary.report_tasks_processing }}</strong>
                <p>{{ summary.report_tasks_processing ? "当前仍有报表在处理，说明有人正在用这条链路。" : "当前没有处理中任务，可以更关注失败和完成率。" }}</p>
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
import { hasOpsAccess, isOpsManager } from "../lib/opsAccess";
import { notifyLoadError } from "../lib/feedback";
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

const hasOpsUser = computed(() => hasOpsAccess(auth.user));
const isManagerUser = computed(() => isOpsManager(auth.user));
const summary = computed(() => overview.value?.summary ?? emptySummary);
const queueSummaries = computed<AdminQueueSummary[]>(() => overview.value?.queue_summaries ?? []);
const recentWorkItems = computed<AdminRecentWorkItem[]>(() => overview.value?.recent_work_items ?? []);
const recentTasks = computed<AdminRecentReportTask[]>(() => overview.value?.recent_tasks ?? []);
const moderationBacklog = computed(() => summary.value.recipes_pending + summary.value.posts_pending + summary.value.pending_reports);
const operationsStage = computed(() => {
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
  if (summary.value.active_record_users_last_7_days < Math.max(1, Math.floor(summary.value.users_active / 3))) {
    return {
      badge: "Usage Gap",
      title: "活跃用户和真实记录量之间有落差",
      copy: "后台这时更适合回看前台链路，判断是不是记录动作仍然太重或报表触发点不够清楚。",
      cta: "回前台记录页看链路",
      link: { path: "/records", query: {} },
    };
  }
  return {
    badge: "Stable",
    title: "当前后台节奏相对稳定",
    copy: "活跃、内容处理和报表任务都没有明显失衡，适合继续补细节而不是紧急救火。",
    cta: isManagerUser.value ? "回后台总览" : "留在运营复核",
    link: { path: isManagerUser.value ? "/ops" : "/ops/reports", query: {} },
  };
});
const operationConclusions = computed(() => [
  {
    label: "活跃判断",
    title: summary.value.active_record_users_last_7_days > 0 ? "最近确实有人持续记录" : "最近真实记录信号偏弱",
    copy: summary.value.active_record_users_last_7_days > 0
      ? `最近 7 天有 ${summary.value.active_record_users_last_7_days} 位用户留下了真实饮食记录，比单纯打开页面更可信。`
      : "如果长期没有真实记录流入，后台要优先怀疑执行链路是否仍然太重。",
    tone: summary.value.active_record_users_last_7_days > 0 ? "good" : "risk",
  },
  {
    label: "内容判断",
    title: moderationBacklog.value > 0 ? "内容处理仍有积压" : "内容审核队列相对平稳",
    copy: moderationBacklog.value > 0
      ? `当前还有 ${moderationBacklog.value} 条内容待处理，建议优先把审核队列清干净。`
      : "当前内容处理压力不大，可以把精力放到体验优化和指标复核。",
    tone: moderationBacklog.value > 0 ? "warning" : "good",
  },
  {
    label: "报表判断",
    title: summary.value.report_tasks_failed > 0 ? "报表链路出现失败" : "报表链路目前稳定",
    copy: summary.value.report_tasks_failed > 0
      ? `已经有 ${summary.value.report_tasks_failed} 条失败任务，最好尽快确认是数据问题还是生成链路问题。`
      : "当前没有明显失败任务，说明报表这条资产沉淀链路还算健康。",
    tone: summary.value.report_tasks_failed > 0 ? "risk" : "good",
  },
]);

onMounted(() => {
  if (hasOpsUser.value) {
    void loadOverview();
  }
});

async function loadOverview() {
  if (!hasOpsUser.value) return;
  loading.value = true;
  try {
    const response = await getAdminOperationsOverview();
    overview.value = response?.data ?? null;
  } catch {
    notifyLoadError("后台运营复核");
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
  if (task.status === "failed") return "这条任务失败了，建议确认生成链路或数据源是否有异常。";
  if (task.status === "processing") return "任务仍在处理中，后台可以顺手观察是否存在长时间卡住的情况。";
  if (task.status === "completed") return "任务已经完成，说明这位用户最近确实在使用复盘能力。";
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
.admin-ops-reports {
  gap: 18px;
}

.head-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.ops-alert-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
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

.admin-grid {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: 16px;
}

.lower-grid {
  align-items: start;
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
.health-list,
.task-list {
  display: grid;
  gap: 12px;
}

.conclusion-item,
.health-item,
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
.health-copy span,
.task-head span,
.stats-grid span {
  color: #638295;
  font-size: 12px;
}

.conclusion-item strong,
.health-copy strong,
.task-head strong,
.stats-grid strong {
  color: #173042;
  font-size: 15px;
}

.conclusion-item p,
.health-copy p,
.task-item p,
.stats-grid p {
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

.health-item {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.health-copy {
  display: grid;
  gap: 4px;
}

.health-item a,
.task-meta a {
  color: #1f4f67;
  text-decoration: none;
  font-weight: 700;
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

.task-meta span {
  color: #5b7888;
  font-size: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 1080px) {
  .ops-alert-strip,
  .admin-grid,
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .health-item,
  .review-stage-card {
    grid-template-columns: 1fr;
  }
}
</style>
