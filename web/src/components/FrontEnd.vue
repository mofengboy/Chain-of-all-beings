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
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1)
}

.main {
  margin: 10px 0;
  padding: 10px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1)
}

.footer {
}
</style>
