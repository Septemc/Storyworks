import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { worldbookApi } from '@/api'

export interface WorldbookEntry {
  id: string
  project_name: string
  category: string
  title: string
  summary?: string
  content?: string
  keywords: string[]
  relations: string[]
  notes?: string
  status: string
  created_at: string
  updated_at: string
}

export interface Category {
  id: string
  name: string
  icon: string
}

export const useWorldbookStore = defineStore('worldbook', () => {
  const entries = ref<WorldbookEntry[]>([])
  const categories = ref<Category[]>([])
  const currentEntry = ref<WorldbookEntry | null>(null)
  const loading = ref(false)
  const generating = ref(false)
  const currentProject = ref('')

  // 按分类分组的条目
  const entriesByCategory = computed(() => {
    const grouped: Record<string, WorldbookEntry[]> = {}
    for (const entry of entries.value) {
      if (!grouped[entry.category]) {
        grouped[entry.category] = []
      }
      grouped[entry.category].push(entry)
    }
    return grouped
  })

  // 获取分类列表
  async function fetchCategories() {
    try {
      const res = await worldbookApi.listCategories()
      if (res.data.code === 200) {
        categories.value = res.data.data || []
      }
    } catch (error) {
      console.error('获取分类失败:', error)
    }
  }

  // 获取条目列表
  async function fetchEntries(projectName: string, category?: string) {
    loading.value = true
    currentProject.value = projectName
    try {
      const res = await worldbookApi.listEntries(projectName, category)
      if (res.data.code === 200) {
        entries.value = res.data.data || []
      }
    } catch (error) {
      console.error('获取条目失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 获取条目详情
  async function fetchEntry(projectName: string, entryId: string) {
    try {
      const res = await worldbookApi.getEntry(projectName, entryId)
      if (res.data.code === 200) {
        currentEntry.value = res.data.data
      }
    } catch (error) {
      console.error('获取条目详情失败:', error)
    }
  }

  // 创建条目
  async function createEntry(data: any) {
    const res = await worldbookApi.createEntry(data)
    if (res.data.code === 200) {
      await fetchEntries(data.project_name)
      return res.data.data
    }
    throw new Error(res.data.message)
  }

  // 更新条目
  async function updateEntry(projectName: string, entryId: string, data: any) {
    const res = await worldbookApi.updateEntry(projectName, entryId, data)
    if (res.data.code === 200) {
      await fetchEntries(projectName)
      if (currentEntry.value?.id === entryId) {
        currentEntry.value = res.data.data
      }
      return res.data.data
    }
    throw new Error(res.data.message)
  }

  // 删除条目
  async function deleteEntry(projectName: string, entryId: string) {
    const res = await worldbookApi.deleteEntry(projectName, entryId)
    if (res.data.code === 200) {
      await fetchEntries(projectName)
      if (currentEntry.value?.id === entryId) {
        currentEntry.value = null
      }
      return true
    }
    throw new Error(res.data.message)
  }

  // AI 生成
  async function generateEntry(data: { project_name: string; category: string; title: string; summary?: string }) {
    generating.value = true
    try {
      const res = await worldbookApi.generate(data)
      if (res.data.code === 200) {
        return res.data.data
      }
      throw new Error(res.data.message)
    } finally {
      generating.value = false
    }
  }

  return {
    entries,
    categories,
    currentEntry,
    loading,
    generating,
    currentProject,
    entriesByCategory,
    fetchCategories,
    fetchEntries,
    fetchEntry,
    createEntry,
    updateEntry,
    deleteEntry,
    generateEntry,
  }
})
