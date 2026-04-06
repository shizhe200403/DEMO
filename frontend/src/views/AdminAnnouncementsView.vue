<template>
  <section class="page admin-announcements">
    <div class="head">
      <div>
        <p class="tag">Announcement Center</p>
        <h2>公告中心</h2>
      </div>
      <div class="head-actions">
        <CompactHint tone="accent" title="发布公告" description="这里负责向全站普通用户推送系统公告。标题要短，正文要明确，跳转入口要真实可达。" />
        <el-button plain @click="loadAnnouncements">刷新公告</el-button>
        <RouterLink class="ghost-link" to="/ops">回后台总览</RouterLink>
      </div>
    </div>

    <PageStateBlock
      v-if="auth.isAuthenticated && !auth.user"
      tone="loading"
      title="正在确认管理员身份"
      description="稍等一下，正在确认当前账号权限。"
      compact
    />
    <PageStateBlock
      v-else-if="!isManagerUser"
      tone="error"
      title="当前账号没有发布公告权限"
      description="公告中心只对 manager 级后台账号开放。"
      action-label="回到首页"
      @action="router.push('/')"
    />
    <template v-else>
      <CollectionSkeleton v-if="loading && !announcements.length" variant="list" :card-count="4" />
      <RefreshFrame v-else :active="loading" label="正在同步公告中心">
        <div class="summary-grid">
          <article v-spotlight>
            <span>已发布公告</span>
            <strong>{{ announcements.length }}</strong>
            <p>这里只看最近 30 条公告。</p>
          </article>
          <article v-spotlight>
            <span>累计触达</span>
            <strong>{{ totalNotificationCount }}</strong>
            <p>所有已发布公告合计写入的站内提醒数。</p>
          </article>
          <article v-spotlight>
            <span>最近一条</span>
            <strong>{{ latestAnnouncementTitle }}</strong>
            <p>确认最近发布的是不是你想让用户先看到的内容。</p>
          </article>
        </div>

        <div class="admin-grid">
          <article class="card console-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>发布新公告</h3>
                <p>建议公告只讲一件事：发生了什么、用户该怎么做、需要去哪一步继续。</p>
              </div>
            </div>

            <el-form label-position="top" class="drawer-form">
              <el-form-item label="公告标题">
                <el-input v-model.trim="draft.title" maxlength="120" show-word-limit placeholder="例如：系统维护通知" />
              </el-form-item>
              <el-form-item label="公告正文">
                <el-input
                  v-model.trim="draft.body"
                  type="textarea"
                  :rows="5"
                  maxlength="255"
                  show-word-limit
                  placeholder="例如：今晚 23:00 到 23:30 将进行短时维护，期间部分报表生成会延迟。"
                />
              </el-form-item>
              <el-form-item label="点击跳转路径（可选）">
                <el-input v-model.trim="draft.link_path" placeholder="例如：/reports 或 /community" />
              </el-form-item>
              <FormActionBar
                compact
                :tone="submitDisabled ? 'warning' : 'ready'"
                :title="submitDisabled ? '先补齐标题和正文' : '公告内容已完整，可以立即发布'"
                :description="draft.link_path ? '用户点开提醒后会直接跳到这个站内页面。' : '如果不填跳转路径，用户点开后只会标记已读，不会跳转页面。'"
                primary-label="发布公告"
                :disabled="submitDisabled"
                :loading="publishing"
                @primary="publishAnnouncement"
              />
            </el-form>
          </article>

          <article class="card console-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>最近公告</h3>
                <p>重点看标题是否清晰、触达人数是否合理，以及跳转页面是不是指向正确。</p>
              </div>
            </div>

            <div v-if="announcements.length" class="announcement-list">
              <article v-for="item in announcements" :key="item.id" class="announcement-item">
                <div class="announcement-head">
                  <div>
                    <strong>{{ item.title }}</strong>
                    <span>{{ formatDateTime(item.published_at) }} · {{ item.created_by?.display_name || item.created_by?.username || "管理员" }}</span>
                  </div>
                  <el-tag type="success" effect="light">已发布</el-tag>
                </div>
                <p>{{ item.body }}</p>
                <div class="announcement-meta">
                  <span>触达 {{ item.notification_count }} 人</span>
                  <span>{{ item.link_path ? `跳转：${item.link_path}` : "无跳转路径" }}</span>
                </div>
              </article>
            </div>
            <PageStateBlock
              v-else
              tone="empty"
              title="还没有发布过公告"
              description="发布第一条系统公告后，这里会开始沉淀历史记录。"
              compact
            />
          </article>
        </div>
      </RefreshFrame>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { RouterLink } from "vue-router";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import CompactHint from "../components/CompactHint.vue";
import FormActionBar from "../components/FormActionBar.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { createAdminAnnouncement, listAdminAnnouncements, type AdminAnnouncementItem } from "../api/adminAnnouncements";
import { extractApiErrorMessage, notifyActionSuccess, notifyErrorMessage, notifyLoadError } from "../lib/feedback";
import { isOpsManager } from "../lib/opsAccess";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const loading = ref(false);
const publishing = ref(false);
const announcements = ref<AdminAnnouncementItem[]>([]);

const draft = reactive({
  title: "",
  body: "",
  link_path: "",
});

const isManagerUser = computed(() => isOpsManager(auth.user));
const submitDisabled = computed(() => !draft.title.trim() || !draft.body.trim());
const totalNotificationCount = computed(() => announcements.value.reduce((sum, item) => sum + Number(item.notification_count || 0), 0));
const latestAnnouncementTitle = computed(() => announcements.value[0]?.title || "暂无");

onMounted(() => {
  if (isManagerUser.value) {
    void loadAnnouncements();
  }
});

async function loadAnnouncements() {
  if (!isManagerUser.value) return;
  loading.value = true;
  try {
    const response = await listAdminAnnouncements();
    announcements.value = response.data?.items ?? [];
  } catch {
    notifyLoadError("公告中心");
  } finally {
    loading.value = false;
  }
}

function resetDraft() {
  draft.title = "";
  draft.body = "";
  draft.link_path = "";
}

async function publishAnnouncement() {
  if (submitDisabled.value) {
    notifyErrorMessage("请先填写公告标题和正文");
    return;
  }

  publishing.value = true;
  try {
    await createAdminAnnouncement({
      title: draft.title.trim(),
      body: draft.body.trim(),
      link_path: draft.link_path.trim(),
    });
    notifyActionSuccess("公告已发布并写入站内提醒");
    resetDraft();
    await loadAnnouncements();
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "发布公告失败"));
  } finally {
    publishing.value = false;
  }
}

function formatDateTime(value?: string) {
  if (!value) return "刚刚";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "刚刚";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
</script>

<style scoped>
.admin-announcements {
  display: grid;
  gap: 18px;
}

.announcement-list {
  display: grid;
  gap: 12px;
}

.announcement-item {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(247, 251, 255, 0.92);
}

.announcement-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.announcement-head strong {
  display: block;
  color: #173042;
}

.announcement-head span,
.announcement-meta span {
  color: #5a7a8a;
  font-size: 12px;
}

.announcement-item p {
  margin: 10px 0 0;
  color: #476072;
  line-height: 1.7;
}

.announcement-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 10px;
}

@media (max-width: 768px) {
  .announcement-head {
    flex-direction: column;
  }
}
</style>
