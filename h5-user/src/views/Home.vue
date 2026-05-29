<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../utils/api'

const router = useRouter()

const storeTypes = [
  { label: '全部', value: '' },
  { label: '夜市摊位', value: 'stall' },
  { label: '家庭厨房', value: 'home_kitchen' },
  { label: '平台自营', value: 'self_operated' },
]

const categories = [
  { name: '烧烤', icon: '🍖', keyword: '烧烤', bg: '#FFF3E0' },
  { name: '面食', icon: '🍜', keyword: '面', bg: '#FFF9E6' },
  { name: '饮品', icon: '🥤', keyword: '饮品', bg: '#E3F2FD' },
  { name: '小吃', icon: '🍢', keyword: '小吃', bg: '#FFF5F0' },
  { name: '炒菜', icon: '🥘', keyword: '炒菜', bg: '#E8F5E9' },
  { name: '甜点', icon: '🍰', keyword: '甜点', bg: '#FCE4EC' },
  { name: '水果', icon: '🍉', keyword: '水果', bg: '#E8F5E9' },
  { name: '全部', icon: '🏪', keyword: '', bg: '#F3E5F5' },
]

const activeType = ref('')
const keyword = ref('')
const stores = ref([])
const featuredStores = ref([])
const page = ref(1)
const total = ref(0)
const loading = ref(false)
const hasMore = ref(true)

onMounted(() => loadStores())

async function loadStores() {
  if (loading.value) return
  loading.value = true
  try {
    const params = { page: page.value, page_size: 10 }
    if (activeType.value) params.store_type = activeType.value
    if (keyword.value) params.keyword = keyword.value
    const res = await api.get('/api/user/stores', params)
    if (page.value === 1) {
      stores.value = res.items
      featuredStores.value = [...res.items].sort((a, b) => (b.rating || 0) - (a.rating || 0)).slice(0, 6)
    } else {
      stores.value = [...stores.value, ...res.items]
    }
    total.value = res.total
    page.value++
    hasMore.value = stores.value.length < res.total
  } catch { } finally {
    loading.value = false
  }
}

function onTypeTap(val) {
  if (val === activeType.value) return
  activeType.value = val
  keyword.value = ''
  page.value = 1
  stores.value = []
  hasMore.value = true
  loadStores()
}

function onCategoryTap(kw) {
  keyword.value = kw
  activeType.value = ''
  page.value = 1
  stores.value = []
  hasMore.value = true
  loadStores()
}

function onStoreTap(id) {
  router.push(`/restaurant/${id}`)
}

function onRefresh() {
  page.value = 1
  stores.value = []
  hasMore.value = true
  loadStores()
}

function onLoadMore() {
  if (hasMore.value && !loading.value) loadStores()
}
</script>

<template>
  <div class="page">
    <!-- 顶部搜索栏 -->
    <div class="bg-white p-2" style="position:sticky;top:0;z-index:100;padding-top:env(safe-area-inset-top)">
      <van-search v-model="keyword" shape="round" placeholder="搜索店铺或菜品"
        @search="onCategoryTap(keyword)" />
    </div>

    <!-- 类型筛选 -->
    <div class="bg-white px-2 pb-2">
      <div class="flex" style="overflow-x:auto;gap:8px">
        <div v-for="t in storeTypes" :key="t.value"
          class="text-center p-2 rounded" style="min-width:64px;font-size:13px;cursor:pointer"
          :style="{ background: activeType === t.value ? '#ff6b35' : '#f5f5f5', color: activeType === t.value ? '#fff' : '#666' }"
          @click="onTypeTap(t.value)">
          {{ t.label }}
        </div>
      </div>
    </div>

    <!-- 品类图标区 -->
    <div class="bg-white mt-2 p-3">
      <div class="flex" style="flex-wrap:wrap;gap:8px">
        <div v-for="c in categories" :key="c.name"
          class="flex flex-col items-center justify-center rounded"
          style="width:calc(25% - 6px);aspect-ratio:1;cursor:pointer"
          :style="{ background: c.bg }"
          @click="onCategoryTap(c.keyword)">
          <span style="font-size:28px">{{ c.icon }}</span>
          <span class="text-sm mt-1">{{ c.name }}</span>
        </div>
      </div>
    </div>

    <!-- 热销推荐 -->
    <div v-if="featuredStores.length" class="bg-white mt-2 p-3">
      <h3 class="font-bold text-lg mb-3">🔥 热销推荐</h3>
      <div class="flex" style="overflow-x:auto;gap:12px">
        <div v-for="s in featuredStores" :key="s.id"
          class="rounded shadow overflow-hidden" style="min-width:150px;cursor:pointer"
          @click="onStoreTap(s.id)">
          <van-image :src="s.logo" width="150" height="100" fit="cover" lazy-load />
          <div class="p-2">
            <div class="font-bold text-sm" style="line-clamp:1">{{ s.name }}</div>
            <div class="flex items-center mt-1">
              <span class="text-primary text-sm">★ {{ s.rating || 4.5 }}</span>
              <span class="text-sm text-gray ml-1">月售{{ s.monthly_sales || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 店铺列表 -->
    <div class="mt-2">
      <van-list v-model:loading="loading" :finished="!hasMore" finished-text="— 全部店铺已加载 —"
        @load="loadStores" @refresh="onRefresh">
        <div v-for="s in stores" :key="s.id"
          class="bg-white mb-2 mx-2 rounded overflow-hidden shadow flex p-3"
          style="cursor:pointer" @click="onStoreTap(s.id)">
          <van-image :src="s.logo" width="80" height="80" fit="cover" round style="flex-shrink:0" lazy-load />
          <div class="ml-3 flex-1" style="min-width:0">
            <div class="font-bold text-lg">{{ s.name }}</div>
            <div class="text-sm text-gray mt-1" style="line-clamp:1">{{ s.description || s.address }}</div>
            <div class="flex items-center justify-between mt-2">
              <div class="flex items-center">
                <span class="text-primary text-sm">★ {{ s.rating || 4.5 }}</span>
                <span class="text-sm text-gray ml-2">月售{{ s.monthly_sales || 0 }}</span>
                <span class="text-sm ml-2 px-2 rounded" style="background:#FFF3E0;color:#ff6b35">{{ s.category || '小吃' }}</span>
              </div>
              <span class="text-sm text-gray">¥{{ s.min_price || 0 }}起送</span>
            </div>
          </div>
        </div>
      </van-list>
    </div>

    <div style="height:60px" />
  </div>
</template>
