<template>
  <el-container class="layout">
    <el-aside width="220px">
      <div class="logo">
        <h2>外卖管理后台</h2>
      </div>
      <el-menu
        :default-active="currentRoute"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据大盘</span>
        </el-menu-item>
        <el-menu-item index="/restaurants">
          <el-icon><Shop /></el-icon>
          <span>商家管理</span>
        </el-menu-item>
        <el-menu-item index="/riders">
          <el-icon><Van /></el-icon>
          <span>骑手管理</span>
        </el-menu-item>
        <el-menu-item index="/orders">
          <el-icon><Document /></el-icon>
          <span>订单监控</span>
        </el-menu-item>
        <el-menu-item index="/regions">
          <el-icon><Location /></el-icon>
          <span>区域管理</span>
        </el-menu-item>
        <el-menu-item index="/system">
          <el-icon><Setting /></el-icon>
          <span>系统配置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header>
        <div class="header-left">
          <span>{{ $route.meta.title }}</span>
        </div>
        <div class="header-right">
          <el-button text @click="logout">退出登录</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const currentRoute = computed(() => route.path)

function logout() {
  localStorage.removeItem('admin_token')
  router.push('/login')
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
.layout { height: 100vh; }
.el-aside { background: #304156; overflow-y: auto; }
.logo { padding: 20px; text-align: center; }
.logo h2 { color: #fff; font-size: 20px; }
.el-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}
.header-left { font-size: 18px; font-weight: bold; }
.el-main { background: #f0f2f5; padding: 20px; }
</style>
