<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showDialog, showToast } from 'vant'
import { cartStore } from '../stores/cart'

const router = useRouter()

const grouped = computed(() => {
  const map = {}
  for (const item of cartStore.items) {
    if (!map[item.storeId]) map[item.storeId] = { storeId: item.storeId, storeName: item.storeName || '未知店铺', items: [] }
    map[item.storeId].items.push(item)
  }
  return Object.values(map).map(g => ({
    ...g,
    subtotal: g.items.reduce((s, i) => s + i.price * i.quantity, 0),
  }))
})

const totalPrice = computed(() => grouped.value.reduce((s, g) => s + g.subtotal, 0))

function addItem(sid, pid) {
  const item = cartStore.items.find(i => i.productId === pid && i.storeId === sid)
  if (item) cartStore.updateQuantity(pid, sid, item.quantity + 1)
}

function reduceItem(sid, pid) {
  const item = cartStore.items.find(i => i.productId === pid && i.storeId === sid)
  if (item) cartStore.updateQuantity(pid, sid, item.quantity - 1)
}

async function removeItem(sid, pid) {
  try { await showDialog({ title: '移除菜品', message: '确定从购物车移除吗？' }) }
  catch { return }
  cartStore.removeItem(pid, sid)
}

async function clearStore(sid) {
  try { await showDialog({ title: '清空', message: '确定清空该店铺所有菜品吗？' }) }
  catch { return }
  cartStore.clearByStore(sid)
}

function goCheckout(sid) {
  router.push(`/order-confirm?store_id=${sid}`)
}

function goCombined() {
  const ids = grouped.value.map(g => g.storeId).join(',')
  router.push(`/order-confirm?store_ids=${ids}`)
}
</script>

<template>
  <div class="page">
    <van-nav-bar title="购物车" left-text="返回" left-arrow @click-left="$router.back()" fixed placeholder />

    <div v-if="grouped.length === 0" class="text-center p-4" style="margin-top:40%">
      <p class="text-xl text-gray mb-4">🛒 购物车是空的</p>
      <van-button type="primary" round color="#ff6b35" @click="$router.replace('/')">去首页逛逛</van-button>
    </div>

    <div v-for="g in grouped" :key="g.storeId" class="bg-white m-3 rounded-lg shadow overflow-hidden">
      <div class="flex items-center justify-between p-3" style="border-bottom:1px solid #f5f5f5">
        <span class="font-bold">{{ g.storeName }}</span>
        <van-button size="small" plain type="danger" @click="clearStore(g.storeId)">清空</van-button>
      </div>
      <div v-for="item in g.items" :key="item.productId" class="flex items-center p-3" style="border-bottom:1px solid #f9f9f9">
        <van-image :src="item.image" width="48" height="48" fit="cover" round style="flex-shrink:0" lazy-load />
        <div class="ml-3 flex-1" style="min-width:0">
          <div class="text-sm font-bold">{{ item.name }}</div>
          <div class="text-primary text-sm mt-1">¥{{ item.price }}</div>
        </div>
        <div class="flex items-center mr-3">
          <span class="flex items-center justify-center rounded-full"
            style="width:24px;height:24px;border:1px solid #ff6b35;color:#ff6b35;cursor:pointer"
            @click="reduceItem(g.storeId, item.productId)">−</span>
          <span class="mx-2" style="min-width:20px;text-align:center">{{ item.quantity }}</span>
          <span class="flex items-center justify-center rounded-full"
            style="width:24px;height:24px;background:#ff6b35;color:#fff;cursor:pointer"
            @click="addItem(g.storeId, item.productId)">+</span>
        </div>
        <span class="text-sm text-gray" style="cursor:pointer" @click="removeItem(g.storeId, item.productId)">🗑</span>
      </div>
      <div class="flex items-center justify-between p-3">
        <span class="text-sm text-gray">小计 ¥{{ g.subtotal.toFixed(2) }}</span>
        <van-button size="small" type="primary" round color="#ff6b35" @click="goCheckout(g.storeId)">结算</van-button>
      </div>
    </div>

    <!-- 合并结算 -->
    <div v-if="grouped.length > 1" class="bg-white mx-3 p-3 rounded-lg shadow flex items-center justify-between">
      <div>
        <span class="font-bold">合并结算</span>
        <span class="text-sm text-gray ml-2">跨店合单，统一配送</span>
      </div>
      <div class="text-right">
        <span class="text-primary font-bold text-lg">¥{{ totalPrice.toFixed(2) }}</span>
        <van-button size="small" type="primary" round color="#ff6b35" class="ml-2" @click="goCombined">去结算</van-button>
      </div>
    </div>

    <div style="height:60px" />
  </div>
</template>
