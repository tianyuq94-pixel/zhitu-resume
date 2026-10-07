import { t } from '@/i18n'
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { api, getApiErrorMessage } from './api'
import type { AxiosResponse } from 'axios'

type Resume = { id: number; original_name: string; size_bytes: number; parsed_text: string; confirmed_at: string | null }
type Match = { id: number; match_score: number; verdict_reason: string; key_requirements: { requirement: string; jd_evidence: string }[]; matched_items: { requirement: string; resume_evidence: string }[]; missing_items: { requirement: string; explanation: string }[]; improvements: string[] }
type Item = { source_kind: 'resume' | 'supplement'; has_suggestion: boolean; item_type: 'heading' | 'bullet'; source_text: string; suggested_text: string; reason: string; final_text: string; decision: 'pending' | 'accepted' | 'rejected' | 'custom' }
type Custom = { id: number; header: { name: string; phone: string; email: string; location: string; political_status: string; birth_date: string; has_photo?: boolean }; sections: { title: string; items: Item[] }[]; missing_information_warnings: string[]; status: string }
type Run = { id: string; title: string; status: string; revision: number; job_title: string; company_name: string; job_description: string; brief: string; generic_requirements: boolean; steps: { tool: string; message: string }[]; messages: { role: string; content: string }[]; error: string | null; match?: Match; custom_resume_id?: number; preparation?: { summary: string; items: { title: string; focus: string; question: string; outline: string[] }[] } }
type History = Pick<Run, 'id' | 'title' | 'status'>

function parseFacts(data: unknown) {
  if (!data || typeof data !== 'object' || !('revision' in data)) throw new Error('The details service is not ready yet, please refresh the page')
  const value = data as Record<string, unknown>
  if (!['about', 'skills', 'experiences'].every(key => typeof value[key] === 'string') || typeof value.revision !== 'number') {
    throw new Error('Unexpected details format, please refresh the page')
  }
  return { about: value.about as string, skills: value.skills as string, experiences: value.experiences as string, revision: value.revision as number }
}

export function useAgent() {
  const facts = ref({ about: '', skills: '', experiences: '', revision: 0 })
  const factsSaving = ref(false), factsNotice = ref(''), addition = ref('')
  const factsTab = ref('CV file')
  async function saveFacts() {
    if (working.value || factsSaving.value) return false
    factsSaving.value = true; factsNotice.value = ''
    try {
      facts.value = parseFacts((await api.put('/profile/facts', facts.value)).data)
      factsNotice.value = 'Details saved; these will be used for future tasks.'
      return true
    } catch (error) { factsNotice.value = getApiErrorMessage(error); return false }
    finally { factsSaving.value = false }
  }
  async function addFacts() {
    if (!addition.value.trim() || working.value || factsSaving.value) return false
    const previous = facts.value.experiences
    const next = [previous, addition.value.trim()].filter(Boolean).join('\n\n')
    if (next.length > 10000) { factsNotice.value = 'The experience library has reached 10,000 characters. Please tidy it up in My CV before adding more'; return false }
    facts.value.experiences = next
    if (!(await saveFacts())) { facts.value.experiences = previous; return false }
    addition.value = ''
    return true
  }
  async function regenerate() {
    if (!run.value || working.value || factsSaving.value) return
    if (addition.value.trim() && !(await addFacts())) return
    if (custom.value && !(await saveCustom())) return
    const target = run.value
    starting.value = true
    try {
      const next = (await api.post<Run>('/agent', { job_title: target.job_title, company_name: target.company_name || '',
        job_description: target.generic_requirements ? '' : target.job_description, brief: target.brief })).data
      run.value = next; custom.value = null; tab.value = 'Tailored CV'
      window.history.replaceState(null, '', '/agent?task=' + next.id)
      await refreshHistory()
      await execute()
    } catch (error) { notice.value = getApiErrorMessage(error) }
    finally { starting.value = false }
  }
  const prompt = ref(''), jobTitle = ref(''), companyName = ref('')
  const run = ref<Run | null>(null), history = ref<History[]>([])
  const resume = ref<Resume | null>(null), parsedText = ref(''), custom = ref<Custom | null>(null)
  const resumeDialog = ref<HTMLDialogElement | null>(null)
  const fileUrl = ref(''), fileError = ref(''), notice = ref('')
  const busy = ref(false), uploading = ref(false), saving = ref(false), ready = ref(false)
  const tab = ref('Role analysis'), mobileTab = ref('Chat'), paused = ref(false)
  let disposed = false
  const starting = ref(false)
  const working = computed(() => busy.value || starting.value)
  const active = computed(() => !!run.value)
  const fileName = computed(() => resume.value?.original_name || '')
  const isPdf = computed(() => fileName.value.toLowerCase().endsWith('.pdf'))
  const currentTitle = computed(() => run.value?.title || 'New career plan')
  const pending = computed(() => custom.value?.sections.reduce((sum, s) => sum + s.items.filter(i => i.decision === 'pending').length, 0) ?? 0)
  const statusLabel = computed(() => working.value ? 'Preparing results' : ({ ready: 'Preparation paused', running: 'Resumable task', waiting: 'Waiting for additional information', failed: 'Needs retry', completed: 'Job preparation complete' }[run.value?.status || ''] || 'Ready'))
  const openResume = () => resumeDialog.value?.showModal()
  function revoke() { if (fileUrl.value.startsWith('blob:')) URL.revokeObjectURL(fileUrl.value); fileUrl.value = '' }
  async function loadFile() {
    revoke()
    if (resume.value) {
      const response = await api.get('/resumes/primary/file', { responseType: 'blob' })
      fileUrl.value = URL.createObjectURL(response.data)
    }
  }
  async function refreshHistory() { history.value = (await api.get<History[]>('/agent')).data }
  async function loadCustom() {
    if (run.value?.custom_resume_id && custom.value?.id !== run.value.custom_resume_id) {
      custom.value = (await api.get<Custom>(`/custom-resumes/${run.value.custom_resume_id}`)).data
    }
  }
  async function initialize() {
    notice.value = ''
    try {
      await api.post('/auth/guest')
      facts.value = parseFacts((await api.get('/profile/facts')).data)
      resume.value = (await api.get<Resume | null>('/resumes/primary')).data
      parsedText.value = resume.value?.parsed_text || ''
      await refreshHistory()
      ready.value = true
      await loadFile()
      const id = new URLSearchParams(location.search).get('task')
      if (id) await openTask(id)
    } catch (error) { notice.value = getApiErrorMessage(error, 'Failed to load workspace, please click to reconnect') }
  }
  async function openTask(id: string) {
    if (working.value || saving.value) return
    try {
      custom.value = null
      run.value = (await api.get<Run>(`/agent/${id}`)).data
      await loadCustom()
      window.history.replaceState(null, '', `/agent?task=${encodeURIComponent(id)}`)
      mobileTab.value = 'Chat'
      prompt.value = ''
    } catch (error) { notice.value = getApiErrorMessage(error) }
  }
  async function execute() {
    if (!run.value || busy.value) return
    busy.value = true; paused.value = false; notice.value = ''
    try {
      while (run.value && ['ready', 'failed', 'running'].includes(run.value.status) && !paused.value && !disposed) {
        const id: string = run.value.id
        const response: AxiosResponse<Run> = await api.post<Run>(`/agent/${id}/step`, { revision: run.value.revision }, { timeout: 290_000 })
        run.value = response.data
        await loadCustom()
        await refreshHistory()
        if (response.data.status === 'failed') { notice.value = response.data.error || 'Execution failed, please try again'; break }
      }
    } catch (error) {
      notice.value = getApiErrorMessage(error)
      if (run.value) {
        try { run.value = (await api.get<Run>(`/agent/${run.value.id}`)).data } catch { /* Keep last durable state visible. */ }
      }
    } finally { busy.value = false }
  }
  async function send() {
    if (!ready.value || busy.value || uploading.value || starting.value) return
    starting.value = true
    notice.value = ''
    try {
      if (run.value?.status === 'waiting') {
        if (!prompt.value.trim()) return
        run.value = (await api.post<Run>(`/agent/${run.value.id}/reply`, { message: prompt.value })).data
      } else if (!run.value) {
        if (jobTitle.value.trim().length < 2) { notice.value = 'Please enter the job title; company name is optional'; return }
        if (!resume.value?.confirmed_at) { openResume(); fileError.value = 'Please add a CV and confirm the parsed text first'; return }
        run.value = (await api.post<Run>('/agent', { job_title: jobTitle.value, company_name: companyName.value,
          job_description: prompt.value, brief: prompt.value.slice(0, 5000) })).data
        window.history.replaceState(null, '', `/agent?task=${run.value.id}`)
        await refreshHistory()
      } else { notice.value = 'Please click to continue the task, or start another job application task'; return }
      prompt.value = ''
      await execute()
    } catch (error) { notice.value = getApiErrorMessage(error) }
    finally { starting.value = false }
  }
  async function pickFile(event: Event) {
    const input = event.target as HTMLInputElement, file = input.files?.[0]
    input.value = ''
    if (!file || busy.value || uploading.value || !ready.value) return
    if (!resumeDialog.value?.open) openResume()
    fileError.value = ''
    if (!/\.(pdf|docx)$/i.test(file.name) || file.size === 0 || file.size > 10 * 1024 * 1024) {
      fileError.value = 'Please select a non-empty PDF or DOCX file no larger than 10 MB'; return
    }
    if (resume.value && !window.confirm(t('After replacing the main CV, unfinished tasks must be recreated. Existing results are kept. Continue replacing?'))) return
    uploading.value = true
    try {
      const form = new FormData(); form.append('file', file)
      resume.value = (await api.post<Resume>('/resumes/primary', form, { timeout: 90_000 })).data
      parsedText.value = resume.value.parsed_text
      await loadFile()
    } catch (error) { fileError.value = getApiErrorMessage(error) }
    finally { uploading.value = false }
  }
  async function confirmResume() {
    if (busy.value || uploading.value) return
    uploading.value = true; fileError.value = ''
    try {
      if (parsedText.value !== resume.value?.parsed_text || !resume.value?.confirmed_at) {
        resume.value = (await api.put<Resume>('/resumes/primary/text', { parsed_text: parsedText.value })).data
      }
      resumeDialog.value?.close()
      notice.value = 'CV saved. You can start career tasks'
    } catch (error) { fileError.value = getApiErrorMessage(error) }
    finally { uploading.value = false }
  }
  async function clearFile() {
    if (busy.value || uploading.value || !window.confirm(t('Deleting the main CV will also delete the associated old analyses and customised CV files. Confirm deletion?'))) return
    uploading.value = true
    try { await api.delete('/resumes/primary'); resume.value = null; parsedText.value = ''; custom.value = null; revoke() }
    catch (error) { fileError.value = getApiErrorMessage(error) }
    finally { uploading.value = false }
  }
  function reset() {
    if (working.value || saving.value) return
    run.value = null; custom.value = null; prompt.value = ''; jobTitle.value = ''; companyName.value = ''
    notice.value = ''; mobileTab.value = 'Chat'; tab.value = 'Role analysis'
    window.history.replaceState(null, '', '/agent')
  }
  async function saveCustom() {
    if (!custom.value || saving.value) return false
    saving.value = true
    try {
      const { has_photo, ...header } = custom.value.header
      custom.value = (await api.put<Custom>(`/custom-resumes/${custom.value.id}`, { header,
        sections: custom.value.sections.map(s => ({ title: s.title, items: s.items.map(i => ({ decision: i.decision, final_text: i.final_text })) })) })).data
      notice.value = 'Customised CV changes saved'
      return true
    } catch (error) { notice.value = getApiErrorMessage(error); return false }
    finally { saving.value = false }
  }
  function decide(item: Item, decision: 'accepted' | 'rejected') {
    item.decision = decision
    item.final_text = decision === 'accepted' ? item.suggested_text : item.source_kind === 'supplement' ? '' : item.source_text
  }
  async function download(format: 'pdf' | 'word') {
    if (!(await saveCustom()) || !custom.value) return
    try {
      const response = await api.post(`/custom-resumes/${custom.value.id}/export${format === 'word' ? '/word' : ''}`, {}, { responseType: 'blob', timeout: 60_000 })
      const url = URL.createObjectURL(response.data)
      const link = document.createElement('a'); link.href = url; link.download = `${currentTitle.value.replace(/[\\/:*?"<>|]/g, '-')}-CV.${format === 'word' ? 'docx' : 'pdf'}`
      link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (error) { notice.value = 'Export failed. Please enter your name, confirm each suggestion one by one and save, then try again' }
  }
  function startInterview() {
    if (run.value) location.href = `/agent/interview?agentRun=${run.value.id}`
  }
  onMounted(initialize)
  onBeforeUnmount(() => { disposed = true; revoke() })
  return { facts, factsSaving, factsNotice, factsTab, addition, saveFacts, addFacts, regenerate, prompt, jobTitle, companyName, run, history, resume, parsedText, custom, resumeDialog,
    fileUrl, fileError, notice, busy, working, uploading, saving, ready, tab, mobileTab, paused, active,
    fileName, isPdf, currentTitle, pending, statusLabel, openResume, initialize, openTask, execute,
    send, pickFile, confirmResume, clearFile, reset, saveCustom, decide, download, startInterview }
}
