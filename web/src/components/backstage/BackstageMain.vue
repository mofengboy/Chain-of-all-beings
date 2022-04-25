<template>
  <div>
    <div class="header">
      <h1>众生之链管理端</h1>
    </div>
    <div class="top-menu">
      <el-menu mode="horizontal" @select="handleSelect">
        <el-menu-item index="1">首页</el-menu-item>
        <el-sub-menu index="2">
          <template #title>众生区块管理</template>
          <el-menu-item index="2-1">众生区块审核</el-menu-item>
          <el-menu-item index="2-2">众生区块待生成队列</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="3">
          <template #title>时代区块管理</template>
          <el-menu-item index="3-1">时代区块推荐</el-menu-item>
          <el-menu-item index="3-2">时代区块推荐列表</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="4">
          <template #title>垃圾区块管理</template>
          <el-menu-item index="4-1">垃圾区块标记</el-menu-item>
          <el-menu-item index="4-2">垃圾区块标记列表</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="5">
          <template #title>节点管理</template>
          <el-menu-item index="5-1">申请加入主节点(本节点)</el-menu-item>
          <el-menu-item index="5-2">申请加入主节点(其他节点)</el-menu-item>
          <el-menu-item index="5-3">申请删除主节点(本节点)</el-menu-item>
          <el-menu-item index="5-4">申请删除主节点(其他节点)</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="6">
          <template #title>投票管理</template>
          <el-menu-item index="6-1">普通用户票数信息</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="7">网站配置</el-menu-item>
      </el-menu>
    </div>
    <div class="main">
      <BeingsAudit v-if="menu==='2-1'"></BeingsAudit>
      <BeingsWaitingRelease v-if="menu==='2-2'"></BeingsWaitingRelease>
      <TimeBlockRecommend v-if="menu==='3-1'"></TimeBlockRecommend>
      <TimesBlockList v-if="menu==='3-2'"></TimesBlockList>
      <GarbageBlockMark v-if="menu==='4-1'"></GarbageBlockMark>
      <GarbageBlockList v-if="menu==='4-2'"></GarbageBlockList>
      <MainNodeApplicationList v-if="menu==='5-1'"></MainNodeApplicationList>
      <OtherNodeApplicationList v-if="menu==='5-2'"></OtherNodeApplicationList>
      <MainNodeActiveDelete v-if="menu==='5-3'"></MainNodeActiveDelete>
      <OtherNodeActiveDeleteList v-if="menu==='5-4'"></OtherNodeActiveDeleteList>
      <SimpleUserVote v-if="menu==='6-1'"></SimpleUserVote>
      <WebConfig v-if="menu==='7'"></WebConfig>
    </div>
  </div>
</template>

<script>
import BeingsAudit from "@/components/backstage/BeingsAudit";
import BeingsWaitingRelease from "@/components/backstage/BeingsWaitingRelease";
import MainNodeApplicationList from "@/components/backstage/MainNodeApplicationList";
import OtherNodeApplicationList from "@/components/backstage/OtherNodeApplicationList";
import WebConfig from "@/components/backstage/WebConfig";
import TimeBlockRecommend from "@/components/backstage/TimeBlockRecommend";
import TimesBlockList from "@/components/backstage/TimesBlockList";
import SimpleUserVote from "@/components/backstage/SimpleUserVote";
import GarbageBlockMark from "@/components/backstage/GarbageBlockMark";
import GarbageBlockList from "@/components/backstage/GarbageBlockList";
import MainNodeActiveDelete from "@/components/backstage/MainNodeActiveDelete";
import OtherNodeActiveDeleteList from "@/components/backstage/OtherNodeActiveDeleteList";

export default {
  name: "BackstageMain",
  components: {
    GarbageBlockList,
    GarbageBlockMark,
    SimpleUserVote,
    TimesBlockList,
    WebConfig, OtherNodeApplicationList, MainNodeApplicationList, BeingsAudit, BeingsWaitingRelease,
    TimeBlockRecommend, MainNodeActiveDelete, OtherNodeActiveDeleteList
  },
  created() {
    this.verifyToken()
  },
  data() {
    return {
      menu: 1,
      token: this.getToken()
    }
  },
  methods: {
    handleSelect: function (key) {
      this.menu = key
    },
    getToken: function () {
      return localStorage.getItem('token');
    },
    verifyToken: function () {
      const _this = this
      this.axios({
        method: "post",
        url: "/backstage/token/verify",
        data: JSON.stringify({
          "token": _this.token
        }),
        headers: {"content-type": "application/json"}
      }).then((res) => {
        if (!res.data["is_success"]) {
          this.$router.push("/backstage/login")
        }
      })
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
