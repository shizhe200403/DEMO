<template>
  <section class="page admin-recipes">
    <div class="head">
      <div>
        <p class="tag">Recipe Operations</p>
        <h2>菜谱管理</h2>
      </div>
      <div class="head-actions">
        <CompactHint tone="warm" title="菜谱管理说明" description="先在列表处理状态和审核，只有需要深看内容结构时再展开详情抽屉。" />
        <el-button plain @click="resetFilters">重置筛选</el-button>
        <el-button type="primary" :loading="loadingRecipes" @click="applyFilters">应用筛选</el-button>
        <el-button plain @click="router.push('/recipes')">去前台菜谱页</el-button>
      </div>
    </div>

    <PageStateBlock
      v-if="auth.isAuthenticated && !auth.user"
      tone="loading"
      title="正在确认后台身份"
      description="先把账号权限拉齐，再展开菜谱管理台。"
      compact
    />
    <PageStateBlock
      v-else-if="!hasOpsUser"
      tone="error"
      title="当前账号没有后台权限"
      description="菜谱管理只对后台值守账号开放，普通账号不会显示这里。"
      action-label="回到首页"
      @action="router.push('/')"
    />
    <template v-else>
      <CollectionSkeleton v-if="loadingRecipes && !recipes.length" variant="list" :card-count="5" />
      <RefreshFrame v-else :active="loadingRecipes && !!recipes.length" label="正在同步菜谱列表与审核状态">
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

        <div class="card filter-card" v-spotlight>
          <div class="card-head">
            <div>
              <div class="section-title-row">
                <h3>筛选与搜索</h3>
                <CompactHint description="先用菜名、审核、状态和来源快速收窄，只有必要时再切换聚焦视角。" />
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
            <span v-for="item in recipeFilterSummary" :key="item" class="filter-summary-chip">{{ item }}</span>
          </div>
          <div v-else class="toolbar-grid">
            <el-input v-model.trim="filters.keyword" placeholder="搜索菜名、描述、标签或来源" clearable @keyup.enter="applyFilters" />
            <el-select v-model="filters.status" clearable placeholder="筛选状态">
              <el-option label="草稿" value="draft" />
              <el-option label="已发布" value="published" />
            </el-select>
            <el-select v-model="filters.auditStatus" clearable placeholder="筛选审核结论">
              <el-option label="待审核" value="pending" />
              <el-option label="已通过" value="approved" />
              <el-option label="已驳回" value="rejected" />
            </el-select>
            <el-select v-model="filters.sourceType" clearable placeholder="筛选来源">
              <el-option label="用户上传" value="user_upload" />
              <el-option label="系统内置" value="builtin" />
            </el-select>
            <el-button type="primary" :loading="loadingRecipes" @click="applyFilters">应用筛选</el-button>
          </div>
        </div>

        <div class="card table-card" v-spotlight>
          <div class="card-head">
            <div>
              <div class="section-title-row">
                <h3>菜谱列表</h3>
                <CompactHint description="聚焦视角的目的是帮助你先清一批高优先项，不需要在列表里阅读完整说明。" />
              </div>
            </div>
            <span class="table-meta">当前显示 {{ displayRecipes.length }} / {{ recipes.length }} 份菜谱</span>
          </div>

          <div v-if="selectedRecipeIds.length" class="bulk-bar">
            <span>已选 {{ selectedRecipeIds.length }} 份菜谱，可直接批量通过、驳回或归档。</span>
            <div class="bulk-actions">
              <el-button :disabled="bulkUpdatingRecipes" @click="clearRecipeSelection">清空选择</el-button>
              <el-button type="success" :loading="bulkUpdatingRecipes" @click="applyBulkRecipeAction('approve')">批量通过</el-button>
              <el-button type="warning" :loading="bulkUpdatingRecipes" @click="applyBulkRecipeAction('reject')">批量驳回</el-button>
              <el-button type="danger" :loading="bulkUpdatingRecipes" @click="applyBulkRecipeAction('archive')">批量归档</el-button>
            </div>
          </div>

          <el-table ref="recipeTableRef" :data="displayRecipes" :row-key="(row: any) => row.id" stripe class="recipe-table" empty-text="当前筛选下没有菜谱" @selection-change="handleRecipeSelectionChange">
            <el-table-column type="selection" width="48" />
            <el-table-column label="菜谱" min-width="220">
              <template #default="{ row }">
                <div class="recipe-cell">
                  <strong>{{ row.title }}</strong>
                  <span>{{ row.description || "暂无描述" }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="餐次 / 用时" width="150">
              <template #default="{ row }">
                <div class="meta-cell">
                  <span>{{ mealTypeLabel(row.meal_type) }}</span>
                  <span>{{ recipeTimeLabel(row) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" effect="light">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="审核" width="120">
              <template #default="{ row }">
                <el-tag :type="auditTagType(row.audit_status)" effect="light">{{ auditLabel(row.audit_status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="Pro 专属" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.is_premium" type="warning" effect="dark" size="small">✦ Pro</el-tag>
                <span v-else class="muted-copy">—</span>
              </template>
            </el-table-column>
            <el-table-column label="来源" width="120">
              <template #default="{ row }">
                <span>{{ sourceLabel(row.source_type) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="内容完整度" width="150">
              <template #default="{ row }">
                <div class="completion-cell">
                  <strong>{{ recipeCompleteness(row) }}%</strong>
                  <small :class="completionToneClass(recipeCompleteness(row))">{{ completionToneLabel(recipeCompleteness(row)) }}</small>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="管理判断" min-width="180">
              <template #default="{ row }">
                <div class="judgement-cell">
                  <span v-for="item in recipeSignals(row)" :key="item">{{ item }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" fixed="right" width="160">
              <template #default="{ row }">
                <el-button text type="primary" @click="openRecipeDrawer(row.id)">查看并处理</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </RefreshFrame>

      <el-drawer v-model="drawerOpen" size="620px" :title="drawerTitle" destroy-on-close>
        <PageStateBlock
          v-if="detailLoading"
          tone="loading"
          title="正在加载菜谱详情"
          description="把状态、审核和内容完整度拉齐后再做处理。"
          compact
        />
        <PageStateBlock
          v-else-if="!selectedRecipe"
          tone="empty"
          title="还没有选中菜谱"
          description="从列表里点开一份菜谱，右侧就会展开详细处理区。"
          compact
        />
        <template v-else>
          <div class="drawer-summary">
            <article v-spotlight>
              <span>来源</span>
              <strong>{{ sourceLabel(recipeDraft.source_type) }}</strong>
            </article>
            <article v-spotlight>
              <span>最近更新</span>
              <strong>{{ formatDateTime(selectedRecipe.updated_at) }}</strong>
            </article>
            <article v-spotlight>
              <span>完整度</span>
              <strong>{{ recipeCompleteness(selectedRecipe) }}%</strong>
            </article>
          </div>

          <div class="drawer-focus" v-spotlight>
            <div class="drawer-focus-head">
              <strong>当前审核判断</strong>
              <span>{{ recipeFocusTitle }}</span>
            </div>
            <div class="drawer-focus-tags">
              <span v-for="item in recipeSignals(selectedRecipe)" :key="item" class="drawer-focus-tag">{{ item }}</span>
            </div>
            <ul class="drawer-checklist">
              <li v-for="item in recipeChecklist" :key="item">{{ item }}</li>
            </ul>
          </div>

          <el-form label-position="top" class="drawer-form">
            <div class="drawer-section" v-spotlight>
              <div class="drawer-section-head">
                <strong>审核状态</strong>
                <span>先决定这份菜谱是否可继续发布，以及审核结论是否要切换。</span>
              </div>
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="状态">
                    <el-select v-model="recipeDraft.status" style="width: 100%">
                      <el-option label="草稿" value="draft" />
                      <el-option label="已发布" value="published" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="审核结论">
                    <el-select v-model="recipeDraft.audit_status" style="width: 100%">
                      <el-option label="待审核" value="pending" />
                      <el-option label="已通过" value="approved" />
                      <el-option label="已驳回" value="rejected" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="Pro 专属" style="margin-top: 8px; margin-bottom: 0">
                <el-switch v-model="recipeDraft.is_premium" active-text="是（仅 Pro 用户可查看详情）" inactive-text="否" />
                <span style="font-size:12px;color:#909399;margin-left:10px;">仅限管理员账号上传的菜谱可标记为 Pro 专属</span>
              </el-form-item>
            </div>

            <div class="drawer-section" v-spotlight>
              <div class="drawer-section-head">
                <strong>内容信息</strong>
                <span>标题、描述和餐次会直接影响前台用户的理解和选择。</span>
              </div>
              <el-row :gutter="12">
                <el-col :span="24">
                  <el-form-item label="标题">
                    <el-input v-model.trim="recipeDraft.title" />
                  </el-form-item>
                </el-col>
                <el-col :span="24">
                  <el-form-item label="描述">
                    <el-input v-model.trim="recipeDraft.description" type="textarea" :rows="3" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="餐次">
                    <el-select v-model="recipeDraft.meal_type" style="width: 100%">
                      <el-option label="早餐" value="breakfast" />
                      <el-option label="午餐" value="lunch" />
                      <el-option label="晚餐" value="dinner" />
                      <el-option label="加餐" value="snack" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="来源名称">
                    <el-input v-model.trim="recipeDraft.source_name" />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <div class="drawer-section" v-spotlight>
              <div class="drawer-section-head">
                <strong>内容结构</strong>
                <span>这里只做快速判断，真正编辑步骤和食材时仍然可以回前台编辑器。</span>
              </div>
              <div class="recipe-structure-grid">
                <article>
                  <span>食材数</span>
                  <strong>{{ selectedRecipe.ingredients?.length || 0 }}</strong>
                </article>
                <article>
                  <span>步骤数</span>
                  <strong>{{ selectedRecipe.steps?.length || 0 }}</strong>
                </article>
                <article>
                  <span>营养信息</span>
                  <strong>{{ selectedRecipe.nutrition_summary ? "已填写" : "待补齐" }}</strong>
                </article>
              </div>
              <RouterLink class="jump-link" to="/recipes">需要深度编辑时，回前台菜谱页处理完整内容</RouterLink>
            </div>
          </el-form>

          <div class="drawer-section" v-spotlight>
            <AdminObjectTimeline
              object-label="这份菜谱"
              :logs="recipeLogs"
              :loading="recipeLogsLoading"
              title="最近处理回放"
              description="直接看这份菜谱最近被谁改过状态、审核结论和基础信息。"
            />
          </div>

          <div class="drawer-actions">
            <el-button plain @click="drawerOpen = false">取消</el-button>
            <el-button type="danger" plain :loading="archivingRecipe" @click="archiveRecipe">归档菜谱</el-button>
            <el-button type="primary" :loading="savingRecipe" @click="saveRecipe">保存修改</el-button>
          </div>
        </template>
      </el-drawer>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import AdminObjectTimeline from "../components/AdminObjectTimeline.vue";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import CompactHint from "../components/CompactHint.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { listAdminOperationLogs } from "../api/adminLogs";
import { bulkUpdateRecipes, deleteRecipe, getRecipeDetail, listRecipes, updateRecipe } from "../api/recipes";
import { hasOpsAccess } from "../lib/opsAccess";
import { extractApiErrorMessage, notifyActionSuccess, notifyErrorMessage, notifyLoadError } from "../lib/feedback";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

type RecipeFocusPreset = "all" | "pending" | "draft" | "incomplete" | "user_upload";

const recipeFocusPresets: RecipeFocusPreset[] = ["all", "pending", "draft", "incomplete", "user_upload"];
const recipeStatuses = ["draft", "published"] as const;
const recipeAuditStatuses = ["pending", "approved", "rejected"] as const;
const recipeSourceTypes = ["user_upload", "builtin"] as const;

const loadingRecipes = ref(false);
const detailLoading = ref(false);
const savingRecipe = ref(false);
const archivingRecipe = ref(false);
const bulkUpdatingRecipes = ref(false);
const recipeLogsLoading = ref(false);
const drawerOpen = ref(false);
const recipeTableRef = ref<any>();
const recipes = ref<any[]>([]);
const selectedRecipe = ref<any | null>(null);
const selectedRecipeIds = ref<number[]>([]);
const recipeLogs = ref<any[]>([]);
const filtersExpanded = ref(false);
const focusPreset = ref<RecipeFocusPreset>("all");
const syncingRoute = ref(false);

const filters = reactive({
  keyword: "",
  status: "",
  auditStatus: "",
  sourceType: "",
});

const recipeDraft = reactive({
  title: "",
  description: "",
  meal_type: "lunch",
  status: "draft",
  audit_status: "pending",
  source_type: "user_upload",
  source_name: "",
  is_premium: false,
});

const hasOpsUser = computed(() => hasOpsAccess(auth.user));
const pendingAuditCount = computed(() => recipes.value.filter((item) => item.audit_status === "pending").length);
const draftLikeCount = computed(() => recipes.value.filter((item) => item.status !== "published").length);
const incompleteCount = computed(() => recipes.value.filter((item) => recipeCompleteness(item) < 70).length);
const focusCards = computed(() => [
  {
    key: "pending" as const,
    label: "待审核",
    value: pendingAuditCount.value,
    copy: pendingAuditCount.value > 0 ? "优先复核描述、食材和营养信息。" : "当前列表没有明显待审核堆积。",
  },
  {
    key: "draft" as const,
    label: "草稿 / 非发布",
    value: draftLikeCount.value,
    copy: draftLikeCount.value > 0 ? "这些菜谱还没有真正进入用户主链路。" : "当前列表发布状态相对稳定。",
  },
  {
    key: "incomplete" as const,
    label: "信息待补齐",
    value: incompleteCount.value,
    copy: incompleteCount.value > 0 ? "这部分会影响用户决策和前台展示质量。" : "当前列表内容完整度还算稳定。",
  },
  {
    key: "user_upload" as const,
    label: "用户上传",
    value: recipes.value.filter((item) => item.source_type === "user_upload").length,
    copy: "这部分更需要后台把审核口径和质量边界看清楚。",
  },
]);
const focusPresetLabel = computed(() => ({
  all: "全部菜谱",
  pending: "待审核菜谱",
  draft: "草稿 / 非发布菜谱",
  incomplete: "信息待补齐菜谱",
  user_upload: "用户上传菜谱",
}[focusPreset.value]));
const filterHint = computed(() => {
  if (focusPreset.value === "all") return "先定位菜名、状态、审核结论和来源，再决定这批内容是否应继续发布。";
  return `当前聚焦：${focusPresetLabel.value}。先把这一批处理完，再回到全量视角。`;
});
const recipeFilterSummary = computed(() => {
  const items = [];
  if (focusPreset.value !== "all") items.push(`视角：${focusPresetLabel.value}`);
  if (filters.keyword) items.push(`搜索：${filters.keyword}`);
  if (filters.status) items.push(`状态：${statusLabel(filters.status)}`);
  if (filters.auditStatus) items.push(`审核：${auditLabel(filters.auditStatus)}`);
  if (filters.sourceType) items.push(`来源：${sourceLabel(filters.sourceType)}`);
  return items.length ? items : ["当前无额外筛选"];
});
const displayRecipes = computed(() => {
  let items = [...recipes.value];

  if (filters.keyword) {
    const keyword = filters.keyword.toLowerCase();
    items = items.filter((item) =>
      [item.title, item.description, item.source_name, ...(item.taste_tags || []), ...(item.cuisine_tags || [])]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(keyword)),
    );
  }

  if (filters.status) {
    items = items.filter((item) => item.status === filters.status);
  }
  if (filters.auditStatus) {
    items = items.filter((item) => item.audit_status === filters.auditStatus);
  }
  if (filters.sourceType) {
    items = items.filter((item) => item.source_type === filters.sourceType);
  }

  switch (focusPreset.value) {
    case "pending":
      items = items.filter((item) => item.audit_status === "pending");
      break;
    case "draft":
      items = items.filter((item) => item.status !== "published");
      break;
    case "incomplete":
      items = items.filter((item) => recipeCompleteness(item) < 70);
      break;
    case "user_upload":
      items = items.filter((item) => item.source_type === "user_upload");
      break;
  }

  return items.sort((a, b) => `${b.updated_at || ""}`.localeCompare(`${a.updated_at || ""}`));
});
const drawerTitle = computed(() => (selectedRecipe.value ? `处理菜谱：${selectedRecipe.value.title}` : "处理菜谱"));
const recipeFocusTitle = computed(() => {
  if (!selectedRecipe.value) return "先打开一份菜谱";
  if (recipeDraft.audit_status === "pending") return "这份菜谱还需要后台给出审核结论";
  if (recipeDraft.audit_status === "rejected") return "这份菜谱当前不建议直接给用户使用";
  if (recipeDraft.status !== "published") return "这份菜谱还没有进入正式发布状态";
  if (recipeCompleteness(selectedRecipe.value) < 70) return "这份菜谱内容结构还不够完整";
  return "这份菜谱当前状态相对稳定";
});
const recipeChecklist = computed(() => {
  if (!selectedRecipe.value) return [];
  const list = [];
  if (!recipeDraft.description) list.push("描述为空时，前台用户很难快速判断这份菜谱适不适合当前场景。");
  if (!(selectedRecipe.value.ingredients?.length)) list.push("食材清单为空时，不建议直接发布给用户使用。");
  if (!(selectedRecipe.value.steps?.length)) list.push("步骤说明缺失时，建议先补齐再继续发布。");
  if (!selectedRecipe.value.nutrition_summary) list.push("缺少营养信息时，前台推荐与报表解释会失真。");
  if (recipeDraft.audit_status === "pending") list.push("当前仍是待审核状态，处理后建议明确改成通过或驳回。");
  if (!list.length) list.push("这份菜谱基础信息比较完整，可以做常规状态维护。");
  return list;
});

watch(
  () => route.query,
  (query) => {
    if (syncingRoute.value) return;
    applyRouteQuery(query as Record<string, unknown>);
    if (hasOpsUser.value) {
      void loadRecipes();
    }
  },
  { immediate: true },
);

watch(
  hasOpsUser,
  (value) => {
    if (value && !recipes.value.length) {
      void loadRecipes();
    }
  },
  { immediate: false },
);

function readQueryText(value: unknown) {
  if (typeof value === "string") return value;
  if (Array.isArray(value) && typeof value[0] === "string") return value[0];
  return "";
}

function normalizeFocusPreset(value: string): RecipeFocusPreset {
  return recipeFocusPresets.includes(value as RecipeFocusPreset) ? (value as RecipeFocusPreset) : "all";
}

function normalizeRecipeStatus(value: string) {
  return recipeStatuses.includes(value as (typeof recipeStatuses)[number]) ? value : "";
}

function normalizeRecipeAuditStatus(value: string) {
  return recipeAuditStatuses.includes(value as (typeof recipeAuditStatuses)[number]) ? value : "";
}

function normalizeRecipeSourceType(value: string) {
  return recipeSourceTypes.includes(value as (typeof recipeSourceTypes)[number]) ? value : "";
}

function applyRouteQuery(query: Record<string, unknown>) {
  focusPreset.value = normalizeFocusPreset(readQueryText(query.preset));
  filters.keyword = readQueryText(query.keyword);
  filters.status = normalizeRecipeStatus(readQueryText(query.status));
  filters.auditStatus = normalizeRecipeAuditStatus(readQueryText(query.audit_status));
  filters.sourceType = normalizeRecipeSourceType(readQueryText(query.source_type));
}

function buildRouteQuery() {
  const query: Record<string, string> = {};
  if (focusPreset.value !== "all") query.preset = focusPreset.value;
  if (filters.keyword) query.keyword = filters.keyword;
  if (filters.status) query.status = filters.status;
  if (filters.auditStatus) query.audit_status = filters.auditStatus;
  if (filters.sourceType) query.source_type = filters.sourceType;
  return query;
}

function syncRouteFromState() {
  syncingRoute.value = true;
  return Promise.resolve(router.replace({ query: buildRouteQuery() })).finally(() => {
    syncingRoute.value = false;
  });
}

function unwrapListPayload(payload: any) {
  if (Array.isArray(payload?.data?.items)) return payload.data.items;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload)) return payload;
  return [];
}

async function loadRecipes() {
  if (!hasOpsUser.value) return;

  loadingRecipes.value = true;
  try {
    const response = await listRecipes();
    recipes.value = unwrapListPayload(response);
    await nextTick();
    clearRecipeSelection();
  } catch {
    notifyLoadError("菜谱列表");
  } finally {
    loadingRecipes.value = false;
  }
}

function handleRecipeSelectionChange(rows: any[]) {
  selectedRecipeIds.value = rows.map((item) => Number(item.id)).filter((id) => Number.isInteger(id) && id > 0);
}

function clearRecipeSelection() {
  selectedRecipeIds.value = [];
  recipeTableRef.value?.clearSelection?.();
}

async function applyBulkRecipeAction(action: "approve" | "reject" | "archive") {
  if (!selectedRecipeIds.value.length) return;

  const ids = [...selectedRecipeIds.value];
  bulkUpdatingRecipes.value = true;
  try {
    await bulkUpdateRecipes({ ids, action });
    notifyActionSuccess(
      action === "approve"
        ? `已批量通过 ${ids.length} 份菜谱`
        : action === "reject"
          ? `已批量驳回 ${ids.length} 份菜谱`
          : `已批量归档 ${ids.length} 份菜谱`,
    );
    await loadRecipes();
    if (selectedRecipe.value && ids.includes(selectedRecipe.value.id)) {
      await openRecipeDrawer(selectedRecipe.value.id);
    }
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "批量处理菜谱失败"));
  } finally {
    bulkUpdatingRecipes.value = false;
  }
}

function resetFilters() {
  filters.keyword = "";
  filters.status = "";
  filters.auditStatus = "";
  filters.sourceType = "";
  focusPreset.value = "all";
  filtersExpanded.value = false;
  void syncRouteFromState();
}

function applyFilters() {
  filtersExpanded.value = false;
  void syncRouteFromState();
}

function fillDraft(recipe: Record<string, any>) {
  Object.assign(recipeDraft, {
    title: recipe.title || "",
    description: recipe.description || "",
    meal_type: recipe.meal_type || "lunch",
    status: recipe.status || "draft",
    audit_status: recipe.audit_status || "pending",
    source_type: recipe.source_type || "user_upload",
    source_name: recipe.source_name || "",
    is_premium: recipe.is_premium ?? false,
  });
}

async function openRecipeDrawer(recipeId: number) {
  drawerOpen.value = true;
  detailLoading.value = true;
  selectedRecipe.value = null;
  recipeLogs.value = [];

  try {
    const response = await getRecipeDetail(recipeId);
    selectedRecipe.value = response?.data ?? null;
    if (selectedRecipe.value) {
      fillDraft(selectedRecipe.value);
      void loadRecipeLogs(selectedRecipe.value.id);
    }
  } catch {
    notifyLoadError("菜谱详情");
    drawerOpen.value = false;
  } finally {
    detailLoading.value = false;
  }
}

async function saveRecipe() {
  if (!selectedRecipe.value) return;

  savingRecipe.value = true;
  try {
    const response = await updateRecipe(selectedRecipe.value.id, { ...recipeDraft });
    selectedRecipe.value = response?.data ?? null;
    if (selectedRecipe.value) {
      fillDraft(selectedRecipe.value);
      await loadRecipeLogs(selectedRecipe.value.id);
    }
    notifyActionSuccess("菜谱状态已经更新");
    await loadRecipes();
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "这次没有成功更新菜谱状态"));
  } finally {
    savingRecipe.value = false;
  }
}

async function archiveRecipe() {
  if (!selectedRecipe.value) return;

  archivingRecipe.value = true;
  try {
    await deleteRecipe(selectedRecipe.value.id);
    notifyActionSuccess("菜谱已经归档");
    drawerOpen.value = false;
    selectedRecipe.value = null;
    await loadRecipes();
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "菜谱归档失败，请稍后重试"));
  } finally {
    archivingRecipe.value = false;
  }
}

async function loadRecipeLogs(recipeId: number) {
  recipeLogsLoading.value = true;
  try {
    const response = await listAdminOperationLogs({
      page: 1,
      page_size: 6,
      target_type: "recipe",
      target_id: recipeId,
    });
    recipeLogs.value = response?.data?.items || response?.items || [];
  } catch {
    recipeLogs.value = [];
  } finally {
    recipeLogsLoading.value = false;
  }
}

function applyFocusPreset(preset: RecipeFocusPreset) {
  focusPreset.value = preset;
  void syncRouteFromState();
}

function recipeCompleteness(recipe: Record<string, any>) {
  const checks = [
    Boolean(recipe.title),
    Boolean(recipe.description),
    Boolean(recipe.meal_type),
    Boolean(recipe.ingredients?.length),
    Boolean(recipe.steps?.length),
    Boolean(recipe.nutrition_summary),
  ];
  return Math.round((checks.filter(Boolean).length / checks.length) * 100);
}

function recipeSignals(recipe: Record<string, any>) {
  const items = [];
  if (recipe.audit_status === "pending") items.push("待审核");
  if (recipe.audit_status === "rejected") items.push("已驳回");
  if (recipe.status !== "published") items.push("未正式发布");
  if (recipeCompleteness(recipe) < 70) items.push("信息待补齐");
  if (recipe.source_type === "user_upload") items.push("用户上传");
  return items.length ? items : ["状态稳定"];
}

function mealTypeLabel(value?: string) {
  return (
    {
      breakfast: "早餐",
      lunch: "午餐",
      dinner: "晚餐",
      snack: "加餐",
    }[value || ""] || "未分类"
  );
}

function recipeTimeLabel(recipe: Record<string, any>) {
  const total = Number(recipe.cook_time_minutes || 0) + Number(recipe.prep_time_minutes || 0);
  return total > 0 ? `${total} 分钟` : "时间未填";
}

function statusLabel(value: string) {
  return (
    {
      draft: "草稿",
      published: "已发布",
    }[value] || value
  );
}

function auditLabel(value: string) {
  return (
    {
      pending: "待审核",
      approved: "已通过",
      rejected: "已驳回",
    }[value] || value
  );
}

function sourceLabel(value: string) {
  return (
    {
      user_upload: "用户上传",
      builtin: "系统内置",
    }[value] || value || "未标记"
  );
}

function statusTagType(value: string) {
  return (
    {
      published: "success",
      draft: "warning",
    }[value] || "info"
  );
}

function auditTagType(value: string) {
  return (
    {
      approved: "success",
      pending: "warning",
      rejected: "danger",
    }[value] || "info"
  );
}

function completionToneLabel(value: number) {
  if (value >= 85) return "完整";
  if (value >= 70) return "可用";
  return "待补齐";
}

function completionToneClass(value: number) {
  if (value >= 85) return "tone-good";
  if (value >= 70) return "tone-mid";
  return "tone-risk";
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
</script>

<style scoped>
.admin-recipes {
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

.bulk-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(240, 248, 252, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.08);
  color: #476072;
}

.bulk-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

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

.table-meta {
  color: #6a8898;
  font-size: 13px;
  white-space: nowrap;
}

.toolbar-grid {
  display: grid;
  grid-template-columns: minmax(220px, 1.8fr) repeat(3, minmax(160px, 0.8fr)) auto;
  gap: 12px;
}

.recipe-cell,
.meta-cell,
.completion-cell,
.judgement-cell {
  display: grid;
  gap: 4px;
}

.recipe-cell strong,
.completion-cell strong {
  color: #173042;
}

.recipe-cell span,
.meta-cell span,
.judgement-cell span {
  color: #5b7888;
  font-size: 13px;
  line-height: 1.5;
}

.completion-cell small {
  font-size: 12px;
}

.tone-good {
  color: #178048;
}

.tone-mid {
  color: #1f6286;
}

.tone-risk {
  color: #b45309;
}

.drawer-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 18px;
}

.drawer-summary article,
.recipe-structure-grid article {
  padding: 14px;
  border-radius: 16px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.08);
  display: grid;
  gap: 6px;
}

.drawer-summary span,
.recipe-structure-grid span {
  color: #5b7888;
  font-size: 12px;
}

.drawer-summary strong,
.recipe-structure-grid strong {
  color: #173042;
  font-size: 15px;
}

.drawer-focus {
  display: grid;
  gap: 12px;
  margin-bottom: 18px;
  padding: 18px;
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(23, 48, 66, 0.96), rgba(40, 84, 107, 0.92)),
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.12), transparent 38%);
}

.drawer-focus-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.drawer-focus-head strong {
  color: #fff;
  font-size: 16px;
}

.drawer-focus-head span {
  color: rgba(242, 247, 251, 0.82);
  font-size: 13px;
}

.drawer-focus-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.drawer-focus-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  font-size: 12px;
}

.drawer-checklist {
  margin: 0;
  padding-left: 18px;
  color: rgba(242, 247, 251, 0.86);
  display: grid;
  gap: 8px;
  line-height: 1.65;
}

.drawer-form {
  display: grid;
  gap: 18px;
}

.drawer-section {
  padding: 18px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.94);
  border: 1px solid rgba(16, 34, 42, 0.08);
}

.drawer-section-head {
  display: grid;
  gap: 6px;
  margin-bottom: 14px;
}

.drawer-section-head strong {
  color: #173042;
  font-size: 16px;
}

.drawer-section-head span {
  color: #5b7888;
  font-size: 13px;
  line-height: 1.6;
}

.recipe-structure-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.jump-link {
  display: inline-flex;
  margin-top: 14px;
  color: #1f4f67;
  text-decoration: none;
  font-weight: 700;
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}

@media (max-width: 1120px) {
  .focus-strip,
  .toolbar-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .drawer-summary,
  .recipe-structure-grid {
    grid-template-columns: 1fr;
  }
}
</style>
