<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Account</p>
        <h2>个人中心</h2>
        <p class="desc">先把资料填对，推荐、目标和报表才会逐步变得可信。</p>
      </div>
      <el-button type="primary" :loading="saving" :disabled="profileSaveDisabled" @click="saveAll">保存全部</el-button>
    </div>

    <div class="summary-grid">
      <article>
        <span>昵称</span>
        <strong>{{ account.nickname || account.username || "未设置" }}</strong>
      </article>
      <article>
        <span>BMI</span>
        <strong>{{ bmiValue }}</strong>
      </article>
      <article>
        <span>目标差值</span>
        <strong>{{ weightGap }}</strong>
      </article>
      <article>
        <span>档案完整度</span>
        <strong>{{ profileCompletion }}</strong>
      </article>
    </div>

    <div class="card">
      <h3>账号信息</h3>
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

    <div class="card">
      <h3>身体与生活方式</h3>
      <el-form :model="profile" label-position="top">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="性别">
              <el-select v-model="profile.gender" style="width: 100%">
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

    <div class="card">
      <h3>健康约束与忌口</h3>
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

    <FormActionBar
      :tone="saving ? 'saving' : profileSaveTone"
      :title="profileSaveTitle"
      :description="profileSaveDescription"
      primary-label="保存全部资料"
      :disabled="profileSaveDisabled"
      :loading="saving"
      @primary="saveAll"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import FormActionBar from "../components/FormActionBar.vue";
import { notifyActionError, notifyActionSuccess, notifyLoadError } from "../lib/feedback";
import { getMe, updateFullProfile } from "../api/auth";
import { trackEvent } from "../api/behavior";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const saving = ref(false);
const allergyOptions = ["花生", "牛奶", "海鲜", "鸡蛋", "芒果", "坚果"];
const avoidFoodOptions = ["油炸", "甜食", "辛辣", "高盐", "高脂", "夜宵"];

const account = reactive({
  username: "",
  email: "",
  phone: "",
  nickname: "",
  signature: "",
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

onMounted(loadProfile);
</script>

<style scoped>
.page {
  display: grid;
  gap: 16px;
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

h2,
h3 {
  margin: 0;
}

h2 {
  font-size: 30px;
}

.desc,
.summary-grid p {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.65;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.summary-grid article,
.card {
  padding: 20px 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.summary-grid span {
  display: block;
  font-size: 12px;
  color: #5a7a8a;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.summary-grid strong {
  display: block;
  margin-top: 8px;
  font-size: 22px;
}

.card h3 {
  margin-bottom: 16px;
  font-size: 20px;
}

.toggle-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

@media (max-width: 768px) {
  .head {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
