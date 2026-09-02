<script setup lang="ts">
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
    errorMessage.value = '两次输入的密码不一致'
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
    errorMessage.value = getApiErrorMessage(error, isRegister.value ? '注册失败，请稍后重试' : '登录失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <RouterLink class="auth-brand" to="/">
      <BrandLogo />
      <span><strong>职途简历</strong><small>CAREER RESUME</small></span>
    </RouterLink>

    <div class="auth-panel">
      <section class="auth-message">
        <span>AI CAREER WORKSPACE</span>
        <h1>{{ isRegister ? '从一份真实简历，开始你的求职准备。' : '欢迎回来，继续完善你的求职计划。' }}</h1>
        <p>简历诊断、岗位匹配、定制简历和岗位模拟面试，都在一个工作台中完成。</p>
        <div class="auth-steps">
          <i>1</i><span>进入工作台</span><i>2</i><span>上传主简历</span><i>3</i><span>按需完善档案</span>
        </div>
      </section>

      <section class="auth-form-card">
        <span class="eyebrow">{{ isRegister ? 'CREATE ACCOUNT' : 'SIGN IN' }}</span>
        <h2>{{ isRegister ? '创建账户' : '登录账户' }}</h2>
        <p>{{ isRegister ? '无需手机号，使用用户名和密码即可注册。' : '输入用户名和密码进入工作台。' }}</p>

        <form @submit.prevent="submit">
          <label>
            <span>用户名</span>
            <input v-model="username" name="username" autocomplete="username" minlength="4" maxlength="32" pattern="[A-Za-z0-9_]+" placeholder="4–32 位字母、数字或下划线" required />
          </label>
          <label>
            <span>密码</span>
            <input v-model="password" name="password" type="password" :autocomplete="isRegister ? 'new-password' : 'current-password'" :minlength="isRegister ? 8 : 1" maxlength="128" placeholder="至少 8 位" required />
          </label>
          <label v-if="isRegister">
            <span>确认密码</span>
            <input v-model="confirmPassword" name="confirm-password" type="password" autocomplete="new-password" minlength="8" maxlength="128" placeholder="再次输入密码" required />
          </label>

          <div v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</div>
          <button class="auth-submit" type="submit" :disabled="submitting">
            {{ submitting ? '正在处理…' : isRegister ? '注册并进入' : '登录' }}
          </button>
        </form>

        <div class="auth-switch">
          {{ isRegister ? '已经有账户？' : '还没有账户？' }}
          <RouterLink :to="isRegister ? '/login' : '/register'">{{ isRegister ? '直接登录' : '免费注册' }}</RouterLink>
        </div>
      </section>
    </div>
  </div>
</template>
