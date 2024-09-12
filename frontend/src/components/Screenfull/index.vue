<template>
  <div>
    <svg-icon
      :icon-class="isFullscreen ? 'exit-fullscreen' : 'fullscreen'"
      @click="toggle"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useFullscreen } from "@vueuse/core";

const props = defineProps({
  target: {
    // 指定全屏的目标元素选择器
    type: String,
    default: "", // 默认全屏整个页面
  },
  onFullscreenChange: {
    // Plotly 在全屏与退出全屏时触发Autoscale
    type: Function,
    default: null,
  },
});

const targetElement = ref(document.documentElement); // 保存将被全屏化的 DOM 元素的引用。初始值设置为 document.documentElement，即整个 HTML 文档元素，表示全屏整个页面

onMounted(() => {
  if (props.target) {
    const target = document.querySelector(props.target); // 查找指定的目标元素，并将其赋值给 targetElement
    if (target) {
      targetElement.value = target;
    }
  }
});

const { isFullscreen, enter, exit, toggle } = useFullscreen(targetElement); // 接受一个 DOM 元素（或其 ref）作为参数，并返回一组工具函数和状态
// isFullscreen：一个布尔值，表示当前是否处于全屏模式。
// enter：一个函数，用于使 targetElement 进入全屏模式。
// exit：一个函数，用于退出全屏模式。
// toggle：一个函数，用于在全屏模式和退出全屏模式之间切换。

// 监听全屏状态变化并调用回调函数
watch(isFullscreen, () => {
  if (props.onFullscreenChange) {
    props.onFullscreenChange();
  }
});
</script>

<style lang='scss' scoped>
// .screenfull-svg {
//   display: inline-block;
//   cursor: pointer;
//   fill: #5a5e66;
//   width: 20px;
//   height: 20px;
//   vertical-align: 10px;}
</style>