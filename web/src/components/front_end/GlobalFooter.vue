<template>
  <div class="icp" v-if="recordNumber!==''">
    <el-link href="https://beian.miit.gov.cn">ICP证：{{ recordNumber }}</el-link>
  </div>
</template>

<script>
export default {
  name: "GlobalFooter",
  data() {
    return {
      recordNumber: this.$userConfig.record_number
    }
  }
}
</script>

<style scoped>
.icp {
  width: 100%;
  margin: auto;
  text-align: center;
}

</style>
