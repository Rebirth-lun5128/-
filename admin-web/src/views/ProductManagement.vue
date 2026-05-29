<template>
  <div class="products-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-hdr">
          <span class="card-hdr-title">📦 商品管理</span>
          <div class="hdr-controls">
            <el-select v-model="selectedStoreId" placeholder="选择店铺" style="width:240px" @change="onStoreChange" filterable>
              <el-option v-for="s in stores" :key="s.id" :label="s.name" :value="s.id" />
            </el-select>
          </div>
        </div>
      </template>

      <!-- 分类标签栏 -->
      <div class="cat-bar" v-if="selectedStoreId">
        <div class="cat-tabs">
          <span
            class="cat-tab"
            :class="{ active: filterCategoryId === null }"
            @click="filterCategoryId = null"
          >全部</span>
          <span
            v-for="cat in categories"
            :key="cat.id"
            class="cat-tab"
            :class="{ active: filterCategoryId === cat.id }"
            @click="filterCategoryId = cat.id"
          >
            {{ cat.name }}
            <el-icon class="cat-edit-icon" @click.stop="openCatEdit(cat)"><EditPen /></el-icon>
            <el-icon class="cat-del-icon" @click.stop="deleteCategory(cat.id)"><Close /></el-icon>
          </span>
        </div>
        <el-button size="small" type="primary" text @click="openCatAdd">+ 添加分类</el-button>
      </div>

      <!-- 商品表格 -->
      <div v-if="selectedStoreId" style="margin-top:16px">
        <div class="table-toolbar">
          <el-button type="primary" size="small" @click="openProductAdd">+ 添加商品</el-button>
        </div>

        <el-table :data="products" stripe v-loading="loading">
          <el-table-column label="图片" width="90" align="center">
            <template #default="{ row }">
              <el-image
                v-if="row.image"
                :src="row.image"
                style="width:50px;height:50px;border-radius:8px"
                fit="cover"
                :preview-src-list="[row.image]"
              />
              <span v-else class="no-img">无图</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="商品名称" min-width="140">
            <template #default="{ row }">
              <span class="prod-name">{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column label="分类" width="120" align="center">
            <template #default="{ row }">
              <el-tag size="small" type="info" effect="plain">{{ getCatName(row.category_id) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="价格" width="120" align="center">
            <template #default="{ row }">
              <span class="price-cell">¥{{ row.price }}</span>
              <span v-if="row.original_price" class="orig-price">¥{{ row.original_price }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="stock" label="库存" width="90" align="center">
            <template #default="{ row }">
              <span v-if="row.stock === -1" class="text-muted">无限</span>
              <span v-else>{{ row.stock }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="monthly_sales" label="月售" width="70" align="center" />
          <el-table-column label="上架" width="80" align="center">
            <template #default="{ row }">
              <el-switch
                :model-value="row.status === 1"
                @change="toggleStatus(row)"
                size="small"
              />
            </template>
          </el-table-column>
          <el-table-column prop="sort_order" label="排序" width="70" align="center" />
          <el-table-column label="操作" width="150" fixed="right" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="openProductEdit(row)" round>编辑</el-button>
              <el-button size="small" type="danger" @click="deleteProduct(row.id)" round>删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else class="empty-hint">请先选择一个店铺</div>
    </el-card>

    <!-- 分类编辑弹窗 -->
    <el-dialog v-model="catDialogVisible" :title="catDialogTitle" width="400px" destroy-on-close>
      <el-input v-model="catForm.name" placeholder="分类名称" maxlength="20" />
      <template #footer>
        <el-button @click="catDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCategory" :loading="catSaving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 商品编辑弹窗 -->
    <el-dialog v-model="prodDialogVisible" :title="prodDialogTitle" width="560px" destroy-on-close>
      <el-form label-width="80px" v-if="prodForm">
        <el-form-item label="商品图片">
          <div class="upload-row">
            <el-image
              v-if="prodForm.image"
              :src="prodForm.image"
              style="width:80px;height:80px;border-radius:8px;margin-right:12px"
              fit="cover"
            />
            <el-upload
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="onUploadSuccess"
              accept="image/*"
            >
              <el-button size="small" type="primary" text>上传图片</el-button>
            </el-upload>
          </div>
        </el-form-item>
        <el-form-item label="商品名称">
          <el-input v-model="prodForm.name" maxlength="100" />
        </el-form-item>
        <el-form-item label="所属分类">
          <el-select v-model="prodForm.category_id" placeholder="选择分类" clearable style="width:100%">
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="价格">
          <el-input-number v-model="prodForm.price" :min="0.01" :precision="2" style="width:160px" />
        </el-form-item>
        <el-form-item label="原价">
          <el-input-number v-model="prodForm.original_price" :min="0" :precision="2" style="width:160px" />
        </el-form-item>
        <el-form-item label="库存">
          <el-input-number v-model="prodForm.stock" :min="-1" style="width:160px" />
          <span class="form-hint-inline">-1 表示无限库存</span>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="prodForm.description" type="textarea" :rows="2" maxlength="300" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="prodForm.sort_order" :min="0" style="width:160px" />
        </el-form-item>
        <el-form-item label="推荐">
          <el-switch v-model="prodForm.is_recommended" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="prodDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProduct" :loading="prodSaving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { EditPen, Close } from '@element-plus/icons-vue'
import http from '../api'

const stores = ref([])
const selectedStoreId = ref(null)
const categories = ref([])
const products = ref([])
const loading = ref(false)
const filterCategoryId = ref(null)

// ====== 店铺列表 ======
async function loadStores() {
  try {
    const res = await http.get('/admin/stores', { params: { page: 1, page_size: 200 } })
    stores.value = res.items || []
  } catch (e) { /* ignore */ }
}

async function onStoreChange() {
  filterCategoryId.value = null
  await Promise.all([loadCategories(), loadProducts()])
}

// ====== 分类 CRUD ======
async function loadCategories() {
  if (!selectedStoreId.value) return
  try {
    const res = await http.get('/admin/categories', { params: { store_id: selectedStoreId.value } })
    categories.value = Array.isArray(res) ? res : []
  } catch (e) { /* ignore */ }
}

function getCatName(id) {
  const cat = categories.value.find(c => c.id === id)
  return cat ? cat.name : '未分类'
}

const catDialogVisible = ref(false)
const catDialogTitle = ref('')
const catForm = ref({ name: '', id: null })
const catSaving = ref(false)

function openCatAdd() {
  catForm.value = { name: '', id: null }
  catDialogTitle.value = '添加分类'
  catDialogVisible.value = true
}

function openCatEdit(cat) {
  catForm.value = { name: cat.name, id: cat.id }
  catDialogTitle.value = '修改分类'
  catDialogVisible.value = true
}

async function saveCategory() {
  if (!catForm.value.name.trim()) return
  catSaving.value = true
  try {
    if (catForm.value.id) {
      await http.put(`/admin/categories/${catForm.value.id}`, { name: catForm.value.name, sort_order: 0 })
    } else {
      await http.post('/admin/categories', { name: catForm.value.name, sort_order: 0 }, {
        params: { store_id: selectedStoreId.value }
      })
    }
    catDialogVisible.value = false
    ElMessage.success('已保存')
    loadCategories()
  } catch (e) { /* ignore */ } finally { catSaving.value = false }
}

async function deleteCategory(id) {
  try {
    await ElMessageBox.confirm('删除分类后，该分类下的商品将变为未分类。确认删除？', '提示', { type: 'warning' })
    await http.del(`/admin/categories/${id}`)
    ElMessage.success('已删除')
    loadCategories()
    loadProducts()
  } catch (e) { /* ignore */ }
}

// ====== 商品 CRUD ======
async function loadProducts() {
  if (!selectedStoreId.value) return
  loading.value = true
  try {
    const params = { store_id: selectedStoreId.value }
    if (filterCategoryId.value) params.category_id = filterCategoryId.value
    const res = await http.get('/admin/products', { params })
    products.value = Array.isArray(res) ? res : []
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

async function toggleStatus(row) {
  const newStatus = row.status === 1 ? 0 : 1
  try {
    await http.put(`/admin/products/${row.id}/status`, null, { params: { status: newStatus } })
    row.status = newStatus
    ElMessage.success(newStatus === 1 ? '已上架' : '已下架')
  } catch (e) { /* ignore */ }
}

async function deleteProduct(id) {
  try {
    await ElMessageBox.confirm('确认删除该商品？', '提示', { type: 'warning' })
    await http.del(`/admin/products/${id}`)
    ElMessage.success('已删除')
    loadProducts()
  } catch (e) { /* ignore */ }
}

// 商品弹窗
const prodDialogVisible = ref(false)
const prodDialogTitle = ref('')
const prodForm = ref(null)
const prodSaving = ref(false)
const editingProdId = ref(null)

const uploadUrl = '/api/common/upload'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('admin_token')}`
}))

function onUploadSuccess(res) {
  if (res.url) {
    prodForm.value.image = res.url
    ElMessage.success('上传成功')
  }
}

function openProductAdd() {
  editingProdId.value = null
  prodForm.value = {
    name: '', image: '', price: 0.01, original_price: null,
    description: '', stock: -1, sort_order: 0, category_id: null, is_recommended: 0
  }
  prodDialogTitle.value = '添加商品'
  prodDialogVisible.value = true
}

function openProductEdit(row) {
  editingProdId.value = row.id
  prodForm.value = {
    name: row.name,
    image: row.image,
    price: row.price,
    original_price: row.original_price,
    description: row.description || '',
    stock: row.stock,
    sort_order: row.sort_order,
    category_id: row.category_id,
    is_recommended: row.is_recommended
  }
  prodDialogTitle.value = '编辑商品'
  prodDialogVisible.value = true
}

async function saveProduct() {
  if (!prodForm.value.name.trim()) return
  prodSaving.value = true
  try {
    if (editingProdId.value) {
      await http.put(`/admin/products/${editingProdId.value}`, prodForm.value)
    } else {
      await http.post('/admin/products', prodForm.value, {
        params: { store_id: selectedStoreId.value }
      })
    }
    prodDialogVisible.value = false
    ElMessage.success('已保存')
    loadProducts()
  } catch (e) { /* ignore */ } finally { prodSaving.value = false }
}

// 分类切换时重新加载
watch(filterCategoryId, () => {
  if (selectedStoreId.value) loadProducts()
})

loadStores()
</script>

<style scoped>
.products-page { animation: fadeIn 0.35s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

.card-hdr { display: flex; justify-content: space-between; align-items: center; }
.card-hdr-title { font-size: 15px; font-weight: 600; color: #333; }
.hdr-controls { display: flex; gap: 12px; align-items: center; }
.empty-hint { text-align: center; padding: 60px 0; color: #bbb; font-size: 15px; }

/* 分类标签栏 */
.cat-bar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.cat-tabs { display: flex; gap: 6px; flex-wrap: wrap; flex: 1; }
.cat-tab {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 6px 14px; border-radius: 20px; font-size: 13px;
  background: #f5f5f5; color: #666; cursor: pointer;
  transition: all 0.2s; white-space: nowrap;
}
.cat-tab:hover { background: #ede7ff; color: #6C5CE7; }
.cat-tab.active { background: #6C5CE7; color: #fff; font-weight: 600; }
.cat-edit-icon { font-size: 11px; opacity: 0.5; }
.cat-edit-icon:hover { opacity: 1; }
.cat-del-icon { font-size: 11px; opacity: 0.5; }
.cat-del-icon:hover { opacity: 1; color: #E17055; }
.cat-tab.active .cat-edit-icon,
.cat-tab.active .cat-del-icon { opacity: 0.7; }

.table-toolbar { margin-bottom: 12px; }

.prod-name { font-weight: 600; color: #333; }
.price-cell { color: #E17055; font-weight: 700; font-size: 14px; }
.orig-price { color: #ccc; font-size: 12px; text-decoration: line-through; margin-left: 6px; }
.no-img { color: #ccc; font-size: 12px; }
.text-muted { color: #bbb; }

.form-hint-inline { font-size: 12px; color: #999; margin-left: 10px; }
.upload-row { display: flex; align-items: center; }

@media (max-width: 767px) {
  .card-hdr { flex-wrap: wrap; gap: 10px; }
  .hdr-controls { width: 100%; }
  .hdr-controls .el-select { width: 100% !important; }
  .cat-bar { flex-direction: column; align-items: flex-start; }
}
</style>
