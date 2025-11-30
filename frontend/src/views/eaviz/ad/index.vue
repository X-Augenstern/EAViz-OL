<template>
  <div class="app-container">
    <el-steps :active="activeStep" direction="vertical" align-center>
      <!-- 第一步：选择EDF -->
      <el-step title="请选择用于分析的EDF">
        <template #description>
          <el-text type="primary" tag="b" size="large" class="title_style">
            当前可用于 AD 分析的 EDF（19通道、1000Hz）
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
          <div class="ad-models">
            <el-radio-group
              v-model="analyseParam.method"
              class="ad-model-grid"
              :disabled="stepDisabled.step2"
            >
              <el-radio
                v-for="obj in eavizItems[itemIdx].methods"
                :key="obj.name"
                :label="obj.name"
                border
                class="ad-model-grid__item"
              >
                <div class="ad-model-grid__title">
                  {{ formatModelName(obj.name) }}
                </div>
                <div class="ad-model-grid__desc">{{ obj.description }}</div>
              </el-radio>
            </el-radio-group>
          </div>
          <div class="empty-line"></div>
        </template>
      </el-step>

      <!-- 第三步：选择节律（PSD 频带） -->
      <el-step title="请选择节律频带" description="PSDEnum.FREQ_BANDS 对应节律">
        <template #description>
          <el-row>
            <el-col :span="24">
              <div class="grid-content">
                <el-radio-group
                  v-model="analyseParam.fbIdx"
                  style="margin-left: 16px"
                  :disabled="stepDisabled.step3"
                >
                  <el-radio
                    v-for="band in freqBands"
                    :key="band.value"
                    :label="band.value"
                  >
                    {{ band.label }}
                    <template v-if="band.range">
                      ({{ band.range[0] }}–{{ band.range[1] }} Hz)
                    </template>
                  </el-radio>
                </el-radio-group>
              </div>
            </el-col>
          </el-row>
          <div class="empty-line"></div>
        </template>
      </el-step>

      <!-- 第四步：选择伪迹类型 -->
      <el-step
        title="请选择伪迹类型（可多选）"
        description="gogogo.Art_Dec 中各 artifact description"
      >
        <template #description>
          <el-row>
            <el-col :span="24">
              <div class="grid-content">
                <el-checkbox-group
                  v-model="selectedArtifacts"
                  style="display: block; margin-top: 10px"
                  :disabled="stepDisabled.step4"
                >
                  <el-checkbox
                    v-for="art in artifactOptions"
                    :key="art.value"
                    :label="art.value"
                  >
                    {{ art.label }}（{{ art.description }}）
                  </el-checkbox>
                </el-checkbox-group>
              </div>
            </el-col>
          </el-row>
          <div class="empty-line"></div>
        </template>
      </el-step>

      <!-- 第五步：选择分析时段 -->
      <el-step>
        <template #title>请选择分析时段</template>
        <template #description>
          <el-row style="margin-bottom: 16px">
            <el-col v-for="idx in [0, 1]" :key="idx" :span="5">
              <div class="grid-content">
                <el-text type="primary" tag="b">
                  {{ idx === 0 ? "开始时间：" : "结束时间：" }}
                </el-text>
                <el-input-number
                  v-model="selectedTime[idx]"
                  :min="idx === 0 ? 0 : span"
                  :max="idx === 0 ? maxTime - span : maxTime"
                  :precision="0"
                  :step="1"
                  controls-position="right"
                  :disabled="stepDisabled.step5"
                  @input="handleInputNumber(idx, $event)"
                ></el-input-number>
              </div>
            </el-col>
          </el-row>
          <div class="empty-line"></div>
        </template>
      </el-step>

      <!-- 第六步：开始分析 -->
      <el-step>
        <template #description>
          <el-button
            type="primary"
            style="margin-bottom: 5px"
            :disabled="stepDisabled.step6"
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

<script setup name="AD">
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
import { adAnalyse } from "../../../api/eaviz/eaviz";

const EDFStore = useEDFStore();
const loading = ref(false);
const itemIdx = eavizItemsIdx.ad;
const maxTime = ref(1000);
const span = eavizItems[itemIdx].span;
const toInt = (value) => {
  const numberVal = Number(value);
  return Number.isNaN(numberVal) ? 0 : Math.round(numberVal);
};
const selectedTime = ref([0, span]);
const selectedTimeValid = computed(() => {
  const [start, end] = selectedTime.value.map((val) => toInt(val));
  return Number.isInteger(start) && Number.isInteger(end) && end > start;
});
const percentage = ref(0);
const resultImages = ref([]); // 分析结果图片
const analysisCompleted = ref(false); // 分析是否完成

// PSDEnum.FREQ_BANDS & FREQ_LABELS（与后端配置保持一致）
const freqBands = ref([
  { value: 0, label: "All" },
  { value: 1, label: "Delta", range: [0, 4] },
  { value: 2, label: "Theta", range: [4, 8] },
  { value: 3, label: "Alpha", range: [8, 12] },
  { value: 4, label: "Beta", range: [12, 30] },
  { value: 5, label: "Gamma", range: [30, 45] },
]);

// arti_list 对应 gogogo.Art_Dec 中的各个 artifact 类别
// 数值为传给后端的 num，label/description 用于前端展示
const artifactOptions = ref([
  { value: 0, label: "Normal", description: "正常脑电" },
  { value: 1, label: "EB", description: "Eye Blinking，眨眼伪迹" },
  { value: 2, label: "FE", description: "Frontal EMG，额区肌电" },
  { value: 3, label: "CE", description: "Chew EMG，咀嚼伪迹" },
  { value: 4, label: "TE", description: "Temporal EMG，颞区肌电" },
  { value: 5, label: "Unclear", description: "异常脑电" },
]);

// 选中的伪迹列表（实际传给后端的是 value 数组）
const selectedArtifacts = ref([1, 2, 3, 4]); // 默认勾选常见伪迹

const formatModelName = (name) =>
  typeof name === "string" ? name.replace(/_/g, " + ") : "";

watch(
  () => selectedTime.value[0],
  (newVal) => {
    analyseParam.startTime = toInt(newVal);
  }
);

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
  fbIdx: undefined,
  artiList: [],
});

const stepCompletion = computed(() => {
  const step1Done = !!analyseParam.edfId;
  const step2Done = step1Done && !!analyseParam.method;
  const step3Done =
    step2Done &&
    analyseParam.fbIdx !== undefined &&
    analyseParam.fbIdx !== null;
  const step4Done = step3Done && selectedArtifacts.value.length > 0;
  const step5Done = step4Done && selectedTimeValid.value;
  const step6Done = analysisCompleted.value;

  let currentStep = 5;
  if (!step1Done) currentStep = 0;
  else if (!step2Done) currentStep = 1;
  else if (!step3Done) currentStep = 2;
  else if (!step4Done) currentStep = 3;
  else if (!step5Done) currentStep = 4;
  else if (step6Done) currentStep = 6;

  return {
    step1Done,
    step2Done,
    step3Done,
    step4Done,
    step5Done,
    step6Done,
    currentStep,
  };
});

const activeStep = computed(() => stepCompletion.value.currentStep);

const stepDisabled = computed(() => ({
  step2: !stepCompletion.value.step1Done,
  step3: !stepCompletion.value.step2Done,
  step4: !stepCompletion.value.step3Done,
  step5: !stepCompletion.value.step4Done,
  step6: !stepCompletion.value.step5Done,
}));

/** 单选 EDF 变化 */
const handleCurrentChange = (current) => {
  analyseParam.edfId = current?.edfId;
  analysisCompleted.value = false; // 重置分析完成状态
};

/** 自动调整另一端的值（保证时长 = span） */
const handleInputNumber = (idx, value) => {
  const normalized = toInt(value);
  if (idx === 0) selectedTime.value = [normalized, normalized + span];
  else selectedTime.value = [normalized - span, normalized];
};

// 开始分析
const handleAnalyse = () => {
  if (!analyseParam.edfId) {
    window?.$modal?.msgError?.("请先选择 EDF！");
    return;
  }
  if (!analyseParam.method) {
    window?.$modal?.msgError?.("请先选择 AD 模型！");
    return;
  }
  if (analyseParam.fbIdx === undefined || analyseParam.fbIdx === null) {
    window?.$modal?.msgError?.("请先选择节律频带！");
    return;
  }
  if (!selectedArtifacts.value.length) {
    window?.$modal?.msgError?.("请至少选择一种伪迹类型！");
    return;
  }
  if (!selectedTimeValid.value) {
    window?.$modal?.msgError?.("请选择有效的分析时段！");
    return;
  }

  loading.value = true;
  percentage.value = 10;
  analysisCompleted.value = false; // 重置分析完成状态，开始新的分析

  // 组装参数
  const payload = {
    edfId: analyseParam.edfId,
    method: analyseParam.method,
    startTime: toInt(selectedTime.value[0]),
    fbIdx: analyseParam.fbIdx,
    artiList: selectedArtifacts.value,
  };

  adAnalyse(payload)
    .then((res) => {
      const data = res?.data ?? res;

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
      analysisCompleted.value = true; // 标记分析完成
    })
    .catch((error) => {
      console.error("AD 分析失败:", error);
      resultImages.value = [];
      percentage.value = 0;
      loading.value = false;
      analysisCompleted.value = false;
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

.ad-models {
  width: 100%;
}

.ad-model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.ad-model-grid__item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  width: 100%;
  text-align: left;
  white-space: normal;
  line-height: 1.4;
  color: #606266;
  background-color: #fff;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.ad-model-grid__item.is-bordered {
  padding: 14px 16px;
  min-height: 110px;
}

.ad-model-grid__item.is-bordered.is-checked {
  border-color: #409eff;
  background-color: #409eff;
  color: #fff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.ad-model-grid__title {
  font-weight: 600;
  font-size: 14px;
  color: #606266;
}

.ad-model-grid__desc {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}

.ad-model-grid__item.is-bordered.is-checked .ad-model-grid__title,
.ad-model-grid__item.is-bordered.is-checked .ad-model-grid__desc {
  color: #fff;
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
</style>
