<template>
  <div class="page">
    <van-nav-bar title="订单详情" left-text="返回" left-arrow @click-left="$router.back()" />
    <van-loading v-if="!order" class="loading" />
    <template v-else>
      <van-cell-group inset>
        <van-cell title="订单状态" :value="statusText(order.status)" />
        <van-cell title="订单金额" :value="'¥' + order.total_price" />
        <van-cell title="配送费" :value="'¥' + (order.delivery_fee || 0)" />
        <van-cell title="取餐地址" :value="order.store_names || '夜市'" />
        <van-cell title="送达地址" :value="order.address_snapshot?.address || ''" />
        <van-cell v-if="order.address_snapshot?.name" title="收货人" :value="order.address_snapshot.name + ' ' + (order.user_phone || '')" />
      </van-cell-group>

      <div class="actions">
        <van-button v-if="order.status === 'pending'" round block type="primary" @click="acceptOrder">🛵 接单配送</van-button>
        <van-button v-if="order.status === 'delivering'" round block type="success" @click="deliverOrder">✅ 确认送达</van-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { riderApi } from '../../utils/api.js'
import { showToast, showConfirmDialog } from 'vant'

const route = useRoute()
const order = ref(null)
const orderId = ref(route.params.id)

const statusText = (s) => {
  const map = { pending: '待配送', delivering: '配送中', completed: '已完成', cancelled: '已取消' }
  return map[s] || s
}

const load = async () => {
  try {
    order.value = await riderApi.get(`/api/rider/orders/${orderId.value}`)
  } catch {}
}

const acceptOrder = async () => {
  try { await showConfirmDialog({ title: '接单确认', message: '确定接收此配送订单吗？' }) } catch { return }
  try { await riderApi.post(`/api/rider/orders/${orderId.value}/accept`); showToast('已接单'); load(); } catch {}
}
const deliverOrder = async () => {
  try { await showConfirmDialog({ title: '送达确认', message: '确认已送达该订单吗？' }) } catch { return }
  try { await riderApi.put(`/api/rider/orders/${orderId.value}/deliver`); showToast('已送达'); load(); } catch {}
}

onMounted(load)
</script>

<style scoped>
.page { min-height: 100vh; background: #f7f8fa; }
.loading { display: flex; justify-content: center; padding-top: 100px; }
.actions { padding: 16px; }
</style>
