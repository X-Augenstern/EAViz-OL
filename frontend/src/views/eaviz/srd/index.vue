<template>
  <div class="app-container">
    <el-steps :active="activeStep" direction="vertical" align-center>
      <!-- 第一步：选择EDF -->
      <el-step title="请选择用于分析的EDF">
        <template #description>
          <el-text type="primary" tag="b" size="large" class="title_style">
            当前可用于 SRD 分析的 EDF（1000 Hz）
          </el-text>
          <el-table
            v-loading="loading"
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
            :disabled="stepDisabled.step4 || loading"
            @click="handleAnalyse"
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

    <!-- 结果展示区 -->
    <el-card class="result-area" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>分析结果</span>
        </div>
      </template>

      <el-skeleton :rows="4" animated v-if="loading" />

      <div v-else>
        <el-alert
          v-if="percentage === 100"
          title="分析完成"
          type="success"
          :closable="false"
          show-icon
          style="margin-bottom: 16px"
        />

        <!-- 图片结果展示 -->
        <div v-if="resultImages.length > 0" class="image-section">
          <el-text
            type="primary"
            tag="b"
            size="large"
            style="display: block; margin-bottom: 16px"
          >
            分析结果图片
          </el-text>
          <div class="image-grid">
            <el-image
              v-for="(img, idx) in resultImages"
              :key="idx"
              :src="img"
              :preview-src-list="resultImages"
              fit="contain"
              class="result-image"
              @load="onImageLoad(idx)"
              @error="onImageError(idx, img)"
            >
              <template #error>
                <div class="image-slot">
                  图片加载失败
                  <br />
                  <small>{{ img }}</small>
                </div>
              </template>
              <template #placeholder>
                <div class="image-slot">图片加载中...</div>
              </template>
            </el-image>
          </div>
        </div>
        <div v-else class="no-data">
          <el-empty description="暂无分析结果" />
        </div>
      </div>
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
import { srdAnalyse } from "../../../api/eaviz/eaviz";
import { parseTime } from "../../../utils/ruoyi";

const EDFStore = useEDFStore();
const loading = ref(false);
const itemIdx = eavizItemsIdx.srd;
const maxTime = ref(1000);
const maxChannels = ref(19);
const percentage = ref(0);
const resultImages = ref([]); // 分析结果图片
const selectedEDF = ref(null);
const channelOptions = ref([]);
const selectedChannelName = ref("");

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

// 步骤状态（与SpiD模块保持一致）
const stepDisabled = computed(() => ({
  step2: !analyseParam.edfId,
  step3: !analyseParam.edfId || !analyseParam.method,
  step4: !analyseParam.edfId || !analyseParam.method || !timeParamsValid.value,
}));

// 计算当前步骤（用于流程图高亮，与SpiD模块保持一致）
const activeStep = computed(() => {
  if (!analyseParam.edfId) return 0;
  if (!analyseParam.method) return 1;
  if (!timeParamsValid.value) return 2;
  return 3;
});

// 时间参数有效性
const timeParamsValid = computed(() => {
  return (
    timeParams.startTime >= 0 &&
    timeParams.stopTime > timeParams.startTime + 1 &&
    selectedChannelName.value !== "" &&
    timeParams.chIdx >= 0 &&
    timeParams.chIdx < maxChannels.value
  );
});

// 图片加载事件
const onImageLoad = (idx) => {
  console.log(`图片 ${idx} 加载成功`);
};

const onImageError = (idx, imgUrl) => {
  console.error(`图片 ${idx} 加载失败:`, imgUrl);
};

// 监听时间参数变化，同步到分析参数
watch(
  timeParams,
  () => {
    analyseParam.startTime = timeParams.startTime;
    analyseParam.stopTime = timeParams.stopTime;
    analyseParam.chIdx = timeParams.chIdx;
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
        timeParams.stopTime = Math.min(1, maxTime.value);

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

        // 重置通道选择
        if (channelOptions.value.length > 0) {
          selectedChannelName.value = channelOptions.value[0];
          timeParams.chIdx = 0;
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

// 开始分析
const handleAnalyse = () => {
  if (!analyseParam.edfId) {
    window?.$modal?.msgError?.("请先选择 EDF！");
    return;
  }
  if (!analyseParam.method) {
    window?.$modal?.msgError?.("请先选择分析方法！");
    return;
  }
  if (!timeParamsValid.value) {
    window?.$modal?.msgError?.("请选择有效的分析时段（时长至少 1 秒）和通道！");
    return;
  }

  loading.value = true;
  percentage.value = 10;

  // 组装参数
  const payload = {
    edfId: analyseParam.edfId,
    method: analyseParam.method,
    startTime: analyseParam.startTime,
    stopTime: analyseParam.stopTime,
    chIdx: analyseParam.chIdx,
  };

  srdAnalyse(payload)
    .then((res) => {
      const data = res?.data ?? res;

      // 处理图片数据：后端返回的 images 数组
      if (Array.isArray(data?.images)) {
        resultImages.value = data.images.map((url) => {
          if (url.startsWith("http")) {
            return url;
          }
          return url;
        });
      } else {
        resultImages.value = [];
      }

      percentage.value = 100;
      loading.value = false;
    })
    .catch((error) => {
      console.error("SRD 分析失败:", error);
      resultImages.value = [];
      percentage.value = 0;
      loading.value = false;
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

.image-section {
  margin-top: 16px;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
  max-width: 100%;
}

.result-image {
  width: 100%;
  height: auto;
  min-height: 300px;
  background: #f6f8fa;
  border: 1px solid #ebeef5;
}

.image-slot {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #999;
  text-align: center;
  flex-direction: column;
}

.no-data {
  text-align: center;
  padding: 40px 0;
}
</style>
