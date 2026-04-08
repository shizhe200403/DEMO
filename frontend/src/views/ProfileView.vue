<template>
  <section class="profile-page">

    <!-- 顶部栏 -->
    <div class="greeting-bar">
      <div class="greeting-left">
        <h2 class="greeting-title">个人中心</h2>
        <p class="greeting-sub">档案完整度 {{ profileCompletion }}，填得越准推荐越贴心</p>
      </div>
      <div class="greeting-right">
        <el-button type="primary" :loading="saving" :disabled="profileSaveDisabled" @click="saveAll">保存全部</el-button>
      </div>
    </div>

    <!-- 双栏主体 -->
    <div class="main-layout">

      <!-- 左侧 sidebar -->
      <aside class="sidebar">

        <!-- 用户摘要卡 -->
        <div class="sidebar-card user-summary-card">
          <div class="avatar-wrap" @click="triggerAvatarUpload" title="点击更换头像">
            <img v-if="account.avatar_url" :src="account.avatar_url" class="avatar-img" alt="头像" />
            <div v-else class="avatar-placeholder">{{ avatarInitial }}</div>
            <div class="avatar-overlay">更换</div>
          </div>
          <input ref="avatarInput" type="file" accept="image/*" style="display:none" @change="onAvatarChange" />
          <strong class="user-name">{{ account.nickname || account.username || "未设置昵称" }}</strong>
          <div class="user-badges">
            <span class="badge-pill">BMI {{ bmiValue }}</span>
            <span class="badge-pill" :class="Number(profileCompletion) >= 80 ? 'badge-good' : 'badge-warn'">
              {{ profileCompletion }} 完整
            </span>
          </div>
        </div>

        <!-- 快速指标 -->
        <div class="sidebar-card metrics-card">
          <span class="card-label">身体指标</span>
          <div class="metric-rows">
            <div class="metric-row">
              <span>身高</span>
              <strong>{{ profile.height_cm ? profile.height_cm + ' cm' : '—' }}</strong>
            </div>
            <div class="metric-row">
              <span>体重</span>
              <strong>{{ profile.weight_kg ? profile.weight_kg + ' kg' : '—' }}</strong>
            </div>
            <div class="metric-row">
              <span>目标体重</span>
              <strong>{{ profile.target_weight_kg ? profile.target_weight_kg + ' kg' : '—' }}</strong>
            </div>
            <div class="metric-row">
              <span>目标差值</span>
              <strong>{{ weightGap }}</strong>
            </div>
            <div class="metric-row">
              <span>活动水平</span>
              <strong>{{ profile.activity_level === 'low' ? '久坐' : profile.activity_level === 'high' ? '高强度' : '轻度' }}</strong>
            </div>
          </div>
        </div>

        <!-- 目录导航 -->
        <div class="sidebar-card nav-card">
          <span class="card-label">快速跳转</span>
          <div class="nav-list">
            <button class="nav-btn" @click="$el.querySelector('#section-basic')?.scrollIntoView({ behavior: 'smooth', block: 'start' })">
              <span class="nav-icon">01</span>基本信息
            </button>
            <button class="nav-btn" @click="$el.querySelector('#section-body')?.scrollIntoView({ behavior: 'smooth', block: 'start' })">
              <span class="nav-icon">02</span>身体参数
            </button>
            <button class="nav-btn" @click="$el.querySelector('#section-health')?.scrollIntoView({ behavior: 'smooth', block: 'start' })">
              <span class="nav-icon">03</span>健康约束
            </button>
            <button class="nav-btn" @click="$el.querySelector('#section-security')?.scrollIntoView({ behavior: 'smooth', block: 'start' })">
              <span class="nav-icon">04</span>账号安全
            </button>
          </div>
        </div>

      </aside>

      <!-- 右侧主内容 -->
      <main class="main-content">

        <!-- 基本信息 -->
        <section id="section-basic" class="content-section">
          <div class="section-header">
            <p class="section-kicker">01 / Basic Info</p>
            <h3>基本信息</h3>
          </div>
          <div class="card">
            <div class="avatar-row">
              <div class="avatar-wrap-inline" @click="triggerAvatarUpload" title="点击更换头像">
                <img v-if="account.avatar_url" :src="account.avatar_url" class="avatar-img" alt="头像" />
                <div v-else class="avatar-placeholder">{{ avatarInitial }}</div>
                <div class="avatar-overlay">更换</div>
              </div>
              <span class="avatar-hint">支持 JPG / PNG，最大 5MB</span>
            </div>
            <el-form :model="account" label-position="top">
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="用户名">
                    <el-input v-model.trim="account.username" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="昵称">
                    <el-input v-model.trim="account.nickname" placeholder="对外展示名称" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="邮箱">
                    <el-input v-model.trim="account.email" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="手机号">
                    <el-input v-model.trim="account.phone" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="个性签名">
                <el-input v-model.trim="account.signature" maxlength="80" show-word-limit placeholder="例如：希望把饮食管理做成长期习惯。" />
              </el-form-item>
            </el-form>
          </div>
        </section>

        <!-- 身体参数 -->
        <section id="section-body" class="content-section">
          <div class="section-header">
            <p class="section-kicker">02 / Body & Lifestyle</p>
            <h3>身体参数</h3>
          </div>
          <div class="card">
            <el-form :model="profile" label-position="top">
              <el-row :gutter="16">
                <el-col :span="8">
                  <el-form-item label="性别">
                    <el-select v-model="profile.gender" style="width: 100%" :teleported="true">
                      <el-option label="未设置" value="" />
                      <el-option label="男" value="male" />
                      <el-option label="女" value="female" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="生日">
                    <el-date-picker v-model="profile.birthday" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="家庭人数">
                    <el-input-number v-model="profile.household_size" :min="1" :max="10" style="width: 100%" />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="16">
                <el-col :span="8">
                  <el-form-item label="身高(cm)">
                    <el-input-number v-model="profile.height_cm" :min="0" :precision="1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="体重(kg)">
                    <el-input-number v-model="profile.weight_kg" :min="0" :precision="1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="目标体重(kg)">
                    <el-input-number v-model="profile.target_weight_kg" :min="0" :precision="1" style="width: 100%" />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="16">
                <el-col :span="8">
                  <el-form-item label="活动水平">
                    <el-select v-model="profile.activity_level" style="width: 100%">
                      <el-option label="久坐为主" value="low" />
                      <el-option label="轻度活动" value="medium" />
                      <el-option label="经常运动" value="high" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="烹饪熟练度">
                    <el-select v-model="profile.cooking_skill" style="width: 100%">
                      <el-option label="新手" value="beginner" />
                      <el-option label="日常家常水平" value="intermediate" />
                      <el-option label="熟练" value="advanced" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="预算水平">
                    <el-select v-model="profile.budget_level" style="width: 100%">
                      <el-option label="节约" value="budget" />
                      <el-option label="均衡" value="balanced" />
                      <el-option label="宽松" value="premium" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="饮食偏好">
                    <el-select v-model="profile.meal_preference" style="width: 100%">
                      <el-option label="家常清淡" value="light_home" />
                      <el-option label="高蛋白优先" value="high_protein" />
                      <el-option label="低脂控能量" value="low_fat" />
                      <el-option label="省时方便" value="fast_easy" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="饮食类型">
                    <el-select v-model="profile.diet_type" style="width: 100%">
                      <el-option label="均衡饮食" value="balanced" />
                      <el-option label="高蛋白" value="high_protein" />
                      <el-option label="低碳水" value="low_carb" />
                      <el-option label="素食" value="vegetarian" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="职业">
                    <el-input v-model.trim="profile.occupation" placeholder="例如：产品经理、教师、学生" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="外食频率">
                    <el-switch v-model="profile.is_outdoor_eating_frequent" active-text="经常外食" inactive-text="以家里吃饭为主" />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </div>
        </section>

        <!-- 健康约束 -->
        <section id="section-health" class="content-section">
          <div class="section-header">
            <p class="section-kicker">03 / Health Constraints</p>
            <h3>健康约束</h3>
          </div>
          <div class="card">
            <el-form :model="health" label-position="top">
              <div class="toggle-grid">
                <el-checkbox v-model="health.has_diabetes">糖尿病</el-checkbox>
                <el-checkbox v-model="health.has_hypertension">高血压</el-checkbox>
                <el-checkbox v-model="health.has_hyperlipidemia">高血脂</el-checkbox>
                <el-checkbox v-model="health.is_pregnant">孕期</el-checkbox>
                <el-checkbox v-model="health.is_lactating">哺乳期</el-checkbox>
                <el-checkbox v-model="health.has_allergy">存在过敏项</el-checkbox>
              </div>

              <el-form-item label="过敏标签">
                <el-select
                  v-model="health.allergy_tags"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  style="width: 100%"
                  placeholder="输入后回车，可添加多个"
                  :teleported="true"
                >
                  <el-option v-for="item in allergyOptions" :key="item" :label="item" :value="item" />
                </el-select>
              </el-form-item>

              <el-form-item label="忌口标签">
                <el-select
                  v-model="health.avoid_food_tags"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  style="width: 100%"
                  placeholder="输入后回车，可添加多个"
                  :teleported="true"
                >
                  <el-option v-for="item in avoidFoodOptions" :key="item" :label="item" :value="item" />
                </el-select>
              </el-form-item>

              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="宗教或特殊限制">
                    <el-input v-model.trim="health.religious_restriction" placeholder="例如：清真、无猪肉" />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="补充说明">
                <el-input v-model.trim="health.notes" type="textarea" :rows="3" placeholder="例如：最近正在控糖，需要优先减少含糖饮料。" />
              </el-form-item>
            </el-form>
          </div>

          <!-- 保存按钮 (资料区) -->
          <div class="section-save-bar">
            <FormActionBar
              :tone="saving ? 'saving' : profileSaveTone"
              :title="profileSaveTitle"
              :description="profileSaveDescription"
              primary-label="保存全部资料"
              :disabled="profileSaveDisabled"
              :loading="saving"
              @primary="saveAll"
            />
          </div>
        </section>

        <!-- 账号安全 -->
        <section id="section-security" class="content-section">
          <div class="section-header">
            <p class="section-kicker">04 / Account Security</p>
            <h3>账号安全</h3>
          </div>

          <!-- 修改密码 -->
          <div class="card">
            <h4 class="sub-title">修改密码</h4>
            <el-form label-position="top" style="max-width: 480px">
              <el-form-item label="当前密码">
                <el-input v-model="pwd.old" type="password" show-password placeholder="请输入当前密码" />
              </el-form-item>
              <el-form-item label="新密码">
                <el-input v-model="pwd.new" type="password" show-password placeholder="至少 8 位，包含字母和数字" />
              </el-form-item>
              <el-form-item label="确认新密码">
                <el-input v-model="pwd.confirm" type="password" show-password placeholder="再次输入新密码" />
                <div v-if="pwd.new && pwd.confirm && pwd.new !== pwd.confirm" class="field-error">两次密码不一致</div>
              </el-form-item>
              <el-button type="primary" :loading="pwdSaving" :disabled="pwdDisabled" @click="submitChangePassword">更新密码</el-button>
            </el-form>
          </div>

          <!-- 密保问题 -->
          <div class="card">
            <h4 class="sub-title">密保问题</h4>
            <p class="security-desc">设置密保问题后，忘记密码时可通过回答密保问题重置密码，无需邮件验证。</p>
            <el-form label-position="top" style="max-width: 480px">
              <el-form-item label="密保问题">
                <el-select v-model="securityForm.question" style="width: 100%" placeholder="选择一个密保问题">
                  <el-option v-for="q in securityQuestions" :key="q" :label="q" :value="q" />
                </el-select>
              </el-form-item>
              <el-form-item label="密保答案">
                <el-input v-model.trim="securityForm.answer" placeholder="答案不区分大小写" />
              </el-form-item>
              <el-button type="primary" :loading="securitySaving" :disabled="!securityForm.question || !securityForm.answer" @click="submitSecurityQuestion">保存密保</el-button>
            </el-form>
          </div>

          <!-- 注销账号（危险区） -->
          <div class="card danger-zone">
            <h4 class="sub-title danger-title">注销账号</h4>
            <p class="danger-desc">注销后账号数据将被永久删除，无法恢复。请输入密码确认操作。</p>
            <el-form label-position="top" style="max-width: 480px">
              <el-form-item label="当前密码">
                <el-input v-model="deletePassword" type="password" show-password placeholder="输入密码确认注销" />
              </el-form-item>
              <el-button type="danger" :disabled="!deletePassword" @click="submitDeleteAccount">注销账号</el-button>
            </el-form>
          </div>
        </section>

      </main>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessageBox } from "element-plus";
import { useRouter } from "vue-router";
import FormActionBar from "../components/FormActionBar.vue";
import { notifyActionError, notifyActionSuccess, notifyLoadError } from "../lib/feedback";
import { getMe, updateFullProfile, changePassword, deleteAccount, uploadAvatar, getSecurityQuestions, setSecurityQuestion } from "../api/auth";
import { trackEvent } from "../api/behavior";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const router = useRouter();
const saving = ref(false);
const allergyOptions = ["花生", "牛奶", "海鲜", "鸡蛋", "芒果", "坚果"];
const avoidFoodOptions = ["油炸", "甜食", "辛辣", "高盐", "高脂", "夜宵"];

const account = reactive({
  username: "",
  email: "",
  phone: "",
  nickname: "",
  signature: "",
  avatar_url: "",
});

const profile = reactive({
  gender: "",
  birthday: "",
  height_cm: 0,
  weight_kg: 0,
  target_weight_kg: 0,
  activity_level: "medium",
  occupation: "",
  budget_level: "balanced",
  cooking_skill: "intermediate",
  meal_preference: "light_home",
  diet_type: "balanced",
  is_outdoor_eating_frequent: false,
  household_size: 1,
});

const health = reactive({
  has_allergy: false,
  allergy_tags: [] as string[],
  avoid_food_tags: [] as string[],
  religious_restriction: "",
  has_hypertension: false,
  has_diabetes: false,
  has_hyperlipidemia: false,
  is_pregnant: false,
  is_lactating: false,
  notes: "",
});

const bmiValue = computed(() => {
  const height = Number(profile.height_cm);
  const weight = Number(profile.weight_kg);
  if (!height || !weight) {
    return "-";
  }
  return (weight / ((height / 100) * (height / 100))).toFixed(1);
});

const weightGap = computed(() => {
  const current = Number(profile.weight_kg);
  const target = Number(profile.target_weight_kg);
  if (!current || !target) {
    return "-";
  }
  const diff = current - target;
  if (diff === 0) {
    return "已达到";
  }
  return `${Math.abs(diff).toFixed(1)} kg ${diff > 0 ? "待减少" : "待增加"}`;
});

const profileCompletion = computed(() => {
  let count = 0;
  if (account.nickname) count += 1;
  if (profile.height_cm) count += 1;
  if (profile.weight_kg) count += 1;
  if (profile.target_weight_kg) count += 1;
  if (profile.activity_level) count += 1;
  if (profile.diet_type) count += 1;
  if (health.allergy_tags.length || health.avoid_food_tags.length || health.has_diabetes || health.has_hypertension || health.has_hyperlipidemia) count += 1;
  const percentage = Math.round((count / 7) * 100);
  return `${percentage}%`;
});
const profileSaveDisabled = computed(() => !account.username.trim());
const profileSaveTone = computed(() => (profileSaveDisabled.value ? "warning" : "ready"));
const profileSaveTitle = computed(() => {
  if (profileSaveDisabled.value) {
    return "用户名不能为空";
  }
  if (Number(profileCompletion.value.replace("%", "")) < 60) {
    return "资料可以保存，但建议继续补齐核心信息";
  }
  return "资料已达到较完整状态，可以保存";
});
const profileSaveDescription = computed(() => {
  return profileSaveDisabled.value
    ? "账号信息里至少需要保留一个用户名。"
    : "优先补齐身高、体重、目标体重和饮食约束，后续推荐、目标和报表会更可信。";
});

async function loadProfile() {
  try {
    const response = await getMe();
    const user = response.data;
    if (!user) return;

    Object.assign(account, {
      username: user.username || "",
      email: user.email || "",
      phone: user.phone || "",
      nickname: user.nickname || "",
      signature: user.signature || "",
      avatar_url: user.avatar_url || "",
    });

    Object.assign(profile, {
      gender: user.profile?.gender || "",
      birthday: user.profile?.birthday || "",
      height_cm: Number(user.profile?.height_cm || 0),
      weight_kg: Number(user.profile?.weight_kg || 0),
      target_weight_kg: Number(user.profile?.target_weight_kg || 0),
      activity_level: user.profile?.activity_level || "medium",
      occupation: user.profile?.occupation || "",
      budget_level: user.profile?.budget_level || "balanced",
      cooking_skill: user.profile?.cooking_skill || "intermediate",
      meal_preference: user.profile?.meal_preference || "light_home",
      diet_type: user.profile?.diet_type || "balanced",
      is_outdoor_eating_frequent: Boolean(user.profile?.is_outdoor_eating_frequent),
      household_size: Number(user.profile?.household_size || 1),
    });

    Object.assign(health, {
      has_allergy: Boolean(user.health_condition?.has_allergy),
      allergy_tags: user.health_condition?.allergy_tags || [],
      avoid_food_tags: user.health_condition?.avoid_food_tags || [],
      religious_restriction: user.health_condition?.religious_restriction || "",
      has_hypertension: Boolean(user.health_condition?.has_hypertension),
      has_diabetes: Boolean(user.health_condition?.has_diabetes),
      has_hyperlipidemia: Boolean(user.health_condition?.has_hyperlipidemia),
      is_pregnant: Boolean(user.health_condition?.is_pregnant),
      is_lactating: Boolean(user.health_condition?.is_lactating),
      notes: user.health_condition?.notes || "",
    });

    trackEvent({ behavior_type: "view", context_scene: "profile" }).catch(() => undefined);
  } catch (error) {
    notifyLoadError("个人资料");
  }
}

async function saveAll() {
  try {
    saving.value = true;
    const response = await updateFullProfile({
      account,
      profile,
      health_condition: {
        ...health,
        has_allergy: Boolean(health.has_allergy || health.allergy_tags.length),
      },
    });
    auth.user = response.data?.account ?? auth.user;
    notifyActionSuccess("资料已保存");
  } catch (error) {
    notifyActionError("保存资料");
  } finally {
    saving.value = false;
  }
}

const avatarInitial = computed(() => {
  const name = account.nickname || account.username;
  return name ? name.charAt(0).toUpperCase() : "?";
});

const avatarInput = ref<HTMLInputElement | null>(null);

function triggerAvatarUpload() {
  avatarInput.value?.click();
}

async function onAvatarChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  try {
    const res = await uploadAvatar(file);
    account.avatar_url = res.avatar_url;
    if (auth.user) auth.user.avatar_url = res.avatar_url;
    notifyActionSuccess("头像已更新");
  } catch {
    notifyActionError("上传头像");
  } finally {
    if (avatarInput.value) avatarInput.value.value = "";
  }
}

onMounted(loadProfile);
onMounted(loadSecurityQuestions);

const pwd = reactive({ old: "", new: "", confirm: "" });
const pwdSaving = ref(false);
const pwdDisabled = computed(
  () => !pwd.old || !pwd.new || pwd.new.length < 8 || pwd.new !== pwd.confirm
);

async function submitChangePassword() {
  try {
    pwdSaving.value = true;
    await changePassword({ old_password: pwd.old, new_password: pwd.new });
    notifyActionSuccess("密码已更新，请重新登录");
    pwd.old = "";
    pwd.new = "";
    pwd.confirm = "";
    auth.clearAuth();
    router.push("/login");
  } catch (error: any) {
    const msg = error?.response?.data?.message || "修改密码失败，请稍后重试";
    notifyActionError(msg);
  } finally {
    pwdSaving.value = false;
  }
}

const deletePassword = ref("");

const securityQuestions = ref<string[]>([]);
const securityForm = reactive({ question: "", answer: "" });
const securitySaving = ref(false);

async function loadSecurityQuestions() {
  try {
    const res = await getSecurityQuestions();
    securityQuestions.value = res.data ?? [];
  } catch {
    // non-critical, ignore
  }
}

async function submitSecurityQuestion() {
  if (!securityForm.question || !securityForm.answer.trim()) return;
  try {
    securitySaving.value = true;
    await setSecurityQuestion({ question: securityForm.question, answer: securityForm.answer.trim() });
    notifyActionSuccess("密保问题已设置");
    securityForm.answer = "";
  } catch {
    notifyActionError("设置密保问题");
  } finally {
    securitySaving.value = false;
  }
}

async function submitDeleteAccount() {
  try {
    await ElMessageBox.confirm("注销后账号数据将被永久删除，此操作不可撤销。确认继续？", "注销账号", {
      confirmButtonText: "确认注销",
      cancelButtonText: "取消",
      type: "warning",
      confirmButtonClass: "el-button--danger",
    });
  } catch {
    return;
  }
  try {
    await deleteAccount({ password: deletePassword.value });
    notifyActionSuccess("账号已注销");
    auth.clearAuth();
    router.push("/login");
  } catch (error: any) {
    const msg = error?.response?.data?.message || "注销失败，请检查密码是否正确";
    notifyActionError(msg);
  }
}
</script>

<style scoped>
/* ── 整体布局 ─────────────────────────────────── */
.profile-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* ── 顶部问候栏 ───────────────────────────────── */
.greeting-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid rgba(16, 34, 42, 0.07);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 10;
  flex-wrap: wrap;
}

.greeting-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #10222a;
}

.greeting-sub {
  margin: 4px 0 0;
  font-size: 13px;
  color: #5a7a8a;
}

.greeting-right {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* ── 双栏主体 ─────────────────────────────────── */
.main-layout {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 0;
  flex: 1;
}

/* ── 左侧栏 ───────────────────────────────────── */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 16px 20px 20px;
  border-right: 1px solid rgba(16, 34, 42, 0.07);
  position: sticky;
  top: 61px;
  max-height: calc(100vh - 61px);
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(16, 34, 42, 0.1) transparent;
}

.sidebar-card {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 34, 42, 0.08);
  border-radius: 20px;
  padding: 18px;
  box-shadow: 0 4px 16px rgba(15, 30, 39, 0.05);
}

.card-label {
  display: block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #5a7a8a;
  margin-bottom: 12px;
}

/* 用户摘要卡 */
.user-summary-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 10px;
}

.avatar-wrap {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  cursor: pointer;
  flex-shrink: 0;
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #d0e8f5;
  color: #2d6a8a;
  font-size: 28px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.38);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.18s ease;
}

.avatar-wrap:hover .avatar-overlay {
  opacity: 1;
}

.user-name {
  font-size: 16px;
  font-weight: 700;
  color: #10222a;
}

.user-badges {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: center;
}

.badge-pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(16, 34, 42, 0.07);
  color: #10222a;
}

.badge-good {
  background: rgba(29, 111, 95, 0.12);
  color: #1d6f5f;
}

.badge-warn {
  background: rgba(185, 115, 38, 0.12);
  color: #b97326;
}

/* 快速指标卡 */
.metric-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid rgba(16, 34, 42, 0.05);
}

.metric-row:last-child {
  border-bottom: none;
}

.metric-row span {
  font-size: 12px;
  color: #5a7a8a;
}

.metric-row strong {
  font-size: 14px;
  font-weight: 700;
  color: #10222a;
}

/* 导航卡 */
.nav-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 12px;
  border: none;
  background: transparent;
  color: #476072;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s ease, color 0.15s ease;
  width: 100%;
}

.nav-btn:hover {
  background: rgba(16, 34, 42, 0.06);
  color: #10222a;
}

.nav-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 24px;
  border-radius: 8px;
  background: rgba(62, 109, 127, 0.1);
  color: #3e6d7f;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

/* ── 右侧主内容 ───────────────────────────────── */
.main-content {
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.content-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.section-header {
  padding-bottom: 4px;
}

.section-kicker {
  margin: 0 0 4px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-size: 11px;
  color: #3e6d7f;
}

h3 {
  margin: 0;
  font-size: 20px;
  color: #10222a;
}

h4 {
  margin: 0;
}

.card {
  padding: 22px 24px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.sub-title {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 700;
  color: #10222a;
}

.toggle-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

/* 头像行（card内行内版） */
.avatar-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.avatar-wrap-inline {
  position: relative;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  cursor: pointer;
  flex-shrink: 0;
  overflow: hidden;
}

.avatar-wrap-inline .avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.avatar-wrap-inline .avatar-overlay {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.38);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.18s ease;
}

.avatar-wrap-inline:hover .avatar-overlay {
  opacity: 1;
}

.avatar-wrap-inline .avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #d0e8f5;
  color: #2d6a8a;
  font-size: 24px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-hint {
  font-size: 13px;
  color: #7a9aaa;
}

/* section 保存栏 */
.section-save-bar {
  margin-top: 4px;
}

/* 字段错误 */
.field-error {
  margin-top: 4px;
  font-size: 12px;
  color: #cf1322;
}

/* 安全描述 */
.security-desc {
  margin: 0 0 16px;
  color: #476072;
  font-size: 14px;
  line-height: 1.6;
}

/* 危险区域 */
.danger-zone {
  border-color: rgba(207, 19, 34, 0.2);
  background: rgba(255, 241, 240, 0.6);
}

.danger-title {
  color: #a8071a;
}

.danger-desc {
  margin: 0 0 16px;
  color: #8c4a50;
  font-size: 14px;
  line-height: 1.6;
}

/* ── 响应式 ───────────────────────────────────── */
@media (max-width: 1100px) {
  .main-layout {
    grid-template-columns: 220px minmax(0, 1fr);
  }
}

@media (max-width: 860px) {
  .main-layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static;
    max-height: none;
    padding: 16px;
    flex-direction: row;
    flex-wrap: wrap;
    border-right: none;
    border-bottom: 1px solid rgba(16, 34, 42, 0.07);
  }

  .sidebar-card {
    flex: 1 1 200px;
  }

  .main-content {
    padding: 16px;
  }
}

@media (max-width: 640px) {
  .greeting-bar {
    padding: 14px 16px;
  }

  .toggle-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
