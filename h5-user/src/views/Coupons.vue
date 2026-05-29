<script setup>
import { ref, onMounted } from 'vue'
import { showToast } from 'vant'
import { api } from '../utils/api'

const activeTab = ref('available')
const availableList = ref([])
const myList = ref([])

async function loadAvailable() {
  try { availableList.value = await api.get('/api/user/coupons/available') } catch { }
}
async function loadMy() {
  try { myList.value = await api.get('/api/user/coupons/my') } catch { }
}

onMounted(loadAvailable)

function switchTab(tab) {
  if (tab === activeTab.value) return
  activeTab.value = tab
  tab === 'available' ? loadAvailable() : loadMy()
}

async function claimCoupon(id) {
  try {
    await api.post(`/api/user/coupons/${id}/claim`)
    showToast({ message: '领取成功', type: 'success' })
    loadAvailable()
  } catch { }
}
</script>

<template>
  <div class="page">
    <van-nav-bar title="优惠券中心" left-text="返回" left-arrow @click-left="$router.back()" fixed placeholder />
    <van-tabs v-model:active="activeTab" @change="switchTab">
      <van-tab title="可领取" name="available">
        <div v-if="availableList.length === 0" class="text-center text-gray p-4">暂无可用优惠券</div>
        <div v-for="c in availableList" :key="c.id" class="bg-white m-3 p-3 rounded shadow">
          <div class="flex items-center">
            <div class="text-primary font-bold" style="font-size:24px">¥{{ c.discount_amount }}</div>
            <div class="ml-3 flex-1">
              <div class="font-bold">{{ c.title || c.name }}</div>
              <div class="text-sm text-gray mt-1" v-if="c.condition_amount > 0">满¥{{ c.condition_amount }}可用</div>
            </div>
            <van-button size="small" round type="primary" color="#ff6b35" @click="claimCoupon(c.id)">领取</van-button>
          </div>
        </div>
      </van-tab>
      <van-tab title="我的" name="my">
        <div v-if="myList.length === 0" class="text-center text-gray p-4">还没有优惠券</div>
        <div v-for="c in myList" :key="c.id || c.user_coupon_id"
          class="bg-white m-3 p-3 rounded shadow"
          :style="{ opacity: c.status === 'used' ? 0.5 : 1 }">
          <div class="flex items-center">
            <div class="text-gray font-bold" style="font-size:24px">¥{{ c.discount_amount }}</div>
            <div class="ml-3 flex-1">
              <div class="font-bold">{{ c.title || c.name }}</div>
              <div class="text-sm text-gray mt-1">状态：{{ c.status === 'unused' ? '未使用' : c.status === 'used' ? '已使用' : '已过期' }}</div>
            </div>
          </div>
        </div>
      </van-tab>
    </van-tabs>
  </div>
</template>
