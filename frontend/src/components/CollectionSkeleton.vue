<template>
  <div class="collection-skeleton" :class="[`is-${variant}`]">
    <template v-if="variant === 'dashboard'">
      <section class="dashboard-hero">
        <article class="surface hero-card">
          <div class="s-line w-20" />
          <div class="s-line w-55 lg" />
          <div class="s-line w-90" />
          <div class="s-line w-72" />
          <div class="cta-row">
            <div class="s-pill" />
            <div class="s-pill" />
            <div class="s-pill" />
          </div>
        </article>
        <div class="summary-grid">
          <article v-for="item in summaryCount" :key="`dashboard-summary-${item}`" class="surface summary-card">
            <div class="s-line w-28" />
            <div class="s-line w-50 lg" />
            <div class="s-line w-88" />
          </article>
        </div>
      </section>

      <div class="dashboard-grid">
        <article v-for="item in cardCount" :key="`dashboard-grid-${item}`" class="surface panel-card">
          <div class="s-line w-34" />
          <div class="s-line w-76" />
          <div class="stack gap-md">
            <div v-for="line in 3" :key="`dashboard-grid-line-${item}-${line}`" class="s-line" :class="line === 3 ? 'w-60' : 'w-100'" />
          </div>
        </article>
      </div>

      <div class="dashboard-list">
        <article v-for="item in 3" :key="`dashboard-list-${item}`" class="surface list-card">
          <div class="row between">
            <div class="stack">
              <div class="s-line w-36" />
              <div class="s-line w-70" />
            </div>
            <div class="s-pill sm" />
          </div>
          <div class="stack gap-sm">
            <div class="s-line w-100" />
            <div class="s-line w-82" />
          </div>
        </article>
      </div>
    </template>

    <template v-else>
      <div v-if="showSummary" class="summary-grid">
        <article v-for="item in summaryCount" :key="`summary-${item}`" class="surface summary-card">
          <div class="s-line w-26" />
          <div class="s-line w-52 lg" />
          <div class="s-line w-84" />
        </article>
      </div>

      <div v-if="showToolbar" class="toolbar-row">
        <div class="s-input" />
        <div class="toolbar-chips">
          <div class="s-pill" />
          <div class="s-pill" />
          <div class="s-pill" />
        </div>
      </div>

      <div class="items" :class="variant === 'list' ? 'is-list' : 'is-grid'">
        <article v-for="item in cardCount" :key="`card-${item}`" class="surface item-card">
          <div class="row between start">
            <div class="stack">
              <div class="s-line w-42" />
              <div class="s-line w-78" />
            </div>
            <div class="s-pill sm" />
          </div>
          <div class="stack gap-sm">
            <div class="s-line w-100" />
            <div class="s-line w-92" />
            <div class="s-line w-64" />
          </div>
          <div class="chip-row">
            <div class="s-chip" />
            <div class="s-chip" />
            <div class="s-chip" />
          </div>
        </article>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: "grid" | "list" | "dashboard";
    cardCount?: number;
    summaryCount?: number;
    showSummary?: boolean;
    showToolbar?: boolean;
  }>(),
  {
    variant: "grid",
    cardCount: 6,
    summaryCount: 4,
    showSummary: true,
    showToolbar: true,
  },
);
</script>

<style scoped>
.collection-skeleton,
.summary-grid,
.dashboard-grid,
.dashboard-list,
.items,
.stack {
  display: grid;
  gap: 14px;
}

.dashboard-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 20px;
}

.summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
}

.dashboard-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.items.is-grid {
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}

.items.is-list,
.dashboard-list {
  grid-template-columns: 1fr;
}

.surface {
  padding: 20px;
  border-radius: 24px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.06);
}

.hero-card {
  padding: 28px;
}

.panel-card,
.item-card,
.list-card {
  min-height: 168px;
}

.toolbar-row,
.row,
.toolbar-chips,
.cta-row,
.chip-row {
  display: flex;
  gap: 12px;
}

.toolbar-row,
.row.between {
  justify-content: space-between;
  align-items: center;
}

.row.start {
  align-items: flex-start;
}

.toolbar-row {
  flex-wrap: wrap;
}

.toolbar-chips,
.cta-row,
.chip-row {
  flex-wrap: wrap;
}

.stack {
  gap: 10px;
}

.gap-sm {
  gap: 8px;
}

.gap-md {
  gap: 12px;
}

.s-line,
.s-pill,
.s-chip,
.s-input {
  position: relative;
  overflow: hidden;
  background: rgba(211, 223, 232, 0.72);
}

.s-line::after,
.s-pill::after,
.s-chip::after,
.s-input::after {
  content: "";
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.65), transparent);
  animation: shimmer 1.35s ease-in-out infinite;
}

.s-line {
  height: 12px;
  border-radius: 999px;
}

.s-line.lg {
  height: 28px;
}

.s-pill,
.s-chip {
  height: 32px;
  width: 92px;
  border-radius: 999px;
}

.s-pill.sm {
  width: 72px;
}

.s-chip {
  width: 64px;
  height: 26px;
  border-radius: 14px;
}

.s-input {
  min-width: 220px;
  height: 42px;
  flex: 1 1 260px;
  border-radius: 14px;
}

.w-20 { width: 20%; }
.w-26 { width: 26%; }
.w-28 { width: 28%; }
.w-34 { width: 34%; }
.w-36 { width: 36%; }
.w-42 { width: 42%; }
.w-50 { width: 50%; }
.w-52 { width: 52%; }
.w-55 { width: 55%; }
.w-60 { width: 60%; }
.w-64 { width: 64%; }
.w-70 { width: 70%; }
.w-72 { width: 72%; }
.w-76 { width: 76%; }
.w-78 { width: 78%; }
.w-82 { width: 82%; }
.w-84 { width: 84%; }
.w-88 { width: 88%; }
.w-90 { width: 90%; }
.w-92 { width: 92%; }
.w-100 { width: 100%; }

@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}

@media (max-width: 960px) {
  .dashboard-hero,
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .surface {
    padding: 18px;
    border-radius: 20px;
  }

  .items.is-grid,
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
