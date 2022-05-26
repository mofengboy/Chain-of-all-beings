<template>
  <div>
    <div style="margin-bottom: 20px">
      <el-button type="primary" style="width: 100%" v-on:click="initSimpleUserVote">计算普通用户票数</el-button>
      <p style="font-size: 10px">tips：初始化当前选举周期所有普通用户的票数,每个选举周期计算一次即可。</p>
    </div>
    <div class="search-epoch">
      <el-form label-position="top">
        <div>
          <el-form-item label="搜索用户票数信息">
            <el-input v-model="searchSimpleUserPK" placeholder="普通用户公钥">
              <template #append>
                <el-button v-on:click="searchSimpleUserVote">搜索</el-button>
              </template>
            </el-input>
          </el-form-item>
        </div>
      </el-form>
    </div>
    <div style="text-align: center;margin-top: 10px">普通用户票数信息列表</div>
    <el-table stripe :data="tableData" class="main-table">
      <el-table-column prop="user_pk" label="用户公钥"></el-table-column>
      <el-table-column header-align="center" prop="used_vote" label="已使用的票数" width="80"></el-table-column>
      <el-table-column header-align="center" prop="total_vote" label="总票数" width="80"></el-table-column>
      <el-table-column header-align="center" prop="update_time" label="更新时间" width="105"></el-table-column>
      <el-table-column header-align="center" fixed="right" label="操作" width="100">
        <template #default="scope">
          <el-button size="small" v-on:click="openDialog(scope.row)">修改总票数</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div>
      <el-button type="primary" style="margin-top:10px;width: 100%" v-on:click="getSimpleUserVoteList">获取更多</el-button>
    </div>
    <div>
      <!--修改总票数弹框-->
      <el-dialog append-to-body v-model="dialog" title="修改总票数" width="80%">
        <div>
          <el-form>
            <p>1. 修改后的总票数不能低于已经使用的票数</p>
            <p>2. 修改后的总票数不能高于当前主节点剩余的票数</p>
            <div>
              <el-form-item label="用户公钥：" label-width="120px">
                <el-input v-model="user_pk" readonly autosize type="textarea"/>
              </el-form-item>
            </div>
            <div>
              <el-form-item label="当前总票数：" label-width="120px">
                <el-input v-model="total_vote" readonly/>
              </el-form-item>
            </div>
            <div>
              <el-form-item label="已使用票数：" label-width="120px">
                <el-input v-model="used_vote" readonly/>
              </el-form-item>
            </div>
            <div>
              <el-form-item label="总票数修改为：" label-width="120px">
                <el-input v-model="modify_total_vote"/>
              </el-form-item>
            </div>
            <el-button type="primary" style="width: 100%" v-on:click="modifySimpleUserVote">提交修改</el-button>
          </el-form>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script>
import {ElNotification} from "element-plus";

export default {
  name: "SimpleUserVote",
  data() {
    return {
      tableData: [],
      token: this.getToken(),
      currentID: 0,
      searchSimpleUserPK: "",
      dialog: false,
      user_pk: "",
      total_vote: 0,
      used_vote: 0,
      modify_total_vote: this.total_vote
    }
  },
  created() {
    this.getSimpleUserVoteList()
  },
  methods: {
    getToken: function () {
      return localStorage.getItem('token');
    },
    openDialog: function (row) {
      this.dialog = true
      this.user_pk = row.user_pk
      this.total_vote = row.total_vote
      this.used_vote = row.used_vote
      this.modify_total_vote = row.total_vote
    },
    getSimpleUserVoteList: function () {
      const _this = this
      this.axios({
        method: 'post',
        url: '/backstage/simple_user_vote_list/get',
        data: JSON.stringify({
          "token": _this.token,
          "offset": _this.currentID,
          "count": _this.currentID + 8
        }),
        headers: {"content-type": "	application/json"}
      }).then((res) => {
        if (res.data["is_success"] === true) {
          const user_pk_list = res.data["data"]
          _this.currentID += user_pk_list.length
          for (let i = 0; i < user_pk_list.length; i++) {
            _this.getSimpleUserVote(user_pk_list[i])
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
    getSimpleUserVote: function (user_pk) {
      const _this = this
      this.axios({
        method: 'post',
        url: '/backstage/simple_user_vote/get',
        data: JSON.stringify({
          "user_pk": user_pk
        }),
        headers: {"content-type": "	application/json"}
      }).then((res) => {
        if (res.data["is_success"] === true) {
          const data = res.data["data"]
          let is_exit = false
          for (let i = 0; i < _this.tableData.length; i++) {
            if (data["user_pk"] === _this.tableData[i]["user_pk"]) {
              is_exit = true
            }
          }
          if (!is_exit) {
            _this.tableData.push({
              "id": data["id"],
              "election_period": data["election_period"],
              "user_pk": data["user_pk"],
              "total_vote": data["total_vote"],
              "used_vote": data["used_vote"],
              "update_time": _this.$dayjs.unix(data["update_time"].substring(0, 10)).format(),
              "create_time": _this.$dayjs.unix(data["create_time"].substring(0, 10)).format()
            })
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
    searchSimpleUserVote: function () {
      const _this = this
      this.axios({
        method: 'post',
        url: '/backstage/simple_user_vote/get',
        data: JSON.stringify({
          "user_pk": _this.searchSimpleUserPK
        }),
        headers: {"content-type": "	application/json"}
      }).then((res) => {
        if (res.data["is_success"] === true) {
          const data = res.data["data"]
          for (let i = 0; i < _this.tableData.length; i++) {
            if (data["user_pk"] === _this.tableData[i]["user_pk"]) {
              _this.tableData.splice(i, 1)
            }
          }
          _this.tableData.unshift({
            "id": data["id"],
            "election_period": data["election_period"],
            "user_pk": data["user_pk"],
            "total_vote": data["total_vote"],
            "used_vote": data["used_vote"],
            "update_time": _this.$dayjs.unix(data["update_time"].substring(0, 10)).format(),
            "create_time": _this.$dayjs.unix(data["create_time"].substring(0, 10)).format()
          })
        } else {
          ElNotification({
            title: '获取失败',
            message: res.data["data"],
            type: 'error',
          })
        }
      })
    },
    modifySimpleUserVote: function () {
      const _this = this
      this.axios({
        method: 'post',
        url: '/backstage/simple_user_vote/modify',
        data: JSON.stringify({
          "token": _this.token,
          "user_pk": _this.user_pk,
          "total_vote": _this.modify_total_vote
        }),
        headers: {"content-type": "	application/json"}
      }).then((res) => {
        if (res.data["is_success"] === true) {
          ElNotification({
            title: '修改成功',
            message: "",
            type: 'success',
          })
        } else {
          ElNotification({
            title: '修改失败',
            message: "",
            type: 'error',
          })
        }
      })
    },
    initSimpleUserVote: function () {
      const _this = this
      this.axios({
        method: 'post',
        url: '/backstage/simple_user_vote/init',
        data: JSON.stringify({
          "token": _this.token
        }),
        headers: {"content-type": "	application/json"}
      }).then((res) => {
        if (res.data["is_success"] === true) {
          ElNotification({
            title: '初始化完成',
            message: "",
            type: 'success',
          })
          _this.getSimpleUserVoteList()
        } else {
          ElNotification({
            title: '初始化失败',
            message: "",
            type: 'error',
          })
        }
      })
    }
  }
}
</script>

<style scoped>
</style>
