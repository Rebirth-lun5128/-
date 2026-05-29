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
        path: 'stores',
        name: 'Stores',
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
        path: 'districts',
        name: 'Districts',
        component: () => import('../views/Regions.vue'),
        meta: { title: '分区管理' },
      },
      {
        path: 'system',
        name: 'System',
        component: () => import('../views/System.vue'),
        meta: { title: '系统配置', role: 'super_admin' },
      },
      {
        path: 'customers',
        name: 'Customers',
        component: () => import('../views/Customers.vue'),
        meta: { title: '客户管理' },
      },
      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('../views/Notifications.vue'),
        meta: { title: '推送通知' },
      },
      {
        path: 'products',
        name: 'Products',
        component: () => import('../views/ProductManagement.vue'),
        meta: { title: '商品管理' },
      },
      {
        path: 'settlements',
        name: 'Settlements',
        component: () => import('../views/Settlements.vue'),
        meta: { title: '结算审批' },
      },
      {
        path: 'admins',
        name: 'Admins',
        component: () => import('../views/Admins.vue'),
        meta: { title: '管理员管理', role: 'super_admin' },
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
