import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

export const presetApi = {
  list(projectName: string, category?: string) {
    const params: any = { project_name: projectName }
    if (category) params.category = category
    return api.get('/presets', { params })
  },
  get(projectName: string, presetId: string) {
    return api.get(`/presets/${presetId}`, { params: { project_name: projectName } })
  },
  create(data: any) {
    return api.post('/presets', data)
  },
  update(projectName: string, presetId: string, data: any) {
    return api.put(`/presets/${presetId}`, data, { params: { project_name: projectName } })
  },
  delete(projectName: string, presetId: string) {
    return api.delete(`/presets/${presetId}`, { params: { project_name: projectName } })
  },
  generate(data: { project_name: string; description: string; category?: string }) {
    return api.post('/generate', data)
  },
  listCategories() {
    return api.get('/categories')
  },
}

export default api
