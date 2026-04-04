<template>
  <section class="dashboard-board">
    <article class="dashboard-hero-card">
      <div class="dashboard-hero-copy">
        <p class="dashboard-kicker">Insight Dashboard</p>
        <h3>你的饮食执行驾驶舱</h3>
        <p>
          把最近 7 天、14 天、30 天的关键变化压到一页里。先看趋势，再看结构，再看目标和资产，避免只盯一个数字。
        </p>
      </div>
      <div class="dashboard-hero-chips">
        <div class="dashboard-chip">
          <span>当前提示</span>
          <strong>{{ dashboard.targets?.goal_hint || "保持均衡饮食" }}</strong>
        </div>
        <div class="dashboard-chip">
          <span>估算 BMI</span>
          <strong>{{ dashboard.targets?.bmi ? dashboard.targets.bmi.toFixed(1) : "待补资料" }}</strong>
        </div>
        <div class="dashboard-chip" :class="balanceScoreClass">
          <span>膳食均衡评分</span>
          <strong>{{ dashboard.targets?.balance_score != null ? dashboard.targets.balance_score + ' / 100' : '记录后可见' }}</strong>
        </div>
        <div class="dashboard-chip">
          <span>最新报表</span>
          <strong>{{ latestReportLabel }}</strong>
        </div>
      </div>
    </article>

    <div class="dashboard-kpi-grid">
      <article v-for="item in dashboard.headline_cards || []" :key="item.key" class="dashboard-kpi-card">
        <div class="dashboard-kpi-head">
          <span>{{ item.label }}</span>
          <strong>{{ item.progress }}%</strong>
        </div>
        <div class="dashboard-kpi-value">
          <strong>{{ formatMetric(item.value, item.unit) }}</strong>
          <small v-if="item.target">目标 {{ formatMetric(item.target, item.unit) }}</small>
        </div>
        <div class="dashboard-kpi-track">
          <div class="dashboard-kpi-fill" :class="`tone-${item.tone}`" :style="{ width: `${item.progress}%` }" />
        </div>
        <p>{{ item.caption }}</p>
      </article>
    </div>

    <div class="dashboard-main-grid">
      <article class="dashboard-panel dashboard-panel-wide">
        <div class="dashboard-panel-head">
          <div>
            <span class="panel-label">Nutrition Trend</span>
            <h4>近14天营养波动</h4>
            <p>鼠标移动到节点上可以看当天餐次、热量和三大营养素细节。</p>
          </div>
          <div class="dashboard-toggle-row">
            <button
              v-for="metric in trendMetrics"
              :key="metric.key"
              type="button"
              class="dashboard-toggle"
              :class="{ active: selectedTrendKey === metric.key }"
              @click="selectedTrendKey = metric.key"
            >
              {{ metric.label }}
            </button>
          </div>
        </div>

        <div v-if="lineChart.points.length" class="dashboard-chart-wrap">
          <svg viewBox="0 0 760 280" class="dashboard-line-chart">
            <g>
              <line
                v-for="tick in lineChart.gridLines"
                :key="tick.value"
                x1="68"
                :y1="tick.y"
                x2="728"
                :y2="tick.y"
                class="chart-grid-line"
              />
              <text
                v-for="tick in lineChart.gridLines"
                :key="`label-${tick.value}`"
                x="58"
                :y="tick.y + 4"
                class="chart-axis-label"
              >
                {{ tick.label }}
              </text>
            </g>

            <path :d="lineChart.areaPath" class="chart-area" :style="{ fill: activeTrend.color }" />
            <path :d="lineChart.path" class="chart-line" :style="{ stroke: activeTrend.color }" />

            <g>
              <circle
                v-for="point in lineChart.points"
                :key="point.point.date"
                :cx="point.x"
                :cy="point.y"
                r="5"
                class="chart-point"
                :style="{ fill: activeTrend.color }"
              />
              <rect
                v-for="point in lineChart.points"
                :key="`hit-${point.point.date}`"
                :x="point.hitX"
                y="24"
                :width="point.hitWidth"
                height="220"
                fill="transparent"
                @mousemove="showTooltip($event, point.point.label, trendTooltipLines(point.point))"
                @mouseleave="hideTooltip"
              />
            </g>

            <g>
              <text
                v-for="point in lineChart.points"
                :key="`x-${point.point.date}`"
                :x="point.x"
                y="264"
                class="chart-axis-label chart-axis-label-center"
              >
                {{ point.point.label }}
              </text>
            </g>
          </svg>
        </div>
        <div v-else class="dashboard-chart-empty">当前还没有足够记录形成趋势。</div>

        <div class="dashboard-panel-foot">
          <div class="dashboard-foot-stat">
            <span>近14天累计</span>
            <strong>{{ formatMetric(sumByKey(trendRows, activeTrend.key), activeTrend.unit) }}</strong>
          </div>
          <div class="dashboard-foot-stat">
            <span>近14天活跃</span>
            <strong>{{ dashboard.period_overview?.fortnight?.active_days || 0 }} 天</strong>
          </div>
          <div class="dashboard-foot-stat">
            <span>菜谱带入率</span>
            <strong>{{ dashboard.period_overview?.week?.recipe_link_rate || 0 }}%</strong>
          </div>
        </div>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel-head">
          <div>
            <span class="panel-label">Meal Split</span>
            <h4>餐次分布</h4>
            <p>看最近一段时间最常记录的是哪一餐，哪一餐最容易漏。</p>
          </div>
        </div>

        <div v-if="mealSegments.length" class="dashboard-donut-wrap">
          <svg viewBox="0 0 240 240" class="dashboard-donut-chart">
            <g transform="translate(120 120)">
              <circle r="74" class="chart-donut-track" />
              <path
                v-for="segment in mealSegments"
                :key="segment.key"
                :d="segment.path"
                class="chart-donut-segment"
                :style="{ stroke: segment.color }"
                @mousemove="showTooltip($event, segment.label, [segment.value + ' 餐', `占比 ${segment.percentage}%`])"
                @mouseleave="hideTooltip"
              />
              <circle r="48" class="chart-donut-hole" />
              <text class="chart-donut-total" text-anchor="middle" y="-4">{{ mealTotal }}</text>
              <text class="chart-donut-caption" text-anchor="middle" y="18">总餐次</text>
            </g>
          </svg>
          <div class="dashboard-legend">
            <button
              v-for="segment in mealSegments"
              :key="segment.key"
              type="button"
              class="dashboard-legend-item"
              @mousemove="showTooltip($event, segment.label, [segment.value + ' 餐', `占比 ${segment.percentage}%`])"
              @mouseleave="hideTooltip"
            >
              <span class="legend-color" :style="{ background: segment.color }" />
              <span>{{ segment.label }}</span>
              <strong>{{ segment.percentage }}%</strong>
            </button>
          </div>
        </div>
        <div v-else class="dashboard-chart-empty">当前还没有足够餐次形成分布。</div>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel-head">
          <div>
            <span class="panel-label">Macro Mix</span>
            <h4>三大营养素结构</h4>
            <p>看近14天能量结构更偏向哪一类营养素。</p>
          </div>
        </div>

        <div v-if="macroSegments.length" class="dashboard-stack-card">
          <div class="dashboard-stack-bar">
            <button
              v-for="segment in macroSegments"
              :key="segment.key"
              type="button"
              class="dashboard-stack-segment"
              :style="{ width: `${Math.max(segment.percentage, 8)}%`, background: segment.color }"
              @mousemove="showTooltip($event, segment.label, [formatMetric(segment.value, 'g'), `占比 ${segment.percentage}%`])"
              @mouseleave="hideTooltip"
            />
          </div>
          <div class="dashboard-legend dashboard-legend-column">
            <button
              v-for="segment in macroSegments"
              :key="`macro-${segment.key}`"
              type="button"
              class="dashboard-legend-item"
              @mousemove="showTooltip($event, segment.label, [formatMetric(segment.value, 'g'), `占比 ${segment.percentage}%`])"
              @mouseleave="hideTooltip"
            >
              <span class="legend-color" :style="{ background: segment.color }" />
              <span>{{ segment.label }}</span>
              <strong>{{ formatMetric(segment.value, "g") }}</strong>
            </button>
          </div>
        </div>
        <div v-else class="dashboard-chart-empty">当前还没有足够营养数据形成结构图。</div>

        <div class="dashboard-subsection">
          <div class="dashboard-subsection-head">
            <strong>餐次完成度</strong>
            <span>按近7天完成情况</span>
          </div>
          <div class="dashboard-completion-list">
            <button
              v-for="item in mealCompletion"
              :key="item.key"
              type="button"
              class="dashboard-completion-item"
              @mousemove="showTooltip($event, item.label, [`${item.value}/${item.expected} 次`, `完成度 ${item.percentage}%`])"
              @mouseleave="hideTooltip"
            >
              <div class="dashboard-completion-meta">
                <span>{{ item.label }}</span>
                <strong>{{ item.percentage }}%</strong>
              </div>
              <div class="dashboard-completion-track">
                <div class="dashboard-completion-fill" :style="{ width: `${item.percentage}%`, background: item.color }" />
              </div>
            </button>
          </div>
        </div>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel-head">
          <div>
            <span class="panel-label">Weekday Pattern</span>
            <h4>周内节奏</h4>
            <p>观察一周里哪几天最容易偏高、偏低或中断。</p>
          </div>
        </div>

        <div v-if="weekdayBars.length" class="dashboard-chart-wrap compact">
          <svg viewBox="0 0 360 250" class="dashboard-bar-chart">
            <line
              v-for="tick in weekdayChart.gridLines"
              :key="tick.value"
              x1="40"
              :y1="tick.y"
              x2="332"
              :y2="tick.y"
              class="chart-grid-line"
            />
            <g v-for="bar in weekdayBars" :key="bar.label">
              <rect
                :x="bar.x"
                :y="bar.y"
                :width="bar.width"
                :height="bar.height"
                rx="12"
                class="chart-bar"
                @mousemove="showTooltip($event, bar.label, weekdayTooltipLines(bar.raw))"
                @mouseleave="hideTooltip"
              />
              <text :x="bar.x + bar.width / 2" y="228" class="chart-axis-label chart-axis-label-center">{{ bar.label }}</text>
            </g>
          </svg>
        </div>
        <div v-else class="dashboard-chart-empty">当前还没有形成明显的周内模式。</div>
      </article>
    </div>

    <div class="dashboard-bottom-grid">
      <article class="dashboard-panel dashboard-panel-wide">
        <div class="dashboard-panel-head">
          <div>
            <span class="panel-label">Heatmap</span>
            <h4>近30天记录热力图</h4>
            <p>快速判断哪些天完全断档、哪些天记录和摄入都更扎实。</p>
          </div>
        </div>

        <div v-if="heatmapRows.length" class="dashboard-heatmap">
          <button
            v-for="item in heatmapRows"
            :key="item.date"
            type="button"
            class="dashboard-heatmap-cell"
            :class="{ empty: !item.has_record }"
            :style="{ background: heatmapColor(item.intensity) }"
            @mousemove="showTooltip($event, `${item.label} ${item.weekday}`, heatmapTooltipLines(item))"
            @mouseleave="hideTooltip"
          >
            <span>{{ item.label.slice(-2) }}</span>
          </button>
        </div>
        <div v-else class="dashboard-chart-empty">当前还没有足够历史记录形成热力图。</div>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel-head">
          <div>
            <span class="panel-label">Goals</span>
            <h4>目标推进</h4>
            <p>把目标、当前值和最新进展压成更直观的进度环。</p>
          </div>
        </div>

        <div v-if="goalItems.length" class="dashboard-goals">
          <article v-for="goal in goalItems" :key="goal.id" class="dashboard-goal-card">
            <button
              type="button"
              class="dashboard-goal-ring"
              :style="{ background: goalRing(goal.progress_percentage) }"
              @mousemove="showTooltip($event, goal.label, goalTooltipLines(goal))"
              @mouseleave="hideTooltip"
            >
              <span>{{ goal.progress_percentage }}%</span>
            </button>
            <div class="dashboard-goal-copy">
              <strong>{{ goal.label }}</strong>
              <p>{{ goal.description || "当前目标正在推进中" }}</p>
              <small>当前 {{ goal.current_value }} / 目标 {{ goal.target_value }}</small>
            </div>
            <svg v-if="goal.progress_points?.length" viewBox="0 0 160 44" class="dashboard-goal-sparkline">
              <path :d="goalSparkline(goal.progress_points).path" class="goal-sparkline-line" />
              <circle
                v-for="point in goalSparkline(goal.progress_points).points"
                :key="`${goal.id}-${point.label}`"
                :cx="point.x"
                :cy="point.y"
                r="3.5"
                class="goal-sparkline-point"
                @mousemove="showTooltip($event, `${goal.label} ${point.label}`, [`进度 ${point.value}`, point.note || '无附加备注'])"
                @mouseleave="hideTooltip"
              />
            </svg>
          </article>
        </div>
        <div v-else class="dashboard-chart-empty">当前没有正在推进中的活跃目标。</div>
      </article>
    </div>

    <div class="dashboard-insight-grid">
      <article v-for="item in dashboard.insights || []" :key="item.title" class="dashboard-insight-card" :class="`tone-${item.tone}`">
        <span>{{ item.tone === 'success' ? 'Keep' : item.tone === 'accent' ? 'Structure' : 'Focus' }}</span>
        <strong>{{ item.title }}</strong>
        <p>{{ item.description }}</p>
      </article>
    </div>

    <div v-if="tooltip.visible" class="dashboard-tooltip" :style="tooltipStyle">
      <strong>{{ tooltip.title }}</strong>
      <p v-for="line in tooltip.lines" :key="line">{{ line }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";

const props = defineProps<{
  dashboard: Record<string, any>;
}>();

const selectedTrendKey = ref("energy");
const tooltip = reactive({
  visible: false,
  x: 0,
  y: 0,
  title: "",
  lines: [] as string[],
});

const trendMetrics = [
  { key: "energy", label: "热量", unit: "kcal", color: "#ff7e1b" },
  { key: "protein", label: "蛋白", unit: "g", color: "#3c7dff" },
  { key: "fat", label: "脂肪", unit: "g", color: "#ff4f79" },
  { key: "carbohydrate", label: "碳水", unit: "g", color: "#9d5cff" },
];

const activeTrend = computed(() => trendMetrics.find((item) => item.key === selectedTrendKey.value) ?? trendMetrics[0]);
const trendRows = computed(() => props.dashboard?.charts?.daily_nutrition_trend ?? []);
const rawMealSegments = computed(() => props.dashboard?.charts?.meal_distribution ?? []);
const macroSegments = computed(() => props.dashboard?.charts?.macro_distribution ?? []);
const heatmapRows = computed(() => props.dashboard?.charts?.activity_heatmap ?? []);
const mealCompletion = computed(() => props.dashboard?.charts?.meal_completion ?? []);
const goalItems = computed(() => props.dashboard?.goals ?? []);

const latestReportLabel = computed(() => {
  const assets = props.dashboard?.report_assets ?? {};
  if (assets.latest_completed_report_type === "monthly") return "最新是月报";
  if (assets.latest_completed_report_type === "weekly") return "最新是周报";
  return "尚未沉淀";
});

const balanceScoreClass = computed(() => {
  const score = props.dashboard?.targets?.balance_score;
  if (score == null) return "";
  if (score >= 80) return "chip-good";
  if (score >= 60) return "chip-ok";
  if (score >= 40) return "chip-warn";
  return "chip-bad";
});

const mealTotal = computed(() => rawMealSegments.value.reduce((sum: number, item: Record<string, any>) => sum + Number(item.value || 0), 0));

const lineChart = computed(() => {
  const width = 760;
  const height = 280;
  const left = 68;
  const right = 32;
  const top = 24;
  const bottom = 36;
  const chartWidth = width - left - right;
  const chartHeight = 208;
  const values = trendRows.value.map((item: Record<string, any>) => Number(item[activeTrend.value.key] || 0));
  const maxValue = Math.max(...values, 1);
  const points = trendRows.value.map((item: Record<string, any>, index: number) => {
    const x = left + (chartWidth * index) / Math.max(trendRows.value.length - 1, 1);
    const y = top + chartHeight - (Number(item[activeTrend.value.key] || 0) / maxValue) * chartHeight;
    const segmentWidth = chartWidth / Math.max(trendRows.value.length, 1);
    return {
      x,
      y,
      point: item,
      hitX: index === 0 ? left : x - segmentWidth / 2,
      hitWidth: segmentWidth,
    };
  });
  const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
  const areaPath = points.length
    ? `${path} L ${points[points.length - 1].x} ${top + chartHeight} L ${points[0].x} ${top + chartHeight} Z`
    : "";
  const gridLines = Array.from({ length: 4 }).map((_, index) => {
    const value = Math.round((maxValue / 3) * index);
    const y = top + chartHeight - (value / maxValue) * chartHeight;
    return { value, y, label: `${value}` };
  });
  return { points, path, areaPath, gridLines };
});

const weekdayChart = computed(() => {
  const rows = props.dashboard?.charts?.weekday_pattern ?? [];
  const width = 360;
  const height = 250;
  const left = 40;
  const bottom = 36;
  const chartHeight = 170;
  const maxEnergy = Math.max(...rows.map((item: Record<string, any>) => Number(item.energy || 0)), 1);
  const barWidth = 28;
  const gap = 14;
  const bars = rows.map((item: Record<string, any>, index: number) => {
    const x = left + index * (barWidth + gap);
    const barHeight = (Number(item.energy || 0) / maxEnergy) * chartHeight;
    return {
      x,
      y: height - bottom - barHeight,
      width: barWidth,
      height: barHeight,
      label: item.label,
      raw: item,
    };
  });
  const gridLines = Array.from({ length: 4 }).map((_, index) => {
    const value = Math.round((maxEnergy / 3) * index);
    const y = height - bottom - (value / maxEnergy) * chartHeight;
    return { value, y };
  });
  return { bars, gridLines };
});

const weekdayBars = computed(() => weekdayChart.value.bars);

const tooltipStyle = computed(() => ({
  left: `${tooltip.x + 14}px`,
  top: `${tooltip.y + 14}px`,
}));

function formatMetric(value: number | string, unit = "") {
  if (value == null || value === "") {
    return unit ? `0 ${unit}` : "0";
  }
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return String(value);
  }
  if (unit === "kcal" || Number.isInteger(numeric)) {
    return `${Math.round(numeric)}${unit ? ` ${unit}` : ""}`;
  }
  return `${numeric.toFixed(1)}${unit ? ` ${unit}` : ""}`;
}

function sumByKey(items: Array<Record<string, any>>, key: string) {
  return items.reduce((sum, item) => sum + Number(item[key] || 0), 0);
}

function showTooltip(event: MouseEvent, title: string, lines: string[]) {
  tooltip.visible = true;
  tooltip.x = event.clientX;
  tooltip.y = event.clientY;
  tooltip.title = title;
  tooltip.lines = lines;
}

function hideTooltip() {
  tooltip.visible = false;
}

function trendTooltipLines(point: Record<string, any>) {
  return [
    `${formatMetric(point.energy, "kcal")} 热量`,
    `${formatMetric(point.protein, "g")} 蛋白`,
    `${formatMetric(point.fat, "g")} 脂肪`,
    `${formatMetric(point.carbohydrate, "g")} 碳水`,
    `${point.meals || 0} 餐记录`,
  ];
}

function weekdayTooltipLines(point: Record<string, any>) {
  return [
    `${formatMetric(point.energy, "kcal")} 热量`,
    `${formatMetric(point.protein, "g")} 蛋白`,
    `${point.meals || 0} 餐`,
    `${point.active_days || 0} 个活跃日`,
  ];
}

function heatmapTooltipLines(item: Record<string, any>) {
  if (!item.has_record) {
    return ["当天没有记录", "建议至少补一餐，趋势才会更真实"];
  }
  return [
    `${formatMetric(item.energy, "kcal")} 热量`,
    `${formatMetric(item.protein, "g")} 蛋白`,
    `${item.meals || 0} 餐记录`,
  ];
}

function goalTooltipLines(goal: Record<string, any>) {
  return [
    `当前 ${goal.current_value}`,
    `目标 ${goal.target_value}`,
    goal.target_date ? `目标日期 ${goal.target_date}` : "未设置目标日期",
  ];
}

function heatmapColor(intensity: number) {
  if (!intensity) {
    return "rgba(23, 48, 66, 0.06)";
  }
  const alpha = 0.18 + Math.min(intensity, 100) / 100 * 0.68;
  return `rgba(93, 92, 255, ${alpha})`;
}

function goalRing(percentage: number) {
  return `conic-gradient(#8a5bff 0deg, #8a5bff ${percentage * 3.6}deg, rgba(23, 48, 66, 0.08) ${percentage * 3.6}deg, rgba(23, 48, 66, 0.08) 360deg)`;
}

function polarToCartesian(centerX: number, centerY: number, radius: number, angle: number) {
  const radians = (angle - 90) * (Math.PI / 180);
  return {
    x: centerX + radius * Math.cos(radians),
    y: centerY + radius * Math.sin(radians),
  };
}

function describeArc(startAngle: number, endAngle: number, radius: number) {
  const start = polarToCartesian(0, 0, radius, endAngle);
  const end = polarToCartesian(0, 0, radius, startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
  return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
}

const mealSegmentsComputed = computed(() => {
  let currentAngle = 0;
  return rawMealSegments.value
    .filter((item: Record<string, any>) => Number(item.value || 0) > 0)
    .map((item: Record<string, any>) => {
      const sweep = (Number(item.percentage || 0) / 100) * 360;
      const path = describeArc(currentAngle, currentAngle + sweep, 74);
      currentAngle += sweep;
      return { ...item, path };
    });
});

const mealSegments = mealSegmentsComputed;

function goalSparkline(points: Array<Record<string, any>>) {
  const width = 160;
  const height = 44;
  const chartWidth = 144;
  const values = points.map((item) => Number(item.value || 0));
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const rows = points.map((item, index) => {
    const x = 8 + (chartWidth * index) / Math.max(points.length - 1, 1);
    const y = height - 8 - ((Number(item.value || 0) - min) / Math.max(max - min, 1)) * 28;
    return { x, y, value: item.value, label: item.label, note: item.note };
  });
  const path = rows.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
  return { path, points: rows };
}
</script>

<style scoped>
.dashboard-board {
  display: grid;
  gap: 16px;
}

.dashboard-hero-card,
.dashboard-kpi-card,
.dashboard-panel,
.dashboard-insight-card {
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 48px rgba(15, 30, 39, 0.08);
}

.dashboard-hero-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
  background:
    radial-gradient(circle at top right, rgba(255, 184, 108, 0.18), transparent 26%),
    linear-gradient(135deg, rgba(247, 251, 255, 0.98), rgba(238, 246, 251, 0.96));
}

.dashboard-kicker,
.panel-label {
  margin: 0;
  font-size: 12px;
  color: #4e7384;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.dashboard-hero-copy h3,
.dashboard-panel h4 {
  margin: 6px 0 0;
}

.dashboard-hero-copy p,
.dashboard-panel-head p,
.dashboard-kpi-card p,
.dashboard-insight-card p,
.dashboard-goal-copy p,
.dashboard-chart-empty {
  margin: 8px 0 0;
  color: #4d6a79;
  line-height: 1.55;
  font-size: 13px;
}

.dashboard-hero-chips {
  display: grid;
  gap: 8px;
  min-width: 200px;
}

.dashboard-chip {
  padding: 10px 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(16, 34, 42, 0.08);
}

.dashboard-chip span,
.dashboard-kpi-head span,
.dashboard-kpi-value small,
.dashboard-foot-stat span,
.dashboard-subsection-head span,
.dashboard-goal-copy small,
.dashboard-insight-card span {
  display: block;
}

.dashboard-chip span,
.dashboard-kpi-head span,
.dashboard-foot-stat span,
.dashboard-goal-copy small {
  font-size: 12px;
  color: #5a7a8a;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.dashboard-chip strong {
  display: block;
  margin-top: 6px;
  font-size: 16px;
}

.dashboard-chip.chip-good { border-color: #22c55e; }
.dashboard-chip.chip-good strong { color: #16a34a; }
.dashboard-chip.chip-ok  { border-color: #3b82f6; }
.dashboard-chip.chip-ok  strong { color: #2563eb; }
.dashboard-chip.chip-warn { border-color: #f59e0b; }
.dashboard-chip.chip-warn strong { color: #d97706; }
.dashboard-chip.chip-bad { border-color: #ef4444; }
.dashboard-chip.chip-bad strong { color: #dc2626; }

.dashboard-kpi-grid,
.dashboard-main-grid,
.dashboard-bottom-grid,
.dashboard-insight-grid {
  display: grid;
  gap: 18px;
}

.dashboard-kpi-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.dashboard-main-grid,
.dashboard-bottom-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.dashboard-insight-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.dashboard-panel-wide {
  grid-column: span 2;
}

.dashboard-kpi-head,
.dashboard-kpi-value,
.dashboard-panel-head,
.dashboard-foot-stat,
.dashboard-subsection-head,
.dashboard-completion-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.dashboard-kpi-head strong {
  color: #4b84ff;
  font-size: 14px;
}

.dashboard-kpi-value {
  margin-top: 10px;
  align-items: flex-end;
}

.dashboard-kpi-value strong {
  font-size: 28px;
}

.dashboard-kpi-value small {
  color: #698592;
}

.dashboard-kpi-track,
.dashboard-completion-track {
  margin-top: 14px;
  height: 8px;
  border-radius: 999px;
  background: rgba(16, 34, 42, 0.08);
  overflow: hidden;
}

.dashboard-kpi-fill,
.dashboard-completion-fill {
  height: 100%;
  border-radius: inherit;
}

.tone-warm {
  background: linear-gradient(90deg, #ff8a1c, #ffb366);
}

.tone-primary {
  background: linear-gradient(90deg, #3c7dff, #6a9cff);
}

.tone-success {
  background: linear-gradient(90deg, #23c06d, #68dc9f);
}

.tone-accent {
  background: linear-gradient(90deg, #8a5bff, #be97ff);
}

.dashboard-toggle-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.dashboard-toggle,
.dashboard-legend-item,
.dashboard-completion-item,
.dashboard-heatmap-cell,
.dashboard-goal-ring {
  border: 0;
  cursor: pointer;
}

.dashboard-toggle {
  padding: 9px 12px;
  border-radius: 999px;
  background: rgba(16, 34, 42, 0.06);
  color: #345464;
  font-weight: 700;
}

.dashboard-toggle.active {
  background: #173042;
  color: #fff;
}

.dashboard-chart-wrap {
  margin-top: 16px;
  overflow-x: auto;
}

.dashboard-chart-wrap.compact {
  overflow: hidden;
}

.dashboard-line-chart,
.dashboard-bar-chart,
.dashboard-donut-chart,
.dashboard-goal-sparkline {
  width: 100%;
  display: block;
}

.chart-grid-line {
  stroke: rgba(16, 34, 42, 0.08);
  stroke-width: 1;
}

.chart-axis-label {
  fill: #6a8391;
  font-size: 11px;
}

.chart-axis-label-center {
  text-anchor: middle;
}

.chart-area {
  fill-opacity: 0.14;
}

.chart-line {
  fill: none;
  stroke-width: 3.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.chart-point,
.goal-sparkline-point {
  stroke: #fff;
  stroke-width: 2;
}

.chart-donut-track {
  fill: none;
  stroke: rgba(16, 34, 42, 0.08);
  stroke-width: 22;
}

.chart-donut-segment {
  fill: none;
  stroke-width: 22;
  stroke-linecap: butt;
}

.chart-donut-hole {
  fill: rgba(255, 255, 255, 0.96);
}

.chart-donut-total,
.chart-donut-caption {
  fill: #173042;
}

.chart-donut-total {
  font-size: 28px;
  font-weight: 800;
}

.chart-donut-caption {
  font-size: 12px;
  fill: #6a8391;
}

.chart-bar {
  fill: #b18bff;
  stroke: rgba(255, 255, 255, 0.4);
}

.dashboard-donut-wrap {
  display: grid;
  gap: 12px;
  margin-top: 12px;
}

.dashboard-legend {
  display: grid;
  gap: 8px;
}

.dashboard-legend-column {
  margin-top: 12px;
}

.dashboard-legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border-radius: 16px;
  background: rgba(247, 251, 255, 0.92);
  text-align: left;
}

.dashboard-legend-item strong {
  margin-left: auto;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 999px;
}

.dashboard-panel-foot {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.dashboard-foot-stat {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.dashboard-foot-stat strong,
.dashboard-subsection-head strong,
.dashboard-goal-copy strong,
.dashboard-insight-card strong {
  font-size: 18px;
}

.dashboard-stack-card,
.dashboard-subsection {
  margin-top: 14px;
}

.dashboard-stack-bar {
  display: flex;
  overflow: hidden;
  height: 26px;
  border-radius: 999px;
  background: rgba(16, 34, 42, 0.06);
}

.dashboard-stack-segment {
  height: 100%;
}

.dashboard-completion-list,
.dashboard-goals {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.dashboard-completion-item {
  width: 100%;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(247, 251, 255, 0.92);
  text-align: left;
}

.dashboard-heatmap {
  display: grid;
  grid-template-columns: repeat(10, minmax(0, 1fr));
  gap: 8px;
  margin-top: 14px;
}

.dashboard-heatmap-cell {
  aspect-ratio: 1 / 1;
  border-radius: 14px;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.dashboard-heatmap-cell.empty {
  color: rgba(16, 34, 42, 0.46);
}

.dashboard-goal-card {
  padding: 14px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.dashboard-goal-ring {
  width: 84px;
  height: 84px;
  padding: 6px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.dashboard-goal-ring::before {
  content: "";
  position: absolute;
  inset: 10px;
  border-radius: inherit;
  background: #fff;
}

.dashboard-goal-ring span {
  position: relative;
  z-index: 1;
  font-weight: 800;
  color: #6531ff;
}

.dashboard-goal-copy {
  margin-top: 12px;
}

.dashboard-goal-sparkline {
  margin-top: 12px;
}

.goal-sparkline-line {
  fill: none;
  stroke: #9d5cff;
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.dashboard-insight-card.tone-primary {
  background: rgba(241, 247, 255, 0.96);
}

.dashboard-insight-card.tone-accent {
  background: rgba(246, 241, 255, 0.96);
}

.dashboard-insight-card.tone-success {
  background: rgba(241, 252, 247, 0.96);
}

.dashboard-tooltip {
  position: fixed;
  z-index: 3000;
  max-width: 260px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(15, 26, 34, 0.94);
  color: #f7fcff;
  box-shadow: 0 18px 40px rgba(15, 30, 39, 0.22);
  pointer-events: none;
}

.dashboard-tooltip strong {
  display: block;
  font-size: 14px;
}

.dashboard-tooltip p {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: rgba(247, 252, 255, 0.78);
}

@media (max-width: 1100px) {
  .dashboard-kpi-grid,
  .dashboard-main-grid,
  .dashboard-bottom-grid,
  .dashboard-insight-grid {
    grid-template-columns: 1fr;
  }

  .dashboard-panel-wide {
    grid-column: auto;
  }
}

@media (max-width: 760px) {
  .dashboard-hero-card,
  .dashboard-panel-head,
  .dashboard-kpi-head,
  .dashboard-kpi-value,
  .dashboard-panel-foot {
    grid-template-columns: 1fr;
    flex-direction: column;
  }

  .dashboard-hero-card {
    flex-direction: column;
  }

  .dashboard-hero-chips {
    width: 100%;
    min-width: 0;
  }

  .dashboard-panel-foot {
    display: grid;
  }

  .dashboard-heatmap {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }
}
</style>
