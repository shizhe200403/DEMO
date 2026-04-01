<template>
  <section class="page admin-page">
    <div class="head">
      <div>
        <p class="tag">Admin</p>
        <h2>用户管理</h2>
      </div>
      <div class="head-actions">
        <el-button plain @click="resetFilters">重置筛选</el-button>
        <el-button type="primary" :loading="loadingUsers" @click="applyFilters">应用筛选</el-button>
      </div>
    </div>

    <PageStateBlock
      v-if="auth.isAuthenticated && !auth.user"
      tone="loading"
      title="正在确认管理员身份"
      description="先把当前账号权限核对清楚，再展开后台内容。"
      compact
    />
    <PageStateBlock
      v-else-if="!isAdminUser"
      tone="error"
      title="当前账号没有后台权限"
      description="用户管理只对管理员开放，普通账号不会显示这块后台能力。"
      action-label="回到首页"
      @action="router.push('/')"
    />
    <template v-else>
      <CollectionSkeleton v-if="loadingUsers && !users.length" variant="list" :card-count="5" />
      <RefreshFrame v-else :active="loadingUsers && !!users.length" label="正在同步用户列表与筛选结果">
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
              <h3>筛选与搜索</h3>
              <p>{{ filterHint }}</p>
            </div>
            <el-button v-if="focusPreset !== 'all'" text type="primary" @click="applyFocusPreset('all')">回到全部视角</el-button>
          </div>
          <div class="toolbar-grid">
            <el-input v-model.trim="filters.keyword" placeholder="搜索用户名 / 昵称 / 邮箱 / 手机号" clearable @keyup.enter="applyFilters" />
            <el-select v-model="filters.role" clearable placeholder="筛选角色">
              <el-option label="普通用户" value="user" />
              <el-option label="管理员" value="admin" />
              <el-option label="审核员" value="auditor" />
            </el-select>
            <el-select v-model="filters.status" clearable placeholder="筛选状态">
              <el-option label="正常" value="active" />
              <el-option label="已停用" value="disabled" />
              <el-option label="待处理" value="pending" />
            </el-select>
            <el-button type="primary" :loading="loadingUsers" @click="applyFilters">应用筛选</el-button>
          </div>
        </div>

        <div class="card table-card" v-spotlight>
          <div class="card-head">
            <div>
              <h3>用户列表</h3>
              <p>默认按注册时间倒序展示。现在聚焦的是{{ focusPresetLabel }}，适合先处理这一批账号。</p>
            </div>
            <span class="table-meta">当前页显示 {{ displayUsers.length }} / {{ users.length }} 人</span>
          </div>

          <div v-if="selectedUserIds.length" class="bulk-bar">
            <span>已选 {{ selectedUserIds.length }} 个账号，可直接批量启用或停用。</span>
            <div class="bulk-actions">
              <el-button :disabled="bulkUpdatingUsers" @click="clearUserSelection">清空选择</el-button>
              <el-button type="success" :loading="bulkUpdatingUsers" @click="applyBulkUserStatus('active')">批量启用</el-button>
              <el-button type="danger" :loading="bulkUpdatingUsers" @click="applyBulkUserStatus('disabled')">批量停用</el-button>
            </div>
          </div>

          <el-table ref="userTableRef" :data="displayUsers" :row-key="(row: any) => row.id" stripe class="user-table" empty-text="当前筛选下没有用户" @selection-change="handleUserSelectionChange">
            <el-table-column type="selection" width="48" />
            <el-table-column label="用户" min-width="200">
              <template #default="{ row }">
                <div class="user-cell">
                  <strong>{{ row.nickname || row.username }}</strong>
                  <span>@{{ row.username }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="联系方式" min-width="220">
              <template #default="{ row }">
                <div class="contact-cell">
                  <span>{{ row.email || "未填写邮箱" }}</span>
                  <span>{{ row.phone || "未填写手机号" }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="角色" width="120">
              <template #default="{ row }">
                <el-tag :type="roleTagType(row.role)" effect="light">{{ roleLabel(row.role) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" effect="light">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="档案完整度" width="140">
              <template #default="{ row }">
                <div class="completion-cell">
                  <strong>{{ row.profile_completion }}%</strong>
                  <small :class="completionToneClass(row.profile_completion)">{{ completionToneLabel(row.profile_completion) }}</small>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="健康提示" min-width="180">
              <template #default="{ row }">
                <div class="flag-cell">
                  <el-tag v-for="item in row.health_flags" :key="item" size="small" type="warning" effect="plain">{{ item }}</el-tag>
                  <span v-if="!row.health_flags?.length" class="muted-copy">暂无特殊标记</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="最近登录" width="170">
              <template #default="{ row }">
                <span>{{ formatDateTime(row.last_login) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="管理判断" min-width="180">
              <template #default="{ row }">
                <div class="judgement-cell">
                  <span v-for="item in userJudgement(row)" :key="item">{{ item }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" fixed="right" width="140">
              <template #default="{ row }">
                <el-button text type="primary" @click="openUserDrawer(row.id)">查看并处理</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="table-footer">
            <span>当前第 {{ pagination.page }} 页，共 {{ pagination.total }} 个账号；当前视角下本页显示 {{ displayUsers.length }} 个。</span>
            <el-pagination
              background
              layout="prev, pager, next"
              :current-page="pagination.page"
              :page-size="pagination.pageSize"
              :total="pagination.total"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </RefreshFrame>

      <el-drawer v-model="drawerOpen" size="560px" :title="drawerTitle" destroy-on-close>
        <PageStateBlock
          v-if="detailLoading"
          tone="loading"
          title="正在加载用户详情"
          description="把这个账号的资料、状态和健康约束拉齐后再允许编辑。"
          compact
        />
        <PageStateBlock
          v-else-if="!selectedUser"
          tone="empty"
          title="还没有选中用户"
          description="从列表里点开一个账号，右侧就会展开详细资料。"
          compact
        />
        <template v-else>
          <div class="drawer-summary">
            <article v-spotlight>
              <span>注册时间</span>
              <strong>{{ formatDateTime(selectedUser.date_joined) }}</strong>
            </article>
            <article v-spotlight>
              <span>最近登录</span>
              <strong>{{ formatDateTime(selectedUser.last_login) }}</strong>
            </article>
            <article v-spotlight>
              <span>当前角色</span>
              <strong>{{ roleLabel(accountDraft.role) }}</strong>
            </article>
          </div>

          <div class="drawer-focus" v-spotlight>
            <div class="drawer-focus-head">
              <strong>当前管理判断</strong>
              <span>{{ drawerFocusTitle }}</span>
            </div>
            <div class="drawer-focus-tags">
              <span v-for="item in selectedUserSignals" :key="item" class="drawer-focus-tag">{{ item }}</span>
            </div>
            <ul class="drawer-checklist">
              <li v-for="item in selectedUserChecklist" :key="item">{{ item }}</li>
            </ul>
          </div>

          <el-form label-position="top" class="drawer-form">
            <div class="drawer-section" v-spotlight>
              <div class="drawer-section-head">
                <strong>账号信息</strong>
                <span>角色、状态和联系方式优先在这里处理。</span>
              </div>
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="用户名">
                    <el-input v-model.trim="accountDraft.username" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="昵称">
                    <el-input v-model.trim="accountDraft.nickname" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="邮箱">
                    <el-input v-model.trim="accountDraft.email" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="手机号">
                    <el-input v-model.trim="accountDraft.phone" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="角色">
                    <el-select v-model="accountDraft.role" style="width: 100%">
                      <el-option label="普通用户" value="user" />
                      <el-option label="管理员" value="admin" />
                      <el-option label="审核员" value="auditor" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="状态">
                    <el-select v-model="accountDraft.status" style="width: 100%">
                      <el-option label="正常" value="active" />
                      <el-option label="已停用" value="disabled" />
                      <el-option label="待处理" value="pending" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="个性签名">
                <el-input v-model.trim="accountDraft.signature" type="textarea" :rows="2" />
              </el-form-item>
            </div>

            <div class="drawer-section" v-spotlight>
              <div class="drawer-section-head">
                <strong>生活方式</strong>
                <span>这些信息会直接影响推荐、目标和今日建议的判断。</span>
              </div>
              <el-row :gutter="12">
                <el-col :span="8">
                  <el-form-item label="身高(cm)">
                    <el-input-number v-model="profileDraft.height_cm" :min="0" :precision="1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="体重(kg)">
                    <el-input-number v-model="profileDraft.weight_kg" :min="0" :precision="1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="目标体重(kg)">
                    <el-input-number v-model="profileDraft.target_weight_kg" :min="0" :precision="1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="活动水平">
                    <el-select v-model="profileDraft.activity_level" style="width: 100%">
                      <el-option label="久坐为主" value="low" />
                      <el-option label="轻度活动" value="medium" />
                      <el-option label="经常运动" value="high" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="饮食偏好">
                    <el-select v-model="profileDraft.meal_preference" style="width: 100%">
                      <el-option label="家常清淡" value="light_home" />
                      <el-option label="高蛋白优先" value="high_protein" />
                      <el-option label="低脂控能量" value="low_fat" />
                      <el-option label="省时方便" value="fast_easy" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="饮食类型">
                    <el-select v-model="profileDraft.diet_type" style="width: 100%">
                      <el-option label="均衡饮食" value="balanced" />
                      <el-option label="高蛋白" value="high_protein" />
                      <el-option label="低碳水" value="low_carb" />
                      <el-option label="素食" value="vegetarian" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="职业">
                    <el-input v-model.trim="profileDraft.occupation" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="外食频率">
                <el-switch v-model="profileDraft.is_outdoor_eating_frequent" active-text="经常外食" inactive-text="以家里吃饭为主" />
              </el-form-item>
            </div>

            <div class="drawer-section" v-spotlight>
              <div class="drawer-section-head">
                <strong>健康约束</strong>
                <span>这些约束会直接影响推荐和风险提醒，不适合留空太久。</span>
              </div>
              <div class="toggle-grid">
                <el-checkbox v-model="healthDraft.has_diabetes">糖尿病</el-checkbox>
                <el-checkbox v-model="healthDraft.has_hypertension">高血压</el-checkbox>
                <el-checkbox v-model="healthDraft.has_hyperlipidemia">高血脂</el-checkbox>
                <el-checkbox v-model="healthDraft.has_allergy">存在过敏项</el-checkbox>
              </div>
              <el-form-item label="过敏标签">
                <el-select
                  v-model="healthDraft.allergy_tags"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  style="width: 100%"
                  placeholder="输入后回车，可添加多个"
                >
                  <el-option v-for="item in allergyOptions" :key="item" :label="item" :value="item" />
                </el-select>
              </el-form-item>
              <el-form-item label="忌口标签">
                <el-select
                  v-model="healthDraft.avoid_food_tags"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  style="width: 100%"
                  placeholder="输入后回车，可添加多个"
                >
                  <el-option v-for="item in avoidFoodOptions" :key="item" :label="item" :value="item" />
                </el-select>
              </el-form-item>
              <el-form-item label="备注">
                <el-input v-model.trim="healthDraft.notes" type="textarea" :rows="3" />
              </el-form-item>
            </div>
          </el-form>

          <div class="drawer-section" v-spotlight>
            <AdminObjectTimeline
              object-label="这个用户"
              :logs="userLogs"
              :loading="userLogsLoading"
              title="最近处理回放"
              description="直接看这位用户最近被谁改过哪些资料、状态和健康约束。"
            />
          </div>

          <div class="drawer-actions">
            <el-button plain @click="drawerOpen = false">取消</el-button>
            <el-button type="primary" :loading="savingUser" @click="saveUser">保存修改</el-button>
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
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { bulkUpdateAdminUsers, getAdminUserDetail, listAdminUsers, updateAdminUser } from "../api/admin";
import { listAdminOperationLogs } from "../api/adminLogs";
import { extractApiErrorMessage, notifyActionSuccess, notifyErrorMessage, notifyLoadError } from "../lib/feedback";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

type UserFocusPreset = "all" | "pending" | "disabled" | "incomplete" | "flagged";

const userFocusPresets: UserFocusPreset[] = ["all", "pending", "disabled", "incomplete", "flagged"];
const userRoles = ["user", "admin", "auditor"] as const;
const userStatuses = ["active", "disabled", "pending"] as const;

const loadingUsers = ref(false);
const detailLoading = ref(false);
const savingUser = ref(false);
const bulkUpdatingUsers = ref(false);
const userLogsLoading = ref(false);
const drawerOpen = ref(false);
const userTableRef = ref<any>();
const users = ref<any[]>([]);
const selectedUser = ref<any | null>(null);
const selectedUserIds = ref<number[]>([]);
const userLogs = ref<any[]>([]);
const focusPreset = ref<UserFocusPreset>("all");
const syncingRoute = ref(false);

const filters = reactive({
  keyword: "",
  role: "",
  status: "",
});

const pagination = reactive({
  page: 1,
  pageSize: 12,
  total: 0,
});

const accountDraft = reactive({
  username: "",
  nickname: "",
  email: "",
  phone: "",
  signature: "",
  role: "user",
  status: "active",
});

const profileDraft = reactive({
  height_cm: null as number | null,
  weight_kg: null as number | null,
  target_weight_kg: null as number | null,
  activity_level: "medium",
  meal_preference: "light_home",
  diet_type: "balanced",
  occupation: "",
  is_outdoor_eating_frequent: false,
});

const healthDraft = reactive({
  has_diabetes: false,
  has_hypertension: false,
  has_hyperlipidemia: false,
  has_allergy: false,
  allergy_tags: [] as string[],
  avoid_food_tags: [] as string[],
  notes: "",
});

const allergyOptions = ["花生", "牛奶", "鸡蛋", "海鲜", "坚果"];
const avoidFoodOptions = ["辛辣", "油炸", "高糖", "高盐", "酒精"];

const isAdminUser = computed(() => Boolean(auth.user && (auth.user.role === "admin" || auth.user.is_superuser || auth.user.is_staff)));
const disabledCount = computed(() => users.value.filter((item) => item.status === "disabled").length);
const pendingCount = computed(() => users.value.filter((item) => item.status === "pending").length);
const flaggedCount = computed(() => users.value.filter((item) => Array.isArray(item.health_flags) && item.health_flags.length > 0).length);
const incompleteCount = computed(() => users.value.filter((item) => Number(item.profile_completion || 0) < 70).length);
const drawerTitle = computed(() => (selectedUser.value ? `编辑用户：${selectedUser.value.nickname || selectedUser.value.username}` : "编辑用户"));
const focusCards = computed(() => [
  {
    key: "pending" as const,
    label: "待处理",
    value: pendingCount.value,
    copy: pendingCount.value > 0 ? "优先确认资料缺口或权限异常。" : "当前页没有明显待处理堆积。",
  },
  {
    key: "disabled" as const,
    label: "已停用",
    value: disabledCount.value,
    copy: disabledCount.value > 0 ? "适合复核是否误伤或需要恢复。" : "当前页没有停用聚集。",
  },
  {
    key: "incomplete" as const,
    label: "资料未满 70%",
    value: incompleteCount.value,
    copy: incompleteCount.value > 0 ? "这部分会直接拉低个性化建议质量。" : "当前页资料完整度还算稳定。",
  },
  {
    key: "flagged" as const,
    label: "有健康标记",
    value: flaggedCount.value,
    copy: flaggedCount.value > 0 ? "需要更关注饮食边界和风险提示。" : "当前页暂无明显健康约束聚集。",
  },
]);
const focusPresetLabel = computed(() => ({
  all: "全部账号",
  pending: "待处理账号",
  disabled: "停用账号",
  incomplete: "资料待补齐账号",
  flagged: "有健康标记账号",
}[focusPreset.value]));
const filterHint = computed(() => {
  if (focusPreset.value === "all") return "先快速定位用户名、邮箱或手机号，再看角色和状态。";
  return `当前聚焦：${focusPresetLabel.value}。先把这一批处理掉，再回到全量视角。`;
});
const displayUsers = computed(() => {
  switch (focusPreset.value) {
    case "pending":
      return users.value.filter((item) => item.status === "pending");
    case "disabled":
      return users.value.filter((item) => item.status === "disabled");
    case "incomplete":
      return users.value.filter((item) => Number(item.profile_completion || 0) < 70);
    case "flagged":
      return users.value.filter((item) => Array.isArray(item.health_flags) && item.health_flags.length > 0);
    default:
      return users.value;
  }
});
const selectedUserSignals = computed(() => {
  if (!selectedUser.value) return [];

  const items = [
    `状态：${statusLabel(accountDraft.status)}`,
    `角色：${roleLabel(accountDraft.role)}`,
    `档案完整度：${selectedUser.value.profile_completion || 0}%`,
  ];
  if (selectedUser.value.email || selectedUser.value.phone) {
    items.push("联系方式已填写");
  } else {
    items.push("联系方式待补齐");
  }
  if (selectedUser.value.health_flags?.length) {
    items.push(`健康标记：${selectedUser.value.health_flags.join("、")}`);
  }
  return items;
});
const drawerFocusTitle = computed(() => {
  if (!selectedUser.value) return "先打开一个账号";
  if (accountDraft.status === "pending") return "这位用户当前需要人工确认";
  if (accountDraft.status === "disabled") return "这位用户当前处于停用状态";
  if (Number(selectedUser.value.profile_completion || 0) < 70) return "这位用户的资料完整度仍偏低";
  return "这位用户的基础状态相对稳定";
});
const selectedUserChecklist = computed(() => {
  if (!selectedUser.value) return [];

  const list = [];
  if (!accountDraft.email && !accountDraft.phone) {
    list.push("先确认至少留下一种联系方式，后续通知和排查会更顺。");
  }
  if (Number(selectedUser.value.profile_completion || 0) < 70) {
    list.push("这位用户的档案完整度还不够，建议优先补齐基础资料。");
  }
  if (selectedUser.value.health_flags?.length) {
    list.push("存在健康约束，检查推荐边界和忌口标签是否已经同步。");
  }
  if (accountDraft.role === "admin") {
    list.push("这是管理员账号，角色边界和状态修改前建议再次确认。");
  }
  if (!list.length) {
    list.push("当前账号没有明显风险堆积，可以做常规资料维护。");
  }
  return list;
});

watch(
  () => route.query,
  (query) => {
    if (syncingRoute.value) return;
    applyRouteQuery(query as Record<string, unknown>);
    if (isAdminUser.value) {
      void loadUsers();
    }
  },
  { immediate: true },
);

watch(
  isAdminUser,
  (value) => {
    if (value && !users.value.length) {
      void loadUsers();
    }
  },
  { immediate: false },
);

function readQueryText(value: unknown) {
  if (typeof value === "string") return value;
  if (Array.isArray(value) && typeof value[0] === "string") return value[0];
  return "";
}

function readQueryPositiveInt(value: unknown) {
  const numeric = Number(readQueryText(value));
  return Number.isInteger(numeric) && numeric > 0 ? numeric : 1;
}

function normalizeFocusPreset(value: string): UserFocusPreset {
  return userFocusPresets.includes(value as UserFocusPreset) ? (value as UserFocusPreset) : "all";
}

function normalizeUserRole(value: string) {
  return userRoles.includes(value as (typeof userRoles)[number]) ? value : "";
}

function normalizeUserStatus(value: string) {
  return userStatuses.includes(value as (typeof userStatuses)[number]) ? value : "";
}

function applyRouteQuery(query: Record<string, unknown>) {
  focusPreset.value = normalizeFocusPreset(readQueryText(query.preset));
  filters.keyword = readQueryText(query.keyword);
  filters.role = normalizeUserRole(readQueryText(query.role));
  filters.status = normalizeUserStatus(readQueryText(query.status));
  pagination.page = readQueryPositiveInt(query.page);
}

function buildRouteQuery() {
  const query: Record<string, string> = {};
  if (focusPreset.value !== "all") query.preset = focusPreset.value;
  if (filters.keyword) query.keyword = filters.keyword;
  if (filters.role) query.role = filters.role;
  if (filters.status) query.status = filters.status;
  if (pagination.page > 1) query.page = String(pagination.page);
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
  if (Array.isArray(payload)) return payload;
  return [];
}

function resetDrafts() {
  Object.assign(accountDraft, {
    username: "",
    nickname: "",
    email: "",
    phone: "",
    signature: "",
    role: "user",
    status: "active",
  });
  Object.assign(profileDraft, {
    height_cm: null,
    weight_kg: null,
    target_weight_kg: null,
    activity_level: "medium",
    meal_preference: "light_home",
    diet_type: "balanced",
    occupation: "",
    is_outdoor_eating_frequent: false,
  });
  Object.assign(healthDraft, {
    has_diabetes: false,
    has_hypertension: false,
    has_hyperlipidemia: false,
    has_allergy: false,
    allergy_tags: [],
    avoid_food_tags: [],
    notes: "",
  });
}

function fillDrafts(user: Record<string, any>) {
  Object.assign(accountDraft, {
    username: user.username || "",
    nickname: user.nickname || "",
    email: user.email || "",
    phone: user.phone || "",
    signature: user.signature || "",
    role: user.role || "user",
    status: user.status || "active",
  });
  Object.assign(profileDraft, {
    height_cm: user.profile?.height_cm ? Number(user.profile.height_cm) : null,
    weight_kg: user.profile?.weight_kg ? Number(user.profile.weight_kg) : null,
    target_weight_kg: user.profile?.target_weight_kg ? Number(user.profile.target_weight_kg) : null,
    activity_level: user.profile?.activity_level || "medium",
    meal_preference: user.profile?.meal_preference || "light_home",
    diet_type: user.profile?.diet_type || "balanced",
    occupation: user.profile?.occupation || "",
    is_outdoor_eating_frequent: Boolean(user.profile?.is_outdoor_eating_frequent),
  });
  Object.assign(healthDraft, {
    has_diabetes: Boolean(user.health_condition?.has_diabetes),
    has_hypertension: Boolean(user.health_condition?.has_hypertension),
    has_hyperlipidemia: Boolean(user.health_condition?.has_hyperlipidemia),
    has_allergy: Boolean(user.health_condition?.has_allergy),
    allergy_tags: Array.isArray(user.health_condition?.allergy_tags) ? [...user.health_condition.allergy_tags] : [],
    avoid_food_tags: Array.isArray(user.health_condition?.avoid_food_tags) ? [...user.health_condition.avoid_food_tags] : [],
    notes: user.health_condition?.notes || "",
  });
}

async function loadUsers() {
  if (!isAdminUser.value) return;

  loadingUsers.value = true;
  try {
    const response = await listAdminUsers({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      role: filters.role || undefined,
      status: filters.status || undefined,
    });
    users.value = unwrapListPayload(response);
    pagination.total = Number(response?.data?.count || 0);
    await nextTick();
    clearUserSelection();
  } catch {
    notifyLoadError("用户列表");
  } finally {
    loadingUsers.value = false;
  }
}

function applyFilters() {
  pagination.page = 1;
  void syncRouteFromState();
}

function resetFilters() {
  filters.keyword = "";
  filters.role = "";
  filters.status = "";
  pagination.page = 1;
  focusPreset.value = "all";
  void syncRouteFromState();
}

function handlePageChange(page: number) {
  pagination.page = page;
  void syncRouteFromState();
}

function handleUserSelectionChange(rows: any[]) {
  selectedUserIds.value = rows.map((item) => Number(item.id)).filter((id) => Number.isInteger(id) && id > 0);
}

function clearUserSelection() {
  selectedUserIds.value = [];
  userTableRef.value?.clearSelection?.();
}

async function applyBulkUserStatus(statusValue: "active" | "disabled") {
  if (!selectedUserIds.value.length) return;

  const ids = [...selectedUserIds.value];
  bulkUpdatingUsers.value = true;
  try {
    await bulkUpdateAdminUsers({ ids, status: statusValue });
    notifyActionSuccess(statusValue === "active" ? `已批量启用 ${ids.length} 个账号` : `已批量停用 ${ids.length} 个账号`);
    await auth.fetchMe();
    await loadUsers();
    if (selectedUser.value && ids.includes(selectedUser.value.id)) {
      await openUserDrawer(selectedUser.value.id);
    }
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "批量更新账号状态失败"));
  } finally {
    bulkUpdatingUsers.value = false;
  }
}

async function openUserDrawer(userId: number) {
  drawerOpen.value = true;
  detailLoading.value = true;
  selectedUser.value = null;
  userLogs.value = [];
  resetDrafts();

  try {
    const response = await getAdminUserDetail(userId);
    selectedUser.value = response?.data ?? null;
    if (selectedUser.value) {
      fillDrafts(selectedUser.value);
      void loadUserLogs(selectedUser.value.id);
    }
  } catch {
    notifyLoadError("用户详情");
    drawerOpen.value = false;
  } finally {
    detailLoading.value = false;
  }
}

async function saveUser() {
  if (!selectedUser.value) return;

  savingUser.value = true;
  try {
    const response = await updateAdminUser(selectedUser.value.id, {
      account: { ...accountDraft },
      profile: { ...profileDraft },
      health_condition: { ...healthDraft },
    });
    selectedUser.value = response?.data ?? null;
    if (selectedUser.value) {
      fillDrafts(selectedUser.value);
      await loadUserLogs(selectedUser.value.id);
    }
    notifyActionSuccess("用户资料已经更新");
    await auth.fetchMe();
    await loadUsers();
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "用户资料这次没有更新成功"));
  } finally {
    savingUser.value = false;
  }
}

function applyFocusPreset(preset: UserFocusPreset) {
  focusPreset.value = preset;
  pagination.page = 1;
  void syncRouteFromState();
}

async function loadUserLogs(userId: number) {
  userLogsLoading.value = true;
  try {
    const response = await listAdminOperationLogs({
      page: 1,
      page_size: 6,
      target_type: "user",
      target_id: userId,
    });
    userLogs.value = response?.data?.items || response?.items || [];
  } catch {
    userLogs.value = [];
  } finally {
    userLogsLoading.value = false;
  }
}

function roleLabel(value: string) {
  return (
    {
      user: "普通用户",
      admin: "管理员",
      auditor: "审核员",
    }[value] || value
  );
}

function statusLabel(value: string) {
  return (
    {
      active: "正常",
      disabled: "已停用",
      pending: "待处理",
    }[value] || value
  );
}

function roleTagType(value: string) {
  return (
    {
      admin: "danger",
      auditor: "warning",
      user: "info",
    }[value] || "info"
  );
}

function statusTagType(value: string) {
  return (
    {
      active: "success",
      disabled: "danger",
      pending: "warning",
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

function completionToneLabel(value: number | string) {
  const numeric = Number(value || 0);
  if (numeric >= 85) return "完整";
  if (numeric >= 70) return "可用";
  return "待补齐";
}

function completionToneClass(value: number | string) {
  const numeric = Number(value || 0);
  if (numeric >= 85) return "tone-good";
  if (numeric >= 70) return "tone-mid";
  return "tone-risk";
}

function userJudgement(user: Record<string, any>) {
  const items = [];
  if (user.status === "pending") items.push("待人工确认");
  if (user.status === "disabled") items.push("复核停用原因");
  if (Number(user.profile_completion || 0) < 70) items.push("资料待补齐");
  if (Array.isArray(user.health_flags) && user.health_flags.length) items.push("关注健康约束");
  if (user.role === "admin") items.push("注意权限边界");
  return items.length ? items : ["常规维护"];
}
</script>

<style scoped>
.admin-page {
  gap: 18px;
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

.head-actions {
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

.toolbar-grid {
  display: grid;
  grid-template-columns: minmax(220px, 1.8fr) repeat(2, minmax(160px, 0.9fr)) auto;
  gap: 12px;
}

.user-table {
  width: 100%;
}

.user-cell,
.contact-cell {
  display: grid;
  gap: 4px;
}

.user-cell strong {
  color: #173042;
}

.user-cell span,
.contact-cell span,
.muted-copy {
  color: #5b7888;
  font-size: 13px;
}

.flag-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.completion-cell,
.judgement-cell {
  display: grid;
  gap: 4px;
}

.completion-cell strong {
  color: #173042;
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

.judgement-cell span {
  color: #476072;
  font-size: 12px;
  line-height: 1.5;
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  color: #5b7888;
  font-size: 13px;
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

.drawer-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 18px;
}

.drawer-summary article {
  padding: 14px;
  border-radius: 16px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.08);
  display: grid;
  gap: 6px;
}

.drawer-summary span {
  color: #5b7888;
  font-size: 12px;
}

.drawer-summary strong {
  color: #173042;
  font-size: 15px;
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

.toggle-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}

@media (max-width: 960px) {
  .focus-strip,
  .toolbar-grid {
    grid-template-columns: 1fr;
  }

  .drawer-summary {
    grid-template-columns: 1fr;
  }

  .toggle-grid {
    grid-template-columns: 1fr;
  }
}
</style>
