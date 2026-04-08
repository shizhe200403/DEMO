<template>
  <section class="page">
    <!-- 顶部栏 -->
    <div class="top-bar">
      <div class="top-bar-left">
        <p class="tag">Community</p>
        <h2>社区分享</h2>
      </div>
      <div class="top-bar-right">
        <el-button :loading="loadingPosts" plain @click="loadPosts">刷新</el-button>
      </div>
    </div>

    <CollectionSkeleton v-if="loadingPosts && !posts.length" variant="list" :card-count="4" />
    <RefreshFrame v-else :active="loadingPosts && !!posts.length" label="正在更新社区内容">
      <div class="layout">
        <!-- 左侧 sidebar -->
        <aside class="sidebar">
          <!-- 社区数据 -->
          <div class="sidebar-block">
            <p class="sidebar-block-title">社区数据</p>
            <div class="stat-list">
              <div class="stat-row">
                <span class="stat-label">社区内容</span>
                <strong class="stat-value">{{ communitySummary.total }}</strong>
              </div>
              <div class="stat-row">
                <span class="stat-label">我的沉淀</span>
                <strong class="stat-value">{{ communitySummary.mine }}</strong>
              </div>
              <div class="stat-row">
                <span class="stat-label">公开讨论</span>
                <strong class="stat-value">{{ communitySummary.published }}</strong>
              </div>
              <div class="stat-row">
                <span class="stat-label">评论互动</span>
                <strong class="stat-value">{{ communitySummary.comments }}</strong>
              </div>
            </div>
          </div>

          <!-- 筛选区 -->
          <div class="sidebar-block">
            <p class="sidebar-block-title">内容筛选</p>
            <el-radio-group v-model="viewMode" size="small" class="filter-group">
              <el-radio-button label="all">全部</el-radio-button>
              <el-radio-button label="mine">我的</el-radio-button>
            </el-radio-group>
            <el-radio-group v-model="statusFilter" size="small" class="filter-group" style="margin-top:8px">
              <el-radio-button label="all">全部状态</el-radio-button>
              <el-radio-button label="published">公开中</el-radio-button>
              <el-radio-button label="archived">已归档</el-radio-button>
            </el-radio-group>
          </div>

          <!-- 发帖面板 -->
          <div class="sidebar-block post-form-block">
            <p class="sidebar-block-title">{{ editingPostId ? "编辑帖子" : "发布帖子" }}</p>
            <el-form :model="form" label-position="top" class="post-form">
              <el-form-item label="标题">
                <el-input v-model.trim="form.title" maxlength="60" show-word-limit placeholder="例如：一周控脂午餐怎么安排更稳定" size="small" />
              </el-form-item>
              <el-form-item label="内容">
                <el-input
                  v-model.trim="form.content"
                  type="textarea"
                  :rows="4"
                  maxlength="500"
                  show-word-limit
                  placeholder="尽量写清楚场景、做法、踩坑和结论。"
                  @input="handlePostDraftInput"
                />
              </el-form-item>
              <div v-if="inlineMentionTarget === 'post'" class="mention-inline-panel">
                <button
                  v-for="item in inlineMentionCandidates"
                  :key="item.id"
                  type="button"
                  class="mention-candidate"
                  @click="insertInlineMention(item)"
                >
                  <div class="user-avatar-xs">
                    <img v-if="item.avatar_url" :src="item.avatar_url" alt="" />
                    <span v-else>{{ (item.display_name || item.username).charAt(0).toUpperCase() }}</span>
                  </div>
                  <div class="mention-candidate-copy">
                    <strong>{{ item.display_name }}</strong>
                    <span>@{{ item.username }}</span>
                  </div>
                </button>
              </div>
              <el-form-item label="帖子图片（可选）">
                <input ref="coverFileInput" type="file" accept="image/*" style="display:none" @change="onCoverFileSelected" />
                <div class="cover-upload-row">
                  <el-button plain size="small" @click="coverFileInput?.click()">{{ coverFile ? '重新选择' : '选择图片' }}</el-button>
                  <span v-if="coverFile" class="cover-hint">{{ coverFile.name }}</span>
                </div>
                <img v-if="coverPreviewUrl" :src="coverPreviewUrl" class="cover-preview" />
              </el-form-item>
              <el-form-item label="分享菜谱（可选）">
                <el-select v-model="form.linked_recipe" clearable placeholder="选择你想分享的菜谱" style="width:100%" :teleported="true" size="small">
                  <el-option v-for="r in myRecipes" :key="r.id" :label="r.title" :value="r.id" />
                </el-select>
              </el-form-item>
              <div class="form-action-row">
                <el-button
                  v-if="editingPostId"
                  plain
                  size="small"
                  @click="resetForm"
                >取消编辑</el-button>
                <el-button
                  type="primary"
                  size="small"
                  :disabled="postSubmitDisabled"
                  :loading="posting"
                  @click="submitPost"
                >{{ editingPostId ? '保存修改' : '发布帖子' }}</el-button>
                <el-button
                  size="small"
                  plain
                  @click="openMentionPicker('post')"
                >@用户</el-button>
              </div>
            </el-form>
          </div>

          <!-- 社区提示 -->
          <div class="sidebar-block sidebar-tips">
            <p class="sidebar-block-title">发帖建议</p>
            <p class="tips-item"><strong>写清楚场景</strong> — 通勤午餐、健身后加餐更容易引发互动。</p>
            <p class="tips-item"><strong>带出结果</strong> — 热量、饱腹感让内容更像真实经验。</p>
            <p class="tips-item"><strong>保留可复用信息</strong> — 别人能不能照着做决定传播价值。</p>
          </div>
        </aside>

        <!-- 右侧主区 -->
        <main class="main-area">
          <!-- toolbar -->
          <div class="toolbar">
            <el-input v-model.trim="keyword" placeholder="搜索标题、内容或作者" clearable class="search-input" size="small" />
            <el-button v-if="authorFilterId" plain size="small" @click="clearAuthorFilter">清除作者过滤</el-button>
          </div>

          <!-- 帖子列表 -->
          <div class="list">
            <article v-for="post in visiblePosts" :id="`post-${post.id}`" :key="post.id" class="post-card">
              <!-- 帖子头部：头像 + 作者 + 时间 + 状态 -->
              <div class="post-header">
                <div class="user-avatar-sm">
                  <button type="button" class="avatar-hit" @click="openUserProfile(Number(post.user))">
                    <img v-if="post.user_info?.avatar_url" :src="post.user_info.avatar_url" alt="" />
                    <span v-else>{{ (post.user_info?.display_name || post.user_info?.username || '?').charAt(0).toUpperCase() }}</span>
                  </button>
                </div>
                <div class="post-meta-line">
                  <button type="button" class="author-link" @click="openUserProfile(Number(post.user))">{{ authorLabel(post) }}</button>
                  <span class="meta-sep">·</span>
                  <span class="meta-time">{{ formatDateTime(post.created_at) }}</span>
                  <span v-if="isMine(post)" class="meta-sep">·</span>
                  <span v-if="isMine(post)" class="meta-mine">我的帖子</span>
                </div>
                <div class="badge-row">
                  <span class="status-pill" :class="statusClass(post.status)">{{ post.status === "archived" ? "已归档" : "公开中" }}</span>
                  <span class="audit-pill" :class="auditClass(post.audit_status)">{{ auditLabel(post.audit_status) }}</span>
                </div>
              </div>

              <!-- 帖子标题 -->
              <h3 class="post-title">{{ post.title }}</h3>

              <!-- 正文 + 封面缩略图 -->
              <div class="post-body-row" :class="{ 'has-cover': post.cover_image_url }">
                <p class="post-content">
                  <template v-for="(segment, index) in parseMentionSegments(post.content)" :key="`${post.id}-content-${index}`">
                    <button
                      v-if="segment.type === 'mention'"
                      type="button"
                      class="author-link mention-link"
                      @click="openUserProfile(segment.userId)"
                    >{{ segment.label }}</button>
                    <span v-else>{{ segment.text }}</span>
                  </template>
                </p>
                <button
                  v-if="post.cover_image_url"
                  type="button"
                  class="post-thumb"
                  @click="lightboxUrl = post.cover_image_url"
                >
                  <img :src="post.cover_image_url" :alt="post.title" loading="lazy" />
                </button>
              </div>

              <!-- 关联菜谱（简化：只显示名称+跳转按钮） -->
              <div v-if="post.linked_recipe_info" class="linked-recipe-row">
                <span class="linked-recipe-icon">🍽</span>
                <span class="linked-recipe-name">{{ post.linked_recipe_info.title }}</span>
                <el-button text size="small" @click="$router.push('/recipes')">查看菜谱</el-button>
              </div>

              <!-- 操作行 -->
              <div class="post-action-bar">
                <div class="post-action-left">
                  <el-button
                    text
                    size="small"
                    :loading="likingPostId === post.id"
                    :class="['like-btn', { 'is-liked': post.is_liked_by_me }]"
                    @click="toggleLike(post)"
                  >
                    <span class="like-heart">{{ post.is_liked_by_me ? '❤️' : '🤍' }}</span>
                    <span class="like-count">{{ post.like_count ?? 0 }}</span>
                  </el-button>
                  <el-button text size="small" class="comment-count-btn">
                    <span>💬</span>
                    <span>{{ post.comments?.length || 0 }}</span>
                  </el-button>
                  <el-button text size="small" @click="viewAuthorPosts(Number(post.user))">看TA更多</el-button>
                  <el-button text size="small" @click="report(post.id)">举报</el-button>
                </div>
                <div v-if="isMine(post)" class="post-action-right">
                  <el-button text size="small" @click="startEdit(post)">编辑</el-button>
                  <el-button text size="small" :loading="deletingPostId === post.id" @click="archivePost(post.id)">归档</el-button>
                  <el-button text size="small" type="danger" :loading="deletingPostId === post.id" @click="removePost(post.id)">删除</el-button>
                </div>
              </div>

              <!-- 评论输入区（紧凑一行） -->
              <div v-if="post.status !== 'archived'" class="comment-input-row">
                <div v-if="replyTargetByPostId[post.id]" class="reply-target-strip">
                  <span>正在回复 {{ replyTargetByPostId[post.id]?.displayName }}</span>
                  <el-button text size="small" @click="clearReplyTarget(post.id)">取消</el-button>
                </div>
                <div class="comment-input-line">
                  <el-input
                    v-model.trim="commentDrafts[post.id]"
                    placeholder="写评论…"
                    size="small"
                    @input="handleCommentDraftInput(post.id)"
                  />
                  <el-button
                    text
                    size="small"
                    class="icon-btn"
                    title="@用户"
                    @click="openMentionPicker(post.id)"
                  >@</el-button>
                  <input
                    :id="`comment-img-input-${post.id}`"
                    type="file" accept="image/*,image/gif" style="display:none"
                    @change="onCommentImageSelected(post.id, $event)"
                  />
                  <el-button
                    text
                    size="small"
                    class="icon-btn"
                    :title="commentImageFiles[post.id] ? '已选图' : '附图'"
                    @click="triggerCommentImageInput(post.id)"
                  >{{ commentImageFiles[post.id] ? '📎✓' : '📎' }}</el-button>
                  <el-button
                    size="small"
                    type="primary"
                    :disabled="!commentDrafts[post.id]?.trim()"
                    :loading="commentSubmittingId === post.id"
                    @click="submitComment(post.id)"
                  >发送</el-button>
                </div>
                <div v-if="inlineMentionTarget === post.id" class="mention-inline-panel mention-inline-panel-comment">
                  <button
                    v-for="item in inlineMentionCandidates"
                    :key="`${post.id}-${item.id}`"
                    type="button"
                    class="mention-candidate"
                    @click="insertInlineMention(item)"
                  >
                    <div class="user-avatar-xs">
                      <img v-if="item.avatar_url" :src="item.avatar_url" alt="" />
                      <span v-else>{{ (item.display_name || item.username).charAt(0).toUpperCase() }}</span>
                    </div>
                    <div class="mention-candidate-copy">
                      <strong>{{ item.display_name }}</strong>
                      <span>@{{ item.username }}</span>
                    </div>
                  </button>
                </div>
              </div>

              <!-- 评论列表 -->
              <div v-if="post.comments?.length" class="comments">
                <div v-for="comment in post.comments" :id="`comment-${comment.id}`" :key="comment.id" class="comment-item">
                  <div class="comment-head">
                    <div class="comment-author">
                      <div class="user-avatar-xs">
                        <button type="button" class="avatar-hit avatar-hit-small" @click="openUserProfile(Number(comment.user))">
                          <img v-if="comment.user_info?.avatar_url" :src="comment.user_info.avatar_url" alt="" />
                          <span v-else>{{ (comment.user_info?.display_name || '?').charAt(0).toUpperCase() }}</span>
                        </button>
                      </div>
                      <strong>
                        <button type="button" class="author-link" @click="openUserProfile(Number(comment.user))">{{ comment.user_info?.display_name || "用户" }}</button>
                      </strong>
                    </div>
                    <span class="comment-time">{{ formatDateTime(comment.created_at) }}</span>
                    <div class="comment-actions">
                      <el-button
                        text size="small"
                        :loading="likingCommentId === comment.id"
                        :class="['comment-like-btn', { 'is-liked': comment.is_liked_by_me }]"
                        @click="toggleCommentLike(post, comment)"
                      >{{ comment.is_liked_by_me ? '❤️' : '🤍' }} {{ comment.like_count ?? 0 }}</el-button>
                      <el-button text size="small" @click="setReplyTarget(post.id, comment)">回复</el-button>
                      <el-button v-if="isMyComment(comment)" text type="danger" size="small" :loading="deletingCommentId === comment.id" @click="removeComment(comment.id)">删除</el-button>
                    </div>
                  </div>
                  <p class="comment-text">
                    <template v-for="(segment, index) in parseMentionSegments(comment.content)" :key="`${comment.id}-comment-${index}`">
                      <button v-if="segment.type === 'mention'" type="button" class="author-link mention-link" @click="openUserProfile(segment.userId)">{{ segment.label }}</button>
                      <span v-else>{{ segment.text }}</span>
                    </template>
                  </p>
                  <img v-if="comment.image_url" :src="comment.image_url" class="comment-img" @click="lightboxUrl = comment.image_url" />
                  <div v-if="comment.replies?.length" class="comment-replies">
                    <div v-for="reply in comment.replies" :id="`comment-${reply.id}`" :key="reply.id" class="comment-item reply-item">
                      <div class="comment-head">
                        <div class="comment-author">
                          <div class="user-avatar-xs">
                            <button type="button" class="avatar-hit avatar-hit-small" @click="openUserProfile(Number(reply.user))">
                              <img v-if="reply.user_info?.avatar_url" :src="reply.user_info.avatar_url" alt="" />
                              <span v-else>{{ (reply.user_info?.display_name || '?').charAt(0).toUpperCase() }}</span>
                            </button>
                          </div>
                          <strong>
                            <button type="button" class="author-link" @click="openUserProfile(Number(reply.user))">{{ reply.user_info?.display_name || "用户" }}</button>
                          </strong>
                        </div>
                        <span class="comment-time">{{ formatDateTime(reply.created_at) }}</span>
                        <div class="comment-actions">
                          <el-button
                            text size="small"
                            :loading="likingCommentId === reply.id"
                            :class="['comment-like-btn', { 'is-liked': reply.is_liked_by_me }]"
                            @click="toggleCommentLike(post, reply)"
                          >{{ reply.is_liked_by_me ? '❤️' : '🤍' }} {{ reply.like_count ?? 0 }}</el-button>
                          <el-button text size="small" @click="setReplyTarget(post.id, reply)">回复</el-button>
                          <el-button v-if="isMyComment(reply)" text type="danger" size="small" :loading="deletingCommentId === reply.id" @click="removeComment(reply.id)">删除</el-button>
                        </div>
                      </div>
                      <p class="comment-text">
                        <template v-for="(segment, index) in parseMentionSegments(reply.content)" :key="`${reply.id}-reply-${index}`">
                          <button v-if="segment.type === 'mention'" type="button" class="author-link mention-link" @click="openUserProfile(segment.userId)">{{ segment.label }}</button>
                          <span v-else>{{ segment.text }}</span>
                        </template>
                      </p>
                      <img v-if="reply.image_url" :src="reply.image_url" class="comment-img" @click="lightboxUrl = reply.image_url" />
                    </div>
                  </div>
                </div>
              </div>
            </article>

            <PageStateBlock
              v-if="!loadingPosts && !visiblePosts.length"
              tone="empty"
              :title="emptyTitle"
              :description="emptyCopy"
              :action-label="emptyActionLabel"
              @action="handleEmptyAction"
            />
          </div>
        </main>
      </div>
    </RefreshFrame>

    <!-- Lightbox -->
    <Teleport to="body">
      <div v-if="lightboxUrl" class="lightbox" @click="lightboxUrl = ''">
        <img :src="lightboxUrl" class="lightbox-img" @click.stop />
        <button class="lightbox-close" @click="lightboxUrl = ''">✕</button>
      </div>
    </Teleport>

    <el-dialog v-model="mentionDialogVisible" title="选择要提到的用户" width="420px">
      <div class="mention-dialog">
        <el-input v-model.trim="mentionKeyword" placeholder="搜索用户名或昵称" @input="loadMentionCandidates" />
        <div v-if="mentionCandidates.length" class="mention-candidate-list">
          <button
            v-for="item in mentionCandidates"
            :key="item.id"
            type="button"
            class="mention-candidate"
            @click="insertMention(item)"
          >
            <div class="user-avatar-xs">
              <img v-if="item.avatar_url" :src="item.avatar_url" alt="" />
              <span v-else>{{ (item.display_name || item.username).charAt(0).toUpperCase() }}</span>
            </div>
            <div class="mention-candidate-copy">
              <strong>{{ item.display_name }}</strong>
              <span>@{{ item.username }}</span>
            </div>
          </button>
        </div>
        <PageStateBlock
          v-else
          tone="empty"
          title="没有匹配的用户"
          description="试试换个昵称或用户名关键词。"
          compact
        />
      </div>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import FormActionBar from "../components/FormActionBar.vue";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { ElMessageBox, extractApiErrorMessage, notifyActionError, notifyActionSuccess, notifyErrorMessage, notifyLoadError, notifyWarning } from "../lib/feedback";
import { createComment, createPost, deleteComment, deletePost, likeComment, likePost, listPosts, reportPost, updatePost, uploadCommentImage, uploadPostCover } from "../api/community";
import { searchPublicUsers } from "../api/auth";
import { listRecipes } from "../api/recipes";
import { trackEvent } from "../api/behavior";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();
const posts = ref<any[]>([]);
const myRecipes = ref<any[]>([]);
const loadingPosts = ref(false);
const viewMode = ref<"all" | "mine">("all");
const statusFilter = ref<"all" | "published" | "archived">("published");
const keyword = ref("");
const posting = ref(false);
const editingPostId = ref<number | null>(null);
const deletingPostId = ref<number | null>(null);
const deletingCommentId = ref<number | null>(null);
const commentSubmittingId = ref<number | null>(null);
const likingPostId = ref<number | null>(null);
const likingCommentId = ref<number | null>(null);
const lightboxUrl = ref("");
const commentDrafts = reactive<Record<number, string>>({});
const commentImageFiles = reactive<Record<number, File | null>>({});
const coverFile = ref<File | null>(null);
const coverPreviewUrl = ref("");
const coverFileInput = ref<HTMLInputElement | null>(null);
const mentionDialogVisible = ref(false);
const mentionKeyword = ref("");
const mentionCandidates = ref<any[]>([]);
const mentionTarget = ref<"post" | number | null>(null);
const inlineMentionTarget = ref<"post" | number | null>(null);
const inlineMentionCandidates = ref<any[]>([]);
const inlineMentionKeyword = ref("");
const form = reactive({
  title: "",
  content: "",
  linked_recipe: null as number | null,
});
const replyTargetByPostId = reactive<Record<number, { id: number; displayName: string } | null>>({});
const postSubmitDisabled = computed(() => !form.title.trim() || !form.content.trim());
const postFormTone = computed(() => (postSubmitDisabled.value ? "warning" : "ready"));
const postFormTitle = computed(() => {
  if (!form.title.trim()) {
    return "先补帖子标题";
  }
  if (!form.content.trim()) {
    return "再补充正文内容";
  }
  return editingPostId.value ? "帖子内容已完整，可以更新" : "帖子内容已完整，可以发布";
});
const postFormDescription = computed(() => {
  return "尽量写清场景、做法和结果，社区内容才更像可复用经验，而不是一句话动态。";
});

const communitySummary = computed(() => ({
  total: posts.value.length,
  mine: posts.value.filter((post) => isMine(post)).length,
  published: posts.value.filter((post) => post.status === "published").length,
  comments: posts.value.reduce((count, post) => count + (post.comments?.length || 0), 0),
}));
const authorFilterId = computed(() => Number(route.query.authorId || 0) || null);
const targetPostId = computed(() => Number(route.query.postId || 0) || null);
const targetCommentId = computed(() => Number(route.query.commentId || 0) || null);
const visiblePosts = computed(() => {
  const query = keyword.value.toLowerCase();
  return posts.value.filter((post) => {
    const matchMode = viewMode.value === "all" || isMine(post);
    const matchStatus = statusFilter.value === "all" || post.status === statusFilter.value;
    const matchAuthor = !authorFilterId.value || Number(post.user) === Number(authorFilterId.value);
    const matchKeyword =
      !query ||
      [post.title, post.content, authorLabel(post)]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(query));
    return matchMode && matchStatus && matchAuthor && matchKeyword;
  });
});
const emptyTitle = computed(() => {
  if (viewMode.value === "mine") {
    return "你还没有符合当前筛选条件的帖子。";
  }
  return "当前没有符合筛选条件的社区内容。";
});
const emptyCopy = computed(() => {
  if (viewMode.value === "mine") {
    return "可以先发布一条自己的饮食经验，或者切换筛选看看归档内容。";
  }
  return "换一个筛选条件，或者先发布一条经验帖给社区一点起始内容。";
});
const emptyActionLabel = computed(() => {
  if (viewMode.value === "mine" || statusFilter.value !== "all" || keyword.value) {
    return "清空筛选";
  }
  return "开始发帖";
});

function isMine(post: Record<string, any>) {
  return Number(post.user) === Number(auth.user?.id);
}

function isMyComment(comment: Record<string, any>) {
  return Number(comment.user) === Number(auth.user?.id);
}

function authorLabel(post: Record<string, any>) {
  return post.user_info?.display_name || post.user_info?.username || "用户";
}

function openUserProfile(userId: number) {
  if (!userId) {
    return;
  }
  if (Number(auth.user?.id) === Number(userId)) {
    router.push("/profile");
    return;
  }
  router.push(`/users/${userId}`);
}

function setReplyTarget(postId: number, comment: Record<string, any>) {
  replyTargetByPostId[postId] = {
    id: Number(comment.id),
    displayName: comment.user_info?.display_name || comment.user_info?.username || "用户",
  };
}

function clearReplyTarget(postId: number) {
  replyTargetByPostId[postId] = null;
}

function clearAuthorFilter() {
  router.push({ path: "/community", query: {} });
}

function viewAuthorPosts(userId: number) {
  router.push({ path: "/community", query: { authorId: String(userId) } });
}

function formatDateTime(value?: string) {
  if (!value) {
    return "刚刚";
  }
  return value.replace("T", " ").slice(0, 16);
}

function auditLabel(value?: string) {
  return {
    pending: "待审核",
    approved: "已通过",
    rejected: "未通过",
  }[value || "pending"] || "待审核";
}

function auditClass(value?: string) {
  return {
    pending: "is-pending",
    approved: "is-approved",
    rejected: "is-rejected",
  }[value || "pending"] || "is-pending";
}

function statusClass(value?: string) {
  return value === "archived" ? "is-archived" : "is-published";
}

function buildModerationNotice(action: "publish_post" | "update_post" | "publish_comment", moderation?: { masked?: boolean; masked_fields?: string[] }) {
  if (!moderation?.masked) {
    return "";
  }
  if (action === "publish_post") {
    return "帖子里的敏感表达已自动替换后发布。";
  }
  if (action === "update_post") {
    return "帖子里的敏感表达已自动替换后保存。";
  }
  return "评论里的敏感表达已自动替换后发布。";
}

function isBlockedModerationMessage(message: string) {
  return message.includes("禁止发布的敏感信息");
}

function handleCommunitySubmitError(error: unknown, action: string) {
  const message = extractApiErrorMessage(error, "");
  if (message && isBlockedModerationMessage(message)) {
    notifyErrorMessage(message);
    return;
  }
  notifyActionError(action);
}

function resetForm() {
  editingPostId.value = null;
  form.title = "";
  form.content = "";
  form.linked_recipe = null;
  coverFile.value = null;
  if (coverPreviewUrl.value) {
    URL.revokeObjectURL(coverPreviewUrl.value);
    coverPreviewUrl.value = "";
  }
}

async function loadMentionCandidates() {
  try {
    const response = await searchPublicUsers(mentionKeyword.value);
    mentionCandidates.value = response.data ?? [];
  } catch {
    mentionCandidates.value = [];
  }
}

async function loadInlineMentionCandidates(keyword: string) {
  try {
    const response = await searchPublicUsers(keyword);
    inlineMentionCandidates.value = response.data ?? [];
  } catch {
    inlineMentionCandidates.value = [];
  }
}

function openMentionPicker(target: "post" | number) {
  mentionTarget.value = target;
  mentionKeyword.value = "";
  mentionDialogVisible.value = true;
  void loadMentionCandidates();
}

function insertMention(user: Record<string, any>) {
  const mentionText = `@[${user.display_name}](user:${user.id}) `;
  if (mentionTarget.value === "post") {
    form.content = `${form.content}${mentionText}`.trimStart();
  } else if (typeof mentionTarget.value === "number") {
    const current = commentDrafts[mentionTarget.value] || "";
    commentDrafts[mentionTarget.value] = `${current}${mentionText}`.trimStart();
  }
  mentionDialogVisible.value = false;
}

function extractTrailingMention(text: string) {
  const matched = text.match(/(?:^|\s)@([^\s@]{1,20})$/);
  return matched ? matched[1] : "";
}

async function handlePostDraftInput() {
  const keywordValue = extractTrailingMention(form.content);
  if (!keywordValue) {
    inlineMentionTarget.value = null;
    inlineMentionCandidates.value = [];
    inlineMentionKeyword.value = "";
    return;
  }
  inlineMentionTarget.value = "post";
  inlineMentionKeyword.value = keywordValue;
  await loadInlineMentionCandidates(keywordValue);
}

async function handleCommentDraftInput(postId: number) {
  const current = commentDrafts[postId] || "";
  const keywordValue = extractTrailingMention(current);
  if (!keywordValue) {
    if (inlineMentionTarget.value === postId) {
      inlineMentionTarget.value = null;
      inlineMentionCandidates.value = [];
      inlineMentionKeyword.value = "";
    }
    return;
  }
  inlineMentionTarget.value = postId;
  inlineMentionKeyword.value = keywordValue;
  await loadInlineMentionCandidates(keywordValue);
}

function insertInlineMention(user: Record<string, any>) {
  const mentionText = `@[${user.display_name}](user:${user.id}) `;
  const replacePattern = new RegExp(`@${inlineMentionKeyword.value.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\$&")}$`);
  if (inlineMentionTarget.value === "post") {
    form.content = form.content.replace(replacePattern, mentionText);
  } else if (typeof inlineMentionTarget.value === "number") {
    const current = commentDrafts[inlineMentionTarget.value] || "";
    commentDrafts[inlineMentionTarget.value] = current.replace(replacePattern, mentionText);
  }
  inlineMentionTarget.value = null;
  inlineMentionCandidates.value = [];
  inlineMentionKeyword.value = "";
}

function parseMentionSegments(content: string) {
  const regex = /@\[(.+?)\]\(user:(\d+)\)/g;
  const segments: Array<{ type: "text"; text: string } | { type: "mention"; label: string; userId: number }> = [];
  let cursor = 0;
  let match;
  while ((match = regex.exec(content)) !== null) {
    if (match.index > cursor) {
      segments.push({ type: "text", text: content.slice(cursor, match.index) });
    }
    segments.push({ type: "mention", label: `@${match[1]}`, userId: Number(match[2]) });
    cursor = match.index + match[0].length;
  }
  if (cursor < content.length) {
    segments.push({ type: "text", text: content.slice(cursor) });
  }
  return segments.length ? segments : [{ type: "text", text: content }];
}

async function loadPosts() {
  try {
    loadingPosts.value = true;
    const [postsResponse, recipesResponse] = await Promise.all([
      listPosts(),
      listRecipes(),
    ]);
    posts.value = postsResponse.data?.items ?? postsResponse.data ?? [];
    myRecipes.value = recipesResponse.data?.items ?? recipesResponse.data ?? [];
    trackEvent({ behavior_type: "view", context_scene: "community" }).catch(() => undefined);
    requestAnimationFrame(() => focusTargetThread());
  } catch (error) {
    notifyLoadError("社区内容");
  } finally {
    loadingPosts.value = false;
  }
}

function focusTargetThread() {
  if (targetCommentId.value) {
    const commentEl = document.getElementById(`comment-${targetCommentId.value}`);
    commentEl?.scrollIntoView({ behavior: "smooth", block: "center" });
    return;
  }
  if (targetPostId.value) {
    const postEl = document.getElementById(`post-${targetPostId.value}`);
    postEl?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function startEdit(post: Record<string, any>) {
  editingPostId.value = Number(post.id);
  form.title = post.title || "";
  form.content = post.content || "";
  form.linked_recipe = post.linked_recipe ?? null;
  coverFile.value = null;
  if (coverPreviewUrl.value) {
    URL.revokeObjectURL(coverPreviewUrl.value);
    coverPreviewUrl.value = "";
  }
}

async function submitPost() {
  try {
    if (!form.title || !form.content) {
      notifyWarning("请先填写标题和内容");
      return;
    }

    posting.value = true;
    if (editingPostId.value) {
      const res = await updatePost(editingPostId.value, form);
      if (coverFile.value) {
        try {
          await uploadPostCover(editingPostId.value, coverFile.value);
        } catch { /* 封面上传失败不阻断主流程 */ }
      }
      const moderationNotice = buildModerationNotice("update_post", res.moderation);
      if (moderationNotice) {
        notifyWarning(moderationNotice);
      } else {
        notifyActionSuccess("帖子已更新");
      }
    } else {
      const res = await createPost(form);
      const newPostId = res.data?.id ?? res.id;
      if (coverFile.value && newPostId) {
        try {
          await uploadPostCover(Number(newPostId), coverFile.value);
        } catch { /* 封面上传失败不阻断主流程 */ }
      }
      const moderationNotice = buildModerationNotice("publish_post", res.moderation);
      if (moderationNotice) {
        notifyWarning(moderationNotice);
      } else {
        notifyActionSuccess("发布成功");
      }
    }
    resetForm();
    await loadPosts();
  } catch (error) {
    handleCommunitySubmitError(error, editingPostId.value ? "更新帖子" : "发布帖子");
  } finally {
    posting.value = false;
  }
}

async function submitComment(postId: number) {
  try {
    const content = commentDrafts[postId];
    if (!content) {
      notifyWarning("请先填写评论内容");
      return;
    }
    commentSubmittingId.value = postId;
    const payload: Record<string, unknown> = { content };
    if (replyTargetByPostId[postId]?.id) {
      payload.parent_comment_id = replyTargetByPostId[postId]?.id;
    }
    const res = await createComment(postId, payload);
    const newCommentId = res.data?.id ?? res.id;
    if (commentImageFiles[postId] && newCommentId) {
      try {
        await uploadCommentImage(Number(newCommentId), commentImageFiles[postId] as File);
      } catch { /* 图片上传失败不阻断评论 */ }
    }
    commentDrafts[postId] = "";
    commentImageFiles[postId] = null;
    clearReplyTarget(postId);
    const moderationNotice = buildModerationNotice("publish_comment", res.moderation);
    if (moderationNotice) {
      notifyWarning(moderationNotice);
    } else {
      notifyActionSuccess("评论已发布");
    }
    await loadPosts();
  } catch (error) {
    handleCommunitySubmitError(error, "发表评论");
  } finally {
    commentSubmittingId.value = null;
  }
}

async function removeComment(commentId: number) {
  try {
    deletingCommentId.value = commentId;
    await deleteComment(commentId);
    notifyActionSuccess("评论已删除");
    await loadPosts();
  } catch {
    notifyActionError("删除评论");
  } finally {
    deletingCommentId.value = null;
  }
}

async function archivePost(postId: number) {
  try {
    await ElMessageBox.confirm("归档后帖子将不再作为公开内容展示，但你仍然可以在“已归档”筛选里看到它。确认继续吗？", "归档帖子", {
      type: "warning",
      confirmButtonText: "归档",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }

  try {
    deletingPostId.value = postId;
    await deletePost(postId, "archive");
    notifyActionSuccess("帖子已归档");
    if (editingPostId.value === postId) {
      resetForm();
    }
    await loadPosts();
  } catch (error) {
    notifyActionError("归档帖子");
  } finally {
    deletingPostId.value = null;
  }
}

async function removePost(postId: number) {
  try {
    await ElMessageBox.confirm("彻底删除后帖子、评论和相关互动记录都会被移除，且无法恢复。确认继续吗？", "彻底删除帖子", {
      type: "warning",
      confirmButtonText: "彻底删除",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }

  try {
    deletingPostId.value = postId;
    await deletePost(postId, "delete");
    notifyActionSuccess("帖子已彻底删除");
    if (editingPostId.value === postId) {
      resetForm();
    }
    await loadPosts();
  } catch (error) {
    notifyActionError("彻底删除帖子");
  } finally {
    deletingPostId.value = null;
  }
}

async function report(postId: number) {
  try {
    const { value } = await ElMessageBox.prompt("请输入举报原因", "举报帖子", {
      confirmButtonText: "提交",
      cancelButtonText: "取消",
    });
    if (!value) return;
    await reportPost(postId, { reason: value });
    notifyActionSuccess("已提交举报，平台会在后续处理");
  } catch (error) {
    if (error !== "cancel") {
      notifyActionError("举报帖子");
    }
  }
}

function handleEmptyAction() {
  if (viewMode.value === "mine" || statusFilter.value !== "all" || keyword.value) {
    viewMode.value = "all";
    statusFilter.value = "published";
    keyword.value = "";
    return;
  }
  const target = document.querySelector(".overview-grid");
  target?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function onCoverFileSelected(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  if (coverPreviewUrl.value) URL.revokeObjectURL(coverPreviewUrl.value);
  coverFile.value = file;
  coverPreviewUrl.value = URL.createObjectURL(file);
}

async function toggleLike(post: Record<string, any>) {
  if (!auth.isAuthenticated) {
    notifyWarning("请先登录后再点赞");
    return;
  }
  try {
    likingPostId.value = Number(post.id);
    const res = await likePost(Number(post.id));
    const target = posts.value.find((p) => p.id === post.id);
    if (target) {
      const liked: boolean = res?.data?.liked ?? !target.is_liked_by_me;
      const count: number = res?.data?.like_count ?? (liked ? (target.like_count ?? 0) + 1 : Math.max(0, (target.like_count ?? 1) - 1));
      // 用 Object.assign 强制触发 Vue 响应式更新
      Object.assign(target, { is_liked_by_me: liked, like_count: count });
    }
  } catch {
    notifyActionError("点赞操作");
  } finally {
    likingPostId.value = null;
  }
}

async function toggleCommentLike(post: Record<string, any>, comment: Record<string, any>) {
  if (!auth.isAuthenticated) {
    notifyWarning("请先登录后再点赞");
    return;
  }
  try {
    likingCommentId.value = Number(comment.id);
    const res = await likeComment(Number(comment.id));
    const targetPost = posts.value.find((p) => p.id === post.id);
    if (targetPost) {
      const targetComment = targetPost.comments?.find((c: any) => c.id === comment.id);
      if (targetComment) {
        const liked: boolean = res?.data?.liked ?? !targetComment.is_liked_by_me;
        const count: number = res?.data?.like_count ?? (liked ? (targetComment.like_count ?? 0) + 1 : Math.max(0, (targetComment.like_count ?? 1) - 1));
        Object.assign(targetComment, { is_liked_by_me: liked, like_count: count });
      }
    }
  } catch {
    notifyActionError("点赞操作");
  } finally {
    likingCommentId.value = null;
  }
}

function triggerCommentImageInput(postId: number) {  const el = document.getElementById(`comment-img-input-${postId}`) as HTMLInputElement | null;
  el?.click();
}

function onCommentImageSelected(postId: number, e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (file) commentImageFiles[postId] = file;
}

function mealTypeLabel(val: string) {
  return ({ breakfast: "早餐", lunch: "午餐", dinner: "晚餐", snack: "加餐" } as Record<string, string>)[val] || val;
}

function difficultyLabel(val: string) {
  return ({ easy: "简单", medium: "中等", hard: "困难" } as Record<string, string>)[val] || val;
}

onMounted(loadPosts);
</script>

<style scoped>
/* ========== 页面骨架 ========== */
.page {
  display: grid;
  gap: 16px;
}

.top-bar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.top-bar-left .tag {
  margin: 0 0 4px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-size: 12px;
  color: #3e6d7f;
}

.top-bar-left h2 {
  margin: 0;
  font-size: 26px;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* ========== 双栏布局 ========== */
.layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 20px;
  align-items: start;
}

/* ========== 左侧 sidebar ========== */
.sidebar {
  display: grid;
  gap: 14px;
  position: sticky;
  top: 16px;
}

.sidebar-block {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 8px 24px rgba(15, 30, 39, 0.06);
}

.sidebar-block-title {
  margin: 0 0 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #3e6d7f;
}

/* 数据统计 */
.stat-list {
  display: grid;
  gap: 6px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.stat-label {
  color: #6f8592;
}

.stat-value {
  font-size: 15px;
  color: #173042;
}

/* 筛选 */
.filter-group {
  width: 100%;
}

/* 发帖表单 */
.post-form-block {
  /* slightly more padding to breathe */
}

.post-form .el-form-item {
  margin-bottom: 10px;
}

.form-action-row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 4px;
}

.cover-upload-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cover-preview {
  margin-top: 8px;
  width: 100%;
  max-height: 120px;
  object-fit: cover;
  border-radius: 10px;
}

.cover-hint {
  font-size: 12px;
  color: #6f8592;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 120px;
}

/* 发帖提示 */
.sidebar-tips {
  font-size: 12px;
}

.tips-item {
  margin: 0 0 6px;
  color: #476072;
  line-height: 1.6;
}

.tips-item:last-child {
  margin-bottom: 0;
}

/* ========== 右侧主区 ========== */
.main-area {
  display: grid;
  gap: 14px;
  min-width: 0;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 180px;
  max-width: 360px;
}

/* ========== 帖子列表 ========== */
.list {
  display: grid;
  gap: 12px;
}

.post-card {
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 6px 20px rgba(15, 30, 39, 0.06);
  display: grid;
  gap: 8px;
}

/* 帖子头部 */
.post-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.post-meta-line {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #6f8592;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
}

.meta-sep {
  color: #aac;
}

.meta-time {
  color: #8a9eab;
}

.meta-mine {
  color: #1d6f5f;
  font-weight: 600;
}

.badge-row {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-shrink: 0;
}

/* 标题 */
.post-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #173042;
  line-height: 1.4;
}

/* 正文 + 封面 */
.post-body-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 10px;
  align-items: start;
}

.post-body-row.has-cover {
  grid-template-columns: minmax(0, 1fr) 64px;
}

.post-content {
  margin: 0;
  font-size: 14px;
  color: #476072;
  line-height: 1.65;
  white-space: pre-wrap;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-thumb {
  border: 0;
  padding: 0;
  background: transparent;
  cursor: pointer;
  border-radius: 10px;
  overflow: hidden;
  flex-shrink: 0;
}

.post-thumb img {
  width: 64px;
  height: 64px;
  object-fit: cover;
  display: block;
  border-radius: 10px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  transition: opacity 0.15s;
}

.post-thumb:hover img {
  opacity: 0.85;
}

/* 关联菜谱（简化行） */
.linked-recipe-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 10px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.07);
  font-size: 13px;
}

.linked-recipe-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.linked-recipe-name {
  flex: 1;
  font-weight: 600;
  color: #173042;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 操作行 */
.post-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  flex-wrap: wrap;
}

.post-action-left,
.post-action-right {
  display: flex;
  align-items: center;
  gap: 2px;
}

/* 评论输入区 */
.comment-input-row {
  display: grid;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px solid rgba(16, 34, 42, 0.06);
}

.comment-input-line {
  display: flex;
  align-items: center;
  gap: 4px;
}

.comment-input-line .el-input {
  flex: 1;
}

.icon-btn {
  flex-shrink: 0;
  padding: 0 6px;
  font-size: 14px;
}

/* 点赞 */
.like-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  padding: 2px 6px;
  transition: transform 0.15s;
}

.like-btn:active {
  transform: scale(1.2);
}

.like-heart {
  font-size: 15px;
  line-height: 1;
}

.like-count {
  font-size: 12px;
  color: #5a7a8a;
}

.comment-count-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  padding: 2px 6px;
}

/* ========== 评论区 ========== */
.comments {
  display: grid;
  gap: 8px;
  padding-top: 4px;
}

.comment-item {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.comment-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.comment-author {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.comment-author strong {
  font-size: 13px;
}

.comment-time {
  font-size: 12px;
  color: #8a9eab;
  flex-shrink: 0;
}

.comment-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.comment-like-btn {
  font-size: 12px;
  padding: 1px 4px;
}

.comment-text {
  margin: 6px 0 0;
  font-size: 13px;
  color: #476072;
  line-height: 1.6;
}

.comment-img {
  margin-top: 6px;
  max-width: 100%;
  max-height: 160px;
  border-radius: 8px;
  object-fit: cover;
  display: block;
  cursor: pointer;
  transition: opacity 0.15s;
}

.comment-img:hover {
  opacity: 0.88;
}

.comment-replies {
  margin-top: 8px;
  padding-left: 14px;
  border-left: 2px solid rgba(62, 109, 127, 0.15);
  display: grid;
  gap: 6px;
}

.reply-item {
  background: rgba(245, 250, 253, 0.7);
  border-radius: 8px;
  padding: 8px 10px;
}

.reply-target-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  background: rgba(62, 109, 127, 0.08);
  border-radius: 6px;
  font-size: 12px;
  color: #3e6d7f;
}

/* ========== 状态/审核标签 ========== */
.status-pill,
.audit-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.status-pill.is-published {
  background: rgba(29, 111, 95, 0.14);
  color: #1d6f5f;
}

.status-pill.is-archived {
  background: rgba(110, 124, 136, 0.14);
  color: #5d6b76;
}

.audit-pill.is-approved {
  background: rgba(23, 48, 66, 0.12);
  color: #173042;
}

.audit-pill.is-pending {
  background: rgba(185, 115, 38, 0.14);
  color: #9a621a;
}

.audit-pill.is-rejected {
  background: rgba(156, 62, 62, 0.14);
  color: #8c3434;
}

/* ========== 通用元素 ========== */
.author-link {
  border: 0;
  padding: 0;
  background: transparent;
  color: #1f4f67;
  font-weight: 700;
  cursor: pointer;
  font-size: inherit;
}

.mention-link {
  display: inline;
  margin-right: 2px;
}

.user-avatar-sm,
.user-avatar-xs {
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  background: #d0e8f5;
  color: #2d6a8a;
}

.user-avatar-sm {
  width: 32px;
  height: 32px;
  font-size: 13px;
}

.user-avatar-xs {
  width: 24px;
  height: 24px;
  font-size: 11px;
}

.user-avatar-sm img,
.user-avatar-xs img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-hit {
  width: 100%;
  height: 100%;
  border: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  cursor: pointer;
}

.avatar-hit-small {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  overflow: hidden;
  background: #d0e8f5;
  color: #2d6a8a;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  padding: 0;
}

.avatar-hit-small img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* ========== @提及面板 ========== */
.mention-inline-panel {
  display: grid;
  gap: 8px;
  margin: 4px 0 8px;
  padding: 10px;
  border-radius: 12px;
  background: rgba(247, 251, 255, 0.96);
  border: 1px solid rgba(16, 34, 42, 0.08);
}

.mention-inline-panel-comment {
  margin-top: 6px;
}

.mention-dialog {
  display: grid;
  gap: 12px;
}

.mention-candidate-list {
  display: grid;
  gap: 8px;
}

.mention-candidate {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(247, 251, 255, 0.94);
  text-align: left;
  cursor: pointer;
}

.mention-candidate-copy {
  display: grid;
  gap: 2px;
}

.mention-candidate-copy strong {
  color: #173042;
  font-size: 13px;
}

.mention-candidate-copy span {
  color: #6f8592;
  font-size: 12px;
}

/* ========== Lightbox ========== */
.lightbox {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.lightbox-img {
  max-width: 92vw;
  max-height: 92vh;
  border-radius: 8px;
  object-fit: contain;
  cursor: default;
  box-shadow: 0 8px 40px rgba(0,0,0,0.5);
}

.lightbox-close {
  position: absolute;
  top: 20px;
  right: 24px;
  background: none;
  border: none;
  color: #fff;
  font-size: 24px;
  cursor: pointer;
  opacity: 0.8;
  line-height: 1;
}

.lightbox-close:hover {
  opacity: 1;
}

/* ========== 响应式 ========== */
@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static;
  }
}

@media (max-width: 600px) {
  .post-body-row.has-cover {
    grid-template-columns: 1fr;
  }

  .post-thumb img {
    width: 100%;
    height: 120px;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input {
    max-width: 100%;
  }

  .post-action-bar {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
