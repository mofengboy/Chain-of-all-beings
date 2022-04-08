<template>
  <div>
    <div>
      <p style="text-align: center">普通用户票数查询（仅显示在本主节点拥有的票数）</p>
      <el-input v-model="simpleUserPk" class="simple-user-input" type="textarea" :autosize="{ minRows: 1}"
                placeholder="用户公钥"></el-input>
      <el-button class="simple-user-button" type="primary" v-on:click="getSimpleUserVote">查询</el-button>
      <div class="simple-user">
        <div class="simple-user-show">已使用票数：{{ simpleUserUsedVote }}</div>
        <div class="simple-user-show">总票数：{{ simpleUserVote }}</div>
      </div>
    </div>
    <el-divider/>
    <div>
      <p style="text-align: center">发起投票</p>
      <p class="sk-alert">注意：在投票之前一定要确认目标主节点推荐了该区块并且确保输入正确，避免票被浪费。</p>
      <el-form label-position="left" label-width="100px" size="default">
        <div>
          <el-form-item label="目标主节点ID">
            <el-input v-model="toNodeId" :autosize="{minRows: 1}" type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item label="区块ID">
            <el-input v-model="toNodeId" :autosize="{minRows: 1}" type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item label="用户私钥">
            <el-input v-model="simpleUserSk" :autosize="{minRows: 1}" type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item label="用户公钥">
            <el-input v-model="simpleUserPk" :autosize="{minRows: 1}" type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item label="投票数量">
            <el-input-number v-model="toVote" :precision="1" :step="0.1" :min="1.0"/>
          </el-form-item>
          <el-button style="width: 100%" type="primary">发起投票</el-button>
        </div>
      </el-form>
    </div>
    <el-divider/>
    <div>
      <p style="text-align: center">所有主节点的拥有的票数信息</p>
      <el-table :data="tableData" stripe style="width: 100%">
        <el-table-column prop="main_node_id" label="主节点ID"/>
        <el-table-column prop="used_vote" label="已使用票数" width="100"/>
        <el-table-column prop="total_vote" label="总票数" width="100"/>
      </el-table>
    </div>
  </div>
</template>

<script>
import {ElNotification} from "element-plus";

export default {
  name: "VotingInformation",
  data() {
    return {
      tableData: [],
      simpleUserPk: "",
      simpleUserVote: 0,
      simpleUserUsedVote: 0,
      toNodeId: "",
      toVote: 1.0,
      simpleUserSk: ""
    }
  },
  created() {
    this.getVoteList()
  },
  methods: {
    getSimpleUserVote: function () {
      const _this = this
      this.axios({
        method: 'post',
        url: '/backstage/simple_user_vote/get',
        data: JSON.stringify({
          "user_pk": _this.simpleUserPk
        }),
        headers: {"content-type": "	application/json"}
      }).then((res) => {
        if (res.data["is_success"] === true) {
          const data = res.data["data"]
          _this.simpleUserVote = data["total_vote"]
          _this.simpleUserUsedVote = data["used_vote"]
        } else {
          ElNotification({
            title: '获取失败',
            message: res.data["data"],
            type: 'error',
          })
        }
      })
    },
    getVoteList: function () {
      const _this = this
      this.axios({
        method: 'get',
        url: '/vote_list/main_node/get'
      }).then((res) => {
        if (res.data["is_success"]) {
          const data_list = res.data["data"]
          for (let i = 0; i < data_list.length; i++) {
            let main_node_user_pk = data_list[i]["node_user_pk"]
            _this.getVote(main_node_user_pk)
          }
        } else {
          ElNotification({
            title: '获取失败',
            message: res.data["data"],
            type: 'error',
          })
        }
      })
    },
    getVote: function (main_node_user_pk) {
      const _this = this
      this.axios({
        method: 'get',
        url: '/vote/main_node/get?user_pk=' + main_node_user_pk
      }).then((res) => {
        if (res.data["is_success"]) {
          const vote_info = res.data["data"]
          _this.tableData.push(vote_info)
        } else {
          ElNotification({
            title: '获取失败',
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
.simple-user-input {
  width: 70%;
  margin-right: 5%;
}

.simple-user {
  margin-top: 10px;;
}

.simple-user-show {
  display: inline-block;
  width: 20%;
  margin-right: 5%;
  text-align: left;
}

.simple-user-button {
  width: 25%;
}

.sk-alert {
  color: #c45656;
}
</style>
