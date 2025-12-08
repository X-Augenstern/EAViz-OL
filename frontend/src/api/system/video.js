import request from '@/utils/request'

// 查询视频列表
export function listVideo(query) {
  return request({
    url: '/system/video/list',
    method: 'get',
    params: query
  })
}

// 根据video的Id查询video详细
export function getVideoByVideoId(videoId) {
  return request({
    url: '/system/video/' + videoId,
    method: 'get'
  })
}

// 根据用户的Id查询video详细
export const getVideoByUserId = (userId) => request.get('/system/video/' + userId);

// 删除视频（路径参数，支持逗号分隔的ID）
export function delVideo(videoIds) {
  return request({
    url: '/system/video/' + videoIds,
    method: 'delete'
  })
}


