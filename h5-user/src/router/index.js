import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
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
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || '社区夜市'
  if (to.meta.needAuth && !localStorage.getItem('token')) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
