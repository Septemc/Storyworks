import { defineStore } from 'pinia'
import { ref } from 'vue'
import { scriptApi } from '@/api'

export interface Script {
  id: string
  project_name: string
  title: string
  type: string
  parent_id?: string
  content: any
  constraints: any
  status: string
  sort_order: number
  children?: Script[]
  created_at: string
  updated_at: string
}

export const useScriptStore = defineStore('script', () => {
  const scripts = ref<Script[]>([])
  const scriptTree = ref<Script[]>([])
  const currentScript = ref<Script | null>(null)
  const loading = ref(false)
  const generating = ref(false)
  const currentProject = ref('')

  async function fetchScriptTree(projectName: string) {
    loading.value = true
    currentProject.value = projectName
    try {
      const res = await scriptApi.getTree(projectName)
      if (res.data.code === 200) {
        scriptTree.value = res.data.data || []
      }
    } catch (error) {
      console.error('获取剧本树失败:', error)
    } finally {
      loading.value = false
    }
  }

  async function fetchScripts(projectName: string, type?: string, parentId?: string) {
    loading.value = true
    currentProject.value = projectName
    try {
      const res = await scriptApi.list(projectName, type, parentId)
      if (res.data.code === 200) {
        scripts.value = res.data.data || []
      }
    } catch (error) {
      console.error('获取剧本列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  async function fetchScript(projectName: string, scriptId: string) {
    try {
      const res = await scriptApi.get(projectName, scriptId)
      if (res.data.code === 200) {
        currentScript.value = res.data.data
      }
    } catch (error) {
      console.error('获取剧本详情失败:', error)
    }
  }

  async function createScript(data: any) {
    const res = await scriptApi.create(data)
    if (res.data.code === 200) {
      await fetchScriptTree(data.project_name)
      return res.data.data
    }
    throw new Error(res.data.message)
  }

  async function updateScript(projectName: string, scriptId: string, data: any) {
    const res = await scriptApi.update(projectName, scriptId, data)
    if (res.data.code === 200) {
      await fetchScriptTree(projectName)
      if (currentScript.value?.id === scriptId) {
        currentScript.value = res.data.data
      }
      return res.data.data
    }
    throw new Error(res.data.message)
  }

  async function deleteScript(projectName: string, scriptId: string) {
    const res = await scriptApi.delete(projectName, scriptId)
    if (res.data.code === 200) {
      await fetchScriptTree(projectName)
      if (currentScript.value?.id === scriptId) {
        currentScript.value = null
      }
      return true
    }
    throw new Error(res.data.message)
  }

  async function generateScript(data: { project_name: string; concept: string; genre?: string }) {
    generating.value = true
    try {
      const res = await scriptApi.generate(data)
      if (res.data.code === 200) {
        return res.data.data
      }
      throw new Error(res.data.message)
    } finally {
      generating.value = false
    }
  }

  return {
    scripts,
    scriptTree,
    currentScript,
    loading,
    generating,
    currentProject,
    fetchScriptTree,
    fetchScripts,
    fetchScript,
    createScript,
    updateScript,
    deleteScript,
    generateScript,
  }
})
