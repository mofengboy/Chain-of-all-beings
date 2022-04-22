<template>
  <div>
    <div class="title">标记垃圾区块</div>
    <el-form label-position="right" label-width="90px" size="default">
      <div>
        <el-form-item label="众生区块ID">
          <el-input placeholder="Please input" v-model="blockID" :autosize="{minRows: 1}" type="textarea"
                    @blur="blurBlockID">
          </el-input>
          <div v-show="blockID!==''">
            <div v-if="!isBlockID" style="color:#c45656">无效的区块ID，请重新输入</div>
            <div v-if="isBlockID">有效的区块ID，
              <el-link type="primary" :href="blockDetailUrl" target="_blank">查看区块详情</el-link>
            </div>
          </div>
        </el-form-item>
        <el-button style="width: 100%" type="primary" v-on:click="marker">提交</el-button>
      </div>
    </el-form>
  </div>
</template>

<script>

import {ElNotification} from "element-plus";

export default {
  name: "GarbageBlockMark",
  data() {
    return {
      token: this.getToken(),
      rules: "",
      blockID: "",
      isBlockID: false
    }
  },
  methods: {
    getToken: function () {
      return localStorage.getItem('token');
    },
    blurBlockID: function () {
      this.verifyBlockOfBeings(this.blockID)
    },
    verifyBlockOfBeings: function (block_id) {
      const _this = this
      this.axios({
        method: 'get',
        url: '/chain/beings/get?block_id=' + block_id
      }).then((res) => {
            _this.isBlockID = res.data["is_success"];
          }
      )
    },
    marker: function () {
      const _this = this
      this.axios({
        method: 'post',
        url: '/backstage/beings/marker',
        data: JSON.stringify({
          "token": _this.token,
          "block_id": _this.blockID
        }),
        headers: {"content-type": "	application/json"}
      }).then((res) => {
        if (res.data["is_success"] === true) {
          ElNotification({
            title: 'Success',
            message: "修改成功",
            type: 'success',
          })
        } else {
          ElNotification({
            title: 'Error',
            message: res.data["data"],
            type: 'error',
          })
        }
      })
    }
  },
  computed: {
    blockDetailUrl: {
      get() {
        return "/chain/beings/detail?block_id=" + this.blockID
      }
    }
  }
}
</script>

<style scoped>
.title {
  margin-bottom: 10px;
  width: 100%;
  text-align: center;
}
</style>
