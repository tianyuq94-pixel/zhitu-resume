<script setup lang="ts">
import { t } from '@/i18n'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, getApiErrorMessage } from '@/services/api'
import { useAuthStore } from '@/stores'

type Profile = {
  real_name: string | null
  school: string | null
  major: string | null
  degree: string | null
  graduation_year: number | null
  career_direction: string | null
  desired_cities: string[]
  job_type: string | null
  profile_completed: boolean
}

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const passwordError = ref('')
const passwordSuccess = ref('')
const changingPassword = ref(false)
const citiesText = ref('')

const form = reactive({
  real_name: '',
  school: '',
  major: '',
  degree: '',
  graduation_year: undefined as number | undefined,
  career_direction: '',
  job_type: '',
})

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

const isOnboarding = computed(() => route.query.onboarding === '1' || !authStore.user?.profile_completed)
const continueTarget = computed(() => {
  const target = route.query.redirect
  if (typeof target !== 'string' || !target.startsWith('/app/') || target.startsWith('/app/profile')) return null
  return target
})

const loadProfile = async () => {
  loading.value = true
  try {
    const response = await api.get<Profile>('/profile')
    const profile = response.data
    form.real_name = profile.real_name ?? ''
    form.school = profile.school ?? ''
    form.major = profile.major ?? ''
    form.degree = profile.degree ?? ''
    form.graduation_year = profile.graduation_year ?? undefined
    form.career_direction = profile.career_direction ?? ''
    form.job_type = profile.job_type ?? ''
    citiesText.value = profile.desired_cities.join('、')
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Failed to load personal details')
  } finally {
    loading.value = false
  }
}

const saveProfile = async () => {
  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await api.put<Profile>('/profile', {
      ...form,
      graduation_year: form.graduation_year || null,
      desired_cities: citiesText.value.split(/[、,，/\s]+/).filter(Boolean),
    })
    await authStore.refreshMe()
    if (continueTarget.value) {
      await router.replace(continueTarget.value)
      return
    }
    successMessage.value = 'Job search profile saved'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Save failed, please try again later')
  } finally {
    saving.value = false
  }
}

const changePassword = async () => {
  passwordError.value = ''
  passwordSuccess.value = ''
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    passwordError.value = 'The two new passwords entered do not match'
    return
  }
  changingPassword.value = true
  try {
    await api.put('/auth/password', {
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    passwordSuccess.value = 'Password updated; old logins on other devices have been invalidated'
  } catch (error) {
    passwordError.value = getApiErrorMessage(error, 'Failed to change password')
  } finally {
    changingPassword.value = false
  }
}

onMounted(loadProfile)
</script>

<template>
  <section class="profile-page">
    <div class="module-intro profile-intro">
      <span class="eyebrow">{{ t("CAREER PROFILE") }}</span>
      <h2>{{ t(isOnboarding ? 'Complete your job-seeking profile first' : 'Personal details') }}</h2>
      <p>{{ t(continueTarget ? 'Before using this AI feature, please add the necessary information; once saved, it will continue automatically.' : 'This information helps the AI understand your background and job goals. Anything you leave blank will not be filled in by the AI on its own.') }}</p>
    </div>

    <div v-if="loading" class="profile-loading">{{ t("Loading profile…") }}</div>
    <template v-else>
      <form class="profile-card" @submit.prevent="saveProfile">
        <div class="card-heading">
          <div><span>01</span><h3>{{ t("Job search profile") }}</h3></div>
          <small>{{ t("Fields marked * are used to determine whether the profile is complete") }}</small>
        </div>

        <div class="profile-form-grid">
          <label><span>{{ t("Name") }}</span><input v-model="form.real_name" maxlength="50" :placeholder="t('Optional, used only for CV content')" /></label>
          <label><span>{{ t("School *") }}</span><input v-model="form.school" maxlength="100" :placeholder="t('For example: Fudan University')" required /></label>
          <label><span>{{ t("Specialism *") }}</span><input v-model="form.major" maxlength="100" :placeholder="t('For example: Computer Science and Technology')" required /></label>
          <label>
            <span>{{ t("Education *") }}</span>
            <select v-model="form.degree" required><option value="" disabled>{{ t("Please select") }}</option><option value="专科">{{ t("Diploma") }}</option><option value="本科">{{ t("Bachelor’s") }}</option><option value="硕士">{{ t("Master’s") }}</option><option value="博士">{{ t("Doctorate") }}</option></select>
          </label>
          <label><span>{{ t("Graduation year *") }}</span><input v-model.number="form.graduation_year" type="number" min="2000" max="2100" :placeholder="t('For example: 2027')" required /></label>
          <label><span>{{ t("Target role *") }}</span><input v-model="form.career_direction" maxlength="100" :placeholder="t('For example: front-end development')" required /></label>
          <label><span>{{ t("Preferred cities") }}</span><input v-model="citiesText" maxlength="100" :placeholder="t('For example: Fuzhou, Xiamen, Shenzhen')" /></label>
          <label>
            <span>{{ t("Job type *") }}</span>
            <select v-model="form.job_type" required><option value="" disabled>{{ t("Please select") }}</option><option value="校招">{{ t("Graduate role") }}</option><option value="社招">{{ t("Experienced role") }}</option><option value="实习">{{ t("Internship") }}</option></select>
          </label>
        </div>

        <div v-if="errorMessage" class="form-error" role="alert">{{ t(errorMessage) }}</div>
        <div v-if="successMessage" class="form-success" role="status">{{ t(successMessage) }}</div>
        <div class="profile-actions"><button class="save-button" type="submit" :disabled="saving">{{ t(saving ? 'Saving…' : continueTarget ? 'Save and continue' : 'Save job profile') }}</button></div>
      </form>

      <form v-if="authStore.user && !authStore.user.username.startsWith('guest_')" class="profile-card password-card" @submit.prevent="changePassword">
        <div class="card-heading"><div><span>02</span><h3>{{ t("Change password") }}</h3></div><small>{{ t("After changing, other devices will need to sign in again") }}</small></div>
        <div class="profile-form-grid password-grid">
          <label><span>{{ t("Current password") }}</span><input v-model="passwordForm.current_password" type="password" autocomplete="current-password" required /></label>
          <label><span>{{ t("New password") }}</span><input v-model="passwordForm.new_password" type="password" autocomplete="new-password" minlength="8" maxlength="128" required /></label>
          <label><span>{{ t("Confirm new password") }}</span><input v-model="passwordForm.confirm_password" type="password" autocomplete="new-password" minlength="8" maxlength="128" required /></label>
        </div>
        <div v-if="passwordError" class="form-error" role="alert">{{ t(passwordError) }}</div>
        <div v-if="passwordSuccess" class="form-success" role="status">{{ t(passwordSuccess) }}</div>
        <div class="profile-actions"><button class="secondary-save-button" type="submit" :disabled="changingPassword">{{ t(changingPassword ? 'Editing…' : 'Change password') }}</button></div>
      </form>
    </template>
  </section>
</template>
