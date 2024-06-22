// 入口
import { createApp } from 'vue'
import App from './App.vue'
import Cookies from 'js-cookie'

// 获取应用实例对象
const app = createApp(App)

// 引入element-plus插件与样式
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// 配置element-plus国际化
// 需要忽略当前文件的ts类型检测，否则打包会失败
//@ts-ignore
import locale from 'element-plus/es/locale/lang/zh-cn'
// 全局配置UI组件库并设置语言为中文
app.use(ElementPlus, {
  locale: locale,
  // 支持 large、default、small
  size: Cookies.get('size') || 'default'
})

// SVG插件需要的配置代码
// 自动注册位于 'src/assets/icons/svg' 文件夹中的所有 SVG 文件为图标
// virtual:svg-icons-register 是一个虚拟模块，它由 vite-plugin-svg-icons 插件生成，并在构建时注入到项目中
import 'virtual:svg-icons-register'

// 引入模板的全局样式
import '@/assets/styles/index.scss'

// 引入并安装路由
import router from './router'
app.use(router)

// 引入并安装pinia
import store from './store'
app.use(store)

// 引入路由鉴权文件
import './permission'

// 引入自定义指令文件
import directive from './directive' // directive
directive(app)

// 引入并安装插件
import plugins from './plugins' // plugins
app.use(plugins)

// 全局方法挂载
import { download } from '@/utils/request'
import { useDict } from '@/utils/dict'
import { parseTime, resetForm, addDateRange, handleTree, selectDictLabel, selectDictLabels } from '@/utils/ruoyi'
app.config.globalProperties.useDict = useDict
app.config.globalProperties.download = download
app.config.globalProperties.parseTime = parseTime
app.config.globalProperties.resetForm = resetForm
app.config.globalProperties.handleTree = handleTree
app.config.globalProperties.addDateRange = addDateRange
app.config.globalProperties.selectDictLabel = selectDictLabel
app.config.globalProperties.selectDictLabels = selectDictLabels

// 全局组件挂载
// 引入自定义插件对象：注册为整个项目全局组件
// 在导入模块时省略文件名，只提供目录路径时，默认会寻找该目录下的index.js或index.ts文件作为入口。这是一种约定俗成的做法，使得模块的导入语句更加简洁。
// .vue需要额外配置
import globalComponents from '@/components'
app.use(globalComponents);  // 安装插件 触发globalComponents内的install方法

// 将应用挂载到挂载点上
app.mount('#app')
