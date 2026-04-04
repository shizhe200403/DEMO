<template>
  <section class="login-layout" @keyup.enter="submit">
    <div class="login-card">
      <p class="tag">每日饮食</p>
      <h2>{{ isRegisterMode ? "创建你的饮食管理账号" : "欢迎回来" }}</h2>
      <p class="desc">
        {{ isRegisterMode ? "完成注册后即可开始记录饮食、保存个人资料并查看趋势。" : "登录后继续查看今日进度、记录三餐并获取饮食建议。" }}
      </p>

      <div class="mode-switch" role="tablist" aria-label="登录模式切换">
        <button :class="{ active: !isRegisterMode }" @click="switchMode('login')">登录</button>
        <button :class="{ active: isRegisterMode }" @click="switchMode('register')">注册</button>
      </div>

      <el-form :model="form" label-position="top" class="form">
        <el-form-item :label="isRegisterMode ? '用户名' : '账号'">
          <el-input
            v-model.trim="form.account"
            :placeholder="isRegisterMode ? '用于登录和个人展示，例如：shizhe01' : '请输入用户名、邮箱或手机号'"
          />
        </el-form-item>

        <template v-if="isRegisterMode">
          <el-form-item label="邮箱">
            <el-input v-model.trim="form.email" placeholder="用于接收通知，可选" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model.trim="form.phone" placeholder="用于联系或后续验证码登录，可选" />
          </el-form-item>
        </template>

        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>

        <el-form-item v-if="isRegisterMode" label="确认密码">
          <el-input v-model="form.confirmPassword" type="password" show-password placeholder="请再次输入密码" />
          <div class="password-rules">
            <span :class="ruleClass(passwordRules.length)">✓ 至少 8 位</span>
            <span :class="ruleClass(passwordRules.hasLetter)">✓ 包含字母</span>
            <span :class="ruleClass(passwordRules.hasNumber)">✓ 包含数字</span>
            <span :class="ruleClass(passwordRules.match)">✓ 两次一致</span>
          </div>
        </el-form-item>

        <template v-if="isRegisterMode">
          <el-form-item label="密保问题（可选，用于找回密码）">
            <el-select v-model="form.securityQuestion" clearable placeholder="选择一个密保问题" style="width: 100%">
              <el-option v-for="q in securityQuestions" :key="q" :label="q" :value="q" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="form.securityQuestion" label="密保答案">
            <el-input v-model.trim="form.securityAnswer" placeholder="答案不区分大小写" />
          </el-form-item>
        </template>

        <div class="tips">
          <span v-if="isRegisterMode">注册后会自动登录，你可以继续完善健康资料。</span>
          <span v-else>支持使用用户名、邮箱或手机号登录。</span>
          <button v-if="!isRegisterMode" class="forgot-btn" type="button" @click="openForgot">忘记密码？</button>
        </div>

        <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>

        <FormActionBar
          compact
          :tone="loading ? 'saving' : submitTone"
          :title="submitTitle"
          :description="submitDescription"
          :primary-label="isRegisterMode ? '注册并进入系统' : '登录系统'"
          :disabled="submitDisabled"
          :loading="loading"
          @primary="submit"
        />
      </el-form>
    </div>

    <!-- 忘记密码弹窗 -->
    <el-dialog v-model="forgotVisible" title="找回密码" width="420px" :close-on-click-modal="false" @close="resetForgot" append-to-body>
      <!-- Step 1: 输入账号 -->
      <div v-if="forgotStep === 1" class="forgot-step">
        <p class="forgot-desc">输入你的账号（用户名、邮箱或手机号），系统将显示你设置的密保问题。</p>
        <el-form label-position="top">
          <el-form-item label="账号">
            <el-input v-model.trim="forgotForm.account" placeholder="用户名 / 邮箱 / 手机号" @keyup.enter="fetchSecurityQuestion" />
          </el-form-item>
          <div v-if="forgotError" class="forgot-error">{{ forgotError }}</div>
        </el-form>
        <div class="forgot-actions">
          <el-button @click="forgotVisible = false">取消</el-button>
          <el-button type="primary" :loading="forgotLoading" :disabled="!forgotForm.account" @click="fetchSecurityQuestion">下一步</el-button>
        </div>
      </div>

      <!-- Step 2: 回答密保问题 -->
      <div v-if="forgotStep === 2" class="forgot-step">
        <p class="forgot-desc">请回答你设置的密保问题，答案不区分大小写。</p>
        <el-form label-position="top">
          <el-form-item label="密保问题">
            <el-input :model-value="forgotForm.question" disabled />
          </el-form-item>
          <el-form-item label="密保答案">
            <el-input v-model.trim="forgotForm.answer" placeholder="请输入密保答案" @keyup.enter="verifyAndNext" />
          </el-form-item>
          <div v-if="forgotError" class="forgot-error">{{ forgotError }}</div>
        </el-form>
        <div class="forgot-actions">
          <el-button @click="forgotStep = 1">上一步</el-button>
          <el-button type="primary" :loading="forgotLoading" :disabled="!forgotForm.answer" @click="verifyAndNext">下一步</el-button>
        </div>
      </div>

      <!-- Step 3: 设置新密码 -->
      <div v-if="forgotStep === 3" class="forgot-step">
        <p class="forgot-desc">密保验证通过，请设置你的新密码。</p>
        <el-form label-position="top">
          <el-form-item label="新密码">
            <el-input v-model="forgotForm.newPassword" type="password" show-password placeholder="至少 8 位，包含字母和数字" />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="forgotForm.confirmPassword" type="password" show-password placeholder="再次输入新密码" @keyup.enter="submitReset" />
          </el-form-item>
          <div class="password-rules">
            <span :class="forgotPwdRuleClass(forgotForm.newPassword.length >= 8)">✓ 至少 8 位</span>
            <span :class="forgotPwdRuleClass(/[a-zA-Z]/.test(forgotForm.newPassword))">✓ 包含字母</span>
            <span :class="forgotPwdRuleClass(/[0-9]/.test(forgotForm.newPassword))">✓ 包含数字</span>
            <span :class="forgotPwdRuleClass(forgotForm.newPassword.length > 0 && forgotForm.newPassword === forgotForm.confirmPassword)">✓ 两次一致</span>
          </div>
          <div v-if="forgotError" class="forgot-error">{{ forgotError }}</div>
        </el-form>
        <div class="forgot-actions">
          <el-button @click="forgotStep = 2">上一步</el-button>
          <el-button type="primary" :loading="forgotLoading" :disabled="!forgotResetValid" @click="submitReset">重置密码</el-button>
        </div>
      </div>

      <!-- Step 4: 重置成功 -->
      <div v-if="forgotStep === 4" class="forgot-step forgot-success">
        <div class="success-icon">✓</div>
        <p class="forgot-desc">密码已重置成功！请用新密码登录。</p>
        <div class="forgot-actions">
          <el-button type="primary" @click="forgotVisible = false">去登录</el-button>
        </div>
      </div>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import FormActionBar from "../components/FormActionBar.vue";
import { resolveOpsHome } from "../lib/opsAccess";
import { extractApiErrorMessage, notifyActionSuccess, notifyWarning } from "../lib/feedback";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { register, getSecurityQuestions, getSecurityQuestion, resetPasswordBySecurity } from "../api/auth";

const router = useRouter();
const auth = useAuthStore();
const loading = ref(false);
const errorMsg = ref("");
const mode = ref<"login" | "register">("login");
const securityQuestions = ref<string[]>([]);

onMounted(async () => {
  try {
    const res = await getSecurityQuestions();
    securityQuestions.value = res.data ?? [];
  } catch {
    // non-critical
  }
});

const form = reactive({
  account: "",
  email: "",
  phone: "",
  password: "",
  confirmPassword: "",
  securityQuestion: "",
  securityAnswer: "",
});

const isRegisterMode = computed(() => mode.value === "register");
const passwordRules = computed(() => ({
  length: form.password.length >= 8,
  hasLetter: /[a-zA-Z]/.test(form.password),
  hasNumber: /[0-9]/.test(form.password),
  match: form.password.length > 0 && form.password === form.confirmPassword,
}));
const passwordValid = computed(() =>
  passwordRules.value.length && passwordRules.value.hasLetter && passwordRules.value.hasNumber
);
const submitDisabled = computed(() => {
  if (!form.account || !form.password) return true;
  if (!isRegisterMode.value) return false;
  return !passwordValid.value || form.password !== form.confirmPassword;
});
const submitTone = computed(() => (submitDisabled.value ? "warning" : "ready"));
const submitTitle = computed(() => {
  if (!isRegisterMode.value) {
    return submitDisabled.value ? "先补齐账号和密码" : "信息已完整，可以登录";
  }
  if (!form.account || !form.password) return "先填写用户名和密码";
  if (!passwordValid.value) return "密码需包含字母和数字，且至少 8 位";
  if (form.password !== form.confirmPassword) return "两次密码还不一致";
  return "信息已完整，可以注册";
});
const submitDescription = computed(() => {
  return isRegisterMode.value
    ? "注册后会自动登录，并继续进入系统完善健康档案。"
    : "支持用户名、邮箱或手机号登录。";
});

function switchMode(nextMode: "login" | "register") {
  mode.value = nextMode;
  form.password = "";
  form.confirmPassword = "";
  form.securityQuestion = "";
  form.securityAnswer = "";
  errorMsg.value = "";
}

function ruleClass(passed: boolean) {
  return passed ? "rule rule-pass" : "rule rule-fail";
}

async function handleLogin() {
  if (!form.account || !form.password) {
    notifyWarning("请先填写账号和密码");
    return;
  }

  await auth.login(form.account, form.password);
  notifyActionSuccess("登录成功");
  router.push(resolveOpsHome(auth.user));
}

async function handleRegister() {
  if (!form.account || !form.password) {
    notifyWarning("请先填写用户名和密码");
    return;
  }
  if (!passwordValid.value) {
    errorMsg.value = "密码需同时包含字母和数字，且至少 8 位。例如：abc12345";
    return;
  }
  if (form.password !== form.confirmPassword) {
    errorMsg.value = "两次输入的密码不一致，请重新确认。";
    return;
  }

  await register({
    username: form.account,
    email: form.email,
    phone: form.phone,
    password: form.password,
    security_question: form.securityQuestion,
    security_answer: form.securityAnswer,
  });
  await auth.login(form.account, form.password);
  notifyActionSuccess("注册成功");
  router.push("/");
}

async function submit() {
  errorMsg.value = "";
  loading.value = true;
  try {
    if (isRegisterMode.value) {
      await handleRegister();
      return;
    }
    await handleLogin();
  } catch (error) {
    const fallback = isRegisterMode.value ? "注册失败，请稍后重试" : "账号或密码错误，请重新输入";
    errorMsg.value = extractApiErrorMessage(error, fallback);
  } finally {
    loading.value = false;
  }
}

// ---- 忘记密码 ----
const forgotVisible = ref(false);
const forgotStep = ref(1);
const forgotLoading = ref(false);
const forgotError = ref("");
const forgotForm = reactive({
  account: "",
  question: "",
  answer: "",
  newPassword: "",
  confirmPassword: "",
});
const forgotResetValid = computed(() => {
  const p = forgotForm.newPassword;
  return p.length >= 8 && /[a-zA-Z]/.test(p) && /[0-9]/.test(p) && p === forgotForm.confirmPassword;
});

function openForgot() {
  resetForgot();
  forgotVisible.value = true;
}

function resetForgot() {
  forgotStep.value = 1;
  forgotError.value = "";
  forgotForm.account = "";
  forgotForm.question = "";
  forgotForm.answer = "";
  forgotForm.newPassword = "";
  forgotForm.confirmPassword = "";
}

function forgotPwdRuleClass(passed: boolean) {
  return passed ? "rule rule-pass" : "rule rule-fail";
}

async function fetchSecurityQuestion() {
  if (!forgotForm.account) return;
  forgotError.value = "";
  forgotLoading.value = true;
  try {
    const res = await getSecurityQuestion(forgotForm.account);
    forgotForm.question = res.data.question;
    forgotStep.value = 2;
  } catch (err: any) {
    forgotError.value = extractApiErrorMessage(err, "该账号未设置密保问题，无法通过此方式找回密码");
  } finally {
    forgotLoading.value = false;
  }
}

function verifyAndNext() {
  if (!forgotForm.answer) return;
  forgotError.value = "";
  forgotStep.value = 3;
}

async function submitReset() {
  if (!forgotResetValid.value) return;
  forgotError.value = "";
  forgotLoading.value = true;
  try {
    await resetPasswordBySecurity({
      account: forgotForm.account,
      answer: forgotForm.answer,
      new_password: forgotForm.newPassword,
    });
    forgotStep.value = 4;
  } catch (err: any) {
    forgotError.value = extractApiErrorMessage(err, "密保答案不正确，请重新输入");
  } finally {
    forgotLoading.value = false;
  }
}
</script>

<style scoped>
.login-layout {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at top left, rgba(87, 181, 231, 0.22), transparent 32%),
    radial-gradient(circle at bottom right, rgba(34, 197, 94, 0.16), transparent 28%),
    linear-gradient(180deg, #f7fbff 0%, #eef4f8 100%);
  padding: 24px;
}

.login-card {
  width: min(100%, 480px);
  padding: 32px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
  backdrop-filter: blur(14px);
}

.tag {
  margin: 0 0 8px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  font-size: 12px;
  color: #3e6d7f;
}

h2 {
  margin: 0;
  font-size: 32px;
}

.desc {
  margin: 12px 0 0;
  color: #476072;
  line-height: 1.7;
}

.mode-switch {
  display: inline-grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  width: 100%;
  margin-top: 24px;
  padding: 6px;
  border-radius: 999px;
  background: #eef4f8;
}

.mode-switch button {
  border: 0;
  background: transparent;
  color: #476072;
  font-weight: 700;
  padding: 10px 12px;
  border-radius: 999px;
}

.mode-switch button.active {
  background: #173042;
  color: #fff;
}

.form {
  margin-top: 18px;
}

.tips {
  margin-top: -4px;
  color: #5a7a8a;
  font-size: 13px;
  line-height: 1.6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.forgot-btn {
  background: none;
  border: none;
  color: #2d6a8a;
  font-size: 13px;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
  text-underline-offset: 2px;
  flex-shrink: 0;
}

.forgot-btn:hover {
  color: #173042;
}

.password-rules {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.rule {
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 999px;
  transition: all 0.2s;
}

.rule-fail {
  background: #f5f5f5;
  color: #999;
}

.rule-pass {
  background: rgba(29, 111, 95, 0.12);
  color: #1d6f5f;
  font-weight: 600;
}

.error-banner {
  margin-top: 4px;
  padding: 12px 16px;
  border-radius: 12px;
  background: #fff1f0;
  border: 1px solid #ffccc7;
  color: #cf1322;
  font-size: 14px;
  font-weight: 500;
  text-align: center;
  line-height: 1.6;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 14px;
}

.actions :deep(.el-button) {
  flex: 1;
}

.forgot-step {
  display: grid;
  gap: 16px;
}

.forgot-desc {
  margin: 0;
  color: #476072;
  font-size: 14px;
  line-height: 1.65;
}

.forgot-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.forgot-error {
  padding: 10px 14px;
  border-radius: 10px;
  background: #fff1f0;
  border: 1px solid #ffccc7;
  color: #cf1322;
  font-size: 13px;
}

.forgot-success {
  text-align: center;
  padding: 16px 0;
}

.success-icon {
  font-size: 48px;
  color: #1d6f5f;
  margin-bottom: 8px;
}
</style>
