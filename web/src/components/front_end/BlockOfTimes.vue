<template>
  <div>
    <div>
      <el-table :data="tableData" style="width: 100%">
        <el-table-column type="expand">
          <template #default="props">
            <el-form label-width="100px">
              <el-form-item label="时代区块ID">
                <el-input v-model="props.row.block_id" :autosize="{minRows: 1}" readonly type="textarea">
                </el-input>
              </el-form-item>
              <el-form-item label="上一区块头部Hash">
                <el-input v-model="props.row.prev_block_header" :autosize="{minRows: 1}" readonly type="textarea">
                </el-input>
              </el-form-item>
              <el-form-item label="上一区块Hash">
                <el-input v-model="props.row.prev_block" :autosize="{minRows: 1}" readonly type="textarea">
                </el-input>
              </el-form-item>
              <el-form-item label="时代区块用户公钥">
                <el-input v-model="props.row.user_pk" :autosize="{minRows: 1}" readonly type="textarea">
                </el-input>
              </el-form-item>
              <el-form-item label="时代区块用户签名">
                <el-input v-model="props.row.body_signature" :autosize="{minRows: 1}" readonly type="textarea">
                </el-input>
              </el-form-item>
              <el-form-item label="原众生区块普通用户公钥">
                <el-input :model-value="props.row.body_users_pk[0]" :autosize="{minRows: 1}" readonly type="textarea">
                </el-input>
              </el-form-item>
              <el-form-item label="原众生区块主节点用户公钥">
                <el-input :model-value="props.row.body_users_pk[1]" :autosize="{minRows: 1}" readonly
                          type="textarea">
                </el-input>
              </el-form-item>
              <el-form-item label="时间戳">
                <el-input v-model="props.row.timestamp" :autosize="{minRows: 1}" readonly type="textarea">
                </el-input>
              </el-form-item>
            </el-form>
          </template>
        </el-table-column>
        <el-table-column prop="election_period" label="上链期次(选举周期)"></el-table-column>
        <el-table-column label="选举的众生区块ID">
          <template #default="scope">
            <div>{{ scope.row.body_block_id }}</div>
          </template>
        </el-table-column>

      </el-table>
      <div>
        <el-button type="primary" style="margin-top:10px;width: 100%" v-on:click="getListOfTimesByOffset">获取更多
        </el-button>
      </div>
      <div class="search-epoch">
        <el-form label-position="top">
          <div>
            <el-form-item label="上链期次范围查询（包含开始，不包含结束):">
              <el-input-number class="epoch-input" v-model="start_election_period" :min=0
                               @change="changeStartEpoch"></el-input-number>
              <el-input-number class="epoch-input" v-model="end_election_period" :min=0
                               @change="changeEndEpoch"></el-input-number>
            </el-form-item>
          </div>
          <div>
            <el-button type="primary" style="width: 100%" v-on:click="getListOfTimesByElectionPeriod">查找</el-button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script>
import {ElNotification, ElTable, ElTableColumn} from "element-plus";

export default {
  name: "BlockOfTimes",
  data() {
    return {
      tableData: [],
      start: 0,
      end: 8,
      more_offset: 0,
      block_id: "",
      start_election_period: 0,
      end_election_period: 8,
    }
  },
  components: {
    ElTable,
    ElTableColumn
  },
  created() {
    this.getListOfTimesByOffset()
  },
  methods: {
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
    //倒序获取区块列表
    getListOfTimesByOffset: function () {
      const _this = this
      this.axios({
        method: 'get',
        url: "/chain/times_list/get?offset=" + _this.more_offset + "&count=8"
      }).then((res) => {
        if (res.data["is_success"]) {
          const id_list = res.data["data"]
          if (id_list.length === 0) {
            ElNotification({
              title: 'Info',
              message: "没有更多区块了，去投票选举吧",
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
                  election_period: id_list[i]["election_period"],
                  prev_block: id_list[i]["prev_block"],
                  prev_block_header: id_list[i]["prev_block_header"],
                  user_pk: id_list[i]["user_pk"],
                  body_signature: id_list[i]["body_signature"],
                  body: id_list[i]["body"],
                  body_users_pk: id_list[i]["body"]["users_pk"],
                  body_block_id: id_list[i]["body"]["block_id"],
                  timestamp: id_list[i]["timestamp"]
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
    getListOfTimesByElectionPeriod: function () {
      const _this = this
      this.axios({
        method: 'get',
        url: '/chain/times_list/get_by_election_period?start=' + _this.start_election_period + "&end=" + _this.end_election_period
      }).then((res) => {
        if (res.data["is_success"]) {
          const id_list = res.data["data"]
          if (id_list.length === 0) {
            ElNotification({
              title: 'Info',
              message: "没有更多区块了，去推荐一个吧",
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
                  election_period: id_list[i]["election_period"],
                  prev_block: id_list[i]["prev_block"],
                  prev_block_header: id_list[i]["prev_block_header"],
                  user_pk: id_list[i]["user_pk"],
                  body_signature: id_list[i]["body_signature"],
                  body: id_list[i]["body"],
                  body_users_pk: id_list[i]["body"]["users_pk"],
                  body_block_id: id_list[i]["body"]["block_id"],
                  timestamp: id_list[i]["timestamp"]
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
