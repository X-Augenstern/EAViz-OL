<template>
  <div class="agent-page" :class="{ 'sidebar-opened': isSidebarOpened }">
    <!-- 上方：对话区域，独立滚动 -->
    <div class="chat-container" :class="{ 'sidebar-opened': isSidebarOpened }">
      <div v-if="lastChatId" class="chat-top-controls">
        <div
          class="chat-id-badge"
          :title="lastChatId"
          role="button"
          tabindex="0"
          @click="copyChatId"
        >
          <span class="chat-id-label">当前对话ID：</span>
          <span class="chat-id-value">{{ chatIdShort }}</span>
        </div>
        <el-button
          v-if="lastChatId"
          class="new-convo-btn"
          type="primary"
          @click="newConversation"
        >
          新建对话
        </el-button>
      </div>
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
          :deepThinking="deepThinking"
          @update:deepThinking="(val) => (deepThinking = val)"
          :loading="loading"
          @send="handleSend"
          @terminate="handleTerminate"
        />
      </div>
    </div>
    <el-backtop
      target=".chat-container"
      :right="22"
      :bottom="22"
      :visibility-height="100"
      style="z-index: 9999"
    >
      <div
        class="el-backtop__icon"
        style="
          width: 42px;
          height: 42px;
          border-radius: 10px;
          background: linear-gradient(180deg, #6fc1ff, #2f8df9);
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
          font-size: 18px;
        "
      >
        ↑
      </div>
    </el-backtop>
    <teleport to="body">
      <button
        v-show="showBackTop"
        class="teleport-backtop"
        aria-label="回到顶部"
        @click="animateScrollToTop(450)"
        title="回到顶部"
      >
        ↑
      </button>
    </teleport>
  </div>
</template>

<script setup>
import {
  ref,
  nextTick,
  watch,
  onBeforeUnmount,
  onMounted,
  computed,
} from "vue";
import { terminateAgentChat } from "@/api/agent";
import { ElMessage, ElMessageBox } from "element-plus";
import AgentComposer from "@/components/AgentComposer/index.vue";
import AgentWelcome from "@/components/AgentWelcome/index.vue";
import useAppStore from "@/store/modules/app";

defineOptions({ name: "EavizAgent" });

const messages = ref([]);
const inputMessage = ref("");
const loading = ref(false);
const messagesContainer = ref(null);
const deepThinking = ref(false); // 默认关闭深度思考模式
const lastSentMessage = ref("");

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
const lastChatId = ref(null);
const chatIdShort = computed(() => {
  const id = lastChatId.value || "";
  if (!id) return "";
  return id.length > 10 ? `${id.slice(0, 8)}...` : id;
});

const copyChatId = async () => {
  try {
    if (!lastChatId.value) return;
    await navigator.clipboard.writeText(lastChatId.value);
    ElMessage.success("chatId 已复制到剪贴板");
  } catch (e) {
    console.warn("复制 chatId 失败", e);
    ElMessage.error("复制失败");
  }
};
const sessionChatId = ref(
  localStorage.getItem("agent_session_chat_id") || null
);

onMounted(() => {
  // restore sessionChatId from storage if present
  const v = localStorage.getItem("agent_session_chat_id");
  if (v) {
    sessionChatId.value = v;
    // if there's a persisted session id, show it as the current lastChatId so UI displays badge/button
    lastChatId.value = v;
  }
});

// fallback back-to-top: show a teleported button if Element BackTop doesn't appear
const showBackTop = ref(false);
function updateBackTopVisibility() {
  try {
    showBackTop.value = window.scrollY > 120;
  } catch (e) {
    showBackTop.value = false;
  }
}
function animateScrollToTop(duration = 450) {
  const container = document.documentElement;
  const start =
    window.scrollY ||
    document.documentElement.scrollTop ||
    document.body.scrollTop ||
    0;
  if (start === 0) return;
  const startTime = performance.now();
  const easeInOutCubic = (t) =>
    t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

  function step(now) {
    const elapsed = now - startTime;
    const progress = Math.min(1, elapsed / duration);
    const eased = easeInOutCubic(progress);
    const current = Math.round(start * (1 - eased));
    try {
      window.scrollTo(0, current);
      document.documentElement.scrollTop = current;
      document.body.scrollTop = current;
    } catch (e) {}
    if (progress < 1) {
      requestAnimationFrame(step);
    }
  }

  requestAnimationFrame(step);
}
onMounted(() => {
  try {
    window.addEventListener("scroll", updateBackTopVisibility, {
      passive: true,
    });
    updateBackTopVisibility();
  } catch (e) {}
});
onBeforeUnmount(() => {
  try {
    window.removeEventListener("scroll", updateBackTopVisibility);
  } catch (e) {}
});

const scrollToBottom = () => {
  // 使用双重 nextTick 和 requestAnimationFrame 确保 DOM 完全更新
  nextTick(() => {
    requestAnimationFrame(() => {
      // 直接滚动到页面底部
      window.scrollTo({
        top: document.documentElement.scrollHeight,
        behavior: "smooth",
      });
    });
  });
};

const handleSend = async (externalMessage) => {
  const payload = externalMessage ?? inputMessage.value;
  if (!payload || !payload.trim() || loading.value) return;

  const userMessage = payload.trim();
  // 保存用户发送内容，方便用户中止后恢复编辑
  lastSentMessage.value = userMessage;
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
    eventSource = createAgentChatConnection(
      userMessage,
      deepThinking.value,
      sessionChatId.value
    );

    const assistant = {
      type: "assistant",
      content: "",
      timestamp: new Date(),
    };
    messages.value.push(assistant);
    const idx = messages.value.length - 1;

    eventSource.onmessage = (event) => {
      const data = (event.data || "").trim();
      // special initial message containing chatId
      if (data.startsWith("__CHAT_ID__:")) {
        const id = data.split(":", 2)[1];
        lastChatId.value = id;
        // if no sessionChatId persisted, save this id as sessionChatId
        if (!sessionChatId.value) {
          sessionChatId.value = id;
          try {
            localStorage.setItem("agent_session_chat_id", id);
          } catch (e) {
            console.warn("无法存储 sessionChatId", e);
          }
        }
        return;
      }
      if (data === "[DONE]") {
        loading.value = false;
        eventSource && eventSource.close();
        eventSource = null;
        scrollToBottom();
        return;
      }
      if (!data) return;

      const current = messages.value[idx];
      if (!current) {
        console.warn(
          "[Agent SSE] missing current message at idx",
          idx,
          messages.value
        );
        return;
      }
      if (current.type !== "assistant") {
        console.warn("[Agent SSE] current message is not assistant:", current);
        return;
      }
      // 检测是否是步骤头【步骤N】，如果是的话再插入换行
      const isStepHeader = /^【步骤\d+】/.test(data);
      const sep = current.content && isStepHeader ? "\n\n" : "";
      current.content = (current.content || "") + sep + data;
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
          ElMessage.error("服务连接失败，请稍后再试");
        } else {
          ElMessage.warning("连接已断开，部分内容可能未完整接收");
        }
      }
      scrollToBottom();
    };
  } catch (error) {
    console.error("创建 SSE 连接失败:", error);
    ElMessage.error("无法连接到服务，请稍后再试");
    loading.value = false;
    scrollToBottom();
  }
};

const handleTerminate = () => {
  // 用户在流式生成过程中点击终止
  (async () => {
    // 如果有 chatId，尝试告知后端转发到 Agent 进行取消
    try {
      const targetChatId = lastChatId.value || sessionChatId.value;
      if (targetChatId) {
        terminateAgentChat(targetChatId).catch((e) => {
          console.warn("terminate request failed", e);
        });
      }
    } catch (e) {
      console.warn("terminate flow error", e);
    } finally {
      if (eventSource) {
        try {
          eventSource.close();
        } catch (e) {
          console.error("关闭 EventSource 失败:", e);
        }
        eventSource = null;
      }

      loading.value = false;

      // 恢复用户输入以便修改
      if (lastSentMessage.value) {
        inputMessage.value = lastSentMessage.value;
      }

      ElMessage.warning("已终止生成，你可以修改并重新发送。");
    }
  })();
};

const newConversation = () => {
  // 询问确认后清理会话标识并重置界面
  ElMessageBox.confirm("确定要新建对话并清除当前会话吗？", "新建对话", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning",
  })
    .then(async () => {
      try {
        // 如果存在 sessionChatId，先向后端/Agent 发起 hard terminate 请求，等待完成或失败后再清理本地会话
        if (sessionChatId && sessionChatId.value) {
          try {
            await terminateAgentChat(sessionChatId.value, true);
          } catch (e) {
            console.warn(
              "newConversation terminate request failed (ignored):",
              e
            );
          }
        }
        if (eventSource) {
          try {
            eventSource.close();
          } catch (e) {
            /* ignore */
          }
          eventSource = null;
        }
        // 清空持久化的 session id
        sessionChatId.value = null;
        lastChatId.value = null;
        try {
          localStorage.removeItem("agent_session_chat_id");
        } catch (e) {
          console.warn("无法移除 sessionChatId", e);
        }
        // 重置消息与输入
        messages.value = [];
        inputMessage.value = "";
        loading.value = false;
        lastSentMessage.value = "";
      } catch (e) {
        console.warn("newConversation error", e);
      }
    })
    .catch(() => {
      // 取消则不做任何操作
    });
};

const formatMessage = (content) => {
  if (!content) return "";
  // Remove literal "data:" prefixes that may be embedded in agent messages
  // and collapse multiple blank lines to a single blank line.
  try {
    let s = content;
    // remove any occurrences of a line starting with "data:" (case-insensitive)
    s = s.replace(/(^|\n)\s*data:\s*/gi, "$1");
    // collapse more than 2 consecutive newlines to 2
    s = s.replace(/\n{3,}/g, "\n\n");
    // trim whitespace at ends
    s = s.trim();
    return s.replace(/\n/g, "<br>");
  } catch (e) {
    return content.replace(/\n/g, "<br>");
  }
};

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
  position: relative;
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

.chat-id-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 8px; /* full pill */
  background: #2f8a2f; /* pill color across whole badge */
  border: none;
  color: #ffffff;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  user-select: none;
  white-space: nowrap; /* prevent label/value wrapping */
  max-width: none;
  overflow: visible;
  flex: none;
  z-index: 61;
  transition: background-color 0.12s ease, transform 0.12s ease,
    box-shadow 0.12s ease;
}

.chat-id-label {
  color: rgba(255, 255, 255, 0.95);
  font-size: 12px;
  display: inline-block;
}
.chat-id-value {
  display: inline-block;
  background: transparent;
  color: #ffffff;
  padding: 4px 1px;
  font-weight: 600;
  font-size: 12px;
  line-height: 1;
  min-width: 0;
  text-align: center;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* hover / focus styles for badge */
.chat-id-badge:hover,
.chat-id-badge:focus {
  background: #2f7e2e;
  box-shadow: 0 8px 22px rgba(47, 141, 255, 0.08);
  transform: translateY(-1px);
  outline: none;
}
.chat-id-badge:active {
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(47, 141, 255, 0.05);
}

.chat-top-controls {
  position: absolute;
  left: -7px;
  top: 11px;
  display: flex;
  align-items: center;
  z-index: 60;
  pointer-events: auto;
  white-space: nowrap;
  padding: 4px;
  background: transparent;
}
.new-convo-btn {
  min-width: 80px;
  border-radius: 8px;
  font-size: 12px;
  white-space: nowrap;
  flex: none;
  align-self: center;
  margin-left: 8px;
  z-index: 61;
  background: #409eff;
  border-color: #409eff;
  color: #ffffff;
}
.new-convo-btn:hover:not(:disabled) {
  background: #66b1ff;
  border-color: #66b1ff;
}

.chat-id-action {
  background: #ffffff;
  border: 1px solid #d5eefa;
  color: #606266;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1;
}

/* ensure action buttons align and match badge height */
.chat-id-action,
.new-convo-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding-top: 6px;
  padding-bottom: 6px;
}

.messages {
  padding-top: 72px; /* make room for top controls */
}

/* scroll-to-top floating button */
.scroll-to-top {
  position: fixed;
  right: 22px;
  bottom: 22px;
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: linear-gradient(180deg, #6fc1ff, #2f8df9);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  cursor: pointer;
  box-shadow: 0 10px 30px rgba(47, 141, 255, 0.12);
  border: none;
  z-index: 200;
  transition: transform 0.12s ease, box-shadow 0.12s ease, opacity 0.12s ease;
}
.scroll-to-top:active {
  transform: translateY(1px) scale(0.98);
}
.scroll-to-top:hover {
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 16px 40px rgba(47, 141, 255, 0.16);
}

@media (max-width: 600px) {
  .scroll-to-top {
    right: 12px;
    bottom: 12px;
    width: 36px;
    height: 36px;
    font-size: 16px;
  }
}

/* teleport fallback backtop */
.teleport-backtop {
  position: fixed;
  right: 30px;
  bottom: 30px;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(180deg, #6fc1ff, #2f8df9);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  cursor: pointer;
  box-shadow: 0 10px 30px rgba(47, 141, 255, 0.12);
  border: none;
  z-index: 99999;
  transition: transform 0.12s ease, box-shadow 0.12s ease, opacity 0.12s ease;
}
.teleport-backtop:active {
  transform: translateY(1px) scale(0.98);
}
.teleport-backtop:hover {
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 16px 40px rgba(47, 141, 255, 0.16);
}
</style>
