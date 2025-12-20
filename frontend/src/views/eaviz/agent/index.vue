<template>
  <div class="agent-page" :class="{ 'sidebar-opened': isSidebarOpened }">
    <!-- 上方：对话区域，独立滚动 -->
    <div class="chat-container" :class="{ 'sidebar-opened': isSidebarOpened }">
      <div class="messages" ref="messagesContainer">
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          :class="['message-item', msg.type]"
        >
          <!-- 用户气泡保留 -->
          <template v-if="msg.type === 'user'">
            <div class="message-bubble">
              <div
                class="message-text"
                v-html="formatMessage(msg.content)"
              ></div>
              <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
            </div>
          </template>
          <!-- 智能体回复去掉气泡，只展示纯文本 -->
          <template v-else>
            <div class="assistant-plain">
              <div
                class="message-text"
                v-html="formatMessage(msg.content)"
              ></div>
              <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
            </div>
          </template>
        </div>

        <div v-if="loading" class="message-item assistant">
          <div class="message-bubble typing">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部：输入区，悬浮在视口底部；整体 fixed，宽度与上方对话区完全一致 -->
    <div
      class="composer"
      :class="{ 'composer-centered': messages.length === 0 }"
    >
      <div
        class="composer-inner"
        :class="{ 'sidebar-opened': isSidebarOpened }"
      >
        <AgentWelcome :visible="messages.length === 0" />
        <AgentComposer
          v-model="inputMessage"
          :loading="loading"
          @send="handleSend"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onBeforeUnmount, computed } from "vue";
import { ElMessage } from "element-plus";
import AgentComposer from "@/components/AgentComposer/index.vue";
import AgentWelcome from "@/components/AgentWelcome/index.vue";
import useAppStore from "@/store/modules/app";

defineOptions({ name: "EavizAgent" });

const messages = ref([]);
const inputMessage = ref("");
const loading = ref(false);
const messagesContainer = ref(null);

// 侧边栏状态：使用布尔，确保 class 绑定能正确触发响应式
const appStore = useAppStore();
const isSidebarOpened = computed(() => appStore.sidebar.opened);

onBeforeUnmount(() => {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
});

let eventSource = null;

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
};

const handleSend = async (externalMessage) => {
  const payload = externalMessage ?? inputMessage.value;
  if (!payload || !payload.trim() || loading.value) return;

  const userMessage = payload.trim();
  inputMessage.value = "";

  messages.value.push({
    type: "user",
    content: userMessage,
    timestamp: new Date(),
  });
  scrollToBottom();

  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
  loading.value = true;

  try {
    const { createAgentChatConnection } = await import("@/api/agent");
    eventSource = createAgentChatConnection(userMessage);

    const assistant = {
      type: "assistant",
      content: "",
      timestamp: new Date(),
    };
    const idx = messages.value.push(assistant) - 1;

    eventSource.onmessage = (event) => {
      const data = (event.data || "").trim();
      if (data === "[DONE]") {
        loading.value = false;
        eventSource && eventSource.close();
        eventSource = null;
        scrollToBottom();
        return;
      }
      if (!data) return;

      const current = messages.value[idx];
      if (!current || current.type !== "assistant") return;
      current.content = current.content ? current.content + "\n" + data : data;
      scrollToBottom();
    };

    eventSource.onerror = (error) => {
      console.error("SSE error:", error);
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
      loading.value = false;

      const current = messages.value[idx];
      if (current) {
        if (!current.content) {
          current.content = "抱歉，连接出现问题，请稍后再试。";
          ElMessage.error("服务连接失败，请稍后再试");
        } else {
          current.content += "\n\n[连接已断开]";
          ElMessage.warning("连接已断开，部分内容可能未完整接收");
        }
      }
      scrollToBottom();
    };
  } catch (error) {
    console.error("创建 SSE 连接失败:", error);
    ElMessage.error("无法连接到服务，请稍后再试");
    loading.value = false;
    messages.value.push({
      type: "assistant",
      content: "抱歉，无法连接到服务，请稍后再试。",
      timestamp: new Date(),
    });
    scrollToBottom();
  }
};

const formatMessage = (content) =>
  content ? content.replace(/\n/g, "<br>") : "";

const formatTime = (ts) => {
  if (!ts) return "";
  const d = new Date(ts);
  const h = d.getHours().toString().padStart(2, "0");
  const m = d.getMinutes().toString().padStart(2, "0");
  return `${h}:${m}`;
};

watch(
  () => messages.value.length,
  () => scrollToBottom()
);

onBeforeUnmount(() => {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
});
</script>

<style scoped lang="scss">
.agent-page {
  /* 整个页面区域，允许根据内容自然滚动 */
  min-height: calc(100vh - 84px); /* 与 hasTagsView 布局中的 app-main 匹配 */
  background: #f7f8fb;
  padding-bottom: 180px; /* 为底部固定输入框预留空间，尽量减少整体滚动条的冗余高度 */
  --sidebar-width-collapsed: 54px;
  --sidebar-width-expanded: 200px;
  --sidebar-offset: 0px;

  &.sidebar-opened {
    --sidebar-offset: calc(
      var(--sidebar-width-expanded) - var(--sidebar-width-collapsed)
    ); /* 200 - 54 = 146 */
  }
}

.chat-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 140px 24px;
  // .main-container 的 margin-left 已经处理了侧边栏偏移
  // 所以这里不需要额外的 transform
}

/* 对话区跟随页面整体滚动，不单独加内部滚动条 */

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 320px;
  color: #9094a6;
}

.empty-text {
  font-size: 16px;
}

.message-item {
  display: flex;
  margin-bottom: 16px;
}

.message-item.user {
  justify-content: flex-end;
}

.message-item.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
  font-size: 16px;
  line-height: 1.6;
}

.message-item.user .message-bubble {
  background: #4f8df9;
  color: #fff;
}

.assistant-plain {
  max-width: 70%;
  font-size: 16px;
  line-height: 1.6;
  color: #303133;
}

.message-time {
  margin-top: 4px;
  font-size: 12px;
  opacity: 0.6;
}

.message-bubble.typing {
  display: flex;
  gap: 4px;
}

.message-bubble.typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #c0c4cc;
  animation: typing 1.4s infinite;
}

.message-bubble.typing span:nth-child(2) {
  animation-delay: 0.2s;
}

.message-bubble.typing span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.7;
  }
  30% {
    transform: translateY(-8px);
    opacity: 1;
  }
}

.composer {
  /* 悬浮在视口底部，宽度与主内容区域一致（排除侧边栏宽度） */
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  border-top: none; // 去掉上下区域的分割线
  background: transparent;
  transform: translateY(0);
  transition: transform 0.35s ease;
  z-index: 10;
}

.composer-inner {
  /* 与上方 chat-container 一样宽度和左右留白，在内容区域内居中 */
  max-width: 1200px;
  margin: 0 auto;
  /* 左右各 140px，与 chat-container 完全同步，确保右侧对齐 */
  padding: 15px 140px 24px 140px;
  background: #f7f8fb;
  position: relative; /* 让欢迎语的 absolute 参考这一块 */
  // .composer 是 fixed，相对于视口，需要补偿 .main-container 的 margin-left 变化
  // 侧边栏收缩时：.main-container margin-left = 54px，中心点 = 50vw + 27px
  // 侧边栏展开时：.main-container margin-left = 200px，中心点 = 50vw + 100px
  // 所以需要从 50vw 移动到 50vw + 27px（收缩）或 50vw + 100px（展开）
  // 即：基础偏移 27px + 动态偏移 73px（展开时）
  transform: translateX(
    calc(var(--sidebar-width-collapsed) / 2 + var(--sidebar-offset) / 2)
  );
  transition: transform 0.28s ease;
}

.composer-centered .composer-inner {
  // 初始状态上移到页面中部附近，合并 transform
  transform: translate(
    calc(var(--sidebar-width-collapsed) / 2 + var(--sidebar-offset) / 2),
    -35vh
  );
}

@media (max-width: 768px) {
  .input-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
