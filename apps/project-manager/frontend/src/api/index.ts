import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 项目管理 API
export const projectApi = {
  // 获取项目列表
  list() {
    return api.get('/projects')
  },

  // 获取项目详情
  get(id: string) {
    return api.get(`/projects/${id}`)
  },

  // 创建项目
  create(data: { name: string; description?: string; genre?: string }) {
    return api.post('/projects', data)
  },

  // 更新项目
  update(id: string, data: { name?: string; description?: string; genre?: string; settings?: any }) {
    return api.put(`/projects/${id}`, data)
  },

  // 删除项目
  delete(id: string) {
    return api.delete(`/projects/${id}`)
  },
}

// 模块 API
export const moduleApi = {
  // 获取模块列表
  list() {
    return api.get('/modules')
  },
}

export default api
