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

const filteredFavorites = computed(() => {
  const query = keyword.value.toLowerCase();
  return favorites.value.filter((recipe) => {
    const hitMeal = mealFilter.value === "all" || recipe.meal_type === mealFilter.value;
    const hitKeyword = !query || [recipe.title, recipe.description, recipe.meal_type].some((field) => String(field || "").toLowerCase().includes(query));
    return hitMeal && hitKeyword;
  });
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
.actions {
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
.empty-state p {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.65;
}

.summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
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

.meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 14px;
}

@media (max-width: 768px) {
  .head,
  .toolbar,
  .card-head,
  .actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
