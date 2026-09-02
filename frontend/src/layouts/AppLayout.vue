<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

import BrandLogo from '@/components/BrandLogo.vue'
import { useAuthStore } from '@/stores'

type NavigationItem = {
  label: string
  to: string
  icon: string
}

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const loggingOut = ref(false)

const navigation: NavigationItem[] = [
  { label: '工作台', to: '/app', icon: 'grid' },
  { label: '我的简历', to: '/app/resume', icon: 'file' },
  { label: '岗位定制简历', to: '/app/custom-resumes', icon: 'wand' },
  { label: '岗位匹配', to: '/app/job-match', icon: 'target' },
  { label: 'AI 面试', to: '/app/interview', icon: 'chat' },
]

const pageTitle = computed(() => String(route.meta.title ?? '工作台'))

const handleLogout = async () => {
  loggingOut.value = true
  await authStore.logout()
  await router.push({ name: 'landing' })
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/app" aria-label="返回工作台">
        <BrandLogo />
        <span>
          <strong>职途简历</strong>
          <small>CAREER RESUME</small>
        </span>
      </RouterLink>

      <nav class="main-nav" aria-label="主要功能">
        <RouterLink v-for="item in navigation" :key="item.to" :to="item.to">
          <span class="nav-icon" aria-hidden="true">
            <svg v-if="item.icon === 'grid'" viewBox="0 0 24 24"><path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z" /></svg>
            <svg v-else-if="item.icon === 'file'" viewBox="0 0 24 24"><path d="M6 3h8l4 4v14H6zM14 3v5h4M9 12h6M9 16h6" /></svg>
            <svg v-else-if="item.icon === 'wand'" viewBox="0 0 24 24"><path d="m5 19 10-10 4 4L9 23zM14 4l1-3 1 3 3 1-3 1-1 3-1-3-3-1zM5 7l.7-2 .8 2 2 .8-2 .7-.8 2-.7-2-2-.7z" /></svg>
            <svg v-else-if="item.icon === 'target'" viewBox="0 0 24 24"><path d="M20 12a8 8 0 1 1-8-8M18 6l-6 6M16 3h5v5M12 8a4 4 0 1 0 4 4" /></svg>
            <svg v-else viewBox="0 0 24 24"><path d="M4 5h16v12H9l-5 4zM8 9h8M8 13h5" /></svg>
          </span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="sidebar-footer logged-in-footer">
        <RouterLink class="signed-in-user" to="/app/profile">
          <div class="user-avatar">{{ authStore.user?.username.slice(0, 1).toUpperCase() }}</div>
          <div>
            <strong>{{ authStore.user?.username }}</strong>
            <small>{{ authStore.user?.profile_completed ? '个人资料' : '完善求职档案' }}</small>
          </div>
        </RouterLink>
        <button type="button" :disabled="loggingOut" @click="handleLogout">
          {{ loggingOut ? '退出中' : '退出' }}
        </button>
      </div>
    </aside>

    <div class="content-shell">
      <header class="topbar">
        <div>
          <span class="topbar-label">职途简历 · 智能求职助手</span>
          <h1>{{ pageTitle }}</h1>
        </div>
        <span class="version-chip">V1.0</span>
      </header>

      <main>
        <RouterView />
      </main>
    </div>
  </div>
</template>
