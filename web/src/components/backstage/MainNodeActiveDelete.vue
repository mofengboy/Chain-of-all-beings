<template>
  <div>
    <div>
      <p class="application-title">本节点已经广播的申请书列表</p>
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
      </el-table>
      <div>
        <el-button type="primary" style="margin-top:10px;width: 100%" v-on:click="getListOfMainNodeApplication">获取更多
        </el-button>
      </div>
    </div>
    <el-divider/>
    <div>
      <p class="application-title">主动申请删除某主节点</p>
      <el-form style="margin-top: 10px" label-position="right" label-width="70px" size="default">
        <div>
          <el-form-item required label="节点ID">
            <el-input v-model="nodeId" :autosize="{minRows: 1}" type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item required label="申请书">
            <el-input v-model="application" :autosize="{minRows: 2}" type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item label="申请书预览">
            <Markdown class="markdown" :source="application"></Markdown>
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="remarks" :autosize="{minRows: 2}" type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item label="备注预览">
            <Markdown class="markdown" :source="remarks"></Markdown>
          </el-form-item>
        </div>
      </el-form>
      <div>
        <el-button type="primary" style="margin-top:10px;width: 100%" v-on:click="addActiveDelete">提交申请
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import Markdown from "vue3-markdown-it";
import {ElNotification} from "element-plus";

export default {
  name: "MainNodeApplicationList",
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
      isMainNode: true,
      token: this.getToken(),
      nodeId: "",
      application: "",
      remarks: ""
    }
  }, methods: {
    getToken: function () {
      return localStorage.getItem('token');
    },
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
        url: "/backstage/main_node/active_delete_list/get",
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
                    application: detail["application_content"],
                    remarks: detail["remarks"],
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
        url: "/backstage/main_node/active_delete/get",
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
    addActiveDelete: function () {
      const _this = this
      this.axios({
        method: "post",
        url: "/backstage/main_node/active_delete/add",
        data: JSON.stringify({
          token: _this.token,
          node_id: _this.nodeId,
          application_content: _this.application,
          remarks: _this.remarks
        }),
        headers: {"content-type": "application/json"}
      }).then((res) => {
        if (res.data["is_success"]) {
          ElNotification({
            title: 'Success',
            message: res.data["data"],
            type: 'success',
          })
        } else {
          ElNotification({
            title: 'Error',
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
