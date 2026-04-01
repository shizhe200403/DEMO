<template>
  <section class="page admin-community">
    <div class="head">
      <div>
        <p class="tag">Community Moderation</p>
        <h2>社区审核</h2>
        <p class="desc">先把帖子审核、举报处理和评论隐藏收紧，再继续放大社区曝光。</p>
      </div>
      <div class="head-actions">
        <el-button plain @click="resetFilters">重置筛选</el-button>
        <el-button type="primary" :loading="loadingPosts || loadingReports" @click="refreshAll">刷新后台内容</el-button>
        <el-button plain @click="router.push('/community')">去前台社区页</el-button>
      </div>
    </div>

    <PageStateBlock
      v-if="auth.isAuthenticated && !auth.user"
      tone="loading"
      title="正在确认管理员身份"
      description="先把当前账号权限拉齐，再展开社区审核。"
      compact
    />
    <PageStateBlock
      v-else-if="!isAdminUser"
      tone="error"
      title="当前账号没有后台权限"
      description="社区审核只对管理员开放，普通账号不会显示这里。"
      action-label="回到首页"
      @action="router.push('/')"
    />
    <template v-else>
      <CollectionSkeleton v-if="showSkeleton" variant="list" :card-count="5" />
      <RefreshFrame v-else :active="loadingPosts || loadingReports" label="正在同步帖子与举报状态">
        <div class="summary-grid">
          <article v-spotlight>
            <span>帖子总数</span>
            <strong>{{ posts.length }}</strong>
            <p>后台当前可审看的帖子数量。</p>
          </article>
          <article v-spotlight>
            <span>待审核帖子</span>
            <strong>{{ pendingPostCount }}</strong>
            <p>适合优先确认是否继续发布。</p>
          </article>
          <article v-spotlight>
            <span>待处理举报</span>
            <strong>{{ pendingReportCount }}</strong>
            <p>这批举报建议尽快给出处理结论。</p>
          </article>
          <article v-spotlight>
            <span>已隐藏评论</span>
            <strong>{{ hiddenCommentCount }}</strong>
            <p>这能帮助判断社区风险是否开始积累。</p>
          </article>
        </div>

        <div class="focus-strip">
          <article
            v-for="item in focusCards"
            :key="item.key"
            class="focus-card"
            :class="{ active: focusPreset === item.key }"
            v-spotlight
            @click="focusPreset = item.key"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <p>{{ item.copy }}</p>
          </article>
        </div>

        <div class="admin-grid">
          <article class="card moderation-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>帖子审核</h3>
                <p>{{ postFilterHint }}</p>
              </div>
              <el-button v-if="focusPreset !== 'all'" text type="primary" @click="focusPreset = 'all'">回到全部视角</el-button>
            </div>
            <div class="toolbar-grid">
              <el-input v-model.trim="postFilters.keyword" placeholder="搜索标题、正文或作者" clearable @keyup.enter="loadPosts" />
              <el-select v-model="postFilters.status" clearable placeholder="状态">
                <el-option label="公开中" value="published" />
                <el-option label="已归档" value="archived" />
              </el-select>
              <el-select v-model="postFilters.auditStatus" clearable placeholder="审核">
                <el-option label="待审核" value="pending" />
                <el-option label="已通过" value="approved" />
                <el-option label="已驳回" value="rejected" />
              </el-select>
              <el-button type="primary" :loading="loadingPosts" @click="loadPosts">应用筛选</el-button>
            </div>

            <el-table :data="displayPosts" stripe class="moderation-table" empty-text="当前筛选下没有帖子">
              <el-table-column label="帖子" min-width="220">
                <template #default="{ row }">
                  <div class="content-cell">
                    <strong>{{ row.title }}</strong>
                    <span>{{ row.user_info?.display_name || row.user_info?.username || "用户" }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="120">
                <template #default="{ row }">
                  <el-tag :type="postStatusTagType(row.status)" effect="light">{{ postStatusLabel(row.status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="审核" width="120">
                <template #default="{ row }">
                  <el-tag :type="auditTagType(row.audit_status)" effect="light">{{ auditLabel(row.audit_status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="互动" width="120">
                <template #default="{ row }">
                  <div class="metric-cell">
                    <span>可见评 {{ row.visible_comment_count }}</span>
                    <span>隐藏评 {{ row.hidden_comment_count }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="举报" width="110">
                <template #default="{ row }">
                  <span>{{ row.report_count }} 条</span>
                </template>
              </el-table-column>
              <el-table-column label="管理判断" min-width="180">
                <template #default="{ row }">
                  <div class="judgement-cell">
                    <span v-for="item in postSignals(row)" :key="item">{{ item }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="150">
                <template #default="{ row }">
                  <el-button text type="primary" @click="openPostDrawer(row.id)">查看并处理</el-button>
                </template>
              </el-table-column>
            </el-table>
          </article>

          <article class="card report-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>举报处理</h3>
                <p>{{ reportFilterHint }}</p>
              </div>
            </div>
            <div class="toolbar-grid reports-toolbar">
              <el-input v-model.trim="reportFilters.keyword" placeholder="搜索举报原因或举报人" clearable @keyup.enter="loadReports" />
              <el-select v-model="reportFilters.status" clearable placeholder="处理状态">
                <el-option label="待处理" value="pending" />
                <el-option label="已处理" value="processed" />
                <el-option label="已驳回" value="rejected" />
              </el-select>
              <el-button type="primary" :loading="loadingReports" @click="loadReports">刷新举报</el-button>
            </div>

            <div v-if="displayReports.length" class="report-list">
              <article v-for="report in displayReports" :key="report.id" class="report-item">
                <div class="report-head">
                  <div>
                    <strong>{{ report.target_post_title || "帖子举报" }}</strong>
                    <span>{{ report.reporter_info?.display_name || report.reporter_info?.username || "用户" }} · {{ formatDateTime(report.created_at) }}</span>
                  </div>
                  <el-tag :type="reportStatusTagType(report.status)" effect="light">{{ reportStatusLabel(report.status) }}</el-tag>
                </div>
                <p>{{ report.reason }}</p>
                <div class="report-actions">
                  <el-button text @click="openReportDrawer(report.id)">查看详情</el-button>
                  <el-button text type="primary" :loading="reportActionId === report.id && reportAction === 'processed'" @click="updateReportStatus(report.id, 'processed')">标记已处理</el-button>
                  <el-button text type="danger" :loading="reportActionId === report.id && reportAction === 'rejected'" @click="updateReportStatus(report.id, 'rejected')">驳回举报</el-button>
                </div>
              </article>
            </div>
            <PageStateBlock
              v-else
              tone="empty"
              title="当前筛选下没有举报"
              description="可以切回全部视角，或稍后刷新看看新的处理任务。"
              compact
            />
          </article>
        </div>
      </RefreshFrame>

      <el-drawer v-model="postDrawerOpen" size="620px" :title="postDrawerTitle" destroy-on-close>
        <PageStateBlock
          v-if="postDetailLoading"
          tone="loading"
          title="正在加载帖子详情"
          description="把帖子状态、审核结论和评论情况拉齐后再处理。"
          compact
        />
        <PageStateBlock
          v-else-if="!selectedPost"
          tone="empty"
          title="还没有选中帖子"
          description="从列表里点开一条帖子，右侧就会展开详情处理区。"
          compact
        />
        <template v-else>
          <div class="drawer-summary">
            <article v-spotlight>
              <span>作者</span>
              <strong>{{ selectedPost.user_info?.display_name || selectedPost.user_info?.username || "用户" }}</strong>
            </article>
            <article v-spotlight>
              <span>最近更新</span>
              <strong>{{ formatDateTime(selectedPost.updated_at) }}</strong>
            </article>
            <article v-spotlight>
              <span>举报数</span>
              <strong>{{ selectedPost.report_count }}</strong>
            </article>
          </div>

          <div class="drawer-focus" v-spotlight>
            <div class="drawer-focus-head">
              <strong>当前审核判断</strong>
              <span>{{ postFocusTitle }}</span>
            </div>
            <div class="drawer-focus-tags">
              <span v-for="item in postSignals(selectedPost)" :key="item" class="drawer-focus-tag">{{ item }}</span>
            </div>
            <ul class="drawer-checklist">
              <li v-for="item in postChecklist" :key="item">{{ item }}</li>
            </ul>
          </div>

          <el-form label-position="top" class="drawer-form">
            <div class="drawer-section" v-spotlight>
              <div class="drawer-section-head">
                <strong>审核状态</strong>
                <span>先决定这条帖子是继续公开、转归档，还是把审核结论改清楚。</span>
              </div>
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="帖子状态">
                    <el-select v-model="postDraft.status" style="width: 100%">
                      <el-option label="公开中" value="published" />
                      <el-option label="已归档" value="archived" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="审核结论">
                    <el-select v-model="postDraft.audit_status" style="width: 100%">
                      <el-option label="待审核" value="pending" />
                      <el-option label="已通过" value="approved" />
                      <el-option label="已驳回" value="rejected" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <div class="drawer-section" v-spotlight>
              <div class="drawer-section-head">
                <strong>帖子内容</strong>
                <span>标题和正文是最直接的审核对象，先把会影响理解的内容看清楚。</span>
              </div>
              <el-form-item label="标题">
                <el-input v-model.trim="postDraft.title" />
              </el-form-item>
              <el-form-item label="正文">
                <el-input v-model.trim="postDraft.content" type="textarea" :rows="5" />
              </el-form-item>
            </div>

            <div class="drawer-section" v-spotlight>
              <div class="drawer-section-head">
                <strong>评论区</strong>
                <span>管理员可以在这里快速判断哪些评论需要隐藏，避免风险继续扩散。</span>
              </div>
              <div v-if="selectedPost.comments?.length" class="comment-list">
                <article v-for="comment in selectedPost.comments" :key="comment.id" class="comment-item">
                  <div class="comment-head">
                    <strong>{{ comment.user_info?.display_name || comment.user_info?.username || "用户" }}</strong>
                    <span>{{ formatDateTime(comment.created_at) }}</span>
                  </div>
                  <p>{{ comment.content }}</p>
                  <div class="comment-actions">
                    <el-tag :type="comment.status === 'hidden' ? 'danger' : 'success'" effect="light">
                      {{ comment.status === "hidden" ? "已隐藏" : "可见" }}
                    </el-tag>
                    <el-button
                      v-if="comment.status !== 'hidden'"
                      text
                      type="danger"
                      :loading="commentActionId === comment.id"
                      @click="hideComment(comment.id)"
                    >
                      隐藏评论
                    </el-button>
                  </div>
                </article>
              </div>
              <PageStateBlock
                v-else
                tone="empty"
                title="这条帖子还没有评论"
                description="当前不需要额外处理评论风险。"
                compact
              />
            </div>
          </el-form>

          <div class="drawer-section" v-spotlight>
            <AdminObjectTimeline
              object-label="这条帖子"
              :logs="postLogs"
              :loading="postLogsLoading"
              title="最近处理回放"
              description="这里会串起帖子本身、隐藏评论和相关举报处理，方便回看完整处理链。"
            />
          </div>

          <div class="drawer-actions">
            <el-button plain @click="postDrawerOpen = false">取消</el-button>
            <el-button type="primary" :loading="savingPost" @click="savePost">保存修改</el-button>
          </div>
        </template>
      </el-drawer>

      <el-drawer v-model="reportDrawerOpen" size="600px" :title="reportDrawerTitle" destroy-on-close>
        <PageStateBlock
          v-if="reportDetailLoading"
          tone="loading"
          title="正在加载举报详情"
          description="把举报对象和处理结论拉齐后再执行。"
          compact
        />
        <PageStateBlock
          v-else-if="!selectedReport"
          tone="empty"
          title="还没有选中举报"
          description="从列表里点开一条举报，右侧就会展开详情。"
          compact
        />
        <template v-else>
          <div class="drawer-summary">
            <article v-spotlight>
              <span>举报人</span>
              <strong>{{ selectedReport.reporter_info?.display_name || selectedReport.reporter_info?.username || "用户" }}</strong>
            </article>
            <article v-spotlight>
              <span>当前状态</span>
              <strong>{{ reportStatusLabel(selectedReport.status) }}</strong>
            </article>
            <article v-spotlight>
              <span>提交时间</span>
              <strong>{{ formatDateTime(selectedReport.created_at) }}</strong>
            </article>
          </div>

          <div class="drawer-focus" v-spotlight>
            <div class="drawer-focus-head">
              <strong>举报判断</strong>
              <span>{{ reportFocusTitle }}</span>
            </div>
            <ul class="drawer-checklist">
              <li>举报原因：{{ selectedReport.reason }}</li>
              <li v-if="selectedReport.target_post_title">目标帖子：{{ selectedReport.target_post_title }}</li>
              <li v-if="selectedReport.processed_by_info">处理人：{{ selectedReport.processed_by_info.display_name || selectedReport.processed_by_info.username }}</li>
            </ul>
          </div>

          <div v-if="selectedReport.target_post" class="drawer-section" v-spotlight>
            <div class="drawer-section-head">
              <strong>目标帖子快照</strong>
              <span>先核对帖子当前状态，再决定举报是通过还是驳回。</span>
            </div>
            <div class="target-post">
              <strong>{{ selectedReport.target_post.title }}</strong>
              <p>{{ selectedReport.target_post.content }}</p>
              <div class="target-post-meta">
                <el-tag :type="postStatusTagType(selectedReport.target_post.status)" effect="light">{{ postStatusLabel(selectedReport.target_post.status) }}</el-tag>
                <el-tag :type="auditTagType(selectedReport.target_post.audit_status)" effect="light">{{ auditLabel(selectedReport.target_post.audit_status) }}</el-tag>
              </div>
            </div>
          </div>

          <div class="drawer-section" v-spotlight>
            <AdminObjectTimeline
              object-label="这条举报"
              :logs="reportLogs"
              :loading="reportLogsLoading"
              title="最近处理回放"
              description="直接回看这条举报最近是谁处理的、状态怎么变过。"
            />
          </div>

          <div class="drawer-actions">
            <el-button plain @click="reportDrawerOpen = false">取消</el-button>
            <el-button type="danger" plain :loading="reportActionId === selectedReport.id && reportAction === 'rejected'" @click="updateReportStatus(selectedReport.id, 'rejected')">驳回举报</el-button>
            <el-button type="primary" :loading="reportActionId === selectedReport.id && reportAction === 'processed'" @click="updateReportStatus(selectedReport.id, 'processed')">标记已处理</el-button>
          </div>
        </template>
      </el-drawer>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import AdminObjectTimeline from "../components/AdminObjectTimeline.vue";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { getAdminCommunityPostDetail, getAdminCommunityReportDetail, listAdminCommunityPosts, listAdminCommunityReports, updateAdminCommunityPost, updateAdminCommunityReport } from "../api/adminContent";
import { listAdminOperationLogs } from "../api/adminLogs";
import { deleteComment } from "../api/community";
import { extractApiErrorMessage, notifyActionSuccess, notifyErrorMessage, notifyLoadError } from "../lib/feedback";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const posts = ref<any[]>([]);
const reports = ref<any[]>([]);
const loadingPosts = ref(false);
const loadingReports = ref(false);
const savingPost = ref(false);
const postDetailLoading = ref(false);
const reportDetailLoading = ref(false);
const postLogsLoading = ref(false);
const reportLogsLoading = ref(false);
const commentActionId = ref<number | null>(null);
const reportActionId = ref<number | null>(null);
const reportAction = ref<"" | "processed" | "rejected">("");
const postDrawerOpen = ref(false);
const reportDrawerOpen = ref(false);
const selectedPost = ref<any | null>(null);
const selectedReport = ref<any | null>(null);
const postLogs = ref<any[]>([]);
const reportLogs = ref<any[]>([]);
const focusPreset = ref<"all" | "pending_posts" | "pending_reports" | "rejected_posts" | "hidden_comments">("all");

const postFilters = reactive({
  keyword: "",
  status: "",
  auditStatus: "",
});

const reportFilters = reactive({
  keyword: "",
  status: "",
});

const postDraft = reactive({
  title: "",
  content: "",
  status: "published",
  audit_status: "pending",
});

const isAdminUser = computed(() => Boolean(auth.user && (auth.user.role === "admin" || auth.user.is_superuser || auth.user.is_staff)));
const showSkeleton = computed(() => (loadingPosts || loadingReports) && !posts.value.length && !reports.value.length);
const pendingPostCount = computed(() => posts.value.filter((item) => item.audit_status === "pending").length);
const rejectedPostCount = computed(() => posts.value.filter((item) => item.audit_status === "rejected").length);
const hiddenCommentCount = computed(() => posts.value.reduce((sum, item) => sum + Number(item.hidden_comment_count || 0), 0));
const pendingReportCount = computed(() => reports.value.filter((item) => item.status === "pending").length);
const focusCards = computed(() => [
  {
    key: "pending_posts" as const,
    label: "待审核帖子",
    value: pendingPostCount.value,
    copy: pendingPostCount.value > 0 ? "适合优先判断是否继续公开。" : "当前列表没有待审核帖子堆积。",
  },
  {
    key: "pending_reports" as const,
    label: "待处理举报",
    value: pendingReportCount.value,
    copy: pendingReportCount.value > 0 ? "这批举报建议尽快给出处理结果。" : "当前没有待处理举报堆积。",
  },
  {
    key: "rejected_posts" as const,
    label: "已驳回帖子",
    value: rejectedPostCount.value,
    copy: "适合复核是否仍需要保留展示或继续归档。",
  },
  {
    key: "hidden_comments" as const,
    label: "已隐藏评论",
    value: hiddenCommentCount.value,
    copy: "可以快速感知评论风险是否开始积累。",
  },
]);
const displayPosts = computed(() => {
  let items = [...posts.value];
  if (focusPreset.value === "pending_posts") items = items.filter((item) => item.audit_status === "pending");
  if (focusPreset.value === "rejected_posts") items = items.filter((item) => item.audit_status === "rejected");
  if (focusPreset.value === "hidden_comments") items = items.filter((item) => Number(item.hidden_comment_count || 0) > 0);
  return items;
});
const displayReports = computed(() => {
  let items = [...reports.value];
  if (focusPreset.value === "pending_reports") items = items.filter((item) => item.status === "pending");
  if (focusPreset.value === "pending_posts") items = items.filter((item) => item.status === "pending");
  return items;
});
const postFilterHint = computed(() => {
  if (focusPreset.value === "pending_posts") return "当前聚焦：待审核帖子。先决定这些内容是继续公开还是转入驳回/归档。";
  if (focusPreset.value === "rejected_posts") return "当前聚焦：已驳回帖子。适合复核是否还要继续保留或归档。";
  if (focusPreset.value === "hidden_comments") return "当前聚焦：带隐藏评论的帖子。适合优先判断评论区风险是否仍在积累。";
  return "先定位帖子状态、审核结论和作者，再决定是否继续公开。";
});
const reportFilterHint = computed(() => {
  if (focusPreset.value === "pending_reports") return "当前聚焦：待处理举报。建议先核对目标帖子，再直接给出处理结论。";
  return "举报处理要先看原因，再回到目标帖子确认是否真的需要介入。";
});
const postDrawerTitle = computed(() => (selectedPost.value ? `处理帖子：${selectedPost.value.title}` : "处理帖子"));
const reportDrawerTitle = computed(() => (selectedReport.value ? `处理举报 #${selectedReport.value.id}` : "处理举报"));
const postFocusTitle = computed(() => {
  if (!selectedPost.value) return "先打开一条帖子";
  if (postDraft.audit_status === "pending") return "这条帖子还需要后台给出审核结论";
  if (postDraft.audit_status === "rejected") return "这条帖子当前不建议继续公开曝光";
  if (postDraft.status === "archived") return "这条帖子已经转入归档状态";
  return "这条帖子的状态相对稳定";
});
const postChecklist = computed(() => {
  if (!selectedPost.value) return [];
  const list = [];
  if (postDraft.audit_status === "pending") list.push("当前仍是待审核状态，处理后建议明确改成通过或驳回。");
  if (selectedPost.value.report_count > 0) list.push("这条帖子已经被举报，建议先结合举报原因再决定是否公开。");
  if (selectedPost.value.hidden_comment_count > 0) list.push("评论区已经出现隐藏动作，建议顺手复核是否还有继续外露的风险。");
  if (!postDraft.content) list.push("正文为空时，不建议继续公开展示。");
  if (!list.length) list.push("当前没有明显风险堆积，可以做常规状态维护。");
  return list;
});
const reportFocusTitle = computed(() => {
  if (!selectedReport.value) return "先打开一条举报";
  if (selectedReport.value.status === "pending") return "这条举报还需要后台给出处理结果";
  if (selectedReport.value.status === "processed") return "这条举报已经完成处理";
  return "这条举报已被驳回";
});

onMounted(() => {
  if (isAdminUser.value) {
    void refreshAll();
  }
});

async function refreshAll() {
  await Promise.all([loadPosts(), loadReports()]);
}

async function loadPosts() {
  if (!isAdminUser.value) return;
  loadingPosts.value = true;
  try {
    const response = await listAdminCommunityPosts({
      keyword: postFilters.keyword || undefined,
      status: postFilters.status || undefined,
      audit_status: postFilters.auditStatus || undefined,
      page_size: 50,
    });
    posts.value = unwrapListPayload(response);
  } catch {
    notifyLoadError("社区帖子");
  } finally {
    loadingPosts.value = false;
  }
}

async function loadReports() {
  if (!isAdminUser.value) return;
  loadingReports.value = true;
  try {
    const response = await listAdminCommunityReports({
      keyword: reportFilters.keyword || undefined,
      status: reportFilters.status || undefined,
      page_size: 50,
    });
    reports.value = unwrapListPayload(response);
  } catch {
    notifyLoadError("举报列表");
  } finally {
    loadingReports.value = false;
  }
}

function resetFilters() {
  focusPreset.value = "all";
  postFilters.keyword = "";
  postFilters.status = "";
  postFilters.auditStatus = "";
  reportFilters.keyword = "";
  reportFilters.status = "";
}

function unwrapListPayload(payload: any) {
  if (Array.isArray(payload?.data?.items)) return payload.data.items;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload)) return payload;
  return [];
}

async function openPostDrawer(postId: number) {
  postDrawerOpen.value = true;
  postDetailLoading.value = true;
  selectedPost.value = null;
  postLogs.value = [];

  try {
    const response = await getAdminCommunityPostDetail(postId);
    selectedPost.value = response?.data ?? null;
    fillPostDraft(selectedPost.value);
    if (selectedPost.value) {
      void loadPostLogs(selectedPost.value.id);
    }
  } catch {
    notifyLoadError("帖子详情");
    postDrawerOpen.value = false;
  } finally {
    postDetailLoading.value = false;
  }
}

function fillPostDraft(post: Record<string, any> | null) {
  Object.assign(postDraft, {
    title: post?.title || "",
    content: post?.content || "",
    status: post?.status || "published",
    audit_status: post?.audit_status || "pending",
  });
}

async function savePost() {
  if (!selectedPost.value) return;
  savingPost.value = true;
  try {
    const response = await updateAdminCommunityPost(selectedPost.value.id, { ...postDraft });
    selectedPost.value = response?.data ?? null;
    fillPostDraft(selectedPost.value);
    await loadPostLogs(selectedPost.value.id);
    notifyActionSuccess("帖子审核状态已经更新");
    await refreshAll();
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "这次没有成功更新帖子"));
  } finally {
    savingPost.value = false;
  }
}

async function hideComment(commentId: number) {
  commentActionId.value = commentId;
  try {
    await deleteComment(commentId);
    notifyActionSuccess("评论已经隐藏");
    if (selectedPost.value) {
      await openPostDrawer(selectedPost.value.id);
      await loadPostLogs(selectedPost.value.id);
    }
    await refreshAll();
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "隐藏评论失败"));
  } finally {
    commentActionId.value = null;
  }
}

async function openReportDrawer(reportId: number) {
  reportDrawerOpen.value = true;
  reportDetailLoading.value = true;
  selectedReport.value = null;
  reportLogs.value = [];

  try {
    const response = await getAdminCommunityReportDetail(reportId);
    selectedReport.value = response?.data ?? null;
    if (selectedReport.value) {
      void loadReportLogs(selectedReport.value.id);
    }
  } catch {
    notifyLoadError("举报详情");
    reportDrawerOpen.value = false;
  } finally {
    reportDetailLoading.value = false;
  }
}

async function updateReportStatus(reportId: number, statusValue: "processed" | "rejected") {
  reportActionId.value = reportId;
  reportAction.value = statusValue;
  try {
    const response = await updateAdminCommunityReport(reportId, { status: statusValue });
    if (selectedReport.value?.id === reportId) {
      selectedReport.value = response?.data ?? null;
      await loadReportLogs(reportId);
    }
    notifyActionSuccess(statusValue === "processed" ? "举报已经标记为已处理" : "举报已经标记为驳回");
    await refreshAll();
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "更新举报状态失败"));
  } finally {
    reportActionId.value = null;
    reportAction.value = "";
  }
}

async function loadPostLogs(postId: number) {
  postLogsLoading.value = true;
  try {
    const response = await listAdminOperationLogs({
      page: 1,
      page_size: 8,
      related_target_type: "post",
      related_target_id: postId,
    });
    postLogs.value = response?.data?.items || response?.items || [];
  } catch {
    postLogs.value = [];
  } finally {
    postLogsLoading.value = false;
  }
}

async function loadReportLogs(reportId: number) {
  reportLogsLoading.value = true;
  try {
    const response = await listAdminOperationLogs({
      page: 1,
      page_size: 6,
      target_type: "content_report",
      target_id: reportId,
    });
    reportLogs.value = response?.data?.items || response?.items || [];
  } catch {
    reportLogs.value = [];
  } finally {
    reportLogsLoading.value = false;
  }
}

function postSignals(post: Record<string, any>) {
  const items = [];
  if (post.audit_status === "pending") items.push("待审核");
  if (post.audit_status === "rejected") items.push("已驳回");
  if (post.status === "archived") items.push("已归档");
  if (Number(post.report_count || 0) > 0) items.push("已有举报");
  if (Number(post.hidden_comment_count || 0) > 0) items.push("评论区已隐藏");
  return items.length ? items : ["状态稳定"];
}

function postStatusLabel(value: string) {
  return (
    {
      published: "公开中",
      archived: "已归档",
    }[value] || value
  );
}

function postStatusTagType(value: string) {
  return (
    {
      published: "success",
      archived: "info",
    }[value] || "info"
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

function auditTagType(value: string) {
  return (
    {
      pending: "warning",
      approved: "success",
      rejected: "danger",
    }[value] || "info"
  );
}

function reportStatusLabel(value: string) {
  return (
    {
      pending: "待处理",
      processed: "已处理",
      rejected: "已驳回",
    }[value] || value
  );
}

function reportStatusTagType(value: string) {
  return (
    {
      pending: "warning",
      processed: "success",
      rejected: "danger",
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
</script>

<style scoped>
.admin-community {
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
}

.focus-card.active span,
.focus-card.active strong,
.focus-card.active p {
  color: #f2f7fb;
}

.admin-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.9fr);
  gap: 16px;
}

.moderation-card,
.report-card {
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
  grid-template-columns: minmax(220px, 1.5fr) repeat(2, minmax(140px, 0.8fr)) auto;
  gap: 12px;
}

.reports-toolbar {
  grid-template-columns: minmax(220px, 1fr) minmax(140px, 0.7fr) auto;
}

.content-cell,
.metric-cell,
.judgement-cell {
  display: grid;
  gap: 4px;
}

.content-cell strong {
  color: #173042;
}

.content-cell span,
.metric-cell span,
.judgement-cell span {
  color: #5b7888;
  font-size: 13px;
  line-height: 1.5;
}

.report-list {
  display: grid;
  gap: 12px;
}

.report-item {
  display: grid;
  gap: 10px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(247, 251, 255, 0.92);
}

.report-head,
.comment-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.report-head strong,
.comment-head strong {
  color: #173042;
}

.report-head span,
.comment-head span {
  color: #5b7888;
  font-size: 12px;
}

.report-item p,
.comment-item p,
.target-post p {
  margin: 0;
  color: #476072;
  line-height: 1.65;
}

.report-actions,
.comment-actions,
.drawer-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.drawer-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 18px;
}

.drawer-summary article,
.target-post {
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

.drawer-summary strong,
.target-post strong {
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

.comment-list {
  display: grid;
  gap: 12px;
}

.comment-item {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(250, 252, 254, 0.98);
  border: 1px solid rgba(16, 34, 42, 0.08);
}

.target-post-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 1120px) {
  .focus-strip,
  .admin-grid,
  .toolbar-grid,
  .reports-toolbar {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .drawer-summary {
    grid-template-columns: 1fr;
  }
}
</style>
