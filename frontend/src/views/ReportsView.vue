<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Reports</p>
        <h2>健康报表</h2>
      </div>
      <div class="head-actions">
        <CompactHint tone="accent" title="报表页说明" description="优先看看板和复盘主线，生成器与历史记录只是支持区，不需要每次都重新生成报表。" />
        <el-button :loading="loadingTasks" @click="loadReportTasks()">刷新记录</el-button>
      </div>
    </div>

    <CollectionSkeleton v-if="showReportsSkeleton" variant="list" :card-count="5" :show-toolbar="false" />
    <RefreshFrame v-else :active="showReportsRefreshing" label="正在同步报表状态">
    <ReportsDashboardBoard v-if="dashboardData" :dashboard="dashboardData" />

    <div class="reports-topline-layout">
      <aside class="reports-summary-column">
        <div class="summary-grid compact-summary-grid">
          <article>
            <span>累计报表</span>
            <strong>{{ reportSummary.total }}</strong>
            <p>可回看结果</p>
          </article>
          <article>
            <span>已完成</span>
            <strong>{{ reportSummary.completed }}</strong>
            <p>可直接打开</p>
          </article>
          <article>
            <span>生成中</span>
            <strong>{{ reportSummary.processing }}</strong>
            <p>{{ reportSummary.processing ? "自动刷新中" : "当前无任务" }}</p>
          </article>
          <article>
            <span>最近生成</span>
            <strong>{{ reportSummary.latestGenerated }}</strong>
            <p>判断是否需重跑</p>
          </article>
        </div>
      </aside>

      <div class="card review-stage-card">
        <div class="review-stage-head">
          <div>
            <p class="section-kicker">Stage Review</p>
            <div class="section-title-row">
              <h3>阶段复盘</h3>
              <CompactHint description="这块只负责一句话结论和当前最该做的事，细节解释交给下方看板和 AI。" />
            </div>
          </div>
          <span class="status-pill" :class="reviewStageTone">{{ reviewStageLabel }}</span>
        </div>

        <div class="review-hero">
          <div class="review-hero-copy">
            <span>当前最该关注</span>
            <strong>{{ reviewHeadline }}</strong>
            <p>{{ reviewSummary }}</p>
          </div>
          <div class="review-hero-actions">
            <el-button v-if="primaryReviewSuggestion" type="primary" @click="handleReportSuggestion(primaryReviewSuggestion)">{{ primaryReviewSuggestion.cta }}</el-button>
            <el-button v-else type="primary" @click="triggerRecommendedGeneration(reviewFallbackType)">
              {{ reviewFallbackType === "monthly" ? "生成推荐月报" : "生成推荐周报" }}
            </el-button>
            <el-button plain @click="openAssistantForReview">让 AI 解释这次复盘</el-button>
            <a v-if="latestCompletedTask?.file_url" class="review-link" :href="latestCompletedTask.file_url" target="_blank" rel="noreferrer">打开最新报表</a>
          </div>
        </div>

        <div class="review-metrics">
          <article v-for="item in reviewMetrics" :key="item.label" class="review-metric">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <p>{{ item.hint }}</p>
          </article>
        </div>

        <div class="review-conclusions">
          <article v-for="item in reviewConclusions" :key="item.label" class="review-conclusion" :class="`tone-${item.tone}`">
            <span>{{ item.label }}</span>
            <strong>{{ item.title }}</strong>
            <p>{{ item.copy }}</p>
          </article>
        </div>
      </div>
    </div>

    <div class="grid reports-focus-layout">
      <div class="card">
        <div class="card-head">
          <div>
            <div class="section-title-row">
              <h3>下周动作计划</h3>
              <CompactHint description="这里只保留最值得执行的少量动作，避免把计划页做成第二个说明区。" />
            </div>
          </div>
          <el-button text @click="openAssistantForNextWeekPlan">让 AI 生成行动版</el-button>
        </div>

        <article class="plan-focus-card">
          <div>
            <span>Plan Focus</span>
            <strong>{{ nextWeekFocusTitle }}</strong>
            <p>{{ nextWeekFocusCopy }}</p>
          </div>
          <div class="status-pill" :class="nextWeekFocusTone">{{ nextWeekFocusBadge }}</div>
        </article>

        <div v-if="nextWeekActionPlan.length" class="plan-list">
          <article v-for="(item, index) in nextWeekActionPlan" :key="item.key" class="plan-item">
            <div class="plan-index">{{ String(index + 1).padStart(2, "0") }}</div>
            <div class="plan-copy">
              <span>{{ item.badge }}</span>
              <strong>{{ item.title }}</strong>
              <p>{{ item.copy }}</p>
            </div>
            <el-button plain @click="handleReportSuggestion(item)">{{ item.cta }}</el-button>
          </article>
        </div>
        <PageStateBlock
          v-else
          tone="info"
          title="当前节奏已经比较稳定"
          description="可以继续回看最新报表，或者按推荐周期生成下一份复盘。"
          compact
        />
      </div>

      <div class="card">
        <div class="card-head">
          <div>
            <div class="section-title-row">
              <h3>本周复盘卡</h3>
              <CompactHint description="这一栏主要是压缩结论，不负责讲完整故事，详细趋势已经放在数据看板里。" />
            </div>
          </div>
        </div>

        <article class="weekly-review-hero">
          <div class="weekly-review-copy">
            <span>Weekly Review</span>
            <strong>{{ weeklyReviewHeadline }}</strong>
            <p>{{ weeklyReviewSummary }}</p>
          </div>
          <div class="status-pill" :class="weeklyReviewTone">{{ weeklyReviewLabel }}</div>
        </article>

        <div class="weekly-review-grid">
          <article v-for="item in weeklyReviewBoard" :key="item.label" class="weekly-review-item">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <p>{{ item.copy }}</p>
          </article>
        </div>

        <div v-if="reportInsights.length" class="status-list compact-status-list">
          <article v-for="item in reportInsights" :key="item.title" class="status-item">
            <div class="status-line">
              <strong>{{ item.title }}</strong>
              <span class="status-pill" :class="item.tone">{{ item.badge }}</span>
            </div>
            <p>{{ item.copy }}</p>
          </article>
        </div>
        <PageStateBlock
          v-else
          tone="empty"
          title="当前还没有足够记录可以分析"
          description="先记录几餐，系统才知道该提醒你复盘什么。"
          compact
        />
      </div>
    </div>

    <div class="grid reports-support-layout">
      <div class="card">
        <div class="card-head">
          <div>
            <h3>记录覆盖度</h3>
            <p>先判断数据量够不够，再决定出周报还是月报。</p>
          </div>
        </div>

        <div class="coverage-grid">
          <article>
            <span>最近7天活跃天数</span>
            <strong>{{ readiness.week.activeDays }}</strong>
            <p>{{ readiness.week.activeDays >= 4 ? "已经具备生成周报的基础。" : "建议至少记录 4 天以上再生成周报。" }}</p>
            <el-progress :percentage="coveragePercent(readiness.week.activeDays, 4)" :stroke-width="8" :show-text="false" />
          </article>
          <article>
            <span>最近30天活跃天数</span>
            <strong>{{ readiness.month.activeDays }}</strong>
            <p>{{ readiness.month.activeDays >= 10 ? "已经具备月报复盘价值。" : "月报还需要更长周期的连续记录。" }}</p>
            <el-progress :percentage="coveragePercent(readiness.month.activeDays, 10)" :stroke-width="8" :show-text="false" />
          </article>
          <article>
            <span>最近7天餐次</span>
            <strong>{{ readiness.week.meals }}</strong>
            <p>活跃天数之外，也要看一周里真正沉淀了多少餐次。</p>
            <el-progress :percentage="coveragePercent(readiness.week.meals, 12)" :stroke-width="8" :show-text="false" />
          </article>
          <article>
            <span>最近30天餐次</span>
            <strong>{{ readiness.month.meals }}</strong>
            <p>餐次越完整，月报越像复盘，不只是空壳 PDF。</p>
            <el-progress :percentage="coveragePercent(readiness.month.meals, 40)" :stroke-width="8" :show-text="false" />
          </article>
        </div>

        <div class="helper-box">
          <strong>{{ readinessHeadline }}</strong>
          <p>{{ readinessCopy }}</p>
        </div>

        <TrendMiniBars
          v-if="weekCoverageBars.length"
          title="最近7天记录节奏"
          description="优先看这一周是否连续，而不是只盯某一天的偶发高值。"
          badge="周内"
          tone="success"
          compact
          :items="weekCoverageBars"
        />
      </div>

      <div class="card">
        <div class="card-head">
          <div>
            <h3>最新报表</h3>
            <p>优先回看最近一次结果，不必每次都重新生成。</p>
          </div>
        </div>

        <div v-if="latestTask" class="report-overview">
          <div class="status-row">
            <div class="status-pill" :class="statusClass(latestTask.status)">{{ taskStatusLabel(latestTask.status) }}</div>
            <span class="overview-tip">{{ latestTask.file_url ? "文件已可下载" : "暂未生成文件" }}</span>
          </div>
          <div class="meta">
            <div>
              <span>报表类型</span>
              <strong>{{ taskTypeLabel(latestTask.report_type) }}</strong>
            </div>
            <div>
              <span>覆盖时间</span>
              <strong>{{ formatDateRange(latestTask.start_date, latestTask.end_date) }}</strong>
            </div>
            <div>
              <span>生成时间</span>
              <strong>{{ formatDateTime(latestTask.generated_at) }}</strong>
            </div>
          </div>
          <div class="download" v-if="latestTask.file_url">
            <a :href="latestTask.file_url" target="_blank" rel="noreferrer">打开最新报表</a>
          </div>
        </div>
        <PageStateBlock
          v-else
          tone="empty"
          title="还没有生成过报表"
          description="先生成一份周报或月报，后续历史记录和复盘中心才会真正形成资产。"
          action-label="生成推荐周报"
          @action="applyRecommendedPreset('weekly')"
        />
      </div>
    </div>

    <div class="grid reports-workflow-layout">
      <div class="card">
        <div class="card-head">
          <div>
            <h3>生成新报表</h3>
            <p>支持按推荐周期一键生成，也可以按自定义时间范围导出。</p>
          </div>
          <div class="head-tip">
            <span>{{ hasCustomRange ? "自定义时间范围" : "推荐周期" }}</span>
          </div>
        </div>

        <el-form label-position="top" class="generator-form">
          <el-form-item label="报表类型">
            <el-radio-group v-model="reportForm.report_type" class="mobile-scroll-row">
              <el-radio-button label="weekly">周报</el-radio-button>
              <el-radio-button label="monthly">月报<span v-if="!auth.isPro" class="pro-lock-tag">🔒 Pro</span></el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="reportForm.dates"
              type="daterange"
              value-format="YYYY-MM-DD"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 100%"
            />
          </el-form-item>
        </el-form>

        <div class="helper-box">
          <strong>{{ generationTitle }}</strong>
          <p>{{ generationDescription }}</p>
        </div>

        <FormActionBar
          :tone="generating ? 'saving' : generationTone"
          :title="generationActionTitle"
          :description="generationActionDescription"
          :primary-label="generationButtonText"
          :disabled="generationDisabled"
          :loading="generating"
          @primary="generateReport"
        >
          <el-button plain @click="applyRecommendedPreset('weekly')">周报建议</el-button>
          <el-button plain @click="applyRecommendedPreset('monthly')">月报建议</el-button>
          <el-button :disabled="!reportForm.dates.length" @click="clearDateRange">清空时间范围</el-button>
        </FormActionBar>
      </div>

      <div class="card">
        <div class="card-head">
          <div>
            <h3>当前状态</h3>
            <p>报表生成中会持续提示并自动刷新。</p>
          </div>
          <div class="head-tip">
            <span>{{ autoRefreshing ? "自动刷新中" : "已稳定" }}</span>
          </div>
        </div>

        <div v-if="processingTasks.length" class="status-list">
          <article v-for="task in processingTasks" :key="task.task_id" class="status-item">
            <div class="status-line">
              <strong>{{ taskTypeLabel(task.report_type) }}</strong>
              <span class="status-pill warm">{{ taskStatusLabel(task.status) }}</span>
            </div>
            <p>{{ formatDateRange(task.start_date, task.end_date) }}</p>
            <p>系统会继续自动刷新，直到文件可以打开为止。</p>
          </article>
        </div>
        <PageStateBlock
          v-else
          tone="info"
          title="当前没有正在处理的报表"
          description="如果需要新的复盘结果，可以按推荐周期生成，或者按自定义时间范围导出。"
          compact
        />
      </div>
    </div>

    <div class="card">
      <div class="history-head">
        <div>
          <h3>历史记录</h3>
          <p>保留最近生成的报表，方便你回看不同周期的饮食变化。</p>
        </div>
      </div>
      <div v-if="reportTasks.length" class="history-list">
        <article v-for="task in reportTasks" :key="task.task_id" class="history-item">
          <div class="history-top">
            <div>
              <strong>{{ taskTypeLabel(task.report_type) }}</strong>
              <p>{{ formatDateRange(task.start_date, task.end_date) }}</p>
            </div>
            <span class="history-status" :class="statusClass(task.status)">{{ taskStatusLabel(task.status) }}</span>
          </div>
          <div class="history-meta">
            <span>生成时间：{{ formatDateTime(task.generated_at) }}</span>
          </div>
          <div class="history-actions">
            <a v-if="task.file_url" :href="task.file_url" target="_blank" rel="noreferrer">下载 PDF</a>
            <span v-else-if="task.status === 'failed'">本次生成失败，可重新发起导出</span>
            <span v-else>文件生成中，页面会自动刷新</span>
            <el-button text type="danger" size="small" :loading="deletingTaskId === task.task_id" @click="removeReportTask(task.task_id)">删除</el-button>
          </div>
        </article>
      </div>
      <PageStateBlock
        v-else
        tone="empty"
        title="暂无历史报表"
        description="生成过一次周报或月报后，这里会保留最近的可回看结果。"
        compact
      />
    </div>
    </RefreshFrame>
  </section>

  <el-dialog v-model="proLockedVisible" title="Pro 专属功能" width="420px">
    <p>月报和 PDF 导出是 Pro 专享功能，升级后即可无限使用。</p>
    <template #footer>
      <el-button @click="proLockedVisible = false">取消</el-button>
      <el-button type="primary" @click="() => { proLockedVisible = false; router.push('/pricing'); }">升级 Pro</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import FormActionBar from "../components/FormActionBar.vue";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import CompactHint from "../components/CompactHint.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import ReportsDashboardBoard from "../components/ReportsDashboardBoard.vue";
import TrendMiniBars from "../components/TrendMiniBars.vue";
import { notifyActionError, notifyActionSuccess, notifyLoadError } from "../lib/feedback";
import { deleteReportTask, exportReport, getReportDashboard, listReportTasks, monthlyReport, weeklyReport } from "../api/reports";
import { trackEvent } from "../api/behavior";
import { listMealRecords, mealStatistics } from "../api/tracking";

type ReportSuggestionAction =
  | { type: "route"; to: string; query?: Record<string, string> }
  | { type: "refresh" }
  | { type: "open"; url: string }
  | { type: "assistant"; source: string; prompt: string }
  | { type: "generate"; reportType: "weekly" | "monthly" };

type ReportSuggestion = {
  key: string;
  title: string;
  copy: string;
  cta: string;
  action: ReportSuggestionAction;
};

type ReviewConclusion = {
  label: string;
  title: string;
  copy: string;
  tone: "warm" | "success" | "accent";
};

type NextWeekPlanItem = ReportSuggestion & {
  badge: string;
};

const router = useRouter();
const auth = useAuthStore();
const proLockedVisible = ref(false);
const generating = ref(false);
const loadingTasks = ref(false);
const loadingReadiness = ref(false);
const loadingDashboard = ref(false);
const autoRefreshing = ref(false);
const reportTasks = ref<Array<Record<string, any>>>([]);
const dashboardData = ref<Record<string, any> | null>(null);
const readinessRecords = ref<Array<Record<string, any>>>([]);
const readiness = reactive({
  week: { activeDays: 0, meals: 0, summary: null as null | Record<string, any>, trend: [] as Record<string, any>[] },
  month: { activeDays: 0, meals: 0, summary: null as null | Record<string, any>, trend: [] as Record<string, any>[] },
});
const reportForm = reactive({
  report_type: "weekly",
  dates: [] as string[],
});

let pollTimer: ReturnType<typeof window.setInterval> | null = null;
const deletingTaskId = ref<string | null>(null);

const hasCustomRange = computed(() => reportForm.dates.length === 2);
const latestTask = computed(() => reportTasks.value[0] ?? null);
const latestCompletedTask = computed(() => reportTasks.value.find((task) => task.status === "completed" && task.file_url) ?? null);
const latestWeeklyTask = computed(() => reportTasks.value.find((task) => task.report_type === "weekly" && task.status === "completed" && task.file_url) ?? null);
const latestMonthlyTask = computed(() => reportTasks.value.find((task) => task.report_type === "monthly" && task.status === "completed" && task.file_url) ?? null);
const processingTasks = computed(() => reportTasks.value.filter((task) => ["pending", "processing"].includes(task.status)));
const latestWeeklyAgeDays = computed(() => taskAgeDays(latestWeeklyTask.value));
const latestMonthlyAgeDays = computed(() => taskAgeDays(latestMonthlyTask.value));
const showReportsSkeleton = computed(() => {
  return (loadingTasks.value || loadingReadiness.value || loadingDashboard.value) && !reportTasks.value.length && !readiness.week.meals && !readiness.month.meals && !dashboardData.value;
});
const showReportsRefreshing = computed(() => !showReportsSkeleton.value && (loadingTasks.value || loadingReadiness.value || loadingDashboard.value));
const reportSummary = computed(() => {
  const completed = reportTasks.value.filter((task) => task.status === "completed").length;
  const processing = reportTasks.value.filter((task) => ["pending", "processing"].includes(task.status)).length;
  const latestCompleted = reportTasks.value.find((task) => task.generated_at);
  return {
    total: reportTasks.value.length,
    completed,
    processing,
    latestGenerated: latestCompleted ? formatDateTime(latestCompleted.generated_at) : "暂无",
  };
});
const generationTitle = computed(() => {
  if (hasCustomRange.value) {
    return `${taskTypeLabel(reportForm.report_type)}将按你选择的时间范围导出`;
  }
  return reportForm.report_type === "monthly" ? "将按系统推荐周期生成月报" : "将按系统推荐周期生成周报";
});
const generationDescription = computed(() => {
  if (hasCustomRange.value) {
    return `${reportForm.dates[0]} 至 ${reportForm.dates[1]} 的数据会用于生成一份独立报表。`;
  }
  return "如果你只是做常规复盘，用推荐周期即可；如果是运营复盘或阶段总结，再改为自定义时间范围。";
});
const generationButtonText = computed(() => {
  if (hasCustomRange.value) {
    return `生成自定义${taskTypeLabel(reportForm.report_type)}`;
  }
  return reportForm.report_type === "monthly" ? "生成推荐月报" : "生成推荐周报";
});
const generationDisabled = computed(() => hasCustomRange.value ? reportForm.dates.length !== 2 : false);
const generationTone = computed(() => (generationDisabled.value ? "warning" : "ready"));
const generationActionTitle = computed(() => {
  if (generationDisabled.value) {
    return "先补齐完整时间范围";
  }
  if (processingTasks.value.length) {
    return "当前已有报表在生成中";
  }
  return "当前配置可以直接生成";
});
const generationActionDescription = computed(() => {
  if (processingTasks.value.length) {
    return "系统会自动刷新已有任务，你也可以继续发起新的周期导出。";
  }
  return hasCustomRange.value
    ? "自定义周期更适合阶段复盘或运营场景，常规使用优先推荐周期即可。"
    : "如果只是日常复盘，推荐周期通常已经足够。";
});
const readinessHeadline = computed(() => {
  if (readiness.month.activeDays >= 10) {
    return "当前已经具备月报复盘价值";
  }
  if (readiness.week.activeDays >= 4) {
    return "当前更适合先做周报复盘";
  }
  return "当前记录量还偏少，建议先补记录";
});
const readinessCopy = computed(() => {
  if (readiness.month.activeDays >= 10) {
    return "最近 30 天已经有相对稳定的记录覆盖，可以优先生成月报看阶段变化。";
  }
  if (readiness.week.activeDays >= 4) {
    return "最近 7 天已经有基本覆盖，先从周报开始更合适，能更快形成反馈闭环。";
  }
  return "记录不足时生成报表，更多只是形式化输出。先把最近几天补完整，再回来看报表。";
});
const weekAverageProtein = computed(() => {
  if (!readiness.week.activeDays) {
    return 0;
  }
  return Number(readiness.week.summary?.protein || 0) / readiness.week.activeDays;
});
const weekRecords = computed(() => readinessRecords.value.filter((item) => isRecordInRecentDays(item.record_date, 7)));
const weekMealCounts = computed(() => {
  return weekRecords.value.reduce(
    (result, record) => {
      const mealType = String(record.meal_type || "");
      if (mealType in result) {
        result[mealType as keyof typeof result] += 1;
      }
      return result;
    },
    {
      breakfast: 0,
      lunch: 0,
      dinner: 0,
      snack: 0,
    },
  );
});
const weakestPrimaryMeal = computed(() => {
  const candidates = [
    { mealType: "breakfast", count: weekMealCounts.value.breakfast },
    { mealType: "lunch", count: weekMealCounts.value.lunch },
    { mealType: "dinner", count: weekMealCounts.value.dinner },
  ].sort((a, b) => a.count - b.count);
  return candidates[0] ?? null;
});
const weekRecipeLinkedCount = computed(() => {
  return weekRecords.value.filter((record) =>
    Array.isArray(record.items) && record.items.some((item: Record<string, any>) => Number(item.recipe_id || 0) > 0),
  ).length;
});
const weekRecipeLinkedRate = computed(() => {
  if (!weekRecords.value.length) {
    return 0;
  }
  return Math.round((weekRecipeLinkedCount.value / weekRecords.value.length) * 100);
});
const weeklyExecutionScore = computed(() => {
  const activeDaysScore = coveragePercent(readiness.week.activeDays, 7) * 0.45;
  const mealCountScore = coveragePercent(readiness.week.meals, 12) * 0.35;
  const recipeLinkScore = weekRecipeLinkedRate.value * 0.2;
  return Math.round(Math.min(100, activeDaysScore + mealCountScore + recipeLinkScore));
});
const weeklyReviewLabel = computed(() => {
  if (weeklyExecutionScore.value >= 75) {
    return "执行稳定";
  }
  if (weeklyExecutionScore.value >= 45) {
    return "仍可补强";
  }
  return "先补执行";
});
const weeklyReviewTone = computed(() => {
  if (weeklyExecutionScore.value >= 75) {
    return "is-completed";
  }
  if (weeklyExecutionScore.value >= 45) {
    return "is-processing";
  }
  return "is-pending";
});
const weeklyReviewHeadline = computed(() => {
  if (readiness.week.activeDays < 4 || readiness.week.meals < 8) {
    return "这周先把记录补连续，比急着看更多数字更重要";
  }
  if ((weakestPrimaryMeal.value?.count ?? 0) <= 1) {
    return `这周最需要补的是${mealTypeLabel(weakestPrimaryMeal.value?.mealType || "lunch")}节奏`;
  }
  if (weekAverageProtein.value > 0 && weekAverageProtein.value < 65) {
    return "主餐蛋白还不够稳，下一周先补强一顿主餐";
  }
  if (weekRecipeLinkedRate.value < 50) {
    return "常吃内容还没沉淀成资产，记录效率还有提升空间";
  }
  if (latestCompletedTask.value?.file_url) {
    return "这周已经能形成复盘闭环，可以直接带着结论进入下一周";
  }
  return "这周执行已经有基础，适合沉淀成更明确的复盘结果";
});
const weeklyReviewSummary = computed(() => {
  if (!weekRecords.value.length) {
    return "当前一周内还没有足够记录，先从记录页补起至少几餐，复盘才会开始有真实判断。";
  }
  if (readiness.week.activeDays < 4 || readiness.week.meals < 8) {
    return `最近 7 天只记录了 ${readiness.week.activeDays} 天、${readiness.week.meals} 餐，当前最该做的是把输入变连续。`;
  }
  return `最近一周执行稳定度约 ${weeklyExecutionScore.value}/100，最常漏的是${mealTypeLabel(weakestPrimaryMeal.value?.mealType || "lunch")}，菜谱带入率约 ${weekRecipeLinkedRate.value}%。`;
});
const weeklyReviewBoard = computed(() => {
  return [
    {
      label: "执行稳定度",
      value: `${weeklyExecutionScore.value} / 100`,
      copy: weeklyExecutionScore.value >= 75 ? "本周节奏比较稳，适合继续做阶段复盘。" : "还可以继续压缩遗漏和断档。",
    },
    {
      label: "最常漏掉",
      value: weekRecords.value.length ? mealTypeLabel(weakestPrimaryMeal.value?.mealType || "lunch") : "待形成",
      copy: weekRecords.value.length
        ? `最近 7 天这餐共记录 ${weakestPrimaryMeal.value?.count || 0} 次，下一步优先把它补稳定。`
        : "先有记录，系统才能判断最常漏掉的是哪一餐。",
    },
    {
      label: "菜谱带入率",
      value: weekRecords.value.length ? `${weekRecipeLinkedRate.value}%` : "暂无",
      copy: weekRecipeLinkedRate.value >= 50 ? "已经有一半以上记录能复用菜谱，效率开始起来了。" : "还可以把常吃内容沉淀成菜谱或收藏，减少手填。",
    },
    {
      label: "复盘资产",
      value: latestCompletedTask.value?.file_url ? `${taskTypeLabel(latestCompletedTask.value.report_type)}已沉淀` : "尚未沉淀",
      copy: latestCompletedTask.value?.file_url
        ? "已经有可以回看的报表资产，后续对比不同阶段会更省事。"
        : "还没有成型的复盘结果，可以在记录更完整后尽快生成一份。",
    },
  ];
});
const reportInsights = computed(() => {
  const insights = [];
  const weekSummary = readiness.week.summary ?? {};
  const monthSummary = readiness.month.summary ?? {};

  if (readiness.week.activeDays > 0) {
    insights.push({
      title: "周内记录连续性",
      badge: readiness.week.activeDays >= 4 ? "良好" : "偏弱",
      tone: readiness.week.activeDays >= 4 ? "is-completed" : "is-pending",
      copy: readiness.week.activeDays >= 4 ? "最近一周有连续记录，适合先做一次周报复盘。" : "最近一周记录天数偏少，建议先补齐缺口再看周报。",
    });
  }

  if (Number(weekSummary.protein || 0) > 0 && Number(weekSummary.energy || 0) > 0) {
    insights.push({
      title: "周内营养摘要",
      badge: "摘要",
      tone: "is-processing",
      copy: `最近 7 天累计约 ${Number(weekSummary.energy).toFixed(0)} kcal，蛋白 ${Number(weekSummary.protein).toFixed(1)} g。`,
    });
  }

  if (Number(monthSummary.energy || 0) > 0) {
    insights.push({
      title: "月度复盘准备度",
      badge: readiness.month.activeDays >= 10 ? "可复盘" : "待积累",
      tone: readiness.month.activeDays >= 10 ? "is-completed" : "is-pending",
      copy:
        readiness.month.activeDays >= 10
          ? "最近 30 天已经有一定连续记录，月报能更真实地反映阶段变化。"
          : "最近 30 天记录还不够稳定，月报价值暂时不高。",
    });
  }

  return insights.slice(0, 3);
});
const reportActionSuggestions = computed<ReportSuggestion[]>(() => {
  const actions: ReportSuggestion[] = [];

  const registerAction = (
    key: string,
    title: string,
    copy: string,
    cta: string,
    action: ReportSuggestionAction,
  ) => {
    if (actions.some((item) => item.key === key)) {
      return;
    }
    actions.push({ key, title, copy, cta, action });
  };

  if (processingTasks.value.length) {
    registerAction(
      "processing",
      "先等待当前报表生成完成",
      "页面会自动刷新状态；如果想确认结果是否已经出来，可以手动刷新一次。",
      "刷新状态",
      { type: "refresh" },
    );
  }

  if (latestTask.value?.status === "failed") {
    registerAction(
      "retry-latest",
      "最近一次报表生成失败",
      "可以直接重试同类型报表，通常不需要重新填写时间范围。",
      `重试${taskTypeLabel(latestTask.value.report_type)}`,
      { type: "generate", reportType: latestTask.value.report_type === "monthly" ? "monthly" : "weekly" },
    );
  }

  if (readiness.week.activeDays < 4 || readiness.week.meals < 8) {
    registerAction(
      "fill-records",
      "先补齐本周记录覆盖度",
      `最近 7 天只有 ${readiness.week.activeDays} 天、${readiness.week.meals} 餐有效记录，先补齐几餐再生成周报更有复盘价值。`,
      "去补记录",
      { type: "route", to: "/records" },
    );
  }

  if (!processingTasks.value.length && readiness.week.activeDays >= 4 && (!latestWeeklyTask.value || (latestWeeklyAgeDays.value ?? 999) >= 7)) {
    registerAction(
      "generate-weekly",
      "现在适合生成一份新周报",
      "最近一周已经有基础覆盖，适合尽快把输入沉淀成一份可回看的复盘结果。",
      "生成推荐周报",
      { type: "generate", reportType: "weekly" },
    );
  }

  if (!processingTasks.value.length && readiness.month.activeDays >= 10 && (!latestMonthlyTask.value || (latestMonthlyAgeDays.value ?? 999) >= 28)) {
    registerAction(
      "generate-monthly",
      "月度记录已经具备复盘价值",
      "最近 30 天记录相对稳定，可以生成一份月报看阶段变化，不必只盯单周波动。",
      "生成推荐月报",
      { type: "generate", reportType: "monthly" },
    );
  }

  if (weekAverageProtein.value > 0 && weekAverageProtein.value < 65) {
    registerAction(
      "protein",
      "最近一周蛋白摄入偏弱",
      `按活跃天估算，日均蛋白约 ${weekAverageProtein.value.toFixed(1)} g，适合优先去找高蛋白选项。`,
      "看高蛋白菜谱",
      { type: "route", to: "/recipes" },
    );
  }

  if (latestCompletedTask.value?.file_url) {
    registerAction(
      "open-latest",
      "可以直接回看最新报表",
      "如果当前不准备重新生成，先打开最近一次完成的结果，效率会更高。",
      "打开最新报表",
      { type: "open", url: latestCompletedTask.value.file_url },
    );
  }

  return actions.slice(0, 3);
});
const nextWeekActionPlan = computed<NextWeekPlanItem[]>(() => {
  const actions: NextWeekPlanItem[] = [];

  const registerAction = (
    key: string,
    badge: string,
    title: string,
    copy: string,
    cta: string,
    action: ReportSuggestionAction,
  ) => {
    if (actions.some((item) => item.key === key)) {
      return;
    }
    actions.push({ key, badge, title, copy, cta, action });
  };

  if (readiness.week.activeDays < 4 || readiness.week.meals < 8) {
    registerAction(
      "fill-week-gap",
      "先补连续性",
      `优先补${mealTypeLabel(weakestPrimaryMeal.value?.mealType || "lunch")}记录`,
      `最近 7 天只有 ${readiness.week.activeDays} 天、${readiness.week.meals} 餐有效记录。先把最容易漏掉的一餐补上，周报才更像真实复盘。`,
      "去记录页",
      { type: "route", to: "/records", query: { meal_type: weakestPrimaryMeal.value?.mealType || "lunch", source: "reports" } },
    );
  }

  if ((weakestPrimaryMeal.value?.count ?? 0) <= 1 && weekRecords.value.length > 0) {
    registerAction(
      "stabilize-meal",
      "先稳一餐",
      `给${mealTypeLabel(weakestPrimaryMeal.value?.mealType || "lunch")}建立固定入口`,
      `这一餐最近只记录了 ${weakestPrimaryMeal.value?.count || 0} 次。先让它变成可快速带入的一餐，下周执行会顺很多。`,
      "去收藏选餐",
      { type: "route", to: "/favorites" },
    );
  }

  if (weekAverageProtein.value > 0 && weekAverageProtein.value < 65) {
    registerAction(
      "lift-protein",
      "补强营养",
      "把一顿主餐换成更高蛋白组合",
      `按活跃天估算，最近一周日均蛋白约 ${weekAverageProtein.value.toFixed(1)} g。下一周不用全改，先把一顿主餐换成更稳的高蛋白搭配。`,
      "去菜谱库",
      { type: "route", to: "/recipes" },
    );
  }

  if (weekRecords.value.length > 0 && weekRecipeLinkedRate.value < 50) {
    registerAction(
      "assetize-meals",
      "沉淀资产",
      "把常吃内容沉淀成菜谱或收藏",
      `最近一周只有 ${weekRecipeLinkedRate.value}% 的记录带了菜谱。把常吃餐食沉淀下来，下次记录就不需要重新手填。`,
      "去管理菜谱",
      { type: "route", to: "/recipes" },
    );
  }

  if (!processingTasks.value.length && readiness.week.activeDays >= 4 && (!latestWeeklyTask.value || (latestWeeklyAgeDays.value ?? 999) >= 7)) {
    registerAction(
      "plan-generate-weekly",
      "沉淀结论",
      "把这一周生成成一份周报",
      "这周样本已经够用，先把输入沉淀成报表，再决定下周要不要继续调整更高阶的策略。",
      "生成周报",
      { type: "generate", reportType: "weekly" },
    );
  }

  if (!processingTasks.value.length && readiness.month.activeDays >= 10 && (!latestMonthlyTask.value || (latestMonthlyAgeDays.value ?? 999) >= 28)) {
    registerAction(
      "plan-generate-monthly",
      "看阶段变化",
      "生成一份新的月报",
      "最近 30 天已经有连续输入，适合回头看阶段变化，而不是只盯这一周。",
      "生成月报",
      { type: "generate", reportType: "monthly" },
    );
  }

  if (latestCompletedTask.value?.file_url) {
    registerAction(
      "plan-open-latest",
      "先看现成结果",
      "先回看最新报表再定下周方向",
      "你已经有可用的复盘资产，不需要每次都从零判断，先看现成结论效率更高。",
      "打开最新报表",
      { type: "open", url: latestCompletedTask.value.file_url },
    );
  }

  if (actions.length < 3) {
    registerAction(
      "plan-ai",
      "让 AI 收口",
      "让 AI 把复盘翻译成下周清单",
      "如果你不想自己整理，直接让 AI 用当前复盘状态生成一版可执行的下周动作清单。",
      "打开 AI 助手",
      { type: "assistant", source: "reports_review_explain", prompt: buildNextWeekPlanPrompt(actions.map((item) => item.title)) },
    );
  }

  return actions.slice(0, 3);
});
const nextWeekFocus = computed<NextWeekPlanItem | null>(() => nextWeekActionPlan.value[0] ?? null);
const nextWeekFocusTitle = computed(() => nextWeekFocus.value?.title || "当前没有额外阻塞");
const nextWeekFocusCopy = computed(() => nextWeekFocus.value?.copy || "可以继续按当前节奏记录，并在合适时机回看最新报表。");
const nextWeekFocusBadge = computed(() => nextWeekFocus.value?.badge || "保持当前节奏");
const nextWeekFocusTone = computed(() => {
  if (!nextWeekFocus.value) {
    return "is-completed";
  }
  if (nextWeekFocus.value.key.includes("fill") || nextWeekFocus.value.key.includes("stabilize")) {
    return "is-pending";
  }
  if (nextWeekFocus.value.key.includes("generate") || nextWeekFocus.value.key.includes("open")) {
    return "is-processing";
  }
  return "is-completed";
});
const primaryReviewSuggestion = computed<ReportSuggestion | null>(() => reportActionSuggestions.value[0] ?? null);
const reviewStageLabel = computed(() => {
  if (readiness.month.activeDays >= 10) {
    return "阶段复盘窗口";
  }
  if (readiness.week.activeDays >= 4) {
    return "周复盘窗口";
  }
  return "先补记录";
});
const reviewStageTone = computed(() => {
  if (readiness.month.activeDays >= 10) {
    return "is-completed";
  }
  if (readiness.week.activeDays >= 4) {
    return "is-processing";
  }
  return "is-pending";
});
const reviewHeadline = computed(() => {
  if (readiness.week.activeDays < 4 || readiness.week.meals < 8) {
    return "先把记录补连续，比急着导出更重要";
  }
  if (weekAverageProtein.value > 0 && weekAverageProtein.value < 65) {
    return "这周先补蛋白，比再看更多数字更关键";
  }
  if (!processingTasks.value.length && readiness.month.activeDays >= 10 && (!latestMonthlyTask.value || (latestMonthlyAgeDays.value ?? 999) >= 28)) {
    return "现在值得做一次月度复盘";
  }
  if (!processingTasks.value.length && readiness.week.activeDays >= 4 && (!latestWeeklyTask.value || (latestWeeklyAgeDays.value ?? 999) >= 7)) {
    return "这一周已经可以沉淀成一份新周报";
  }
  if (latestCompletedTask.value?.file_url) {
    return "先回看最新报表，再决定要不要重新生成";
  }
  return readinessHeadline.value;
});
const reviewSummary = computed(() => {
  if (readiness.week.activeDays < 4 || readiness.week.meals < 8) {
    return `最近 7 天只有 ${readiness.week.activeDays} 天、${readiness.week.meals} 餐有效记录。先补齐输入，再生成报表，结论会更像真实复盘。`;
  }
  if (weekAverageProtein.value > 0 && weekAverageProtein.value < 65) {
    return `按活跃天估算，最近一周日均蛋白约 ${weekAverageProtein.value.toFixed(1)} g。下一步优先把几顿主餐拉到更稳的蛋白水平。`;
  }
  if (!processingTasks.value.length && readiness.month.activeDays >= 10 && (!latestMonthlyTask.value || (latestMonthlyAgeDays.value ?? 999) >= 28)) {
    return `最近 30 天已有 ${readiness.month.activeDays} 天活跃记录，阶段样本已经够用，适合看一次月报而不只是单周波动。`;
  }
  if (!processingTasks.value.length && readiness.week.activeDays >= 4 && (!latestWeeklyTask.value || (latestWeeklyAgeDays.value ?? 999) >= 7)) {
    return `最近 7 天已有 ${readiness.week.activeDays} 天活跃记录，可以把这周的输入沉淀成一份更容易回看的周复盘。`;
  }
  if (latestCompletedTask.value?.file_url) {
    return "你已经有可回看的报表资产，先打开最新结果看结论，再决定是否需要重新导出。";
  }
  return readinessCopy.value;
});
const reviewMetrics = computed(() => [
  {
    label: "最近7天活跃",
    value: `${readiness.week.activeDays} 天`,
    hint: readiness.week.activeDays >= 4 ? "周报条件基本够用" : "还差一点连续性",
  },
  {
    label: "最近7天餐次",
    value: `${readiness.week.meals} 餐`,
    hint: readiness.week.meals >= 8 ? "输入量足够看趋势" : "样本还偏少",
  },
  {
    label: "日均蛋白",
    value: weekAverageProtein.value > 0 ? `${weekAverageProtein.value.toFixed(1)} g` : "待累计",
    hint: weekAverageProtein.value >= 65 ? "主餐结构相对稳" : "可以继续补强",
  },
]);
const reviewConclusions = computed<ReviewConclusion[]>(() => {
  const issue: ReviewConclusion =
    readiness.week.activeDays < 4 || readiness.week.meals < 8
      ? {
          label: "最大问题",
          title: "记录覆盖度还不够连续",
          copy: `现在先补记录更划算，至少补到 4 天活跃、8 餐以上，再看周报会更有意义。`,
          tone: "warm",
        }
      : weekAverageProtein.value > 0 && weekAverageProtein.value < 65
        ? {
            label: "最大问题",
            title: "蛋白摄入偏弱",
            copy: `最近一周日均蛋白约 ${weekAverageProtein.value.toFixed(1)} g，下一阶段优先把一日一餐换成更高蛋白的组合。`,
            tone: "warm",
          }
        : {
            label: "最大问题",
            title: "当前更缺明确复盘动作",
            copy: "数据已经在累积，下一步不是继续观望，而是尽快生成或回看一份报表，把结论落到行动上。",
            tone: "warm",
          };

  const keep: ReviewConclusion =
    readiness.week.activeDays >= 5
      ? {
          label: "值得保留",
          title: "最近一周记录节奏是稳定的",
          copy: `你已经连续记录了 ${readiness.week.activeDays} 天，这种输入习惯本身就是后续复盘有用的基础。`,
          tone: "success",
        }
      : latestCompletedTask.value?.file_url
        ? {
            label: "值得保留",
            title: "已经开始积累可回看的报表资产",
            copy: "不需要每次都从零分析，已有报表会让后续比较不同阶段时更省力。",
            tone: "success",
          }
        : {
            label: "值得保留",
            title: "当前记录习惯已经开始形成",
            copy: "哪怕现在还不够完整，也建议继续保持每天至少记录一餐，别让输入节奏断掉。",
            tone: "success",
          };

  const next: ReviewConclusion = primaryReviewSuggestion.value
    ? {
        label: "下一步",
        title: primaryReviewSuggestion.value.title,
        copy: primaryReviewSuggestion.value.copy,
        tone: "accent",
      }
    : {
        label: "下一步",
        title: "先打开推荐周期",
        copy: "如果当前没有明显阻塞，直接从推荐周报或月报开始，通常已经足够。",
        tone: "accent",
      };

  return [issue, keep, next];
});
const reviewFallbackType = computed<"weekly" | "monthly">(() => (readiness.month.activeDays >= 10 ? "monthly" : "weekly"));
const weekCoverageBars = computed(() => {
  return readiness.week.trend.slice(-7).map((item, index, source) => ({
    label: String(item.date || "").slice(5),
    value: Number(item.energy || 0),
    display: Number(item.energy || 0) > 0 ? "已记" : "空",
    highlight: index === source.length - 1,
  }));
});

function unwrapPayload<T>(payload: unknown, fallback: T): T {
  if (payload == null) {
    return fallback;
  }
  if (typeof payload === "object" && payload && "data" in payload && (payload as { data?: T }).data !== undefined) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}

function unwrapList(payload: unknown) {
  const raw = unwrapPayload<any>(payload, []);
  if (Array.isArray(raw)) {
    return raw;
  }
  if (Array.isArray(raw?.items)) {
    return raw.items;
  }
  if (Array.isArray(raw?.results)) {
    return raw.results;
  }
  return [];
}

function taskTypeLabel(type: string) {
  return type === "monthly" ? "月报" : "周报";
}

function taskStatusLabel(status: string) {
  return {
    pending: "等待中",
    processing: "生成中",
    completed: "已完成",
    failed: "失败",
  }[status] || status;
}

function statusClass(status: string) {
  return {
    pending: "is-pending",
    processing: "is-processing",
    completed: "is-completed",
    failed: "is-failed",
  }[status] || "";
}

function mealTypeLabel(value: string) {
  return {
    breakfast: "早餐",
    lunch: "午餐",
    dinner: "晚餐",
    snack: "加餐",
  }[value] || value;
}

function coveragePercent(value: number, target: number) {
  if (!target) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round((value / target) * 100)));
}

function formatDateRange(startDate?: string, endDate?: string) {
  if (!startDate && !endDate) {
    return "未记录";
  }
  return `${startDate || "-"} 至 ${endDate || "-"}`;
}

function formatDateTime(value?: string) {
  if (!value) {
    return "刚刚生成";
  }
  return value.replace("T", " ").slice(0, 16);
}

function taskAgeDays(task?: Record<string, any> | null) {
  const reference = task?.generated_at || task?.end_date;
  if (!reference) {
    return null;
  }
  const diff = Date.now() - new Date(reference).getTime();
  if (!Number.isFinite(diff) || diff < 0) {
    return null;
  }
  return Math.floor(diff / (1000 * 60 * 60 * 24));
}

function clearDateRange() {
  reportForm.dates = [];
}

function formatDate(date: Date) {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function isRecordInRecentDays(recordDate?: string, days = 7) {
  if (!recordDate) {
    return false;
  }
  const current = new Date();
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  start.setDate(current.getDate() - days);
  const target = new Date(`${recordDate}T00:00:00`);
  return target >= start;
}

function applyRecommendedPreset(kind: "weekly" | "monthly") {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - (kind === "monthly" ? 30 : 7));
  reportForm.report_type = kind;
  reportForm.dates = [formatDate(start), formatDate(end)];
}

async function triggerRecommendedGeneration(kind: "weekly" | "monthly") {
  clearDateRange();
  reportForm.report_type = kind;
  await generateReport();
}

async function handleReportSuggestion(item: {
  action: ReportSuggestionAction;
}) {
  if (item.action.type === "route") {
    router.push(item.action.query ? { path: item.action.to, query: item.action.query } : item.action.to);
    return;
  }
  if (item.action.type === "refresh") {
    await loadReportTasks();
    return;
  }
  if (item.action.type === "open") {
    window.open(item.action.url, "_blank", "noopener,noreferrer");
    return;
  }
  if (item.action.type === "assistant") {
    router.push({
      path: "/assistant",
      query: {
        source: item.action.source,
        prompt: item.action.prompt,
      },
    });
    return;
  }
  await triggerRecommendedGeneration(item.action.reportType);
}

function buildReviewAssistantPrompt() {
  return [
    "请基于我当前的报表页状态，用直接、可执行的语言解释这次复盘结论。",
    `当前复盘标题：${reviewHeadline.value}。`,
    `当前复盘摘要：${reviewSummary.value}。`,
    `最近7天活跃天数：${readiness.week.activeDays}。`,
    `最近7天餐次：${readiness.week.meals}。`,
    `最近30天活跃天数：${readiness.month.activeDays}。`,
    `日均蛋白估算：${weekAverageProtein.value.toFixed(1)} g。`,
    primaryReviewSuggestion.value ? `当前推荐动作：${primaryReviewSuggestion.value.title}。` : "当前没有单独推荐动作。",
    "请输出三部分：1）这次复盘最主要的问题是什么；2）哪些习惯值得保留；3）下周如果只改一件事，先改什么。",
  ].join("\n");
}

function buildNextWeekPlanPrompt(planTitles?: string[]) {
  const titles = planTitles?.length ? planTitles : nextWeekActionPlan.value.map((item) => item.title);
  return [
    "请基于我当前报表页的复盘状态，帮我生成一版下周行动清单。",
    `本周一句话结论：${weeklyReviewHeadline.value}。`,
    `本周摘要：${weeklyReviewSummary.value}。`,
    `执行稳定度：${weeklyExecutionScore.value}/100。`,
    `最常漏掉的餐次：${mealTypeLabel(weakestPrimaryMeal.value?.mealType || "lunch")}。`,
    `菜谱带入率：${weekRecipeLinkedRate.value}%。`,
    titles.length
      ? `当前页面已给出的动作建议：${titles.map((item, index) => `${index + 1}.${item}`).join("；")}。`
      : "当前页面还没有形成完整动作建议。",
    "请输出三部分：1）下周先改哪一件事；2）为什么是它；3）按周一到周日给我一个尽量省事的执行建议。",
  ].join("\n");
}

function openAssistantForReview() {
  router.push({
    path: "/assistant",
    query: {
      source: "reports_review_explain",
      prompt: buildReviewAssistantPrompt(),
    },
  });
}

function openAssistantForNextWeekPlan() {
  router.push({
    path: "/assistant",
    query: {
      source: "reports_review_explain",
      prompt: buildNextWeekPlanPrompt(),
    },
  });
}

function syncPolling() {
  const needsPolling = processingTasks.value.length > 0;
  if (!needsPolling) {
    autoRefreshing.value = false;
    if (pollTimer) {
      window.clearInterval(pollTimer);
      pollTimer = null;
    }
    return;
  }

  if (pollTimer) {
    autoRefreshing.value = true;
    return;
  }

  autoRefreshing.value = true;
  pollTimer = window.setInterval(() => {
    loadReportTasks(true).catch(() => undefined);
    loadDashboard(true).catch(() => undefined);
  }, 6000);
}

async function removeReportTask(taskId: string) {
  try {
    deletingTaskId.value = taskId;
    await deleteReportTask(taskId);
    reportTasks.value = reportTasks.value.filter((task) => task.task_id !== taskId);
    await loadDashboard(true);
    notifyActionSuccess("报表记录已删除");
  } catch {
    notifyActionError("删除报表记录");
  } finally {
    deletingTaskId.value = null;
  }
}

async function loadReportTasks(silent = false) {
  try {
    if (!silent) {
      loadingTasks.value = true;
    }
    const response = await listReportTasks();
    reportTasks.value = unwrapList(response);
    syncPolling();
  } catch (error) {
    if (!silent) {
      notifyLoadError("报表历史");
    }
  } finally {
    if (!silent) {
      loadingTasks.value = false;
    }
  }
}

async function loadDashboard(silent = false) {
  try {
    if (!silent) {
      loadingDashboard.value = true;
    }
    const response = await getReportDashboard();
    dashboardData.value = unwrapPayload<Record<string, any>>(response, {});
  } catch {
    if (!silent) {
      notifyLoadError("数据看板");
    }
  } finally {
    if (!silent) {
      loadingDashboard.value = false;
    }
  }
}

async function loadReadiness() {
  try {
    loadingReadiness.value = true;
    const [recordsResponse, weekStats, monthStats] = await Promise.all([listMealRecords(), mealStatistics("week"), mealStatistics("month")]);
    const records = unwrapList(recordsResponse);
    readinessRecords.value = records;
    const weekData = unwrapPayload<Record<string, any>>(weekStats, {});
    const monthData = unwrapPayload<Record<string, any>>(monthStats, {});
    const weekTrendData = Array.isArray(weekData?.trend) ? weekData.trend : [];
    const monthTrendData = Array.isArray(monthData?.trend) ? monthData.trend : [];
    const now = new Date();
    const weekStart = new Date();
    weekStart.setDate(now.getDate() - 7);
    const monthStart = new Date();
    monthStart.setDate(now.getDate() - 30);

    readiness.week.meals = records.filter((item: Record<string, any>) => new Date(`${item.record_date}T00:00:00`) >= weekStart).length;
    readiness.month.meals = records.filter((item: Record<string, any>) => new Date(`${item.record_date}T00:00:00`) >= monthStart).length;
    readiness.week.activeDays = weekTrendData.filter((item: Record<string, any>) => Number(item.energy || 0) > 0).length;
    readiness.month.activeDays = monthTrendData.filter((item: Record<string, any>) => Number(item.energy || 0) > 0).length;
    readiness.week.summary = weekData?.summary ?? null;
    readiness.month.summary = monthData?.summary ?? null;
    readiness.week.trend = weekTrendData;
    readiness.month.trend = monthTrendData;
  } catch {
    readinessRecords.value = [];
    readiness.week.activeDays = 0;
    readiness.month.activeDays = 0;
    readiness.week.meals = 0;
    readiness.month.meals = 0;
    readiness.week.summary = null;
    readiness.month.summary = null;
    readiness.week.trend = [];
    readiness.month.trend = [];
  } finally {
    loadingReadiness.value = false;
  }
}

async function generateReport() {
  // 月报和 PDF 导出（exportReport）均为 Pro 专享
  const isPdfExport = hasCustomRange.value || reportForm.report_type === "monthly";
  const isMonthly = reportForm.report_type === "monthly";
  if ((isPdfExport || isMonthly) && !auth.isPro) {
    proLockedVisible.value = true;
    return;
  }
  try {
    generating.value = true;

    let response;
    if (hasCustomRange.value) {
      response = await exportReport({
        report_type: reportForm.report_type,
        start_date: reportForm.dates[0],
        end_date: reportForm.dates[1],
      });
    } else if (reportForm.report_type === "monthly") {
      response = await monthlyReport();
    } else {
      response = await weeklyReport();
    }

    const data = unwrapPayload<Record<string, any>>(response, {});
    trackEvent({ behavior_type: "view", context_scene: `reports_${reportForm.report_type}` }).catch(() => undefined);
    await loadReportTasks(true);
    await loadDashboard(true);

    if (data?.file_url) {
      notifyActionSuccess("报表已生成，可直接打开查看");
      window.open(data.file_url, "_blank", "noopener,noreferrer");
    } else {
      notifyActionSuccess("报表已开始生成，页面会自动刷新结果");
    }
  } catch (error) {
    notifyActionError("生成报表");
  } finally {
    generating.value = false;
  }
}

onMounted(() => {
  loadReportTasks();
  loadReadiness();
  loadDashboard();
});

onBeforeUnmount(() => {
  if (pollTimer) {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }
});
</script>

<style scoped>
.page {
  display: grid;
  gap: 16px;
}

.head,
.card-head,
.review-stage-head,
.history-head,
.history-top,
.status-line,
.status-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.tag {
  margin: 0 0 6px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-size: 12px;
  color: #3e6d7f;
}

h2,
h3 {
  margin: 0;
}

h2 {
  font-size: 30px;
}

.desc,
.card-head p,
.review-stage-head p,
.review-hero-copy p,
.review-metric p,
.review-conclusion p,
.empty-state p,
.history-item p,
.history-meta,
.helper-box p,
.summary-grid p,
.status-item p,
.action-copy p {
  margin: 10px 0 0;
  color: #476072;
  line-height: 1.7;
}

.summary-grid,
.grid,
.coverage-grid {
  display: grid;
  gap: 14px;
}

.reports-topline-layout {
  display: grid;
  grid-template-columns: minmax(240px, 0.72fr) minmax(0, 1.28fr);
  gap: 18px;
  align-items: start;
}

.reports-summary-column {
  min-width: 0;
}

.summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
}

.compact-summary-grid {
  grid-template-columns: 1fr;
  gap: 10px;
}

.grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.coverage-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 14px;
}

.review-stage-card {
  grid-column: 1 / -1;
  background:
    radial-gradient(circle at top right, rgba(134, 197, 178, 0.22), transparent 30%),
    linear-gradient(135deg, rgba(250, 252, 255, 0.98), rgba(242, 248, 251, 0.96));
}

.summary-grid article,
.card,
.coverage-grid article {
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.summary-grid span,
.coverage-grid span,
.meta span,
.head-tip span,
.review-hero-copy span,
.review-metric span,
.review-conclusion span {
  display: block;
  font-size: 12px;
  color: #5a7a8a;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.section-kicker {
  margin: 0 0 8px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-size: 12px;
  color: #2f6672;
}

.summary-grid strong {
  display: block;
  margin-top: 8px;
  font-size: 24px;
}

.compact-summary-grid article {
  padding: 16px;
  border-radius: 18px;
}

.compact-summary-grid strong {
  font-size: 20px;
}

.compact-summary-grid p {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.45;
}

.coverage-grid strong {
  display: block;
  margin-top: 8px;
  font-size: 22px;
}

.generator-form {
  margin-top: 18px;
}

.helper-box,
.report-overview,
.empty-state,
.history-item,
.status-item,
.review-metric,
.review-conclusion,
.weekly-review-item,
.plan-focus-card,
.plan-item {
  margin-top: 14px;
  padding: 18px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.helper-box strong,
.meta strong,
.empty-state strong,
.history-item strong,
.status-item strong,
.review-hero-copy strong,
.review-metric strong,
.review-conclusion strong,
.weekly-review-copy strong,
.weekly-review-item strong,
.plan-focus-card strong,
.plan-copy strong {
  font-size: 18px;
}

.review-hero-copy p,
.review-metric p,
.review-conclusion p,
.status-item p,
.helper-box p,
.plan-copy p,
.weekly-review-item p {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.review-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  margin-top: 18px;
  padding: 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(16, 34, 42, 0.08);
}

.review-hero-copy strong {
  display: block;
  margin-top: 10px;
  font-size: 28px;
  line-height: 1.3;
}

.review-hero-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  min-width: 168px;
}

.review-link {
  color: #173042;
  font-weight: 700;
  text-decoration: none;
}

.review-metrics,
.review-conclusions {
  display: grid;
  gap: 12px;
  margin-top: 14px;
}

.review-metrics {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.review-conclusions {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.review-metric {
  margin-top: 0;
}

.review-metric strong,
.review-conclusion strong {
  display: block;
  margin-top: 10px;
}

.review-conclusion {
  margin-top: 0;
}

.review-conclusion.tone-warm {
  background: rgba(255, 248, 241, 0.96);
  border-color: rgba(185, 115, 38, 0.18);
}

.review-conclusion.tone-success {
  background: rgba(241, 252, 247, 0.96);
  border-color: rgba(29, 111, 95, 0.16);
}

.review-conclusion.tone-accent {
  background: rgba(240, 248, 255, 0.96);
  border-color: rgba(62, 109, 127, 0.16);
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.status-list,
.history-list,
.action-list,
.plan-list,
.weekly-review-grid {
  display: grid;
  gap: 12px;
  margin-top: 14px;
}

.action-item,
.plan-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 18px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.action-copy strong,
.plan-copy strong {
  font-size: 18px;
}

.plan-focus-card,
.weekly-review-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.plan-focus-card span,
.weekly-review-copy span,
.weekly-review-item span,
.plan-copy span,
.plan-focus-card strong,
.weekly-review-item strong {
  display: block;
}

.plan-focus-card span,
.weekly-review-copy span,
.weekly-review-item span,
.plan-copy span {
  font-size: 12px;
  color: #5a7a8a;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.weekly-review-copy strong {
  margin-top: 10px;
  font-size: 24px;
  line-height: 1.35;
}

.weekly-review-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.weekly-review-item,
.plan-focus-card,
.plan-item {
  margin-top: 0;
}

.plan-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  min-height: 40px;
  border-radius: 14px;
  background: rgba(23, 48, 66, 0.08);
  color: #173042;
  font-size: 14px;
  font-weight: 700;
}

.plan-copy {
  flex: 1;
}

.compact-status-list {
  margin-top: 16px;
}

.status-pill,
.history-status {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  background: #173042;
  color: #fff;
}

.status-pill.warm,
.history-status.is-processing,
.history-status.is-pending,
.status-pill.is-processing,
.status-pill.is-pending {
  background: #b97326;
}

.history-status.is-completed,
.status-pill.is-completed {
  background: #1d6f5f;
}

.history-status.is-failed,
.status-pill.is-failed {
  background: #9c3e3e;
}

.overview-tip {
  color: #5a7a8a;
  font-size: 13px;
}

.meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.download,
.history-actions {
  margin-top: 18px;
}

.download a,
.history-actions a {
  color: #173042;
  font-weight: 700;
  text-decoration: none;
}

.history-meta span,
.history-actions span {
  color: #5a7a8a;
}

.empty-state.compact {
  margin-top: 14px;
}

@media (max-width: 960px) {
  .reports-topline-layout,
  .grid,
  .coverage-grid,
  .review-metrics,
  .review-conclusions,
  .weekly-review-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .summary-grid article,
  .card,
  .coverage-grid article {
    padding: 16px;
    border-radius: 18px;
  }

  .summary-grid,
  .compact-summary-grid,
  .meta {
    grid-template-columns: 1fr;
  }

  .head,
  .card-head,
  .review-stage-head,
  .history-head,
  .history-top,
  .status-line,
  .status-row,
  .action-item,
  .plan-item,
  .plan-focus-card,
  .weekly-review-hero {
    flex-direction: column;
  }

  .review-hero {
    flex-direction: column;
  }

  .review-hero-copy strong {
    font-size: 22px;
  }

  .actions {
    flex-direction: column;
    align-items: stretch;
  }
}
.pro-lock-tag {
  margin-left: 4px;
  font-size: 11px;
  color: #7b3fe4;
  font-weight: 600;
}
</style>
