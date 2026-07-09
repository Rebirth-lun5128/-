<template>
  <div class="page">
    <van-nav-bar title="订单列表" left-text="返回" left-arrow @click-left="$router.back()" />
    <van-tabs v-model:active="activeTab" @change="onTabChange">
      <van-tab v-for="(t, i) in tabs" :key="i" :title="t" />
    </van-tabs>
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list v-model:loading="loading" :finished="finished" @load="onLoad">
        <div v-for="o in orders" :key="o.id" class="order-card" @click="goDetail(o.id)">
          <div class="order-hd">
            <span>订单 #{{ o.id }}</span>
            <van-tag :type="tagType(o.status)">{{ statusText(o.status) }}</van-tag>
          </div>
          <div class="order-items">
            {{ o.items?.map(i => i.name).join('、') || '暂无商品' }}
          </div>
          <div class="order-ft">
            <span>¥{{ o.items_total }}</span>
            <span style="color:#999;font-size:12px">{{ o.created_at }}</span>
          </div>
        </div>
      </van-list>
    </van-pull-refresh>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { merchantApi } from '../../utils/api.js'

const route = useRoute()
const tabs = ['全部', '待接单', '进行中', '已完成']
const statusMap = ['', 'pending_accept', 'preparing,ready', 'completed,cancelled']
const activeTab = ref(0)
const orders = ref([])
const page = ref(1)
const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)

const statusText = (s) => {
  const map = { pending_accept: '待接单', preparing: '备餐中', ready: '已出餐', delivering: '配送中', completed: '已完成', cancelled: '已取消' }
  return map[s] || s
}
const tagType = (s) => {
  const map = { pending_accept: 'danger', preparing: 'warning', ready: 'primary', delivering: 'primary', completed: 'success', cancelled: 'default' }
  return map[s] || 'default'
}

const loadOrders = async () => {
  if (loading.value) return
  loading.value = true
  try {
    const params = { page: page.value, page_size: 10 }
    const statusStr = statusMap[activeTab.value]
    if (statusStr) params.status = statusStr
    const res = await merchantApi.get('/api/merchant/orders', params)
    const items = (res.items || [])
    orders.value = page.value === 1 ? items : [...orders.value, ...items]
    finished.value = items.length < 10
    page.value++
  } catch {} finally { loading.value = false }
}

const onTabChange = () => {
  page.value = 1
  orders.value = []
  finished.value = false
  loadOrders()
}
const onLoad = () => { loadOrders() }
const onRefresh = async () => {
  page.value = 1
  orders.value = []
  finished.value = false
  refreshing.value = true
  await loadOrders()
  refreshing.value = false
}
const goDetail = (id) => window.location.hash = `#/m/order/${id}`

onMounted(() => {
  if (route.query.status) activeTab.value = parseInt(route.query.status) || 0
  loadOrders()
})
</script>

<style scoped>
.page { min-height: 100vh; background: #f7f8fa; }
.order-card { background: #fff; margin: 8px 12px; padding: 12px; border-radius: 8px; cursor: pointer; }
.order-hd { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 14px; }
.order-items { color: #666; font-size: 13px; margin-bottom: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.order-ft { display: flex; justify-content: space-between; font-weight: bold; }
</style>
