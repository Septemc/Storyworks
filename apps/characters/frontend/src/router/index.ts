import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Characters',
    component: () => import('@/views/CharactersView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
