import request from '@/utils/request'

// ESC + SD
export const escsdAnalyse = (query) => request.post('/eaviz/escsd', query);

// AD
export const adAnalyse = (query) =>
  request.post('/eaviz/ad', query, {
    timeout: 5 * 60 * 1000, // AD 请求可能需要较长时间
  });

// SpiD
export const spidAnalyse = (query) =>
  request.post('/eaviz/spid', query, {
    timeout: 5 * 60 * 1000,
  });

// SRD
export const srdAnalyse = (query) =>
  request.post('/eaviz/srd', query, {
    timeout: 5 * 60 * 1000,
  });

// VD
export const vdAnalyse = (query) =>
  request.post('/eaviz/vd', query, {
    timeout: 10 * 60 * 1000, // 视频处理可能需要更长时间
  });