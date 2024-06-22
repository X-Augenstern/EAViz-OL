<template>
  <!-- 在页面中切换和显示多个 iframe 视图 -->
  <inner-link v-for="(item, index) in tagsViewStore.iframeViews" :key="item.path" :iframeId="'iframe' + index"
    v-show="route.path === item.path" :src="iframeUrl(item.meta.link, item.query)"></inner-link>
</template>

<script setup name="IframeToggle">
import InnerLink from "../InnerLink/index";
import useTagsViewStore from "@/store/modules/tagsView";

const route = useRoute();
const tagsViewStore = useTagsViewStore();

function iframeUrl(url, query) {
  // 根据给定的基本URL和查询参数对象（query parameters），构建一个完整的URL
  if (Object.keys(query).length > 0) {
    // 构建查询字符串：
    // 如果query对象中有键值对，函数将使用Object.keys(query)获取所有参数的键（即参数名）。
    // 使用map方法，对每个键进行操作，将键和其对应的值（从query对象中获取）结合成key=value的格式。
    // 使用join("&")将所有的key=value对通过&符号连接起来，形成一个完整的查询字符串。
    // iframeUrl("http://example.com", { user: "john", age: 30 })
    // -> http://example.com?user=john&age=30
    let params = Object.keys(query).map((key) => key + "=" + query[key]).join("&");
    return url + "?" + params;
  }
  return url;
}
</script>
