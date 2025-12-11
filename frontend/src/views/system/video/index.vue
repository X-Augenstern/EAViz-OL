<template>
  <div class="app-container">
    <!-- Video查询表单 -->
    <el-form
      :model="queryParams"
      ref="queryRef"
      :inline="true"
      v-show="showSearch"
      label-width="68px"
    >
      <el-form-item label="视频名称" prop="videoName">
        <el-input
          v-model="queryParams.videoName"
          placeholder="请输入视频名称"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="分析结果" prop="resultStatus">
        <el-select
          v-model="queryParams.resultStatus"
          placeholder="请选择分析结果"
          clearable
          style="width: 240px"
        >
          <el-option label="发作" value="seizure" />
          <el-option label="正常" value="normal" />
        </el-select>
      </el-form-item>
      <el-form-item label="上传用户" prop="uploadBy">
        <el-input
          v-model="queryParams.uploadBy"
          placeholder="请输入上传用户"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="生成时间" style="width: 308px">
        <el-date-picker
          v-model="dateRange"
          value-format="YYYY-MM-DD"
          type="daterange"
          range-separator="-"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
        ></el-date-picker>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery"
          >搜索</el-button
        >
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="danger"
          plain
          icon="Delete"
          :disabled="!hasSelect"
          @click="handleDelete"
          v-hasPermi="['system:video:remove']"
          >删除</el-button
        >
      </el-col>
      <right-toolbar
        v-model:showSearch="showSearch"
        @queryTable="getList"
        :columns="columns"
      ></right-toolbar>
    </el-row>

    <!-- 视频表格 -->
    <el-table
      v-loading="loading"
      :data="videoList"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="50" align="center" />
      <el-table-column
        :label="columns[0].label"
        align="center"
        key="videoId"
        prop="videoId"
        v-if="columns[0].visible"
      />
      <el-table-column
        :label="columns[1].label"
        align="center"
        key="videoName"
        prop="videoName"
        v-if="columns[1].visible"
        :show-overflow-tooltip="true"
      />
      <el-table-column
        :label="columns[2].label"
        align="center"
        key="videoSize"
        prop="videoSize"
        v-if="columns[2].visible"
      >
        <template #default="scope">
          <span>{{ formatSize(scope.row.videoSize) }}</span>
        </template>
      </el-table-column>
      <el-table-column
        :label="columns[3].label"
        align="center"
        key="videoTime"
        prop="videoTime"
        v-if="columns[3].visible"
        :show-overflow-tooltip="true"
      >
        <template #default="scope">
          <span>{{ formatTime(scope.row.videoTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column
        :label="columns[4].label"
        align="center"
        key="videoRes"
        prop="videoRes"
        v-if="columns[4].visible"
        width="220"
      >
        <template #default="scope">
          <div
            v-if="scope.row.videoRes"
            style="
              display: flex;
              align-items: center;
              justify-content: center;
              gap: 8px;
            "
          >
            <el-tag
              :type="
                getResultSummary(scope.row.videoRes).hasSeizure
                  ? 'danger'
                  : 'success'
              "
              size="small"
            >
              {{ getResultSummary(scope.row.videoRes).summary }}
            </el-tag>
            <el-button
              link
              type="primary"
              icon="View"
              size="small"
              @click="handleViewResults(scope.row)"
            >
              详情
            </el-button>
          </div>
          <span v-else style="color: #909399">暂无结果</span>
        </template>
      </el-table-column>
      <el-table-column
        :label="columns[5].label"
        align="center"
        key="uploadBy"
        prop="uploadBy"
        v-if="columns[5].visible"
        :show-overflow-tooltip="true"
      />
      <el-table-column
        :label="columns[6].label"
        align="center"
        key="uploadTime"
        prop="uploadTime"
        v-if="columns[6].visible"
        :show-overflow-tooltip="true"
      >
        <template #default="scope">
          <span>{{ parseTime(scope.row.uploadTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column
        label="操作"
        align="center"
        width="150"
        class-name="small-padding fixed-width"
      >
        <template #default="scope">
          <el-tooltip content="播放" placement="top">
            <el-button
              link
              type="primary"
              icon="VideoPlay"
              @click="handlePlay(scope.row)"
              v-hasPermi="['system:video:play']"
            ></el-button>
          </el-tooltip>
          <el-tooltip content="删除" placement="top">
            <el-button
              link
              type="primary"
              icon="Delete"
              @click="handleDelete(scope.row)"
              v-hasPermi="['system:video:remove']"
            ></el-button>
          </el-tooltip>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 播放对话框 -->
    <el-dialog
      title="视频预览"
      v-model="player.open"
      width="800px"
      append-to-body
    >
      <div v-if="player.url" class="video-player-wrapper">
        <video
          ref="videoPlayerRef"
          controls
          style="width: 100%; max-height: 450px"
          crossorigin="anonymous"
        >
          <source :src="player.url" type="video/mp4" />
        </video>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="player.open = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 分析结果对话框 -->
    <el-dialog
      title="分析结果详情"
      v-model="resultsDialog.open"
      width="700px"
      append-to-body
    >
      <div v-if="resultsDialog.results && resultsDialog.results.length > 0">
        <el-text
          type="primary"
          tag="b"
          size="large"
          style="display: block; margin-bottom: 16px"
        >
          动作识别结果（共 {{ resultsDialog.results.length }} 条）
        </el-text>
        <el-table
          :data="resultsDialog.results"
          border
          stripe
          style="width: 100%"
          max-height="400"
        >
          <el-table-column
            prop="time_range"
            label="时间段"
            width="200"
            align="center"
          />
          <el-table-column prop="action" label="识别动作" align="center">
            <template #default="scope">
              <el-tag
                :type="scope.row.action === 'Seizure' ? 'danger' : 'success'"
                size="large"
              >
                {{
                  scope.row.action === "Seizure"
                    ? "发作"
                    : scope.row.action === "Interictal"
                    ? "发作间期"
                    : scope.row.action
                }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else>
        <el-empty description="暂无分析结果" />
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="resultsDialog.open = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="Video">
import { onMounted, reactive, ref, toRef, nextTick } from "vue";
import { listVideo, delVideo } from "@/api/system/video";

const { proxy } = getCurrentInstance();

const videoList = ref([]);
const loading = ref(true);
const showSearch = ref(true);
const ids = ref([]);
const hasSelect = ref(false);
const total = ref(0);
const dateRange = ref([]);

// 列显隐
const columns = ref([
  { key: 0, label: `视频编号`, visible: true },
  { key: 1, label: `名称`, visible: true },
  { key: 2, label: `大小`, visible: true },
  { key: 3, label: `时长`, visible: true },
  { key: 4, label: `分析结果`, visible: true },
  { key: 5, label: `上传用户`, visible: true },
  { key: 6, label: `生成时间`, visible: true },
]);

// 查询参数
const data = reactive({
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    videoName: undefined,
    uploadBy: undefined,
    resultStatus: undefined,
  },
});
const queryParams = toRef(data, "queryParams");

// 播放器状态
const player = reactive({
  open: false,
  url: "",
});
const videoPlayerRef = ref(null);

// 分析结果对话框状态
const resultsDialog = reactive({
  open: false,
  results: [],
});

onMounted(() => {
  getList();
});

// 获取列表
function getList() {
  loading.value = true;
  listVideo(proxy.addDateRange(queryParams.value, dateRange.value)).then(
    (res) => {
      loading.value = false;
      videoList.value = res.rows;
      total.value = res.total;
    }
  );
}

// 搜索按钮操作
function handleQuery() {
  queryParams.value.pageNum = 1;
  getList();
}

// 重置按钮操作
function resetQuery() {
  dateRange.value = [];
  proxy.resetForm("queryRef");
  handleQuery();
}

// 选择
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.videoId);
  hasSelect.value = selection.length !== 0;
}

// 删除按钮操作
function handleDelete(row) {
  const videoIds = row?.videoId || ids.value.join(",");
  if (!videoIds) return;
  proxy.$modal
    .confirm('是否确认删除视频编号为"' + videoIds + '"的数据项？')
    .then(function () {
      return delVideo(videoIds);
    })
    .then(() => {
      getList();
      proxy.$modal.msgSuccess("删除成功");
    })
    .catch(() => {});
}

// 播放
function handlePlay(row) {
  if (!row.videoUrl) {
    proxy.$modal.msgWarning("该视频URL不存在");
    return;
  }
  // 加时间戳避免缓存
  const ts = Date.now();
  player.url = row.videoUrl.includes("?")
    ? `${row.videoUrl}&ts=${ts}`
    : `${row.videoUrl}?ts=${ts}`;
  player.open = true;

  nextTick(() => {
    if (videoPlayerRef.value) {
      const v = videoPlayerRef.value;
      v.load();
      v.play().catch(() => {});
    }
  });
}

// 格式化文件大小
function formatSize(size) {
  if (!size && size !== 0) return "";
  if (size < 1024) return size + " B";
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + " KB";
  if (size < 1024 * 1024 * 1024) return (size / 1024 / 1024).toFixed(1) + " MB";
  return (size / 1024 / 1024 / 1024).toFixed(1) + " GB";
}

// 格式化时长（秒转换为时分秒）
function formatTime(seconds) {
  if (!seconds && seconds !== 0) return "";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${String(
      secs
    ).padStart(2, "0")}`;
  } else {
    return `${minutes}:${String(secs).padStart(2, "0")}`;
  }
}

// 获取分析结果摘要
function getResultSummary(videoRes) {
  try {
    let results = [];
    if (videoRes) {
      if (typeof videoRes === "string") {
        results = JSON.parse(videoRes);
      } else if (Array.isArray(videoRes)) {
        results = videoRes;
      }
    }

    if (!results || results.length === 0) {
      return { summary: "暂无结果", hasSeizure: false };
    }

    const seizureCount = results.filter((r) => r.action === "Seizure").length;
    const interictalCount = results.filter(
      (r) => r.action === "Interictal"
    ).length;

    if (seizureCount > 0) {
      return { summary: `检测到${seizureCount}次发作`, hasSeizure: true };
    } else if (interictalCount > 0) {
      return { summary: `${interictalCount}段发作间期`, hasSeizure: false };
    } else {
      return { summary: `${results.length}条记录`, hasSeizure: false };
    }
  } catch (e) {
    return { summary: "解析失败", hasSeizure: false };
  }
}

// 查看分析结果
function handleViewResults(row) {
  try {
    let results = [];
    if (row.videoRes) {
      // 尝试解析JSON字符串
      if (typeof row.videoRes === "string") {
        results = JSON.parse(row.videoRes);
      } else if (Array.isArray(row.videoRes)) {
        results = row.videoRes;
      }
    }
    resultsDialog.results = results;
    resultsDialog.open = true;
  } catch (e) {
    proxy.$modal.msgError("解析分析结果失败");
    console.error("解析分析结果失败:", e);
  }
}
</script>

<style scoped>
.video-player-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>


