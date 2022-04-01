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
        <el-menu-item index="3">众生区块发布</el-menu-item>
        <el-menu-item index="4">主节点申请</el-menu-item>
        <el-menu-item index="5">开源仓库</el-menu-item>
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
    return {}
  },
  components: {
    GlobalHeader,
    GlobalFooter,
    ElMenu,
    ElSubMenu,
    ElMenuItem,
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
        case '3':
          this.$router.push("/release/beings")
          break
        case '4':
          this.$router.push("/main_node_apply")
          break
        case '5':
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
