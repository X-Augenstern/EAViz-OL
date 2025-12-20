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
      <div class="input-scroll">
        <textarea
          v-model="innerValue"
          class="composer-textarea"
          placeholder="请输入你的问题或需求"
          @keydown.enter.exact.prevent="onSend()"
          :disabled="loading"
        ></textarea>
      </div>
      <!-- 下半部分：发送按钮区域（在同一卡片内） -->
      <div class="send-row">
        <el-button
          type="primary"
          class="send-btn"
          :loading="loading"
          :disabled="!innerValue.trim()"
          @click="onSend()"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

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
});

const emits = defineEmits(["update:modelValue", "send"]);

const innerValue = computed({
  get() {
    return props.modelValue;
  },
  set(val) {
    emits("update:modelValue", val);
  },
});

const onSend = (externalMessage) => {
  emits("send", externalMessage);
};

const onQuickClick = (text) => {
  emits("send", text);
};
</script>

<style scoped lang="scss">
.quick-row {
  display: flex;
  flex-wrap: nowrap; /* 不换行，保持一行展示 */
  justify-content: flex-start; /* 宽度由文字决定，自然排布 */
  gap: 8px; /* 按钮之间固定间距 */
  width: 100%;
  /* 与输入框同宽，由外层容器控制整体左右留白，这里不再额外缩进 */
  padding: 0;
  margin-bottom: 8px;
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
  max-height: 140px;
  overflow-y: auto;
}

.composer-textarea {
  width: 100%;
  min-height: 80px;
  border: none;
  outline: none;
  resize: none;
  background: transparent;
  font-size: 16px;
  font-family: inherit;
  line-height: 1.6;
  color: #303133;
}

.send-btn {
  min-width: 80px;
}

.send-row {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .input-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
