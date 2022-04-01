<template>
  <router-view></router-view>
</template>

<script>
// import WaitingForLoading from "@/components/WaitingForLoading";

export default {
  name: 'App',
  created() {
  }
}
</script>

<style>
@media screen and (min-width: 600px) {
  #app {
    margin: auto;
    width: 80%;
  }
}

@media screen and (max-width: 600px) {
  #app {
    margin: auto;
    width: 100%;
  }
}

</style>
