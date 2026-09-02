import { createPinia, defineStore } from 'pinia'
import { ref } from 'vue'

import { api } from '@/services/api'

export type CurrentUser = {
  id: number
  username: string
  profile_completed: boolean
  created_at: string
}

export const pinia = createPinia()

export const useAuthStore = defineStore('auth', () => {
  const user = ref<CurrentUser | null>(null)
  const initialized = ref(false)

  const initialize = async () => {
    if (initialized.value) return
    try {
      const response = await api.get<CurrentUser>('/auth/me')
      user.value = response.data
    } catch {
      user.value = null
    } finally {
      initialized.value = true
    }
  }

  const register = async (username: string, password: string) => {
    const response = await api.post<CurrentUser>('/auth/register', { username, password })
    user.value = response.data
    initialized.value = true
  }

  const login = async (username: string, password: string) => {
    const response = await api.post<CurrentUser>('/auth/login', { username, password })
    user.value = response.data
    initialized.value = true
  }

  const refreshMe = async () => {
    const response = await api.get<CurrentUser>('/auth/me')
    user.value = response.data
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } finally {
      user.value = null
      initialized.value = true
    }
  }

  return { user, initialized, initialize, register, login, refreshMe, logout }
})

