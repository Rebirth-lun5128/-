<template>
  <el-container class="layout" :class="{ 'is-mobile': isMobile }">
    <!-- 移动端遮罩 -->
    <div
      v-if="isMobile && mobileMenuOpen"
      class="mobile-overlay"
      @click="closeMobileMenu"
    ></div>

    <!-- 侧边栏 -->
    <el-aside
      :class="{
        'app-aside': true,
        'aside-mobile-open': isMobile && mobileMenuOpen,
        'aside-collapsed': isCollapsed && !isMobile
      }"
      :style="asideStyle"
    >
      <!-- 品牌区 -->
      <div class="brand-area" :class="{ collapsed: isCollapsed && !isMobile }">
        <div class="brand-logo">
          <span class="logo-emoji">🍜</span>
        </div>
        <div v-if="!(isCollapsed && !isMobile)" class="brand-info">
          <div class="brand-name">夜市管理后台</div>
          <div class="brand-desc">社区外卖平台</div>
        </div>
      </div>

      <!-- 菜单 -->
      <div class="nav-wrap">
        <div
          v-for="item in menuItems"
          :key="item.path"
          class="nav-item"
          :class="{ active: currentRoute === item.path }"
          @click="navigate(item.path)"
        >
          <span class="nav-icon" :style="{ background: item.color }">
            <component :is="item.icon" />
          </span>
          <span v-if="!(isCollapsed && !isMobile)" class="nav-label">{{ item.label }}</span>
          <span v-if="!(isCollapsed && !isMobile) && currentRoute === item.path" class="nav-bar"></span>
        </div>
      </div>

      <!-- 底部用户 -->
      <div class="sidebar-footer" :class="{ collapsed: isCollapsed && !isMobile }">
        <div class="footer-avatar">管</div>
        <div v-if="!(isCollapsed && !isMobile)" class="footer-info">
          <div class="footer-name">超级管理员</div>
          <div class="footer-role">平台运营</div>
        </div>
        <el-icon v-if="!(isCollapsed && !isMobile)" class="footer-logout" @click="logout"><SwitchButton /></el-icon>
      </div>

      <!-- 桌面端折叠按钮 -->
      <div v-if="!isMobile" class="collapse-btn" @click="isCollapsed = !isCollapsed">
        <el-icon><Fold v-if="!isCollapsed" /><Expand v-else /></el-icon>
      </div>
    </el-aside>

    <!-- 右侧主体 -->
    <el-container class="main-container">
      <!-- 顶栏 -->
      <el-header class="app-header">
        <div class="header-left">
          <!-- 移动端汉堡按钮 -->
          <span v-if="isMobile" class="hamburger" @click="toggleMobileMenu">
            <el-icon size="22"><Operation /></el-icon>
          </span>
          <!-- 桌面端折叠按钮 -->
          <span v-else class="header-collapse" @click="isCollapsed = !isCollapsed">
            <el-icon size="18"><Fold v-if="!isCollapsed" /><Expand v-else /></el-icon>
          </span>
          <span class="header-breadcrumb">{{ currentTitle }}</span>
        </div>
        <div class="header-right">
          <span v-if="!isMobile" class="header-time">{{ nowTime }}</span>
          <el-badge :value="newOrderCount" :hidden="newOrderCount === 0" class="header-badge">
            <el-button text circle class="header-btn" @click="goToOrders" title="新订单提醒">
              <el-icon size="18"><Bell /></el-icon>
            </el-button>
          </el-badge>
          <el-button text circle class="header-btn" @click="logout" title="退出登录">
            <el-icon size="18"><SwitchButton /></el-icon>
          </el-button>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  DataAnalysis, Shop, Van, Document, Location,
  Setting, SwitchButton, Fold, Expand, Operation, Goods, User, Bell, Avatar, Money
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const isCollapsed = ref(false)
const isMobile = ref(false)
const mobileMenuOpen = ref(false)
const nowTime = ref('')
let timer = null

const currentRoute = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '管理后台')

// ---- WebSocket 新订单通知 ----
const newOrderCount = ref(0)
let ws = null
let wsReconnectTimer = null

function connectWebSocket() {
  const token = localStorage.getItem('admin_token')
  if (!token) return
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${protocol}//${location.host}/ws?token=${token}`
  try {
    ws = new WebSocket(url)
    ws.onopen = () => {
      if (wsReconnectTimer) { clearTimeout(wsReconnectTimer); wsReconnectTimer = null }
    }
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.event === 'new_order') {
          newOrderCount.value++
          // 桌面端弹窗通知
          if (window.Notification && Notification.permission === 'granted') {
            new Notification('新订单提醒', {
              body: `${data.order?.order_no || ''} 待处理`,
              icon: '/favicon.ico',
            })
          }
        }
      } catch (_) {}
    }
    ws.onclose = () => {
      wsReconnectTimer = setTimeout(connectWebSocket, 5000)
    }
    ws.onerror = () => { ws?.close() }
  } catch (_) {}
}

function goToOrders() {
  newOrderCount.value = 0
  router.push('/orders')
}

// 请求桌面通知权限
if (window.Notification && Notification.permission === 'default') {
  Notification.requestPermission()
}

const menuItems = [
  { path: '/dashboard', label: '数据大盘', icon: DataAnalysis, color: 'linear-gradient(135deg, #667eea, #764ba2)' },
  { path: '/customers',     label: '客户管理', icon: User,          color: 'linear-gradient(135deg, #74b9ff, #0984e3)' },
  { path: '/notifications',label: '推送通知', icon: Bell,          color: 'linear-gradient(135deg, #fdcb6e, #f39c12)' },
  { path: '/stores',        label: '商家管理', icon: Shop,          color: 'linear-gradient(135deg, #00B894, #55efc4)' },
  { path: '/riders',     label: '骑手管理', icon: Van,           color: 'linear-gradient(135deg, #FDCB6E, #e17055)' },
  { path: '/orders',     label: '订单监控', icon: Document,      color: 'linear-gradient(135deg, #E17055, #d63031)' },
  { path: '/districts',  label: '分区管理', icon: Location,      color: 'linear-gradient(135deg, #74b9ff, #0984e3)' },
  { path: '/products',   label: '商品管理', icon: Goods,         color: 'linear-gradient(135deg, #fd79a8, #e84393)' },
  { path: '/settlements',label: '结算审批', icon: Operation,     color: 'linear-gradient(135deg, #fdcb6e, #e17055)' },
  { path: '/commission', label: '佣金设置', icon: Money,         color: 'linear-gradient(135deg, #00b894, #00cec9)' },
  { path: '/admins',     label: '管理员管理', icon: Avatar,       color: 'linear-gradient(135deg, #636e72, #2d3436)' },
  { path: '/system',     label: '系统配置', icon: Setting,       color: 'linear-gradient(135deg, #a29bfe, #6c5ce7)' },
]

const asideStyle = computed(() => {
  if (isMobile.value) return {}
  return { width: isCollapsed.value ? '72px' : '240px' }
})

function navigate(path) {
  router.push(path)
  if (isMobile.value) {
    mobileMenuOpen.value = false
  }
}

function toggleMobileMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

function closeMobileMenu() {
  mobileMenuOpen.value = false
}

function logout() {
  localStorage.removeItem('admin_token')
  router.push('/login')
}

function updateTime() {
  const d = new Date()
  const week = ['日','一','二','三','四','五','六']
  nowTime.value = `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()} 星期${week[d.getDay()]} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  updateTime()
  timer = setInterval(updateTime, 30000)
  window.addEventListener('resize', checkMobile)
  connectWebSocket()
})
onUnmounted(() => {
  clearInterval(timer)
  window.removeEventListener('resize', checkMobile)
  if (wsReconnectTimer) clearTimeout(wsReconnectTimer)
  if (ws) { ws.close(); ws = null }
})
</script>

<style>
/* ==================== 全局 CSS 变量 ==================== */
:root {
  --app-primary: #6C5CE7;
  --app-primary-light: #A29BFE;
  --app-primary-dark: #5A4BD1;
  --app-success: #00B894;
  --app-warning: #FDCB6E;
  --app-danger: #E17055;
  --app-info: #74B9FF;
  --app-bg: #f0f2f7;
  --app-sidebar-start: #1a1940;
  --app-sidebar-end: #2d2b6b;
  --app-card-shadow: 0 2px 16px rgba(0,0,0,0.06);
  --app-card-shadow-hover: 0 8px 32px rgba(0,0,0,0.10);
  --app-radius: 14px;
}

/* ==================== 全局重置 ==================== */
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  background: var(--app-bg);
}

/* 自定义滚动条 */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.22); }

/* ==================== 全局卡片 ==================== */
.el-card {
  border-radius: var(--app-radius) !important;
  box-shadow: var(--app-card-shadow) !important;
  border: none !important;
  transition: box-shadow 0.3s ease;
}
.el-card:hover { box-shadow: var(--app-card-shadow-hover) !important; }
.el-card__header {
  padding: 18px 24px !important;
  border-bottom: 1px solid #f0f0f0 !important;
}

/* ==================== 全局表格 ==================== */
.el-table {
  border-radius: 10px;
  overflow: hidden;
  --el-table-border-color: #f0f0f0;
}
.el-table th.el-table__cell {
  background: #f8f9fc !important;
  color: #606266;
  font-weight: 600;
  font-size: 13px;
  border-bottom: 2px solid #eef0f6 !important;
}
.el-table .el-table__row:hover > td.el-table__cell {
  background: #f5f3ff !important;
}

/* ==================== 全局按钮 ==================== */
.el-button--primary {
  --el-button-bg-color: var(--app-primary);
  --el-button-border-color: var(--app-primary);
  --el-button-hover-bg-color: var(--app-primary-dark);
  --el-button-hover-border-color: var(--app-primary-dark);
}

/* ==================== 全局分页 ==================== */
.el-pagination .el-pager li.is-active {
  background: var(--app-primary) !important;
  border-radius: 6px;
}

/* ==================== 移动端全局调整 ==================== */
@media (max-width: 767px) {
  .el-card__header { padding: 14px 16px !important; }
  .el-card__body { padding: 16px !important; }
  .el-message-box { width: 90vw !important; }
  .el-dialog { width: 92vw !important; }
  .el-drawer { width: 90vw !important; }
  .el-table { font-size: 12px; }
  .el-form-item__label { font-size: 13px !important; }
  .el-button { font-size: 12px; }
}
</style>

<style scoped>
/* ==================== 布局 ==================== */
.layout { height: 100vh; overflow: hidden; }

/* ==================== 移动端遮罩 ==================== */
.mobile-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.45);
  z-index: 199;
  animation: fadeIn 0.25s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

/* ==================== 侧边栏 ==================== */
.app-aside {
  background: linear-gradient(180deg, #1a1940 0%, #25236b 40%, #2d2b6b 100%) !important;
  display: flex;
  flex-direction: column;
  position: relative;
  width: 240px;
  transition: width 0.3s ease;
  box-shadow: 4px 0 30px rgba(0,0,0,0.2);
  z-index: 200;
  overflow: hidden;
  flex-shrink: 0;
}
.app-aside.aside-collapsed { width: 72px; }

/* 品牌区 */
.brand-area {
  padding: 24px 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  transition: all 0.3s;
}
.brand-area.collapsed {
  justify-content: center;
  padding: 20px 0;
}
.brand-logo {
  width: 44px; height: 44px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(108,92,231,0.4), rgba(162,155,254,0.2));
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  backdrop-filter: blur(4px);
}
.logo-emoji { font-size: 24px; }
.brand-info { overflow: hidden; white-space: nowrap; }
.brand-name {
  color: #fff; font-size: 16px; font-weight: 700;
  letter-spacing: 0.5px;
}
.brand-desc {
  color: rgba(255,255,255,0.4); font-size: 11px; margin-top: 3px;
}

/* 导航区域 */
.nav-wrap {
  flex: 1;
  padding: 16px 10px;
  overflow-y: auto;
  overflow-x: hidden;
}
.nav-item {
  display: flex;
  align-items: center;
  height: 48px;
  padding: 0 14px;
  margin-bottom: 6px;
  border-radius: 12px;
  cursor: pointer;
  position: relative;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  color: rgba(255,255,255,0.6);
  -webkit-tap-highlight-color: transparent;
}
.nav-item:hover {
  background: rgba(255,255,255,0.06);
  color: #fff;
}
.nav-item.active {
  background: rgba(108,92,231,0.25);
  color: #fff;
  font-weight: 600;
}
.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0; top: 12px; bottom: 12px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: linear-gradient(180deg, var(--app-primary-light), var(--app-primary));
}
.nav-icon {
  width: 34px; height: 34px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  font-size: 16px;
  color: #fff;
}
.nav-label {
  margin-left: 12px;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 底部用户区 */
.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 18px;
  border-top: 1px solid rgba(255,255,255,0.06);
  transition: all 0.3s;
}
.sidebar-footer.collapsed { justify-content: center; }
.footer-avatar {
  width: 36px; height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--app-primary), var(--app-primary-light));
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; font-weight: 700;
  flex-shrink: 0;
}
.footer-info { overflow: hidden; flex: 1; }
.footer-name {
  color: #fff; font-size: 13px; font-weight: 600;
}
.footer-role {
  color: rgba(255,255,255,0.4); font-size: 11px; margin-top: 1px;
}
.footer-logout {
  color: rgba(255,255,255,0.3); cursor: pointer; font-size: 16px;
  transition: color 0.2s;
}
.footer-logout:hover { color: #ff6b6b; }

/* 折叠按钮 */
.collapse-btn {
  position: absolute;
  bottom: 80px;
  right: -12px;
  width: 24px; height: 24px;
  border-radius: 50%;
  background: #fff;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  color: #666;
  font-size: 12px;
  transition: all 0.3s;
  z-index: 10;
}
.collapse-btn:hover { color: var(--app-primary); box-shadow: 0 4px 14px rgba(0,0,0,0.2); }

/* ==================== 顶部栏 ==================== */
.main-container { background: var(--app-bg); }
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  padding: 0 28px;
  height: 60px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.04);
  z-index: 10;
  flex-shrink: 0;
}
.header-left {
  display: flex; align-items: center; gap: 14px;
}
.hamburger {
  cursor: pointer;
  color: #333;
  padding: 4px;
  display: flex;
  align-items: center;
}
.header-collapse {
  cursor: pointer;
  color: #999;
  padding: 4px;
  display: flex;
  align-items: center;
  transition: color 0.2s;
}
.header-collapse:hover { color: var(--app-primary); }
.header-breadcrumb {
  font-size: 16px; font-weight: 600; color: #2d3436;
}
.header-right {
  display: flex; align-items: center; gap: 16px;
}
.header-time {
  font-size: 13px; color: #999;
  font-variant-numeric: tabular-nums;
}
.header-btn {
  color: #999 !important;
  transition: color 0.2s;
}
.header-btn:hover { color: #ff6b6b !important; }
.header-badge { margin-right: -4px; }
.header-badge :deep(.el-badge__content) { font-size: 10px; }

/* ==================== 内容区 ==================== */
.app-main {
  padding: 24px;
  overflow-y: auto;
  height: calc(100vh - 60px);
}

/* ==================== 路由动画 ==================== */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.page-fade-enter-from { opacity: 0; transform: translateY(10px); }
.page-fade-leave-to   { opacity: 0; transform: translateY(-10px); }

/* ==================== 移动端 ==================== */
@media (max-width: 767px) {
  /* 侧边栏变成滑出抽屉 */
  .app-aside {
    position: fixed;
    left: 0; top: 0; bottom: 0;
    width: 260px;
    transform: translateX(-100%);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 200;
  }
  .app-aside.aside-mobile-open {
    transform: translateX(0);
    box-shadow: 4px 0 40px rgba(0,0,0,0.35);
  }

  /* 顶栏 */
  .app-header {
    padding: 0 16px;
    height: 52px;
  }
  .header-breadcrumb { font-size: 15px; }

  /* 内容区 */
  .app-main {
    padding: 14px;
    height: calc(100vh - 52px);
  }
}
</style>
