<template>
  <div>
    <div v-show="!is_detail">
      <el-table :data="tableData" @row-click="openDetail" class="table-data">
        <el-table-column prop="epoch" label="上链期次" width="100" :row-style="getRowClass" :header-row-style="getRowClass" :header-cell-style="getRowClass"></el-table-column>
        <el-table-column label="内容摘要">
          <template #default="scope">
            <el-tooltip class="box-item" content="点击查看详情" placement="top">
              <div>{{ scope.row.body_digest }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
      <div>
        <el-button type="primary" class="button-get-more button-search-style" v-on:click="getIdListOfBeingsByOffset">
          获取更多
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
            <el-button type="primary" v-on:click="getIdListOfBeingsByEpoch" class="button-search button-search-style ">
              查找
            </el-button>
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
      table_data_row: "background-color: transparent;"
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
  updated() {
    let block_id = this.getRequest("block_id")
    if (block_id == null) {
      this.is_detail = false
    } else {
      this.is_detail = true
    }
    console.log(block_id)
  },
  methods: {
    getRowClass:function() {
      return "background:#3f5c6d2c;color:#000;";
    },
    getRequest: function (url_name) {
      let reg = new RegExp("(^|&)" + url_name + "=([^&]*)(&|$)", "i");
      let r = window.location.search.substr(1).match(reg);
      if (r != null) {
        return decodeURIComponent(r[2]);
      }
      return null;
    },
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
.table-data {
  width: 100%;
}

.table-data-row {
  background-color: transparent;
}
/*最外层透明*/
.el-table, .el-table__expanded-cell{
  background-color: transparent;
}
/* 表格内背景颜色 */
.el-table th,
.el-table tr,
.el-table td {
  background-color: transparent;
}

.search-epoch {
  margin: 10px 0;
}

.epoch-input {
  margin: 0 25px 0 0;
}

.button-get-more {
  margin: 15px 10%;
  width: 80%;
  text-align: center;
}

.button-search {
  margin: 5px 10%;
  width: 80%;
  text-align: center
}

.button-search-style {
  --color: #3992e6;
  position: relative;
  z-index: 1;
}

.button-search-style::before {
  content: '';
  position: absolute;
  width: 30px;
  height: 30px;
  background: transparent;
  top: -7px;
  left: -7px;
  z-index: -5;
  border-top: 3px solid var(--color);
  border-left: 3px solid var(--color);
  transition: 0.5s;
}

.button-search-style::after {
  content: '';
  position: absolute;
  width: 30px;
  height: 30px;
  background: transparent;
  bottom: -7px;
  right: -7px;
  z-index: -5;
  border-right: 3px solid var(--color);
  border-bottom: 3px solid var(--color);
  transition: 0.5s;
}

.button-search-style:hover::before {
  width: 100%;
  height: 100%;
}

.button-search-style:hover::after {
  width: 100%;
  height: 100%;
}

.button-search-style button {
  padding: 0.7em 2em;
  font-size: 16px;
  background: #222222;
  color: #fff;
  border: none;
  cursor: pointer;
  font-family: inherit;
}

</style>
