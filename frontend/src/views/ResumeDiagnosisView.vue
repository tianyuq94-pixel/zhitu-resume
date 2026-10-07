<script setup lang="ts">
import { t, locale } from '@/i18n'
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { api, getApiErrorMessage } from '@/services/api'

type ResumeSummary = {
  original_name: string
  content_version: number
  confirmed_at: string | null
}

type DimensionScores = {
  information_completeness: number
  content_quality: number
  achievement_quantification: number
  professional_expression: number
  career_direction_fit: number
}

type Suggestion = {
  source_text: string
  suggested_text: string
  reason: string
}

type Diagnosis = {
  id: number
  resume_version: number
  overall_score: number
  dimension_scores: DimensionScores
  strengths: string[]
  issues: string[]
  suggestions: Suggestion[]
  created_at: string
}

const resume = ref<ResumeSummary | null>(null)
const diagnosis = ref<Diagnosis | null>(null)
const loading = ref(true)
const generating = ref(false)
const errorMessage = ref('')

const dimensions = computed(() => {
  if (!diagnosis.value) return []
  const scores = diagnosis.value.dimension_scores
  return [
    { label: 'Information completeness', score: scores.information_completeness },
    { label: 'Content quality', score: scores.content_quality },
    { label: 'Quantified results', score: scores.achievement_quantification },
    { label: 'Professionalism of expression', score: scores.professional_expression },
    { label: 'Direction match', score: scores.career_direction_fit },
  ]
})

const formatDate = (value: string) => {
  const utcValue = /(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`
  return new Intl.DateTimeFormat(locale.value === 'zh' ? 'zh-CN' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(utcValue))
}

const loadPage = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const [resumeResponse, diagnosisResponse] = await Promise.all([
      api.get<ResumeSummary | null>('/resumes/primary'),
      api.get<Diagnosis | null>('/resumes/primary/diagnoses/latest'),
    ])
    resume.value = resumeResponse.data
    diagnosis.value = diagnosisResponse.data
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Failed to load diagnosis page')
  } finally {
    loading.value = false
  }
}

const generateDiagnosis = async () => {
  generating.value = true
  errorMessage.value = ''
  try {
    const response = await api.post<Diagnosis>('/resumes/primary/diagnoses', undefined, { timeout: 90_000 })
    diagnosis.value = response.data
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'AI review failed. Please try again later.')
  } finally {
    generating.value = false
  }
}

onMounted(loadPage)
</script>

<template>
  <section class="diagnosis-page">
    <div class="diagnosis-header">
      <div class="module-intro">
        <span class="eyebrow">{{ t("AI RESUME DIAGNOSIS") }}</span>
        <h2>{{ t("AI CV Review") }}</h2>
        <p>{{ t("The diagnosis is based only on the main CV and job profile you confirm, and will not write in experience that does not exist.") }}</p>
      </div>
      <RouterLink class="back-text-link" to="/app/resume">{{ t("← Back to my CV") }}</RouterLink>
    </div>

    <div v-if="loading" class="profile-loading">{{ t("Loading diagnostic information…") }}</div>
    <template v-else>
      <div v-if="!resume" class="diagnosis-empty-card">
        <span>01</span><h3>{{ t("No main CV yet") }}</h3><p>{{ t("Upload and confirm the CV text before starting AI diagnosis.") }}</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">{{ t("Go to upload CV") }}</RouterLink>
      </div>

      <div v-else-if="!resume.confirmed_at" class="diagnosis-empty-card">
        <span>02</span><h3>{{ t("CV text not yet confirmed") }}</h3><p>{{ t("Please check whether the parsed text is accurate; the AI will only use this content once confirmed.") }}</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">{{ t("Go to confirm text") }}</RouterLink>
      </div>

      <div v-else-if="!diagnosis" class="diagnosis-ready-card">
        <div class="diagnosis-ready-visual" aria-hidden="true"><b>{{ t("AI") }}</b><i></i><i></i><i></i></div>
        <div>
          <span>{{ t("Ready") }}</span>
          <h3>{{ t("Analyse") }} {{ t(resume.original_name) }}</h3>
          <p>{{ t("Usually takes a few dozen seconds. The system checks the completeness of the result; if it fails, you can retry directly.") }}</p>
          <button class="save-button diagnosis-main-button" type="button" :disabled="generating" @click="generateDiagnosis">
            {{ t(generating ? 'AI is analysing. Please wait…' : 'Start AI diagnosis') }}
          </button>
        </div>
      </div>

      <template v-else>
        <div class="diagnosis-summary-card">
          <div class="diagnosis-score">
            <span>{{ t("Overall score") }}</span><strong>{{ t(diagnosis.overall_score) }}</strong><small>/ 100</small>
          </div>
          <div class="diagnosis-summary-main">
            <div class="diagnosis-summary-heading">
              <div><span>{{ t("Diagnosis complete") }}</span><h3>{{ t(resume.original_name) }}</h3></div>
              <button type="button" :disabled="generating" @click="generateDiagnosis">{{ t(generating ? 'Re-analysing…' : 'Re-diagnose') }}</button>
            </div>
            <div class="dimension-grid">
              <div v-for="item in dimensions" :key="item.label" class="dimension-item">
                <div><span>{{ t(item.label) }}</span><b>{{ t(item.score) }}</b></div>
                <i><em :style="{ width: `${item.score}%` }"></em></i>
              </div>
            </div>
            <small>{{ t("Based on master CV content version") }} {{ t(diagnosis.resume_version) }} · {{ t(formatDate(diagnosis.created_at)) }}</small>
          </div>
        </div>

        <div class="diagnosis-columns">
          <article class="diagnosis-list-card strengths-card">
            <div class="card-heading"><div><span>{{ t("STRENGTHS") }}</span><h3>{{ t("CV strengths") }}</h3></div></div>
            <ol><li v-for="item in diagnosis.strengths" :key="item">{{ t(item) }}</li></ol>
          </article>
          <article class="diagnosis-list-card issues-card">
            <div class="card-heading"><div><span>{{ t("ISSUES") }}</span><h3>{{ t("Main issues") }}</h3></div></div>
            <ol><li v-for="item in diagnosis.issues" :key="item">{{ t(item) }}</li></ol>
          </article>
        </div>

        <section class="suggestions-section">
          <div class="section-heading diagnosis-section-heading">
            <div><span class="eyebrow">{{ t("SUGGESTIONS") }}</span><h2>{{ t("Item-by-item revision suggestions") }}</h2></div>
            <small>{{ t(diagnosis.suggestions.length) }} {{ t("suggestions") }}</small>
          </div>
          <article v-for="(item, index) in diagnosis.suggestions" :key="`${index}-${item.source_text}`" class="suggestion-card">
            <div class="suggestion-index">{{ t(String(index + 1).padStart(2, '0')) }}</div>
            <div class="suggestion-content">
              <div class="suggestion-comparison">
                <div><span>{{ t("Original text") }}</span><p>{{ t(item.source_text) }}</p></div>
                <div><span>{{ t("Suggested wording") }}</span><p>{{ t(item.suggested_text) }}</p></div>
              </div>
              <div class="suggestion-reason"><b>{{ t("Reason for change") }}</b><span>{{ t(item.reason) }}</span></div>
            </div>
          </article>
        </section>

        <div class="ai-reference-note">{{ t("AI scores and suggestions are for job preparation reference only and do not represent recruitment outcomes. Please reconfirm important content against your real experience.") }}</div>
      </template>

      <div v-if="errorMessage" class="form-error diagnosis-error" role="alert">{{ t(errorMessage) }}</div>
    </template>
  </section>
</template>
