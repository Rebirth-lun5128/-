<template>
  <div class="page">
    <van-nav-bar title="订单详情" left-text="返回" left-arrow @click-left="$router.back()" />
    <van-loading v-if="!order" class="loading" />
    <template v-else>
      <van-cell-group inset>
        <van-cell title="订单状态" :value="statusText(order.status)" />
        <van-cell title="订单金额" :value="'¥' + order.items_total" />
        <van-cell v-for="item in (order.items || [])" :key="item.id" :title="item.name" :value="'x' + item.quantity + ' ¥' + item.price" />
        <van-cell title="备注" :value="order.remark || '无'" />
      </van-cell-group>

      <!-- 操作按钮 -->
      <div class="actions" v-if="order.status">
        <van-button v-if="order.status === 'pending_accept'" round block type="primary" @click="acceptOrder">✅ 接受订单</van-button>
        <van-button v-if="order.status === 'pending_accept'" round block type="danger" @click="rejectOrder" style="margin-top:8px">❌ 拒单</van-button>
        <van-button v-if="order.status === 'preparing'" round block type="warning" @click="markReady">📦 已出餐</van-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { merchantApi } from '../../utils/api.js'
import { showToast, showConfirmDialog } from 'vant'

const route = useRoute()
const order = ref(null)
const orderId = ref(route.params.id)

const statusText = (s) => {
  const map = { pending_accept: '待接单', preparing: '备餐中', ready: '已出餐', delivering: '配送中', completed: '已完成', cancelled: '已取消' }
  return map[s] || s
}

const load = async () => {
  try {
    order.value = await merchantApi.get(`/api/merchant/orders/${orderId.value}`)
  } catch {}
}

const acceptOrder = async () => {
  try { await merchantApi.put(`/api/merchant/orders/${orderId.value}/accept`); showToast('已接单'); load(); } catch {}
}
const rejectOrder = async () => {
  try { await showConfirmDialog({ title: '拒单', message: '确定拒接此单吗？' }) } catch { return }
  try { await merchantApi.put(`/api/merchant/orders/${orderId.value}/reject?reason=商家拒单`); showToast('已拒单'); load(); } catch {}
}
const markReady = async () => {
  try { await merchantApi.put(`/api/merchant/orders/${orderId.value}/ready`); showToast('已出餐'); load(); } catch {}
}

onMounted(load)
</script>

<style scoped>
.page { min-height: 100vh; background: #f7f8fa; }
.loading { display: flex; justify-content: center; padding-top: 100px; }
.actions { padding: 16px; }
</style>
