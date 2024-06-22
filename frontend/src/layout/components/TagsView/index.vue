<template>
  <div id="tags-view-container" class="tags-view-container">
    <!-- 滚动滚轮时会关闭当前已打开的右键菜单 -->
    <scroll-pane ref="scrollPaneRef" class="tags-view-wrapper" @scroll="handleScroll">
      <!-- 
      v-for="tag in visitedViews"：遍历 visitedViews 数组，为每个 tag 创建一个 router-link。
      :key="tag.path"：使用 tag.path 作为每个 router-link 的唯一键。
      :data-path="tag.path"：为每个 router-link 添加 data-path 属性，值为 tag.path。
      :class="isActive(tag) ? 'active' : ''"：根据 isActive(tag) 的返回值设置 router-link 的 CSS 类。如果标签是激活的，添加 active 类。
      :to="{ path: tag.path, query: tag.query, fullPath: tag.fullPath }"：设置 router-link 的目标路由，包括路径、查询参数和完整路径。
      class="tags-view-item"：为每个 router-link 添加 tags-view-item 类，用于样式。
      :style="activeStyle(tag)"：根据标签状态应用样式。
      @click.middle="!isAffix(tag) ? closeSelectedTag(tag) : ''"：如果点击中键且标签不是固定的，调用 closeSelectedTag(tag) 关闭标签。
      @contextmenu.prevent="openMenu(tag, $event)"：右键点击时阻止默认上下文菜单，并调用 openMenu(tag, $event) 打开自定义菜单。

      在 Vue.js 中，.prevent 是一个事件修饰符，用于阻止事件的默认行为。
      此处 .prevent 修饰符用于阻止右键菜单的默认行为，即浏览器默认的上下文菜单，显示自定义的菜单。
       -->
      <router-link v-for="tag in visitedViews" :key="tag.path" :data-path="tag.path"
        :class="isActive(tag) ? 'active' : ''" :to="{ path: tag.path, query: tag.query, fullPath: tag.fullPath }"
        class="tags-view-item" :style="activeStyle(tag)" @click.middle="!isAffix(tag) ? closeSelectedTag(tag) : ''"
        @contextmenu.prevent="openMenu(tag, $event)">
        {{ tag.title }}
        <!-- 如果标签不是固定的，显示关闭按钮，点击关闭按钮时调用 closeSelectedTag(tag) 并阻止事件冒泡。
         如果不用 prevent 阻止默认行为：点击关闭按钮不会删除 Tag，而是将该 Tag 作为当前 Tag
         .stop 修饰符用于阻止事件的传播（冒泡）。当事件触发时，它会停止向父级元素传播，避免父级元素上绑定的同一事件处理程序被调用。 -->

        <!-- 
         何时使用 .prevent 和 .stop：
        .prevent：阻止默认行为
        1、希望阻止浏览器执行事件的默认行为。例如：
            阻止表单提交导致的页面刷新。
            阻止点击链接导致的页面跳转。
            阻止右键点击打开默认上下文菜单。
        .stop：阻止事件冒泡
        2、希望阻止事件向父级元素传播。例如：
            在嵌套的元素中，只希望处理子元素的点击事件，而不希望父元素的点击事件被触发。
            在自定义组件中，只处理组件内部的事件，而不触发外部的事件监听器。
         -->
        <span v-if="!isAffix(tag)" @click.prevent.stop="closeSelectedTag(tag)">
          <close class="el-icon-close" style="width: 1em; height: 1em;vertical-align: middle;" />
        </span>
      </router-link>
    </scroll-pane>
    <!-- 
    <ul> 标签定义无序（带项目符号）列表。
    <li> 标签定义列表项。

    显示菜单：
    将 visible.value 设置为 true，使菜单可见。
    将 selectedTag.value 设置为当前右键点击的标签 tag。

    菜单的显示：
    <ul v-show="visible" 根据 visible 的值决定菜单的显示与否。
    :style="{ left: left + 'px', top: top + 'px' }" 动态设置菜单的位置，使其显示在鼠标点击的位置。
     -->
    <ul v-show="visible" :style="{ left: left + 'px', top: top + 'px' }" class="contextmenu">
      <li @click="refreshSelectedTag(selectedTag)">
        <refresh-right style="width: 1em; height: 1em;" /> 刷新页面
      </li>
      <li v-if="!isAffix(selectedTag)" @click="closeSelectedTag(selectedTag)">
        <close style="width: 1em; height: 1em;" /> 关闭当前
      </li>
      <li @click="closeOthersTags">
        <circle-close style="width: 1em; height: 1em;" /> 关闭其他
      </li>
      <li v-if="!isFirstView()" @click="closeLeftTags">
        <back style="width: 1em; height: 1em;" /> 关闭左侧
      </li>
      <li v-if="!isLastView()" @click="closeRightTags">
        <right style="width: 1em; height: 1em;" /> 关闭右侧
      </li>
      <li @click="closeAllTags(selectedTag)">
        <circle-close style="width: 1em; height: 1em;" /> 全部关闭
      </li>
    </ul>
  </div>
</template>

<script setup name="TagsView">
import ScrollPane from './ScrollPane'
import { getNormalPath } from '@/utils/ruoyi'
import useTagsViewStore from '@/store/modules/tagsView'
import useSettingsStore from '@/store/modules/settings'
import usePermissionStore from '@/store/modules/permission'

const visible = ref(false);  // 控制右键菜单的显示与隐藏
const top = ref(0);  // 右键菜单顶部位置
const left = ref(0);  // 右键菜单的左侧位置
const selectedTag = ref({});
const affixTags = ref([]);
const scrollPaneRef = ref(null);

const { proxy } = getCurrentInstance();
/**
 * 返回当前激活的路由对象
 * 包含的信息：
 * path：当前路由的路径。
 * params：当前路由的参数。
 * query：当前路由的查询参数。
 * name：当前路由的名称。
 * meta：当前路由的元数据。
 * 其他与当前路由状态相关的信息。
 */
const route = useRoute();
/**
 * 返回路由器实例对象，该对象包含用于导航的多种方法和属性
 * push(location)：导航到一个新的路由。
 * replace(location)：替换当前路由。
 * go(n)：在路由历史中前进或后退 n 步。
 * 其他用于编程式导航和路由管理的方法。
 */
const router = useRouter();

const visitedViews = computed(() => useTagsViewStore().visitedViews);
const routes = computed(() => usePermissionStore().routes);
const theme = computed(() => useSettingsStore().theme);

onMounted(() => {
  initTags()
  addTags()
})
/**
 * 从一个路由配置数组中筛选出带有 affix 元数据的路由，并将它们的信息整理成一个新的数组返回。（只有Layout）
 * 
 * 具体来说，它会递归地遍历每个路由及其子路由，找到带有 affix 元数据的路由，并将这些路由的信息（包括全路径、路径、名称和元数据）存储在一个 tags 数组中。
 * @param {*} routes 路由配置数组
 * @param {*} basePath 当前根路径
 */
function filterAffixTags(routes, basePath = '') {
  let tags = []
  routes.forEach(route => {
    if (route.meta && route.meta.affix) {
      const tagPath = getNormalPath(basePath + '/' + route.path)
      tags.push({
        fullPath: tagPath,
        path: tagPath,
        name: route.name,
        meta: { ...route.meta }
      })
    }
    if (route.children) {
      const tempTags = filterAffixTags(route.children, route.path)
      if (tempTags.length >= 1) {
        tags = [...tags, ...tempTags]  // 将 tempTags 中的元素添加到 tags 数组中的方法
      }
    }
  })
  return tags
}
function initTags() {
  const res = filterAffixTags(routes.value);
  affixTags.value = res;
  for (const tag of res) {
    // Must have tag name
    if (tag.name) {
      useTagsViewStore().addVisitedView(tag)
    }
  }
}
function addTags() {
  const { name } = route
  if (name) {
    useTagsViewStore().addView(route)
    if (route.meta.link) {
      useTagsViewStore().addIframeView(route);
    }
  }
  return false
}

function isActive(r) {
  return r.path === route.path
}
function activeStyle(tag) {
  if (!isActive(tag)) return {};
  return {
    "background-color": theme.value,
    "border-color": theme.value
  };
}
function isAffix(tag) {
  return tag.meta && tag.meta.affix
}

/**
 * 判断是否为首页或除首页外第一个
 */
function isFirstView() {
  try {
    return selectedTag.value.fullPath === '/index' || selectedTag.value.fullPath === visitedViews.value[1].fullPath
  } catch (err) {
    return false
  }
}
/**
 * 判断是否为最后一个
 */
function isLastView() {
  try {
    return selectedTag.value.fullPath === visitedViews.value[visitedViews.value.length - 1].fullPath
  } catch (err) {
    return false
  }
}

watch(route, () => {
  addTags()
  moveToCurrentTag()
})
watch(visible, (value) => {
  if (value) {
    document.body.addEventListener('click', closeMenu)
  } else {
    document.body.removeEventListener('click', closeMenu)
  }
})
function moveToCurrentTag() {
  /**
   * nextTick 用于在下一个 DOM 更新周期之后执行回调函数。这意味着在当前的 DOM 更新完成后，nextTick 内的代码才会被执行。
   * 这对于确保在操作或访问 DOM 时，所有的绑定、更新和渲染已经完成是非常重要的（保证 visitedViews.value 已经更新）
   * 这样可以避免在 DOM 还没有完全更新时进行操作，防止出现数据不一致或视图渲染不正确的问题。
   * 
   * 需要使用 nextTick 的场景：
   * 1、DOM 操作：当需要确保在操作或访问 DOM 元素之前，Vue 的更新已经完成。例如，滚动到某个元素，计算元素的大小或位置等。
   * 2、依赖数据更新：当逻辑依赖于 Vue 的响应式数据更新，并且需要在数据更新之后执行某些操作时。
   * 不需要使用 nextTick 的场景：
   * 1、简单的逻辑判断：如果代码仅仅是进行简单的逻辑判断或数据处理，而不涉及 DOM 操作或复杂的响应式数据更新，则不需要使用 nextTick。
   * 2、立即执行的操作：当操作不依赖于 Vue 的更新周期，且不需要等待 DOM 更新时。
   */
  nextTick(() => {
    for (const r of visitedViews.value) {
      if (r.path === route.path) {
        scrollPaneRef.value.moveToTarget(r);
        // when query is different then update
        if (r.fullPath !== route.fullPath) {
          useTagsViewStore().updateVisitedView(route)
        }
      }
    }
  })
}

// -------------------- plugins/tab.js + modules/tagsView.js --------------------
// 刷新页面
function refreshSelectedTag(view) {
  // console.log(proxy)
  proxy.$tab.refreshPage(view);  // 刷新当前选中的标签页
  if (route.meta.link) {  // 如果当前路由的元数据中包含链接，则删除 iframe 视图
    useTagsViewStore().delIframeView(route);
  }
}
// 关闭当前：如果未激活-关闭，若已激活-当前页面跳转到最后
function closeSelectedTag(view) {
  proxy.$tab.closePage(view).then(({ visitedViews }) => {
    if (isActive(view)) {
      toLastView(visitedViews, view)
    }
  })
}
// 关闭右侧
function closeRightTags() {
  proxy.$tab.closeRightPage(selectedTag.value).then(visitedViews => {
    // 检查当前路由是否在剩余的访问视图中。如果当前路由不在其中，它会导航到最近访问的视图
    if (!visitedViews.find(i => i.fullPath === route.fullPath)) {
      toLastView(visitedViews)
    }
  })
}
// 关闭左侧
function closeLeftTags() {
  proxy.$tab.closeLeftPage(selectedTag.value).then(visitedViews => {
    if (!visitedViews.find(i => i.fullPath === route.fullPath)) {
      toLastView(visitedViews)
    }
  })
}
// 关闭其他
function closeOthersTags() {
  router.push(selectedTag.value).catch(() => { });  // 导航到当前选中的标签页
  proxy.$tab.closeOtherPage(selectedTag.value).then(() => {
    moveToCurrentTag()  // 确保视图滚动到当前标签页
  })
}
// 全部关闭
function closeAllTags(view) {
  proxy.$tab.closeAllPage().then(({ visitedViews }) => {
    // 如果当前路径在 affixTags 中，什么都不做
    if (affixTags.value.some(tag => tag.path === route.path)) {
      return
    }
    toLastView(visitedViews, view)
  })
}
function toLastView(visitedViews, view) {
  const latestView = visitedViews.slice(-1)[0]
  if (latestView) {
    router.push(latestView.fullPath)
  } else {
    // now the default is to redirect to the home page if there is no tags-view,
    // you can adjust it according to your needs.
    if (view.name === 'Dashboard') {
      // to reload home page
      router.replace({ path: '/redirect' + view.fullPath })
    } else {
      router.push('/')
    }
  }
}

/**
 * 右键点击某个元素，打开一个上下文菜单以执行相关操作，确保菜单在用户点击位置打开且不超出容器的边界。
 * 
 * 假设容器宽度是 500px，菜单最小宽度是 105px，鼠标点击位置相对于视口的水平位置是 450px。
 * offsetLeft 是容器相对于视口左边缘的距离，假设是 50px。
 * offsetWidth 是容器的宽度，500px。
 * maxLeft 是 500px - 105px = 395px。
 * 鼠标点击位置相对于容器左边缘的位置是 450px - 50px + 15px = 415px。
 * 因为 415px 超过了 maxLeft 的 395px，所以菜单的左侧位置被设置为 395px，确保菜单不会超出容器的右边界。
 */
function openMenu(tag, e) {
  const menuMinWidth = 105
  const offsetWidth = proxy.$el.offsetWidth   // 获取容器的宽度，用于确定菜单的位置边界
  const maxLeft = offsetWidth - menuMinWidth   // 计算菜单在容器内的最大左侧位置，以防止菜单超出容器的右边界
  const offsetLeft = proxy.$el.getBoundingClientRect().left  // 获取容器相对于视口左边缘的距离，用于计算菜单的水平位置
  const l = e.clientX - offsetLeft + 15  // 计算鼠标点击位置相对于容器的左侧位置，并向右偏移 15 像素
  if (l > maxLeft) {
    left.value = maxLeft
  } else {
    left.value = l
  }
  top.value = e.clientY  // 将菜单的顶部位置设置为鼠标点击位置的垂直坐标
  visible.value = true
  selectedTag.value = tag
}
/**
 * 关闭右键菜单
 */
function closeMenu() {
  visible.value = false
}

/**
 * 滚动滚轮事件
 */
function handleScroll() {
  closeMenu()
}
</script>

<style lang='scss' scoped>
.tags-view-container {
  height: 34px;
  width: 100%;
  background: #fff;
  border-bottom: 1px solid #d8dce5;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.12), 0 0 3px 0 rgba(0, 0, 0, 0.04);

  .tags-view-wrapper {
    .tags-view-item {
      display: inline-block;
      position: relative;
      cursor: pointer;
      height: 26px;
      line-height: 26px;
      border: 1px solid #d8dce5;
      color: #495060;
      background: #fff;
      padding: 0 8px;
      font-size: 12px;
      margin-left: 5px;
      margin-top: 4px;

      &:first-of-type {
        margin-left: 15px;
      }

      &:last-of-type {
        margin-right: 15px;
      }

      &.active {
        background-color: #42b983;
        color: #fff;
        border-color: #42b983;

        // 现代 CSS 规范推荐使用双冒号 :: 来区分伪元素，而单冒号 : 用于伪类。
        // 伪类（Pseudo-class）：用于选择元素的特定状态。例如，:hover 选择鼠标悬停状态的元素。
        // 伪元素（Pseudo-element）：用于创建和样式化页面中实际不存在的部分。例如，::before 和 ::after 允许在元素内容之前或之后插入内容。
        // 伪元素 ::before，用于在选定元素的内容之前插入一个自定义的装饰性元素
        // 实际效果：在右击菜单的每项前添加一个白色小圆点
        &::before {
          // 生成一个空内容的伪元素
          content: "";
          // 设置伪元素的背景颜色。
          background: #fff;
          // inline-block，使伪元素具有块级元素的特性，但仍与其他行内元素在同一行显示
          display: inline-block;
          width: 8px;
          height: 8px;
          border-radius: 50%;
          position: relative;
          margin-right: 5px;
        }
      }
    }
  }

  .contextmenu {
    margin: 0;
    background: #fff;
    z-index: 3000;
    position: absolute;
    list-style-type: none;
    padding: 5px 0;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 400;
    color: #333;
    box-shadow: 2px 2px 3px 0 rgba(0, 0, 0, 0.3);

    li {
      margin: 0;
      padding: 7px 16px;
      cursor: pointer;

      &:hover {
        background: #eee;
      }
    }
  }
}
</style>

<style lang="scss">
//reset element css of el-icon-close
.tags-view-wrapper {
  .tags-view-item {
    .el-icon-close {
      width: 16px;
      height: 16px;
      vertical-align: 2px;
      border-radius: 50%;
      text-align: center;
      transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
      transform-origin: 100% 50%;

      &:before {
        transform: scale(0.6);
        display: inline-block;
        vertical-align: -3px;
      }

      &:hover {
        background-color: #b4bccc;
        color: #fff;
        width: 12px !important;
        height: 12px !important;
      }
    }
  }
}
</style>