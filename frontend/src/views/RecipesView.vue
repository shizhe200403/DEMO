<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Recipe Library</p>
        <h2>菜谱库</h2>
        <p class="desc">从浏览升级到决策。这里不只展示菜谱，还要帮助用户按场景、时间成本和营养目标更快做选择。</p>
      </div>
      <div class="head-actions">
        <el-button @click="loadRecipes">刷新</el-button>
        <el-button plain @click="router.push('/favorites')">进入收藏中心</el-button>
      </div>
    </div>

    <CollectionSkeleton v-if="loadingRecipes && !recipes.length" variant="grid" :card-count="6" />
    <RefreshFrame v-else :active="loadingRecipes && !!recipes.length" label="正在更新菜谱列表">
    <div class="summary-grid">
      <article>
        <span>菜谱总数</span>
        <strong>{{ recipeSummary.total }}</strong>
        <p>当前可浏览的菜谱总量。</p>
      </article>
      <article>
        <span>已收藏</span>
        <strong>{{ recipeSummary.favorites }}</strong>
        <p>已经沉淀为你的个人资产的菜谱数。</p>
      </article>
      <article>
        <span>15 分钟内</span>
        <strong>{{ recipeSummary.quick }}</strong>
        <p>适合工作日快速决策的轻量选择。</p>
      </article>
      <article>
        <span>高蛋白</span>
        <strong>{{ recipeSummary.highProtein }}</strong>
        <p>更适合增肌或补蛋白场景的选择。</p>
      </article>
    </div>

    <div class="focus-strip">
      <div>
        <strong>{{ activeGoal ? `${goalTypeLabel(activeGoal.goal_type)}阶段推荐` : "当前未设置重点目标" }}</strong>
        <p>{{ goalFocusedCopy }}</p>
      </div>
      <el-button v-if="goalSuggestedFilter !== 'all'" plain @click="sceneFilter = goalSuggestedFilter">应用目标筛选</el-button>
    </div>

    <div class="toolbar">
      <el-input v-model.trim="keyword" placeholder="搜索菜名、描述或餐次" clearable />
      <el-select v-model="mealFilter" style="width: 160px">
        <el-option label="全部餐次" value="all" />
        <el-option label="早餐" value="breakfast" />
        <el-option label="午餐" value="lunch" />
        <el-option label="晚餐" value="dinner" />
        <el-option label="加餐" value="snack" />
      </el-select>
      <el-select v-model="sortMode" style="width: 180px">
        <el-option label="智能排序" value="smart" />
        <el-option label="最快出餐" value="time" />
        <el-option label="蛋白优先" value="protein" />
        <el-option label="热量更低" value="energy" />
      </el-select>
      <el-switch v-model="favoriteOnly" active-text="只看收藏" inactive-text="全部菜谱" />
    </div>

    <div class="scene-row mobile-scroll-row">
      <el-button :type="sceneFilter === 'all' ? 'primary' : 'default'" plain @click="sceneFilter = 'all'">全部</el-button>
      <el-button :type="sceneFilter === 'quick' ? 'primary' : 'default'" plain @click="sceneFilter = 'quick'">15 分钟内</el-button>
      <el-button :type="sceneFilter === 'high_protein' ? 'primary' : 'default'" plain @click="sceneFilter = 'high_protein'">高蛋白</el-button>
      <el-button :type="sceneFilter === 'light' ? 'primary' : 'default'" plain @click="sceneFilter = 'light'">轻负担</el-button>
      <el-button :type="sceneFilter === 'favorites' ? 'primary' : 'default'" plain @click="sceneFilter = 'favorites'">收藏优先</el-button>
    </div>

    <div v-if="quickPicks.length" class="quick-picks">
      <article v-for="recipe in quickPicks" :key="recipe.id">
        <div class="card-head">
          <strong>{{ recipe.title }}</strong>
          <span class="pick-badge">{{ quickPickLabel(recipe) }}</span>
        </div>
        <p>{{ recipe.description || "适合当前筛选条件，可直接加入记录。" }}</p>
        <div class="footer-actions">
          <el-button text @click="openDetail(recipe)">查看详情</el-button>
          <el-button type="primary" plain @click="addToRecord(recipe)">加入记录</el-button>
        </div>
      </article>
    </div>

    <div v-if="filteredRecipes.length" class="grid">
      <article v-for="recipe in filteredRecipes" :key="recipe.id">
        <div class="card-head">
          <strong>{{ recipe.title }}</strong>
          <el-button text :loading="favoriteLoadingId === recipe.id" @click="toggleFavorite(recipe)">
            {{ isFavorited(recipe.id) ? "取消收藏" : "收藏" }}
          </el-button>
        </div>
        <p>{{ recipe.description || "暂无描述" }}</p>
        <div class="meta">
          <span>{{ mealTypeLabel(recipe.meal_type) }}</span>
          <span>{{ difficultyLabel(recipe.difficulty) }}</span>
          <span>{{ recipe.cook_time_minutes ?? "-" }} 分钟</span>
        </div>
        <div class="tag-row">
          <span v-if="isFavorited(recipe.id)" class="feature-tag is-favorite">已收藏</span>
          <span v-if="isQuickRecipe(recipe)" class="feature-tag is-quick">快手</span>
          <span v-if="isHighProtein(recipe)" class="feature-tag is-protein">高蛋白</span>
          <span v-if="isLightRecipe(recipe)" class="feature-tag is-light">轻负担</span>
          <span v-if="matchesGoal(recipe)" class="feature-tag is-goal">适合当前目标</span>
        </div>
        <div class="nutrition" v-if="recipe.nutrition_summary">
          <span>{{ recipe.nutrition_summary.per_serving_energy ?? 0 }} kcal / 份</span>
          <span>{{ recipe.nutrition_summary.per_serving_protein ?? 0 }} g 蛋白</span>
        </div>
        <div class="footer">
          <div class="footer-copy">
            <p>{{ footerCopy(recipe) }}</p>
          </div>
          <div class="footer-actions">
            <el-button text @click="openDetail(recipe)">查看详情</el-button>
            <el-button type="primary" plain @click="addToRecord(recipe)">加入记录</el-button>
          </div>
        </div>
      </article>
    </div>
    <PageStateBlock
      v-else
      tone="empty"
      :title="emptyTitle"
      :description="emptyDescription"
      :action-label="emptyActionLabel"
      @action="resetFilters"
    />

    <RecipeDetailDialog
      v-model="detailVisible"
      :recipe-id="selectedRecipeId"
      :recipe="selectedRecipe"
      :favorited="selectedRecipeId ? isFavorited(selectedRecipeId) : false"
      :reason-text="selectedReasonText"
      @favorite-change="handleFavoriteChange"
      @add-to-record="addToRecord"
    />
    </RefreshFrame>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { notifyActionError, notifyActionSuccess, notifyLoadError } from "../lib/feedback";
import { useRouter } from "vue-router";
import RecipeDetailDialog from "../components/RecipeDetailDialog.vue";
import { explainRecommendation, favoriteRecipe, listFavoriteRecipes, listRecipes, unfavoriteRecipe } from "../api/recipes";
import { trackEvent } from "../api/behavior";
import { listHealthGoals } from "../api/goals";

const router = useRouter();
const recipes = ref<any[]>([]);
const favoriteIds = ref<number[]>([]);
const favoriteLoadingId = ref<number | null>(null);
const loadingRecipes = ref(false);
const keyword = ref("");
const mealFilter = ref("all");
const sceneFilter = ref<"all" | "quick" | "high_protein" | "light" | "favorites">("all");
const sortMode = ref<"smart" | "time" | "protein" | "energy">("smart");
const favoriteOnly = ref(false);
const detailVisible = ref(false);
const selectedRecipe = ref<Record<string, any> | null>(null);
const selectedRecipeId = ref<number | null>(null);
const selectedReasonText = ref("");
const activeGoal = ref<Record<string, any> | null>(null);

const goalSuggestedFilter = computed(() => {
  const goalType = activeGoal.value?.goal_type;
  if (goalType === "muscle_gain" || goalType === "protein_up") {
    return "high_protein";
  }
  if (goalType === "weight_loss" || goalType === "fat_control" || goalType === "blood_sugar_control") {
    return "light";
  }
  return "all";
});
const goalFocusedCopy = computed(() => {
  if (!activeGoal.value) {
    return "先建立一个重点目标，菜谱页才能更像决策工具，而不是普通列表。";
  }
  return `当前重点是${goalTypeLabel(activeGoal.value.goal_type)}，建议优先看更符合这一目标的菜谱。`;
});
const recipeSummary = computed(() => ({
  total: recipes.value.length,
  favorites: favoriteIds.value.length,
  quick: recipes.value.filter((item) => isQuickRecipe(item)).length,
  highProtein: recipes.value.filter((item) => isHighProtein(item)).length,
}));
const hasActiveFilters = computed(() => {
  return (
    Boolean(keyword.value) ||
    mealFilter.value !== "all" ||
    sceneFilter.value !== "all" ||
    sortMode.value !== "smart" ||
    favoriteOnly.value
  );
});
const filteredRecipes = computed(() => {
  const query = keyword.value.toLowerCase();
  return [...recipes.value]
    .filter((recipe) => {
      const hitMeal = mealFilter.value === "all" || recipe.meal_type === mealFilter.value;
      const hitKeyword =
        !query || [recipe.title, recipe.description, recipe.meal_type].some((field) => String(field || "").toLowerCase().includes(query));
      const hitFavorite = !favoriteOnly.value || favoriteIds.value.includes(Number(recipe.id));
      const hitScene =
        sceneFilter.value === "all" ||
        (sceneFilter.value === "favorites" && isFavorited(Number(recipe.id))) ||
        (sceneFilter.value === "quick" && isQuickRecipe(recipe)) ||
        (sceneFilter.value === "high_protein" && isHighProtein(recipe)) ||
        (sceneFilter.value === "light" && isLightRecipe(recipe));
      return hitMeal && hitKeyword && hitFavorite && hitScene;
    })
    .sort((a, b) => compareRecipes(a, b));
});
const quickPicks = computed(() => filteredRecipes.value.slice(0, 3));
const emptyTitle = computed(() => {
  if (favoriteOnly.value || sceneFilter.value === "favorites") {
    return "你还没有匹配条件的收藏菜谱。";
  }
  if (!recipes.value.length) {
    return "当前还没有可浏览的菜谱。";
  }
  return "没有找到匹配的菜谱。";
});
const emptyDescription = computed(() => {
  if (favoriteOnly.value || sceneFilter.value === "favorites") {
    return "先收藏几个常用菜谱，后续每天记录会明显更顺手。";
  }
  if (!recipes.value.length) {
    return "可以稍后刷新，或者先完善目标与档案，让系统逐步补充更适合的内容。";
  }
  return "试试切换场景、放宽关键词，或回到“全部”。";
});
const emptyActionLabel = computed(() => (hasActiveFilters.value ? "重置筛选" : "刷新菜谱"));

function numericValue(value: unknown) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function isFavorited(recipeId: number) {
  return favoriteIds.value.includes(Number(recipeId));
}

function isQuickRecipe(recipe: Record<string, any>) {
  return numericValue(recipe.cook_time_minutes) > 0 && numericValue(recipe.cook_time_minutes) <= 15;
}

function isHighProtein(recipe: Record<string, any>) {
  return numericValue(recipe.nutrition_summary?.per_serving_protein) >= 18;
}

function isLightRecipe(recipe: Record<string, any>) {
  const energy = numericValue(recipe.nutrition_summary?.per_serving_energy);
  return energy > 0 && energy <= 450;
}

function matchesGoal(recipe: Record<string, any>) {
  const goalType = activeGoal.value?.goal_type;
  if (!goalType) {
    return false;
  }
  if (goalType === "muscle_gain" || goalType === "protein_up") {
    return isHighProtein(recipe);
  }
  if (goalType === "weight_loss" || goalType === "fat_control" || goalType === "blood_sugar_control") {
    return isLightRecipe(recipe);
  }
  return false;
}

function compareRecipes(a: Record<string, any>, b: Record<string, any>) {
  if (sortMode.value === "time") {
    return numericValue(a.cook_time_minutes) - numericValue(b.cook_time_minutes);
  }
  if (sortMode.value === "protein") {
    return numericValue(b.nutrition_summary?.per_serving_protein) - numericValue(a.nutrition_summary?.per_serving_protein);
  }
  if (sortMode.value === "energy") {
    return numericValue(a.nutrition_summary?.per_serving_energy) - numericValue(b.nutrition_summary?.per_serving_energy);
  }

  const score = (recipe: Record<string, any>) => {
    let total = 0;
    if (isFavorited(recipe.id)) total += 6;
    if (matchesGoal(recipe)) total += 5;
    if (isQuickRecipe(recipe)) total += 2;
    total += Math.min(2, numericValue(recipe.nutrition_summary?.per_serving_protein) / 10);
    total -= numericValue(recipe.cook_time_minutes) / 30;
    return total;
  };

  return score(b) - score(a);
}

function mealTypeLabel(mealType: string) {
  return {
    breakfast: "早餐",
    lunch: "午餐",
    dinner: "晚餐",
    snack: "加餐",
  }[mealType] || "不限";
}

function difficultyLabel(difficulty: string) {
  return {
    easy: "简单",
    medium: "适中",
    hard: "复杂",
  }[difficulty] || "难度未知";
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

function quickPickLabel(recipe: Record<string, any>) {
  if (matchesGoal(recipe)) {
    return "适合当前目标";
  }
  if (isFavorited(recipe.id)) {
    return "收藏优先";
  }
  if (isQuickRecipe(recipe)) {
    return "快手选择";
  }
  return "当前值得先看";
}

function footerCopy(recipe: Record<string, any>) {
  if (matchesGoal(recipe)) {
    return "这道菜更贴近你当前目标，适合优先尝试。";
  }
  if (isQuickRecipe(recipe)) {
    return "时间成本较低，适合工作日快速决策。";
  }
  if (isHighProtein(recipe)) {
    return "蛋白相对更高，适合需要补蛋白的场景。";
  }
  return "适合作为日常均衡饮食的一部分。";
}

async function loadRecipes() {
  try {
    loadingRecipes.value = true;
    const [recipeResponse, favoriteResponse, goalResponse] = await Promise.all([listRecipes(), listFavoriteRecipes(), listHealthGoals()]);
    recipes.value = recipeResponse.data?.items ?? recipeResponse.data ?? [];
    favoriteIds.value = (favoriteResponse.data ?? []).map((item: Record<string, any>) => Number(item.id));
    const goals = goalResponse.data?.items ?? goalResponse.data ?? [];
    activeGoal.value = goals.find((item: Record<string, any>) => item.status === "active") ?? null;
    if (sceneFilter.value === "all" && goalSuggestedFilter.value !== "all") {
      sceneFilter.value = goalSuggestedFilter.value;
    }
    trackEvent({ behavior_type: "view", context_scene: "recipes" }).catch(() => undefined);
  } catch (error) {
    notifyLoadError("菜谱");
  } finally {
    loadingRecipes.value = false;
  }
}

async function toggleFavorite(recipe: Record<string, any>) {
  try {
    favoriteLoadingId.value = Number(recipe.id);
    if (isFavorited(Number(recipe.id))) {
      await unfavoriteRecipe(Number(recipe.id));
      favoriteIds.value = favoriteIds.value.filter((id) => id !== Number(recipe.id));
      notifyActionSuccess("已取消收藏");
      return;
    }
    await favoriteRecipe(Number(recipe.id));
    favoriteIds.value = [...favoriteIds.value, Number(recipe.id)];
    notifyActionSuccess("已加入收藏");
  } catch (error) {
    notifyActionError("收藏操作");
  } finally {
    favoriteLoadingId.value = null;
  }
}

function resetFilters() {
  if (!hasActiveFilters.value) {
    loadRecipes();
    return;
  }
  keyword.value = "";
  mealFilter.value = "all";
  sceneFilter.value = goalSuggestedFilter.value !== "all" ? goalSuggestedFilter.value : "all";
  sortMode.value = "smart";
  favoriteOnly.value = false;
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

async function openDetail(recipe: Record<string, any>) {
  selectedRecipe.value = recipe;
  selectedRecipeId.value = Number(recipe.id);
  detailVisible.value = true;
  try {
    const response = await explainRecommendation(Number(recipe.id));
    selectedReasonText.value = response.data?.reason_text || "";
  } catch {
    selectedReasonText.value = "";
  }
}

function handleFavoriteChange(payload: { recipeId: number; favorited: boolean }) {
  if (payload.favorited && !favoriteIds.value.includes(payload.recipeId)) {
    favoriteIds.value = [...favoriteIds.value, payload.recipeId];
    return;
  }
  if (!payload.favorited) {
    favoriteIds.value = favoriteIds.value.filter((id) => id !== payload.recipeId);
  }
}

onMounted(loadRecipes);
</script>

<style scoped>
.page {
  display: grid;
  gap: 18px;
}

.head,
.head-actions,
.toolbar,
.card-head,
.footer,
.footer-actions,
.scene-row,
.focus-strip,
.tag-row {
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

h2 {
  margin: 0;
  font-size: 30px;
}

.desc,
.grid p,
.empty-state p,
.summary-grid p,
.focus-strip p,
.quick-picks p {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.65;
}

.summary-grid,
.quick-picks,
.grid {
  display: grid;
  gap: 14px;
}

.summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
}

.summary-grid article,
.focus-strip,
.quick-picks article,
.grid article,
.empty-state {
  padding: 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.summary-grid span,
.meta span,
.nutrition span,
.pick-badge {
  padding: 6px 10px;
  border-radius: 999px;
  background: #e8f1f7;
  color: #24566a;
  font-size: 12px;
}

.summary-grid strong,
.grid strong,
.empty-state strong,
.focus-strip strong {
  display: block;
  font-size: 18px;
}

.toolbar,
.scene-row,
.tag-row {
  flex-wrap: wrap;
}

.focus-strip {
  align-items: center;
}

.quick-picks {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.grid {
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.meta,
.nutrition {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 14px;
}

.tag-row {
  margin-top: 14px;
}

.feature-tag {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.feature-tag.is-favorite {
  background: rgba(23, 48, 66, 0.12);
  color: #173042;
}

.feature-tag.is-quick {
  background: rgba(186, 114, 22, 0.14);
  color: #9a621a;
}

.feature-tag.is-protein {
  background: rgba(29, 111, 95, 0.14);
  color: #1d6f5f;
}

.feature-tag.is-light {
  background: rgba(69, 108, 180, 0.14);
  color: #2d5fa1;
}

.feature-tag.is-goal {
  background: rgba(120, 64, 148, 0.14);
  color: #6b2f8e;
}

.footer {
  margin-top: 18px;
}

.footer-copy {
  flex: 1;
}

@media (max-width: 960px) {
  .quick-picks {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .head,
  .head-actions,
  .toolbar,
  .card-head,
  .footer,
  .footer-actions,
  .scene-row,
  .focus-strip {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
