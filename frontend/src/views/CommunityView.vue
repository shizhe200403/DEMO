<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Community</p>
        <h2>社区分享</h2>
      </div>
      <el-button @click="loadPosts">刷新</el-button>
    </div>

    <div class="card">
      <h3>发布帖子</h3>
      <el-form :model="form" label-position="top">
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-button type="primary" @click="submitPost">发布</el-button>
      </el-form>
    </div>

    <div class="list">
      <article v-for="post in posts" :key="post.id">
        <div class="row">
          <strong>{{ post.title }}</strong>
          <span>{{ post.created_at }}</span>
        </div>
        <p>{{ post.content }}</p>
        <div class="comment-box">
          <el-input v-model="commentDrafts[post.id]" placeholder="写评论" />
          <el-button @click="submitComment(post.id)">评论</el-button>
          <el-button plain @click="report(post.id)">举报</el-button>
        </div>
        <div class="comments" v-if="post.comments?.length">
          <div v-for="comment in post.comments" :key="comment.id">
            {{ comment.content }}
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { createComment, createPost, listPosts, reportPost } from "../api/community";
import { trackEvent } from "../api/behavior";

const posts = ref<any[]>([]);
const commentDrafts = reactive<Record<number, string>>({});
const form = reactive({
  title: "",
  content: "",
});

async function loadPosts() {
  try {
    const response = await listPosts();
    posts.value = response.data?.results ?? response.data?.data?.items ?? response.data?.data ?? [];
    trackEvent({ behavior_type: "view", context_scene: "community" }).catch(() => undefined);
  } catch (error) {
    ElMessage.error("加载社区失败");
  }
}

async function submitPost() {
  try {
    await createPost(form);
    form.title = "";
    form.content = "";
    ElMessage.success("发布成功");
    await loadPosts();
  } catch (error) {
    ElMessage.error("发布失败");
  }
}

async function submitComment(postId: number) {
  try {
    const content = commentDrafts[postId];
    if (!content) return;
    await createComment(postId, { content });
    commentDrafts[postId] = "";
    ElMessage.success("评论成功");
    await loadPosts();
  } catch (error) {
    ElMessage.error("评论失败");
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
    ElMessage.success("已提交举报");
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("举报失败");
    }
  }
}

onMounted(loadPosts);
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

.card,
.list article {
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.list {
  display: grid;
  gap: 14px;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.row strong {
  font-size: 18px;
}

.row span {
  font-size: 12px;
  color: #5a7a8a;
}

.comment-box {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.comments {
  margin-top: 12px;
  display: grid;
  gap: 8px;
  color: #476072;
}
</style>
