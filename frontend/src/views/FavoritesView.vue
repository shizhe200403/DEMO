<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Favorites</p>
        <h2>收藏中心</h2>
        <p class="desc">把想吃、值得复用的菜谱沉淀下来，后面记录饮食会快很多。</p>
      </div>
      <el-button @click="loadFavorites">刷新</el-button>
    </div>

    <CollectionSkeleton v-if="loadingFavorites && !favorites.length" variant="grid" :card-count="5" />
    <RefreshFrame v-else :active="loadingFavorites && !!favorites.length" label="正在更新收藏内容">
    <div class="focus-strip">
      <div class="focus-copy">
        <span class="focus-badge">{{ currentMealFocus.badge }}</span>
        <strong>{{ currentMealFocus.title }}</strong>
        <p>{{ currentMealFocus.copy }}</p>
      </div>
      <div class="focus-actions">
        <el-button v-if="priorityFavorite" type="primary" @click="addToRecord(priorityFavorite)">直接加入记录</el-button>
        <el-button plain @click="router.push('/records')">去记录页</el-button>
      </div>
    </div>

    <div class="summary">
      <article>
        <span>收藏总数</span>
        <strong>{{ favorites.length }}</strong>
      </article>
      <article>
        <span>早餐收藏</span>
        <strong>{{ mealCounts.breakfast }}</strong>
      </article>
      <article>
        <span>午晚餐收藏</span>
        <strong>{{ mealCounts.mainMeal }}</strong>
      </article>
      <article>
        <span>加餐收藏</span>
        <strong>{{ mealCounts.snack }}</strong>
      </article>
    </div>

    <div v-if="priorityFavorite || quickFavorites.length || proteinFavorites.length" class="workbench-grid">
      <article v-if="priorityFavorite" class="panel-card">
        <div class="panel-head">
          <div>
            <h3>当前优先</h3>
            <p>先给你一个更适合当前时段和使用习惯的选择，减少临时决策成本。</p>
          </div>
        </div>
        <div class="favorite-spotlight">
          <strong>{{ priorityFavorite.title }}</strong>
          <p>{{ priorityFavorite.description || "这道菜已经沉淀进收藏，可以直接带入今天记录。" }}</p>
          <div class="meta">
            <span>{{ mealTypeLabel(priorityFavorite.meal_type) }}</span>
            <span>{{ priorityFavorite.cook_time_minutes ?? "-" }} 分钟</span>
          </div>
          <div class="actions">
            <el-button text @click="openDetail(priorityFavorite)">查看详情</el-button>
            <el-button type="primary" plain @click="addToRecord(priorityFavorite)">加入记录</el-button>
          </div>
        </div>
      </article>

      <article v-if="quickFavorites.length" class="panel-card">
        <div class="panel-head">
          <div>
            <h3>现在最省事</h3>
            <p>优先把时间成本低的收藏放前面，适合工作日直接做决定。</p>
          </div>
        </div>
        <div class="mini-list">
          <button v-for="recipe in quickFavorites" :key="`quick-${recipe.id}`" type="button" class="mini-card" @click="addToRecord(recipe)">
            <strong>{{ recipe.title }}</strong>
            <small>{{ mealTypeLabel(recipe.meal_type) }} · {{ recipe.cook_time_minutes ?? "-" }} 分钟</small>
          </button>
        </div>
      </article>

      <article v-if="proteinFavorites.length" class="panel-card">
        <div class="panel-head">
          <div>
            <h3>补蛋白优先</h3>
            <p>当你今天还差蛋白时，先从已经收藏的高蛋白选择里挑，比重新搜索更快。</p>
          </div>
        </div>
        <div class="mini-list">
          <button v-for="recipe in proteinFavorites" :key="`protein-${recipe.id}`" type="button" class="mini-card" @click="addToRecord(recipe)">
            <strong>{{ recipe.title }}</strong>
            <small>{{ formatProtein(recipe) }} 蛋白 · {{ mealTypeLabel(recipe.meal_type) }}</small>
          </button>
        </div>
      </article>
    </div>

    <div class="toolbar">
      <el-input v-model.trim="keyword" clearable placeholder="搜索收藏的菜谱" />
      <el-select v-model="mealFilter" style="width: 160px">
        <el-option label="全部餐次" value="all" />
        <el-option label="早餐" value="breakfast" />
        <el-option label="午餐" value="lunch" />
        <el-option label="晚餐" value="dinner" />
        <el-option label="加餐" value="snack" />
      </el-select>
    </div>

    <div v-if="filteredFavorites.length" class="grid">
      <article v-for="recipe in filteredFavorites" :key="recipe.id">
        <div class="card-head">
          <strong>{{ recipe.title }}</strong>
          <el-button text type="danger" :loading="favoriteLoadingId === recipe.id" @click="toggleFavorite(recipe)">移出收藏</el-button>
        </div>
        <p>{{ recipe.description || "暂无描述" }}</p>
        <div class="meta">
          <span>{{ mealTypeLabel(recipe.meal_type) }}</span>
          <span>{{ recipe.cook_time_minutes ?? "-" }} 分钟</span>
        </div>
        <div class="actions">
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
.page {
  display: grid;
  gap: 18px;
}

.head,
.toolbar,
.card-head,
.actions,
.focus-strip,
.focus-actions,
.panel-head {
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
.focus-strip p,
.panel-card p {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.65;
}

.focus-strip,
.panel-card {
  padding: 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.focus-copy {
  display: grid;
  gap: 8px;
}

.focus-badge {
  justify-self: flex-start;
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(23, 48, 66, 0.08);
  color: #173042;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.focus-strip strong,
.panel-card strong {
  display: block;
  font-size: 18px;
}

.summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.workbench-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.summary article,
.grid article,
.empty-state {
  padding: 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.summary span,
.meta span {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: #e8f1f7;
  color: #24566a;
  font-size: 12px;
}

.summary strong,
.grid strong,
.empty-state strong {
  display: block;
  margin-top: 12px;
  font-size: 22px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
}

.favorite-spotlight,
.mini-list {
  display: grid;
  gap: 12px;
}

.mini-card {
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(247, 251, 255, 0.92);
  text-align: left;
}

.mini-card strong {
  font-size: 15px;
  color: #173042;
}

.mini-card small {
  display: block;
  margin-top: 6px;
  color: #5a7a8a;
  line-height: 1.5;
}

.meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 14px;
}

@media (max-width: 768px) {
  .summary,
  .workbench-grid,
  .grid {
    grid-template-columns: 1fr;
  }

  .head,
  .toolbar,
  .card-head,
  .actions,
  .focus-strip,
  .focus-actions,
  .panel-head {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
