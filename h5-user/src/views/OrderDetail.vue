<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showDialog } from 'vant'
import { api } from '../utils/api'
import { connectWS, onWSEvent, offWSEvent, closeWS } from '../utils/websocket'
import { getOrderStatusText, getOrderStatusColor, needPay } from '../utils/util'

const route = useRoute()
const router = useRouter()
const orderId = parseInt(route.params.id)

const order = ref(null)
const subOrders = ref([])
const reviewScore = ref(5)
const reviewTags = ref([])
const reviewContent = ref('')
const riderLat = ref(null)
const riderLng = ref(null)

onMounted(() => loadOrder())
onUnmounted(() => closeWS())

function closeAndBack() {
  closeWS()
  router.back()
}

async function loadOrder() {
  try {
    const o = await api.get(`/api/user/orders/${orderId}`)
    order.value = {
      ...o,
      statusText: getOrderStatusText(o.status),
      statusColor: getOrderStatusColor(o.status),
      storeCount: (o.sub_orders || []).filter(s => s.status !== 'cancelled').length,
    }
    subOrders.value = o.sub_orders || []

    const liveStatuses = ['pending', 'pending_accept', 'preparing', 'ready', 'delivering']
    if (liveStatuses.includes(o.status)) {
      connectWS()
      onWSEvent('*', handleWS)
    }

    if (o.status === 'delivering') {
      try {
        const loc = await api.get(`/api/user/orders/${orderId}/rider-location`)
        if (loc.lat && loc.lng) {
          riderLat.value = loc.lat
          riderLng.value = loc.lng
        }
      } catch {}
    }
  } catch {}
}

function handleWS(data) {
  const rawOrder = data.order || data
  const wsOrderId = rawOrder.id || rawOrder.order_id
  if (!wsOrderId || wsOrderId !== orderId) return

  if (data.event === 'rider_location') {
    const lat = data.lat || rawOrder.lat
    const lng = data.lng || rawOrder.lng
    if (lat && lng) {
      riderLat.value = lat
      riderLng.value = lng
    }
    return
  }
  loadOrder()
}

async function payOrder() {
  try {
    await showDialog({ title: '确认支付', message: `订单金额: ¥${order.value.total_price}` })
    await api.post(`/api/user/orders/${orderId}/pay`)
    showToast({ message: '支付成功', type: 'success' })
    loadOrder()
  } catch {}
}

async function cancelOrder() {
  try {
    await showDialog({ title: '取消订单', message: '确定要取消该订单吗？' })
    await api.put(`/api/user/orders/${orderId}/cancel?reason=用户主动取消`)
    showToast({ message: '已取消', type: 'success' })
    loadOrder()
  } catch {}
}

async function submitReview(subId) {
  try {
    await api.post(`/api/user/orders/sub/${subId}/review`, {
      score: reviewScore.value,
      content: reviewContent.value,
      tags: reviewTags.value,
    })
    showToast({ message: '评价成功', type: 'success' })
    reviewContent.value = ''
    reviewTags.value = []
    reviewScore.value = 5
    loadOrder()
  } catch {}
}

function toggleTag(tag) {
  const idx = reviewTags.value.indexOf(tag)
  if (idx >= 0) reviewTags.value = reviewTags.value.filter(t => t !== tag)
  else reviewTags.value = [...reviewTags.value, tag]
}

function openMapApp() {
  if (riderLat.value && riderLng.value) {
    window.open(`https://uri.amap.com/marker?position=${riderLng.value},${riderLat.value}&name=骑手位置`, '_blank')
  }
}

const reviewTagsList = ['味道好', '分量足', '包装好', '性价比高', '送餐快']
</script>

<template>
  <div class="page" v-if="order">
    <van-nav-bar title="订单详情" left-text="返回" left-arrow @click-left="closeAndBack" fixed placeholder />

    <!-- 状态横幅 -->
    <div class="text-center p-4" :style="{ background: order.statusColor + '15' }">
      <div style="font-size:40px">
        {{ order.status === 'pending_pay' ? '🕐' : order.status === 'delivering' ? '🛵' : order.status === 'completed' ? '✅' : '📋' }}
      </div>
      <div class="font-bold text-lg mt-2" :style="{ color: order.statusColor }">
        {{ order.statusText }}
        <span v-if="order.storeCount > 1" class="text-sm ml-1 px-2 py-0.5 rounded"
          style="background:#FFF3E0;color:#ff6b35">{{ order.storeCount }}店合单</span>
      </div>
      <div class="text-sm text-gray mt-1" v-if="order.status === 'pending_pay'">请尽快完成支付</div>
      <div class="text-sm mt-1" v-if="order.rider_name && order.status === 'delivering'">
        骑手：{{ order.rider_name }}
      </div>
    </div>

    <!-- 骑手追踪卡片 -->
    <div v-if="order.status === 'delivering' && riderLat && riderLng" class="bg-white mt-2 p-3">
      <div class="flex items-center justify-between mb-2">
        <span class="font-bold text-sm">骑手实时位置</span>
        <span class="text-xs text-primary" style="cursor:pointer" @click="openMapApp">查看地图 ›</span>
      </div>
      <div class="flex items-center justify-center p-4 rounded" style="background:#f5f7fa;min-height:120px">
        <div class="text-center">
          <div style="font-size:36px">🛵</div>
          <div class="text-sm text-gray mt-2">骑手正在配送中</div>
          <div class="text-xs text-gray mt-1" v-if="riderLat && riderLng">
            位置: {{ riderLat.toFixed(4) }}, {{ riderLng.toFixed(4) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 子单列表 -->
    <div v-for="sub in subOrders" :key="sub.id" class="bg-white mt-2 p-3">
      <div class="flex items-center justify-between mb-2">
        <span class="font-bold">{{ sub.store_name || sub.store_name_snapshot }}</span>
        <span class="text-sm" :style="{ color: getOrderStatusColor(sub.status) }">{{ getOrderStatusText(sub.status) }}</span>
      </div>

      <!-- 子单商品 -->
      <div v-for="item in (sub.items || [])" :key="item.id"
        class="flex items-center justify-between py-2" style="border-bottom:1px solid #f9f9f9">
        <div class="flex items-center flex-1" style="min-width:0">
          <van-image :src="item.product_image || item.image" width="40" height="40" fit="cover" round style="flex-shrink:0" lazy-load />
          <span class="ml-2 text-sm">{{ item.product_name || item.name }}</span>
        </div>
        <span class="text-sm text-gray ml-2">x{{ item.quantity }}</span>
        <span class="text-sm ml-2">¥{{ item.price }}</span>
      </div>

      <!-- 子单时间线 -->
      <div v-if="sub.timeline && sub.timeline.length" class="mt-2 pt-2" style="border-top:1px solid #f5f5f5">
        <div v-for="tl in sub.timeline.slice(0, 3)" :key="tl.id" class="flex items-center text-xs text-gray py-1">
          <span class="w-2 h-2 rounded-full mr-2" style="background:#ff6b35;flex-shrink:0" />
          <span>{{ tl.status_text || tl.description || tl.status }}</span>
          <span class="ml-auto" style="flex-shrink:0">{{ tl.created_at?.slice(11, 19) || '' }}</span>
        </div>
      </div>

      <!-- 已评价展示 -->
      <div v-if="sub.review" class="mt-3 p-3 rounded" style="background:#f9fafb">
        <div class="text-sm font-bold mb-1">我的评价 — {{ sub.store_name }}</div>
        <div class="flex items-center mb-1">
          <span v-for="i in 5" :key="i" :style="{ color: i <= sub.review.score ? '#ff6b35' : '#ddd' }">
            {{ i <= sub.review.score ? '★' : '☆' }}
          </span>
        </div>
        <div class="flex flex-wrap mb-1" style="gap:4px">
          <span v-for="tag in (sub.review.tags || [])" :key="tag"
            class="text-xs px-2 py-1 rounded" style="background:#FFF3E0;color:#ff6b35">{{ tag }}</span>
        </div>
        <div class="text-sm text-gray" v-if="sub.review.content">{{ sub.review.content }}</div>
      </div>

      <!-- 评价表单 -->
      <div v-if="sub.status === 'completed' && !sub.review" class="mt-3 p-3 rounded" style="background:#fff9f5">
        <div class="text-sm font-bold mb-2">评价 {{ sub.store_name }}</div>
        <div class="flex items-center mb-2">
          <span v-for="i in 5" :key="i" style="cursor:pointer;font-size:24px"
            @click="reviewScore = i">{{ i <= reviewScore ? '★' : '☆' }}</span>
        </div>
        <div class="flex flex-wrap mb-2" style="gap:6px">
          <span v-for="tag in reviewTagsList" :key="tag"
            class="text-sm px-2 py-1 rounded" style="cursor:pointer"
            :style="{ background: reviewTags.includes(tag) ? '#FFF3E0' : '#f5f5f5', color: reviewTags.includes(tag) ? '#ff6b35' : '#666' }"
            @click="toggleTag(tag)">{{ tag }}</span>
        </div>
        <van-field v-model="reviewContent" type="textarea" rows="2" maxlength="500" placeholder="说点什么吧..." />
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
    <div class="p-3 flex" style="gap:10px" v-if="needPay(order.status)">
      <van-button block round plain type="danger" @click="cancelOrder">取消订单</van-button>
      <van-button block round type="primary" color="#ff6b35" @click="payOrder">立即支付</van-button>
    </div>
    <div class="p-3 flex" style="gap:10px" v-if="['pending_accept','preparing','ready'].includes(order.status)">
      <van-button block round plain type="danger" @click="cancelOrder">取消订单</van-button>
    </div>

    <div style="height:60px" />
  </div>
</template>
