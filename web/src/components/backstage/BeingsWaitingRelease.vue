<template>
  <div>
    <el-table :data="tableData" style="width: 100%">
      <el-table-column type="expand">
        <template #default="props">
          <el-form label-position="top" label-width="100px">
            <el-form-item label="用户公钥">
              <el-input v-model="props.row.userPK" autosize readonly type="textarea"/>
            </el-form-item>
            <el-form-item label="内容预览">
              <Markdown class="markdown" :source="props.row.body"></Markdown>
            </el-form-item>
            <el-form-item label="签名">
              <el-input v-model="props.row.signature" autosize readonly type="textarea"/>
            </el-form-item>
          </el-form>
        </template>
      </el-table-column>
      <el-table-column label="ID" prop="id"/>
      <el-table-column label="申请时间" prop="applyTime"/>
      <el-table-column align="right">
        <template #default="scope">
          <el-button size="small" type="danger" @click="handlePass(scope.row.id,0)">撤销</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div>
      <el-button type="primary" style="margin-top:10px;width: 100%" v-on:click="getListOfBeings">获取更多</el-button>
    </div>
  </div>
</template>

<script>
import {ElNotification} from "element-plus";
import Markdown from "vue3-markdown-it";

export default {
  name: "BeingsAudit",
  components: {
    Markdown
  },
  mounted() {
    this.getListOfBeings()
  },
  data() {
    return {
      tableData: [],
      maxID: 0,
      token: this.getToken()
    }
  },
  methods: {
    getToken: function () {
      return localStorage.getItem('token');
    },
    getListOfBeings: function () {
      const loading = this.$loading({lock: true, text: '正在获取数据...', background: 'rgba(0, 0, 0, 0.7)'})
      const _this = this
      const reqData = JSON.stringify({
        offset: this.maxID,
        count: 8,
        token: this.token
      })
      this.axios({
        method: "post",
        url: "/backstage/waiting_beings_list/get",
        data: reqData,
        headers: {"content-type": "application/json"}
      }).then((res) => {
        if (res.data["is_success"]) {
          const data = res.data["data"]
          for (let i = 0; i < data.length; i++) {
            // 获取详细信息
            _this.getDetailOfBeings(data[i]["db_id"])
                .then((detail) => {
                  _this.tableData.push({
                    id: data[i]["db_id"],
                    applyTime: _this.$dayjs.unix(data[i]["create_time"]).format(),
                    userPK: detail["user_pk"],
                    body: Buffer.from(detail["body"], 'base64').toString('utf-8'),
                    signature: detail["signature"]
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
    getDetailOfBeings: function (db_id) {
      const _this = this
      return this.axios({
        method: "post",
        url: "/backstage/beings/get",
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
        url: "/backstage/beings/audit",
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
</style>
