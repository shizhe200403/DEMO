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
          <div class="mention-entry">
            <el-button plain @click="openMentionPicker('post')">@用户</el-button>
            <span class="mention-entry-copy">需要提到某位用户时，先选人再插入到正文。</span>
          </div>
          <el-form-item label="帖子图片（可选）">
            <input ref="coverFileInput" type="file" accept="image/*" style="display:none" @change="onCoverFileSelected" />
            <div class="cover-upload-row">
              <el-button plain @click="coverFileInput?.click()">{{ coverFile ? '重新选择' : '选择图片' }}</el-button>
              <span v-if="coverFile" class="cover-hint">{{ coverFile.name }}</span>
            </div>
            <img v-if="coverPreviewUrl" :src="coverPreviewUrl" class="cover-preview" />
          </el-form-item>
          <el-form-item label="分享菜谱（可选）">
            <el-select v-model="form.linked_recipe" clearable placeholder="选择你想分享的菜谱" style="width:100%" :teleported="true">
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
        <el-button v-if="authorFilterId" plain @click="clearAuthorFilter">清除作者过滤</el-button>
      </div>

    <div class="list">
      <article v-for="post in visiblePosts" :id="`post-${post.id}`" :key="post.id" class="post-card">
        <div class="row">
          <div class="user-avatar-sm">
            <button type="button" class="avatar-hit" @click="openUserProfile(Number(post.user))">
              <img v-if="post.user_info?.avatar_url" :src="post.user_info.avatar_url" alt="" />
              <span v-else>{{ (post.user_info?.display_name || post.user_info?.username || '?').charAt(0).toUpperCase() }}</span>
            </button>
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
              <button type="button" class="author-link" @click="openUserProfile(Number(post.user))">{{ authorLabel(post) }}</button>
              · {{ formatDateTime(post.created_at) }}
              <span v-if="isMine(post)"> · 我的帖子</span>
              <span> · {{ post.comments?.length || 0 }} 条评论</span>
            </p>
          </div>
          <div class="post-actions" v-if="isMine(post)">
            <el-button text @click="startEdit(post)">编辑</el-button>
            <el-button text type="danger" :loading="deletingPostId === post.id" @click="removePost(post.id)">删除</el-button>
          </div>
        </div>
        <div class="post-secondary-actions">
          <el-button text @click="viewAuthorPosts(Number(post.user))">看作者全部内容</el-button>
        </div>

        <div class="post-content-row" :class="{ 'has-cover': post.cover_image_url }">
          <p class="content">
            <template v-for="(segment, index) in parseMentionSegments(post.content)" :key="`${post.id}-content-${index}`">
              <button
                v-if="segment.type === 'mention'"
                type="button"
                class="author-link mention-link"
                @click="openUserProfile(segment.userId)"
              >
                {{ segment.label }}
              </button>
              <span v-else>{{ segment.text }}</span>
            </template>
          </p>
          <button
            v-if="post.cover_image_url"
            type="button"
            class="post-inline-cover"
            @click="lightboxUrl = post.cover_image_url"
          >
            <img :src="post.cover_image_url" :alt="post.title" loading="lazy" />
            <span>查看大图</span>
          </button>
        </div>

        <div v-if="post.linked_recipe_info" class="linked-recipe-card">
          <div class="linked-recipe-header">
            <img v-if="post.linked_recipe_info.cover_image_url" :src="post.linked_recipe_info.cover_image_url" class="linked-recipe-thumb" @click="lightboxUrl = post.linked_recipe_info.cover_image_url" />
            <div class="linked-recipe-meta">
              <strong>{{ post.linked_recipe_info.title }}</strong>
              <div class="linked-recipe-tags">
                <span v-if="post.linked_recipe_info.meal_type" class="recipe-tag">{{ mealTypeLabel(post.linked_recipe_info.meal_type) }}</span>
                <span v-if="post.linked_recipe_info.difficulty" class="recipe-tag">{{ difficultyLabel(post.linked_recipe_info.difficulty) }}</span>
                <span v-if="post.linked_recipe_info.prep_time_minutes" class="recipe-tag">备料 {{ post.linked_recipe_info.prep_time_minutes }} 分钟</span>
                <span v-if="post.linked_recipe_info.cook_time_minutes" class="recipe-tag">烹饪 {{ post.linked_recipe_info.cook_time_minutes }} 分钟</span>
                <span v-if="post.linked_recipe_info.servings" class="recipe-tag">{{ post.linked_recipe_info.servings }} 人份</span>
              </div>
              <div v-if="post.linked_recipe_info.taste_tags?.length || post.linked_recipe_info.cuisine_tags?.length" class="linked-recipe-flavor-tags">
                <span v-for="tag in [...(post.linked_recipe_info.taste_tags||[]), ...(post.linked_recipe_info.cuisine_tags||[])]" :key="tag" class="flavor-tag">{{ tag }}</span>
              </div>
              <p v-if="post.linked_recipe_info.description" class="linked-recipe-desc">{{ post.linked_recipe_info.description }}</p>
            </div>
          </div>
          <div v-if="post.linked_recipe_info.ingredients?.length" class="linked-recipe-section">
            <p class="linked-recipe-section-title">食材</p>
            <div class="ingredient-list">
              <span v-for="ing in post.linked_recipe_info.ingredients" :key="ing.name" class="ingredient-chip" :class="{ 'is-main': ing.is_main }">
                {{ ing.name }} {{ ing.amount }}{{ ing.unit }}
              </span>
            </div>
          </div>
          <div v-if="post.linked_recipe_info.steps?.length" class="linked-recipe-section">
            <p class="linked-recipe-section-title">做法步骤</p>
            <ol class="step-list">
              <li v-for="step in post.linked_recipe_info.steps" :key="step.step_no" class="step-item">
                <span class="step-text">{{ step.content }}</span>
                <img v-if="step.step_image_url" :src="step.step_image_url" class="step-img" @click="lightboxUrl = step.step_image_url" />
              </li>
            </ol>
          </div>
        </div>

        <div class="comment-box" v-if="post.status !== 'archived'">
          <el-button
            text
            :loading="likingPostId === post.id"
            :class="['like-btn', { 'is-liked': post.is_liked_by_me }]"
            @click="toggleLike(post)"
          >
            <span class="like-heart">{{ post.is_liked_by_me ? '❤️' : '🤍' }}</span>
            <span class="like-count">{{ post.like_count ?? 0 }}</span>
          </el-button>
          <el-input v-model.trim="commentDrafts[post.id]" placeholder="写评论" @input="handleCommentDraftInput(post.id)" />
          <el-button plain @click="openMentionPicker(post.id)">@用户</el-button>
          <input
            :id="`comment-img-input-${post.id}`"
            type="file" accept="image/*,image/gif" style="display:none"
            @change="onCommentImageSelected(post.id, $event)"
          />
          <el-button plain @click="triggerCommentImageInput(post.id)">{{ commentImageFiles[post.id] ? '已选图' : '附图' }}</el-button>
          <el-button :disabled="!commentDrafts[post.id]?.trim()" :loading="commentSubmittingId === post.id" @click="submitComment(post.id)">评论</el-button>
          <el-button plain @click="report(post.id)">举报</el-button>
        </div>
        <div v-if="replyTargetByPostId[post.id]" class="reply-target-strip">
          <span>正在回复 {{ replyTargetByPostId[post.id]?.displayName }}</span>
          <el-button text @click="clearReplyTarget(post.id)">取消回复</el-button>
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

        <div class="comments" v-if="post.comments?.length">
          <div v-for="comment in post.comments" :id="`comment-${comment.id}`" :key="comment.id" class="comment-item">
            <div class="comment-head">
              <div class="comment-author">
                <div class="user-avatar-xs">
                  <button type="button" class="avatar-hit avatar-hit-small" @click="openUserProfile(Number(comment.user))">
                    <img v-if="comment.user_info?.avatar_url" :src="comment.user_info.avatar_url" alt="" />
                    <span v-else>{{ (comment.user_info?.display_name || '?').charAt(0).toUpperCase() }}</span>
                  </button>
                </div>
                <strong><button type="button" class="author-link" @click="openUserProfile(Number(comment.user))">{{ comment.user_info?.display_name || "用户" }}</button></strong>
              </div>
              <span>{{ formatDateTime(comment.created_at) }}</span>
              <div class="comment-actions">
                <el-button
                  text
                  size="small"
                  :loading="likingCommentId === comment.id"
                  :class="['comment-like-btn', { 'is-liked': comment.is_liked_by_me }]"
                  @click="toggleCommentLike(post, comment)"
                >
                  {{ comment.is_liked_by_me ? '❤️' : '🤍' }} {{ comment.like_count ?? 0 }}
                </el-button>
                <el-button text size="small" @click="setReplyTarget(post.id, comment)">回复</el-button>
                <el-button v-if="isMyComment(comment)" text type="danger" size="small" :loading="deletingCommentId === comment.id" @click="removeComment(comment.id)">删除</el-button>
              </div>
            </div>
            <p>
              <template v-for="(segment, index) in parseMentionSegments(comment.content)" :key="`${comment.id}-comment-${index}`">
                <button
                  v-if="segment.type === 'mention'"
                  type="button"
                  class="author-link mention-link"
                  @click="openUserProfile(segment.userId)"
                >
                  {{ segment.label }}
                </button>
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
                    <strong><button type="button" class="author-link" @click="openUserProfile(Number(reply.user))">{{ reply.user_info?.display_name || "用户" }}</button></strong>
                  </div>
                  <span>{{ formatDateTime(reply.created_at) }}</span>
                  <div class="comment-actions">
                    <el-button
                      text
                      size="small"
                      :loading="likingCommentId === reply.id"
                      :class="['comment-like-btn', { 'is-liked': reply.is_liked_by_me }]"
                      @click="toggleCommentLike(post, reply)"
                    >
                      {{ reply.is_liked_by_me ? '❤️' : '🤍' }} {{ reply.like_count ?? 0 }}
                    </el-button>
                    <el-button text size="small" @click="setReplyTarget(post.id, reply)">回复</el-button>
                    <el-button v-if="isMyComment(reply)" text type="danger" size="small" :loading="deletingCommentId === reply.id" @click="removeComment(reply.id)">删除</el-button>
                  </div>
                </div>
                <p>
                  <template v-for="(segment, index) in parseMentionSegments(reply.content)" :key="`${reply.id}-reply-${index}`">
                    <button
                      v-if="segment.type === 'mention'"
                      type="button"
                      class="author-link mention-link"
                      @click="openUserProfile(segment.userId)"
                    >
                      {{ segment.label }}
                    </button>
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
import { ElMessageBox, notifyActionError, notifyActionSuccess, notifyLoadError, notifyWarning } from "../lib/feedback";
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

.author-link {
  border: 0;
  padding: 0;
  background: transparent;
  color: #1f4f67;
  font-weight: 700;
}

.mention-link {
  display: inline;
  margin-right: 2px;
}

.content {
  white-space: pre-wrap;
}

.post-content-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.post-content-row.has-cover {
  grid-template-columns: minmax(0, 1fr) 136px;
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

.post-secondary-actions {
  margin-top: 8px;
}

.comment-box {
  margin-top: 14px;
}

.mention-entry {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: -6px 0 12px;
}

.mention-entry-copy {
  color: #6f8592;
  font-size: 12px;
}

.mention-inline-panel {
  display: grid;
  gap: 10px;
  margin: -2px 0 12px;
  padding: 12px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.96);
  border: 1px solid rgba(16, 34, 42, 0.08);
}

.mention-inline-panel-comment {
  margin-top: 10px;
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

.avatar-hit {
  width: 100%;
  height: 100%;
  border: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
}

.avatar-hit-small {
  width: 28px;
  height: 28px;
  border-radius: 50%;
}

.comment-author {
  display: flex;
  align-items: center;
  gap: 8px;
}

.post-inline-cover {
  display: grid;
  gap: 8px;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  color: #476072;
}

.post-inline-cover img {
  width: 136px;
  height: 136px;
  object-fit: cover;
  display: block;
  border-radius: 18px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 14px 28px rgba(15, 30, 39, 0.08);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.post-inline-cover span {
  font-size: 12px;
  font-weight: 700;
  color: #1f4f67;
}

.post-inline-cover:hover img {
  transform: translateY(-1px);
  box-shadow: 0 18px 32px rgba(15, 30, 39, 0.12);
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
  margin-top: 12px;
  padding: 16px;
  border-radius: 16px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.08);
}

.linked-recipe-header {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.linked-recipe-thumb {
  width: 80px;
  height: 80px;
  border-radius: 12px;
  object-fit: cover;
  flex-shrink: 0;
  cursor: pointer;
  transition: opacity 0.15s;
}

.linked-recipe-thumb:hover {
  opacity: 0.85;
}

.linked-recipe-meta {
  flex: 1;
  min-width: 0;
}

.linked-recipe-meta strong {
  font-size: 15px;
  display: block;
  margin-bottom: 6px;
}

.linked-recipe-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 6px;
}

.recipe-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  background: rgba(16, 34, 42, 0.07);
  color: #3e6272;
}

.linked-recipe-flavor-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 6px;
}

.flavor-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  background: rgba(29, 111, 95, 0.10);
  color: #1d6f5f;
}

.linked-recipe-desc {
  margin: 4px 0 0;
  font-size: 12px;
  color: #476072;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.linked-recipe-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(16, 34, 42, 0.06);
}

.linked-recipe-section-title {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  color: #3e6272;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.ingredient-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ingredient-chip {
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  background: rgba(16, 34, 42, 0.05);
  color: #476072;
  border: 1px solid rgba(16, 34, 42, 0.07);
}

.ingredient-chip.is-main {
  background: rgba(23, 48, 66, 0.10);
  color: #173042;
  font-weight: 600;
}

.step-list {
  margin: 0;
  padding-left: 20px;
  display: grid;
  gap: 10px;
}

.step-item {
  font-size: 13px;
  color: #3a5566;
  line-height: 1.6;
}

.step-img {
  margin-top: 6px;
  max-width: 100%;
  max-height: 160px;
  border-radius: 8px;
  object-fit: cover;
  cursor: pointer;
  display: block;
}

.like-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 15px;
  padding: 4px 8px;
  transition: transform 0.15s;
}

.like-btn:active {
  transform: scale(1.2);
}

.like-heart {
  font-size: 18px;
  line-height: 1;
}

.like-count {
  font-size: 13px;
  color: #5a7a8a;
}

.comment-actions {  display: flex;
  align-items: center;
  gap: 4px;
}

.comment-like-btn {
  font-size: 13px;
  padding: 2px 6px;
}

.comment-img {
  margin-top: 8px;
  max-width: 100%;
  max-height: 200px;
  border-radius: 10px;
  object-fit: cover;
  display: block;
  cursor: pointer;
  transition: opacity 0.15s;
}

.comment-img:hover {
  opacity: 0.88;
}

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

.mention-dialog {
  display: grid;
  gap: 12px;
}

.mention-candidate-list {
  display: grid;
  gap: 10px;
}

.mention-candidate {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(247, 251, 255, 0.94);
  text-align: left;
}

.mention-candidate-copy {
  display: grid;
  gap: 4px;
}

.mention-candidate-copy strong {
  color: #173042;
}

.mention-candidate-copy span {
  color: #6f8592;
  font-size: 12px;
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

  .post-content-row.has-cover {
    grid-template-columns: 1fr;
  }

  .post-inline-cover img {
    width: min(180px, 100%);
    height: 120px;
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

  .mention-entry {
    align-items: flex-start;
    flex-direction: column;
  }
}

.comment-replies {
  margin-top: 8px;
  padding-left: 16px;
  border-left: 2px solid rgba(62, 109, 127, 0.15);
}

.reply-item {
  background: rgba(245, 250, 253, 0.7);
  border-radius: 10px;
  padding: 10px 12px;
  margin-top: 6px;
}

.reply-target-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  margin-bottom: 4px;
  background: rgba(62, 109, 127, 0.08);
  border-radius: 8px;
  font-size: 13px;
  color: #3e6d7f;
}

.user-avatar-xs {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
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
}</style>
