/**
 * Shared API helper: single place for the backend base URL and auth token.
 * The auth token is stored in localStorage (no secrets in source code).
 */

export const API_URL = import.meta.env.VITE_API_URL || ''

const TOKEN_KEY = 'sa_token'

export function getToken() {
  try { return localStorage.getItem(TOKEN_KEY) || '' } catch { return '' }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch { /* ignore */ }
}

/** Build headers for a request, attaching the bearer token when present. */
export function authHeaders(extra = {}) {
  const headers = { ...extra }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  return headers
}

/**
 * Fetch JSON with a consistent error shape.
 * Throws an Error carrying `status` and a safe `message`.
 */
export async function apiFetch(path, { method = 'GET', body, headers = {}, auth = false } = {}) {
  const finalHeaders = { ...headers }
  if (body !== undefined) finalHeaders['Content-Type'] = 'application/json'
  if (auth) Object.assign(finalHeaders, authHeaders())

  let res
  try {
    res = await fetch(`${API_URL}${path}`, {
      method,
      headers: finalHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    const err = new Error('network')
    err.code = 'network'
    throw err
  }

  let data = null
  try { data = await res.json() } catch { /* non-JSON body */ }

  if (!res.ok) {
    const err = new Error(extractDetail(data) || `HTTP ${res.status}`)
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

function extractDetail(data) {
  if (!data) return ''
  const detail = data.detail
  if (!detail) return ''
  if (Array.isArray(detail)) return detail.map((d) => d.msg || JSON.stringify(d)).join(' ')
  return typeof detail === 'string' ? detail : JSON.stringify(detail)
}
