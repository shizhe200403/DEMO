<template>
  <div class="refresh-frame" :class="{ 'is-refreshing': active }">
    <div v-if="active" class="refresh-overlay" aria-live="polite" role="status">
      <span>{{ label }}</span>
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    active?: boolean;
    label?: string;
  }>(),
  {
    active: false,
    label: "正在更新",
  },
);
</script>

<style scoped>
.refresh-frame {
  position: relative;
  min-width: 0;
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.refresh-frame.is-refreshing {
  transform: translateY(2px);
}

.refresh-overlay {
  position: absolute;
  top: -8px;
  right: 0;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 10px 30px rgba(15, 30, 39, 0.08);
  color: #24566a;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.refresh-overlay::before {
  content: "";
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: linear-gradient(135deg, #2f7c98, #57b5e7);
  box-shadow: 0 0 0 0 rgba(87, 181, 231, 0.48);
  animation: pulse 1.2s ease-in-out infinite;
}

.refresh-frame.is-refreshing::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 26px;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), transparent 32%);
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(87, 181, 231, 0.34);
  }
  50% {
    transform: scale(1.08);
    box-shadow: 0 0 0 8px rgba(87, 181, 231, 0);
  }
}

@media (max-width: 768px) {
  .refresh-overlay {
    left: 0;
    right: auto;
    top: -10px;
  }
}
</style>
