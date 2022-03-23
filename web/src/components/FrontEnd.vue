<template>
  <div>
    <div class="header">
      <GlobalHeader></GlobalHeader>
    </div>
    <div class="top-menu">
      <el-menu mode="horizontal" @select="handleSelect">
        <el-menu-item index="1">首页</el-menu-item>
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
      <FrontHome v-if="menu==='1'"></FrontHome>
      <BlockOfBeings v-if="menu==='2-1'"></BlockOfBeings>
      <ReleaseBlock v-if="menu==='3'"></ReleaseBlock>
      <MainNodeApply v-if="menu==='4'"></MainNodeApply>
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
import BlockOfBeings from "@/components/front_end/BlockOfBeings";
import ReleaseBlock from "@/components/front_end/ReleaseBlock";
import FrontHome from "@/components/front_end/FrontHome";
import MainNodeApply from "@/components/front_end/MainNodeApply";

export default {
  name: "FrontEnd",
  data() {
    return {
      menu: "1"
    }
  },
  components: {
    FrontHome,
    ReleaseBlock,
    GlobalHeader,
    GlobalFooter,
    BlockOfBeings,
    ElMenu,
    ElSubMenu,
    ElMenuItem,
    MainNodeApply,
  },
  methods: {
    handleSelect: function (key) {
      this.menu = key
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
