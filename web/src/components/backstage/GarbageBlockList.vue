<template>
  <div>
    <div v-show="!is_detail">
      <div class="search-epoch">
        <el-form label-position="top">
          <div>
            <el-form-item label="搜索众生区块ID">
              <el-input v-model="search_block_id">
                <template #append>
                  <el-button v-on:click="searchGarbageBlock">搜索</el-button>
                </template>
              </el-input>
            </el-form-item>
          </div>
        </el-form>
      </div>
      <div style="text-align: center;">本主节点标记的区块</div>
      <el-table stripe :data="tableData" class="main-table">
        <el-table-column prop="beings_block_id" label="众生区块ID"></el-table-column>
        <el-table-column header-align="center" prop="votes" label="当前票数" width="80"></el-table-column>
        <el-table-column header-align="center" fixed="right" label="操作" width="135">
          <template #default="scope">
            <el-button size="small" v-on:click="openDetail(scope.row.beings_block_id)">详情</el-button>
            <el-button size="small" type="danger" v-on:click="unmark(scope.row.beings_block_id)">撤销
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div>
        <el-button type="primary" style="margin-top:10px;width: 100%" v-on:click="getListOfGarbageBlock">获取更多</el-button>
      </div>
    </div>
    <div v-show="is_detail" class="detail">
      <el-page-header content="推荐区块详细信息" @back="closeDetail"/>
      <div class="detail-header">
        <el-tag class="ml-2" type="success" style="margin-right:10px">区块ID:{{ timesBlockDetail["beings_block_id"] }}
        </el-tag>
        <el-tag class="ml-2" type="success">选举周期:{{ timesBlockDetail["election_period"] }}</el-tag>
      </div>
      <div class="detail-votes">总票数：{{ timesBlockDetail["votes"] }}</div>
      <div class="detail-vote-list">
        <p>投票列表</p>
      </div>
    </div>
  </div>
</template>

<script>
import {ElNotification, ElTable, ElTableColumn} from "element-plus";

export default {
  name: "GarbageBlockList",
  data() {
    return {
      tableData: [],
      timesBlockDetail: {},
      start: 0,
      end: 8,
      moreOffset: 0,
      is_detail: false,
      block_id: "",
      search_block_id: "",
      epoch: 0,
      electionPeriodValue: 20160,
      token: this.getToken()
    }
  },
  components: {
    ElTable,
    ElTableColumn
  },
  created() {
    const _this = this
    this.getPeriod().then(() => {
      _this.getListOfGarbageBlock()
    })
  },
  beforeUnmount() {
    clearInterval(this.timer);
  },
  methods: {
    getToken: function () {
      return localStorage.getItem('token');
    },
    openDetail: function (beings_block_id) {
      this.is_detail = true
      this.getGarbageBlock(beings_block_id)
    },
    closeDetail: function () {
      this.is_detail = false
    },
    getPeriod: function () {
      const _this = this
      return this.axios({
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
    getListOfGarbageBlock: function () {
      const loading = this.$loading({lock: true, text: '正在计算中...', background: 'rgba(0, 0, 0, 0.7)'})
      let election_period = Math.floor(this.epoch / this.electionPeriodValue)
      const _this = this
      this.axios({
        method: 'get',
        url: "/garbage_block_list/get?election_period=" + election_period + "&offset=" + _this.moreOffset + "&count=8"
      }).then((res) => {
        loading.close()
        if (res.data["is_success"]) {
          const data_list = res.data["data"]
          if (data_list.length === 0) {
            ElNotification({
              title: 'Info',
              message: "没有更多区块了，去发布一个吧",
              type: 'info',
            })
          } else {
            _this.moreOffset += data_list.length
            for (let i = 0; i < data_list.length; i++) {
              this.tableData.push({
                id: data_list[i]["id"],
                election_period: data_list[i]["election_period"],
                beings_block_id: data_list[i]["beings_block_id"],
                votes: data_list[i]["votes"]
              })
            }
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
    getGarbageBlock: function (beings_block_id) {
      const loading = this.$loading({lock: true, text: '正在计算中...', background: 'rgba(0, 0, 0, 0.7)'})
      const _this = this
      this.axios({
        method: 'get',
        url: "/garbage_block/get?block_id=" + beings_block_id
      }).then((res) => {
        loading.close()
        if (res.data["is_success"]) {
          const data = res.data["data"]
          _this.timesBlockDetail = {
            id: data["id"],
            election_period: data["election_period"],
            beings_block_id: data["beings_block_id"],
            votes: data["votes"],
            vote_list: data["vote_list"],
            status: data["status"],
            create_time: data["create_time"]
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
    searchGarbageBlock: function () {
      const loading = this.$loading({lock: true, text: '正在计算中...', background: 'rgba(0, 0, 0, 0.7)'})
      const _this = this
      this.axios({
        method: 'get',
        url: "/garbage_block/get?block_id=" + this.search_block_id
      }).then((res) => {
        loading.close()
        if (res.data["is_success"]) {
          const data = res.data["data"]
          const beings_block_id = data["beings_block_id"]
          for (let i = 0; i < _this.tableData.length; i++) {
            if (beings_block_id === _this.tableData[i]["beings_block_id"]) {
              _this.tableData.splice(i, 1)
            }
          }
          _this.tableData.unshift({
            id: data["id"],
            election_period: data["election_period"],
            beings_block_id: data["beings_block_id"],
            votes: data["votes"]
          })
        } else {
          ElNotification({
            title: '搜索失败',
            message: res.data["data"],
            type: 'error',
          })
        }
      })
    },
    unmark: function (beings_block_id) {
      const _this = this
      this.axios({
        method: 'post',
        url: '/backstage/beings/unmark',
        data: JSON.stringify({
          "token": _this.token,
          "block_id": beings_block_id
        }),
        headers: {"content-type": "	application/json"}
      }).then((res) => {
        if (res.data["is_success"] === true) {
          for (let i = 0; i < _this.tableData.length; i++) {
            if (beings_block_id === _this.tableData[i]["beings_block_id"]) {
              _this.tableData.splice(i, 1)
              break
            }
          }
          ElNotification({
            title: 'Success',
            message: res.data["data"],
            type: 'success',
          })
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
.main-table {
  width: 100%;
  text-align: center;
}

.detail-header {
  margin-top: 10px;
}

.detail-votes {
  margin-top: 10px;
}

.detail-vote-list {
  margin-top: 10px;
}

</style>
