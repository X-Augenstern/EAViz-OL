import { defineConfig, loadEnv } from 'vite'
import path from 'path'
import createVitePlugins from './vite/plugins'

// https://vitejs.dev/config/
export default defineConfig(({ mode, command }) => {  // command用于获取当前开发环境
  const env = loadEnv(mode, process.cwd())  // 从项目根目录加载（默认为.env.development）文件
  const { VITE_APP_ENV } = env
  return {
    // 部署生产环境和开发环境下的URL。
    // 默认情况下，vite 会假设应用是被部署在一个域名的根路径上，例如 https://www.ruoyi.vip/。
    // 如果应用被部署在一个子路径上，就需要用这个选项指定这个子路径。例如，如果应用被部署在 https://www.ruoyi.vip/admin/，则设置 baseUrl 为 /admin/。
    base: VITE_APP_ENV === 'production' ? '/' : '/',
    plugins: createVitePlugins(env, command === 'build'),
    resolve: {
      // https://cn.vitejs.dev/config/#resolve-alias
      alias: {
        // 设置路径
        '~': path.resolve(__dirname, './'),
        // 设置别名
        '@': path.resolve(__dirname, './src')
      },
      // https://cn.vitejs.dev/config/#resolve-extensions
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue']
    },
    /**
     * vite 相关配置
     * 
     * /dev-api 前缀的请求会被代理到 http://localhost:9099，并且 /dev-api 前缀会被移除。
     * 这意味着在开发环境中，当请求 /dev-api/profile/... 时：Vite 代理会将请求转发到 http://localhost:9099/profile/...。
     * 在 http://localhost:9099/profile/... 位置，FastAPI 会处理请求并返回相应的资源。
     * 
     * 代理路径：/dev-api/profile/... 是在开发环境中通过 Vite 代理配置的路径，这个路径被重写并代理到后端服务器。
     * 直接路径：/profile/... 是在后端服务器上实际配置的路径。
     * 
     * 工作流程:
     * 1、当前端发出一个请求，比如 /dev-api/profile/avatar/2024/07/07/avatar_20240707150538A004.png
     * 2、Vite 代理接收到这个请求，并将其传递给代理配置的 rewrite 函数
     * 3、rewrite 会将请求路径 /dev-api/profile/avatar/2024/07/07/avatar_20240707150538A004.png 转换为 /profile/avatar/2024/07/07/avatar_20240707150538A004.png
     * 4、代理将重写后的路径转发到目标服务器 http://localhost:9099
     * 5、目标服务器处理请求，并返回对应的资源（FastAPI 处理 /profile/... 路径，并返回相应的静态文件）
     * 
     * 在浏览器中直接访问 http://localhost:9099/profile/avatar/2024/07/07/avatar_20240707150538A004.png 时：
     * 相当于直接请求 FastAPI 服务器上的静态文件路径，FastAPI 会返回对应的文件。
     */
    server: {
      port: 80,
      host: true,
      open: true,
      proxy: {
        // https://cn.vitejs.dev/config/#server-proxy
        '/dev-api': {  // 代理跨域关键字
          target: 'http://localhost:9099',  // 数据的服务器地址
          changeOrigin: true,  // 需要代理跨域
          // ^: 匹配字符串的开头。
          // \/: 匹配字符 /。在正则表达式中，/ 是一个特殊字符，需要用 \ 进行转义。
          rewrite: (p) => p.replace(/^\/dev-api/, '')  // 路径重写将/api替换为''，因为提供的服务器上没有/api前缀路径
        }
      }
    },
    //fix:error:stdin>:7356:1: warning: "@charset" must be the first rule in the file
    css: {
      postcss: {
        plugins: [
          {
            postcssPlugin: 'internal:charset-removal',
            AtRule: {
              charset: (atRule) => {
                if (atRule.name === 'charset') {
                  atRule.remove();
                }
              }
            }
          }
        ]
      }
    }
  }
})
