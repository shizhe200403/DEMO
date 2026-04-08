<template>
  <section class="records-page">

    <!-- 顶部栏 -->
    <div class="page-topbar">
      <div class="topbar-left">
        <h2>饮食记录</h2>
        <p class="topbar-hint">记录每一餐，热量与营养实时统计</p>
      </div>
      <div class="topbar-right">
        <el-select v-model="period" style="width: 130px" @change="loadRecords">
          <el-option label="最近7天" value="week" />
          <el-option label="最近30天" value="month" />
        </el-select>
      </div>
    </div>

    <CollectionSkeleton v-if="loadingRecords && !records.length" variant="list" :card-count="5" />
    <RefreshFrame v-else :active="loadingRecords && !!records.length" label="正在更新记录与统计">

    <!-- 双栏主体 -->
    <div class="records-layout">

      <!-- 左侧 sidebar -->
      <aside class="records-sidebar">

        <!-- 今日进度 -->
        <div class="sidebar-card today-card">
          <span class="sidebar-label">今日进度</span>
          <div class="progress-rows">
            <div class="progress-item" :class="{ 'is-save-pulse': recordCompletionPulse }">
              <div class="progress-top">
                <span>热量</span>
                <strong>{{ todayMetricLabel(animatedTodayEnergy, energyTarget, "kcal") }}</strong>
              </div>
              <el-progress :percentage="progressPercent(animatedTodayEnergy, energyTarget)" :stroke-width="8" :show-text="false" />
              <p>{{ remainingCopy(animatedTodayEnergy, energyTarget, "kcal", "热量") }}</p>
            </div>
            <div class="progress-item" :class="{ 'is-save-pulse': recordCompletionPulse }">
              <div class="progress-top">
                <span>蛋白质</span>
                <strong>{{ todayMetricLabel(animatedTodayProtein, proteinTarget, "g") }}</strong>
              </div>
              <el-progress :percentage="progressPercent(animatedTodayProtein, proteinTarget)" :stroke-width="8" :show-text="false" />
              <p>{{ remainingCopy(animatedTodayProtein, proteinTarget, "g", "蛋白质") }}</p>
            </div>
          </div>
          <div class="meal-checklist">
            <div
              v-for="item in mealChecklist"
              :key="item.value"
              v-spotlight
              class="meal-chip"
              :class="{ done: item.done, 'is-save-pulse': recordCompletionPulse && item.done }"
            >
              <span>{{ item.label }}</span>
              <strong>{{ item.done ? "已记录" : "待补充" }}</strong>
            </div>
          </div>
        </div>

        <!-- 快捷操作 -->
        <div class="sidebar-card actions-card">
          <span class="sidebar-label">下一餐操作</span>
          <p class="workbench-status-line">{{ workbenchStatus }}</p>
          <strong class="workbench-headline">{{ workbenchHeadline }}</strong>
          <div class="quick-action-btns">
            <el-button type="primary" size="small" @click="applyQuickMeal(recommendedMealType)">
              {{ `快速记${mealTypeLabel(recommendedMealType)}` }}
            </el-button>
            <el-button v-if="latestReusableRecord" size="small" plain @click="applyRecordTemplate(latestReusableRecord)">复制最近一餐</el-button>
            <el-button v-if="recommendedMealYesterdayRecord" size="small" plain @click="applyRecordTemplate(recommendedMealYesterdayRecord)">复制昨天同餐</el-button>
            <el-button size="small" plain @click="openAssistantForRecordPlan">AI 建议</el-button>
          </div>
        </div>

        <!-- 周期概览统计 -->
        <div class="sidebar-card summary-card">
          <span class="sidebar-label">{{ period === "week" ? "最近7天" : "最近30天" }}</span>
          <div class="stat-rows">
            <div class="stat-row"><span>记录餐次</span><strong>{{ animatedFilteredRecordCount }}</strong></div>
            <div class="stat-row"><span>活跃天数</span><strong>{{ animatedActiveDayCount }}</strong></div>
            <div class="stat-row"><span>已关联菜谱</span><strong>{{ animatedLinkedRecipeCount }}</strong></div>
          </div>
        </div>

        <!-- 周期营养卡 -->
        <div class="sidebar-card period-cards">
          <div v-for="item in periodSummaryCards" :key="item.key" class="period-item" :class="`tone-${item.tone}`">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <p>{{ item.copy }}</p>
          </div>
        </div>

      </aside>

      <!-- 右侧主内容 -->
      <main class="records-main">

        <!-- 新增一餐表单 -->
        <div class="content-card form-card">
          <div class="card-header">
            <h3>{{ editingRecordId ? "编辑记录" : "新增一餐" }}</h3>
            <p>关联菜谱后热量与营养自动计算，只填备注也可以。</p>
          </div>

          <article v-spotlight class="form-rhythm-banner" :class="{ 'is-ready': !recordSubmitDisabled, 'is-editing': !!editingRecordId }">
            <div class="form-rhythm-copy">
              <span>{{ editingRecordId ? "正在编辑" : "当前输入状态" }}</span>
              <strong>{{ recordFormTitle }}</strong>
              <p>{{ recordFormDescription }}</p>
            </div>
            <div class="form-rhythm-meta">
              <span>{{ mealTypeLabel(form.meal_type) }}</span>
              <span>{{ form.record_date || "待选日期" }}</span>
            </div>
          </article>

          <el-form :model="form" label-position="top">
            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="日期">
                  <el-date-picker
                    v-model="form.record_date"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="选择日期"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="餐次">
                  <el-select v-model="form.meal_type" style="width: 100%">
                    <el-option label="早餐" value="breakfast" />
                    <el-option label="午餐" value="lunch" />
                    <el-option label="晚餐" value="dinner" />
                    <el-option label="加餐" value="snack" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="关联菜谱">
                  <el-select v-model="form.recipe_id" clearable filterable placeholder="选择菜谱（可选）" style="width: 100%">
                    <el-option v-for="recipe in recipeOptions" :key="recipe.id" :label="recipe.title" :value="recipe.id" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="备注">
              <el-input v-model.trim="form.note" placeholder="例如：公司午餐、外卖、聚餐等" />
            </el-form-item>

            <div class="quick-helpers mobile-scroll-row">
              <el-button plain @click="applyQuickMeal('breakfast')">快速记早餐</el-button>
              <el-button plain @click="applyQuickMeal('lunch')">快速记午餐</el-button>
              <el-button plain @click="applyQuickMeal('dinner')">快速记晚餐</el-button>
              <el-button plain @click="applyQuickMeal('snack')">快速记加餐</el-button>
              <el-button plain @click="applyToday">切到今天</el-button>
              <el-button v-if="yesterdaySameMealRecord" plain @click="copyYesterdayMeal">复制昨天同餐</el-button>
            </div>

            <div v-spotlight class="helper-panel">
              <div>
                <strong>没有合适的菜谱？</strong>
                <p>常吃的菜谱先上传进来，热量营养手动填也行，后面 AI 可以帮你补齐。</p>
              </div>
              <div class="helper-actions">
                <el-button plain @click="router.push('/recipes')">去上传菜谱</el-button>
                <el-button plain :disabled="!mealDraftReadyForAi" @click="openAssistantForMealDraft">让 AI 帮我补全这一餐</el-button>
              </div>
            </div>
            <div v-if="recordHandoff" v-spotlight class="record-handoff">
              <div class="record-handoff-copy">
                <span class="record-handoff-badge">{{ recordHandoff.badge }}</span>
                <strong>{{ recordHandoff.title }}</strong>
                <p>{{ recordHandoff.description }}</p>
              </div>
              <div class="record-handoff-actions">
                <el-button plain @click="router.push(recordHandoff.to)">{{ recordHandoff.cta }}</el-button>
                <el-button text @click="clearRecordHandoff">关闭提示</el-button>
              </div>
            </div>

            <div v-if="recentRecipeShortcuts.length || frequentRecipeShortcuts.length" class="shortcut-panel">
              <div v-if="recentRecipeShortcuts.length" class="shortcut-block">
                <span class="shortcut-label">最近吃过</span>
                <div class="shortcut-list mobile-scroll-row">
                  <button v-for="item in recentRecipeShortcuts" :key="`recent-${item.recipe_id}`" type="button" v-spotlight class="shortcut-card interactive-shortcut-card" @click="applyRecipeShortcut(item)">
                    <strong>{{ item.title }}</strong>
                    <small>{{ mealTypeLabel(item.meal_type || 'lunch') }} · {{ item.last_used_date }}</small>
                  </button>
                </div>
              </div>
              <div v-if="frequentRecipeShortcuts.length" class="shortcut-block">
                <span class="shortcut-label">常吃</span>
                <div class="shortcut-list mobile-scroll-row">
                  <button v-for="item in frequentRecipeShortcuts" :key="`frequent-${item.recipe_id}`" type="button" v-spotlight class="shortcut-card interactive-shortcut-card" @click="applyRecipeShortcut(item)">
                    <strong>{{ item.title }}</strong>
                    <small>{{ item.count }} 次记录 · {{ mealTypeLabel(item.meal_type || 'lunch') }}</small>
                  </button>
                </div>
              </div>
            </div>

            <div v-if="selectedRecipe" v-spotlight class="recipe-preview">
              <div class="preview-head">
                <div>
                  <strong>{{ selectedRecipe.title }}</strong>
                  <p>{{ selectedRecipe.description || "已选中菜谱，保存后会自动计入营养统计。" }}</p>
                </div>
                <span>{{ mealTypeLabel(selectedRecipe.meal_type || "lunch") }}</span>
              </div>
              <div class="preview-metrics">
                <span>热量 {{ formatMetric(selectedRecipe.nutrition_summary?.per_serving_energy, "kcal") }}</span>
                <span>蛋白 {{ formatMetric(selectedRecipe.nutrition_summary?.per_serving_protein, "g") }}</span>
                <span>脂肪 {{ formatMetric(selectedRecipe.nutrition_summary?.per_serving_fat, "g") }}</span>
                <span>碳水 {{ formatMetric(selectedRecipe.nutrition_summary?.per_serving_carbohydrate, "g") }}</span>
              </div>
            </div>
            <div v-if="savePreview" v-spotlight class="save-preview" :class="{ 'is-save-pulse': recordCompletionPulse }">
              <div class="save-preview-copy">
                <span class="save-preview-badge">{{ savePreview.badge }}</span>
                <strong>{{ savePreview.title }}</strong>
                <p>{{ savePreview.description }}</p>
              </div>
              <div class="save-preview-highlights">
                <span v-for="item in savePreview.highlights" :key="item">{{ item }}</span>
              </div>
            </div>
            <FormActionBar
              :tone="saving ? 'saving' : recordFormTone"
              :title="recordFormTitle"
              :description="recordFormDescription"
              :primary-label="editingRecordId ? '保存修改' : '保存记录'"
              :secondary-label="editingRecordId ? '取消编辑' : '清空本次输入'"
              :disabled="recordSubmitDisabled"
              :loading="saving"
              @primary="saveRecord"
              @secondary="resetForm"
            />
            <div v-if="lastSavedFollowUp" v-spotlight class="save-follow-up" :class="{ 'is-save-pulse': recordCompletionPulse }">
              <div class="save-follow-up-copy">
                <span class="save-follow-up-badge">{{ lastSavedFollowUp.badge }}</span>
                <strong>{{ lastSavedFollowUp.title }}</strong>
                <p>{{ lastSavedFollowUp.description }}</p>
                <div v-if="lastSavedFollowUp.highlights.length" class="save-follow-up-highlights">
                  <span v-for="item in lastSavedFollowUp.highlights" :key="item">{{ item }}</span>
                </div>
              </div>
              <div class="save-follow-up-actions">
                <el-button
                  v-for="action in lastSavedFollowUp.actions"
                  :key="action.label"
                  :type="action.primary ? 'primary' : 'default'"
                  :plain="!action.primary"
                  @click="runFollowUpAction(action)"
                >
                  {{ action.label }}
                </el-button>
              </div>
            </div>
          </el-form>
        </div>

        <!-- 模板快速记录 -->
        <div v-if="recentRecordTemplates.length" class="content-card template-card">
          <div class="card-header">
            <h3>最近照着记</h3>
            <p>昨天吃了什么、上次吃了什么，直接复用，省得重新找。</p>
          </div>
          <div class="template-grid">
            <button
              v-for="item in recentRecordTemplates"
              :key="item.id"
              type="button"
              v-spotlight
              class="template-card-item interactive-template-card"
              @click="applyRecordTemplate(item)"
            >
              <span>{{ mealTypeLabel(item.meal_type || "lunch") }}</span>
              <strong>{{ recordPrimaryTitle(item) }}</strong>
              <p>{{ recordSecondaryLabel(item) }}</p>
            </button>
          </div>
        </div>

        <!-- 记录列表 -->
        <div class="content-card list-card">
          <div class="card-header">
            <h3>最近记录</h3>
            <p>同一天同一餐再保存会覆盖旧的，按日期分好组。</p>
          </div>

          <div v-for="group in groupedRecords" :key="group.date" class="day-group">
            <div class="day-head">
              <strong>{{ group.date }}</strong>
              <p>共 {{ group.records.length }} 餐 · 热量 {{ formatMetric(group.energy, "kcal") }} · 蛋白 {{ formatMetric(group.protein, "g") }}</p>
            </div>

            <article v-for="record in group.records" :key="record.id" v-spotlight class="history-record-card">
              <div class="record-head">
                <div>
                  <strong>{{ mealTypeLabel(record.meal_type) }}</strong>
                  <p>{{ record.note || "未填写备注" }}</p>
                </div>
                <div class="record-actions">
                  <el-button text @click="editRecord(record)">编辑</el-button>
                  <el-button text @click="reuseRecord(record)">再记一餐</el-button>
                  <el-button text type="danger" :loading="deletingId === record.id" @click="removeRecord(record.id)">删除</el-button>
                </div>
              </div>
              <p class="muted">
                共 {{ record.items?.length || 0 }} 个条目
                <span v-if="record.items?.length">
                  · {{ record.items[0].recipe_title || record.items[0].ingredient_name_snapshot || "已关联菜谱" }}
                </span>
                <span v-if="recordEnergy(record) > 0"> · 热量 {{ formatMetric(recordEnergy(record), "kcal") }}</span>
              </p>
            </article>
          </div>

          <PageStateBlock
            v-if="!groupedRecords.length"
            tone="empty"
            title="最近还没有饮食记录"
            description="先新增一餐，顶部统计和趋势会在保存后自动刷新。"
            action-label="快速记午餐"
            @action="applyQuickMeal('lunch')"
          >
            <div class="first-run-guide">
              <article>
                <strong>先选餐次</strong>
                <p>如果今天只是想快速落一条数据，先点上面的快速记早餐/午餐/晚餐。</p>
              </article>
              <article>
                <strong>有菜谱就关联</strong>
                <p>关联菜谱后，热量和营养会自动带出，后面的统计和报表才更有意义。</p>
              </article>
              <article>
                <strong>没有菜谱也能记</strong>
                <p>哪怕只有一句备注，也先把记录补上，后续再慢慢把数据补细。</p>
              </article>
            </div>
          </PageStateBlock>
        </div>

        <!-- 趋势明细 -->
        <div class="content-card trend-card">
          <h3>趋势明细</h3>
          <TrendMiniBars
            v-if="trendBars.length"
            title="当前周期热量走势"
            :description="trendHeadline"
            :badge="period === 'week' ? '最近7天' : '最近30天'"
            tone="energy"
            :items="trendBars"
          />
          <div v-if="stats.trend.length" class="trend">
            <article v-for="item in stats.trend" :key="item.date">
              <strong>{{ item.date }}</strong>
              <p>热量 {{ formatMetric(item.energy, "kcal") }} · 蛋白 {{ formatMetric(item.protein, "g") }}</p>
            </article>
          </div>
          <PageStateBlock
            v-else
            tone="empty"
            title="当前周期还没有趋势数据"
            description="多记几餐，热量和蛋白的走势就慢慢出来了。"
            compact
          />
        </div>

      </main>
    </div>
    </RefreshFrame>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import FormActionBar from "../components/FormActionBar.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import TrendMiniBars from "../components/TrendMiniBars.vue";
import { ElMessageBox, notifyActionError, notifyActionSuccess, notifyLoadError, notifyWarning } from "../lib/feedback";
import { createMealRecord, copyYesterdayMealRecords, deleteMealRecord, listMealRecords, mealStatistics, updateMealRecord } from "../api/tracking";
import { listRecipes } from "../api/recipes";
import { trackEvent } from "../api/behavior";
import { useRoute, useRouter } from "vue-router";
import { nutritionAnalysis } from "../api/nutrition";
import { useAnimatedNumber } from "../composables/useAnimatedNumber";

const route = useRoute();
const router = useRouter();
const period = ref("week");
const saving = ref(false);
const deletingId = ref<number | null>(null);
const editingRecordId = ref<number | null>(null);
const loadingRecords = ref(false);
const records = ref<any[]>([]);
const recordCompletionPulse = ref(false);
let recordCompletionTimer: ReturnType<typeof window.setTimeout> | null = null;
const lastSavedFollowUp = ref<null | {
  badge: string;
  title: string;
  description: string;
  highlights: string[];
  actions: Array<{
    label: string;
    primary?: boolean;
    to?: string;
    mealType?: "breakfast" | "lunch" | "dinner" | "snack";
  }>;
}>(null);
const recipeOptions = ref<Array<Record<string, any>>>([]);
const stats = reactive({
  summary: null as null | Record<string, any>,
  trend: [] as any[],
});
const targets = reactive({
  calorie: 0,
  protein: 0,
});
const todaySummary = reactive({
  energy: 0,
  protein: 0,
  fat: 0,
  carbohydrate: 0,
});
const form = reactive({
  record_date: "",
  meal_type: "lunch",
  recipe_id: null as null | number,
  note: "",
});

const selectedRecipe = computed(() => recipeOptions.value.find((item) => Number(item.id) === Number(form.recipe_id)) ?? null);
const recordSubmitDisabled = computed(() => !form.record_date || (!form.recipe_id && !form.note.trim()));
const recordFormTone = computed(() => (recordSubmitDisabled.value ? "warning" : "ready"));
const recordFormTitle = computed(() => {
  if (!form.record_date) {
    return "先选择记录日期";
  }
  if (!form.recipe_id && !form.note.trim()) {
    return "至少选择菜谱或填写备注";
  }
  return editingRecordId.value ? "本次修改可以提交" : "本条记录可以保存";
});
const recordFormDescription = computed(() => {
  if (selectedRecipe.value) {
    return "已关联菜谱，保存后会自动计入热量和营养统计。";
  }
  return "如果暂时没有匹配菜谱，也可以先记备注，后续再慢慢补细。";
});
const recipeShortcutSource = computed(() => {
  const map = new Map<number, { recipe_id: number; title: string; meal_type: string; last_used_date: string; count: number }>();

  records.value.forEach((record) => {
    (record.items ?? []).forEach((item: Record<string, any>) => {
      const recipeId = Number(item.recipe_id || 0);
      if (!recipeId) {
        return;
      }
      const existing = map.get(recipeId);
      if (!existing) {
        map.set(recipeId, {
          recipe_id: recipeId,
          title: item.recipe_title || record.note || "已记录菜谱",
          meal_type: record.meal_type || "lunch",
          last_used_date: record.record_date || "",
          count: 1,
        });
        return;
      }
      existing.count += 1;
      if ((record.record_date || "") > existing.last_used_date) {
        existing.last_used_date = record.record_date || existing.last_used_date;
        existing.meal_type = record.meal_type || existing.meal_type;
        existing.title = item.recipe_title || existing.title;
      }
    });
  });

  return Array.from(map.values());
});
const recentRecipeShortcuts = computed(() => recipeShortcutSource.value.slice().sort((a, b) => `${b.last_used_date}`.localeCompare(`${a.last_used_date}`)).slice(0, 4));
const frequentRecipeShortcuts = computed(() => recipeShortcutSource.value.slice().sort((a, b) => b.count - a.count || `${b.last_used_date}`.localeCompare(`${a.last_used_date}`)).slice(0, 4));
const yesterdaySameMealRecord = computed(() => {
  return findYesterdayMealRecord(form.meal_type);
});
const filteredRecords = computed(() => {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - (period.value === "month" ? 30 : 7));
  cutoff.setHours(0, 0, 0, 0);
  return [...records.value]
    .filter((record) => {
      const recordDate = new Date(`${record.record_date}T00:00:00`);
      return recordDate >= cutoff;
    })
    .sort((a, b) => `${b.record_date} ${b.meal_type}`.localeCompare(`${a.record_date} ${a.meal_type}`));
});
const groupedRecords = computed(() => {
  const groups = new Map<string, { date: string; records: any[]; energy: number; protein: number }>();
  filteredRecords.value.forEach((record) => {
    if (!groups.has(record.record_date)) {
      groups.set(record.record_date, { date: record.record_date, records: [], energy: 0, protein: 0 });
    }
    const group = groups.get(record.record_date)!;
    group.records.push(record);
    group.energy += recordEnergy(record);
    group.protein += recordProtein(record);
  });
  return Array.from(groups.values());
});
const linkedRecipeCount = computed(
  () => filteredRecords.value.filter((record) => record.items?.some((item: Record<string, any>) => item.recipe_id)).length,
);
const animatedTodayEnergy = useAnimatedNumber(computed(() => Number(todaySummary.energy || 0)), { duration: 520, decimals: 1 });
const animatedTodayProtein = useAnimatedNumber(computed(() => Number(todaySummary.protein || 0)), { duration: 520, decimals: 1 });
const animatedFilteredRecordCount = useAnimatedNumber(computed(() => filteredRecords.value.length));
const animatedActiveDayCount = useAnimatedNumber(computed(() => groupedRecords.value.length));
const animatedLinkedRecipeCount = useAnimatedNumber(linkedRecipeCount);
const energyTarget = computed(() => targets.calorie);
const proteinTarget = computed(() => targets.protein);
const periodSummaryCards = computed(() => {
  const activeDays = groupedRecords.value.length || 1;
  const totalEnergy = numericValue(stats.summary?.energy);
  const totalProtein = numericValue(stats.summary?.protein);
  return [
    {
      key: "energy",
      label: "热量",
      value: formatMetric(totalEnergy, "kcal"),
      copy: `日均 ${formatMetric(totalEnergy / activeDays, "kcal")}`,
      tone: totalEnergy > 0 ? "energy" : "muted",
    },
    {
      key: "protein",
      label: "蛋白质",
      value: formatMetric(totalProtein, "g"),
      copy: `日均 ${formatMetric(totalProtein / activeDays, "g")}`,
      tone: totalProtein >= activeDays * 20 ? "success" : "muted",
    },
    {
      key: "fat",
      label: "脂肪",
      value: formatMetric(stats.summary?.fat, "g"),
      copy: "关注整体均衡，不只看单日高低",
      tone: "muted",
    },
    {
      key: "carbohydrate",
      label: "碳水",
      value: formatMetric(stats.summary?.carbohydrate, "g"),
      copy: "结合目标与体感判断是否需要调整",
      tone: "muted",
    },
  ];
});
const trendBars = computed(() => {
  return stats.trend.slice(-7).map((item: Record<string, any>, index: number, source: Record<string, any>[]) => ({
    label: String(item.date || "").slice(5),
    value: numericValue(item.energy),
    display: `${numericValue(item.energy).toFixed(0)}`,
    highlight: index === source.length - 1,
  }));
});
const trendHeadline = computed(() => {
  if (!trendBars.value.length) {
    return "多记几餐，热量走势就慢慢出来了。";
  }
  const values = trendBars.value.map((item) => item.value);
  const average = values.reduce((total, value) => total + value, 0) / values.length;
  return `最近可见日均约 ${average.toFixed(0)} kcal，适合先看整体节奏，再判断某一天是否异常偏高。`;
});
const todayRecordSet = computed(() => new Set(records.value.filter((record) => record.record_date === todayString()).map((record) => record.meal_type)));
const mealChecklist = computed(() => {
  return [
    { label: "早餐", value: "breakfast", done: todayRecordSet.value.has("breakfast") },
    { label: "午餐", value: "lunch", done: todayRecordSet.value.has("lunch") },
    { label: "晚餐", value: "dinner", done: todayRecordSet.value.has("dinner") },
    { label: "加餐", value: "snack", done: todayRecordSet.value.has("snack") },
  ];
});
const latestReusableRecord = computed(() => {
  return [...records.value]
    .sort((left, right) => buildRecordSortValue(right) - buildRecordSortValue(left))
    .find((record) => Boolean(record.id)) ?? null;
});
const recentRecordTemplates = computed(() => {
  const seen = new Set<string>();
  return [...records.value]
    .sort((left, right) => buildRecordSortValue(right) - buildRecordSortValue(left))
    .filter((record) => {
      const recipeId = Number(record.items?.[0]?.recipe_id || 0);
      const signature = `${record.meal_type || "lunch"}::${recipeId || 0}::${record.note || ""}`;
      if (seen.has(signature)) {
        return false;
      }
      seen.add(signature);
      return true;
    })
    .slice(0, 4);
});
const recommendedMealType = computed<"breakfast" | "lunch" | "dinner" | "snack">(() => {
  const anchorMeal = currentTimeMealType();
  if (!todayRecordSet.value.has(anchorMeal)) {
    return anchorMeal;
  }
  return (
    ["breakfast", "lunch", "dinner", "snack"].find((mealType) => !todayRecordSet.value.has(mealType)) || "snack"
  ) as "breakfast" | "lunch" | "dinner" | "snack";
});
const recommendedMealYesterdayRecord = computed(() => findYesterdayMealRecord(recommendedMealType.value));
const mealDraftReadyForAi = computed(() => Boolean(form.note.trim() || form.recipe_id));
const prefillSource = computed(() => String(route.query.source || "").trim());
const recordHandoff = computed<null | { badge: string; title: string; description: string; cta: string; to: string }>(() => {
  const source = prefillSource.value;
  const fromTitle = String(route.query.from_title || "").trim();
  const dishLabel = selectedRecipe.value?.title || form.note.trim() || fromTitle;

  if (source === "home") {
    return {
      badge: "首页接续",
      title: "你正在接首页的今天工作台",
      description: dishLabel
        ? `当前带入的是「${dishLabel}」。保存完这条记录后，可以直接回首页继续看今天还差什么。`
        : "这是从首页工作台接过来的记录动作，保存后再回首页看今天进度会更顺。",
      cta: "回首页工作台",
      to: "/",
    };
  }

  if (source === "recipes") {
    return {
      badge: "菜谱接续",
      title: "你正在接菜谱页的决策结果",
      description: dishLabel
        ? `当前带入的是「${dishLabel}」。如果这条记录顺利落下，就等于把刚才在菜谱页的决策真正执行了。`
        : "这是从菜谱页带过来的选择，先记上这一餐，再决定要不要继续挑下一道。",
      cta: "回菜谱页",
      to: "/recipes",
    };
  }

  if (source === "favorites") {
    return {
      badge: "收藏接续",
      title: "你正在把常用收藏落成今天记录",
      description: dishLabel
        ? `当前带入的是「${dishLabel}」。把收藏真正记进今天，首页和趋势才会开始反映这次选择。`
        : "这是从收藏中心带过来的常用选择，先记上这一餐，收藏才真正变成执行资产。",
      cta: "回收藏中心",
      to: "/favorites",
    };
  }

  return null;
});
const workbenchStatus = computed(() => {
  const missingCount = mealChecklist.value.filter((item) => !item.done).length;
  if (!records.value.length) {
    return "先记第一餐";
  }
  if (missingCount === 0) {
    return "今天主线已齐";
  }
  return `还差 ${missingCount} 餐`;
});
const workbenchHeadline = computed(() => {
  const missingCount = mealChecklist.value.filter((item) => !item.done).length;
  if (!records.value.length) {
    return "先把今天第一餐记上";
  }
  if (missingCount === 0) {
    return "今天三餐主线已经基本齐了";
  }
  if (recommendedMealYesterdayRecord.value) {
    return `先补${mealTypeLabel(recommendedMealType.value)}，可以直接复制昨天同餐`;
  }
  return `现在最适合先补${mealTypeLabel(recommendedMealType.value)}`;
});
const workbenchDescription = computed(() => {
  if (!records.value.length) {
    return "先保存一餐，今天进度、趋势和后续建议才会真正开始运转。";
  }
  if (mealChecklist.value.every((item) => item.done)) {
    return "如果只是补录，优先复制最近一餐；如果今天已经记全，可以按需补加餐或回看趋势。";
  }
  if (recommendedMealYesterdayRecord.value) {
    return `昨天已经记过${mealTypeLabel(recommendedMealType.value)}，这次直接复用会比重新选菜谱更省事。`;
  }
  if (latestReusableRecord.value) {
    return "最近已有可复用内容，优先从“复制最近一餐”或“最近照着记”开始，效率会更高。";
  }
  return "先选一个最接近当前场景的餐次，把今天的记录连续性补起来。";
});
const savePreview = computed<null | { badge: string; title: string; description: string; highlights: string[] }>(() => {
  if (!form.record_date || (!form.recipe_id && !form.note.trim())) {
    return null;
  }

  const recordDate = form.record_date;
  const mealType = form.meal_type;
  const isToday = recordDate === todayString();
  const isEditing = Boolean(editingRecordId.value);
  const selectedRecipeEnergy = numericValue(selectedRecipe.value?.nutrition_summary?.per_serving_energy);
  const selectedRecipeProtein = numericValue(selectedRecipe.value?.nutrition_summary?.per_serving_protein);
  const dateRecords = records.value.filter((record) => record.record_date === recordDate);
  const existingSameMealRecord = dateRecords.find(
    (record) => record.meal_type === mealType && Number(record.id) !== Number(editingRecordId.value || 0),
  );
  const projectedMealCount = new Set([
    ...dateRecords
      .filter((record) => Number(record.id) !== Number(editingRecordId.value || 0))
      .map((record) => record.meal_type),
    mealType,
  ]).size;
  const nextMeal = nextMealType(mealType);

  if (!isToday) {
    return {
      badge: isEditing ? "修改预览" : "保存预览",
      title: `${mealTypeLabel(mealType)}会归档到 ${recordDate}`,
      description: existingSameMealRecord
        ? "这个日期同餐次已经有记录，保存后会以当前内容覆盖它。"
        : "保存后这条记录会进入对应日期，不会影响今天的即时进度卡片。",
      highlights: [
        `归档日期 ${recordDate}`,
        existingSameMealRecord ? "同餐次将被覆盖" : `当日将累计 ${projectedMealCount} 餐`,
        `完成后可继续补${mealTypeLabel(nextMeal)}`,
      ],
    };
  }

  if (!form.recipe_id) {
    return {
      badge: isEditing ? "修改预览" : "保存预览",
      title: `${mealTypeLabel(mealType)}会先作为备注记录保存`,
      description: "这能先把今天的连续性补上，但不会自动增加热量和蛋白统计，后续最好补成正式菜谱。",
      highlights: [
        `今日将累计 ${projectedMealCount} / 4 餐`,
        "营养统计暂不增加",
        `下一步建议补${mealTypeLabel(nextMeal)}`,
      ],
    };
  }

  const projectedEnergy = todaySummary.energy + selectedRecipeEnergy;
  const projectedProtein = todaySummary.protein + selectedRecipeProtein;
  return {
    badge: isEditing ? "修改预览" : "保存预览",
    title: `${mealTypeLabel(mealType)}保存后会直接进入今日统计`,
    description: existingSameMealRecord
      ? "当前餐次今天已经有记录，保存后会覆盖同餐次内容，并更新下方趋势与今日进度。"
      : "保存后今日进度、趋势和后续建议会一起刷新，你可以直接顺着下一步继续记。",
    highlights: [
      `今日将累计 ${projectedMealCount} / 4 餐`,
      `热量预计 ${formatMetric(projectedEnergy, "kcal")}`,
      `蛋白预计 ${formatMetric(projectedProtein, "g")}`,
    ],
  };
});

function todayString() {
  const date = new Date();
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function yesterdayString() {
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const year = yesterday.getFullYear();
  const month = `${yesterday.getMonth() + 1}`.padStart(2, "0");
  const day = `${yesterday.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function resetForm() {
  lastSavedFollowUp.value = null;
  editingRecordId.value = null;
  form.record_date = todayString();
  form.meal_type = "lunch";
  form.recipe_id = null;
  form.note = "";
}

function applyToday() {
  form.record_date = todayString();
}

function applyQuickMeal(mealType: "breakfast" | "lunch" | "dinner" | "snack") {
  lastSavedFollowUp.value = null;
  editingRecordId.value = null;
  form.record_date = todayString();
  form.meal_type = mealType;
  form.recipe_id = null;
  if (!form.note) {
    form.note = {
      breakfast: "今天的早餐",
      lunch: "今天的午餐",
      dinner: "今天的晚餐",
      snack: "今天的加餐",
    }[mealType];
  }
}

function applyPrefillFromQuery() {
  const recipeId = Number(route.query.recipe_id || 0);
  const mealType = String(route.query.meal_type || "");
  const note = String(route.query.note || "");
  if (recipeId) {
    form.recipe_id = recipeId;
  }
  if (mealType && ["breakfast", "lunch", "dinner", "snack"].includes(mealType)) {
    form.meal_type = mealType;
  }
  if (note) {
    form.note = note;
  }
  if (!form.record_date) {
    form.record_date = todayString();
  }
}

function mealTypeLabel(mealType: string) {
  return {
    breakfast: "早餐",
    lunch: "午餐",
    dinner: "晚餐",
    snack: "加餐",
  }[mealType] || mealType;
}

function numericValue(value: unknown) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function currentTimeMealType(): "breakfast" | "lunch" | "dinner" | "snack" {
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

function mealTypeOrder(mealType: string) {
  return {
    breakfast: 1,
    lunch: 2,
    dinner: 3,
    snack: 4,
  }[mealType] || 0;
}

function buildRecordSortValue(record: Record<string, any>) {
  const dateScore = Number(String(record.record_date || "").replaceAll("-", ""));
  return dateScore * 10 + mealTypeOrder(record.meal_type || "");
}

function findYesterdayMealRecord(mealType: string) {
  const targetDate = yesterdayString();
  return records.value.find((record) => record.record_date === targetDate && record.meal_type === mealType) ?? null;
}

function formatMetric(value: unknown, unit: string) {
  const number = numericValue(value);
  if (!Number.isFinite(number) || number <= 0) {
    return `0 ${unit}`;
  }
  return `${number.toFixed(unit === "kcal" ? 0 : 1)} ${unit}`;
}

function progressPercent(actual: unknown, target: unknown) {
  const actualNumber = numericValue(actual);
  const targetNumber = numericValue(target);
  if (targetNumber <= 0) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round((actualNumber / targetNumber) * 100)));
}

function remainingCopy(actual: unknown, target: unknown, unit: string, label: string) {
  const actualNumber = numericValue(actual);
  const targetNumber = numericValue(target);
  if (targetNumber <= 0) {
    return "完善档案后，系统才会给出更准确的目标值。";
  }
  const gap = targetNumber - actualNumber;
  if (gap <= 0) {
    return `${label}已达到当前目标，可关注整体均衡。`;
  }
  return `距离目标还差 ${gap.toFixed(unit === "kcal" ? 0 : 1)} ${unit}。`;
}

function todayMetricLabel(actual: unknown, target: unknown, unit: string) {
  const actualNumber = numericValue(actual);
  const targetNumber = numericValue(target);
  if (targetNumber <= 0) {
    return formatMetric(actualNumber, unit);
  }
  return `${formatMetric(actualNumber, unit)} / ${formatMetric(targetNumber, unit)}`;
}

function recordMetric(record: Record<string, any>, field: "energy" | "protein" | "fat" | "carbohydrate") {
  return (record.items ?? []).reduce((total: number, item: Record<string, any>) => total + numericValue(item[field]), 0);
}

function recordEnergy(record: Record<string, any>) {
  return recordMetric(record, "energy");
}

function recordProtein(record: Record<string, any>) {
  return recordMetric(record, "protein");
}

function syncTodaySummary() {
  const today = todayString();
  const todayRecords = records.value.filter((record) => record.record_date === today);
  todaySummary.energy = todayRecords.reduce((total, record) => total + recordMetric(record, "energy"), 0);
  todaySummary.protein = todayRecords.reduce((total, record) => total + recordMetric(record, "protein"), 0);
  todaySummary.fat = todayRecords.reduce((total, record) => total + recordMetric(record, "fat"), 0);
  todaySummary.carbohydrate = todayRecords.reduce((total, record) => total + recordMetric(record, "carbohydrate"), 0);
}

function applyRecipeShortcut(item: { recipe_id: number; title: string; meal_type?: string }) {
  lastSavedFollowUp.value = null;
  form.recipe_id = item.recipe_id;
  form.note = item.title;
  form.meal_type = item.meal_type || form.meal_type;
  if (!form.record_date) {
    form.record_date = todayString();
  }
}

function recordPrimaryTitle(record: Record<string, any>) {
  return record.items?.[0]?.recipe_title || record.note || "未命名记录";
}

function recordSecondaryLabel(record: Record<string, any>) {
  const datePart = record.record_date || "最近记录";
  const energy = recordEnergy(record);
  if (energy > 0) {
    return `${datePart} · 热量 ${formatMetric(energy, "kcal")}`;
  }
  return `${datePart} · ${record.items?.length || 0} 个条目`;
}

function applyRecordTemplate(record: Record<string, any>) {
  reuseRecord(record);
}

function copyYesterdayMeal() {
  if (!yesterdaySameMealRecord.value) {
    notifyWarning("昨天没有找到同餐次记录");
    return;
  }
  reuseRecord(yesterdaySameMealRecord.value);
}

const copyingYesterday = ref(false);
async function copyAllYesterday() {
  if (copyingYesterday.value) return;
  copyingYesterday.value = true;
  try {
    const res = await copyYesterdayMealRecords();
    if (res?.code === 0) {
      notifyActionSuccess(`${res.message || "已复制昨日饮食"}`);
      await loadRecords();
    } else {
      notifyWarning(res?.message || "昨日没有记录可复制");
    }
  } catch {
    notifyActionError("复制昨日饮食");
  } finally {
    copyingYesterday.value = false;
  }
}

function nextMealType(mealType: string): "breakfast" | "lunch" | "dinner" | "snack" {
  return (
    {
      breakfast: "lunch",
      lunch: "dinner",
      dinner: "snack",
      snack: "dinner",
    }[mealType] || "lunch"
  ) as "breakfast" | "lunch" | "dinner" | "snack";
}

function followUpLibraryLabel() {
  return recentRecipeShortcuts.value.length || frequentRecipeShortcuts.value.length ? "从常用菜谱里选" : "去菜谱库找一餐";
}

function followUpLibraryTarget() {
  return recentRecipeShortcuts.value.length || frequentRecipeShortcuts.value.length ? "/favorites" : "/recipes";
}

function buildFollowUpHighlights(recordDate: string, mealType: string) {
  const isToday = recordDate === todayString();
  const completedMeals = mealChecklist.value.filter((item) => item.done).length;
  const proteinGap = proteinTarget.value > 0 ? Math.max(0, proteinTarget.value - todaySummary.protein) : 0;
  const energyGap = energyTarget.value > 0 ? energyTarget.value - todaySummary.energy : 0;
  const nextMissingMeal = mealChecklist.value.find((item) => !item.done)?.label || mealTypeLabel(nextMealType(mealType));

  if (!isToday) {
    return [`归档到 ${recordDate}`, "已同步到历史记录", `下一步可补${mealTypeLabel(nextMealType(mealType))}`];
  }

  return [
    `今日已记录 ${completedMeals} / 4 餐`,
    energyTarget.value > 0 ? (energyGap > 0 ? `热量还差 ${formatMetric(energyGap, "kcal")}` : "热量已达到目标") : `热量 ${formatMetric(todaySummary.energy, "kcal")}`,
    proteinTarget.value > 0 ? (proteinGap > 0 ? `蛋白还差 ${formatMetric(proteinGap, "g")}` : "蛋白已达到目标") : `下一步建议补${nextMissingMeal}`,
  ];
}

function buildFollowUp(recordDate: string, mealType: string, mode: "create" | "update") {
  const badge = mode === "update" ? "已更新" : "已保存";
  const isToday = recordDate === todayString();
  const nextMeal = nextMealType(mealType);
  const sourceReturnAction =
    prefillSource.value === "home"
      ? { label: "回首页看今天工作台", to: "/" }
      : prefillSource.value === "recipes"
        ? { label: "回菜谱页继续挑", to: "/recipes" }
        : prefillSource.value === "favorites"
          ? { label: "回收藏中心", to: "/favorites" }
          : null;

  if (!isToday) {
    return {
      badge,
      title: `${mealTypeLabel(mealType)}已同步到 ${recordDate}`,
      description: "这条记录已经归档到对应日期。现在可以补今天的一餐，或者回看最近记录确认整体节奏。",
      highlights: buildFollowUpHighlights(recordDate, mealType).concat(sourceReturnAction ? [`来源 ${recordHandoff.value?.badge || "跨页带入"}`] : []),
      actions: [
        { label: `快速记${mealTypeLabel(nextMeal)}`, primary: true, mealType: nextMeal },
        { label: "查看最近记录", to: "/records" },
        ...(sourceReturnAction ? [sourceReturnAction] : []),
      ],
    };
  }

  const proteinGap = Math.max(0, proteinTarget.value - todaySummary.protein);
  const energyGap = Math.max(0, energyTarget.value - todaySummary.energy);

  if (proteinTarget.value > 0 && proteinGap >= 18) {
    return {
      badge,
      title: `今天蛋白还差 ${proteinGap.toFixed(1)} g`,
      description: `当前${mealTypeLabel(mealType)}已经记上了。下一步更适合补一份高蛋白选择，而不是继续盲目加量。`,
      highlights: buildFollowUpHighlights(recordDate, mealType).concat(sourceReturnAction ? [`来源 ${recordHandoff.value?.badge || "跨页带入"}`] : []),
      actions: [
        { label: followUpLibraryLabel(), primary: true, to: followUpLibraryTarget() },
        { label: `继续记${mealTypeLabel(nextMeal)}`, mealType: nextMeal },
        ...(sourceReturnAction ? [sourceReturnAction] : []),
      ],
    };
  }

  if (energyTarget.value > 0 && todaySummary.energy > energyTarget.value * 1.15) {
    return {
      badge,
      title: "今天热量已经明显偏高",
      description: "后续一餐更适合轻负担、低油低糖一点，先避免继续上冲，再回看整体趋势。",
      highlights: buildFollowUpHighlights(recordDate, mealType).concat(sourceReturnAction ? [`来源 ${recordHandoff.value?.badge || "跨页带入"}`] : []),
      actions: [
        { label: "去菜谱库看轻负担", primary: true, to: "/recipes" },
        { label: "查看今天记录", to: "/records" },
        ...(sourceReturnAction ? [sourceReturnAction] : []),
      ],
    };
  }

  if (energyTarget.value > 0 && energyGap > 0) {
    return {
      badge,
      title: `距离今日热量目标还差 ${energyGap.toFixed(0)} kcal`,
      description: "今天的记录已经在推进，继续补下一餐，热量和蛋白会更接近目标。",
      highlights: buildFollowUpHighlights(recordDate, mealType).concat(sourceReturnAction ? [`来源 ${recordHandoff.value?.badge || "跨页带入"}`] : []),
      actions: [
        { label: `继续记${mealTypeLabel(nextMeal)}`, primary: true, mealType: nextMeal },
        { label: followUpLibraryLabel(), to: followUpLibraryTarget() },
        ...(sourceReturnAction ? [sourceReturnAction] : []),
      ],
    };
  }

  return {
    badge,
    title: "这一餐已经记上，今天节奏基本正常",
    description: "可以继续补下一餐，或者回看趋势和报表，确认这几天是不是都在稳定推进。",
    highlights: buildFollowUpHighlights(recordDate, mealType).concat(sourceReturnAction ? [`来源 ${recordHandoff.value?.badge || "跨页带入"}`] : []),
    actions: [
      { label: "看看报表", primary: true, to: "/reports" },
      { label: `继续记${mealTypeLabel(nextMeal)}`, mealType: nextMeal },
      ...(sourceReturnAction ? [sourceReturnAction] : []),
    ],
  };
}

function triggerRecordCompletionPulse() {
  recordCompletionPulse.value = false;
  if (recordCompletionTimer) {
    window.clearTimeout(recordCompletionTimer);
  }
  requestAnimationFrame(() => {
    recordCompletionPulse.value = true;
    recordCompletionTimer = window.setTimeout(() => {
      recordCompletionPulse.value = false;
      recordCompletionTimer = null;
    }, 1100);
  });
}

function runFollowUpAction(action: { to?: string; mealType?: "breakfast" | "lunch" | "dinner" | "snack" }) {
  if (action.mealType) {
    applyQuickMeal(action.mealType);
    return;
  }
  if (action.to) {
    router.push(action.to);
  }
}

function clearRecordHandoff() {
  const nextQuery = { ...route.query };
  delete nextQuery.source;
  delete nextQuery.from_title;
  router.replace({ path: route.path, query: nextQuery });
}

function openAssistantForRecordPlan() {
  const prompt = [
    "请基于我当前记录页状态，用非常直接、可执行的话告诉我下一步该做什么。",
    `今天已记录餐次：${mealChecklist.value.filter((item) => item.done).length} / 4。`,
    `当前建议优先补：${mealTypeLabel(recommendedMealType.value)}。`,
    `今日热量：${formatMetric(todaySummary.energy, "kcal")}，目标：${formatMetric(energyTarget.value, "kcal")}。`,
    `今日蛋白：${formatMetric(todaySummary.protein, "g")}，目标：${formatMetric(proteinTarget.value, "g")}。`,
    latestReusableRecord.value ? `最近可复用的一餐：${recordPrimaryTitle(latestReusableRecord.value)}。` : "当前还没有可直接复用的历史记录。",
    recommendedMealYesterdayRecord.value ? `昨天同餐可复用：${recordPrimaryTitle(recommendedMealYesterdayRecord.value)}。` : "昨天没有同餐可复用记录。",
    "请输出三部分：1）我现在最该点哪个动作；2）为什么；3）如果想最快完成这一条记录，应该怎么做。",
  ].join("\n");

  router.push({
    path: "/assistant",
    query: {
      source: "records_next_step",
      prompt,
    },
  });
}

function openAssistantForMealDraft() {
  if (!mealDraftReadyForAi.value) {
    return;
  }

  const prompt = [
    "请帮我判断这条饮食记录应该怎么记得更完整，并告诉我最省事的下一步。",
    `记录日期：${form.record_date || todayString()}。`,
    `餐次：${mealTypeLabel(form.meal_type)}。`,
    selectedRecipe.value ? `已选菜谱：${selectedRecipe.value.title}。` : "当前还没有关联菜谱。",
    `备注：${form.note.trim() || "未填写备注"}。`,
    `今日热量：${formatMetric(todaySummary.energy, "kcal")}，目标：${formatMetric(energyTarget.value, "kcal")}。`,
    `今日蛋白：${formatMetric(todaySummary.protein, "g")}，目标：${formatMetric(proteinTarget.value, "g")}。`,
    "请输出三部分：1）这条记录现在可以怎么保存；2）如果想把它补成更正式的记录，最缺什么信息；3）我下一步应该留在记录页保存，还是去菜谱页补上传。",
  ].join("\n");

  router.push({
    path: "/assistant",
    query: {
      source: "records_meal_draft",
      prompt,
    },
  });
}

async function loadRecords() {
  try {
    loadingRecords.value = true;
    const [recordsResult, statsResult, nutritionResult] = await Promise.allSettled([
      listMealRecords(),
      mealStatistics(period.value),
      nutritionAnalysis(),
    ]);

    const recordsResponse = recordsResult.status === "fulfilled" ? recordsResult.value : null;
    const statsResponse = statsResult.status === "fulfilled" ? statsResult.value : null;
    const nutritionResponse = nutritionResult.status === "fulfilled" ? nutritionResult.value : null;

    if (!recordsResponse && !statsResponse && !nutritionResponse) {
      throw new Error("records load failed");
    }

    records.value = recordsResponse?.data?.items ?? recordsResponse?.data ?? [];
    stats.summary = statsResponse?.data?.summary ?? null;
    stats.trend = statsResponse?.data?.trend ?? [];
    targets.calorie = numericValue(nutritionResponse?.data?.calorie_target);
    targets.protein = numericValue(nutritionResponse?.data?.protein_target);
    syncTodaySummary();
    trackEvent({ behavior_type: "view", context_scene: "records" }).catch(() => undefined);
  } catch (error) {
    notifyLoadError("饮食记录");
  } finally {
    loadingRecords.value = false;
  }
}

async function loadRecipes() {
  try {
    const response = await listRecipes();
    recipeOptions.value = response.data?.items ?? response.data ?? [];
  } catch (error) {
    recipeOptions.value = [];
  }
}

async function createRecord() {
  try {
    if (!form.record_date) {
      notifyWarning("请选择日期");
      return;
    }
    if (!form.recipe_id && !form.note.trim()) {
      notifyWarning("请至少选择一个菜谱或填写备注");
      return;
    }

    saving.value = true;
    const recordDate = form.record_date;
    const mealType = form.meal_type;
    await createMealRecord({
      record_date: form.record_date,
      meal_type: form.meal_type,
      source_type: "manual",
      note: form.note.trim(),
      items: [
        form.recipe_id
          ? { recipe_id: form.recipe_id, amount: 1, unit: "serving" }
          : { ingredient_name_snapshot: form.note.trim() || "manual entry", amount: 1, unit: "serving" },
      ],
    });
    notifyActionSuccess("记录已保存");
    resetForm();
    await loadRecords();
    lastSavedFollowUp.value = buildFollowUp(recordDate, mealType, "create");
    triggerRecordCompletionPulse();
  } catch (error) {
    notifyActionError("保存记录");
  } finally {
    saving.value = false;
  }
}

async function saveRecord() {
  if (editingRecordId.value) {
    await updateRecord();
    return;
  }
  await createRecord();
}

async function updateRecord() {
  try {
    if (!editingRecordId.value) {
      return;
    }
    if (!form.record_date) {
      notifyWarning("请选择日期");
      return;
    }
    if (!form.recipe_id && !form.note.trim()) {
      notifyWarning("请至少选择一个菜谱或填写备注");
      return;
    }

    saving.value = true;
    const recordDate = form.record_date;
    const mealType = form.meal_type;
    await updateMealRecord(editingRecordId.value, {
      record_date: form.record_date,
      meal_type: form.meal_type,
      source_type: "manual",
      note: form.note.trim(),
      items: [
        form.recipe_id
          ? { recipe_id: form.recipe_id, amount: 1, unit: "serving" }
          : { ingredient_name_snapshot: form.note.trim() || "manual entry", amount: 1, unit: "serving" },
      ],
    });
    notifyActionSuccess("记录已更新");
    resetForm();
    await loadRecords();
    lastSavedFollowUp.value = buildFollowUp(recordDate, mealType, "update");
    triggerRecordCompletionPulse();
  } catch (error) {
    notifyActionError("更新记录");
  } finally {
    saving.value = false;
  }
}

function editRecord(record: Record<string, any>) {
  lastSavedFollowUp.value = null;
  editingRecordId.value = Number(record.id);
  form.record_date = record.record_date || todayString();
  form.meal_type = record.meal_type || "lunch";
  form.note = record.note || "";
  const recipeId = Number(record.items?.[0]?.recipe_id || 0);
  form.recipe_id = recipeId || null;
}

function reuseRecord(record: Record<string, any>) {
  lastSavedFollowUp.value = null;
  editingRecordId.value = null;
  form.record_date = todayString();
  form.meal_type = record.meal_type || "lunch";
  form.note = record.note || "";
  const recipeId = Number(record.items?.[0]?.recipe_id || 0);
  form.recipe_id = recipeId || null;
  notifyActionSuccess("已带入上一餐内容，请确认后保存");
}

async function removeRecord(recordId: number) {
  try {
    await ElMessageBox.confirm("删除后该餐次记录会从统计中移除，确认继续吗？", "删除记录", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }

  try {
    deletingId.value = recordId;
    await deleteMealRecord(recordId);
    notifyActionSuccess("记录已删除");
    await loadRecords();
  } catch (error) {
    notifyActionError("删除记录");
  } finally {
    deletingId.value = null;
  }
}

onMounted(() => {
  resetForm();
  applyPrefillFromQuery();
  loadRecords();
  loadRecipes();
});

onBeforeUnmount(() => {
  if (recordCompletionTimer) {
    window.clearTimeout(recordCompletionTimer);
    recordCompletionTimer = null;
  }
});

watch(
  () => route.fullPath,
  () => {
    applyPrefillFromQuery();
  },
);
</script>

<style scoped>
/* ── Page shell ─────────────────────────────────────────── */
.records-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: linear-gradient(160deg, #f0f7fb 0%, #f8fbfc 100%);
}

/* ── Topbar ─────────────────────────────────────────────── */
.page-topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 14px 24px;
  background: rgba(255, 255, 255, 0.92);
  border-bottom: 1px solid rgba(16, 34, 42, 0.07);
  backdrop-filter: blur(12px);
}

.topbar-left h2 {
  margin: 0;
  font-size: 20px;
  color: #173042;
}

.topbar-hint {
  margin: 2px 0 0;
  font-size: 12px;
  color: #5a7a8a;
}

.topbar-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* ── Two-column layout ───────────────────────────────────── */
.records-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 0;
  align-items: start;
  flex: 1;
}

/* ── Sidebar ─────────────────────────────────────────────── */
.records-sidebar {
  position: sticky;
  top: 57px;
  max-height: calc(100vh - 57px);
  overflow-y: auto;
  padding: 16px 12px 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-right: 1px solid rgba(16, 34, 42, 0.07);
  background: rgba(255, 255, 255, 0.6);
}

.sidebar-card {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 34, 42, 0.07);
  box-shadow: 0 4px 14px rgba(15, 30, 39, 0.05);
}

.sidebar-label {
  display: block;
  margin-bottom: 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #3e6d7f;
}

/* ── Today progress ──────────────────────────────────────── */
.progress-rows {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-item {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.progress-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.progress-top span {
  font-size: 12px;
  color: #5a7a8a;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.progress-top strong {
  font-size: 13px;
  color: #173042;
}

.progress-item p {
  margin: 6px 0 0;
  font-size: 12px;
  color: #476072;
  line-height: 1.5;
}

/* ── Meal checklist ──────────────────────────────────────── */
.meal-checklist {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
  margin-top: 12px;
}

.meal-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px;
  border-radius: 12px;
  background: rgba(247, 251, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.06);
  text-align: center;
  transition: background 0.28s ease, border-color 0.28s ease;
}

.meal-chip span {
  font-size: 11px;
  color: #5a7a8a;
  letter-spacing: 0.08em;
}

.meal-chip strong {
  font-size: 12px;
  color: #173042;
  margin-top: 2px;
}

.meal-chip.done {
  background: rgba(224, 247, 238, 0.9);
  border-color: rgba(31, 120, 89, 0.16);
}

.meal-chip.done strong {
  color: #1f6a4c;
}

/* ── Quick actions sidebar ───────────────────────────────── */
.workbench-status-line {
  margin: 0 0 4px;
  font-size: 11px;
  color: #5a7a8a;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.workbench-headline {
  display: block;
  font-size: 14px;
  color: #173042;
  margin-bottom: 10px;
}

.quick-action-btns {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* ── Stat rows ───────────────────────────────────────────── */
.stat-rows {
  display: grid;
  gap: 4px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  font-size: 13px;
  border-bottom: 1px solid rgba(16, 34, 42, 0.05);
  color: #476072;
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-row strong {
  font-size: 15px;
  color: #173042;
}

/* ── Period stat cards in sidebar ───────────────────────── */
.period-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.period-item {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(247, 251, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.05);
}

.period-item span {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #5a7a8a;
}

.period-item strong {
  display: block;
  font-size: 18px;
  color: #173042;
  margin: 4px 0;
}

.period-item p {
  margin: 0;
  font-size: 11px;
  color: #476072;
  line-height: 1.5;
}

.period-item.tone-energy {
  background: rgba(255, 245, 231, 0.9);
}

.period-item.tone-success {
  background: rgba(228, 247, 238, 0.9);
}

/* ── Main content ────────────────────────────────────────── */
.records-main {
  padding: 20px 24px 40px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.content-card {
  padding: 22px 24px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 10px 30px rgba(15, 30, 39, 0.07);
}

.card-header {
  margin-bottom: 16px;
}

.card-header h3 {
  margin: 0;
  font-size: 17px;
  color: #173042;
}

.card-header p {
  margin: 4px 0 0;
  font-size: 13px;
  color: #476072;
  line-height: 1.6;
}

/* ── Form rhythm banner ──────────────────────────────────── */
.form-rhythm-banner {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
  padding: 18px;
  border-radius: 16px;
  background:
    radial-gradient(circle at top right, rgba(87, 181, 231, 0.16), transparent 34%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(247, 251, 255, 0.96));
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 10px 28px rgba(15, 30, 39, 0.07);
  animation: pop-in-bounce 0.56s cubic-bezier(0.22, 1.2, 0.36, 1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.form-rhythm-banner.is-ready {
  background:
    radial-gradient(circle at top right, rgba(210, 245, 229, 0.34), transparent 34%),
    linear-gradient(135deg, rgba(248, 255, 252, 0.94), rgba(244, 251, 248, 0.96));
  border-color: rgba(31, 120, 89, 0.12);
}

.form-rhythm-banner.is-editing {
  background:
    radial-gradient(circle at top right, rgba(255, 236, 210, 0.42), transparent 34%),
    linear-gradient(135deg, rgba(255, 252, 247, 0.94), rgba(251, 247, 241, 0.96));
  border-color: rgba(185, 115, 38, 0.14);
}

.form-rhythm-copy {
  display: grid;
  gap: 8px;
}

.form-rhythm-copy span {
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #607d8b;
}

.form-rhythm-copy strong {
  font-size: 20px;
  line-height: 1.35;
  color: #173042;
}

.form-rhythm-copy p {
  margin: 0;
  color: #476072;
  line-height: 1.65;
}

.form-rhythm-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}

.form-rhythm-meta span {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(16, 34, 42, 0.08);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #607d8b;
}

/* ── Helper panel ────────────────────────────────────────── */
.helper-panel {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.helper-panel strong {
  font-size: 15px;
  color: #173042;
}

.helper-panel p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #476072;
  line-height: 1.5;
}

.helper-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-end;
}

/* ── Quick helpers ───────────────────────────────────────── */
.quick-helpers {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
}

/* ── Record handoff ──────────────────────────────────────── */
.record-handoff {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 14px;
  padding: 14px 16px;
  border-radius: 14px;
  background:
    radial-gradient(circle at top right, rgba(87, 181, 231, 0.14), transparent 34%),
    rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.08);
}

.record-handoff-copy {
  display: grid;
  gap: 6px;
}

.record-handoff-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(23, 48, 66, 0.08);
  color: #173042;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.record-handoff strong {
  font-size: 15px;
  color: #173042;
}

.record-handoff p {
  margin: 0;
  font-size: 13px;
  color: #476072;
  line-height: 1.5;
}

.record-handoff-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

/* ── Shortcut panel ──────────────────────────────────────── */
.shortcut-panel {
  margin-bottom: 14px;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.shortcut-block + .shortcut-block {
  margin-top: 12px;
}

.shortcut-label {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #5a7a8a;
}

.shortcut-list {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: none;
}

.shortcut-list::-webkit-scrollbar {
  display: none;
}

.shortcut-card {
  min-width: 160px;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(255, 255, 255, 0.82);
  text-align: left;
  cursor: pointer;
  box-shadow: 0 6px 16px rgba(15, 30, 39, 0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.interactive-shortcut-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(15, 30, 39, 0.1);
}

.shortcut-card strong {
  display: block;
  font-size: 14px;
  color: #173042;
}

.shortcut-card small {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  color: #5a7a8a;
  line-height: 1.5;
}

/* ── Recipe preview ──────────────────────────────────────── */
.recipe-preview {
  margin-bottom: 14px;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(247, 251, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.preview-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.preview-head strong {
  font-size: 15px;
  color: #173042;
}

.preview-head p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #476072;
  line-height: 1.5;
}

.preview-head > span {
  padding: 5px 10px;
  border-radius: 999px;
  background: #173042;
  color: #fff;
  font-size: 12px;
  white-space: nowrap;
}

.preview-metrics {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.preview-metrics span {
  padding: 4px 8px;
  border-radius: 999px;
  background: #e8f1f7;
  color: #24566a;
  font-size: 11px;
}

/* ── Save preview & follow-up ────────────────────────────── */
.save-preview,
.save-follow-up {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 14px;
  animation: pop-in-bounce 0.52s cubic-bezier(0.22, 1.2, 0.36, 1);
  transition: transform 0.3s ease;
}

.save-preview {
  background: rgba(255, 245, 231, 0.72);
  border: 1px solid rgba(185, 115, 38, 0.16);
}

.save-follow-up {
  background: rgba(224, 247, 238, 0.72);
  border: 1px solid rgba(31, 120, 89, 0.16);
}

.save-preview-copy,
.save-follow-up-copy {
  display: grid;
  gap: 6px;
}

.save-preview-badge,
.save-follow-up-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.save-preview-badge {
  background: rgba(185, 115, 38, 0.12);
  color: #9a5f17;
}

.save-follow-up-badge {
  background: rgba(31, 120, 89, 0.12);
  color: #1f6a4c;
}

.save-preview strong,
.save-follow-up strong {
  font-size: 16px;
  color: #173042;
}

.save-preview p,
.save-follow-up p {
  margin: 0;
  font-size: 13px;
  color: #476072;
  line-height: 1.5;
}

.save-preview-highlights,
.save-follow-up-highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.save-preview-highlights span,
.save-follow-up-highlights span {
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.save-preview-highlights span {
  background: rgba(255, 255, 255, 0.78);
  color: #8d5818;
  border: 1px solid rgba(185, 115, 38, 0.12);
}

.save-follow-up-highlights span {
  background: rgba(255, 255, 255, 0.78);
  color: #1f6a4c;
  border: 1px solid rgba(31, 120, 89, 0.12);
}

.save-follow-up-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

/* ── is-save-pulse ───────────────────────────────────────── */
.progress-item.is-save-pulse,
.meal-chip.is-save-pulse,
.save-preview.is-save-pulse,
.save-follow-up.is-save-pulse {
  animation: record-complete-pop 0.96s cubic-bezier(0.22, 1.2, 0.36, 1);
}

/* ── Template card ───────────────────────────────────────── */
.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}

.template-card-item {
  padding: 14px;
  border-radius: 14px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(255, 255, 255, 0.82);
  text-align: left;
  cursor: pointer;
  box-shadow: 0 6px 16px rgba(15, 30, 39, 0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.template-card-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(15, 30, 39, 0.1);
}

.template-card-item span {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #5a7a8a;
}

.template-card-item strong {
  display: block;
  margin-top: 6px;
  font-size: 14px;
  color: #173042;
}

.template-card-item p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #476072;
  line-height: 1.5;
}

/* ── Record list ─────────────────────────────────────────── */
.day-group {
  display: grid;
  gap: 8px;
}

.day-group + .day-group {
  margin-top: 14px;
}

.day-head {
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(16, 34, 42, 0.08);
}

.day-head strong {
  font-size: 15px;
  color: #173042;
}

.day-head p {
  margin: 2px 0 0;
  font-size: 12px;
  color: #476072;
  line-height: 1.5;
}

.history-record-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(247, 251, 255, 0.78);
  border: 1px solid rgba(16, 34, 42, 0.06);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.history-record-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(15, 30, 39, 0.08);
}

.record-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.record-head strong {
  font-size: 14px;
  color: #173042;
}

.record-head p {
  margin: 2px 0 0;
  font-size: 12px;
  color: #476072;
}

.record-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.muted {
  font-size: 12px;
  color: #6f8592;
}

/* ── First run guide ─────────────────────────────────────── */
.first-run-guide {
  display: grid;
  gap: 8px;
  margin-top: 14px;
}

.first-run-guide article {
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px dashed rgba(16, 34, 42, 0.12);
}

.first-run-guide strong {
  font-size: 14px;
  color: #173042;
}

.first-run-guide p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #476072;
  line-height: 1.5;
}

/* ── Trend ───────────────────────────────────────────────── */
.trend {
  display: grid;
  gap: 8px;
  margin-top: 14px;
}

.trend article {
  padding: 12px;
  border-radius: 12px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.trend strong {
  font-size: 14px;
  color: #173042;
}

.trend p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #476072;
}

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 900px) {
  .records-layout {
    grid-template-columns: 1fr;
  }

  .records-sidebar {
    position: static;
    max-height: none;
    flex-direction: row;
    flex-wrap: wrap;
    border-right: none;
    border-bottom: 1px solid rgba(16, 34, 42, 0.07);
    padding: 14px 16px;
  }

  .sidebar-card {
    min-width: 200px;
    flex: 1;
  }

  .meal-checklist {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 640px) {
  .page-topbar,
  .helper-panel,
  .record-handoff,
  .save-preview,
  .save-follow-up,
  .form-rhythm-banner {
    flex-direction: column;
  }

  .meal-checklist {
    grid-template-columns: repeat(2, 1fr);
  }

  .template-grid {
    grid-template-columns: 1fr;
  }

  .save-follow-up-actions {
    width: 100%;
    justify-content: stretch;
  }

  .record-handoff-actions :deep(.el-button),
  .save-follow-up-actions :deep(.el-button) {
    width: 100%;
    margin-left: 0;
  }
}

@keyframes record-complete-pop {
  0% {
    transform: translateY(0) scale(1);
    box-shadow: 0 0 0 rgba(31, 120, 89, 0);
  }
  35% {
    transform: translateY(-4px) scale(1.018);
    box-shadow: 0 20px 40px rgba(31, 120, 89, 0.16);
  }
  100% {
    transform: translateY(0) scale(1);
    box-shadow: 0 0 0 rgba(31, 120, 89, 0);
  }
}
</style>
