<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { api } from '@/services/api'

type ServiceState = 'checking' | 'ready' | 'offline'

const serviceState = ref<ServiceState>('checking')
const resumeExists = ref(false)
const readinessScore = ref<number | null>(null)

const readinessLabel = computed(() => {
  if (readinessScore.value !== null) return '最新简历诊断结果'
  return resumeExists.value ? '简历已添加，等待 AI 诊断' : '添加简历后开始分析'
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
        <span class="eyebrow">CAREER WORKSPACE</span>
        <h2>让每一次求职准备<br />都更有方向</h2>
        <p>从一份真实简历出发，完成岗位定制、匹配分析和针对性模拟面试。</p>
        <div class="hero-actions">
          <RouterLink class="primary-button" to="/app/resume">创建我的简历</RouterLink>
          <RouterLink class="secondary-button" to="/app/job-match">了解岗位匹配</RouterLink>
        </div>
      </div>

      <RouterLink class="hero-visual" :to="readinessScore === null ? '/app/resume' : '/app/resume/diagnosis'" :style="readinessStyle" aria-label="查看简历准备度详情">
        <div class="score-orbit score-orbit-large"></div>
        <div class="score-orbit score-orbit-small"></div>
        <div :class="['score-card', { measured: readinessScore !== null }]">
          <span>准备度</span>
          <strong>{{ readinessScore === null ? '—' : readinessScore }}</strong>
          <small>{{ readinessLabel }}</small>
        </div>
      </RouterLink>
    </div>

    <div class="section-heading">
      <div>
        <span class="eyebrow">QUICK START</span>
        <h2>从这里开始</h2>
      </div>
      <button class="service-status" type="button" @click="checkService">
        <span :class="['status-dot', serviceState]"></span>
        <template v-if="serviceState === 'checking'">正在检查基础服务</template>
        <template v-else-if="serviceState === 'ready'">基础服务运行正常</template>
        <template v-else>后端服务尚未启动</template>
      </button>
    </div>

    <div class="feature-grid">
      <RouterLink class="feature-card" to="/app/resume">
        <span class="feature-index">01</span>
        <h3>建立主简历</h3>
        <p>上传 PDF 或 Word，确认系统解析出的教育、项目、实习和技能信息。</p>
        <span class="card-link">进入我的简历 <b>→</b></span>
      </RouterLink>
      <RouterLink class="feature-card" to="/app/custom-resumes">
        <span class="feature-index">02</span>
        <h3>生成定制版本</h3>
        <p>围绕目标岗位重新组织真实经历，得到可以继续编辑和导出的简历。</p>
        <span class="card-link">进入定制简历 <b>→</b></span>
      </RouterLink>
      <RouterLink class="feature-card" to="/app/interview">
        <span class="feature-index">03</span>
        <h3>开始岗位面试</h3>
        <p>指定岗位后回答五道相关问题，逐题获得反馈，最后查看完整报告。</p>
        <span class="card-link">进入 AI 面试 <b>→</b></span>
      </RouterLink>
    </div>
  </section>
</template>
