import Cookies from 'js-cookie'

/*
    Cookies 是存储在用户浏览器中的小块数据，它们用于保持状态和在服务器与客户端之间传递信息。它们通常用于以下目的：
    会话管理: 登录状态、购物车内容等。
    个性化设置: 用户偏好设置、主题等。
    跟踪和分析: 用户行为分析、广告等。
 */

const TokenKey = 'Admin-Token'

export function getToken() {
  return Cookies.get(TokenKey)
}

export function setToken(token) {
  return Cookies.set(TokenKey, token)
}

export function removeToken() {
  return Cookies.remove(TokenKey)
}
