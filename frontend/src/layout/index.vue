<template>
  <div :class="classObj" class="app-wrapper" :style="{ '--current-color': theme }">
    <!-- 如果设备是移动设备并且侧边栏是打开状态，显示一个背景遮罩，点击时触发handleClickOutside方法 -->
    <div v-if="device === 'mobile' && sidebar.opened" class="drawer-bg" @click="handleClickOutside" />
    <!-- 侧边栏组件，只有在sidebar.hide为false时才显示 -->
    <sidebar v-if="!sidebar.hide" class="sidebar-container" />
    <!-- 主容器，包含导航栏、标签视图和主要内容 -->
    <div :class="{ hasTagsView: needTagsView, sidebarHide: sidebar.hide }" class="main-container">
      <!-- 如果fixedHeader为true，给导航栏添加'fixed-header'类 -->
      <div :class="{ 'fixed-header': fixedHeader }">
        <!-- 
        导航栏组件，设置布局时触发setLayout方法
        在Vue.js中，组件之间可以通过事件传递数据或通知状态变化。@setLayout="setLayout"是事件监听的简写形式，
        用于监听navbar组件触发的setLayout事件，并在父组件中调用名为setLayout的方法。 

        1、事件传递机制：
        在Vue.js组件中，可以使用$emit方法来触发自定义事件，并通过父组件监听这些事件来执行相应的逻辑。
        2、navbar组件的定义：
        navbar组件内部可能会在某些情况下使用emits('setLayout')来触发setLayout事件。
        3、父组件的事件监听：
        父组件使用@setLayout="setLayout"来监听这个事件，当navbar组件触发setLayout事件时，父组件中的setLayout方法就会被调用。
        
        这种方式使得子组件能够通过触发自定义事件与父组件通信，父组件可以监听这些事件并在事件被触发时执行相应的操作。
        这是一种松散耦合的通信方式，非常适合在复杂应用中使用。
        -->
        <navbar @setLayout="setLayout" />
        <!-- 标签视图组件，只有在needTagsView为true时才显示 -->
        <tags-view v-if="needTagsView" />
      </div>
      <!-- 主要内容区域组件 -->
      <app-main />
      <!-- 设置组件，通过ref属性可以在父组件中引用这个组件 -->
      <settings ref="settingRef" />
    </div>
  </div>
</template>

<script setup name="Layout">
import { useWindowSize } from '@vueuse/core'
import Sidebar from './components/Sidebar/index.vue'
import { AppMain, Navbar, Settings, TagsView } from './components'
import defaultSettings from '@/settings'

import useAppStore from '@/store/modules/app'
import useSettingsStore from '@/store/modules/settings'

const settingsStore = useSettingsStore()
const theme = computed(() => settingsStore.theme);
const sideTheme = computed(() => settingsStore.sideTheme);
const sidebar = computed(() => useAppStore().sidebar);
const device = computed(() => useAppStore().device);
const needTagsView = computed(() => settingsStore.tagsView);
const fixedHeader = computed(() => settingsStore.fixedHeader);

const classObj = computed(() => ({
  hideSidebar: !sidebar.value.opened,
  openSidebar: sidebar.value.opened,
  withoutAnimation: sidebar.value.withoutAnimation,
  mobile: device.value === 'mobile'
}))

const { width, height } = useWindowSize();
const WIDTH = 992; // refer to Bootstrap's responsive design

watchEffect(() => {
  if (device.value === 'mobile' && sidebar.value.opened) {
    useAppStore().closeSideBar({ withoutAnimation: false })
  }
  if (width.value - 1 < WIDTH) {
    useAppStore().toggleDevice('mobile')
    useAppStore().closeSideBar({ withoutAnimation: true })
  } else {
    useAppStore().toggleDevice('desktop')
  }
})

function handleClickOutside() {
  useAppStore().closeSideBar({ withoutAnimation: false })
}

const settingRef = ref(null);
function setLayout() {
  // Navbar点击布局设置触发setLayout() -> 调用emits方法触发setLayout事件 -> @setLayout="setLayout"监听到此事件触发当前setLayout()
  // -> Setting触发openSetting()将showSettings改为true，布局设置显示
  // 子 -> 父 -> 子
  settingRef.value.openSetting();
}
</script>

<style lang="scss" scoped>
@import "@/assets/styles/mixin.scss";
@import "@/assets/styles/variables.module.scss";

.app-wrapper {
  @include clearfix;
  position: relative;
  height: 100%;
  width: 100%;

  &.mobile.openSidebar {
    position: fixed;
    top: 0;
  }
}

.drawer-bg {
  background: #000;
  opacity: 0.3;
  width: 100%;
  top: 0;
  height: 100%;
  position: absolute;
  z-index: 999;
}

.fixed-header {
  position: fixed;
  top: 0;
  right: 0;
  z-index: 9;
  width: calc(100% - #{$base-sidebar-width});
  transition: width 0.28s;
}

.hideSidebar .fixed-header {
  width: calc(100% - 54px);
}

.sidebarHide .fixed-header {
  width: 100%;
}

.mobile .fixed-header {
  width: 100%;
}
</style>