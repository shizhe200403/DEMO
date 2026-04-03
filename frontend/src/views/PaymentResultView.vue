<template>
  <section class="page">
    <div class="result-card" :class="isPaid ? 'result-success' : 'result-pending'">
      <!-- 成功状态 -->
      <template v-if="isPaid">
        <div class="result-icon success-icon">✓</div>
        <h2>升级成功！</h2>
        <p class="result-desc">欢迎加入 Pro 会员，所有 Pro 功能已立即解锁。</p>
        <div class="result-meta" v-if="planEnd">
          <span class="meta-label">有效期至</span>
          <span class="meta-value">{{ planEnd }}</span>
        </div>
        <div class="result-actions">
          <el-button type="primary" @click="router.push('/')">回到首页</el-button>
          <el-button @click="router.push('/recipes')">查看 Pro 菜谱</el-button>
        </div>
      </template>

      <!-- 处理中/查询中 -->
      <template v-else-if="loading">
        <div class="waiting-spinner"></div>
        <h2>正在确认支付状态…</h2>
        <p class="result-desc">请稍等，正在向服务器确认你的付款。</p>
      </template>

      <!-- 未付款 / 取消 -->
      <template v-else>
        <div class="result-icon pending-icon">?</div>
        <h2>支付尚未完成</h2>
        <p class="result-desc">未检测到支付成功记录。如已完成付款请点击"重新查询"，否则可返回重新发起。</p>
        <div class="result-actions">
          <el-button type="primary" :loading="checking" @click="checkNow">重新查询</el-button>
          <el-button @click="router.push('/pricing')">返回定价页</el-button>
        </div>
      </template>

      <p v-if="orderNo" class="order-no">订单号：{{ orderNo }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "../stores/auth";
import { getOrder } from "../api/payments";

const route  = useRoute();
const router = useRouter();
const auth   = useAuthStore();

// order_no 由我们自己拼入 return_url；out_trade_no 是支付宝追加的兜底字段
const orderNo  = ref((route.query.order_no as string) || (route.query.out_trade_no as string) || "");
const statusParam = (route.query.status as string) || "";
const isPaid   = ref(statusParam === "paid");
const loading  = ref(false);
const checking = ref(false);
const planEnd  = ref("");

onMounted(async () => {
  if (isPaid.value) {
    // Alipay return_url 已携带 status=paid，直接刷新用户信息
    await auth.fetchMe().catch(() => {});
    loadPlanEnd();
    return;
  }
  // 没有明确的 paid 参数时主动查询一次
  if (orderNo.value) {
    await checkNow();
  }
});

function loadPlanEnd() {
  // 从刷新后的用户订单列表里找有效期（简化：直接显示 auth 用户 plan 信息）
  // 若没有就不显示
  if (orderNo.value) {
    getOrder(orderNo.value).then((o) => {
      if (o.plan_end) {
        planEnd.value = o.plan_end.slice(0, 10);
      }
    }).catch(() => {});
  }
}

async function checkNow() {
  if (!orderNo.value) {
    ElMessage.error("未找到订单号，请返回重新发起支付");
    return;
  }
  checking.value = true;
  loading.value  = true;
  // 最多轮询 10 次，每次间隔 3s（共约 30s），等待异步 notify 到达
  for (let i = 0; i < 10; i++) {
    try {
      const order = await getOrder(orderNo.value);
      if (order.status === "paid") {
        isPaid.value = true;
        await auth.fetchMe().catch(() => {});
        loadPlanEnd();
        checking.value = false;
        loading.value  = false;
        return;
      }
    } catch {
      // 忽略单次查询错误，继续重试
    }
    if (i < 9) await new Promise((r) => setTimeout(r, 3000));
  }
  checking.value = false;
  loading.value  = false;
  ElMessage.warning("支付尚未确认，若已付款请等待片刻后再试。");
}
</script>

<style scoped>
.page {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 40px;
}

.result-card {
  width: min(520px, 100%);
  padding: 40px 36px;
  border-radius: 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  text-align: center;
  box-shadow: 0 24px 60px rgba(15,30,39,0.12);
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(16,34,42,0.08);
}

.result-success {
  border-color: rgba(62,143,122,0.3);
  background: rgba(240,252,248,0.95);
}

.result-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  font-size: 36px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.success-icon {
  background: rgba(62,143,122,0.16);
  color: #2d8a6d;
}

.pending-icon {
  background: rgba(16,34,42,0.07);
  color: #4b6674;
}

h2 { margin: 0; font-size: 26px; color: #173042; }

.result-desc { margin: 0; color: #476072; line-height: 1.7; max-width: 360px; }

.result-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 12px;
  background: rgba(62,143,122,0.1);
}

.meta-label { font-size: 13px; color: #3a7060; }
.meta-value { font-weight: 700; color: #1f5c4a; }

.result-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.order-no {
  margin: 4px 0 0;
  font-size: 12px;
  color: #9ab4be;
  font-family: monospace;
}

.waiting-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(22,119,255,0.18);
  border-top-color: #1677ff;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 600px) {
  .result-card { padding: 28px 20px; }
  h2 { font-size: 22px; }
}
</style>
