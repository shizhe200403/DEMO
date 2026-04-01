<template>
  <div class="timeline-block">
    <div class="timeline-head">
      <div>
        <strong>{{ title }}</strong>
        <p>{{ description }}</p>
      </div>
      <span v-if="logs.length" class="timeline-meta">最近 {{ logs.length }} 条</span>
    </div>

    <PageStateBlock
      v-if="loading"
      tone="loading"
      title="正在拉取处理轨迹"
      :description="`先把 ${objectLabel} 最近被谁改过、改了什么同步出来。`"
      compact
    />
    <PageStateBlock
      v-else-if="!logs.length"
      tone="empty"
      title="还没有处理轨迹"
      :description="`${objectLabel} 目前还没有沉淀后台操作日志。`"
      compact
    />
    <div v-else class="timeline-list">
      <article v-for="log in logs" :key="log.id" class="timeline-item">
        <div class="timeline-item-head">
          <div>
            <span>{{ formatDateTime(log.created_at) }}</span>
            <strong>{{ log.summary }}</strong>
            <p>{{ log.actor?.display_name || log.actor?.username || "系统" }} · {{ moduleLabel(log.module) }}</p>
          </div>
          <el-tag size="small" :type="moduleTagType(log.module)" effect="light">{{ moduleLabel(log.module) }}</el-tag>
        </div>
        <div v-if="log.changes?.length" class="timeline-change-list">
          <article
            v-for="(change, index) in log.changes.slice(0, maxChanges)"
            :key="`${log.id}-${index}-${change.field}`"
            class="timeline-change-item"
          >
            <strong>{{ change.section ? `${change.section} · ${change.label}` : change.label }}</strong>
            <div class="timeline-change-values">
              <span>前：{{ formatChangeValue(change.before) }}</span>
              <span>后：{{ formatChangeValue(change.after) }}</span>
            </div>
          </article>
        </div>
        <div v-else class="timeline-change-empty">这条记录主要用来保留处理轨迹，没有字段差异明细。</div>
      </article>
    </div>
  </div>
</template>

<script setup lang="ts">
import PageStateBlock from "./PageStateBlock.vue";

withDefaults(
  defineProps<{
    title?: string;
    description?: string;
    objectLabel?: string;
    logs?: Array<Record<string, any>>;
    loading?: boolean;
    maxChanges?: number;
  }>(),
  {
    title: "最近处理回放",
    description: "直接看这个对象最近被谁怎么改过，避免只看到结果看不到过程。",
    objectLabel: "这个对象",
    logs: () => [],
    loading: false,
    maxChanges: 4,
  },
);

function moduleLabel(value: string) {
  return (
    {
      users: "用户管理",
      recipes: "菜谱管理",
      community: "社区审核",
      reports: "运营复核",
    }[value] || value
  );
}

function moduleTagType(value: string) {
  return (
    {
      users: "danger",
      recipes: "warning",
      community: "success",
      reports: "info",
    }[value] || "info"
  );
}

function formatDateTime(value?: string) {
  if (!value) return "暂无";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "暂无";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatChangeValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "空";
  if (Array.isArray(value)) return value.length ? value.join("、") : "空";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
</script>

<style scoped>
.timeline-block {
  display: grid;
  gap: 14px;
}

.timeline-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
}

.timeline-head strong {
  color: #173042;
  font-size: 17px;
}

.timeline-head p {
  margin: 6px 0 0;
  color: #5f7c8c;
  line-height: 1.6;
}

.timeline-meta {
  color: #698392;
  font-size: 12px;
}

.timeline-list {
  display: grid;
  gap: 10px;
}

.timeline-item {
  display: grid;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(248, 252, 255, 0.9);
}

.timeline-item-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.timeline-item-head span,
.timeline-item-head p,
.timeline-change-values span,
.timeline-change-empty {
  color: #678291;
  font-size: 12px;
}

.timeline-item-head strong {
  display: block;
  margin-top: 4px;
  color: #173042;
  font-size: 15px;
}

.timeline-item-head p {
  margin: 6px 0 0;
}

.timeline-change-list {
  display: grid;
  gap: 8px;
}

.timeline-change-item {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
}

.timeline-change-item strong {
  color: #173042;
  font-size: 13px;
}

.timeline-change-values {
  display: grid;
  gap: 4px;
}

@media (max-width: 720px) {
  .timeline-head,
  .timeline-item-head {
    display: grid;
    grid-template-columns: 1fr;
  }
}
</style>
