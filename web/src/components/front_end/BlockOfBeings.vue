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
      <el-page-header content="区块详细信息" @back="this.is_detail=false"/>
      <div class="detail-main">
        <el-tag class="info-tag" color="#dedfe0">区块ID:{{ block_id }}</el-tag>
        <el-tag class="info-tag">上链期次:{{ epoch }}</el-tag>
        <el-tag class="info-tag" type="success">创建时间:{{ create_time }}</el-tag>
        <div class="content">
          <markdown :source="body"></markdown>
        </div>
        <el-collapse>
          <el-collapse-item title="区块头部信息" name="1">
            <el-form label-width="100px">
              <el-form-item label="上一期次区块头部哈希列表">
                <el-input v-model="preBlockHeaderHash" :autosize="{minRows: 1}" readonly type="textarea">
                </el-input>
              </el-form-item>
              <el-form-item label="上一期次区块哈希列表">
                <el-input v-model="preBlockHash" :autosize="{minRows: 1}" readonly type="textarea">
                </el-input>
              </el-form-item>
              <el-form-item label="普通用户公钥">
                <el-input v-model="general_user_public_key" :autosize="{minRows: 1}" readonly type="textarea">
                </el-input>
              </el-form-item>
              <el-form-item label="普通用户签名">
                <el-input v-model="general_user_signature" :autosize="{minRows: 1}" readonly type="textarea">
                </el-input>
              </el-form-item>
              <el-form-item label="主节点用户公钥">
                <el-input v-model="main_node_public_key" :autosize="{minRows: 1}" readonly type="textarea">
                </el-input>
              </el-form-item>
              <el-form-item label="主节点用户签名">
                <el-input v-model="main_node_signature" :autosize="{minRows: 1}" readonly type="textarea">
                </el-input>
              </el-form-item>
            </el-form>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>
  </div>
</template>

<script>
import {ElNotification, ElTable, ElTableColumn} from "element-plus";
import Markdown from "vue3-markdown-it";


export default {
  name: "BlockOfBeings",
  data() {
    return {
      tableData: [],
      start: 0,
      end: 8,
      more_offset: 0,
      is_detail: false,
      body: "",
      create_time: "",
      epoch: "",
      block_id: "",
      preBlockHash: "",
      preBlockHeaderHash: "",
      general_user_public_key: "",
      general_user_signature: "",
      main_node_public_key: "",
      main_node_signature: "",
      start_epoch: 0,
      end_epoch: 8,
    }
  },
  components: {
    ElTable,
    ElTableColumn,
    Markdown
  },
  created() {
    this.getIdListOfBeingsByOffset()
  },
  methods: {
    openDetail: function (event) {
      for (let i = 0; i < this.tableData.length; i++) {
        if (event.id === this.tableData[i]["id"]) {
          this.is_detail = true
          this.body = this.tableData[i]["body"]
          this.epoch = this.tableData[i]["epoch"]
          this.create_time = this.$dayjs.unix((this.tableData[i]["timestamp"].toString()).substring(0, 10)).format()
          this.preBlockHeaderHash = this.tableData[i]["prev_block_header"]
          this.preBlockHash = this.tableData[i]["prev_block"]
          this.general_user_public_key = this.tableData[i]["user_pk"]
          this.general_user_signature = this.tableData[i]["user_signature"]
          this.main_node_public_key = this.tableData[i]["main_node_user_pk"]
          this.main_node_signature = this.tableData[i]["main_node_signature"]
          this.block_id = this.tableData[i]["block_id"]
          break
        }
      }
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
    getMore: function () {
      if (this.start >= 0) {
        this.start -= 8
        this.end -= 8
        this.getIdListOfBeings()
      } else {
        ElNotification({
          title: '没有更多了',
          message: "去发布一个吧",
          type: 'error',
        })
      }
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
          }
          for (let i = 0; i < id_list.length; i++) {
            _this.getBlockOfBeings(id_list[i])
          }
          _this.more_offset += id_list.length
        } else {
          ElNotification({
            title: '获取区块列表ID失败',
            message: res.data["data"],
            type: 'error',
          })
        }
      })
    },
    getIdListOfBeings: function () {
      const _this = this
      this.axios({
        method: 'get',
        url: '/chain/beings_list/get?start=' + _this.start + "&end=" + _this.end
      }).then((res) => {
        if (res.data["is_success"]) {
          const id_list = res.data["data"]
          for (let i = 0; i < id_list.length; i++) {
            _this.getBlockOfBeings(id_list[i])
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
              message: 'Epoch:' + _this.start_epoch + "-" + _this.end_epoch + "中没有区块生成",
              type: 'info',
            })
          }
          for (let i = 0; i < id_list.length; i++) {
            _this.getBlockOfBeings(id_list[i])
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
    getBlockOfBeings: function (db_id) {
      const _this = this
      this.axios({
        method: 'get',
        url: '/chain/beings/get?db_id=' + db_id
      }).then((res) => {
        if (res.data["is_success"]) {
          const block = res.data["data"]
          let is_exist = false
          for (let i = 0; i < _this.tableData.length; i++) {
            if (_this.tableData[i]["id"] === block["id"]) {
              is_exist = true
            }
          }
          const block_dict = {
            "id": block["id"],
            "block_id": block["block_id"],
            "epoch": block["epoch"],
            "prev_block": block["prev_block"],
            "prev_block_header": block["prev_block_header"],
            "user_pk": block["user_pk"][0],
            "main_node_user_pk": block["user_pk"][1],
            "user_signature": block["body_signature"][0],
            "main_node_signature": block["body_signature"][1],
            "body": Buffer.from(block["body"], "base64").toString("utf-8"),
            "body_digest": (Buffer.from(block["body"], "base64").toString("utf-8")).substring(0, 32),
            "timestamp": block["timestamp"]
          }
          if (!is_exist) {
            _this.tableData.push(block_dict)
          }
        } else {
          ElNotification({
            title: '获取众生区块失败',
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
.detail {

}

.detail-main {
  margin-top: 10px;
}

.info-tag {
  margin: 0 15px 5px 0;
}

.content {
  margin: 10px 0;
  padding: 0 10px;
  border-radius: 4px;
  border: 2px dashed var(--el-border-color-base);
}

.search-epoch {
  margin: 10px 0;
}

.epoch-input {
  margin: 0 25px 0 0;
}
</style>
