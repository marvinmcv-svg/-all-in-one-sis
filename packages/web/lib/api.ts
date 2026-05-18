const BASE_URL = process.env.NEXT_PUBLIC_APP_URL ?? ''

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error((error as { error?: string }).error ?? 'Request failed')
  }
  return res.json() as Promise<T>
}
