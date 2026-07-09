<template>
  <div class="page">
    <div class="top-bar">
      <h2>🏪 商家中心</h2>
      <van-button size="small" plain type="primary" @click="doLogout">退出</van-button>
    </div>

    <!-- 今日概览 -->
    <div class="stats">
      <div class="stat-item" v-for="s in stats" :key="s.label" @click="goOrders(s.status)">
        <div class="stat-num" :style="{ color: s.color }">{{ s.count }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <!-- 新订单提醒 -->
    <van-cell-group inset v-if="newOrders.length">
      <van-cell v-for="o in newOrders" :key="o.id" :title="`${o.user_info?.name || '用户'} - ¥${o.items_total}`"
        :label="o.items?.map(i => i.name).join('、')" is-link @click="goDetail(o.id)">
        <template #right-icon><van-tag type="danger" size="small">新订单</van-tag></template>
      </van-cell>
    </van-cell-group>

    <div class="actions">
      <van-button round block type="primary" @click="goOrders('')">📋 查看全部订单</van-button>
      <van-button round block style="margin-top:12px" @click="goMenu">📝 管理菜品</van-button>
      <van-button round block plain style="margin-top:12px" @click="goShop">🏪 店铺设置</van-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { merchantApi } from '../../utils/api.js'

const stats = ref([
  { label: '待接单', count: 0, status: 'pending_accept', color: '#ee0a24' },
  { label: '进行中', count: 0, status: 'preparing,ready', color: '#ff976a' },
  { label: '已完成', count: 0, status: 'completed', color: '#07c160' },
])
const newOrders = ref([])

const load = async () => {
  try {
    // 获取待接单数量
    const res1 = await merchantApi.get('/api/merchant/orders', { status: 'pending_accept', page_size: 1 })
    stats.value[0].count = res1.total || 0
    // 获取进行中
    const res2 = await merchantApi.get('/api/merchant/orders', { status: 'preparing,ready', page_size: 1 })
    stats.value[1].count = res2.total || 0
    // 获取待接单的前5条
    const res3 = await merchantApi.get('/api/merchant/orders', { status: 'pending_accept', page_size: 5 })
    newOrders.value = res3.items || []
  } catch {}
}

const goOrders = (status) => {
  const hash = status ? `#/m/orders?status=${status}` : '#/m/orders'
  window.location.hash = hash
}
const goDetail = (id) => { window.location.hash = `#/m/order/${id}` }
const goMenu = () => { window.location.hash = '#/m/menu' }
const goShop = () => { window.location.hash = '#/m/shop' }
const doLogout = () => {
  localStorage.removeItem('merchant_token')
  window.location.hash = '#/m/login'
}

onMounted(() => {
  const token = localStorage.getItem('merchant_token')
  if (!token) { window.location.hash = '#/m/login'; return }
  load()
})
</script>

<style scoped>
.page { min-height: 100vh; background: #f7f8fa; padding-bottom: 20px; }
.top-bar { display: flex; justify-content: space-between; align-items: center; padding: 16px; background: #fff; }
.top-bar h2 { font-size: 18px; margin: 0; }
.stats { display: flex; padding: 16px; gap: 12px; }
.stat-item { flex: 1; text-align: center; padding: 16px 8px; background: #fff; border-radius: 8px; cursor: pointer; }
.stat-num { font-size: 28px; font-weight: bold; }
.stat-label { font-size: 12px; color: #999; margin-top: 4px; }
.actions { padding: 16px; }
</style>
