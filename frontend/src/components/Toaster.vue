<template>
    <div>
    </div>
</template>
<script>
import { Toast } from "toaster-js";
import "toaster-js/default.css"
export default {
  name: 'ToasterComponent',
  data() {
    return {
        alertTypes: {
            "info": Toast.TYPE_INFO,
            "error": Toast.TYPE_ERROR,
            "warning": Toast.TYPE_WARNING,
            "done": Toast.TYPE_DONE
        }
    }
  },
  mounted: function() {
      this.emitter.on('alert', (data) => {
          this.fireAlert(data)
      })
  },
  beforeDestroy: function() {
      this.emitter.off('alert')
  },
  methods: {
      fireAlert: function(data) {
          if (this.alertTypes.hasOwnProperty(data.messageType)){
              new Toast(data.message, this.alertTypes[data.messageType])
          } else {
              new Toast(data.message)
          }
      }
  }
};
</script>
