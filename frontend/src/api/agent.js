import { getToken } from '@/utils/auth'

// 智能体对话接口 - 创建SSE连接
export const createAgentChatConnection = (message, deepThinking = false) => {
  // 使用EventSource创建SSE连接
  const baseURL = import.meta.env.VITE_APP_BASE_API || ''
  // 获取token（如果需要认证）
  const token = getToken()
  // EventSource不支持自定义headers，所以token通过URL参数传递
  // 后端会从URL参数或请求头中获取token进行认证
  // 统一调用接口 /agent/chat，传递 deepThinking 参数
  const endpoint = '/agent/chat'
  let url = `${baseURL}${endpoint}?message=${encodeURIComponent(message)}&deepThinking=${deepThinking ? 'true' : 'false'}`
  if (token) {
    url += `&token=${encodeURIComponent(token)}`
  }
  
  return new EventSource(url)
}

// 终止/取消当前 chat 的请求（后端会转发到 Agent terminate endpoint）
export const terminateAgentChat = async (chatId) => {
  const baseURL = import.meta.env.VITE_APP_BASE_API || ''
  const token = getToken()
  const endpoint = '/agent/terminate'
  let url = `${baseURL}${endpoint}?chatId=${encodeURIComponent(chatId)}`
  if (token) {
    url += `&token=${encodeURIComponent(token)}`
  }
  // POST request, return fetch Promise so caller can optionally await
  return fetch(url, { method: 'POST' })
}
