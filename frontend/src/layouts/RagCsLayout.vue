<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const navItems = [
  { path: '/rag-cs/chat', label: '💬 对话' },
  { path: '/rag-cs/phones', label: '📱 机型库' },
  { path: '/rag-cs/about', label: 'ℹ️ 说明' }
]

const activePath = computed(() => route.path)
</script>

<template>
  <section class="rag-shell">
    <header class="rag-shell__header">
      <h1 class="rag-shell__title">💬 智能客服 · 手机导购</h1>
      <p class="rag-shell__version">Milvus + 本机 Embedding + 远程 Ollama</p>
    </header>

    <nav class="rag-shell__nav" aria-label="智能客服导航">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="rag-shell__nav-link"
        :class="{ 'rag-shell__nav-link--active': activePath === item.path }"
      >
        {{ item.label }}
      </router-link>
    </nav>

    <div class="rag-shell__content">
      <router-view />
    </div>
  </section>
</template>

<style scoped>
.rag-shell { width: 100%; max-width: 960px; margin: 0 auto; }
.rag-shell__header {
  padding: var(--space-7) 0 var(--space-5);
  border-bottom: var(--border-weak);
}
.rag-shell__title {
  font-size: var(--font-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
}
.rag-shell__version {
  margin-top: var(--space-2);
  color: var(--color-text-muted);
  font-size: var(--font-xs);
}
.rag-shell__nav {
  display: flex;
  gap: var(--space-1);
  overflow-x: auto;
  border-bottom: var(--border-weak);
  padding-top: var(--space-2);
}
.rag-shell__nav-link {
  flex: 0 0 auto;
  padding: var(--space-3) var(--space-4);
  color: var(--color-text-secondary);
  font-size: var(--font-sm);
  font-weight: var(--weight-medium);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}
.rag-shell__nav-link:hover { text-decoration: none; color: var(--color-text); }
.rag-shell__nav-link--active {
  color: var(--color-accent);
  border-bottom-color: var(--color-accent);
}
.rag-shell__content { padding: var(--space-6) 0 var(--space-8); }
</style>
