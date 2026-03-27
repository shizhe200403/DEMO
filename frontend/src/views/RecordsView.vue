<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Tracking</p>
        <h2>饮食记录</h2>
        <p class="desc">先保证记录顺手，再谈复杂录入方式。当前页面只保留真正可用的录入链路。</p>
      </div>
      <el-select v-model="period" style="width: 140px" @change="loadRecords">
        <el-option label="最近7天" value="week" />
        <el-option label="最近30天" value="month" />
      </el-select>
    </div>

    <CollectionSkeleton v-if="loadingRecords && !records.length" variant="list" :card-count="5" />
    <RefreshFrame v-else :active="loadingRecords && !!records.length" label="正在更新记录与统计">
    <div class="overview-grid">
      <article class="card planner-card">
        <div class="card-head">
          <div>
            <h3>今日进度</h3>
            <p>让用户先知道今天还差多少，再决定要不要继续记录、补蛋白还是控制热量。</p>
          </div>
          <div class="planner-actions">
            <el-button text @click="router.push('/favorites')">从收藏选餐</el-button>
            <el-button text @click="router.push('/recipes')">去菜谱库</el-button>
          </div>
        </div>

        <div class="progress-grid">
          <div class="progress-card">
            <div class="progress-top">
              <strong>热量</strong>
              <span>{{ todayMetricLabel(todaySummary.energy, energyTarget, "kcal") }}</span>
            </div>
            <el-progress :percentage="progressPercent(todaySummary.energy, energyTarget)" :stroke-width="10" :show-text="false" />
            <p>{{ remainingCopy(todaySummary.energy, energyTarget, "kcal", "热量") }}</p>
          </div>
          <div class="progress-card">
            <div class="progress-top">
              <strong>蛋白质</strong>
              <span>{{ todayMetricLabel(todaySummary.protein, proteinTarget, "g") }}</span>
            </div>
            <el-progress :percentage="progressPercent(todaySummary.protein, proteinTarget)" :stroke-width="10" :show-text="false" />
            <p>{{ remainingCopy(todaySummary.protein, proteinTarget, "g", "蛋白质") }}</p>
          </div>
        </div>

        <div class="meal-checklist">
          <div v-for="item in mealChecklist" :key="item.value" class="meal-chip" :class="{ done: item.done }">
            <span>{{ item.label }}</span>
            <strong>{{ item.done ? "已记录" : "待补充" }}</strong>
          </div>
        </div>
      </article>

      <article class="card planner-card">
        <div class="card-head">
          <div>
            <h3>当前周期概览</h3>
            <p>记录页不只用来保存数据，也应该告诉用户这段时间到底记了多少、主要集中在哪些天。</p>
          </div>
        </div>

        <div class="summary-grid">
          <div>
            <span>展示范围</span>
            <strong>{{ period === "week" ? "最近7天" : "最近30天" }}</strong>
          </div>
          <div>
            <span>记录餐次</span>
            <strong>{{ filteredRecords.length }}</strong>
          </div>
          <div>
            <span>活跃天数</span>
            <strong>{{ groupedRecords.length }}</strong>
          </div>
          <div>
            <span>已关联菜谱</span>
            <strong>{{ linkedRecipeCount }}</strong>
          </div>
        </div>

        <p class="helper-copy">
          {{ filteredRecords.length ? "已经有连续记录了，继续补齐空缺餐次，趋势会更稳定。" : "当前周期还没有记录，先保存一餐再看趋势。" }}
        </p>
      </article>
    </div>

    <div class="card">
      <div class="card-head">
        <div>
          <h3>新增一餐</h3>
          <p>选择菜谱后会自动带出营养统计；如果只填备注，记录会保存，但不会产生热量和营养汇总。</p>
        </div>
      </div>

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
            <el-form-item label="是否关联菜谱">
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
        </div>

        <div v-if="selectedRecipe" class="recipe-preview">
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
      </el-form>
    </div>

    <div class="stats">
      <article v-for="item in periodSummaryCards" :key="item.key" :class="`is-${item.tone}`">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p>{{ item.copy }}</p>
      </article>
    </div>

    <div class="list">
      <div class="list-head">
        <h3>最近记录</h3>
        <p>同一天同一餐次再次保存时，会覆盖旧内容；列表已按日期分组，方便快速复盘。</p>
      </div>

      <div v-for="group in groupedRecords" :key="group.date" class="day-group">
        <div class="day-head">
          <div>
            <strong>{{ group.date }}</strong>
            <p>共 {{ group.records.length }} 餐 · 热量 {{ formatMetric(group.energy, "kcal") }} · 蛋白 {{ formatMetric(group.protein, "g") }}</p>
          </div>
        </div>

        <article v-for="record in group.records" :key="record.id">
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

    <div class="card">
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
        description="先补几餐记录，趋势页才会逐步显示这段时间的热量和蛋白变化。"
        compact
      />
    </div>
    </RefreshFrame>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import FormActionBar from "../components/FormActionBar.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import TrendMiniBars from "../components/TrendMiniBars.vue";
import { ElMessageBox, notifyActionError, notifyActionSuccess, notifyLoadError, notifyWarning } from "../lib/feedback";
import { createMealRecord, deleteMealRecord, listMealRecords, mealStatistics, updateMealRecord } from "../api/tracking";
import { listRecipes } from "../api/recipes";
import { trackEvent } from "../api/behavior";
import { useRoute, useRouter } from "vue-router";
import { nutritionAnalysis } from "../api/nutrition";

const route = useRoute();
const router = useRouter();
const period = ref("week");
const saving = ref(false);
const deletingId = ref<number | null>(null);
const editingRecordId = ref<number | null>(null);
const loadingRecords = ref(false);
const records = ref<any[]>([]);
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
    return "先补几餐记录，趋势页才会逐步显示这段时间的热量变化。";
  }
  const values = trendBars.value.map((item) => item.value);
  const average = values.reduce((total, value) => total + value, 0) / values.length;
  return `最近可见日均约 ${average.toFixed(0)} kcal，适合先看整体节奏，再判断某一天是否异常偏高。`;
});
const mealChecklist = computed(() => {
  const today = todayString();
  const set = new Set(records.value.filter((record) => record.record_date === today).map((record) => record.meal_type));
  return [
    { label: "早餐", value: "breakfast", done: set.has("breakfast") },
    { label: "午餐", value: "lunch", done: set.has("lunch") },
    { label: "晚餐", value: "dinner", done: set.has("dinner") },
    { label: "加餐", value: "snack", done: set.has("snack") },
  ];
});

function todayString() {
  const date = new Date();
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function resetForm() {
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
  } catch (error) {
    notifyActionError("更新记录");
  } finally {
    saving.value = false;
  }
}

function editRecord(record: Record<string, any>) {
  editingRecordId.value = Number(record.id);
  form.record_date = record.record_date || todayString();
  form.meal_type = record.meal_type || "lunch";
  form.note = record.note || "";
  const recipeId = Number(record.items?.[0]?.recipe_id || 0);
  form.recipe_id = recipeId || null;
}

function reuseRecord(record: Record<string, any>) {
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

watch(
  () => route.fullPath,
  () => {
    applyPrefillFromQuery();
  },
);
</script>

<style scoped>
.page {
  display: grid;
  gap: 18px;
}

.head,
.card-head,
.list-head,
.record-head,
.day-head,
.actions,
.record-actions,
.planner-actions,
.preview-head,
.progress-top,
.quick-helpers {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
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
.list-head p,
.list p,
.muted,
.empty-state p,
.helper-copy,
.recipe-preview p,
.day-head p,
.progress-card p {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.65;
}

.card,
.day-group,
.list article,
.empty-state {
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.overview-grid,
.progress-grid,
.summary-grid {
  display: grid;
  gap: 12px;
}

.overview-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.progress-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 16px;
}

.summary-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 16px;
}

.summary-grid div,
.progress-card,
.meal-chip,
.recipe-preview {
  padding: 16px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.summary-grid span,
.meal-chip span,
.progress-top span,
.preview-metrics span {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #5a7a8a;
}

.summary-grid strong,
.meal-chip strong,
.progress-top strong {
  display: block;
  margin-top: 8px;
  font-size: 22px;
}

.meal-checklist {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.meal-chip.done {
  background: rgba(224, 247, 238, 0.95);
  border-color: rgba(31, 120, 89, 0.16);
}

.planner-card {
  min-height: 100%;
}

.helper-copy {
  margin-top: 16px;
}

.recipe-preview {
  margin-bottom: 16px;
}

.preview-head strong {
  font-size: 18px;
}

.preview-head span {
  padding: 6px 12px;
  border-radius: 999px;
  background: #173042;
  color: #fff;
  font-size: 13px;
}

.preview-metrics {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.quick-helpers {
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
}

.stats article {
  padding: 18px;
  border-radius: 20px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.stats span {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #5a7a8a;
}

.stats strong {
  display: block;
  margin-top: 8px;
  font-size: 24px;
}

.stats p {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.6;
}

.stats article.is-energy {
  background: rgba(255, 245, 231, 0.92);
}

.stats article.is-success {
  background: rgba(228, 247, 238, 0.92);
}

.list {
  display: grid;
  gap: 12px;
}

.day-group {
  display: grid;
  gap: 12px;
}

.first-run-guide {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}

.first-run-guide article {
  padding: 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px dashed rgba(16, 34, 42, 0.12);
}

.first-run-guide strong {
  font-size: 16px;
}

.day-head {
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(16, 34, 42, 0.08);
}

.record-head strong,
.day-head strong,
.empty-state strong {
  font-size: 18px;
}

.muted {
  font-size: 13px;
  color: #6f8592;
}

.trend {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}

.trend article {
  padding: 14px;
  border-radius: 16px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.empty-state.compact {
  margin-top: 16px;
}

@media (max-width: 768px) {
  .head,
  .card-head,
  .list-head,
  .record-head,
  .day-head,
  .actions,
  .record-actions,
  .planner-actions,
  .preview-head,
  .progress-top,
  .quick-helpers {
    flex-direction: column;
  }

  .overview-grid,
  .progress-grid,
  .summary-grid,
  .meal-checklist {
    grid-template-columns: 1fr;
  }
}
</style>
