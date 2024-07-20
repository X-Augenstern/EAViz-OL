import request from '@/utils/request'

// 查询edf列表
export function listEdf(query) {
  return request({
    url: '/system/edf/list',
    method: 'get',
    params: query
  })
}

// 根据edf的Id查询edf详细
export function getEdfByEdfId(edfId) {
  return request({
    url: '/system/edf/' + edfId,
    method: 'get'
  })
}

// 根据用户的Id查询edf详细
export const getEdfByUserId = (userId) => request.get('/system/edf/' + userId);

// 删除edf（路径参数）
export const delEdf = (edfIds) => request.delete('/system/edf/' + edfIds);

// 获取edf数据（查询参数）
// 这个请求将 query 对象中的键值对作为查询参数附加到 URL 后。
// 例如，如果 query 是 { edf_id: 123, selected_channels: ['channel1', 'channel2'] }，请求的 URL 将是 /system/edf/getData?edf_id=123&selected_channels=channel1,channel2。
// export const getEdfDataById = (query) => request.get('/system/edf/getData', { params: query })
// -> 改为请求体参数
// 使用 axios.post 方法时，第二个参数会作为请求体发送。
// data 对象在发送时会被序列化为JSON格式，并包含在HTTP请求的请求体中。
// 服务器端会解析这个请求体，并将其映射到相应的Pydantic模型中。
export const getEdfDataById = (data) => request.post('/system/edf/getData', data, { responseType: 'arraybuffer' });  // { timeout: 60000 } 自定义请求超时时间