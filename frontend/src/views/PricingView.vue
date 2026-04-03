<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Pricing</p>
        <h2>选择你的套餐</h2>
        <p class="desc">免费版够用来体验，Pro 版让你的健康管理真正跑起来。</p>
      </div>
    </div>

    <div class="plans-grid">
      <!-- 免费版 -->
      <div class="plan-card">
        <div class="plan-header">
          <span class="plan-badge free">免费版</span>
          <div class="plan-price">
            <span class="price-amount">¥0</span>
            <span class="price-period">永久免费</span>
          </div>
        </div>
        <ul class="plan-features">
          <li class="feature-ok">AI 营养师对话 <strong>30 次 / 月</strong></li>
          <li class="feature-ok">个性化菜谱推荐</li>
          <li class="feature-ok">饮食记录与热量追踪</li>
          <li class="feature-ok">健康目标管理</li>
          <li class="feature-ok">周报数据看板</li>
          <li class="feature-ok">基础社区互动</li>
          <li class="feature-locked">月报（Pro 专享）</li>
          <li class="feature-locked">PDF 报表导出（Pro 专享）</li>
          <li class="feature-locked">Pro 专属菜谱（Pro 专享）</li>
        </ul>
        <div class="plan-action">
          <el-button v-if="!auth.isAuthenticated" type="default" @click="router.push('/login')">免费注册</el-button>
          <el-button v-else-if="!auth.isPro" disabled>当前套餐</el-button>
          <el-button v-else type="default" disabled>基础版</el-button>
        </div>
      </div>

      <!-- Pro 版 -->
      <div class="plan-card plan-card-pro">
        <div class="plan-badge-row">
          <span class="plan-badge pro">Pro 版</span>
          <span class="plan-recommended">推荐</span>
        </div>

        <!-- 套餐切换 -->
        <div class="billing-toggle" v-if="!auth.isPro">
          <button
            class="billing-btn"
            :class="{ active: selectedPlan === 'monthly' }"
            @click="selectedPlan = 'monthly'"
          >月付</button>
          <button
            class="billing-btn"
            :class="{ active: selectedPlan === 'annual' }"
            @click="selectedPlan = 'annual'"
          >年付 <span class="save-tag">省¥101</span></button>
        </div>

        <div class="plan-price">
          <span class="price-amount">{{ selectedPlan === 'monthly' ? '¥25' : '¥199' }}</span>
          <span class="price-period">{{ selectedPlan === 'monthly' ? '/ 月' : '/ 年' }}</span>
        </div>
        <p v-if="selectedPlan === 'monthly'" class="price-annual">或选择年付 ¥199（节省 ¥101）</p>
        <p v-else class="price-annual">相当于 ¥16.6 / 月</p>

        <ul class="plan-features">
          <li class="feature-ok"><strong>无限</strong> AI 营养师对话</li>
          <li class="feature-ok">个性化菜谱推荐</li>
          <li class="feature-ok">饮食记录与热量追踪</li>
          <li class="feature-ok">健康目标管理</li>
          <li class="feature-ok">周报 + <strong>月报</strong>数据看板</li>
          <li class="feature-ok"><strong>PDF 报表</strong>下载导出</li>
          <li class="feature-ok"><strong>Pro 专属菜谱</strong>（营养师精选）</li>
          <li class="feature-ok">社区全功能</li>
          <li class="feature-ok">优先客服支持</li>
        </ul>
        <div class="plan-action">
          <el-button v-if="auth.isPro" type="primary" disabled>当前套餐</el-button>
          <el-button
            v-else-if="auth.isAuthenticated"
            type="primary"
            :loading="paying"
            @click="startPayment"
          >
            {{ paying ? '正在跳转...' : `支付宝支付 ${selectedPlan === 'monthly' ? '¥25' : '¥199'}` }}
          </el-button>
          <el-button v-else type="primary" @click="router.push('/login')">登录后升级</el-button>
        </div>
      </div>
    </div>

    <!-- FAQ -->
    <div class="card note-card">
      <h3>常见问题</h3>
      <div class="faq-list">
        <div class="faq-item">
          <p class="faq-q">支付后多久生效？</p>
          <p class="faq-a">支付宝确认收款后立即生效，无需等待人工审核。</p>
        </div>
        <div class="faq-item">
          <p class="faq-q">支持哪些支付方式？</p>
          <p class="faq-a">目前支持支付宝扫码 / 账号支付。</p>
        </div>
        <div class="faq-item">
          <p class="faq-q">到期后会自动续费吗？</p>
          <p class="faq-a">不会自动续费，到期后恢复免费版，数据不丢失。</p>
        </div>
        <div class="faq-item">
          <p class="faq-q">可以申请退款吗？</p>
          <p class="faq-a">支付后 24 小时内未使用任何 Pro 功能可联系客服申请退款。</p>
        </div>
      </div>
    </div>

    <!-- 等待支付确认 dialog -->
    <el-dialog
      v-model="waitingVisible"
      title="等待支付确认"
      width="420px"
      :close-on-click-modal="false"
      :show-close="true"
      @close="cancelWaiting"
    >
      <div class="waiting-content">
        <div class="waiting-spinner"></div>
        <p>请在已打开的支付宝页面完成付款。</p>
        <p class="waiting-tip">完成后点击「我已付款」，系统将自动验证。</p>
        <p v-if="currentOrderNo" class="waiting-order">订单号：{{ currentOrderNo }}</p>
      </div>
      <template #footer>
        <el-button @click="cancelWaiting">取消</el-button>
        <el-button type="primary" :loading="checking" @click="checkPayment">我已付款</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "../stores/auth";
import { createOrder, getOrder } from "../api/payments";

const auth = useAuthStore();
const router = useRouter();

const selectedPlan = ref<"monthly" | "annual">("monthly");
const paying = ref(false);
const waitingVisible = ref(false);
const checking = ref(false);
const currentOrderNo = ref("");
let pollTimer: ReturnType<typeof setInterval> | null = null;

async function startPayment() {
  if (!auth.isAuthenticated) {
    router.push("/login");
    return;
  }
  if (paying.value) return;

  paying.value = true;
  try {
    const order = await createOrder(selectedPlan.value);
    currentOrderNo.value = order.order_no;
    window.open(order.pay_url, "_blank");
    waitingVisible.value = true;
    startPolling();
  } catch (e: any) {
    const msg = e?.response?.data?.message || "发起支付失败，请稍后重试";
    ElMessage.error(msg);
  } finally {
    paying.value = false;
  }
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(async () => {
    await silentCheck();
  }, 3000);
}

function stopPolling() {
  if (pollTimer !== null) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function silentCheck() {
  if (!currentOrderNo.value) return;
  try {
    const order = await getOrder(currentOrderNo.value);
    if (order.status === "paid") {
      stopPolling();
      onPaymentSuccess();
    }
  } catch {
    // 静默忽略
  }
}

async function checkPayment() {
  if (checking.value || !currentOrderNo.value) return;
  checking.value = true;
  try {
    const order = await getOrder(currentOrderNo.value);
    if (order.status === "paid") {
      stopPolling();
      onPaymentSuccess();
    } else {
      ElMessage.warning("尚未检测到支付成功，请确认已在支付宝完成付款后再试。");
    }
  } catch {
    ElMessage.error("查询订单状态失败，请稍后重试");
  } finally {
    checking.value = false;
  }
}

function onPaymentSuccess() {
  waitingVisible.value = false;
  auth.fetchMe().then(() => {
    router.push(`/payment/result?order_no=${currentOrderNo.value}&status=paid`);
  });
}

function cancelWaiting() {
  stopPolling();
  waitingVisible.value = false;
  currentOrderNo.value = "";
}
</script>

<style scoped>
.page { display: grid; gap: 24px; }
.head { display: flex; justify-content: space-between; align-items: flex-start; }
.tag { margin: 0 0 6px; letter-spacing: 0.16em; text-transform: uppercase; font-size: 12px; color: #3e6d7f; }
h2 { margin: 0; font-size: 30px; }
.desc { margin: 8px 0 0; color: #476072; line-height: 1.65; }

.plans-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

.plan-card {
  padding: 28px;
  border-radius: 24px;
  background: rgba(255,255,255,0.86);
  border: 1px solid rgba(16,34,42,0.08);
  box-shadow: 0 18px 50px rgba(15,30,39,0.08);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.plan-card-pro {
  border-color: #3e6d7f;
  background: rgba(240,248,255,0.92);
  box-shadow: 0 20px 60px rgba(62,109,127,0.15);
}

.plan-header { display: flex; flex-direction: column; gap: 10px; }
.plan-badge-row { display: flex; align-items: center; gap: 10px; }

.plan-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
}
.plan-badge.free { background: rgba(16,34,42,0.07); color: #3a5868; }
.plan-badge.pro  { background: #173042; color: #fff; }

.plan-recommended {
  font-size: 12px;
  color: #3e8f7a;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(62,143,122,0.12);
}

.billing-toggle { display: flex; gap: 8px; }
.billing-btn {
  flex: 1;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(16,34,42,0.14);
  background: rgba(255,255,255,0.7);
  color: #476072;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.billing-btn.active { background: #173042; color: #fff; border-color: #173042; }
.billing-btn:hover:not(.active) { border-color: #173042; color: #173042; }
.save-tag {
  font-size: 11px;
  background: rgba(62,143,122,0.18);
  color: #2d7a62;
  padding: 2px 6px;
  border-radius: 999px;
}
.billing-btn.active .save-tag { background: rgba(255,255,255,0.2); color: #a8e6d8; }

.plan-price { display: flex; align-items: baseline; gap: 6px; }
.price-amount { font-size: 38px; font-weight: 800; color: #173042; line-height: 1; }
.price-period { font-size: 16px; color: #4b6674; }
.price-annual { margin: -12px 0 0; font-size: 13px; color: #4b8f8a; }

.plan-features { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; flex: 1; }
.plan-features li { display: flex; align-items: center; gap: 8px; font-size: 14px; line-height: 1.5; color: #2a4857; }
.plan-features li::before {
  content: "";
  flex: 0 0 auto;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: no-repeat center/10px;
}
.feature-ok::before {
  background-color: rgba(62,143,122,0.15);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3E%3Cpath d='M2 6l3 3 5-5' stroke='%232d7a62' stroke-width='1.5' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
}
.feature-locked { color: #8fa8b4; }
.feature-locked::before {
  background-color: rgba(16,34,42,0.06);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3E%3Crect x='3' y='5.5' width='6' height='5' rx='1' stroke='%238fa8b4' stroke-width='1.2' fill='none'/%3E%3Cpath d='M4 5.5V4a2 2 0 014 0v1.5' stroke='%238fa8b4' stroke-width='1.2' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
}

.plan-action { margin-top: auto; }
.plan-action .el-button { width: 100%; }

.note-card {
  padding: 24px 28px;
  border-radius: 20px;
  background: rgba(255,255,255,0.82);
  border: 1px solid rgba(16,34,42,0.07);
}
.note-card h3 { margin: 0 0 16px; font-size: 18px; }
.faq-list { display: grid; gap: 14px; }
.faq-item { display: grid; gap: 4px; }
.faq-q { margin: 0; font-weight: 700; font-size: 14px; color: #1f3d50; }
.faq-a { margin: 0; font-size: 13px; color: #476072; line-height: 1.6; }

/* 等待弹窗 */
.waiting-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
  padding: 8px 0;
}
.waiting-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(22,119,255,0.18);
  border-top-color: #1677ff;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.waiting-tip { font-size: 13px; color: #476072; margin: 0; }
.waiting-order { font-size: 12px; color: #8fa8b4; margin: 0; font-family: monospace; }

@media (max-width: 640px) {
  .plans-grid { grid-template-columns: 1fr; }
  h2 { font-size: 24px; }
}
</style>
