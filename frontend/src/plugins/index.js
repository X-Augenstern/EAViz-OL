import tab from './tab'
import auth from './auth'
import cache from './cache'
import modal from './modal'
import download from './download'

// 将一些自定义对象或插件（如 $tab、$auth、$cache、$modal、$download）添加到 Vue 应用实例的全局属性中，使得这些对象可以在整个应用中轻松访问和使用
export default function installPlugins(app) {
  // Vue 3 中用于添加全局属性的对象。这些属性可以在整个应用中的任意组件中通过 this 访问
  // 页签操作，将 tab 对象（假设是预先定义的对象或插件）添加为全局属性 $tab。这样就可以在任何组件中通过 this.$tab 访问和使用 tab 对象
  app.config.globalProperties.$tab = tab
  // 认证对象
  app.config.globalProperties.$auth = auth
  // 缓存对象
  app.config.globalProperties.$cache = cache
  // 模态框对象
  app.config.globalProperties.$modal = modal
  // 下载文件
  app.config.globalProperties.$download = download
}
