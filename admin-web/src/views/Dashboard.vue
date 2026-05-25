<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="4" v-for="card in statsCards" :key="card.label">
        <el-card shadow="never">
          <div class="stat-card">
            <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
            <div class="stat-label">{{ card.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 平台财务 -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>平台营收概览</template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="今日交易额">¥{{ finance.today_revenue }}</el-descriptions-item>
            <el-descriptions-item label="今日订单数">{{ finance.today_orders }} 单</el-descriptions-item>
            <el-descriptions-item label="平台抽成比例">{{ (finance.fee_rate * 100).toFixed(0) }}%</el-descriptions-item>
            <el-descriptions-item label="今日平台收入">¥{{ finance.today_platform_fee }}</el-descriptions-item>
            <el-descriptions-item label="本月交易额">¥{{ finance.month_revenue }}</el-descriptions-item>
            <el-descriptions-item label="本月平台收入">¥{{ finance.month_platform_fee }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>待处理事项</template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="待核验商家">
              <el-tag type="warning">{{ dashboard.pending_verify_merchants }} 个</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="进行中订单">
              <el-tag type="danger">{{ dashboard.pending_orders }} 单</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="已核验商家">{{ dashboard.verified_merchants }} 个</el-descriptions-item>
            <el-descriptions-item label="注册用户">{{ dashboard.total_users }} 人</el-descriptions-item>
            <el-descriptions-item label="注册骑手">{{ dashboard.total_riders }} 人</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import http from '../api'

const statsCards = ref([
  { label: '用户总数', value: 0, color: '#409EFF' },
  { label: '商家总数', value: 0, color: '#67C23A' },
  { label: '骑手总数', value: 0, color: '#E6A23C' },
  { label: '今日订单', value: 0, color: '#F56C6C' },
  { label: '今日交易额', value: '¥0', color: '#909399' },
  { label: '平台收入', value: '¥0', color: '#FF6B35' },
])

const finance = reactive({
  today_revenue: 0, today_orders: 0, today_platform_fee: 0,
  month_revenue: 0, month_platform_fee: 0, fee_rate: 0,
})

const dashboard = reactive({
  pending_verify_merchants: 0, pending_orders: 0,
  verified_merchants: 0, total_users: 0, total_riders: 0,
})

onMounted(async () => {
  try {
    const dash = await http.get('/admin/dashboard')
    statsCards.value[0].value = dash.total_users
    statsCards.value[1].value = dash.total_merchants
    statsCards.value[2].value = dash.total_riders
    statsCards.value[3].value = dash.today_orders
    statsCards.value[4].value = '¥' + dash.today_revenue
    statsCards.value[5].value = '¥' + dash.today_platform_fee
    Object.assign(dashboard, {
      pending_verify_merchants: dash.pending_verify_merchants,
      pending_orders: dash.pending_orders,
      verified_merchants: dash.verified_merchants,
      total_users: dash.total_users,
      total_riders: dash.total_riders,
    })
  } catch (e) { }

  try {
    const fin = await http.get('/admin/finance')
    Object.assign(finance, fin)
  } catch (e) { }
})
</script>

<style scoped>
.stat-card { text-align: center; padding: 10px 0; }
.stat-value { font-size: 28px; font-weight: bold; }
.stat-label { font-size: 13px; color: #999; margin-top: 6px; }
</style>
