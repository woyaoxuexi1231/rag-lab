<script setup>
import { onMounted, ref } from 'vue'
import AppButton from '../../components/AppButton.vue'
import LoadingState from '../../components/LoadingState.vue'
import { fetchRagHealth } from '../../api/ragCs.js'

const loading = ref(false)
const error = ref('')
const health = ref(null)

onMounted(load)

async function load () {
  loading.value = true
  error.value = ''
  try {
    health.value = await fetchRagHealth()
  } catch (e) {
    error.value = e.message || '健康检查失败'
  } finally {
    loading.value = false
  }
}

function statusText (ok) {
  return ok ? '正常' : '异常'
}
</script>

<template>
  <div class="about-page">
    <section class="about-block">
      <h2>🔗 链路说明</h2>
      <ol>
        <li>用户提问进入 FastAPI。</li>
        <li>本机 CPU 使用 <code>bge-small-zh-v1.5</code> 做查询向量化。</li>
        <li>Milvus 检索 Top-K 机型文档。</li>
        <li>将检索结果拼入提示词，交给远程 Ollama（qwen2.5）流式生成。</li>
        <li>前端以 SSE 展示回答，并附带引用机型。</li>
      </ol>
    </section>

    <section class="about-block">
      <h2>💻 为何 Embedding 在本机</h2>
      <p>
        算力机为 GTX 1650（约 4GB 显存），已承载 qwen2.5 对话。
        Embedding 算力需求远低于生成，放在本机 CPU 可避免与对话模型争抢显存。
      </p>
    </section>

    <section class="about-block">
      <h2>📦 数据说明</h2>
      <p>
        知识库覆盖 2025–2026 主流品牌代表机型（非全球全 SKU）。
        价格为人民币参考价快照，可能滞后，回答中会按资料表述。
      </p>
    </section>

    <section class="about-block">
      <div class="about-block__head">
        <h2>🩺 依赖状态</h2>
        <AppButton variant="ghost" size="sm" :disabled="loading" @click="load">🔄 刷新</AppButton>
      </div>
      <LoadingState v-if="loading" text="⏳ 检查中…" />
      <p v-else-if="error" class="about-error">❌ {{ error }}</p>
      <ul v-else-if="health" class="about-status">
        <li>整体：{{ health.status }}</li>
        <li>🗄️ Milvus：{{ statusText(health.milvus?.ok) }} · {{ health.milvus?.count ?? 0 }} 条</li>
        <li>🤖 Ollama：{{ statusText(health.ollama?.ok) }} · {{ health.ollama?.model }}</li>
        <li>🧮 Embedder：{{ health.embedder?.model }} · dim {{ health.embedder?.dim }}</li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.about-page { display: grid; gap: var(--space-6); max-width: 720px; }
.about-block h2 {
  font-size: var(--font-md);
  font-weight: var(--weight-semibold);
  letter-spacing: 0;
  margin-bottom: var(--space-3);
}
.about-block p,
.about-block li {
  font-size: var(--font-sm);
  line-height: 1.7;
  color: var(--color-text-secondary);
}
.about-block ol,
.about-block ul {
  padding-left: var(--space-5);
  display: grid;
  gap: var(--space-2);
}
.about-block code {
  font-family: var(--font-mono);
  font-size: var(--font-xs);
  color: var(--color-text);
}
.about-block__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
}
.about-status { list-style: none; padding-left: 0; }
.about-error { color: var(--color-error); font-size: var(--font-sm); }
</style>
