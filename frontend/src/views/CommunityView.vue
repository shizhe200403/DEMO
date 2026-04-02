<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Community</p>
        <h2>社区分享</h2>
        <p class="desc">社区不只是“能发帖”，还要让用户看得懂谁发的、哪些内容正在沉淀、哪些已经归档，以及自己下一步适合做什么。</p>
      </div>
      <el-button :loading="loadingPosts" @click="loadPosts">刷新</el-button>
    </div>

    <CollectionSkeleton v-if="loadingPosts && !posts.length" variant="list" :card-count="4" />
    <RefreshFrame v-else :active="loadingPosts && !!posts.length" label="正在更新社区内容">
    <div class="summary-grid">
      <article>
        <span>社区内容</span>
        <strong>{{ communitySummary.total }}</strong>
        <p>当前可查看的帖子总数。</p>
      </article>
      <article>
        <span>我的沉淀</span>
        <strong>{{ communitySummary.mine }}</strong>
        <p>你已经发布并保留在系统中的帖子数量。</p>
      </article>
      <article>
        <span>公开讨论</span>
        <strong>{{ communitySummary.published }}</strong>
        <p>仍然作为公开内容展示的帖子数。</p>
      </article>
      <article>
        <span>评论互动</span>
        <strong>{{ communitySummary.comments }}</strong>
        <p>当前页面可见的评论总数。</p>
      </article>
    </div>

    <div class="overview-grid">
      <div class="card">
        <div class="card-head">
          <div>
            <h3>{{ editingPostId ? "编辑帖子" : "发布帖子" }}</h3>
            <p>{{ editingPostId ? "修改后会覆盖当前帖子内容。" : "分享今天吃了什么、做法心得或饮食管理经验，让内容真正沉淀下来。" }}</p>
          </div>
          <el-button v-if="editingPostId" plain @click="resetForm">取消编辑</el-button>
        </div>
        <el-form :model="form" label-position="top">
          <el-form-item label="标题">
            <el-input v-model.trim="form.title" maxlength="60" show-word-limit placeholder="例如：一周控脂午餐怎么安排更稳定" />
          </el-form-item>
          <el-form-item label="内容">
            <el-input
              v-model.trim="form.content"
              type="textarea"
              :rows="5"
              maxlength="500"
              show-word-limit
              placeholder="尽量写清楚场景、做法、踩坑和结论，用户更容易互动。"
            />
          </el-form-item>
          <el-form-item label="帖子图片（可选）">
            <input ref="coverFileInput" type="file" accept="image/*" style="display:none" @change="onCoverFileSelected" />
            <div class="cover-upload-row">
              <el-button plain @click="coverFileInput?.click()">{{ coverFile ? '重新选择' : '选择图片' }}</el-button>
              <span v-if="coverFile" class="cover-hint">{{ coverFile.name }}</span>
            </div>
            <img v-if="coverPreviewUrl" :src="coverPreviewUrl" class="cover-preview" />
          </el-form-item>
          <el-form-item label="分享菜谱（可选）">
            <el-select v-model="form.linked_recipe" clearable placeholder="选择你想分享的菜谱" style="width:100%">
              <el-option v-for="r in myRecipes" :key="r.id" :label="r.title" :value="r.id" />
            </el-select>
          </el-form-item>
          <FormActionBar
            compact
            :tone="posting ? 'saving' : postFormTone"
            :title="postFormTitle"
            :description="postFormDescription"
            :primary-label="editingPostId ? '保存修改' : '发布帖子'"
            :secondary-label="editingPostId ? '取消编辑' : ''"
            :disabled="postSubmitDisabled"
            :loading="posting"
            @primary="submitPost"
            @secondary="resetForm"
          />
        </el-form>
      </div>

      <div class="card">
        <div class="card-head">
          <div>
            <h3>发布建议</h3>
            <p>社区内容更适合沉淀“经验”和“复盘”，而不是一句话动态。</p>
          </div>
        </div>
        <div class="tips">
          <article>
            <strong>写清楚场景</strong>
            <p>例如通勤午餐、健身后加餐、控糖早餐，比泛泛而谈更容易引发互动。</p>
          </article>
          <article>
            <strong>带出结果</strong>
            <p>说明热量、饱腹感、执行成本或复购意愿，内容会更像真实经验。</p>
          </article>
          <article>
            <strong>保留可复用信息</strong>
            <p>别人能不能照着做，决定这条帖子有没有二次传播和收藏价值。</p>
          </article>
        </div>
      </div>
    </div>

    <div class="toolbar">
      <el-radio-group v-model="viewMode" size="large" class="mobile-scroll-row">
        <el-radio-button label="all">全部内容</el-radio-button>
        <el-radio-button label="mine">我的帖子</el-radio-button>
      </el-radio-group>
      <el-radio-group v-model="statusFilter" size="large" class="mobile-scroll-row">
        <el-radio-button label="all">全部状态</el-radio-button>
        <el-radio-button label="published">公开中</el-radio-button>
        <el-radio-button label="archived">已归档</el-radio-button>
      </el-radio-group>
      <el-input v-model.trim="keyword" placeholder="搜索标题、内容或作者" clearable class="search-input" />
    </div>

    <div class="list">
      <article v-for="post in visiblePosts" :key="post.id" class="post-card">
        <div v-if="post.cover_image_url" class="post-cover">
          <img :src="post.cover_image_url" :alt="post.title" />
        </div>
        <div class="row">
          <div class="user-avatar-sm">
            <img v-if="post.user_info?.avatar_url" :src="post.user_info.avatar_url" alt="" />
            <span v-else>{{ (post.user_info?.display_name || post.user_info?.username || '?').charAt(0).toUpperCase() }}</span>
          </div>
          <div class="post-main">
            <div class="post-top">
              <strong>{{ post.title }}</strong>
              <div class="badge-row">
                <span class="status-pill" :class="statusClass(post.status)">{{ post.status === "archived" ? "已归档" : "公开中" }}</span>
                <span class="audit-pill" :class="auditClass(post.audit_status)">{{ auditLabel(post.audit_status) }}</span>
              </div>
            </div>
            <p class="meta">
              {{ authorLabel(post) }} · {{ formatDateTime(post.created_at) }}
              <span v-if="isMine(post)"> · 我的帖子</span>
              <span> · {{ post.comments?.length || 0 }} 条评论</span>
            </p>
          </div>
          <div class="post-actions" v-if="isMine(post)">
            <el-button text @click="startEdit(post)">编辑</el-button>
            <el-button text type="danger" :loading="deletingPostId === post.id" @click="removePost(post.id)">删除</el-button>
          </div>
        </div>

        <p class="content">{{ post.content }}</p>

        <div v-if="post.linked_recipe_info" class="linked-recipe-card">
          <img v-if="post.linked_recipe_info.cover_image_url" :src="post.linked_recipe_info.cover_image_url" class="linked-recipe-thumb" />
          <div class="linked-recipe-meta">
            <strong>{{ post.linked_recipe_info.title }}</strong>
            <p>{{ mealTypeLabel(post.linked_recipe_info.meal_type) }}{{ post.linked_recipe_info.cook_time_minutes ? ` · ${post.linked_recipe_info.cook_time_minutes} 分钟` : '' }}</p>
          </div>
        </div>

        <div class="comment-box" v-if="post.status !== 'archived'">
          <el-button
            text
            :loading="likingPostId === post.id"
            :type="post.is_liked_by_me ? 'primary' : 'default'"
            @click="toggleLike(post)"
          >{{ post.is_liked_by_me ? '已点赞' : '点赞' }} {{ post.like_count || 0 }}</el-button>
          <el-input v-model.trim="commentDrafts[post.id]" placeholder="写评论" />
          <input
            :ref="(el) => { commentImageInputs[post.id] = el as HTMLInputElement }"
            type="file" accept="image/*" style="display:none"
            @change="onCommentImageSelected(post.id, $event)"
          />
          <el-button plain @click="commentImageInputs[post.id]?.click()">{{ commentImageFiles[post.id] ? '已选图' : '附图' }}</el-button>
          <el-button :disabled="!commentDrafts[post.id]?.trim()" :loading="commentSubmittingId === post.id" @click="submitComment(post.id)">评论</el-button>
          <el-button plain @click="report(post.id)">举报</el-button>
        </div>

        <div class="comments" v-if="post.comments?.length">
          <div v-for="comment in post.comments" :key="comment.id" class="comment-item">
            <div class="comment-head">
              <div class="comment-author">
                <div class="user-avatar-xs">
                  <img v-if="comment.user_info?.avatar_url" :src="comment.user_info.avatar_url" alt="" />
                  <span v-else>{{ (comment.user_info?.display_name || '?').charAt(0).toUpperCase() }}</span>
                </div>
                <strong>{{ comment.user_info?.display_name || "用户" }}</strong>
              </div>
              <span>{{ formatDateTime(comment.created_at) }}</span>
              <el-button v-if="isMyComment(comment)" text type="danger" size="small" :loading="deletingCommentId === comment.id" @click="removeComment(comment.id)">删除</el-button>
            </div>
            <p>{{ comment.content }}</p>
            <img v-if="comment.image_url" :src="comment.image_url" class="comment-img" />
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
    </RefreshFrame>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import FormActionBar from "../components/FormActionBar.vue";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { ElMessageBox, notifyActionError, notifyActionSuccess, notifyLoadError, notifyWarning } from "../lib/feedback";
import { createComment, createPost, deleteComment, deletePost, likePost, listPosts, reportPost, updatePost, uploadCommentImage, uploadPostCover } from "../api/community";
import { listRecipes } from "../api/recipes";
import { trackEvent } from "../api/behavior";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
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
const commentDrafts = reactive<Record<number, string>>({});
const commentImageFiles = reactive<Record<number, File | null>>({});
const commentImageInputs = reactive<Record<number, HTMLInputElement | null>>({});
const coverFile = ref<File | null>(null);
const coverPreviewUrl = ref("");
const coverFileInput = ref<HTMLInputElement | null>(null);
const form = reactive({
  title: "",
  content: "",
  linked_recipe: null as number | null,
});
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
const visiblePosts = computed(() => {
  const query = keyword.value.toLowerCase();
  return posts.value.filter((post) => {
    const matchMode = viewMode.value === "all" || isMine(post);
    const matchStatus = statusFilter.value === "all" || post.status === statusFilter.value;
    const matchKeyword =
      !query ||
      [post.title, post.content, authorLabel(post)]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(query));
    return matchMode && matchStatus && matchKeyword;
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
  } catch (error) {
    notifyLoadError("社区内容");
  } finally {
    loadingPosts.value = false;
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
      await updatePost(editingPostId.value, form);
      if (coverFile.value) {
        try {
          await uploadPostCover(editingPostId.value, coverFile.value);
        } catch { /* 封面上传失败不阻断主流程 */ }
      }
      notifyActionSuccess("帖子已更新");
    } else {
      const res = await createPost(form);
      const newPostId = res.data?.id ?? res.id;
      if (coverFile.value && newPostId) {
        try {
          await uploadPostCover(Number(newPostId), coverFile.value);
        } catch { /* 封面上传失败不阻断主流程 */ }
      }
      notifyActionSuccess("发布成功");
    }
    resetForm();
    await loadPosts();
  } catch (error) {
    notifyActionError(editingPostId.value ? "更新帖子" : "发布帖子");
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
    const res = await createComment(postId, { content });
    const newCommentId = res.data?.id ?? res.id;
    if (commentImageFiles[postId] && newCommentId) {
      try {
        await uploadCommentImage(Number(newCommentId), commentImageFiles[postId] as File);
      } catch { /* 图片上传失败不阻断评论 */ }
    }
    commentDrafts[postId] = "";
    commentImageFiles[postId] = null;
    notifyActionSuccess("评论已发布");
    await loadPosts();
  } catch (error) {
    notifyActionError("发表评论");
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

async function removePost(postId: number) {
  try {
    await ElMessageBox.confirm("删除后帖子将进入归档状态，不再作为公开内容展示。确认继续吗？", "删除帖子", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }

  try {
    deletingPostId.value = postId;
    await deletePost(postId);
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
    post.is_liked_by_me = res.data.liked;
    post.like_count = res.data.like_count;
  } catch {
    notifyActionError("点赞操作");
  } finally {
    likingPostId.value = null;
  }
}

function onCommentImageSelected(postId: number, e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (file) commentImageFiles[postId] = file;
}

function mealTypeLabel(val: string) {
  return ({ breakfast: "早餐", lunch: "午餐", dinner: "晚餐", snack: "加餐" } as Record<string, string>)[val] || "";
}

onMounted(loadPosts);
</script>

<style scoped>
.page {
  display: grid;
  gap: 16px;
}

.head,
.card-head,
.row,
.actions,
.toolbar,
.post-top,
.badge-row,
.comment-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
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
.meta,
.content,
.comment-item p,
.empty-state p,
.tips p,
.summary-grid p {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.65;
}

.summary-grid,
.overview-grid,
.list,
.tips,
.comments {
  display: grid;
  gap: 14px;
}

.summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
}

.overview-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.card,
.summary-grid article,
.post-card,
.empty-state {
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.summary-grid span,
.comment-head span {
  font-size: 12px;
  color: #5a7a8a;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.summary-grid strong {
  display: block;
  margin-top: 8px;
  font-size: 24px;
}

.tips article,
.comment-item {
  padding: 16px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.toolbar {
  flex-wrap: wrap;
}

.search-input {
  width: min(320px, 100%);
}

.post-main {
  flex: 1;
}

.post-top strong,
.empty-state strong {
  font-size: 20px;
}

.meta {
  font-size: 13px;
  color: #6f8592;
}

.content {
  white-space: pre-wrap;
}

.status-pill,
.audit-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
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

.post-actions,
.comment-box {
  display: flex;
  gap: 10px;
  align-items: center;
}

.comment-box {
  margin-top: 14px;
}

.comment-item strong {
  font-size: 15px;
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
  width: 40px;
  height: 40px;
  font-size: 16px;
}

.user-avatar-xs {
  width: 28px;
  height: 28px;
  font-size: 12px;
}

.user-avatar-sm img,
.user-avatar-xs img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.comment-author {
  display: flex;
  align-items: center;
  gap: 8px;
}

.post-cover {
  margin: -24px -24px 16px;
  border-radius: 20px 20px 0 0;
  overflow: hidden;
  height: 180px;
}

.post-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-upload-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cover-preview {
  margin-top: 8px;
  width: 100%;
  max-height: 140px;
  object-fit: cover;
  border-radius: 12px;
}

.cover-hint {
  font-size: 12px;
  color: #6f8592;
}

.linked-recipe-card {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.linked-recipe-thumb {
  width: 56px;
  height: 56px;
  border-radius: 10px;
  object-fit: cover;
  flex-shrink: 0;
}

.linked-recipe-meta strong {
  font-size: 14px;
}

.linked-recipe-meta p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #5a7a8a;
}

.comment-img {
  margin-top: 8px;
  max-width: 100%;
  max-height: 200px;
  border-radius: 10px;
  object-fit: cover;
  display: block;
}

@media (max-width: 960px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .summary-grid,
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .head,
  .card-head,
  .row,
  .actions,
  .toolbar,
  .post-top,
  .badge-row,
  .post-actions,
  .comment-box,
  .comment-head {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input {
    width: 100%;
  }
}
</style>
