/* ============================================================
   RAG 智能客服 API（智能手机导购）
   ============================================================ */
import { request } from './http'

export function fetchRagHealth () {
  return request('/api/rag-cs/health')
}

export function fetchPhones (params = {}) {
  const qs = new URLSearchParams()
  if (params.brand) qs.set('brand', params.brand)
  if (params.year) qs.set('year', String(params.year))
  const suffix = qs.toString() ? `?${qs}` : ''
  return request(`/api/rag-cs/phones${suffix}`)
}

export function fetchPhone (id) {
  return request(`/api/rag-cs/phones/${encodeURIComponent(id)}`)
}

export function ingestPhones (dropExisting = false) {
  const qs = dropExisting ? '?drop_existing=true' : ''
  return request(`/api/rag-cs/ingest${qs}`, { method: 'POST' })
}

/**
 * SSE 对话。回调：
 * - onMeta({ citations, session_id })
 * - onToken(content)
 * - onDone()
 * - onError(message)
 * @returns {{ abort: () => void }}
 */
export function streamChat (message, { sessionId, onMeta, onToken, onDone, onError } = {}) {
  const controller = new AbortController()

  ;(async () => {
    try {
      const resp = await fetch('/api/rag-cs/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
        credentials: 'include',
        body: JSON.stringify({ message, session_id: sessionId || null }),
        signal: controller.signal
      })

      if (!resp.ok) {
        let detail = `请求失败 (HTTP ${resp.status})`
        try {
          const data = await resp.json()
          detail = data.detail || data.error || detail
        } catch { /* ignore */ }
        onError?.(detail)
        return
      }

      const reader = resp.body?.getReader()
      if (!reader) {
        onError?.('浏览器不支持流式响应')
        return
      }

      const decoder = new TextDecoder('utf-8')
      let buffer = ''
      let eventName = 'message'
      let dataLines = []

      const flush = () => {
        if (!dataLines.length) return
        const raw = dataLines.join('\n')
        dataLines = []
        let payload = raw
        try { payload = JSON.parse(raw) } catch { /* keep string */ }

        if (eventName === 'meta') onMeta?.(payload)
        else if (eventName === 'token') onToken?.(payload?.content ?? '')
        else if (eventName === 'done') onDone?.(payload)
        else if (eventName === 'error') onError?.(payload?.error || '生成失败')
        eventName = 'message'
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split(/\r?\n/)
        buffer = parts.pop() ?? ''

        for (const line of parts) {
          if (line === '') {
            flush()
            continue
          }
          if (line.startsWith('event:')) {
            eventName = line.slice(6).trim()
          } else if (line.startsWith('data:')) {
            dataLines.push(line.slice(5).trimStart())
          }
        }
      }
      flush()
    } catch (e) {
      if (e?.name === 'AbortError') return
      onError?.(e?.message || '网络错误')
    }
  })()

  return { abort: () => controller.abort() }
}
