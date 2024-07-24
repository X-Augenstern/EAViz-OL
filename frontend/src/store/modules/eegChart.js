import { defineStore } from "pinia";
import { ref, watch } from "vue";
import { getToken } from "@/utils/auth";

export const useEEGChartStore = defineStore('EEGChart', () => {
  const edfName = ref('');  // 不定义为响应式往store里赋值在请求体参数中都还是undefined
  const selectedChannels = ref('');
  const numChannels = ref(0);
  let buffer = new Uint8Array(0);  // 数据缓冲区
  let initialDraw = ref(true);  // 第一次绘图
  let isExist = ref(false);  // 组件存在
  const curXAxisLength = ref(0);  // 当前x轴长度（已绘制的样本点数）

  // 来自eegChart回调函数引用
  let drawEEGDataCallback = null;
  let appendEEGDataCallback = null;

  // 设置回调函数
  const setDrawEEGDataCallback = (callback) => {
    drawEEGDataCallback = callback;
  };
  const setAppendEEGDataCallback = (callback) => {
    appendEEGDataCallback = callback;
  };

  watch(() => selectedChannels.value, (newVal) => {
    // split(',')返回分割后的数组，不会影响到原数据
    if (newVal != '') numChannels.value = selectedChannels.value.split(',').length;
  });

  /**
   * 获取并处理流式EEG数据
   * @param {*} row edfListWithCount 的 row 对象
   * @param {*} start 开始样本点
   * @param {*} end 结束样本点
   */
  const fetchEdfData = async (row, start, end) => {
    edfName.value = row.edfName;
    selectedChannels.value = row.validChannels;

    // 获取EDF数据请求体参数
    const getDataParam = {
      edfId: row.edfId,
      selectedChannels: row.validChannels,
      start: start !== undefined ? start : 0,
    }
    if (end !== undefined) getDataParam.end = end;
    // console.log('Sending request with params:', getDataParam);  // 打印请求体参数

    try {
      await fetch(import.meta.env.VITE_APP_BASE_API + '/system/edf/getData', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': "Bearer " + getToken()
        },
        body: JSON.stringify(getDataParam)  // JSON 序列化
      }).then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.body;  // 响应的主体是一个数据流
      }).then(body => {
        const reader = body.getReader();  // 创建一个数据流读取器

        const processStream = async ({ done, value }) => {
          console.log(`Reader result:`, { done, value });
          if (done) {
            console.log('Stream reading done.');
            if (buffer.length > 0) {
              console.log('Remaining buffer data which not be plotted:', buffer.length);
              // processBufferedData();
              buffer = new Uint8Array(0);  // 清空缓冲区
            }
            console.log('Data streaming completed.');
            return;
          }

          // 合并缓冲区和新数据
          const newBuffer = new Uint8Array(buffer.length + value.length);
          newBuffer.set(buffer);  // 将旧的 buffer 数据放入 newBuffer 中
          newBuffer.set(value, buffer.length);  // 将新的 value 数据放到旧的 buffer 数据后
          buffer = newBuffer;
          // 处理可以完整转换为 Float64Array 的部分
          const float64Size = Float64Array.BYTES_PER_ELEMENT;  // 计算 Float64Array 每个元素的字节大小（通常是 8 个字节）
          const completeSize = Math.floor(buffer.length / (float64Size * numChannels.value)) * (float64Size * numChannels.value);  // 计算 buffer 中可以完整地转换为 Float64Array 且可以均匀地分配到每个通道的字节数
          const chunk = buffer.slice(0, completeSize);  // 将这些完整的数据提取出来作为 chunk
          buffer = buffer.slice(completeSize);  // 更新 buffer，去除已经处理的部分
          console.log('buffer', buffer)

          processStreamedDataChunk(new Float64Array(chunk.buffer));  // doc 4
          reader.read().then(processStream);  // 继续读取下一个数据块，并递归调用 processStream 处理后续数据
        };

        reader.read().then(processStream);  // 开始从数据流中读取数据块，第一次调用 processStream
      }).catch(e => console.error('There has been a problem with your fetch operation:', e));
    } catch (error) {
      console.error('An error occurred while fetching EDF data:', error);
    }
  };

  /**
   * 处理可以完整地转换为 Float64Array 且可以均匀地分配到每个通道的数据块
   * @param {*} newData chunk.buffer
   */
  const processStreamedDataChunk = (newData) => {
    let completeLength = Math.floor(newData.length / numChannels.value) * numChannels.value;  // 计算 newData 中可以完整地分配给每个通道的数据长度
    const chunk = newData.slice(0, completeLength);

    const chunkData = Array.from({ length: numChannels.value }, (_, i) =>  // doc 6
      chunk.filter((_, idx) => idx % numChannels.value === i)
    );
    console.log('chunkData:', chunkData);

    if (initialDraw.value) {
      if (drawEEGDataCallback) drawEEGDataCallback(chunkData.map(channel => Array.from(channel)));  // doc 7
      initialDraw.value = false;  // 只在第一次绘图
    } else {
      if (appendEEGDataCallback) appendEEGDataCallback(chunkData);
    }
  };

  /**
   * 处理剩余的缓冲数据
   * 
   * 按照当前缓冲数据的处理逻辑，如果一个正常的edf（使用 Float64Array 存储每个采样数据（8字节）、且各个通道的采样点相同），不应该会有剩余的缓冲数据
   * 因此如果绘制的是有部分通道缺少采样点的edf，只绘制到所有通道都有采样点为止，多余部分不绘制
   * 而且仅凭目前的 appendEEGData 函数也只能绘制全部通道都有采样点的情况
   */
  const processBufferedData = () => {
    const bufferedData = Array.from({ length: numChannels.value }, (_, i) =>
      buffer.filter((_, idx) => idx % numChannels.value === i)
    );
    console.log('bufferedData:', bufferedData);

    if (bufferedData[0].length > 0) {
      if (initialDraw.value) {
        if (drawEEGDataCallback) drawEEGDataCallback(bufferedData.map(channel => Array.from(channel)));
      } else {
        if (appendEEGDataCallback) appendEEGDataCallback(bufferedData);
      }
    }

    buffer = new Uint8Array(0);  // 清空缓冲区
  };
  return { edfName, selectedChannels, numChannels, initialDraw, isExist, curXAxisLength, fetchEdfData, setDrawEEGDataCallback, setAppendEEGDataCallback }
})