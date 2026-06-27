export type ApiMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
export type ApiRequestOptions = {
  signal?: AbortSignal
  preferAiReady?: boolean
}

const API_BASE = '/api'
const REQUEST_TIMEOUT_MS = 30_000
const DISCOVERY_TIMEOUT_MS = 1_500
const API_BASE_STORAGE_KEY = 'storyworks.apiBase'
const LOCAL_BACKEND_PORTS = [8022, 8021, 8020, 8023, 8024, 8000, 8001, 8002, 8010, 8011]

export class ApiError extends Error {
  status: number
  payload: any

  constructor(message: string, status: number, payload: any) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

function unique(values: string[]) {
  return Array.from(new Set(values.filter(Boolean)))
}

function normalizeApiBase(base: string) {
  const cleaned = String(base || '').trim().replace(/\/+$/, '')
  if (!cleaned) return ''
  return cleaned.endsWith('/api') ? cleaned : `${cleaned}/api`
}

function storedApiBase() {
  try {
    return typeof window === 'undefined' ? '' : window.localStorage.getItem(API_BASE_STORAGE_KEY) || ''
  } catch {
    return ''
  }
}

function rememberApiBase(base: string) {
  try {
    if (typeof window !== 'undefined' && base && base !== API_BASE) window.localStorage.setItem(API_BASE_STORAGE_KEY, base)
  } catch {
    // localStorage can be unavailable in private or embedded contexts.
  }
}

function forgetApiBase(base: string) {
  try {
    if (typeof window !== 'undefined' && base && window.localStorage.getItem(API_BASE_STORAGE_KEY) === base) {
      window.localStorage.removeItem(API_BASE_STORAGE_KEY)
    }
  } catch {
    // localStorage can be unavailable in private or embedded contexts.
  }
}

function candidateApiBases() {
  const configured = normalizeApiBase((import.meta as any).env?.VITE_STORYWORKS_API_BASE || '')
  const directLocalBases = LOCAL_BACKEND_PORTS.map((port) => `http://127.0.0.1:${port}/api`)
  return unique([configured, storedApiBase(), API_BASE, ...directLocalBases])
}

function aiSettingsReady(settings: any) {
  return String(settings?.provider || '').toLowerCase() === 'mock' || Boolean(settings?.has_api_key)
}

function isAiEndpoint(url: string) {
  return /\/ai(\/|$)|\/settings\/ai$/.test(url)
}

function isAiConfigurationError(error: any) {
  if (!(error instanceof ApiError)) return false
  const text = `${error.message || ''} ${error.payload?.detail || ''} ${error.payload?.message || ''}`
  return error.status === 400 && text.includes('未配置 AI API Key')
}

function shouldTryFallback(error: any) {
  return error instanceof ApiError && ([0, 404, 408].includes(error.status) || isAiConfigurationError(error))
}

function cancellationError(method: ApiMethod, url: string) {
  return new ApiError(`请求已取消：${method} ${url}`, 499, {})
}

async function requestFromBase<T = any>(
  base: string,
  method: ApiMethod,
  url: string,
  data?: any,
  options: ApiRequestOptions & { timeoutMs?: number } = {},
): Promise<T> {
  const controller = new AbortController()
  const abortState: { reason: 'timeout' | 'cancel' } = { reason: 'timeout' }
  const timeoutMs = options.timeoutMs ?? REQUEST_TIMEOUT_MS
  const cancel = () => {
    abortState.reason = 'cancel'
    controller.abort()
  }
  if (options.signal?.aborted) throw cancellationError(method, url)
  options.signal?.addEventListener('abort', cancel, { once: true })
  const timer = globalThis.setTimeout(() => {
    abortState.reason = 'timeout'
    controller.abort()
  }, timeoutMs)
  try {
    const response = await fetch(`${base}${url}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: data === undefined ? undefined : JSON.stringify(data),
      signal: controller.signal,
    })
    const text = await response.text()
    let payload: any = {}
    if (text) {
      try {
        payload = JSON.parse(text)
      } catch {
        payload = { raw: text }
      }
    }
    if (!response.ok || Number(payload?.code || 0) >= 400) {
      const fallback =
        response.status === 404
          ? `接口不存在：${method} ${url}。请确认前端代理指向 Storyworks 统一后端，或刷新页面让前端自动发现后端。`
          : `请求失败（${response.status || 'network'}）`
      const message = response.status === 404 && (payload?.detail === 'Not Found' || payload?.message === 'Not Found') ? fallback : payload?.detail || payload?.message || fallback
      throw new ApiError(message, response.status, payload)
    }
    return payload.data as T
  } catch (error: any) {
    if (error?.name === 'AbortError') {
      if (abortState.reason === 'cancel') throw cancellationError(method, url)
      throw new ApiError(`请求超时：${method} ${url}。请检查后端服务是否正常响应。`, 408, {})
    }
    if (error instanceof ApiError) throw error
    throw new ApiError(error?.message || `无法连接后端服务：${method} ${url}`, 0, {})
  } finally {
    options.signal?.removeEventListener('abort', cancel)
    globalThis.clearTimeout(timer)
  }
}

async function probeStoryworksApiBase(base: string) {
  try {
    const health = await requestFromBase<any>(base, 'GET', '/health', undefined, { timeoutMs: DISCOVERY_TIMEOUT_MS })
    if (health?.status !== 'ok') return null
    const settings = await requestFromBase<any>(base, 'GET', '/settings/ai', undefined, { timeoutMs: DISCOVERY_TIMEOUT_MS })
    return { health, settings }
  } catch {
    return null
  }
}

async function isStoryworksApiBase(base: string) {
  return Boolean(await probeStoryworksApiBase(base))
}

async function discoverApiBase(exclude: string, preferAiReady = false) {
  let firstCompatible = ''
  for (const base of candidateApiBases()) {
    if (base === exclude) continue
    const probe = await probeStoryworksApiBase(base)
    if (!probe) continue
    firstCompatible ||= base
    if (!preferAiReady || aiSettingsReady(probe.settings)) return base
  }
  return firstCompatible
}

export async function apiRequest<T = any>(method: ApiMethod, url: string, data?: any, options: ApiRequestOptions = {}): Promise<T> {
  const bases = candidateApiBases()
  const preferAiReady = Boolean(options.preferAiReady || isAiEndpoint(url))
  if (preferAiReady && !options.signal) {
    const preferred = await discoverApiBase('', true)
    if (preferred) bases.unshift(preferred)
  }
  let firstError: any = null
  for (const base of bases) {
    if (options.signal?.aborted) throw cancellationError(method, url)
    try {
      const payloadData = await requestFromBase<T>(base, method, url, data, options)
      rememberApiBase(base)
      return payloadData
    } catch (error: any) {
      if (!firstError) firstError = error
      if (error instanceof ApiError && error.status === 404) forgetApiBase(base)
      if (!shouldTryFallback(error)) throw error
      const discovered = await discoverApiBase(base, preferAiReady || isAiConfigurationError(error))
      if (discovered && discovered !== base) {
        try {
          const payloadData = await requestFromBase<T>(discovered, method, url, data, options)
          rememberApiBase(discovered)
          return payloadData
        } catch (discoveredError: any) {
          if (!firstError) firstError = discoveredError
          if (!shouldTryFallback(discoveredError)) throw discoveredError
          if (!bases.includes(discovered)) bases.push(discovered)
        }
      }
    }
  }
  throw firstError || new ApiError(`无法连接后端服务：${method} ${url}`, 0, {})
}
