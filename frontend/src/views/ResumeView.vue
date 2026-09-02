<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { api, getApiErrorMessage } from '@/services/api'

type Resume = {
  id: number
  original_name: string
  mime_type: string
  size_bytes: number
  parsed_text: string
  parse_status: string
  content_version: number
  confirmed_at: string | null
  created_at: string
  updated_at: string
}

const fileInput = ref<HTMLInputElement | null>(null)
const resume = ref<Resume | null>(null)
const editedText = ref('')
const loading = ref(true)
const uploading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const dropActive = ref(false)
const uploadProgress = ref(0)
const errorMessage = ref('')
const successMessage = ref('')

const hasChanges = computed(() => resume.value !== null && editedText.value !== resume.value.parsed_text)
const effectiveCharacters = computed(() => editedText.value.replace(/\s/g, '').length)

const formatBytes = (bytes: number) => {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

const formatDate = (value: string | null) => {
  if (!value) return '尚未确认'
  const utcValue = /(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(utcValue))
}

const loadResume = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await api.get<Resume | null>('/resumes/primary')
    resume.value = response.data
    editedText.value = response.data?.parsed_text ?? ''
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '简历信息加载失败')
  } finally {
    loading.value = false
  }
}

const chooseFile = () => fileInput.value?.click()

const validateFile = (file: File): string | null => {
  const extension = file.name.toLowerCase().split('.').pop()
  if (!['pdf', 'docx'].includes(extension ?? '')) return '只支持 PDF 和 DOCX 文件'
  if (file.size > 10 * 1024 * 1024) return '简历文件不能超过 10 MB'
  if (file.size === 0) return '不能上传空文件'
  return null
}

const uploadFile = async (file: File) => {
  const validationError = validateFile(file)
  if (validationError) {
    errorMessage.value = validationError
    return
  }
  uploading.value = true
  uploadProgress.value = 0
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const body = new FormData()
    body.append('file', file)
    const response = await api.post<Resume>('/resumes/primary', body, {
      timeout: 60_000,
      onUploadProgress: (event) => {
        if (event.total) uploadProgress.value = Math.round((event.loaded / event.total) * 100)
      },
    })
    resume.value = response.data
    editedText.value = response.data.parsed_text
    successMessage.value = '简历上传并解析成功，请检查下方文字'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '简历上传失败，请稍后重试')
  } finally {
    uploading.value = false
    uploadProgress.value = 0
    if (fileInput.value) fileInput.value.value = ''
  }
}

const onFileSelected = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) void uploadFile(file)
}

const onDrop = (event: DragEvent) => {
  dropActive.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) void uploadFile(file)
}

const saveText = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  if (effectiveCharacters.value < 30) {
    errorMessage.value = '简历文字不能少于 30 个有效字符'
    return
  }
  saving.value = true
  try {
    const response = await api.put<Resume>('/resumes/primary/text', { parsed_text: editedText.value })
    resume.value = response.data
    editedText.value = response.data.parsed_text
    successMessage.value = '简历文字已确认并保存'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '简历文字保存失败')
  } finally {
    saving.value = false
  }
}

const deleteResume = async () => {
  if (!window.confirm('确定删除当前主简历吗？原文件和解析文字都会被删除。')) return
  deleting.value = true
  errorMessage.value = ''
  try {
    await api.delete('/resumes/primary')
    resume.value = null
    editedText.value = ''
    successMessage.value = '主简历已删除'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '删除失败，请稍后重试')
  } finally {
    deleting.value = false
  }
}

onMounted(loadResume)
</script>

<template>
  <section class="resume-page">
    <div class="module-intro resume-intro">
      <span class="eyebrow">PRIMARY RESUME</span>
      <h2>我的简历</h2>
      <p>上传一份主简历，系统会先解析成可编辑文字。后续所有 AI 功能只使用你确认后的内容。</p>
    </div>

    <div v-if="loading" class="profile-loading">正在加载主简历…</div>
    <template v-else>
      <input ref="fileInput" class="visually-hidden" type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" @change="onFileSelected" />

      <div
        v-if="!resume"
        :class="['resume-upload-zone', { active: dropActive }]"
        @dragenter.prevent="dropActive = true"
        @dragover.prevent="dropActive = true"
        @dragleave.prevent="dropActive = false"
        @drop.prevent="onDrop"
      >
        <div class="upload-icon" aria-hidden="true">↑</div>
        <h3>上传你的主简历</h3>
        <p>将 PDF 或 DOCX 文件拖到这里，或点击下方按钮选择文件。</p>
        <button class="save-button upload-button" type="button" :disabled="uploading" @click="chooseFile">
          {{ uploading ? `正在上传 ${uploadProgress}%` : '选择简历文件' }}
        </button>
        <small>文件不超过 10 MB · PDF 需要具有正常文字层 · 暂不支持旧版 DOC</small>
      </div>

      <template v-else>
        <div class="resume-file-card">
          <div class="resume-file-type">{{ resume.mime_type === 'application/pdf' ? 'PDF' : 'DOCX' }}</div>
          <div class="resume-file-main">
            <span>当前主简历</span>
            <h3>{{ resume.original_name }}</h3>
            <div class="resume-file-meta">
              <b>解析完成</b><span>{{ formatBytes(resume.size_bytes) }}</span><span>内容版本 {{ resume.content_version }}</span><span>{{ formatDate(resume.confirmed_at) }}</span>
            </div>
          </div>
          <div class="resume-file-actions">
            <a href="/api/v1/resumes/primary/file" target="_blank" rel="noopener">查看原文件</a>
            <button type="button" :disabled="uploading" @click="chooseFile">{{ uploading ? `替换中 ${uploadProgress}%` : '替换文件' }}</button>
            <button class="danger-text-button" type="button" :disabled="deleting" @click="deleteResume">{{ deleting ? '删除中' : '删除' }}</button>
          </div>
        </div>

        <div class="resume-editor-card">
          <div class="card-heading resume-editor-heading">
            <div><span>PARSED TEXT</span><h3>检查简历文字</h3></div>
            <small>{{ effectiveCharacters.toLocaleString() }} 个有效字符</small>
          </div>
          <div class="resume-editor-note">请检查姓名、时间、项目和技能是否解析正确。这里保存的文字将作为后续 AI 分析的唯一事实来源。</div>
          <textarea v-model="editedText" maxlength="200000" spellcheck="false" aria-label="简历解析文字"></textarea>
          <div class="resume-editor-footer">
            <span v-if="hasChanges">内容有未保存的修改</span><span v-else>当前内容已同步</span>
            <button class="save-button" type="button" :disabled="saving || (!hasChanges && !!resume.confirmed_at)" @click="saveText">
              {{ saving ? '保存中…' : resume.confirmed_at ? '保存修改' : '确认并保存文字' }}
            </button>
          </div>
        </div>

        <div class="resume-diagnosis-entry">
          <div>
            <span>AI DIAGNOSIS</span>
            <h3>让 AI 检查这份简历</h3>
            <p>从完整度、内容质量、成果量化、专业表达和求职方向五个维度生成诊断报告。</p>
          </div>
          <RouterLink v-if="resume.confirmed_at" class="save-button diagnosis-entry-button" to="/app/resume/diagnosis">进入 AI 诊断</RouterLink>
          <button v-else class="save-button diagnosis-entry-button" type="button" disabled>请先确认简历文字</button>
        </div>
      </template>

      <div v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</div>
      <div v-if="successMessage" class="form-success" role="status">{{ successMessage }}</div>

      <div class="resume-privacy-note">
        <b>文件处理说明</b>
        <p>原文件保存在网站私有目录，不会公开访问；只有当前登录账户可以读取或删除。扫描版 PDF 和图片简历暂不支持文字识别。</p>
      </div>
    </template>
  </section>
</template>
