import {createApp} from 'vue'
import App from './App.vue'

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

axios.defaults.baseURL = 'http://127.0.0.1:5000';

app.use(VueAxios, axios)

// 路由
import router from "@/router";

app.use(router)

//格式化时间
const dayjs = require('dayjs')
app.config.globalProperties.$dayjs = dayjs


app.mount('#app')

