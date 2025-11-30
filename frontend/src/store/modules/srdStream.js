import { defineStore } from "pinia";
import { ref } from "vue";
import { getToken } from "@/utils/auth";

export const useSRDStreamStore = defineStore('SRDStream', () => {
  const edfId = ref(null);
  const channelName = ref('');
  const channelIdx = ref(0);
  const startTime = ref(0);
  const stopTime = ref(0);
  const windowSize = ref(5.0);  // 后端分块窗口大小（秒），固定为5秒
  const sfreq = ref(1000);  // 采样频率
  
  let buffer = '';  // 文本缓冲区（用于累积 JSON 行）
  const initialDraw = ref(true);  // 第一次绘图
  const isStreaming = ref(false);  // 是否正在流式传输
  
  // 导出 initialDraw 以便外部重置
  const resetInitialDraw = () => {
    initialDraw.value = true;
  };
  
  // 所有标注信息
  const allAnnotations = ref([]);
  
  // 来自组件回调函数引用
  let drawSRDDataCallback = null;
  let appendSRDDataCallback = null;
  let annotationsCallback = null;
  
  // 设置回调函数
  const setDrawSRDDataCallback = (callback) => {
    drawSRDDataCallback = callback;
  };
  
  const setAppendSRDDataCallback = (callback) => {
    appendSRDDataCallback = callback;
  };
  
  const setAnnotationsCallback = (callback) => {
    annotationsCallback = callback;
  };

  /**
   * 获取并处理流式 SRD 数据
   * @param {Object} params - 请求参数
   * @param {number} params.edfId - EDF ID
   * @param {string} params.method - 分析方法
   * @param {number} params.startTime - 开始时间（秒）
   * @param {number} params.stopTime - 结束时间（秒）
   * @param {number} params.chIdx - 通道索引
   * @param {number} params.windowSize - 窗口大小（秒），默认 5
   */
  const fetchSRDData = async (params) => {
    edfId.value = params.edfId;
    channelIdx.value = params.chIdx;
    startTime.value = params.startTime;
    stopTime.value = params.stopTime;
    windowSize.value = params.windowSize || 5.0;
    
    // 重置状态
    buffer = '';
    initialDraw.value = true;
    isStreaming.value = true;
    allAnnotations.value = [];

    const requestParams = {
      edfId: params.edfId,
      method: params.method,
      startTime: params.startTime,
      stopTime: params.stopTime,
      chIdx: params.chIdx,
      windowSize: windowSize.value
    };

    try {
      await fetch(import.meta.env.VITE_APP_BASE_API + '/eaviz/srd', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': "Bearer " + getToken()
        },
        body: JSON.stringify(requestParams)
      }).then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.body;
      }).then(body => {
        const reader = body.getReader();
        const decoder = new TextDecoder();

        const processStream = async ({ done, value }) => {
          if (done) {
            console.log('SRD Stream reading done.');
            // 处理剩余的缓冲区数据
            if (buffer.length > 0) {
              processBufferedData();
              buffer = '';
            }
            isStreaming.value = false;
            // 发送所有标注信息
            if (annotationsCallback && allAnnotations.value.length > 0) {
              annotationsCallback(allAnnotations.value);
            }
            return;
          }

          // 解码数据并添加到缓冲区
          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;

          // 处理完整的 JSON 行（以换行符分隔）
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';  // 保留最后一个不完整的行

          // 处理每个完整的 JSON 行
          for (const line of lines) {
            if (line.trim()) {
              try {
                const windowData = JSON.parse(line);
                processWindowData(windowData);
              } catch (e) {
                console.error('Failed to parse JSON:', e, 'Line:', line);
              }
            }
          }

          reader.read().then(processStream);
        };

        reader.read().then(processStream);
      }).catch(e => {
        console.error('There has been a problem with your fetch operation:', e);
        isStreaming.value = false;
      });
    } catch (error) {
      console.error('An error occurred while fetching SRD data:', error);
      isStreaming.value = false;
    }
  };

  /**
   * 处理窗口数据
   * @param {Object} windowData - 窗口数据对象
   */
  const processWindowData = (windowData) => {
    if (windowData.type === 'summary') {
      // 汇总信息，包含所有标注（在数据流开始前发送）
      allAnnotations.value = windowData.annotations || [];
      // 立即通知前端更新标注（在数据绘制之前）
      if (annotationsCallback) {
        annotationsCallback(allAnnotations.value);
      }
      return;
    }

    // 数据窗口（type === 'data' 或不包含 type）
    // 更新采样频率
    if (windowData.sfreq) {
      sfreq.value = windowData.sfreq;
    }

    // 准备绘图数据（不包含标注，标注已通过汇总信息处理）
    const plotData = {
      time: windowData.time,
      windowSize: windowData.windowSize,
      raw: {
        times: windowData.raw.times,
        data: windowData.raw.data
      },
      low: {
        times: windowData.low.times,
        data: windowData.low.data
      },
      high: {
        times: windowData.high.times,
        data: windowData.high.data
      },
      bias: windowData.bias,
      // 不包含 annotations，因为标注已经通过 summary 发送
      annotations: []
    };

    if (initialDraw.value) {
      if (drawSRDDataCallback) {
        drawSRDDataCallback(plotData);
      }
      initialDraw.value = false;
    } else {
      if (appendSRDDataCallback) {
        appendSRDDataCallback(plotData);
      }
    }
  };

  /**
   * 处理剩余的缓冲数据
   */
  const processBufferedData = () => {
    if (buffer.trim()) {
      try {
        const windowData = JSON.parse(buffer);
        processWindowData(windowData);
      } catch (e) {
        console.error('Failed to parse buffered data:', e);
      }
    }
    buffer = '';
  };

  /**
   * 重置 store
   */
  const reset = () => {
    buffer = '';
    initialDraw.value = true;
    isStreaming.value = false;
    allAnnotations.value = [];
    edfId.value = null;
    channelName.value = '';
    channelIdx.value = 0;
    startTime.value = 0;
    stopTime.value = 0;
    windowSize.value = 5.0;
    sfreq.value = 1000;
  };

  return {
    edfId,
    channelName,
    channelIdx,
    startTime,
    stopTime,
    windowSize,
    sfreq,
    initialDraw,
    isStreaming,
    allAnnotations,
    fetchSRDData,
    setDrawSRDDataCallback,
    setAppendSRDDataCallback,
    setAnnotationsCallback,
    resetInitialDraw,
    reset
  };
});

