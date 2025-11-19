<template>
  <div class="app-container">
    <el-steps :active="activeStep" direction="vertical" align-center>
      <el-step title="请选择用于分析的EDF">
        <template #description>
          <el-text type="primary" tag="b" size="large" class="title_style">
            当前可用于 ESC SD 分析的 EDF（21 通道、1000 Hz）
          </el-text>
          <el-table
            v-loading="loading"
            :data="
              EDFStore.edfListWithCount.filter(
                (edf) => edf.validChannelsCount == 21 && edf.edfSfreq == 1000
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
      <el-step title="请选择分析时段" description="选择分析时段">
        <template #description>
          <!-- <el-slider
            v-model="seletcedTime"
            :min="0"
            :max="maxTime"
            step="0.01"
            show-tooltip
            range
            @input="handleSliderInput"
          >
          </el-slider> -->
          <!-- 将事件对象（value）显式传递给处理函数 -->
          <el-row>
            <el-col v-for="idx in [0, 1]" :key="idx" :span="5">
              <div class="grid-content">
                <el-text type="primary" tag="b"
                  >{{ idx === 0 ? "开始时间：" : "结束时间：" }}
                </el-text>
                <el-input-number
                  v-model="selectedTime[idx]"
                  :min="idx === 0 ? 0 : span"
                  :max="idx === 0 ? maxTime - span : maxTime"
                  :precision="2"
                  controls-position="right"
                  :disabled="stepDisabled.step3"
                  @input="handleInputNumber(idx, $event)"
                ></el-input-number>
              </div>
            </el-col>
          </el-row>
          <div class="empty-line"></div>
        </template>
      </el-step>
      <el-step>
        <template #description>
          <el-button
            type="primary"
            style="margin-bottom: 5px"
            :disabled="stepDisabled.step4"
            @click="handleAnalyse"
            >开始分析
          </el-button>
          <el-progress
            :percentage="percentage"
            :stroke-width="15"
            striped
            striped-flow
            :duration="50"
            style="width: 74vw"
          />
        </template>
        <div class="empty-line"></div>
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

<script setup name="ESCSD">
import {
  reactive,
  ref,
  toRefs,
  watch,
  onMounted,
  onBeforeUnmount,
  nextTick,
  computed,
} from "vue";
import { eavizItemsIdx, eavizItems } from "../../../eaviz/config";
import { useEDFStore } from "../../../store/modules/edf";
import { escsdAnalyse } from "../../../api/eaviz/eaviz";

const EDFStore = useEDFStore();
const visible = ref(false);
const loading = ref(false);
const activeNames = ref;
const itemIdx = eavizItemsIdx.escsd;
const maxTime = ref(1000);
const span = eavizItems[itemIdx].span;
const selectedTime = ref([0, span]);
const percentage = ref(0);
const resultImages = ref([]); // 分析结果图片
const selectedTimeValid = computed(() => {
  const [start, end] = selectedTime.value;
  return (
    typeof start === "number" &&
    typeof end === "number" &&
    !Number.isNaN(start) &&
    !Number.isNaN(end) &&
    end > start
  );
});
const activeStep = computed(() => {
  if (!analyseParam.edfId) return 0;
  if (!analyseParam.method) return 1;
  if (!selectedTimeValid.value) return 2;
  return 3;
});
const stepDisabled = computed(() => ({
  step2: !analyseParam.edfId,
  step3: !analyseParam.edfId || !analyseParam.method,
  step4:
    !analyseParam.edfId || !analyseParam.method || !selectedTimeValid.value,
}));

watch(
  () => selectedTime.value[0],
  (newVal) => {
    analyseParam.startTime = newVal;
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
});

/** 单选项发生变化  */
const handleCurrentChange = (current) => {
  analyseParam.edfId = current.edfId;
};

/** 自动调整滑块的结束时间 */
// const handleSliderInput = (newValue) => {
//   if (newValue[1] - newValue[0] !== 4)
//     selectedTime.value = [newValue[0], newValue[0] + 4];
// };

/** 自动调整另一端的值 */
const handleInputNumber = (idx, value) => {
  if (idx === 0) selectedTime.value = [value, value + span];
  else selectedTime.value = [value - span, value];
};

// 开始分析
const handleAnalyse = () => {
  if (stepDisabled.value.step4) return;
  loading.value = true;
  percentage.value = 10;
  // 组装参数，包含起止时间与方法
  const payload = { ...analyseParam };
  payload.startTime = selectedTime.value[0];
  payload.endTime = selectedTime.value[1];

  escsdAnalyse(payload)
    .then((res) => {
      // 兼容不同的返回结构：可能是 {code, data:{...}} 或直接 {...}
      const data = res?.data ?? res;

      // 处理图片数据：后端返回的 images 数组
      if (Array.isArray(data?.images)) {
        resultImages.value = data.images.map((url) => {
          // 如果URL已经是完整路径，直接返回
          if (url.startsWith("http")) {
            return url;
          }
          // 后端现在返回包含 root_path 的URL，直接使用即可
          console.log("后端返回的图片URL:", url);
          return url;
        });
      } else {
        console.log("没有找到图片数据");
        resultImages.value = [];
      }

      // 图表相关数据暂时不需要处理

      percentage.value = 100;
      loading.value = false;
    })
    .catch((error) => {
      console.error("分析失败:", error);
      resultImages.value = [];
      percentage.value = 0;
      loading.value = false;
    });
};

// 组件挂载时的初始化
onMounted(() => {
  // 可以在这里添加其他初始化逻辑
});

// 图片加载成功事件
const onImageLoad = (idx) => {
  console.log(`图片 ${idx} 加载成功`);
};

// 图片加载失败事件
const onImageError = (idx, imgUrl) => {
  console.error(`图片 ${idx} 加载失败:`, imgUrl);
};

onBeforeUnmount(() => {
  // 清理资源
});
</script>

<style lang="scss" scoped>
.empty-line {
  height: 30px; /* 设置空行的高度以增加间距 */
  background: transparent; /* 确保没有颜色影响布局 */
}

.title_style {
  display: block; /* 确保元素为块级元素 */
  width: fit-content;
  margin: 10px auto; /* 水平居中 */
  text-align: center; /* 确保文本内容居中 */
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

/* 使用 :deep(<inner-selector>) 覆盖 el-progress 组件的百分比文字样式 */
:deep(.el-progress__text) {
  font-size: 15px !important; /* 设置百分比文字的大小，例如12px */
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
}

.image-section {
  margin-top: 16px;
}

.no-data {
  text-align: center;
  padding: 40px 0;
}
</style>