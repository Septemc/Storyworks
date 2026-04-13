import { http } from '@/services/http'
import type { ProjectCreate, ProjectRead } from '@/schemas/project'

export function fetchProjects() {
  return http<ProjectRead[]>('/api/projects')
}

export function createProject(payload: ProjectCreate) {
  return http<ProjectRead>('/api/projects', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
