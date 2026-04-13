export const worldbookCategories = [
  '历史',
  '地理',
  '政治',
  '人文',
  '风俗',
  '科学',
  '经济',
  '宗教',
  '阵营',
  '制度',
  '种族',
  '组织',
  '事件',
  '术语',
  '技术体系',
  '能力体系',
] as const

export type WorldbookCategory = (typeof worldbookCategories)[number]

export interface WorldbookContent {
  definition: string
  origin: string
  structure: string
  rules: string
  impact: string
}

export interface WorldbookRead {
  id: number
  project_id: number
  category: WorldbookCategory
  title: string
  summary: string
  keywords: string[]
  content: WorldbookContent
  notes: string
  status: string
  created_at: string
  updated_at: string
}

export interface WorldbookCreate {
  category: WorldbookCategory
  title: string
  summary: string
  keywords: string[]
  content: WorldbookContent
  notes: string
  status: string
}

export interface WorldbookUpdate extends Partial<WorldbookCreate> {}

export interface WorldbookGenerateRequest {
  category: WorldbookCategory
  title: string
  idea: string
  mode: string
}

export interface WorldbookGenerateResponse {
  category: WorldbookCategory
  title: string
  summary: string
  keywords: string[]
  content: WorldbookContent
  notes: string
  status: string
}

export function createEmptyWorldbookDraft(): WorldbookCreate {
  return {
    category: '历史',
    title: '',
    summary: '',
    keywords: [],
    content: {
      definition: '',
      origin: '',
      structure: '',
      rules: '',
      impact: '',
    },
    notes: '',
    status: 'draft',
  }
}
