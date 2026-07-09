import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  // ===== 用户端 =====
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { title: '首页', tab: 0 },
  },
  {
    path: '/restaurant/:id',
    name: 'Restaurant',
    component: () => import('../views/Restaurant.vue'),
    meta: { title: '店铺详情' },
  },
  {
    path: '/cart',
    name: 'Cart',
    component: () => import('../views/Cart.vue'),
    meta: { title: '购物车', tab: -1 },
  },
  {
    path: '/order-confirm',
    name: 'OrderConfirm',
    component: () => import('../views/OrderConfirm.vue'),
    meta: { title: '确认订单', needAuth: true },
  },
  {
    path: '/orders',
    name: 'Orders',
    component: () => import('../views/Orders.vue'),
    meta: { title: '订单列表', tab: 1, needAuth: true },
  },
  {
    path: '/order/:id',
    name: 'OrderDetail',
    component: () => import('../views/OrderDetail.vue'),
    meta: { title: '订单详情', needAuth: true },
  },
  {
    path: '/address',
    name: 'Address',
    component: () => import('../views/Address.vue'),
    meta: { title: '地址管理', needAuth: true },
  },
  {
    path: '/address-form/:id?',
    name: 'AddressForm',
    component: () => import('../views/AddressForm.vue'),
    meta: { title: '编辑地址', needAuth: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { title: '个人中心', tab: 2, needAuth: true },
  },
  {
    path: '/profile-edit',
    name: 'ProfileEdit',
    component: () => import('../views/ProfileEdit.vue'),
    meta: { title: '编辑资料', needAuth: true },
  },
  {
    path: '/coupons',
    name: 'Coupons',
    component: () => import('../views/Coupons.vue'),
    meta: { title: '优惠券', needAuth: true },
  },
  {
    path: '/agreement',
    name: 'Agreement',
    component: () => import('../views/Agreement.vue'),
    meta: { title: '用户服务协议' },
  },
  {
    path: '/privacy',
    name: 'Privacy',
    component: () => import('../views/Privacy.vue'),
    meta: { title: '隐私政策' },
  },

  // ===== 商家端 =====
  {
    path: '/m/login',
    name: 'MerchantLogin',
    component: () => import('../views/merchant/Login.vue'),
    meta: { title: '商家登录' },
  },
  {
    path: '/m/dashboard',
    name: 'MerchantDashboard',
    component: () => import('../views/merchant/Dashboard.vue'),
    meta: { title: '商家中心' },
  },
  {
    path: '/m/orders',
    name: 'MerchantOrders',
    component: () => import('../views/merchant/Orders.vue'),
    meta: { title: '订单管理' },
  },
  {
    path: '/m/order/:id',
    name: 'MerchantOrderDetail',
    component: () => import('../views/merchant/OrderDetail.vue'),
    meta: { title: '订单详情' },
  },
  {
    path: '/m/menu',
    name: 'MerchantMenu',
    component: () => import('../views/merchant/Menu.vue'),
    meta: { title: '菜品管理' },
  },

  // ===== 骑手端 =====
  {
    path: '/r/login',
    name: 'RiderLogin',
    component: () => import('../views/rider/Login.vue'),
    meta: { title: '骑手登录' },
  },
  {
    path: '/r/dashboard',
    name: 'RiderDashboard',
    component: () => import('../views/rider/Dashboard.vue'),
    meta: { title: '骑手中心' },
  },
  {
    path: '/r/orders',
    name: 'RiderOrders',
    component: () => import('../views/rider/Orders.vue'),
    meta: { title: '我的订单' },
  },
  {
    path: '/r/order/:id',
    name: 'RiderOrderDetail',
    component: () => import('../views/rider/OrderDetail.vue'),
    meta: { title: '订单详情' },
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || '社区夜市'
  // 用户端需要登录的页面
  if (to.meta.needAuth && !localStorage.getItem('token')) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
