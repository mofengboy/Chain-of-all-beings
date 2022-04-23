<template>
  <div>
    <div v-show="!is_detail">
      <el-table :data="tableData" style="width: 100%" @row-click="openDetail">
        <el-table-column prop="epoch" label="上链期次" width="100"></el-table-column>
        <el-table-column label="内容摘要">
          <template #default="scope">
            <el-tooltip class="box-item" content="点击查看详情" placement="top">
              <div>{{ scope.row.body_digest }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
      <div>
        <el-button type="primary" style="margin-top:10px;width: 100%" v-on:click="getIdListOfBeingsByOffset">获取更多
        </el-button>
      </div>
      <div class="search-epoch">
        <el-form label-position="top">
          <div>
            <el-form-item label="上链期次范围查询（包含开始，不包含结束):">
              <el-input-number class="epoch-input" v-model="start_epoch" :min=0
                               @change="changeStartEpoch"></el-input-number>
              <el-input-number class="epoch-input" v-model="end_epoch" :min=0
                               @change="changeEndEpoch"></el-input-number>
            </el-form-item>
          </div>
          <div>
            <el-button type="primary" style="width: 100%" v-on:click="getIdListOfBeingsByEpoch">查找</el-button>
          </div>
        </el-form>
      </div>
    </div>
    <div v-show="is_detail" class="detail">
      <el-page-header content="区块详细信息" @back="closeDetail"/>
      <router-view></router-view>
    </div>
  </div>
</template>

<script>
import {ElNotification, ElTable, ElTableColumn} from "element-plus";

export default {
  name: "BlockOfBeings",
  data() {
    return {
      tableData: [],
      start: 0,
      end: 8,
      more_offset: 0,
      is_detail: false,
      block_id: "",
      start_epoch: 0,
      end_epoch: 8,
    }
  },
  components: {
    ElTable,
    ElTableColumn
  },
  created() {
    this.getIdListOfBeingsByOffset()
    this.is_detail = this.$route.query.block_id !== undefined;
  },
  methods: {
    openDetail: function (event) {
      for (let i = 0; i < this.tableData.length; i++) {
        if (event.id === this.tableData[i]["id"]) {
          this.is_detail = true
          this.block_id = this.tableData[i]["block_id"]
          break
        }
      }
      const _this = this
      this.$router.push({path: '/chain/beings/detail', query: {block_id: _this.block_id}})
    },
    closeDetail: function () {
      this.$router.push('/chain/beings')
      this.is_detail = false
    },
    changeStartEpoch: function (value) {
      if (this.end_epoch - value > 8) {
        this.end_epoch = value + 8
      }
      if (value > this.end_epoch) {
        this.end_epoch = value
      }
    },
    changeEndEpoch: function (value) {
      if (value - this.start_epoch > 8) {
        this.start_epoch = value - 8
      }
      if (value < this.start_epoch) {
        this.start_epoch = value
      }
    },
    getMaxEpoch: function () {
      return this.axios({
        method: 'get',
        url: '/chain/beings/max_epoch'
      }).then((res) => {
        if (res.data["is_success"]) {
          return parseInt(res.data["data"]) + 1
        } else {
          ElNotification({
            title: '获取max epoch失败',
            message: res.data["data"],
            type: 'error',
          })
        }
      })
    },
    //倒序获取区块列表
    getIdListOfBeingsByOffset: function () {
      const _this = this
      this.axios({
        method: 'get',
        url: "/chain/beings_list/offset_get?offset=" + _this.more_offset + "&count=8"
      }).then((res) => {
        if (res.data["is_success"]) {
          const id_list = res.data["data"]
          if (id_list.length === 0) {
            ElNotification({
              title: 'Info',
              message: "没有更多区块了，去发布一个吧",
              type: 'info',
            })
          } else {
            for (let i = 0; i < id_list.length; i++) {
              let is_exit = false
              for (let k = 0; k < _this.tableData.length; k++) {
                if (_this.tableData[k]["block_id"] === id_list[i]["block_id"]) {
                  is_exit = true
                  break
                }
              }
              if (!is_exit) {
                this.tableData.push({
                  id: id_list[i]["id"],
                  block_id: id_list[i]["block_id"],
                  epoch: id_list[i]["epoch"],
                  body_digest: Buffer.from(id_list[i]["body_digest"], "base64").toString("utf-8").substring(0, 32)
                })
              }
            }
            _this.more_offset += id_list.length
          }
        } else {
          ElNotification({
            title: '获取区块列表ID失败',
            message: res.data["data"],
            type: 'error',
          })
        }
      })
    },
    getIdListOfBeingsByEpoch: function () {
      const _this = this
      this.axios({
        method: 'get',
        url: '/chain/beings_list/get?start=' + _this.start_epoch + "&end=" + _this.end_epoch
      }).then((res) => {
        if (res.data["is_success"]) {
          const id_list = res.data["data"]
          if (id_list.length === 0) {
            ElNotification({
              title: 'Info',
              message: "没有更多区块了，去发布一个吧",
              type: 'info',
            })
          } else {
            for (let i = 0; i < id_list.length; i++) {
              let is_exit = false
              for (let k = 0; k < _this.tableData.length; k++) {
                if (_this.tableData[k]["block_id"] === id_list[i]["block_id"]) {
                  is_exit = true
                  break
                }
              }
              if (!is_exit) {
                this.tableData.push({
                  id: id_list[i]["id"],
                  block_id: id_list[i]["block_id"],
                  epoch: id_list[i]["epoch"],
                  body_digest: Buffer.from(id_list[i]["body_digest"], "base64").toString("utf-8").substring(0, 32)
                })
              }
            }
            _this.more_offset += id_list.length
          }
        } else {
          ElNotification({
            title: '获取区块列表ID失败',
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
.detail {

}

.search-epoch {
  margin: 10px 0;
}

.epoch-input {
  margin: 0 25px 0 0;
}
</style>
