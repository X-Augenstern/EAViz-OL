<template>
  <div>
    <!-- 快捷问题 -->
    <div class="quick-row">
      <el-button
        v-for="item in quickList"
        :key="item"
        size="small"
        plain
        @click="onQuickClick(item)"
      >
        {{ item }}
      </el-button>
    </div>

    <!-- 输入区域 -->
    <div class="input-row">
      <!-- 上半部分：可滚动的文本区域 -->
      <div
        class="input-scroll"
        :class="{ 'has-scroll': hasScroll }"
        :style="{ height: hasScroll ? '130px' : textareaHeight + 'px' }"
      >
        <textarea
          ref="textareaRef"
          v-model="innerValue"
          class="composer-textarea"
          placeholder="请输入你的问题或需求"
          @keydown.enter.exact.prevent="onSend()"
          @input="adjustTextareaHeight"
          :disabled="loading"
          :style="{ height: textareaHeight + 'px' }"
        ></textarea>
      </div>
      <!-- 下半部分：发送按钮区域（在同一卡片内） -->
      <div class="send-row">
        <!-- 深度思考按钮 -->
        <el-button
          class="deep-thinking-btn"
          :class="{ 'is-active': isDeepThinking }"
          :disabled="loading"
          @click="toggleDeepThinking"
        >
          深度思考
        </el-button>
        <!-- 发送 / 终止 按钮：发送时显示，流式进行中则显示终止 -->
        <div class="send-action">
          <el-button
            v-if="!loading"
            type="primary"
            class="send-btn"
            :loading="loading"
            :disabled="!innerValue.trim()"
            @click="onSend()"
          >
            发送
          </el-button>

          <el-button
            v-else
            type="danger"
            class="send-btn"
            @click="onTerminate"
          >
            终止
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick, onMounted } from "vue";

const props = defineProps({
  modelValue: {
    type: String,
    default: "",
  },
  loading: {
    type: Boolean,
    default: false,
  },
  quickList: {
    type: Array,
    default: () => [
      "帮我生成本周的查房周报",
      "总结癫痫FS+综合征的最新治疗方案",
      "患BECT综合征的临床表现有哪些",
      "帮我起草随访记录",
      "有什么药可以缓解癫痫发作",
    ],
  },
  deepThinking: {
    type: Boolean,
    default: false, // 默认关闭深度思考模式
  },
});

const emits = defineEmits(["update:modelValue", "send", "terminate", "update:deepThinking"]);

const isDeepThinking = computed({
  get() {
    return props.deepThinking;
  },
  set(val) {
    emits("update:deepThinking", val);
  },
});

const toggleDeepThinking = () => {
  isDeepThinking.value = !isDeepThinking.value;
};

const textareaRef = ref(null);
const textareaHeight = ref(80); // 初始高度，约3行
const hasScroll = ref(false);

// 单行高度（根据 line-height: 1.6 和 font-size: 16px 计算）
// 实际测量：font-size 16px * line-height 1.6 = 25.6px，加上一些边距，实际约 26px
const lineHeight = 26; // 单行实际高度
const minLines = 3; // 最小行数
const maxLines = 5; // 最大行数（超过此值才显示滚动条）
const minHeight = lineHeight * minLines; // 3行：78px，取整为 80px
const maxHeight = lineHeight * maxLines; // 5行：130px

const innerValue = computed({
  get() {
    return props.modelValue;
  },
  set(val) {
    emits("update:modelValue", val);
  },
});

const adjustTextareaHeight = () => {
  nextTick(() => {
    requestAnimationFrame(() => {
      if (!textareaRef.value) return;

      const textarea = textareaRef.value;

      // 临时设置为 auto 以获取真实的 scrollHeight
      const currentHeight = textarea.style.height;
      textarea.style.height = "auto";

      // 获取内容实际需要的高度
      const scrollHeight = textarea.scrollHeight;

      // 恢复之前的高度（避免闪烁）
      if (currentHeight) {
        textarea.style.height = currentHeight;
      }

      if (scrollHeight <= minHeight) {
        // 3行及以下：固定为最小高度（3行）
        textareaHeight.value = minHeight;
        hasScroll.value = false;
      } else if (scrollHeight <= maxHeight) {
        // 3-5行之间：自动扩展高度以显示所有内容（最多5行）
        // 直接使用 scrollHeight 确保能显示所有内容
        textareaHeight.value = scrollHeight;
        hasScroll.value = false;
      } else {
        // 超过5行：固定为最大高度（5行），启用滚动条
        textareaHeight.value = maxHeight;
        hasScroll.value = true;
      }
    });
  });
};

// 监听 modelValue 变化，调整高度
watch(
  () => props.modelValue,
  () => {
    adjustTextareaHeight();
  },
  { immediate: true }
);

// 组件挂载后也调整一次高度
onMounted(() => {
  adjustTextareaHeight();
});

const onSend = (externalMessage) => {
  emits("send", externalMessage);
};

const onTerminate = () => {
  emits("terminate");
};

const onQuickClick = (text) => {
  emits("send", text);
};
</script>

<style scoped lang="scss">
.quick-row {
  display: flex;
  flex-wrap: nowrap; /* 不换行，保持一行展示 */
  justify-content: space-between; /* 按钮均匀分布，第一个和最后一个贴边 */
  width: 100%;
  /* 与输入框同宽，由外层容器控制整体左右留白，这里不再额外缩进 */
  padding: 0;
  margin-bottom: 8px;
  /* 确保不超出容器 */
  overflow: hidden;
}

.quick-row :deep(.el-button) {
  flex: 0 0 auto; /* 宽度由内容决定 */
}

.input-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: stretch;
  width: 100%;
  border-radius: 24px;
  border: 1px solid #dcdfe6;
  /* 内部留白统一在卡片内处理，避免影响整体对齐 */
  padding: 12px 20px 10px;
  background: #ffffff;
}

.input-scroll {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80px; /* 最小高度，由 JS 动态控制实际高度 */
  transition: height 0.2s ease;
  overflow: hidden; /* 防止内容溢出 */
}

.input-scroll.has-scroll {
  height: 130px !important; /* 5行的最大高度，超过5行时固定 */
  max-height: 130px;
  overflow-y: auto;
  align-items: flex-start;
  justify-content: flex-start;
}

.composer-textarea {
  width: 100%;
  min-height: 80px; /* 最小高度，由 JS 动态控制实际高度 */
  border: none;
  outline: none;
  resize: none;
  background: transparent;
  font-size: 16px;
  font-family: inherit;
  line-height: 1.6;
  color: #303133;
  overflow: hidden; /* 3-5行时隐藏滚动条 */
  transition: height 0.2s ease;
  padding: 0;
  margin: 0;
  vertical-align: middle;
  box-sizing: border-box;
}

.input-scroll.has-scroll .composer-textarea {
  overflow-y: auto; /* 超过5行时显示滚动条 */
  max-height: 130px;
}

.send-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.deep-thinking-btn {
  min-width: 80px;
  flex-shrink: 0;
  border: 1px solid #dcdfe6;
  background: #ffffff;
  color: #606266;
  border-radius: 20px;
  transition: all 0.3s ease;

  &:hover:not(:disabled) {
    border-color: #409eff;
    color: #409eff;
  }

  &.is-active {
    background: #409eff;
    border-color: #409eff;
    color: #ffffff;
  }

  &.is-active:hover:not(:disabled) {
    background: #66b1ff;
    border-color: #66b1ff;
  }
}

.send-btn {
  min-width: 80px;
  flex-shrink: 0;
}

.send-action :deep(.el-button--danger) {
  min-width: 80px;
  flex-shrink: 0;
  border-radius: 20px;
  background: #f56c6c;
  border-color: #f56c6c;
  color: #ffffff;
}

.send-action :deep(.el-button--danger):hover:not(:disabled) {
  background: #ff7b7b;
  border-color: #ff7b7b;
}

@media (max-width: 768px) {
  .input-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
