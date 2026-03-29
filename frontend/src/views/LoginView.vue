<template>
  <section class="login-layout">
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

        <div class="tips">
          <span v-if="isRegisterMode">注册后会自动登录，你可以继续完善健康资料。</span>
          <span v-else>支持使用用户名、邮箱或手机号登录。</span>
        </div>

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
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { ElMessageBox } from "element-plus";
import FormActionBar from "../components/FormActionBar.vue";
import { extractApiErrorMessage, notifyActionSuccess, notifyWarning } from "../lib/feedback";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { register } from "../api/auth";

const router = useRouter();
const auth = useAuthStore();
const loading = ref(false);
const mode = ref<"login" | "register">("login");

const form = reactive({
  account: "",
  email: "",
  phone: "",
  password: "",
  confirmPassword: "",
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
  router.push("/");
}

async function handleRegister() {
  if (!form.account || !form.password) {
    notifyWarning("请先填写用户名和密码");
    return;
  }
  if (!passwordValid.value) {
    ElMessageBox.alert("密码需同时包含字母和数字，且至少 8 位。\n例如：abc12345", "密码不符合要求", { confirmButtonText: "知道了" });
    return;
  }
  if (form.password !== form.confirmPassword) {
    ElMessageBox.alert("两次输入的密码不一致，请重新确认。", "密码不一致", { confirmButtonText: "知道了" });
    return;
  }

  await register({
    username: form.account,
    email: form.email,
    phone: form.phone,
    password: form.password,
  });
  await auth.login(form.account, form.password);
  notifyActionSuccess("注册成功");
  router.push("/");
}

async function submit() {
  loading.value = true;
  try {
    if (isRegisterMode.value) {
      await handleRegister();
      return;
    }
    await handleLogin();
  } catch (error) {
    const fallback = isRegisterMode.value ? "注册失败，请稍后重试" : "账号或密码错误，请重新输入";
    const msg = extractApiErrorMessage(error, fallback);
    ElMessageBox.alert(msg, isRegisterMode.value ? "注册失败" : "登录失败", { confirmButtonText: "知道了", type: "error" });
  } finally {
    loading.value = false;
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

.actions {
  display: flex;
  gap: 12px;
  margin-top: 14px;
}

.actions :deep(.el-button) {
  flex: 1;
}
</style>
