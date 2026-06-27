import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiRequest } from './client'

function jsonResponse(status: number, payload: any) {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(payload),
  }
}

describe('apiRequest backend discovery', () => {
  const originalFetch = globalThis.fetch

  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it('prefers a discovered AI-ready backend for settings saves', async () => {
    const calls: string[] = []
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      calls.push(url)
      if (url === '/api/health') return jsonResponse(404, { detail: 'Not Found' }) as any
      if (url === '/api/settings/ai') return jsonResponse(404, { detail: 'Not Found' }) as any
      if (url === 'http://127.0.0.1:8022/api/health') {
        return jsonResponse(200, { code: 200, data: { status: 'ok', features: { ai_settings: true } } }) as any
      }
      if (url === 'http://127.0.0.1:8022/api/settings/ai') {
        return jsonResponse(200, { code: 200, data: { provider: 'mock', has_api_key: true } }) as any
      }
      return jsonResponse(404, { detail: 'Not Found' }) as any
    }) as any

    const result = await apiRequest('PUT', '/settings/ai', { provider: 'mock', apiKey: 'secret' })

    expect(result).toEqual({ provider: 'mock', has_api_key: true })
    expect(calls).toEqual([
      '/api/health',
      'http://127.0.0.1:8022/api/health',
      'http://127.0.0.1:8022/api/settings/ai',
      'http://127.0.0.1:8022/api/settings/ai',
    ])
  })

  it('uses an AI-ready backend instead of a stale unconfigured backend for AI calls', async () => {
    const calls: string[] = []
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      calls.push(url)
      if (url === '/api/health') return jsonResponse(200, { code: 200, data: { status: 'ok' } }) as any
      if (url === '/api/settings/ai') return jsonResponse(200, { code: 200, data: { provider: 'openai_compatible', has_api_key: false } }) as any
      if (url === 'http://127.0.0.1:8022/api/health') return jsonResponse(200, { code: 200, data: { status: 'ok' } }) as any
      if (url === 'http://127.0.0.1:8022/api/settings/ai') return jsonResponse(200, { code: 200, data: { provider: 'openai_compatible', has_api_key: true } }) as any
      if (url === 'http://127.0.0.1:8022/api/projects/proj_demo/characters/char_linyuan/ai/iterate') {
        return jsonResponse(200, { code: 200, data: { developer_data: { basic: { name: '林远' } } } }) as any
      }
      return jsonResponse(400, { detail: '未配置 AI API Key' }) as any
    }) as any

    const result = await apiRequest('POST', '/projects/proj_demo/characters/char_linyuan/ai/iterate', { instruction: '补强' })

    expect(result).toEqual({ developer_data: { basic: { name: '林远' } } })
    expect(calls).toEqual([
      '/api/health',
      '/api/settings/ai',
      'http://127.0.0.1:8022/api/health',
      'http://127.0.0.1:8022/api/settings/ai',
      'http://127.0.0.1:8022/api/projects/proj_demo/characters/char_linyuan/ai/iterate',
    ])
  })

  it('cancels an in-flight request through the caller abort signal', async () => {
    const controller = new AbortController()
    const calls: string[] = []
    globalThis.fetch = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      calls.push(String(input))
      return new Promise((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => reject({ name: 'AbortError' }), { once: true })
      })
    }) as any

    const pending = apiRequest('POST', '/projects/proj_demo/scripts/ai/generate', { prompt: '长调用' }, { signal: controller.signal })
    controller.abort()

    await expect(pending).rejects.toBeInstanceOf(ApiError)
    await expect(pending).rejects.toMatchObject({ status: 499, message: expect.stringContaining('请求已取消') })
    expect(calls).toEqual(['/api/projects/proj_demo/scripts/ai/generate'])
  })
})
