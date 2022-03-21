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
    </div>
    <div v-show="is_detail" class="detail">
      <el-page-header content="区块详细信息" @back="this.is_detail=false"/>
      <div class="detail-main">
        <el-tag class="info-tag">Epoch:{{ epoch }}</el-tag>
        <el-tag class="info-tag" type="success">创建时间:{{ create_time }}</el-tag>
        <div class="content">
          <markdown :source="body"></markdown>
        </div>
        <el-collapse>
          <el-collapse-item title="区块头部信息" name="1">
            <el-form label-width="100px">
              <el-form-item label="前一个区块的头部哈希值">
                <el-input v-model="preBlockHeaderHash" :autosize="{minRows: 1}" readonly type="textarea">
                </el-input>
              </el-form-item>
              <el-form-item label="前一个区块的哈希值">
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
      is_detail: false,
      body: "",
      create_time: "",
      epoch: "",
      preBlockHash: "",
      preBlockHeaderHash: "",
      general_user_public_key: "",
      general_user_signature: "",
      main_node_public_key: "",
      main_node_signature: ""
    }
  },
  components: {
    ElTable,
    ElTableColumn,
    Markdown
  },
  created() {
    this.getMaxEpoch()
    this.getIdListOfBeings()
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
          break
        }
      }
    },
    getMaxEpoch: function () {
      const _this = this
      this.axios({
        method: 'get',
        url: '/chain/beings/max_epoch'
      }).then((res) => {
        if (res.data["is_success"]) {
          _this.start = parseInt(res.data["data"]) - 8
          _this.end = parseInt(res.data["data"])
        } else {
          ElNotification({
            title: '获取max epoch失败',
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
    getBlockOfBeings: function (db_id) {
      const _this = this
      this.axios({
        method: 'get',
        url: '/chain/beings/get?db_id=' + db_id
      }).then((res) => {
        if (res.data["is_success"]) {
          const block = res.data["data"]
          const block_dict = {
            "id": block["id"],
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
          _this.tableData.push(block_dict)
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
  margin: 0 10px;
}

.content {
  margin: 10px 0;
  padding: 0 10px;
  border-radius: 4px;
  border: 2px dashed var(--el-border-color-base);
}
</style>
