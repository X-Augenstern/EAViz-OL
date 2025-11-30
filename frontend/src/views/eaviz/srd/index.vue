<template>
  <div class="app-container">
    <el-steps :active="activeStep" direction="vertical" align-center>
      <!-- 第一步：选择EDF -->
      <el-step title="请选择用于分析的EDF">
        <template #description>
          <el-text type="primary" tag="b" size="large" class="title_style">
            当前可用于 SRD 分析的 EDF（1000Hz）
          </el-text>
          <el-table
            :data="
              EDFStore.edfListWithCount.filter((edf) => edf.edfSfreq == 1000)
            "
            highlight-current-row
            @current-change="handleCurrentChange"
          >
            <el-table-column
              :label="columns[0].label"
              align="center"
              key="edfId"
              prop="edfId"
              v-if="columns[0].visible"
            />
            <el-table-column
              :label="columns[1].label"
              align="center"
              key="edfName"
              prop="edfName"
              v-if="columns[1].visible"
              :show-overflow-tooltip="true"
            />
            <el-table-column
              :label="columns[2].label"
              align="center"
              key="edfSfreq"
              prop="edfSfreq"
              v-if="columns[2].visible"
              :show-overflow-tooltip="true"
            />
            <el-table-column
              :label="columns[3].label"
              align="center"
              key="edfTime"
              prop="edfTime"
              v-if="columns[3].visible"
              :show-overflow-tooltip="true"
            />
            <el-table-column
              :label="columns[4].label"
              align="center"
              key="validChannels"
              prop="validChannels"
              v-if="columns[4].visible"
              :show-overflow-tooltip="true"
            />
            <el-table-column
              :label="columns[5].label"
              align="center"
              key="validCounts"
              prop="validChannelsCount"
              v-if="columns[5].visible"
              :show-overflow-tooltip="true"
            />
            <el-table-column
              :label="columns[6].label"
              align="center"
              key="uploadBy"
              prop="uploadBy"
              v-if="columns[6].visible"
              :show-overflow-tooltip="true"
            />
            <el-table-column
              :label="columns[7].label"
              align="center"
              key="uploadTime"
              prop="uploadTime"
              v-if="columns[7].visible"
              :show-overflow-tooltip="true"
            >
              <template #default="scope">
                <span>{{ parseTime(scope.row.uploadTime) }}</span>
              </template>
            </el-table-column>
          </el-table>
          <div class="empty-line"></div>
        </template>
      </el-step>

      <!-- 第二步：选择模型 -->
      <el-step title="请选择分析方法">
        <template #description>
          <el-collapse>
            <el-collapse-item
              v-for="(obj, idx) in eavizItems[itemIdx].methods"
              :key="idx"
              :name="obj.name"
            >
              <template #title>
                <el-radio-group
                  v-model="analyseParam.method"
                  size="large"
                  :disabled="stepDisabled.step2"
                >
                  <el-radio-button :label="obj.name" @click.stop />
                </el-radio-group>
              </template>
              <div>
                {{ obj.description }}
              </div>
            </el-collapse-item>
          </el-collapse>
          <div class="empty-line"></div>
        </template>
      </el-step>

      <!-- 第三步：选择分析时段和通道 -->
      <el-step>
        <template #title>请选择分析时段和通道</template>
        <template #description>
          <el-row style="margin-bottom: 16px">
            <el-col :span="5">
              <div class="grid-content">
                <el-text type="primary" tag="b">开始时间（秒）：</el-text>
                <el-input-number
                  v-model="timeParams.startTime"
                  :min="0"
                  :max="maxTime"
                  :precision="1"
                  :step="0.1"
                  controls-position="right"
                  :disabled="stepDisabled.step3"
                  style="width: 100%"
                ></el-input-number>
              </div>
            </el-col>
            <el-col :span="5" style="margin-left: 20px">
              <div class="grid-content">
                <el-text type="primary" tag="b">结束时间（秒）：</el-text>
                <el-input-number
                  v-model="timeParams.stopTime"
                  :min="timeParams.startTime + 1"
                  :max="
                    Math.min(timeParams.startTime + MAX_ANALYSIS_TIME, maxTime)
                  "
                  :precision="1"
                  :step="0.1"
                  controls-position="right"
                  :disabled="stepDisabled.step3"
                  style="width: 100%"
                ></el-input-number>
                <el-text
                  type="warning"
                  size="small"
                  style="display: block; margin-top: 4px"
                >
                  最大分析时长：{{ MAX_ANALYSIS_TIME }}秒（5分钟）
                </el-text>
              </div>
            </el-col>
            <el-col :span="5" style="margin-left: 20px">
              <div class="grid-content">
                <el-text type="primary" tag="b">选择通道：</el-text>
                <el-select
                  v-model="selectedChannelName"
                  placeholder="请选择通道"
                  :disabled="stepDisabled.step3 || channelOptions.length === 0"
                  style="width: 100%"
                  @change="handleChannelChange"
                >
                  <el-option
                    v-for="(channel, idx) in channelOptions"
                    :key="idx"
                    :label="channel"
                    :value="channel"
                  />
                </el-select>
              </div>
            </el-col>
          </el-row>
          <div class="empty-line"></div>
        </template>
      </el-step>

      <!-- 第四步：开始分析 -->
      <el-step>
        <template #description>
          <el-button
            type="primary"
            style="margin-bottom: 5px"
            :disabled="stepDisabled.step4 || isStreaming"
            @click="handleStreamAnalyse"
          >
            开始分析
          </el-button>
          <el-progress
            :percentage="percentage"
            :stroke-width="15"
            striped
            striped-flow
            :duration="50"
            style="width: 74vw"
          />
          <div class="empty-line"></div>
        </template>
      </el-step>
    </el-steps>

    <!-- 分析结果 -->
    <el-card v-if="showStreamView" class="stream-area" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>分析结果</span>
          <el-button
            type="danger"
            size="small"
            @click="closeStreamView"
            style="float: right"
          >
            关闭
          </el-button>
        </div>
      </template>

      <!-- 控制面板 -->
      <div
        class="stream-controls"
        style="
          margin-bottom: 16px;
          display: flex;
          align-items: center;
          gap: 30px;
          flex-wrap: wrap;
        "
      >
        <div style="display: flex; align-items: center; gap: 10px">
          <el-text type="primary" tag="b">传输状态：</el-text>
          <el-tag :type="isStreaming ? 'success' : 'info'">
            {{ isStreaming ? "传输中" : "已停止" }}
          </el-tag>
        </div>
        <div style="display: flex; align-items: center; gap: 10px">
          <el-text type="primary" tag="b">窗口大小：</el-text>
          <el-input-number
            v-model="streamWindowSize"
            :min="5"
            :max="300"
            :step="5"
            :precision="0"
            :disabled="isStreaming"
            style="width: 120px"
            @change="updateTimeRange"
          />
        </div>
        <div style="display: flex; align-items: center; gap: 10px">
          <el-text type="primary" tag="b">标注数量：</el-text>
          <el-tag type="warning">
            {{ allAnnotations.length }}
          </el-tag>
        </div>
      </div>

      <!-- 图表容器 -->
      <div
        id="srdStreamPlot"
        class="srd-stream-plot"
        ref="streamPlotContainer"
      ></div>
    </el-card>
  </div>
</template>

<script setup name="SRD">
import {
  reactive,
  ref,
  computed,
  watch,
  onMounted,
  onBeforeUnmount,
  nextTick,
} from "vue";
import { eavizItemsIdx, eavizItems } from "../../../eaviz/config";
import { useEDFStore } from "../../../store/modules/edf";
import { useSRDStreamStore } from "../../../store/modules/srdStream";
import { parseTime } from "../../../utils/ruoyi";
import Plotly from "plotly.js-dist-min";

const EDFStore = useEDFStore();
const SRDStreamStore = useSRDStreamStore();
const itemIdx = eavizItemsIdx.srd;
const maxTime = ref(1000);
const maxChannels = ref(19);
const selectedEDF = ref(null);
const channelOptions = ref([]);
const selectedChannelName = ref("");

// 最大分析时间限制（秒）- 防止浏览器卡顿
const MAX_ANALYSIS_TIME = 300; // 5分钟

// 进度条
const percentage = ref(0);
const analysisCompleted = ref(false); // 分析是否完成

// 流式查看相关
const showStreamView = ref(false);
const streamPlotContainer = ref(null);
const streamWindowSize = ref(30.0); // 默认30秒，用于控制x轴显示范围
const currentTimeRange = ref({ start: 0, end: 30 }); // 当前显示的时间范围
const isStreaming = computed(() => SRDStreamStore.isStreaming);
const allAnnotations = computed(() => SRDStreamStore.allAnnotations);

// 存储所有接收到的数据，用于计算bias
const allReceivedData = ref({
  raw: { times: [], data: [] },
  low: { times: [], data: [] },
  high: { times: [], data: [] },
});

// 存储所有标注，用于在图表中显示
const chartAnnotations = ref([]);

// 时间参数
const timeParams = reactive({
  startTime: 0,
  stopTime: 1,
  chIdx: 0,
});

// 分析参数
const analyseParam = reactive({
  edfId: undefined,
  method: undefined,
  startTime: 0,
  stopTime: 1,
  chIdx: 0,
});

// 表格列配置
const columns = reactive([
  { key: 0, label: `EDF ID`, visible: true },
  { key: 1, label: `EDF 名称`, visible: true },
  { key: 2, label: `采样频率(Hz)`, visible: true },
  { key: 3, label: `时长(秒)`, visible: true },
  { key: 4, label: `有效通道`, visible: true },
  { key: 5, label: `有效通道数`, visible: true },
  { key: 6, label: `上传者`, visible: true },
  { key: 7, label: `上传时间`, visible: true },
]);

// 步骤状态
const stepDisabled = computed(() => ({
  step2: !analyseParam.edfId,
  step3: !analyseParam.edfId || !analyseParam.method,
  step4: !analyseParam.edfId || !analyseParam.method || !timeParamsValid.value,
}));

// 计算当前步骤
const activeStep = computed(() => {
  if (analysisCompleted.value) return 4;
  if (!analyseParam.edfId) return 0;
  if (!analyseParam.method) return 1;
  if (!timeParamsValid.value) return 2;
  return 3;
});

// 时间参数有效性
const timeParamsValid = computed(() => {
  const duration = timeParams.stopTime - timeParams.startTime;
  return (
    timeParams.startTime >= 0 &&
    timeParams.stopTime > timeParams.startTime + 1 &&
    duration <= MAX_ANALYSIS_TIME &&
    selectedChannelName.value !== "" &&
    timeParams.chIdx >= 0 &&
    timeParams.chIdx < maxChannels.value
  );
});

// 监听时间参数变化，同步到分析参数
watch(
  timeParams,
  () => {
    analyseParam.startTime = timeParams.startTime;
    analyseParam.stopTime = timeParams.stopTime;
    analyseParam.chIdx = timeParams.chIdx;

    // 如果分析时长超过限制，自动调整结束时间
    const duration = timeParams.stopTime - timeParams.startTime;
    if (duration > MAX_ANALYSIS_TIME) {
      timeParams.stopTime = timeParams.startTime + MAX_ANALYSIS_TIME;
      analyseParam.stopTime = timeParams.stopTime;
    }
  },
  { deep: true }
);

// 初始化时同步通道选择
watch(
  () => timeParams.chIdx,
  (newIdx) => {
    if (
      channelOptions.value.length > 0 &&
      newIdx >= 0 &&
      newIdx < channelOptions.value.length
    ) {
      selectedChannelName.value = channelOptions.value[newIdx];
    }
  }
);

// 监听EDF选择变化
watch(
  () => analyseParam.edfId,
  (newId) => {
    if (newId) {
      const edf = EDFStore.edfListWithCount.find((e) => e.edfId === newId);
      if (edf) {
        selectedEDF.value = edf;
        maxTime.value = edf.edfTime || 1000;
        maxChannels.value = edf.validChannelsCount || 19;
        // 重置时间参数
        timeParams.startTime = 0;
        // 使用EDF的最大时间，但不超过最大分析时间限制
        timeParams.stopTime = Math.min(maxTime.value, MAX_ANALYSIS_TIME);

        // 解析有效通道列表
        if (edf.validChannels) {
          if (typeof edf.validChannels === "string") {
            channelOptions.value = edf.validChannels
              .split(",")
              .map((ch) => ch.trim());
          } else if (Array.isArray(edf.validChannels)) {
            channelOptions.value = edf.validChannels;
          } else {
            channelOptions.value = [];
          }
        } else {
          channelOptions.value = [];
        }

        // 重置通道选择，默认选择F4
        if (channelOptions.value.length > 0) {
          const f4Index = channelOptions.value.findIndex(
            (ch) => ch.trim().toUpperCase() === "F4"
          );
          if (f4Index >= 0) {
            selectedChannelName.value = channelOptions.value[f4Index];
            timeParams.chIdx = f4Index;
          } else {
            selectedChannelName.value = channelOptions.value[0];
            timeParams.chIdx = 0;
          }
        } else {
          selectedChannelName.value = "";
          timeParams.chIdx = 0;
        }
      }
    } else {
      selectedEDF.value = null;
      channelOptions.value = [];
      selectedChannelName.value = "";
      timeParams.chIdx = 0;
    }
  }
);

/** 单选 EDF 变化 */
const handleCurrentChange = (current) => {
  analyseParam.edfId = current?.edfId;
  analysisCompleted.value = false; // 重置分析完成状态
};

/** 通道选择变化 */
const handleChannelChange = (channelName) => {
  if (channelName && channelOptions.value.length > 0) {
    const idx = channelOptions.value.indexOf(channelName);
    if (idx >= 0) {
      timeParams.chIdx = idx;
      analyseParam.chIdx = idx;
    }
  }
};

// 监听流式传输状态，当传输完成时设置进度为100%
watch(isStreaming, (newVal, oldVal) => {
  if (oldVal === true && newVal === false) {
    // 流式传输完成
    percentage.value = 100;
    analysisCompleted.value = true; // 标记分析完成
  }
});

// 开始分析（流式查看）
const handleStreamAnalyse = () => {
  if (!analyseParam.edfId) {
    window?.$modal?.msgError?.("请先选择 EDF！");
    return;
  }
  if (!analyseParam.method) {
    window?.$modal?.msgError?.("请先选择分析方法！");
    return;
  }
  if (!timeParamsValid.value) {
    const duration = timeParams.stopTime - timeParams.startTime;
    if (duration > MAX_ANALYSIS_TIME) {
      window?.$modal?.msgError?.(
        `分析时长不能超过 ${MAX_ANALYSIS_TIME} 秒（5分钟），当前为 ${duration.toFixed(
          1
        )} 秒！`
      );
    } else {
      window?.$modal?.msgError?.(
        "请选择有效的分析时段（时长至少 1 秒）和通道！"
      );
    }
    return;
  }

  // 初始化进度条
  percentage.value = 0;

  // 显示流式查看面板
  showStreamView.value = true;

  // 初始化时间范围
  currentTimeRange.start = analyseParam.startTime;
  currentTimeRange.end = Math.min(
    analyseParam.startTime + streamWindowSize.value,
    analyseParam.stopTime
  );

  // 等待 DOM 更新
  nextTick(() => {
    // 设置回调函数
    SRDStreamStore.setDrawSRDDataCallback(drawSRDData);
    SRDStreamStore.setAppendSRDDataCallback(appendSRDData);
    SRDStreamStore.setAnnotationsCallback(updateAnnotations);

    // 开始流式传输（后端使用streamWindowSize作为传输窗口大小）
    SRDStreamStore.fetchSRDData({
      edfId: analyseParam.edfId,
      method: analyseParam.method,
      startTime: analyseParam.startTime,
      stopTime: analyseParam.stopTime,
      chIdx: analyseParam.chIdx,
      windowSize: streamWindowSize.value, // 使用配置的窗口大小
    });
  });
};

// 关闭流式查看
const closeStreamView = () => {
  showStreamView.value = false;
  SRDStreamStore.reset();
  chartAnnotations.value = [];
  // 重置累积的数据
  allReceivedData.value = {
    raw: { times: [], data: [] },
    low: { times: [], data: [] },
    high: { times: [], data: [] },
  };
  // 重置进度条和分析完成状态
  percentage.value = 0;
  analysisCompleted.value = false;
  if (streamPlotContainer.value) {
    Plotly.purge(streamPlotContainer.value);
  }
  // 重置初始绘制标志
  SRDStreamStore.resetInitialDraw();
};

// 更新进度条
const updateProgress = (plotData) => {
  const totalDuration = analyseParam.stopTime - analyseParam.startTime;
  if (totalDuration <= 0) {
    percentage.value = 0;
    return;
  }

  // 计算当前已处理的时间范围
  // plotData.time 是当前窗口的开始时间，plotData.windowSize 是窗口大小
  const processedTime =
    plotData.time + plotData.windowSize - analyseParam.startTime;
  const progress = Math.min((processedTime / totalDuration) * 100, 100);
  percentage.value = Math.round(progress);
};

// 更新时间范围（用于控制x轴显示）
const updateTimeRange = () => {
  if (!streamPlotContainer.value) return;

  // 直接获取当前图表的布局信息
  const gd = streamPlotContainer.value;
  if (!gd || !gd.layout) return;

  // 获取当前x轴的显示范围，如果没有则使用默认值
  const currentRange = gd.layout.xaxis?.range;
  let currentStart;

  if (
    currentRange &&
    Array.isArray(currentRange) &&
    currentRange.length === 2
  ) {
    // 使用当前x轴的起始值
    currentStart = currentRange[0];
  } else {
    // 如果没有范围信息，使用数据的最小值或开始时间
    if (allReceivedData.value.raw.times.length > 0) {
      currentStart = Math.min(...allReceivedData.value.raw.times);
    } else {
      currentStart = analyseParam.startTime;
    }
  }

  const currentEnd = Math.min(
    currentStart + streamWindowSize.value,
    analyseParam.stopTime
  );

  currentTimeRange.start = currentStart;
  currentTimeRange.end = currentEnd;

  // 更新x轴范围（基于当前x轴的起始值）
  Plotly.relayout(streamPlotContainer.value, {
    "xaxis.range": [currentStart, currentEnd],
  });
};

// 绘制初始数据
const drawSRDData = (plotData) => {
  // 重置累积的数据
  allReceivedData.value = {
    raw: { times: [], data: [] },
    low: { times: [], data: [] },
    high: { times: [], data: [] },
  };

  // 累积初始数据
  allReceivedData.value.raw.times.push(...plotData.raw.times);
  allReceivedData.value.raw.data.push(...plotData.raw.data);
  allReceivedData.value.low.times.push(...plotData.low.times);
  allReceivedData.value.low.data.push(...plotData.low.data);
  allReceivedData.value.high.times.push(...plotData.high.times);
  allReceivedData.value.high.data.push(...plotData.high.data);

  // 更新进度条
  updateProgress(plotData);

  nextTick(() => {
    requestAnimationFrame(() => {
      if (!streamPlotContainer.value) return;

      const traces = [
        {
          x: plotData.raw.times,
          y: plotData.raw.data,
          type: "scattergl",
          mode: "lines",
          name: "Raw",
          line: { width: 1 },
          xaxis: "x",
          yaxis: "y1",
        },
        {
          x: plotData.low.times,
          y: plotData.low.data,
          type: "scattergl",
          mode: "lines",
          name: "1-70Hz",
          line: { width: 1 },
          xaxis: "x",
          yaxis: "y2",
        },
        {
          x: plotData.high.times,
          y: plotData.high.data,
          type: "scattergl",
          mode: "lines",
          name: "80-450Hz",
          line: { width: 1 },
          xaxis: "x",
          yaxis: "y3",
        },
      ];

      // 添加 bias 线
      const shapes = [];
      const annotations = [];

      // 计算所有高频数据的bias（使用累积的数据）
      if (allReceivedData.value.high.data.length > 0) {
        const highData = allReceivedData.value.high.data;
        const meanVal = highData.reduce((a, b) => a + b, 0) / highData.length;
        const variance =
          highData.reduce((sum, val) => sum + Math.pow(val - meanVal, 2), 0) /
          highData.length;
        const stdVal = Math.sqrt(variance);
        const biasLower = meanVal - stdVal * 2;
        const biasUpper = meanVal + stdVal * 2;

        // 使用分析的时间范围（从startTime到stopTime），确保覆盖整个分析时间段
        const timeRange = [analyseParam.startTime, analyseParam.stopTime];

        shapes.push({
          type: "line",
          xref: "x",
          yref: "y3",
          x0: timeRange[0],
          x1: timeRange[1],
          y0: biasLower,
          y1: biasLower,
          line: { color: "red", width: 1.5, dash: "dash" },
          layer: "above",
        });
        shapes.push({
          type: "line",
          xref: "x",
          yref: "y3",
          x0: timeRange[0],
          x1: timeRange[1],
          y0: biasUpper,
          y1: biasUpper,
          line: { color: "red", width: 1.5, dash: "dash" },
          layer: "above",
        });
      }

      // 添加标注区域（使用已收到的所有标注）
      // 注意：标注应该已经通过 summary 信息接收到了
      const annotationsToShow =
        chartAnnotations.value.length > 0 ? chartAnnotations.value : [];

      console.log(
        "Drawing annotations:",
        annotationsToShow.length,
        chartAnnotations.value.length
      );

      annotationsToShow.forEach((ann) => {
        const startTime = ann.onset;
        const endTime = ann.onset + ann.duration;
        const centerTime = startTime + ann.duration / 2;

        // 标注区域（紫罗兰色，与深绿色数据线形成强烈对比）
        shapes.push({
          type: "rect",
          xref: "x",
          yref: "paper",
          x0: startTime,
          x1: endTime,
          y0: 0,
          y1: 1,
          fillcolor: "rgba(138, 43, 226, 0.5)", // 紫罗兰色
          line: { width: 0 },
          layer: "below",
        });

        // 计算文字标记的位置（在标注区域内，靠近顶部）
        // 在1-70Hz图中添加"Spike"文字标记
        const lowMax =
          plotData.low.data.length > 0 ? Math.max(...plotData.low.data) : 0;
        annotations.push({
          x: centerTime,
          y: lowMax,
          xref: "x",
          yref: "y2",
          text: "Spike",
          showarrow: false,
          font: {
            color: "red",
            size: 12,
            family: "Arial, sans-serif",
            weight: "bold",
          },
          bgcolor: "rgba(255, 255, 255, 0.9)",
          bordercolor: "red",
          borderwidth: 1,
          borderpad: 2,
        });

        // 在80-450Hz图中添加"HFO"文字标记
        const highMax =
          plotData.high.data.length > 0 ? Math.max(...plotData.high.data) : 0;
        annotations.push({
          x: centerTime,
          y: highMax,
          xref: "x",
          yref: "y3",
          text: ann.description || "HFO",
          showarrow: false,
          font: {
            color: "red",
            size: 12,
            family: "Arial, sans-serif",
            weight: "bold",
          },
          bgcolor: "rgba(255, 255, 255, 0.9)",
          bordercolor: "red",
          borderwidth: 1,
          borderpad: 2,
        });
      });

      const layout = {
        title: "SRD 流式查看",
        autosize: true,
        height: 800,
        grid: {
          rows: 3,
          columns: 1,
          pattern: "independent",
        },
        xaxis: {
          title: "Time (s)",
          domain: [0, 1],
          anchor: "y3",
          range: [currentTimeRange.start, currentTimeRange.end], // 设置初始显示范围
        },
        yaxis: {
          title: "Raw (μV)",
          domain: [0.67, 1],
          anchor: "x",
        },
        yaxis2: {
          title: "1-70Hz (μV)",
          domain: [0.34, 0.66],
          anchor: "x",
        },
        yaxis3: {
          title: "80-450Hz (μV)",
          domain: [0, 0.33],
          anchor: "x",
        },
        shapes: shapes,
        annotations: annotations,
        showlegend: true,
        legend: { x: 1.02, y: 1 },
      };

      Plotly.purge(streamPlotContainer.value);
      Plotly.newPlot(streamPlotContainer.value, traces, layout, {
        responsive: true,
        displayModeBar: true,
      }).then(() => {
        // 图表绘制完成后，再次更新标注（以防标注在图表绘制后才收到）
        if (chartAnnotations.value.length > 0) {
          updateChartAnnotations(chartAnnotations.value);
        }
      });
    });
  });
};

// 追加数据
const appendSRDData = (plotData) => {
  if (!streamPlotContainer.value) return;

  try {
    // 累积所有数据
    allReceivedData.value.raw.times.push(...plotData.raw.times);
    allReceivedData.value.raw.data.push(...plotData.raw.data);
    allReceivedData.value.low.times.push(...plotData.low.times);
    allReceivedData.value.low.data.push(...plotData.low.data);
    allReceivedData.value.high.times.push(...plotData.high.times);
    allReceivedData.value.high.data.push(...plotData.high.data);

    // 更新进度条
    updateProgress(plotData);

    // 使用 extendTraces 追加数据（移除maxPoints限制，确保所有数据都被追加）
    const traceUpdate = {
      x: [plotData.raw.times, plotData.low.times, plotData.high.times],
      y: [plotData.raw.data, plotData.low.data, plotData.high.data],
    };

    // 追加数据到图表（不限制最大点数）
    Plotly.extendTraces(streamPlotContainer.value, traceUpdate, [0, 1, 2]);

    // 更新 x 轴范围以适应新数据（使用累积的所有数据）
    const allXData = [
      ...allReceivedData.value.raw.times,
      ...allReceivedData.value.low.times,
      ...allReceivedData.value.high.times,
    ];
    if (allXData.length > 0) {
      const minTime = Math.min(...allXData);
      const maxTime = Math.max(...allXData);
      // 不强制更新x轴范围，让用户自己控制
      // Plotly.relayout(streamPlotContainer.value, {
      //   "xaxis.range": [minTime, maxTime],
      // });
    }

    // 更新标注（标注已经通过 summary 信息接收，这里只需要更新显示）
    if (chartAnnotations.value.length > 0) {
      updateChartAnnotations(chartAnnotations.value);
    }

    // 更新 bias 线（使用所有累积的高频数据计算bias）
    if (allReceivedData.value.high.data.length > 0) {
      updateBiasLinesFromAllData();
    }
  } catch (error) {
    console.error("Error appending data:", error);
  }
};

// 更新标注（从汇总信息，在数据流开始前调用）
const updateAnnotations = (annotations) => {
  console.log("All annotations received:", annotations.length, annotations);
  chartAnnotations.value = [...annotations];
  // 如果图表已经初始化，立即更新标注
  if (streamPlotContainer.value) {
    // 延迟一下，确保图表已经绘制
    nextTick(() => {
      updateChartAnnotations(chartAnnotations.value);
    });
  }
  // 如果图表还没初始化，在初始绘制时也会使用这些标注
  // drawSRDData 函数会使用 chartAnnotations.value
};

// 更新图表标注
const updateChartAnnotations = (newAnnotations) => {
  if (!streamPlotContainer.value) return;

  // 获取当前图表的 shapes 和 annotations（保留 bias 线）
  Plotly.relayout(streamPlotContainer.value, {}, (gd) => {
    const currentShapes = gd.layout.shapes || [];
    const currentAnnotations = gd.layout.annotations || [];

    // 过滤出 bias 线（type === 'line'）
    const biasLines = currentShapes.filter((s) => s.type === "line");
    // 过滤出非标注相关的 annotations（如果有其他 annotations）
    const otherAnnotations = currentAnnotations.filter(
      (a) => !a.text || (a.text !== "Spike" && a.text !== "HFO")
    );

    // 创建标注区域和文字标记
    const annotationShapes = [];
    const annotationTexts = [];

    newAnnotations.forEach((ann) => {
      const startTime = ann.onset;
      const endTime = ann.onset + ann.duration;
      const centerTime = startTime + ann.duration / 2;

      // 标注区域（紫罗兰色，与深绿色数据线形成强烈对比）
      annotationShapes.push({
        type: "rect",
        xref: "x",
        yref: "paper",
        x0: startTime,
        x1: endTime,
        y0: 0,
        y1: 1,
        fillcolor: "rgba(138, 43, 226, 0.5)", // 紫罗兰色
        line: { width: 0 },
        layer: "below",
      });

      // 获取当前数据范围用于定位文字
      // 需要找到标注时间范围内的数据最大值
      const y2Data = gd.data[1]?.y || [];
      const y3Data = gd.data[2]?.y || [];
      const y2Times = gd.data[1]?.x || [];
      const y3Times = gd.data[2]?.x || [];

      // 找到标注时间范围内的数据点
      const y2InRange = y2Data.filter((_, idx) => {
        const time = y2Times[idx];
        return time >= startTime && time <= endTime;
      });
      const y3InRange = y3Data.filter((_, idx) => {
        const time = y3Times[idx];
        return time >= startTime && time <= endTime;
      });

      const y2Max =
        y2InRange.length > 0
          ? Math.max(...y2InRange)
          : y2Data.length > 0
          ? Math.max(...y2Data)
          : 0;
      const y3Max =
        y3InRange.length > 0
          ? Math.max(...y3InRange)
          : y3Data.length > 0
          ? Math.max(...y3Data)
          : 0;

      // 在1-70Hz图中添加"Spike"文字标记
      annotationTexts.push({
        x: centerTime,
        y: y2Max,
        xref: "x",
        yref: "y2",
        text: "Spike",
        showarrow: false,
        font: {
          color: "red",
          size: 12,
          family: "Arial, sans-serif",
          weight: "bold",
        },
        bgcolor: "rgba(255, 255, 255, 0.9)",
        bordercolor: "red",
        borderwidth: 1,
        borderpad: 2,
      });

      // 在80-450Hz图中添加"HFO"文字标记
      annotationTexts.push({
        x: centerTime,
        y: y3Max,
        xref: "x",
        yref: "y3",
        text: ann.description || "HFO",
        showarrow: false,
        font: {
          color: "red",
          size: 12,
          family: "Arial, sans-serif",
          weight: "bold",
        },
        bgcolor: "rgba(255, 255, 255, 0.9)",
        bordercolor: "red",
        borderwidth: 1,
        borderpad: 2,
      });
    });

    // 合并 bias 线、标注区域和文字标记
    Plotly.relayout(streamPlotContainer.value, {
      shapes: [...biasLines, ...annotationShapes],
      annotations: [...otherAnnotations, ...annotationTexts],
    });
  });
};

// 从所有累积的数据计算bias并更新bias线
const updateBiasLinesFromAllData = () => {
  if (
    !streamPlotContainer.value ||
    allReceivedData.value.high.data.length === 0
  )
    return;

  // 计算所有高频数据的bias
  const highData = allReceivedData.value.high.data;
  const meanVal = highData.reduce((a, b) => a + b, 0) / highData.length;
  const variance =
    highData.reduce((sum, val) => sum + Math.pow(val - meanVal, 2), 0) /
    highData.length;
  const stdVal = Math.sqrt(variance);
  const biasLower = meanVal - stdVal * 2;
  const biasUpper = meanVal + stdVal * 2;

  // 使用分析的时间范围（从startTime到stopTime），确保覆盖整个分析时间段
  const timeRange = [analyseParam.startTime, analyseParam.stopTime];

  // 获取当前图表的 shapes（保留标注区域）
  Plotly.relayout(streamPlotContainer.value, {}, (gd) => {
    const currentShapes = gd.layout.shapes || [];
    // 过滤出标注区域（type === 'rect'）
    const annotationShapes = currentShapes.filter((s) => s.type === "rect");

    // 创建新的 bias 线（覆盖整个分析时间范围）
    const biasLines = [
      {
        type: "line",
        xref: "x",
        yref: "y3",
        x0: timeRange[0],
        x1: timeRange[1],
        y0: biasLower,
        y1: biasLower,
        line: { color: "red", width: 1.5, dash: "dash" },
        layer: "above",
      },
      {
        type: "line",
        xref: "x",
        yref: "y3",
        x0: timeRange[0],
        x1: timeRange[1],
        y0: biasUpper,
        y1: biasUpper,
        line: { color: "red", width: 1.5, dash: "dash" },
        layer: "above",
      },
    ];

    // 合并 bias 线和标注区域
    Plotly.relayout(streamPlotContainer.value, {
      shapes: [...biasLines, ...annotationShapes],
    });
  });
};

onMounted(() => {
  // 如果已经有选中的EDF，初始化通道列表
  if (analyseParam.edfId) {
    const edf = EDFStore.edfListWithCount.find(
      (e) => e.edfId === analyseParam.edfId
    );
    if (edf) {
      selectedEDF.value = edf;
      maxTime.value = edf.edfTime || 1000;
      maxChannels.value = edf.validChannelsCount || 19;

      // 解析有效通道列表
      if (edf.validChannels) {
        if (typeof edf.validChannels === "string") {
          channelOptions.value = edf.validChannels
            .split(",")
            .map((ch) => ch.trim());
        } else if (Array.isArray(edf.validChannels)) {
          channelOptions.value = edf.validChannels;
        } else {
          channelOptions.value = [];
        }
      } else {
        channelOptions.value = [];
      }

      // 设置默认通道选择
      if (channelOptions.value.length > 0) {
        const currentIdx =
          timeParams.chIdx >= 0 &&
          timeParams.chIdx < channelOptions.value.length
            ? timeParams.chIdx
            : 0;
        selectedChannelName.value = channelOptions.value[currentIdx];
        timeParams.chIdx = currentIdx;
        analyseParam.chIdx = currentIdx;
      }
    }
  }
});

onBeforeUnmount(() => {
  // 清理资源
  closeStreamView();
});
</script>

<style lang="scss" scoped>
.empty-line {
  height: 30px;
  background: transparent;
}

.title_style {
  display: block;
  width: fit-content;
  margin: 10px auto;
  text-align: center;
}

.el-row {
  margin-bottom: 20px;
}
.el-row:last-child {
  margin-bottom: 0;
}
.el-col {
  border-radius: 4px;
}

.grid-content {
  border-radius: 4px;
  min-height: 36px;
}

::deep(.el-progress__text) {
  font-size: 15px !important;
}

.result-area {
  margin-top: 16px;
}

.stream-area {
  margin-top: 16px;
}

.stream-controls {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.srd-stream-plot {
  width: 100%;
  height: 800px;
  min-height: 600px;
}
</style>
