<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { api } from '../utils/api'
import { authStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const phone = ref('')
const password = ref('')
const loading = ref(false)
const agreed = ref(false)

async function handleLogin() {
  if (!agreed.value) {
    showToast({ message: '请先阅读并同意用户协议和隐私政策', type: 'fail' })
    return
  }
  if (!phone.value.trim()) {
    showToast({ message: '请输入手机号', type: 'fail' })
    return
  }
  loading.value = true
  try {
    const res = await api.post('/api/common/auth/phone', {
      phone: phone.value.trim(),
      password: password.value || '123456',
      role: 'user',
    })
    authStore.login(res.token, res.user)
    showToast({ message: '登录成功', type: 'success' })
    const redirect = route.query.redirect || '/'
    setTimeout(() => router.replace(redirect), 500)
  } catch { } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page flex flex-col items-center justify-center" style="min-height:100vh">
    <div class="p-4" style="width:100%;max-width:360px">
      <h1 class="text-2xl font-bold text-center mb-4" style="color:#ff6b35">社区夜市</h1>
      <p class="text-center text-gray mb-4">登录后开始点餐</p>
      <van-cell-group inset>
        <van-field v-model="phone" type="tel" maxlength="11" placeholder="请输入手机号"
          left-icon="phone-o" />
        <van-field v-model="password" type="password" placeholder="密码（默认123456）"
          left-icon="lock" @keyup.enter="handleLogin" />
      </van-cell-group>
      <div class="p-3">
        <van-button type="primary" block round :loading="loading" :disabled="!agreed"
          color="#ff6b35" @click="handleLogin" style="height:44px">
          登录
        </van-button>
      </div>
      <div style="display:flex;align-items:center;justify-content:center;margin-top:16px;font-size:13px;color:#999">
        <van-checkbox v-model="agreed" style="margin-right:4px" />
        <span>已阅读并同意</span>
        <router-link to="/agreement" style="color:#ff6b35;margin:0 2px">《用户服务协议》</router-link>
        <span>和</span>
        <router-link to="/privacy" style="color:#ff6b35;margin-left:2px">《隐私政策》</router-link>
      </div>
      <p class="text-center text-sm text-gray mt-2">测试账号：13800000099</p>
    </div>
  </div>
</template>
