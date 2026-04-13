export interface ScriptRead {
  id: number
  project_id: number
  title: string
  script_type: string
  theme: string
  summary: string
  main_characters: Array<Record<string, unknown> | string>
  core_conflict: string
  story_stage: string
  major_nodes: Array<Record<string, unknown> | string>
  branch_ideas: Array<Record<string, unknown> | string>
  forbidden_content: string
  chapters: Array<Record<string, unknown>>
  scene_cards: Array<Record<string, unknown>>
  constraints: Record<string, unknown>
  notes: string
  status: string
  created_at: string
  updated_at: string
}

export interface ScriptCreate {
  title: string
  script_type: string
  theme: string
  summary: string
  main_characters: Array<Record<string, unknown> | string>
  core_conflict: string
  story_stage: string
  major_nodes: Array<Record<string, unknown> | string>
  branch_ideas: Array<Record<string, unknown> | string>
  forbidden_content: string
  chapters: Array<Record<string, unknown>>
  scene_cards: Array<Record<string, unknown>>
  constraints: Record<string, unknown>
  notes: string
  status: string
}

export interface ScriptUpdate extends Partial<ScriptCreate> {}

export interface ScriptGenerateRequest {
  title: string
  script_type: string
  concept: string
  project_context: string
  status: string
}

export interface ScriptGenerateResponse extends ScriptCreate {}

export function createEmptyScriptDraft(): ScriptCreate {
  return {
    title: '',
    script_type: '主线',
    theme: '',
    summary: '',
    main_characters: [],
    core_conflict: '',
    story_stage: '',
    major_nodes: [],
    branch_ideas: [],
    forbidden_content: '',
    chapters: [],
    scene_cards: [],
    constraints: {},
    notes: '',
    status: 'draft',
  }
}
