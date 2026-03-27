<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Goals</p>
        <h2>健康目标</h2>
        <p class="desc">目标页不该只负责“新增一条数据”，而应该帮助用户持续管理目标、记录进展并决定下一步动作。</p>
      </div>
      <el-button :loading="loadingGoals" @click="loadGoals">刷新</el-button>
    </div>

    <CollectionSkeleton v-if="loadingGoals && !goals.length" variant="list" :card-count="4" />
    <RefreshFrame v-else :active="loadingGoals && !!goals.length" label="正在更新目标与进展">
    <div class="summary-grid">
      <article>
        <span>目标总数</span>
        <strong>{{ goalSummary.total }}</strong>
        <p>已经建立的健康目标总量。</p>
      </article>
      <article>
        <span>进行中</span>
        <strong>{{ goalSummary.active }}</strong>
        <p>建议优先只推进 1 到 2 个目标。</p>
      </article>
      <article>
        <span>已完成</span>
        <strong>{{ goalSummary.completed }}</strong>
        <p>代表已经真正沉淀下来的阶段性成果。</p>
      </article>
      <article>
        <span>临近到期</span>
        <strong>{{ goalSummary.dueSoon }}</strong>
        <p>{{ goalSummary.dueSoon ? "建议尽快补一次进展，避免目标失焦。" : "当前没有临近到期的目标。" }}</p>
      </article>
    </div>

    <div class="overview-grid">
      <div class="card">
        <div class="card-head">
          <div>
            <h3>{{ editingGoalId ? "编辑目标" : "新增目标" }}</h3>
            <p>{{ editingGoalId ? "更新目标后，会保留已有进展记录。" : "建议一次只专注 1 到 2 个目标，过多目标会明显降低执行率。" }}</p>
          </div>
          <el-button v-if="editingGoalId" plain @click="cancelEditing">取消编辑</el-button>
        </div>

        <el-form :model="goalForm" label-position="top">
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="目标类型">
                <el-select v-model="goalForm.goal_type" style="width: 100%">
                  <el-option v-for="item in goalTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="目标值">
                <el-input-number v-model="goalForm.target_value" :min="0" :precision="1" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="当前值">
                <el-input-number v-model="goalForm.current_value" :min="0" :precision="1" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="开始日期">
                <el-date-picker v-model="goalForm.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="目标日期">
                <el-date-picker v-model="goalForm.target_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="目标描述">
            <el-input v-model.trim="goalForm.description" type="textarea" :rows="3" placeholder="例如：三个月内把体重从 68kg 调整到 65kg。" />
          </el-form-item>
          <FormActionBar
            :tone="savingGoal ? 'saving' : goalFormTone"
            :title="goalFormTitle"
            :description="goalFormDescription"
            :primary-label="editingGoalId ? '保存修改' : '保存目标'"
            :secondary-label="editingGoalId ? '恢复默认' : '重置'"
            :disabled="goalSubmitDisabled"
            :loading="savingGoal"
            @primary="submitGoal"
            @secondary="resetGoalForm"
          />
        </el-form>
      </div>

      <div class="card">
        <div class="card-head">
          <div>
            <h3>当前重点目标</h3>
            <p>首页和后续推荐都应该围绕一个明确目标展开，而不是让用户同时处理一堆分散意图。</p>
          </div>
        </div>

        <div v-if="primaryGoal" class="focus-box">
          <div class="focus-top">
            <strong>{{ goalTypeLabel(primaryGoal.goal_type) }}</strong>
            <span class="goal-status" :class="goalStatusClass(primaryGoal.status)">{{ goalStatusLabel(primaryGoal.status) }}</span>
          </div>
          <p>{{ primaryGoal.description || "建议补充一句目标描述，让后续行动更清晰。" }}</p>
          <div class="focus-metrics">
            <div>
              <span>当前值</span>
              <strong>{{ formatValue(primaryGoal.current_value) }}</strong>
            </div>
            <div>
              <span>目标值</span>
              <strong>{{ formatValue(primaryGoal.target_value) }}</strong>
            </div>
            <div>
              <span>进度</span>
              <strong>{{ goalCompletion(primaryGoal) }}%</strong>
            </div>
          </div>
          <el-progress :percentage="goalCompletion(primaryGoal)" :stroke-width="10" :show-text="false" />
          <p class="focus-copy">{{ goalDirectionCopy(primaryGoal) }}</p>
        </div>
        <PageStateBlock
          v-else
          tone="empty"
          title="当前没有进行中的重点目标"
          description="先创建一个明确目标，后续记录、推荐和报表才会真正围绕它运转。"
          compact
        />
      </div>
    </div>

    <div class="toolbar">
      <el-radio-group v-model="statusFilter" size="large" class="mobile-scroll-row">
        <el-radio-button label="all">全部目标</el-radio-button>
        <el-radio-button label="active">进行中</el-radio-button>
        <el-radio-button label="paused">已暂停</el-radio-button>
        <el-radio-button label="completed">已完成</el-radio-button>
      </el-radio-group>
    </div>

    <div class="goal-list">
      <article v-for="goal in visibleGoals" :key="goal.id" class="goal-card">
        <div class="goal-head">
          <div>
            <strong>{{ goalTypeLabel(goal.goal_type) }}</strong>
            <p>{{ goal.description || "暂未填写目标说明" }}</p>
          </div>
          <div class="goal-head-actions">
            <span class="goal-status" :class="goalStatusClass(goal.status)">{{ goalStatusLabel(goal.status) }}</span>
            <div class="goal-actions">
              <el-button text @click="startEdit(goal)">编辑</el-button>
              <el-button v-if="goal.status === 'active'" text @click="updateStatus(goal, 'paused')">暂停</el-button>
              <el-button v-else-if="goal.status === 'paused'" text @click="updateStatus(goal, 'active')">恢复</el-button>
              <el-button v-if="goal.status !== 'completed'" text @click="updateStatus(goal, 'completed')">完成</el-button>
            </div>
          </div>
        </div>

        <div class="goal-metrics">
          <div>
            <span>当前进度</span>
            <strong>{{ formatValue(goal.current_value) }}</strong>
          </div>
          <div>
            <span>目标值</span>
            <strong>{{ formatValue(goal.target_value) }}</strong>
          </div>
          <div>
            <span>时间范围</span>
            <strong>{{ formatDateRange(goal.start_date, goal.target_date) }}</strong>
          </div>
          <div>
            <span>最近进展</span>
            <strong>{{ latestProgressLabel(goal) }}</strong>
          </div>
        </div>

        <el-progress :percentage="goalCompletion(goal)" :stroke-width="10" :show-text="false" />
        <p class="progress-copy">{{ goalDirectionCopy(goal) }}</p>

        <div v-if="goal.status === 'active'" class="progress-entry">
          <el-date-picker
            v-model="progressDrafts[goal.id].progress_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="记录日期"
            style="width: 160px"
          />
          <el-input-number
            v-model="progressDrafts[goal.id].progress_value"
            :min="0"
            :precision="1"
            style="width: 150px"
          />
          <el-input v-model.trim="progressDrafts[goal.id].note" placeholder="进度备注，可选" />
          <el-button type="primary" :loading="progressSavingId === goal.id" @click="submitProgress(goal.id)">记录进展</el-button>
        </div>

        <div v-if="goal.progress_records?.length" class="history">
          <div v-for="item in goal.progress_records.slice(0, 3)" :key="item.id" class="history-item">
            <strong>{{ item.progress_date }}</strong>
            <span>{{ formatValue(item.progress_value) }}</span>
            <p>{{ item.note || "已更新进度" }}</p>
          </div>
        </div>
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
import { createGoalProgress, createHealthGoal, listGoalProgress, listHealthGoals, updateHealthGoal } from "../api/goals";
import { trackEvent } from "../api/behavior";

const goals = ref<any[]>([]);
const loadingGoals = ref(false);
const savingGoal = ref(false);
const progressSavingId = ref<number | null>(null);
const editingGoalId = ref<number | null>(null);
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
.page {
  display: grid;
  gap: 18px;
}

.head,
.card-head,
.goal-head,
.actions,
.focus-top,
.goal-head-actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.tag {
  margin: 0 0 6px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-size: 12px;
  color: #3e6d7f;
}

h2,
h3 {
  margin: 0;
}

h2 {
  font-size: 30px;
}

.desc,
.card-head p,
.goal-head p,
.progress-copy,
.history-item p,
.empty-state p,
.focus-copy,
.summary-grid p {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.65;
}

.summary-grid,
.overview-grid,
.goal-list {
  display: grid;
  gap: 16px;
}

.summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
}

.overview-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.card,
.goal-card,
.empty-state,
.summary-grid article {
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.summary-grid span,
.goal-metrics span,
.history-item span,
.focus-metrics span {
  display: block;
  font-size: 12px;
  color: #5a7a8a;
  margin-bottom: 6px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.summary-grid strong {
  display: block;
  font-size: 24px;
}

.toolbar {
  display: flex;
  justify-content: flex-start;
}

.focus-box {
  padding: 18px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.focus-metrics,
.goal-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin: 18px 0 16px;
}

.focus-metrics strong,
.goal-metrics strong,
.empty-state strong {
  font-size: 18px;
}

.goal-status {
  padding: 8px 12px;
  border-radius: 999px;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  background: #173042;
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

.goal-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.progress-entry {
  display: grid;
  grid-template-columns: 160px 150px minmax(0, 1fr) 120px;
  gap: 12px;
  margin-top: 18px;
}

.history {
  display: grid;
  gap: 10px;
  margin-top: 18px;
}

.history-item {
  padding: 14px;
  border-radius: 16px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

@media (max-width: 960px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .progress-entry {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .head,
  .card-head,
  .goal-head,
  .actions,
  .focus-top,
  .goal-head-actions {
    flex-direction: column;
  }
}
</style>
