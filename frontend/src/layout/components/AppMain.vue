<template>
  <section class="app-main">
    <!-- Vue Router 提供的 router-view 组件，它会根据当前的路由展示相应的组件。通过使用 v-slot 可以获取当前渲染的 Component 和 route 对象
    
    v-slot 是 Vue 3 中用于命名插槽的指令，可以用来解构插槽内容。v-slot="{ Component, route }" 
    表示使用解构的方式从 router-view 的默认插槽中获取 Component 和 route。 
    -->
    <router-view v-slot="{ Component, route }">
      <!-- Vue 的过渡组件，用于添加组件切换时的动画效果。这里指定了 fade-transform 作为过渡动画名称，
       且使用了 out-in 模式（先进行离开动画，再进行进入动画）。 -->
      <transition name="fade-transform" mode="out-in">
        <!-- kee-alive 是 Vue 内置的一个组件，可以使被包含的组件保留状态，或避免重新渲染。也就是所谓的组件缓存。
         :include="tagsViewStore.cachedViews" 表示只缓存 tagsViewStore.cachedViews 中包含的组件。
         :is="Component"：动态渲染当前路由匹配的组件。
         :key="route.path"：确保每个路由的组件实例是独立的，触发组件的重新渲染。
          -->
        <keep-alive :include="tagsViewStore.cachedViews">
          <component v-if="!route.meta.link" :is="Component" :key="route.path" />
        </keep-alive>
      </transition>
    </router-view>
    <iframe-toggle />
  </section>
</template>

<script setup name="AppMain">
import iframeToggle from "./IframeToggle/index"
import useTagsViewStore from '@/store/modules/tagsView'

const tagsViewStore = useTagsViewStore()
</script>

<style lang="scss" scoped>
.app-main {
  /* 50= navbar  50  */
  min-height: calc(100vh - 50px);
  width: 100%;
  position: relative;
  overflow: hidden;
}

.fixed-header+.app-main {
  padding-top: 50px;
}

.hasTagsView {
  .app-main {
    /* 84 = navbar + tags-view = 50 + 34 */
    min-height: calc(100vh - 84px);
  }

  .fixed-header+.app-main {
    padding-top: 84px;
  }
}
</style>

<style lang="scss">
// fix css style bug in open el-dialog
.el-popup-parent--hidden {
  .fixed-header {
    padding-right: 6px;
  }
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background-color: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background-color: #c0c0c0;
  border-radius: 3px;
}
</style>
