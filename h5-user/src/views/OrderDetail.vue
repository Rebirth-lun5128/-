<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showDialog } from 'vant'
import { api } from '../utils/api'
import { connectWS, onWSEvent, offWSEvent, closeWS } from '../utils/websocket'

const route = useRoute()
const router = useRouter()
const orderId = parseInt(route.params.id)

const order = ref(null)
const subOrders = ref([])
const timeline = ref([])
const reviewScore = ref(5)
const reviewTags = ref([])
const reviewContent = ref('')

onMounted(() => loadOrder())

function closeAndBack() {
  closeWS()
  router.back()
}

function statusText(s) {
  const map = { pending_pay: '待支付', pending: '处理中', pending_accept: '等待接单', preparing: '备餐中', ready: '待取餐', delivering: '配送中', delivered: '已送达', completed: '已完成', partial: '部分完成', cancelled: '已取消' }
  return map[s] || s
}
function statusColor(s) {
  const map = { pending_pay: '#FF9800', pending: '#FF6B35', pending_accept: '#FF6B35', preparing: '#2196F3', ready: '#4CAF50', delivering: '#2196F3', completed: '#999', partial: '#FF9800', cancelled: '#999' }
  return map[s] || '#999'
}

async function loadOrder() {
  try {
    const o = await api.get(`/api/user/orders/${orderId}`)
    order.value = { ...o, statusText: statusText(o.status), statusColor: statusColor(o.status) }
    subOrders.value = o.sub_orders || []
    timeline.value = subOrders.value[0]?.timeline || o.timeline || []

    const liveStatuses = ['pending_accept', 'preparing', 'ready', 'delivering']
    if (liveStatuses.includes(o.status)) {
      connectWS()
      onWSEvent('*', handleWS)
    }
  } catch { }
}

function handleWS(data) {
  if (data.order?.id !== orderId) return
  loadOrder()
}

async function payOrder() {
  try {
    await showDialog({ title: '确认支付', message: `订单金额: ¥${order.value.total_price}` })
    await api.post(`/api/user/orders/${orderId}/pay`)
    showToast({ message: '支付成功', type: 'success' })
    loadOrder()
  } catch { }
}

async function cancelOrder() {
  try {
    await showDialog({ title: '取消订单', message: '确定要取消该订单吗？' })
    await api.put(`/api/user/orders/${orderId}/cancel?reason=用户主动取消`)
    showToast({ message: '已取消', type: 'success' })
    loadOrder()
  } catch { }
}

async function submitReview(subId) {
  try {
    await api.post(`/api/user/orders/sub/${subId}/review`, {
      score: reviewScore.value,
      content: reviewContent.value,
      tags: reviewTags.value,
    })
    showToast({ message: '评价成功', type: 'success' })
    loadOrder()
  } catch { }
}

function toggleTag(tag) {
  const idx = reviewTags.value.indexOf(tag)
  if (idx >= 0) reviewTags.value = reviewTags.value.filter(t => t !== tag)
  else reviewTags.value = [...reviewTags.value, tag]
}
</script>

<template>
  <div class="page" v-if="order">
    <van-nav-bar title="订单详情" left-text="返回" left-arrow @click-left="closeAndBack" fixed placeholder />

    <!-- 状态横幅 -->
    <div class="text-center p-4" :style="{ background: order.statusColor + '15' }">
      <div style="font-size:40px">{{ order.status === 'pending_pay' ? '🕐' : order.status === 'delivering' ? '🛵' : order.status === 'completed' ? '✅' : '📋' }}</div>
      <div class="font-bold text-lg mt-2" :style="{ color: order.statusColor }">{{ order.statusText }}</div>
      <div class="text-sm text-gray mt-1" v-if="order.status === 'pending_pay'">请尽快完成支付</div>
    </div>

    <!-- 子单列表 -->
    <div v-for="sub in subOrders" :key="sub.id" class="bg-white mt-2 p-3">
      <div class="flex items-center justify-between mb-2">
        <span class="font-bold">{{ sub.store_name || sub.store_name_snapshot }}</span>
        <span class="text-sm" :style="{ color: statusColor(sub.status) }">{{ statusText(sub.status) }}</span>
      </div>
      <div v-for="item in (sub.items || [])" :key="item.id"
        class="flex items-center justify-between py-2" style="border-bottom:1px solid #f9f9f9">
        <div class="flex items-center flex-1" style="min-width:0">
          <van-image :src="item.product_image || item.image" width="40" height="40" fit="cover" round style="flex-shrink:0" lazy-load />
          <span class="ml-2 text-sm">{{ item.product_name || item.name }}</span>
        </div>
        <span class="text-sm text-gray ml-2">x{{ item.quantity }}</span>
        <span class="text-sm ml-2">¥{{ item.price }}</span>
      </div>
      <!-- 评价 -->
      <div v-if="sub.status === 'completed' && !sub.review" class="mt-3 p-3 rounded" style="background:#fff9f5">
        <div class="text-sm font-bold mb-2">评价 {{ sub.store_name }}</div>
        <div class="flex items-center mb-2">
          <span v-for="i in 5" :key="i" style="cursor:pointer;font-size:24px"
            @click="reviewScore = i">{{ i <= reviewScore ? '★' : '☆' }}</span>
        </div>
        <div class="flex flex-wrap mb-2" style="gap:6px">
          <span v-for="tag in ['味道好','分量足','包装好','性价比高']" :key="tag"
            class="text-sm px-2 py-1 rounded" style="cursor:pointer"
            :style="{ background: reviewTags.includes(tag) ? '#FFF3E0' : '#f5f5f5', color: reviewTags.includes(tag) ? '#ff6b35' : '#666' }"
            @click="toggleTag(tag)">{{ tag }}</span>
        </div>
        <van-field v-model="reviewContent" type="textarea" rows="2" maxlength="200" placeholder="说点什么吧..." />
        <van-button size="small" type="primary" round color="#ff6b35" class="mt-2" @click="submitReview(sub.id)">提交评价</van-button>
      </div>
    </div>

    <!-- 订单信息 -->
    <div class="bg-white mt-2 p-3">
      <div class="text-sm text-gray mb-1">订单号：{{ order.order_no }}</div>
      <div class="text-sm text-gray mb-1" v-if="order.address_snapshot">
        收货地址：{{ order.address_snapshot.address || order.address_snapshot.detail || '' }}
      </div>
      <div class="text-sm text-gray mb-1">创建时间：{{ order.created_at }}</div>
      <div class="flex justify-between mt-3 pt-3" style="border-top:1px solid #f5f5f5">
        <span class="text-gray">订单金额</span>
        <span class="text-primary font-bold text-xl">¥{{ order.total_price }}</span>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="p-3 flex" style="gap:10px" v-if="order.status === 'pending_pay'">
      <van-button block round plain type="danger" @click="cancelOrder">取消订单</van-button>
      <van-button block round type="primary" color="#ff6b35" @click="payOrder">立即支付</van-button>
    </div>
    <div class="p-3 flex" style="gap:10px" v-if="['pending_accept','preparing','ready'].includes(order.status)">
      <van-button block round plain type="danger" @click="cancelOrder">取消订单</van-button>
    </div>

    <div style="height:60px" />
  </div>
</template>
