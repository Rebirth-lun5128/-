import { reactive } from 'vue'

export const cartStore = reactive({
  items: JSON.parse(localStorage.getItem('cart') || '[]'),

  _save() {
    localStorage.setItem('cart', JSON.stringify(this.items))
  },

  get totalCount() {
    return this.items.reduce((sum, i) => sum + i.quantity, 0)
  },

  get totalPrice() {
    return this.items.reduce((sum, i) => sum + i.price * i.quantity, 0)
  },

  addItem(item) {
    const exist = this.items.find(
      (i) => i.productId === item.productId && i.storeId === item.storeId,
    )
    if (exist) {
      exist.quantity += item.quantity || 1
    } else {
      this.items.push({ ...item, quantity: item.quantity || 1 })
    }
    this._save()
  },

  updateQuantity(productId, storeId, quantity) {
    const idx = this.items.findIndex(
      (i) => i.productId === productId && i.storeId === storeId,
    )
    if (idx >= 0) {
      if (quantity <= 0) {
        this.items.splice(idx, 1)
      } else {
        this.items[idx].quantity = quantity
      }
    }
    this._save()
  },

  removeItem(productId, storeId) {
    this.items = this.items.filter(
      (i) => !(i.productId === productId && i.storeId === storeId),
    )
    this._save()
  },

  clearByStore(storeId) {
    this.items = this.items.filter((i) => i.storeId !== storeId)
    this._save()
  },

  clearAll() {
    this.items = []
    this._save()
  },

  getItemsByStore(storeId) {
    return this.items.filter((i) => i.storeId === storeId)
  },

  getStoreIds() {
    return [...new Set(this.items.map((i) => i.storeId))]
  },
})
