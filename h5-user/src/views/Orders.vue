<script setup>
import { ref, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../utils/api'

const router = useRouter()

const tabs = ['全部', '待付款', '处理中', '配送中', '已完成']
const statusMap = ['', 'pending_pay', 'pending', 'delivering', 'completed']
const activeTab = ref(0)
const orders = ref([])
const page = ref(1)
const hasMore = ref(true)
const loading = ref(false)

function statusText(s) {
  const map = { pending_pay: '待支付', pending: '处理中', pending_accept: '等待接单', preparing: '备餐中', ready: '待取餐', delivering: '配送中', delivered: '已送达', completed: '已完成', partial: '部分完成', cancelled: '已取消' }
  return map[s] || s
}
function statusColor(s) {
  const map = { pending_pay: '#FF9800', pending: '#FF6B35', pending_accept: '#FF6B35', preparing: '#2196F3', ready: '#4CAF50', delivering: '#2196F3', delivered: '#4CAF50', completed: '#999', partial: '#FF9800', cancelled: '#999' }
  return map[s] || '#999'
}

onActivated(() => loadOrders())

async function loadOrders() {
  if (loading.value) return
  loading.value = true
  try {
    const params = { page: page.value, page_size: 10 }
    const s = statusMap[activeTab.value]
    if (s) params.status = s
    const res = await api.get('/api/user/orders', params)
    const items = (res.items || []).map(o => ({
      ...o,
      statusText: statusText(o.status),
      statusColor: statusColor(o.status),
    }))
    orders.value = page.value === 1 ? items : [...orders.value, ...items]
    page.value++
    hasMore.value = items.length < res.total
  } catch { } finally {
    loading.value = false
  }
}

function onTabTap(idx) {
  if (idx === activeTab.value) return
  activeTab.value = idx
  page.value = 1
  orders.value = []
  hasMore.value = true
  loadOrders()
}

function goOrder(id) {
  router.push(`/order/${id}`)
}
</script>

<template>
  <div class="page">
    <van-nav-bar title="我的订单" fixed placeholder />
    <div class="flex bg-white" style="position:sticky;top:46px;z-index:50;border-bottom:1px solid #eee">
      <div v-for="(t, i) in tabs" :key="t"
        class="flex-1 text-center p-3" style="font-size:14px;cursor:pointer"
        :style="{ color: activeTab === i ? '#ff6b35' : '#666', borderBottom: activeTab === i ? '2px solid #ff6b35' : '2px solid transparent' }"
        @click="onTabTap(i)">{{ t }}</div>
    </div>

    <van-list v-model:loading="loading" :finished="!hasMore" finished-text="— 没有更多了 —" @load="loadOrders">
      <div v-if="orders.length === 0 && !loading" class="text-center text-gray p-4">暂无订单</div>
      <div v-for="o in orders" :key="o.id" class="bg-white m-3 rounded-lg shadow overflow-hidden"
        style="cursor:pointer" @click="goOrder(o.id)">
        <div class="flex items-center justify-between p-3" style="border-bottom:1px solid #f5f5f5">
          <span class="text-sm text-gray">订单号：{{ o.order_no }}</span>
          <span :style="{ color: o.statusColor }">{{ o.statusText }}</span>
        </div>
        <div class="p-3">
          <div v-for="sub in (o.sub_orders || [])" :key="sub.id" class="text-sm mb-1">
            <span class="font-bold">{{ sub.store_name || sub.store_name_snapshot }}</span>
            <span class="text-gray ml-2">{{ sub.items?.map(i=>i.product_name||i.name).join('、') || '' }}</span>
          </div>
          <div v-if="!o.sub_orders?.length" class="text-sm text-gray">{{ o.items?.map(i=>i.name).join('、') || '' }}</div>
        </div>
        <div class="flex items-center justify-between px-3 pb-3">
          <span class="text-sm text-gray">{{ o.created_at }}</span>
          <span class="font-bold text-lg">¥{{ o.total_price }}</span>
        </div>
      </div>
    </van-list>
    <div style="height:60px" />
  </div>
</template>
