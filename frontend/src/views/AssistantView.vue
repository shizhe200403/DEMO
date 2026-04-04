<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">AI Assistant</p>
        <h2>AI 营养助手</h2>
        <p class="desc">有什么吃的困惑，或者不知道今天该怎么补，直接问我就好。</p>
      </div>
      <el-button @click="startNewConversation" :loading="creating">新建对话</el-button>
    </div>

    <div class="chat-layout">
      <!-- 对话列表 -->
      <aside class="sidebar">
        <div class="sidebar-head">
          <strong>历史对话</strong>
        </div>
        <div class="conv-list">
          <div
            v-for="conv in conversations"
            :key="conv.id"
            class="conv-item"
            :class="{ active: currentConvId === conv.id }"
            @click="selectConversation(conv)"
          >
            <span class="conv-title">{{ conv.title }}</span>
            <el-button
              text
              type="danger"
              size="small"
              class="conv-delete"
              :loading="deletingId === conv.id"
              @click.stop="removeConversation(conv.id)"
            >删</el-button>
          </div>
          <div v-if="!conversations.length" class="conv-empty">暂无对话记录</div>
        </div>
      </aside>

      <!-- 聊天区域 -->
      <div class="chat-area">
        <div v-if="!currentConvId" class="chat-placeholder">
          <div class="placeholder-inner">
            <p class="placeholder-icon">🥗</p>
            <strong>先从一个具体任务开始</strong>
            <p>比起空白聊天，更推荐直接从“今天下一步、这餐怎么记、菜谱怎么补、这周怎么复盘”这些真实任务进入。</p>
            <div class="task-starter-grid">
              <button
                v-for="task in starterTasks"
                :key="task.key"
                type="button"
                class="task-starter-card"
                @click="launchTaskPrompt(task.source, task.prompt)"
              >
                <span>{{ task.badge }}</span>
                <strong>{{ task.title }}</strong>
                <p>{{ task.description }}</p>
              </button>
            </div>
            <div class="placeholder-actions">
              <el-button type="primary" @click="startNewConversation" :loading="creating">新建空白对话</el-button>
            </div>
          </div>
        </div>

        <template v-else>
          <div v-if="activeTaskContext" class="task-banner">
            <span>{{ activeTaskContext.badge }}</span>
            <strong>{{ activeTaskContext.title }}</strong>
            <p>{{ activeTaskContext.description }}</p>
          </div>
          <div v-if="taskFollowUpActions.length" class="task-follow-up-row">
            <el-button
              v-for="item in taskFollowUpActions"
              :key="item.label"
              plain
              size="small"
              :disabled="streaming"
              @click="sendTaskFollowUp(item.prompt)"
            >
              {{ item.label }}
            </el-button>
          </div>
          <div class="messages" ref="messagesEl">
            <div v-if="loadingMessages" class="msg-loading">加载中...</div>
            <template v-else>
              <div
                v-for="msg in messages"
                :key="msg.id"
                class="msg-row"
                :class="msg.role === 'user' ? 'msg-user' : 'msg-assistant'"
              >
                <div class="bubble">
                  <div class="bubble-content" v-html="renderContent(msg.content)"></div>
                </div>
              </div>
              <!-- 流式输出中的消息 -->
              <div v-if="streamingContent" class="msg-row msg-assistant">
                <div class="bubble">
                  <div class="bubble-content" v-html="renderContent(streamingContent)"></div>
                  <span class="typing-dot">▋</span>
                </div>
              </div>
            </template>
          </div>

          <div class="input-area">
            <div v-if="!auth.isPro && auth.aiUsageRemaining !== null" class="quota-bar">
              本月剩余免费对话：<strong>{{ auth.aiUsageRemaining }} 次</strong>
              <router-link to="/pricing" class="quota-upgrade">升级 Pro →</router-link>
            </div>
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="2"
              :autosize="{ minRows: 2, maxRows: 5 }"
              placeholder="输入你的问题，例如：我最近蛋白质摄入够吗？"
              :disabled="streaming"
              @keydown.enter.exact.prevent="sendMessage"
            />
            <el-button
              type="primary"
              :loading="streaming"
              :disabled="!inputText.trim()"
              @click="sendMessage"
            >{{ streaming ? '回复中...' : '发送' }}</el-button>
          </div>
        </template>
      </div>
    </div>
  </section>

  <el-dialog v-model="quotaExceededVisible" title="本月免费次数已用尽" width="420px" :close-on-click-modal="false">
    <p>免费版每月 <strong>30 次</strong> AI 对话，本月已全部使用。</p>
    <p style="margin-top: 8px; color: #5a7a8a; font-size: 14px;">升级 Pro 版后享受无限 AI 对话、PDF 报表导出、Pro 专属菜谱等全部高级功能。</p>
    <template #footer>
      <el-button @click="quotaExceededVisible = false">下月再用</el-button>
      <el-button type="primary" @click="() => { quotaExceededVisible = false; router.push('/pricing'); }">了解 Pro 版</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { chatSSE, createConversation, deleteConversation, getConversation, listConversations } from "../api/assistant";
import { notifyActionError, notifyActionSuccess } from "../lib/feedback";
import { useAuthStore } from "../stores/auth";
import { ElMessageBox } from "element-plus";

interface Conversation { id: number; title: string; created_at: string; updated_at: string }
interface Message { id: number; role: string; content: string; created_at: string }
type AssistantTask = {
  key: string;
  source: string;
  badge: string;
  title: string;
  description: string;
  prompt: string;
};

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const quotaExceededVisible = ref(false);
const conversations = ref<Conversation[]>([]);
const currentConvId = ref<number | null>(null);
const messages = ref<Message[]>([]);
const inputText = ref("");
const streaming = ref(false);
const streamingContent = ref("");
const creating = ref(false);
const deletingId = ref<number | null>(null);
const loadingMessages = ref(false);
const messagesEl = ref<HTMLElement | null>(null);
const autoLaunching = ref(false);
const handledPromptToken = ref("");
const taskConversationId = ref<number | null>(null);
const activeTaskSource = ref("");
const activeTaskContext = ref<null | { badge: string; title: string; description: string }>(null);
const starterTasks = computed<AssistantTask[]>(() => [
  {
    key: "home",
    source: "home_today_workbench",
    badge: "首页任务",
    title: "解释今天下一步",
    description: "适合先判断今天还差什么、下一餐该怎么补。",
    prompt: [
      "请基于我的饮食系统当前状态，用非常直接、可执行的话告诉我今天下一步怎么做。",
      "请输出三部分：1）一句话结论；2）为什么；3）我现在最该点哪个页面里的哪个动作。",
    ].join("\n"),
  },
  {
    key: "record",
    source: "records_next_step",
    badge: "记录任务",
    title: "帮我判断先记什么",
    description: "适合还没决定该补哪一餐、是复制还是新记的时候。",
    prompt: [
      "请帮我判断记录页里下一步最该做什么。",
      "请输出三部分：1）优先动作；2）最省事做法；3）如果只花 30 秒，应该怎么完成。",
    ].join("\n"),
  },
  {
    key: "recipe",
    source: "recipes_creator_draft",
    badge: "菜谱任务",
    title: "帮我补全菜谱草稿",
    description: "适合已经有菜名或食材，但不确定描述和录入粒度的时候。",
    prompt: [
      "请帮我补全一份即将上传到饮食系统的菜谱草稿。",
      "请输出三部分：1）这道菜适合什么场景；2）最值得补齐的字段；3）给我一版可直接粘贴的描述文案。",
    ].join("\n"),
  },
  {
    key: "report",
    source: "reports_review_explain",
    badge: "报表任务",
    title: "解释这周复盘重点",
    description: "适合快速看清这周最大问题、保留习惯和下周动作。",
    prompt: [
      "请基于我的饮食复盘场景，用直接、可执行的语言解释这次阶段复盘。",
      "请输出三部分：1）最大问题；2）值得保留；3）下周只改一件事先改什么。",
    ].join("\n"),
  },
]);
const taskFollowUpActions = computed(() => {
  return {
    home_today_workbench: [
      { label: "给我一句结论", prompt: "把刚才的建议压缩成一句最短、最明确的结论。" },
      { label: "拆成 3 步", prompt: "把刚才的建议拆成 3 个最容易执行的步骤。" },
      { label: "最省事版本", prompt: "如果我现在只想用最省事的方式完成今天下一步，具体怎么做？" },
    ],
    records_next_step: [
      { label: "先点哪个", prompt: "直接告诉我现在先点哪个按钮、为什么。" },
      { label: "30 秒完成", prompt: "如果我只想 30 秒内完成这一条记录，怎么做最快？" },
      { label: "还差多少", prompt: "基于当前记录思路，再告诉我今天最可能还差什么。" },
    ],
    records_meal_draft: [
      { label: "先保存还是先补", prompt: "直接告诉我这条记录应该先保存，还是先补成正式菜谱。" },
      { label: "缺什么信息", prompt: "只告诉我这条记录最缺的 3 个信息字段。" },
      { label: "生成可填备注", prompt: "按当前草稿，帮我生成一版更清楚的备注文案。" },
    ],
    recipes_creator_draft: [
      { label: "补描述", prompt: "基于当前草稿，给我一版可直接粘贴到描述栏的成品文案。" },
      { label: "补字段优先级", prompt: "只告诉我当前最值得先补的 3 个字段，以及原因。" },
      { label: "适合什么场景", prompt: "直接判断这道菜更适合什么场景和什么目标。" },
    ],
    reports_review_explain: [
      { label: "一句话结论", prompt: "把这次复盘压缩成一句最重要的结论。" },
      { label: "下周只改一件事", prompt: "如果下周只改一件事，优先改什么，为什么？" },
      { label: "保留哪些习惯", prompt: "只列出这次复盘里最值得保留的习惯和原因。" },
    ],
  }[activeTaskSource.value] || [];
});

function renderContent(text: string) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
    }
  });
}

async function loadConversations() {
  try {
    const res = await listConversations();
    conversations.value = res.data ?? [];
  } catch {
    // silent
  }
}

async function selectConversation(conv: Conversation) {
  currentConvId.value = conv.id;
  if (taskConversationId.value !== conv.id) {
    activeTaskSource.value = "";
    activeTaskContext.value = null;
  } else if (activeTaskSource.value) {
    activeTaskContext.value = taskContextFromSource(activeTaskSource.value);
  }
  loadingMessages.value = true;
  try {
    const res = await getConversation(conv.id);
    messages.value = (res.data?.messages ?? []).filter((m: Message) => m.role !== "system");
    scrollToBottom();
  } catch {
    notifyActionError("加载对话");
  } finally {
    loadingMessages.value = false;
  }
}

async function startNewConversation() {
  creating.value = true;
  try {
    const res = await createConversation();
    const conv = res.data;
    conversations.value = [conv, ...conversations.value];
    currentConvId.value = conv.id;
    messages.value = [];
    taskConversationId.value = null;
    activeTaskSource.value = "";
    activeTaskContext.value = null;
  } catch {
    notifyActionError("创建对话");
  } finally {
    creating.value = false;
  }
}

async function removeConversation(id: number) {
  try {
    await ElMessageBox.confirm("确认删除这条对话记录？", "删除对话", { type: "warning", confirmButtonText: "删除", cancelButtonText: "取消" });
  } catch { return; }
  try {
    deletingId.value = id;
    await deleteConversation(id);
    conversations.value = conversations.value.filter((c) => c.id !== id);
    if (currentConvId.value === id) {
      currentConvId.value = null;
      messages.value = [];
      taskConversationId.value = null;
      activeTaskSource.value = "";
      activeTaskContext.value = null;
    }
    notifyActionSuccess("对话已删除");
  } catch {
    notifyActionError("删除对话");
  } finally {
    deletingId.value = null;
  }
}

async function ensureConversation(forceNew = false) {
  if (currentConvId.value && !forceNew) {
    return currentConvId.value;
  }
  creating.value = true;
  try {
    const res = await createConversation();
    const conv = res.data;
    conversations.value = [conv, ...conversations.value];
    currentConvId.value = conv.id;
    messages.value = [];
    return conv.id;
  } finally {
    creating.value = false;
  }
}

function taskContextFromSource(source: string) {
  return {
    home_today_workbench: {
      badge: "首页任务",
      title: "今天工作台解释",
      description: "这次对话是从首页带进来的，目标是尽快回答“我今天下一步最该做什么”。",
    },
    reports_review_explain: {
      badge: "报表任务",
      title: "阶段复盘解释",
      description: "这次对话聚焦报表页的复盘结论，优先讲清问题、保留项和下周动作。",
    },
    records_next_step: {
      badge: "记录任务",
      title: "下一餐执行建议",
      description: "这次对话来自记录页，重点不是泛泛聊天，而是帮你尽快决定现在该记哪一餐、怎么记最省事。",
    },
    records_meal_draft: {
      badge: "记录任务",
      title: "当前这餐怎么补全",
      description: "这次对话聚焦你手头这条记录草稿，优先判断是先保存、补菜谱，还是补齐关键信息。",
    },
    recipes_creator_draft: {
      badge: "菜谱任务",
      title: "菜谱草稿补全",
      description: "这次对话来自菜谱上传弹窗，重点是帮你把当前草稿补到更适合收藏、记录和复用的状态。",
    },
  }[source] || {
    badge: "任务对话",
    title: "当前任务协助",
    description: "这次对话是从具体页面动作带进来的，回答会优先围绕当前任务，而不是泛泛展开。",
  };
}

function sendPrompt(text: string) {
  const prompt = text.trim();
  if (!prompt || !currentConvId.value || streaming.value) {
    return;
  }

  messages.value.push({ id: Date.now(), role: "user", content: prompt, created_at: new Date().toISOString() });
  scrollToBottom();

  streaming.value = true;
  streamingContent.value = "";

  chatSSE(
    currentConvId.value,
    prompt,
    (chunk) => {
      streamingContent.value += chunk;
      scrollToBottom();
    },
    () => {
      messages.value.push({ id: Date.now() + 1, role: "assistant", content: streamingContent.value, created_at: new Date().toISOString() });
      streamingContent.value = "";
      streaming.value = false;
      // 从服务器同步真实配额计数（避免乐观递增与服务器不一致）
      if (auth.user && auth.user.plan === "free") {
        auth.fetchMe().catch(() => {});
      }
      loadConversations();
      scrollToBottom();
    },
    (err) => {
      streamingContent.value = "";
      streaming.value = false;
      // 移除乐观插入的用户消息
      messages.value = messages.value.filter((m) => m.role !== "user" || m.content !== prompt);
      if (err === "QUOTA_EXCEEDED") {
        quotaExceededVisible.value = true;
      } else {
        notifyActionError(err || "AI 助手");
      }
    },
  );
}

function sendTaskFollowUp(prompt: string) {
  if (!prompt || !currentConvId.value || streaming.value) {
    return;
  }
  sendPrompt(prompt);
}

async function sendMessage() {
  const text = inputText.value.trim();
  if (!text || streaming.value) return;
  if (!currentConvId.value) {
    await ensureConversation();
  }
  inputText.value = "";
  sendPrompt(text);
}

async function launchTaskPrompt(source: string, prompt: string, consumeRoute = false) {
  const token = `${source}::${prompt}`;
  if (!prompt || handledPromptToken.value === token || autoLaunching.value || streaming.value) {
    return;
  }

  autoLaunching.value = true;
  handledPromptToken.value = token;
  try {
    const convId = await ensureConversation(true);
    taskConversationId.value = convId;
    activeTaskSource.value = source;
    activeTaskContext.value = taskContextFromSource(source);
    sendPrompt(prompt);
    if (consumeRoute) {
      const nextQuery = { ...route.query };
      delete nextQuery.prompt;
      delete nextQuery.source;
      router.replace({ path: route.path, query: nextQuery });
    }
  } catch {
    handledPromptToken.value = "";
    notifyActionError("初始化任务对话");
  } finally {
    autoLaunching.value = false;
  }
}

async function launchPromptFromRoute() {
  const prompt = String(route.query.prompt || "").trim();
  const source = String(route.query.source || "").trim();
  await launchTaskPrompt(source, prompt, true);
}

onMounted(async () => {
  await loadConversations();
  await launchPromptFromRoute();
});

watch(
  () => route.fullPath,
  () => {
    launchPromptFromRoute();
  },
);
</script>

<style scoped>
.page {
  display: grid;
  gap: 16px;
  min-height: calc(100dvh - 140px);
  grid-template-rows: auto 1fr;
}

.head {
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

h2 { margin: 0; font-size: 30px; }

.desc {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.65;
}

.chat-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 14px;
  min-height: 0;
}

/* Sidebar */
.sidebar {
  display: flex;
  flex-direction: column;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 8px 30px rgba(15, 30, 39, 0.06);
  overflow: hidden;
}

.sidebar-head {
  padding: 14px 16px 10px;
  font-size: 13px;
  color: #476072;
  border-bottom: 1px solid rgba(16, 34, 42, 0.06);
}

.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.conv-item:hover { background: rgba(16, 34, 42, 0.05); }
.conv-item.active { background: rgba(29, 111, 95, 0.1); }

.conv-title {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-delete { opacity: 0; transition: opacity 0.15s; flex-shrink: 0; }
.conv-item:hover .conv-delete { opacity: 1; }

.conv-empty {
  padding: 20px 12px;
  font-size: 13px;
  color: #8a9faa;
  text-align: center;
}

/* Chat area */
.chat-area {
  display: flex;
  flex-direction: column;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 8px 30px rgba(15, 30, 39, 0.06);
  overflow: hidden;
  min-height: 0;
}

.task-banner {
  display: grid;
  gap: 8px;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(16, 34, 42, 0.06);
  background:
    radial-gradient(circle at top right, rgba(87, 181, 231, 0.14), transparent 35%),
    rgba(247, 251, 255, 0.9);
}

.task-banner span {
  justify-self: flex-start;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(23, 48, 66, 0.08);
  color: #173042;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.task-banner strong {
  font-size: 18px;
  color: #173042;
}

.task-banner p {
  margin: 0;
  color: #476072;
  line-height: 1.65;
}

.chat-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-inner {
  width: min(760px, 100%);
  padding: 32px;
}

.placeholder-icon { font-size: 48px; margin: 0 0 16px; text-align: center; }
.placeholder-inner strong { display: block; font-size: 18px; margin-bottom: 10px; text-align: center; }
.placeholder-inner p { color: #476072; line-height: 1.65; margin: 0 0 20px; text-align: center; }

.task-starter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.task-starter-card {
  display: grid;
  gap: 8px;
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(247, 251, 255, 0.88);
  text-align: left;
  cursor: pointer;
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.task-starter-card:hover {
  transform: translateY(-1px);
  border-color: rgba(23, 48, 66, 0.16);
  box-shadow: 0 12px 24px rgba(15, 30, 39, 0.08);
}

.task-starter-card span {
  justify-self: flex-start;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(23, 48, 66, 0.08);
  color: #173042;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.task-starter-card strong,
.task-starter-card p {
  margin: 0;
  text-align: left;
}

.task-starter-card strong {
  font-size: 16px;
  color: #173042;
}

.task-starter-card p {
  color: #476072;
  line-height: 1.65;
}

.placeholder-actions {
  display: flex;
  justify-content: center;
  margin-top: 18px;
}

.task-follow-up-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px 16px 0;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 0;
}

.msg-loading {
  text-align: center;
  color: #8a9faa;
  font-size: 13px;
  padding: 20px;
}

.msg-row { display: flex; }
.msg-user { justify-content: flex-end; }
.msg-assistant { justify-content: flex-start; }

.bubble {
  max-width: 72%;
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.7;
  position: relative;
}

.msg-user .bubble {
  background: #173042;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.msg-assistant .bubble {
  background: #f0f6fa;
  color: #10202c;
  border-bottom-left-radius: 4px;
}

.bubble-content { word-break: break-word; }

.typing-dot {
  display: inline-block;
  animation: blink 0.8s step-end infinite;
  color: #3e6d7f;
  margin-left: 2px;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.input-area {
  display: flex;
  gap: 10px;
  padding: 14px 16px;
  border-top: 1px solid rgba(16, 34, 42, 0.06);
  align-items: flex-end;
}

.input-area :deep(.el-textarea) { flex: 1; }

@media (max-width: 768px) {
  .page {
    min-height: auto;
    grid-template-rows: auto;
  }

  .head,
  .input-area {
    flex-direction: column;
    align-items: stretch;
  }

  h2 {
    font-size: 22px;
  }

  .chat-layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    max-height: 200px;
    border-radius: 16px;
  }

  .chat-area {
    min-height: calc(100dvh - 280px);
    border-radius: 16px;
  }

  .messages {
    padding: 14px;
    gap: 10px;
  }

  .placeholder-inner {
    padding: 24px 16px;
  }

  .task-starter-grid {
    grid-template-columns: 1fr;
  }

  .placeholder-actions,
  .task-follow-up-row {
    justify-content: stretch;
  }

  .task-follow-up-row :deep(.el-button) {
    width: 100%;
    margin-left: 0;
  }

  .bubble {
    max-width: 92%;
    padding: 10px 12px;
  }

  .input-area {
    padding: 12px;
  }
}

.quota-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  margin-bottom: 8px;
  background: rgba(62, 109, 127, 0.06);
  border-radius: 8px;
  font-size: 13px;
  color: #476072;
}

.quota-upgrade {
  margin-left: auto;
  color: #3e6d7f;
  font-weight: 600;
  text-decoration: none;
  font-size: 13px;
}

.quota-upgrade:hover {
  text-decoration: underline;
}
</style>
