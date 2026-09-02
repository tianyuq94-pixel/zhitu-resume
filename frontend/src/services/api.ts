import axios, { AxiosError } from 'axios'

type ApiErrorBody = {
  detail?: string | Array<{ msg?: string }>
}

const mutatingMethods = new Set(['post', 'put', 'patch', 'delete'])

const readCookie = (name: string): string | undefined => {
  const prefix = `${encodeURIComponent(name)}=`
  return document.cookie
    .split('; ')
    .find((item) => item.startsWith(prefix))
    ?.slice(prefix.length)
}

export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15_000,
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  if (config.method && mutatingMethods.has(config.method.toLowerCase())) {
    const csrfToken = readCookie('ai_career_csrf')
    if (csrfToken) {
      config.headers.set('X-CSRF-Token', decodeURIComponent(csrfToken))
    }
  }
  return config
})

export const getApiErrorMessage = (error: unknown, fallback = '操作失败，请稍后重试'): string => {
  if (!(error instanceof AxiosError)) {
    return fallback
  }
  const detail = (error.response?.data as ApiErrorBody | undefined)?.detail
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail) && detail[0]?.msg) {
    return detail[0].msg.replace(/^Value error,\s*/, '')
  }
  if (error.code === 'ECONNABORTED') {
    return '请求超时，请稍后重试'
  }
  return fallback
}

