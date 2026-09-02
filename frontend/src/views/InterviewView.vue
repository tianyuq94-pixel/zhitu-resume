<script setup lang="ts">
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
  relevance: '回答相关性',
  specificity: '具体程度',
  structure: '回答结构',
  communication: '表达清晰度',
}

const reportDimensionLabels: Record<keyof FinalReport['dimension_scores'], string> = {
  expression: '表达能力',
  role_understanding: '岗位理解',
  experience_evidence: '经历证明',
  answer_structure: '回答结构',
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
    errorMessage.value = getApiErrorMessage(error, 'AI 面试页面加载失败')
  } finally {
    loading.value = false
  }
}

const startInterview = async () => {
  resetMessages()
  if (!canStart.value) {
    errorMessage.value = '请填写岗位名称'
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
    successMessage.value = '5 道岗位面试题已生成。'
    void router.replace({ path: '/app/interview' })
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'AI 暂时无法生成面试题，请稍后重试')
  } finally {
    generating.value = false
  }
}

const submitAnswer = async () => {
  if (!session.value || !currentQuestion.value) return
  resetMessages()
  if (!canSubmit.value) {
    errorMessage.value = '回答不能少于 10 个有效字符'
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
      successMessage.value = '五道题已完成，综合报告已生成。'
    } else {
      feedbackQuestionIndex.value = answeredIndex
      screen.value = 'feedback'
    }
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'AI 暂时无法点评这次回答，请稍后重试')
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
    successMessage.value = '综合报告已生成。'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '综合报告生成失败，请稍后重试')
  } finally {
    retryingReport.value = false
  }
}

const abandonInterview = async () => {
  if (!session.value || !window.confirm('确定结束本次面试吗？已经提交的回答会保留，但不会生成综合报告。')) return
  resetMessages()
  abandoning.value = true
  try {
    await api.post(`/interviews/${session.value.id}/abandon`)
    session.value = null
    resetForm()
    screen.value = 'prepare'
    successMessage.value = '本次面试已结束，可以重新选择岗位。'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '结束面试失败')
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
      <div><span class="eyebrow">AI INTERVIEW</span><h2>AI 模拟面试</h2><p>先确定本次目标岗位，再完成 5 道文字题。每题都有独立点评，全部完成后生成综合报告。</p></div>
      <button v-if="session && screen === 'report'" class="save-button" type="button" @click="startNewInterview">开始新的面试</button>
    </div>

    <div v-if="loading" class="profile-loading">正在加载模拟面试…</div>
    <template v-else>
      <div v-if="!resume" class="diagnosis-empty-card">
        <span>01</span><h3>还没有主简历</h3><p>AI 会结合主简历生成岗位相关问题，请先上传一份真实简历。</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">去上传简历</RouterLink>
      </div>
      <div v-else-if="!resume.confirmed_at" class="diagnosis-empty-card">
        <span>02</span><h3>主简历文字尚未确认</h3><p>请先检查解析文字，再开始模拟面试。</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">去确认文字</RouterLink>
      </div>

      <template v-else>
        <form v-if="screen === 'prepare'" class="job-match-form-card interview-prepare-card" @submit.prevent="startInterview">
          <div class="job-match-form-heading"><div><span>本次岗位</span><h3>准备 5 道针对性面试题</h3></div><small>预计 10–20 分钟</small></div>
          <div v-if="prefilledFromMatch" class="interview-prefill-note">已从岗位匹配结果带入信息，你仍可以在开始前修改。</div>
          <div class="job-basic-grid">
            <label><span>岗位名称 <b>*</b></span><input v-model="form.job_title" maxlength="100" placeholder="例如：前端开发工程师" /></label>
            <label><span>公司名称 <small>选填</small></span><input v-model="form.company_name" maxlength="100" placeholder="例如：某某科技" /></label>
          </div>
          <label class="job-jd-field"><span class="field-label">岗位要求 <small>选填</small></span>
            <textarea v-model="form.job_requirements" maxlength="20000" placeholder="可以粘贴岗位职责和任职要求；不填写时会根据岗位名称生成通用岗位题。"></textarea>
            <span class="field-count">{{ form.job_requirements.length.toLocaleString() }} / 20,000 字符</span>
          </label>
          <div v-if="!form.job_requirements.trim()" class="interview-specificity-hint">填写岗位要求后，专业题和情境题会更贴近实际招聘需求。</div>
          <div class="job-form-footer">
            <div><b>题目依据</b><span>{{ resume.original_name }} · 主简历版本 {{ resume.content_version }}</span></div>
            <button class="save-button job-analyze-button" type="submit" :disabled="generating || !canStart">{{ generating ? '正在准备 5 道岗位题目…' : '确认岗位并生成面试题' }}</button>
          </div>
        </form>

        <template v-else-if="session">
          <div v-if="screen === 'answer' || screen === 'feedback'" class="interview-session-bar">
            <div><span>{{ session.company_name || '目标岗位' }}</span><h3>{{ session.job_title }}</h3><small>基于主简历版本 {{ session.resume_version }}</small></div>
            <div class="interview-progress">
              <span v-for="index in 5" :key="index" :class="{ completed: index <= session.current_question_index, current: index === session.current_question_index + 1 }"></span>
              <small>{{ Math.min(session.current_question_index + (screen === 'feedback' ? 0 : 1), 5) }} / 5</small>
            </div>
            <button type="button" :disabled="abandoning" @click="abandonInterview">{{ abandoning ? '结束中…' : '结束本次面试' }}</button>
          </div>

          <section v-if="screen === 'answer' && currentQuestion" class="interview-question-card">
            <div class="interview-question-meta"><span>QUESTION {{ String(currentQuestion.sequence_no).padStart(2, '0') }}</span><b>{{ currentQuestion.focus_area }}</b></div>
            <h3>{{ currentQuestion.question_text }}</h3>
            <label><span>你的回答</span><textarea v-model="answerText" maxlength="5000" placeholder="建议用真实情境、你的行动和实际结果来回答…"></textarea></label>
            <div class="interview-answer-footer"><small>{{ answerLength }} / 5,000 个有效字符</small><button class="save-button" type="button" :disabled="submitting || !canSubmit" @click="submitAnswer">{{ submitting ? '正在分析这次回答…' : session.current_question_index === 4 ? '提交并生成综合报告' : '提交回答' }}</button></div>
          </section>

          <section v-else-if="screen === 'feedback' && feedbackQuestion?.feedback" class="interview-feedback-stack">
            <div class="interview-feedback-hero">
              <div class="interview-feedback-score"><span>本题得分</span><strong>{{ feedbackQuestion.feedback.score }}</strong><small>/ 100</small></div>
              <div><span>QUESTION {{ String(feedbackQuestion.sequence_no).padStart(2, '0') }} · {{ feedbackQuestion.focus_area }}</span><h3>本题点评</h3><p>{{ feedbackQuestion.question_text }}</p></div>
            </div>
            <div class="interview-dimension-grid">
              <article v-for="(score, key) in feedbackQuestion.feedback.dimension_scores" :key="key"><span>{{ dimensionLabels[key] }}</span><strong>{{ score }}</strong><div><i :style="{ width: `${score}%` }"></i></div></article>
            </div>
            <div class="interview-feedback-columns">
              <section class="interview-positive-card"><span>STRENGTHS</span><h3>回答优点</h3><ul><li v-for="item in feedbackQuestion.feedback.strengths" :key="item">{{ item }}</li></ul></section>
              <section class="interview-issue-card"><span>ISSUES</span><h3>需要改进</h3><ul><li v-for="item in feedbackQuestion.feedback.issues" :key="item">{{ item }}</li></ul></section>
            </div>
            <section class="interview-suggestions-card"><div><span>NEXT ATTEMPT</span><h3>下次这样改</h3></div><ol><li v-for="item in feedbackQuestion.feedback.suggestions" :key="item">{{ item }}</li></ol></section>
            <section class="interview-outline-card"><span>回答结构参考</span><div><i v-for="(item, index) in feedbackQuestion.feedback.answer_outline" :key="item"><b>{{ index + 1 }}</b>{{ item }}</i></div></section>
            <button class="save-button interview-next-button" type="button" @click="continueInterview">进入第 {{ session.current_question_index + 1 }} 题 →</button>
          </section>

          <section v-else-if="screen === 'reporting'" class="interview-reporting-card">
            <span>5 / 5</span><h3>五道回答已经全部保存</h3><p>综合报告暂时没有生成成功。无需重新答题，直接重试即可。</p>
            <button class="save-button" type="button" :disabled="retryingReport" @click="retryReport">{{ retryingReport ? '正在生成综合报告…' : '重新生成综合报告' }}</button>
          </section>

          <section v-else-if="screen === 'report' && report" class="interview-report-stack">
            <div class="interview-report-hero">
              <div class="interview-report-score"><span>综合表现</span><strong>{{ report.overall_score }}</strong><small>/ 100</small></div>
              <div><span>INTERVIEW REPORT</span><h3>{{ session.job_title }} · 模拟面试报告</h3><p>{{ report.summary }}</p><small>已完成 5 道文字面试题</small></div>
            </div>
            <div class="interview-report-dimensions">
              <article v-for="(score, key) in report.dimension_scores" :key="key"><span>{{ reportDimensionLabels[key] }}</span><strong>{{ score }}</strong><div><i :style="{ width: `${score}%` }"></i></div></article>
            </div>
            <div class="interview-report-columns">
              <section><span>WHAT WENT WELL</span><h3>表现较好</h3><ul><li v-for="item in report.strengths" :key="item">{{ item }}</li></ul></section>
              <section><span>PRIORITY IMPROVEMENTS</span><h3>重点改进</h3><ul><li v-for="item in report.improvements" :key="item">{{ item }}</li></ul></section>
            </div>
            <section class="interview-practice-card"><div><span>PRACTICE PLAN</span><h3>下一步练习重点</h3></div><ol><li v-for="(item, index) in report.practice_focus" :key="item"><b>{{ String(index + 1).padStart(2, '0') }}</b>{{ item }}</li></ol></section>
            <div class="interview-report-actions"><RouterLink to="/app">返回工作台</RouterLink><button class="save-button" type="button" @click="startNewInterview">重新开始一次面试</button></div>
            <div class="ai-reference-note">模拟面试报告用于辅助练习，不代表真实招聘方的评价或录用结论。</div>
          </section>
        </template>

        <div v-if="successMessage" class="form-success custom-page-message" role="status">{{ successMessage }}</div>
        <div v-if="errorMessage" class="form-error diagnosis-error custom-page-message" role="alert">{{ errorMessage }}</div>
      </template>
    </template>
  </section>
</template>
