<script setup lang="ts">
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
    errorMessage.value = getApiErrorMessage(error, '个人资料加载失败')
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
    successMessage.value = '求职档案已保存'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

const changePassword = async () => {
  passwordError.value = ''
  passwordSuccess.value = ''
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    passwordError.value = '两次输入的新密码不一致'
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
    passwordSuccess.value = '密码已更新，其他设备上的旧登录已失效'
  } catch (error) {
    passwordError.value = getApiErrorMessage(error, '密码修改失败')
  } finally {
    changingPassword.value = false
  }
}

onMounted(loadProfile)
</script>

<template>
  <section class="profile-page">
    <div class="module-intro profile-intro">
      <span class="eyebrow">CAREER PROFILE</span>
      <h2>{{ isOnboarding ? '先完善你的求职档案' : '个人资料' }}</h2>
      <p>{{ continueTarget ? '使用这项 AI 功能前，请先补充必要信息；保存后会自动继续。' : '这些信息会帮助 AI 理解你的背景和求职目标。未填写的内容不会被 AI 擅自补充。' }}</p>
    </div>

    <div v-if="loading" class="profile-loading">正在加载个人资料…</div>
    <template v-else>
      <form class="profile-card" @submit.prevent="saveProfile">
        <div class="card-heading">
          <div><span>01</span><h3>求职档案</h3></div>
          <small>带 * 的信息用于判断档案是否完整</small>
        </div>

        <div class="profile-form-grid">
          <label><span>姓名</span><input v-model="form.real_name" maxlength="50" placeholder="选填，仅用于简历内容" /></label>
          <label><span>学校 *</span><input v-model="form.school" maxlength="100" placeholder="例如：复旦大学" required /></label>
          <label><span>专业 *</span><input v-model="form.major" maxlength="100" placeholder="例如：计算机科学与技术" required /></label>
          <label>
            <span>学历 *</span>
            <select v-model="form.degree" required><option value="" disabled>请选择</option><option>专科</option><option>本科</option><option>硕士</option><option>博士</option></select>
          </label>
          <label><span>毕业年份 *</span><input v-model.number="form.graduation_year" type="number" min="2000" max="2100" placeholder="例如：2027" required /></label>
          <label><span>求职方向 *</span><input v-model="form.career_direction" maxlength="100" placeholder="例如：前端开发" required /></label>
          <label><span>意向城市</span><input v-model="citiesText" maxlength="100" placeholder="例如：福州、厦门、深圳" /></label>
          <label>
            <span>求职类型 *</span>
            <select v-model="form.job_type" required><option value="" disabled>请选择</option><option>校招</option><option>社招</option><option>实习</option></select>
          </label>
        </div>

        <div v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</div>
        <div v-if="successMessage" class="form-success" role="status">{{ successMessage }}</div>
        <div class="profile-actions"><button class="save-button" type="submit" :disabled="saving">{{ saving ? '保存中…' : continueTarget ? '保存并继续' : '保存求职档案' }}</button></div>
      </form>

      <form class="profile-card password-card" @submit.prevent="changePassword">
        <div class="card-heading"><div><span>02</span><h3>修改密码</h3></div><small>修改后其他设备需要重新登录</small></div>
        <div class="profile-form-grid password-grid">
          <label><span>当前密码</span><input v-model="passwordForm.current_password" type="password" autocomplete="current-password" required /></label>
          <label><span>新密码</span><input v-model="passwordForm.new_password" type="password" autocomplete="new-password" minlength="8" maxlength="128" required /></label>
          <label><span>确认新密码</span><input v-model="passwordForm.confirm_password" type="password" autocomplete="new-password" minlength="8" maxlength="128" required /></label>
        </div>
        <div v-if="passwordError" class="form-error" role="alert">{{ passwordError }}</div>
        <div v-if="passwordSuccess" class="form-success" role="status">{{ passwordSuccess }}</div>
        <div class="profile-actions"><button class="secondary-save-button" type="submit" :disabled="changingPassword">{{ changingPassword ? '修改中…' : '修改密码' }}</button></div>
      </form>
    </template>
  </section>
</template>
