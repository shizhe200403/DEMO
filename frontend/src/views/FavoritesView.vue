<template>
  <section class="page">
    <!-- 顶部问候栏 -->
    <div class="greeting-bar">
      <div class="greeting-left">
        <h2 class="greeting-title">收藏中心</h2>
        <p class="greeting-sub">{{ currentMealFocus.badge }} · {{ currentMealFocus.title }}</p>
      </div>
      <div class="greeting-right">
        <el-button :loading="loadingFavorites" @click="loadFavorites">刷新</el-button>
      </div>
    </div>

    <CollectionSkeleton v-if="loadingFavorites && !favorites.length" variant="grid" :card-count="5" />
    <RefreshFrame v-else :active="loadingFavorites && !!favorites.length" label="正在更新收藏内容">

      <!-- 双栏主体 -->
      <div class="main-layout">

        <!-- 左侧 sidebar -->
        <aside class="sidebar">

          <!-- 今日推荐卡 -->
          <div class="sidebar-card">
            <div class="sidebar-card-header">
              <span class="card-label">当前时段推荐</span>
            </div>
            <template v-if="priorityFavorite">
              <strong class="focus-title">{{ priorityFavorite.title }}</strong>
              <p class="focus-desc">{{ priorityFavorite.description || "这道菜已经沉淀进收藏，可以直接带入今天记录。" }}</p>
              <div class="focus-meta">
                <span class="meta-tag">{{ mealTypeLabel(priorityFavorite.meal_type) }}</span>
                <span class="meta-tag">{{ priorityFavorite.cook_time_minutes ?? "-" }} 分钟</span>
              </div>
              <div class="focus-actions">
                <el-button text size="small" @click="openDetail(priorityFavorite)">查看详情</el-button>
                <el-button type="primary" plain size="small" @click="addToRecord(priorityFavorite)">加入记录</el-button>
              </div>
            </template>
            <p v-else class="empty-hint">收藏一些常用菜谱后，这里会优先推荐当前时段最合适的。</p>
          </div>

          <!-- 统计数字 -->
          <div class="sidebar-card">
            <div class="sidebar-card-header">
              <span class="card-label">收藏统计</span>
            </div>
            <div class="stat-rows">
              <div class="stat-row">
                <span class="stat-label">收藏总数</span>
                <strong class="stat-value">{{ favorites.length }}</strong>
              </div>
              <div class="stat-row">
                <span class="stat-label">早餐</span>
                <strong class="stat-value">{{ mealCounts.breakfast }}</strong>
              </div>
              <div class="stat-row">
                <span class="stat-label">午晚餐</span>
                <strong class="stat-value">{{ mealCounts.mainMeal }}</strong>
              </div>
              <div class="stat-row">
                <span class="stat-label">加餐</span>
                <strong class="stat-value">{{ mealCounts.snack }}</strong>
              </div>
            </div>
          </div>

          <!-- 餐次筛选 -->
          <div class="sidebar-card">
            <div class="sidebar-card-header">
              <span class="card-label">餐次筛选</span>
            </div>
            <div class="filter-tabs">
              <button
                v-for="item in [
                  { label: '全部', value: 'all' },
                  { label: '早餐', value: 'breakfast' },
                  { label: '午餐', value: 'lunch' },
                  { label: '晚餐', value: 'dinner' },
                  { label: '加餐', value: 'snack' },
                ]"
                :key="item.value"
                type="button"
                class="filter-tab"
                :class="{ active: mealFilter === item.value }"
                @click="mealFilter = item.value"
              >
                {{ item.label }}
              </button>
            </div>
          </div>

        </aside>

        <!-- 右侧主内容 -->
        <main class="main-content">

          <!-- 搜索工具栏 -->
          <div class="toolbar">
            <el-input v-model.trim="keyword" clearable placeholder="搜索收藏的菜谱" style="max-width: 360px" />
          </div>

          <!-- 卡片网格 -->
          <div v-if="filteredFavorites.length" class="grid">
            <article v-for="recipe in filteredFavorites" :key="recipe.id" class="recipe-card">
              <div class="card-head">
                <strong>{{ recipe.title }}</strong>
                <el-button text type="danger" :loading="favoriteLoadingId === recipe.id" @click="toggleFavorite(recipe)">移出收藏</el-button>
              </div>
              <p class="card-desc">{{ recipe.description || "暂无描述" }}</p>
              <div class="card-meta">
                <span class="meta-tag">{{ mealTypeLabel(recipe.meal_type) }}</span>
                <span class="meta-tag">{{ recipe.cook_time_minutes ?? "-" }} 分钟</span>
              </div>
              <div class="card-actions">
                <el-button text @click="openDetail(recipe)">查看详情</el-button>
                <el-button type="primary" plain @click="addToRecord(recipe)">加入记录</el-button>
              </div>
            </article>
          </div>
          <PageStateBlock
            v-else
            tone="empty"
            :title="emptyTitle"
            :description="emptyDescription"
            :action-label="emptyActionLabel"
            @action="handleEmptyAction"
          />

        </main>
      </div>

      <RecipeDetailDialog
        v-model="detailVisible"
        :recipe-id="selectedRecipeId"
        :recipe="selectedRecipe"
        :favorited="selectedRecipeId ? true : false"
        @favorite-change="handleFavoriteChange"
        @add-to-record="addToRecord"
      />
    </RefreshFrame>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { notifyActionError, notifyActionSuccess, notifyLoadError } from "../lib/feedback";
import { useRouter } from "vue-router";
import RecipeDetailDialog from "../components/RecipeDetailDialog.vue";
import { listFavoriteRecipes, unfavoriteRecipe } from "../api/recipes";

const router = useRouter();
const favorites = ref<any[]>([]);
const keyword = ref("");
const mealFilter = ref("all");
const favoriteLoadingId = ref<number | null>(null);
const loadingFavorites = ref(false);
const detailVisible = ref(false);
const selectedRecipe = ref<Record<string, any> | null>(null);
const selectedRecipeId = ref<number | null>(null);
const hasFilters = computed(() => Boolean(keyword.value) || mealFilter.value !== "all");
const currentMealFocus = computed(() => {
  const hour = new Date().getHours();
  if (hour < 10) {
    return {
      mealType: "breakfast",
      badge: "早餐时段",
      title: "先从早餐收藏里做决定",
      copy: "收藏中心更适合拿来快速落下一餐，而不是重新浏览整个菜谱库。",
    };
  }
  if (hour < 15) {
    return {
      mealType: "lunch",
      badge: "午餐时段",
      title: "先看你已经验证过的午餐选择",
      copy: "中午更需要快速决定，收藏页应该优先承担这个角色。",
    };
  }
  if (hour < 21) {
    return {
      mealType: "dinner",
      badge: "晚餐时段",
      title: "晚餐优先从常用收藏里选",
      copy: "晚餐更容易纠结，先用收藏把范围收窄，再考虑是否要去菜谱库继续挑。",
    };
  }
  return {
    mealType: "snack",
    badge: "加餐时段",
    title: "先看更轻量的收藏备选",
    copy: "晚上或加餐时，更适合先从已收藏的轻量选择里快速决策。",
  };
});

const filteredFavorites = computed(() => {
  const query = keyword.value.toLowerCase();
  return favorites.value.filter((recipe) => {
    const hitMeal = mealFilter.value === "all" || recipe.meal_type === mealFilter.value;
    const hitKeyword = !query || [recipe.title, recipe.description, recipe.meal_type].some((field) => String(field || "").toLowerCase().includes(query));
    return hitMeal && hitKeyword;
  });
});
const sortedFavorites = computed(() => {
  return [...favorites.value].sort((a, b) => scoreFavorite(b) - scoreFavorite(a));
});
const priorityFavorite = computed(() => {
  const sameMeal = sortedFavorites.value.find((item) => item.meal_type === currentMealFocus.value.mealType);
  return sameMeal ?? sortedFavorites.value[0] ?? null;
});
const quickFavorites = computed(() => {
  return sortedFavorites.value.filter((item) => numericValue(item.cook_time_minutes) > 0 && numericValue(item.cook_time_minutes) <= 15).slice(0, 3);
});
const proteinFavorites = computed(() => {
  return sortedFavorites.value.filter((item) => numericValue(item.nutrition_summary?.per_serving_protein) >= 18).slice(0, 3);
});

const mealCounts = computed(() => ({
  breakfast: favorites.value.filter((item) => item.meal_type === "breakfast").length,
  mainMeal: favorites.value.filter((item) => item.meal_type === "lunch" || item.meal_type === "dinner").length,
  snack: favorites.value.filter((item) => item.meal_type === "snack").length,
}));
const emptyTitle = computed(() => {
  if (hasFilters.value) {
    return "当前筛选条件下没有匹配的收藏。";
  }
  return "当前还没有收藏内容。";
});
const emptyDescription = computed(() => {
  if (hasFilters.value) {
    return "可以清空筛选条件，或者去菜谱库继续沉淀新的常用选择。";
  }
  return "去菜谱页收藏一些常吃、常做的菜谱，后面会形成自己的私人菜单。";
});
const emptyActionLabel = computed(() => (hasFilters.value ? "清空筛选" : "去菜谱库"));

function mealTypeLabel(mealType: string) {
  return {
    breakfast: "早餐",
    lunch: "午餐",
    dinner: "晚餐",
    snack: "加餐",
  }[mealType] || "不限";
}

function numericValue(value: unknown) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function scoreFavorite(recipe: Record<string, any>) {
  let score = 0;
  if (recipe.meal_type === currentMealFocus.value.mealType) score += 6;
  if (numericValue(recipe.cook_time_minutes) > 0 && numericValue(recipe.cook_time_minutes) <= 15) score += 4;
  score += Math.min(4, numericValue(recipe.nutrition_summary?.per_serving_protein) / 10);
  score -= numericValue(recipe.cook_time_minutes) / 20;
  return score;
}

function formatProtein(recipe: Record<string, any>) {
  const protein = numericValue(recipe.nutrition_summary?.per_serving_protein);
  return `${protein.toFixed(1)} g`;
}

async function loadFavorites() {
  try {
    loadingFavorites.value = true;
    const response = await listFavoriteRecipes();
    favorites.value = response.data ?? [];
  } catch (error) {
    notifyLoadError("收藏内容");
  } finally {
    loadingFavorites.value = false;
  }
}

function openDetail(recipe: Record<string, any>) {
  selectedRecipe.value = recipe;
  selectedRecipeId.value = Number(recipe.id);
  detailVisible.value = true;
}

function addToRecord(recipe: Record<string, any>) {
  router.push({
    path: "/records",
    query: {
      recipe_id: String(recipe.id),
      meal_type: recipe.meal_type || "lunch",
      note: recipe.title || "",
      source: "favorites",
      from_title: recipe.title || "",
    },
  });
}

async function toggleFavorite(recipe: Record<string, any>) {
  try {
    favoriteLoadingId.value = Number(recipe.id);
    await unfavoriteRecipe(Number(recipe.id));
    favorites.value = favorites.value.filter((item) => Number(item.id) !== Number(recipe.id));
    notifyActionSuccess("已移出收藏");
  } catch (error) {
    notifyActionError("移出收藏");
  } finally {
    favoriteLoadingId.value = null;
  }
}

function handleEmptyAction() {
  if (hasFilters.value) {
    keyword.value = "";
    mealFilter.value = "all";
    return;
  }
  router.push("/recipes");
}

function handleFavoriteChange(payload: { recipeId: number; favorited: boolean }) {
  if (payload.favorited) {
    return;
  }
  favorites.value = favorites.value.filter((item) => Number(item.id) !== payload.recipeId);
}

loadFavorites();
</script>

<style scoped>
/* ── 全局容器 ─────────────────────────────────── */
.page {
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* ── 顶部问候栏 ───────────────────────────────── */
.greeting-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 28px;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid rgba(16, 34, 42, 0.07);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 10;
  flex-wrap: wrap;
}

.greeting-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.greeting-title {
  margin: 0;
  font-size: clamp(18px, 2vw, 24px);
  font-weight: 700;
  color: #173042;
  line-height: 1.2;
}

.greeting-sub {
  margin: 0;
  font-size: 13px;
  color: #5a7a8a;
  line-height: 1.5;
}

.greeting-right {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-shrink: 0;
}

/* ── 双栏主体 ─────────────────────────────────── */
.main-layout {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 0;
  min-height: calc(100vh - 110px);
  align-items: start;
}

/* ── 左侧栏 ───────────────────────────────────── */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 16px 20px 20px;
  border-right: 1px solid rgba(16, 34, 42, 0.07);
  position: sticky;
  top: 60px;
  max-height: calc(100vh - 60px);
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(16, 34, 42, 0.1) transparent;
}

.sidebar-card {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 34, 42, 0.08);
  border-radius: 20px;
  padding: 16px;
  box-shadow: 0 4px 16px rgba(15, 30, 39, 0.05);
}

.sidebar-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}

.card-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #5a7a8a;
}

/* 今日推荐卡 */
.focus-title {
  display: block;
  font-size: 16px;
  font-weight: 700;
  color: #173042;
  line-height: 1.3;
}

.focus-desc {
  margin: 6px 0 10px;
  font-size: 13px;
  color: #476072;
  line-height: 1.6;
}

.focus-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.focus-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.empty-hint {
  margin: 0;
  font-size: 13px;
  color: #5a7a8a;
  line-height: 1.6;
}

/* 统计行 */
.stat-rows {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-label {
  font-size: 13px;
  color: #5a7a8a;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #173042;
}

/* 筛选 tab */
.filter-tabs {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-tab {
  display: block;
  width: 100%;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  text-align: left;
  font-size: 14px;
  color: #476072;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.filter-tab:hover {
  background: rgba(232, 241, 247, 0.7);
}

.filter-tab.active {
  background: rgba(23, 48, 66, 0.08);
  color: #173042;
  font-weight: 600;
  border-color: rgba(23, 48, 66, 0.12);
}

/* ── 右侧主内容 ───────────────────────────────── */
.main-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px 24px 32px;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 卡片网格 */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}

.recipe-card {
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 4px 16px rgba(15, 30, 39, 0.05);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.card-head strong {
  font-size: 15px;
  font-weight: 700;
  color: #173042;
  line-height: 1.3;
}

.card-desc {
  margin: 0;
  font-size: 13px;
  color: #476072;
  line-height: 1.6;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.meta-tag {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 999px;
  background: #e8f1f7;
  color: #24566a;
  font-size: 12px;
}

.card-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

/* ── 响应式 ───────────────────────────────────── */
@media (max-width: 900px) {
  .main-layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static;
    max-height: none;
    border-right: none;
    border-bottom: 1px solid rgba(16, 34, 42, 0.07);
    padding: 16px;
    flex-direction: row;
    flex-wrap: wrap;
    overflow: visible;
  }

  .sidebar-card {
    flex: 1 1 200px;
  }
}

@media (max-width: 640px) {
  .greeting-bar {
    padding: 14px 16px;
    flex-direction: column;
    align-items: flex-start;
  }

  .main-content {
    padding: 14px 16px 20px;
  }

  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
