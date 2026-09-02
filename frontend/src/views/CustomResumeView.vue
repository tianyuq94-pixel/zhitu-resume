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

type Decision = 'pending' | 'accepted' | 'rejected' | 'custom'
type CustomItem = {
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
  template_name: '简历模板'
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
const totalItems = computed(() => current.value?.sections.reduce((total, section) => total + section.items.length, 0) ?? 0)
const headerComplete = computed(() => Boolean(current.value?.header.name.trim()))
const photoUrl = computed(() => current.value?.header.has_photo
  ? `/api/v1/custom-resumes/${current.value.id}/photo?v=${photoVersion.value}`
  : '')

const formatDate = (value: string) => {
  const utcValue = /(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(utcValue))
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
    errorMessage.value = getApiErrorMessage(error, '定制简历页面加载失败')
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
    errorMessage.value = '请填写岗位名称，并输入不少于 30 个有效字符的岗位 JD'
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
    successMessage.value = '定制简历已生成。补充基本信息并确认内容后即可导出成品。'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'AI 定制简历生成失败，请稍后重试')
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
    errorMessage.value = getApiErrorMessage(error, '定制简历加载失败')
  }
}

const acceptItem = (item: CustomItem) => {
  item.decision = 'accepted'
  item.final_text = item.suggested_text
}

const rejectItem = (item: CustomItem) => {
  item.decision = 'rejected'
  item.final_text = item.source_text
}

const markCustom = (item: CustomItem) => {
  item.decision = 'custom'
}

const applyAll = (decision: 'accepted' | 'rejected') => {
  if (!current.value) return
  current.value.sections.forEach((section) => section.items.forEach((item) => {
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
      ? '成品简历已保存，可以导出 PDF 或 Word。'
      : !response.data.header.name
        ? '草稿已保存，请填写姓名后再次保存。'
        : `草稿已保存，还有 ${response.data.pending_count} 条建议待处理。`
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '定制简历保存失败')
  } finally {
    saving.value = false
  }
}

const exportPdf = async () => {
  if (!current.value) return
  resetMessages()
  if (!headerComplete.value || pendingCount.value > 0 || current.value.status !== 'ready') {
    errorMessage.value = '请填写姓名、处理完全部建议并保存，再导出 PDF'
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
    anchor.download = `${current.value.job_title}-定制简历.pdf`
    anchor.click()
    URL.revokeObjectURL(url)
    successMessage.value = 'PDF 已导出。'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'PDF 导出失败')
  } finally {
    exporting.value = false
  }
}

const exportWord = async () => {
  if (!current.value) return
  resetMessages()
  if (!headerComplete.value || pendingCount.value > 0 || current.value.status !== 'ready') {
    errorMessage.value = '请填写姓名、处理完全部建议并保存，再导出 Word'
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
    anchor.download = `${current.value.job_title}-定制简历.docx`
    anchor.click()
    URL.revokeObjectURL(url)
    successMessage.value = 'Word 已导出，可以继续修改。'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Word 导出失败')
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
    errorMessage.value = '证件照只支持不超过 2 MB 的 JPG 或 PNG 图片'
    return
  }
  photoBusy.value = true
  try {
    const data = new FormData()
    data.append('photo', file)
    await api.post<CustomResume>(`/custom-resumes/${current.value.id}/photo`, data)
    current.value.header.has_photo = true
    photoVersion.value += 1
    successMessage.value = '证件照已加入简历。'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '证件照上传失败')
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
    successMessage.value = '证件照已移除。'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '证件照移除失败')
  } finally {
    photoBusy.value = false
  }
}

const deleteVersion = async (item: CustomResumeSummary) => {
  if (!window.confirm(`确定删除“${item.job_title}”定制简历吗？删除后无法恢复。`)) return
  resetMessages()
  deletingId.value = item.id
  try {
    await api.delete(`/custom-resumes/${item.id}`)
    versions.value = versions.value.filter((version) => version.id !== item.id)
    if (current.value?.id === item.id) backToList()
    successMessage.value = '定制简历已删除。'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '定制简历删除失败')
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
        <span class="eyebrow">TAILORED RESUME</span>
        <h2>岗位定制简历</h2>
        <p>围绕目标岗位重新组织主简历中的真实内容。每一处 AI 改写都由你决定是否采用。</p>
      </div>
      <button v-if="pageMode !== 'create' && resume?.confirmed_at" class="save-button" type="button" @click="startCreate">
        创建新版本
      </button>
    </div>

    <div v-if="loading" class="profile-loading">正在加载定制简历…</div>
    <template v-else>
      <div v-if="!resume" class="diagnosis-empty-card">
        <span>01</span><h3>还没有主简历</h3><p>定制版本必须从一份真实主简历开始。</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">去上传简历</RouterLink>
      </div>

      <div v-else-if="!resume.confirmed_at" class="diagnosis-empty-card">
        <span>02</span><h3>主简历文字尚未确认</h3><p>请先检查解析文字，再生成岗位定制版本。</p>
        <RouterLink class="save-button diagnosis-main-button" to="/app/resume">去确认文字</RouterLink>
      </div>

      <template v-else>
        <section v-if="pageMode === 'list'" class="custom-version-section">
          <div v-if="versions.length" class="custom-version-grid">
            <article v-for="item in versions" :key="item.id" class="custom-version-card">
              <div class="custom-version-topline">
                <span :class="['custom-status', item.status]">{{ item.status === 'ready' ? '已确认' : '待确认' }}</span>
                <button type="button" :disabled="deletingId === item.id" @click="deleteVersion(item)">
                  {{ deletingId === item.id ? '删除中' : '删除' }}
                </button>
              </div>
              <small>{{ item.company_name || '目标岗位' }}</small>
              <h3>{{ item.job_title }}</h3>
              <p>基于主简历内容版本 {{ item.source_resume_version }}</p>
              <div><span>{{ item.pending_count ? `${item.pending_count} 条建议待处理` : '全部建议已处理' }}</span><span>{{ formatDate(item.updated_at) }}</span></div>
              <button class="custom-open-button" type="button" @click="openVersion(item.id)">打开版本 →</button>
            </article>
          </div>
          <div v-else class="custom-empty-state">
            <span>TAILOR YOUR STORY</span>
            <h3>还没有岗位定制简历</h3>
            <p>输入目标岗位，AI 会基于主简历生成逐条可确认的改写建议，并保存为独立版本。</p>
            <button class="save-button" type="button" @click="startCreate">创建第一份定制简历</button>
          </div>
        </section>

        <form v-else-if="pageMode === 'create'" class="job-match-form-card custom-create-card" @submit.prevent="generateResume">
          <div class="job-match-form-heading">
            <div><span>目标岗位</span><h3>创建一份新的定制简历</h3></div>
            <button type="button" @click="backToList">返回版本列表</button>
          </div>

          <div v-if="prefilledFromMatch" class="custom-prefill-note">
            已从刚才的岗位匹配结果带入岗位信息。生成内容仍只使用主简历中的真实事实。
          </div>
          <div class="job-basic-grid">
            <label><span>岗位名称 <b>*</b></span><input v-model="form.job_title" maxlength="100" placeholder="例如：前端开发工程师" :disabled="prefilledFromMatch" /></label>
            <label><span>公司名称 <small>选填</small></span><input v-model="form.company_name" maxlength="100" placeholder="例如：某某科技" :disabled="prefilledFromMatch" /></label>
          </div>
          <label class="job-jd-field"><span class="field-label">岗位 JD <b>*</b></span>
            <textarea v-model="form.job_description" maxlength="20000" placeholder="粘贴岗位职责、任职要求和加分项…" :disabled="prefilledFromMatch"></textarea>
            <span class="field-count">{{ effectiveJdLength.toLocaleString() }} / 20,000 个有效字符</span>
          </label>
          <div class="job-form-footer">
            <div><b>内容来源</b><span>{{ resume.original_name }} · 内容版本 {{ resume.content_version }}</span></div>
            <button class="save-button job-analyze-button" type="submit" :disabled="generating || !canGenerate">
              {{ generating ? '正在生成定制简历…' : '生成定制简历' }}
            </button>
          </div>
        </form>

        <template v-else-if="current">
          <div class="custom-editor-header">
            <button type="button" @click="backToList">← 返回版本列表</button>
            <div><span>{{ current.company_name || '目标岗位' }}</span><h3>{{ current.job_title }}</h3><small>基于主简历内容版本 {{ current.source_resume_version }}</small></div>
            <div class="custom-editor-actions">
              <button type="button" @click="applyAll('rejected')">全部保留原文</button>
              <button type="button" @click="applyAll('accepted')">全部采纳建议</button>
              <button class="save-button" type="button" :disabled="saving" @click="saveResume">{{ saving ? '保存中…' : '保存版本' }}</button>
              <button class="custom-word-export-button" type="button" :disabled="exporting || exportingWord || current.status !== 'ready'" @click="exportWord">{{ exportingWord ? '导出中…' : '导出 Word' }}</button>
              <button class="custom-export-button" type="button" :disabled="exporting || exportingWord || current.status !== 'ready'" @click="exportPdf">{{ exporting ? '导出中…' : '导出 PDF' }}</button>
            </div>
          </div>

          <div class="custom-progress-card">
            <div><strong>{{ totalItems - pendingCount }}</strong><span>/ {{ totalItems }} 条已处理</span></div>
            <p>{{ pendingCount ? `还有 ${pendingCount} 条建议需要采纳、保留或手动修改。` : '全部建议已处理，保存后即可导出。' }}</p>
          </div>

          <section v-if="current.missing_information_warnings.length" class="custom-warning-card">
            <div><span>NOT IN RESUME</span><h3>不能直接添加的岗位要求</h3></div>
            <ul><li v-for="warning in current.missing_information_warnings" :key="warning">{{ warning }}</li></ul>
          </section>

          <div class="custom-workspace-grid">
            <div class="custom-review-column">
              <section class="resume-header-editor">
                <div class="resume-header-editor-title">
                  <div><span>简历模板</span><h3>基本信息与证件照</h3></div>
                  <small>识别结果可以直接修改，姓名为导出必填项。</small>
                </div>
                <div class="resume-header-form">
                  <label><span>姓名 <b>*</b></span><input v-model="current.header.name" maxlength="40" placeholder="请输入真实姓名" /></label>
                  <label><span>政治面貌</span><input v-model="current.header.political_status" maxlength="40" placeholder="选填" /></label>
                  <label><span>联系电话</span><input v-model="current.header.phone" maxlength="50" placeholder="选填" /></label>
                  <label><span>电子邮箱</span><input v-model="current.header.email" maxlength="100" placeholder="选填" /></label>
                  <label><span>所在地</span><input v-model="current.header.location" maxlength="100" placeholder="选填" /></label>
                  <label><span>出生年月</span><input v-model="current.header.birth_date" maxlength="40" placeholder="选填" /></label>
                </div>
                <div class="resume-photo-actions">
                  <input ref="photoInput" class="visually-hidden" type="file" accept="image/jpeg,image/png" @change="onPhotoSelected" />
                  <button type="button" :disabled="photoBusy" @click="choosePhoto">{{ photoBusy ? '处理中…' : current.header.has_photo ? '更换证件照' : '上传证件照' }}</button>
                  <button v-if="current.header.has_photo" class="resume-photo-remove" type="button" :disabled="photoBusy" @click="removePhoto">移除照片</button>
                  <small>支持 JPG、PNG，不超过 2 MB；未上传时成品中不保留空照片框。</small>
                </div>
              </section>

              <div class="custom-sections">
                <section v-for="(section, sectionIndex) in current.sections" :key="sectionIndex" class="custom-section-card">
                  <div class="custom-section-title"><span>{{ String(sectionIndex + 1).padStart(2, '0') }}</span><input v-model="section.title" maxlength="50" aria-label="简历栏目标题" /></div>
                  <article v-for="(item, itemIndex) in section.items" :key="itemIndex" class="custom-change-card">
                    <div class="custom-change-heading">
                      <span :class="['decision-chip', item.decision]">{{ { pending: '待处理', accepted: '已采纳', rejected: '保留原文', custom: '手动修改' }[item.decision] }}</span>
                      <span class="resume-line-type">{{ item.item_type === 'heading' ? '经历标题' : '内容要点' }}</span>
                      <p>{{ item.reason }}</p>
                    </div>
                    <div class="custom-comparison-grid">
                      <div><span>主简历原文</span><p>{{ item.source_text }}</p></div>
                      <div><span>AI 建议</span><p>{{ item.suggested_text }}</p></div>
                    </div>
                    <label class="custom-final-field"><span>最终内容</span><textarea v-model="item.final_text" maxlength="2000" @input="markCustom(item)"></textarea></label>
                    <div class="custom-decision-actions">
                      <button type="button" @click="rejectItem(item)">保留原文</button>
                      <button type="button" @click="acceptItem(item)">采纳 AI 建议</button>
                    </div>
                  </article>
                </section>
              </div>
            </div>

            <aside class="resume-preview-panel">
              <div class="resume-preview-heading"><span>成品预览</span><small>PDF 与 Word 使用同一套简历模板</small></div>
              <div class="resume-paper">
                <header class="resume-paper-header">
                  <div class="resume-paper-identity">
                    <h2>{{ current.header.name || '姓名' }} <small v-if="current.header.political_status">（{{ current.header.political_status }}）</small></h2>
                    <div class="resume-paper-contacts">
                      <span v-if="current.header.phone"><b>联系电话：</b>{{ current.header.phone }}</span>
                      <span v-if="current.header.email"><b>电子邮箱：</b>{{ current.header.email }}</span>
                      <span v-if="current.header.location"><b>所在地：</b>{{ current.header.location }}</span>
                      <span v-if="current.header.birth_date"><b>出生年月：</b>{{ current.header.birth_date }}</span>
                    </div>
                  </div>
                  <img v-if="current.header.has_photo" :src="photoUrl" alt="简历证件照" />
                </header>
                <section v-for="(section, sectionIndex) in current.sections" :key="`preview-${sectionIndex}`" class="resume-paper-section">
                  <h3>{{ section.title }}</h3>
                  <template v-for="(item, itemIndex) in section.items" :key="`preview-${sectionIndex}-${itemIndex}`">
                    <p v-if="item.final_text.trim()" :class="item.item_type === 'heading' ? 'resume-paper-entry' : 'resume-paper-bullet'">
                      <span v-if="item.item_type !== 'heading'">▪</span>{{ item.final_text }}
                    </p>
                  </template>
                </section>
              </div>
            </aside>
          </div>
          <div class="ai-reference-note">AI 只负责重组和改写。导出前请再次核对事实、联系方式和时间信息。</div>
        </template>

        <div v-if="successMessage" class="form-success custom-page-message" role="status">{{ successMessage }}</div>
        <div v-if="errorMessage" class="form-error diagnosis-error custom-page-message" role="alert">{{ errorMessage }}</div>
      </template>
    </template>
  </section>
</template>
