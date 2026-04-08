<template>
  <section class="page">
    <!-- 顶部栏 -->
    <div class="greeting-bar">
      <div class="greeting-left">
        <h2 class="greeting-title">健康目标</h2>
        <p class="greeting-sub">{{ editingGoalId ? "编辑目标中 — 修改后保存" : "定方向，记进展，让饮食选择有参照点" }}</p>
      </div>
      <div class="greeting-right">
        <el-button v-if="editingGoalId" plain @click="cancelEditing">取消编辑</el-button>
        <el-button :loading="loadingGoals" @click="loadGoals">刷新</el-button>
      </div>
    </div>

    <CollectionSkeleton v-if="loadingGoals && !goals.length" variant="list" :card-count="4" />
    <RefreshFrame v-else :active="loadingGoals && !!goals.length" label="正在更新目标与进展">

      <!-- 双栏主体 -->
      <div class="main-layout">

        <!-- 左侧 sidebar -->
        <aside class="sidebar">

          <!-- 统计卡 -->
          <div class="sidebar-card">
            <div class="sidebar-card-header">
              <span class="card-label">目标统计</span>
            </div>
            <div class="stat-rows">
              <div class="stat-row">
                <span class="stat-label">进行中</span>
                <strong class="stat-value stat-active">{{ goalSummary.active }}</strong>
              </div>
              <div class="stat-row">
                <span class="stat-label">已完成</span>
                <strong class="stat-value">{{ goalSummary.completed }}</strong>
              </div>
              <div class="stat-row">
                <span class="stat-label">目标总数</span>
                <strong class="stat-value">{{ goalSummary.total }}</strong>
              </div>
              <div v-if="goalSummary.dueSoon" class="stat-row stat-row-warn">
                <span class="stat-label">临近到期</span>
                <strong class="stat-value stat-warn">{{ goalSummary.dueSoon }}</strong>
              </div>
            </div>
          </div>

          <!-- 新建/编辑目标表单 -->
          <div class="sidebar-card form-card">
            <div class="sidebar-card-header">
              <span class="card-label">{{ editingGoalId ? "编辑目标" : "新建目标" }}</span>
            </div>

            <el-form :model="goalForm" label-position="top" class="goal-form">
              <el-form-item label="目标类型">
                <el-select v-model="goalForm.goal_type" style="width: 100%">
                  <el-option v-for="item in goalTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
                </el-select>
              </el-form-item>
              <div class="form-row-2">
                <el-form-item label="目标值">
                  <el-input-number v-model="goalForm.target_value" :min="0" :precision="1" style="width: 100%" />
                </el-form-item>
                <el-form-item label="当前值">
                  <el-input-number v-model="goalForm.current_value" :min="0" :precision="1" style="width: 100%" />
                </el-form-item>
              </div>
              <div class="form-row-2">
                <el-form-item label="开始日期">
                  <el-date-picker v-model="goalForm.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
                </el-form-item>
                <el-form-item label="目标日期">
                  <el-date-picker v-model="goalForm.target_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
                </el-form-item>
              </div>
              <el-form-item label="目标描述">
                <el-input v-model.trim="goalForm.description" type="textarea" :rows="2" placeholder="例如：三个月内把体重从 68kg 调整到 65kg。" />
              </el-form-item>
              <div class="form-actions">
                <el-button type="primary" :loading="savingGoal" :disabled="goalSubmitDisabled" @click="submitGoal">
                  {{ editingGoalId ? "保存修改" : "保存目标" }}
                </el-button>
                <el-button plain @click="resetGoalForm">重置</el-button>
              </div>
            </el-form>
          </div>

          <!-- 状态筛选 -->
          <div class="sidebar-card">
            <div class="sidebar-card-header">
              <span class="card-label">状态筛选</span>
            </div>
            <div class="filter-tabs">
              <button
                v-for="item in [
                  { label: '全部目标', value: 'all' },
                  { label: '进行中', value: 'active' },
                  { label: '已暂停', value: 'paused' },
                  { label: '已完成', value: 'completed' },
                ]"
                :key="item.value"
                type="button"
                class="filter-tab"
                :class="{ active: statusFilter === item.value }"
                @click="statusFilter = item.value"
              >
                {{ item.label }}
              </button>
            </div>
          </div>

        </aside>

        <!-- 右侧主内容 -->
        <main class="main-content">

          <!-- 目标卡列表 -->
          <div class="goal-list">
            <article v-for="goal in visibleGoals" :key="goal.id" class="goal-card">

              <!-- 卡片头部 -->
              <div class="goal-card-head">
                <div class="goal-card-title-row">
                  <span class="goal-type-tag">{{ goalTypeLabel(goal.goal_type) }}</span>
                  <span class="goal-status" :class="goalStatusClass(goal.status)">{{ goalStatusLabel(goal.status) }}</span>
                </div>
                <div class="goal-card-actions">
                  <el-button text size="small" @click="startEdit(goal)">编辑</el-button>
                  <el-button v-if="goal.status === 'active'" text size="small" @click="updateStatus(goal, 'paused')">暂停</el-button>
                  <el-button v-else-if="goal.status === 'paused'" text size="small" @click="updateStatus(goal, 'active')">恢复</el-button>
                  <el-button v-if="goal.status !== 'completed'" text size="small" @click="updateStatus(goal, 'completed')">完成</el-button>
                  <el-button text size="small" type="danger" :loading="deletingGoalId === goal.id" @click="removeGoal(goal)">删除</el-button>
                </div>
              </div>

              <p v-if="goal.description" class="goal-desc">{{ goal.description }}</p>

              <!-- 进度区 -->
              <div class="goal-progress-area">
                <div class="goal-metrics-row">
                  <span class="metrics-label">当前</span>
                  <strong class="metrics-value">{{ formatValue(goal.current_value) }}</strong>
                  <span class="metrics-sep">/</span>
                  <span class="metrics-label">目标</span>
                  <strong class="metrics-value">{{ formatValue(goal.target_value) }}</strong>
                  <span class="metrics-pct">{{ goalCompletion(goal) }}%</span>
                </div>
                <el-progress :percentage="goalCompletion(goal)" :stroke-width="8" :show-text="false" />
                <p class="progress-copy">{{ goalDirectionCopy(goal) }}</p>
              </div>

              <!-- 进展录入（一行，仅进行中目标） -->
              <div v-if="goal.status === 'active'" class="entry-row">
                <el-date-picker
                  v-model="progressDrafts[goal.id].progress_date"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="日期"
                  style="width: 140px; flex-shrink: 0"
                />
                <el-input-number
                  v-model="progressDrafts[goal.id].progress_value"
                  :min="0"
                  :precision="1"
                  placeholder="数值"
                  style="width: 130px; flex-shrink: 0"
                />
                <el-input v-model.trim="progressDrafts[goal.id].note" placeholder="备注（可选）" style="flex: 1" />
                <el-button type="primary" size="small" :loading="progressSavingId === goal.id" @click="submitProgress(goal.id)">记录进展</el-button>
              </div>

              <!-- 历史折叠 -->
              <el-collapse v-if="goal.progress_records?.length" class="history-collapse">
                <el-collapse-item :title="`历史记录（${goal.progress_records.length}条）`">
                  <div class="history-list">
                    <div v-for="item in goal.progress_records.slice(0, 3)" :key="item.id" class="history-item">
                      <strong>{{ item.progress_date }}</strong>
                      <span>{{ formatValue(item.progress_value) }}</span>
                      <p>{{ item.note || "已更新进度" }}</p>
                    </div>
                  </div>
                </el-collapse-item>
              </el-collapse>

            </article>

            <PageStateBlock
              v-if="!visibleGoals.length"
              tone="empty"
              :title="emptyStateTitle"
              :description="emptyStateDescription"
              :action-label="emptyStateActionLabel"
              @action="handleEmptyStateAction"
            />
          </div>

        </main>
      </div>

    </RefreshFrame>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import FormActionBar from "../components/FormActionBar.vue";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { notifyActionError, notifyActionSuccess, notifyLoadError, notifyWarning } from "../lib/feedback";
import { ElMessageBox } from "element-plus";
import { createGoalProgress, createHealthGoal, deleteHealthGoal, listGoalProgress, listHealthGoals, updateHealthGoal } from "../api/goals";
import { trackEvent } from "../api/behavior";

const goals = ref<any[]>([]);
const loadingGoals = ref(false);
const savingGoal = ref(false);
const progressSavingId = ref<number | null>(null);
const editingGoalId = ref<number | null>(null);
const deletingGoalId = ref<number | null>(null);
const statusFilter = ref<"all" | "active" | "paused" | "completed">("active");
const progressDrafts = reactive<Record<number, { progress_date: string; progress_value: number | null; note: string }>>({});

const goalTypeOptions = [
  { label: "减重", value: "weight_loss" },
  { label: "增肌", value: "muscle_gain" },
  { label: "控糖", value: "blood_sugar_control" },
  { label: "控脂", value: "fat_control" },
  { label: "提升蛋白摄入", value: "protein_up" },
  { label: "饮食均衡", value: "diet_balance" },
];

const goalForm = reactive({
  goal_type: "weight_loss",
  target_value: 0,
  current_value: 0,
  start_date: "",
  target_date: "",
  description: "",
});
const goalSubmitDisabled = computed(() => goalForm.target_value === null || goalForm.current_value === null);
const goalFormTone = computed(() => (goalSubmitDisabled.value ? "warning" : "ready"));
const goalFormTitle = computed(() => {
  if (goalSubmitDisabled.value) {
    return "先填写目标值和当前值";
  }
  return editingGoalId.value ? "目标修改后可以提交" : "目标信息已完整，可以保存";
});
const goalFormDescription = computed(() => {
  return goalForm.description
    ? "描述已补充，后续首页推荐和阶段复盘会更容易围绕同一个目标展开。"
    : "补一句目标描述会更好，后续行动和复盘会更清晰。";
});

const visibleGoals = computed(() => {
  if (statusFilter.value === "all") {
    return goals.value;
  }
  return goals.value.filter((goal) => goal.status === statusFilter.value);
});
const primaryGoal = computed(() => goals.value.find((goal) => goal.status === "active") ?? null);
const emptyStateTitle = computed(() => {
  return statusFilter.value === "all" ? "你还没有建立任何健康目标" : "当前筛选条件下没有目标";
});
const emptyStateDescription = computed(() => {
  return statusFilter.value === "all"
    ? "先从一个最明确、最容易坚持的目标开始，比如体重、蛋白摄入或控脂。"
    : "可以切换筛选查看其他状态，或者新增一个新目标。";
});
const emptyStateActionLabel = computed(() => (statusFilter.value === "all" ? "创建目标" : "查看全部目标"));
const goalSummary = computed(() => {
  const today = new Date();
  const dueSoon = goals.value.filter((goal) => {
    if (goal.status !== "active" || !goal.target_date) {
      return false;
    }
    const diff = Math.ceil((new Date(`${goal.target_date}T00:00:00`).getTime() - today.getTime()) / (24 * 60 * 60 * 1000));
    return diff >= 0 && diff <= 7;
  }).length;
  return {
    total: goals.value.length,
    active: goals.value.filter((goal) => goal.status === "active").length,
    completed: goals.value.filter((goal) => goal.status === "completed").length,
    dueSoon,
  };
});

function todayString() {
  const date = new Date();
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function goalTypeLabel(value: string) {
  return goalTypeOptions.find((item) => item.value === value)?.label || value;
}

function goalStatusLabel(value: string) {
  return {
    active: "进行中",
    paused: "已暂停",
    completed: "已完成",
    cancelled: "已取消",
  }[value] || value;
}

function goalStatusClass(value: string) {
  return {
    active: "is-active",
    paused: "is-paused",
    completed: "is-completed",
    cancelled: "is-cancelled",
  }[value] || "";
}

function numericValue(value: unknown) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function formatValue(value: unknown) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "-";
  }
  return number.toFixed(1);
}

function formatDateRange(startDate?: string, endDate?: string) {
  if (!startDate && !endDate) {
    return "未设置";
  }
  return `${startDate || "即刻开始"} 至 ${endDate || "未设置"}`;
}

function ensureProgressDraft(goalId: number) {
  if (!progressDrafts[goalId]) {
    progressDrafts[goalId] = {
      progress_date: todayString(),
      progress_value: null,
      note: "",
    };
  }
}

function goalCompletion(goal: Record<string, any>) {
  const target = numericValue(goal.target_value);
  const current = numericValue(goal.current_value);
  if (target <= 0) {
    return 0;
  }

  if (goal.goal_type === "weight_loss" || goal.goal_type === "fat_control") {
    const baseline =
      goal.progress_records?.length && goal.progress_records[goal.progress_records.length - 1]?.progress_value !== undefined
        ? numericValue(goal.progress_records[goal.progress_records.length - 1].progress_value)
        : current;
    if (baseline <= target) {
      return Math.min(100, Math.max(0, Math.round((current / target) * 100)));
    }
    return Math.min(100, Math.max(0, Math.round(((baseline - current) / (baseline - target)) * 100)));
  }

  return Math.min(100, Math.max(0, Math.round((current / target) * 100)));
}

function goalDirectionCopy(goal: Record<string, any>) {
  const target = numericValue(goal.target_value);
  const current = numericValue(goal.current_value);
  if (target <= 0) {
    return "先补充目标值，系统才知道应该往哪里走。";
  }

  if (goal.goal_type === "weight_loss" || goal.goal_type === "fat_control") {
    const gap = current - target;
    if (gap <= 0) {
      return "当前值已经接近或达到目标，建议继续观察是否稳定。";
    }
    return `距离目标还差 ${gap.toFixed(1)}。`;
  }

  const gap = target - current;
  if (gap <= 0) {
    return "当前值已经达到目标，可以考虑进入维护阶段。";
  }
  return `距离目标还差 ${gap.toFixed(1)}。`;
}

function latestProgressLabel(goal: Record<string, any>) {
  const latest = goal.progress_records?.[0];
  if (!latest) {
    return "暂无";
  }
  return latest.progress_date || "刚刚";
}

function resetGoalForm() {
  goalForm.goal_type = "weight_loss";
  goalForm.target_value = 0;
  goalForm.current_value = 0;
  goalForm.start_date = todayString();
  goalForm.target_date = "";
  goalForm.description = "";
}

function cancelEditing() {
  editingGoalId.value = null;
  resetGoalForm();
}

function startEdit(goal: Record<string, any>) {
  editingGoalId.value = Number(goal.id);
  goalForm.goal_type = goal.goal_type || "weight_loss";
  goalForm.target_value = numericValue(goal.target_value);
  goalForm.current_value = numericValue(goal.current_value);
  goalForm.start_date = goal.start_date || todayString();
  goalForm.target_date = goal.target_date || "";
  goalForm.description = goal.description || "";
}

async function loadGoals() {
  try {
    loadingGoals.value = true;
    const response = await listHealthGoals();
    const items = response.data?.items ?? response.data ?? [];
    const goalsWithProgress = await Promise.all(
      items.map(async (goal: Record<string, any>) => {
        const progressResponse = await listGoalProgress(Number(goal.id));
        ensureProgressDraft(Number(goal.id));
        return {
          ...goal,
          progress_records: progressResponse.data ?? [],
        };
      }),
    );
    goals.value = goalsWithProgress;
    trackEvent({ behavior_type: "view", context_scene: "goals" }).catch(() => undefined);
  } catch (error) {
    notifyLoadError("健康目标");
  } finally {
    loadingGoals.value = false;
  }
}

async function submitGoal() {
  try {
    if (goalForm.target_value === null || goalForm.current_value === null) {
      notifyWarning("请先填写目标值和当前值");
      return;
    }

    savingGoal.value = true;
    if (editingGoalId.value) {
      await updateHealthGoal(editingGoalId.value, goalForm);
      notifyActionSuccess("目标已更新");
    } else {
      await createHealthGoal(goalForm);
      notifyActionSuccess("目标已保存");
    }
    cancelEditing();
    await loadGoals();
  } catch (error) {
    notifyActionError(editingGoalId.value ? "更新目标" : "保存目标");
  } finally {
    savingGoal.value = false;
  }
}

async function removeGoal(goal: Record<string, any>) {
  try {
    await ElMessageBox.confirm(`确认删除目标「${goalTypeLabel(goal.goal_type)}」？此操作不可恢复。`, "删除目标", { type: "warning", confirmButtonText: "删除", cancelButtonText: "取消" });
  } catch {
    return;
  }
  try {
    deletingGoalId.value = Number(goal.id);
    await deleteHealthGoal(Number(goal.id));
    goals.value = goals.value.filter((item) => Number(item.id) !== Number(goal.id));
    if (editingGoalId.value === Number(goal.id)) cancelEditing();
    notifyActionSuccess("目标已删除");
  } catch {
    notifyActionError("删除目标");
  } finally {
    deletingGoalId.value = null;
  }
}

async function updateStatus(goal: Record<string, any>, status: "active" | "paused" | "completed") {
  try {
    await updateHealthGoal(Number(goal.id), { status });
    notifyActionSuccess(`目标已${goalStatusLabel(status).replace("已", "")}`);
    await loadGoals();
  } catch (error) {
    notifyActionError("更新目标状态");
  }
}

async function submitProgress(goalId: number) {
  const draft = progressDrafts[goalId];
  if (!draft?.progress_date || draft.progress_value === null) {
    notifyWarning("请先填写进展日期和数值");
    return;
  }

  try {
    progressSavingId.value = goalId;
    await createGoalProgress(goalId, draft);
    notifyActionSuccess("进展已记录");
    progressDrafts[goalId] = {
      progress_date: todayString(),
      progress_value: null,
      note: "",
    };
    await loadGoals();
  } catch (error) {
    notifyActionError("记录目标进展");
  } finally {
    progressSavingId.value = null;
  }
}

function handleEmptyStateAction() {
  if (statusFilter.value === "all") {
    resetGoalForm();
    return;
  }
  statusFilter.value = "all";
}

onMounted(() => {
  resetGoalForm();
  loadGoals();
});
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

/* ── 双栏主体布局 ─────────────────────────────── */
.main-layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
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

.stat-row-warn {
  padding-top: 6px;
  border-top: 1px solid rgba(16, 34, 42, 0.06);
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

.stat-active {
  color: #1d6f5f;
}

.stat-warn {
  color: #9a6a28;
}

/* 表单卡 */
.form-card {
  /* 表单内容稍多，不做特殊限制 */
}

.goal-form {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.form-row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.form-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
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
  gap: 16px;
  padding: 20px 24px 32px;
}

/* 目标列表 */
.goal-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.goal-card {
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 4px 16px rgba(15, 30, 39, 0.05);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 卡片头部 */
.goal-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.goal-card-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.goal-type-tag {
  font-size: 15px;
  font-weight: 700;
  color: #173042;
}

.goal-card-actions {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.goal-desc {
  margin: 0;
  font-size: 13px;
  color: #476072;
  line-height: 1.6;
}

/* 状态标签 */
.goal-status {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  background: #173042;
  color: #fff;
}

.goal-status.is-active {
  background: #1d6f5f;
}

.goal-status.is-paused {
  background: #9a6a28;
}

.goal-status.is-completed {
  background: #173042;
}

.goal-status.is-cancelled {
  background: #7d4a4a;
}

/* 进度区 */
.goal-progress-area {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.goal-metrics-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.metrics-label {
  font-size: 12px;
  color: #5a7a8a;
}

.metrics-value {
  font-size: 16px;
  font-weight: 700;
  color: #173042;
}

.metrics-sep {
  color: #aac0cc;
  font-size: 14px;
}

.metrics-pct {
  margin-left: auto;
  font-size: 13px;
  font-weight: 700;
  color: #24566a;
  background: #e8f1f7;
  padding: 3px 8px;
  border-radius: 999px;
}

.progress-copy {
  margin: 0;
  font-size: 13px;
  color: #476072;
  line-height: 1.6;
}

/* 进展录入行 */
.entry-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(232, 241, 247, 0.5);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

/* 历史折叠 */
.history-collapse {
  border: none;
}

:deep(.history-collapse .el-collapse-item__header) {
  font-size: 13px;
  color: #5a7a8a;
  background: transparent;
  border: none;
  padding: 0;
}

:deep(.history-collapse .el-collapse-item__content) {
  padding-bottom: 0;
}

:deep(.history-collapse .el-collapse-item__wrap) {
  border: none;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.history-item {
  display: grid;
  grid-template-columns: auto auto 1fr;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.history-item strong {
  font-size: 13px;
  color: #173042;
}

.history-item span {
  font-size: 13px;
  color: #24566a;
  font-weight: 600;
}

.history-item p {
  margin: 0;
  font-size: 12px;
  color: #5a7a8a;
  line-height: 1.5;
  text-align: right;
}

/* ── 响应式 ───────────────────────────────────── */
@media (max-width: 1000px) {
  .main-layout {
    grid-template-columns: 240px minmax(0, 1fr);
  }
}

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
    overflow: visible;
  }

  .form-card {
    order: -1;
  }

  .entry-row {
    flex-direction: column;
    align-items: stretch;
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

  .form-row-2 {
    grid-template-columns: 1fr;
  }

  .history-item {
    grid-template-columns: 1fr;
  }

  .history-item p {
    text-align: left;
  }
}
</style>
