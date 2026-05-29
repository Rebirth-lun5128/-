<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { api } from '../utils/api'
import { authStore } from '../stores/auth'

const router = useRouter()

const nickname = ref('')
const phone = ref('')
const avatar = ref('')
const originalNickname = ref('')
const originalPhone = ref('')
const originalAvatar = ref('')
const saving = ref(false)

onMounted(() => {
  const user = authStore.userInfo
  if (user) {
    nickname.value = user.nickname || ''
    phone.value = user.phone || ''
    avatar.value = user.avatar || ''
    originalNickname.value = user.nickname || ''
    originalPhone.value = user.phone || ''
    originalAvatar.value = user.avatar || ''
  }
})

const changed = () => nickname.value !== originalNickname.value || phone.value !== originalPhone.value || avatar.value !== originalAvatar.value

function chooseAvatar() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = (e) => {
    const file = e.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (ev) => { avatar.value = ev.target.result }
      reader.readAsDataURL(file)
    }
  }
  input.click()
}

async function onSave() {
  if (!changed() || saving.value) return
  const p = phone.value.trim()
  if (p && !/^1\d{10}$/.test(p)) {
    showToast({ message: '请输入正确的手机号', type: 'fail' })
    return
  }
  saving.value = true
  try {
    const body = {}
    if (nickname.value !== originalNickname.value) body.nickname = nickname.value.trim()
    if (phone.value !== originalPhone.value) body.phone = p
    if (avatar.value !== originalAvatar.value) body.avatar = avatar.value
    const res = await api.put('/api/common/auth/profile', body)
    authStore.updateUserInfo(res)
    showToast({ message: '保存成功', type: 'success' })
    setTimeout(() => router.back(), 800)
  } catch { } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="page">
    <van-nav-bar title="编辑资料" left-text="返回" left-arrow @click-left="$router.back()" fixed placeholder />
    <div class="p-3">
      <!-- 头像 -->
      <div class="flex items-center justify-center p-4" @click="chooseAvatar">
        <van-image :src="avatar" width="80" height="80" fit="cover" round lazy-load
          style="border:2px solid #eee;cursor:pointer" />
        <span class="text-sm text-gray ml-3">点击更换头像</span>
      </div>
      <van-cell-group inset>
        <van-field v-model="nickname" label="昵称" placeholder="请输入昵称" />
        <van-field v-model="phone" label="手机号" type="tel" maxlength="11" placeholder="请输入手机号" />
      </van-cell-group>
      <div class="p-3">
        <van-button type="primary" block round color="#ff6b35" :loading="saving"
          :disabled="!changed()" @click="onSave" style="height:44px">
          保存
        </van-button>
      </div>
    </div>
  </div>
</template>
