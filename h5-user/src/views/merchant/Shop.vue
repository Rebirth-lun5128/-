<template>
  <div class="page">
    <van-nav-bar :title="isRegister ? '店铺入驻' : '店铺设置'" left-text="返回" left-arrow @click-left="$router.back()" />

    <van-cell-group inset title="基本信息">
      <van-field v-model="form.name" label="店铺名称" placeholder="请输入店铺名称" required />
      <van-field v-model="form.phone" label="联系电话" placeholder="店铺联系电话" />
      <van-field v-model="form.address" label="店铺地址" placeholder="请输入地址" />
      <van-field v-model="form.category" label="经营品类" placeholder="如：烧烤、面食、小吃" />
    </van-cell-group>

    <van-cell-group inset title="配送设置">
      <van-field v-model="form.min_price" type="number" label="起送价(元)" placeholder="0" />
      <van-field v-model="form.delivery_time" label="预计送达" placeholder="30分钟" />
      <van-field v-model="form.notice" label="店铺公告" placeholder="给顾客的留言" />
    </van-cell-group>

    <van-cell-group inset title="店铺类型">
      <van-field label="类型" readonly :value="form.store_type === 'stall' ? '夜市摊位' : form.store_type === 'home_kitchen' ? '家庭厨房' : '平台自营'" is-link @click="showTypePicker = true" />
      <van-field v-if="form.store_type === 'stall'" v-model="form.stall_location" label="出摊位置" placeholder="夜市内具体位置" />
    </van-cell-group>

    <van-cell-group inset title="营业执照（选填）" v-if="isRegister">
      <van-field label="证件照片">
        <template #input>
          <div style="display:flex;align-items:center;gap:8px">
            <van-image v-if="form.id_card_photo" :src="form.id_card_photo" width="60" height="40" fit="cover" radius="4" />
            <span v-if="form.id_card_photo" @click="form.id_card_photo = ''" style="color:#ee0a24;font-size:12px;cursor:pointer">删除</span>
            <input type="file" accept="image/*" @change="onUploadIdCard" style="font-size:12px" />
          </div>
        </template>
      </van-field>
    </van-cell-group>

    <div style="padding:16px">
      <van-button round block type="primary" :loading="loading" @click="onSubmit">
        {{ isRegister ? '提交入驻申请' : '保存修改' }}
      </van-button>
      <div style="margin-top:12px;text-align:center;font-size:12px;color:#999" v-if="isRegister">
        提交后需等待管理员审核
      </div>
    </div>

    <!-- 类型选择器 -->
    <van-popup v-model:show="showTypePicker" position="bottom">
      <van-picker :columns="['夜市摊位', '家庭厨房', '平台自营']" :default-index="typeIndex" @confirm="onTypeConfirm" @cancel="showTypePicker = false" />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { merchantApi } from '../../utils/api.js'
import { showToast } from 'vant'

const route = useRoute()
const isRegister = ref(route.query.register === '1')
const loading = ref(false)
const showTypePicker = ref(false)
const typeIndex = ref(0)
const typeKeys = ['stall', 'home_kitchen', 'self_operated']

const form = ref({
  store_type: 'stall',
  name: '', phone: '', address: '', category: '',
  stall_location: '', id_card_photo: '',
  min_price: '', delivery_time: '30分钟', notice: '',
})

const load = async () => {
  if (isRegister.value) return
  try {
    const shop = await merchantApi.get('/api/merchant/shop')
    const idx = typeKeys.indexOf(shop.store_type || 'stall')
    typeIndex.value = idx >= 0 ? idx : 0
    form.value = {
      store_type: shop.store_type || 'stall',
      name: shop.name || '', phone: shop.phone || '', address: shop.address || '',
      category: shop.category || '', stall_location: shop.stall_location || '',
      id_card_photo: shop.id_card_photo || '',
      min_price: shop.min_price ? String(shop.min_price) : '',
      delivery_time: shop.delivery_time || '30分钟', notice: shop.notice || '',
    }
  } catch {}
}

const onUploadIdCard = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  const token = localStorage.getItem('merchant_token')
  try {
    const res = await fetch('/api/common/upload', { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: fd })
    const data = await res.json()
    if (data.url) form.value.id_card_photo = data.url
  } catch {}
}

const onTypeConfirm = ({ selectedOptions }) => {
  const idx = selectedOptions[0]?.index || 0
  typeIndex.value = idx
  form.value.store_type = typeKeys[idx]
  showTypePicker.value = false
}

const onSubmit = async () => {
  if (!form.value.name) { showToast('请填写店铺名称'); return }
  if (!form.value.phone) { showToast('请填写联系电话'); return }
  loading.value = true
  try {
    const data = {
      store_type: form.value.store_type,
      name: form.value.name, phone: form.value.phone,
      address: form.value.address, category: form.value.category,
      stall_location: form.value.stall_location, id_card_photo: form.value.id_card_photo,
      min_price: parseFloat(form.value.min_price) || 0,
      delivery_time: form.value.delivery_time, notice: form.value.notice,
      status: 'closed',
    }
    if (isRegister.value) {
      await merchantApi.post('/api/merchant/shop/register', data)
      showToast('入驻申请已提交，等待审核')
    } else {
      await merchantApi.put('/api/merchant/shop', data)
      showToast('保存成功')
    }
    setTimeout(() => window.location.hash = '#/m/dashboard', 800)
  } catch {} finally { loading.value = false }
}

onMounted(() => {
  if (!isRegister.value && !localStorage.getItem('merchant_token')) { window.location.hash = '#/m/login'; return }
  load()
})
</script>

<style scoped>
.page { min-height: 100vh; background: #f7f8fa; padding-bottom: 20px; }
</style>
