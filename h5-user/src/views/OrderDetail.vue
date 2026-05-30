<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
  loadModifications()
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
  if (data.event === 'modification_reviewed' || data.event === 'modification_requested') {
    loadModifications()
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

// ==================== 改动申请 ====================
const modTypes = [
  { type: 'cancel', label: '退单申请', icon: '↩️', desc: '不想要了，申请取消订单' },
  { type: 'refund', label: '退款申请', icon: '💰', desc: '已支付，申请退款' },
  { type: 'address_change', label: '修改地址', icon: '📍', desc: '修改收货地址信息' },
  { type: 'other', label: '其他申请', icon: '💬', desc: '其他需要调整的地方' },
]
const showModSheet = ref(false)
const showModDialog = ref(false)
const modType = ref('')
const modSubId = ref(null)
const modReason = ref('')
const modContactName = ref('')
const modContactPhone = ref('')
const modAddressDetail = ref('')
const modifications = ref([])
const modPending = ref(false)
const submittingMod = ref(false)

async function loadModifications() {
  try {
    const mods = await api.get(`/api/user/orders/${orderId}/modifications`, {}, { silent: true })
    modifications.value = mods || []
    modPending.value = modifications.value.some(m => m.status === 'pending_review')
  } catch {}
}

function modTypeLabel(type) {
  const map = { cancel: '退单申请', refund: '退款申请', address_change: '修改地址', other: '其他申请' }
  return map[type] || type
}
function modStatusLabel(s) {
  const map = { pending_review: '待审核', approved: '已通过', rejected: '已拒绝' }
  return map[s] || s
}
function modStatusColor(s) {
  const map = { pending_review: '#FF9800', approved: '#4CAF50', rejected: '#999' }
  return map[s] || '#999'
}

function selectModType(type) {
  showModSheet.value = false
  modType.value = type
  if (type === 'address_change') {
    const addr = order.value?.address_snapshot || {}
    modContactName.value = addr.contact_name || ''
    modContactPhone.value = addr.contact_phone || ''
    modAddressDetail.value = addr.detail || addr.address || ''
  }
  modReason.value = ''
  modSubId.value = null
  setTimeout(() => { showModDialog.value = true }, 200)
}

async function submitMod() {
  if (!modReason.value.trim()) {
    showToast({ message: '请填写申请理由', type: 'fail' })
    return
  }
  submittingMod.value = true
  try {
    if (modType.value === 'address_change') {
      await api.post(`/api/user/orders/${orderId}/request-modification`, {
        type: modType.value,
        reason: modReason.value.trim(),
        new_address: {
          contact_name: modContactName.value,
          contact_phone: modContactPhone.value,
          detail: modAddressDetail.value,
        },
      })
    } else {
      const subId = modSubId.value || (subOrders.value.length === 1 ? subOrders.value[0].id : null)
      if (!subId) {
        showToast({ message: '请选择要修改的店铺', type: 'fail' })
        submittingMod.value = false
        return
      }
      await api.post(`/api/user/orders/sub/${subId}/request-modification`, {
        type: modType.value,
        reason: modReason.value.trim(),
      })
    }
    showToast({ message: '申请已提交，等待审核', type: 'success' })
    showModDialog.value = false
    loadModifications()
  } catch {} finally { submittingMod.value = false }
}

const canModify = computed(() => {
  const s = order.value?.status
  return ['pending', 'pending_accept', 'preparing', 'ready'].includes(s)
})
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

    <!-- 申请修改按钮 -->
    <div class="p-3" v-if="canModify">
      <van-button block round plain type="primary" @click="showModSheet = true">
        {{ modPending ? '已有待审核申请' : '申请修改' }}
      </van-button>
    </div>

    <!-- 改动申请记录 -->
    <div class="bg-white mt-2 p-3" v-if="modifications.length > 0">
      <div class="font-bold text-sm mb-2">📝 改动申请记录</div>
      <div v-for="mod in modifications" :key="mod.id"
        class="py-3" style="border-bottom:1px solid #f0f0f0">
        <div class="flex items-center justify-between">
          <span class="font-bold text-sm">{{ modTypeLabel(mod.type) }}</span>
          <span class="text-xs font-bold" :style="{ color: modStatusColor(mod.status) }">{{ modStatusLabel(mod.status) }}</span>
        </div>
        <div class="text-xs text-gray mt-1">理由：{{ mod.reason }}</div>
        <div class="text-xs mt-1" style="color:#FF9800" v-if="mod.review_comment">审核意见：{{ mod.review_comment }}</div>
        <div class="text-xs mt-1" style="color:#ccc">{{ mod.created_at }}</div>
      </div>
    </div>

    <div style="height:80px" />

    <!-- ====== 修改类型 ActionSheet ====== -->
    <van-action-sheet v-model:show="showModSheet" title="选择修改类型" :actions="modTypes.map(t=>({name:t.icon+' '+t.label+' - '+t.desc,type:t.type}))" @select="(a)=>{selectModType(a.type)}" cancel-text="取消" />

    <!-- ====== 修改申请弹窗 ====== -->
    <van-popup v-model:show="showModDialog" position="bottom" round :style="{ maxHeight: '65%' }">
      <div class="p-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-lg">申请修改</h3>
          <span class="text-sm text-gray" style="cursor:pointer" @click="showModDialog = false">✕</span>
        </div>

        <!-- 子单选择（多店合单 & 非地址修改） -->
        <div class="mb-3" v-if="subOrders.length > 1 && modType !== 'address_change'">
          <div class="text-sm text-gray mb-1">选择店铺</div>
          <van-radio-group v-model="modSubId" direction="horizontal">
            <van-radio v-for="sub in subOrders" :key="sub.id" :name="sub.id">{{ sub.store_name || sub.store_name_snapshot }}</van-radio>
          </van-radio-group>
        </div>

        <!-- 地址修改表单 -->
        <div v-if="modType === 'address_change'">
          <div class="text-xs text-gray mb-2">当前地址：{{ order.address_snapshot.contact_name }} {{ order.address_snapshot.contact_phone }} {{ order.address_snapshot.detail || order.address_snapshot.address }}</div>
          <van-field v-model="modContactName" label="新联系人" placeholder="收货人姓名" />
          <van-field v-model="modContactPhone" label="新电话" placeholder="收货人电话" />
          <van-field v-model="modAddressDetail" label="新地址" placeholder="详细地址" />
        </div>

        <!-- 理由 -->
        <van-field v-model="modReason" type="textarea" rows="3" maxlength="300" placeholder="请详细说明修改原因..." class="mt-3" />

        <van-button block round type="primary" color="#2196F3" :loading="submittingMod" class="mt-4" @click="submitMod" style="height:44px">
          提交申请
        </van-button>
      </div>
    </van-popup>
  </div>
</template>
