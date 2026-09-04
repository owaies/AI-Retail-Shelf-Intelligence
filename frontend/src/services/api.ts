import type { Analysis, AnalysisSummary, ApiHealth } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'
const TOKEN_KEY = 'retail_vision_access_token'

export function getAccessToken() { return localStorage.getItem(TOKEN_KEY) ?? '' }
export function setAccessToken(token: string) { token.trim() ? localStorage.setItem(TOKEN_KEY, token.trim()) : localStorage.removeItem(TOKEN_KEY) }

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const token = getAccessToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers })
  if (!response.ok) {
    let detail = `API request failed: ${response.status}`
    try { const body = await response.json(); if (typeof body.detail === 'string') detail = body.detail } catch { /* non-JSON error */ }
    throw new Error(detail)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  health: () => request<ApiHealth>('/health'),
  analyses: () => request<AnalysisSummary[]>('/analyses'),
  analysis: (id: string) => request<Analysis>(`/analyses/${id}`),
  createAnalysis: (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return request<Analysis>('/analyses', { method: 'POST', body })
  },
  deleteAnalysis: (id: string) => request<void>(`/analyses/${id}`, { method: 'DELETE' }),
}
