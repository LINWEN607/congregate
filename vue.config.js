const path = require('path');
module.exports = {
  configureWebpack: {
    resolve: {
      alias: {
        "@": path.resolve(__dirname, 'frontend/src/')
      }
    }
  },
  assetsDir: 'static'
}
