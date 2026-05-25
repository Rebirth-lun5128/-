import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
  },
  {
    path: '/',
    component: () => import('../layout/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '数据大盘' },
      },
      {
        path: 'restaurants',
        name: 'Restaurants',
        component: () => import('../views/Restaurants.vue'),
        meta: { title: '商家管理' },
      },
      {
        path: 'riders',
        name: 'Riders',
        component: () => import('../views/Riders.vue'),
        meta: { title: '骑手管理' },
      },
      {
        path: 'orders',
        name: 'Orders',
        component: () => import('../views/Orders.vue'),
        meta: { title: '订单监控' },
      },
      {
        path: 'regions',
        name: 'Regions',
        component: () => import('../views/Regions.vue'),
        meta: { title: '区域管理' },
      },
      {
        path: 'system',
        name: 'System',
        component: () => import('../views/System.vue'),
        meta: { title: '系统配置', role: 'super_admin' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('admin_token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
