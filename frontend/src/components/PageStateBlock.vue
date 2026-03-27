<template>
  <div class="state-block" :class="[compact ? 'is-compact' : '', `is-${tone}`]" role="status" aria-live="polite">
    <span class="state-badge">{{ toneLabel }}</span>
    <strong>{{ title }}</strong>
    <p v-if="description">{{ description }}</p>
    <div v-if="$slots.default" class="state-extra">
      <slot />
    </div>
    <div v-if="actionLabel || $slots.actions" class="state-actions">
      <slot name="actions">
        <el-button plain @click="emit('action')">{{ actionLabel }}</el-button>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    title: string;
    description?: string;
    tone?: "loading" | "empty" | "error" | "info";
    compact?: boolean;
    actionLabel?: string;
  }>(),
  {
    description: "",
    tone: "info",
    compact: false,
    actionLabel: "",
  },
);

const emit = defineEmits<{
  (event: "action"): void;
}>();

const toneLabel = computed(() => {
  return {
    loading: "加载中",
    empty: "暂无内容",
    error: "需要处理",
    info: "提示",
  }[props.tone];
});
</script>

<style scoped>
.state-block {
  display: grid;
  gap: 10px;
  padding: 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.state-block.is-compact {
  padding: 16px 18px;
  border-radius: 18px;
}

.state-badge {
  justify-self: flex-start;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #24566a;
  background: #e8f1f7;
}

.state-block strong {
  font-size: 18px;
  color: #173042;
}

.state-block p {
  margin: 0;
  color: #476072;
  line-height: 1.65;
}

.state-extra,
.state-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.state-block.is-loading {
  background: rgba(246, 250, 253, 0.94);
}

.state-block.is-empty .state-badge {
  background: rgba(232, 241, 247, 0.95);
}

.state-block.is-error .state-badge {
  background: rgba(255, 233, 231, 0.9);
  color: #8a3e35;
}

.state-block.is-info .state-badge {
  background: rgba(230, 244, 236, 0.92);
  color: #1f6a4c;
}
</style>
