<template>
  <div class="page">
    <van-nav-bar title="我的订单" left-text="返回" left-arrow @click-left="$router.back()" />
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list v-model:loading="loading" :finished="finished" @load="onLoad">
        <div v-for="o in orders" :key="o.id" class="order-card" @click="goDetail(o.id)">
          <div class="order-hd">
            <span>订单 #{{ o.id }}</span>
            <van-tag :type="tagType(o.status)">{{ statusText(o.status) }}</van-tag>
          </div>
          <div class="order-body">
            <div>{{ o.store_names || '夜市配送' }}</div>
            <div class="order-addr">📍 {{ o.address_snapshot?.address || '' }}</div>
          </div>
          <div class="order-ft">
            <span>配送费 ¥{{ o.delivery_fee || 0 }}</span>
            <span style="color:#999;font-size:12px">{{ o.created_at }}</span>
          </div>
        </div>
      </van-list>
    </van-pull-refresh>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { riderApi } from '../../utils/api.js'

const orders = ref([])
const page = ref(1)
const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)

const statusText = (s) => {
  const map = { pending: '待配送', delivering: '配送中', completed: '已完成', cancelled: '已取消' }
  return map[s] || s
}
const tagType = (s) => {
  const map = { pending: 'warning', delivering: 'primary', completed: 'success', cancelled: 'default' }
  return map[s] || 'default'
}

const loadOrders = async () => {
  if (loading.value) return
  loading.value = true
  try {
    const res = await riderApi.get('/api/rider/orders/my', { page: page.value, page_size: 10 })
    const items = res.items || []
    orders.value = page.value === 1 ? items : [...orders.value, ...items]
    finished.value = items.length < 10
    page.value++
  } catch {} finally { loading.value = false }
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
const goDetail = (id) => window.location.hash = `#/r/order/${id}`

onMounted(loadOrders)
</script>

<style scoped>
.page { min-height: 100vh; background: #f7f8fa; }
.order-card { background: #fff; margin: 8px 12px; padding: 12px; border-radius: 8px; cursor: pointer; }
.order-hd { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.order-body { color: #666; font-size: 13px; margin-bottom: 8px; }
.order-addr { color: #999; font-size: 12px; }
.order-ft { display: flex; justify-content: space-between; font-weight: bold; }
</style>
