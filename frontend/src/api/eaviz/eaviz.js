import request from '@/utils/request'

// ESC + SD
export const escsdAnalyse = (query) => request.post('/eaviz/escsd', query);

// AD
export const adAnalyse = (query) =>
  request.post('/eaviz/ad', query, {
    timeout: 5 * 60 * 1000, // AD 请求可能需要较长时间
  });