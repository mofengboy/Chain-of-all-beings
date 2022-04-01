<template>
  <div>
    <div class="info-item">首页公告</div>
    <el-tag style="margin: 0 0 5px 0">上次更新时间：{{ indexNoticeTime }}</el-tag>
    <el-input
        v-model="indexNoticeContent"
        :autosize="{ minRows: 2}"
        type="textarea"
        placeholder="Please input"
    />
    <el-collapse style="width: 100%" v-model="collapse_item">
      <el-collapse-item title="预览效果(markdown格式)" name="1">
        <div>
          <Markdown class="markdown" :source="indexNoticeContent"></Markdown>
        </div>
      </el-collapse-item>
    </el-collapse>
    <el-button class="button-submit" v-on:click="modifyIndexNotice" type="primary">提交修改</el-button>
  </div>
</template>

<script>
import Markdown from "vue3-markdown-it";
import {ElNotification} from "element-plus";

export default {
  name: "WebConfig",
  components: {
    Markdown
  },
  data() {
    return {
      indexNoticeContent: "",
      indexNoticeTime: "",
      collapse_item: "1",
      token: this.getToken()
    }
  },
  created() {
    this.getIndexNotice()
  },
  methods: {
    getToken: function () {
      return localStorage.getItem('token');
    },
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
    modifyIndexNotice: function () {
      const _this = this
      this.axios({
        method: 'post',
        url: '/backstage/index_notice/modify',
        data: JSON.stringify({
          "token": _this.token,
          "content": Buffer.from(_this.indexNoticeContent, 'utf-8').toString('base64')
        }),
        headers: {"content-type": "	application/json"}
      }).then((res) => {
        if (res.data["is_success"] === true) {
          const index_notice = res.data["data"]
          _this.indexNoticeContent = Buffer.from(index_notice[2], "base64").toString("utf-8")
          _this.indexNoticeTime = _this.$dayjs.unix(index_notice[3].toString().substring(0.10)).format()
          ElNotification({
            title: 'Success',
            message: "修改成功",
            type: 'success',
          })
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
.info-item {
  margin: 0 0 10px 0;
}

.button-submit {
  margin: 10px auto;
  width: 100%;
}
</style>
