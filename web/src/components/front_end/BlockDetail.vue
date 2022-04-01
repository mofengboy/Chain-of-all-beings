<template>
  <div class="detail-main">
    <el-tag class="info-tag" color="#dedfe0">区块ID:{{ block_id }}</el-tag>
    <el-tag class="info-tag">上链期次:{{ epoch }}</el-tag>
    <el-tag class="info-tag" type="success">创建时间:{{ create_time }}</el-tag>
    <div class="content">
      <markdown :source="body"></markdown>
    </div>
    <el-collapse v-model="collapse_item">
      <el-collapse-item title="区块头部信息" name="1">
        <el-form label-width="100px">
          <el-form-item label="上一期次区块头部哈希列表">
            <el-input v-model="local_preBlockHeaderHash" :autosize="{minRows: 1}" readonly type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item label="上一期次区块哈希列表">
            <el-input v-model="local_preBlockHash" :autosize="{minRows: 1}" readonly type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item label="普通用户公钥">
            <el-input v-model="local_general_user_public_key" :autosize="{minRows: 1}" readonly type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item label="普通用户签名">
            <el-input v-model="local_general_user_signature" :autosize="{minRows: 1}" readonly type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item label="主节点用户公钥">
            <el-input v-model="local_main_node_public_key" :autosize="{minRows: 1}" readonly type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item label="主节点用户签名">
            <el-input v-model="local_main_node_signature" :autosize="{minRows: 1}" readonly type="textarea">
            </el-input>
          </el-form-item>
        </el-form>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script>
import Markdown from "vue3-markdown-it";
import {ElNotification} from "element-plus";

export default {
  name: "BlockDetail",
  components: {Markdown},
  created() {
    const loading = this.$loading({lock: true, text: '正在计算中...', background: 'rgba(0, 0, 0, 0.7)'})
    let block_id = this.$route.query.block_id
    this.getBlockOfBeings(block_id)
    loading.close()
  },
  data() {
    return {
      db_id: "",
      block_id: "",
      epoch: "",
      create_time: "",
      body: "",
      local_main_node_signature: "",
      local_main_node_public_key: "",
      local_general_user_signature: "",
      local_general_user_public_key: "",
      local_preBlockHash: "",
      local_preBlockHeaderHash: "",
      collapse_item: "1"
    }
  },
  methods: {
    getBlockOfBeings: function (block_id) {
      const _this = this
      this.axios({
        method: 'get',
        url: '/chain/beings/get?block_id=' + block_id
      }).then((res) => {
            if (res.data["is_success"]) {
              const block = res.data["data"]
              _this.db_id = block["id"]
              _this.block_id = block["block_id"]
              _this.epoch = block["epoch"]
              _this.local_preBlockHash = block["prev_block"]
              _this.local_preBlockHeaderHash = block["prev_block_header"]
              _this.local_general_user_public_key = block["user_pk"][0]
              _this.local_main_node_public_key = block["user_pk"][1]
              _this.local_general_user_signature = block["body_signature"][0]
              _this.local_main_node_signature = block["body_signature"][1]
              _this.body = Buffer.from(block["body"], "base64").toString("utf-8")
              _this.create_time = block["timestamp"]
            } else {
              ElNotification({
                title: '获取众生区块失败',
                message: res.data["data"],
                type: 'error',
              })
            }
          }
      )
    }
  }
}
</script>

<style scoped>
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
</style>
