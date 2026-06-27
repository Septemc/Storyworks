import { defineStore } from 'pinia'
import { ref } from 'vue'
import { characterApi } from '@/api'

export interface Character {
  id: string
  project_name: string
  template_id?: string
  name: string
  developer_mode: any
  player_mode: any
  status: string
  created_at: string
  updated_at: string
}

export const useCharacterStore = defineStore('character', () => {
  const characters = ref<Character[]>([])
  const currentCharacter = ref<Character | null>(null)
  const loading = ref(false)
  const generating = ref(false)
  const currentProject = ref('')
  const selectedIds = ref<string[]>([])

  async function fetchCharacters(projectName: string) {
    loading.value = true
    currentProject.value = projectName
    try {
      const res = await characterApi.list(projectName)
      if (res.data.code === 200) {
        characters.value = res.data.data || []
      }
    } catch (error) {
      console.error('Failed to fetch characters:', error)
    } finally {
      loading.value = false
    }
  }

  async function fetchCharacter(projectName: string, characterId: string) {
    try {
      const res = await characterApi.get(projectName, characterId)
      if (res.data.code === 200) {
        currentCharacter.value = res.data.data
      }
    } catch (error) {
      console.error('Failed to fetch character:', error)
    }
  }

  async function createCharacter(data: any) {
    const res = await characterApi.create(data)
    if (res.data.code === 200) {
      await fetchCharacters(data.project_name)
      return res.data.data
    }
    throw new Error(res.data.message)
  }

  async function updateCharacter(projectName: string, characterId: string, data: any) {
    const res = await characterApi.update(projectName, characterId, data)
    if (res.data.code === 200) {
      await fetchCharacters(projectName)
      if (currentCharacter.value?.id === characterId) {
        currentCharacter.value = res.data.data
      }
      return res.data.data
    }
    throw new Error(res.data.message)
  }

  async function deleteCharacter(projectName: string, characterId: string) {
    const res = await characterApi.delete(projectName, characterId)
    if (res.data.code === 200) {
      await fetchCharacters(projectName)
      if (currentCharacter.value?.id === characterId) {
        currentCharacter.value = null
      }
      return true
    }
    throw new Error(res.data.message)
  }

  async function batchDeleteCharacters(projectName: string, ids: string[]) {
    const res = await characterApi.batchDelete(projectName, ids)
    if (res.data.code === 200) {
      await fetchCharacters(projectName)
      selectedIds.value = []
      return res.data.data
    }
    throw new Error(res.data.message)
  }

  async function generateCharacter(data: { project_name: string; concept: string; character_type?: string }) {
    generating.value = true
    try {
      const res = await characterApi.generate(data)
      if (res.data.code === 200) {
        return res.data.data
      }
      throw new Error(res.data.message)
    } finally {
      generating.value = false
    }
  }

  async function generateCharactersBatch(data: { project_name: string; concepts: string[]; character_type?: string }) {
    generating.value = true
    try {
      const res = await characterApi.generateBatch(data)
      if (res.data.code === 200) {
        return res.data.data
      }
      throw new Error(res.data.message)
    } finally {
      generating.value = false
    }
  }

  async function exportMarkdown(projectName: string, characterId?: string) {
    const res = await characterApi.exportMarkdown(projectName, characterId)
    const blob = new Blob([res.data], { type: 'text/markdown' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = characterId ? `character_${characterId}.md` : 'characters.md'
    a.click()
    window.URL.revokeObjectURL(url)
  }

  async function exportJson(projectName: string, characterId?: string) {
    const res = await characterApi.exportJson(projectName, characterId)
    const blob = new Blob([res.data], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = characterId ? `character_${characterId}.json` : 'characters.json'
    a.click()
    window.URL.revokeObjectURL(url)
  }

  function toggleSelect(id: string) {
    const index = selectedIds.value.indexOf(id)
    if (index === -1) {
      selectedIds.value.push(id)
    } else {
      selectedIds.value.splice(index, 1)
    }
  }

  function selectAll() {
    if (selectedIds.value.length === characters.value.length) {
      selectedIds.value = []
    } else {
      selectedIds.value = characters.value.map(c => c.id)
    }
  }

  return {
    characters,
    currentCharacter,
    loading,
    generating,
    currentProject,
    selectedIds,
    fetchCharacters,
    fetchCharacter,
    createCharacter,
    updateCharacter,
    deleteCharacter,
    batchDeleteCharacters,
    generateCharacter,
    generateCharactersBatch,
    exportMarkdown,
    exportJson,
    toggleSelect,
    selectAll,
  }
})
