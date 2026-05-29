<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { api } from '../utils/api'
import { cartStore } from '../stores/cart'

const route = useRoute()
const router = useRouter()
const restaurant = ref(null)
const categories = ref([])
const activeCategory = ref(0)
const scrollToCategory = ref('')

onMounted(() => loadRestaurant(route.params.id))

async function loadRestaurant(id) {
  try {
    const res = await api.get(`/api/user/stores/${id}`)
    restaurant.value = res
    categories.value = res.categories || []
  } catch { }
}

function onCategoryTap(index) {
  activeCategory.value = index
  scrollToCategory.value = `cat-${index}`
}

function addToCart(product) {
  cartStore.addItem({
    productId: product.id,
    storeId: parseInt(route.params.id),
    storeName: restaurant.value?.name || '未知店铺',
    name: product.name,
    image: product.image,
    price: product.price,
    quantity: 1,
  })
  showToast({ message: '已加入购物车', type: 'success', duration: 800 })
}

function getCartQty(productId) {
  const item = cartStore.items.find(i => i.productId === productId && i.storeId === parseInt(route.params.id))
  return item ? item.quantity : 0
}

function reduceCart(productId) {
  cartStore.updateQuantity(productId, parseInt(route.params.id), getCartQty(productId) - 1)
}

const storeCartTotal = () => cartStore.items
  .filter(i => i.storeId === parseInt(route.params.id))
  .reduce((s, i) => s + i.price * i.quantity, 0)
const storeCartCount = () => cartStore.items
  .filter(i => i.storeId === parseInt(route.params.id))
  .reduce((s, i) => s + i.quantity, 0)

function goToConfirm() {
  if (storeCartCount() === 0) {
    showToast({ message: '请先添加菜品', type: 'fail' })
    return
  }
  router.push(`/order-confirm?store_id=${route.params.id}`)
}
</script>

<template>
  <div class="page" v-if="restaurant">
    <!-- 店铺头部 -->
    <div class="bg-white p-3">
      <van-nav-bar :title="restaurant.name" left-text="返回" left-arrow @click-left="$router.back()" />
      <van-image :src="restaurant.logo" height="160" fit="cover" round style="width:100%" lazy-load />
      <div class="flex items-center justify-between mt-3">
        <div>
          <h2 class="font-bold text-xl">{{ restaurant.name }}</h2>
          <p class="text-sm text-gray mt-1">{{ restaurant.description || restaurant.address }}</p>
          <div class="flex items-center mt-1">
            <span class="text-primary text-sm">★ {{ restaurant.rating || 4.5 }}</span>
            <span class="text-sm text-gray ml-2">月售{{ restaurant.monthly_sales || 0 }}</span>
            <span class="text-sm text-gray ml-2">¥{{ restaurant.delivery_fee || 0 }}配送</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 分类导航 -->
    <div class="bg-white mt-2" style="position:sticky;top:0;z-index:50">
      <div class="flex" style="overflow-x:auto">
        <div v-for="(c, i) in categories" :key="c.id"
          class="px-4 py-3 text-center flex-shrink-0" style="font-size:14px;cursor:pointer;min-width:60px"
          :style="{ color: activeCategory === i ? '#ff6b35' : '#666', borderBottom: activeCategory === i ? '2px solid #ff6b35' : '2px solid transparent' }"
          @click="onCategoryTap(i)">
          {{ c.name }}
        </div>
      </div>
    </div>

    <!-- 菜品列表 -->
    <div class="pb-4">
      <div v-for="(c, catIndex) in categories" :key="c.id" :id="`cat-${catIndex}`">
        <div class="px-3 py-2 font-bold text-lg bg-white mt-2">{{ c.name }}</div>
        <div v-for="p in (c.products || [])" :key="p.id"
          class="bg-white mx-2 mb-1 p-3 flex items-center rounded" style="cursor:pointer">
          <van-image :src="p.image" width="64" height="64" fit="cover" round style="flex-shrink:0" lazy-load />
          <div class="ml-3 flex-1" style="min-width:0">
            <div class="font-bold">{{ p.name }}</div>
            <div class="text-sm text-gray mt-1" style="line-clamp:1">{{ p.description || '' }}</div>
            <div class="text-sm text-gray mt-1">月售{{ p.monthly_sales || 0 }}</div>
            <div class="flex items-center justify-between mt-2">
              <span class="text-primary font-bold text-lg">¥{{ p.price }}</span>
              <div class="flex items-center" @click.stop>
                <span v-if="getCartQty(p.id) > 0"
                  class="flex items-center justify-center rounded-full"
                  style="width:24px;height:24px;border:1px solid #ff6b35;color:#ff6b35;cursor:pointer"
                  @click="reduceCart(p.id)">−</span>
                <span v-if="getCartQty(p.id) > 0" class="mx-2 text-sm" style="min-width:16px;text-align:center">
                  {{ getCartQty(p.id) }}
                </span>
                <span class="flex items-center justify-center rounded-full"
                  style="width:24px;height:24px;background:#ff6b35;color:#fff;cursor:pointer"
                  @click="addToCart(p)">+</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="categories.length === 0" class="text-center text-gray p-4">暂无菜品</div>
    </div>

    <!-- 底部购物车栏 -->
    <div v-if="storeCartCount() > 0" class="bg-white p-3 shadow flex items-center"
      style="position:fixed;bottom:0;left:0;right:0;z-index:100;padding-bottom:env(safe-area-inset-bottom)">
      <div class="flex-1">
        <span class="font-bold text-lg">¥{{ storeCartTotal().toFixed(2) }}</span>
        <span class="text-sm text-gray ml-2">{{ storeCartCount() }}件</span>
      </div>
      <van-button type="primary" round color="#ff6b35" @click="goToConfirm" style="height:40px">去结算</van-button>
    </div>
  </div>
</template>
