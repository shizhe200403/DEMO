<template>
  <section class="dashboard">
    <div class="hero">
      <div class="hero-copy">
        <p class="tag">Today</p>
        <h2>推荐、记录、分析已经连成闭环。</h2>
        <p class="desc">
          当前展示的是你最近的推荐菜谱、基础营养分析和目标概览。后续接入外部营养库后，这里还能直接显示食材补全结果。
        </p>
      </div>

      <div class="summary-grid">
        <article>
          <span>状态</span>
          <strong>{{ auth.user?.status || "active" }}</strong>
        </article>
        <article>
          <span>BMI</span>
          <strong>{{ nutritionSummary.bmi ?? "-" }}</strong>
        </article>
        <article>
          <span>提示</span>
          <strong>{{ nutritionSummary.goal_hint || "保持均衡饮食" }}</strong>
        </article>
        <article>
          <span>热量目标</span>
          <strong>{{ nutritionSummary.calorie_target }}</strong>
        </article>
        <article>
          <span>蛋白目标</span>
          <strong>{{ nutritionSummary.protein_target }}</strong>
        </article>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <h3>推荐菜谱</h3>
        <span>{{ recommendations.length }} 条</span>
      </div>
      <div class="recommend-list">
        <article v-for="item in recommendations" :key="item.recipe_id" @click="showReason(item.recipe_id)">
          <div class="row">
            <strong>{{ item.title }}</strong>
            <span>{{ item.score.toFixed(2) }}</span>
          </div>
          <p>{{ item.reason_text }}</p>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useAuthStore } from "../stores/auth";
import { explainRecommendation, listRecommendations } from "../api/recipes";
import { getMe } from "../api/auth";
import { trackEvent } from "../api/behavior";
import { nutritionAnalysis } from "../api/nutrition";

const auth = useAuthStore();
const recommendations = ref<Array<{ recipe_id: number; title: string; score: number; reason_text: string }>>([]);
const nutritionSummary = reactive({
  bmi: "-",
  goal_hint: "",
  calorie_target: "-",
  protein_target: "-",
});

async function loadDashboard() {
  try {
    const [meResult, recommendationResult, nutritionResult] = await Promise.allSettled([
      getMe(),
      listRecommendations(),
      nutritionAnalysis(),
    ]);

    const meResponse = meResult.status === "fulfilled" ? meResult.value : null;
    const recommendationResponse = recommendationResult.status === "fulfilled" ? recommendationResult.value : null;
    const nutritionResponse = nutritionResult.status === "fulfilled" ? nutritionResult.value : null;

    if (!meResponse && !recommendationResponse && !nutritionResponse) {
      throw new Error("dashboard load failed");
    }

    auth.user = meResponse?.data?.data ?? null;

    const profile = meResponse?.data?.data?.profile;
    const height = profile?.height_cm ? Number(profile.height_cm) : 0;
    const weight = profile?.weight_kg ? Number(profile.weight_kg) : 0;
    if (height > 0 && weight > 0) {
      nutritionSummary.bmi = (weight / ((height / 100) * (height / 100))).toFixed(1);
    }

    const health = meResponse?.data?.data?.health_condition;
    if (health?.has_diabetes) {
      nutritionSummary.goal_hint = "优先控制碳水与添加糖";
    } else if (health?.has_hypertension) {
      nutritionSummary.goal_hint = "优先控制钠摄入";
    } else if (health?.has_hyperlipidemia) {
      nutritionSummary.goal_hint = "优先控制脂肪摄入";
    } else {
      nutritionSummary.goal_hint = "保持均衡饮食";
    }

    const nutritionData = nutritionResponse?.data?.data;
    nutritionSummary.calorie_target = nutritionData?.calorie_target ?? "-";
    nutritionSummary.protein_target = nutritionData?.protein_target ?? "-";

    recommendations.value = recommendationResponse?.data?.data || [];
    trackEvent({ behavior_type: "view", context_scene: "home" }).catch(() => undefined);
  } catch (error) {
    ElMessage.error("加载首页数据失败");
  }
}

onMounted(loadDashboard);

async function showReason(recipeId: number) {
  try {
    const response = await explainRecommendation(recipeId);
    ElMessage.info(response.data?.data?.reason_text || "暂无推荐理由");
  } catch (error) {
    ElMessage.error("获取推荐理由失败");
  }
}
</script>

<style scoped>
.dashboard {
  display: grid;
  gap: 20px;
}

.hero {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 20px;
}

.hero-copy,
.panel {
  padding: 28px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.8);
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
  font-size: clamp(30px, 4vw, 52px);
  line-height: 1.05;
}

.desc {
  margin: 14px 0 0;
  color: #476072;
  line-height: 1.75;
}

.summary-grid {
  display: grid;
  gap: 14px;
}

.summary-grid article,
.recommend-list article {
  padding: 18px;
  border-radius: 20px;
  background: rgba(247, 251, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.06);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.recommend-list article:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(15, 30, 39, 0.08);
}

.summary-grid span,
.panel-header span {
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #5a7a8a;
}

.summary-grid strong {
  display: block;
  margin-top: 6px;
  font-size: 22px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.panel-header h3 {
  margin: 0;
  font-size: 22px;
}

.recommend-list {
  display: grid;
  gap: 12px;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.row strong {
  font-size: 18px;
}

.row span {
  font-weight: 700;
  color: #173042;
}

.recommend-list p {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.65;
}

@media (max-width: 960px) {
  .hero {
    grid-template-columns: 1fr;
  }
}
</style>
