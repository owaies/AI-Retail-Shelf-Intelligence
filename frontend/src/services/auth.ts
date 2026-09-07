const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL ?? ''
const SUPABASE_PUBLISHABLE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ?? ''
const TOKEN_KEY = 'retail_vision_access_token'

export type AuthSession = {
  access_token: string
  refresh_token?: string
  user: { id: string; email?: string }
}

function assertConfigured() {
  if (!SUPABASE_URL || !SUPABASE_PUBLISHABLE_KEY) {
    throw new Error('Supabase authentication is not configured')
  }
}

async function authRequest<T>(path: string, init: RequestInit): Promise<T> {
  assertConfigured()
  const response = await fetch(`${SUPABASE_URL.replace(/\/$/, '')}/auth/v1${path}`, {
    ...init,
    headers: {
      apikey: SUPABASE_PUBLISHABLE_KEY,
      'Content-Type': 'application/json',
      ...(init.headers ?? {}),
    },
  })
  if (!response.ok) {
    let message = `Authentication failed (${response.status})`
    try {
      const body = await response.json()
      if (typeof body.msg === 'string') message = body.msg
      else if (typeof body.error_description === 'string') message = body.error_description
      else if (typeof body.message === 'string') message = body.message
    } catch { /* non-JSON response */ }
    throw new Error(message)
  }
  return response.json() as Promise<T>
}

export async function signIn(email: string, password: string): Promise<AuthSession> {
  const session = await authRequest<AuthSession>('/token?grant_type=password', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  sessionStorage.setItem(TOKEN_KEY, session.access_token)
  return session
}

export function getAccessToken() {
  return sessionStorage.getItem(TOKEN_KEY) ?? ''
}

export function signOut() {
  sessionStorage.removeItem(TOKEN_KEY)
}
