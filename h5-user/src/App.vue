<script setup>
import { useRouter, useRoute } from 'vue-router'
import { computed } from 'vue'

const router = useRouter()
const route = useRoute()

const tabs = [
  { name: 'Home', label: '首页', icon: 'home-o' },
  { name: 'Orders', label: '订单', icon: 'orders-o' },
  { name: 'Profile', label: '我的', icon: 'user-o' },
]

const active = computed(() => {
  const idx = tabs.findIndex((t) => t.name === route.name)
  return idx >= 0 ? idx : -1
})

function onTabChange(idx) {
  const tab = tabs[idx]
  if (tab) router.replace({ name: tab.name })
}
</script>

<template>
  <router-view v-slot="{ Component: C }">
    <keep-alive include="Home,Orders,Profile">
      <component :is="C" />
    </keep-alive>
  </router-view>
  <van-tabbar
    v-if="route.meta.tab !== undefined"
    :model-value="active"
    @update:model-value="onTabChange"
    active-color="#ff6b35"
    safe-area-inset-bottom
  >
    <van-tabbar-item v-for="t in tabs" :key="t.name" :icon="t.icon">
      {{ t.label }}
    </van-tabbar-item>
  </van-tabbar>
</template>

<style>
#app {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 50px;
}
</style>
