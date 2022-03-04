<template>
  <div>
    <el-form :rules="rules" label-position="right" label-width="70px" class="demo-ruleForm"
             size="default">
      <el-form-item label="用户公钥">
        <el-input v-model="publicKey" :autosize="{minRows: 1}" type="textarea">
        </el-input>
        <div>
          <el-link type="primary" v-on:click="publicKeyDialog = true">没有公钥？</el-link>
        </div>
      </el-form-item>
      <div>
        <el-form-item label="内容">
          <el-input :autosize="{ minRows: 2 }" v-model="body" type="textarea">
          </el-input>
          <el-collapse style="width: 100%">
            <el-collapse-item title="预览" name="1">
              <div>
                <Markdown :source="body"></Markdown>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-form-item>
      </div>
      <el-form-item label="签名">
        <el-input :autosize="{ minRows: 1 }" type="textarea" v-model="signature">
        </el-input>
        <div>
          <el-link type="primary" v-on:click="signatureDialog = true">如何计算签名？</el-link>
        </div>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" v-on:click="verifySign">提交到主节点</el-button>
        <el-button v-on:click="privateKey='';publicKey='';signature='';body=''">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
  <div>
    <!--公钥生成弹框-->
    <el-dialog v-model="publicKeyDialog" title="在线生成" width="80%">
      <div>
        <el-form>
          <p>此处不会存储您的私钥，计算任务全部都在本地进行。</p>
          <p class="sk-alert">注意：</p>

          <el-form-item label="用户私钥：">
            <el-input v-model="privateKey" autosize type="textarea" autofocus>
            </el-input>
          </el-form-item>
          <el-form-item label="用户公钥：">
            <el-input v-model="publicKey" autosize type="textarea" readonly>
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
          <div>
            <el-form-item label="用户私钥：" label-width="90px">
              <el-input v-model="privateKey" autosize type="textarea"/>
            </el-form-item>
          </div>
          <div>
            <el-form-item label="签名：" label-width="90px">
              <el-input v-model="signature" autosize type="textarea"/>
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

export default {
  name: "ReleaseBlock",
  components: {
    Markdown
  },
  data() {
    return {
      path: "http://localhost:8080/static/js/jsrsasign/",
      fullscreenLoading: false,
      publicKeyDialog: false,
      signatureDialog: false,
      privateKeyDialog: false,
      privateKey: "",
      publicKey: "",
      body: '# markdown文件格式',
      signature: "",
      computeLoading: false,
      ruleForm: {
        name: '',
        region: '',
        date1: '',
        date2: '',
        delivery: false,
        type: [],
        resource: '',
        desc: '',
      },
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
    //生成密钥对
    generatePK: function () {
      const loading = this.$loading({lock: true, text: '正在计算中...', background: 'rgba(0, 0, 0, 0.7)'})
      const _this = this
      this.$worker.run((path) => {
        this.importScripts(path + "jsrsasign-all-min.js")
        const ec = new this.KJUR.crypto.ECDSA({'curve': 'NIST P-384'});
        // EC公钥的十六进制字符串
        const keyPairHex = ec.generateKeyPairHex()
        const pubHex = keyPairHex.ecpubhex
        const prvHex = keyPairHex.ecprvhex
        return [pubHex, prvHex]
      }, [this.path]).then((res) => {
        console.log(res)
        _this.publicKey = res[0]
        _this.privateKey = res[1]
        loading.close()
      })
    },
    //签名
    sign: function () {
      const loading = this.$loading({lock: true, text: '正在计算中...', background: 'rgba(0, 0, 0, 0.7)'})
      const _this = this
      this.$worker.run((path, prvHex, message) => {
        this.importScripts(path + "jsrsasign-all-min.js")
        const sig = new this.KJUR.crypto.Signature({'alg': 'SHA256withECDSA'});
        sig.init({d: prvHex, curve: 'NIST P-384'});
        sig.updateString(message);
        const sigValueHex = sig.sign()
        return sigValueHex
      }, [this.path, this.privateKey, this.body]).then((res) => {
        console.log(res)
        _this.signature = res
        loading.close()
      })
    },
    //  验证签名
    verifySign: function () {
      const loading = this.$loading({lock: true, text: '正在计算中...', background: 'rgba(0, 0, 0, 0.7)'})
      // const _this = this
      this.$worker.run((path, pubHex, message, sigValueHex) => {
        this.importScripts(path + "jsrsasign-all-min.js")
        const sig = new this.KJUR.crypto.Signature({"alg": 'SHA256withECDSA', "prov": "cryptojs/jsrsa"});
        sig.init({xy: pubHex, curve: 'NIST P-384'});
        sig.updateString(message);
        const result = sig.verify(sigValueHex);
        return result
      }, [this.path, this.publicKey, this.body, this.signature]).then((res) => {
        console.log(res)
        loading.close()
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

.button-sk {
  margin: 20px auto;
  text-align: center;
}
</style>
