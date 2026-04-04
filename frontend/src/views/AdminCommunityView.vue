<template>
  <section class="page admin-community">
    <div class="head">
      <div>
        <p class="tag">Community Moderation</p>
        <h2>社区审核</h2>
      </div>
      <div class="head-actions">
        <CompactHint tone="warm" title="社区审核说明" description="先看列表和批量动作，帖子筛选和举报筛选都已经支持按需展开，不必默认读说明。" />
        <el-button plain @click="resetFilters">重置筛选</el-button>
        <el-button type="primary" :loading="loadingPosts || loadingReports" @click="refreshAll">刷新后台内容</el-button>
        <el-button plain @click="router.push('/community')">去前台社区页</el-button>
      </div>
    </div>

    <PageStateBlock
      v-if="auth.isAuthenticated && !auth.user"
      tone="loading"
      title="正在确认后台身份"
      description="先把当前账号权限拉齐，再展开社区审核。"
      compact
    />
    <PageStateBlock
      v-else-if="!hasOpsUser"
      tone="error"
      title="当前账号没有后台权限"
      description="社区审核只对后台值守账号开放，普通账号不会显示这里。"
      action-label="回到首页"
      @action="router.push('/')"
    />
    <template v-else>
      <CollectionSkeleton v-if="showSkeleton" variant="list" :card-count="5" />
      <RefreshFrame v-else :active="loadingPosts || loadingReports" label="正在同步帖子与举报状态">
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

        <div class="admin-grid">
          <article class="card moderation-card" v-spotlight>
            <div class="card-head">
              <div>
                <div class="section-title-row">
                  <h3>帖子审核</h3>
                  <CompactHint description="先判断状态和审核，再决定是否需要打开详情。评论和举报信息只是辅助判断，不是主阅读入口。" />
                </div>
              </div>
              <div class="card-head-actions">
                <el-button class="filter-toggle" plain @click="postFiltersExpanded = !postFiltersExpanded">
                  {{ postFiltersExpanded ? "收起筛选" : "展开筛选" }}
                </el-button>
                <el-button v-if="focusPreset !== 'all'" text type="primary" @click="applyFocusPreset('all')">回到全部视角</el-button>
              </div>
            </div>
            <div v-if="!postFiltersExpanded" class="filter-summary-strip">
              <span v-for="item in postFilterSummary" :key="item" class="filter-summary-chip">{{ item }}</span>
            </div>
            <div v-else class="toolbar-grid">
              <el-input v-model.trim="postFilters.keyword" placeholder="搜索标题、正文或作者" clearable @keyup.enter="applyPostFilters" />
              <el-select v-model="postFilters.status" clearable placeholder="状态">
                <el-option label="公开中" value="published" />
                <el-option label="已归档" value="archived" />
              </el-select>
              <el-select v-model="postFilters.auditStatus" clearable placeholder="审核">
                <el-option label="待审核" value="pending" />
                <el-option label="已通过" value="approved" />
                <el-option label="已驳回" value="rejected" />
              </el-select>
              <el-button type="primary" :loading="loadingPosts" @click="applyPostFilters">应用筛选</el-button>
            </div>

            <div v-if="selectedPostIds.length" class="bulk-bar">
              <span>已选 {{ selectedPostIds.length }} 条帖子，可直接批量通过、驳回或归档。</span>
              <div class="bulk-actions">
                <el-button :disabled="bulkUpdatingPosts" @click="clearPostSelection">清空选择</el-button>
                <el-button type="success" :loading="bulkUpdatingPosts" @click="applyBulkPostAction('approve')">批量通过</el-button>
                <el-button type="warning" :loading="bulkUpdatingPosts" @click="applyBulkPostAction('reject')">批量驳回</el-button>
                <el-button type="danger" :loading="bulkUpdatingPosts" @click="applyBulkPostAction('archive')">批量归档</el-button>
              </div>
            </div>

            <el-table ref="postTableRef" :data="displayPosts" :row-key="(row: any) => row.id" stripe class="moderation-table" empty-text="当前筛选下没有帖子" @selection-change="handlePostSelectionChange">
              <el-table-column type="selection" width="48" />
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
                <div class="section-title-row">
                  <h3>举报处理</h3>
                  <CompactHint description="先处理待处理举报，再看优先级和指派；只有复杂协作场景才需要展开完整信息。" />
                </div>
              </div>
              <div class="card-head-actions">
                <el-button class="filter-toggle" plain @click="reportFiltersExpanded = !reportFiltersExpanded">
                  {{ reportFiltersExpanded ? "收起筛选" : "展开筛选" }}
                </el-button>
                <el-button v-if="focusPreset !== 'all'" text type="primary" @click="applyFocusPreset('all')">回到全部视角</el-button>
              </div>
            </div>
            <div v-if="!reportFiltersExpanded" class="filter-summary-strip">
              <span v-for="item in reportFilterSummary" :key="item" class="filter-summary-chip">{{ item }}</span>
            </div>
            <div v-else class="toolbar-grid reports-toolbar">
              <el-input v-model.trim="reportFilters.keyword" placeholder="搜索举报原因、举报人或内部备注" clearable @keyup.enter="applyReportFilters" />
              <el-select v-model="reportFilters.status" clearable placeholder="处理状态">
                <el-option label="待处理" value="pending" />
                <el-option label="已处理" value="processed" />
                <el-option label="已驳回" value="rejected" />
              </el-select>
              <el-select v-model="reportFilters.priority" clearable placeholder="优先级">
                <el-option label="低" value="low" />
                <el-option label="普通" value="normal" />
                <el-option label="高" value="high" />
                <el-option label="紧急" value="urgent" />
              </el-select>
              <el-select v-model="reportFilters.assignedTo" clearable placeholder="处理人">
                <el-option label="未指派" value="unassigned" />
                <el-option
                  v-for="user in reportAssignableUsers"
                  :key="user.id"
                  :label="user.display_name || user.username"
                  :value="String(user.id)"
                />
              </el-select>
              <el-button type="primary" :loading="loadingReports" @click="applyReportFilters">刷新举报</el-button>
            </div>

            <div v-if="selectedReportIds.length" class="bulk-bar bulk-bar-compact">
              <span>已选 {{ selectedReportIds.length }} 条举报，可直接批量标记已处理或驳回。</span>
              <div class="bulk-actions">
                <el-button :disabled="bulkUpdatingReports" @click="clearReportSelection">清空选择</el-button>
                <el-button type="primary" :loading="bulkUpdatingReports" @click="applyBulkReportAction('processed')">批量已处理</el-button>
                <el-button type="danger" :loading="bulkUpdatingReports" @click="applyBulkReportAction('rejected')">批量驳回</el-button>
              </div>
            </div>

            <div v-if="displayReports.length" class="report-list">
              <article v-for="report in displayReports" :key="report.id" class="report-item">
                <div class="report-head">
                  <div>
                    <strong>{{ report.target_post_title || "帖子举报" }}</strong>
                    <span>{{ report.reporter_info?.display_name || report.reporter_info?.username || "用户" }} · {{ formatDateTime(report.created_at) }}</span>
                  </div>
                  <div class="report-head-side">
                    <div class="report-tags">
                      <el-tag :type="priorityTagType(report.priority)" effect="light">{{ priorityLabel(report.priority) }}</el-tag>
                      <el-tag :type="reportStatusTagType(report.status)" effect="light">{{ reportStatusLabel(report.status) }}</el-tag>
                    </div>
                    <el-checkbox :model-value="selectedReportIds.includes(report.id)" @change="toggleReportSelection(report.id, $event)">选择</el-checkbox>
                  </div>
                </div>
                <p>{{ report.reason }}</p>
                <div class="report-meta-row">
                  <span>指派：{{ report.assigned_to_info?.display_name || report.assigned_to_info?.username || "未指派" }}</span>
                  <span v-if="report.follow_up_at">跟进：{{ formatDateTime(report.follow_up_at) }}</span>
                </div>
                <div v-if="report.internal_note" class="report-note-preview">
                  <strong>内部备注</strong>
                  <span>{{ report.internal_note }}</span>
                </div>
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

      <el-drawer v-model="postDrawerOpen" size="620px" :title="postDrawerTitle" destroy-on-close append-to-body>
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

      <el-drawer v-model="reportDrawerOpen" size="600px" :title="reportDrawerTitle" destroy-on-close append-to-body>
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
              <strong>{{ reportStatusLabel(reportDraft.status) }}</strong>
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
            <div class="drawer-focus-tags">
              <span class="drawer-focus-tag">优先级：{{ priorityLabel(reportDraft.priority) }}</span>
              <span class="drawer-focus-tag">指派：{{ selectedReport.assigned_to_info?.display_name || selectedReport.assigned_to_info?.username || "未指派" }}</span>
              <span v-if="reportDraft.follow_up_at" class="drawer-focus-tag">跟进：{{ formatDateTime(reportDraft.follow_up_at) }}</span>
            </div>
            <ul class="drawer-checklist">
              <li v-for="item in reportChecklist" :key="item">{{ item }}</li>
            </ul>
          </div>

          <el-form label-position="top" class="drawer-form">
            <div class="drawer-section" v-spotlight>
              <div class="drawer-section-head">
                <strong>处理协作</strong>
                <span>先明确状态、优先级和责任人，再决定什么时候继续跟进。</span>
              </div>
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="处理状态">
                    <el-select v-model="reportDraft.status" style="width: 100%">
                      <el-option v-for="option in reportStatusOptions" :key="option.value" :label="option.label" :value="option.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="优先级">
                    <el-select v-model="reportDraft.priority" style="width: 100%">
                      <el-option v-for="option in reportPriorityOptions" :key="option.value" :label="option.label" :value="option.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="指派处理人">
                    <el-select v-model="reportDraft.assigned_to" clearable style="width: 100%" placeholder="暂不指派">
                      <el-option
                        v-for="user in reportAssignableUsers"
                        :key="user.id"
                        :label="user.display_name || user.username"
                        :value="user.id"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="跟进时间">
                    <el-input v-model="reportDraft.follow_up_at" type="datetime-local" />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <div class="drawer-section" v-spotlight>
              <div class="drawer-section-head">
                <strong>内部备注</strong>
                <span>写清楚当前判断、下一步动作或需要谁继续跟进。</span>
              </div>
              <el-form-item label="备注内容">
                <el-input v-model.trim="reportDraft.internal_note" type="textarea" :rows="5" placeholder="仅后台可见" />
              </el-form-item>
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
          </el-form>

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
            <el-button type="primary" plain :loading="reportActionId === selectedReport.id && reportAction === 'processed'" @click="updateReportStatus(selectedReport.id, 'processed')">标记已处理</el-button>
            <el-button type="primary" :loading="reportActionId === selectedReport.id && !reportAction" @click="saveReport">保存协作信息</el-button>
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
import { bulkUpdateAdminCommunityPosts, bulkUpdateAdminCommunityReports, getAdminCommunityPostDetail, getAdminCommunityReportDetail, listAdminCommunityPosts, listAdminCommunityReports, updateAdminCommunityPost, updateAdminCommunityReport } from "../api/adminContent";
import { listAdminOperationLogs } from "../api/adminLogs";
import { deleteComment } from "../api/community";
import { hasOpsAccess } from "../lib/opsAccess";
import { extractApiErrorMessage, notifyActionSuccess, notifyErrorMessage, notifyLoadError } from "../lib/feedback";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

type CommunityFocusPreset = "all" | "pending_posts" | "pending_reports" | "rejected_posts" | "hidden_comments";

const communityFocusPresets: CommunityFocusPreset[] = ["all", "pending_posts", "pending_reports", "rejected_posts", "hidden_comments"];
const postStatuses = ["published", "archived"] as const;
const postAuditStatuses = ["pending", "approved", "rejected"] as const;
const reportStatuses = ["pending", "processed", "rejected"] as const;
const reportPriorities = ["low", "normal", "high", "urgent"] as const;

const posts = ref<any[]>([]);
const reports = ref<any[]>([]);
const loadingPosts = ref(false);
const loadingReports = ref(false);
const savingPost = ref(false);
const bulkUpdatingPosts = ref(false);
const bulkUpdatingReports = ref(false);
const postDetailLoading = ref(false);
const reportDetailLoading = ref(false);
const postLogsLoading = ref(false);
const reportLogsLoading = ref(false);
const commentActionId = ref<number | null>(null);
const reportActionId = ref<number | null>(null);
const reportAction = ref<"" | "processed" | "rejected">("");
const postDrawerOpen = ref(false);
const reportDrawerOpen = ref(false);
const postTableRef = ref<any>();
const selectedPost = ref<any | null>(null);
const selectedReport = ref<any | null>(null);
const selectedPostIds = ref<number[]>([]);
const selectedReportIds = ref<number[]>([]);
const postLogs = ref<any[]>([]);
const reportLogs = ref<any[]>([]);
const postFiltersExpanded = ref(false);
const reportFiltersExpanded = ref(false);
const focusPreset = ref<CommunityFocusPreset>("all");
const syncingRoute = ref(false);

const postFilters = reactive({
  keyword: "",
  status: "",
  auditStatus: "",
});

const reportFilters = reactive({
  keyword: "",
  status: "",
  priority: "",
  assignedTo: "",
});

const reportDraft = reactive({
  status: "pending",
  priority: "normal",
  assigned_to: null as number | null,
  internal_note: "",
  follow_up_at: "",
});

const postDraft = reactive({
  title: "",
  content: "",
  status: "published",
  audit_status: "pending",
});

const hasOpsUser = computed(() => hasOpsAccess(auth.user));
const showSkeleton = computed(() => (loadingPosts || loadingReports) && !posts.value.length && !reports.value.length);
const pendingPostCount = computed(() => posts.value.filter((item) => item.audit_status === "pending").length);
const rejectedPostCount = computed(() => posts.value.filter((item) => item.audit_status === "rejected").length);
const hiddenCommentCount = computed(() => posts.value.reduce((sum, item) => sum + Number(item.hidden_comment_count || 0), 0));
const pendingReportCount = computed(() => reports.value.filter((item) => item.status === "pending").length);
const reportAssignableUsers = computed(() => {
  const detailUsers = Array.isArray(selectedReport.value?.assignable_users) ? selectedReport.value.assignable_users : [];
  const seenUsers = reports.value
    .map((item) => item.assigned_to_info)
    .filter((item): item is Record<string, any> => Boolean(item?.id));
  const merged = [...detailUsers, ...seenUsers];
  const byId = new Map<number, Record<string, any>>();
  merged.forEach((item) => {
    if (!byId.has(item.id)) byId.set(item.id, item);
  });
  return Array.from(byId.values());
});
const reportStatusOptions = [
  { label: "待处理", value: "pending" },
  { label: "已处理", value: "processed" },
  { label: "已驳回", value: "rejected" },
];
const reportPriorityOptions = [
  { label: "低", value: "low" },
  { label: "普通", value: "normal" },
  { label: "高", value: "high" },
  { label: "紧急", value: "urgent" },
];
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
const postFilterSummary = computed(() => {
  const items = [];
  if (focusPreset.value !== "all") items.push(`视角：${focusCards.value.find((item) => item.key === focusPreset.value)?.label || "当前聚焦"}`);
  if (postFilters.keyword) items.push(`搜索：${postFilters.keyword}`);
  if (postFilters.status) items.push(`状态：${postStatusLabel(postFilters.status)}`);
  if (postFilters.auditStatus) items.push(`审核：${auditLabel(postFilters.auditStatus)}`);
  return items.length ? items : ["帖子侧当前无额外筛选"];
});
const reportFilterSummary = computed(() => {
  const items = [];
  if (focusPreset.value === "pending_reports") items.push("视角：待处理举报");
  if (reportFilters.keyword) items.push(`搜索：${reportFilters.keyword}`);
  if (reportFilters.status) items.push(`状态：${reportStatusLabel(reportFilters.status)}`);
  if (reportFilters.priority) items.push(`优先级：${priorityLabel(reportFilters.priority)}`);
  if (reportFilters.assignedTo) items.push(reportFilters.assignedTo === "unassigned" ? "未指派" : "已指定处理人");
  return items.length ? items : ["举报侧当前无额外筛选"];
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
  if (reportDraft.status === "pending") return "这条举报还需要后台给出处理结果";
  if (reportDraft.status === "processed") return "这条举报已经完成处理";
  return "这条举报已被驳回";
});
const reportChecklist = computed(() => {
  if (!selectedReport.value) return [];
  const list = [];
  list.push(`举报原因：${selectedReport.value.reason || "暂无"}`);
  if (selectedReport.value.target_post_title) list.push(`目标帖子：${selectedReport.value.target_post_title}`);
  if (reportDraft.assigned_to) {
    const assignee = reportAssignableUsers.value.find((item: any) => item.id === reportDraft.assigned_to);
    if (assignee) list.push(`当前指派：${assignee.display_name || assignee.username}`);
  } else {
    list.push("当前未指派处理人，适合先明确责任人。");
  }
  if (reportDraft.internal_note) list.push("已填写内部备注，可直接继续协作处理。");
  if (reportDraft.follow_up_at) list.push(`跟进时间：${formatDateTime(reportDraft.follow_up_at)}`);
  if (selectedReport.value.processed_by_info) {
    list.push(`最近处理人：${selectedReport.value.processed_by_info.display_name || selectedReport.value.processed_by_info.username}`);
  }
  return list;
});

watch(
  () => route.query,
  (query) => {
    if (syncingRoute.value) return;
    applyRouteQuery(query as Record<string, unknown>);
    if (hasOpsUser.value) {
      void refreshAll();
    }
  },
  { immediate: true },
);

watch(
  hasOpsUser,
  (value) => {
    if (value && !posts.value.length && !reports.value.length) {
      void refreshAll();
    }
  },
  { immediate: false },
);

function readQueryText(value: unknown) {
  if (typeof value === "string") return value;
  if (Array.isArray(value) && typeof value[0] === "string") return value[0];
  return "";
}

function normalizeFocusPreset(value: string): CommunityFocusPreset {
  return communityFocusPresets.includes(value as CommunityFocusPreset) ? (value as CommunityFocusPreset) : "all";
}

function normalizePostStatus(value: string) {
  return postStatuses.includes(value as (typeof postStatuses)[number]) ? value : "";
}

function normalizePostAuditStatus(value: string) {
  return postAuditStatuses.includes(value as (typeof postAuditStatuses)[number]) ? value : "";
}

function normalizeReportStatus(value: string) {
  return reportStatuses.includes(value as (typeof reportStatuses)[number]) ? value : "";
}

function normalizeReportPriority(value: string) {
  return reportPriorities.includes(value as (typeof reportPriorities)[number]) ? value : "";
}

function applyRouteQuery(query: Record<string, unknown>) {
  focusPreset.value = normalizeFocusPreset(readQueryText(query.preset));
  postFilters.keyword = readQueryText(query.post_keyword);
  postFilters.status = normalizePostStatus(readQueryText(query.post_status));
  postFilters.auditStatus = normalizePostAuditStatus(readQueryText(query.post_audit_status) || readQueryText(query.audit_status));
  reportFilters.keyword = readQueryText(query.report_keyword);
  reportFilters.status = normalizeReportStatus(readQueryText(query.report_status));
  reportFilters.priority = normalizeReportPriority(readQueryText(query.report_priority) || readQueryText(query.priority));
  reportFilters.assignedTo = readQueryText(query.report_assigned_to) || readQueryText(query.assigned_to);
}

function buildRouteQuery() {
  const query: Record<string, string> = {};
  if (focusPreset.value !== "all") query.preset = focusPreset.value;
  if (postFilters.keyword) query.post_keyword = postFilters.keyword;
  if (postFilters.status) query.post_status = postFilters.status;
  if (postFilters.auditStatus) query.post_audit_status = postFilters.auditStatus;
  if (reportFilters.keyword) query.report_keyword = reportFilters.keyword;
  if (reportFilters.status) query.report_status = reportFilters.status;
  if (reportFilters.priority) query.report_priority = reportFilters.priority;
  if (reportFilters.assignedTo) query.report_assigned_to = reportFilters.assignedTo;
  return query;
}

function syncRouteFromState() {
  syncingRoute.value = true;
  return Promise.resolve(router.replace({ query: buildRouteQuery() })).finally(() => {
    syncingRoute.value = false;
  });
}

async function refreshAll() {
  await Promise.all([loadPosts(), loadReports()]);
}

async function loadPosts() {
  if (!hasOpsUser.value) return;
  loadingPosts.value = true;
  try {
    const response = await listAdminCommunityPosts({
      keyword: postFilters.keyword || undefined,
      status: postFilters.status || undefined,
      audit_status: postFilters.auditStatus || undefined,
      page_size: 50,
    });
    posts.value = unwrapListPayload(response);
    await nextTick();
    clearPostSelection();
  } catch {
    notifyLoadError("社区帖子");
  } finally {
    loadingPosts.value = false;
  }
}

async function loadReports() {
  if (!hasOpsUser.value) return;
  loadingReports.value = true;
  try {
    const response = await listAdminCommunityReports({
      keyword: reportFilters.keyword || undefined,
      status: reportFilters.status || undefined,
      priority: reportFilters.priority || undefined,
      assigned_to: reportFilters.assignedTo || undefined,
      page_size: 50,
    });
    reports.value = unwrapListPayload(response);
    clearReportSelection();
  } catch {
    notifyLoadError("举报列表");
  } finally {
    loadingReports.value = false;
  }
}

function handlePostSelectionChange(rows: any[]) {
  selectedPostIds.value = rows.map((item) => Number(item.id)).filter((id) => Number.isInteger(id) && id > 0);
}

function clearPostSelection() {
  selectedPostIds.value = [];
  postTableRef.value?.clearSelection?.();
}

async function applyBulkPostAction(action: "approve" | "reject" | "archive") {
  if (!selectedPostIds.value.length) return;

  const ids = [...selectedPostIds.value];
  bulkUpdatingPosts.value = true;
  try {
    await bulkUpdateAdminCommunityPosts({ ids, action });
    notifyActionSuccess(
      action === "approve"
        ? `已批量通过 ${ids.length} 条帖子`
        : action === "reject"
          ? `已批量驳回 ${ids.length} 条帖子`
          : `已批量归档 ${ids.length} 条帖子`,
    );
    await refreshAll();
    if (selectedPost.value && ids.includes(selectedPost.value.id)) {
      await openPostDrawer(selectedPost.value.id);
    }
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "批量处理帖子失败"));
  } finally {
    bulkUpdatingPosts.value = false;
  }
}

function toggleReportSelection(reportId: number, checked: boolean | string | number) {
  if (checked) {
    if (!selectedReportIds.value.includes(reportId)) {
      selectedReportIds.value = [...selectedReportIds.value, reportId];
    }
    return;
  }
  selectedReportIds.value = selectedReportIds.value.filter((id) => id !== reportId);
}

function clearReportSelection() {
  selectedReportIds.value = [];
}

async function applyBulkReportAction(action: "processed" | "rejected") {
  if (!selectedReportIds.value.length) return;

  const ids = [...selectedReportIds.value];
  bulkUpdatingReports.value = true;
  try {
    await bulkUpdateAdminCommunityReports({ ids, action });
    notifyActionSuccess(action === "processed" ? `已批量处理 ${ids.length} 条举报` : `已批量驳回 ${ids.length} 条举报`);
    await refreshAll();
    if (selectedReport.value && ids.includes(selectedReport.value.id)) {
      await openReportDrawer(selectedReport.value.id);
    }
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "批量处理举报失败"));
  } finally {
    bulkUpdatingReports.value = false;
  }
}

function applyPostFilters() {
  postFiltersExpanded.value = false;
  void syncRouteFromState();
}

function applyReportFilters() {
  reportFiltersExpanded.value = false;
  void syncRouteFromState();
}

function resetFilters() {
  focusPreset.value = "all";
  postFilters.keyword = "";
  postFilters.status = "";
  postFilters.auditStatus = "";
  reportFilters.keyword = "";
  reportFilters.status = "";
  reportFilters.priority = "";
  reportFilters.assignedTo = "";
  postFiltersExpanded.value = false;
  reportFiltersExpanded.value = false;
  void syncRouteFromState();
}

function applyFocusPreset(preset: CommunityFocusPreset) {
  focusPreset.value = preset;
  void syncRouteFromState();
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

function fillReportDraft(report: Record<string, any> | null) {
  Object.assign(reportDraft, {
    status: report?.status || "pending",
    priority: report?.priority || "normal",
    assigned_to: typeof report?.assigned_to === "number" ? report.assigned_to : null,
    internal_note: report?.internal_note || "",
    follow_up_at: toDatetimeLocalValue(report?.follow_up_at),
  });
}

function toDatetimeLocalValue(value?: string) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

function toApiDatetimeValue(value: string) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString();
}

function priorityLabel(value: string) {
  return (
    {
      low: "低",
      normal: "普通",
      high: "高",
      urgent: "紧急",
    }[value] || value
  );
}

function priorityTagType(value: string) {
  return (
    {
      low: "info",
      normal: "success",
      high: "warning",
      urgent: "danger",
    }[value] || "info"
  );
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
    fillReportDraft(selectedReport.value);
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

async function saveReport() {
  if (!selectedReport.value) return;
  reportActionId.value = selectedReport.value.id;
  reportAction.value = reportDraft.status === "rejected" ? "rejected" : reportDraft.status === "processed" ? "processed" : "";
  try {
    const response = await updateAdminCommunityReport(selectedReport.value.id, {
      status: reportDraft.status,
      priority: reportDraft.priority,
      assigned_to: reportDraft.assigned_to,
      internal_note: reportDraft.internal_note,
      follow_up_at: toApiDatetimeValue(reportDraft.follow_up_at),
    });
    selectedReport.value = response?.data ?? null;
    fillReportDraft(selectedReport.value);
    await loadReportLogs(selectedReport.value.id);
    notifyActionSuccess("举报协作信息已经更新");
    await refreshAll();
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "更新举报协作信息失败"));
  } finally {
    reportActionId.value = null;
    reportAction.value = "";
  }
}

async function updateReportStatus(reportId: number, statusValue: "processed" | "rejected") {
  reportActionId.value = reportId;
  reportAction.value = statusValue;
  try {
    const response = await updateAdminCommunityReport(reportId, { status: statusValue });
    if (selectedReport.value?.id === reportId) {
      selectedReport.value = response?.data ?? null;
      fillReportDraft(selectedReport.value);
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

.bulk-bar-compact {
  margin-bottom: 12px;
}

.bulk-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.report-head-side {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.report-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.report-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: #5b7888;
  font-size: 13px;
}

.report-note-preview {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.75);
  border: 1px dashed rgba(16, 34, 42, 0.12);
}

.report-note-preview strong {
  color: #173042;
  font-size: 13px;
}

.report-note-preview span {
  color: #587686;
  line-height: 1.6;
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
