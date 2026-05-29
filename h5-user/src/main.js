import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

import {
  Button,
  NavBar,
  Image,
  Search,
  List,
  Tabs,
  Tab,
  CellGroup,
  Cell,
  Field,
  Popup,
  Tabbar,
  TabbarItem,
  Icon,
  Toast,
  Dialog,
} from 'vant'
import 'vant/lib/index.css'
import './assets/styles/global.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(Button)
app.use(NavBar)
app.use(Image)
app.use(Search)
app.use(List)
app.use(Tabs)
app.use(Tab)
app.use(CellGroup)
app.use(Cell)
app.use(Field)
app.use(Popup)
app.use(Tabbar)
app.use(TabbarItem)
app.use(Icon)
app.use(Toast)
app.use(Dialog)
app.mount('#app')
