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
  },
  created() {
    this.getRecordNumber()
  },
  methods: {
    getRecordNumber: function () {
      const _this = this
      this.axios({
        method: 'get',
        url: '/record_number/get',
      }).then((res) => {
        if (res.data["is_success"] === true) {
        _this.recordNumber = res.data["data"]["content"]
        }
      })
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
