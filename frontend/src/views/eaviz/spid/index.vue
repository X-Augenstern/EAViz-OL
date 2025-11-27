<template>
  <div class="app-container">
    <el-steps :active="activeStep" direction="vertical" align-center>
      <!-- 第一步：选择EDF -->
      <el-step title="请选择用于分析的EDF">
        <template #description>
          <el-text type="primary" tag="b" size="large" class="title_style">
            当前可用于 SpiD 分析的 EDF（19 通道、1000 Hz）
          </el-text>
          <el-table
            v-loading="loading"
            :data="
              EDFStore.edfListWithCount.filter(
                (edf) => edf.validChannelsCount == 19 && edf.edfSfreq == 1000
              )
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
                  <!-- 使用 @click.stop 阻止点击事件冒泡 -->
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

      <!-- 第三步：选择分析时段（根据方法动态显示） -->
      <el-step>
        <template #title>请选择分析时段</template>
        <template #description>
          <!-- Template Matching: 开始时间和结束时间 -->
          <div v-if="analyseParam.method === 'Template Matching'">
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
                    :min="timeParams.startTime + 0.3"
                    :max="maxTime"
                    :precision="1"
                    :step="0.1"
                    controls-position="right"
                    :disabled="stepDisabled.step3"
                    style="width: 100%"
                  ></el-input-number>
                </div>
              </el-col>
            </el-row>
          </div>

          <!-- Unet+ResNet34: 开始时间和30s片段数量 -->
          <div v-else-if="analyseParam.method === 'Unet+ResNet34'">
            <el-row style="margin-bottom: 16px">
              <el-col :span="5">
                <div class="grid-content">
                  <el-text type="primary" tag="b">开始时间（秒）：</el-text>
                  <el-input-number
                    v-model="timeParams.startTime"
                    :min="0"
                    :max="maxTime - timeParams.segmentCount * 30"
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
                  <el-text type="primary" tag="b">30秒片段数量：</el-text>
                  <el-input-number
                    v-model="timeParams.segmentCount"
                    :min="1"
                    :max="Math.floor((maxTime - timeParams.startTime) / 30)"
                    :precision="0"
                    :step="1"
                    controls-position="right"
                    :disabled="stepDisabled.step3"
                    style="width: 100%"
                  ></el-input-number>
                </div>
              </el-col>
              <el-col :span="12" style="margin-left: 20px">
                <div class="grid-content">
                  <el-text type="info" style="line-height: 40px">
                    结束时间：{{
                      (
                        timeParams.startTime +
                        timeParams.segmentCount * 30
                      ).toFixed(1)
                    }}
                    秒 （总时长：{{ (timeParams.segmentCount * 30).toFixed(1) }}
                    秒）
                  </el-text>
                </div>
              </el-col>
            </el-row>
          </div>

          <div v-else class="grid-content">
            <el-text type="info">请先选择分析方法</el-text>
          </div>
          <div class="empty-line"></div>
        </template>
      </el-step>

      <!-- 第四步：开始分析 -->
      <el-step>
        <template #description>
          <el-button
            type="primary"
            style="margin-bottom: 5px"
            :disabled="stepDisabled.step4"
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

        <!-- SWI 结果展示 -->
        <div v-if="swiResult !== null" style="margin-bottom: 16px">
          <el-text
            type="primary"
            tag="b"
            size="large"
            style="display: block; margin-bottom: 8px"
          >
            SWI 结果
          </el-text>
          <el-card shadow="never" body-style="{ padding: '12px' }">
            <pre class="swi-result-value"
              >{{
                typeof swiResult === "object"
                  ? JSON.stringify(swiResult, null, 2)
                  : swiResult
              }}
            </pre>
          </el-card>
        </div>

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
          <el-empty description="暂无分析结果图片" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup name="SpiD">
import {
  reactive,
  ref,
  toRefs,
  watch,
  onMounted,
  onBeforeUnmount,
  computed,
} from "vue";
import { eavizItemsIdx, eavizItems } from "../../../eaviz/config";
import { useEDFStore } from "../../../store/modules/edf";
import { spidAnalyse } from "../../../api/eaviz/eaviz";
import { parseTime } from "../../../utils/ruoyi";

const EDFStore = useEDFStore();
const loading = ref(false);
const itemIdx = eavizItemsIdx.spid;
const maxTime = ref(1000);
const percentage = ref(0);
const resultImages = ref([]); // 分析结果图片
const swiResult = ref(null); // Swi 数值结果

// 时间参数
const timeParams = reactive({
  startTime: 0,
  stopTime: 0.3, // Template Matching 默认至少 0.3s
  segmentCount: 1, // Unet+ResNet34 默认 1 个 30s 片段
});

const data = reactive({
  queryParams: {
    edfName: undefined,
    useMethod: undefined,
    uploadBy: undefined,
    uploadTime: undefined,
  },
});
const queryParams = toRefs(data).queryParams;

/** 列显隐信息 */
const columns = ref([
  { key: 0, label: `EDF编号`, visible: true },
  { key: 1, label: `名称`, visible: true },
  { key: 2, label: `采样频率`, visible: true },
  { key: 3, label: `采样时长`, visible: true },
  { key: 4, label: `有效通道`, visible: true },
  { key: 5, label: `有效通道数`, visible: true },
  { key: 6, label: `上传者`, visible: true },
  { key: 7, label: `上传时间`, visible: true },
]);

/** 分析参数 */
const analyseParam = reactive({
  edfId: undefined,
  method: undefined,
  startTime: 0,
  stopTime: 0,
});

// Template Matching 时间验证：时长至少 0.3s
const templateMatchingTimeValid = computed(() => {
  if (analyseParam.method !== "Template Matching") return false;
  const duration = timeParams.stopTime - timeParams.startTime;
  return (
    duration >= 0.3 &&
    timeParams.startTime >= 0 &&
    timeParams.stopTime > timeParams.startTime
  );
});

// Unet+ResNet34 时间验证：开始时间有效，片段数量 >= 1
const unetTimeValid = computed(() => {
  if (analyseParam.method !== "Unet+ResNet34") return false;
  return (
    timeParams.startTime >= 0 &&
    timeParams.segmentCount >= 1 &&
    timeParams.startTime + timeParams.segmentCount * 30 <= maxTime.value
  );
});

// 时间参数有效性
const timeParamsValid = computed(() => {
  if (analyseParam.method === "Template Matching") {
    return templateMatchingTimeValid.value;
  } else if (analyseParam.method === "Unet+ResNet34") {
    return unetTimeValid.value;
  }
  return false;
});

// 计算当前步骤（用于流程图高亮）
const activeStep = computed(() => {
  if (!analyseParam.edfId) return 0;
  if (!analyseParam.method) return 1;
  if (!timeParamsValid.value) return 2;
  return 3;
});

const stepDisabled = computed(() => ({
  step2: !analyseParam.edfId,
  step3: !analyseParam.edfId || !analyseParam.method,
  step4: !analyseParam.edfId || !analyseParam.method || !timeParamsValid.value,
}));

// 监听方法变化，重置时间参数
watch(
  () => analyseParam.method,
  (newMethod) => {
    if (newMethod === "Template Matching") {
      timeParams.startTime = 0;
      timeParams.stopTime = 0.3;
    } else if (newMethod === "Unet+ResNet34") {
      timeParams.startTime = 0;
      timeParams.segmentCount = 1;
    }
  }
);

// 监听开始时间变化（Unet+ResNet34），自动调整片段数量
watch(
  () => timeParams.startTime,
  (newStartTime) => {
    if (analyseParam.method === "Unet+ResNet34") {
      const maxSegments = Math.floor((maxTime.value - newStartTime) / 30);
      if (timeParams.segmentCount > maxSegments && maxSegments >= 1) {
        timeParams.segmentCount = maxSegments;
      }
    }
  }
);

// 监听时间参数变化，更新分析参数
watch(
  () => [
    timeParams.startTime,
    timeParams.stopTime,
    timeParams.segmentCount,
    analyseParam.method,
  ],
  () => {
    if (analyseParam.method === "Template Matching") {
      analyseParam.startTime = timeParams.startTime;
      analyseParam.stopTime = timeParams.stopTime;
    } else if (analyseParam.method === "Unet+ResNet34") {
      analyseParam.startTime = timeParams.startTime;
      analyseParam.stopTime =
        timeParams.startTime + timeParams.segmentCount * 30;
    }
  },
  { deep: true }
);

/** 单选 EDF 变化 */
const handleCurrentChange = (current) => {
  analyseParam.edfId = current?.edfId;
  // 可以根据 EDF 的时长更新 maxTime
  if (current?.edfTime) {
    maxTime.value = current.edfTime;
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
    if (analyseParam.method === "Template Matching") {
      window?.$modal?.msgError?.("请选择有效的分析时段（时长至少 0.3 秒）！");
    } else if (analyseParam.method === "Unet+ResNet34") {
      window?.$modal?.msgError?.("请选择有效的开始时间和片段数量！");
    }
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
  };

  spidAnalyse(payload)
    .then((res) => {
      const data = res?.data ?? res;

      // 保存 SWI 结果
      swiResult.value = data?.swi ?? null;

      if (Array.isArray(data?.images)) {
        resultImages.value = data.images.map((url) => {
          if (url.startsWith("http")) {
            return url;
          }
          console.log("后端返回的图片URL:", url);
          return url;
        });
      } else {
        console.log("没有找到图片数据");
        resultImages.value = [];
      }

      percentage.value = 100;
      loading.value = false;
    })
    .catch((error) => {
      console.error("SpiD 分析失败:", error);
      resultImages.value = [];
      percentage.value = 0;
      loading.value = false;
    });
};

onMounted(() => {
  // 这里可以根据 EDF 时长等信息动态设置 maxTime
});

// 图片事件
const onImageLoad = (idx) => {
  console.log(`图片 ${idx} 加载成功`);
};

const onImageError = (idx, imgUrl) => {
  console.error(`图片 ${idx} 加载失败:`, imgUrl);
};

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

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
  max-width: 100%;
}

.result-image {
  width: 100%;
  height: 220px;
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

.image-section {
  margin-top: 16px;
}

.no-data {
  text-align: center;
  padding: 40px 0;
}

.swi-result-value {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: "Harmony OS", "SF Mono", "Monaco", "Inconsolata", "Fira Code",
    "Droid Sans Mono", "Source Code Pro", monospace;
  font-size: 16px;
  font-weight: 500;
  line-height: 1.6;
  color: #303133;
  letter-spacing: 0.3px;
}
</style>
