const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

async function parseApiError(res: Response): Promise<Error> {
  const fallback = `API error: ${res.status}`
  try {
    const payload = await res.json()
    if (typeof payload?.detail === 'string') return new Error(`${fallback} - ${payload.detail}`)
    return new Error(`${fallback} - ${JSON.stringify(payload)}`)
  } catch {
    return new Error(fallback)
  }
}

async function parseApiResponse<T>(res: Response): Promise<T> {
  if (!res.ok) throw await parseApiError(res)
  return res.json()
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`)
  return parseApiResponse<T>(res)
}

export async function apiPost<T = unknown>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return parseApiResponse<T>(res)
}

export async function apiPut<T = unknown>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return parseApiResponse<T>(res)
}

export async function apiDelete<T = unknown>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { method: 'DELETE' })
  return parseApiResponse<T>(res)
}

export async function apiPostForm<T = unknown>(path: string, body: FormData): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    body,
  })
  return parseApiResponse<T>(res)
}
