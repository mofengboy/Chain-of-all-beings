<template>
  <div>
    <div class="header">
      <h1>众生之链管理端</h1>
    </div>
    <div class="top-menu">
      <el-menu mode="horizontal" @select="handleSelect">
        <el-menu-item index="1">首页</el-menu-item>
        <el-sub-menu index="2">
          <template #title>区块管理</template>
          <el-menu-item index="2-1">众生区块审核</el-menu-item>
          <el-menu-item index="2-2">众生区块待生成队列</el-menu-item>
          <el-menu-item index="2-3">时代区块推荐</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="3">
          <template #title>节点管理</template>
          <el-menu-item index="3-1">申请书列表(本节点)</el-menu-item>
          <el-menu-item index="3-2">申请书列表(其他节点)</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </div>
    <div class="main">
      <BeingsAudit v-if="menu==='2-1'" :token="token"></BeingsAudit>
      <BeingsWaitingRelease v-if="menu==='2-2'" :token="token"></BeingsWaitingRelease>
      <MainNodeApplicationList v-if="menu==='3-1'" :token="token"></MainNodeApplicationList>
      <OtherNodeApplicationList v-if="menu==='3-2'" :token="token"></OtherNodeApplicationList>
    </div>
  </div>
</template>

<script>
import BeingsAudit from "@/components/backstage/BeingsAudit";
import BeingsWaitingRelease from "@/components/backstage/BeingsWaitingRelease";
import MainNodeApplicationList from "@/components/backstage/MainNodeApplicationList";
import OtherNodeApplicationList from "@/components/backstage/OtherNodeApplicationList";

export default {
  name: "BackstageMain",
  components: {OtherNodeApplicationList, MainNodeApplicationList, BeingsAudit, BeingsWaitingRelease},
  props: ['token'],
  data() {
    return {
      menu: 1,
    }
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
</style>
