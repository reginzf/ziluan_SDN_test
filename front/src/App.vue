<template>
  <div id="app">
    <router-view v-if="showRouter" />
  </div>
</template>

<script>
export default {
  name: 'App',
  provide() {
    return {
      reload: this.reload
    }
  },
  data() {
    return {
      showRouter: true
    }
  },
  methods: {
    reload() {
      this.showRouter = false
      this.$nextTick(function() {
        this.showRouter = true
      })
    }
  }
}
</script>
