<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { api } from '../utils/api'
import { authStore } from '../stores/auth'

const router = useRouter()

const form = ref({
  id: null,
  contact_name: '',
  contact_phone: '',
  gender: 1,
  province: '',
  city: '',
  district: '',
  detail: '',
  label: '',
  is_default: 0,
})
const isEdit = ref(false)

// 从路由参数判断是否编辑
import { useRoute } from 'vue-router'
const route = useRoute()
const addrId = route.params.id

if (addrId) {
  isEdit.value = true
  loadAddress(addrId)
}

async function loadAddress(id) {
  try {
    const addresses = await api.get('/api/user/addresses')
    const addr = addresses.find(a => a.id == id)
    if (addr) form.value = { ...addr }
  } catch { }
}

async function onSubmit() {
  const f = form.value
  if (!f.contact_name || !f.contact_phone || !f.detail) {
    showToast({ message: '请填写必填项', type: 'fail' })
    return
  }
  try {
    if (isEdit.value) {
      await api.put(`/api/user/addresses/${f.id}`, f)
    } else {
      await api.post('/api/user/addresses', f)
    }
    showToast({ message: '保存成功', type: 'success' })
    setTimeout(() => router.back(), 500)
  } catch { }
}
</script>

<template>
  <div class="page">
    <van-nav-bar :title="isEdit ? '编辑地址' : '新增地址'" left-text="返回" left-arrow @click-left="$router.back()" fixed placeholder />
    <div class="p-3">
      <van-cell-group inset>
        <van-field v-model="form.contact_name" label="联系人" placeholder="请输入联系人姓名" required />
        <van-field v-model="form.contact_phone" label="手机号" type="tel" maxlength="11" placeholder="请输入手机号" required />
        <van-field v-model="form.province" label="省份" placeholder="省份" />
        <van-field v-model="form.city" label="城市" placeholder="城市" />
        <van-field v-model="form.district" label="区县" placeholder="区县" />
        <van-field v-model="form.detail" label="详细地址" type="textarea" rows="2" placeholder="街道/小区/门牌号" required />
        <van-field v-model="form.label" label="标签" placeholder="如：公司、家" />
      </van-cell-group>
      <div class="p-3">
        <van-button type="primary" block round color="#ff6b35" @click="onSubmit" style="height:44px">保存</van-button>
      </div>
    </div>
  </div>
</template>
