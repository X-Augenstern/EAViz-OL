// 引入项目中的全部全局组件

// 分页组件
import Pagination from "./Pagination/index.vue"
// 自定义表格工具组件
import RightToolbar from "./RightToolbar/index.vue"
// 富文本组件
import Editor from "./Editor/index.vue"
// 文件上传组件
import FileUpload from "./FileUpload/index.vue"
// 图片上传组件
import ImageUpload from "./ImageUpload/index.vue"
// 图片预览组件
import ImagePreview from "./ImagePreview/index.vue"
// 自定义树选择组件
import TreeSelect from "./TreeSelect/index.vue"
// 字典标签组件
import DictTag from "./DictTag/index.vue"
// SVG组件
import SvgIcon from "./SvgIcon/index.vue"

// 引入element-plus提供的全部icon组件
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 全局对象
const allGlobalComponent = { Pagination, RightToolbar, Editor, FileUpload, ImageUpload, ImagePreview, TreeSelect, DictTag, SvgIcon }
// console.log(Object.keys(allGlobalComponent))  // ['SvgIcon', 'Pagination']

// 对外暴露插件对象
export default {
  install(app) {  // 会传入app应用实例
    // console.log(app)
    // 注册
    Object.keys(allGlobalComponent).forEach(key => {
      app.component(key, allGlobalComponent[key])  // 'SvgIcon' - SvgIcon对象
    })

    // 将element-plus提供的图标注册为全局组件
    for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
      app.component(key, component)
    }
  }
}

