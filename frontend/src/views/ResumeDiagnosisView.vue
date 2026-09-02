<script setup lang="ts">
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
    { label: '信息完整度', score: scores.information_completeness },
    { label: '内容质量', score: scores.content_quality },
    { label: '成果量化', score: scores.achievement_quantification },
    { label: '表达专业度', score: scores.professional_expression },
    { label: '方向匹配度', score: scores.career_direction_fit },
  ]
})

const formatDate = (value: string) => {
  const utcValue = /(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(utcValue))
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
    errorMessage.value = getApiErrorMessage(error, '诊断页面加载失败')
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
    errorMessage.value = getApiErrorMessage(error, 'AI 诊断失败，请稍后重试')
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
        <span class="eyebrow">AI RESUME DIAGNOSIS</span>
        <h2>AI 简历诊断</h2>
        <p>诊断只基于你确认的主简历和求职档案，不会替你补写不存在的经历。</p>
      </div>
      <RouterLink class="back-text-link" to="/app/resume">← 返回我的简历</RouterLink>
    </div>

    <div v-if="loading" class="profile-loading">正在加载诊断信息…</div>
    <template v-else>
      <div v-if="!resume" class="diagnosis-empty-card">
        <span>01</span><h3>还没有主简历</h3><p>先上传并确认简历文字，才能开始 AI 诊断。</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">去上传简历</RouterLink>
      </div>

      <div v-else-if="!resume.confirmed_at" class="diagnosis-empty-card">
        <span>02</span><h3>简历文字尚未确认</h3><p>请检查解析文字是否准确，确认后 AI 才会使用这些内容。</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">去确认文字</RouterLink>
      </div>

      <div v-else-if="!diagnosis" class="diagnosis-ready-card">
        <div class="diagnosis-ready-visual" aria-hidden="true"><b>AI</b><i></i><i></i><i></i></div>
        <div>
          <span>已准备好</span>
          <h3>分析 {{ resume.original_name }}</h3>
          <p>通常需要几十秒。系统会校验结果完整性，失败时可以直接重试。</p>
          <button class="save-button diagnosis-main-button" type="button" :disabled="generating" @click="generateDiagnosis">
            {{ generating ? 'AI 正在分析，请稍候…' : '开始 AI 诊断' }}
          </button>
        </div>
      </div>

      <template v-else>
        <div class="diagnosis-summary-card">
          <div class="diagnosis-score">
            <span>综合评分</span><strong>{{ diagnosis.overall_score }}</strong><small>/ 100</small>
          </div>
          <div class="diagnosis-summary-main">
            <div class="diagnosis-summary-heading">
              <div><span>诊断完成</span><h3>{{ resume.original_name }}</h3></div>
              <button type="button" :disabled="generating" @click="generateDiagnosis">{{ generating ? '重新分析中…' : '重新诊断' }}</button>
            </div>
            <div class="dimension-grid">
              <div v-for="item in dimensions" :key="item.label" class="dimension-item">
                <div><span>{{ item.label }}</span><b>{{ item.score }}</b></div>
                <i><em :style="{ width: `${item.score}%` }"></em></i>
              </div>
            </div>
            <small>基于主简历内容版本 {{ diagnosis.resume_version }} · {{ formatDate(diagnosis.created_at) }}</small>
          </div>
        </div>

        <div class="diagnosis-columns">
          <article class="diagnosis-list-card strengths-card">
            <div class="card-heading"><div><span>STRENGTHS</span><h3>简历优势</h3></div></div>
            <ol><li v-for="item in diagnosis.strengths" :key="item">{{ item }}</li></ol>
          </article>
          <article class="diagnosis-list-card issues-card">
            <div class="card-heading"><div><span>ISSUES</span><h3>主要问题</h3></div></div>
            <ol><li v-for="item in diagnosis.issues" :key="item">{{ item }}</li></ol>
          </article>
        </div>

        <section class="suggestions-section">
          <div class="section-heading diagnosis-section-heading">
            <div><span class="eyebrow">SUGGESTIONS</span><h2>逐条修改建议</h2></div>
            <small>{{ diagnosis.suggestions.length }} 条建议</small>
          </div>
          <article v-for="(item, index) in diagnosis.suggestions" :key="`${index}-${item.source_text}`" class="suggestion-card">
            <div class="suggestion-index">{{ String(index + 1).padStart(2, '0') }}</div>
            <div class="suggestion-content">
              <div class="suggestion-comparison">
                <div><span>原文</span><p>{{ item.source_text }}</p></div>
                <div><span>建议表达</span><p>{{ item.suggested_text }}</p></div>
              </div>
              <div class="suggestion-reason"><b>修改理由</b><span>{{ item.reason }}</span></div>
            </div>
          </article>
        </section>

        <div class="ai-reference-note">AI 评分和建议仅作为求职准备参考，不代表招聘结果。重要内容请根据你的真实经历再次确认。</div>
      </template>

      <div v-if="errorMessage" class="form-error diagnosis-error" role="alert">{{ errorMessage }}</div>
    </template>
  </section>
</template>
