<template>
  <el-dialog :model-value="modelValue" width="760px" :title="detail?.title || '菜谱详情'" @close="emit('update:modelValue', false)">
    <PageStateBlock
      v-if="loading"
      tone="loading"
      title="正在加载菜谱详情"
      description="系统正在读取食材、营养和做法信息。"
      compact
    />
    <div v-else-if="detail" class="detail">
      <div class="hero">
        <div>
          <p class="description">{{ detail.description || "暂无描述" }}</p>
          <div class="meta">
            <span>{{ mealTypeLabel(detail.meal_type) }}</span>
            <span>{{ difficultyLabel(detail.difficulty) }}</span>
            <span>{{ detail.cook_time_minutes ?? "-" }} 分钟</span>
            <span>{{ detail.servings ?? 1 }} 份</span>
          </div>
        </div>
        <div class="hero-actions">
          <el-button text :loading="favoriteLoading" @click="toggleFavorite">
            {{ favorited ? "取消收藏" : "加入收藏" }}
          </el-button>
          <el-button type="primary" plain @click="emit('add-to-record', detail)">加入记录</el-button>
        </div>
      </div>

      <div v-if="reasonText" class="reason-box">
        <span>推荐理由</span>
        <p>{{ reasonText }}</p>
      </div>

      <div class="section-grid">
        <article>
          <h4>营养概览</h4>
          <div v-if="detail.nutrition_summary" class="nutrition-grid">
            <div>
              <span>热量</span>
              <strong>{{ detail.nutrition_summary.per_serving_energy ?? 0 }} kcal</strong>
            </div>
            <div>
              <span>蛋白质</span>
              <strong>{{ detail.nutrition_summary.per_serving_protein ?? 0 }} g</strong>
            </div>
            <div>
              <span>脂肪</span>
              <strong>{{ detail.nutrition_summary.per_serving_fat ?? 0 }} g</strong>
            </div>
            <div>
              <span>碳水</span>
              <strong>{{ detail.nutrition_summary.per_serving_carbohydrate ?? 0 }} g</strong>
            </div>
            <template v-if="detail.nutrition_summary.per_serving_fiber != null || detail.nutrition_summary.per_serving_sodium != null">
              <div v-if="detail.nutrition_summary.per_serving_fiber != null">
                <span>膳食纤维</span>
                <strong>{{ detail.nutrition_summary.per_serving_fiber }} g</strong>
              </div>
              <div v-if="detail.nutrition_summary.per_serving_sodium != null">
                <span>钠</span>
                <strong>{{ detail.nutrition_summary.per_serving_sodium }} mg</strong>
              </div>
              <div v-if="detail.nutrition_summary.per_serving_calcium != null">
                <span>钙</span>
                <strong>{{ detail.nutrition_summary.per_serving_calcium }} mg</strong>
              </div>
              <div v-if="detail.nutrition_summary.per_serving_iron != null">
                <span>铁</span>
                <strong>{{ detail.nutrition_summary.per_serving_iron }} mg</strong>
              </div>
              <div v-if="detail.nutrition_summary.per_serving_vitamin_a != null">
                <span>维生素 A</span>
                <strong>{{ detail.nutrition_summary.per_serving_vitamin_a }} μgRAE</strong>
              </div>
              <div v-if="detail.nutrition_summary.per_serving_vitamin_c != null">
                <span>维生素 C</span>
                <strong>{{ detail.nutrition_summary.per_serving_vitamin_c }} mg</strong>
              </div>
            </template>
          </div>
          <PageStateBlock v-else tone="info" title="暂无营养汇总数据" compact />
        </article>

        <article>
          <h4>食材</h4>
          <ul v-if="detail.ingredients?.length" class="list">
            <li v-for="item in detail.ingredients" :key="item.id">
              {{ item.ingredient?.canonical_name || "未知食材" }} · {{ item.amount }} {{ item.unit }}
            </li>
          </ul>
          <PageStateBlock v-else tone="info" title="暂无食材清单" compact />
        </article>
      </div>

      <article class="steps-section">
        <h4>做法步骤</h4>
        <ol v-if="detail.steps?.length" class="steps">
          <li v-for="step in detail.steps" :key="step.id">
            <strong>步骤 {{ step.step_no }}</strong>
            <p>{{ step.content }}</p>
          </li>
        </ol>
        <PageStateBlock v-else tone="info" title="暂无步骤说明" compact />
      </article>
    </div>
    <PageStateBlock v-else tone="empty" title="未找到该菜谱详情" description="可以返回列表重新选择，或稍后再试。" compact />
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import PageStateBlock from "./PageStateBlock.vue";
import { notifyActionError, notifyActionSuccess, notifyLoadError } from "../lib/feedback";
import { favoriteRecipe, getRecipeDetail, unfavoriteRecipe } from "../api/recipes";

const props = defineProps<{
  modelValue: boolean;
  recipeId: number | null;
  recipe?: Record<string, any> | null;
  reasonText?: string;
  favorited?: boolean;
}>();

const emit = defineEmits<{
  (event: "update:modelValue", value: boolean): void;
  (event: "favorite-change", payload: { recipeId: number; favorited: boolean }): void;
  (event: "add-to-record", recipe: Record<string, any>): void;
}>();

const loading = ref(false);
const favoriteLoading = ref(false);
const detail = ref<Record<string, any> | null>(null);

watch(
  () => [props.modelValue, props.recipeId],
  async ([visible, recipeId]) => {
    if (!visible || !recipeId) {
      return;
    }

    detail.value = props.recipe ?? null;
    try {
      loading.value = true;
      const response = await getRecipeDetail(recipeId);
      detail.value = response.data ?? null;
    } catch (error) {
      detail.value = props.recipe ?? null;
      notifyLoadError("菜谱详情");
    } finally {
      loading.value = false;
    }
  },
  { immediate: true },
);

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

async function toggleFavorite() {
  if (!props.recipeId) {
    return;
  }

  try {
    favoriteLoading.value = true;
    if (props.favorited) {
      await unfavoriteRecipe(props.recipeId);
      emit("favorite-change", { recipeId: props.recipeId, favorited: false });
      notifyActionSuccess("已取消收藏");
      return;
    }
    await favoriteRecipe(props.recipeId);
    emit("favorite-change", { recipeId: props.recipeId, favorited: true });
    notifyActionSuccess("已加入收藏");
  } catch (error) {
    notifyActionError("收藏操作");
  } finally {
    favoriteLoading.value = false;
  }
}
</script>

<style scoped>
.detail {
  display: grid;
  gap: 18px;
}

.hero,
.hero-actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.description,
.reason-box p,
.steps p,
.state {
  margin: 0;
  color: #476072;
  line-height: 1.7;
}

.meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.meta span,
.reason-box span,
.nutrition-grid span {
  padding: 6px 10px;
  border-radius: 999px;
  background: #e8f1f7;
  color: #24566a;
  font-size: 12px;
}

.reason-box,
.section-grid article,
.steps-section {
  padding: 18px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.section-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

h4 {
  margin: 0 0 12px;
  font-size: 18px;
}

.nutrition-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.nutrition-grid strong {
  display: block;
  margin-top: 8px;
  font-size: 18px;
}

.list,
.steps {
  margin: 0;
  padding-left: 18px;
  color: #173042;
  display: grid;
  gap: 10px;
}

.steps strong {
  display: block;
  margin-bottom: 4px;
}

@media (max-width: 768px) {
  .hero,
  .hero-actions {
    flex-direction: column;
  }

  .section-grid,
  .nutrition-grid {
    grid-template-columns: 1fr;
  }
}
</style>
