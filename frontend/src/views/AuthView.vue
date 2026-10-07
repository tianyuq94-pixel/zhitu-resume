<script setup lang="ts">
import { t } from '@/i18n'
import { computed, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import BrandLogo from '@/components/BrandLogo.vue'
import { getApiErrorMessage } from '@/services/api'
import { useAuthStore } from '@/stores'

const props = defineProps<{ mode: 'login' | 'register' }>()

const router = useRouter()
const authStore = useAuthStore()
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const errorMessage = ref('')
const submitting = ref(false)

const isRegister = computed(() => props.mode === 'register')

const submit = async () => {
  errorMessage.value = ''
  if (isRegister.value && password.value !== confirmPassword.value) {
    errorMessage.value = 'The two passwords entered do not match'
    return
  }
  submitting.value = true
  try {
    if (isRegister.value) {
      await authStore.register(username.value, password.value)
      await router.push({ name: 'dashboard' })
    } else {
      await authStore.login(username.value, password.value)
      await router.push({ name: 'dashboard' })
    }
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, isRegister.value ? 'Registration failed, please try again later' : 'Login failed, please try again later')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <RouterLink class="auth-brand" to="/">
      <BrandLogo />
      <span><strong>{{ t("Zhitu CV") }}</strong><small>{{ t("CAREER RESUME") }}</small></span>
    </RouterLink>

    <div class="auth-panel">
      <section class="auth-message">
        <span>{{ t("AI CAREER WORKSPACE") }}</span>
        <h1>{{ t(isRegister ? 'Start your job preparation from a real CV.' : 'Welcome back, continue refining your job search plan.') }}</h1>
        <p>{{ t("CV review, job matching, tailored CVs and mock job interviews, all in one workspace.") }}</p>
        <div class="auth-steps">
          <i>1</i><span>{{ t("Go to workspace") }}</span><i>2</i><span>{{ t("Upload master CV") }}</span><i>3</i><span>{{ t("Complete your profile as needed") }}</span>
        </div>
      </section>

      <section class="auth-form-card">
        <span class="eyebrow">{{ t(isRegister ? 'CREATE ACCOUNT' : 'SIGN IN') }}</span>
        <h2>{{ t(isRegister ? 'Create account' : 'Log in to account') }}</h2>
        <p>{{ t(isRegister ? 'No phone number needed; register with a username and password.' : 'Enter your username and password to access the workspace.') }}</p>

        <form @submit.prevent="submit">
          <label>
            <span>{{ t("Username") }}</span>
            <input v-model="username" name="username" autocomplete="username" minlength="4" maxlength="32" pattern="[A-Za-z0-9_]+" :placeholder="t('4–32 letters, numbers or underscores')" required />
          </label>
          <label>
            <span>{{ t("Password") }}</span>
            <input v-model="password" name="password" type="password" :autocomplete="isRegister ? 'new-password' : 'current-password'" :minlength="isRegister ? 8 : 1" maxlength="128" :placeholder="t('At least 8 characters')" required />
          </label>
          <label v-if="isRegister">
            <span>{{ t("Confirm password") }}</span>
            <input v-model="confirmPassword" name="confirm-password" type="password" autocomplete="new-password" minlength="8" maxlength="128" :placeholder="t('Re-enter password')" required />
          </label>

          <div v-if="errorMessage" class="form-error" role="alert">{{ t(errorMessage) }}</div>
          <button class="auth-submit" type="submit" :disabled="submitting">
            {{ t(submitting ? 'Processing…' : isRegister ? 'Register and enter' : 'Log in') }}
          </button>
        </form>

        <div class="auth-switch">
          {{ t(isRegister ? 'Already have an account?' : 'Don\'t have an account yet?') }}
          <RouterLink :to="isRegister ? '/login' : '/register'">{{ t(isRegister ? 'Log in directly' : 'Sign up for free') }}</RouterLink>
        </div>
      </section>
    </div>
  </div>
</template>
