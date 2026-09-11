import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '@/layouts/AppLayout.vue'
import { pinia, useAuthStore } from '@/stores'
import CustomResumeView from '@/views/CustomResumeView.vue'
import DashboardView from '@/views/DashboardView.vue'
import AgentInterviewView from '@/views/AgentInterviewView.vue'
import { api } from '@/services/api'
import JobMatchView from '@/views/JobMatchView.vue'
import InterviewView from '@/views/InterviewView.vue'
import HubView from '@/views/HubView.vue'
import PersonaView from '@/views/PersonaView.vue'
import AuthView from '@/views/AuthView.vue'
import AgentView from '@/views/AgentView.vue'
import ProfileView from '@/views/ProfileView.vue'
import ResumeView from '@/views/ResumeView.vue'
import ResumeDiagnosisView from '@/views/ResumeDiagnosisView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/me', component: PersonaView, meta: { title: '齐天宇的 AI 分身', publicPreview: true } },
    { path: '/agent/interview', component: AgentInterviewView, meta: { title: '模拟面试', agentGuest: true } },
    {
      path: '/agent',
      name: 'agent-preview',
      component: AgentView,
      meta: { title: '求职 Agent', publicPreview: true },
    },
    {
      path: '/',
      name: 'landing',
      component: HubView,
      meta: { title: '天宇的 AI 工作室', publicPreview: true },
    },
    {
      path: '/login',
      name: 'login',
      component: AuthView,
      props: { mode: 'login' },
      meta: { title: '登录', guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: AuthView,
      props: { mode: 'register' },
      meta: { title: '注册', guestOnly: true },
    },
    {
      path: '/app',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: DashboardView,
          meta: { title: '工作台' },
        },
        {
          path: 'resume',
          name: 'resumes',
          component: ResumeView,
          meta: { title: '我的简历' },
        },
        {
          path: 'resume/diagnosis',
          name: 'resume-diagnosis',
          component: ResumeDiagnosisView,
          meta: { title: 'AI 简历诊断', requiresProfile: true },
        },
        {
          path: 'custom-resumes',
          name: 'tailored-resumes',
          component: CustomResumeView,
          meta: { title: '岗位定制简历', requiresProfile: true },
        },
        {
          path: 'job-match',
          name: 'job-matching',
          component: JobMatchView,
          meta: { title: '岗位匹配', requiresProfile: true },
        },
        {
          path: 'interview',
          name: 'interviews',
          component: InterviewView,
          meta: { title: 'AI 面试', requiresProfile: true },
        },
        {
          path: 'profile',
          name: 'profile',
          component: ProfileView,
          meta: { title: '个人资料' },
        },
      ],
    },
    { path: '/resumes', redirect: '/app/resume' },
    { path: '/tailored-resumes', redirect: '/app/custom-resumes' },
    { path: '/job-matching', redirect: '/app/job-match' },
    { path: '/interviews', redirect: '/app/interview' },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.publicPreview) return
  if (to.meta.agentGuest) {
    try { await api.post('/auth/guest'); return } catch { return '/agent' }
  }
  const authStore = useAuthStore(pinia)
  await authStore.initialize()
  // Guest identity may have been established by the public Agent or persona page.
  if (to.matched.some(record => record.meta.requiresAuth)) {
    try { await authStore.refreshMe() } catch { authStore.user = null }
  }

  if (to.matched.some((record) => record.meta.requiresAuth) && !authStore.user) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && authStore.user && !authStore.user.username.startsWith('guest_')) {
    return { name: 'dashboard' }
  }
  if (to.matched.some((record) => record.meta.requiresProfile) && !authStore.user?.profile_completed) {
    return { name: 'profile', query: { onboarding: '1', redirect: to.fullPath } }
  }
})

router.afterEach((to) => {
  const title = String(to.meta.title ?? '职途简历')
  document.title = title === '职途简历' ? title : `${title} · 职途简历`
})

export default router
