<template>
  <div>
    <div class="login">
      <h1 style="text-align: center">管理员登录</h1>
      <el-form label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="username"></el-input>
        </el-form-item>
        <el-form-item label="密码">
          <el-input show-password v-model="password"></el-input>
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
      </el-form>
      <div class="login-button">
        <el-button type="primary" v-on:click="login">登录</el-button>
      </div>
    </div>
  </div>
</template>

<script>
import {ElNotification} from "element-plus";

export default {
  name: "BackstageLogin",
  components: {},
  data() {
    return {
      token: this.getToken(),
      username: "",
      password: "",
      captchaSrc: "",
      captchaInput: ""
    }
  },
  created() {
    this.verifyToken()
    this.getCAPTCHA()
  },
  methods: {
    getToken: function () {
      return localStorage.getItem('token');
    },
    getCAPTCHA: function () {
      this.axios.post("/captcha/get")
          .then((res) => {
            this.captchaSrc = res.data.data
          })
      this.captchaInput = ""
    },
    verifyToken: function () {
      const _this = this
      this.axios({
        method: "post",
        url: "/backstage/token/verify",
        data: JSON.stringify({
          "token": _this.token
        }),
        headers: {"content-type": "application/json"}
      }).then((res) => {
        if (res.data["is_success"]) {
          this.$router.push("/backstage")
        }
      })
    },
    login: function () {
      const _this = this
      this.axios({
        method: "post",
        url: "/backstage/login",
        data: JSON.stringify({
          "username": _this.username,
          "password": _this.password,
          "captcha": {
            "uuid": _this.captchaSrc["uuid"],
            "word": _this.captchaInput
          }
        }),
        headers: {"content-type": "	application/json"}
      }).then((res) => {
        localStorage.setItem("token", res.data["data"])
        if (!res.data["is_success"]) {
          ElNotification({
            title: 'Error',
            message: res.data["data"],
            type: 'error',
          })
          _this.getCAPTCHA()
        } else {
          this.$router.push("/backstage")
        }
      })
    },
  }
}
</script>

<style scoped>
.login {
  margin: 15% auto;
  padding: 10px 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1)
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

.login-button {
  margin: 10px auto;
  text-align: center;
}
</style>
