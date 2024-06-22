import request from '@/utils/request'

// 获取路由
// @loginController.get("/getRouters")
// get_login_user_routers：根据用户id获取当前用户路由信息
export const getRouters = () => {
  return request({
    url: '/getRouters',
    method: 'get'
  })
}