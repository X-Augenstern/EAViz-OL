<!-- 根据传入的 to 属性判断链接类型，并动态地选择渲染一个普通的 <a> 标签或者一个 router-link 组件
  组件内部处理流程：
    1、定义和接收 props：
    通过 defineProps 定义了 to 属性，并声明其类型和必填要求。
    组件在使用时，Vue 会自动将传递的 to 属性值赋给 props.to。
  
    2、使用 props.to 计算属性和方法：
    isExt 计算属性根据 props.to 的值来判断是否为外部链接。
    type 计算属性根据 isExt 的值来确定渲染的组件类型（<a> 或 router-link）。
    linkProps 方法根据 isExt 的值来返回相应的属性对象。
-->
<template>
  <!-- <component> 是 Vue.js 提供的内置组件，它允许动态地渲染不同的组件。通过使用 :is 绑定一个变量，可以根据变量的值来决定渲染哪个具体的组件 -->
  <!-- v-bind="linkProps()" 会将 linkProps() 返回的属性对象绑定到生成的组件上。 -->
  <component :is="type" v-bind="linkProps()">
    <!-- 插槽，用来分发组件内容。插槽允许在使用组件时向组件传递自定义内容。这个机制使得组件更加灵活和可复用。 -->
    <!-- <slot /> 表示这个 Link 组件可以接收并展示它的子内容。无论渲染的是 <a> 还是 router-link，都会在组件内部展示传递给它的子内容。
      eg:
          <Link to="/internal/path">
            <svg-icon icon-class="example-icon"></svg-icon>
            <span>Click here to visit internal path</span>
          </Link>

          在 Vue.js 中，组件接收的所有属性都可以通过 props 进行声明和访问。
          to="/internal/path" 作为一个属性传递给了 Link 组件。
          Link 组件通过 defineProps 定义了 to 属性，用于接收传入的值。

      这会渲染成：
          <router-link :to="/internal/path">
            <svg-icon icon-class="example-icon"></svg-icon>
            <span>Click here to visit internal path</span>
          </router-link>
    -->
    <slot />
  </component>
</template>

<script setup name="Link">
import { isExternal } from '@/utils/validate'

const props = defineProps({
  // 由外部传入
  to: {
    type: [String, Object],  // to 属性可以是字符串类型或对象类型
    required: true  // to 属性是必填的。这意味着在使用 Link 组件时，必须提供 to 属性，否则 Vue 会在开发环境中发出警告
  }
})

const isExt = computed(() => {
  // computed 属性会根据其依赖的响应式数据（这里是 props.to）自动更新
  // 当 props.to 发生变化时，isExt 计算属性会自动重新计算，从而保持数据的同步
  // 惰性计算
  // 基于其依赖的数据进行缓存的，只有当依赖的数据发生变化时才会重新计算
  return isExternal(props.to)
})

const type = computed(() => {
  // 基于 isExt 的值决定要渲染的组件类型
  // 若为外部链接渲染为a标签（定义超链接）
  if (isExt.value) {
    return 'a'
  }
  return 'router-link'
})

function linkProps() {
  // 基于 isExt 的值返回不同的属性对象

  /* eg： 假设 props.to 为 'https://example.com'（一个外部链接）
          linkProps 会返回 { href: 'https://example.com', target: '_blank', rel: 'noopener' }。
          模板渲染为：
              <a href="https://example.com" target="_blank" rel="noopener">
                <slot />
              </a>
        
          如果 props.to 为 '/internal/path'（一个内部路由），那么：
          linkProps 会返回 { to: '/internal/path' }。
          模板渲染为：
              <router-link :to="'/internal/path'">
                <slot />
              </router-link>

          为什么 linkProps() 返回 { to: '/internal/path' } 会渲染成 :to="..."?
              当 linkProps() 返回 { to: '/internal/path' } 时，它是为了与 Vue Router 的 router-link 组件的 to 属性相匹配。
              Vue Router 的 router-link 组件使用 to 属性来指定导航目的地，这与 HTML 中的 href 属性类似。

              这是因为在 Vue 模板中，:to="..." 是用于绑定 router-link 组件的 to 属性的标准语法。
              Vue 会根据 linkProps() 返回的对象，将其属性和值正确地绑定到组件上。
              这是 Vue 响应式系统和模板语法的一部分，使得开发者可以动态地绑定和更新组件属性。
  */
  if (isExt.value) {
    return {
      href: props.to,
      target: '_blank',
      rel: 'noopener'
    }
  }
  return {
    to: props.to
  }
}
</script>
