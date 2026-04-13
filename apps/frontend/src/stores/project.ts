import { defineStore } from 'pinia'
import { ref } from 'vue'

import { fetchProjects } from '@/services/projects'
import type { ProjectRead } from '@/schemas/project'

export const useProjectStore = defineStore('project', () => {
  const items = ref<ProjectRead[]>([])
  const loading = ref(false)

  async function refresh() {
    loading.value = true
    try {
      items.value = await fetchProjects()
    } finally {
      loading.value = false
    }
  }

  return {
    items,
    loading,
    refresh,
  }
})
