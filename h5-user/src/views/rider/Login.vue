<template>
  <div class="page">
    <div class="header">
      <h1>🛵 骑手登录</h1>
      <p>社区夜市配送平台</p>
    </div>
    <van-form @submit="doLogin">
      <van-cell-group inset>
        <van-field v-model="phone" type="tel" label="手机号" placeholder="请输入手机号" maxlength="11" />
        <van-field v-model="password" type="password" label="密码" placeholder="请输入密码" />
      </van-cell-group>
      <div style="margin: 16px">
        <van-button round block type="primary" native-type="submit" :loading="loading">登录</van-button>
      </div>
    </van-form>
    <div class="agreement">
      <van-checkbox v-model="agreed" shape="square" icon-size="14px">
        已阅读并同意
        <router-link to="/agreement">《用户服务协议》</router-link>
        和
        <router-link to="/privacy">《隐私政策》</router-link>
      </van-checkbox>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { riderApi } from '../../utils/api.js'
import { showToast } from 'vant'

const phone = ref('')
const password = ref('')
const loading = ref(false)
const agreed = ref(false)

const doLogin = async () => {
  if (!agreed.value) { showToast('请先阅读并同意协议'); return }
  if (!phone.value || !password.value) { showToast('请填写信息'); return }
  loading.value = true
  try {
    const res = await riderApi.post('/api/common/auth/phone', {
      phone: phone.value,
      password: password.value,
    })
    localStorage.setItem('rider_token', res.token)
    localStorage.setItem('rider_phone', phone.value)
    showToast('登录成功')
    window.location.hash = '#/r/dashboard'
  } catch {} finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page { min-height: 100vh; background: #f7f8fa; padding-top: 60px; }
.header { text-align: center; margin-bottom: 30px; }
.header h1 { font-size: 24px; margin-bottom: 8px; }
.header p { color: #999; font-size: 14px; }
.agreement { display: flex; justify-content: center; margin-top: 20px; font-size: 12px; }
</style>
