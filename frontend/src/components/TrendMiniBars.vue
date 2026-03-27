<template>
  <div class="trend-card" :class="[`is-${tone}`]">
    <div class="head">
      <div>
        <strong>{{ title }}</strong>
        <p v-if="description">{{ description }}</p>
      </div>
      <span v-if="badge" class="badge">{{ badge }}</span>
    </div>
    <div class="bars" :class="{ compact }">
      <div v-for="item in normalizedItems" :key="item.label" class="bar-item" :class="{ highlight: item.highlight }">
        <div class="bar-track">
          <div class="bar-fill" :style="{ height: `${item.height}%` }" />
        </div>
        <span class="bar-value">{{ item.display }}</span>
        <span class="bar-label">{{ item.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

type TrendItem = {
  label: string;
  value: number;
  display?: string;
  highlight?: boolean;
};

const props = withDefaults(
  defineProps<{
    title: string;
    description?: string;
    badge?: string;
    tone?: "neutral" | "energy" | "protein" | "success";
    compact?: boolean;
    items: TrendItem[];
  }>(),
  {
    description: "",
    badge: "",
    tone: "neutral",
    compact: false,
  },
);

const normalizedItems = computed(() => {
  const max = Math.max(...props.items.map((item) => Number(item.value) || 0), 1);
  return props.items.map((item, index) => {
    const value = Number(item.value) || 0;
    return {
      ...item,
      display: item.display ?? String(value),
      height: value <= 0 ? 10 : Math.max(16, Math.round((value / max) * 100)),
      highlight: item.highlight ?? index === props.items.length - 1,
    };
  });
});
</script>

<style scoped>
.trend-card {
  display: grid;
  gap: 14px;
  margin-top: 16px;
  padding: 18px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.head strong {
  font-size: 17px;
  color: #173042;
}

.head p {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.6;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: #e8f1f7;
  color: #24566a;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.bars {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(54px, 1fr));
  gap: 10px;
  align-items: end;
}

.bars.compact {
  grid-template-columns: repeat(auto-fit, minmax(42px, 1fr));
}

.bar-item {
  display: grid;
  gap: 8px;
  justify-items: center;
}

.bar-track {
  position: relative;
  width: 100%;
  height: 92px;
  border-radius: 16px;
  background: rgba(221, 232, 239, 0.72);
  border: 1px solid rgba(16, 34, 42, 0.05);
  overflow: hidden;
}

.bars.compact .bar-track {
  height: 74px;
}

.bar-fill {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 14px 14px 12px 12px;
  background: linear-gradient(180deg, #8db7cb 0%, #2f7c98 100%);
  transition: height 0.28s ease;
}

.bar-item.highlight .bar-fill {
  filter: saturate(1.05);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.22);
}

.bar-value,
.bar-label {
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.bar-value {
  color: #173042;
  font-weight: 700;
}

.bar-label {
  color: #5a7a8a;
}

.is-energy .badge,
.is-energy .bar-fill {
  background: linear-gradient(180deg, #f0bb72 0%, #c57a1e 100%);
}

.is-protein .badge,
.is-protein .bar-fill {
  background: linear-gradient(180deg, #78c6aa 0%, #2f8c6f 100%);
}

.is-success .badge,
.is-success .bar-fill {
  background: linear-gradient(180deg, #88cf9f 0%, #2f8c58 100%);
}

.is-energy .badge,
.is-protein .badge,
.is-success .badge {
  color: #fff;
}

@media (max-width: 768px) {
  .head {
    flex-direction: column;
  }
}
</style>
