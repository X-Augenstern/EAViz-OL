<template>
  <!-- 如果 item.hidden 为 false，则渲染该导航项 -->
  <div v-if="!item.hidden">
    <!-- 如果只有一个子项要显示，并且该子项没有子项或该子项的子项没有要显示的子项，并且 item.alwaysShow 为 false -->
    <template
      v-if="hasOneShowingChild(item.children, item) && (!onlyOneChild.children || onlyOneChild.noShowingChildren) && !item.alwaysShow">
      <!-- 渲染单个导航项链接 -->
      <app-link v-if="onlyOneChild.meta" :to="resolvePath(onlyOneChild.path, onlyOneChild.query)">
        <!-- 动态 class 绑定表达式。具体来说，它用于根据 isNest 的值动态地应用或移除 CSS 类 submenu-title-noDropdown 
          :class 属性: Vue.js 提供的一个特性，允许我们动态绑定一个或多个 CSS 类
          { 'submenu-title-noDropdown': !isNest }: 这是一个对象语法的表达式。
          在对象语法中，键是 CSS 类名，值是一个布尔值。如果值为 true，则应用这个 CSS 类；如果值为 false，则移除这个 CSS 类
          假设 isNest 的值为 false，那么 !isNest 就是 true，所以 submenu-title-noDropdown 类会被应用到这个元素上
        -->
        <el-menu-item :index="resolvePath(onlyOneChild.path)" :class="{ 'submenu-title-noDropdown': !isNest }">
          <!-- 显示图标 -->
          <svg-icon :icon-class="onlyOneChild.meta.icon || (item.meta && item.meta.icon)" />
          <!-- 显示标题 -->
          <template #title><span class="menu-title" :title="hasTitle(onlyOneChild.meta.title)">{{
            onlyOneChild.meta.title }}</span></template>
        </el-menu-item>
      </app-link>
    </template>

    <!-- 否则，渲染一个带有子菜单的导航项 -->
    <!-- 带 : 的属性表示绑定动态属性，也叫做指令绑定。它允许绑定 JavaScript 表达式的值到属性上，Vue.js 会在组件实例的上下文中求值这些表达式。
          :index="resolvePath(item.path)"：这里的 index 属性值是动态计算的。Vue.js 会求值 resolvePath(item.path) 并将其结果绑定到 index 属性上。
          这意味着 index 属性的值会随着 resolvePath(item.path) 计算结果的变化而变化。
    
        不带 : 的属性表示绑定静态属性。它的值是一个固定的字符串，不会随组件的状态或属性变化而变化。
          index="fixed-value"：这里的 index 属性值是一个固定的字符串 "fixed-value"，不会随着组件的状态变化而变化。
    -->

    <!-- teleported 是 Vue 3 中引入的一个特性，用于将组件的内容渲染到 DOM 的其他位置，而不是它在模板中原本的位置。
        这在处理层叠样式表 (CSS) 的 z-index 或在结构化 HTML 布局时非常有用。
     
        teleported 常用于以下场景：
        1、模态框和弹出层: 将模态框或弹出层内容渲染到 <body> 元素下，以确保它们的 z-index 能够正确覆盖其他元素。
        2、工具提示和下拉菜单: 类似于模态框，将这些元素渲染到页面的其他位置，以避免 CSS 层级问题。
        3、嵌套菜单: 在复杂的导航结构中，将子菜单内容放置在页面的其他位置，避免嵌套导致的布局问题。

        当使用 teleported 特性时，Vue 会将组件的内容移动到一个指定的容器中。
        例如，如果有一个 <el-sub-menu> 组件并且使用了 teleported 属性，Vue 会将该子菜单的内容移动到 <body> 元素或其他指定的 DOM 位置，
        从而避免嵌套菜单可能遇到的 CSS 层级问题。
    -->
    <el-sub-menu v-else ref="subMenu" :index="resolvePath(item.path)" teleported>
      <!-- 如果 item 有 meta 信息，则渲染标题 -->
      <template v-if="item.meta" #title>
        <svg-icon :icon-class="item.meta && item.meta.icon" />
        <span class="menu-title" :title="hasTitle(item.meta.title)">{{ item.meta.title }}</span>
      </template>
      <!-- 遍历并渲染子菜单项 -->
      <sidebar-item v-for="(child, index) in item.children" :key="child.path + index" :is-nest="true" :item="child"
        :base-path="resolvePath(child.path)" class="nest-menu" />
    </el-sub-menu>
  </div>
</template>

<script setup name="SidebarItem">
import { isExternal } from '@/utils/validate'
import AppLink from './Link.vue'
import { getNormalPath } from '@/utils/ruoyi'

const props = defineProps({
  // route object
  item: {
    type: Object,
    required: true
  },
  isNest: {
    type: Boolean,
    default: false
  },
  basePath: {
    type: String,
    default: ''
  }
})

const onlyOneChild = ref({});

function hasOneShowingChild(children = [], parent) {
  // 如果 children 为 null 或未定义，将其设置为空数组
  if (!children) {
    children = [];
  }
  // 筛选出未隐藏的子路由
  const showingChildren = children.filter(item => {
    if (item.hidden) {
      return false
    } else {
      // Temp set(will be used if only has one showing child) 临时保存唯一的未隐藏子路由
      onlyOneChild.value = item
      return true
    }
  })

  // When there is only one child router, the child router is displayed by default
  if (showingChildren.length === 1) {
    return true
  }

  // Show parent if there are no child router to display
  // 如果没有未隐藏的子路由，将父路由信息保存到 onlyOneChild
  if (showingChildren.length === 0) {
    // ...parent 是 JavaScript 中的扩展运算符（spread operator），用于对象的解构和扩展。
    // 在这个上下文中，它用于创建一个新的对象，该对象包含 parent 对象中的所有属性，并且可以添加或覆盖一些属性。
    onlyOneChild.value = { ...parent, path: '', noShowingChildren: true }
    return true
  }
  // 如果有多个未隐藏的子路由，返回 false
  return false
};

function resolvePath(routePath, routeQuery) {
  if (isExternal(routePath)) {  // routePath是外部链接
    return routePath
  }
  if (isExternal(props.basePath)) {  // props.basePath是外部链接
    return props.basePath
  }
  if (routeQuery) {  // 如果存在 routeQuery，将 routeQuery 解析为对象，并返回包含路径和查询参数的对象
    let query = JSON.parse(routeQuery);
    return { path: getNormalPath(props.basePath + '/' + routePath), query: query }
  }
  return getNormalPath(props.basePath + '/' + routePath)  // 否则，返回规范化后的完整路径字符串
}

function hasTitle(title) {
  if (title.length > 5) {
    return title;
  } else {
    return "";
  }
}
</script>
