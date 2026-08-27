import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/rag-cs/chat' },
  {
    path: '/rag-cs',
    component: () => import('../layouts/RagCsLayout.vue'),
    redirect: '/rag-cs/chat',
    children: [
      { path: 'chat', name: 'RagChat', component: () => import('../views/rag-cs/RagChat.vue'), meta: { title: '对话' } },
      { path: 'phones', name: 'RagPhones', component: () => import('../views/rag-cs/RagPhones.vue'), meta: { title: '机型库' } },
      { path: 'about', name: 'RagAbout', component: () => import('../views/rag-cs/RagAbout.vue'), meta: { title: '说明' } }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(import.meta.env.VITE_APP_BASE),
  routes
})

export default router
