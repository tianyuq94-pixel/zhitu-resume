<script setup lang="ts">
import { t } from '@/i18n'
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
  { label: 'Workbench', to: '/app', icon: 'grid' },
  { label: 'My CV', to: '/app/resume', icon: 'file' },
  { label: 'Job-tailored CV', to: '/app/custom-resumes', icon: 'wand' },
  { label: 'Job match', to: '/app/job-match', icon: 'target' },
  { label: 'AI Interview', to: '/app/interview', icon: 'chat' },
]

const pageTitle = computed(() => String(route.meta.title ?? 'Workbench'))

const handleLogout = async () => {
  loggingOut.value = true
  await authStore.logout()
  await router.push({ name: 'landing' })
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/app" :aria-label="t('Return to workspace')">
        <BrandLogo />
        <span>
          <strong>{{ t("Zhitu CV") }}</strong>
          <small>{{ t("CAREER RESUME") }}</small>
        </span>
      </RouterLink>

      <nav class="main-nav" :aria-label="t('Main features')">
        <RouterLink to="/">{{ t("← Back to the three entry points") }}</RouterLink>
        <RouterLink v-for="item in navigation" :key="item.to" :to="item.to">
          <span class="nav-icon" aria-hidden="true">
            <svg v-if="item.icon === 'grid'" viewBox="0 0 24 24"><path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z" /></svg>
            <svg v-else-if="item.icon === 'file'" viewBox="0 0 24 24"><path d="M6 3h8l4 4v14H6zM14 3v5h4M9 12h6M9 16h6" /></svg>
            <svg v-else-if="item.icon === 'wand'" viewBox="0 0 24 24"><path d="m5 19 10-10 4 4L9 23zM14 4l1-3 1 3 3 1-3 1-1 3-1-3-3-1zM5 7l.7-2 .8 2 2 .8-2 .7-.8 2-.7-2-2-.7z" /></svg>
            <svg v-else-if="item.icon === 'target'" viewBox="0 0 24 24"><path d="M20 12a8 8 0 1 1-8-8M18 6l-6 6M16 3h5v5M12 8a4 4 0 1 0 4 4" /></svg>
            <svg v-else viewBox="0 0 24 24"><path d="M4 5h16v12H9l-5 4zM8 9h8M8 13h5" /></svg>
          </span>
          <span>{{ t(item.label) }}</span>
        </RouterLink>
      </nav>

      <div class="sidebar-footer logged-in-footer">
        <RouterLink class="signed-in-user" to="/app/profile">
          <div class="user-avatar">{{ t(authStore.user?.username.slice(0, 1).toUpperCase()) }}</div>
          <div>
            <strong>{{ t(authStore.user?.username.startsWith('guest_') ? 'Guest workspace' : authStore.user?.username) }}</strong>
            <small>{{ t(authStore.user?.profile_completed ? 'Personal details' : 'Complete your job-seeking profile') }}</small>
          </div>
        </RouterLink>
        <button type="button" :disabled="loggingOut" @click="handleLogout">
          {{ t(loggingOut ? 'Exiting' : 'Exit') }}
        </button>
      </div>
    </aside>

    <div class="content-shell">
      <header class="topbar">
        <div>
          <span class="topbar-label">{{ t("Zhitu CV · Smart Career Assistant") }}</span>
          <h1>{{ t(pageTitle) }}</h1>
        </div>
        <span class="version-chip">{{ t("V1.0") }}</span>
      </header>

      <main>
        <RouterView />
      </main>
    </div>
  </div>
</template>
