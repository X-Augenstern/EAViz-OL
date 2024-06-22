<template>
  <div class="sidebar-logo-container" :class="{ 'collapse': collapse }"
    :style="{ backgroundColor: sideTheme === 'theme-dark' ? variables.menuBackground : variables.menuLightBackground }">
    <!-- <transition> 是一个用于包装元素或组件，以便为它们添加进入和离开过渡效果的组件。name="sidebarLogoFade" 是一个用于指定过渡效果名称的属性
      <transition> 组件可以为进入和离开 DOM 的元素或组件添加过渡效果。它会在元素或组件的进入和离开时应用 CSS 类，允许定义不同状态下的样式。

      name 属性用于指定过渡效果的名称。Vue.js 会根据这个名称生成一组 CSS 类，用于在不同的过渡阶段应用样式。
      假设 name="sidebarLogoFade"，Vue.js 会生成以下 CSS 类：
      
      进入阶段
      sidebarLogoFade-enter-from （或简写为enter）: 定义进入时的起始状态（通常是隐藏或透明）。
      sidebarLogoFade-enter-active: 定义进入时的过渡效果。
      sidebarLogoFade-enter-to: 定义进入时的结束状态（通常是显示或不透明）。
      
      离开阶段
      sidebarLogoFade-leave-from: 定义离开时的起始状态（通常是显示或不透明）。
      sidebarLogoFade-leave-active: 定义离开时的过渡效果。
      sidebarLogoFade-leave-to: 定义离开时的结束状态（通常是隐藏或透明）。
    -->
    <transition name="sidebarLogoFade">
      <router-link v-if="collapse" key="collapse" class="sidebar-logo-link" to="/">
        <img v-if="logo_path" :src="logo_path" class="sidebar-logo" />
        <h1 v-else class="sidebar-title"
          :style="{ color: sideTheme === 'theme-dark' ? variables.logoTitleColor : variables.logoLightTitleColor }">{{
            title }}</h1>
      </router-link>
      <router-link v-else key="expand" class="sidebar-logo-link" to="/">
        <img v-if="logo_path" :src="logo_path" class="sidebar-logo" />
        <h1 class="sidebar-title"
          :style="{ color: sideTheme === 'theme-dark' ? variables.logoTitleColor : variables.logoLightTitleColor }">{{
            title }}</h1>
      </router-link>
    </transition>
  </div>
</template>

<script setup name="Logo">
import variables from '@/assets/styles/variables.module.scss'
import useSettingsStore from '@/store/modules/settings'

defineProps({
  collapse: {
    type: Boolean,
    required: true
  }
})

const title = import.meta.env.VITE_APP_TITLE;
const logo_path = import.meta.env.VITE_APP_LOGO;
const settingsStore = useSettingsStore();
const sideTheme = computed(() => settingsStore.sideTheme);
</script>

<style lang="scss" scoped>
.sidebarLogoFade-enter-active {
  transition: opacity 1.5s;
}

.sidebarLogoFade-enter,
.sidebarLogoFade-leave-to {
  opacity: 0;
}

.sidebar-logo-container {
  position: relative;
  width: 100%;
  height: 50px;
  line-height: 50px;
  background: #2b2f3a;
  text-align: center;
  overflow: hidden;

  & .sidebar-logo-link {
    height: 100%;
    width: 100%;

    & .sidebar-logo {
      width: 32px;
      height: 32px;
      vertical-align: middle;
      margin-right: 20px;
    }

    & .sidebar-title {
      display: inline-block;
      margin: 0;
      color: #fff;
      font-weight: 600;
      line-height: 50px;
      font-size: 18px;
      font-family: Avenir, Helvetica Neue, Arial, Helvetica, sans-serif;
      vertical-align: middle;
      margin-top: 5px;
    }
  }

  &.collapse {
    .sidebar-logo {
      margin-right: 0px;
    }
  }
}
</style>