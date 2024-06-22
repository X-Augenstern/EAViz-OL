/**
 * 获取早上/上午/下午/晚上
 */
export const getTime = () => {
  let msg = '';
  let hour = new Date().getHours();
  if (hour <= 9) msg = '早上';
  else if (hour <= 12) msg = '上午';
  else if (hour <= 18) msg = '下午';
  else msg = '晚上';
  return msg;
}