<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showDialog } from 'vant'
import { api } from '../utils/api'
import { authStore } from '../stores/auth'

const router = useRouter()
const orderCount = ref(0)
const pendingCount = ref(0)
const deliveringCount = ref(0)
const couponCount = ref(0)
const loading = ref(false)

onMounted(loadStats)

async function loadStats() {
  loading.value = true
  try {
    await authStore.refreshUser()
    const [all, pending, delivering, coupons] = await Promise.all([
      api.get('/api/user/orders', { page: 1, page_size: 1, status: '' }, { silent: true }).catch(() => ({ total: 0 })),
      api.get('/api/user/orders', { page: 1, page_size: 1, status: 'pending_pay' }, { silent: true }).catch(() => ({ total: 0 })),
      api.get('/api/user/orders', { page: 1, page_size: 1, status: 'delivering' }, { silent: true }).catch(() => ({ total: 0 })),
      api.get('/api/user/coupons/my', {}, { silent: true }).catch(() => []),
    ])
    orderCount.value = all.total || 0
    pendingCount.value = pending.total || 0
    deliveringCount.value = delivering.total || 0
    couponCount.value = Array.isArray(coupons) ? coupons.filter(c => c.status === 'unused').length : 0
  } catch { } finally {
    loading.value = false
  }
}

async function logout() {
  try {
    await showDialog({ title: '退出登录', message: '确定要退出吗？' })
    authStore.logout()
    router.replace('/login')
  } catch { }
}

async function deleteAccount() {
  try {
    await showDialog({ title: '注销账号', message: '注销后账户将被禁用，手机号将被释放。\n确定要注销吗？' })
    await api.delete('/api/common/auth/account')
    showToast({ message: '账号已注销', type: 'success' })
    authStore.logout()
    router.replace('/login')
  } catch { }
}

const showShare = ref(false)
const shareText = '🔥 社区夜市外卖来啦！\n跨摊下单 · 一次配送 · 新鲜直达\n烧烤面食小吃一站购齐\n👉 https://yswm-1.cn/h5/'
const isWechat = /MicroMessenger/i.test(navigator.userAgent)

async function doShare() {
  const data = { title: '社区夜市外卖', text: '🔥 跨摊下单 · 一次配送 · 新鲜直达\n烧烤面食小吃一站购齐\n👉 https://yswm-1.cn/h5/', url: 'https://yswm-1.cn/h5/' }
  try {
    if (navigator.share) {
      await navigator.share(data)
    } else if (navigator.clipboard) {
      await navigator.clipboard.writeText(data.text)
      showToast('链接已复制，去粘贴分享吧')
    } else {
      showShare.value = true
    }
  } catch (e) {
    // 用户取消或分享失败 → 弹备选方案
    if (e?.name !== 'AbortError') showShare.value = true
  }
}

function copyShare() {
  navigator.clipboard.writeText(shareText).then(() => showToast('已复制，去粘贴发送吧')).catch(() => showToast('长按手动复制'))
}

function goOrders(status) {
  router.replace('/orders')
  sessionStorage.setItem('orderFilter', status || '')
}

const userInfo = () => authStore.userInfo || { nickname: '食客', phone: '', avatar: '' }
</script>

<template>
  <div class="page">
    <van-nav-bar title="个人中心" fixed placeholder />

    <!-- 用户信息 -->
    <div class="bg-white p-4 flex items-center" style="background:linear-gradient(135deg, #ff6b35, #ff8f66);color:#fff">
      <van-image :src="userInfo().avatar" width="60" height="60" fit="cover" round lazy-load
        style="border:2px solid rgba(255,255,255,0.5)" />
      <div class="ml-3 flex-1">
        <div class="font-bold text-lg">{{ userInfo().nickname }}</div>
        <div class="text-sm mt-1" style="opacity:0.8">{{ userInfo().phone || '未绑定手机号' }}</div>
      </div>
      <span class="text-sm" style="opacity:0.8;cursor:pointer" @click="router.push('/profile-edit')">编辑 ›</span>
    </div>

    <!-- 订单统计 -->
    <div class="bg-white mt-2 p-3">
      <div class="flex text-center">
        <div class="flex-1" style="cursor:pointer" @click="goOrders('')">
          <div class="text-xl font-bold">{{ orderCount }}</div>
          <div class="text-sm text-gray mt-1">全部订单</div>
        </div>
        <div class="flex-1" style="cursor:pointer" @click="goOrders('pending_pay')">
          <div class="text-xl font-bold" style="color:#FF9800">{{ pendingCount }}</div>
          <div class="text-sm text-gray mt-1">待付款</div>
        </div>
        <div class="flex-1" style="cursor:pointer" @click="goOrders('delivering')">
          <div class="text-xl font-bold" style="color:#2196F3">{{ deliveringCount }}</div>
          <div class="text-sm text-gray mt-1">配送中</div>
        </div>
        <div class="flex-1" style="cursor:pointer" @click="router.push('/coupons')">
          <div class="text-xl font-bold" style="color:#ff6b35">{{ couponCount }}</div>
          <div class="text-sm text-gray mt-1">优惠券</div>
        </div>
      </div>
    </div>

    <!-- 菜单 -->
    <div class="bg-white mt-2">
      <van-cell title="收货地址" icon="location-o" is-link @click="router.push('/address')" />
      <van-cell title="优惠券中心" icon="coupon-o" is-link @click="router.push('/coupons')" />
      <van-cell title="购物车" icon="cart-o" is-link @click="router.push('/cart')" />
      <van-cell title="分享给朋友" icon="share-o" is-link @click="doShare" />
      <van-cell title="联系客服" icon="service-o" is-link @click="showDialog({ title:'联系客服', message:'客服电话：138-0000-0000\n工作时间：17:00 - 00:00' })" />
    </div>
    <div class="bg-white mt-2">
      <van-cell title="关于夜市外卖" icon="info-o" is-link @click="showDialog({ title:'关于', message:'社区夜市外卖平台\n版本：2.0.0' })" />
    </div>

    <div class="p-3">
      <van-button block round plain type="danger" @click="logout" style="height:44px">退出登录</van-button>
    </div>
    <div class="p-2 text-center">
      <span style="color:#E53935;opacity:0.6;font-size:13px" @click="deleteAccount">注销账号</span>
    </div>

    <div style="height:60px" />

    <!-- 分享弹窗 -->
    <van-popup v-model:show="showShare" round position="bottom" :style="{ padding: '24px 20px' }" :close-on-click-overlay="true">
      <h3 style="text-align:center;margin-bottom:16px">📤 分享给朋友</h3>
      <div style="background:linear-gradient(135deg,#ff6b35,#ff8f66);border-radius:12px;padding:20px;color:#fff;text-align:center;margin-bottom:16px">
        <div style="font-size:40px;margin-bottom:8px">🌙🔥</div>
        <div style="font-size:20px;font-weight:bold;margin-bottom:6px">社区夜市外卖</div>
        <div style="font-size:13px;opacity:0.9;margin-bottom:4px">跨摊下单 · 一次配送 · 新鲜直达</div>
        <div style="font-size:12px;opacity:0.7">烧烤 · 面食 · 小吃 · 一站购齐</div>
        <div style="margin-top:12px;padding:8px 12px;background:rgba(255,255,255,0.2);border-radius:8px;font-size:12px;word-break:break-all">
          yswm-1.cn/h5
        </div>
      </div>
      <van-button round block type="primary" color="#ff6b35" @click="copyShare">📋 复制文案和链接</van-button>
      <p style="text-align:center;color:#999;font-size:12px;margin-top:8px">复制后去微信粘贴发送即可</p>
    </van-popup>
  </div>
</template>
