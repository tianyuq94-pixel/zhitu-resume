<script setup lang="ts">
import { t, locale } from '@/i18n'
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { api, getApiErrorMessage } from '@/services/api'

type ResumeSummary = {
  original_name: string
  content_version: number
  confirmed_at: string | null
}

type KeyRequirement = { requirement: string; jd_evidence: string }
type MatchedItem = { requirement: string; resume_evidence: string }
type MissingItem = { requirement: string; explanation: string }

type JobMatch = {
  id: number
  resume_version: number
  job_title: string
  company_name: string | null
  job_description: string
  match_score: number
  key_requirements: KeyRequirement[]
  matched_items: MatchedItem[]
  missing_items: MissingItem[]
  verdict: 'recommend' | 'consider' | 'low'
  verdict_reason: string
  improvements: string[]
  created_at: string
}

const resume = ref<ResumeSummary | null>(null)
const result = ref<JobMatch | null>(null)
const loading = ref(true)
const analyzing = ref(false)
const showForm = ref(true)
const errorMessage = ref('')

const form = reactive({
  job_title: '',
  company_name: '',
  job_description: '',
})

const effectiveJdLength = computed(() => form.job_description.replace(/\s/g, '').length)
const canAnalyze = computed(() => form.job_title.trim().length >= 2 && effectiveJdLength.value >= 30)

const verdictText = computed(() => {
  if (!result.value) return ''
  return { recommend: 'Recommended applications', consider: 'You can try', low: 'Not recommended for now' }[result.value.verdict]
})

const formatDate = (value: string) => {
  const utcValue = /(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`
  return new Intl.DateTimeFormat(locale.value === 'zh' ? 'zh-CN' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(utcValue))
}

const populateForm = (jobMatch: JobMatch) => {
  form.job_title = jobMatch.job_title
  form.company_name = jobMatch.company_name ?? ''
  form.job_description = jobMatch.job_description
}

const loadPage = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const [resumeResponse, matchResponse] = await Promise.all([
      api.get<ResumeSummary | null>('/resumes/primary'),
      api.get<JobMatch | null>('/job-matches/current'),
    ])
    resume.value = resumeResponse.data
    result.value = matchResponse.data
    if (matchResponse.data) {
      populateForm(matchResponse.data)
      showForm.value = false
    }
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Failed to load the job match page')
  } finally {
    loading.value = false
  }
}

const analyzeJob = async () => {
  errorMessage.value = ''
  if (!canAnalyze.value) {
    errorMessage.value = 'Please enter the job title and a job description of at least 30 valid characters'
    return
  }
  analyzing.value = true
  try {
    const response = await api.post<JobMatch>(
      '/job-matches',
      {
        job_title: form.job_title,
        company_name: form.company_name || null,
        job_description: form.job_description,
      },
      { timeout: 90_000 },
    )
    result.value = response.data
    populateForm(response.data)
    showForm.value = false
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'AI job matching failed, please try again later')
  } finally {
    analyzing.value = false
  }
}

const startNewAnalysis = () => {
  showForm.value = true
  errorMessage.value = ''
}

onMounted(loadPage)
</script>

<template>
  <section class="job-match-page">
    <div class="module-intro job-match-intro">
      <span class="eyebrow">{{ t("JOB MATCHING") }}</span>
      <h2>{{ t("Job match") }}</h2>
      <p>{{ t("Compare the target role's JD with the confirmed master CV item by item to determine which requirements already have evidence and which are not yet reflected in the CV.") }}</p>
    </div>

    <div v-if="loading" class="profile-loading">{{ t("Loading role match information…") }}</div>
    <template v-else>
      <div v-if="!resume" class="diagnosis-empty-card">
        <span>01</span><h3>{{ t("No main CV yet") }}</h3><p>{{ t("Job matching must be based on a real master CV.") }}</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">{{ t("Go to upload CV") }}</RouterLink>
      </div>

      <div v-else-if="!resume.confirmed_at" class="diagnosis-empty-card">
        <span>02</span><h3>{{ t("Main CV text not yet confirmed") }}</h3><p>{{ t("Please check the parsed text to avoid the AI matching with incorrect content.") }}</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">{{ t("Go to confirm text") }}</RouterLink>
      </div>

      <template v-else>
        <form v-if="showForm || !result" class="job-match-form-card" @submit.prevent="analyzeJob">
          <div class="job-match-form-heading">
            <div><span>{{ t("Role information") }}</span><h3>{{ t(result ? 'Analyse a new target role' : 'Is this role right for me?') }}</h3></div>
            <button v-if="result" type="button" @click="showForm = false">{{ t("Cancel") }}</button>
          </div>

          <div class="job-basic-grid">
            <label><span>{{ t("Job title") }} <b>*</b></span>
              <input v-model="form.job_title" maxlength="100" :placeholder="t('For example: Front-end Development Engineer')" />
            </label>
            <label><span>{{ t("Company name") }} <small>{{ t("Optional") }}</small></span>
              <input v-model="form.company_name" maxlength="100" :placeholder="t('For example: XX Technology')" />
            </label>
          </div>

          <label class="job-jd-field"><span class="field-label">{{ t("Role JD") }} <b>*</b></span>
            <textarea v-model="form.job_description" maxlength="20000" :placeholder="t('Paste the job responsibilities, requirements and desirable criteria…')"></textarea>
            <span class="field-count">{{ t(effectiveJdLength.toLocaleString()) }} {{ t("/ 20,000 valid characters") }}</span>
          </label>

          <div class="job-form-footer">
            <div><b>{{ t("Current master CV") }}</b><span>{{ t(resume.original_name) }} {{ t("· Content version") }} {{ t(resume.content_version) }}</span></div>
            <button class="save-button job-analyze-button" type="submit" :disabled="analyzing || !canAnalyze">
              {{ t(analyzing ? 'Analysing role match item by item…' : 'Start AI matching') }}
            </button>
          </div>
        </form>

        <template v-if="result && !showForm">
          <div class="job-match-summary">
            <div :class="['job-match-score', `verdict-${result.verdict}`]">
              <span>{{ t("Job match score") }}</span><strong>{{ t(result.match_score) }}</strong><small>/ 100</small>
            </div>
            <div class="job-match-summary-main">
              <div class="job-summary-topline">
                <div><span>{{ t(result.company_name || 'Target role') }}</span><h3>{{ t(result.job_title) }}</h3></div>
                <button type="button" @click="startNewAnalysis">{{ t("Analyse new role") }}</button>
              </div>
              <div :class="['verdict-badge', `verdict-${result.verdict}`]">{{ t(verdictText) }}</div>
              <p>{{ t(result.verdict_reason) }}</p>
              <small>{{ t("Based on master CV content version") }} {{ t(result.resume_version) }} · {{ t(formatDate(result.created_at)) }}</small>
            </div>
          </div>

          <section class="job-requirements-section">
            <div class="section-heading job-section-heading">
              <div><span class="eyebrow">{{ t("KEY REQUIREMENTS") }}</span><h2>{{ t("Key job requirements") }}</h2></div>
              <small>{{ t(result.key_requirements.length) }} {{ t("items") }}</small>
            </div>
            <div class="requirement-grid">
              <article v-for="(item, index) in result.key_requirements" :key="item.requirement">
                <span>{{ t(String(index + 1).padStart(2, '0')) }}</span><h3>{{ t(item.requirement) }}</h3>
                <blockquote>{{ t(item.jd_evidence) }}</blockquote>
              </article>
            </div>
          </section>

          <div class="job-evidence-columns">
            <section class="job-evidence-card matched-card">
              <div class="card-heading"><div><span>{{ t("MATCHED") }}</span><h3>{{ t("Matched skills") }}</h3></div><small>{{ t(result.matched_items.length) }} {{ t("items") }}</small></div>
              <div v-if="result.matched_items.length" class="evidence-list">
                <article v-for="item in result.matched_items" :key="item.requirement">
                  <h4>{{ t(item.requirement) }}</h4><p>{{ t(item.resume_evidence) }}</p><small>{{ t("From the original main CV") }}</small>
                </article>
              </div>
              <p v-else class="empty-evidence">{{ t("No directly matching evidence found in the current CV.") }}</p>
            </section>

            <section class="job-evidence-card missing-card">
              <div class="card-heading"><div><span>{{ t("NOT SHOWN") }}</span><h3>{{ t("Not shown on CV") }}</h3></div><small>{{ t(result.missing_items.length) }} {{ t("items") }}</small></div>
              <div v-if="result.missing_items.length" class="evidence-list">
                <article v-for="item in result.missing_items" :key="item.requirement">
                  <h4>{{ t(item.requirement) }}</h4><p>{{ t(item.explanation) }}</p><small>{{ t("does not necessarily mean you lack") }}</small>
                </article>
              </div>
              <p v-else class="empty-evidence">{{ t("All key job requirements can be evidenced in the CV.") }}</p>
            </section>
          </div>

          <section class="job-improvements-card">
            <div><span>{{ t("BEFORE APPLYING") }}</span><h3>{{ t("Areas for improvement before applying") }}</h3></div>
            <ol><li v-for="item in result.improvements" :key="item">{{ t(item) }}</li></ol>
          </section>

          <div class="job-next-actions">
            <div><b>{{ t("Continue preparing for this role") }}</b><span>{{ t("Role information will be carried over automatically in the next feature.") }}</span></div>
            <RouterLink :to="{ path: '/app/custom-resumes', query: { jobMatchId: result.id } }">{{ t("Generate role-customised CV") }}</RouterLink>
            <RouterLink :to="{ path: '/app/interview', query: { jobMatchId: result.id } }">{{ t("Start role-play mock interview") }}</RouterLink>
          </div>

          <div class="ai-reference-note">{{ t("The match results are based only on the information presented in the current CV. They are a job preparation reference and do not represent the recruiter's actual screening conclusion.") }}</div>
        </template>

        <div v-if="errorMessage" class="form-error diagnosis-error" role="alert">{{ t(errorMessage) }}</div>
      </template>
    </template>
  </section>
</template>
