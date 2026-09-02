<script setup lang="ts">
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
  return { recommend: '推荐投递', consider: '可以尝试', low: '暂不推荐' }[result.value.verdict]
})

const formatDate = (value: string) => {
  const utcValue = /(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(utcValue))
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
    errorMessage.value = getApiErrorMessage(error, '岗位匹配页面加载失败')
  } finally {
    loading.value = false
  }
}

const analyzeJob = async () => {
  errorMessage.value = ''
  if (!canAnalyze.value) {
    errorMessage.value = '请填写岗位名称，并输入不少于 30 个有效字符的岗位 JD'
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
    errorMessage.value = getApiErrorMessage(error, 'AI 岗位匹配失败，请稍后重试')
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
      <span class="eyebrow">JOB MATCHING</span>
      <h2>岗位匹配</h2>
      <p>把目标岗位 JD 与已确认的主简历逐项对照，判断哪些要求已有证据、哪些尚未在简历中体现。</p>
    </div>

    <div v-if="loading" class="profile-loading">正在加载岗位匹配信息…</div>
    <template v-else>
      <div v-if="!resume" class="diagnosis-empty-card">
        <span>01</span><h3>还没有主简历</h3><p>岗位匹配必须基于一份真实主简历。</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">去上传简历</RouterLink>
      </div>

      <div v-else-if="!resume.confirmed_at" class="diagnosis-empty-card">
        <span>02</span><h3>主简历文字尚未确认</h3><p>请先检查解析文字，避免 AI 使用错误内容进行匹配。</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">去确认文字</RouterLink>
      </div>

      <template v-else>
        <form v-if="showForm || !result" class="job-match-form-card" @submit.prevent="analyzeJob">
          <div class="job-match-form-heading">
            <div><span>岗位信息</span><h3>{{ result ? '分析新的目标岗位' : '这个岗位适合我吗？' }}</h3></div>
            <button v-if="result" type="button" @click="showForm = false">取消</button>
          </div>

          <div class="job-basic-grid">
            <label><span>岗位名称 <b>*</b></span>
              <input v-model="form.job_title" maxlength="100" placeholder="例如：前端开发工程师" />
            </label>
            <label><span>公司名称 <small>选填</small></span>
              <input v-model="form.company_name" maxlength="100" placeholder="例如：某某科技" />
            </label>
          </div>

          <label class="job-jd-field"><span class="field-label">岗位 JD <b>*</b></span>
            <textarea v-model="form.job_description" maxlength="20000" placeholder="粘贴岗位职责、任职要求和加分项…"></textarea>
            <span class="field-count">{{ effectiveJdLength.toLocaleString() }} / 20,000 个有效字符</span>
          </label>

          <div class="job-form-footer">
            <div><b>当前主简历</b><span>{{ resume.original_name }} · 内容版本 {{ resume.content_version }}</span></div>
            <button class="save-button job-analyze-button" type="submit" :disabled="analyzing || !canAnalyze">
              {{ analyzing ? '正在逐项分析岗位匹配…' : '开始 AI 匹配' }}
            </button>
          </div>
        </form>

        <template v-if="result && !showForm">
          <div class="job-match-summary">
            <div :class="['job-match-score', `verdict-${result.verdict}`]">
              <span>岗位匹配度</span><strong>{{ result.match_score }}</strong><small>/ 100</small>
            </div>
            <div class="job-match-summary-main">
              <div class="job-summary-topline">
                <div><span>{{ result.company_name || '目标岗位' }}</span><h3>{{ result.job_title }}</h3></div>
                <button type="button" @click="startNewAnalysis">分析新岗位</button>
              </div>
              <div :class="['verdict-badge', `verdict-${result.verdict}`]">{{ verdictText }}</div>
              <p>{{ result.verdict_reason }}</p>
              <small>基于主简历内容版本 {{ result.resume_version }} · {{ formatDate(result.created_at) }}</small>
            </div>
          </div>

          <section class="job-requirements-section">
            <div class="section-heading job-section-heading">
              <div><span class="eyebrow">KEY REQUIREMENTS</span><h2>岗位核心要求</h2></div>
              <small>{{ result.key_requirements.length }} 项</small>
            </div>
            <div class="requirement-grid">
              <article v-for="(item, index) in result.key_requirements" :key="item.requirement">
                <span>{{ String(index + 1).padStart(2, '0') }}</span><h3>{{ item.requirement }}</h3>
                <blockquote>{{ item.jd_evidence }}</blockquote>
              </article>
            </div>
          </section>

          <div class="job-evidence-columns">
            <section class="job-evidence-card matched-card">
              <div class="card-heading"><div><span>MATCHED</span><h3>已匹配能力</h3></div><small>{{ result.matched_items.length }} 项</small></div>
              <div v-if="result.matched_items.length" class="evidence-list">
                <article v-for="item in result.matched_items" :key="item.requirement">
                  <h4>{{ item.requirement }}</h4><p>{{ item.resume_evidence }}</p><small>来自主简历原文</small>
                </article>
              </div>
              <p v-else class="empty-evidence">当前简历中暂未找到直接匹配证据。</p>
            </section>

            <section class="job-evidence-card missing-card">
              <div class="card-heading"><div><span>NOT SHOWN</span><h3>简历未体现</h3></div><small>{{ result.missing_items.length }} 项</small></div>
              <div v-if="result.missing_items.length" class="evidence-list">
                <article v-for="item in result.missing_items" :key="item.requirement">
                  <h4>{{ item.requirement }}</h4><p>{{ item.explanation }}</p><small>不代表你一定不具备</small>
                </article>
              </div>
              <p v-else class="empty-evidence">岗位核心要求均能在简历中找到对应证据。</p>
            </section>
          </div>

          <section class="job-improvements-card">
            <div><span>BEFORE APPLYING</span><h3>投递前改进方向</h3></div>
            <ol><li v-for="item in result.improvements" :key="item">{{ item }}</li></ol>
          </section>

          <div class="job-next-actions">
            <div><b>继续准备这个岗位</b><span>岗位信息会在下一功能中自动带入。</span></div>
            <RouterLink :to="{ path: '/app/custom-resumes', query: { jobMatchId: result.id } }">生成岗位定制简历</RouterLink>
            <RouterLink :to="{ path: '/app/interview', query: { jobMatchId: result.id } }">开始岗位模拟面试</RouterLink>
          </div>

          <div class="ai-reference-note">匹配结果仅基于当前简历呈现的信息，属于求职准备参考，不代表招聘方的实际筛选结论。</div>
        </template>

        <div v-if="errorMessage" class="form-error diagnosis-error" role="alert">{{ errorMessage }}</div>
      </template>
    </template>
  </section>
</template>
