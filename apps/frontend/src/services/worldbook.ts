import { API_BASE_URL, http, readErrorMessage } from '@/services/http'
import type {
  WorldbookCreate,
  WorldbookGenerateRequest,
  WorldbookGenerateResponse,
  WorldbookRead,
  WorldbookUpdate,
} from '@/schemas/worldbook'

export function fetchWorldbookEntries(projectId: number) {
  return http<WorldbookRead[]>(`/api/projects/${projectId}/worldbook`)
}

export function createWorldbookEntry(projectId: number, payload: WorldbookCreate) {
  return http<WorldbookRead>(`/api/projects/${projectId}/worldbook`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateWorldbookEntry(entryId: number, payload: WorldbookUpdate) {
  return http<WorldbookRead>(`/api/worldbook/${entryId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteWorldbookEntry(entryId: number) {
  const response = await fetch(`${API_BASE_URL}/api/worldbook/${entryId}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error(await readErrorMessage(response))
  }
}

export function generateWorldbookDraft(payload: WorldbookGenerateRequest) {
  return http<WorldbookGenerateResponse>('/api/worldbook/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function exportWorldbookEntry(entryId: number, format: 'json' | 'markdown') {
  const response = await fetch(`${API_BASE_URL}/api/worldbook/${entryId}/export?format=${format}`)

  if (!response.ok) {
    throw new Error(await readErrorMessage(response))
  }

  return format === 'json' ? response.json() : response.text()
}
