import {createApp} from 'vue'
import App from './App.vue'
import config from "./config"

const app = createApp(App)

//密码库
import rs from "jsrsasign";
import rsu from "jsrsasign-util";

app.config.globalProperties.$rs = rs
app.config.globalProperties.$eccrypto = rsu

//UI
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

app.use(ElementPlus)

//多线程库
import vueWorker from 'simple-web-worker'

app.config.globalProperties.$worker = vueWorker

// axios
import axios from 'axios'
import VueAxios from 'vue-axios'

axios.defaults.baseURL = config.server_url;

app.use(VueAxios, axios)

// 路由
import router from "@/router";

app.use(router)

//格式化时间
const dayjs = require('dayjs')
app.config.globalProperties.$dayjs = dayjs

//host_url
const url = window.location.href
app.config.globalProperties.$host_url = url


app.mount('#app')

