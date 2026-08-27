<script setup>
import { nextTick, onBeforeUnmount, ref } from 'vue'
import AppButton from '../../components/AppButton.vue'
import EmptyState from '../../components/EmptyState.vue'
import { streamChat } from '../../api/ragCs.js'

const input = ref('')
const messages = ref([])
const streaming = ref(false)
const error = ref('')
const listEl = ref(null)
let activeStream = null

const suggestions = [
  '预算 5000 左右，推荐哪些 2025–2026 旗舰？',
  '对比一下 iPhone 17 Pro Max 和小米 17 Ultra',
  '拍长焦比较强的安卓机有哪些？',
  '华为 Mate 80 Pro Max 大概多少钱？'
]

onBeforeUnmount(() => {
  activeStream?.abort()
})

async function scrollToBottom () {
  await nextTick()
  if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight
}

function useSuggestion (text) {
  input.value = text
}

async function send () {
  const text = input.value.trim()
  if (!text || streaming.value) return

  error.value = ''
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  const assistant = { role: 'assistant', content: '', citations: [], pending: true }
  messages.value.push(assistant)
  streaming.value = true
  await scrollToBottom()

  activeStream = streamChat(text, {
    onMeta (meta) {
      assistant.citations = meta?.citations || []
    },
    onToken (token) {
      assistant.content += token
      assistant.pending = false
      scrollToBottom()
    },
    onDone () {
      assistant.pending = false
      if (!assistant.content) assistant.content = '（未收到模型输出，请检查 Ollama 连接）'
      streaming.value = false
      activeStream = null
      scrollToBottom()
    },
    onError (msg) {
      assistant.pending = false
      if (!assistant.content) assistant.content = ''
      error.value = msg
      streaming.value = false
      activeStream = null
    }
  })
}

function onKeydown (e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

function stop () {
  activeStream?.abort()
  streaming.value = false
  activeStream = null
  const last = messages.value[messages.value.length - 1]
  if (last?.role === 'assistant') last.pending = false
}

function formatPrice (n) {
  if (!n) return '—'
  return `¥${Number(n).toLocaleString('zh-CN')}`
}
</script>

<template>
  <div class="chat-page">
    <div class="chat-page__intro">
      <p class="chat-page__lead">📚 基于知识库检索的智能手机导购客服。回答仅依据已入库机型资料。</p>
    </div>

    <div ref="listEl" class="chat-page__messages" role="log" aria-live="polite">
      <EmptyState v-if="!messages.length" text="还没有对话。可从下方推荐问题开始，或直接输入你的选购需求。">
        <div class="chat-page__empty">
          <p>👋 还没有对话。可从下方推荐问题开始，或直接输入你的选购需求。</p>
          <div class="chat-page__suggestions">
            <button
              v-for="s in suggestions"
              :key="s"
              type="button"
              class="chat-page__suggestion"
              @click="useSuggestion(s)"
            >
              {{ s }}
            </button>
          </div>
        </div>
      </EmptyState>

      <article
        v-for="(msg, idx) in messages"
        :key="idx"
        class="bubble"
        :class="msg.role === 'user' ? 'bubble--user' : 'bubble--assistant'"
      >
        <p class="bubble__role">{{ msg.role === 'user' ? '🙋 你' : '🤖 客服' }}</p>
        <p class="bubble__content">{{ msg.content || (msg.pending ? '正在检索并生成…' : '') }}</p>
        <ul v-if="msg.citations?.length" class="bubble__citations" aria-label="引用机型">
          <li v-for="c in msg.citations" :key="c.id">
            {{ c.brand }} {{ c.name }}
            <span class="muted">{{ formatPrice(c.price_cny) }} · score {{ c.score }}</span>
          </li>
        </ul>
      </article>
    </div>

    <p v-if="error" class="chat-page__error" role="alert">{{ error }}</p>

    <form class="chat-page__composer" @submit.prevent="send">
      <label class="sr-only" for="rag-chat-input">输入问题</label>
      <textarea
        id="rag-chat-input"
        v-model="input"
        rows="3"
        placeholder="例如：预算 6000，想要续航和影像都强的安卓机…"
        :disabled="streaming"
        @keydown="onKeydown"
      />
      <div class="chat-page__actions">
        <AppButton v-if="streaming" type="button" variant="secondary" @click="stop">⏹ 停止</AppButton>
        <AppButton type="submit" :loading="streaming" :disabled="!input.trim()">📤 发送</AppButton>
      </div>
    </form>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  min-height: calc(100vh - 220px);
}
.chat-page__lead {
  font-size: var(--font-sm);
  color: var(--color-text-secondary);
  letter-spacing: var(--tracking-body);
}
.chat-page__messages {
  flex: 1;
  min-height: 320px;
  max-height: min(58vh, 640px);
  overflow-y: auto;
  border: var(--border-weak);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.chat-page__empty {
  display: grid;
  gap: var(--space-4);
  text-align: left;
}
.chat-page__suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.chat-page__suggestion {
  font: inherit;
  font-size: var(--font-xs);
  color: var(--color-text-secondary);
  background: var(--color-surface-muted);
  border: var(--border-weak);
  border-radius: 999px;
  padding: var(--space-2) var(--space-3);
  cursor: pointer;
  text-align: left;
}
.chat-page__suggestion:hover {
  color: var(--color-accent);
  background: var(--color-accent-bg);
  border-color: var(--color-accent);
}
.bubble {
  max-width: min(720px, 100%);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  border: var(--border-weak);
}
.bubble--user {
  align-self: flex-end;
  background: var(--color-accent-bg);
  border-color: color-mix(in srgb, var(--color-accent) 25%, transparent);
}
.bubble--assistant {
  align-self: flex-start;
  background: var(--color-surface);
}
.bubble__role {
  font-size: var(--font-xs);
  color: var(--color-text-muted);
  letter-spacing: 1px;
  margin-bottom: var(--space-2);
}
.bubble__content {
  font-size: var(--font-sm);
  line-height: 1.7;
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: break-word;
}
.bubble__citations {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: var(--border-weak);
  list-style: none;
  display: grid;
  gap: var(--space-1);
  font-size: var(--font-xs);
  color: var(--color-text-secondary);
}
.muted { color: var(--color-text-muted); margin-left: var(--space-2); }
.chat-page__error {
  color: var(--color-error);
  font-size: var(--font-sm);
}
.chat-page__composer {
  display: grid;
  gap: var(--space-3);
}
.chat-page__composer textarea {
  width: 100%;
  resize: vertical;
  min-height: 84px;
  padding: var(--space-3) var(--space-4);
  font: inherit;
  font-size: var(--font-sm);
  line-height: 1.6;
  color: var(--color-text);
  background: var(--color-surface);
  border: var(--border);
  border-radius: var(--radius);
}
.chat-page__composer textarea:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: var(--focus-ring);
}
.chat-page__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
</style>
