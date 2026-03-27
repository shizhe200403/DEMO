<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Recipe Library</p>
        <h2>菜谱库</h2>
        <p class="desc">按餐次、准备时间和营养重点筛选菜谱，尽快找到今天更适合的一餐。</p>
      </div>
      <div class="head-actions">
        <el-button type="primary" @click="openCreator">上传菜谱</el-button>
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

    <div class="creator-strip">
      <div class="creator-copy">
        <strong>先把自己的菜谱沉淀进系统</strong>
        <p>当前已去掉外部菜谱与外部食物依赖。常吃什么就先上传什么，后面的记录、收藏和报表会更稳定。</p>
      </div>
      <div class="creator-actions">
        <el-button type="primary" @click="openCreator">上传我的菜谱</el-button>
      </div>
    </div>

    <PageStateBlock
      tone="info"
      title="AI 图片识别会在后续版本接入"
      description="后续会支持上传食物照片，由 AI 助手识别食材、份量与营养估算。本轮先把手动上传菜谱链路做顺。"
      compact
    />

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
    <el-dialog v-model="creatorVisible" width="760px" title="上传菜谱">
      <el-form label-position="top" class="creator-form">
        <el-row :gutter="16">
          <el-col :span="24" :md="12">
            <el-form-item label="菜谱名称">
              <el-input v-model.trim="creatorForm.title" placeholder="例如：香煎鸡胸沙拉" />
            </el-form-item>
          </el-col>
          <el-col :span="24" :md="12">
            <el-form-item label="餐次">
              <el-select v-model="creatorForm.meal_type" style="width: 100%">
                <el-option label="早餐" value="breakfast" />
                <el-option label="午餐" value="lunch" />
                <el-option label="晚餐" value="dinner" />
                <el-option label="加餐" value="snack" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述">
          <el-input v-model.trim="creatorForm.description" type="textarea" :rows="2" placeholder="例如：适合工作日晚餐，准备时间短，蛋白更高。" />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12" :md="6">
            <el-form-item label="份数">
              <el-input-number v-model="creatorForm.servings" :min="1" :max="20" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12" :md="6">
            <el-form-item label="每份说明">
              <el-input v-model.trim="creatorForm.portion_size" placeholder="1 份 / 1 碗" />
            </el-form-item>
          </el-col>
          <el-col :span="12" :md="6">
            <el-form-item label="准备时间">
              <el-input-number v-model="creatorForm.prep_time_minutes" :min="0" :max="300" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12" :md="6">
            <el-form-item label="烹饪时间">
              <el-input-number v-model="creatorForm.cook_time_minutes" :min="0" :max="300" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="难度">
          <el-radio-group v-model="creatorForm.difficulty">
            <el-radio-button label="easy">简单</el-radio-button>
            <el-radio-button label="medium">适中</el-radio-button>
            <el-radio-button label="hard">复杂</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <div class="creator-section">
          <div class="section-head">
            <strong>食材清单</strong>
            <el-button plain @click="addCreatorIngredient">新增食材</el-button>
          </div>
          <div v-for="(ingredient, index) in creatorForm.ingredients" :key="`ingredient-${index}`" class="creator-row">
            <el-input v-model.trim="ingredient.ingredient_name" placeholder="食材名称，例如：鸡胸肉" />
            <el-input-number v-model="ingredient.amount" :min="0" :max="9999" :precision="1" />
            <el-input v-model.trim="ingredient.unit" placeholder="单位，例如：g / 个 / 份" />
            <el-switch v-model="ingredient.is_main" active-text="主食材" />
            <el-button text type="danger" :disabled="creatorForm.ingredients.length === 1" @click="removeCreatorIngredient(index)">删除</el-button>
          </div>
        </div>

        <div class="creator-section">
          <div class="section-head">
            <strong>做法步骤</strong>
            <el-button plain @click="addCreatorStep">新增步骤</el-button>
          </div>
          <div v-for="(step, index) in creatorForm.steps" :key="`step-${index}`" class="creator-step-row">
            <span class="step-index">步骤 {{ index + 1 }}</span>
            <el-input v-model.trim="step.content" type="textarea" :rows="2" placeholder="描述这一步怎么做" />
            <el-button text type="danger" :disabled="creatorForm.steps.length === 1" @click="removeCreatorStep(index)">删除</el-button>
          </div>
        </div>

        <div class="creator-section">
          <div class="section-head">
            <strong>营养信息</strong>
            <span>可以先手动填写；如果暂时不确定，可以留空，等后续 AI 助手补全。</span>
          </div>
          <div class="nutrition-editor">
            <el-input-number v-model="creatorForm.nutrition.energy" :min="0" :max="5000" :precision="1" placeholder="热量" />
            <el-input-number v-model="creatorForm.nutrition.protein" :min="0" :max="500" :precision="1" placeholder="蛋白质" />
            <el-input-number v-model="creatorForm.nutrition.fat" :min="0" :max="500" :precision="1" placeholder="脂肪" />
            <el-input-number v-model="creatorForm.nutrition.carbohydrate" :min="0" :max="500" :precision="1" placeholder="碳水" />
          </div>
        </div>
      </el-form>

      <template #footer>
        <div class="dialog-actions">
          <el-button @click="creatorVisible = false">取消</el-button>
          <el-button type="primary" :loading="creatingRecipe" @click="submitCreatorRecipe">保存菜谱</el-button>
        </div>
      </template>
    </el-dialog>
    </RefreshFrame>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { notifyActionError, notifyActionSuccess, notifyLoadError, notifyWarning } from "../lib/feedback";
import { useRouter } from "vue-router";
import RecipeDetailDialog from "../components/RecipeDetailDialog.vue";
import { createRecipe, explainRecommendation, favoriteRecipe, listFavoriteRecipes, listRecipes, unfavoriteRecipe } from "../api/recipes";
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
const creatorVisible = ref(false);
const creatingRecipe = ref(false);
const creatorForm = reactive({
  title: "",
  description: "",
  meal_type: "lunch",
  servings: 1,
  portion_size: "1 份",
  difficulty: "easy",
  prep_time_minutes: 10,
  cook_time_minutes: 15,
  ingredients: [{ ingredient_name: "", amount: 1, unit: "份", is_main: true }],
  steps: [{ content: "" }],
  nutrition: {
    energy: null as number | null,
    protein: null as number | null,
    fat: null as number | null,
    carbohydrate: null as number | null,
  },
});

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
    return "先建立一个重点目标，系统会更容易推荐适合你当前状态的菜谱。";
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
    return "先上传一两个你常吃的菜谱，后面的记录、收藏和报表都会更顺手。";
  }
  return "试试切换场景、放宽关键词，或回到“全部”。";
});
const emptyActionLabel = computed(() => {
  if (!recipes.value.length && !hasActiveFilters.value) {
    return "上传第一道菜谱";
  }
  return hasActiveFilters.value ? "重置筛选" : "刷新菜谱";
});

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
    if (!recipes.value.length) {
      openCreator();
      return;
    }
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

function resetCreatorForm() {
  creatorForm.title = "";
  creatorForm.description = "";
  creatorForm.meal_type = "lunch";
  creatorForm.servings = 1;
  creatorForm.portion_size = "1 份";
  creatorForm.difficulty = "easy";
  creatorForm.prep_time_minutes = 10;
  creatorForm.cook_time_minutes = 15;
  creatorForm.ingredients = [{ ingredient_name: "", amount: 1, unit: "份", is_main: true }];
  creatorForm.steps = [{ content: "" }];
  creatorForm.nutrition.energy = null;
  creatorForm.nutrition.protein = null;
  creatorForm.nutrition.fat = null;
  creatorForm.nutrition.carbohydrate = null;
}

function openCreator() {
  resetCreatorForm();
  creatorVisible.value = true;
}

function addCreatorIngredient() {
  creatorForm.ingredients.push({ ingredient_name: "", amount: 1, unit: "份", is_main: false });
}

function removeCreatorIngredient(index: number) {
  if (creatorForm.ingredients.length === 1) {
    return;
  }
  creatorForm.ingredients.splice(index, 1);
}

function addCreatorStep() {
  creatorForm.steps.push({ content: "" });
}

function removeCreatorStep(index: number) {
  if (creatorForm.steps.length === 1) {
    return;
  }
  creatorForm.steps.splice(index, 1);
}

async function submitCreatorRecipe() {
  if (!creatorForm.title.trim()) {
    notifyWarning("请先填写菜谱名称");
    return;
  }

  const ingredients = creatorForm.ingredients
    .map((item) => ({
      ingredient_name: item.ingredient_name.trim(),
      amount: Number(item.amount || 0),
      unit: item.unit.trim() || "份",
      is_main: Boolean(item.is_main),
    }))
    .filter((item) => item.ingredient_name);

  const steps = creatorForm.steps
    .map((item, index) => ({ step_no: index + 1, content: item.content.trim() }))
    .filter((item) => item.content);

  if (!ingredients.length) {
    notifyWarning("请至少填写一个食材");
    return;
  }
  if (!steps.length) {
    notifyWarning("请至少填写一个步骤");
    return;
  }

  const nutritionSummary = [creatorForm.nutrition.energy, creatorForm.nutrition.protein, creatorForm.nutrition.fat, creatorForm.nutrition.carbohydrate].some((value) => value != null)
    ? {
        per_serving_energy: creatorForm.nutrition.energy,
        per_serving_protein: creatorForm.nutrition.protein,
        per_serving_fat: creatorForm.nutrition.fat,
        per_serving_carbohydrate: creatorForm.nutrition.carbohydrate,
      }
    : undefined;

  try {
    creatingRecipe.value = true;
    const response = await createRecipe({
      title: creatorForm.title.trim(),
      description: creatorForm.description.trim(),
      meal_type: creatorForm.meal_type,
      servings: creatorForm.servings || 1,
      portion_size: creatorForm.portion_size.trim() || "1 份",
      difficulty: creatorForm.difficulty,
      prep_time_minutes: creatorForm.prep_time_minutes,
      cook_time_minutes: creatorForm.cook_time_minutes,
      ingredients,
      steps,
      nutrition_input: nutritionSummary,
      cuisine_tags: ["用户上传"],
    });
    const createdRecipe = response?.data ?? response;
    if (createdRecipe?.id) {
      recipes.value = [createdRecipe, ...recipes.value.filter((item) => Number(item.id) !== Number(createdRecipe.id))];
      keyword.value = "";
      mealFilter.value = "all";
      sceneFilter.value = "all";
      sortMode.value = "smart";
      favoriteOnly.value = false;
    }
    creatorVisible.value = false;
    notifyActionSuccess("菜谱已上传");
    loadRecipes().catch(() => undefined);
  } catch {
    notifyActionError("上传菜谱");
  } finally {
    creatingRecipe.value = false;
  }
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
.tag-row,
.creator-strip,
.creator-actions,
.section-head,
.dialog-actions {
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
.quick-picks p,
.creator-strip p {
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
.creator-strip,
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

.creator-copy {
  flex: 1;
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

.creator-form {
  display: grid;
  gap: 16px;
}

.creator-section {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.section-head strong {
  font-size: 16px;
}

.section-head span {
  color: #5a7a8a;
  font-size: 13px;
  line-height: 1.6;
}

.creator-row,
.creator-step-row,
.nutrition-editor {
  display: grid;
  gap: 10px;
}

.creator-row {
  grid-template-columns: minmax(0, 2fr) 120px 120px 100px auto;
  align-items: center;
}

.creator-step-row {
  grid-template-columns: 88px minmax(0, 1fr) auto;
  align-items: flex-start;
}

.nutrition-editor {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.step-index {
  padding-top: 10px;
  color: #476072;
  font-size: 13px;
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
  .focus-strip,
  .creator-strip,
  .creator-actions,
  .section-head,
  .dialog-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .creator-row,
  .creator-step-row,
  .nutrition-editor {
    grid-template-columns: 1fr;
  }
}
</style>
