<template>
  <div>
    <BackstageMain></BackstageMain>
  </div>
</template>

<script>
import BackstageMain from "@/components/backstage/BackstageMain";
import {ElNotification} from "element-plus";

export default {
  name: "BackStage",
  components: {
    BackstageMain
  },
  data() {
    return {
      token: this.getToken(),
    }
  },
  created() {
    this.verifyToken()
  },
  methods: {
    getToken: function () {
      return localStorage.getItem('token');
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
        if (!res.data["is_success"]) {
          this.$router.push("/backstage/login")
        }
      }).catch((err)=>{
        ElNotification({
          title: 'Error',
          message: err,
          type: 'error',
        })
        this.$router.push("/backstage/login")
      })
    },
  }
}
</script>

<style scoped>

</style>
