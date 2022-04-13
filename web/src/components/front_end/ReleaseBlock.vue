<template>
  <div>
    <el-form :rules="rules" label-position="right" label-width="70px"
             size="default">
      <el-form-item label="用户公钥">
        <el-input v-model="publicKeyRaw" :autosize="{minRows: 1}" type="textarea">
        </el-input>
        <div>
          <el-link type="primary" v-on:click="publicKeyDialog = true">没有公钥？</el-link>
        </div>
      </el-form-item>
      <div>
        <el-form-item label="内容">
          <el-input :autosize="{ minRows: 2 }" v-model="body" type="textarea">
          </el-input>
          <el-collapse style="width: 100%" v-model="collapse_item">
            <el-collapse-item title="预览" name="1">
              <div>
                <Markdown class="markdown" :source="body"></Markdown>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-form-item>
      </div>
      <el-form-item label="签名">
        <el-input :autosize="{ minRows: 1 }" type="textarea" v-model="signatureRaw">
        </el-input>
        <div>
          <el-link type="primary" v-on:click="signatureDialog = true">如何计算签名？</el-link>
        </div>
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
      <el-form-item>
        <el-button type="primary" v-on:click="sendBlockOfBeings">提交到主节点</el-button>
        <el-button v-on:click="privateKey='';publicKey='';signature='';signatureRaw='';body='# markdown文件格式'">重置
        </el-button>
      </el-form-item>
    </el-form>
  </div>
  <div>
    <!--公钥生成弹框-->
    <el-dialog v-model="publicKeyDialog" title="在线生成" width="80%">
      <div>
        <el-form>
          <p>此处不会存储您的私钥，计算任务全部都在本地进行。</p>
          <p class="sk-alert">注意：请务必谨慎保存您的私钥和公钥，私钥一旦丢失或被盗，将无法找回！</p>
          <el-form-item label="用户私钥：">
            <el-input v-model="privateKey" autosize type="textarea" autofocus>
            </el-input>
          </el-form-item>
          <el-form-item label="用户公钥：">
            <el-input v-model="publicKeyRaw" autosize type="textarea" readonly>
            </el-input>
          </el-form-item>
        </el-form>
        <div class="button-sk-to-pk">
          <el-button type="primary" v-on:click="generatePK">在线生成密钥对</el-button>
        </div>
      </div>
    </el-dialog>
    <!--签名弹框-->
    <el-dialog v-model="signatureDialog" title="计算签名" width="80%">
      <div>
        <el-form>
          <p>若内容发生改变，则必须重新计算签名。</p>
          <div>
            <el-form-item label="用户私钥：" label-width="90px">
              <el-input v-model="privateKey" autosize type="textarea"/>
            </el-form-item>
          </div>
          <div>
            <el-form-item label="签名：" label-width="90px">
              <el-input v-model="signatureRaw" autosize type="textarea"/>
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
      privateKey: "",
      publicKeyRaw: "",
      body: '# 使用Markdown格式渲染',
      signature: "",
      signatureRaw: "",
      computeLoading: false,
      captchaSrc: "",
      captchaInput: "",
      collapse_item: "1",
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
  computed: {
    publicKey: {
      get() {
        return "04" + this.publicKeyRaw
      }
    }
  },
  methods: {
    //生成密钥对
    generatePK: function () {
      const loading = this.$loading({lock: true, text: '正在计算中...', background: 'rgba(0, 0, 0, 0.7)'})
      const _this = this
      this.$worker.run((path) => {
        this.importScripts(path + "/static/js/jsrsasign/jsrsasign-all-min.js")
        const ec = new this.KJUR.crypto.ECDSA({'curve': 'NIST P-384'});
        // EC公钥的十六进制字符串
        const keyPairHex = ec.generateKeyPairHex()
        const pubHex = keyPairHex.ecpubhex
        const prvHex = keyPairHex.ecprvhex
        // const pubHexRaw = keyPairHex
        return [pubHex, prvHex]
      }, [this.path]).then((res) => {
        // _this.publicKey = res[0]
        _this.publicKeyRaw = res[0].substring(2)
        _this.privateKey = res[1]
        loading.close()
      })
    },
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
      }, [this.path, this.privateKey, this.getBase64Body()]).then((res) => {
        _this.signature = res[0]
        //后端通过这个格式的签名进行验证
        _this.signatureRaw = res[1]
        loading.close()
      })
    },
    //  验证签名
    verifySign: function () {
      const loading = this.$loading({lock: true, text: '正在计算中...', background: 'rgba(0, 0, 0, 0.7)'})
      // const _this = this
      return this.$worker.run((path, pubHex, message, sigValueHex) => {
        this.importScripts(path + "/static/js/jsrsasign/jsrsasign-all-min.js")
        const sig = new this.KJUR.crypto.Signature({"alg": 'SHA256withECDSA', "prov": "cryptojs/jsrsa"});
        sig.init({xy: pubHex, curve: 'NIST P-384'});
        sig.updateString(message);
        const result = sig.verify(sigValueHex);
        return result
      }, [this.path, this.publicKey, this.getBase64Body(), this.signature])
          .then((res) => {
            loading.close()
            return res
          })
    },
    getBase64Body: function () {
      return Buffer.from(this.body, 'utf-8').toString('base64')
    },
    getCAPTCHA: function () {
      this.axios.post("/captcha/get")
          .then((res) => {
            this.captchaSrc = res.data.data
          })
    },
    sendBlockOfBeings: function () {
      const _this = this
      this.verifySign().then((res) => {
        if (res === true) {
          // 签名验证成功
          _this.axios({
            method: 'post',
            url: '/block/beings/save',
            data: JSON.stringify({
              "user_pk": _this.publicKeyRaw,
              "body": _this.getBase64Body(),
              "signature": _this.signatureRaw,
              "captcha": {
                "uuid": _this.captchaSrc["uuid"],
                "word": _this.captchaInput
              }
            }),
            headers: {"content-type": "	application/json"}
          }).then((res) => {
            if (res.data["is_success"] === true) {
              ElNotification({
                title: 'Success',
                message: '提交成功',
                type: 'success',
              })
              _this.body = "# markdown文件格式"
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
            title: '签名验证失败',
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
