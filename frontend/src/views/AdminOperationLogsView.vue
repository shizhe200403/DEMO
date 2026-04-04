<template>
  <section class="page admin-operation-logs">
    <div class="head">
      <div>
        <p class="tag">Operation Logs</p>
        <h2>操作日志</h2>
      </div>
      <div class="head-actions">
        <CompactHint tone="accent" title="操作日志" description="按模块、操作人或关键词缩小范围，再看字段前后变化，比直接翻全量日志高效多了。" />
        <el-button plain @click="resetFilters">重置筛选</el-button>
        <el-button type="primary" :loading="loading" @click="applyFilters">应用筛选</el-button>
        <el-button plain @click="router.push(resolveOpsHome(auth.user))">回后台首页</el-button>
      </div>
    </div>

    <PageStateBlock
      v-if="auth.isAuthenticated && !auth.user"
      tone="loading"
      title="正在确认后台身份"
      description="稍等一下，正在确认你的账号权限。"
      compact
    />
    <PageStateBlock
      v-else-if="!hasOpsUser"
      tone="error"
      title="当前账号没有后台权限"
      description="操作日志只开放给后台管理账号，如果你需要权限可以联系超管。"
      action-label="回到首页"
      @action="router.push('/')"
    />
    <template v-else>
      <CollectionSkeleton v-if="loading && !logs.length" variant="dashboard" :card-count="4" />
      <RefreshFrame v-else :active="loading" label="正在同步后台操作日志">
        <div class="summary-grid">
          <article
            v-for="item in focusCards"
            :key="item.key"
            :class="{ active: focusPreset === item.key }"
            v-spotlight
            @click="applyFocusPreset(item.key)"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <p>{{ item.copy }}</p>
          </article>
        </div>

        <article class="card console-card filter-card" v-spotlight>
          <div class="card-head">
            <div>
              <div class="section-title-row">
                <h3>筛选与检索</h3>
                <CompactHint description="先按模块或操作人缩小范围，再看字段前后变化，会省很多翻页时间。" />
              </div>
            </div>
            <div class="card-head-actions">
              <el-button class="filter-toggle" plain @click="filtersExpanded = !filtersExpanded">
                {{ filtersExpanded ? "收起筛选" : "展开筛选" }}
              </el-button>
              <el-button v-if="focusPreset !== 'all'" text type="primary" @click="applyFocusPreset('all')">回到全部视角</el-button>
            </div>
          </div>
          <div v-if="!filtersExpanded" class="filter-summary-strip">
            <span v-for="item in logFilterSummary" :key="item" class="filter-summary-chip">{{ item }}</span>
          </div>
          <div v-else class="toolbar-grid">
            <el-select v-model="filters.module" clearable placeholder="筛选模块">
              <el-option label="用户管理" value="users" />
              <el-option label="菜谱管理" value="recipes" />
              <el-option label="社区审核" value="community" />
              <el-option label="运营复核" value="reports" />
            </el-select>
            <el-input v-model.trim="filters.actor" placeholder="搜索操作人" clearable @keyup.enter="applyFilters" />
            <el-input v-model.trim="filters.keyword" placeholder="搜索对象或动作摘要" clearable @keyup.enter="applyFilters" />
            <el-button type="primary" :loading="loading" @click="applyFilters">应用筛选</el-button>
          </div>
        </article>

        <article class="card console-card table-card" v-spotlight>
          <div class="card-head">
            <div>
              <div class="section-title-row">
                <h3>最近处理动作</h3>
                <CompactHint description="重点看这次操作改了哪些字段，没有字段变化的日志主要用来留个轨迹。" />
              </div>
            </div>
            <span class="table-meta">当前显示 {{ logs.length }} / {{ total }} 条</span>
          </div>

          <div v-if="logs.length" class="log-list">
            <article v-for="log in logs" :key="log.id" class="log-item">
              <div class="log-head">
                <div>
                  <div class="log-topline">
                    <el-tag size="small" :type="moduleTagType(log.module)" effect="light">{{ moduleLabel(log.module) }}</el-tag>
                    <span>{{ formatDateTime(log.created_at) }}</span>
                  </div>
                  <strong>{{ log.summary }}</strong>
                  <p>{{ buildMetaLine(log) }}</p>
                </div>
                <div class="log-actor">
                  <span>操作人</span>
                  <strong>{{ log.actor?.display_name || log.actor?.username || "系统" }}</strong>
                </div>
              </div>

              <div class="log-signals">
                <el-tag v-for="signal in logSignals(log)" :key="`${log.id}-${signal}`" size="small" effect="light">{{ signal }}</el-tag>
              </div>

              <div v-if="log.changes?.length" class="change-list">
                <article v-for="(change, index) in log.changes" :key="`${log.id}-${index}-${change.field}`" class="change-item">
                  <div class="change-head">
                    <strong>{{ change.section ? `${change.section} · ${change.label}` : change.label }}</strong>
                    <span>{{ change.field }}</span>
                  </div>
                  <div class="change-values">
                    <div>
                      <span>修改前</span>
                      <strong>{{ formatChangeValue(change.before) }}</strong>
                    </div>
                    <div>
                      <span>修改后</span>
                      <strong>{{ formatChangeValue(change.after) }}</strong>
                    </div>
                  </div>
                </article>
              </div>
              <div v-else class="change-empty">这条动作没有记录字段差异，主要用来保留处理轨迹。</div>
            </article>
          </div>
          <PageStateBlock
            v-else
            tone="empty"
            title="当前筛选下还没有日志"
            description="当前筛选下还没有日志，试试放宽条件，或去各后台模块操作一下再来看。"
            compact
          />
        </article>
      </RefreshFrame>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import CompactHint from "../components/CompactHint.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { listAdminOperationLogs } from "../api/adminLogs";
import { hasOpsAccess, resolveOpsHome } from "../lib/opsAccess";
import { notifyLoadError } from "../lib/feedback";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

type LogFocusPreset = "all" | "users" | "recipes" | "community" | "reports";

const focusPresets: LogFocusPreset[] = ["all", "users", "recipes", "community", "reports"];

const loading = ref(false);
const logs = ref<any[]>([]);
const total = ref(0);
const filtersExpanded = ref(false);
const focusPreset = ref<LogFocusPreset>("all");
const syncingRoute = ref(false);
const summary = ref({
  total: 0,
  today_total: 0,
  unique_operators: 0,
  user_actions: 0,
  recipe_actions: 0,
  community_actions: 0,
  report_actions: 0,
});
const filters = reactive({
  module: "",
  actor: "",
  keyword: "",
});

const hasOpsUser = computed(() => hasOpsAccess(auth.user));
const topModule = computed(() => {
  const entries = [
    { key: "users", count: summary.value.user_actions, label: "用户管理" },
    { key: "recipes", count: summary.value.recipe_actions, label: "菜谱管理" },
    { key: "community", count: summary.value.community_actions, label: "社区审核" },
    { key: "reports", count: summary.value.report_actions, label: "运营复核" },
  ];
  return entries.sort((a, b) => b.count - a.count)[0] || { key: "users", count: 0, label: "用户管理" };
});
const topModuleCount = computed(() => topModule.value.count);
const topModuleCopy = computed(() => topModule.value.count > 0 ? `${topModule.value.label}是当前筛选下最活跃的处理入口，适合先回看这里的处理节奏。` : "当前筛选下各模块还没有明显动作沉淀。");
const focusCards = computed(() => [
  {
    key: "users" as const,
    label: "用户侧动作",
    value: summary.value.user_actions,
    copy: summary.value.user_actions > 0 ? "账号状态、角色边界和资料改动已经开始沉淀可追踪记录。" : "当前筛选下还没有用户管理动作。",
  },
  {
    key: "recipes" as const,
    label: "菜谱侧动作",
    value: summary.value.recipe_actions,
    copy: summary.value.recipe_actions > 0 ? "菜谱审核、状态调整和归档动作都能回看了。" : "当前筛选下还没有菜谱处理动作。",
  },
  {
    key: "community" as const,
    label: "社区侧动作",
    value: summary.value.community_actions,
    copy: summary.value.community_actions > 0 ? "帖子审核、举报处理和评论隐藏已经能串成完整轨迹。" : "当前筛选下还没有社区处理动作。",
  },
  {
    key: "reports" as const,
    label: "复盘侧动作",
    value: summary.value.report_actions,
    copy: summary.value.report_actions > 0 ? "报表生成、复核和异常处理也已经能串回日志。" : "当前筛选下还没有运营复核动作。",
  },
]);
const focusPresetLabel = computed(() => ({
  all: "全部日志",
  users: "用户管理日志",
  recipes: "菜谱管理日志",
  community: "社区审核日志",
  reports: "运营复核日志",
}[focusPreset.value]));
const filterHint = computed(() => {
  if (focusPreset.value === "all") return "先按模块或操作人收窄，再看具体字段前后变化，复盘会比从全量列表硬翻快很多。";
  return `当前聚焦：${focusPresetLabel.value}。先看这一批处理轨迹，再回到全量视角。`;
});
const logFilterSummary = computed(() => {
  const items = [];
  if (focusPreset.value !== "all") items.push(`视角：${focusPresetLabel.value}`);
  if (filters.module) items.push(`模块：${moduleLabel(filters.module)}`);
  if (filters.actor) items.push(`操作人：${filters.actor}`);
  if (filters.keyword) items.push(`关键词：${filters.keyword}`);
  return items.length ? items : ["当前无额外筛选"];
});

onMounted(() => {
  if (hasOpsUser.value) {
    applyRouteQuery(route.query);
    void loadLogs();
  }
});

watch(
  () => route.query,
  (query) => {
    if (!hasOpsUser.value || syncingRoute.value) return;
    applyRouteQuery(query);
    void loadLogs();
  },
);

function readQueryText(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function normalizeFocusPreset(value: string): LogFocusPreset {
  return focusPresets.includes(value as LogFocusPreset) ? (value as LogFocusPreset) : "all";
}

function normalizeModule(value: string) {
  return ["users", "recipes", "community", "reports"].includes(value) ? value : "";
}

function applyRouteQuery(query: Record<string, unknown>) {
  focusPreset.value = normalizeFocusPreset(readQueryText(query.preset));
  filters.module = normalizeModule(readQueryText(query.module));
  filters.actor = readQueryText(query.actor);
  filters.keyword = readQueryText(query.keyword);
  if (!filters.module && focusPreset.value !== "all") {
    filters.module = focusPreset.value;
  }
}

function buildRouteQuery() {
  const query: Record<string, string> = {};
  if (focusPreset.value !== "all") query.preset = focusPreset.value;
  if (filters.module) query.module = filters.module;
  if (filters.actor) query.actor = filters.actor;
  if (filters.keyword) query.keyword = filters.keyword;
  return query;
}

function syncRouteFromState() {
  syncingRoute.value = true;
  return Promise.resolve(router.replace({ query: buildRouteQuery() })).finally(() => {
    syncingRoute.value = false;
  });
}

function unwrapItems(payload: any) {
  if (Array.isArray(payload?.data?.items)) return payload.data.items;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

async function loadLogs() {
  if (!hasOpsUser.value) return;
  loading.value = true;
  try {
    const response = await listAdminOperationLogs({
      page: 1,
      page_size: 20,
      module: filters.module || undefined,
      actor: filters.actor || undefined,
      keyword: filters.keyword || undefined,
    });
    logs.value = unwrapItems(response);
    total.value = Number(response?.data?.count || response?.count || logs.value.length);
    summary.value = response?.data?.summary || response?.summary || summary.value;
  } catch {
    notifyLoadError("后台操作日志");
  } finally {
    loading.value = false;
  }
}

function applyFilters() {
  if (filters.module) {
    focusPreset.value = normalizeFocusPreset(filters.module);
  } else if (focusPreset.value !== "all") {
    filters.module = focusPreset.value;
  }
  filtersExpanded.value = false;
  void syncRouteFromState();
}

function resetFilters() {
  filters.module = "";
  filters.actor = "";
  filters.keyword = "";
  focusPreset.value = "all";
  filtersExpanded.value = false;
  void syncRouteFromState();
}

function applyFocusPreset(preset: LogFocusPreset) {
  focusPreset.value = preset;
  filters.module = preset === "all" ? "" : preset;
  void syncRouteFromState();
}

function moduleLabel(value: string) {
  return (
    {
      users: "用户管理",
      recipes: "菜谱管理",
      community: "社区审核",
      reports: "运营复核",
    }[value] || value
  );
}

function moduleTagType(value: string) {
  return (
    {
      users: "danger",
      recipes: "warning",
      community: "success",
      reports: "info",
    }[value] || "info"
  );
}

function formatDateTime(value?: string) {
  if (!value) return "暂无";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "暂无";
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatChangeValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "空";
  if (Array.isArray(value)) return value.length ? value.join("、") : "空";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function buildMetaLine(log: Record<string, any>) {
  const target = log.target_label ? `对象：${log.target_label}` : "对象：未命名";
  const action = log.action ? `动作：${log.action}` : "";
  return [target, action].filter(Boolean).join(" · ");
}

function logSignals(log: Record<string, any>) {
  const items = [moduleLabel(log.module)];
  if (log.target_type) items.push(`对象类型：${log.target_type}`);
  if (Array.isArray(log.changes) && log.changes.length) items.push(`字段变更 ${log.changes.length} 项`);
  else items.push("仅保留处理轨迹");
  if (log.actor?.display_name || log.actor?.username) items.push(`操作人：${log.actor.display_name || log.actor.username}`);
  return items;
}
</script>

<style scoped>
.admin-operation-logs {
  gap: 18px;
}

.head-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.focus-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.focus-card {
  display: grid;
  gap: 6px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background:
    linear-gradient(135deg, rgba(252, 254, 255, 0.96), rgba(244, 249, 252, 0.94)),
    radial-gradient(circle at top right, rgba(87, 181, 231, 0.1), transparent 36%);
  cursor: pointer;
}

.focus-card span {
  color: #638295;
  font-size: 12px;
}

.focus-card strong {
  color: #173042;
  font-size: 24px;
}

.focus-card p {
  margin: 0;
  color: #587686;
  line-height: 1.6;
}

.focus-card.active {
  border-color: rgba(23, 48, 66, 0.2);
  background: linear-gradient(135deg, rgba(23, 48, 66, 0.96), rgba(39, 76, 99, 0.92));
  box-shadow: 0 16px 30px rgba(15, 30, 39, 0.14);
}

.focus-card.active span,
.focus-card.active strong,
.focus-card.active p {
  color: #f2f7fb;
}

.console-card,
.filter-card,
.table-card {
  display: grid;
  gap: 16px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.card-head h3 {
  margin: 0;
  font-size: 20px;
  color: #173042;
}

.card-head p {
  margin: 6px 0 0;
  color: #5b7888;
  line-height: 1.65;
}

.toolbar-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.table-meta {
  color: #6c8796;
  font-size: 13px;
}

.log-list {
  display: grid;
  gap: 14px;
}

.log-item {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 20px;
  border: 1px solid rgba(18, 43, 56, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(244, 249, 252, 0.95)),
    radial-gradient(circle at top right, rgba(88, 194, 255, 0.08), transparent 34%);
}

.log-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 14px;
  align-items: start;
}

.log-topline {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}

.log-head strong {
  color: #173042;
  font-size: 18px;
}

.log-head p,
.log-topline span,
.log-actor span {
  margin: 0;
  color: #648190;
}

.log-actor {
  min-width: 104px;
  text-align: right;
}

.log-actor strong {
  display: block;
  margin-top: 6px;
}

.log-signals {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.change-list {
  display: grid;
  gap: 10px;
}

.change-item {
  display: grid;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(241, 248, 251, 0.92);
  border: 1px solid rgba(18, 43, 56, 0.06);
}

.change-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.change-head strong {
  color: #173042;
  font-size: 14px;
}

.change-head span {
  color: #6a8797;
  font-size: 12px;
}

.change-values {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.change-values div {
  display: grid;
  gap: 6px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.88);
}

.change-values span {
  color: #6d8794;
  font-size: 12px;
}

.change-values strong {
  color: #173042;
  font-size: 14px;
  word-break: break-word;
}

.change-empty {
  color: #698595;
  font-size: 13px;
}

@media (max-width: 1080px) {
  .change-values {
    grid-template-columns: 1fr;
  }

  .log-head {
    grid-template-columns: 1fr;
  }

  .log-actor {
    text-align: left;
  }
}

@media (max-width: 720px) {
  .focus-strip {
    grid-template-columns: 1fr;
  }
}
</style>
