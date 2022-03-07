<template>
  <div>
    <div class="header">
      <h1>众生之链管理端</h1>
    </div>
    <div class="top-menu">
      <el-menu mode="horizontal" @select="handleSelect">
        <el-menu-item index="1">首页</el-menu-item>
        <el-menu-item index="2">众生链审核</el-menu-item>
        <el-menu-item index="3">众生链待发布列表</el-menu-item>
        <el-menu-item index="4">时代链推荐</el-menu-item>
      </el-menu>
    </div>
    <div class="main">
      <BeingsAudit v-if="menu==='2'" :token="token"></BeingsAudit>
      <BeingsWaitingRelease v-if="menu==='3'" :token="token"></BeingsWaitingRelease>
    </div>
  </div>
</template>

<script>
import BeingsAudit from "@/components/backstage/BeingsAudit";
import BeingsWaitingRelease from "@/components/backstage/BeingsWaitingRelease";

export default {
  name: "BackstageMain",
  components: {BeingsAudit, BeingsWaitingRelease},
  props: ['token'],
  data() {
    return {
      menu: 1,
    }
  },
  methods: {
    handleSelect: function (key, keyPath) {
      console.log(key, keyPath)
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
