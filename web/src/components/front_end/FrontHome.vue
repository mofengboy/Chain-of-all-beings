<template>
  <div>
    <markdown :source="indexNoticeContent"></markdown>
    <el-tag style="margin: 0 0 5px 0">更新时间：{{ indexNoticeTime }}</el-tag>
  </div>
</template>

<script>
import Markdown from "vue3-markdown-it";
import {ElNotification} from "element-plus";

export default {
  name: "FrontHome",
  components: {
    Markdown
  },
  data() {
    return {
      indexNoticeContent: "",
      indexNoticeTime: ""
    }
  },
  created() {
    this.getIndexNotice()
  },
  methods: {
    getIndexNotice: function () {
      const _this = this
      this.axios({
        method: 'get',
        url: '/index_notice/get',
      }).then((res) => {
        if (res.data["is_success"] === true) {
          const index_notice = res.data["data"]
          _this.indexNoticeContent = Buffer.from(index_notice[2], "base64").toString("utf-8")
          _this.indexNoticeTime = _this.$dayjs.unix(index_notice[3].toString().substring(0.10)).format()
        } else {
          ElNotification({
            title: '首页公告获取失败',
            message: res.data["data"],
            type: 'error',
          })
        }
      })
    },
  }
}
</script>

<style scoped>

</style>
