<script setup lang="ts">
import { t } from '@/i18n'
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { api } from '@/services/api'

type ServiceState = 'checking' | 'ready' | 'offline'

const serviceState = ref<ServiceState>('checking')
const resumeExists = ref(false)
const readinessScore = ref<number | null>(null)

const readinessLabel = computed(() => {
  if (readinessScore.value !== null) return 'Latest CV diagnosis result'
  return resumeExists.value ? 'CV added. Waiting for AI diagnosis' : 'Add a CV to start the analysis'
})

const readinessStyle = computed(() => ({
  '--readiness-angle': `${(readinessScore.value ?? 0) * 3.6}deg`,
}))

const checkService = async () => {
  serviceState.value = 'checking'
  try {
    const response = await fetch('/api/v1/health/database')
    serviceState.value = response.ok ? 'ready' : 'offline'
  } catch {
    serviceState.value = 'offline'
  }
}

const loadReadiness = async () => {
  try {
    const [resumeResponse, diagnosisResponse] = await Promise.all([
      api.get('/resumes/primary'),
      api.get<{ overall_score: number } | null>('/resumes/primary/diagnoses/latest'),
    ])
    resumeExists.value = Boolean(resumeResponse.data)
    readinessScore.value = diagnosisResponse.data?.overall_score ?? null
  } catch {
    resumeExists.value = false
    readinessScore.value = null
  }
}

onMounted(() => {
  void checkService()
  void loadReadiness()
})
</script>

<template>
  <section class="dashboard-stack">
    <div class="hero-card">
      <div class="hero-copy">
        <span class="eyebrow">{{ t("CAREER WORKSPACE") }}</span>
        <h2>{{ t("Give every application") }}<br />{{ t("a clearer direction.") }}</h2>
        <p>{{ t("Starting from a real CV, complete role customisation, fit analysis and targeted mock interviews.") }}</p>
        <div class="hero-actions">
          <RouterLink class="primary-button" to="/app/resume">{{ t("Create my CV") }}</RouterLink>
          <RouterLink class="secondary-button" to="/app/job-match">{{ t("Explore role fit") }}</RouterLink>
        </div>
      </div>

      <RouterLink class="hero-visual" :to="readinessScore === null ? '/app/resume' : '/app/resume/diagnosis'" :style="readinessStyle" :aria-label="t('View CV readiness details')">
        <div class="score-orbit score-orbit-large"></div>
        <div class="score-orbit score-orbit-small"></div>
        <div :class="['score-card', { measured: readinessScore !== null }]">
          <span>{{ t("Readiness") }}</span>
          <strong>{{ t(readinessScore === null ? '—' : readinessScore) }}</strong>
          <small>{{ t(readinessLabel) }}</small>
        </div>
      </RouterLink>
    </div>

    <div class="section-heading">
      <div>
        <span class="eyebrow">{{ t("QUICK START") }}</span>
        <h2>{{ t("Start here") }}</h2>
      </div>
      <button class="service-status" type="button" @click="checkService">
        <span :class="['status-dot', serviceState]"></span>
        <template v-if="serviceState === 'checking'">{{ t("Checking core services") }}</template>
        <template v-else-if="serviceState === 'ready'">{{ t("Core services running normally") }}</template>
        <template v-else>{{ t("The backend service has not been started yet") }}</template>
      </button>
    </div>

    <div class="feature-grid">
      <RouterLink class="feature-card" to="/app/resume">
        <span class="feature-index">01</span>
        <h3>{{ t("Create master CV") }}</h3>
        <p>{{ t("Upload a PDF or Word file and confirm the education, projects, internships and skills the system has parsed.") }}</p>
        <span class="card-link">{{ t("Go to my CV") }} <b>→</b></span>
      </RouterLink>
      <RouterLink class="feature-card" to="/app/custom-resumes">
        <span class="feature-index">02</span>
        <h3>{{ t("Generate customised version") }}</h3>
        <p>{{ t("Reorganise your real experience around the target role to produce a CV you can keep editing and export.") }}</p>
        <span class="card-link">{{ t("Go to customised CV") }} <b>→</b></span>
      </RouterLink>
      <RouterLink class="feature-card" to="/app/interview">
        <span class="feature-index">03</span>
        <h3>{{ t("Start role interview") }}</h3>
        <p>{{ t("After specifying a role, answer five related questions, receive feedback on each, and finally view the full report.") }}</p>
        <span class="card-link">{{ t("Go to AI interview") }} <b>→</b></span>
      </RouterLink>
    </div>
  </section>
</template>
