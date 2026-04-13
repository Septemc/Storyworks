export interface PresetRead {
  id: number
  project_id: number
  title: string
  preset_type: string
  scope: string
  style_description: string
  wording_tendency: string
  sentence_tendency: string
  description_density: string
  dialogue_ratio: string
  rhythm_tendency: string
  emotion_intensity: string
  plot_preferences: string[]
  character_preferences: string[]
  forbidden_expressions: string[]
  output_requirements: string[]
  notes: string
  status: string
  created_at: string
  updated_at: string
}

export interface PresetCreate {
  title: string
  preset_type: string
  scope: string
  style_description: string
  wording_tendency: string
  sentence_tendency: string
  description_density: string
  dialogue_ratio: string
  rhythm_tendency: string
  emotion_intensity: string
  plot_preferences: string[]
  character_preferences: string[]
  forbidden_expressions: string[]
  output_requirements: string[]
  notes: string
  status: string
}

export interface PresetUpdate extends Partial<PresetCreate> {}

export interface PresetGenerateRequest {
  title: string
  preset_type: string
  style_goal: string
  reference_text: string
  target_use: string
  status: string
}

export interface PresetGenerateResponse extends PresetCreate {}

export interface PresetTestRequest {
  title: string
  preset_type: string
  style_description: string
  wording_tendency: string
  sentence_tendency: string
  description_density: string
  dialogue_ratio: string
  rhythm_tendency: string
  emotion_intensity: string
  plot_preferences: string[]
  character_preferences: string[]
  forbidden_expressions: string[]
  output_requirements: string[]
  sample_target: string
  sample_input: string
}

export interface PresetTestResponse {
  preview_summary: string
  recommended_prompt: string
  active_directives: string[]
  quality_checklist: string[]
}

export function createEmptyPresetDraft(): PresetCreate {
  return {
    title: '',
    preset_type: '文风预设',
    scope: '通用',
    style_description: '',
    wording_tendency: '',
    sentence_tendency: '',
    description_density: '',
    dialogue_ratio: '',
    rhythm_tendency: '',
    emotion_intensity: '',
    plot_preferences: [],
    character_preferences: [],
    forbidden_expressions: [],
    output_requirements: [],
    notes: '',
    status: 'draft',
  }
}
