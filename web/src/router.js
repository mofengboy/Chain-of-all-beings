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
import TimesBlockRecommendation from "@/components/front_end/TimesBlockRecommendation";
import VotingInformation from "@/components/front_end/VotingInformation";
import BlockOfTimes from "@/components/front_end/BlockOfTimes";

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
                    }
                ]
            },
            //时代区块查询
            {
                path: "/chain/times",
                name: "BlockOfTimes",
                component: BlockOfTimes,
            },
            //记录生命
            {
                path: "/release/beings",
                name: "ReleaseBlock",
                component: ReleaseBlock
            },
            //投票信息
            {
                path: "/vote/info",
                name: "VotingInformation",
                component: VotingInformation
            },
            //众生区块推荐列表
            {
                path: "/beings/recommendation/list",
                name: "TimesBlockRecommendation",
                component: TimesBlockRecommendation
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
