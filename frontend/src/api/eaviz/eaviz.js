import request from '@/utils/request'

// escsd
export const escsdAnalyse = (query)=>request.post('/eaviz/escsd',query);