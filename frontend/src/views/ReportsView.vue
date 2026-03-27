<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Reports</p>
        <h2>健康报表</h2>
        <p class="desc">报表中心应该让用户看清当前有哪些结果、哪些还在生成，以及是否需要按自定义周期重新导出。</p>
      </div>
      <el-button :loading="loadingTasks" @click="loadReportTasks()">刷新记录</el-button>
    </div>

    <CollectionSkeleton v-if="showReportsSkeleton" variant="list" :card-count="5" :show-toolbar="false" />
    <RefreshFrame v-else :active="showReportsRefreshing" label="正在同步报表状态">
    <div class="summary-grid">
      <article>
        <span>累计报表</span>
        <strong>{{ reportSummary.total }}</strong>
        <p>已经沉淀下来的可回看结果数。</p>
      </article>
      <article>
        <span>已完成</span>
        <strong>{{ reportSummary.completed }}</strong>
        <p>可直接打开或下载的报表数量。</p>
      </article>
      <article>
        <span>生成中</span>
        <strong>{{ reportSummary.processing }}</strong>
        <p>{{ reportSummary.processing ? "页面会自动刷新，不需要重复点击。" : "当前没有正在处理的报表任务。" }}</p>
      </article>
      <article>
        <span>最近生成</span>
        <strong>{{ reportSummary.latestGenerated }}</strong>
        <p>帮助用户判断是否需要重新生成一份新周期报告。</p>
      </article>
    </div>

    <div class="grid">
      <div class="card">
        <div class="card-head">
          <div>
            <h3>记录覆盖度</h3>
            <p>先判断数据量够不够，再决定该出周报还是月报，避免用户空跑一次生成流程。</p>
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
            <h3>复盘提示</h3>
            <p>把最近记录转成更接近决策的信息，而不是让用户自己看一堆数字。</p>
          </div>
        </div>

        <div v-if="reportInsights.length" class="status-list">
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

      <div class="card">
        <div class="card-head">
          <div>
            <h3>建议动作</h3>
            <p>只保留当前最值得执行的动作，避免用户面对很多状态却不知道下一步是什么。</p>
          </div>
        </div>

        <div v-if="reportActionSuggestions.length" class="action-list">
          <article v-for="item in reportActionSuggestions" :key="item.key" class="action-item">
            <div class="action-copy">
              <strong>{{ item.title }}</strong>
              <p>{{ item.copy }}</p>
            </div>
            <el-button plain @click="handleReportSuggestion(item)">{{ item.cta }}</el-button>
          </article>
        </div>
        <PageStateBlock
          v-else
          tone="info"
          title="当前建议已经比较明确"
          description="可以继续查看最新报表，或者按推荐周期发起新的复盘。"
          compact
        />
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <div class="card-head">
          <div>
            <h3>生成新报表</h3>
            <p>支持推荐周期一键生成，也支持按自定义时间范围导出，不再把内部任务字段暴露给用户。</p>
          </div>
          <div class="head-tip">
            <span>{{ hasCustomRange ? "自定义时间范围" : "推荐周期" }}</span>
          </div>
        </div>

        <el-form label-position="top" class="generator-form">
          <el-form-item label="报表类型">
            <el-radio-group v-model="reportForm.report_type" class="mobile-scroll-row">
              <el-radio-button label="weekly">周报</el-radio-button>
              <el-radio-button label="monthly">月报</el-radio-button>
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
            <p>如果报表还在生成中，这里会持续提示并自动刷新，不需要让用户猜接口有没有成功。</p>
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
      <h3>最新报表</h3>
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

    <div class="card">
      <div class="history-head">
        <div>
          <h3>历史记录</h3>
          <p>保留最近生成的报表，方便你回看不同周期的变化，不展示内部任务细节。</p>
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
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import FormActionBar from "../components/FormActionBar.vue";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import TrendMiniBars from "../components/TrendMiniBars.vue";
import { notifyActionError, notifyActionSuccess, notifyLoadError } from "../lib/feedback";
import { exportReport, listReportTasks, monthlyReport, weeklyReport } from "../api/reports";
import { trackEvent } from "../api/behavior";
import { listMealRecords, mealStatistics } from "../api/tracking";

const router = useRouter();
const generating = ref(false);
const loadingTasks = ref(false);
const loadingReadiness = ref(false);
const autoRefreshing = ref(false);
const reportTasks = ref<Array<Record<string, any>>>([]);
const readiness = reactive({
  week: { activeDays: 0, meals: 0, summary: null as null | Record<string, any>, trend: [] as Record<string, any>[] },
  month: { activeDays: 0, meals: 0, summary: null as null | Record<string, any>, trend: [] as Record<string, any>[] },
});
const reportForm = reactive({
  report_type: "weekly",
  dates: [] as string[],
});

let pollTimer: ReturnType<typeof window.setInterval> | null = null;

const hasCustomRange = computed(() => reportForm.dates.length === 2);
const latestTask = computed(() => reportTasks.value[0] ?? null);
const latestCompletedTask = computed(() => reportTasks.value.find((task) => task.status === "completed" && task.file_url) ?? null);
const latestWeeklyTask = computed(() => reportTasks.value.find((task) => task.report_type === "weekly" && task.status === "completed" && task.file_url) ?? null);
const latestMonthlyTask = computed(() => reportTasks.value.find((task) => task.report_type === "monthly" && task.status === "completed" && task.file_url) ?? null);
const processingTasks = computed(() => reportTasks.value.filter((task) => ["pending", "processing"].includes(task.status)));
const showReportsSkeleton = computed(() => {
  return (loadingTasks.value || loadingReadiness.value) && !reportTasks.value.length && !readiness.week.meals && !readiness.month.meals;
});
const showReportsRefreshing = computed(() => !showReportsSkeleton.value && (loadingTasks.value || loadingReadiness.value));
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
const latestWeeklyAgeDays = computed(() => taskAgeDays(latestWeeklyTask.value));
const latestMonthlyAgeDays = computed(() => taskAgeDays(latestMonthlyTask.value));
const reportActionSuggestions = computed(() => {
  const actions: Array<{
    key: string;
    title: string;
    copy: string;
    cta: string;
    action:
      | { type: "route"; to: string }
      | { type: "refresh" }
      | { type: "open"; url: string }
      | { type: "generate"; reportType: "weekly" | "monthly" };
  }> = [];

  const registerAction = (
    key: string,
    title: string,
    copy: string,
    cta: string,
    action: { type: "route"; to: string } | { type: "refresh" } | { type: "open"; url: string } | { type: "generate"; reportType: "weekly" | "monthly" },
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
      "页面会自动刷新状态，不需要重复点击生成；如果想确认结果是否已经出来，可以手动刷新一次。",
      "刷新状态",
      { type: "refresh" },
    );
  }

  if (latestTask.value?.status === "failed") {
    registerAction(
      "retry-latest",
      "最近一次报表生成失败",
      "通常直接重试同类型推荐报表就够了，不需要用户理解内部任务细节。",
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

  return actions.slice(0, 4);
});
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
  action: { type: "route"; to: string } | { type: "refresh" } | { type: "open"; url: string } | { type: "generate"; reportType: "weekly" | "monthly" };
}) {
  if (item.action.type === "route") {
    router.push(item.action.to);
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
  await triggerRecommendedGeneration(item.action.reportType);
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
  }, 6000);
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

async function loadReadiness() {
  try {
    loadingReadiness.value = true;
    const [recordsResponse, weekStats, monthStats] = await Promise.all([listMealRecords(), mealStatistics("week"), mealStatistics("month")]);
    const records = unwrapList(recordsResponse);
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

.summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
}

.grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.coverage-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 14px;
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
.head-tip span {
  display: block;
  font-size: 12px;
  color: #5a7a8a;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.summary-grid strong {
  display: block;
  margin-top: 8px;
  font-size: 24px;
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
.status-item {
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
.status-item strong {
  font-size: 18px;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.status-list,
.history-list,
.action-list {
  display: grid;
  gap: 12px;
  margin-top: 14px;
}

.action-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 18px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.action-copy strong {
  font-size: 18px;
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
  .grid,
  .coverage-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .head,
  .card-head,
  .history-head,
  .history-top,
  .status-line,
  .status-row,
  .action-item {
    flex-direction: column;
  }
}
</style>
