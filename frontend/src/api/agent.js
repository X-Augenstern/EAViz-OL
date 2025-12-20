import { getToken } from '@/utils/auth'

// 智能体对话接口 - 创建SSE连接
export const createAgentChatConnection = (message, deepThinking = true) => {
  // 使用EventSource创建SSE连接
  const baseURL = import.meta.env.VITE_APP_BASE_API || ''
  
  // 获取token（如果需要认证）
  const token = getToken()
  
  // EventSource不支持自定义headers，所以token通过URL参数传递
  // 后端会从URL参数或请求头中获取token进行认证
  // 根据模式选择不同的接口
  const endpoint = deepThinking ? '/agent/chat/liteMind' : '/agent/chat/simple'
  let url = `${baseURL}${endpoint}?message=${encodeURIComponent(message)}`
  if (token) {
    url += `&token=${encodeURIComponent(token)}`
  }
  
  return new EventSource(url)
}
