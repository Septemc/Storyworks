export interface ProjectCreate {
  title: string
  summary: string
}

export interface ProjectRead {
  id: number
  title: string
  summary: string
  status: string
  created_at: string
  updated_at: string
}
