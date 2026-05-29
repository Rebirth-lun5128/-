<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showDialog, showToast } from 'vant'
import { api } from '../utils/api'
import { cartStore } from '../stores/cart'

const router = useRouter()
const districtMap = ref({})

onMounted(() => loadDistricts())

async function loadDistricts() {
  try {
    const list = await api.get('/api/user/stores/districts/list')
    const map = {}
    for (const d of list) map[d.id] = d.name || `分区${d.id}`
    districtMap.value = map
  } catch {}
}

function districtName(id) {
  return districtMap.value[id] || `分区${id || '未知'}`
}

/** 按分区 -> 店铺分组 */
const grouped = computed(() => {
  const districtGroups = {}
  for (const item of cartStore.items) {
    const did = item.districtId || 0
    if (!districtGroups[did]) districtGroups[did] = {}
    if (!districtGroups[did][item.storeId]) {
      districtGroups[did][item.storeId] = { storeId: item.storeId, storeName: item.storeName || '未知店铺', items: [] }
    }
    districtGroups[did][item.storeId].items.push(item)
  }
  const result = []
  for (const [did, stores] of Object.entries(districtGroups)) {
    const storeList = Object.values(stores).map(g => ({
      ...g,
      subtotal: g.items.reduce((s, i) => s + i.price * i.quantity, 0),
      count: g.items.reduce((s, i) => s + i.quantity, 0),
      selected: cartStore.selectedStoreIds.includes(g.storeId),
    }))
    result.push({
      districtId: parseInt(did),
      districtName: districtName(parseInt(did)),
      stores: storeList,
    })
  }
  return result
})

const selectedCount = computed(() => cartStore.selectedCount)
const selectedTotal = computed(() => cartStore.selectedTotal)
const crossDistrict = computed(() => cartStore.crossDistrict)

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

function toggleStore(sid) {
  cartStore.toggleStore(sid)
}

function goCheckout(sid) {
  router.push(`/order-confirm?store_id=${sid}`)
}

function goCombined() {
  if (crossDistrict.value) {
    showToast({ message: '跨区店铺需分开结算', type: 'fail' })
    return
  }
  const ids = cartStore.selectedStoreIds.join(',')
  if (!ids) {
    showToast({ message: '请选择要结算的店铺', type: 'fail' })
    return
  }
  router.push(`/order-confirm?store_ids=${ids}`)
}

function goSelectAll() {
  if (cartStore.selectedStoreIds.length === cartStore.storeIds.length) {
    cartStore.deselectAll()
  } else {
    cartStore.selectAll()
  }
}

const allSelected = computed(() =>
  cartStore.storeIds.length > 0 && cartStore.selectedStoreIds.length === cartStore.storeIds.length
)
</script>

<template>
  <div class="page">
    <van-nav-bar title="购物车" left-text="返回" left-arrow @click-left="$router.back()" fixed placeholder />

    <div v-if="grouped.length === 0" class="text-center p-4" style="margin-top:40%">
      <p class="text-xl text-gray mb-4">购物车是空的</p>
      <van-button type="primary" round color="#ff6b35" @click="$router.replace('/')">去首页逛逛</van-button>
    </div>

    <div v-for="dg in grouped" :key="dg.districtId">
      <!-- 分区标题 -->
      <div class="px-3 pt-3 pb-1 text-sm font-bold" style="color:#ff6b35">
        {{ dg.districtName }}
      </div>

      <div v-for="g in dg.stores" :key="g.storeId" class="bg-white mx-3 mb-3 rounded-lg shadow overflow-hidden">
        <!-- 店铺头部 -->
        <div class="flex items-center p-3" style="border-bottom:1px solid #f5f5f5">
          <van-checkbox :model-value="g.selected" @change="toggleStore(g.storeId)" />
          <span class="font-bold ml-2 flex-1">{{ g.storeName }}</span>
          <van-button size="small" plain type="danger" @click="clearStore(g.storeId)">清空</van-button>
        </div>

        <!-- 商品列表 -->
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
          <span class="text-sm text-gray" style="cursor:pointer" @click="removeItem(g.storeId, item.productId)">删除</span>
        </div>

        <!-- 店铺小计 -->
        <div class="flex items-center justify-between p-3">
          <span class="text-sm text-gray">小计 ¥{{ g.subtotal.toFixed(2) }}</span>
          <van-button size="small" type="primary" round color="#ff6b35" @click="goCheckout(g.storeId)">单店结算</van-button>
        </div>
      </div>
    </div>

    <!-- 跨区提示 -->
    <div v-if="crossDistrict && selectedCount > 0" class="mx-3 p-3 rounded text-center text-sm"
      style="background:#FFF3E0;color:#E65100">
      已选店铺跨不同配送区域，需分开结算
    </div>

    <!-- 底部结算栏 -->
    <div v-if="grouped.length > 0" class="bg-white p-3 shadow flex items-center"
      style="position:fixed;bottom:0;left:0;right:0;z-index:100;padding-bottom:env(safe-area-inset-bottom)">
      <div class="flex items-center flex-1" style="cursor:pointer" @click="goSelectAll">
        <van-checkbox :model-value="allSelected" />
        <span class="text-sm text-gray ml-2">全选</span>
      </div>
      <div class="text-right">
        <div v-if="selectedCount > 0">
          <span class="text-sm text-gray">已选{{ selectedCount }}件</span>
          <span class="text-primary font-bold text-lg ml-2">¥{{ selectedTotal.toFixed(2) }}</span>
        </div>
        <div v-else class="text-sm text-gray">请选择店铺</div>
      </div>
      <van-button type="primary" round color="#ff6b35" class="ml-3" style="height:44px;min-width:100px"
        :disabled="selectedCount === 0" @click="goCombined">
        合并结算
      </van-button>
    </div>

    <div style="height:60px" />
  </div>
</template>
