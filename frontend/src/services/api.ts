import axios, { AxiosError } from 'axios'
import { locale } from '@/i18n'

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
  config.headers.set('Accept-Language', locale.value === 'zh' ? 'zh-CN' : 'en-GB')
  if (config.method && mutatingMethods.has(config.method.toLowerCase())) {
    const csrfToken = readCookie('ai_career_csrf')
    if (csrfToken) {
      config.headers.set('X-CSRF-Token', decodeURIComponent(csrfToken))
    }
  }
  return config
})

export const getApiErrorMessage = (error: unknown, fallback = 'Operation failed, please try again later'): string => {
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
    return 'Request timed out, please try again later'
  }
  return fallback
}
