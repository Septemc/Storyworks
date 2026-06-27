import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

export const scriptApi = {
  list(projectName: string, type?: string, parentId?: string) {
    const params: any = { project_name: projectName }
    if (type) params.type = type
    if (parentId) params.parent_id = parentId
    return api.get('/scripts', { params })
  },
  get(projectName: string, scriptId: string) {
    return api.get(`/scripts/${scriptId}`, { params: { project_name: projectName } })
  },
  create(data: any) {
    return api.post('/scripts', data)
  },
  update(projectName: string, scriptId: string, data: any) {
    return api.put(`/scripts/${scriptId}`, data, { params: { project_name: projectName } })
  },
  delete(projectName: string, scriptId: string) {
    return api.delete(`/scripts/${scriptId}`, { params: { project_name: projectName } })
  },
  getTree(projectName: string) {
    return api.get('/scripts/tree', { params: { project_name: projectName } })
  },
  generate(data: { project_name: string; concept: string; genre?: string }) {
    return api.post('/generate', data)
  },
}

export default api
