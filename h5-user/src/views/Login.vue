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
const confirmPwd = ref('')
const loading = ref(false)
const agreed = ref(false)
const isRegister = ref(false)

async function handleSubmit() {
  if (!agreed.value) {
    showToast({ message: '请先阅读并同意用户协议和隐私政策', type: 'fail' })
    return
  }
  if (!phone.value.trim() || !password.value) {
    showToast({ message: '请填写手机号和密码', type: 'fail' })
    return
  }
  if (!/^1\d{10}$/.test(phone.value.trim())) {
    showToast({ message: '请输入正确的手机号', type: 'fail' })
    return
  }
  if (isRegister.value && password.value !== confirmPwd.value) {
    showToast({ message: '两次密码不一致', type: 'fail' })
    return
  }
  loading.value = true
  try {
    const url = isRegister.value ? '/api/common/auth/register' : '/api/common/auth/phone'
    const data = isRegister.value
      ? { phone: phone.value.trim(), password: password.value, role: 'user' }
      : { phone: phone.value.trim(), password: password.value, role: 'user' }
    const res = await api.post(url, data)
    authStore.login(res.token, res.user)
    showToast({ message: isRegister.value ? '注册成功' : '登录成功', type: 'success' })
    const redirect = route.query.redirect || '/'
    setTimeout(() => router.replace(redirect), 500)
  } catch { } finally {
    loading.value = false
  }
}

function toggleMode() {
  isRegister.value = !isRegister.value
  confirmPwd.value = ''
}
</script>

<template>
  <div class="page flex flex-col items-center justify-center" style="min-height:100vh">
    <div class="p-4" style="width:100%;max-width:360px">
      <h1 class="text-2xl font-bold text-center mb-4" style="color:#ff6b35">社区夜市</h1>
      <p class="text-center text-gray mb-4">{{ isRegister ? '注册账号' : '登录后开始点餐' }}</p>
      <van-cell-group inset>
        <van-field v-model="phone" type="tel" maxlength="11" placeholder="请输入手机号"
          left-icon="phone-o" />
        <van-field v-model="password" type="password" placeholder="请输入密码"
          left-icon="lock" @keyup.enter="handleSubmit" />
        <van-field v-if="isRegister" v-model="confirmPwd" type="password" placeholder="请确认密码"
          left-icon="lock" />
      </van-cell-group>
      <div class="p-3">
        <van-button type="primary" block round :loading="loading" :disabled="!agreed"
          color="#ff6b35" @click="handleSubmit" style="height:44px">
          {{ isRegister ? '注册' : '登录' }}
        </van-button>
      </div>
      <div style="display:flex;align-items:center;justify-content:center;margin-top:16px;font-size:13px;color:#999">
        <van-checkbox v-model="agreed" style="margin-right:4px" />
        <span>已阅读并同意</span>
        <router-link to="/agreement" style="color:#ff6b35;margin:0 2px">《用户服务协议》</router-link>
        <span>和</span>
        <router-link to="/privacy" style="color:#ff6b35;margin-left:2px">《隐私政策》</router-link>
      </div>
      <p class="text-center text-sm mt-3" style="color:#ff6b35;cursor:pointer" @click="toggleMode">
        {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
      </p>
    </div>
  </div>
</template>
