<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Reports</p>
        <h2>健康报表</h2>
      </div>
      <el-button @click="refreshReports">刷新</el-button>
    </div>

    <div class="card">
      <h3>导出报表</h3>
      <div class="actions">
        <el-button type="primary" @click="loadWeekly">生成周报</el-button>
        <el-button @click="loadMonthly">生成月报</el-button>
      </div>
      <div class="download" v-if="currentFileUrl">
        <a :href="currentFileUrl" target="_blank" rel="noreferrer">下载最新报表</a>
      </div>
    </div>

    <div class="card">
      <h3>最近结果</h3>
      <div class="meta">
        <div><span>任务ID</span><strong>{{ reportState.task_id || "-" }}</strong></div>
        <div><span>周期</span><strong>{{ reportState.period || "-" }}</strong></div>
        <div><span>起始</span><strong>{{ reportState.start_date || "-" }}</strong></div>
        <div><span>结束</span><strong>{{ reportState.end_date || "-" }}</strong></div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { monthlyReport, weeklyReport } from "../api/reports";
import { trackEvent } from "../api/behavior";

const currentFileUrl = ref("");
const currentReportType = ref<"weekly" | "monthly">("weekly");
const reportState = reactive({
  task_id: "",
  period: "",
  start_date: "",
  end_date: "",
});

async function loadWeekly() {
  try {
    const response = await weeklyReport();
    const data = response.data?.data;
    currentFileUrl.value = data.file_url || "";
    currentReportType.value = "weekly";
    reportState.task_id = data.task_id || "";
    reportState.period = "weekly";
    reportState.start_date = data.start_date || "";
    reportState.end_date = data.end_date || "";
    trackEvent({ behavior_type: "view", context_scene: "reports_weekly" }).catch(() => undefined);
    ElMessage.success("周报已生成");
  } catch (error) {
    ElMessage.error("生成周报失败");
  }
}

async function loadMonthly() {
  try {
    const response = await monthlyReport();
    const data = response.data?.data;
    currentFileUrl.value = data.file_url || "";
    currentReportType.value = "monthly";
    reportState.task_id = data.task_id || "";
    reportState.period = "monthly";
    reportState.start_date = data.start_date || "";
    reportState.end_date = data.end_date || "";
    trackEvent({ behavior_type: "view", context_scene: "reports_monthly" }).catch(() => undefined);
    ElMessage.success("月报已生成");
  } catch (error) {
    ElMessage.error("生成月报失败");
  }
}

async function refreshReports() {
  if (currentReportType.value === "monthly") {
    await loadMonthly();
    return;
  }
  await loadWeekly();
}
</script>

<style scoped>
.page {
  display: grid;
  gap: 16px;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.card {
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.download {
  margin-top: 16px;
}

.meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.meta span {
  display: block;
  font-size: 12px;
  color: #5a7a8a;
  margin-bottom: 6px;
}

.meta strong {
  font-size: 18px;
}
</style>
