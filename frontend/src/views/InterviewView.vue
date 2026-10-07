<script setup lang="ts">
import { t } from '@/i18n'
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { api, getApiErrorMessage } from '@/services/api'

type ResumeSummary = {
  original_name: string
  content_version: number
  confirmed_at: string | null
}

type JobMatch = {
  id: number
  job_title: string
  company_name: string | null
  job_description: string
}

type DimensionScores = {
  relevance: number
  specificity: number
  structure: number
  communication: number
}

type QuestionFeedback = {
  score: number
  dimension_scores: DimensionScores
  strengths: string[]
  issues: string[]
  suggestions: string[]
  answer_outline: string[]
}

type InterviewQuestion = {
  id: number
  sequence_no: number
  question_text: string
  focus_area: string
  answer_text: string | null
  feedback: QuestionFeedback | null
  answered_at: string | null
}

type FinalReport = {
  overall_score: number
  summary: string
  dimension_scores: {
    expression: number
    role_understanding: number
    experience_evidence: number
    answer_structure: number
  }
  strengths: string[]
  improvements: string[]
  practice_focus: string[]
}

type InterviewSession = {
  id: number
  resume_version: number
  job_match_id: number | null
  job_title: string
  company_name: string | null
  job_requirements: string | null
  status: 'answering' | 'reporting' | 'completed' | 'abandoned'
  current_question_index: number
  questions: InterviewQuestion[]
  final_feedback: FinalReport | null
  started_at: string | null
  completed_at: string | null
}

type Screen = 'prepare' | 'answer' | 'feedback' | 'reporting' | 'report'

const route = useRoute()
const router = useRouter()
const resume = ref<ResumeSummary | null>(null)
const session = ref<InterviewSession | null>(null)
const screen = ref<Screen>('prepare')
const loading = ref(true)
const generating = ref(false)
const submitting = ref(false)
const retryingReport = ref(false)
const abandoning = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const answerText = ref('')
const feedbackQuestionIndex = ref<number | null>(null)
const prefilledFromMatch = ref(false)

const form = reactive({
  job_match_id: null as number | null,
  job_title: '',
  company_name: '',
  job_requirements: '',
})

const canStart = computed(() => form.job_title.replace(/\s/g, '').length >= 2)
const answerLength = computed(() => answerText.value.replace(/\s/g, '').length)
const canSubmit = computed(() => answerLength.value >= 10)
const currentQuestion = computed(() => {
  if (!session.value || session.value.current_question_index >= 5) return null
  return session.value.questions[session.value.current_question_index] ?? null
})
const feedbackQuestion = computed(() => {
  if (!session.value || feedbackQuestionIndex.value === null) return null
  return session.value.questions[feedbackQuestionIndex.value] ?? null
})
const report = computed(() => session.value?.final_feedback ?? null)

const dimensionLabels: Record<keyof DimensionScores, string> = {
  relevance: 'Answer relevance',
  specificity: 'Level of detail',
  structure: 'Answer structure',
  communication: 'Clarity of expression',
}

const reportDimensionLabels: Record<keyof FinalReport['dimension_scores'], string> = {
  expression: 'Communication skills',
  role_understanding: 'Job understanding',
  experience_evidence: 'Experience evidence',
  answer_structure: 'Answer structure',
}

const resetMessages = () => {
  errorMessage.value = ''
  successMessage.value = ''
}

const resetForm = () => {
  form.job_match_id = null
  form.job_title = ''
  form.company_name = ''
  form.job_requirements = ''
  prefilledFromMatch.value = false
}

const applyJobMatch = (jobMatch: JobMatch) => {
  form.job_match_id = jobMatch.id
  form.job_title = jobMatch.job_title
  form.company_name = jobMatch.company_name ?? ''
  form.job_requirements = jobMatch.job_description
  prefilledFromMatch.value = true
}

const setScreenFromSession = (value: InterviewSession) => {
  if (value.status === 'completed') screen.value = 'report'
  else if (value.status === 'reporting') screen.value = 'reporting'
  else screen.value = 'answer'
}

const loadPage = async () => {
  loading.value = true
  resetMessages()
  try {
    const [resumeResponse, sessionResponse] = await Promise.all([
      api.get<ResumeSummary | null>('/resumes/primary'),
      api.get<InterviewSession | null>('/interviews/current'),
    ])
    resume.value = resumeResponse.data
    session.value = sessionResponse.data

    if (typeof route.query.agentRun === 'string') {
      const { data: task } = await api.get<{ job_title: string; company_name: string; job_description: string; match?: { id: number } }>(`/agent/${route.query.agentRun}`)
      form.job_title = task.job_title
      form.company_name = task.company_name
      form.job_requirements = task.job_description
      form.job_match_id = task.match?.id ?? null
      screen.value = 'prepare'
      return
    }

    const queryId = Number(route.query.jobMatchId)
    if (Number.isInteger(queryId) && queryId > 0) {
      const matchResponse = await api.get<JobMatch | null>('/job-matches/current')
      if (matchResponse.data?.id === queryId) {
        applyJobMatch(matchResponse.data)
        screen.value = 'prepare'
        return
      }
    }
    if (sessionResponse.data) setScreenFromSession(sessionResponse.data)
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Failed to load the AI interview page')
  } finally {
    loading.value = false
  }
}

const startInterview = async () => {
  resetMessages()
  if (!canStart.value) {
    errorMessage.value = 'Please enter the job title'
    return
  }
  generating.value = true
  try {
    const response = await api.post<InterviewSession>('/interviews', {
      job_match_id: form.job_match_id,
      job_title: form.job_title,
      company_name: form.company_name || null,
      job_requirements: form.job_requirements || null,
    }, { timeout: 90_000 })
    session.value = response.data
    answerText.value = ''
    feedbackQuestionIndex.value = null
    screen.value = 'answer'
    successMessage.value = '5 interview questions for the role have been generated.'
    void router.replace({ path: '/agent/interview' })
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'AI cannot generate interview questions right now. Please try again later.')
  } finally {
    generating.value = false
  }
}

const submitAnswer = async () => {
  if (!session.value || !currentQuestion.value) return
  resetMessages()
  if (!canSubmit.value) {
    errorMessage.value = 'The answer must contain at least 10 valid characters'
    return
  }
  submitting.value = true
  const answeredIndex = session.value.current_question_index
  try {
    const response = await api.post<InterviewSession>(`/interviews/${session.value.id}/answers`, {
      question_id: currentQuestion.value.id,
      answer_text: answerText.value,
    }, { timeout: 120_000 })
    session.value = response.data
    answerText.value = ''
    if (response.data.status === 'completed') {
      screen.value = 'report'
      successMessage.value = 'All five questions completed, summary report generated.'
    } else {
      feedbackQuestionIndex.value = answeredIndex
      screen.value = 'feedback'
    }
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'The AI cannot review this answer at the moment, please try again later')
    try {
      const refreshed = await api.get<InterviewSession>(`/interviews/${session.value.id}`)
      session.value = refreshed.data
      if (refreshed.data.status === 'reporting') screen.value = 'reporting'
    } catch {
      // 保留原错误，用户可以刷新后恢复会话。
    }
  } finally {
    submitting.value = false
  }
}

const continueInterview = () => {
  feedbackQuestionIndex.value = null
  answerText.value = ''
  resetMessages()
  screen.value = 'answer'
}

const retryReport = async () => {
  if (!session.value) return
  resetMessages()
  retryingReport.value = true
  try {
    const response = await api.post<InterviewSession>(`/interviews/${session.value.id}/report`, undefined, { timeout: 90_000 })
    session.value = response.data
    screen.value = 'report'
    successMessage.value = 'The overall report has been generated.'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Failed to generate the overall report. Please try again later')
  } finally {
    retryingReport.value = false
  }
}

const abandonInterview = async () => {
  if (!session.value || !window.confirm(t('End this interview? Submitted answers will be kept, but no overall report will be generated.'))) return
  resetMessages()
  abandoning.value = true
  try {
    await api.post(`/interviews/${session.value.id}/abandon`)
    session.value = null
    resetForm()
    screen.value = 'prepare'
    successMessage.value = 'This interview has ended. You can choose a job again.'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Failed to end interview')
  } finally {
    abandoning.value = false
  }
}

const startNewInterview = () => {
  resetMessages()
  resetForm()
  screen.value = 'prepare'
  void router.replace({ path: '/app/interview' })
}

onMounted(loadPage)
</script>

<template>
  <section class="interview-page">
    <div class="module-intro interview-intro">
      <div><span class="eyebrow">{{ t("AI INTERVIEW") }}</span><h2>{{ t("AI Mock Interview") }}</h2><p>{{ t("First confirm the target role for this session, then complete 5 written questions. Each question has its own feedback, and a comprehensive report is generated once all are completed.") }}</p></div>
      <button v-if="session && screen === 'report'" class="save-button" type="button" @click="startNewInterview">{{ t("Start a new interview") }}</button>
    </div>

    <div v-if="loading" class="profile-loading">{{ t("Loading mock interview…") }}</div>
    <template v-else>
      <div v-if="!resume" class="diagnosis-empty-card">
        <span>01</span><h3>{{ t("No main CV yet") }}</h3><p>{{ t("The AI generates role-related questions based on the main CV. Please upload a real CV first.") }}</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">{{ t("Go to upload CV") }}</RouterLink>
      </div>
      <div v-else-if="!resume.confirmed_at" class="diagnosis-empty-card">
        <span>02</span><h3>{{ t("Main CV text not yet confirmed") }}</h3><p>{{ t("Please check the parsed text before starting the mock interview.") }}</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">{{ t("Go to confirm text") }}</RouterLink>
      </div>

      <template v-else>
        <form v-if="screen === 'prepare'" class="job-match-form-card interview-prepare-card" @submit.prevent="startInterview">
          <div class="job-match-form-heading"><div><span>{{ t("This job") }}</span><h3>{{ t("Prepare 5 targeted interview questions") }}</h3></div><small>{{ t("Estimated 10–20 minutes") }}</small></div>
          <div v-if="prefilledFromMatch" class="interview-prefill-note">{{ t("Information has been carried over from the job match result; you can still edit it before starting.") }}</div>
          <div class="job-basic-grid">
            <label><span>{{ t("Job title") }} <b>*</b></span><input v-model="form.job_title" maxlength="100" :placeholder="t('For example: Front-end Development Engineer')" /></label>
            <label><span>{{ t("Company name") }} <small>{{ t("Optional") }}</small></span><input v-model="form.company_name" maxlength="100" :placeholder="t('For example: XX Technology')" /></label>
          </div>
          <label class="job-jd-field"><span class="field-label">{{ t("Job requirements") }} <small>{{ t("Optional") }}</small></span>
            <textarea v-model="form.job_requirements" maxlength="20000" :placeholder="t('You can paste the job responsibilities and requirements; if left blank, general role questions will be generated based on the job title.')"></textarea>
            <span class="field-count">{{ t(form.job_requirements.length.toLocaleString()) }} {{ t("/ 20,000 characters") }}</span>
          </label>
          <div v-if="!form.job_requirements.trim()" class="interview-specificity-hint">{{ t("Once you enter the job requirements, the professional and situational questions will be closer to real recruitment needs.") }}</div>
          <div class="job-form-footer">
            <div><b>{{ t("Question basis") }}</b><span>{{ t(resume.original_name) }} {{ t("· Master CV version") }} {{ t(resume.content_version) }}</span></div>
            <button class="save-button job-analyze-button" type="submit" :disabled="generating || !canStart">{{ t(generating ? 'Preparing 5 role-specific questions…' : 'Confirm the role and generate interview questions') }}</button>
          </div>
        </form>

        <template v-else-if="session">
          <div v-if="screen === 'answer' || screen === 'feedback'" class="interview-session-bar">
            <div><span>{{ t(session.company_name || 'Target role') }}</span><h3>{{ t(session.job_title) }}</h3><small>{{ t("Based on master CV version") }} {{ t(session.resume_version) }}</small></div>
            <div class="interview-progress">
              <span v-for="index in 5" :key="index" :class="{ completed: index <= session.current_question_index, current: index === session.current_question_index + 1 }"></span>
              <small>{{ t(Math.min(session.current_question_index + (screen === 'feedback' ? 0 : 1), 5)) }} / 5</small>
            </div>
            <button type="button" :disabled="abandoning" @click="abandonInterview">{{ t(abandoning ? 'Ending…' : 'End this interview') }}</button>
          </div>

          <section v-if="screen === 'answer' && currentQuestion" class="interview-question-card">
            <div class="interview-question-meta"><span>{{ t("QUESTION") }} {{ t(String(currentQuestion.sequence_no).padStart(2, '0')) }}</span><b>{{ t(currentQuestion.focus_area) }}</b></div>
            <h3>{{ t(currentQuestion.question_text) }}</h3>
            <label><span>{{ t("Your answer") }}</span><textarea v-model="answerText" maxlength="5000" :placeholder="t('Answer using real situations, your actions and actual results…')"></textarea></label>
            <div class="interview-answer-footer"><small>{{ t(answerLength) }} {{ t("/ 5,000 valid characters") }}</small><button class="save-button" type="button" :disabled="submitting || !canSubmit" @click="submitAnswer">{{ t(submitting ? 'Analysing this answer…' : session.current_question_index === 4 ? 'Submit and generate comprehensive report' : 'Submit answer') }}</button></div>
          </section>

          <section v-else-if="screen === 'feedback' && feedbackQuestion?.feedback" class="interview-feedback-stack">
            <div class="interview-feedback-hero">
              <div class="interview-feedback-score"><span>{{ t("Score for this question") }}</span><strong>{{ t(feedbackQuestion.feedback.score) }}</strong><small>/ 100</small></div>
              <div><span>{{ t("QUESTION") }} {{ t(String(feedbackQuestion.sequence_no).padStart(2, '0')) }} · {{ t(feedbackQuestion.focus_area) }}</span><h3>{{ t("Feedback for this question") }}</h3><p>{{ t(feedbackQuestion.question_text) }}</p></div>
            </div>
            <div class="interview-dimension-grid">
              <article v-for="(score, key) in feedbackQuestion.feedback.dimension_scores" :key="key"><span>{{ t(dimensionLabels[key]) }}</span><strong>{{ t(score) }}</strong><div><i :style="{ width: `${score}%` }"></i></div></article>
            </div>
            <div class="interview-feedback-columns">
              <section class="interview-positive-card"><span>{{ t("STRENGTHS") }}</span><h3>{{ t("Answer strengths") }}</h3><ul><li v-for="item in feedbackQuestion.feedback.strengths" :key="item">{{ t(item) }}</li></ul></section>
              <section class="interview-issue-card"><span>{{ t("ISSUES") }}</span><h3>{{ t("Needs improvement") }}</h3><ul><li v-for="item in feedbackQuestion.feedback.issues" :key="item">{{ t(item) }}</li></ul></section>
            </div>
            <section class="interview-suggestions-card"><div><span>{{ t("NEXT ATTEMPT") }}</span><h3>{{ t("Change it like this next time") }}</h3></div><ol><li v-for="item in feedbackQuestion.feedback.suggestions" :key="item">{{ t(item) }}</li></ol></section>
            <section class="interview-outline-card"><span>{{ t("Answer structure reference") }}</span><div><i v-for="(item, index) in feedbackQuestion.feedback.answer_outline" :key="item"><b>{{ t(index + 1) }}</b>{{ t(item) }}</i></div></section>
            <button class="save-button interview-next-button" type="button" @click="continueInterview">{{ t("Enter the") }} {{ t(session.current_question_index + 1) }} {{ t("question →") }}</button>
          </section>

          <section v-else-if="screen === 'reporting'" class="interview-reporting-card">
            <span>5 / 5</span><h3>{{ t("All five answers saved") }}</h3><p>{{ t("The overall report could not be generated for now. No need to answer again — just retry.") }}</p>
            <button class="save-button" type="button" :disabled="retryingReport" @click="retryReport">{{ t(retryingReport ? 'Generating comprehensive report…' : 'Regenerate the comprehensive report') }}</button>
          </section>

          <section v-else-if="screen === 'report' && report" class="interview-report-stack">
            <div class="interview-report-hero">
              <div class="interview-report-score"><span>{{ t("Overall performance") }}</span><strong>{{ t(report.overall_score) }}</strong><small>/ 100</small></div>
              <div><span>{{ t("INTERVIEW REPORT") }}</span><h3>{{ t(session.job_title) }} {{ t("· Mock interview report") }}</h3><p>{{ t(report.summary) }}</p><small>{{ t("Completed 5 written interview questions") }}</small></div>
            </div>
            <div class="interview-report-dimensions">
              <article v-for="(score, key) in report.dimension_scores" :key="key"><span>{{ t(reportDimensionLabels[key]) }}</span><strong>{{ t(score) }}</strong><div><i :style="{ width: `${score}%` }"></i></div></article>
            </div>
            <div class="interview-report-columns">
              <section><span>{{ t("WHAT WENT WELL") }}</span><h3>{{ t("Performs well") }}</h3><ul><li v-for="item in report.strengths" :key="item">{{ t(item) }}</li></ul></section>
              <section><span>{{ t("PRIORITY IMPROVEMENTS") }}</span><h3>{{ t("Key improvements") }}</h3><ul><li v-for="item in report.improvements" :key="item">{{ t(item) }}</li></ul></section>
            </div>
            <section class="interview-practice-card"><div><span>{{ t("PRACTICE PLAN") }}</span><h3>{{ t("Focus for the next practice session") }}</h3></div><ol><li v-for="(item, index) in report.practice_focus" :key="item"><b>{{ t(String(index + 1).padStart(2, '0')) }}</b>{{ t(item) }}</li></ol></section>
            <div class="interview-report-actions"><RouterLink to="/app">{{ t("Return to workspace") }}</RouterLink><button class="save-button" type="button" @click="startNewInterview">{{ t("Start a new interview") }}</button></div>
            <div class="ai-reference-note">{{ t("The mock interview report is for practice purposes and does not represent a real recruiter's assessment or hiring decision.") }}</div>
          </section>
        </template>

        <div v-if="successMessage" class="form-success custom-page-message" role="status">{{ t(successMessage) }}</div>
        <div v-if="errorMessage" class="form-error diagnosis-error custom-page-message" role="alert">{{ t(errorMessage) }}</div>
      </template>
    </template>
  </section>
</template>
