<template>
  <section class="page public-user-page">
    <CollectionSkeleton v-if="loading && !profileData" variant="dashboard" :card-count="4" />
    <RefreshFrame v-else :active="loading && !!profileData" label="正在加载用户主页">
      <template v-if="profileData">
        <div class="head">
          <div>
            <p class="tag">Community Profile</p>
            <h2>{{ displayName }}</h2>
            <p class="desc">{{ profileData.account.signature || "这个人还没有留下个性签名。" }}</p>
          </div>
          <div class="head-actions">
            <el-button type="primary" plain @click="openCommunityPosts">看 TA 的帖子</el-button>
            <el-button plain @click="router.push('/community')">回社区</el-button>
            <el-button @click="loadProfile">刷新主页</el-button>
          </div>
        </div>

        <div class="profile-hero">
          <article class="profile-card profile-identity">
            <div class="profile-avatar">
              <img v-if="profileData.account.avatar_url" :src="profileData.account.avatar_url" alt="" />
              <span v-else>{{ displayName.charAt(0).toUpperCase() }}</span>
            </div>
            <div class="profile-copy">
              <span>@{{ profileData.account.username }}</span>
              <strong>{{ displayName }}</strong>
              <p>{{ profileData.account.signature || "这个人更喜欢用内容说话。" }}</p>
            </div>
          </article>

          <div class="summary-grid">
            <article>
              <span>公开帖子</span>
              <strong>{{ profileData.stats.published_posts }}</strong>
            </article>
            <article>
              <span>可见评论</span>
              <strong>{{ profileData.stats.comment_count }}</strong>
            </article>
            <article>
              <span>加入时间</span>
              <strong>{{ formatDate(profileData.stats.member_since) }}</strong>
            </article>
            <article>
              <span>饮食风格</span>
              <strong>{{ dietTypeLabel(profileData.account.profile?.diet_type) }}</strong>
            </article>
          </div>
        </div>

        <div class="grid">
          <div class="card">
            <div class="card-head">
              <div>
                <h3>公开信息</h3>
                <p>这里只展示适合社区互动的公开资料，不会泄露联系方式和健康隐私。</p>
              </div>
            </div>
            <div class="public-info-list">
              <article>
                <span>职业</span>
                <strong>{{ profileData.account.profile?.occupation || "未公开" }}</strong>
              </article>
              <article>
                <span>烹饪熟练度</span>
                <strong>{{ cookingSkillLabel(profileData.account.profile?.cooking_skill) }}</strong>
              </article>
              <article>
                <span>餐次偏好</span>
                <strong>{{ mealPreferenceLabel(profileData.account.profile?.meal_preference) }}</strong>
              </article>
            </div>
          </div>

          <div class="card">
            <div class="card-head">
              <div>
                <h3>最近公开帖子</h3>
                <p>快速看看这个人在社区里最近沉淀了什么内容。</p>
              </div>
            </div>
            <div v-if="profileData.recent_posts.length" class="public-post-list">
              <article v-for="post in profileData.recent_posts" :key="post.id" class="public-post-card">
                <div class="public-post-copy">
                  <strong>{{ post.title }}</strong>
                  <p>{{ post.content }}</p>
                </div>
                <button
                  v-if="post.cover_image_url"
                  type="button"
                  class="public-post-cover"
                  @click="lightboxUrl = post.cover_image_url"
                >
                  <img :src="post.cover_image_url" :alt="post.title" loading="lazy" />
                </button>
                <div class="public-post-meta">
                  <span>{{ formatDateTime(post.created_at) }}</span>
                  <span>{{ post.comment_count }} 条评论</span>
                </div>
              </article>
            </div>
            <PageStateBlock
              v-else
              tone="empty"
              title="这个人还没有公开帖子"
              description="等他在社区里发布内容后，这里就会展示最近的沉淀。"
              compact
            />
          </div>
        </div>

        <div class="grid">
          <div class="card">
            <div class="card-head">
              <div>
                <h3>公开收藏菜谱</h3>
                <p>看看 TA 平时更愿意沉淀和反复使用哪些选择。</p>
              </div>
            </div>
            <div v-if="profileData.public_favorites?.length" class="favorite-public-list">
              <article v-for="recipe in profileData.public_favorites" :key="recipe.id" class="favorite-public-card">
                <img v-if="recipe.cover_image_url" :src="recipe.cover_image_url" class="favorite-public-cover" alt="" />
                <div class="favorite-public-copy">
                  <strong>{{ recipe.title }}</strong>
                  <p>{{ mealTypeLabel(recipe.meal_type) }}<span v-if="recipe.protein != null"> · {{ Number(recipe.protein).toFixed(0) }} g 蛋白</span></p>
                </div>
              </article>
            </div>
            <PageStateBlock
              v-else
              tone="empty"
              title="TA 还没有公开收藏菜谱"
              description="等他沉淀出公开可用的常用菜谱后，这里就会出现。"
              compact
            />
          </div>

          <div class="card">
            <div class="card-head">
              <div>
                <h3>最近常发餐次</h3>
                <p>根据公开帖子里关联菜谱的餐次分布，快速判断 TA 最近更常分享什么。</p>
              </div>
            </div>
            <div v-if="profileData.recent_meal_types?.length" class="meal-type-list">
              <article v-for="item in profileData.recent_meal_types" :key="item.meal_type" class="meal-type-card">
                <span>{{ mealTypeLabel(item.meal_type) }}</span>
                <strong>{{ item.count }} 次</strong>
              </article>
            </div>
            <PageStateBlock
              v-else
              tone="empty"
              title="最近还看不出明确餐次偏好"
              description="等 TA 分享更多带菜谱的内容后，这里会更像一张稳定的偏好画像。"
              compact
            />
          </div>
        </div>
      </template>
      <PageStateBlock
        v-else
        tone="empty"
        title="没有找到这个用户的公开主页"
        description="可能账号不存在，或者当前没有可展示的公开资料。"
        action-label="回社区"
        @action="router.push('/community')"
      />
    </RefreshFrame>

    <Teleport to="body">
      <div v-if="lightboxUrl" class="lightbox" @click="lightboxUrl = ''">
        <img :src="lightboxUrl" class="lightbox-img" @click.stop />
        <button class="lightbox-close" @click="lightboxUrl = ''">✕</button>
      </div>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { getPublicUserProfile } from "../api/auth";
import { notifyLoadError } from "../lib/feedback";

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const profileData = ref<any | null>(null);
const lightboxUrl = ref("");

const userId = computed(() => Number(route.params.userId || 0));
const displayName = computed(() => {
  return profileData.value?.account?.nickname || profileData.value?.account?.username || "用户";
});

function dietTypeLabel(value?: string) {
  return (
    {
      balanced: "均衡饮食",
      high_protein: "高蛋白",
      low_carb: "低碳水",
      vegetarian: "素食",
      low_fat: "低脂",
    }[value || ""] || "未公开"
  );
}

function cookingSkillLabel(value?: string) {
  return (
    {
      beginner: "新手",
      intermediate: "家常熟练",
      advanced: "熟练",
    }[value || ""] || "未公开"
  );
}

function mealPreferenceLabel(value?: string) {
  return (
    {
      light_home: "家常清淡",
      high_protein: "高蛋白优先",
      low_fat: "低脂控能量",
      fast_easy: "省时方便",
    }[value || ""] || "未公开"
  );
}

function mealTypeLabel(value?: string) {
  return (
    {
      breakfast: "早餐",
      lunch: "午餐",
      dinner: "晚餐",
      snack: "加餐",
    }[value || ""] || "未公开"
  );
}

function formatDate(value?: string) {
  if (!value) return "未公开";
  return value.slice(0, 10);
}

function formatDateTime(value?: string) {
  if (!value) return "刚刚";
  return value.replace("T", " ").slice(0, 16);
}

async function loadProfile() {
  if (!userId.value) {
    profileData.value = null;
    return;
  }
  loading.value = true;
  try {
    const response = await getPublicUserProfile(userId.value);
    profileData.value = response.data ?? null;
  } catch {
    profileData.value = null;
    notifyLoadError("用户主页");
  } finally {
    loading.value = false;
  }
}

function openCommunityPosts() {
  if (!profileData.value?.account?.id) {
    return;
  }
  router.push({ path: "/community", query: { authorId: String(profileData.value.account.id) } });
}

onMounted(loadProfile);
</script>

<style scoped>
.public-user-page {
  display: grid;
  gap: 16px;
}

.profile-hero,
.public-info-list,
.public-post-list,
.favorite-public-list,
.meal-type-list {
  display: grid;
  gap: 14px;
}

.profile-hero {
  grid-template-columns: minmax(280px, 0.72fr) minmax(0, 1.28fr);
}

.profile-card,
.public-info-list article,
.public-post-card,
.favorite-public-card,
.meal-type-card {
  padding: 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 42px rgba(15, 30, 39, 0.08);
}

.profile-identity {
  display: grid;
  gap: 16px;
  align-content: start;
}

.profile-avatar {
  width: 92px;
  height: 92px;
  border-radius: 999px;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #d0e8f5;
  color: #2d6a8a;
  font-size: 32px;
  font-weight: 800;
}

.profile-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-copy {
  display: grid;
  gap: 6px;
}

.profile-copy span,
.public-info-list span,
.public-post-meta span {
  color: #5a7a8a;
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.profile-copy strong,
.public-info-list strong,
.public-post-copy strong {
  color: #173042;
}

.profile-copy strong {
  font-size: 28px;
}

.profile-copy p,
.public-post-copy p {
  margin: 0;
  color: #476072;
  line-height: 1.65;
}

.public-info-list {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.public-info-list article {
  display: grid;
  gap: 8px;
}

.public-post-card {
  display: grid;
  gap: 12px;
}

.public-post-copy {
  display: grid;
  gap: 8px;
}

.public-post-cover {
  width: 156px;
  height: 156px;
  padding: 0;
  border: 0;
  background: transparent;
}

.public-post-cover img {
  width: 100%;
  height: 100%;
  border-radius: 18px;
  object-fit: cover;
  border: 1px solid rgba(16, 34, 42, 0.08);
}

.public-post-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.favorite-public-card {
  display: flex;
  gap: 14px;
  align-items: center;
}

.favorite-public-cover {
  width: 76px;
  height: 76px;
  border-radius: 14px;
  object-fit: cover;
  border: 1px solid rgba(16, 34, 42, 0.08);
}

.favorite-public-copy {
  display: grid;
  gap: 6px;
}

.favorite-public-copy p {
  margin: 0;
  color: #476072;
  line-height: 1.5;
}

.meal-type-list {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.meal-type-card {
  display: grid;
  gap: 8px;
}

.meal-type-card span {
  color: #5a7a8a;
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.meal-type-card strong {
  color: #173042;
  font-size: 20px;
}

.lightbox {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.88);
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-img {
  max-width: 92vw;
  max-height: 92vh;
  border-radius: 8px;
  object-fit: contain;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.5);
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
}

@media (max-width: 960px) {
  .profile-hero,
  .public-info-list,
  .meal-type-list {
    grid-template-columns: 1fr;
  }
}
</style>
