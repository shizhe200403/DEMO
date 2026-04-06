<template>
  <Teleport to="body">
    <Transition name="assistant-panel-float">
      <section
        v-if="open"
        class="assistant-float-panel"
        :class="{ 'assistant-float-panel-admin': isAdminRoute, 'panel-left': ballOnLeft }"
        :style="panelStyle"
      >
        <header class="assistant-float-head">
          <div class="assistant-float-head-copy">
            <span class="assistant-float-kicker">{{ isAdminRoute ? 'Admin Help Desk' : 'AI Help Desk' }}</span>
            <strong>{{ isAdminRoute ? '后台操作助手' : '随手问 AI 使用助手' }}</strong>
            <p>当前页面：{{ currentContext.label }}。优先回答现在这一步该怎么用、该点哪里、下一步做什么。</p>
          </div>
          <div class="assistant-float-head-actions">
            <button
              type="button"
              class="assistant-float-head-btn"
              :disabled="creating || streaming"
              @click="startFreshConversation"
            >
              新对话
            </button>
            <button type="button" class="assistant-float-head-btn" @click="jumpToAssistant">
              完整页
            </button>
            <button type="button" class="assistant-float-close" aria-label="关闭 AI 助手" @click="open = false">
              关
            </button>
          </div>
        </header>

        <div class="assistant-float-context">
          <div class="assistant-float-context-badge">{{ currentContext.badge }}</div>
          <p>{{ currentContext.summary }}</p>
        </div>

        <div ref="messagesRef" class="assistant-float-messages">
          <div v-if="!messages.length && !streamingContent" class="assistant-float-empty">
            <strong>从当前页面直接问。</strong>
            <p>比起泛泛聊天，更适合直接问"这个页面怎么用""我现在先点什么""如果只花 30 秒该怎么做"。</p>
            <div class="assistant-float-shortcuts">
              <button
                v-for="item in currentContext.prompts"
                :key="item.label"
                type="button"
                class="assistant-float-chip"
                :disabled="creating || streaming"
                @click="useShortcut(item.prompt)"
              >
                {{ item.label }}
              </button>
            </div>
          </div>

          <template v-else>
            <div
              v-for="msg in messages"
              :key="msg.id"
              class="assistant-float-row"
              :class="msg.role === 'user' ? 'assistant-float-row-user' : 'assistant-float-row-assistant'"
            >
              <div class="assistant-float-bubble">
                <div class="assistant-float-bubble-content" v-html="renderContent(msg.content)" />
              </div>
            </div>
            <div v-if="streamingContent" class="assistant-float-row assistant-float-row-assistant">
              <div class="assistant-float-bubble">
                <div class="assistant-float-bubble-content" v-html="renderContent(streamingContent)" />
                <span class="assistant-float-caret">▋</span>
              </div>
            </div>
          </template>
        </div>

        <div class="assistant-float-shortcuts assistant-float-shortcuts-inline" v-if="messages.length && currentContext.prompts.length">
          <button
            v-for="item in currentContext.prompts"
            :key="item.label"
            type="button"
            class="assistant-float-chip assistant-float-chip-inline"
            :disabled="creating || streaming"
            @click="useShortcut(item.prompt)"
          >
            {{ item.label }}
          </button>
        </div>

        <footer class="assistant-float-compose">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            :autosize="{ minRows: 2, maxRows: 5 }"
            resize="none"
            :disabled="creating || streaming"
            placeholder="例如：这个页面我先点哪里最合适？"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <div class="assistant-float-compose-actions">
            <p>{{ streaming ? "AI 正在结合你的账号上下文组织回答" : "回答会结合你的档案、记录和当前页面场景" }}</p>
            <el-button
              type="primary"
              :loading="creating || streaming"
              :disabled="!inputText.trim()"
              @click="sendMessage"
            >
              {{ streaming ? "回复中..." : "发送" }}
            </el-button>
          </div>
        </footer>
      </section>
    </Transition>

    <!-- Draggable floating ball -->
    <div
      ref="ballRef"
      class="assistant-float-ball"
      :class="{ open, admin: isAdminRoute, 'ball-left': ballOnLeft }"
      :style="ballStyle"
      @pointerdown="onPointerDown"
      @click="onBallClick"
    >
      <span class="assistant-float-ball-pulse" aria-hidden="true" />
      <span class="assistant-float-ball-label">小食</span>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { chatSSE, createConversation } from "../api/assistant";
import { notifyActionError } from "../lib/feedback";

type ChatMessage = {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

type AssistantContext = {
  path: string;
  label: string;
  badge: string;
  summary: string;
  prompts: Array<{ label: string; prompt: string }>;
};

const route = useRoute();
const router = useRouter();
const open = ref(false);
const currentConversationId = ref<number | null>(null);
const messages = ref<ChatMessage[]>([]);
const inputText = ref("");
const creating = ref(false);
const streaming = ref(false);
const streamingContent = ref("");
const messagesRef = ref<HTMLElement | null>(null);
const ballRef = ref<HTMLElement | null>(null);
const pendingContextReset = ref(false);

// Ball position state
const BALL_SIZE = 60; // px, matches CSS
const BALL_SIZE_MOBILE = 52;
const EDGE_MARGIN = 12; // px from screen edge

// ballOnLeft: true = left side, false = right side (default)
const ballOnLeft = ref(false);
// ballTop: vertical position in px from top (null = use CSS default)
const ballTop = ref<number | null>(null);

// Drag state
let dragging = false;
let dragMoved = false;
let startPointerX = 0;
let startPointerY = 0;
let startBallX = 0;
let startBallY = 0;
let pointerId = -1;

function isMobile() {
  return window.innerWidth <= 760;
}

function ballSize() {
  return isMobile() ? BALL_SIZE_MOBILE : BALL_SIZE;
}

function defaultBallTop() {
  return window.innerHeight - ballSize() - 90 - (isMobile() ? 14 : 26);
}

function currentBallLeft() {
  if (ballOnLeft.value) return EDGE_MARGIN;
  return window.innerWidth - ballSize() - EDGE_MARGIN;
}

function currentBallTop() {
  return ballTop.value ?? defaultBallTop();
}

const ballStyle = computed(() => {
  const top = currentBallTop();
  const left = ballOnLeft.value ? EDGE_MARGIN : undefined;
  const right = ballOnLeft.value ? undefined : EDGE_MARGIN;
  return {
    top: `${top}px`,
    ...(left !== undefined ? { left: `${left}px`, right: "auto" } : { right: `${right}px`, left: "auto" }),
    width: `${BALL_SIZE}px`,
    height: `${BALL_SIZE}px`,
  };
});

const PANEL_WIDTH = 420;
const PANEL_HEIGHT_MAX = 680;

const panelStyle = computed(() => {
  const bTop = currentBallTop();
  const bs = BALL_SIZE;
  const vp = window.innerHeight;
  const isMob = isMobile();

  if (isMob) {
    return {
      left: "14px",
      right: "14px",
      bottom: `${vp - bTop + 8}px`,
    };
  }

  // Panel height estimate
  const panelH = Math.min(PANEL_HEIGHT_MAX, vp - 80);
  // Prefer panel above the ball; if not enough space, place below
  let top: number;
  if (bTop - panelH - 8 >= 8) {
    top = bTop - panelH - 8;
  } else {
    top = Math.min(bTop + bs + 8, vp - panelH - 8);
  }

  if (ballOnLeft.value) {
    return {
      left: `${BALL_SIZE + EDGE_MARGIN + 8}px`,
      top: `${top}px`,
      width: `${PANEL_WIDTH}px`,
    };
  } else {
    return {
      right: `${BALL_SIZE + EDGE_MARGIN + 8}px`,
      top: `${top}px`,
      width: `${PANEL_WIDTH}px`,
    };
  }
});

function onPointerDown(e: PointerEvent) {
  // Only track primary pointer
  if (e.button !== 0) return;
  dragging = true;
  dragMoved = false;
  pointerId = e.pointerId;
  startPointerX = e.clientX;
  startPointerY = e.clientY;
  startBallX = currentBallLeft();
  startBallY = currentBallTop();
  (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", onPointerUp);
  e.preventDefault();
}

function onPointerMove(e: PointerEvent) {
  if (!dragging || e.pointerId !== pointerId) return;
  const dx = e.clientX - startPointerX;
  const dy = e.clientY - startPointerY;
  if (Math.abs(dx) > 4 || Math.abs(dy) > 4) {
    dragMoved = true;
  }
  if (!dragMoved) return;

  const bs = ballSize();
  const newTop = Math.max(8, Math.min(window.innerHeight - bs - 8, startBallY + dy));
  ballTop.value = newTop;

  // Update left/right based on drag position
  const newX = startBallX + dx;
  ballOnLeft.value = newX + bs / 2 < window.innerWidth / 2;
}

function onPointerUp(e: PointerEvent) {
  if (e.pointerId !== pointerId) return;
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", onPointerUp);
  dragging = false;

  // Snap to nearest edge
  const dx = e.clientX - startPointerX;
  if (dragMoved) {
    const newX = startBallX + dx;
    ballOnLeft.value = newX + ballSize() / 2 < window.innerWidth / 2;
  }
}

function onBallClick() {
  // If pointer was dragged, ignore click
  if (dragMoved) {
    dragMoved = false;
    return;
  }
  toggleWidget();
}

const contexts: AssistantContext[] = [
  {
    path: "/ops/users",
    label: "用户管理",
    badge: "Admin Users",
    summary: "适合问账号状态、角色含义、批量操作和资料字段该怎么处理。",
    prompts: [
      { label: "这个页先看什么", prompt: "我当前在用户管理页。请直接告诉我这个页面最该先看哪 3 个区域，以及分别解决什么问题。" },
      { label: "停用和角色怎么区分", prompt: "我当前在用户管理页。请用很直接的话解释账号停用、角色变更、资料修改分别适合什么场景。" },
      { label: "批量操作风险", prompt: "我当前在用户管理页。请告诉我做批量操作前最需要确认的 3 个风险点。" },
    ],
  },
  {
    path: "/ops/community",
    label: "社区审核",
    badge: "Admin Community",
    summary: "适合问审核顺序、举报处理标准和评论隐藏的使用方法。",
    prompts: [
      { label: "审核顺序", prompt: "我当前在社区审核页。请直接告诉我应该按什么顺序处理待审核帖子、举报和评论问题。" },
      { label: "举报怎么判断", prompt: "我当前在社区审核页。请告诉我处理举报时最实用的判断标准，避免泛泛而谈。" },
      { label: "先做哪一步", prompt: "我当前在社区审核页。请只告诉我现在先做哪一步最值当，以及原因。" },
    ],
  },
  {
    path: "/ops/reports",
    label: "运营复核",
    badge: "Admin Reports",
    summary: "适合问运营指标怎么看、报表任务异常怎么排查。",
    prompts: [
      { label: "报表怎么读", prompt: "我当前在运营复核页。请用最短路径告诉我这页的指标应该怎么看，先看什么，后看什么。" },
      { label: "异常先排什么", prompt: "我当前在运营复核页。请告诉我发现指标异常时第一轮排查应该看哪几类问题。" },
      { label: "今天后台主线", prompt: "我当前在运营复核页。请直接判断今天后台主线最可能是什么。" },
    ],
  },
  {
    path: "/ops",
    label: "后台总览",
    badge: "Admin Overview",
    summary: "适合问后台总览怎么判断优先级，以及该跳到哪个后台模块。",
    prompts: [
      { label: "总览先看哪块", prompt: "我当前在后台总览页。请告诉我先看哪块最能判断今天的后台优先级。" },
      { label: "下一步跳哪里", prompt: "我当前在后台总览页。请直接告诉我下一步该进哪个后台模块，为什么。" },
      { label: "如何快速值守", prompt: "我当前在后台总览页。请把值守动作压缩成一个 3 步流程。" },
    ],
  },
  {
    path: "/records",
    label: "饮食记录",
    badge: "Records Flow",
    summary: "适合问这一餐怎么记、先保存还是先补齐、最快完成路径是什么。",
    prompts: [
      { label: "先点哪里", prompt: "我当前在饮食记录页。请直接告诉我这个页面现在先点哪里最合适，以及为什么。" },
      { label: "30 秒怎么记完", prompt: "我当前在饮食记录页。请告诉我如果只花 30 秒，怎么最快完成这一餐记录。" },
      { label: "这餐该怎么补", prompt: "我当前在饮食记录页。请帮我判断这餐记录最值得先补的字段是什么。" },
    ],
  },
  {
    path: "/recipes",
    label: "菜谱库",
    badge: "Recipe Library",
    summary: "适合问怎么选菜谱、怎么录菜谱、哪些字段最重要。",
    prompts: [
      { label: "怎么挑菜谱", prompt: "我当前在菜谱页。请告诉我用这个页面挑下一餐时最省事的做法。" },
      { label: "上传先填什么", prompt: "我当前在菜谱页。请直接告诉我录入新菜谱时最先要补的字段。" },
      { label: "适合我的路线", prompt: "我当前在菜谱页。请根据健康管理场景，告诉我应该优先找什么类型的菜谱。" },
    ],
  },
  {
    path: "/reports",
    label: "健康报表",
    badge: "Review Board",
    summary: "适合问报表怎么读、复盘重点是什么、下周先改什么。",
    prompts: [
      { label: "报表怎么看", prompt: "我当前在报表页。请直接告诉我这类报表应该先看哪个结论，再看哪些细节。" },
      { label: "下周先改什么", prompt: "我当前在报表页。请告诉我如果下周只改一件事，优先改什么。" },
      { label: "复盘重点", prompt: "我当前在报表页。请帮我概括这类复盘最值得抓的 3 个重点。" },
    ],
  },
  {
    path: "/goals",
    label: "目标管理",
    badge: "Goal Tuning",
    summary: "适合问目标怎么设、什么时候该暂停或调整。",
    prompts: [
      { label: "目标怎么设", prompt: "我当前在目标页。请告诉我设目标时最容易犯的错误，以及更稳妥的做法。" },
      { label: "何时该调整", prompt: "我当前在目标页。请直接告诉我什么情况下应该调整目标，而不是硬扛。" },
      { label: "目标和今天怎么连", prompt: "我当前在目标页。请说明阶段目标应该怎样影响我今天的操作。" },
    ],
  },
  {
    path: "/community",
    label: "社区",
    badge: "Community",
    summary: "适合问社区怎么发、怎么互动、怎么举报不合适内容。",
    prompts: [
      { label: "社区怎么用", prompt: "我当前在社区页。请直接告诉我这个页面最常见的 3 个操作怎么用。" },
      { label: "举报怎么做", prompt: "我当前在社区页。请告诉我看到不合适内容时该怎么处理最合适。" },
      { label: "适合发什么", prompt: "我当前在社区页。请告诉我这里更适合发哪类内容，避免跑偏。" },
    ],
  },
  {
    path: "/profile",
    label: "个人档案",
    badge: "Profile",
    summary: "适合问哪些档案信息最重要，怎么让推荐更准确。",
    prompts: [
      { label: "哪些信息最重要", prompt: "我当前在个人档案页。请告诉我哪些资料最值得优先补齐，以及为什么。" },
      { label: "推荐如何更准", prompt: "我当前在个人档案页。请直接告诉我怎么补资料，才能让系统建议更准。" },
      { label: "容易漏什么", prompt: "我当前在个人档案页。请列出用户最容易漏填但很关键的字段。" },
    ],
  },
  {
    path: "/favorites",
    label: "收藏",
    badge: "Quick Return",
    summary: "适合问怎么把收藏变成更快的执行路径。",
    prompts: [
      { label: "收藏怎么快速用", prompt: "我当前在收藏页。请告诉我怎样把收藏真正变成更快的执行路径。" },
      { label: "下一餐怎么选", prompt: "我当前在收藏页。请直接告诉我怎么从收藏里更快选出下一餐。" },
      { label: "收藏要不要清理", prompt: "我当前在收藏页。请告诉我哪些收藏值得保留，哪些应该清理。" },
    ],
  },
  {
    path: "/assistant",
    label: "AI 助手页",
    badge: "Assistant",
    summary: "这里更适合做完整对话，悬浮窗则适合当前页面的快速求助。",
    prompts: [
      { label: "怎么提问更有效", prompt: "我当前在 AI 助手页。请告诉我怎样提问最容易得到直接、可执行的回答。" },
      { label: "什么时候用悬浮窗", prompt: "我当前在 AI 助手页。请解释悬浮助手和完整助手页分别适合什么场景。" },
    ],
  },
  {
    path: "/",
    label: "首页",
    badge: "Today Workbench",
    summary: "适合问今天下一步该做什么、先看哪里、应该跳去哪个页面。",
    prompts: [
      { label: "今天下一步", prompt: "我当前在首页。请直接告诉我今天下一步最该做什么，以及为什么。" },
      { label: "先看哪个模块", prompt: "我当前在首页。请告诉我首页里先看哪个模块最有价值。" },
      { label: "应该去哪个页面", prompt: "我当前在首页。请直接判断我现在最该去哪个页面继续操作。" },
    ],
  },
];

const isAdminRoute = computed(() => route.path.startsWith("/ops"));

const currentContext = computed(() => {
  const matched = [...contexts].sort((a, b) => b.path.length - a.path.length).find((item) => route.path.startsWith(item.path));
  return matched ?? contexts[contexts.length - 1];
});

// Derive page_context key for backend from route path
const pageContext = computed(() => {
  const p = route.path;
  if (p.startsWith("/ops/users")) return "ops:users";
  if (p.startsWith("/ops/community")) return "ops:community";
  if (p.startsWith("/ops/reports")) return "ops:reports";
  if (p.startsWith("/ops/logs")) return "ops:logs";
  if (p.startsWith("/ops/recipes")) return "ops:recipes";
  if (p.startsWith("/ops")) return "ops";
  return "";
});
const routeContextKey = computed(() => pageContext.value || currentContext.value.path);

watch(
  () => route.fullPath,
  () => {
    nextTick(() => scrollToBottom());
  },
);

watch(routeContextKey, (nextValue, previousValue) => {
  if (!previousValue || nextValue === previousValue) {
    return;
  }
  if (streaming.value) {
    pendingContextReset.value = true;
    return;
  }
  resetConversationState();
});

onMounted(() => {
  document.addEventListener("keydown", handleEscape);
  window.addEventListener("resize", onResize);
});

onBeforeUnmount(() => {
  document.removeEventListener("keydown", handleEscape);
  window.removeEventListener("resize", onResize);
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", onPointerUp);
});

function onResize() {
  // Clamp ballTop so ball stays in viewport after resize
  if (ballTop.value !== null) {
    const bs = ballSize();
    ballTop.value = Math.max(8, Math.min(window.innerHeight - bs - 8, ballTop.value));
  }
}

function handleEscape(event: KeyboardEvent) {
  if (event.key === "Escape" && open.value) {
    open.value = false;
  }
}

function toggleWidget() {
  open.value = !open.value;
  if (open.value) {
    nextTick(() => scrollToBottom());
  }
}

function jumpToAssistant() {
  open.value = false;
  if (pageContext.value) {
    router.push({
      path: "/assistant",
      query: {
        page_context: pageContext.value,
      },
    });
    return;
  }
  router.push("/assistant");
}

function renderContent(text: string) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");
}

function scrollToBottom() {
  if (!messagesRef.value) {
    return;
  }
  messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
}

function resetConversationState() {
  currentConversationId.value = null;
  messages.value = [];
  streamingContent.value = "";
  inputText.value = "";
}

function applyPendingContextReset() {
  if (!pendingContextReset.value) {
    return;
  }
  pendingContextReset.value = false;
  resetConversationState();
}

async function ensureConversation() {
  if (currentConversationId.value) {
    return currentConversationId.value;
  }

  creating.value = true;
  try {
    const response = await createConversation();
    currentConversationId.value = response.data?.id ?? null;
    return currentConversationId.value;
  } catch {
    notifyActionError("创建 AI 对话");
    return null;
  } finally {
    creating.value = false;
  }
}

function finishStreaming() {
  if (!streamingContent.value) {
    streaming.value = false;
    return;
  }

  messages.value.push({
    id: Date.now() + 1,
    role: "assistant",
    content: streamingContent.value,
    created_at: new Date().toISOString(),
  });
  streamingContent.value = "";
  streaming.value = false;
  applyPendingContextReset();
  nextTick(() => scrollToBottom());
}

function sendPrompt(prompt: string) {
  if (!currentConversationId.value || streaming.value) {
    return;
  }

  const content = prompt.trim();
  if (!content) {
    return;
  }

  messages.value.push({
    id: Date.now(),
    role: "user",
    content,
    created_at: new Date().toISOString(),
  });
  streaming.value = true;
  streamingContent.value = "";
  nextTick(() => scrollToBottom());

  chatSSE(
    currentConversationId.value,
    content,
    (chunk) => {
      streamingContent.value += chunk;
      nextTick(() => scrollToBottom());
    },
    () => {
      finishStreaming();
    },
    (error) => {
      streamingContent.value = "";
      streaming.value = false;
      applyPendingContextReset();
      notifyActionError(error || "AI 助手");
    },
    pageContext.value,
  );
}

async function sendMessage() {
  const content = inputText.value.trim();
  if (!content || creating.value || streaming.value) {
    return;
  }

  const conversationId = await ensureConversation();
  if (!conversationId) {
    return;
  }

  inputText.value = "";
  sendPrompt(content);
}

async function useShortcut(prompt: string) {
  if (creating.value || streaming.value) {
    return;
  }

  open.value = true;
  const conversationId = await ensureConversation();
  if (!conversationId) {
    return;
  }
  sendPrompt(prompt);
}

async function startFreshConversation() {
  if (creating.value || streaming.value) {
    return;
  }

  pendingContextReset.value = false;
  resetConversationState();
  await ensureConversation();
}
</script>

<style scoped>
/* ── Floating ball ──────────────────────────────────────────────── */
.assistant-float-ball {
  position: fixed;
  right: 12px;
  bottom: calc(90px + env(safe-area-inset-bottom));
  z-index: 2400;
  border-radius: 50%;
  cursor: grab;
  user-select: none;
  touch-action: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background:
    linear-gradient(135deg, rgba(19, 59, 76, 0.96), rgba(26, 97, 117, 0.96)),
    linear-gradient(135deg, rgba(255, 184, 108, 0.3), transparent);
  color: #f7fcff;
  box-shadow:
    0 14px 36px rgba(10, 30, 40, 0.32),
    inset 0 1px 0 rgba(255, 255, 255, 0.18);
  transition: box-shadow 0.18s ease, transform 0.18s ease;
}

.assistant-float-ball.admin {
  background:
    linear-gradient(135deg, rgba(196, 117, 42, 0.96), rgba(238, 165, 83, 0.96)),
    linear-gradient(135deg, rgba(255, 255, 255, 0.12), transparent);
  color: #1f160d;
}

.assistant-float-ball:hover {
  transform: scale(1.06);
  box-shadow:
    0 18px 40px rgba(10, 30, 40, 0.36),
    inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

.assistant-float-ball:active {
  cursor: grabbing;
}

.assistant-float-ball.open {
  box-shadow:
    0 8px 20px rgba(10, 30, 40, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

.assistant-float-ball-pulse {
  position: absolute;
  inset: -7px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(116, 223, 226, 0.22), transparent 70%);
  pointer-events: none;
  animation: assistant-pulse 2.8s ease-in-out infinite;
}

.assistant-float-ball.admin .assistant-float-ball-pulse {
  background: radial-gradient(circle, rgba(255, 200, 130, 0.22), transparent 70%);
}

.assistant-float-ball-label {
  position: relative;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.04em;
  line-height: 1;
}

/* ── Panel ──────────────────────────────────────────────────────── */
.assistant-float-panel {
  position: fixed;
  right: calc(60px + 12px + 8px);
  z-index: 2390;
  width: min(420px, calc(100vw - 24px));
  max-height: min(680px, calc(100vh - 80px));
  display: grid;
  grid-template-rows: auto auto 1fr auto auto;
  overflow: hidden;
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(107, 214, 217, 0.16), transparent 30%),
    linear-gradient(180deg, rgba(251, 254, 255, 0.98), rgba(239, 247, 251, 0.98));
  border: 1px solid rgba(16, 34, 42, 0.1);
  box-shadow:
    0 28px 64px rgba(15, 30, 39, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px);
}

.assistant-float-panel.panel-left {
  right: auto;
  left: calc(60px + 12px + 8px);
}

.assistant-float-panel-admin {
  background:
    radial-gradient(circle at top right, rgba(255, 193, 112, 0.2), transparent 30%),
    linear-gradient(180deg, rgba(27, 39, 51, 0.98), rgba(18, 28, 37, 0.98));
  border-color: rgba(255, 211, 163, 0.16);
  color: #edf7ff;
}

.assistant-float-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 18px 18px 14px;
}

.assistant-float-head-copy {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.assistant-float-kicker {
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #4e7d8b;
}

.assistant-float-panel-admin .assistant-float-kicker {
  color: rgba(255, 213, 167, 0.74);
}

.assistant-float-head-copy strong {
  font-size: 20px;
  line-height: 1.1;
}

.assistant-float-head-copy p,
.assistant-float-context p,
.assistant-float-empty p,
.assistant-float-compose-actions p {
  margin: 0;
  line-height: 1.6;
  color: #4b6674;
}

.assistant-float-panel-admin .assistant-float-head-copy p,
.assistant-float-panel-admin .assistant-float-context p,
.assistant-float-panel-admin .assistant-float-empty p,
.assistant-float-panel-admin .assistant-float-compose-actions p {
  color: rgba(214, 228, 237, 0.78);
}

.assistant-float-head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
}

.assistant-float-head-btn,
.assistant-float-close,
.assistant-float-chip {
  border: 0;
  transition: transform var(--app-ease), background var(--app-ease), color var(--app-ease), box-shadow var(--app-ease);
}

.assistant-float-head-btn,
.assistant-float-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(23, 48, 66, 0.08);
  color: #173042;
  font-weight: 700;
}

.assistant-float-close {
  width: 36px;
  padding: 0;
}

.assistant-float-panel-admin .assistant-float-head-btn,
.assistant-float-panel-admin .assistant-float-close {
  background: rgba(255, 255, 255, 0.08);
  color: #fff3e4;
}

.assistant-float-head-btn:hover,
.assistant-float-close:hover,
.assistant-float-chip:hover {
  transform: translateY(-1px);
}

.assistant-float-context {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 18px 14px;
  border-bottom: 1px solid rgba(16, 34, 42, 0.08);
}

.assistant-float-panel-admin .assistant-float-context {
  border-color: rgba(255, 255, 255, 0.08);
}

.assistant-float-context-badge {
  min-width: 92px;
  padding: 8px 12px;
  background: rgba(23, 48, 66, 0.08);
  color: #173042;
  font-size: 11px;
  border-radius: 999px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.assistant-float-panel-admin .assistant-float-context-badge {
  background: rgba(255, 208, 150, 0.12);
  color: #fff0dc;
}

.assistant-float-messages {
  min-height: 0;
  overflow-y: auto;
  padding: 16px 18px 8px;
}

.assistant-float-empty {
  display: grid;
  gap: 10px;
  padding: 18px;
  border-radius: 24px;
  background:
    linear-gradient(135deg, rgba(17, 53, 66, 0.92), rgba(25, 88, 103, 0.9)),
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.16), transparent 40%);
  color: #f6fcff;
  box-shadow: 0 18px 32px rgba(15, 30, 39, 0.16);
}

.assistant-float-panel-admin .assistant-float-empty {
  background:
    linear-gradient(135deg, rgba(102, 61, 24, 0.94), rgba(148, 84, 31, 0.92)),
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.14), transparent 40%);
}

.assistant-float-empty strong {
  font-size: 18px;
}

.assistant-float-empty p {
  color: rgba(239, 248, 252, 0.78);
}

.assistant-float-shortcuts {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.assistant-float-shortcuts-inline {
  padding: 0 18px 14px;
}

.assistant-float-chip {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: #173042;
  font-weight: 700;
  box-shadow: 0 10px 22px rgba(15, 30, 39, 0.08);
  cursor: pointer;
}

.assistant-float-chip-inline {
  background: rgba(23, 48, 66, 0.07);
  box-shadow: none;
}

.assistant-float-panel-admin .assistant-float-chip {
  background: rgba(255, 244, 230, 0.94);
  color: #523011;
}

.assistant-float-panel-admin .assistant-float-chip-inline {
  background: rgba(255, 255, 255, 0.08);
  color: #fff0dc;
}

.assistant-float-row {
  display: flex;
  margin-bottom: 12px;
}

.assistant-float-row-user {
  justify-content: flex-end;
}

.assistant-float-row-assistant {
  justify-content: flex-start;
}

.assistant-float-bubble {
  max-width: min(86%, 320px);
  padding: 14px 16px;
  border-radius: 20px;
  box-shadow: 0 14px 28px rgba(15, 30, 39, 0.08);
}

.assistant-float-row-user .assistant-float-bubble {
  background: linear-gradient(135deg, #173042, #24586d);
  color: #f5fbff;
  border-bottom-right-radius: 8px;
}

.assistant-float-row-assistant .assistant-float-bubble {
  background: rgba(255, 255, 255, 0.92);
  color: #173042;
  border: 1px solid rgba(16, 34, 42, 0.08);
  border-bottom-left-radius: 8px;
}

.assistant-float-panel-admin .assistant-float-row-assistant .assistant-float-bubble {
  background: rgba(255, 250, 245, 0.92);
  color: #43280f;
  border-color: rgba(255, 210, 167, 0.18);
}

.assistant-float-bubble-content {
  line-height: 1.7;
  word-break: break-word;
}

.assistant-float-caret {
  display: inline-block;
  margin-top: 4px;
  opacity: 0.72;
  animation: assistant-caret 0.95s step-end infinite;
}

.assistant-float-compose {
  display: grid;
  gap: 10px;
  padding: 0 18px 18px;
}

.assistant-float-compose-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.assistant-float-compose-actions p {
  font-size: 12px;
}

.assistant-panel-float-enter-active,
.assistant-panel-float-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.assistant-panel-float-enter-from,
.assistant-panel-float-leave-to {
  opacity: 0;
  transform: scale(0.96);
}

@keyframes assistant-pulse {
  0%,
  100% {
    transform: scale(0.96);
    opacity: 0.5;
  }
  50% {
    transform: scale(1.06);
    opacity: 0.92;
  }
}

@keyframes assistant-caret {
  0%,
  100% {
    opacity: 0.2;
  }
  50% {
    opacity: 0.88;
  }
}

@media (max-width: 760px) {
  .assistant-float-ball {
    width: 52px !important;
    height: 52px !important;
  }

  .assistant-float-ball-label {
    font-size: 13px;
  }

  .assistant-float-panel {
    left: 14px !important;
    right: 14px !important;
    width: auto !important;
    max-height: min(72vh, 640px);
    border-radius: 24px;
  }

  .assistant-float-panel.panel-left {
    left: 14px !important;
    right: 14px !important;
  }

  .assistant-float-head,
  .assistant-float-context,
  .assistant-float-compose-actions {
    flex-direction: column;
    align-items: flex-start;
  }

  .assistant-float-head-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .assistant-float-head-btn {
    flex: 1 1 0;
  }

  .assistant-float-close {
    margin-left: auto;
  }

  .assistant-float-compose-actions .el-button {
    width: 100%;
  }

  .assistant-float-bubble {
    max-width: 92%;
  }
}
</style>
