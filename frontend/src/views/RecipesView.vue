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
      <article v-spotlight>
        <span>菜谱总数</span>
        <strong>{{ recipeSummary.total }}</strong>
        <p>当前可浏览的菜谱总量。</p>
      </article>
      <article v-spotlight>
        <span>已收藏</span>
        <strong>{{ recipeSummary.favorites }}</strong>
        <p>已经沉淀为你的个人资产的菜谱数。</p>
      </article>
      <article v-spotlight>
        <span>15 分钟内</span>
        <strong>{{ recipeSummary.quick }}</strong>
        <p>适合工作日快速决策的轻量选择。</p>
      </article>
      <article v-spotlight>
        <span>高蛋白</span>
        <strong>{{ recipeSummary.highProtein }}</strong>
        <p>更适合增肌或补蛋白场景的选择。</p>
      </article>
    </div>

    <div v-spotlight class="focus-strip interactive-focus-strip">
      <div>
        <strong>{{ activeGoal ? `${goalTypeLabel(activeGoal.goal_type)}阶段推荐` : "当前未设置重点目标" }}</strong>
        <p>{{ goalFocusedCopy }}</p>
      </div>
      <el-button v-if="goalSuggestedFilter !== 'all'" plain @click="sceneFilter = goalSuggestedFilter">应用目标筛选</el-button>
    </div>

    <div v-spotlight class="creator-strip interactive-creator-strip">
      <div class="creator-copy">
        <strong>先把自己的菜谱沉淀进系统</strong>
        <p>当前已去掉外部菜谱与外部食物依赖。常吃什么就先上传什么，后面的记录、收藏和报表会更稳定。</p>
      </div>
      <div class="creator-actions">
        <el-button type="primary" @click="openCreator">上传我的菜谱</el-button>
      </div>
    </div>

    <div v-if="recipeFollowUp" ref="recipeFollowUpRef" v-spotlight class="recipe-follow-up">
      <div class="recipe-follow-up-copy">
        <span class="recipe-follow-up-badge">{{ recipeFollowUp.badge }}</span>
        <strong>{{ recipeFollowUp.title }}</strong>
        <p>{{ recipeFollowUp.description }}</p>
        <div v-if="recipeFollowUp.highlights.length" class="recipe-follow-up-highlights">
          <span v-for="item in recipeFollowUp.highlights" :key="item">{{ item }}</span>
        </div>
      </div>
      <div class="recipe-follow-up-actions">
        <el-button
          v-if="recipeFollowUp.showCommonAction"
          :loading="followUpFavoriting"
          type="primary"
          plain
          @click="favoriteFollowUpRecipe"
        >
          {{ recipeFollowUp.commonLabel }}
        </el-button>
        <el-button v-else plain @click="router.push('/favorites')">{{ recipeFollowUp.commonLabel }}</el-button>
        <el-button type="primary" @click="addFollowUpRecipeToRecord">加入今天记录</el-button>
        <el-button plain @click="openCreatorForNext">继续上传</el-button>
        <el-button text @click="dismissRecipeFollowUp">收起</el-button>
      </div>
    </div>

    <PageStateBlock
      tone="info"
      title="AI 图片识别已开放试用"
      description="现在可以先上传一张食物照片，系统会尝试识别食材、份量与营养估算，并回填到菜谱草稿中。识别结果仍建议人工确认。"
      action-label="上传照片识别"
      @action="openCreator"
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

    <div v-if="workbenchPrimaryRecipe" class="decision-workbench">
      <div class="decision-hero">
        <div class="decision-copy">
          <p class="section-kicker">Meal Guide</p>
          <strong>{{ recipeWorkbenchHeadline }}</strong>
          <p>{{ recipeWorkbenchDescription }}</p>
        </div>
        <article v-spotlight class="decision-primary-card interactive-decision-card">
          <div class="card-head">
            <strong>{{ workbenchPrimaryRecipe.title }}</strong>
            <span class="pick-badge">{{ quickPickLabel(workbenchPrimaryRecipe) }}</span>
          </div>
          <p>{{ workbenchPrimaryRecipe.description || footerCopy(workbenchPrimaryRecipe) }}</p>
          <div class="meta">
            <span>{{ mealTypeLabel(workbenchPrimaryRecipe.meal_type) }}</span>
            <span>{{ recipeTimeLabel(workbenchPrimaryRecipe) }}</span>
            <span>{{ recipeProteinLabel(workbenchPrimaryRecipe) }}</span>
          </div>
          <div class="footer-actions">
            <el-button text @click="openDetail(workbenchPrimaryRecipe)">查看详情</el-button>
            <el-button type="primary" plain @click="addToRecord(workbenchPrimaryRecipe)">加入记录</el-button>
          </div>
        </article>
      </div>

      <div v-if="decisionSupportCards.length" class="decision-support-grid">
        <article v-for="item in decisionSupportCards" :key="item.key" v-spotlight class="decision-support-card interactive-decision-card">
          <span class="support-label">{{ item.label }}</span>
          <strong>{{ item.recipe.title }}</strong>
          <p>{{ item.copy }}</p>
          <div class="meta">
            <span>{{ mealTypeLabel(item.recipe.meal_type) }}</span>
            <span>{{ recipeTimeLabel(item.recipe) }}</span>
            <span>{{ recipeProteinLabel(item.recipe) }}</span>
          </div>
          <div class="footer-actions">
            <el-button text @click="openDetail(item.recipe)">查看详情</el-button>
            <el-button type="primary" plain @click="addToRecord(item.recipe)">加入记录</el-button>
          </div>
        </article>
      </div>
    </div>

    <div v-if="quickPicks.length" class="quick-picks">
      <article v-for="recipe in quickPicks" :key="recipe.id" v-spotlight class="interactive-quick-pick">
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
      <article v-for="recipe in filteredRecipes" :key="recipe.id" v-spotlight class="interactive-recipe-card">
        <div v-if="recipe.cover_image_url" class="recipe-cover">
          <img :src="recipe.cover_image_url" :alt="recipe.title" />
        </div>
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
          <span>{{ recipeTimeLabel(recipe) }}</span>
        </div>
        <div class="tag-row">
          <span v-if="isFavorited(recipe.id)" class="feature-tag is-favorite">已收藏</span>
          <span v-if="isQuickRecipe(recipe)" class="feature-tag is-quick">快手</span>
          <span v-if="isHighProtein(recipe)" class="feature-tag is-protein">高蛋白</span>
          <span v-if="isLightRecipe(recipe)" class="feature-tag is-light">轻负担</span>
          <span v-if="matchesGoal(recipe)" class="feature-tag is-goal">适合当前目标</span>
        </div>
        <div class="decision-note">
          <strong>{{ recipeDecisionLabel(recipe) }}</strong>
          <p>{{ footerCopy(recipe) }}</p>
        </div>
        <div class="nutrition" v-if="recipe.nutrition_summary">
          <span>{{ recipeEnergyLabel(recipe) }}</span>
          <span>{{ recipeProteinLabel(recipe) }}</span>
        </div>
        <div class="footer-actions">
          <el-button text @click="openDetail(recipe)">查看详情</el-button>
          <el-button type="primary" plain @click="addToRecord(recipe)">加入记录</el-button>
          <el-button text @click="openEditor(recipe)">编辑</el-button>
          <el-button text @click="triggerCoverUpload(recipe)">上传封面</el-button>
          <el-button text type="danger" :loading="deletingId === recipe.id" @click="handleDelete(recipe)">删除</el-button>
        </div>
        <input ref="coverInput" type="file" accept="image/*" style="display:none" @change="onCoverChange" />
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
    <el-dialog v-model="creatorVisible" width="760px" :title="editingRecipeId ? '编辑菜谱' : '上传菜谱'">
      <el-form label-position="top" class="creator-form">
        <div class="creator-section vision-section">
          <div class="section-head">
            <div>
              <strong>AI 图片识别</strong>
              <span>上传一张食物照片，系统会尝试识别菜品、主要食材和每份营养信息，并回填到下方表单。</span>
            </div>
            <div class="vision-actions">
              <input
                ref="foodImageInput"
                class="hidden-file-input"
                type="file"
                accept="image/*"
                @change="handleFoodImageSelected"
              />
              <el-button plain @click="foodImageInput?.click()">
                {{ selectedFoodImageName ? "重新选择照片" : "选择照片" }}
              </el-button>
              <el-button
                type="primary"
                plain
                :disabled="!selectedFoodImage || analyzingFoodImage"
                :loading="analyzingFoodImage"
                @click="runFoodImageAnalysis"
              >
                AI 识别并填充
              </el-button>
            </div>
          </div>

          <div v-if="selectedFoodImagePreview || foodImageAnalysis" v-spotlight class="vision-result">
            <img v-if="selectedFoodImagePreview" :src="selectedFoodImagePreview" alt="待识别食物照片预览" class="vision-preview" />
            <div class="vision-copy">
              <strong>{{ foodImageAnalysis?.title || selectedFoodImageName || "已选择待识别图片" }}</strong>
              <p v-if="foodImageAnalysis?.description">{{ foodImageAnalysis.description }}</p>
              <p v-else-if="selectedFoodImageName">已选择图片：{{ selectedFoodImageName }}</p>
              <div v-if="foodImageAnalysis" class="vision-tags">
                <span>{{ mealTypeLabel(foodImageAnalysis.meal_type) }}</span>
                <span>{{ `${Math.max(1, Math.round(Number(foodImageAnalysis.servings || 1)))} 份` }}</span>
                <span v-if="foodImageAnalysis.nutrition?.energy != null">{{ `${foodImageAnalysis.nutrition.energy} kcal/份` }}</span>
              </div>
              <p v-if="foodImageAnalysis?.confidence_notes" class="vision-note">
                {{ foodImageAnalysis.confidence_notes }}
              </p>
              <p v-if="foodImageAnalysis?.warning" class="vision-note is-warning">
                {{ foodImageAnalysis.warning }}
              </p>
            </div>
          </div>
        </div>

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
          <div v-for="(ingredient, index) in creatorForm.ingredients" :key="`ingredient-${index}`" v-spotlight class="creator-row">
            <el-input class="ingredient-name-field" v-model.trim="ingredient.ingredient_name" placeholder="食材名称，例如：鸡胸肉" />
            <el-input-number
              class="ingredient-amount-field"
              v-model="ingredient.amount"
              :min="0"
              :max="9999"
              :precision="1"
              controls-position="right"
            />
            <el-input class="ingredient-unit-field" v-model.trim="ingredient.unit" placeholder="单位，例如：g / 个 / 份" />
            <el-switch class="ingredient-main-switch" v-model="ingredient.is_main" active-text="主食材" />
            <el-button class="ingredient-remove-button" text type="danger" :disabled="creatorForm.ingredients.length === 1" @click="removeCreatorIngredient(index)">删除</el-button>
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
          <el-button plain :disabled="creatorAiDisabled" @click="openAssistantForRecipeDraft">让 AI 帮我补全这道菜</el-button>
          <el-button @click="creatorVisible = false">取消</el-button>
          <el-button type="primary" :loading="creatingRecipe" @click="submitCreatorRecipe">{{ editingRecipeId ? '保存修改' : '保存菜谱' }}</el-button>
        </div>
      </template>
    </el-dialog>
    </RefreshFrame>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { ElMessageBox } from "element-plus";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { extractApiErrorMessage, notifyActionError, notifyActionSuccess, notifyErrorMessage, notifyLoadError, notifyWarning } from "../lib/feedback";
import { useRouter } from "vue-router";
import RecipeDetailDialog from "../components/RecipeDetailDialog.vue";
import { createRecipe, explainRecommendation, favoriteRecipe, listFavoriteRecipes, listRecipes, unfavoriteRecipe, updateRecipe, deleteRecipe, uploadRecipeCover } from "../api/recipes";
import { analyzeFoodImage } from "../api/assistant";
import { trackEvent } from "../api/behavior";
import { listHealthGoals } from "../api/goals";

type FoodImageAnalysis = {
  title?: string;
  description?: string;
  meal_type: "breakfast" | "lunch" | "dinner" | "snack";
  servings?: number | null;
  portion_size?: string;
  ingredients?: Array<{
    ingredient_name: string;
    amount?: number | null;
    unit?: string;
    is_main?: boolean;
  }>;
  steps?: string[];
  nutrition?: {
    energy?: number | null;
    protein?: number | null;
    fat?: number | null;
    carbohydrate?: number | null;
  };
  confidence_notes?: string;
  warning?: string;
};

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
const editingRecipeId = ref<number | null>(null);
const deletingId = ref<number | null>(null);
const coverInput = ref<HTMLInputElement | null>(null);
const coverUploadingRecipeId = ref<number | null>(null);
const followUpFavoriting = ref(false);
const latestSavedRecipe = ref<null | { id: number; title: string; meal_type?: string; source_type?: string; mode: "create" | "update" }>(null);
const recipeFollowUpRef = ref<HTMLElement | null>(null);
const analyzingFoodImage = ref(false);
const foodImageInput = ref<HTMLInputElement | null>(null);
const selectedFoodImage = ref<File | null>(null);
const selectedFoodImageName = ref("");
const selectedFoodImagePreview = ref("");
const foodImageAnalysis = ref<FoodImageAnalysis | null>(null);
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
const creatorAiDisabled = computed(() => {
  return !creatorForm.title.trim() && !creatorForm.description.trim() && !creatorForm.ingredients.some((item) => item.ingredient_name.trim());
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
const currentMealFocusType = computed<"breakfast" | "lunch" | "dinner" | "snack">(() => {
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
});
const workbenchPrimaryRecipe = computed(() => {
  const sameMeal = filteredRecipes.value.filter((recipe) => recipe.meal_type === currentMealFocusType.value);
  return sameMeal[0] ?? filteredRecipes.value[0] ?? null;
});
const decisionSupportCards = computed(() => {
  const pickedIds = new Set<number>();
  if (workbenchPrimaryRecipe.value?.id) {
    pickedIds.add(Number(workbenchPrimaryRecipe.value.id));
  }

  const nextDistinct = (items: Array<Record<string, any>>) => items.find((item) => !pickedIds.has(Number(item.id))) ?? null;
  const cards: Array<{ key: string; label: string; copy: string; recipe: Record<string, any> }> = [];
  const register = (key: string, label: string, copy: string, recipe: Record<string, any> | null) => {
    if (!recipe) {
      return;
    }
    const recipeId = Number(recipe.id);
    if (pickedIds.has(recipeId)) {
      return;
    }
    pickedIds.add(recipeId);
    cards.push({ key, label, copy, recipe });
  };

  register(
    "quick",
    "现在最省事",
    "如果你只是想尽快定一餐，优先看准备时间更短的选项。",
    nextDistinct([...filteredRecipes.value].filter((recipe) => isQuickRecipe(recipe)).sort((left, right) => compareRecipesByMode(left, right, "time"))),
  );
  register(
    "protein",
    "补蛋白优先",
    "如果今天更想补蛋白，先看每份蛋白更高的几道菜。",
    nextDistinct([...filteredRecipes.value].filter((recipe) => isHighProtein(recipe)).sort((left, right) => compareRecipesByMode(left, right, "protein"))),
  );
  register(
    "light",
    "轻一点",
    "如果这一餐想吃得轻一点，先看热量更低、负担更小的选择。",
    nextDistinct([...filteredRecipes.value].filter((recipe) => isLightRecipe(recipe)).sort((left, right) => compareRecipesByMode(left, right, "energy"))),
  );

  return cards.slice(0, 3);
});
const recipeWorkbenchHeadline = computed(() => {
  if (!filteredRecipes.value.length) {
    return "先放宽筛选，系统才能帮你缩小范围";
  }
  if (workbenchPrimaryRecipe.value?.meal_type === currentMealFocusType.value) {
    return `现在更适合先看${mealTypeLabel(currentMealFocusType.value)}候选`;
  }
  return "当前筛选结果里，先从这道开始最省事";
});
const recipeWorkbenchDescription = computed(() => {
  if (!filteredRecipes.value.length) {
    return "试着切回“全部”或放宽关键词，先让结果集恢复到可决策状态。";
  }
  if (matchesGoal(workbenchPrimaryRecipe.value || {})) {
    return "这道菜同时贴近你当前目标和当前时段，适合作为第一决策位。";
  }
  if (workbenchPrimaryRecipe.value?.meal_type === currentMealFocusType.value) {
    return `当前时段更像在决定${mealTypeLabel(currentMealFocusType.value)}，系统优先把更贴近这一餐次的菜放到前面。`;
  }
  return "当前结果里这道菜综合时间成本、目标匹配和营养结构更适合先看。";
});
const latestSavedRecipeDetail = computed(() => {
  if (!latestSavedRecipe.value) {
    return null;
  }
  return recipes.value.find((item) => Number(item.id) === Number(latestSavedRecipe.value?.id)) ?? latestSavedRecipe.value;
});
const recipeFollowUp = computed(() => {
  if (!latestSavedRecipe.value) {
    return null;
  }
  const savedMeta = latestSavedRecipe.value;
  const recipe = latestSavedRecipeDetail.value || savedMeta;
  const alreadyFavorited = isFavorited(Number(recipe.id));
  const followUpHighlights = [
    `${mealTypeLabel(recipe.meal_type || currentMealFocusType.value)}候选`,
    isQuickRecipe(recipe) ? "适合快手决策" : recipeTimeLabel(recipe),
    alreadyFavorited ? "已进入常用收藏" : "设为常用后更容易在首页和记录页出现",
  ];

  if (isHighProtein(recipe)) {
    followUpHighlights[1] = "高蛋白优先";
  } else if (isLightRecipe(recipe)) {
    followUpHighlights[1] = "轻负担选择";
  }

  return {
    badge: savedMeta.mode === "update" ? "已更新" : "已上传",
    title: savedMeta.mode === "update" ? `菜谱「${recipe.title}」已更新` : `菜谱「${recipe.title}」已进入你的菜谱库`,
    description:
      savedMeta.mode === "update"
        ? "现在可以直接把这道菜加入今天记录；如果它会反复吃到，顺手设为常用，后面在首页和记录页都会更容易复用。"
        : "下一步最自然的动作是先设为常用，或者直接放进今天的一餐里，不要让这次录入停在表单里。",
    highlights: followUpHighlights,
    showCommonAction: !alreadyFavorited,
    commonLabel: alreadyFavorited ? "去常用区查看" : "设为常用",
  };
});
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

function compareRecipesByMode(a: Record<string, any>, b: Record<string, any>, mode: "time" | "protein" | "energy") {
  if (mode === "time") {
    return numericValue(a.cook_time_minutes) - numericValue(b.cook_time_minutes);
  }
  if (mode === "protein") {
    return numericValue(b.nutrition_summary?.per_serving_protein) - numericValue(a.nutrition_summary?.per_serving_protein);
  }
  return numericValue(a.nutrition_summary?.per_serving_energy) - numericValue(b.nutrition_summary?.per_serving_energy);
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
  if (recipe.meal_type === currentMealFocusType.value) {
    return `更像${mealTypeLabel(currentMealFocusType.value)}`;
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
  if (recipe.meal_type === currentMealFocusType.value) {
    return `现在更像在决定${mealTypeLabel(currentMealFocusType.value)}，这道菜会更贴近当前场景。`;
  }
  if (isQuickRecipe(recipe)) {
    return "时间成本较低，适合工作日快速决策。";
  }
  if (isHighProtein(recipe)) {
    return "蛋白相对更高，适合需要补蛋白的场景。";
  }
  return "适合作为日常均衡饮食的一部分。";
}

function recipeDecisionLabel(recipe: Record<string, any>) {
  if (matchesGoal(recipe)) {
    return `更贴近${goalTypeLabel(activeGoal.value?.goal_type || "")}目标`;
  }
  if (recipe.meal_type === currentMealFocusType.value) {
    return `当前更适合的${mealTypeLabel(currentMealFocusType.value)}`;
  }
  if (isQuickRecipe(recipe)) {
    return "工作日更省事";
  }
  if (isHighProtein(recipe)) {
    return "适合补蛋白";
  }
  if (isLightRecipe(recipe)) {
    return "整体更轻负担";
  }
  return "日常稳妥选择";
}

function recipeTimeLabel(recipe: Record<string, any>) {
  const minutes = numericValue(recipe.cook_time_minutes);
  return minutes > 0 ? `${minutes} 分钟` : "时间待补充";
}

function recipeProteinLabel(recipe: Record<string, any>) {
  return `${numericValue(recipe.nutrition_summary?.per_serving_protein).toFixed(0)} g 蛋白`;
}

function recipeEnergyLabel(recipe: Record<string, any>) {
  return `${numericValue(recipe.nutrition_summary?.per_serving_energy).toFixed(0)} kcal / 份`;
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
      source: "recipes",
      from_title: recipe.title || "",
    },
  });
}

function dismissRecipeFollowUp() {
  latestSavedRecipe.value = null;
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

function resetFoodImageState() {
  selectedFoodImage.value = null;
  selectedFoodImageName.value = "";
  foodImageAnalysis.value = null;
  if (selectedFoodImagePreview.value) {
    URL.revokeObjectURL(selectedFoodImagePreview.value);
    selectedFoodImagePreview.value = "";
  }
  if (foodImageInput.value) {
    foodImageInput.value.value = "";
  }
}

function openCreator() {
  latestSavedRecipe.value = null;
  resetCreatorForm();
  resetFoodImageState();
  editingRecipeId.value = null;
  creatorVisible.value = true;
}

function openEditor(recipe: Record<string, any>) {
  latestSavedRecipe.value = null;
  resetCreatorForm();
  resetFoodImageState();
  editingRecipeId.value = Number(recipe.id);
  creatorForm.title = recipe.title || "";
  creatorForm.description = recipe.description || "";
  creatorForm.meal_type = recipe.meal_type || "lunch";
  creatorForm.servings = recipe.servings || 1;
  creatorForm.portion_size = recipe.portion_size || "1 份";
  creatorForm.difficulty = recipe.difficulty || "easy";
  creatorForm.prep_time_minutes = recipe.prep_time_minutes || 10;
  creatorForm.cook_time_minutes = recipe.cook_time_minutes || 15;
  if (recipe.ingredients?.length) {
    creatorForm.ingredients = recipe.ingredients.map((item: Record<string, any>) => ({
      ingredient_name: item.ingredient?.canonical_name || item.ingredient_name || "",
      amount: item.amount || 1,
      unit: item.unit || "份",
      is_main: item.is_main || false,
    }));
  }
  if (recipe.steps?.length) {
    creatorForm.steps = recipe.steps.map((item: Record<string, any>) => ({ content: item.content || "" }));
  }
  if (recipe.nutrition_summary) {
    creatorForm.nutrition.energy = recipe.nutrition_summary.per_serving_energy ?? null;
    creatorForm.nutrition.protein = recipe.nutrition_summary.per_serving_protein ?? null;
    creatorForm.nutrition.fat = recipe.nutrition_summary.per_serving_fat ?? null;
    creatorForm.nutrition.carbohydrate = recipe.nutrition_summary.per_serving_carbohydrate ?? null;
  }
  creatorVisible.value = true;
}

function addCreatorIngredient() {
  creatorForm.ingredients.push({ ingredient_name: "", amount: 1, unit: "份", is_main: false });
}

function openCreatorForNext() {
  latestSavedRecipe.value = null;
  openCreator();
}

async function favoriteFollowUpRecipe() {
  if (!latestSavedRecipe.value || isFavorited(latestSavedRecipe.value.id)) {
    return;
  }
  try {
    followUpFavoriting.value = true;
    await favoriteRecipe(latestSavedRecipe.value.id);
    favoriteIds.value = [...favoriteIds.value, latestSavedRecipe.value.id];
    notifyActionSuccess("已加入收藏");
  } catch {
    notifyActionError("收藏操作");
  } finally {
    followUpFavoriting.value = false;
  }
}

function addFollowUpRecipeToRecord() {
  if (!latestSavedRecipe.value) {
    return;
  }
  addToRecord(latestSavedRecipe.value);
}

async function revealRecipeFollowUp() {
  await nextTick();
  recipeFollowUpRef.value?.scrollIntoView({ behavior: "smooth", block: "center" });
}

function openAssistantForRecipeDraft() {
  if (creatorAiDisabled.value) {
    return;
  }

  const ingredients = creatorForm.ingredients
    .filter((item) => item.ingredient_name.trim())
    .map((item) => `${item.ingredient_name.trim()} ${item.amount || 1}${item.unit || "份"}`)
    .join("、");
  const steps = creatorForm.steps
    .map((item, index) => item.content.trim() ? `${index + 1}. ${item.content.trim()}` : "")
    .filter(Boolean)
    .join("；");
  const nutritionLines = [
    creatorForm.nutrition.energy != null ? `热量 ${creatorForm.nutrition.energy} kcal` : "",
    creatorForm.nutrition.protein != null ? `蛋白 ${creatorForm.nutrition.protein} g` : "",
    creatorForm.nutrition.fat != null ? `脂肪 ${creatorForm.nutrition.fat} g` : "",
    creatorForm.nutrition.carbohydrate != null ? `碳水 ${creatorForm.nutrition.carbohydrate} g` : "",
  ].filter(Boolean).join("，");

  const prompt = [
    "请基于我当前正在上传的菜谱草稿，用非常直接、可执行的话告诉我还需要补什么，才能更适合放进饮食系统里。",
    `菜谱名称：${creatorForm.title.trim() || "未填写"}。`,
    `餐次：${mealTypeLabel(creatorForm.meal_type)}。`,
    `描述：${creatorForm.description.trim() || "未填写"}。`,
    `份数与每份说明：${creatorForm.servings} 份，${creatorForm.portion_size.trim() || "未填写"}。`,
    `食材：${ingredients || "未填写"}。`,
    `步骤：${steps || "未填写"}。`,
    `营养信息：${nutritionLines || "未填写"}。`,
    "请输出三部分：1）这道菜现在更适合什么场景；2）最值得补齐的 3 个字段；3）给我一版可以直接放进描述栏的成品文案。",
  ].join("\n");

  router.push({
    path: "/assistant",
    query: {
      source: "recipes_creator_draft",
      prompt,
    },
  });
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

function handleFoodImageSelected(event: Event) {
  const input = event.target as HTMLInputElement | null;
  const file = input?.files?.[0];
  if (!file) {
    return;
  }
  if (!file.type.startsWith("image/")) {
    notifyWarning("请选择图片文件");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    notifyWarning("图片大小不能超过 10MB");
    return;
  }

  if (selectedFoodImagePreview.value) {
    URL.revokeObjectURL(selectedFoodImagePreview.value);
  }

  selectedFoodImage.value = file;
  selectedFoodImageName.value = file.name;
  selectedFoodImagePreview.value = URL.createObjectURL(file);
  foodImageAnalysis.value = null;
}

function applyFoodImageAnalysis(analysis: FoodImageAnalysis) {
  if (analysis.title) {
    creatorForm.title = analysis.title;
  }
  if (analysis.description) {
    creatorForm.description = analysis.description;
  }
  if (analysis.meal_type) {
    creatorForm.meal_type = analysis.meal_type;
  }
  if (analysis.servings != null) {
    creatorForm.servings = Math.max(1, Math.round(Number(analysis.servings || 1)));
  }
  if (analysis.portion_size) {
    creatorForm.portion_size = analysis.portion_size;
  }
  if (analysis.ingredients?.length) {
    creatorForm.ingredients = analysis.ingredients.map((item, index) => ({
      ingredient_name: item.ingredient_name,
      amount: item.amount != null ? Number(item.amount) : 1,
      unit: item.unit || "份",
      is_main: index === 0 ? true : Boolean(item.is_main),
    }));
  }
  if (analysis.steps?.length) {
    creatorForm.steps = analysis.steps.map((content) => ({ content }));
  }
  if (analysis.nutrition) {
    creatorForm.nutrition.energy = analysis.nutrition.energy ?? null;
    creatorForm.nutrition.protein = analysis.nutrition.protein ?? null;
    creatorForm.nutrition.fat = analysis.nutrition.fat ?? null;
    creatorForm.nutrition.carbohydrate = analysis.nutrition.carbohydrate ?? null;
  }
}

async function runFoodImageAnalysis() {
  if (!selectedFoodImage.value) {
    notifyWarning("请先选择一张食物照片");
    return;
  }

  try {
    analyzingFoodImage.value = true;
    const response = await analyzeFoodImage(selectedFoodImage.value);
    const analysis = (response.data ?? response) as FoodImageAnalysis;
    foodImageAnalysis.value = analysis;
    applyFoodImageAnalysis(analysis);
    notifyActionSuccess("已根据照片填充菜谱草稿");
    if (analysis.warning) {
      notifyWarning(analysis.warning);
    }
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "图片识别失败，请稍后重试"));
  } finally {
    analyzingFoodImage.value = false;
  }
}

function triggerCoverUpload(recipe: Record<string, any>) {
  coverUploadingRecipeId.value = Number(recipe.id);
  coverInput.value?.click();
}

async function onCoverChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  const recipeId = coverUploadingRecipeId.value;
  if (!file || !recipeId) return;
  try {
    const res = await uploadRecipeCover(recipeId, file);
    recipes.value = recipes.value.map((r) =>
      Number(r.id) === recipeId ? { ...r, cover_image_url: res.cover_image_url } : r
    );
    notifyActionSuccess("封面已更新");
  } catch {
    notifyActionError("上传封面");
  } finally {
    coverUploadingRecipeId.value = null;
    if (coverInput.value) coverInput.value.value = "";
  }
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
    const payload = {
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
    };
    if (editingRecipeId.value) {
      const response = await updateRecipe(editingRecipeId.value, payload);
      const updated = response?.data ?? response;
      if (updated?.id) {
        recipes.value = recipes.value.map((item) => Number(item.id) === Number(updated.id) ? updated : item);
        latestSavedRecipe.value = {
          id: Number(updated.id),
          title: updated.title || creatorForm.title.trim(),
          meal_type: updated.meal_type || creatorForm.meal_type,
          source_type: updated.source_type,
          mode: "update",
        };
      }
      creatorVisible.value = false;
      notifyActionSuccess("菜谱已更新");
      await loadRecipes();
      await revealRecipeFollowUp();
    } else {
      const response = await createRecipe(payload);
      const createdRecipe = response?.data ?? response;
      if (createdRecipe?.id) {
        recipes.value = [createdRecipe, ...recipes.value.filter((item) => Number(item.id) !== Number(createdRecipe.id))];
        latestSavedRecipe.value = {
          id: Number(createdRecipe.id),
          title: createdRecipe.title || creatorForm.title.trim(),
          meal_type: createdRecipe.meal_type || creatorForm.meal_type,
          source_type: createdRecipe.source_type,
          mode: "create",
        };
        keyword.value = "";
        mealFilter.value = "all";
        sceneFilter.value = "all";
        sortMode.value = "smart";
        favoriteOnly.value = false;
      }
      creatorVisible.value = false;
      notifyActionSuccess("菜谱已上传");
      await loadRecipes();
      await revealRecipeFollowUp();
    }
  } catch {
    notifyActionError("上传菜谱");
  } finally {
    creatingRecipe.value = false;
  }
}

async function handleDelete(recipe: Record<string, any>) {
  try {
    await ElMessageBox.confirm(`确认删除菜谱「${recipe.title}」？`, "删除确认", { type: "warning", confirmButtonText: "删除", cancelButtonText: "取消" });
  } catch {
    return;
  }
  try {
    deletingId.value = Number(recipe.id);
    await deleteRecipe(Number(recipe.id));
    recipes.value = recipes.value.filter((item) => Number(item.id) !== Number(recipe.id));
    if (latestSavedRecipe.value?.id === Number(recipe.id)) {
      latestSavedRecipe.value = null;
    }
    notifyActionSuccess("菜谱已删除");
  } catch {
    notifyActionError("删除菜谱");
  } finally {
    deletingId.value = null;
  }
}

async function openDetail(recipe: Record<string, any>) {
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
onBeforeUnmount(() => {
  if (selectedFoodImagePreview.value) {
    URL.revokeObjectURL(selectedFoodImagePreview.value);
  }
});
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

.interactive-focus-strip,
.interactive-creator-strip,
.interactive-decision-card,
.interactive-quick-pick,
.interactive-recipe-card,
.recipe-follow-up,
.vision-result,
.creator-row {
  transition:
    transform 0.34s cubic-bezier(0.22, 1.2, 0.36, 1),
    box-shadow 0.34s cubic-bezier(0.22, 1, 0.36, 1),
    border-color 0.28s ease,
    background 0.28s ease;
}

.recipe-cover {
  margin: -20px -24px 16px;
  border-radius: 20px 20px 0 0;
  overflow: hidden;
  height: 160px;
}

.recipe-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.interactive-focus-strip:hover,
.interactive-creator-strip:hover,
.interactive-decision-card:hover,
.interactive-quick-pick:hover,
.interactive-recipe-card:hover,
.recipe-follow-up:hover,
.vision-result:hover,
.creator-row:hover {
  transform: translateY(-4px) scale(1.01);
  box-shadow: 0 24px 46px rgba(15, 30, 39, 0.12);
}

.footer-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(16, 34, 42, 0.06);
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
  gap: 16px;
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
  padding: 22px 24px;
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

.section-kicker {
  margin: 0 0 8px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-size: 12px;
  color: #2f6672;
}

.focus-strip {
  align-items: center;
  background:
    radial-gradient(circle at top right, rgba(87, 181, 231, 0.16), transparent 34%),
    rgba(255, 255, 255, 0.88);
}

.creator-copy {
  flex: 1;
}

.creator-strip {
  background:
    radial-gradient(circle at top right, rgba(255, 236, 210, 0.18), transparent 34%),
    rgba(255, 255, 255, 0.9);
}

.recipe-follow-up {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 18px 20px;
  border-radius: 20px;
  background: rgba(224, 247, 238, 0.72);
  border: 1px solid rgba(31, 120, 89, 0.16);
  animation: pop-in-bounce 0.54s cubic-bezier(0.22, 1.2, 0.36, 1);
}

.recipe-follow-up-copy {
  display: grid;
  gap: 8px;
}

.recipe-follow-up-badge {
  justify-self: flex-start;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(31, 120, 89, 0.12);
  color: #1f6a4c;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.recipe-follow-up strong {
  font-size: 18px;
  color: #173042;
}

.recipe-follow-up p {
  margin: 0;
  color: #476072;
  line-height: 1.65;
}

.recipe-follow-up-highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.recipe-follow-up-highlights span {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(31, 120, 89, 0.12);
  color: #1f6a4c;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.recipe-follow-up-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.decision-workbench {
  display: grid;
  gap: 14px;
  padding: 22px 24px;
  border-radius: 22px;
  background:
    radial-gradient(circle at top right, rgba(123, 173, 204, 0.18), transparent 30%),
    linear-gradient(135deg, rgba(250, 252, 255, 0.98), rgba(242, 248, 251, 0.96));
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.decision-hero {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(320px, 1.1fr);
  gap: 16px;
}

.decision-copy strong {
  display: block;
  font-size: 28px;
  line-height: 1.3;
}

.decision-copy p {
  margin: 10px 0 0;
  color: #476072;
  line-height: 1.7;
}

.decision-primary-card,
.decision-support-card,
.decision-note {
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  position: relative;
  overflow: hidden;
}

.decision-primary-card::after,
.decision-support-card::after,
.interactive-quick-pick::after,
.interactive-recipe-card::after {
  content: "";
  position: absolute;
  inset: auto -24% -52% auto;
  width: 150px;
  height: 150px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  pointer-events: none;
}

.decision-support-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.support-label {
  display: inline-flex;
  margin-bottom: 10px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #e8f1f7;
  color: #24566a;
  font-size: 12px;
}

.decision-note {
  margin-top: 14px;
}

.decision-note strong {
  display: block;
  font-size: 16px;
}

.decision-note p {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.6;
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
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
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

.hidden-file-input {
  display: none;
}

.section-head strong {
  font-size: 16px;
}

.section-head span {
  color: #5a7a8a;
  font-size: 13px;
  line-height: 1.6;
}

.vision-section .section-head {
  align-items: center;
}

.vision-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.vision-result {
  display: grid;
  grid-template-columns: 160px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
  padding: 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 12px 28px rgba(15, 30, 39, 0.06);
}

.vision-preview {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  border-radius: 14px;
  background: rgba(232, 241, 247, 0.9);
}

.vision-copy {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.vision-copy p {
  margin: 0;
  color: #476072;
  line-height: 1.6;
}

.vision-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.vision-tags span {
  padding: 6px 10px;
  border-radius: 999px;
  background: #e8f1f7;
  color: #24566a;
  font-size: 12px;
}

.vision-note {
  font-size: 13px;
}

.vision-note.is-warning {
  color: #a35b13;
}

.creator-row,
.creator-step-row,
.nutrition-editor {
  display: grid;
  gap: 10px;
}

.creator-row {
  grid-template-columns: minmax(0, 2.2fr) minmax(148px, 0.9fr) minmax(112px, 0.7fr) max-content auto;
  align-items: center;
  padding: 12px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(16, 34, 42, 0.05);
}

.creator-row > * {
  min-width: 0;
}

.ingredient-main-switch,
.ingredient-remove-button {
  justify-self: start;
}

.creator-row :deep(.el-input),
.creator-row :deep(.el-input-number) {
  width: 100%;
}

.creator-row :deep(.el-input-number .el-input__wrapper) {
  padding-right: 44px;
}

.creator-row :deep(.el-input-number.is-controls-right .el-input__wrapper) {
  padding-left: 12px;
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
  .decision-hero,
  .decision-support-grid,
  .quick-picks {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .summary-grid,
  .grid {
    grid-template-columns: 1fr;
  }

  .head,
  .head-actions,
  .toolbar,
  .card-head,
  .scene-row,
  .focus-strip,
  .creator-strip,
  .recipe-follow-up,
  .decision-workbench,
  .creator-actions,
  .section-head,
  .dialog-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .decision-copy strong {
    font-size: 22px;
  }

  .creator-row,
  .creator-step-row,
  .nutrition-editor,
  .vision-result {
    grid-template-columns: 1fr;
  }

  .recipe-follow-up-actions {
    width: 100%;
    justify-content: stretch;
  }

  .recipe-follow-up-highlights {
    width: 100%;
  }

  .recipe-follow-up-actions :deep(.el-button) {
    width: 100%;
    margin-left: 0;
  }
}
</style>
