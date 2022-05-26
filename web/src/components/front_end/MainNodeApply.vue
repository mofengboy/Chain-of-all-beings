<template>
  <div>
    <el-form :rules="rules" label-position="right" label-width="70px" size="default">
      <div>
        <el-form-item label="节点ID">
          <el-input v-model="nodeID" :autosize="{minRows: 1}" type="textarea">
          </el-input>
        </el-form-item>
        <el-form-item label="用户公钥">
          <el-input v-model="publicKey" :autosize="{minRows: 1}" type="textarea">
          </el-input>
        </el-form-item>
        <el-form-item label="节点IP">
          <el-input v-model="nodeIP" :autosize="{minRows: 1}" type="textarea">
          </el-input>
        </el-form-item>
        <el-form-item label="平台服务地址">
          <el-input v-model="serverUrl" :autosize="{minRows: 1}" type="textarea">
          </el-input>
        </el-form-item>
        <el-form-item label="节点创建时间">
          <el-input v-model="nodeCreateTime" :autosize="{minRows: 1}" type="textarea">
          </el-input>
        </el-form-item>
        <el-form-item label="节点签名">
          <el-input v-model="nodeSignatureRaw" :autosize="{minRows: 1}" type="textarea">
          </el-input>
          <div>
            <el-link type="primary" v-on:click="publicKeyDialog = true">如何得到以上节点信息？</el-link>
          </div>
        </el-form-item>
      </div>
      <div>
        <el-form-item label="申请书">
          <el-input :autosize="{ minRows: 2 }" v-model="application" type="textarea">
          </el-input>
          <el-collapse style="width: 100%;margin-top: 10px" v-model="collapse_item">
            <el-collapse-item name="1">
              <div>
                <Markdown class="markdown" :source="application"></Markdown>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-form-item>
      </div>
      <el-form-item label="申请书 签名">
        <el-input :autosize="{ minRows: 2 }" type="textarea" v-model="applicationSignatureRaw">
        </el-input>
        <div>
          <el-link type="primary" v-on:click="signatureDialog = true">如何计算签名？</el-link>
        </div>
      </el-form-item>
      <div>
        <el-form-item label="备注">
          <el-input :autosize="{ minRows: 2 }" v-model="remarks" type="textarea">
          </el-input>
          <el-collapse style="width: 100%;margin-top: 10px" v-model="collapse_item">
            <el-collapse-item name="1">
              <div>
                <Markdown class="markdown" :source="remarks"></Markdown>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-form-item>
      </div>
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
      <el-form-item>
        <el-button type="primary" v-on:click="sendApplicationForm">提交到主节点</el-button>
        <el-button
            v-on:click="privateKey='';publicKey='';applicationSignature='';applicationSignatureRaw='';application='# markdown文件格式'">
          重置
        </el-button>
      </el-form-item>
    </el-form>
  </div>
  <div>
    <!--签名弹框-->
    <el-dialog append-to-body v-model="signatureDialog" title="计算签名" width="80%">
      <div>
        <el-form>
          <p>若内容发生改变，则必须重新计算签名。</p>
          <p class="sk-alert">注意：此处不会存储您的私钥，计算任务全部都在本地进行。</p>
          <div>
            <el-form-item label="用户私钥：" label-width="90px">
              <el-input v-model="privateKey" autosize type="textarea"/>
            </el-form-item>
          </div>
          <div>
            <el-form-item label="签名：" label-width="90px">
              <el-input v-model="applicationSignatureRaw" autosize type="textarea"/>
            </el-form-item>
          </div>
          <div class="button-sign">
            <el-button type="primary" v-on:click="sign">生成签名</el-button>
          </div>
        </el-form>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import Markdown from 'vue3-markdown-it';
import 'highlight.js/styles/monokai.css';
import {ElNotification} from "element-plus";

export default {
  name: "ReleaseBlock",
  components: {
    Markdown
  },
  created() {
    this.getCAPTCHA()
  },
  data() {
    return {
      path: this.$host_url,
      fullscreenLoading: false,
      publicKeyDialog: false,
      signatureDialog: false,
      privateKeyDialog: false,
      nodeID: "",
      nodeIP: "",
      serverUrl: "",
      nodeCreateTime: "",
      //后端通过这个格式的签名进行验证
      nodeSignatureRaw: "",
      privateKey: "",
      publicKey: "",
      application: '# 使用Markdown格式渲染',
      applicationSignature: "",
      //后端通过这个格式的签名进行验证
      applicationSignatureRaw: "",
      computeLoading: false,
      captchaSrc: "",
      captchaInput: "",
      collapse_item: "1",
      remarks: "### 添加备注信息是为了更好的进行沟通交流。备注信息不会出现在申请书内",
      rules: {
        name: [
          {
            required: true,
            message: 'Please input Activity name',
            trigger: 'blur',
          }
        ],
      }
    }
  },
  methods: {
    //签名
    sign: function () {
      const loading = this.$loading({lock: true, text: '正在计算中...', background: 'rgba(0, 0, 0, 0.7)'})
      const _this = this
      this.$worker.run((path, prvHex, message) => {
        this.importScripts(path + "/static/js/jsrsasign/jsrsasign-all-min.js")
        const sig = new this.KJUR.crypto.Signature({'alg': 'SHA256withECDSA'});
        sig.init({d: prvHex, curve: 'NIST P-384'});
        sig.updateString(message);
        const sigValueHex = sig.sign()
        return [sigValueHex, this.KJUR.crypto.ECDSA.asn1SigToConcatSig(sigValueHex)]
      }, [this.path, this.privateKey, this.getBase64Application()]).then((res) => {
        _this.applicationSignature = res[0]
        //后端通过这个格式的签名进行验证
        _this.applicationSignatureRaw = res[1]
        loading.close()
      })
    },
    //  验证申请书签名
    verifyApplicationSign: function () {
      const loading = this.$loading({lock: true, text: '正在计算中...', background: 'rgba(0, 0, 0, 0.7)'})
      return this.$worker.run((path, pubHex, message, sigValueHex) => {
        this.importScripts(path + "/static/js/jsrsasign/jsrsasign-all-min.js")
        const sig = new this.KJUR.crypto.Signature({"alg": 'SHA256withECDSA', "prov": "cryptojs/jsrsa"});
        // python端传输的公钥首部应该添加"04",别问为什么，我也不知道，试出来的。
        // 总之，这样做就对了。
        const ans1PubHex = "04" + pubHex
        sig.init({xy: ans1PubHex, curve: 'NIST P-384'});
        sig.updateString(message);
        const result = sig.verify(sigValueHex);
        return result
      }, [this.path, this.publicKey, this.getBase64Application(), this.applicationSignature])
          .then((res) => {
            loading.close()
            return res
          })
    },
    //  验证主节点签名
    verifyNodeSign: function () {
      const loading = this.$loading({lock: true, text: '正在计算中...', background: 'rgba(0, 0, 0, 0.7)'})
      return this.$worker.run((path, pubHex, message, sigValueHex) => {
        this.importScripts(path + "/static/js/jsrsasign/jsrsasign-all-min.js")
        // python端传输的公钥首部应该添加"04",别问为什么，我也不知道，试出来的。
        // 总之，这样做就对了。
        const ans1SigValueHex = this.KJUR.crypto.ECDSA.concatSigToASN1Sig(sigValueHex)
        const ans1PubHex = "04" + pubHex
        const sig = new this.KJUR.crypto.Signature({"alg": 'SHA256withECDSA', "prov": "cryptojs/jsrsa"});
        sig.init({xy: ans1PubHex, curve: 'NIST P-384'});
        sig.updateString(message);
        const result = sig.verify(ans1SigValueHex);
        return result
      }, [this.path, this.publicKey, this.getNodeInfo(), this.nodeSignatureRaw])
          .then((res) => {
            loading.close()
            console.log(res)
            return res
          })
    },
    getNodeInfo: function () {
      const node_info = "{'node_id': '" + this.nodeID + "', 'user_pk': '" + this.publicKey + "', 'node_ip': '" + this.nodeIP + "', 'server_url': '" + this.serverUrl + "', 'create_time': " + parseInt(this.nodeCreateTime) + "}"
      return node_info
    },
    getBase64Application: function () {
      return Buffer.from(this.application, 'utf-8').toString('base64')
    },
    getBase64Remarks: function () {
      return Buffer.from(this.remarks, 'utf-8').toString('base64')
    },
    getCAPTCHA: function () {
      this.axios.post("/captcha/get")
          .then((res) => {
            this.captchaSrc = res.data.data
          })
    },
    sendApplicationForm: function () {
      const _this = this
      //验证节点签名
      _this.verifyNodeSign().then((response) => {
        if (response === true) {
          //验证申请书签名
          _this.verifyApplicationSign().then((res) => {
            if (res === true) {
              // 签名验证成功
              _this.axios({
                method: 'post',
                url: '/main_node/new_apply/save',
                data: JSON.stringify({
                  "captcha": {
                    "uuid": _this.captchaSrc["uuid"],
                    "word": _this.captchaInput
                  },
                  "node_id": _this.nodeID,
                  "user_pk": _this.publicKey,
                  "node_ip": _this.nodeIP,
                  "server_url": _this.serverUrl,
                  "node_create_time": _this.nodeCreateTime,
                  "node_signature": _this.nodeSignatureRaw,
                  "application": _this.getBase64Application(),
                  "application_signature": _this.applicationSignatureRaw,
                  "remarks": _this.getBase64Remarks()
                }),
                headers: {"content-type": "	application/json"}
              }).then((res) => {
                if (res.data["is_success"] === true) {
                  ElNotification({
                    title: 'Success',
                    message: '提交成功',
                    type: 'success',
                  })
                } else {
                  ElNotification({
                    title: '提交失败',
                    message: res.data["data"],
                    type: 'error',
                  })
                  _this.getCAPTCHA()
                }
              })
            } else {
              // 签名验证失败
              ElNotification({
                title: '申请书签名验证失败',
                message: '请重新计算签名！',
                type: 'error',
              })
              _this.getCAPTCHA()
            }
          })
        } else {
          ElNotification({
            title: '节点签名验证失败',
            message: '请重新计算签名！',
            type: 'error',
          })
          _this.getCAPTCHA()
        }
      })
    }
  }

}
</script>

<style scoped>
.button-sk-to-pk {
  margin: 10px auto;
  text-align: center;
}

.sk-alert {
  color: #c45656;
}

.button-sk-to-pk {
  margin: 20px auto;
  text-align: center;
}

.button-sign {
  margin: 20px auto;
  text-align: center;
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

.markdown {
  padding: 5px;
  border-radius: 4px;
  border: 2px dashed var(--el-border-color-base);
}
</style>
