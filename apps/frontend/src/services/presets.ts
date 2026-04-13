import { API_BASE_URL, http, readErrorMessage } from '@/services/http'
import type {
  PresetCreate,
  PresetGenerateRequest,
  PresetGenerateResponse,
  PresetRead,
  PresetTestRequest,
  PresetTestResponse,
  PresetUpdate,
} from '@/schemas/preset'

export function fetchPresets(projectId: number) {
  return http<PresetRead[]>(`/api/projects/${projectId}/presets`)
}

export function createPreset(projectId: number, payload: PresetCreate) {
  return http<PresetRead>(`/api/projects/${projectId}/presets`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updatePreset(presetId: number, payload: PresetUpdate) {
  return http<PresetRead>(`/api/presets/${presetId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deletePreset(presetId: number) {
  const response = await fetch(`${API_BASE_URL}/api/presets/${presetId}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error(await readErrorMessage(response))
  }
}

export function generatePresetDraft(payload: PresetGenerateRequest) {
  return http<PresetGenerateResponse>('/api/presets/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function testPreset(payload: PresetTestRequest) {
  return http<PresetTestResponse>('/api/presets/test', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function exportPreset(presetId: number, format: 'json' | 'markdown') {
  const response = await fetch(`${API_BASE_URL}/api/presets/${presetId}/export?format=${format}`)

  if (!response.ok) {
    throw new Error(await readErrorMessage(response))
  }

  return format === 'json' ? response.json() : response.text()
}
