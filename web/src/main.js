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

// //多线程库
import vueWorker from 'simple-web-worker'
app.config.globalProperties.$worker = vueWorker


app.mount('#app')

