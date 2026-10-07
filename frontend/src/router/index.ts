import { createRouter, createWebHistory } from 'vue-router'
import { watch } from 'vue'
import { locale, t } from '@/i18n'

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
import { projects, l, say } from '@/content/portfolio'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: (to) => to.hash ? { el: to.hash, top: 20 } : { top: 0 },
  routes: [
    { path: '/demo', component: () => import('@/views/DemoView.vue'), meta: { title: 'Recorded example', publicPreview: true } },
    { path: '/projects/:slug', component: () => import('@/views/ProjectView.vue'), meta: { title: 'Project case study', publicPreview: true } },
    { path: '/me', component: PersonaView, meta: { title: 'Tianyu Qi\'s AI Persona', publicPreview: true } },
    { path: '/agent/interview', component: AgentInterviewView, meta: { title: 'Mock interview', agentGuest: true } },
    {
      path: '/agent',
      name: 'agent-preview',
      component: AgentView,
      meta: { title: 'Career Agent', publicPreview: true },
    },
    {
      path: '/',
      name: 'landing',
      component: HubView,
      meta: { title: 'Tianyu\'s AI Studio', publicPreview: true },
    },
    {
      path: '/login',
      name: 'login',
      component: AuthView,
      props: { mode: 'login' },
      meta: { title: 'Log in', guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: AuthView,
      props: { mode: 'register' },
      meta: { title: 'Register', guestOnly: true },
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
          meta: { title: 'Workbench' },
        },
        {
          path: 'resume',
          name: 'resumes',
          component: ResumeView,
          meta: { title: 'My CV' },
        },
        {
          path: 'resume/diagnosis',
          name: 'resume-diagnosis',
          component: ResumeDiagnosisView,
          meta: { title: 'AI CV Review', requiresProfile: true },
        },
        {
          path: 'custom-resumes',
          name: 'tailored-resumes',
          component: CustomResumeView,
          meta: { title: 'Job-tailored CV', requiresProfile: true },
        },
        {
          path: 'job-match',
          name: 'job-matching',
          component: JobMatchView,
          meta: { title: 'Job match', requiresProfile: true },
        },
        {
          path: 'interview',
          name: 'interviews',
          component: InterviewView,
          meta: { title: 'AI Interview', requiresProfile: true },
        },
        {
          path: 'profile',
          name: 'profile',
          component: ProfileView,
          meta: { title: 'Personal details' },
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
    try { await authStore.enterGuest() }
    catch { return { name: 'login', query: { redirect: to.fullPath } } }
  }
  if (to.meta.guestOnly && authStore.user && !authStore.user.username.startsWith('guest_')) {
    return { name: 'dashboard' }
  }
  if (to.matched.some((record) => record.meta.requiresProfile) && !authStore.user?.profile_completed) {
    return { name: 'profile', query: { onboarding: '1', redirect: to.fullPath } }
  }
})

function updateTitle() {
  const current = router.currentRoute.value
  const project = projects.find(p => p.id === current.params.slug)
  if (current.path.startsWith('/projects/')) {
    document.title = `${project ? l(project.name) : say('Project not found', '未找到项目')} · ${say('Tianyu Qi', '齐天宇')}`
    return
  }
  if (current.path === '/demo') { document.title = `${say('Recorded example', '成果示例')} · ${say('Tianyu Qi', '齐天宇')}`; return }
  const title = t(router.currentRoute.value.meta.title ?? 'Zhitu CV')
  document.title = title === t('Zhitu CV') ? title : `${title} · ${t('Zhitu CV')}`
}
router.afterEach(updateTitle)
watch(locale, updateTitle)

export default router
