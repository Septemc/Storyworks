export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export async function readErrorMessage(response: Response) {
  const text = (await response.text()).trim()
  return text || `请求失败（状态码 ${response.status}）。`
}

export function resolveErrorMessage(error: unknown, fallback = '操作失败，请稍后重试。') {
  if (error instanceof Error && error.message) {
    return error.message
  }

  return fallback
}

export async function http<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
      ...init,
    })
  } catch {
    throw new Error('无法连接后端服务，请检查接口地址或服务状态。')
  }

  if (!response.ok) {
    throw new Error(await readErrorMessage(response))
  }

  return response.json() as Promise<T>
}
