import useTagsViewStore from '@/store/modules/tagsView'
import router from '@/router'

export default {
  /**
   * 刷新当前tab页签
   */
  refreshPage(obj) {
    // 从当前路由中解构出 path, query 和 matched
    const { path, query, matched } = router.currentRoute.value;
    if (obj === undefined) {  // 如果 obj 未定义，从当前路由中提取信息生成 obj
      matched.forEach((m) => {
        if (m.components && m.components.default && m.components.default.name) {
          // 排除 Layout 和 ParentView 这两个特定的组件
          if (!['Layout', 'ParentView'].includes(m.components.default.name)) {
            obj = { name: m.components.default.name, path: path, query: query };
          }
        }
      });
    }
    // 删除缓存的视图，然后重定向以刷新页面
    return useTagsViewStore().delCachedView(obj).then(() => {
      const { path, query } = obj
      router.replace({
        path: '/redirect' + path,
        query: query
      })
    })
  },
  /**
   * 关闭当前tab页签，打开新页签
   */
  closeOpenPage(obj) {
    useTagsViewStore().delView(router.currentRoute.value);
    if (obj !== undefined) {
      return router.push(obj);
    }
  },
  /**
   * 关闭指定tab页签
   */
  closePage(obj) {
    if (obj === undefined) {  // 删除当前页面的视图，并在删除后导航到最近访问的视图或主页
      return useTagsViewStore().delView(router.currentRoute.value).then(({ visitedViews }) => {
        const latestView = visitedViews.slice(-1)[0]  //  获取最近访问的视图（数组中的最后一个元素）
        if (latestView) {
          return router.push(latestView.fullPath)
        }
        return router.push('/');
      });
    }
    return useTagsViewStore().delView(obj);  // 删除指定的视图
  },
  /**
   * 关闭所有tab页签
   */
  closeAllPage() {
    return useTagsViewStore().delAllViews();
  },
  // 关闭左侧tab页签
  closeLeftPage(obj) {
    return useTagsViewStore().delLeftTags(obj || router.currentRoute.value);
  },
  // 关闭右侧tab页签
  closeRightPage(obj) {
    return useTagsViewStore().delRightTags(obj || router.currentRoute.value);
  },
  // 关闭其他tab页签
  closeOtherPage(obj) {
    return useTagsViewStore().delOthersViews(obj || router.currentRoute.value);
  },
  // 打开tab页签
  openPage(url) {
    return router.push(url);
  },
  // 修改tab页签
  updatePage(obj) {
    return useTagsViewStore().updateVisitedView(obj);
  }
}
