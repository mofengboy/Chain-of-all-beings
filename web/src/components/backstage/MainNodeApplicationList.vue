<template>
  <div>
    <p class="application-title">来自本节点的申请书</p>
    <el-divider/>
    <div v-if="isMainNode">
      <el-table :data="tableData" style="width: 100%">
        <el-table-column type="expand">
          <template #default="props">
            <el-form label-position="top" label-width="100px">
              <el-form-item label="节点ID">
                <el-input v-model="props.row.nodeID" autosize readonly type="textarea"/>
              </el-form-item>
              <el-form-item label="节点用户公钥">
                <el-input v-model="props.row.userPK" autosize readonly type="textarea"/>
              </el-form-item>
              <el-form-item label="节点IP">
                <el-input v-model="props.row.nodeIP" autosize readonly type="textarea"/>
              </el-form-item>
              <el-form-item label="节点创建时间">
                <el-input v-model="props.row.nodeCreateTime" autosize readonly type="textarea"/>
              </el-form-item>
              <el-form-item label="节点签名">
                <el-input v-model="props.row.nodeSignature" autosize readonly type="textarea"/>
              </el-form-item>
              <el-form-item label="节点IP">
                <el-input v-model="props.row.nodeIP" autosize readonly type="textarea"/>
              </el-form-item>
              <el-form-item label="申请书预览">
                <Markdown class="markdown" :source="props.row.application"></Markdown>
              </el-form-item>
              <el-form-item label="申请书签名">
                <el-input v-model="props.row.applicationSignature" autosize readonly type="textarea"/>
              </el-form-item>
              <el-form-item label="备注">
                <Markdown class="markdown" :source="props.row.remarks"></Markdown>
              </el-form-item>
              <el-form-item label="创建时间">
                <el-input v-model="props.row.createTime" autosize readonly type="textarea"/>
              </el-form-item>
            </el-form>
          </template>
        </el-table-column>
        <el-table-column label="ID" prop="id"/>
        <el-table-column label="申请时间" prop="createTime"/>
        <el-table-column align="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="handlePass(scope.row.id,1)">通过</el-button>
            <el-button size="small" type="danger" @click="handlePass(scope.row.id,2)">拒绝</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div>
        <el-button type="primary" style="margin-top:10px;width: 100%" v-on:click="getListOfBeings">获取更多</el-button>
      </div>
    </div>
  </div>
</template>

<script>
import Markdown from "vue3-markdown-it";
import {ElNotification} from "element-plus";

export default {
  name: "MainNodeApplicationList",
  props: ['token'],
  components: {
    Markdown
  },
  mounted() {
    this.getListOfMainNodeApplication()
  },
  data() {
    return {
      tableData: [],
      maxID: 0,
      isMainNode: true
    }
  }, methods: {
    getListOfMainNodeApplication: function () {
      const loading = this.$loading({lock: true, text: '正在获取数据...', background: 'rgba(0, 0, 0, 0.7)'})
      const _this = this
      const reqData = JSON.stringify({
        offset: this.maxID,
        count: 8,
        token: this.token
      })
      this.axios({
        method: "post",
        url: "/backstage/main_node/new_apply_list/get",
        data: reqData,
        headers: {"content-type": "application/json"}
      }).then((res) => {
        if (res.data["is_success"]) {
          const data = res.data["data"]
          for (let i = 0; i < data.length; i++) {
            // 获取详细信息
            _this.getDetailOfMainNodeApplication(data[i]["db_id"])
                .then((detail) => {
                  _this.tableData.push({
                    id: data[i]["db_id"],
                    nodeID: detail["node_id"],
                    userPK: detail["user_pk"],
                    nodeIP: detail["node_ip"],
                    nodeCreateTime: _this.$dayjs.unix(detail["node_create_time"]).format(),
                    nodeSignature: detail["node_signature"],
                    application: Buffer.from(detail["application"], "base64").toString("utf-8"),
                    applicationSignature: detail["application_signature"],
                    remarks: Buffer.from(detail["remarks"], "base64").toString("utf-8"),
                    createTime: _this.$dayjs.unix(detail["create_time"]).format(),
                  })
                })
          }
          if (data.length > 0) {
            _this.maxID = data[data.length - 1]["db_id"]
          }
        } else {
          ElNotification({
            title: 'Error',
            message: res.data["data"],
            type: 'error',
          })
        }
        loading.close()
      })
    },
    getDetailOfMainNodeApplication: function (db_id) {
      const _this = this
      return this.axios({
        method: "post",
        url: "/backstage/main_node/new_apply/get",
        data: JSON.stringify({
          db_id: db_id,
          token: _this.token
        }),
        headers: {"content-type": "application/json"}
      }).then((res) => {
        if (res.data["is_success"]) {
          return res.data["data"]
        } else {
          ElNotification({
            title: 'Error',
            message: res.data["data"],
            type: 'error',
          })
        }
      })
    },
    handlePass: function (db_id, review) {
      const _this = this
      this.axios({
        method: "post",
        url: "/backstage/main_node/new_apply/review",
        data: JSON.stringify({
          db_id: db_id,
          token: _this.token,
          is_review: review
        }),
        headers: {"content-type": "application/json"}
      }).then((res) => {
        const data = res.data
        if (data["is_success"]) {
          ElNotification({
            title: 'Success',
            message: data["data"],
            type: 'success',
          })
          for (let i = 0; i < _this.tableData.length; i++) {
            if (_this.tableData[i].id === db_id) {
              _this.tableData.splice(i, 1)
              break
            }
          }
        } else {
          ElNotification({
            title: 'Error',
            message: data["data"],
            type: 'success',
          })
        }
      })
    },
  }
}
</script>

<style scoped>
.markdown {
  padding: 5px;
  width: 100%;
  border-radius: 4px;
  border: 2px dashed var(--el-border-color-base);
}

.application-title {
  margin: auto;
  text-align: center;
}
</style>
