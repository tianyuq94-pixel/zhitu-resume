<script setup lang="ts">
import { t, locale } from '@/i18n'
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
  if (!value) return 'Not yet confirmed'
  const utcValue = /(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`
  return new Intl.DateTimeFormat(locale.value === 'zh' ? 'zh-CN' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(utcValue))
}

const loadResume = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await api.get<Resume | null>('/resumes/primary')
    resume.value = response.data
    editedText.value = response.data?.parsed_text ?? ''
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Failed to load CV information')
  } finally {
    loading.value = false
  }
}

const chooseFile = () => fileInput.value?.click()

const validateFile = (file: File): string | null => {
  const extension = file.name.toLowerCase().split('.').pop()
  if (!['pdf', 'docx'].includes(extension ?? '')) return 'Only PDF and DOCX files are supported'
  if (file.size > 10 * 1024 * 1024) return 'CV files cannot exceed 10 MB'
  if (file.size === 0) return 'Cannot upload an empty file'
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
    successMessage.value = 'CV uploaded and parsed successfully. Please check the text below'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'CV upload failed. Please try again later')
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
    errorMessage.value = 'CV text must contain at least 30 valid characters'
    return
  }
  saving.value = true
  try {
    const response = await api.put<Resume>('/resumes/primary/text', { parsed_text: editedText.value })
    resume.value = response.data
    editedText.value = response.data.parsed_text
    successMessage.value = 'CV text confirmed and saved'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Failed to save CV text')
  } finally {
    saving.value = false
  }
}

const deleteResume = async () => {
  if (!window.confirm(t('Delete the current main CV? The original file and parsed text will both be deleted.'))) return
  deleting.value = true
  errorMessage.value = ''
  try {
    await api.delete('/resumes/primary')
    resume.value = null
    editedText.value = ''
    successMessage.value = 'Main CV deleted'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Deletion failed, please try again later')
  } finally {
    deleting.value = false
  }
}

onMounted(loadResume)
</script>

<template>
  <section class="resume-page">
    <div class="module-intro resume-intro">
      <span class="eyebrow">{{ t("PRIMARY RESUME") }}</span>
      <h2>{{ t("My CV") }}</h2>
      <p>{{ t("Upload a master CV and the system will first parse it into editable text. All subsequent AI features will only use the content you have confirmed.") }}</p>
    </div>

    <div v-if="loading" class="profile-loading">{{ t("Loading master CV…") }}</div>
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
        <h3>{{ t("Upload your master CV") }}</h3>
        <p>{{ t("Drag a PDF or DOCX file here, or click the button below to choose a file.") }}</p>
        <button class="save-button upload-button" type="button" :disabled="uploading" @click="chooseFile">
          {{ t(uploading ? `Uploading ${uploadProgress}%` : 'Select CV file') }}
        </button>
        <small>{{ t("File up to 10 MB · PDF must have a normal text layer · Legacy DOC is not currently supported") }}</small>
      </div>

      <template v-else>
        <div class="resume-file-card">
          <div class="resume-file-type">{{ t(resume.mime_type === 'application/pdf' ? 'PDF' : 'DOCX') }}</div>
          <div class="resume-file-main">
            <span>{{ t("Current master CV") }}</span>
            <h3>{{ t(resume.original_name) }}</h3>
            <div class="resume-file-meta">
              <b>{{ t("Parsing complete") }}</b><span>{{ t(formatBytes(resume.size_bytes)) }}</span><span>{{ t("Content version") }} {{ t(resume.content_version) }}</span><span>{{ t(formatDate(resume.confirmed_at)) }}</span>
            </div>
          </div>
          <div class="resume-file-actions">
            <a href="/api/v1/resumes/primary/file" target="_blank" rel="noopener">{{ t("View original file") }}</a>
            <button type="button" :disabled="uploading" @click="chooseFile">{{ t(uploading ? `Replacing ${uploadProgress}%` : 'Replace file') }}</button>
            <button class="danger-text-button" type="button" :disabled="deleting" @click="deleteResume">{{ t(deleting ? 'Deleting' : 'Delete') }}</button>
          </div>
        </div>

        <div class="resume-editor-card">
          <div class="card-heading resume-editor-heading">
            <div><span>{{ t("PARSED TEXT") }}</span><h3>{{ t("Check CV text") }}</h3></div>
            <small>{{ t(effectiveCharacters.toLocaleString()) }} {{ t("valid characters") }}</small>
          </div>
          <div class="resume-editor-note">{{ t("Please check whether your name, dates, projects and skills have been parsed correctly. The text saved here will be the sole source of truth for subsequent AI analysis.") }}</div>
          <textarea v-model="editedText" maxlength="200000" spellcheck="false" :aria-label="t('CV parsed text')"></textarea>
          <div class="resume-editor-footer">
            <span v-if="hasChanges">{{ t("There are unsaved changes") }}</span><span v-else>{{ t("Current content is synced") }}</span>
            <button class="save-button" type="button" :disabled="saving || (!hasChanges && !!resume.confirmed_at)" @click="saveText">
              {{ t(saving ? 'Saving…' : resume.confirmed_at ? 'Save changes' : 'Confirm and save text') }}
            </button>
          </div>
        </div>

        <div class="resume-diagnosis-entry">
          <div>
            <span>{{ t("AI DIAGNOSIS") }}</span>
            <h3>{{ t("Have AI check this CV") }}</h3>
            <p>{{ t("Generate a diagnostic report across five dimensions: completeness, content quality, quantified results, professional expression and career direction.") }}</p>
          </div>
          <RouterLink v-if="resume.confirmed_at" class="save-button diagnosis-entry-button" to="/app/resume/diagnosis">{{ t("Go to AI diagnosis") }}</RouterLink>
          <button v-else class="save-button diagnosis-entry-button" type="button" disabled>{{ t("Please confirm the CV text first") }}</button>
        </div>
      </template>

      <div v-if="errorMessage" class="form-error" role="alert">{{ t(errorMessage) }}</div>
      <div v-if="successMessage" class="form-success" role="status">{{ t(successMessage) }}</div>

      <div class="resume-privacy-note">
        <b>{{ t("File processing notes") }}</b>
        <p>{{ t("The original file is stored in a private directory on the site and will not be publicly accessible; only the currently logged-in account can read or delete it. Text recognition is not currently supported for scanned PDFs or image CVs.") }}</p>
      </div>
    </template>
  </section>
</template>
