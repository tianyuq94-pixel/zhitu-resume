<script setup lang="ts">
import { t, locale } from '@/i18n'
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

type Decision = 'pending' | 'accepted' | 'rejected' | 'custom'
type CustomItem = {
  source_kind: 'resume' | 'supplement'
  has_suggestion: boolean
  item_type: 'heading' | 'bullet'
  source_text: string
  suggested_text: string
  reason: string
  decision: Decision
  final_text: string
}
type CustomSection = { title: string; items: CustomItem[] }
type ResumeHeader = {
  name: string
  political_status: string
  phone: string
  email: string
  location: string
  birth_date: string
  has_photo: boolean
}

type CustomResumeSummary = {
  id: number
  source_resume_version: number
  job_match_id: number | null
  job_title: string
  company_name: string | null
  status: 'draft' | 'ready'
  pending_count: number
  created_at: string
  updated_at: string
}

type CustomResume = CustomResumeSummary & {
  job_description: string
  template_name: 'CV template'
  header: ResumeHeader
  sections: CustomSection[]
  missing_information_warnings: string[]
}

const route = useRoute()
const router = useRouter()
const resume = ref<ResumeSummary | null>(null)
const versions = ref<CustomResumeSummary[]>([])
const current = ref<CustomResume | null>(null)
const pageMode = ref<'list' | 'create' | 'editor'>('list')
const loading = ref(true)
const generating = ref(false)
const saving = ref(false)
const exporting = ref(false)
const exportingWord = ref(false)
const deletingId = ref<number | null>(null)
const photoBusy = ref(false)
const photoVersion = ref(0)
const photoInput = ref<HTMLInputElement | null>(null)
const errorMessage = ref('')
const successMessage = ref('')
const prefilledFromMatch = ref(false)

const form = reactive({
  job_match_id: null as number | null,
  job_title: '',
  company_name: '',
  job_description: '',
})

const effectiveJdLength = computed(() => form.job_description.replace(/\s/g, '').length)
const canGenerate = computed(() => form.job_title.trim().length >= 2 && effectiveJdLength.value >= 30)
const pendingCount = computed(() => current.value?.sections.reduce(
  (total, section) => total + section.items.filter((item) => item.decision === 'pending').length,
  0,
) ?? 0)
const totalItems = computed(() => current.value?.sections.reduce((total, section) => total + section.items.filter(item => item.has_suggestion).length, 0) ?? 0)
const headerComplete = computed(() => Boolean(current.value?.header.name.trim()))
const photoUrl = computed(() => current.value?.header.has_photo
  ? `/api/v1/custom-resumes/${current.value.id}/photo?v=${photoVersion.value}`
  : '')

const formatDate = (value: string) => {
  const utcValue = /(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`
  return new Intl.DateTimeFormat(locale.value === 'zh' ? 'zh-CN' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(utcValue))
}

const resetMessages = () => {
  errorMessage.value = ''
  successMessage.value = ''
}

const resetForm = () => {
  form.job_match_id = null
  form.job_title = ''
  form.company_name = ''
  form.job_description = ''
  prefilledFromMatch.value = false
}

const applyJobMatch = (jobMatch: JobMatch) => {
  form.job_match_id = jobMatch.id
  form.job_title = jobMatch.job_title
  form.company_name = jobMatch.company_name ?? ''
  form.job_description = jobMatch.job_description
  prefilledFromMatch.value = true
}

const loadPage = async () => {
  loading.value = true
  resetMessages()
  try {
    const [resumeResponse, versionsResponse] = await Promise.all([
      api.get<ResumeSummary | null>('/resumes/primary'),
      api.get<CustomResumeSummary[]>('/custom-resumes'),
    ])
    resume.value = resumeResponse.data
    versions.value = versionsResponse.data

    const queryId = Number(route.query.jobMatchId)
    if (Number.isInteger(queryId) && queryId > 0) {
      const matchResponse = await api.get<JobMatch | null>('/job-matches/current')
      if (matchResponse.data?.id === queryId) {
        applyJobMatch(matchResponse.data)
        pageMode.value = 'create'
      }
    }
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Failed to load the customised CV page')
  } finally {
    loading.value = false
  }
}

const startCreate = () => {
  resetMessages()
  resetForm()
  pageMode.value = 'create'
  void router.replace({ path: '/app/custom-resumes' })
}

const backToList = () => {
  resetMessages()
  current.value = null
  pageMode.value = 'list'
  void router.replace({ path: '/app/custom-resumes' })
}

const generateResume = async () => {
  resetMessages()
  if (!canGenerate.value) {
    errorMessage.value = 'Please enter the job title and a job description of at least 30 valid characters'
    return
  }
  generating.value = true
  try {
    const payload = form.job_match_id
      ? { job_match_id: form.job_match_id }
      : {
          job_title: form.job_title,
          company_name: form.company_name || null,
          job_description: form.job_description,
        }
    const response = await api.post<CustomResume>('/custom-resumes', payload, { timeout: 90_000 })
    current.value = response.data
    versions.value = [response.data, ...versions.value.filter((item) => item.id !== response.data.id)]
    pageMode.value = 'editor'
    successMessage.value = 'Customised CV generated. Add your basic details and confirm the content, then you can export the finished version.'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Failed to generate the AI customised CV, please try again later')
  } finally {
    generating.value = false
  }
}

const openVersion = async (id: number) => {
  resetMessages()
  try {
    const response = await api.get<CustomResume>(`/custom-resumes/${id}`)
    current.value = response.data
    photoVersion.value += 1
    pageMode.value = 'editor'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Failed to load customised CV')
  }
}

const acceptItem = (item: CustomItem) => {
  item.decision = 'accepted'
  item.final_text = item.suggested_text
}

const rejectItem = (item: CustomItem) => {
  item.decision = 'rejected'
  item.final_text = item.source_kind === 'supplement' ? '' : item.source_text
}

const markCustom = (item: CustomItem) => {
  item.decision = 'custom'
}

const applyAll = (decision: 'accepted' | 'rejected') => {
  if (!current.value) return
  current.value.sections.forEach((section) => section.items.forEach((item) => {
    if (!item.has_suggestion) return
    if (decision === 'accepted') acceptItem(item)
    else rejectItem(item)
  }))
}

const saveResume = async () => {
  if (!current.value) return
  resetMessages()
  saving.value = true
  try {
    const response = await api.put<CustomResume>(`/custom-resumes/${current.value.id}`, {
      header: {
        name: current.value.header.name,
        political_status: current.value.header.political_status,
        phone: current.value.header.phone,
        email: current.value.header.email,
        location: current.value.header.location,
        birth_date: current.value.header.birth_date,
      },
      sections: current.value.sections.map((section) => ({
        title: section.title,
        items: section.items.map((item) => ({ decision: item.decision, final_text: item.final_text })),
      })),
    })
    current.value = response.data
    const index = versions.value.findIndex((item) => item.id === response.data.id)
    if (index >= 0) versions.value[index] = response.data
    successMessage.value = response.data.status === 'ready'
      ? 'The final CV has been saved; you can export it as PDF or Word.'
      : !response.data.header.name
        ? 'Draft saved. Please enter a name and save again.'
        : `Draft saved. There are still ${response.data.pending_count} suggestions to handle.`
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Failed to save customised CV')
  } finally {
    saving.value = false
  }
}

const exportPdf = async () => {
  if (!current.value) return
  resetMessages()
  if (!headerComplete.value || pendingCount.value > 0 || current.value.status !== 'ready') {
    errorMessage.value = 'Please enter your name, process all suggestions and save, then export PDF'
    return
  }
  exporting.value = true
  try {
    const response = await api.post(`/custom-resumes/${current.value.id}/export`, undefined, {
      responseType: 'blob',
      timeout: 30_000,
    })
    const url = URL.createObjectURL(response.data)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${current.value.job_title}-customised-CV.pdf`
    anchor.click()
    URL.revokeObjectURL(url)
    successMessage.value = 'PDF exported.'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'PDF export failed')
  } finally {
    exporting.value = false
  }
}

const exportWord = async () => {
  if (!current.value) return
  resetMessages()
  if (!headerComplete.value || pendingCount.value > 0 || current.value.status !== 'ready') {
    errorMessage.value = 'Please enter your name, process all suggestions and save, then export Word'
    return
  }
  exportingWord.value = true
  try {
    const response = await api.post(`/custom-resumes/${current.value.id}/export/word`, undefined, {
      responseType: 'blob',
      timeout: 30_000,
    })
    const url = URL.createObjectURL(response.data)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${current.value.job_title}-customised-CV.docx`
    anchor.click()
    URL.revokeObjectURL(url)
    successMessage.value = 'Word exported. You can continue editing.'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Word export failed')
  } finally {
    exportingWord.value = false
  }
}

const choosePhoto = () => photoInput.value?.click()

const onPhotoSelected = async (event: Event) => {
  if (!current.value) return
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  resetMessages()
  if (!['image/jpeg', 'image/png'].includes(file.type) || file.size > 2 * 1024 * 1024) {
    errorMessage.value = 'ID photo only supports JPG or PNG images up to 2 MB'
    return
  }
  photoBusy.value = true
  try {
    const data = new FormData()
    data.append('photo', file)
    await api.post<CustomResume>(`/custom-resumes/${current.value.id}/photo`, data)
    current.value.header.has_photo = true
    photoVersion.value += 1
    successMessage.value = 'ID photo added to CV.'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'ID photo upload failed')
  } finally {
    photoBusy.value = false
  }
}

const removePhoto = async () => {
  if (!current.value?.header.has_photo) return
  resetMessages()
  photoBusy.value = true
  try {
    await api.delete(`/custom-resumes/${current.value.id}/photo`)
    current.value.header.has_photo = false
    photoVersion.value += 1
    successMessage.value = 'ID photo removed.'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Failed to remove ID photo')
  } finally {
    photoBusy.value = false
  }
}

const deleteVersion = async (item: CustomResumeSummary) => {
  if (!window.confirm(t(`Delete the customised CV for "${item.job_title}"? This cannot be undone.`))) return
  resetMessages()
  deletingId.value = item.id
  try {
    await api.delete(`/custom-resumes/${item.id}`)
    versions.value = versions.value.filter((version) => version.id !== item.id)
    if (current.value?.id === item.id) backToList()
    successMessage.value = 'Customised CV deleted.'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Failed to delete customised CV')
  } finally {
    deletingId.value = null
  }
}

onMounted(loadPage)
</script>

<template>
  <section class="custom-resume-page">
    <div class="module-intro custom-resume-intro">
      <div>
        <span class="eyebrow">{{ t("TAILORED RESUME") }}</span>
        <h2>{{ t("Job-tailored CV") }}</h2>
        <p>{{ t("Reorganise the real content from your master CV around the target role. You decide whether to accept each AI rewrite.") }}</p>
      </div>
      <button v-if="pageMode !== 'create' && resume?.confirmed_at" class="save-button" type="button" @click="startCreate">
        {{ t("Create new version") }}
      </button>
    </div>

    <div v-if="loading" class="profile-loading">{{ t("Loading tailored CV…") }}</div>
    <template v-else>
      <div v-if="!resume" class="diagnosis-empty-card">
        <span>01</span><h3>{{ t("No main CV yet") }}</h3><p>{{ t("A customised version must start from a genuine master CV.") }}</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">{{ t("Go to upload CV") }}</RouterLink>
      </div>

      <div v-else-if="!resume.confirmed_at" class="diagnosis-empty-card">
        <span>02</span><h3>{{ t("Main CV text not yet confirmed") }}</h3><p>{{ t("Please check the parsed text before generating the customised version for the role.") }}</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">{{ t("Go to confirm text") }}</RouterLink>
      </div>

      <template v-else>
        <section v-if="pageMode === 'list'" class="custom-version-section">
          <div v-if="versions.length" class="custom-version-grid">
            <article v-for="item in versions" :key="item.id" class="custom-version-card">
              <div class="custom-version-topline">
                <span :class="['custom-status', item.status]">{{ t(item.status === 'ready' ? 'Confirmed' : 'To confirm') }}</span>
                <button type="button" :disabled="deletingId === item.id" @click="deleteVersion(item)">
                  {{ t(deletingId === item.id ? 'Deleting' : 'Delete') }}
                </button>
              </div>
              <small>{{ t(item.company_name || 'Target role') }}</small>
              <h3>{{ t(item.job_title) }}</h3>
              <p>{{ t("Based on master CV content version") }} {{ t(item.source_resume_version) }}</p>
              <div><span>{{ t(item.pending_count ? `${item.pending_count} suggestions pending` : 'All suggestions processed') }}</span><span>{{ t(formatDate(item.updated_at)) }}</span></div>
              <button class="custom-open-button" type="button" @click="openVersion(item.id)">{{ t("Open version →") }}</button>
            </article>
          </div>
          <div v-else class="custom-empty-state">
            <span>{{ t("TAILOR YOUR STORY") }}</span>
            <h3>{{ t("No role-specific CV yet") }}</h3>
            <p>{{ t("Enter the target role and the AI will generate line-by-line rewrite suggestions based on your main CV for you to confirm, saving them as a separate version.") }}</p>
            <button class="save-button" type="button" @click="startCreate">{{ t("Create your first customised CV") }}</button>
          </div>
        </section>

        <form v-else-if="pageMode === 'create'" class="job-match-form-card custom-create-card" @submit.prevent="generateResume">
          <div class="job-match-form-heading">
            <div><span>{{ t("Target role") }}</span><h3>{{ t("Create a new customised CV") }}</h3></div>
            <button type="button" @click="backToList">{{ t("Return to version list") }}</button>
          </div>

          <div v-if="prefilledFromMatch" class="custom-prefill-note">
            {{ t("Job information has been carried over from the previous job match result. The generated content still only uses real facts from the master CV.") }}
          </div>
          <div class="job-basic-grid">
            <label><span>{{ t("Job title") }} <b>*</b></span><input v-model="form.job_title" maxlength="100" :placeholder="t('For example: Front-end Development Engineer')" :disabled="prefilledFromMatch" /></label>
            <label><span>{{ t("Company name") }} <small>{{ t("Optional") }}</small></span><input v-model="form.company_name" maxlength="100" :placeholder="t('For example: XX Technology')" :disabled="prefilledFromMatch" /></label>
          </div>
          <label class="job-jd-field"><span class="field-label">{{ t("Role JD") }} <b>*</b></span>
            <textarea v-model="form.job_description" maxlength="20000" :placeholder="t('Paste the job responsibilities, requirements and desirable criteria…')" :disabled="prefilledFromMatch"></textarea>
            <span class="field-count">{{ t(effectiveJdLength.toLocaleString()) }} {{ t("/ 20,000 valid characters") }}</span>
          </label>
          <div class="job-form-footer">
            <div><b>{{ t("Content source") }}</b><span>{{ t(resume.original_name) }} {{ t("· Content version") }} {{ t(resume.content_version) }}</span></div>
            <button class="save-button job-analyze-button" type="submit" :disabled="generating || !canGenerate">
              {{ t(generating ? 'Generating tailored CV…' : 'Generate customised CV') }}
            </button>
          </div>
        </form>

        <template v-else-if="current">
          <div class="custom-editor-header">
            <button type="button" @click="backToList">{{ t("← Back to the version list") }}</button>
            <div><span>{{ t(current.company_name || 'Target role') }}</span><h3>{{ t(current.job_title) }}</h3><small>{{ t("Based on master CV content version") }} {{ t(current.source_resume_version) }}</small></div>
            <div class="custom-editor-actions">
              <button type="button" @click="applyAll('rejected')">{{ t("Keep all original text") }}</button>
              <button type="button" @click="applyAll('accepted')">{{ t("Accept all suggestions") }}</button>
              <button class="save-button" type="button" :disabled="saving" @click="saveResume">{{ t(saving ? 'Saving…' : 'Save version') }}</button>
              <button class="custom-word-export-button" type="button" :disabled="exporting || exportingWord || current.status !== 'ready'" @click="exportWord">{{ t(exportingWord ? 'Exporting…' : 'Export Word') }}</button>
              <button class="custom-export-button" type="button" :disabled="exporting || exportingWord || current.status !== 'ready'" @click="exportPdf">{{ t(exporting ? 'Exporting…' : 'Export PDF') }}</button>
            </div>
          </div>

          <div class="custom-progress-card">
            <div><strong>{{ t(totalItems - pendingCount) }}</strong><span>/ {{ t(totalItems) }} {{ t("items processed") }}</span></div>
            <p>{{ t(pendingCount ? `There are still ${pendingCount} suggestions to accept, keep or edit manually.` : 'All suggestions processed; export once saved.') }}</p>
          </div>

          <section v-if="current.missing_information_warnings.length" class="custom-warning-card">
            <div><span>{{ t("NOT IN RESUME") }}</span><h3>{{ t("Job requirements that cannot be added directly") }}</h3></div>
            <ul><li v-for="warning in current.missing_information_warnings" :key="warning">{{ t(warning) }}</li></ul>
          </section>

          <div class="custom-workspace-grid">
            <div class="custom-review-column">
              <section class="resume-header-editor">
                <div class="resume-header-editor-title">
                  <div><span>{{ t("CV template") }}</span><h3>{{ t("Basic information and ID photo") }}</h3></div>
                  <small>{{ t("Results can be edited directly; name is required for export.") }}</small>
                </div>
                <div class="resume-header-form">
                  <label><span>{{ t("Name") }} <b>*</b></span><input v-model="current.header.name" maxlength="40" :placeholder="t('Please enter your real name')" /></label>
                  <label><span>{{ t("Political affiliation") }}</span><input v-model="current.header.political_status" maxlength="40" :placeholder="t('Optional')" /></label>
                  <label><span>{{ t("Contact phone") }}</span><input v-model="current.header.phone" maxlength="50" :placeholder="t('Optional')" /></label>
                  <label><span>{{ t("Email") }}</span><input v-model="current.header.email" maxlength="100" :placeholder="t('Optional')" /></label>
                  <label><span>{{ t("Location") }}</span><input v-model="current.header.location" maxlength="100" :placeholder="t('Optional')" /></label>
                  <label><span>{{ t("Date of birth") }}</span><input v-model="current.header.birth_date" maxlength="40" :placeholder="t('Optional')" /></label>
                </div>
                <div class="resume-photo-actions">
                  <input ref="photoInput" class="visually-hidden" type="file" accept="image/jpeg,image/png" @change="onPhotoSelected" />
                  <button type="button" :disabled="photoBusy" @click="choosePhoto">{{ t(photoBusy ? 'Processing…' : current.header.has_photo ? 'Change ID photo' : 'Upload ID photo') }}</button>
                  <button v-if="current.header.has_photo" class="resume-photo-remove" type="button" :disabled="photoBusy" @click="removePhoto">{{ t("Remove photo") }}</button>
                  <small>{{ t("Supports JPG and PNG, up to 2 MB; if none is uploaded, no empty photo frame will be kept in the final output.") }}</small>
                </div>
              </section>

              <div class="custom-sections">
                <section v-for="(section, sectionIndex) in current.sections" :key="sectionIndex" class="custom-section-card">
                  <div class="custom-section-title"><span>{{ t(String(sectionIndex + 1).padStart(2, '0')) }}</span><input v-model="section.title" maxlength="50" :aria-label="t('CV section title')" /></div>
                  <article v-for="(item, itemIndex) in section.items" :key="itemIndex" class="custom-change-card">
                    <div class="custom-change-heading">
                      <span :class="['decision-chip', item.decision]">{{ t({ pending: 'To do', accepted: 'Adopted', rejected: 'Keep original', custom: 'Edit manually' }[item.decision]) }}</span>
                      <span class="resume-line-type">{{ t(item.item_type === 'heading' ? 'Experience title' : 'Key points') }}</span>
                      <p v-if="item.has_suggestion">{{ t(item.reason) }}</p>
                    </div>
                    <div v-if="item.has_suggestion" class="custom-comparison-grid">
                      <div><span>{{ t("Main CV text") }}</span><p>{{ t(item.source_text) }}</p></div>
                      <div><span>{{ t("AI suggestions") }}</span><p>{{ t(item.suggested_text) }}</p></div>
                    </div>
                    <label class="custom-final-field"><span>{{ t("Final content") }}</span><textarea v-model="item.final_text" maxlength="2000" @input="markCustom(item)"></textarea></label>
                    <div v-if="item.has_suggestion" class="custom-decision-actions">
                      <button type="button" @click="rejectItem(item)">{{ t("Keep original") }}</button>
                      <button type="button" @click="acceptItem(item)">{{ t("Adopt AI suggestions") }}</button>
                    </div>
                  </article>
                </section>
              </div>
            </div>

            <aside class="resume-preview-panel">
              <div class="resume-preview-heading"><span>{{ t("Final preview") }}</span><small>{{ t("PDF and Word use the same CV template") }}</small></div>
              <div class="resume-paper">
                <header class="resume-paper-header">
                  <div class="resume-paper-identity">
                    <h2>{{ t(current.header.name || 'Name') }} <small v-if="current.header.political_status">（{{ t(current.header.political_status) }}）</small></h2>
                    <div class="resume-paper-contacts">
                      <span v-if="current.header.phone"><b>{{ t("Contact phone:") }}</b>{{ t(current.header.phone) }}</span>
                      <span v-if="current.header.email"><b>{{ t("Email:") }}</b>{{ t(current.header.email) }}</span>
                      <span v-if="current.header.location"><b>{{ t("Location:") }}</b>{{ t(current.header.location) }}</span>
                      <span v-if="current.header.birth_date"><b>{{ t("Date of birth:") }}</b>{{ t(current.header.birth_date) }}</span>
                    </div>
                  </div>
                  <img v-if="current.header.has_photo" :src="photoUrl" :alt="t('CV photo')" />
                </header>
                <section v-for="(section, sectionIndex) in current.sections" :key="`preview-${sectionIndex}`" class="resume-paper-section">
                  <h3>{{ t(section.title) }}</h3>
                  <template v-for="(item, itemIndex) in section.items" :key="`preview-${sectionIndex}-${itemIndex}`">
                    <p v-if="item.final_text.trim()" :class="item.item_type === 'heading' ? 'resume-paper-entry' : 'resume-paper-bullet'">
                      <span v-if="item.item_type !== 'heading'">▪</span>{{ t(item.final_text) }}
                    </p>
                  </template>
                </section>
              </div>
            </aside>
          </div>
          <div class="ai-reference-note">{{ t("The AI only reorganises and rewrites. Before exporting, please check the facts, contact details and dates again.") }}</div>
        </template>

        <div v-if="successMessage" class="form-success custom-page-message" role="status">{{ t(successMessage) }}</div>
        <div v-if="errorMessage" class="form-error diagnosis-error custom-page-message" role="alert">{{ t(errorMessage) }}</div>
      </template>
    </template>
  </section>
</template>
