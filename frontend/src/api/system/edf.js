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
export const getEdfByUserId = (userId) => request.get('/system/edf/' + userId)

// 删除edf
export const delEdf = (edfIds) => request.delete('/system/edf/' + edfIds)