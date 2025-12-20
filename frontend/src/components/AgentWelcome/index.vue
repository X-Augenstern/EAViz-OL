<template>
  <div class="welcome-text">
    {{ displayText }}
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from "vue";

const props = defineProps({
  text: {
    type: String,
    default: "我是智慧医疗助手，有什么可以帮助您的吗？",
  },
  visible: {
    type: Boolean,
    default: true,
  },
});

const displayText = ref("");
let typingIndex = 0;
let typingTimer = null;

const clearTyping = () => {
  if (typingTimer) {
    clearInterval(typingTimer);
    typingTimer = null;
  }
};

const startTyping = () => {
  if (typingTimer || !props.visible) return;
  clearTyping();
  typingIndex = 0;
  displayText.value = "";

  typingTimer = setInterval(() => {
    // 如果不可见，停止打字机并清空
    if (!props.visible) {
      clearTyping();
      displayText.value = "";
      return;
    }

    if (typingIndex < props.text.length) {
      typingIndex++;
    } else {
      typingIndex = 0; // 完成一轮后重新开始
    }
    displayText.value = props.text.slice(0, typingIndex);
  }, 250);
};

// 监听 visible 变化
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      startTyping();
    } else {
      clearTyping();
      displayText.value = "";
    }
  },
  { immediate: true }
);

// 监听 text 变化，重新开始打字机效果
watch(
  () => props.text,
  () => {
    if (props.visible) {
      startTyping();
    }
  }
);

onMounted(() => {
  if (props.visible) {
    startTyping();
  }
});

onBeforeUnmount(() => {
  clearTyping();
});
</script>

<style scoped lang="scss">
.welcome-text {
  position: absolute;
  // 相对于父容器 .composer-inner 的 padding box 居中
  // 由于父容器会根据侧边栏状态移动，欢迎语会自动跟随并保持居中
  left: 50%;
  top: 0;
  transform: translate(-50%, -160%);
  font-size: 26px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  // 确保过渡动画与父容器同步
  transition: transform 0.28s ease;
}
</style>
