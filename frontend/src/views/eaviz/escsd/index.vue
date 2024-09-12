<template>
  <div class="app-container">
    <el-steps :active="0" direction="vertical" align-center>
      <el-step title="请选择用于分析的EDF">
        <template #description>
          <el-text type="primary" tag="b" size="large" class="title_style">
            当前可用于分析的EDF
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
            <template
              v-for="(obj, idx) in eavizItems[itemIdx].methods"
              :key="idx"
            >
              <el-collapse-item :name="obj.name">
                <template #title>
                  <el-radio-group v-model="analyseParam.method" size="large">
                    <!-- 使用 @click.stop 阻止点击事件冒泡 -->
                    <el-radio-button :label="obj.name" @click.stop />
                  </el-radio-group>
                </template>
                <div>
                  {{ obj.description }}
                </div>
              </el-collapse-item>
            </template>
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
            <template v-for="idx in [0, 1]" :key="idx">
              <el-col :span="5">
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
                    @input="handleInputNumber(idx, $event)"
                  ></el-input-number>
                </div>
              </el-col>
            </template>
          </el-row>
          <div class="empty-line"></div>
        </template>
      </el-step>
      <el-step>
        <template #description>
          <el-button
            type="primary"
            style="margin-bottom: 5px"
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
  </div>
</template>

<script setup name="ESCSD">
import { reactive, ref, toRefs, watch } from "vue";
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
const percentage = ref(100);
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
  console.log(analyseParam);
  escsdAnalyse(analyseParam);
};
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
</style>