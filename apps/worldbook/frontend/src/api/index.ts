import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const worldbookApi = {
  // 条目
  listEntries(projectName: string, category?: string, status?: string) {
    const params: any = { project_name: projectName }
    if (category) params.category = category
    if (status) params.status = status
    return api.get('/entries', { params })
  },

  getEntry(projectName: string, entryId: string) {
    return api.get(`/entries/${entryId}`, { params: { project_name: projectName } })
  },

  createEntry(data: any) {
    return api.post('/entries', data)
  },

  updateEntry(projectName: string, entryId: string, data: any) {
    return api.put(`/entries/${entryId}`, data, { params: { project_name: projectName } })
  },

  deleteEntry(projectName: string, entryId: string) {
    return api.delete(`/entries/${entryId}`, { params: { project_name: projectName } })
  },

  // 蓝图
  listBlueprints(projectName: string) {
    return api.get('/blueprints', { params: { project_name: projectName } })
  },

  createBlueprint(data: any) {
    return api.post('/blueprints', data)
  },

  // AI 生成
  generate(data: { project_name: string; category: string; title: string; summary?: string }) {
    return api.post('/generate', data)
  },

  // 分类
  listCategories() {
    return api.get('/categories')
  },
}

export default api
