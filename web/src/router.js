import {createRouter, createWebHistory} from "vue-router"
import backStage from "@/components/BackStage";
import FrontEnd from "@/components/FrontEnd";
import BackstageLogin from "@/components/backstage/BackstageLogin";
import MainNodeApply from "@/components/front_end/MainNodeApply";
import BlockOfBeings from "@/components/front_end/BlockOfBeings";
import ReleaseBlock from "@/components/front_end/ReleaseBlock";
import NotFound from "@/components/NotFound";
import FrontHome from "@/components/front_end/FrontHome";
import BlockDetail from "@/components/front_end/BlockDetail";

const routes = [
    //首页
    {
        path: "/",
        name: "index",
        component: FrontEnd,
        children: [
            //首页介绍
            {
                path: '/introduction',
                name: "Introduction",
                component: FrontHome
            },
            //众生区块查询
            {
                path: "/chain/beings",
                name: "BlockOfBeings",
                component: BlockOfBeings,
                children: [
                    // 区块详细信息
                    {
                        path: '/chain/beings/detail',
                        name: "BlockDetail",
                        component: BlockDetail
                    },
                ]
            },
            //众生区块发布
            {
                path: "/release/beings",
                name: "ReleaseBlock",
                component: ReleaseBlock
            },
            //主节点申请
            {
                path: "/main_node_apply",
                name: "MainNodeApply",
                component: MainNodeApply
            },
        ]
    },

    //后台登录
    {
        path: "/backstage/login",
        name: "login",
        component: BackstageLogin
    },
    //后台
    {
        path: "/backstage",
        name: "backstage",
        component: backStage
    },
    //404
    {
        path: '/:pathMatch(.*)*',
        name: "404",
        component: NotFound
    },
]

const router = createRouter({
    mode: "history",
    history: createWebHistory(),
    routes
})

export default router
