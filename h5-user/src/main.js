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
  Swipe,
  SwipeItem,
  PullRefresh,
  Checkbox,
  ActionSheet,
  RadioGroup,
  Radio,
  Rate,
  Uploader,
  Notify,
  Skeleton,
  Card,
  Tag,
  Stepper,
  SubmitBar,
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
app.use(Swipe)
app.use(SwipeItem)
app.use(PullRefresh)
app.use(Checkbox)
app.use(ActionSheet)
app.use(RadioGroup)
app.use(Radio)
app.use(Rate)
app.use(Uploader)
app.use(Notify)
app.use(Skeleton)
app.use(Card)
app.use(Tag)
app.use(Stepper)
app.use(SubmitBar)
app.mount('#app')
