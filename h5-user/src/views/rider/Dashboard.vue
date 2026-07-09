<template>
  <div class="page">
    <div class="top-bar">
      <h2>🛵 骑手中心</h2>
      <van-button size="small" plain type="primary" @click="doLogout">退出</van-button>
    </div>

    <!-- 统计 -->
    <div class="stats">
      <div class="stat-item" @click="goMyOrders">
        <div class="stat-num" style="color:#1989fa">{{ myCount }}</div>
        <div class="stat-label">我的配送</div>
      </div>
      <div class="stat-item">
        <div class="stat-num" style="color:#07c160">¥{{ todayEarnings }}</div>
        <div class="stat-label">今日收入</div>
      </div>
    </div>

    <!-- 可抢订单 -->
    <van-cell-group inset title="可接订单">
      <van-cell v-for="o in availableOrders" :key="o.id"
        :title="`#${o.id} ${o.store_names || ''}`"
        :label="`¥${o.total_price} · ${o.address_snapshot?.address || ''}`"
        is-link @click="goDetail(o.id)">
        <template #right-icon><van-tag type="danger" size="small">可接</van-tag></template>
      </van-cell>
      <van-cell v-if="!availableOrders.length" title="暂无可接订单" label="下拉刷新试试" />
    </van-cell-group>

    <div class="actions">
      <van-button round block type="primary" @click="goMyOrders">📋 查看我的订单</van-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { riderApi } from '../../utils/api.js'

const myCount = ref(0)
const todayEarnings = ref(0)
const availableOrders = ref([])

const load = async () => {
  try {
    // 获取可接订单
    const res1 = await riderApi.get('/api/rider/orders/available', { page_size: 10 })
    availableOrders.value = res1.items || []
    // 获取我的订单
    const res2 = await riderApi.get('/api/rider/orders', { status: 'delivering,completed', page_size: 20 })
    myCount.value = res2.total || 0
    // 估算今日收入
    const today = new Date().toISOString().slice(0, 10)
    const completed = (res2.items || []).filter(o => o.completed_at && o.completed_at.startsWith(today))
    todayEarnings.value = completed.reduce((sum, o) => sum + (o.delivery_fee || 0), 0)
  } catch {}
}

const goDetail = (id) => { window.location.hash = `#/r/order/${id}` }
const goMyOrders = () => { window.location.hash = '#/r/orders' }
const doLogout = () => {
  localStorage.removeItem('rider_token')
  window.location.hash = '#/r/login'
}

onMounted(load)
</script>

<style scoped>
.page { min-height: 100vh; background: #f7f8fa; }
.top-bar { display: flex; justify-content: space-between; align-items: center; padding: 16px; background: #fff; }
.top-bar h2 { font-size: 18px; margin: 0; }
.stats { display: flex; padding: 16px; gap: 12px; }
.stat-item { flex: 1; text-align: center; padding: 16px 8px; background: #fff; border-radius: 8px; cursor: pointer; }
.stat-num { font-size: 28px; font-weight: bold; }
.stat-label { font-size: 12px; color: #999; margin-top: 4px; }
.actions { padding: 16px; }
</style>
