import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Worldbook',
    component: () => import('@/views/WorldbookView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
