<template>
  <div class="page">
    <van-nav-bar :title="isEdit ? '编辑菜品' : '添加菜品'" left-text="取消" left-arrow @click-left="$router.back()" />

    <van-cell-group inset>
      <van-field v-model="form.name" label="商品名称" placeholder="请输入" required />
      <van-field v-model="form.price" type="number" label="售价(元)" placeholder="0.00" required />
      <van-field v-model="form.original_price" type="number" label="原价(元)" placeholder="选填" />
      <van-field v-model="form.description" label="描述" placeholder="选填" />
      <van-field label="商品图片">
        <template #input>
          <div style="display:flex;align-items:center;gap:8px">
            <van-image v-if="form.image" :src="form.image" width="48" height="48" fit="cover" radius="4" />
            <input type="file" accept="image/*" @change="onUploadImg" style="font-size:12px" />
          </div>
        </template>
      </van-field>
    </van-cell-group>

    <van-cell-group inset title="分类">
      <van-field v-model="selectedCatName" label="选择分类" readonly is-link @click="showCatPicker = true" placeholder="请选择" />
    </van-cell-group>

    <van-cell-group inset title="库存">
      <van-cell title="不限库存">
        <template #right-icon><van-switch v-model="stockUnlimited" size="22" /></template>
      </van-cell>
      <van-field v-if="!stockUnlimited" v-model="form.stock" type="number" label="库存数量" placeholder="0" />
    </van-cell-group>

    <van-cell-group inset title="限购">
      <van-cell title="不限购">
        <template #right-icon><van-switch v-model="limitUnlimited" size="22" /></template>
      </van-cell>
      <van-field v-if="!limitUnlimited" v-model="form.limit_per_order" type="number" label="每人限购" placeholder="0" />
    </van-cell-group>

    <div style="padding:16px">
      <van-button round block type="primary" :loading="loading" @click="onSubmit">保存</van-button>
      <van-button v-if="isEdit" round block type="danger" style="margin-top:12px" @click="onDelete">删除商品</van-button>
    </div>

    <!-- 分类选择器 -->
    <van-popup v-model:show="showCatPicker" position="bottom">
      <van-picker :columns="catNames" @confirm="onCatConfirm" @cancel="showCatPicker = false" />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { merchantApi } from '../../utils/api.js'
import { showToast, showConfirmDialog } from 'vant'

const route = useRoute()
const isEdit = ref(!!route.params.id && route.params.id !== 'new')
const itemId = ref(isEdit.value ? route.params.id : null)
const loading = ref(false)
const showCatPicker = ref(false)

const categories = ref([])
const catNames = ref([])
const selectedCatName = ref('')

const stockUnlimited = ref(true)
const limitUnlimited = ref(true)

const form = ref({
  name: '', price: '', original_price: '', description: '',
  image: '', category_id: null, stock: '-1', limit_per_order: '0',
})

const loadCats = async () => {
  try {
    const cats = await merchantApi.get('/api/merchant/menu/categories')
    categories.value = cats || []
    catNames.value = (cats || []).map(c => c.name)
    // 从URL参数获取分类
    if (!isEdit.value && route.query.cat) {
      const cid = parseInt(route.query.cat)
      const cat = cats.find(c => c.id === cid)
      if (cat) {
        form.value.category_id = cat.id
        selectedCatName.value = cat.name
      }
    }
  } catch {}
}

const loadItem = async () => {
  if (!isEdit.value) return
  try {
    const items = await merchantApi.get('/api/merchant/menu/items')
    const item = items.find(i => i.id == itemId.value)
    if (!item) return
    const cats = categories.value
    const cat = cats.find(c => c.id === item.category_id)
    selectedCatName.value = cat?.name || ''
    stockUnlimited.value = (item.stock ?? -1) === -1
    limitUnlimited.value = (item.limit_per_order ?? 0) === 0
    form.value = {
      name: item.name, price: String(item.price || ''),
      original_price: item.original_price ? String(item.original_price) : '',
      description: item.description || '',
      image: item.image || '', category_id: item.category_id,
      stock: stockUnlimited.value ? '-1' : String(item.stock),
      limit_per_order: limitUnlimited.value ? '0' : String(item.limit_per_order),
    }
  } catch {}
}

const onUploadImg = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  const token = localStorage.getItem('merchant_token')
  try {
    const res = await fetch('/api/common/upload', { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: fd })
    const data = await res.json()
    if (data.url) form.value.image = data.url
  } catch {}
}

const onCatConfirm = ({ selectedOptions }) => {
  const idx = selectedOptions[0]?.index
  if (idx !== undefined && categories.value[idx]) {
    form.value.category_id = categories.value[idx].id
    selectedCatName.value = categories.value[idx].name
  }
  showCatPicker.value = false
}

const onSubmit = async () => {
  if (!form.value.name) { showToast('请填写商品名称'); return }
  if (!form.value.price) { showToast('请填写价格'); return }
  loading.value = true
  const data = {
    name: form.value.name, price: parseFloat(form.value.price),
    original_price: form.value.original_price ? parseFloat(form.value.original_price) : null,
    description: form.value.description, image: form.value.image,
    category_id: form.value.category_id,
    stock: stockUnlimited.value ? -1 : (parseInt(form.value.stock) || -1),
    limit_per_order: limitUnlimited.value ? 0 : (parseInt(form.value.limit_per_order) || 0),
  }
  try {
    if (isEdit.value) {
      await merchantApi.put(`/api/merchant/menu/items/${itemId.value}`, data)
    } else {
      await merchantApi.post('/api/merchant/menu/items', data)
    }
    showToast('保存成功')
    setTimeout(() => window.location.hash = '#/m/menu', 300)
  } catch {} finally { loading.value = false }
}

const onDelete = async () => {
  try { await showConfirmDialog({ title: '删除确认', message: '确定删除该商品吗？' }) } catch { return }
  try {
    await merchantApi.del(`/api/merchant/menu/items/${itemId.value}`)
    showToast('已删除')
    setTimeout(() => window.location.hash = '#/m/menu', 300)
  } catch {}
}

onMounted(async () => {
  await loadCats()
  await loadItem()
})
</script>

<style scoped>
.page { min-height: 100vh; background: #f7f8fa; padding-bottom: 20px; }
</style>
