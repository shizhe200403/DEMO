<template>
  <section class="dashboard">
    <CollectionSkeleton v-if="showDashboardSkeleton" variant="dashboard" :card-count="4" />
    <RefreshFrame v-else :active="loadingDashboard" label="正在更新首页数据">
    <div class="hero">
      <article class="hero-copy">
        <p class="tag">Today</p>
        <h2>{{ greetingTitle }}</h2>
        <p class="desc">
          先看今天还差什么，再决定下一餐怎么吃、怎么记，不把首页做成一块只读看板。
        </p>
        <div class="hero-status-strip">
          <span>{{ profileReady ? "档案已完善" : "先补档案" }}</span>
          <span>{{ activeGoal ? `${goalTypeLabel(activeGoal.goal_type)}进行中` : "还没有重点目标" }}</span>
          <span>{{ hasTodayRecord ? `${todayCompletedMealCount} 餐已记录` : "今天还没开记" }}</span>
        </div>
        <div class="cta-row mobile-scroll-row">
          <el-button type="primary" @click="goToNextMealRecord">{{ primaryRecordButtonLabel }}</el-button>
          <el-button @click="router.push('/favorites')">从收藏选餐</el-button>
          <el-button plain @click="router.push('/recipes')">看看推荐菜谱</el-button>
        </div>
      </article>

      <article class="panel today-workbench">
        <div class="panel-header">
          <div>
            <h3>今天工作台</h3>
            <p>先回答还差什么、下一餐怎么选、能不能一键记上，不让首页变成只读总览。</p>
          </div>
        </div>

        <div class="today-topline">
          <div class="today-copy">
            <span class="workbench-kicker">Today Flow</span>
            <strong>{{ todayWorkbenchHeadline }}</strong>
            <p>{{ todayWorkbenchDescription }}</p>
          </div>
          <div class="today-primary-actions">
            <el-button type="primary" @click="goToNextMealRecord">{{ primaryRecordButtonLabel }}</el-button>
            <el-button v-if="todaySuggestedRecipe" plain @click="addToRecord(todaySuggestedRecipe)">一键带入推荐菜</el-button>
          </div>
        </div>

        <div class="meal-progress-grid">
          <article v-for="item in todayMealChecklist" :key="item.value" class="meal-progress-card" :class="{ done: item.done, active: item.value === nextMealFocusType }">
            <span>{{ item.label }}</span>
            <strong>{{ item.done ? "已记录" : item.value === nextMealFocusType ? "建议优先" : "待补" }}</strong>
            <p>{{ item.done ? "今天这餐已经落下记录。" : `下一步可先补${item.label}。` }}</p>
          </article>
        </div>

        <div class="metric-grid">
          <article v-for="item in focusMetricCards" :key="item.key" class="metric-card" :class="`is-${item.tone}`">
            <div class="metric-top">
              <span>{{ item.label }}</span>
              <em>{{ item.badge }}</em>
            </div>
            <strong>{{ item.value }}</strong>
            <p>{{ item.copy }}</p>
          </article>
        </div>

        <div class="today-lower-grid">
          <article class="today-suggest-card">
            <span>下一餐更省事</span>
            <strong>{{ todaySuggestedRecipe?.title || "先去挑一顿合适的菜" }}</strong>
            <p>{{ todaySuggestedRecipeCopy }}</p>
            <div class="footer-actions">
              <el-button v-if="todaySuggestedRecipe" text @click="openFavoriteDetail(todaySuggestedRecipe)">查看详情</el-button>
              <el-button v-if="todaySuggestedRecipe" type="primary" plain @click="addToRecord(todaySuggestedRecipe)">加入记录</el-button>
              <el-button v-else plain @click="router.push('/recipes')">去菜谱库</el-button>
            </div>
          </article>

          <div v-if="heroNextActions.length" class="action-list compact-action-list">
            <article v-for="item in heroNextActions" :key="item.title" class="action-item">
              <div>
                <strong>{{ item.title }}</strong>
                <p>{{ item.copy }}</p>
              </div>
              <el-button plain @click="router.push(item.to)">{{ item.cta }}</el-button>
            </article>
          </div>
        </div>
      </article>
    </div>

    <div class="panel">
      <div class="panel-header">
        <div>
          <h3>推荐菜谱</h3>
          <p>优先展示更适合你当前目标和饮食约束的选择，让“下一餐吃什么”更容易落地。</p>
        </div>
        <div class="head-actions">
          <el-button plain @click="loadDashboard">刷新推荐</el-button>
          <el-button plain @click="router.push('/recipes')">去菜谱库</el-button>
        </div>
      </div>

      <div v-if="recommendations.length" class="recommend-list">
        <article v-for="item in recommendations" :key="item.recipe_id">
          <div class="row">
            <strong>{{ item.title }}</strong>
            <div class="recommend-actions">
              <el-button text @click="openRecipeDetail(item)">查看详情</el-button>
              <el-button text @click="showReason(item.recipe_id)">为什么推荐</el-button>
            </div>
          </div>
          <p>{{ item.reason_text }}</p>
        </article>
      </div>
      <PageStateBlock
        v-else
        tone="empty"
        title="当前还没有可展示的推荐"
        description="先完善健康档案或补充几条饮食记录，系统才能逐步学到你的偏好。"
        action-label="去完善资料"
        @action="router.push('/profile')"
      />
    </div>

    <div class="secondary-grid">
      <article class="panel">
        <div class="panel-header">
          <div>
            <h3>收藏捷径</h3>
            <p>把已经验证过的菜谱直接变成下一餐入口，而不是每次从头筛选。</p>
          </div>
          <el-button text @click="router.push('/favorites')">管理收藏</el-button>
        </div>
        <div v-if="favoriteShortcuts.length" class="shortcut-list">
          <article v-for="item in favoriteShortcuts" :key="item.id" class="shortcut-item">
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.description || "已收藏，可直接加入记录。" }}</p>
            </div>
            <div class="shortcut-actions">
              <el-button text @click="openFavoriteDetail(item)">查看详情</el-button>
              <el-button type="primary" plain @click="addToRecord(item)">加入记录</el-button>
            </div>
          </article>
        </div>
        <PageStateBlock
          v-else
          tone="empty"
          title="还没有收藏沉淀"
          description="遇到合适的菜谱先收藏，后续记录会快很多。"
          action-label="去菜谱库"
          compact
          @action="router.push('/recipes')"
        />
      </article>

      <article class="panel">
        <div class="panel-header">
          <div>
            <h3>最近记录</h3>
            <p>帮助你快速确认最近吃了什么，避免今天继续重复或漏记。</p>
          </div>
          <el-button text @click="router.push('/records')">查看全部</el-button>
        </div>
        <div v-if="recentRecords.length" class="record-list">
          <article v-for="record in recentRecords.slice(0, 4)" :key="record.id" class="record-item">
            <div>
              <strong>{{ record.record_date }} · {{ mealTypeLabel(record.meal_type) }}</strong>
              <p>{{ record.items?.[0]?.recipe_title || record.note || "已记录一餐" }}</p>
            </div>
            <span>{{ record.items?.length || 0 }} 条目</span>
          </article>
        </div>
        <PageStateBlock
          v-else
          tone="empty"
          title="最近还没有记录"
          description="先记一餐，系统才会开始形成趋势与推荐。"
          action-label="去记录"
          compact
          @action="router.push('/records')"
        />
      </article>
    </div>

    <div class="workbench-grid">
      <article class="panel">
        <div class="panel-header">
          <div>
            <h3>最近7天热量节奏</h3>
            <p>把今天放回最近一周里看，才更容易判断是偶发还是持续偏移。</p>
          </div>
          <el-button text @click="router.push('/records')">去记录</el-button>
        </div>
        <TrendMiniBars
          v-if="weekEnergyBars.length"
          title="最近7天热量节奏"
          description="看一眼最近几天的整体摄入强弱，判断今天是不是明显偏高或偏低。"
          badge="近7天"
          tone="energy"
          compact
          :items="weekEnergyBars"
        />
        <PageStateBlock
          v-else
          tone="empty"
          title="最近还没有趋势数据"
          description="先记录几餐，热量节奏和趋势判断才会开始出现。"
          compact
        />
      </article>

      <article class="panel">
        <div class="panel-header">
          <div>
            <h3>当前目标</h3>
            <p>优先关注一项正在推进的目标，避免页面里全是概念却没有行动。</p>
          </div>
          <el-button text @click="router.push('/goals')">去目标页</el-button>
        </div>
        <div v-if="activeGoal" class="focus-box">
          <div class="focus-topline">
            <strong>{{ goalTypeLabel(activeGoal.goal_type) }}</strong>
            <span class="focus-badge">{{ goalProgressLabel }}</span>
          </div>
          <p>{{ activeGoal.description || "已创建目标，建议继续补录进展。" }}</p>
          <div class="progress-line">
            <span>当前 {{ formatDecimal(activeGoal.current_value) }}</span>
            <span>目标 {{ formatDecimal(activeGoal.target_value) }}</span>
          </div>
          <el-progress :percentage="goalProgressPercent" :stroke-width="10" :show-text="false" />
        </div>
        <PageStateBlock
          v-else
          tone="empty"
          title="你还没有正在进行的目标"
          description="先创建一个最明确的健康目标，首页才会形成真正的工作台。"
          action-label="去创建目标"
          compact
          @action="router.push('/goals')"
        />
      </article>

      <article class="panel">
        <div class="panel-header">
          <div>
            <h3>最新报表</h3>
            <p>最近生成的报表会沉淀在这里，方便你快速回到复盘环节。</p>
          </div>
          <el-button text @click="router.push('/reports')">去报表页</el-button>
        </div>
        <div v-if="latestReport" class="focus-box">
          <strong>{{ reportTypeLabel(latestReport.report_type) }} · {{ reportStatusLabel(latestReport.status) }}</strong>
          <p>{{ formatDateRange(latestReport.start_date, latestReport.end_date) }}</p>
          <a v-if="latestReport.file_url" :href="latestReport.file_url" target="_blank" rel="noreferrer">打开最新报表</a>
        </div>
        <PageStateBlock
          v-else
          tone="empty"
          title="还没有生成过报表"
          description="当记录累计起来后，再做周报和月报才有复盘价值。"
          action-label="去报表页"
          compact
          @action="router.push('/reports')"
        />
      </article>
    </div>

    <div v-if="onboardingSteps.length" class="panel onboarding-panel">
      <div class="panel-header">
        <div>
          <h3>起步引导</h3>
          <p>只有在关键基础还没铺开时才显示，把资料、记录和报表先走通一遍就够了。</p>
        </div>
      </div>
      <div class="onboarding-list">
        <article v-for="item in onboardingSteps" :key="item.title" class="onboarding-item">
          <div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.copy }}</p>
          </div>
          <el-button plain @click="router.push(item.to)">{{ item.cta }}</el-button>
        </article>
      </div>
    </div>

    <RecipeDetailDialog
      v-model="detailVisible"
      :recipe-id="selectedRecipeId"
      :recipe="selectedRecipe"
      :favorited="selectedRecipeId ? favoriteIds.includes(selectedRecipeId) : false"
      :reason-text="selectedReasonText"
      @favorite-change="handleFavoriteChange"
      @add-to-record="addToRecord"
    />
    </RefreshFrame>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import TrendMiniBars from "../components/TrendMiniBars.vue";
import { ElMessageBox, notifyLoadError } from "../lib/feedback";
import { useRouter } from "vue-router";
import RecipeDetailDialog from "../components/RecipeDetailDialog.vue";
import { useAuthStore } from "../stores/auth";
import { explainRecommendation, listFavoriteRecipes, listRecommendations, profileRecommendations } from "../api/recipes";
import { getMe } from "../api/auth";
import { trackEvent } from "../api/behavior";
import { nutritionAnalysis } from "../api/nutrition";
import { listMealRecords, mealStatistics } from "../api/tracking";
import { listHealthGoals } from "../api/goals";
import { listReportTasks } from "../api/reports";

const router = useRouter();
const auth = useAuthStore();
const loadingDashboard = ref(true);
const dashboardReady = ref(false);
const recommendations = ref<Array<{ recipe_id: number; title: string; reason_text: string }>>([]);
const favoriteIds = ref<number[]>([]);
const favoriteItems = ref<any[]>([]);
const favoriteCount = ref(0);
const recentRecords = ref<any[]>([]);
const goals = ref<any[]>([]);
const reportTasks = ref<any[]>([]);
const weekTrend = ref<Array<Record<string, any>>>([]);
const todayMetrics = reactive({
  energy: 0,
  protein: 0,
  fat: 0,
  carbohydrate: 0,
});
const nutritionSummary = reactive({
  bmi: "-",
  goal_hint: "",
  calorie_target: "-",
  protein_target: "-",
});
const detailVisible = ref(false);
const selectedRecipeId = ref<number | null>(null);
const selectedRecipe = ref<Record<string, any> | null>(null);
const selectedReasonText = ref("");
const showDashboardSkeleton = computed(() => loadingDashboard.value && !dashboardReady.value);

const profileReady = computed(() => {
  const profile = auth.user?.profile;
  return Boolean(profile?.height_cm && profile?.weight_kg && profile?.target_weight_kg);
});
const greetingTitle = computed(() => {
  const name = auth.user?.nickname || auth.user?.username || "你";
  return `${name}，先看进度，再做动作。`;
});
const activeGoal = computed(() => goals.value.find((item) => item.status === "active") ?? null);
const latestReport = computed(() => reportTasks.value[0] ?? null);
const favoriteShortcuts = computed(() => favoriteItems.value.slice(0, 3));
const hasTodayRecord = computed(() => recentRecords.value.some((item) => item.record_date === todayString()));
const todayRecordSet = computed(() => new Set(recentRecords.value.filter((item) => item.record_date === todayString()).map((item) => item.meal_type)));
const todayMealChecklist = computed(() => [
  { label: "早餐", value: "breakfast", done: todayRecordSet.value.has("breakfast") },
  { label: "午餐", value: "lunch", done: todayRecordSet.value.has("lunch") },
  { label: "晚餐", value: "dinner", done: todayRecordSet.value.has("dinner") },
  { label: "加餐", value: "snack", done: todayRecordSet.value.has("snack") },
]);
const todayCompletedMealCount = computed(() => todayMealChecklist.value.filter((item) => item.done).length);
const nextMealFocusType = computed<"breakfast" | "lunch" | "dinner" | "snack">(() => {
  const anchor = currentMealType();
  if (!todayRecordSet.value.has(anchor)) {
    return anchor;
  }
  return (
    ["breakfast", "lunch", "dinner", "snack"].find((mealType) => !todayRecordSet.value.has(mealType)) || "snack"
  ) as "breakfast" | "lunch" | "dinner" | "snack";
});
const calorieTargetNumber = computed(() => Number(nutritionSummary.calorie_target) || 0);
const proteinTargetNumber = computed(() => Number(nutritionSummary.protein_target) || 0);
const energyGap = computed(() => Math.max(0, calorieTargetNumber.value - todayMetrics.energy));
const proteinGap = computed(() => Math.max(0, proteinTargetNumber.value - todayMetrics.protein));
const weekRecordedDays = computed(() => weekTrend.value.slice(-7).filter((item) => Number(item.energy || 0) > 0).length);
const weekAverageEnergy = computed(() => {
  const activeDays = weekTrend.value
    .slice(-7)
    .map((item) => Number(item.energy || 0))
    .filter((value) => value > 0);
  if (!activeDays.length) {
    return 0;
  }
  return activeDays.reduce((sum, value) => sum + value, 0) / activeDays.length;
});
const latestReportAgeDays = computed(() => {
  const generatedAt = latestReport.value?.generated_at;
  if (!generatedAt) {
    return null;
  }
  const diff = Date.now() - new Date(generatedAt).getTime();
  if (!Number.isFinite(diff) || diff < 0) {
    return null;
  }
  return Math.floor(diff / (1000 * 60 * 60 * 24));
});
const todayMetricCards = computed(() => {
  const items = [
    {
      key: "energy",
      label: "热量",
      value: formatMetric(todayMetrics.energy, "kcal"),
      target: Number(nutritionSummary.calorie_target) || 0,
    },
    {
      key: "protein",
      label: "蛋白质",
      value: formatMetric(todayMetrics.protein, "g"),
      target: Number(nutritionSummary.protein_target) || 0,
    },
    {
      key: "fat",
      label: "脂肪",
      value: formatMetric(todayMetrics.fat, "g"),
      target: 0,
    },
    {
      key: "carbohydrate",
      label: "碳水",
      value: formatMetric(todayMetrics.carbohydrate, "g"),
      target: 0,
    },
  ];

  return items.map((item) => {
    const actual = Number(todayMetrics[item.key as keyof typeof todayMetrics]) || 0;
    if (item.target > 0) {
      const ratio = actual / item.target;
      return {
        ...item,
        badge: ratio >= 1 ? "已达标" : ratio >= 0.7 ? "接近目标" : "仍有缺口",
        tone: ratio >= 1 ? "success" : ratio >= 0.7 ? "steady" : "warning",
        copy: ratio >= 1 ? `已达到今日目标 ${formatMetric(item.target, item.key === "energy" ? "kcal" : "g")}` : `目标 ${formatMetric(item.target, item.key === "energy" ? "kcal" : "g")}`,
      };
    }
    return {
      ...item,
      badge: actual > 0 ? "已记录" : "暂无",
      tone: actual > 0 ? "steady" : "muted",
      copy: actual > 0 ? "今日已有摄入记录" : "今天还没有相关摄入数据",
    };
  });
});
const focusMetricCards = computed(() => todayMetricCards.value.slice(0, 2));
const heroNextActions = computed(() => nextActions.value.slice(0, 3));
const todaySuggestedRecipe = computed<Record<string, any> | null>(() => {
  const favoriteMatch = favoriteItems.value.find((item) => item.meal_type === nextMealFocusType.value) ?? favoriteItems.value[0];
  if (favoriteMatch) {
    return favoriteMatch;
  }
  const recommendationMatch = recommendations.value.find((item) => item.meal_type === nextMealFocusType.value) ?? recommendations.value[0];
  if (!recommendationMatch) {
    return null;
  }
  return {
    id: recommendationMatch.recipe_id,
    title: recommendationMatch.title,
    description: recommendationMatch.reason_text,
    meal_type: recommendationMatch.meal_type || nextMealFocusType.value,
  };
});
const primaryRecordButtonLabel = computed(() => `去记${mealTypeLabel(nextMealFocusType.value)}`);
const todayProgressSummary = computed(() => {
  if (!hasTodayRecord.value) {
    return "今天还没有任何记录，先记下一餐，系统才知道你现在差多少。";
  }
  if (proteinTargetNumber.value > 0 && proteinGap.value >= 18) {
    return `今天蛋白质还差约 ${formatMetric(proteinGap.value, "g")}，下一餐更适合优先补高蛋白。`;
  }
  if (calorieTargetNumber.value > 0 && todayMetrics.energy > calorieTargetNumber.value * 1.15) {
    return "今天热量已经明显偏高，后续一餐更适合轻负担一点。";
  }
  if (calorieTargetNumber.value > 0 && energyGap.value > 0) {
    return `距离今日热量目标还差约 ${formatMetric(energyGap.value, "kcal")}，可以继续补一餐或补记录。`;
  }
  return "今天主要指标已经接近目标，可以把注意力放到记录连续性和下一餐质量。";
});
const todayWorkbenchHeadline = computed(() => {
  if (!hasTodayRecord.value) {
    return "先把今天第一餐记上";
  }
  if (todayMealChecklist.value.every((item) => item.done)) {
    return "今天的主线已经基本齐了";
  }
  if (proteinTargetNumber.value > 0 && proteinGap.value >= 18) {
    return `先补${mealTypeLabel(nextMealFocusType.value)}，顺手把蛋白缺口拉上来`;
  }
  return `现在最值得先补${mealTypeLabel(nextMealFocusType.value)}`;
});
const todayWorkbenchDescription = computed(() => {
  if (!hasTodayRecord.value) {
    return "先记一餐，今天的缺口、推荐和复盘建议才会真正开始运转。";
  }
  if (todayMealChecklist.value.every((item) => item.done)) {
    return "如果只是补录，优先去记录页复用上一餐；如果今天已经记全，就回看趋势和报表。";
  }
  if (proteinTargetNumber.value > 0 && proteinGap.value >= 18) {
    return `今天蛋白还差约 ${formatMetric(proteinGap.value, "g")}，下一餐优先补高蛋白会比继续观望更有效。`;
  }
  if (calorieTargetNumber.value > 0 && energyGap.value > 0) {
    return `距离今日热量目标还差约 ${formatMetric(energyGap.value, "kcal")}，现在直接补上下一餐最省事。`;
  }
  return `当前最自然的动作是先补${mealTypeLabel(nextMealFocusType.value)}，别让今天断在半路。`;
});
const todaySuggestedRecipeCopy = computed(() => {
  if (!todaySuggestedRecipe.value) {
    return "如果收藏和推荐还不够，就直接去菜谱库按当前时段挑一顿更合适的。";
  }
  if (favoriteIds.value.includes(Number(todaySuggestedRecipe.value.id))) {
    return "这道菜已经进过你的收藏，直接带入记录会更快。";
  }
  if (todaySuggestedRecipe.value.meal_type === nextMealFocusType.value) {
    return `它更贴近当前该补的${mealTypeLabel(nextMealFocusType.value)}，可以直接一键带入记录。`;
  }
  return todaySuggestedRecipe.value.description || "这是当前更值得先看的下一餐候选。";
});
const weekEnergyBars = computed(() => {
  return weekTrend.value.slice(-7).map((item, index, source) => ({
    label: String(item.date || "").slice(5),
    value: Number(item.energy || 0),
    display: `${Number(item.energy || 0).toFixed(0)}`,
    highlight: index === source.length - 1,
  }));
});
const goalProgressPercent = computed(() => {
  const goal = activeGoal.value;
  if (!goal) {
    return 0;
  }
  const target = Number(goal.target_value || 0);
  const current = Number(goal.current_value || 0);
  if (!target) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round((current / target) * 100)));
});
const goalProgressLabel = computed(() => {
  if (!activeGoal.value) {
    return "";
  }
  if (goalProgressPercent.value >= 100) {
    return "已达成";
  }
  if (goalProgressPercent.value >= 70) {
    return "推进顺畅";
  }
  return "继续推进";
});
const nextActions = computed(() => {
  const actions: Array<{ title: string; copy: string; cta: string; to: string }> = [];
  const registerAction = (title: string, copy: string, cta: string, to: string) => {
    if (actions.some((item) => item.title === title)) {
      return;
    }
    actions.push({ title, copy, cta, to });
  };

  if (!profileReady.value) {
    registerAction("先补齐健康档案", "身高、体重和目标体重是推荐和目标计算的基础。", "去完善", "/profile");
  }
  if (!activeGoal.value) {
    registerAction("建立一个重点目标", "有了明确目标，推荐、记录和报表会更贴近你当前的需要。", "去创建", "/goals");
  }
  if (!hasTodayRecord.value) {
    registerAction("补上今天第一条记录", "先记录一餐，系统才知道今天的摄入与缺口。", "去记录", "/records");
  }
  if (hasTodayRecord.value && proteinTargetNumber.value > 0 && proteinGap.value >= 18) {
    registerAction(
      "今天蛋白质还有明显缺口",
      `距离今日目标还差约 ${formatMetric(proteinGap.value, "g")}，优先补一份高蛋白菜谱更有效。`,
      favoriteCount.value ? "去收藏中心" : "去找菜谱",
      favoriteCount.value ? "/favorites" : "/recipes",
    );
  }
  if (hasTodayRecord.value && calorieTargetNumber.value > 0 && todayMetrics.energy > calorieTargetNumber.value * 1.15) {
    registerAction(
      "今天热量已经偏高",
      "后续一餐更适合选择轻负担、低油低糖的搭配，避免继续上冲。",
      "看菜谱建议",
      "/recipes",
    );
  }
  if (hasTodayRecord.value && calorieTargetNumber.value > 0 && todayMetrics.energy > 0 && todayMetrics.energy < calorieTargetNumber.value * 0.55) {
    registerAction(
      "今天热量还偏低",
      `当前距离目标还差约 ${formatMetric(energyGap.value, "kcal")}，如果还有一餐未记，先补记录。`,
      "继续补记录",
      "/records",
    );
  }
  if (weekRecordedDays.value > 0 && weekRecordedDays.value < 4) {
    registerAction("这一周记录连续性偏弱", "最近 7 天活跃天数还不够，先把记录连续性补起来，再看趋势和报表。", "去补记录", "/records");
  }
  if (weekRecordedDays.value >= 4 && (!latestReport.value || (latestReportAgeDays.value ?? 999) >= 7)) {
    registerAction(
      "可以安排一次阶段复盘",
      "最近一周已经有基本记录覆盖，适合生成新周报，把输入变成复盘结果。",
      "去报表页",
      "/reports",
    );
  }
  if (weekAverageEnergy.value > 0 && calorieTargetNumber.value > 0 && weekAverageEnergy.value > calorieTargetNumber.value * 1.1) {
    registerAction(
      "最近一周整体摄入偏高",
      "过去几天的平均热量已经持续高于目标，建议从收藏或菜谱里替换掉一两道高负担选择。",
      favoriteCount.value ? "去收藏中心" : "去菜谱库",
      favoriteCount.value ? "/favorites" : "/recipes",
    );
  }
  if (!favoriteCount.value) {
    registerAction("沉淀几个可复用菜谱", "收藏越完整，后续记录和决策成本越低。", "去挑选", "/recipes");
  }
  return actions.slice(0, 4);
});
const onboardingSteps = computed(() => {
  const steps = [];
  if (!profileReady.value) {
    steps.push({
      title: "完善档案",
      copy: "先补齐身高、体重和目标体重，后续推荐与目标才不会漂。",
      cta: "去完善",
      to: "/profile",
    });
  }
  if (!recentRecords.value.length) {
    steps.push({
      title: "记录第一餐",
      copy: "先形成一条真实饮食记录，首页、统计和报表才会开始动起来。",
      cta: "去记录",
      to: "/records",
    });
  }
  if (!favoriteCount.value) {
    steps.push({
      title: "收藏常用菜谱",
      copy: "把可复用选择沉淀下来，之后每天记录会更顺手。",
      cta: "去收藏",
      to: "/recipes",
    });
  }
  if (!latestReport.value && recentRecords.value.length) {
    steps.push({
      title: "生成第一份周报",
      copy: "有了基础记录后，生成一份周报会更容易看清这一周的变化。",
      cta: "去报表",
      to: "/reports",
    });
  }
  return steps.slice(0, 4);
});

function todayString() {
  const date = new Date();
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function currentMealType(): "breakfast" | "lunch" | "dinner" | "snack" {
  const hour = new Date().getHours();
  if (hour < 10) {
    return "breakfast";
  }
  if (hour < 15) {
    return "lunch";
  }
  if (hour < 20) {
    return "dinner";
  }
  return "snack";
}

function formatMetric(value: unknown, unit: string) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) {
    return `0 ${unit}`;
  }
  return `${number.toFixed(unit === "kcal" ? 0 : 1)} ${unit}`;
}

function formatDecimal(value: unknown) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "-";
  }
  return number.toFixed(1);
}

function goalTypeLabel(value: string) {
  return {
    weight_loss: "减重",
    muscle_gain: "增肌",
    blood_sugar_control: "控糖",
    fat_control: "控脂",
    protein_up: "提升蛋白摄入",
    diet_balance: "饮食均衡",
  }[value] || value;
}

function mealTypeLabel(value: string) {
  return {
    breakfast: "早餐",
    lunch: "午餐",
    dinner: "晚餐",
    snack: "加餐",
  }[value] || value;
}

function reportTypeLabel(type: string) {
  return type === "monthly" ? "月报" : "周报";
}

function reportStatusLabel(status: string) {
  return {
    pending: "等待中",
    processing: "生成中",
    completed: "已完成",
    failed: "失败",
  }[status] || status;
}

function formatDateRange(startDate?: string, endDate?: string) {
  if (!startDate && !endDate) {
    return "未记录";
  }
  return `${startDate || "-"} 至 ${endDate || "-"}`;
}

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

async function loadDashboard() {
  try {
    loadingDashboard.value = true;
    const [meResult, recommendationResult, nutritionResult, favoriteResult, goalResult, reportResult, statsResult, recordsResult] =
      await Promise.allSettled([
        getMe(),
        listRecommendations(),
        nutritionAnalysis(),
        listFavoriteRecipes(),
        listHealthGoals(),
        listReportTasks(),
        mealStatistics("week"),
        listMealRecords(),
      ]);

    const meResponse = meResult.status === "fulfilled" ? meResult.value : null;
    const recommendationResponse = recommendationResult.status === "fulfilled" ? recommendationResult.value : null;
    const nutritionResponse = nutritionResult.status === "fulfilled" ? nutritionResult.value : null;
    const favoriteResponse = favoriteResult.status === "fulfilled" ? favoriteResult.value : null;
    const goalResponse = goalResult.status === "fulfilled" ? goalResult.value : null;
    const reportResponse = reportResult.status === "fulfilled" ? reportResult.value : null;
    const statsResponse = statsResult.status === "fulfilled" ? statsResult.value : null;
    const recordsResponse = recordsResult.status === "fulfilled" ? recordsResult.value : null;

    if (!meResponse && !recommendationResponse && !nutritionResponse) {
      throw new Error("dashboard load failed");
    }

    const meData = unwrapPayload<Record<string, any> | null>(meResponse, null);
    const nutritionData = unwrapPayload<Record<string, any>>(nutritionResponse, {});
    const recommendationData = unwrapList(recommendationResponse);
    // 若 home 推荐为空，尝试 by-profile 推荐作为 fallback
    let finalRecommendationData = recommendationData;
    if (!recommendationData.length) {
      try {
        const profileResult = await profileRecommendations();
        finalRecommendationData = unwrapList(profileResult);
      } catch {
        // ignore
      }
    }
    const favoriteData = unwrapList(favoriteResponse);
    const goalData = unwrapList(goalResponse);
    const reportData = unwrapList(reportResponse);
    const statsData = unwrapPayload<Record<string, any>>(statsResponse, {});
    const recordData = unwrapList(recordsResponse);

    auth.user = meData ?? auth.user;

    const profile = meData?.profile;
    const height = profile?.height_cm ? Number(profile.height_cm) : 0;
    const weight = profile?.weight_kg ? Number(profile.weight_kg) : 0;
    if (height > 0 && weight > 0) {
      nutritionSummary.bmi = (weight / ((height / 100) * (height / 100))).toFixed(1);
    }

    const health = meData?.health_condition;
    if (health?.has_diabetes) {
      nutritionSummary.goal_hint = "优先控制碳水与添加糖";
    } else if (health?.has_hypertension) {
      nutritionSummary.goal_hint = "优先控制钠摄入";
    } else if (health?.has_hyperlipidemia) {
      nutritionSummary.goal_hint = "优先控制脂肪摄入";
    } else {
      nutritionSummary.goal_hint = "保持均衡饮食";
    }

    nutritionSummary.calorie_target = nutritionData?.calorie_target ?? "-";
    nutritionSummary.protein_target = nutritionData?.protein_target ?? "-";

    recommendations.value = finalRecommendationData.map((item: Record<string, any>) => ({
      recipe_id: Number(item.recipe_id),
      title: item.title,
      reason_text: item.reason_text,
      meal_type: item.meal_type || item.recipe?.meal_type || "lunch",
    }));

    favoriteItems.value = favoriteData;
    favoriteIds.value = favoriteData.map((item: Record<string, any>) => Number(item.id));
    favoriteCount.value = favoriteData.length;
    goals.value = goalData;
    reportTasks.value = reportData;
    recentRecords.value = recordData;

    const trend = Array.isArray(statsData?.trend) ? statsData.trend : [];
    weekTrend.value = trend;
    const today = trend[trend.length - 1];
    todayMetrics.energy = Number(today?.energy || 0);
    todayMetrics.protein = Number(today?.protein || 0);
    todayMetrics.fat = Number(today?.fat || 0);
    todayMetrics.carbohydrate = Number(today?.carbohydrate || 0);

    trackEvent({ behavior_type: "view", context_scene: "home" }).catch(() => undefined);
  } catch (error) {
    notifyLoadError("首页数据");
  } finally {
    dashboardReady.value = true;
    loadingDashboard.value = false;
  }
}

async function showReason(recipeId: number) {
  try {
    const response = await explainRecommendation(recipeId);
    const reasonData = unwrapPayload<Record<string, any>>(response, {});
    await ElMessageBox.alert(reasonData?.reason_text || "暂无推荐理由", "推荐说明", {
      confirmButtonText: "知道了",
    });
  } catch (error) {
    notifyLoadError("推荐说明");
  }
}

async function openRecipeDetail(item: { recipe_id: number; title: string; reason_text: string }) {
  selectedRecipeId.value = item.recipe_id;
  selectedRecipe.value = {
    id: item.recipe_id,
    title: item.title,
    description: item.reason_text,
  };
  selectedReasonText.value = item.reason_text;
  detailVisible.value = true;
}

function openFavoriteDetail(recipe: Record<string, any>) {
  selectedRecipeId.value = Number(recipe.id);
  selectedRecipe.value = recipe;
  selectedReasonText.value = "";
  detailVisible.value = true;
}

function addToRecord(recipe: Record<string, any>) {
  router.push({
    path: "/records",
    query: {
      recipe_id: String(recipe.id),
      meal_type: recipe.meal_type || "lunch",
      note: recipe.title || "",
    },
  });
}

function goToNextMealRecord() {
  router.push({
    path: "/records",
    query: {
      meal_type: nextMealFocusType.value,
      note: `今天的${mealTypeLabel(nextMealFocusType.value)}`,
    },
  });
}

function handleFavoriteChange(payload: { recipeId: number; favorited: boolean }) {
  if (payload.favorited && !favoriteIds.value.includes(payload.recipeId)) {
    favoriteIds.value = [...favoriteIds.value, payload.recipeId];
    favoriteCount.value += 1;
    return;
  }
  if (!payload.favorited) {
    favoriteIds.value = favoriteIds.value.filter((id) => id !== payload.recipeId);
    favoriteItems.value = favoriteItems.value.filter((item) => Number(item.id) !== payload.recipeId);
    favoriteCount.value = Math.max(0, favoriteCount.value - 1);
  }
}

onMounted(loadDashboard);
</script>

<style scoped>
.dashboard {
  display: grid;
  gap: 20px;
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(360px, 1.08fr);
  gap: 20px;
}

.hero-copy,
.panel {
  padding: 28px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.tag {
  margin: 0 0 10px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  font-size: 12px;
  color: #3e6d7f;
}

h2 {
  margin: 0;
  font-size: clamp(32px, 4vw, 52px);
  line-height: 1.05;
}

.desc {
  margin: 14px 0 0;
  color: #476072;
  line-height: 1.8;
}

.cta-row,
.head-actions,
.recommend-actions,
.shortcut-actions,
.today-topline,
.today-primary-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.cta-row {
  margin-top: 24px;
}

.hero-status-strip,
.hero-meta-grid {
  display: grid;
  gap: 12px;
  margin-top: 18px;
}

.hero-status-strip {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.hero-status-strip span {
  padding: 10px 12px;
  border-radius: 16px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
  color: #24566a;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.5;
}

.hero-meta-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.today-workbench {
  background:
    radial-gradient(circle at top right, rgba(123, 173, 204, 0.18), transparent 30%),
    linear-gradient(135deg, rgba(250, 252, 255, 0.98), rgba(242, 248, 251, 0.96));
}

.workbench-kicker {
  margin: 0 0 8px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-size: 12px;
  color: #2f6672;
}

.today-copy strong {
  display: block;
  font-size: 30px;
  line-height: 1.25;
}

.today-copy p {
  margin: 10px 0 0;
  color: #476072;
  line-height: 1.75;
}

.today-topline,
.today-lower-grid {
  display: grid;
  gap: 14px;
  margin-top: 18px;
}

.today-topline {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
}

.today-primary-actions {
  justify-content: flex-end;
  align-items: flex-start;
}

.meal-progress-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.meal-progress-card,
.today-suggest-card {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(16, 34, 42, 0.08);
}

.meal-progress-card span {
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #5a7a8a;
}

.meal-progress-card strong {
  display: block;
  margin-top: 8px;
  font-size: 18px;
}

.meal-progress-card p,
.today-suggest-card p {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.6;
}

.meal-progress-card.done {
  background: rgba(224, 247, 238, 0.9);
  border-color: rgba(31, 120, 89, 0.16);
}

.meal-progress-card.active {
  background: rgba(255, 245, 231, 0.92);
  border-color: rgba(185, 115, 38, 0.16);
}

.today-lower-grid {
  grid-template-columns: minmax(260px, 0.9fr) minmax(0, 1.1fr);
}

.today-suggest-card span {
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #5a7a8a;
}

.today-suggest-card strong {
  display: block;
  margin-top: 8px;
  font-size: 22px;
}

.compact-action-list {
  margin-top: 0;
}

.hero-meta-grid article {
  padding: 16px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.hero-meta-grid strong {
  display: block;
  margin-top: 8px;
  font-size: 22px;
}

.hero-meta-grid p {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.6;
}

.summary-grid,
.workbench-grid,
.secondary-grid,
.action-list,
.recommend-list,
.shortcut-list,
.record-list,
.onboarding-list {
  display: grid;
  gap: 14px;
}

.workbench-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.secondary-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.summary-grid article,
.recommend-list article,
.empty-state,
.focus-box,
.action-item,
.shortcut-item,
.record-item,
.onboarding-item {
  padding: 18px;
  border-radius: 20px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.summary-grid span,
.metric-grid span,
.progress-line span,
.record-item span {
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #5a7a8a;
}

.summary-grid strong,
.metric-grid strong,
.focus-box strong,
.action-item strong,
.shortcut-item strong,
.record-item strong {
  display: block;
  margin-top: 8px;
  font-size: 22px;
}

.summary-grid p,
.panel-header p,
.recommend-list p,
.empty-state p,
.focus-box p,
.action-item p,
.shortcut-item p,
.record-item p,
.onboarding-item p {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.65;
}

.panel-header,
.row,
.action-item,
.shortcut-item,
.record-item,
.onboarding-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.panel-header h3 {
  margin: 0;
  font-size: 22px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  padding: 16px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.metric-top,
.focus-topline {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.metric-top em,
.focus-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-style: normal;
  color: #24566a;
  background: #e8f1f7;
}

.metric-card.is-success .metric-top em {
  background: rgba(224, 247, 238, 0.95);
  color: #1d6f5f;
}

.metric-card.is-warning .metric-top em {
  background: rgba(255, 237, 218, 0.95);
  color: #b97326;
}

.metric-card.is-muted .metric-top em {
  background: rgba(232, 241, 247, 0.95);
  color: #5a7a8a;
}

.progress-line {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
}

.focus-box a {
  display: inline-block;
  margin-top: 14px;
  color: #173042;
  font-weight: 700;
  text-decoration: none;
}

@media (max-width: 1080px) {
  .hero,
  .workbench-grid,
  .secondary-grid,
  .today-topline,
  .today-lower-grid,
  .meal-progress-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero-copy,
  .panel,
  .summary-grid article,
  .recommend-list article,
  .focus-box,
  .action-item,
  .shortcut-item,
  .record-item,
  .onboarding-item {
    padding: 16px;
    border-radius: 18px;
  }

  .cta-row {
    margin-top: 16px;
  }

  .summary-grid,
  .metric-grid,
  .hero-status-strip,
  .hero-meta-grid,
  .workbench-grid,
  .secondary-grid,
  .meal-progress-grid,
  .today-lower-grid {
    grid-template-columns: 1fr;
  }

  .panel-header,
  .row,
  .action-item,
  .shortcut-item,
  .record-item,
  .onboarding-item,
  .metric-top,
  .focus-topline,
  .today-topline,
  .today-primary-actions {
    flex-direction: column;
  }

  .today-copy strong {
    font-size: 24px;
  }
}
</style>
