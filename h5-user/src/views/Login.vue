<script setup>
import { ref, computed } from 'vue'
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
const rememberPwd = ref(true)  // 记住密码，默认开启

// 记住的上次登录信息
const lastPhone = localStorage.getItem('last_login_phone') || ''
const lastInfo = (() => {
  try { return JSON.parse(localStorage.getItem('userInfo') || 'null') } catch { return null }
})()
const showWelcome = computed(() => !isRegister.value && !!lastPhone)

// 自动填充：手机号 + 记住的密码
if (lastPhone && !phone.value) {
  phone.value = lastPhone
}
const rememberedPwd = localStorage.getItem('remembered_pwd')
if (rememberedPwd && lastPhone) {
  try { password.value = atob(rememberedPwd) } catch {}
}

function switchAccount() {
  phone.value = ''
  password.value = ''
  localStorage.removeItem('last_login_phone')
  localStorage.removeItem('remembered_pwd')
  localStorage.removeItem('remembered_phone')
}

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
    authStore.login(res.token, res.refresh_token, res.user)

    // 记住密码
    if (rememberPwd.value) {
      localStorage.setItem('remembered_phone', phone.value.trim())
      localStorage.setItem('remembered_pwd', btoa(password.value))
    } else {
      localStorage.removeItem('remembered_pwd')
      localStorage.removeItem('remembered_phone')
    }

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

      <!-- 欢迎回来卡片 -->
      <div v-if="showWelcome" class="mb-3"
        style="background:#fff;border-radius:12px;padding:16px;display:flex;align-items:center;box-shadow:0 2px 8px rgba(0,0,0,0.06)">
        <van-image v-if="lastInfo?.avatar" :src="lastInfo.avatar" width="48" height="48" fit="cover" round />
        <div v-else style="width:48px;height:48px;border-radius:50%;background:#ff6b35;color:#fff;display:flex;align-items:center;justify-content:center;font-size:20px">👋</div>
        <div class="ml-3 flex-1">
          <div class="font-bold" style="color:#333">{{ lastInfo?.nickname || '欢迎回来' }}</div>
          <div class="text-sm" style="color:#999">{{ lastPhone.slice(0,3) }}****{{ lastPhone.slice(-4) }}</div>
        </div>
        <span style="color:#ff6b35;font-size:13px;cursor:pointer" @click="switchAccount">切换账号</span>
      </div>

      <van-cell-group inset>
        <van-field v-model="phone" type="tel" maxlength="11" placeholder="请输入手机号"
          left-icon="phone-o" />
        <van-field v-model="password" type="password" placeholder="请输入密码"
          left-icon="lock" @keyup.enter="handleSubmit" />
        <van-field v-if="isRegister" v-model="confirmPwd" type="password" placeholder="请确认密码"
          left-icon="lock" />
      </van-cell-group>

      <!-- 记住密码（仅登录模式） -->
      <div v-if="!isRegister" style="display:flex;align-items:center;justify-content:space-between;padding:8px 16px 0">
        <van-checkbox v-model="rememberPwd" icon-size="16px" style="font-size:13px;color:#999">记住密码</van-checkbox>
      </div>

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
      <div style="margin-top:24px;text-align:center">
        <span style="color:#666;font-size:14px">{{ isRegister ? '已有账号？' : '还没有账号？' }}</span>
        <span style="color:#ff6b35;font-size:16px;font-weight:bold;cursor:pointer;margin-left:4px" @click="toggleMode">
          {{ isRegister ? '去登录' : '注册新账号' }}
        </span>
      </div>
    </div>
  </div>
</template>
