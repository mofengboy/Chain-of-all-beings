<template>
  <div>
    <div>
      <p style="text-align: center">普通用户票数查询（仅显示在本主节点拥有的票数）</p>
      <el-input v-model="simpleUserPk" class="simple-user-input" type="textarea" :autosize="{ minRows: 1}"
                placeholder="用户公钥"></el-input>
      <el-button class="simple-user-button" type="primary" v-on:click="getSimpleUserVote">查询</el-button>
      <div class="simple-user">
        <div class="simple-user-show">已使用票数：{{ simpleUserUsedVote }}</div>
        <div class="simple-user-show">总票数：{{ simpleUserVote }}</div>
      </div>
    </div>
    <el-divider/>
    <div>
      <p style="text-align: center">发起投票</p>
      <p class="sk-alert">注意：在投票之前一定要确认目标主节点推荐了该区块并且确保输入正确，避免票被浪费。</p>
      <el-form label-position="left" label-width="100px" size="default">
        <div>
          <el-form-item label="目标主节点ID">
            <el-input v-model="toNodeId" :autosize="{minRows: 1}" type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item label="区块ID">
            <el-input v-model="blockId" :autosize="{minRows: 1}" type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item label="用户公钥">
            <el-input v-model="simpleUserPk" :autosize="{minRows: 1}" type="textarea">
            </el-input>
          </el-form-item>
          <el-form-item label="签名">
            <el-input v-model="voteSignature" :autosize="{minRows: 1}" type="textarea">
            </el-input>
            <div>
              <el-link type="primary" v-on:click="signatureDialog = true">如何计算签名？</el-link>
            </div>
          </el-form-item>
          <!--签名弹框-->
          <el-dialog v-model="signatureDialog" title="计算签名" width="80%">
            <div>
              <el-form>
                <p>若内容发生改变，则必须重新计算签名。</p>
                <div>
                  <el-form-item label="用户私钥：" label-width="90px">
                    <el-input v-model="simpleUserSk" autosize type="textarea"/>
                  </el-form-item>
                </div>
                <div>
                  <el-form-item label="签名：" label-width="90px">
                    <el-input v-model="voteSignature" autosize type="textarea"/>
                  </el-form-item>
                </div>
                <div class="button-sign">
                  <el-button type="primary" style="width: 100%" v-on:click="sign">生成签名</el-button>
                </div>
              </el-form>
            </div>
          </el-dialog>
          <el-form-item label="投票数量">
            <el-input-number v-model="toVote" :precision="1" :step="0.1" :min="1.0"/>
          </el-form-item>
          <el-form-item label="验证码">
            <div>
              <div class="CAPTCHA" v-on:click="getCAPTCHA">
                <el-image :src="'data:image/png;base64,'+this.captchaSrc['pic_base64']"></el-image>
              </div>
              <div class="CAPTCHA_input">
                <el-input v-model="captchaInput"></el-input>
              </div>
            </div>
            <p class="CAPTCHA_tip">点击图片刷新验证码，验证码有效期为五分钟</p>
          </el-form-item>
          <el-button style="width: 100%" type="primary" v-on:click="initVote">发起投票</el-button>
        </div>
      </el-form>
    </div>
    <el-divider/>
    <div>
      <p style="text-align: center">所有主节点的拥有的票数信息</p>
      <el-table :data="tableData" stripe style="width: 100%">
        <el-table-column prop="main_node_id" label="主节点ID"/>
        <el-table-column prop="used_vote" label="已使用票数" width="100"/>
        <el-table-column prop="total_vote" label="总票数" width="100"/>
      </el-table>
    </div>
  </div>
</template>

<script>
import {ElNotification} from "element-plus";

export default {
  name: "VotingInformation",
  data() {
    return {
      path: this.$host_url,
      tableData: [],
      simpleUserPk: "",
      simpleUserVote: 0,
      simpleUserUsedVote: 0,
      toNodeId: "",
      blockId: "",
      toVote: 1.0,
      asn1Signature: "",
      voteSignature: "",
      simpleUserSk: "",
      captchaSrc: "",
      captchaInput: "",
      signatureDialog: false,
      epoch: 0,
      electionPeriodValue: 1
    }
  },
  created() {
    this.getVoteList()
    this.getCAPTCHA()
  },
  methods: {
    getSimpleUserVote: function () {
      const _this = this
      this.axios({
        method: 'post',
        url: '/backstage/simple_user_vote/get',
        data: JSON.stringify({
          "user_pk": _this.simpleUserPk
        }),
        headers: {"content-type": "	application/json"}
      }).then((res) => {
        if (res.data["is_success"] === true) {
          const data = res.data["data"]
          _this.simpleUserVote = data["total_vote"]
          _this.simpleUserUsedVote = data["used_vote"]
        } else {
          ElNotification({
            title: '获取失败',
            message: res.data["data"],
            type: 'error',
          })
        }
      })
    },
    getVoteList: function () {
      const _this = this
      this.axios({
        method: 'get',
        url: '/vote_list/main_node/get'
      }).then((res) => {
        if (res.data["is_success"]) {
          const data_list = res.data["data"]
          for (let i = 0; i < data_list.length; i++) {
            let main_node_user_pk = data_list[i]["node_user_pk"]
            _this.getVote(main_node_user_pk)
          }
        } else {
          ElNotification({
            title: '获取失败',
            message: res.data["data"],
            type: 'error',
          })
        }
      })
    },
    getVote: function (main_node_user_pk) {
      const _this = this
      this.axios({
        method: 'get',
        url: '/vote/main_node/get?user_pk=' + main_node_user_pk
      }).then((res) => {
        if (res.data["is_success"]) {
          const vote_info = res.data["data"]
          _this.tableData.push(vote_info)
        } else {
          ElNotification({
            title: '获取失败',
            message: res.data["data"],
            type: 'error',
          })
        }
      })
    },
    getCAPTCHA: function () {
      this.axios.post("/captcha/get")
          .then((res) => {
            this.captchaSrc = res.data.data
          })
    },
    initVote: function () {
      const _this = this
      this.verifySign().then((res) => {
        if (res) {
          _this.axios({
            method: 'post',
            url: '/vote/add',
            data: JSON.stringify({
              "captcha": {
                "uuid": _this.captchaSrc["uuid"],
                "word": _this.captchaInput
              },
              "to_node_id": _this.toNodeId,
              "block_id": _this.blockId,
              "to_vote": _this.toVote,
              "simple_user_pk": _this.simpleUserPk,
              "signature": _this.voteSignature
            }),
            headers: {"content-type": "	application/json"}
          }).then((res) => {
            if (res.data["is_success"]) {
              ElNotification({
                title: '投票成功',
                message: res.data["data"],
                type: 'success',
              })
            } else {
              ElNotification({
                title: '投票失败',
                message: res.data["data"],
                type: 'error',
              })
              _this.getCAPTCHA()
            }
          })
        } else {
          // 签名验证失败
          ElNotification({
            title: '投票信息签名验证失败',
            message: '请重新计算签名！',
            type: 'error',
          })
        }
      })
    },
    getPeriod: function () {
      const _this = this
      return this.axios({
        method: 'get',
        url: '/period/get'
      }).then((res) => {
        if (res.data["is_success"]) {
          const data = res.data["data"]
          _this.epoch = data["epoch"]
          _this.electionPeriodValue = data["election_period_value"]
        }
      })
    },
    getVoteInfo: function () {
      return this.getPeriod().then(() => {
        return "{'election_period': " + Math.floor(this.epoch / this.electionPeriodValue) + ", 'to_node_id': " + this.toNodeId + ", 'block_id': " + this.blockId + ", 'vote': " + this.toVote + ", 'simple_user_pk': " + this.simpleUserPk + "}"
      })
    },
    //签名
    sign: function () {
      const _this = this
      this.getVoteInfo().then((vote_info) => {
        console.log(vote_info)
        const loading = this.$loading({lock: true, text: '正在计算中...', background: 'rgba(0, 0, 0, 0.7)'})
        _this.$worker.run((path, prvHex, message) => {
          this.importScripts(path + "/static/js/jsrsasign/jsrsasign-all-min.js")
          const sig = new this.KJUR.crypto.Signature({'alg': 'SHA256withECDSA'});
          sig.init({d: prvHex, curve: 'NIST P-384'});
          sig.updateString(message);
          const sigValueHex = sig.sign()
          return [sigValueHex, this.KJUR.crypto.ECDSA.asn1SigToConcatSig(sigValueHex)]
        }, [_this.path, _this.simpleUserSk, vote_info]).then((res) => {
          _this.asn1Signature = res[0]
          //后端通过这个格式的签名进行验证
          _this.voteSignature = res[1]
          loading.close()
        })
      })
    },
    //  验证签名
    verifySign: function () {
      const _this = this
      return this.getVoteInfo().then((vote_info) => {
        const loading = this.$loading({lock: true, text: '正在计算中...', background: 'rgba(0, 0, 0, 0.7)'})
        return _this.$worker.run((path, pubHex, message, sigValueHex) => {
          this.importScripts(path + "/static/js/jsrsasign/jsrsasign-all-min.js")
          const sig = new this.KJUR.crypto.Signature({"alg": 'SHA256withECDSA', "prov": "cryptojs/jsrsa"});
          sig.init({xy: pubHex, curve: 'NIST P-384'});
          sig.updateString(message);
          const result = sig.verify(sigValueHex);
          return result
        }, [_this.path, "04" + _this.simpleUserPk, vote_info, _this.asn1Signature])
            .then((res) => {
              loading.close()
              return res
            })
      })
    },
  }
}
</script>

<style scoped>
.simple-user-input {
  width: 70%;
  margin-right: 5%;
}

.simple-user {
  margin-top: 10px;;
}

.simple-user-show {
  display: inline-block;
  width: 20%;
  margin-right: 5%;
  text-align: left;
}

.simple-user-button {
  width: 25%;
}

.sk-alert {
  color: #c45656;
}

.CAPTCHA {
  float: left;
  text-align: center;
  border-right: solid 1px var(--el-border-color-base);
  display: inline-block;
  width: 150px;
  box-sizing: border-box;
  vertical-align: top;
}

.CAPTCHA_input {
  float: left;
  margin-left: 10px;
  margin-top: 4px;
  width: 150px;
}

.CAPTCHA_tip {
  padding: 0;
  margin: 0;
  width: 100%;
}

.CAPTCHA .el-image {
  padding: 0 5px;
  width: 100%;
  height: 40px;
}

</style>
