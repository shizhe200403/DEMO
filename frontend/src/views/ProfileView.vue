<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Account</p>
        <h2>个人中心</h2>
      </div>
      <el-button type="primary" @click="saveAll">保存全部</el-button>
    </div>

    <div class="card">
      <h3>基础资料</h3>
      <el-form :model="account" label-position="top">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="用户名">
              <el-input v-model="account.username" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱">
              <el-input v-model="account.email" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机号">
              <el-input v-model="account.phone" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="昵称">
              <el-input v-model="account.nickname" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="签名">
          <el-input v-model="account.signature" />
        </el-form-item>
      </el-form>
    </div>

    <div class="card">
      <h3>健康档案</h3>
      <el-form :model="profile" label-position="top">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="身高(cm)">
              <el-input-number v-model="profile.height_cm" :min="0" :precision="1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="体重(kg)">
              <el-input-number v-model="profile.weight_kg" :min="0" :precision="1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="目标体重(kg)">
              <el-input-number v-model="profile.target_weight_kg" :min="0" :precision="1" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="饮食偏好">
              <el-input v-model="profile.meal_preference" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="饮食类型">
              <el-input v-model="profile.diet_type" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </div>

    <div class="card">
      <h3>健康约束</h3>
      <el-form :model="health" label-position="top">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-checkbox v-model="health.has_diabetes">糖尿病</el-checkbox>
          </el-col>
          <el-col :span="8">
            <el-checkbox v-model="health.has_hypertension">高血压</el-checkbox>
          </el-col>
          <el-col :span="8">
            <el-checkbox v-model="health.has_hyperlipidemia">高血脂</el-checkbox>
          </el-col>
        </el-row>
        <el-form-item label="过敏标签">
          <el-input v-model="health.allergy_tags_text" placeholder="用英文逗号分隔" />
        </el-form-item>
        <el-form-item label="忌口标签">
          <el-input v-model="health.avoid_food_tags_text" placeholder="用英文逗号分隔" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="health.notes" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive } from "vue";
import { ElMessage } from "element-plus";
import { getMe, updateFullProfile } from "../api/auth";
import { trackEvent } from "../api/behavior";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const account = reactive({
  username: "",
  email: "",
  phone: "",
  nickname: "",
  signature: "",
});

const profile = reactive({
  height_cm: 0,
  weight_kg: 0,
  target_weight_kg: 0,
  meal_preference: "",
  diet_type: "",
});

const health = reactive({
  has_diabetes: false,
  has_hypertension: false,
  has_hyperlipidemia: false,
  allergy_tags_text: "",
  avoid_food_tags_text: "",
  notes: "",
});

async function loadProfile() {
  try {
    const response = await getMe();
    const user = response.data?.data;
    if (!user) return;

    Object.assign(account, {
      username: user.username || "",
      email: user.email || "",
      phone: user.phone || "",
      nickname: user.nickname || "",
      signature: user.signature || "",
    });

    Object.assign(profile, {
      height_cm: Number(user.profile?.height_cm || 0),
      weight_kg: Number(user.profile?.weight_kg || 0),
      target_weight_kg: Number(user.profile?.target_weight_kg || 0),
      meal_preference: user.profile?.meal_preference || "",
      diet_type: user.profile?.diet_type || "",
    });

    Object.assign(health, {
      has_diabetes: Boolean(user.health_condition?.has_diabetes),
      has_hypertension: Boolean(user.health_condition?.has_hypertension),
      has_hyperlipidemia: Boolean(user.health_condition?.has_hyperlipidemia),
      allergy_tags_text: (user.health_condition?.allergy_tags || []).join(","),
      avoid_food_tags_text: (user.health_condition?.avoid_food_tags || []).join(","),
      notes: user.health_condition?.notes || "",
    });

    trackEvent({ behavior_type: "view", context_scene: "profile" }).catch(() => undefined);
  } catch (error) {
    ElMessage.error("加载个人资料失败");
  }
}

async function saveAll() {
  try {
    const response = await updateFullProfile({
      account,
      profile,
      health_condition: {
        has_diabetes: health.has_diabetes,
        has_hypertension: health.has_hypertension,
        has_hyperlipidemia: health.has_hyperlipidemia,
        allergy_tags: health.allergy_tags_text.split(",").map((item) => item.trim()).filter(Boolean),
        avoid_food_tags: health.avoid_food_tags_text.split(",").map((item) => item.trim()).filter(Boolean),
        notes: health.notes,
      },
    });
    auth.user = response.data?.data?.account ?? auth.user;
    ElMessage.success("保存成功");
  } catch (error) {
    ElMessage.error("保存失败");
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
  align-items: center;
  gap: 12px;
}

.tag {
  margin: 0 0 6px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-size: 12px;
  color: #3e6d7f;
}

h2 {
  margin: 0;
  font-size: 30px;
}

.card {
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.card h3 {
  margin: 0 0 16px;
  font-size: 20px;
}
</style>
