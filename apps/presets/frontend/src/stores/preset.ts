import { defineStore } from 'pinia'
import { ref } from 'vue'
import { presetApi } from '@/api'

export interface Preset {
  id: string
  project_name: string
  name: string
  category?: string
  description?: string
  content: any
  status: string
  created_at: string
  updated_at: string
}

export const usePresetStore = defineStore('preset', () => {
  const presets = ref<Preset[]>([])
  const currentPreset = ref<Preset | null>(null)
  const loading = ref(false)
  const generating = ref(false)
  const currentProject = ref('')

  async function fetchPresets(projectName: string, category?: string) {
    loading.value = true
    currentProject.value = projectName
    try {
      const res = await presetApi.list(projectName, category)
      if (res.data.code === 200) {
        presets.value = res.data.data || []
      }
    } catch (error) {
      console.error('获取预设列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  async function fetchPreset(projectName: string, presetId: string) {
    try {
      const res = await presetApi.get(projectName, presetId)
      if (res.data.code === 200) {
        currentPreset.value = res.data.data
      }
    } catch (error) {
      console.error('获取预设详情失败:', error)
    }
  }

  async function createPreset(data: any) {
    const res = await presetApi.create(data)
    if (res.data.code === 200) {
      await fetchPresets(data.project_name)
      return res.data.data
    }
    throw new Error(res.data.message)
  }

  async function updatePreset(projectName: string, presetId: string, data: any) {
    const res = await presetApi.update(projectName, presetId, data)
    if (res.data.code === 200) {
      await fetchPresets(projectName)
      if (currentPreset.value?.id === presetId) {
        currentPreset.value = res.data.data
      }
      return res.data.data
    }
    throw new Error(res.data.message)
  }

  async function deletePreset(projectName: string, presetId: string) {
    const res = await presetApi.delete(projectName, presetId)
    if (res.data.code === 200) {
      await fetchPresets(projectName)
      if (currentPreset.value?.id === presetId) {
        currentPreset.value = null
      }
      return true
    }
    throw new Error(res.data.message)
  }

  async function generatePreset(data: { project_name: string; description: string; category?: string }) {
    generating.value = true
    try {
      const res = await presetApi.generate(data)
      if (res.data.code === 200) {
        return res.data.data
      }
      throw new Error(res.data.message)
    } finally {
      generating.value = false
    }
  }

  return {
    presets,
    currentPreset,
    loading,
    generating,
    currentProject,
    fetchPresets,
    fetchPreset,
    createPreset,
    updatePreset,
    deletePreset,
    generatePreset,
  }
})
