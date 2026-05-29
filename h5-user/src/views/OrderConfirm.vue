<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast, showDialog } from 'vant'
import { api } from '../utils/api'
import { cartStore } from '../stores/cart'

const router = useRouter()
const route = useRoute()

const storeIds = computed(() => {
  if (route.query.store_ids) return route.query.store_ids.split(',').map(Number)
  return [parseInt(route.query.store_id)]
})
const isCombined = computed(() => storeIds.value.length > 1)

const storeGroups = ref([])
const itemsTotal = ref(0)
const deliveryFee = ref(0)
const deliveryFeeOriginal = ref(0)
const deliveryFeeDiscount = ref(0)
const couponDiscount = ref(0)
const totalPrice = computed(() => Math.max(0, itemsTotal.value + deliveryFee.value - couponDiscount.value))
const address = ref(null)
const remark = ref('')
const coupons = ref([])
const selectedCoupon = ref(null)
const showCouponPopup = ref(false)
const loading = ref(false)

onMounted(async () => {
  await loadAddress()
  await loadCoupons()
  buildStoreGroups()
  await loadDeliveryFee()
})

function buildStoreGroups() {
  const groups = []
  let total = 0
  for (const sid of storeIds.value) {
    const items = cartStore.items.filter(i => i.storeId === sid)
    if (items.length === 0) continue
    const subtotal = items.reduce((s, i) => s + i.price * i.quantity, 0)
    const storeName = items[0]?.storeName || '未知店铺'
    groups.push({ store_id: sid, store_name: storeName, items, subtotal })
    total += subtotal
  }
  storeGroups.value = groups
  itemsTotal.value = total
}

async function loadDeliveryFee() {
  try {
    let totalFee = 0
    let totalOriginal = 0
    for (const sid of storeIds.value) {
      try {
        const store = await api.get(`/api/user/stores/${sid}`, {}, { silent: true })
        const fee = parseFloat(store.delivery_fee) || 0
        totalOriginal += fee
        totalFee += fee
      } catch {}
    }
    deliveryFeeOriginal.value = totalOriginal
    deliveryFee.value = totalFee
    deliveryFeeDiscount.value = Math.max(0, totalOriginal - totalFee)
  } catch {}
}

async function loadAddress() {
  try {
    const addresses = await api.get('/api/user/addresses')
    if (route.query.addr_id) {
      address.value = addresses.find(a => a.id == route.query.addr_id) || addresses.find(a => a.is_default) || addresses[0] || null
    } else {
      address.value = addresses.find(a => a.is_default) || addresses[0] || null
    }
  } catch {}
}

async function loadCoupons() {
  try {
    const res = await api.get('/api/user/coupons/my')
    coupons.value = res.filter(c => c.status === 'unused')
  } catch {}
}

function chooseAddress() {
  router.push('/address?select=1')
}

function selectCoupon(c) {
  if (c.coupon_type === 'full_reduction' && itemsTotal.value < c.condition_amount) return
  selectedCoupon.value = c
  couponDiscount.value = parseFloat(c.discount_amount) || 0
  showCouponPopup.value = false
}

function clearCoupon() {
  selectedCoupon.value = null
  couponDiscount.value = 0
  showCouponPopup.value = false
}

async function submitOrder() {
  if (!address.value) {
    showToast({ message: '请选择收货地址', type: 'fail' })
    return
  }
  loading.value = true
  try {
    const body = {
      address_id: address.value.id,
      sub_orders: storeGroups.value.map(g => ({
        store_id: g.store_id,
        items: g.items.map(item => ({
          product_id: item.productId,
          name: item.name,
          image: item.image || '',
          price: item.price,
          quantity: item.quantity,
        })),
      })),
      remark: remark.value,
    }
    if (selectedCoupon.value) body.user_coupon_id = selectedCoupon.value.id

    const order = await api.post('/api/user/orders', body)
    for (const sid of storeIds.value) cartStore.clearByStore(sid)

    try {
      await showDialog({ title: '确认支付', message: `订单金额: ¥${order.total_price}\n(开发阶段为模拟支付)` })
    } catch {
      // 用户取消支付弹窗 → 订单保留在 pending_pay 状态
      showToast({ message: '订单已创建，请尽快支付', type: 'success' })
      setTimeout(() => router.replace('/orders'), 800)
      return
    }

    try {
      await api.post(`/api/user/orders/${order.id}/pay`)
      showToast({ message: '支付成功', type: 'success' })
      setTimeout(() => router.replace('/orders'), 800)
    } catch {
      showToast({ message: '订单已创建，请尽快支付', type: 'success' })
      setTimeout(() => router.replace('/orders'), 800)
    }
  } catch {} finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <van-nav-bar title="确认订单" left-text="返回" left-arrow @click-left="$router.back()" fixed placeholder />

    <div v-if="storeGroups.length === 0" class="text-center p-4">订单数据为空</div>

    <!-- 收货地址 -->
    <div class="bg-white mt-2 p-3 flex items-center" style="cursor:pointer" @click="chooseAddress">
      <span style="font-size:24px">📍</span>
      <div class="ml-3 flex-1" v-if="address">
        <div class="font-bold">{{ address.contact_name }} {{ address.contact_phone }}</div>
        <div class="text-sm text-gray mt-1">{{ address.province }}{{ address.city }}{{ address.district }} {{ address.detail }}</div>
      </div>
      <div class="ml-3 flex-1 text-gray" v-else>请选择收货地址</div>
      <span style="font-size:18px;color:#999">›</span>
    </div>

    <!-- 商品列表 -->
    <div v-for="g in storeGroups" :key="g.store_id" class="bg-white mt-2 p-3">
      <div class="font-bold mb-2">{{ g.store_name }}</div>
      <div v-for="item in g.items" :key="item.productId" class="flex items-center justify-between py-2" style="border-bottom:1px solid #f9f9f9">
        <div class="flex items-center flex-1" style="min-width:0">
          <van-image :src="item.image" width="48" height="48" fit="cover" round style="flex-shrink:0" lazy-load />
          <span class="ml-2 text-sm">{{ item.name }}</span>
        </div>
        <span class="text-sm text-gray ml-2">x{{ item.quantity }}</span>
        <span class="text-primary font-bold ml-2">¥{{ (item.price * item.quantity).toFixed(2) }}</span>
      </div>
    </div>

    <!-- 费用明细 -->
    <div class="bg-white mt-2 p-3">
      <div class="flex justify-between mb-2"><span class="text-gray">商品总额</span><span>¥{{ itemsTotal.toFixed(2) }}</span></div>
      <div class="flex justify-between mb-2">
        <span class="text-gray">配送费</span>
        <span>
          <span v-if="deliveryFeeOriginal > deliveryFee" class="text-gray" style="text-decoration:line-through;font-size:12px">¥{{ deliveryFeeOriginal.toFixed(2) }}</span>
          <span :class="deliveryFee > 0 ? '' : 'text-primary'">{{ deliveryFee > 0 ? '¥' + deliveryFee.toFixed(2) : '免配送费' }}</span>
        </span>
      </div>
      <div class="flex justify-between mb-2" v-if="deliveryFeeDiscount > 0">
        <span class="text-gray">配送费满减</span><span class="text-danger">−¥{{ deliveryFeeDiscount.toFixed(2) }}</span>
      </div>
      <div class="flex justify-between mb-2" v-if="couponDiscount > 0"><span class="text-gray">优惠券</span><span class="text-danger">−¥{{ couponDiscount.toFixed(2) }}</span></div>
    </div>

    <!-- 优惠券 -->
    <div class="bg-white mt-2 p-3 flex items-center justify-between" style="cursor:pointer" @click="showCouponPopup = true">
      <span class="text-gray">优惠券</span>
      <span :class="selectedCoupon ? 'text-primary' : 'text-gray'">
        {{ selectedCoupon ? `满¥${selectedCoupon.condition_amount}减¥${selectedCoupon.discount_amount}` : `${coupons.length}张可用` }}
        <span style="font-size:14px;color:#999">›</span>
      </span>
    </div>

    <!-- 备注 -->
    <div class="bg-white mt-2 p-3">
      <van-field v-model="remark" type="textarea" rows="2" maxlength="100" placeholder="备注信息（选填）" />
    </div>

    <!-- 底部提交栏 -->
    <div class="bg-white p-3 shadow flex items-center justify-between"
      style="position:fixed;bottom:0;left:0;right:0;z-index:100;padding-bottom:env(safe-area-inset-bottom)">
      <div>
        <span class="text-sm text-gray">合计</span>
        <span class="text-primary font-bold text-xl ml-1">¥{{ totalPrice.toFixed(2) }}</span>
        <span class="text-sm text-gray ml-2" v-if="isCombined">跨店合单</span>
      </div>
      <van-button type="primary" round color="#ff6b35" :loading="loading" @click="submitOrder" style="height:44px;min-width:120px">
        提交订单
      </van-button>
    </div>

    <!-- 优惠券弹窗 -->
    <van-popup v-model:show="showCouponPopup" position="bottom" round :style="{ maxHeight: '50%' }">
      <div class="p-3">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-bold text-lg">选择优惠券</h3>
          <span class="text-sm text-primary" style="cursor:pointer" @click="clearCoupon">不使用优惠券</span>
        </div>
        <div v-if="coupons.length === 0" class="text-center text-gray p-3">暂无可用优惠券</div>
        <div v-for="c in coupons" :key="c.id" class="p-3 mb-2 rounded shadow-sm"
          :style="{
            background: selectedCoupon?.id === c.id ? '#FFF3E0' : '#fff',
            border: selectedCoupon?.id === c.id ? '1px solid #ff6b35' : '1px solid #eee',
            cursor: (c.coupon_type === 'full_reduction' && itemsTotal < c.condition_amount) ? 'not-allowed' : 'pointer',
            opacity: (c.coupon_type === 'full_reduction' && itemsTotal < c.condition_amount) ? 0.5 : 1,
          }"
          @click="selectCoupon(c)">
          <div class="flex items-center">
            <div class="text-primary font-bold" style="font-size:20px">¥{{ c.discount_amount }}</div>
            <div class="ml-3">
              <div class="font-bold">{{ c.title || c.name }}</div>
              <div class="text-sm text-gray mt-1" v-if="c.condition_amount > 0">满¥{{ c.condition_amount }}可用</div>
            </div>
          </div>
        </div>
      </div>
    </van-popup>
  </div>
</template>
