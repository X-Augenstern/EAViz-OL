<template>
  <div class="app-container">
    <el-steps :active="activeStep" direction="vertical" align-center>
      <!-- 第一步：上传视频 -->
      <el-step title="请上传要分析的视频（支持格式：MP4，20FPS）">
        <template #description>
          <div style="margin-top: 16px">
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :on-change="handleFileChange"
              :show-file-list="false"
              accept="video/mp4,.mp4"
              multiple
            >
              <el-button type="primary" :disabled="loading">
                <el-icon><Upload /></el-icon>
                选择视频文件（可多选）
              </el-button>
            </el-upload>
            <div v-if="selectedVideoFiles.length" style="margin-top: 16px">
              <el-alert
                :title="`已选择 ${selectedVideoFiles.length} 个视频`"
                type="success"
                :closable="false"
                show-icon
              />
              <el-tag
                v-for="item in selectedVideoFiles"
                :key="item.uid || item.name"
                type="info"
                closable
                size="large"
                effect="plain"
                style="margin: 8px 8px 0 0"
                @close="handleRemoveFile(item.uid)"
              >
                <el-icon style="margin-right: 4px"><VideoPlay /></el-icon>
                {{ item.name }}
              </el-tag>
            </div>
            <div class="empty-line"></div>
          </div>
        </template>
      </el-step>

      <!-- 第二步：设置参数 -->
      <el-step title="设置分析参数">
        <template #description>
          <el-form :model="analyseParam" label-width="0">
            <div style="display: flex; align-items: center; height: 32px">
              <el-text style="margin-right: 12px; white-space: nowrap"
                >是否保存分析结果（无痕分析）：</el-text
              >
              <el-switch
                v-model="analyseParam.saveOutput"
                :disabled="stepDisabled.step2"
              />
            </div>
          </el-form>
          <div class="empty-line"></div>
        </template>
      </el-step>

      <!-- 第三步：开始分析 -->
      <el-step title="开始分析">
        <template #description>
          <el-button
            type="primary"
            size="large"
            :disabled="!selectedVideoFiles.length || loading"
            :loading="loading"
            @click="handleAnalyse"
          >
            <el-icon v-if="!loading"><VideoPlay /></el-icon>
            开始分析
          </el-button>
          <div v-if="loading" style="margin-top: 16px">
            <el-progress
              :percentage="percentage"
              :status="percentage === 100 ? 'success' : undefined"
            />
            <el-text
              type="info"
              size="small"
              style="display: block; margin-top: 8px"
            >
              正在处理视频，请稍候...
            </el-text>
          </div>
          <div class="empty-line"></div>
        </template>
      </el-step>
    </el-steps>

    <!-- 结果展示区 -->
    <el-card class="result-area" shadow="hover" v-if="analysisCompleted">
      <template #header>
        <div class="card-header">
          <span>分析结果</span>
        </div>
      </template>

      <el-skeleton :rows="4" animated v-if="loading" />

      <div v-else>
        <el-alert
          title="分析完成"
          type="success"
          :closable="false"
          show-icon
          style="margin-bottom: 16px"
        />

        <!-- 多视频选择器 -->
        <div v-if="videosData.length > 1" style="margin-bottom: 16px">
          <el-text style="margin-right: 12px">当前查看视频：</el-text>
          <el-select
            v-model="currentVideoIndex"
            placeholder="请选择要查看的视频"
            style="width: 320px"
            @change="handleVideoChange"
          >
            <el-option
              v-for="(video, index) in videosData"
              :key="index"
              :label="video.video_name || `视频 ${index + 1}`"
              :value="index"
            />
          </el-select>
        </div>

        <!-- 处理后的视频播放器 -->
        <div
          v-if="outputVideoUrl || analysisTextList.length"
          class="video-section"
          style="margin-bottom: 24px"
        >
          <el-card shadow="never" class="video-player-card">
            <div class="video-layout">
              <div
                v-if="outputVideoUrl"
                class="video-container"
                :class="{ 'full-width': !analysisTextList.length }"
              >
                <video
                  ref="videoPlayer"
                  controls
                  preload="metadata"
                  class="video-player"
                  @error="handleVideoError"
                  @loadedmetadata="handleVideoLoaded"
                  crossorigin="anonymous"
                >
                  <source :src="outputVideoUrl" type="video/mp4" />
                  您的浏览器不支持视频播放
                </video>
                <div v-if="videoError" style="margin-top: 8px">
                  <el-alert
                    :title="videoError"
                    type="error"
                    :closable="false"
                    show-icon
                  />
                </div>
                <div v-if="videoInfo" class="video-info">
                  <el-descriptions :column="2" size="small" border>
                    <el-descriptions-item label="时长">
                      {{ formatDuration(videoInfo.duration) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="分辨率">
                      {{ videoInfo.width }} × {{ videoInfo.height }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </div>

              <div
                v-if="analysisTextList.length"
                class="analysis-text"
                :class="{ 'no-video': !outputVideoUrl }"
              >
                <el-text
                  type="primary"
                  tag="b"
                  size="large"
                  style="display: block; margin-bottom: 12px"
                >
                  分析文本
                </el-text>
                <el-timeline>
                  <el-timeline-item
                    v-for="(text, index) in analysisTextList"
                    :key="index"
                    :timestamp="text.time"
                  >
                    {{ text.label }}
                  </el-timeline-item>
                </el-timeline>
              </div>
            </div>
          </el-card>
        </div>

        <!-- 动作识别结果表格 -->
        <div v-if="actionResults.length > 0" class="results-section">
          <el-text
            type="primary"
            tag="b"
            size="large"
            style="display: block; margin-bottom: 16px"
          >
            动作识别结果
          </el-text>
          <el-table
            :data="actionResults"
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
                <el-tag type="success" size="large">
                  {{ scope.row.action }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-else class="no-data">
          <el-empty description="暂无动作识别结果" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup name="VD">
import { reactive, ref, computed, getCurrentInstance, nextTick } from "vue";
import { eavizItemsIdx } from "../../../eaviz/config";
import { getToken } from "@/utils/auth";
import { Upload, VideoPlay } from "@element-plus/icons-vue";
import request from "@/utils/request";

const { proxy } = getCurrentInstance();
const itemIdx = eavizItemsIdx.vd;
const loading = ref(false);
const percentage = ref(0);
const analysisCompleted = ref(false);
const selectedVideoFiles = ref([]); // 保存选中的视频文件对象列表
const outputVideoUrl = ref("");
const actionResults = ref([]);
const videoError = ref("");
const videoPlayer = ref(null);
const videoInfo = ref(null);
const videosData = ref([]); // 后端返回的多视频结果
const currentVideoIndex = ref(0);
const analysisTextList = ref([]);

// 上传相关
const uploadRef = ref(null);
const baseUrl = import.meta.env.VITE_APP_BASE_API;
const headers = ref({
  Authorization: "Bearer " + getToken(),
});

// 分析参数
const analyseParam = reactive({
  saveOutput: false, // 默认不保存（无痕分析）
});

// 步骤状态
const activeStep = computed(() => {
  if (!selectedVideoFiles.value.length) return 0;
  if (analysisCompleted.value) return 3;
  if (loading.value) return 2;
  return 1;
});

const stepDisabled = computed(() => ({
  step2: !selectedVideoFiles.value.length,
  step3: !selectedVideoFiles.value.length || loading.value,
}));

// 获取文件名
function getFileName(path) {
  if (!path) return "";
  const parts = path.split("/");
  return parts[parts.length - 1];
}

// 文件选择处理（支持多文件）
function handleFileChange(file, fileList) {
  if (!fileList || !fileList.length) {
    uploadRef.value?.clearFiles();
    selectedVideoFiles.value = [];
    return;
  }

  const validFiles = [];
  for (const item of fileList) {
    const raw = item.raw || item;
    const name = raw.name || item.name;
    const size = raw.size ?? item.size ?? 0;

    const isMP4 =
      raw.type === "video/mp4" || name?.toLowerCase().endsWith(".mp4");
    const isLt100M = size / 1024 / 1024 < 100;

    if (!isMP4) {
      proxy.$modal.msgError(`文件 ${name} 不是MP4格式，已忽略`);
      continue;
    }
    if (!isLt100M) {
      proxy.$modal.msgError(`文件 ${name} 大小超过 100MB，已忽略`);
      continue;
    }

    validFiles.push({ raw, name });
  }

  if (!validFiles.length) {
    uploadRef.value?.clearFiles();
    selectedVideoFiles.value = [];
    return;
  }

  selectedVideoFiles.value = validFiles.map((f) => ({
    name: f.name,
    file: f.raw,
    uid: f.raw?.uid || `${f.name}-${Date.now()}`,
  }));
  proxy.$modal.msgSuccess(`已选择 ${selectedVideoFiles.value.length} 个视频！`);
}

function handleRemoveFile(uid) {
  const idx = selectedVideoFiles.value.findIndex((item) => item.uid === uid);
  if (idx === -1) return;
  selectedVideoFiles.value.splice(idx, 1);
  if (!selectedVideoFiles.value.length) {
    uploadRef.value?.clearFiles();
  }
}

// 开始分析
function handleAnalyse() {
  if (!selectedVideoFiles.value.length) {
    proxy.$modal.msgError("请先选择视频文件！");
    return;
  }

  loading.value = true;
  percentage.value = 10;
  analysisCompleted.value = false;
  actionResults.value = [];
  outputVideoUrl.value = "";
  videosData.value = [];
  currentVideoIndex.value = 0;

  // 使用FormData上传文件
  const formData = new FormData();
  selectedVideoFiles.value.forEach((item) => {
    formData.append("video_files", item.file);
  });
  formData.append("save_output", analyseParam.saveOutput);

  // 使用request工具上传文件
  request({
    url: "/eaviz/vd",
    method: "post",
    data: formData,
    headers: {
      "Content-Type": "multipart/form-data",
    },
    timeout: 10 * 60 * 1000, // 10分钟超时
    onUploadProgress: (progressEvent) => {
      // 上传进度（0-50%）
      if (progressEvent.total) {
        const uploadPercent = Math.round(
          (progressEvent.loaded * 50) / progressEvent.total
        );
        percentage.value = 10 + uploadPercent;
      }
    },
  })
    .then((res) => {
      const data = res?.data ?? res;
      const payload = data?.data ?? data;

      // 批量视频结果
      const videos = payload?.videos || payload?.data?.videos;
      if (Array.isArray(videos)) {
        videosData.value = videos;
      } else if (
        payload?.video_name ||
        payload?.output_url ||
        payload?.results
      ) {
        // 兼容单视频结构被包装为对象的情况
        videosData.value = [payload];
      } else {
        videosData.value = [];
      }

      const hasVideos = videosData.value.length > 0;
      if (!hasVideos) {
        outputVideoUrl.value = "";
        actionResults.value = [];
        analysisTextList.value = [];
      } else {
        currentVideoIndex.value = 0;
      }

      percentage.value = 100;
      loading.value = false;
      analysisCompleted.value = true;
      const message = payload?.message || payload?.msg || "分析完成！";
      proxy.$modal.msgSuccess(message);

      if (hasVideos) {
        nextTick(() => {
          applyCurrentVideo();
        });
      }
    })
    .catch((error) => {
      console.error("分析失败:", error);
      const errorMsg =
        error?.response?.data?.msg || error?.message || "分析失败，请重试";
      proxy.$modal.msgError(errorMsg);
      percentage.value = 0;
      loading.value = false;
      analysisCompleted.value = false;
    });
}

// 根据 currentVideoIndex 应用当前视频到播放器和表格
function applyCurrentVideo() {
  const idx = currentVideoIndex.value ?? 0;
  if (!videosData.value.length || idx < 0 || idx >= videosData.value.length) {
    outputVideoUrl.value = "";
    actionResults.value = [];
    analysisTextList.value = [];
    return;
  }

  const current = videosData.value[idx];
  const videoUrl = current.output_url || current.outputUrl;

  if (videoUrl) {
    videoError.value = "";
    if (videoUrl.startsWith("http")) {
      outputVideoUrl.value = videoUrl;
    } else if (videoUrl.startsWith("/")) {
      outputVideoUrl.value = videoUrl;
    } else {
      outputVideoUrl.value = `${baseUrl}/download/${videoUrl}`;
    }
    const cacheBustingQuery = outputVideoUrl.value.includes("?")
      ? `&ts=${Date.now()}`
      : `?ts=${Date.now()}`;
    outputVideoUrl.value += cacheBustingQuery;
    console.log("当前视频URL已设置:", outputVideoUrl.value);
    nextTick(() => {
      const vp = videoPlayer.value;
      if (vp && typeof vp.load === "function") {
        vp.load();
      }
      if (vp && typeof vp.play === "function") {
        const playPromise = vp.play();
        if (playPromise && typeof playPromise.catch === "function") {
          playPromise.catch((err) => {
            console.warn("自动播放被浏览器阻止:", err);
          });
        }
      }
    });
  } else {
    outputVideoUrl.value = "";
  }

  const rawResults = Array.isArray(current.results)
    ? current.results
    : Array.isArray(current.data?.results)
    ? current.data.results
    : [];
  actionResults.value = rawResults.map((item) => ({
    time_range: item.time_range || item.timeRange || "",
    action: item.action || "",
  }));

  analysisTextList.value = rawResults.map((item, idx) => ({
    time: item.time_range || item.timeRange || `第${idx + 1}段`,
    label: `${item.time_range || item.timeRange || ""}：${
      item.action || "无结果"
    }`,
  }));
}

function handleVideoChange() {
  applyCurrentVideo();
}

// 视频加载错误处理
function handleVideoError(event) {
  console.error("视频加载失败:", event);
  videoError.value = "视频加载失败，请检查视频文件是否存在或URL是否正确";
  videoInfo.value = null;
}

// 视频元数据加载完成
function handleVideoLoaded(event) {
  const video = event.target;
  if (video) {
    videoInfo.value = {
      duration: video.duration,
      width: video.videoWidth,
      height: video.videoHeight,
    };
    videoError.value = "";
  }
}

// 格式化视频时长
function formatDuration(seconds) {
  if (!seconds || isNaN(seconds)) return "未知";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${String(
      secs
    ).padStart(2, "0")}`;
  }
  return `${minutes}:${String(secs).padStart(2, "0")}`;
}
</script>

<style lang="scss" scoped>
.app-container {
  padding: 20px;
}

.title_style {
  display: block;
  margin-bottom: 16px;
}

.empty-line {
  height: 20px;
}

.result-area {
  margin-top: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.video-section {
  .video-player-card {
    background: #f5f5f5;
    border-radius: 8px;
  }

  .video-layout {
    display: flex;
    gap: 16px;
    align-items: flex-start;
    padding: 16px;
  }

  .video-container {
    flex: 3;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .analysis-text {
    flex: 2;
    max-height: 400px;
    overflow-y: auto;
  }

  .analysis-text.no-video {
    flex: 1;
    width: 100%;
  }

  .video-player {
    width: 100%;
    max-width: 640px;
    border-radius: 8px;
    background: #000;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  }

  .video-info {
    margin-top: 16px;
    width: 100%;
    max-width: 640px;
  }
}

.results-section {
  margin-top: 24px;
}

.no-data {
  text-align: center;
  padding: 40px 0;
}
</style>
