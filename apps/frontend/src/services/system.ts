import { http } from '@/services/http'

export interface HealthResponse {
  status: string
  app_name: string
  environment: string
  debug: boolean
}

export function getHealth() {
  return http<HealthResponse>('/api/health')
}
