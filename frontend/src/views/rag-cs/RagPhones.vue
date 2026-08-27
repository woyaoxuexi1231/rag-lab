<script setup>
import { computed, onMounted, ref } from 'vue'
import AppButton from '../../components/AppButton.vue'
import EmptyState from '../../components/EmptyState.vue'
import LoadingState from '../../components/LoadingState.vue'
import { fetchPhones, ingestPhones } from '../../api/ragCs.js'

const loading = ref(false)
const ingesting = ref(false)
const error = ref('')
const notice = ref('')
const items = ref([])
const brand = ref('')
const year = ref('')

const brands = computed(() => {
  const set = new Set(items.value.map(p => p.brand))
  return Array.from(set).sort()
})

const filtered = computed(() => {
  return items.value.filter(p => {
    if (brand.value && p.brand !== brand.value) return false
    if (year.value && String(p.year) !== year.value) return false
    return true
  })
})

onMounted(load)

async function load () {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchPhones()
    items.value = data.items || []
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function doIngest () {
  ingesting.value = true
  notice.value = ''
  error.value = ''
  try {
    const res = await ingestPhones(true)
    notice.value = `已写入 Milvus ${res.ingested} 条`
  } catch (e) {
    error.value = e.message || '入库失败'
  } finally {
    ingesting.value = false
  }
}

function formatPrice (n) {
  if (n == null || n === 0) return '—'
  return `¥${Number(n).toLocaleString('zh-CN')}`
}
</script>

<template>
  <div class="phones-page">
    <div class="phones-page__toolbar">
      <div class="phones-page__filters">
        <label>
          <span class="label">品牌</span>
          <select v-model="brand">
            <option value="">全部</option>
            <option v-for="b in brands" :key="b" :value="b">{{ b }}</option>
          </select>
        </label>
        <label>
          <span class="label">年份</span>
          <select v-model="year">
            <option value="">全部</option>
            <option value="2024">2024</option>
            <option value="2025">2025</option>
            <option value="2026">2026</option>
          </select>
        </label>
      </div>
      <div class="phones-page__actions">
        <AppButton variant="secondary" size="sm" :disabled="loading" @click="load">🔄 刷新</AppButton>
        <AppButton variant="primary" size="sm" :loading="ingesting" @click="doIngest">📥 重建入库</AppButton>
      </div>
    </div>

    <p v-if="notice" class="phones-page__notice">{{ notice }}</p>
    <p v-if="error" class="phones-page__error" role="alert">{{ error }}</p>

    <LoadingState v-if="loading" text="⏳ 正在加载机型库…" />
    <EmptyState v-else-if="!filtered.length" text="📭 没有匹配的机型。可调整筛选，或确认后端种子数据已就绪。" />

    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>品牌</th>
            <th>机型</th>
            <th>年份</th>
            <th class="align-right">参考价</th>
            <th>处理器</th>
            <th>定位</th>
            <th>数据日期</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in filtered" :key="p.id">
            <td>{{ p.brand }}</td>
            <td>{{ p.name }}</td>
            <td class="mono">{{ p.year }}</td>
            <td class="align-right mono">{{ formatPrice(p.price_cny) }}</td>
            <td class="muted">{{ p.soc || '—' }}</td>
            <td class="muted">{{ (p.tags || []).join(' / ') || '—' }}</td>
            <td class="muted">{{ p.as_of || '—' }}</td>
          </tr>
        </tbody>
      </table>
      <p class="phones-page__count">共 {{ filtered.length }} 款</p>
    </div>
  </div>
</template>

<style scoped>
.phones-page { display: grid; gap: var(--space-4); }
.phones-page__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: var(--space-4);
  flex-wrap: wrap;
}
.phones-page__filters {
  display: flex;
  gap: var(--space-4);
  flex-wrap: wrap;
}
.phones-page__filters label {
  display: grid;
  gap: var(--space-1);
  font-size: var(--font-sm);
}
.label { color: var(--color-text-muted); font-size: var(--font-xs); }
select {
  min-width: 140px;
  padding: var(--space-2) var(--space-3);
  font: inherit;
  font-size: var(--font-sm);
  border: var(--border);
  border-radius: var(--radius);
  background: var(--color-surface);
  color: var(--color-text);
}
.phones-page__actions { display: flex; gap: var(--space-2); }
.phones-page__notice { color: var(--color-success); font-size: var(--font-sm); }
.phones-page__error { color: var(--color-error); font-size: var(--font-sm); }
.table-wrap { overflow-x: auto; border: var(--border-weak); border-radius: var(--radius-md); background: var(--color-surface); }
table { width: 100%; border-collapse: collapse; font-size: var(--font-sm); }
th, td { padding: var(--space-3) var(--space-4); border-bottom: var(--border-weak); text-align: left; vertical-align: top; }
th { color: var(--color-text-muted); font-weight: var(--weight-regular); font-size: var(--font-xs); letter-spacing: 1px; }
.align-right { text-align: right; }
.mono { font-family: var(--font-mono); }
.muted { color: var(--color-text-secondary); }
.phones-page__count {
  padding: var(--space-3) var(--space-4);
  color: var(--color-text-muted);
  font-size: var(--font-xs);
}
@media (max-width: 720px) {
  .phones-page__toolbar { align-items: stretch; }
  .phones-page__actions { justify-content: flex-start; }
}
</style>
