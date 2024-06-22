// 路由鉴权：路由组件访问权限设置
import router from './router'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'
// 引入进度条样式
import 'nprogress/nprogress.css'
import { getToken } from '@/utils/auth'
import { isHttp } from '@/utils/validate'
import { isRelogin } from '@/utils/request'
import useUserStore from '@/store/modules/user'
import useSettingsStore from '@/store/modules/settings'
import usePermissionStore from '@/store/modules/permission'

NProgress.configure({ showSpinner: false });  // 取消加载转圈显示

const whiteList = ['/login', '/register'];

// 全局守卫：项目中任意路由切换都会触发的钩子 hook
// 全局前置守卫：访问某个路由前的守卫 to：将要访问的路由对象 from：从哪个路由而来 next：路由的放行函数
router.beforeEach((to, from, next) => {
  NProgress.start()
  if (getToken()) {  // 已登录状态
    to.meta.title && useSettingsStore().setTitle(to.meta.title)  // 设置页面标题
    /* has token*/
    if (to.path === '/login') {
      next({ path: '/' })  // 重定向到主页
      NProgress.done()
    }
    else if (whiteList.indexOf(to.path) !== -1) {  // 检查当前路径是否在免登录白名单中。如果是，直接调用next()继续路由跳转
      next()
    }
    else {
      if (useUserStore().roles.length === 0) {
        isRelogin.show = true
        // 判断当前用户是否已拉取完user_info信息
        useUserStore().getInfo().then(() => {
          isRelogin.show = false
          usePermissionStore().generateRoutes().then(accessRoutes => {  // rewriteRoutes = filterAsyncRouter(rdata, false, true)
            // console.log('accessRoutes')
            // console.log(accessRoutes)
            // 根据roles权限生成可访问的路由表
            accessRoutes.forEach(route => {
              if (!isHttp(route.path)) {
                router.addRoute(route) // 动态添加可访问路由表
              }
            })
            /**
             * 将用户重定向到他们试图访问的路由，但在浏览器的历史记录中不保留前一个路由记录，避免可能的重复导航。
             * 这种做法在处理登录重定向或在表单提交后防止重复提交时非常有用。
             * 在 next({ ...to, replace: true }) 中，用户将被重定向到 to 对象中指定的路由。这里的 to 对象代表着目标路由的所有信息，包括路径、查询参数、哈希值等。
             * 具体来说：
             * 路径（path）：to.path 指定了用户试图访问的路径。比如，如果用户试图访问 /dashboard，那么 to.path 将是 /dashboard。
             * 查询参数（query）：如果在导航时包含了查询参数（例如 /search?query=example），这些参数也会在 to 对象中。
             * 哈希值（hash）：如果有哈希值（如 /path#section1），这也会被包括在内。
             * 
             * 使用 next({ ...to, replace: true }) 相比于简单地调用 next()，主要的差别在于它通过 replace: true 选项改变了路由的导航方式。
             * 这会导致新的路由替换当前历史记录中的条目，而不是向历史记录添加一个新条目。
             * 
             * 在Vue Router的路由守卫中，next() 函数用来控制导航流程，可以接受几种不同形式的参数：
             * next()：无参数调用，直接允许继续当前的导航。
             * next(false)：终止当前的导航。
             * next('/path') 或 next({ path: '/path' })：重定向到一个不同的地址。
             * next(error)：如果传入参数是一个Error实例，则导航会被终止并且该错误会被传递给路由器的错误处理回调。
             * next({ ...to, replace: true })：允许继续到目标路由 to，并使用 replace: true 来替换历史记录条目。
             */
            next({ ...to, replace: true }) // 确保addRoutes已完成
          })
        }).catch(err => {
          useUserStore().logOut().then(() => {
            ElMessage.error(err)
            next({ path: '/login', query: { redirect: to.path } })
          })
        })
      }
      else {
        next()
      }
    }
  }
  else {
    // 没有token
    if (whiteList.indexOf(to.path) !== -1) {
      // 在免登录白名单，直接进入
      next()
    } else {
      next(`/login?redirect=${to.fullPath}`) // 否则全部重定向到登录页
      NProgress.done()
    }
  }
})

// 全局后置守卫：只有前置守卫放行路由后才会触发
router.afterEach(() => {
  NProgress.done()
})
