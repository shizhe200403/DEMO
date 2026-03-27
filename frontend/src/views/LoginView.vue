<template>
  <section class="login-layout">
    <div class="login-card">
      <p class="tag">Nutrition OS</p>
      <h2>登录系统</h2>
      <p class="desc">使用你的账号进入菜谱推荐、饮食记录和健康目标管理。</p>

      <el-form :model="form" label-position="top" class="form">
        <el-form-item label="账号">
          <el-input v-model="form.username" placeholder="请输入用户名、邮箱或手机号" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="注册时可填写邮箱" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="注册时可填写手机号" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <div class="actions">
          <el-button type="primary" :loading="loading" @click="handleLogin">登录</el-button>
          <el-button @click="handleRegister" :loading="loading" plain>注册并登录</el-button>
        </div>
      </el-form>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { register } from "../api/auth";

const router = useRouter();
const auth = useAuthStore();
const loading = ref(false);

const form = reactive({
  username: "",
  email: "",
  phone: "",
  password: "",
});

async function handleLogin() {
  loading.value = true;
  try {
    await auth.login(form.username, form.password);
    ElMessage.success("登录成功");
    router.push("/");
  } catch (error) {
    ElMessage.error("登录失败，请检查账号或密码");
  } finally {
    loading.value = false;
  }
}

async function handleRegister() {
  loading.value = true;
  try {
    await register({
      username: form.username,
      email: form.email,
      phone: form.phone,
      password: form.password,
    });
    await handleLogin();
  } catch (error) {
    ElMessage.error("注册失败，请检查输入");
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
  width: min(100%, 460px);
  padding: 32px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.82);
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

.form {
  margin-top: 22px;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.actions :deep(.el-button) {
  flex: 1;
}
</style>
