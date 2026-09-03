import type { ApiHealth } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  health: () => request<ApiHealth>('/health'),
}
