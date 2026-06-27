import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const characterApi = {
  // 角色 CRUD
  list(projectName: string, status?: string) {
    const params: any = { project_name: projectName }
    if (status) params.status = status
    return api.get('/characters', { params })
  },

  get(projectName: string, characterId: string) {
    return api.get(`/characters/${characterId}`, { params: { project_name: projectName } })
  },

  create(data: any) {
    return api.post('/characters', data)
  },

  update(projectName: string, characterId: string, data: any) {
    return api.put(`/characters/${characterId}`, data, { params: { project_name: projectName } })
  },

  delete(projectName: string, characterId: string) {
    return api.delete(`/characters/${characterId}`, { params: { project_name: projectName } })
  },

  // 批量操作
  batchDelete(projectName: string, ids: string[]) {
    return api.post('/characters/batch-delete', { project_name: projectName, ids })
  },

  // 模板
  listTemplates(projectName?: string) {
    return api.get('/templates', { params: { project_name: projectName } })
  },

  createTemplate(data: any) {
    return api.post('/templates', data)
  },

  // AI 生成
  generate(data: { project_name: string; concept: string; character_type?: string }) {
    return api.post('/generate', data)
  },

  generateBatch(data: { project_name: string; concepts: string[]; character_type?: string }) {
    return api.post('/generate-batch', data)
  },

  // 导出
  exportMarkdown(projectName: string, characterId?: string) {
    const params: any = { project_name: projectName }
    if (characterId) params.character_id = characterId
    return api.get('/export/markdown', { params, responseType: 'blob' })
  },

  exportJson(projectName: string, characterId?: string) {
    const params: any = { project_name: projectName }
    if (characterId) params.character_id = characterId
    return api.get('/export/json', { params, responseType: 'blob' })
  },

  // 获取世界书上下文
  getWorldbookContext(projectName: string) {
    return api.get('/worldbook-context', { params: { project_name: projectName } })
  },
}

export default api
