import {createRouter, createWebHistory} from "vue-router"
import backStage from "@/components/BackStage";
import FrontEnd from "@/components/FrontEnd";

const routes = [
    {
        path: "/",
        name: "index",
        component: FrontEnd
    },
    {
        path: "/backstage",
        name: "backstage",
        component: backStage
    }
]

const router = createRouter({
    mode: "history",
    history: createWebHistory(),
    routes
})

export default router
