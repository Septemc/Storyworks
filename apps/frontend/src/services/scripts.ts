import { API_BASE_URL, http, readErrorMessage } from '@/services/http'
import type {
  ScriptCreate,
  ScriptGenerateRequest,
  ScriptGenerateResponse,
  ScriptRead,
  ScriptUpdate,
} from '@/schemas/script'

export function fetchScripts(projectId: number) {
  return http<ScriptRead[]>(`/api/projects/${projectId}/scripts`)
}

export function createScript(projectId: number, payload: ScriptCreate) {
  return http<ScriptRead>(`/api/projects/${projectId}/scripts`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateScript(scriptId: number, payload: ScriptUpdate) {
  return http<ScriptRead>(`/api/scripts/${scriptId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteScript(scriptId: number) {
  const response = await fetch(`${API_BASE_URL}/api/scripts/${scriptId}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error(await readErrorMessage(response))
  }
}

export function generateScriptDraft(payload: ScriptGenerateRequest) {
  return http<ScriptGenerateResponse>('/api/scripts/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function exportScript(scriptId: number, format: 'json' | 'markdown') {
  const response = await fetch(`${API_BASE_URL}/api/scripts/${scriptId}/export?format=${format}`)

  if (!response.ok) {
    throw new Error(await readErrorMessage(response))
  }

  return format === 'json' ? response.json() : response.text()
}
