<template>
  <div class="dashboard">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="welcome-content">
        <div class="welcome-text">
          <h2 class="welcome-greeting">下午好，管理员 👋</h2>
          <p class="welcome-sub">欢迎回到夜市管理后台，以下是平台的经营概况</p>
        </div>
        <div class="welcome-stats">
          <div class="welcome-stat-item">
            <span class="ws-value">{{ dashboard.verified_merchants }}</span>
            <span class="ws-label">家摊位已核验</span>
          </div>
          <div class="welcome-divider"></div>
          <div class="welcome-stat-item">
            <span class="ws-value">{{ dashboard.total_riders }}</span>
            <span class="ws-label">位骑手注册</span>
          </div>
          <div class="welcome-divider"></div>
          <div class="welcome-stat-item">
            <span class="ws-value">{{ dashboard.pending_orders }}</span>
            <span class="ws-label">笔进行中订单</span>
          </div>
        </div>
      </div>
      <div class="welcome-decoration">
        <div class="deco-circle c1"></div>
        <div class="deco-circle c2"></div>
        <div class="deco-circle c3"></div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stat-grid">
      <div
        v-for="card in visibleCards"
        :key="card.label"
        class="stat-card"
        :style="{ '--card-color': card.color, '--card-bg': card.bg }"
      >
        <div class="stat-card-icon">
          <span>{{ card.icon }}</span>
        </div>
        <div class="stat-card-info">
          <span class="stat-card-value">{{ card.value }}</span>
          <span class="stat-card-label">{{ card.label }}</span>
        </div>
        <div class="stat-card-spark"></div>
      </div>
    </div>

    <!-- 图表 + 待办 -->
    <div class="content-grid">
      <!-- 趋势图 -->
      <div class="content-main">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-hdr">
              <span class="card-hdr-title">📈 近 7 天订单趋势</span>
              <el-tag size="small" effect="plain" round type="info">实时</el-tag>
            </div>
          </template>
          <div ref="chartRef" class="chart-box"></div>
        </el-card>

        <!-- 营收 -->
        <el-card shadow="never" class="revenue-card">
          <template #header>
            <div class="card-hdr">
              <span class="card-hdr-title">💰 平台营收概览</span>
              <el-tag size="small" type="warning" effect="plain" round>
                抽成 {{ (finance.fee_rate * 100).toFixed(0) }}%
              </el-tag>
            </div>
          </template>
          <div class="revenue-grid">
            <div class="rev-item">
              <div class="rev-icon-wrap" style="background:#fff3e0"><span>📦</span></div>
              <div class="rev-info">
                <span class="rev-value">{{ finance.today_orders }}</span>
                <span class="rev-label">今日订单数</span>
              </div>
            </div>
            <div class="rev-item">
              <div class="rev-icon-wrap" style="background:#fce4ec"><span>💵</span></div>
              <div class="rev-info">
                <span class="rev-value gold">¥{{ finance.today_revenue }}</span>
                <span class="rev-label">今日交易额</span>
              </div>
            </div>
            <div class="rev-item">
              <div class="rev-icon-wrap" style="background:#ede7f6"><span>🏦</span></div>
              <div class="rev-info">
                <span class="rev-value purple">¥{{ finance.today_platform_fee }}</span>
                <span class="rev-label">今日平台收入</span>
              </div>
            </div>
            <div class="rev-item">
              <div class="rev-icon-wrap" style="background:#e8f5e9"><span>📊</span></div>
              <div class="rev-info">
                <span class="rev-value gold">¥{{ finance.month_revenue }}</span>
                <span class="rev-label">本月交易额</span>
              </div>
            </div>
            <div class="rev-item">
              <div class="rev-icon-wrap" style="background:#e3f2fd"><span>🎯</span></div>
              <div class="rev-info">
                <span class="rev-value purple">¥{{ finance.month_platform_fee }}</span>
                <span class="rev-label">本月平台收入</span>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 待处理 -->
      <div class="content-side">
        <el-card shadow="never" class="pending-card">
          <template #header>
            <div class="card-hdr">
              <span class="card-hdr-title">⏳ 待处理事项</span>
            </div>
          </template>
          <div class="pending-items">
            <div class="p-item p-warning">
              <div class="p-item-left">
                <div class="p-item-dot"></div>
                <span>待核验商家</span>
              </div>
              <span class="p-item-num">{{ dashboard.pending_verify_merchants }}</span>
            </div>
            <div class="p-item p-danger">
              <div class="p-item-left">
                <div class="p-item-dot"></div>
                <span>进行中订单</span>
              </div>
              <span class="p-item-num">{{ dashboard.pending_orders }}</span>
            </div>
            <div class="p-item p-primary">
              <div class="p-item-left">
                <div class="p-item-dot"></div>
                <span>待审核修改申请</span>
              </div>
              <span class="p-item-num">{{ dashboard.pending_modifications }}</span>
            </div>
          </div>
        </el-card>

        <el-card shadow="never" class="summary-card">
          <template #header>
            <div class="card-hdr">
              <span class="card-hdr-title">📋 平台概况</span>
            </div>
          </template>
          <div class="summary-list">
            <div class="s-row">
              <span>注册用户</span>
              <b>{{ dashboard.total_users }}</b>
            </div>
            <div class="s-row">
              <span>已核验摊位</span>
              <b class="green">{{ dashboard.verified_merchants }}</b>
            </div>
            <div class="s-row">
              <span>在线骑手</span>
              <b class="purple">{{ dashboard.total_riders }}</b>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import http from '../api'

const chartRef = ref(null)
let chartInst = null

const allCards = [
  { key: 'total_users',    label: '用户总数',   icon: '👤', value: 0, color: '#667eea', bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { key: 'total_merchants',label: '商家总数',   icon: '🏪', value: 0, color: '#00B894', bg: 'linear-gradient(135deg, #00B894 0%, #55efc4 100%)' },
  { key: 'total_riders',   label: '骑手总数',   icon: '🛵', value: 0, color: '#f39c12', bg: 'linear-gradient(135deg, #FDCB6E 0%, #e17055 100%)' },
  { key: 'today_orders',   label: '今日订单',   icon: '📋', value: 0, color: '#E17055', bg: 'linear-gradient(135deg, #E17055 0%, #d63031 100%)' },
  { key: 'today_revenue',  label: '今日交易额', icon: '💰', value: '¥0', color: '#6C5CE7', bg: 'linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%)' },
  { key: 'today_fee',      label: '平台收入',   icon: '📊', value: '¥0', color: '#0984e3', bg: 'linear-gradient(135deg, #74b9ff 0%, #0984e3 100%)' },
]
const visibleCards = computed(() => allCards)

const finance = reactive({
  today_revenue: 0, today_orders: 0, today_platform_fee: 0,
  month_revenue: 0, month_platform_fee: 0, fee_rate: 0,
})

const dashboard = reactive({
  pending_verify_merchants: 0, pending_orders: 0, pending_modifications: 0,
  verified_merchants: 0, total_users: 0, total_riders: 0,
})

async function loadDashboard() {
  try {
    const d = await http.get('/admin/dashboard')
    allCards[0].value = d.total_users ?? 0
    allCards[1].value = d.total_merchants ?? 0
    allCards[2].value = d.total_riders ?? 0
    allCards[3].value = d.today_orders ?? 0
    allCards[4].value = '¥' + (d.today_revenue ?? 0)
    allCards[5].value = '¥' + (d.today_platform_fee ?? 0)
    Object.assign(dashboard, {
      pending_verify_merchants: d.pending_verify_merchants ?? d.pending_verify_stores ?? 0,
      pending_orders: d.pending_orders ?? 0,
      pending_modifications: d.pending_modifications ?? 0,
      verified_merchants: d.verified_merchants ?? d.verified_stores ?? 0,
      total_users: d.total_users ?? 0,
      total_riders: d.total_riders ?? 0,
    })
    Object.assign(finance, {
      today_revenue: d.today_revenue ?? 0,
      today_orders: d.today_orders ?? 0,
      today_platform_fee: d.today_platform_fee ?? 0,
    })
  } catch (e) { /* ignore */ }
}

async function loadFinance() {
  try {
    const f = await http.get('/admin/finance')
    finance.today_revenue = f.today_revenue ?? 0
    finance.today_orders = f.today_orders ?? 0
    finance.today_platform_fee = f.today_platform_fee ?? 0
    finance.month_revenue = f.month_revenue ?? 0
    finance.month_platform_fee = f.month_platform_fee ?? 0
    finance.fee_rate = f.fee_rate ?? 0
  } catch (e) { /* ignore */ }
}

async function loadChart() {
  try {
    const stats = await http.get('/admin/orders/stats', { params: { days: 7 } })
    await nextTick()
    if (!chartRef.value) return
    if (chartInst) chartInst.dispose()
    chartInst = echarts.init(chartRef.value)

    const dates = stats.map(s => s.date.slice(5))
    const counts = stats.map(s => s.count)
    const revenues = stats.map(s => s.revenue)

    chartInst.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#fff',
        borderColor: '#eee',
        textStyle: { color: '#333', fontSize: 13 },
        boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
      },
      legend: {
        data: ['订单数', '交易额'],
        bottom: 0,
        textStyle: { color: '#999', fontSize: 12 },
        itemWidth: 12,
        itemHeight: 8,
        itemGap: 20,
      },
      grid: { left: 16, right: 40, top: 16, bottom: 40 },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#e8e8e8' } },
        axisTick: { show: false },
        axisLabel: { color: '#999', fontSize: 12 },
      },
      yAxis: [
        {
          type: 'value', name: '单',
          nameTextStyle: { color: '#999', fontSize: 11 },
          axisLabel: { color: '#999', fontSize: 11 },
          splitLine: { lineStyle: { color: '#f5f5f5', type: 'dashed' } },
        },
        {
          type: 'value', name: '元',
          nameTextStyle: { color: '#999', fontSize: 11 },
          axisLabel: { color: '#999', fontSize: 11 },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: '订单数', type: 'bar',
          data: counts,
          barWidth: 32,
          itemStyle: {
            borderRadius: [8, 8, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#A29BFE' },
              { offset: 1, color: '#6C5CE7' },
            ]),
          },
          emphasis: {
            itemStyle: { color: '#6C5CE7' },
          },
        },
        {
          name: '交易额', type: 'line',
          yAxisIndex: 1,
          data: revenues,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          showSymbol: false,
          lineStyle: { color: '#E17055', width: 3 },
          itemStyle: { color: '#E17055', borderColor: '#fff', borderWidth: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(225,112,85,0.25)' },
              { offset: 1, color: 'rgba(225,112,85,0.0)' },
            ]),
          },
        },
      ],
    })
  } catch (e) { /* ignore */ }
}

function onResize() {
  chartInst?.resize()
}

onMounted(() => {
  loadDashboard()
  loadFinance()
  loadChart()
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chartInst?.dispose()
})
</script>

<style scoped>
.dashboard { animation: fadeUp 0.4s ease; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }

/* ====== 欢迎横幅 ====== */
.welcome-banner {
  position: relative;
  background: linear-gradient(135deg, #1a1940 0%, #2d2b6b 50%, #3d3b9b 100%);
  border-radius: 16px;
  padding: 28px 32px;
  margin-bottom: 24px;
  overflow: hidden;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.welcome-content { position: relative; z-index: 1; }
.welcome-greeting { color: #fff; font-size: 22px; font-weight: 700; margin: 0 0 6px; }
.welcome-sub { color: rgba(255,255,255,0.55); font-size: 13px; margin: 0; }
.welcome-stats { display: flex; align-items: center; gap: 20px; margin-top: 18px; }
.welcome-stat-item { display: flex; flex-direction: column; }
.ws-value { color: #fff; font-size: 24px; font-weight: 800; }
.ws-label { color: rgba(255,255,255,0.55); font-size: 12px; margin-top: 2px; }
.welcome-divider { width: 1px; height: 36px; background: rgba(255,255,255,0.15); }
.welcome-decoration { position: absolute; right: -40px; top: -40px; }
.deco-circle {
  position: absolute; border-radius: 50%;
  background: rgba(255,255,255,0.04);
}
.deco-circle.c1 { width: 200px; height: 200px; right: 0; top: 0; }
.deco-circle.c2 { width: 140px; height: 140px; right: 80px; top: -20px; }
.deco-circle.c3 { width: 100px; height: 100px; right: 40px; top: 60px; }

/* ====== 统计卡片网格 ====== */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 18px;
  margin-bottom: 24px;
}
.stat-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: default;
  position: relative;
  overflow: hidden;
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.10);
}
.stat-card-spark {
  position: absolute;
  right: -20px; bottom: -20px;
  width: 80px; height: 80px;
  border-radius: 50%;
  background: var(--card-bg);
  opacity: 0.08;
}
.stat-card-icon {
  width: 52px; height: 52px;
  border-radius: 14px;
  background: var(--card-bg);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  font-size: 28px;
}
.stat-card-info { display: flex; flex-direction: column; z-index: 1; }
.stat-card-value {
  font-size: 26px; font-weight: 800;
  color: #2d3436; line-height: 1.2;
}
.stat-card-label { font-size: 13px; color: #999; margin-top: 2px; }

/* ====== 内容网格 ====== */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 24px;
}
.content-main { display: flex; flex-direction: column; gap: 24px; }
.content-side { display: flex; flex-direction: column; gap: 24px; }

/* ====== 卡片头部 ====== */
.card-hdr { display: flex; justify-content: space-between; align-items: center; }
.card-hdr-title { font-size: 15px; font-weight: 600; color: #333; }

/* ====== 图表 ====== */
.chart-card { overflow: visible; }
.chart-box { height: 340px; }

/* ====== 营收网格 ====== */
.revenue-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}
.rev-item {
  text-align: center;
  padding: 20px 10px;
  border-radius: 14px;
  transition: all 0.2s;
}
.rev-item:hover { background: #f8f9ff; }
.rev-icon-wrap {
  width: 40px; height: 40px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 10px;
  font-size: 18px;
}
.rev-info { display: flex; flex-direction: column; }
.rev-value { font-size: 20px; font-weight: 700; color: #333; }
.rev-value.gold { color: #E17055; }
.rev-value.purple { color: #6C5CE7; }
.rev-label { font-size: 12px; color: #999; margin-top: 2px; }

/* ====== 待处理 ====== */
.pending-items { display: flex; flex-direction: column; gap: 12px; }
.p-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 18px;
  border-radius: 12px;
  background: #f8f9fa;
  transition: background 0.2s;
}
.p-item:hover { background: #f0f2f5; }
.p-item-left { display: flex; align-items: center; gap: 10px; font-size: 14px; color: #555; }
.p-item-dot { width: 8px; height: 8px; border-radius: 50%; }
.p-item-num { font-size: 22px; font-weight: 800; }
.p-warning .p-item-dot { background: #E17055; }
.p-warning .p-item-num { color: #E17055; }
.p-danger .p-item-dot { background: #d63031; }
.p-danger .p-item-num { color: #d63031; }
.p-primary .p-item-dot { background: #6C5CE7; }
.p-primary .p-item-num { color: #6C5CE7; }

/* ====== 平台概况 ====== */
.summary-list { display: flex; flex-direction: column; gap: 14px; }
.s-row {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 14px; color: #666;
}
.s-row b { font-size: 16px; color: #333; }
.s-row b.green { color: #00B894; }
.s-row b.purple { color: #6C5CE7; }

/* ====== 移动端 ====== */
@media (max-width: 767px) {
  .welcome-banner {
    flex-direction: column;
    padding: 20px;
    gap: 16px;
  }
  .welcome-greeting { font-size: 17px; }
  .welcome-stats { gap: 14px; margin-top: 12px; flex-wrap: wrap; }
  .ws-value { font-size: 20px; }
  .welcome-divider { display: none; }
  .welcome-decoration { display: none; }

  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  .stat-card { padding: 16px 14px; gap: 10px; border-radius: 12px; }
  .stat-card-icon { width: 40px; height: 40px; border-radius: 10px; font-size: 22px; }
  .stat-card-value { font-size: 20px; }
  .stat-card-label { font-size: 11px; }

  .content-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  .chart-box { height: 240px; }

  .revenue-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }
  .rev-item { padding: 12px 6px; }
  .rev-value { font-size: 16px; }
  .rev-label { font-size: 10px; }
}
</style>
