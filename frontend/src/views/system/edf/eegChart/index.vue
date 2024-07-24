<template>
  <el-card style="margin-top: 50px;">
    <!-- 换成类选择器也可 -->
    <div id="eegPlot" class="eeg-plot" ref="plotContainer">
      <!-- 嵌入在 eegPlot 内成为其子元素，这样在进入全屏模式时，这些组件也会被包括在内 -->
      <screenfull target="#eegPlot" :on-fullscreen-change="handleFullscreenChange" class="fullscreen-control" />
      <el-backtop target=".eeg-plot" :visibility-height="200" :right="50" :bottom="50" />
    </div>
  </el-card>
</template>

<script setup name="EEGChart">
import { onBeforeUnmount, onMounted } from 'vue';
import { useEEGChartStore } from "@/store/modules/eegChart";
import Plotly from 'plotly.js-dist-min';
import Screenfull from '@/components/Screenfull'

const EEGChartStore = useEEGChartStore();
const plotContainer = ref('');

onMounted(() => {
  EEGChartStore.isExist = true;
  // 设置回调函数
  EEGChartStore.setDrawEEGDataCallback(drawEEGData);
  EEGChartStore.setAppendEEGDataCallback(appendEEGData);
})

onBeforeUnmount(() => {
  clearEEGPlot();
  EEGChartStore.$reset();
})

/**
  * 根据初始的数据绘制脑电图
  */
const drawEEGData = (eegData) => {
  const channelNames = EEGChartStore.selectedChannels.split(',');
  // const eegDataLength = EEGChartStore.eegData.length;  // (numChannels * sampling points)
  const numChannels = EEGChartStore.numChannels;

  const traces = eegData.map((data, index) => ({
    x: Array.from({ length: data.length }, (_, i) => i),  // 样本点的索引数组
    y: data,  // 对应通道的 EEG 数据
    type: 'scatter',
    mode: 'lines',
    name: channelNames[index],
    xaxis: 'x',
    yaxis: 'y' + (index + 1)
  }));

  const layout = {
    title: EEGChartStore.edfName,
    autosize: true,
    height: 200 * numChannels, // 调整高度以增加通道间的间隔
    grid: {
      rows: numChannels,  // 行数与通道数量一致
      columns: 1,  // 每行一个通道
      pattern: 'independent'
    },
    legend: {
      orientation: 'v', // 纵向排列
      y: 1,
      yanchor: 'top',
      x: -0.1, // 调整图例的水平位置，确保在左侧
      xanchor: 'right', // 图例水平对齐方式
      traceorder: 'normal', // 按照trace顺序排列
      font: {
        size: 16
      }
    },
    xaxis: {  // 共用的x轴
      title: 'Time (samples)',
      domain: [0, 1],  // 轴在图表中的相对位置和大小。它是一个包含两个数值的数组，表示轴在容器中的相对位置范围。这两个数值通常在 0 到 1 之间，表示轴从图表的哪个百分比开始到哪个百分比结束
      anchor: 'y' + numChannels  // 将一个轴与另一个轴链接起来。它指定该轴应该与哪个轴交叉。通常用于设置多个 x 轴或 y 轴时，确定它们之间的关联
    }
  };

  // 往布局配置中添加每个通道的y轴，从上到下排列
  eegData.forEach((_, index) => {  // 不会修改eegData
    layout['yaxis' + (index + 1)] = {
      title: channelNames[index],
      // 0: 20/21, 20.8/21  1: 19/21, 19.8/21  ...  20: 0/21, 0.8/21
      // 将每个 y 轴按通道数等分到图表的垂直空间中，每个通道占据 80% 的分配空间，这样通道之间有一定的间隔，避免绘图时相互重叠
      domain: [(numChannels - index - 1) / numChannels, (numChannels - index - 1 + 0.8) / numChannels],
      showticklabels: true,  // 标签显示
      visible: true // 初始状态下所有 y 轴都是可见的
    };
  });

  // Plotly.Root 可以直接使用目标容器的 ID ('eegPlot')，也可以使用 DOM 元素的响应式引用 plotContainer.value
  // Plotly.newPlot('eegPlot', traces, layout);  // 创建新的绘图或更新现有的绘图。参数包括目标容器的 ID ('eegPlot')、图形追踪数组 (traces)、以及布局对象 (layout)
  Plotly.newPlot(plotContainer.value, traces, layout);  // 使用引用
  EEGChartStore.curXAxisLength += eegData[0].length;
};

/**
  * 根据追加的数据继续绘制脑电图
  */
const appendEEGData = (newData) => {
  console.log('Current length:', EEGChartStore.curXAxisLength);
  console.log('New data length:', newData[0].length);

  // 确保 newData 是一个二维数组
  if (!Array.isArray(newData) && !Array.isArray(newData[0]) && !(newData[0] instanceof Float64Array)) {
    console.error('newData is not a valid 2D array');
    return;
  }

  const traceUpdate = {
    y: newData.map(data => Array.from(data)),  // 追加通道的 EEG 数据
    x: newData.map(data => Array.from({ length: data.length }, (_, i) => i + EEGChartStore.curXAxisLength))  // 为每个数据点生成 x 坐标，坐标是从当前 x 轴长度开始递增的索引值
  };
  console.log('Trace update:', traceUpdate);

  try {
    Plotly.extendTraces(plotContainer.value, traceUpdate, Array.from({ length: newData.length }, (_, i) => i));  // 用 traceUpdate 中的 x 和 y 数据扩展图表中的相应 trace。第三个参数是一个数组，表示要更新的 trace 索引，这里更新所有通道的数据

    Plotly.relayout(plotContainer.value, { 'xaxis.range': [0, EEGChartStore.curXAxisLength + newData[0].length] });  // 更新 x 轴的范围以适应新数据
    EEGChartStore.curXAxisLength += newData[0].length;
  } catch (error) {
    console.error('Error extending traces:', error);
  }
};

/**
 * 清除脑电图
 */
const clearEEGPlot = () => {
  Plotly.purge(plotContainer.value);  // 会删除图表并清除其关联的数据和元素。
}

/**
 * 监听全屏事件并调整图表的布局
 * @param {*} isFullscreen 全屏标志回调
 */
const handleFullscreenChange = () => {
  relayout();
}

/**
 * 重置图表的布局
 */
const relayout = () => {
  Plotly.relayout(plotContainer.value, {
    'xaxis.autorange': true,  // 将轴重置到原始的自动范围
    'yaxis.autorange': true,
  });
};
</script>

<style lang="scss" scoped>
.eeg-plot {
  /* 固定高度 */
  height: 500px;
  /* 垂直滚动条 */
  overflow-y: auto;
  /* 禁用水平滚动条 */
  overflow-x: hidden;
  /* 为子元素提供定位上下文，这是必要的，因为 absolute 定位的元素相对于其最近的已定位祖先（即非 static 定位的祖先）定位 */
  position: relative;
}

.fullscreen-control {
  /* 绝对定位，相对于最近的已定位祖先（这里是 eegPlot）进行定位。它们的位置将根据 top, right, bottom, 和 left 属性进行调整 */
  position: absolute;
  /* 使其固定在视口的位置。当页面滚动时，fullscreen-control 将保持在视口的指定位置，而不随内容滚动，但是此时的位置属性是相对于视口左上角而言的 */
  // position: fixed;
  top: 6px;
  left: 6px;
  /* 确保在其他元素之上显示，值越大，元素越靠前 */
  z-index: 1000;
}
</style>
