import Vue from 'vue'
import axios from 'axios'

import 'normalize.css/normalize.css' // A modern alternative to CSS resets

import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
import locale from 'element-ui/lib/locale/lang/en' // lang i18n

import '@/styles/index.scss' // global css

import App from './App'
import store from './store'
import router from './router'

import '@/icons' // icon
import '@/permission' // permission control

/**
 * If you don't want to use mock-server
 * you want to use MockJs for mock api
 * you can execute: mockXHR()
 *
 * Currently MockJs will be used in the production environment,
 * please remove it before going online ! ! !
 */
if (process.env.NODE_ENV === 'production') {
  const { mockXHR } = require('../mock')
  mockXHR()
}
axios.defaults.baseURL = 'http://172.25.18.51:10001'
axios.defaults.headers.get['Content-Type'] = 'application/json;charset=UTF-8'
axios.defaults.headers.post['Content-Type'] = 'application/json;charset=UTF-8'

// set ElementUI lang to EN
Vue.use(ElementUI, { locale }, axios)
// 如果想要中文版 element-ui，按如下方式声明
// Vue.use(ElementUI)

Vue.config.productionTip = false
Vue.prototype.axios = axios

new Vue({
  el: '#app',
  router,
  store,
  render: h => h(App)
})
