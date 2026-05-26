<template>
  <div class="login-page">
    <!-- 装饰背景 -->
    <div class="login-bg">
      <div class="bg-shape shape-1"></div>
      <div class="bg-shape shape-2"></div>
      <div class="bg-shape shape-3"></div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card">
      <div class="login-brand">
        <div class="brand-icon-wrap">
          <span class="brand-icon">🍜</span>
        </div>
        <h2 class="brand-title">夜市管理后台</h2>
        <p class="brand-sub">社区外卖平台 · 商家管理中心</p>
      </div>

      <el-form :model="form" label-position="top" class="login-form">
        <el-form-item label="手机号">
          <el-input
            v-model="form.phone"
            placeholder="请输入手机号"
            size="large"
            class="login-input"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
            size="large"
            class="login-input"
            @keyup.enter="doLogin"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="login-btn"
          @click="doLogin"
          :loading="loading"
          round
        >
          登 录
        </el-button>
      </el-form>

      <p class="login-tip">仅限已授权的管理员登录</p>
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
  } catch (e) { /* ignore */ } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #1a1940 0%, #2d2b6b 40%, #3d3b9b 70%, #6C5CE7 100%);
  overflow: hidden;
}

/* 装饰背景 */
.login-bg { position: absolute; inset: 0; overflow: hidden; }
.bg-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,0.03);
}
.shape-1 { width: 500px; height: 500px; top: -150px; right: -100px; }
.shape-2 { width: 300px; height: 300px; bottom: -80px; left: -60px; }
.shape-3 { width: 200px; height: 200px; top: 50%; left: 60%; }

/* 登录卡片 */
.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  padding: 52px 44px 44px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 24px 80px rgba(0,0,0,0.35);
}

/* 品牌区 */
.login-brand { text-align: center; margin-bottom: 36px; }
.brand-icon-wrap {
  width: 72px; height: 72px;
  border-radius: 20px;
  background: linear-gradient(135deg, #f5f3ff, #ede7ff);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 18px;
}
.brand-icon { font-size: 36px; }
.brand-title {
  font-size: 24px; font-weight: 800; color: #2d3436;
  margin: 0 0 6px; letter-spacing: 1px;
}
.brand-sub { font-size: 13px; color: #999; margin: 0; }

/* 表单 */
.login-form { margin-top: 8px; }

.login-btn {
  width: 100%;
  margin-top: 12px;
  height: 50px;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 4px;
  background: linear-gradient(135deg, #6C5CE7 0%, #A29BFE 100%) !important;
  border: none !important;
  box-shadow: 0 6px 24px rgba(108,92,231,0.35);
  transition: all 0.3s ease;
}
.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 32px rgba(108,92,231,0.45);
}

.login-tip {
  text-align: center;
  margin-top: 24px;
  color: #ccc;
  font-size: 12px;
}

@media (max-width: 767px) {
  .login-card {
    width: 88vw;
    padding: 36px 24px 28px;
    border-radius: 16px;
  }
  .brand-icon-wrap { width: 56px; height: 56px; border-radius: 16px; }
  .brand-icon { font-size: 28px; }
  .brand-title { font-size: 20px; }
}
</style>
