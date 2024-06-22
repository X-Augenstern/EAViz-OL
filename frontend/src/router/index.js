// 通过vue-router实现模板路由配置
import { createRouter, createWebHistory } from "vue-router";
import { constantRoutes } from "./routes";

// 创建路由器
const router = createRouter({
  // 路由模式
  history: createWebHistory(),
  routes: constantRoutes,
  // 滚动行为：滚动时水平、垂直方向均归零
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
});

// 暴露router
export default router;