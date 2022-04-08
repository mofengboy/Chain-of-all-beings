<template>
  <div class="title">
    众生之链
  </div>
  <div class="epoch">
    <el-tag class="ml-2" type="success" style="margin-right: 10px">众生区块生成周期：{{ epoch }}</el-tag>
    <el-tag class="ml-2" type="success">选举周期：{{ Math.floor(epoch / electionPeriodValue) }}</el-tag>
  </div>
</template>

<script>
export default {
  name: "GlobalHeader",
  data() {
    return {
      epoch: 0,
      electionPeriodValue: 20160,
      timer: null,
      host_url: this.$host_url
    }
  },
  created() {
    this.getPeriod()
  },
  beforeUnmount() {
    clearInterval(this.timer);
  },
  methods: {
    addEpoch: function () {
      this.epoch = this.epoch + 1
    },
    getPeriod: function () {
      const _this = this
      this.axios({
        method: 'get',
        url: '/period/get'
      }).then((res) => {
        if (res.data["is_success"]) {
          const data = res.data["data"]
          _this.epoch = data["epoch"]
          _this.electionPeriodValue = data["election_period_value"]
          //  定时器 每一分钟增加1
          _this.timer = setInterval(_this.addEpoch, 60000)
        }
      })
    },

  }
}
</script>

<style scoped>
.title {
  margin: 10px;
  font-size: 25px;
  text-align: left;
}

.epoch {
  margin: 10px 0;
  text-align: left;
}
</style>
