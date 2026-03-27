<template>
  <div class="form-action-bar" :class="[`is-${tone}`, compact ? 'is-compact' : '']">
    <div class="copy">
      <span class="badge">{{ badgeLabel }}</span>
      <strong>{{ title }}</strong>
      <p v-if="description">{{ description }}</p>
    </div>
    <div class="actions">
      <slot />
      <el-button v-if="secondaryLabel" @click="emit('secondary')">{{ secondaryLabel }}</el-button>
      <el-button type="primary" :loading="loading" :disabled="disabled" @click="emit('primary')">
        {{ primaryLabel }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    title: string;
    description?: string;
    primaryLabel: string;
    secondaryLabel?: string;
    tone?: "ready" | "warning" | "saving";
    disabled?: boolean;
    loading?: boolean;
    compact?: boolean;
  }>(),
  {
    description: "",
    secondaryLabel: "",
    tone: "ready",
    disabled: false,
    loading: false,
    compact: false,
  },
);

const emit = defineEmits<{
  (event: "primary"): void;
  (event: "secondary"): void;
}>();

const badgeLabel = computed(() => {
  return {
    ready: "可提交",
    warning: "待完善",
    saving: "提交中",
  }[props.tone];
});
</script>

<style scoped>
.form-action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-top: 18px;
  padding: 18px 20px;
  border-radius: 20px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(247, 251, 255, 0.94);
}

.form-action-bar.is-compact {
  padding: 16px 18px;
}

.copy {
  display: grid;
  gap: 6px;
}

.badge {
  justify-self: flex-start;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  background: #e8f1f7;
  color: #24566a;
}

.copy strong {
  color: #173042;
  font-size: 16px;
}

.copy p {
  margin: 0;
  color: #476072;
  line-height: 1.6;
}

.actions {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10px;
}

.is-warning .badge {
  background: rgba(255, 233, 231, 0.9);
  color: #8a3e35;
}

.is-saving .badge {
  background: rgba(230, 244, 236, 0.92);
  color: #1f6a4c;
}

@media (max-width: 768px) {
  .form-action-bar,
  .actions {
    flex-direction: column;
    align-items: stretch;
  }

  .actions :deep(.el-button) {
    width: 100%;
    margin-left: 0;
  }
}
</style>
