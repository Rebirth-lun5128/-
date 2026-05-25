<template>
  <div class="login-page">
    <div class="login-card">
      <h2>外卖平台管理后台</h2>
      <el-form :model="form" label-position="top">
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-button type="primary" size="large" style="width:100%" @click="doLogin" :loading="loading">
          登录
        </el-button>
      </el-form>
      <p class="tip">请使用已注册的手机号和密码登录</p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import http from '../api'

const router = useRouter()
const loading = ref(false)
const form = reactive({ phone: '', password: '' })

async function doLogin() {
  if (!form.phone || !form.password) {
    ElMessage.warning('请填写手机号和密码')
    return
  }
  loading.value = true
  try {
    const res = await http.post('/common/auth/phone', form)
    localStorage.setItem('admin_token', res.token)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (e) { } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f0f2f5;
}
.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}
.login-card h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
}
.tip {
  text-align: center;
  margin-top: 16px;
  color: #999;
  font-size: 13px;
}
</style>
