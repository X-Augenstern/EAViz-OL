<!-- 嵌入一个自适应高度的内联框架（iframe）。通过传递src和iframeId属性，可以控制iframe加载的内容和识别iframe。
高度的计算是为了让iframe在不同设备和屏幕尺寸下都能合适地展示内容，94.5px的减法是为了留出页面上方的一些空间，例如导航栏
 
<iframe> 标签定义行内框架（内联框架）。
行内框架用于在当前 HTML 文档中嵌入另一个文档。 
src：	URL	规定要嵌入到 <iframe> 中的文档的地址。
id	规定元素的唯一 id。
-->
<template>
  <div :style="'height:' + height">
    <iframe :id="iframeId" style="width: 100%; height: 100%" :src="src" frameborder="no"></iframe>
  </div>
</template>

<script setup name="InnerLink">
const props = defineProps({
  src: {
    type: String,
    default: "/"
  },
  iframeId: {
    type: String
  }
});

const height = ref(document.documentElement.clientHeight - 94.5 + "px");
</script>
