import { API_BASE_URL, http, readErrorMessage } from '@/services/http'
import type {
  CharacterCreate,
  CharacterGenerateRequest,
  CharacterGenerateResponse,
  CharacterRead,
  CharacterTemplate,
  CharacterUpdate,
} from '@/schemas/character'

export function fetchCharacterTemplates() {
  return http<CharacterTemplate[]>('/api/character/templates')
}

export function fetchCharacterTemplate(templateId: string) {
  return http<CharacterTemplate>(`/api/character/templates/${templateId}`)
}

export function fetchCharacters(projectId: number) {
  return http<CharacterRead[]>(`/api/projects/${projectId}/characters`)
}

export function createCharacter(projectId: number, payload: CharacterCreate) {
  return http<CharacterRead>(`/api/projects/${projectId}/characters`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateCharacter(characterId: number, payload: CharacterUpdate) {
  return http<CharacterRead>(`/api/characters/${characterId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteCharacter(characterId: number) {
  const response = await fetch(`${API_BASE_URL}/api/characters/${characterId}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error(await readErrorMessage(response))
  }
}

export function generateCharacterDraft(payload: CharacterGenerateRequest) {
  return http<CharacterGenerateResponse>('/api/characters/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function exportCharacter(characterId: number, format: 'json' | 'markdown') {
  const response = await fetch(`${API_BASE_URL}/api/characters/${characterId}/export?format=${format}`)

  if (!response.ok) {
    throw new Error(await readErrorMessage(response))
  }

  return format === 'json' ? response.json() : response.text()
}
