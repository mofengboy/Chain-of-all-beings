import {createApp} from 'vue'
import App from './App.vue'
import config from "./config"

const app = createApp(App)
//用户自定义配置
app.config.globalProperties.$userConfig = config

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

axios.defaults.baseURL = config.server_url
//axios 拦截token失效
axios.interceptors.response.use(res => {
    if (localStorage.getItem("token") != null) {
        if (res.data["data"] === "Token无效") {
            localStorage.removeItem("token")
            window.location.href = "/backstage/login"
        }
    }
    return res
})

app.use(VueAxios, axios)

// 路由
import router from "@/router";

app.use(router)

//格式化时间
const dayjs = require('dayjs')
app.config.globalProperties.$dayjs = dayjs

//host_url
const url = window.location.href
const host = url.split("/")
app.config.globalProperties.$host_url = host[0] + host[1] + host[2]


app.mount('#app')

