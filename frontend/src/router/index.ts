import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '@/layouts/AppLayout.vue'
import { pinia, useAuthStore } from '@/stores'
import AuthView from '@/views/AuthView.vue'
import CustomResumeView from '@/views/CustomResumeView.vue'
import DashboardView from '@/views/DashboardView.vue'
import LandingView from '@/views/LandingView.vue'
import JobMatchView from '@/views/JobMatchView.vue'
import InterviewView from '@/views/InterviewView.vue'
import ProfileView from '@/views/ProfileView.vue'
import ResumeView from '@/views/ResumeView.vue'
import ResumeDiagnosisView from '@/views/ResumeDiagnosisView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: LandingView,
      meta: { title: '职途简历' },
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
  const authStore = useAuthStore(pinia)
  await authStore.initialize()

  if (to.matched.some((record) => record.meta.requiresAuth) && !authStore.user) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && authStore.user) {
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
