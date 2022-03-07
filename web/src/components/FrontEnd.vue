<template>
  <div>
    <div class="header">
      <GlobalHeader></GlobalHeader>
    </div>
    <div class="top-menu">
      <el-menu mode="horizontal" @select="handleSelect">
        <el-menu-item index="1">首页</el-menu-item>
        <el-sub-menu index="2">
          <template #title>众生之链</template>
          <el-menu-item index="2-1">众生链</el-menu-item>
          <el-menu-item index="2-2">时代链</el-menu-item>
          <el-menu-item index="2-3">垃圾标识链</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="3">发布</el-menu-item>
        <el-menu-item index="4">查询</el-menu-item>
        <el-menu-item index="5">源码</el-menu-item>
      </el-menu>
    </div>
    <div class="main">
      <BlockOfBeings v-if="menu==='2-1'"></BlockOfBeings>
      <ReleaseBlock v-if="menu==='3'"></ReleaseBlock>
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

export default {
  name: "FrontEnd",
  data() {
    return {
      menu: 1
    }
  },
  components: {
    ReleaseBlock,
    GlobalHeader,
    GlobalFooter,
    BlockOfBeings,
    ElMenu,
    ElSubMenu,
    ElMenuItem,
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
  margin: 20px 0;
  padding: 25px 10px 10px 10px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1)
}

.footer {
}
</style>
