<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Recipe Library</p>
        <h2>菜谱库</h2>
      </div>
      <el-button @click="loadRecipes">刷新</el-button>
    </div>

    <div class="grid">
      <article v-for="recipe in recipes" :key="recipe.id">
        <strong>{{ recipe.title }}</strong>
        <p>{{ recipe.description || "暂无描述" }}</p>
        <div class="meta">
          <span>{{ recipe.meal_type || "all-day" }}</span>
          <span>{{ recipe.difficulty || "unknown" }}</span>
          <span>{{ recipe.cook_time_minutes ?? "-" }} min</span>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { listRecipes } from "../api/recipes";
import { trackEvent } from "../api/behavior";

const recipes = ref<any[]>([]);

async function loadRecipes() {
  try {
    const response = await listRecipes();
    recipes.value = response.data?.results ?? response.data?.data?.items ?? response.data?.data ?? [];
    trackEvent({ behavior_type: "view", context_scene: "recipes" }).catch(() => undefined);
  } catch (error) {
    ElMessage.error("加载菜谱失败");
  }
}

onMounted(loadRecipes);
</script>

<style scoped>
.page {
  padding: 28px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
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

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}

.grid article {
  padding: 18px;
  border-radius: 20px;
  background: rgba(247, 251, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.grid strong {
  display: block;
  font-size: 18px;
}

.grid p {
  margin: 10px 0;
  line-height: 1.6;
  color: #476072;
}

.meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.meta span {
  padding: 6px 10px;
  border-radius: 999px;
  background: #e8f1f7;
  color: #24566a;
  font-size: 12px;
}
</style>
