export interface CharacterTemplateTab {
  id: string
  label: string
  order: number
}

export interface CharacterTemplateField {
  id: string
  label: string
  type: string
  tab: string
  path: string
  developer_mode_desc: string
  player_mode_desc: string
}

export interface CharacterTemplate {
  template_id: string
  name: string
  is_active: boolean
  config: {
    mode_contract: {
      developer_mode_requirements: string
      player_mode_requirements: string
      developer_mode_visible_blocks: string[]
    }
    tabs: CharacterTemplateTab[]
    fields: CharacterTemplateField[]
  }
}

export interface CharacterRead {
  id: number
  project_id: number
  template_id: string
  template_name: string
  name: string
  summary: string
  developer_mode: Record<string, Record<string, unknown>>
  player_mode: Record<string, Record<string, unknown>>
  meta: Record<string, unknown>
  notes: string
  status: string
  created_at: string
  updated_at: string
}

export interface CharacterCreate {
  template_id: string
  developer_mode: Record<string, Record<string, unknown>>
  player_mode: Record<string, Record<string, unknown>>
  meta: Record<string, unknown>
  notes: string
  status: string
}

export interface CharacterUpdate extends Partial<CharacterCreate> {}

export interface CharacterGenerateRequest {
  template_id: string
  name_hint: string
  concept: string
  project_context: string
  status: string
}

export interface CharacterGenerateResponse {
  template_id: string
  template_name: string
  name: string
  summary: string
  developer_mode: Record<string, Record<string, unknown>>
  player_mode: Record<string, Record<string, unknown>>
  meta: Record<string, unknown>
  notes: string
  status: string
}

export type CharacterEditorState = Record<string, Record<string, string>>

function defaultFieldValue(field: CharacterTemplateField, mode: 'developer' | 'player') {
  if (mode === 'player' && (field.tab === 'tab_secrets' || field.tab === 'tab_fortune')) {
    return '未知'
  }
  return ''
}

export function createEmptyCharacterEditor(template: CharacterTemplate, mode: 'developer' | 'player') {
  const editor: CharacterEditorState = {}

  for (const tab of template.config.tabs) {
    editor[tab.id] = {}
  }

  for (const field of template.config.fields) {
    editor[field.tab][field.id] = defaultFieldValue(field, mode)
  }

  return editor
}
