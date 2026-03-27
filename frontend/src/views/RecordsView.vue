<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Tracking</p>
        <h2>饮食记录</h2>
      </div>
      <el-select v-model="period" style="width: 140px" @change="loadRecords">
        <el-option label="最近7天" value="week" />
        <el-option label="最近30天" value="month" />
      </el-select>
    </div>

    <div class="card">
      <h3>快速录入</h3>
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
            <el-form-item label="录入方式">
              <el-select v-model="form.source_type" style="width: 100%">
                <el-option label="手动" value="manual" />
                <el-option label="快速添加" value="quick_add" />
                <el-option label="复制昨天" value="copy_yesterday" />
                <el-option label="扫码" value="scan" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="关联菜谱">
              <el-select v-model="form.recipe_id" clearable filterable placeholder="选择菜谱（可选）" style="width: 100%">
                <el-option v-for="recipe in recipeOptions" :key="recipe.id" :label="recipe.title" :value="recipe.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="备注">
              <el-input v-model="form.note" placeholder="例如：公司午餐" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-button type="primary" @click="createRecord">保存记录</el-button>
      </el-form>
    </div>

    <div class="stats">
      <article>
        <span>热量</span>
        <strong>{{ stats.summary?.energy ?? 0 }}</strong>
      </article>
      <article>
        <span>蛋白质</span>
        <strong>{{ stats.summary?.protein ?? 0 }}</strong>
      </article>
      <article>
        <span>脂肪</span>
        <strong>{{ stats.summary?.fat ?? 0 }}</strong>
      </article>
      <article>
        <span>碳水</span>
        <strong>{{ stats.summary?.carbohydrate ?? 0 }}</strong>
      </article>
    </div>

    <div class="list">
      <article v-for="record in records" :key="record.id">
        <strong>{{ record.record_date }} - {{ record.meal_type }}</strong>
        <p>{{ record.note || "无备注" }}</p>
        <p class="muted">
          条目数：{{ record.items?.length || 0 }}
          <span v-if="record.items?.length">
            | 首条：{{ record.items[0].recipe_title || record.items[0].ingredient_name_snapshot || (record.items[0].recipe_id ? `菜谱 #${record.items[0].recipe_id}` : "菜谱记录") }}
          </span>
        </p>
      </article>
    </div>

    <div class="card">
      <h3>趋势明细</h3>
      <div class="trend">
        <article v-for="item in stats.trend" :key="item.date">
          <strong>{{ item.date }}</strong>
          <p>热量 {{ item.energy }} | 蛋白 {{ item.protein }}</p>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { createMealRecord, listMealRecords, mealStatistics } from "../api/tracking";
import { listRecipes } from "../api/recipes";
import { trackEvent } from "../api/behavior";

const period = ref("week");
const records = ref<any[]>([]);
const recipeOptions = ref<Array<{ id: number; title: string }>>([]);
const stats = reactive({
  summary: null as null | Record<string, any>,
  trend: [] as any[],
});
const form = reactive({
  record_date: "",
  meal_type: "lunch",
  source_type: "manual",
  recipe_id: null as null | number,
  note: "",
});

async function loadRecords() {
  try {
    const [recordsResult, statsResult] = await Promise.allSettled([
      listMealRecords(),
      mealStatistics(period.value),
    ]);

    const recordsResponse = recordsResult.status === "fulfilled" ? recordsResult.value : null;
    const statsResponse = statsResult.status === "fulfilled" ? statsResult.value : null;

    if (!recordsResponse && !statsResponse) {
      throw new Error("records load failed");
    }

    records.value = recordsResponse?.data?.results ?? recordsResponse?.data?.data?.items ?? recordsResponse?.data?.data ?? [];
    stats.summary = statsResponse?.data?.data?.summary ?? null;
    stats.trend = statsResponse?.data?.data?.trend ?? [];
    trackEvent({ behavior_type: "view", context_scene: "records" }).catch(() => undefined);
  } catch (error) {
    ElMessage.error("加载记录失败");
  }
}

async function loadRecipes() {
  try {
    const response = await listRecipes();
    recipeOptions.value = response.data?.results ?? response.data?.data?.items ?? response.data?.data ?? [];
  } catch (error) {
    recipeOptions.value = [];
  }
}

async function createRecord() {
  try {
    if (!form.record_date) {
      ElMessage.warning("请选择日期");
      return;
    }

    await createMealRecord({
      record_date: form.record_date,
      meal_type: form.meal_type,
      source_type: form.source_type,
      note: form.note,
      items: [
        form.recipe_id
          ? { recipe_id: form.recipe_id, amount: 1, unit: "serving" }
          : { ingredient_name_snapshot: form.note || "manual entry", amount: 1, unit: "serving" },
      ],
    });
    ElMessage.success("记录已保存");
    form.note = "";
    form.recipe_id = null;
    await loadRecords();
  } catch (error) {
    ElMessage.error("保存记录失败");
  }
}

onMounted(loadRecords);
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

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.stats article,
.list article {
  padding: 16px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.9);
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
  margin-top: 6px;
  font-size: 24px;
}

.list {
  display: grid;
  gap: 12px;
}

.card {
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
  margin-bottom: 18px;
}

.card h3 {
  margin: 0 0 14px;
  font-size: 20px;
}

.trend {
  display: grid;
  gap: 10px;
}

.trend article {
  padding: 14px;
  border-radius: 16px;
  background: rgba(247, 251, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.list p {
  margin: 8px 0 0;
  color: #476072;
}

.muted {
  font-size: 13px;
  color: #6f8592;
}
</style>
