<template>
  <div>
    <p class="application-title">来自其他节点的申请书(申请删除某主节点)</p>
    <el-divider/>
    <el-table :data="tableData" style="width: 100%">
      <el-table-column type="expand">
        <template #default="props">
          <el-form label-position="top" label-width="100px">
            <el-form-item label="节点ID">
              <el-input v-model="props.row.nodeID" autosize readonly type="textarea"/>
            </el-form-item>
            <el-form-item label="申请书预览">
              <Markdown class="markdown" :source="props.row.application"></Markdown>
            </el-form-item>
            <el-form-item label="申请时间">
              <el-input v-model="props.row.applicationTime" autosize readonly type="textarea"/>
            </el-form-item>
            <el-form-item label="申请主节点公钥">
              <el-input v-model="props.row.mainNodeUserPk" autosize readonly type="textarea"/>
            </el-form-item>
            <el-form-item label="申请主节点签名">
              <el-input v-model="props.row.mainNodeSignature" autosize readonly type="textarea"/>
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
          <el-button size="small" type="primary" @click="handlePass(scope.row.id,1)">同意</el-button>
          <el-button size="small" type="danger" @click="handlePass(scope.row.id,2)">拒绝</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div>
      <el-button type="primary" style="margin-top:10px;width: 100%" v-on:click="getListOfOtherNodeApplication">获取更多
      </el-button>
    </div>
  </div>
</template>

<script>
import Markdown from "vue3-markdown-it";
import {ElNotification} from "element-plus";

export default {
  name: "OtherNodeActiveDeleteList",
  components: {
    Markdown
  },
  mounted() {
    this.getListOfOtherNodeApplication()
  },
  data() {
    return {
      tableData: [],
      maxID: 0,
      isMainNode: true,
      token: this.getToken()
    }
  },
  methods: {
    getToken: function () {
      return localStorage.getItem('token');
    },
    getListOfOtherNodeApplication: function () {
      const loading = this.$loading({lock: true, text: '正在获取数据...', background: 'rgba(0, 0, 0, 0.7)'})
      const _this = this
      const reqData = JSON.stringify({
        offset: this.maxID,
        count: 8,
        token: this.token
      })
      this.axios({
        method: "post",
        url: "/backstage/main_node/other_active_delete_list/get",
        data: reqData,
        headers: {"content-type": "application/json"}
      }).then((res) => {
        if (res.data["is_success"]) {
          const data = res.data["data"]
          for (let i = 0; i < data.length; i++) {
            // 获取详细信息
            _this.getDetailOfOtherNodeApplication(data[i]["id"])
                .then((detail) => {
                  _this.tableData.push({
                    id: data[i]["id"],
                    nodeID: detail["node_id"],
                    application: detail["application_content"],
                    applicationTime: _this.$dayjs.unix(parseInt(detail["application_time"].toString().substring(0, 10))).format(),
                    mainNodeSignature: detail["main_node_signature"],
                    mainNodeUserPk: detail["main_node_user_pk"],
                    createTime: _this.$dayjs.unix(parseInt(detail["create_time"].toString().substring(0, 10))).format(),
                  })
                })
          }
          if (data.length > 0) {
            _this.maxID = data[data.length - 1]["id"]
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
    getDetailOfOtherNodeApplication: function (db_id) {
      const _this = this
      return this.axios({
        method: "post",
        url: "/backstage/main_node/other_active_delete/get",
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
        url: "/backstage/main_node/other_active_delete/review",
        data: JSON.stringify({
          db_id: db_id,
          token: _this.token,
          review: review
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
