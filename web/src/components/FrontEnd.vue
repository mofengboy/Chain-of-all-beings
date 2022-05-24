<template>
  <div>
    <div class="header">
      <GlobalHeader></GlobalHeader>
    </div>
    <div class="top-menu">
      <el-menu mode="horizontal" @select="handleSelect">
        <el-menu-item index="1">介绍</el-menu-item>
        <el-sub-menu index="2">
          <template #title>众生之链查询</template>
          <el-menu-item index="2-1">众生链</el-menu-item>
          <el-menu-item index="2-2">时代链</el-menu-item>
          <el-menu-item index="2-3">垃圾标识链</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="3">记录生命</el-menu-item>
        <el-sub-menu index="4">
          <template #title>投票</template>
          <el-menu-item index="4-1">发起投票</el-menu-item>
          <el-menu-item index="4-2">时代区块推荐列表</el-menu-item>
          <el-menu-item index="4-3">垃圾区块标记列表</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="5">主节点申请</el-menu-item>
        <el-menu-item index="6">源代码</el-menu-item>
      </el-menu>
    </div>
    <div class="main">
      <router-view></router-view>
    </div>
    <div class="footer">
      <GlobalFooter></GlobalFooter>
    </div>
  </div>
</template>

<script>

import {ElMenu, ElMenuItem, ElSubMenu} from "element-plus";
import GlobalHeader from "@/components/front_end/GlobalHeader";
import GlobalFooter from "@/components/front_end/GlobalFooter";

export default {
  name: "FrontEnd",
  data() {
    return {
      menu: ""
    }
  },
  components: {
    GlobalHeader,
    GlobalFooter,
    ElMenu,
    ElSubMenu,
    ElMenuItem,
  },
  mounted() {
    let pathname = window.location.pathname;
    if (pathname === "/") {
      this.$router.push("/introduction")
    }
  },
  methods: {
    handleSelect: function (key) {
      switch (key) {
        case '1':
          this.$router.push("/introduction")
          break
        case '2-1':
          this.$router.push("/chain/beings")
          break
        case '2-2':
          this.$router.push("/chain/times")
          break
        case '2-3':
          this.$router.push("/chain/garbage")
          break
        case '3':
          this.$router.push("/release/beings")
          break
        case '4-1':
          this.$router.push("/vote/info")
          break
        case '4-2':
          this.$router.push("/beings/recommendation/list")
          break
        case '4-3':
          this.$router.push("/beings/marker/list")
          break
        case '5':
          this.$router.push("/main_node_apply")
          break
        case '6':
          window.location.href = "https://github.com/mofengboy/Chain-of-all-beings"
          break
      }
    },
  }
}
</script>

<style scoped>
.header {
  margin: 20px 0;
}

.top-menu {
  /*box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1)*/
}

.main {
  margin: 10px 0;
  padding: 10px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1)
}
.footer {
}
.el-menu{
  background: #a5bffc;
  border-radius: 50px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1)
  /*box-shadow: 0px -23px 25px 0px inset, rgba(0, 0, 0, 0.15) 0px -36px 30px 0px inset, 0px -79px 40px 0px inset, rgba(0, 0, 0, 0.06) 0px 2px 1px, rgba(0, 0, 0, 0.09) 0px 4px 2px, rgba(0, 0, 0, 0.09) 0px 8px 4px, rgba(0, 0, 0, 0.09) 0px 16px 8px, rgba(0, 0, 0, 0.09) 0px 32px 16px;*/
}
.el-menu:hover{
  background: #a5bffc;
  border-radius: 50px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1)
  /*box-shadow: rgba(0, 0, 0, 0.17) 0px -23px 25px 0px inset, rgba(0, 0, 0, 0.15) 0px -36px 30px 0px inset, rgba(0, 0, 0, 0.1) 0px -79px 40px 0px inset, rgba(0, 0, 0, 0.06) 0px 2px 1px, rgba(0, 0, 0, 0.09) 0px 4px 2px, rgba(0, 0, 0, 0.09) 0px 8px 4px, rgba(0, 0, 0, 0.09) 0px 16px 8px, rgba(0, 0, 0, 0.09) 0px 32px 16px;*/
}
/*.el-menu-item{*/
/*  background: linear-gradient(-45deg, #3f00b5, #9f69fe, #27c8b7, #3f00b5);*/
/*  !*background-size: 800% 400%;*!*/
/*  !*padding: 1em 2em;*!*/
/*  display: inline-block;*/
/*  border: none;*/
/*  border-radius: 10px;*/
/*  !*font-size: 17px;*!*/
/*  !*font-weight: 700;*!*/
/*  color: white;*/
/*  transition: all .5s ease-in-out;*/
/*  animation: gradient 10s infinite cubic-bezier(.62, .28, .23, .99) both;*/
/*}*/

/*.el-menu-item:hover {*/
/*  animation: gradient 3s infinite;*/
/*  transform: scale(1.05);*/
/*}*/

/*.el-menu-item:active {*/
/*  animation: gradient 3s infinite;*/
/*  transform: scale(0.8);*/
/*}*/

/*@keyframes gradient {*/
/*  0% {*/
/*    background-position: 0% 50%;*/
/*  }*/

/*  50% {*/
/*    background-position: 100% 50%;*/
/*  }*/

/*  100% {*/
/*    background-position: 0% 50%;*/
/*  }*/
/*}*/

</style>
