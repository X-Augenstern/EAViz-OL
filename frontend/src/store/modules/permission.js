import auth from '@/plugins/auth'
import { constantRoutes, dynamicRoutes } from '@/router/routes'
import router from '@/router'
import { getRouters } from '@/api/menu'
import Layout from '@/layout/index'
import ParentView from '@/components/ParentView'
import InnerLink from '@/layout/components/InnerLink'

const usePermissionStore = defineStore(
  'permission',
  {
    state: () => ({
      routes: [],  // 存储当前用户可访问的路由数组      filterAsyncRouter(rdata, false, true)
      addRoutes: [],  // 添加的路由数组                 filterAsyncRouter(rdata, false, true) + constantRoutes
      defaultRoutes: [],  // 默认路由数组               同sidebarRouters
      topbarRouters: [],  // 顶部导航栏使用的路由数组   filterAsyncRouter(defaultData)
      sidebarRouters: []  // 侧边栏使用的路由数组       在topbarRouters + constantRoutes
    }),
    actions: {
      setRoutes(routes) {
        this.addRoutes = routes
        this.routes = constantRoutes.concat(routes)  // 设置用户可访问的路由，并合并常量路由
      },
      setDefaultRoutes(routes) {
        this.defaultRoutes = constantRoutes.concat(routes)  // 设置默认的路由列表，并合并常量路由
      },
      setTopbarRoutes(routes) {
        this.topbarRouters = routes
      },
      setSidebarRouters(routes) {
        this.sidebarRouters = routes
      },
      generateRoutes(roles) {  // 动态生成和设置路由
        /**
         * 在JavaScript中，resolve是Promise对象中使用的一个函数，
         * 它的主要用途是在异步操作成功完成时改变Promise的状态从"pending（等待中）"到"fulfilled（已完成）"。
         * 当创建一个新的Promise时，会提供一个执行器（executor）函数，这个函数接受两个参数：resolve和reject。
         * 这两个参数也是函数，用于在异步操作成功时调用resolve，或在发生错误时调用reject。
         * 
         * 1. 改变Promise状态：
         * 使用resolve可以标记Promise为成功完成，其参数会作为Promise的结果传递给后续的.then()处理程序。
         * 2. 传递数据：
         * 可以通过resolve函数传递数据，这些数据可以在Promise链中的下一个.then()回调中被接收和处理。
         * 3. 链接Promise：
         * 如果resolve的参数是另一个Promise，那么当前Promise的状态将由这个新Promise的状态决定。这允许你将多个异步操作串联起来。
         * 
          eg：
            function fetchData() {  // 返回一个新的Promise
              return new Promise((resolve, reject) => {
                setTimeout(() => {  // 模拟异步操作，一秒后执行。一秒后，调用resolve(data)改变Promise的状态，并将data对象作为结果传递
                  const data = { message: "Hello, World!" };
                  resolve(data);  // 将Promise状态改变为fulfilled，并传递data对象
                }, 1000);
              });
            }

            fetchData().then(data => {  // 使用.then()处理Promise结果，打印从resolve传递的消息
              console.log(data.message);  // 输出: Hello, World!
            });
        */
        return new Promise(resolve => {
          // 向后端请求路由数据
          getRouters().then(res => {  // 从服务器获取路由数据
            // console.log(res);
            // data: Array(3)
            // 0: {name: 'System', hidden: false, component: 'Layout', path: '/system', redirect: 'noRedirect', …}
            //    alwaysShow: true
            //    children: Array(9)
            //        0: {name: 'User', path: 'user', query: '', hidden: false, component: 'system/user/index', …}
            //        1: {name: 'Role', path: 'role', query: '', hidden: false, component: 'system/role/index', …}
            //        2: {name: 'Menu', path: 'menu', query: '', hidden: false, component: 'system/menu/index', …}
            //        3: {name: 'Dept', path: 'dept', query: '', hidden: false, component: 'system/dept/index', …}
            //        4: {name: 'Post', path: 'post', query: '', hidden: false, component: 'system/post/index', …}
            //        5: {name: 'Dict', path: 'dict', query: '', hidden: false, component: 'system/dict/index', …}
            //        6: {name: 'Config', path: 'config', query: '', hidden: false, component: 'system/config/index', …}
            //        7: {name: 'Notice', path: 'notice', query: '', hidden: false, component: 'system/notice/index', …}
            //        8: {name: 'Log', hidden: false, component: 'ParentView', path: 'log', redirect: 'noRedirect', …}
            //    component: "Layout"
            //    hidden: false
            //    meta: {title: '系统管理', icon: 'system', noCache: true, link: null}
            //    name: "System"
            //    path: "/system"
            //    redirect: "noRedirect"
            // 1: {name: 'Monitor', hidden: false, component: 'Layout', path: '/monitor', redirect: 'noRedirect', …}
            //    alwaysShow: true
            //    children: Array(6)
            //        0: {name: 'Online', path: 'online', query: '', hidden: false, component: 'monitor/online/index', …}
            //        1: {name: 'Job', path: 'job', query: '', hidden: false, component: 'monitor/job/index', …}
            //        2: {name: 'Druid', path: 'druid', query: '', hidden: false, component: 'monitor/druid/index', …}
            //        3: {name: 'Server', path: 'server', query: '', hidden: false, component: 'monitor/server/index', …}
            //        4: {name: 'Cache', path: 'cache', query: '', hidden: false, component: 'monitor/cache/index', …}
            //        5: {name: 'Cachelist', path: 'cacheList', query: '', hidden: false, component: 'monitor/cache/list', …}
            //    component: "Layout"
            //    hidden: false
            //    meta: {title: '系统监控', icon: 'monitor', noCache: true, link: null}
            //    name: "Monitor"
            //    path: "/monitor"
            //    redirect: "noRedirect"
            // 2: {name: 'Tool', hidden: false, component: 'Layout', path: '/tool', redirect: 'noRedirect', …}
            //    alwaysShow: true
            //    children: Array(3)
            //        0: {name: 'Build', path: 'build', query: '', hidden: false, component: 'tool/build/index', …}
            //        1: {name: 'Gen', path: 'gen', query: '', hidden: false, component: 'tool/gen/index', …}
            //        2: {name: 'Swagger', path: 'swagger', query: '', hidden: false, component: 'tool/swagger/index', …}
            //    component: "Layout"
            //    hidden: false
            //    meta: {title: '系统工具', icon: 'tool', noCache: true, link: null}
            //    name: "Tool"
            //    path: "/tool"
            //    redirect: "noRedirect"

            // 实现深拷贝（deep copy）一个对象。这是一个简单但有效的方法来创建一个对象的完整副本，与原始数据互不影响
            // JSON.stringify：这个函数将一个JavaScript对象转换成一个JSON字符串。这个过程中，对象里的数据（包括其嵌套结构）被完整地序列化成字符串。
            // JSON.parse：这个函数将JSON字符串解析回JavaScript对象。这个过程创建了原始数据的一个全新副本，因为它是基于字符串的内容构建的，而不是原始数据的引用。
            const sdata = JSON.parse(JSON.stringify(res.data))
            const rdata = JSON.parse(JSON.stringify(res.data))
            const defaultData = JSON.parse(JSON.stringify(res.data))
            const sidebarRoutes = filterAsyncRouter(sdata)
            // console.log(sidebarRoutes)
            const rewriteRoutes = filterAsyncRouter(rdata, false, true)
            // console.log(rewriteRoutes)
            const defaultRoutes = filterAsyncRouter(defaultData)
            // console.log(defaultData)

            // 在JavaScript中，对象之间的比较是基于它们的引用（即内存地址），而不是它们的内容
            // js会检查这两个对象是否是同一个内存地址的引用。即使两个对象的所有属性和值都完全相同，只要它们不是同一个对象的引用，
            // == 与 === 的比较结果就是 false
            // 如果需要比较两个对象的内容是否相同，需要使用深度比较方法
            // console.log(sdata == defaultData)
            // console.log(sidebarRoutes === defaultRoutes)
            const asyncRoutes = filterDynamicRoutes(dynamicRoutes)
            // console.log('asyncRoutes')
            // console.log(asyncRoutes)
            // 0: {path: '/system/user-auth', component: {…}, hidden: true, permissions: Array(1), children: Array(1)}
            // 1: {path: '/system/role-auth', component: {…}, hidden: true, permissions: Array(1), children: Array(1)}
            // 2: {path: '/system/dict-data', component: {…}, hidden: true, permissions: Array(1), children: Array(1)}
            // 3: {path: '/monitor/job-log', component: {…}, hidden: true, permissions: Array(1), children: Array(1)}
            // 4: {path: '/tool/gen-edit', component: {…}, hidden: true, permissions: Array(1), children: Array(1)}
            asyncRoutes.forEach(route => { router.addRoute(route) })  // 动态追加异步路由
            this.setRoutes(rewriteRoutes)
            this.setSidebarRouters(constantRoutes.concat(sidebarRoutes))
            this.setDefaultRoutes(sidebarRoutes)
            this.setTopbarRoutes(defaultRoutes)
            resolve(rewriteRoutes)  // 通过resolve返回处理后的重写路由。
          })
        })
      }
    }
  })

/**
 * 遍历后端传来的组件字符串，转换为组件对象
 * @param {*} type 决定是否对子路由调用filterChildren函数进行进一步的处理
 */
function filterAsyncRouter(asyncRouterMap, lastRouter = false, type = false) {
  return asyncRouterMap.filter(route => {  // 过滤asyncRouterMap数组，每个route代表数组中的一个路由对象
    if (type && route.children) {
      route.children = filterChildren(route.children)
    }
    if (route.component) {
      // Layout ParentView 组件特殊处理
      if (route.component === 'Layout') {
        route.component = Layout
      } else if (route.component === 'ParentView') {
        route.component = ParentView
      } else if (route.component === 'InnerLink') {
        route.component = InnerLink
      } else {
        route.component = loadView(route.component)  // component: () => import('@/views/login'),
      }
    }
    if (route.children != null && route.children && route.children.length) {  // 更深层次的子路由
      route.children = filterAsyncRouter(route.children, route, type)
    } else {  // 如果没有子路由，从路由对象中删除 children 和 redirect 属性
      delete route['children']
      delete route['redirect']
    }
    // filter 函数在此总是返回 true，意味着原始数组中的每个元素都会被保留在结果数组中。
    // 但实际的路由对象可能已经被修改（例如，删除了某些属性，或修改了组件引用）。
    return true
  })
}

/**
 * 处理嵌套的子路由，确保路径正确拼接，特别是在存在ParentView这样的特殊组件时
 * 
 * {name: 'Log', hidden: false, component: {…}, path: 'log', redirect: 'noRedirect', …}
 * -> {name: 'Operlog', path: 'log/operlog', query: '', hidden: false, component: ƒ, …}
 *    {name: 'Logininfor', path: 'log/logininfor', query: '', hidden: false, component: ƒ, …}
 */
function filterChildren(childrenMap, lastRouter = false) {
  var children = []
  childrenMap.forEach((el, index) => {  // 遍历每个子路由对象el
    if (el.children && el.children.length) {  // 有进一步的子路由
      if (el.component === 'ParentView' && !lastRouter) {  // 当前组件为'ParentView'且没有上一级路由（lastRouter）
        el.children.forEach(c => {
          c.path = el.path + '/' + c.path  // 修改每个子路由的路径，使其包括ParentView的路径，形成嵌套路径
          if (c.children && c.children.length) {  // 如果这些子路由也有子路由，递归调用filterChildren处理它们
            /**
             * concat 是 JavaScript 中的一个数组方法，用于将一个或多个数组连接到另一个数组的末尾，并返回一个新的数组，而不会改变原有的数组。
             * 这是一种常用的方法来合并数组中的元素，特别是在处理不可变数据或者需要保持原数组不变的场景中。
             * 
             * 特点：
             * 不修改原数组：concat方法不会改变原来的数组，而是返回一个全新的数组。
             * 可以接受多个参数：concat可以接受多个数组作为参数，依次将它们合并到一起。
             * 添加非数组值：除了数组，concat也可以接受非数组值作为参数，这些值将作为单独的元素添加到新数组的末尾。
             */
            children = children.concat(filterChildren(c.children, c))
            return
          }
          children.push(c)
        })
        return
      }
    }
    if (lastRouter) {  // 如果有上一级路由
      el.path = lastRouter.path + '/' + el.path  // 修改当前子路由的路径，使其包括上一级路由的路径
      if (el.children && el.children.length) {
        children = children.concat(filterChildren(el.children, el))
        return
      }
    }
    children = children.concat(el)  // 对于不满足上述特殊处理的普通路由元素或在处理完成后的元素，将其加入到结果数组children中
  })
  return children
}

/**
 * 筛选具有特定权限或角色要求的路由配置，以确保用户界面上只显示当前用户有权限访问的路由
 */
export function filterDynamicRoutes(routes) {
  const res = []
  routes.forEach(route => {
    if (route.permissions) {
      if (auth.hasPermiOr(route.permissions)) {
        res.push(route)  // 如果用户具有所需权限，则将该路由对象添加到res数组中
      }
    } else if (route.roles) {
      if (auth.hasRoleOr(route.roles)) {
        res.push(route)  // 如果用户具有所需角色，则将该路由对象添加到res数组中
      }
    }
  })
  // console.log(res)
  return res
}

/**
 * 匹配views里面所有的.vue文件
 * 
 * import.meta.glob 是一个比较新的特性
 * 用于在构建时进行模块的动态导入。这种方法允许基于文件路径模式动态地导入多个模块，非常适合处理大量文件，比如自动导入一个目录下的所有组件
 * 路径模式：用来匹配相对于当前文件的上两级目录中 views 目录下的所有 .vue 文件（包括所有子目录中的 .vue 文件）。
 * 动态导入：import.meta.glob 使用这个模式来查找所有匹配的文件，并返回一个对象。这个对象的键是匹配的文件路径，值是相应的函数，这些函数可以被调用来动态导入相应的模块。
 * 
 * 返回的 modules 对象会像这样：
 * {
 * '../../views/example1.vue': () => import('../../views/example1.vue'),
 * '../../views/subfolder/example2.vue': () => import('../../views/subfolder/example2.vue'),
 * // 更多匹配的 .vue 文件
 * }
 * 
 **/
const modules = import.meta.glob('./../../views/**/*.vue')

/**
 * 动态地import了一个Vue组件，但它与静态import语句有所不同。
 * 这里是使用一个更灵活的方式来加载组件，通常被称为懒加载或异步组件加载。
 * 只有在函数被调用时，指定的组件才会被加载。这可以延迟组件的加载时间，直到真正需要它们的时候。
 * 这种方式非常适合大型应用，可以减少应用的初始加载时间，提高性能。
 */
export const loadView = (view) => {
  let res;
  for (const path in modules) {
    const dir = path.split('views/')[1].split('.vue')[0];
    if (dir === view) {  // 如果从路径中提取出的组件名称与函数参数view指定的名称相匹配
      res = () => modules[path]();  // 设置res为一个新的箭头函数（工厂函数）。这个函数在调用时会执行modules[path]()，即动态导入并执行相应的Vue组件模块
    }
  }
  return res;
}

export default usePermissionStore
