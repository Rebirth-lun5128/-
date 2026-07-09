<template>
  <div class="page">
    <div class="header">
      <h1>🛵 骑手中心</h1>
      <p>社区夜市配送平台</p>
    </div>
    <van-form @submit="doSubmit">
      <van-cell-group inset>
        <van-field v-model="phone" type="tel" label="手机号" placeholder="请输入手机号" maxlength="11" />
        <van-field v-model="password" type="password" label="密码" placeholder="请输入密码" />
        <van-field v-if="isRegister" v-model="confirmPwd" type="password" label="确认密码" placeholder="请确认密码" />
      </van-cell-group>
      <div style="margin: 16px">
        <van-button round block type="primary" native-type="submit" :loading="loading">{{ isRegister ? '注册' : '登录' }}</van-button>
      </div>
    </van-form>
    <div class="agreement">
      <van-checkbox v-model="agreed" shape="square" icon-size="14px">
        已阅读并同意 <router-link to="/agreement">《用户服务协议》</router-link> 和 <router-link to="/privacy">《隐私政策》</router-link>
      </van-checkbox>
    </div>
    <div style="margin-top:24px;text-align:center">
      <span style="color:#666;font-size:14px">{{ isRegister ? '已有账号？' : '还没有账号？' }}</span>
      <span style="color:#ff6b35;font-size:16px;font-weight:bold;cursor:pointer;margin-left:4px" @click="toggleMode">
        {{ isRegister ? '去登录' : '注册新账号' }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { riderApi } from '../../utils/api.js'
import { showToast } from 'vant'

const phone = ref('')
const password = ref('')
const confirmPwd = ref('')
const loading = ref(false)
const agreed = ref(false)
const isRegister = ref(false)

const toggleMode = () => {
  isRegister.value = !isRegister.value
  confirmPwd.value = ''
}

const doSubmit = async () => {
  if (!agreed.value) { showToast('请先阅读并同意协议'); return }
  if (!phone.value || !password.value) { showToast('请填写信息'); return }
  if (!/^1\d{10}$/.test(phone.value.trim())) { showToast('请输入正确的手机号'); return }
  if (isRegister.value && password.value !== confirmPwd.value) { showToast('两次密码不一致'); return }
  loading.value = true
  try {
    const url = isRegister.value ? '/api/common/auth/register' : '/api/common/auth/phone'
    const data = { phone: phone.value.trim(), password: password.value, role: 'rider' }
    const res = await riderApi.post(url, data)
    localStorage.setItem('rider_token', res.token)
    localStorage.setItem('rider_phone', phone.value)
    showToast(isRegister.value ? '注册成功' : '登录成功')
    window.location.hash = '#/r/dashboard'
  } catch {} finally { loading.value = false }
}
</script>

<style scoped>
.page { min-height: 100vh; background: #f7f8fa; padding-top: 60px; }
.header { text-align: center; margin-bottom: 30px; }
.header h1 { font-size: 24px; margin-bottom: 8px; }
.header p { color: #999; font-size: 14px; }
.agreement { display: flex; justify-content: center; margin-top: 20px; font-size: 12px; }
</style>
