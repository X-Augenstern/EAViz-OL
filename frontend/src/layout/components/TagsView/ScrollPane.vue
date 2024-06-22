<template>
  <!-- 监听滚轮事件（wheel event），并调用组件中的handleScroll方法，同时使用.prevent修饰符来阻止默认的滚动行为 -->
  <el-scrollbar ref="scrollContainer" class="scroll-container" @wheel.prevent="handleScroll">
    <!-- 插槽，用于渲染组件内容。这意味着在使用该组件时，可以将其他内容放入该组件内，并且这些内容将被渲染到插槽位置。 -->
    <!-- 
    slot 是 Vue.js 2.x 中定义插槽的方式。
    v-slot 是 Vue.js 2.6.0 引入的一种新的插槽语法，它在 Vue 3.x 中继续使用。
    v-slot 提供了一种更灵活和清晰的方式来定义具名插槽 (named slots) 和作用域插槽 (scoped slots)。 
    -->
    <slot />
  </el-scrollbar>
</template>

<script setup>
import useTagsViewStore from '@/store/modules/tagsView'
import { getCurrentInstance } from 'vue';

const tagAndTagSpacing = ref(4);

// 用于获取当前组件实例的 API。它通常用于组合式 API (Composition API) 中，允许访问当前组件实例的一些内部细节。
// getCurrentInstance() 返回的是一个包含当前组件实例上下文的对象，而 proxy 是这个对象中的一个属性，它指向当前组件的代理对象。
// 通过 proxy 可以访问和操作当前组件实例的所有响应式属性和方法，就像在模板或选项式 API (Options API) 中使用 this 一样。
const { proxy } = getCurrentInstance();

// $refs 是 Vue 中用来访问组件模板中被 ref 特性引用的 DOM 元素或子组件实例的对象。
// proxy.$refs.scrollContainer 获取到 el-scrollbar 组件实例后，再次通过 $refs 访问该组件内部的 wrapRef。
// wrapRef 是 el-scrollbar 组件内部定义的一个引用，通常指向实际的滚动包裹容器。
const scrollWrapper = computed(() => proxy.$refs.scrollContainer.$refs.wrapRef);

onMounted(() => {
  // addEventListener 方法用于给 scrollWrapper 添加一个滚动事件监听器
  // 'scroll' 是事件类型，表示监听滚动事件
  // emitScroll 是回调函数，当发生滚动事件时会执行这个函数
  // true 是事件捕获选项，表示在捕获阶段触发事件
  scrollWrapper.value.addEventListener('scroll', emitScroll, true)
})
onBeforeUnmount(() => {
  // removeEventListener 方法用于移除滚动事件监听器，可以确保在组件卸载时不会再触发滚动事件，从而避免潜在的内存泄漏
  scrollWrapper.value.removeEventListener('scroll', emitScroll)
})

/**
 * 根据鼠标滚轮的垂直滚动来实现横向滚动。当用户滚动鼠标滚轮或使用触控板进行垂直滚动时，函数将计算滚动增量，并将其应用于横向滚动位置，从而实现内容的水平滚动
 * @param {*} e 事件对象 e 作为参数。这个事件对象通常是鼠标滚轮事件或触控板滚动事件
 */
function handleScroll(e) {
  // e.wheelDelta 是鼠标滚轮事件的滚动增量属性。在现代浏览器中，这个属性通常表示垂直滚动增量
  // e.deltaY 是标准的滚动事件属性，表示垂直滚动距离。由于 deltaY 通常是一个较小的值（与 wheelDelta 相比），它乘以 -40 后得到一个与 wheelDelta 相当的值。
  const eventDelta = e.wheelDelta || -e.deltaY * 40
  const $scrollWrapper = scrollWrapper.value;
  // scrollLeft 是 DOM 元素的属性，表示元素的横向滚动位置
  // eventDelta / 4 将滚动增量除以 4，以减少滚动的敏感度，使滚动更平滑
  $scrollWrapper.scrollLeft = $scrollWrapper.scrollLeft + eventDelta / 4
}

// defineEmits 是 Vue 3 提供的组合式 API，用于定义组件可以发射的事件。
// 调用 defineEmits() 会返回一个函数 emits，这个函数可以用来触发事件。
const emits = defineEmits()
const emitScroll = () => {
  emits('scroll')  // 使用 emits('scroll') 来发射（触发）scroll 事件。
}

const tagsViewStore = useTagsViewStore()
const visitedViews = computed(() => tagsViewStore.visitedViews);

/**
 * 在标签导航视图中滚动到指定的标签，根据当前标签的位置调整滚动容器的滚动位置，以确保目标标签在视口内可见
 * 
 * 1、若目标标签就是第一个：滚动到最左侧
 * 2、若目标标签就是最后一个：让目标标签刚好在视口的最右侧
 * 3、若目标标签在中间：获取其前一个标签和后一个标签
 *    若下一个标签的右边缘加上标签间距的位置位于视口外，让下一个标签的右边缘加上标签间距的位置刚好在视口的最右侧
 *    若上一个标签的左边缘减去标签间距的位置位于视口外，让上一个标签的左边缘减去标签间距的位置刚好在视口的最左侧
 * @param {*} currentTag 目标标签
 */
function moveToTarget(currentTag) {
  // 在自定义组件中，$el 属性始终指向组件实例的根 DOM 元素。这对于需要直接操作组件的根元素或获取元素的大小、位置等信息时非常有用。
  // 对于 el-scrollbar 组件，它的 $el 属性指向实际渲染的滚动条容器的 DOM 元素。
  const $container = proxy.$refs.scrollContainer.$el  // 滚动容器的 DOM 元素
  const $containerWidth = $container.offsetWidth  // 滚动容器的可见宽度，即视口的宽度。它表示当前能够在视口中看到的那部分内容的宽度
  const $scrollWrapper = scrollWrapper.value;  // 内部实际的滚动包裹容器，通过计算属性 scrollWrapper.value 获取

  let firstTag = null
  let lastTag = null

  // find first tag and last tag
  if (visitedViews.value.length > 0) {
    firstTag = visitedViews.value[0]
    lastTag = visitedViews.value[visitedViews.value.length - 1]
  }

  if (firstTag === currentTag) {
    $scrollWrapper.scrollLeft = 0  // 滚动到最左侧
  } else if (lastTag === currentTag) {
    // scrollWidth：滚动容器的总内容宽度，包括不可见的部分。它表示整个内容的宽度，无论内容是否在视口内（会随着Tag的增加而延伸）
    // 假设滚动容器的总内容宽度为 2000px，视口宽度为 500px。当要滚动到最右边时：
    // 设置 scrollWrapper.scrollLeft 为 1500px，意味着内容的最后 500px 部分将显示在视口内，确保最后一个标签完全可见
    // （让最后一个标签刚好在视口的最右侧）
    $scrollWrapper.scrollLeft = $scrollWrapper.scrollWidth - $containerWidth  // 最大滚动距离，即滚动到最右侧
  } else {
    const tagListDom = document.getElementsByClassName('tags-view-item');  // 获取所有标签的 DOM 元素列表 tagListDom
    const currentIndex = visitedViews.value.findIndex(item => item === currentTag)
    let prevTag = null
    let nextTag = null
    for (const k in tagListDom) {  // k 是当前遍历到的属性名称
      // 确保在遍历 tagListDom 时，只处理实际存在的标签元素，而不是集合的内建属性或继承的属性
      if (k !== 'length' && Object.hasOwnProperty.call(tagListDom, k)) {  // 确保 tagListDom 对象自身拥有 k 属性，而不是从其原型链继承来的属性
        // 在 HTMLCollection 或 NodeList 这样的类数组对象中，属性名称实际上是字符串类型的索引，所以可以使用 tagListDom[k] 来访问对应的 DOM 元素
        // dataset 是一个 DOM 属性，它是一个 DOMStringMap 对象，包含所有以 data- 为前缀的自定义数据属性
        // path 是自定义数据属性 data-path 的名称
        // tagListDom[k].dataset.path 获取到的是该元素的 data-path 属性的值
        if (tagListDom[k].dataset.path === visitedViews.value[currentIndex - 1].path) {
          prevTag = tagListDom[k];
        }
        if (tagListDom[k].dataset.path === visitedViews.value[currentIndex + 1].path) {
          nextTag = tagListDom[k];
        }
      }
    }

    // the tag's offsetLeft after of nextTag
    // nextTag.offsetLeft：nextTag 元素相对于其包含块（最近的已定位的祖先元素）的左边距
    // afterNextTagOffsetLeft 表示 nextTag 的右边缘加上标签间距的位置。
    const afterNextTagOffsetLeft = nextTag.offsetLeft + nextTag.offsetWidth + tagAndTagSpacing.value

    // the tag's offsetLeft before of prevTag
    // beforePrevTagOffsetLeft 表示 prevTag 的左边缘减去标签间距的位置
    const beforePrevTagOffsetLeft = prevTag.offsetLeft - tagAndTagSpacing.value

    if (afterNextTagOffsetLeft > $scrollWrapper.scrollLeft + $containerWidth) {
      $scrollWrapper.scrollLeft = afterNextTagOffsetLeft - $containerWidth  // 同理
    } else if (beforePrevTagOffsetLeft < $scrollWrapper.scrollLeft) {
      $scrollWrapper.scrollLeft = beforePrevTagOffsetLeft
    }
  }
}

defineExpose({
  moveToTarget,
})
</script>

<style lang='scss' scoped>
.scroll-container {
  white-space: nowrap;
  position: relative;
  overflow: hidden;
  width: 100%;

  // deep 是 Vue 特有的选择器，用于在 scoped 样式中定义全局样式或作用于子组件的深层次选择器。
  :deep(.el-scrollbar__bar) {
    // :deep 可以用于跨越作用域边界应用样式。
    // .el-scrollbar__bar 是 Element UI 滚动条组件的内部滚动条的类名。
    bottom: 0px;
  }

  :deep(.el-scrollbar__wrap) {
    // .el-scrollbar__wrap 是 Element UI 滚动条组件的内部滚动容器的类名。
    height: 39px;
  }
}
</style>