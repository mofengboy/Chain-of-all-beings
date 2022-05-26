<template>
  <div>
    <el-row>
      <el-col :span="4">
        <div>
          <el-menu @select="handleSelect">
            <el-menu-item index="1">
              首页公告
            </el-menu-item>
            <el-menu-item index="2">
              后台管理密码
            </el-menu-item>
            <el-menu-item index="3">
              备案号
            </el-menu-item>
          </el-menu>
        </div>
      </el-col>
      <el-col :span="1"></el-col>
      <el-col :span="19">
        <div v-if="subMenu==='1'">
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
        <div v-if="subMenu==='3'">
          <div class="info-item">设置备案号</div>
          <div class="info-item">当前备案号：{{ recordNumber }}</div>
          <el-input v-model="recordNumberInput"/>
          <el-button class="button-submit" v-on:click="setRecordNumber" type="primary">提交修改</el-button>
        </div>
      </el-col>
    </el-row>
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
      token: this.getToken(),
      subMenu: "1",
      recordNumber: "",
      recordNumberInput: ""
    }
  },
  created() {
    this.getIndexNotice()
  },
  methods: {
    handleSelect: function (index) {
      this.subMenu = index
      if (index === '3') {
        this.getRecordNumber()
      }
    },
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
    },
    setRecordNumber: function () {
      const _this = this
      _this.axios({
        method: 'post',
        url: '/backstage/record_number/set',
        data: JSON.stringify({
          "token": _this.token,
          "record_number": _this.recordNumberInput
        }),
        headers: {"content-type": "	application/json"}
      }).then((res) => {
        if (res.data["is_success"] === true) {
          _this.recordNumber = res.data["data"]["content"]
        } else {
          ElNotification({
            title: '修改失败',
            message: res.data["data"],
            type: 'error',
          })
        }
      })
    }
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
.markdown{
  padding: 10px;
}
</style>
