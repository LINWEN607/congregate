<template>
  <footer class="footer">
    <div class="container">
      <div id="stage_log">
        <p>Status</p>
      </div>
      <button v-on:click="stage()" :id="asset" class="stage_button">{{ msg }}</button>
    </div>
  </footer>
</template>

<script>
import { EventBus } from "@/event-bus.js";
export default {
  name: "Footer",
  props: {
    msg: String,
    asset: String
  },
  methods: {
    stage: function() {
      EventBus.$emit(this.asset);
    }
  }
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="less">
footer {
  position: fixed;
  bottom: 0;
  width: 100%;
  background-color: #ddd;
  padding-bottom: 1em;
}
</style>
