import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectApi } from '@/api'

export interface Project {
  id: string
  name: string
  description?: string
  genre?: string
  settings?: any
  modules?: any[]
  created_at: string
  updated_at: string
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const loading = ref(false)

  // 获取项目列表
  async function fetchProjects() {
    loading.value = true
    try {
      const res = await projectApi.list()
      if (res.data.code === 200) {
        projects.value = res.data.data || []
      }
    } catch (error) {
      console.error('获取项目列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 获取项目详情
  async function fetchProject(id: string) {
    loading.value = true
    try {
      const res = await projectApi.get(id)
      if (res.data.code === 200) {
        currentProject.value = res.data.data
      }
    } catch (error) {
      console.error('获取项目详情失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 创建项目
  async function createProject(data: { name: string; description?: string; genre?: string }) {
    const res = await projectApi.create(data)
    if (res.data.code === 200) {
      await fetchProjects()
      return res.data.data
    }
    throw new Error(res.data.message)
  }

  // 更新项目
  async function updateProject(id: string, data: any) {
    const res = await projectApi.update(id, data)
    if (res.data.code === 200) {
      await fetchProjects()
      if (currentProject.value?.id === id) {
        currentProject.value = res.data.data
      }
      return res.data.data
    }
    throw new Error(res.data.message)
  }

  // 删除项目
  async function deleteProject(id: string) {
    const res = await projectApi.delete(id)
    if (res.data.code === 200) {
      await fetchProjects()
      if (currentProject.value?.id === id) {
        currentProject.value = null
      }
      return true
    }
    throw new Error(res.data.message)
  }

  return {
    projects,
    currentProject,
    loading,
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    deleteProject,
  }
})
