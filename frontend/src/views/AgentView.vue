<script setup lang="ts">
import { useAgent } from '@/services/agent'
import { computed, ref } from 'vue'
const { facts, factsSaving, factsNotice, factsTab, addition, saveFacts, addFacts, regenerate, prompt, jobTitle, companyName, run, history, resume, parsedText, custom, resumeDialog,
  fileUrl, fileError, notice, busy, working, uploading, saving, ready, tab, mobileTab, paused, active,
  fileName, isPdf, currentTitle, pending, statusLabel, openResume, initialize, openTask, execute,
  send, pickFile, confirmResume, clearFile, reset, saveCustom, decide, download, startInterview } = useAgent()
const tabs = ['岗位分析', '定制简历', '面试准备']
const examples = ['AI 应用开发工程师', '产品经理', '前端开发工程师']
const paperPreview = ref(false)
const missingPrompts = computed(() => (custom.value?.missing_information_warnings || []).map(text => text
  .replace(/主简历中未明确体现|主简历中未体现/g, '可以补充')
  .replace(/[，,；;]?不能直接添加[。.]?/g, '：如有相关实践，请补充具体任务、你的贡献和真实结果；没有可跳过。')))
const factCount = computed(() => [facts.value.about, facts.value.skills, facts.value.experiences].filter(Boolean).length)
const suggestionSections = computed(() => (custom.value?.sections || []).map(s => ({ ...s, items: s.items.filter(i => i.has_suggestion) })).filter(s => s.items.length))
const suggestionCount = computed(() => suggestionSections.value.reduce((n, s) => n + s.items.length, 0))
const question = computed(() => run.value?.status === 'waiting' ? [...run.value.messages].reverse().find(m => m.role === 'assistant')?.content : '')
const resultReady = computed(() => tab.value === '岗位分析' ? !!run.value?.match : tab.value === '定制简历' ? !!custom.value : !!run.value?.preparation)
</script>

<template>
  <div class="agent-shell">
    <aside class="agent-rail">
      <a class="agent-brand" href="/" title="返回三个入口"><span class="agent-mark">↗</span><span>职途简历<small>YOUR NEXT CHAPTER</small></span></a>
      <button class="agent-new" :disabled="working || saving" @click="reset"><span>＋</span> 开启新的求职任务</button>
      <a class="workspace-back" href="/">← 返回三个入口</a><div class="agent-nav-label">工作空间</div>
      <button class="agent-nav selected" @click="mobileTab = '对话'"><span>◈</span> 求职 Agent <i>NEW</i></button>
      <button class="agent-nav" @click="openResume"><span>▤</span> 我的简历</button>
      <div class="agent-nav-label history-label">最近任务</div>
      <div class="agent-history-list"><button v-for="task in history" :key="task.id" class="agent-history" :class="{ 'task-selected': task.id === run?.id }" :disabled="working || saving" :title="task.title" @click="openTask(task.id)">{{ task.title }}</button></div>
      <p v-if="!history.length" class="agent-empty-history">每一次准备，<br />都从一个新目标开始。</p>
      <div class="facts-mini"><span>YOUR STORY</span><strong>不止一页简历</strong><p>已补充 {{ factCount }} 类资料<br />为不同岗位挑选不同亮点</p><button @click="factsTab = '补充资料'; openResume()">完善我的资料 ↗</button></div><div class="agent-rail-bottom"><span class="guest-avatar">访</span><div>访客工作空间<small>同一浏览器可继续任务</small></div></div>
    </aside>
    <main class="agent-main">
      <header class="agent-header"><div><span class="agent-breadcrumb">工作空间 /</span> {{ currentTitle }}</div><span class="agent-preview-badge">{{ ready ? '访客模式 · 自动保存' : '正在连接工作空间' }}</span></header>
      <div v-if="notice" class="agent-notice global-notice" role="status">{{ notice }}<button v-if="!ready" @click="initialize">重新连接</button><button aria-label="关闭提示" @click="notice = ''">×</button></div>
      <div class="agent-mobile-tabs"><button v-for="item in ['对话', '成果']" :key="item" :class="{ chosen: mobileTab === item }" @click="mobileTab = item">{{ item }}</button><button @click="openResume">我的简历</button><button :disabled="working" @click="reset">新任务</button></div>
      <select class="mobile-history" aria-label="最近任务" :value="run?.id || ''" :disabled="working" @change="openTask(($event.target as HTMLSelectElement).value)"><option value="" disabled>最近任务</option><option v-for="task in history" :key="task.id" :value="task.id">{{ task.title }}</option></select>
      <div class="agent-columns" :class="{ 'show-results': mobileTab === '成果', 'has-task': active }">
        <section class="agent-conversation">
          <div v-if="!active" class="agent-welcome">
            <span class="agent-kicker"><span></span> A LITTLE PREPARATION. A BIG NEXT STEP.</span>
            <h1>这次，<br />你想争取<span>什么岗位？</span></h1>
            <p>带上你的经历和目标。<br />从岗位分析到一份准备好的简历，我们一起完成。</p>
            <div class="agent-suggestions"><button v-for="(example, index) in examples" :key="example" @click="jobTitle = example"><span>0{{ index + 1 }}</span>{{ example }}<b>↗</b></button></div>
          </div>
          <div v-else-if="run" class="agent-thread">
            <div class="agent-task-label">本次目标 <span>{{ statusLabel }}</span></div>
            <h2>{{ run.title }}</h2>
            <div v-if="run.generic_requirements" class="agent-notice">未提供完整 JD，本次采用岗位通用建议，不代表该公司的实际招聘要求。</div>
            <div v-if="question" class="agent-question"><h3>还需要你补充一点信息</h3><p>{{ question }}</p></div>
            <div v-if="run.error" class="resume-file-error" role="alert">{{ run.error }}</div>
            <button v-if="!working && ['ready', 'failed', 'running'].includes(run.status)" class="agent-result-action" @click="execute">{{ run.status === 'failed' ? '重新尝试' : '继续准备' }} →</button>
            <button v-if="!working" class="refresh-facts-button" @click="regenerate">使用最新资料重新生成 ↗</button>
            <p v-if="run.status === 'completed'" class="completion-note">你的求职成果已准备好。查看下方结果，确认简历后即可下载。</p>
          </div>
          <div v-if="!run || run.status === 'waiting'" class="agent-composer-wrap">
            <form v-if="!run || run.status === 'waiting'" class="agent-composer" @submit.prevent="send">
              <div v-if="!run" class="agent-job-fields"><label>岗位名称 *<input v-model="jobTitle" required minlength="2" maxlength="100" placeholder="例如：AI 应用开发工程师" /></label><label>公司名称<input v-model="companyName" maxlength="100" placeholder="选填，例如：小米" /></label></div>
              <label class="agent-sr" for="agent-prompt">{{ run ? '补充信息' : '岗位要求' }}</label><textarea id="agent-prompt" v-model="prompt" :maxlength="run ? 5000 : 20000" :placeholder="run ? '回答上面的补充问题…' : '粘贴岗位要求（选填），帮助分析得更准确…'" rows="3"></textarea>
              <div class="agent-composer-actions"><button type="button" class="resume-open-button" @click="openResume">＋ {{ fileName || '添加简历' }}</button><button class="agent-send" type="submit" :disabled="!ready || working || uploading || (run ? !prompt.trim() : jobTitle.trim().length < 2)" aria-label="开始或继续求职任务">↑</button></div>
            </form>
            <p class="agent-composer-hint">简历与任务私有保存 · 清除 Cookie 或访客会话过期后无法找回，请及时下载成果</p>
          </div>
        </section>
        <div v-if="working" class="analysis-wait" role="status" aria-live="polite">
          <span class="analysis-orbit" aria-hidden="true">✧</span>
          <div><h3>正在为你准备求职成果<span class="waiting-dots" aria-hidden="true">…</span></h3><p>需要一点时间，已完成的结果会显示在下方。无需重复提交。</p></div>
          <button v-if="busy" @click="paused = true" :disabled="paused">{{ paused ? '完成当前处理后暂停' : '暂停后续准备' }}</button>
        </div>
        <aside class="agent-results">
          <div class="agent-results-heading"><div><span class="agent-kicker">YOUR CAREER KIT</span><h2>{{ active ? '你的求职成果' : '每一步，都有收获' }}</h2></div><span class="agent-kit-icon">✳</span></div>
          <template v-if="!active">
            <div class="agent-paper-scene"><div class="agent-paper"><div class="paper-top"><b>你的下一步</b><span>RESUME</span></div><div class="paper-name">更清晰地，呈现自己。</div><i></i><i></i><div class="paper-section">经历 · 能力 · 潜力</div><i></i><i></i><i></i><div class="paper-section">为目标岗位而准备</div><i></i><i></i></div><span class="agent-paper-tag">✧ 真实经历，精准表达</span></div>
            <div class="agent-outcomes"><div><span class="outcome-icon peach">◎</span><div><h3>看清岗位契合点</h3><p>找到你的优势，也明确需要补足的部分。</p></div></div><div><span class="outcome-icon mint">▤</span><div><h3>带走一份成品简历</h3><p>针对岗位调整，支持 PDF 与 Word 导出。</p></div></div><div><span class="outcome-icon lilac">✧</span><div><h3>有方向地准备面试</h3><p>知识重点、项目追问与回答思路。</p></div></div></div>
            <div class="agent-side-note">按你的节奏来。<br /><span>准备方案完成后，可自行选择模拟面试。</span></div>
          </template>
          <template v-else-if="run">
            <div class="agent-result-tabs" role="tablist" aria-label="求职成果"><button v-for="item in tabs" :key="item" role="tab" :aria-selected="tab === item" :class="{ chosen: tab === item }" @click="tab = item">{{ item }}</button></div>
            <div v-if="!resultReady" class="result-placeholder" :aria-busy="working">
              <template v-if="working"><div class="result-skeleton" aria-hidden="true"><i></i><i></i><i></i></div><h3>{{ tab }}正在准备中</h3><p>准备好后会自动展示，无需刷新。</p></template>
              <template v-else><h3>{{ tab }}尚未生成</h3><p>{{ run.status === 'waiting' ? '补充上方信息后继续。' : '继续任务后，将在这里展示成果。' }}</p></template>
            </div>
            <div v-else-if="tab === '岗位分析'" class="agent-result-content">
              <template v-if="run.match"><h3>{{ run.job_title }} · 岗位解读</h3><p v-if="!run.generic_requirements">参考匹配分：{{ run.match.match_score }} / 100</p><p>{{ run.match.verdict_reason }}</p>
                <h4>岗位关注</h4><ul><li v-for="item in run.match.key_requirements" :key="item.requirement">{{ item.requirement }}</li></ul>
                <div v-for="item in run.match.matched_items" :key="item.requirement" class="agent-insight"><small>你的优势 · {{ item.requirement }}</small><p>{{ item.resume_evidence }}</p></div>
                <h4>需要补足</h4><p v-for="item in run.match.missing_items" :key="item.requirement">{{ item.requirement }}：{{ item.explanation }}</p><h4>建议下一步</h4><ul><li v-for="item in run.match.improvements" :key="item">{{ item }}</li></ul>
              </template><p v-else>岗位分析完成后，会在这里展示真实结果。</p>
            </div>
            <div v-else-if="tab === '定制简历'" class="agent-result-content">
              <template v-if="custom"><h3>确认表达，留下真实经历</h3><p>共 {{ suggestionCount }} 条有效建议，{{ pending }} 条待确认。未改写内容已保留在完整简历中。</p><label class="agent-editor-label">姓名 *<input v-model="custom.header.name" maxlength="40" /></label>
                <div class="agent-job-fields"><label>电话<input v-model="custom.header.phone" maxlength="50" /></label><label>邮箱<input v-model="custom.header.email" maxlength="100" /></label></div>
                <button class="resume-open-button" @click="paperPreview = !paperPreview">{{ paperPreview ? '查看修改建议' : '查看 / 编辑完整简历' }}</button>
                <div v-if="paperPreview" class="agent-live-paper"><h2>{{ custom.header.name || '请填写姓名' }}</h2><p>{{ custom.header.phone }}　{{ custom.header.email }}</p><section v-for="section in custom.sections" :key="section.title"><h3>{{ section.title }}</h3><textarea v-for="(item, index) in section.items" :key="index" v-model="item.final_text" class="paper-text-editor" :aria-label="section.title + '正文' + (index + 1)" maxlength="2000" rows="2" @input="item.decision = 'custom'"></textarea></section></div>
                <template v-else><p v-if="!suggestionCount" class="no-change-note">当前没有需要你确认的实质改写。原文已保留，可在“查看 / 编辑完整简历”中修改并导出。</p><section v-for="(section, si) in suggestionSections" :key="si"><h4>{{ section.title }}</h4><div v-for="(item, ii) in section.items" :key="ii" class="agent-edit-item"><div class="suggestion-comparison"><div><small>{{ item.source_kind === 'supplement' ? '来自补充资料 · 建议新增' : '原文' }}</small><p>{{ item.source_text }}</p></div><div><small>建议表达</small><p>{{ item.suggested_text }}</p></div></div><small>{{ item.reason }}</small><div class="agent-downloads"><button @click="decide(item, 'accepted')">采纳建议</button><button @click="decide(item, 'rejected')">{{ item.source_kind === 'supplement' ? '暂不加入' : '保留原文' }}</button></div><textarea v-model="item.final_text" class="agent-resume-editor" :aria-label="section.title + '最终内容' + (ii + 1)" maxlength="2000" rows="3" @input="item.decision = 'custom'"></textarea><small>{{ item.decision === 'pending' ? '待确认' : '已确认' }}</small></div></section></template>
                <section class="facts-opportunity">
                  <span class="agent-kicker">MAKE YOUR EXPERIENCE COUNT</span>
                  <h3>{{ missingPrompts.length ? '这些经历，你也许还没有写进简历' : '还有值得展示的经历吗？' }}</h3>
                  <p>简历不是你的全部。如果有相关技能、课程项目、实习或实践，补充真实细节后可以重新定制；没有就跳过。</p>
                  <ul v-if="missingPrompts.length"><li v-for="hint in missingPrompts" :key="hint">{{ hint }}</li></ul>
                  <label class="agent-editor-label">补充岗位相关经历<textarea v-model="addition" class="agent-resume-editor" maxlength="3000" rows="4" :disabled="working || factsSaving" placeholder="例如：在什么时间、什么项目中，用什么工具完成了什么工作？你负责哪部分？有什么可核实的结果？不必填写没有的经历。"></textarea></label>
                  <small>保存到个人经历库，今后的岗位任务也可使用。原成果保留，重新生成会创建新版本。</small>
                  <p v-if="factsNotice" role="status">{{ factsNotice }}</p>
                  <div class="facts-actions"><button :disabled="working || factsSaving || !addition.trim()" @click="addFacts">{{ factsSaving ? '保存中…' : '只保存经历' }}</button><button :disabled="working || factsSaving" @click="regenerate">保存补充并重新生成 ↗</button><button @click="factsTab = '补充资料'; openResume()">管理全部资料</button></div>
                </section>
                <button class="agent-result-action" :disabled="saving" @click="saveCustom">{{ saving ? '保存中…' : '保存修改' }}</button>
                <div class="agent-downloads"><button :disabled="saving || pending > 0 || !custom.header.name.trim()" @click="download('pdf')">↓ PDF</button><button :disabled="saving || pending > 0 || !custom.header.name.trim()" @click="download('word')">↓ Word</button></div>
              </template><p v-else>定制简历完成后，可在这里确认、编辑并导出。</p>
            </div>
            <div v-else class="agent-result-content"><template v-if="run.preparation"><h3>为下一场面试做好准备</h3><p>{{ run.preparation.summary }}</p><div v-for="(item, index) in run.preparation.items" :key="index" class="agent-prep-item"><span>0{{ index + 1 }}</span><div><h4>{{ item.title }}</h4><p>{{ item.focus }}</p><h4>{{ item.question }}</h4><ul><li v-for="point in item.outline" :key="point">{{ point }}</li></ul></div></div><div class="agent-interview-option"><h4>准备好了，再来一场模拟面试</h4><p>需要你逐题作答，可稍后开始。</p><button @click="startInterview">进入模拟面试 →</button></div></template><p v-else>面试准备方案完成后，会在这里展示。不会自动开始模拟面试。</p></div>
          </template>
        </aside>
      </div>
    </main>
    <dialog ref="resumeDialog" class="agent-resume-dialog" aria-labelledby="resume-dialog-title" @click="($event.target === resumeDialog) && resumeDialog?.close()">
      <div class="resume-dialog-header"><div><span class="agent-kicker">YOUR EXPERIENCE</span><h2 id="resume-dialog-title">我的简历</h2></div><button autofocus aria-label="关闭我的简历" @click="resumeDialog?.close()">×</button></div>
      <div class="agent-result-tabs"><button v-for="item in ['简历文件', '补充资料']" :key="item" :class="{ chosen: factsTab === item }" @click="factsTab = item">{{ item }}</button></div>
      <section v-if="factsTab === '补充资料'" class="facts-library">
        <h3>把一页简历装不下的你，记录下来</h3>
        <p>这里的内容会参与岗位分析、定制简历和面试准备。只写真实情况，不要填身份证、账号密码等敏感信息。</p>
        <label>个人补充 <small>{{ facts.about.length }} / 1500</small><textarea v-model="facts.about" maxlength="1500" rows="3" :disabled="working || factsSaving" placeholder="专业方向、课程背景、证书、语言能力等简历里未写的信息"></textarea></label>
        <label>技能与熟练程度 <small>{{ facts.skills.length }} / 3500</small><textarea v-model="facts.skills" maxlength="3500" rows="4" :disabled="working || factsSaving" placeholder="掌握哪些工具或技能？在哪些场景实际用过？请区分了解、学习中和熟练使用。"></textarea></label>
        <label>项目、实习与实践经历 <small>{{ facts.experiences.length }} / 10000</small><textarea v-model="facts.experiences" maxlength="10000" rows="7" :disabled="working || factsSaving" placeholder="每段经历建议写：时间与名称 → 你的角色 → 做了什么 → 使用的技能 → 真实结果。课程项目、社团、志愿活动也可以。"></textarea></label>
        <p v-if="factsNotice" role="status">{{ factsNotice }}</p>
        <button class="agent-result-action" :disabled="working || factsSaving" @click="saveFacts">{{ factsSaving ? '保存中…' : '保存个人资料' }}</button>
        <p>不会自动更改已有成果。保存后，可回到任务点击“使用最新资料重新生成”。</p>
      </section>
      <template v-else>
      <p class="resume-dialog-description">上传后请检查解析文字，确认它准确地表达了你的真实经历。</p>
      <p v-if="fileError" class="resume-file-error" role="alert">{{ fileError }}</p>
      <label class="resume-upload-zone"><strong>{{ uploading ? '正在处理简历…' : resume ? '替换简历' : '＋ 选择你的简历' }}</strong><span>PDF / DOCX · 最大 10 MB</span><input type="file" accept=".pdf,.docx" :disabled="working || uploading || !ready" @change="pickFile" /></label>
      <template v-if="resume">
        <div class="resume-file-info"><div><strong>{{ fileName }}</strong><small>{{ (resume.size_bytes / 1024).toFixed(1) }} KB · 已私有保存</small></div><button :disabled="working || uploading" @click="clearFile">删除</button></div>
        <iframe v-if="isPdf && fileUrl" :src="fileUrl" title="原始 PDF 简历预览" class="resume-pdf-preview"></iframe>
        <label class="agent-editor-label" for="parsed-resume">检查与修正简历文字</label><textarea id="parsed-resume" class="agent-resume-editor" v-model="parsedText" rows="12" :disabled="working || uploading"></textarea>
        <div class="resume-dialog-actions"><a v-if="fileUrl" :href="fileUrl" :download="fileName">下载原文件</a><button :disabled="working || uploading" @click="confirmResume">确认文字，保存简历 →</button></div>
      </template>
      </template>
      <p class="resume-local-note">同一浏览器可继续使用。更换设备或清除 Cookie 后无法访问原访客资料。</p>
    </dialog>
  </div>
</template>

<style scoped>
.agent-history-list{max-height:42vh;overflow:auto}.agent-history{display:block;width:100%}.task-selected{background:#e1e9dc;border-radius:7px}.global-notice{margin:12px 25px}.agent-job-fields{display:flex;gap:12px;margin:8px 0 18px}.agent-job-fields label{flex:1;min-width:0;font-size:11px;color:#63795d}.agent-job-fields input,.agent-editor-label input{display:block;width:100%;margin-top:8px;border:1px solid #d3decb;background:#fff;border-radius:7px;padding:10px;font:inherit;color:#284c37}.resume-open-button{border:0;background:none;color:#4d7354;font-size:12px;padding:10px 0;text-align:left;overflow-wrap:anywhere}.agent-brief{font-size:13px;color:#78906f;line-height:1.8;white-space:pre-wrap;max-height:170px;overflow:auto}.agent-response p{white-space:pre-wrap;line-height:1.9}.agent-edit-item{padding:14px;background:#fff;border:1px solid #dfe6d8;border-radius:8px;margin:12px 0}.agent-edit-item small{font-size:10px;color:#8b987f}.agent-shell button:disabled{opacity:.45;cursor:default}.agent-live-paper{background:#fff;padding:25px;margin-top:20px;box-shadow:0 4px 18px #14321610}.agent-live-paper h2{font-size:20px}.agent-live-paper h3{font-size:14px;border-bottom:1px solid #bbc9b3}.agent-live-paper p{font-size:11px;white-space:pre-wrap}.mobile-history{display:none}.agent-conversation,.agent-results{overflow-wrap:anywhere}.agent-job-fields{flex-wrap:wrap}@media(max-width:850px){.mobile-history{display:block;width:calc(100% - 40px);margin:10px 20px;background:#f0f4e8;border:1px solid #d3decb;border-radius:6px;padding:8px;color:#345638}.agent-history-list{display:none}}

.agent-resume-dialog{width:min(760px,calc(100vw - 32px));max-height:90vh;overflow:auto;border:1px solid #d8e1d0;border-radius:18px;padding:28px;background:#fafbf7;color:#18332f;box-shadow:0 20px 80px #18332f30}.agent-resume-dialog::backdrop{background:#102c2466;backdrop-filter:blur(3px)}.resume-dialog-header{display:flex;justify-content:space-between;align-items:center}.resume-dialog-header h2{font-size:24px;margin:8px 0}.resume-dialog-header button{border:0;background:#e8eedf;border-radius:50%;width:34px;height:34px;font-size:23px;color:#244b37}.resume-dialog-description,.resume-word-note{font-size:13px;color:#76837b;line-height:1.8}.resume-upload-zone{display:flex;position:relative;align-items:center;flex-direction:column;gap:10px;border:1px dashed #a8bca0;background:#f0f4e9;border-radius:12px;padding:24px;margin:20px 0;cursor:pointer}.resume-upload-zone span{font-size:11px;color:#76837b}.resume-upload-zone input{position:absolute;inset:0;width:100%;height:100%;opacity:0;cursor:pointer}.resume-upload-zone:focus-within{outline:2px solid #518860;outline-offset:3px}.resume-file-info{display:flex;align-items:center;justify-content:space-between;gap:15px;margin-bottom:16px}.resume-file-info strong{font-size:13px;overflow-wrap:anywhere}.resume-file-info small{display:block;color:#76837b;font-size:11px;margin-top:6px}.resume-file-info button{border:0;background:none;color:#986151;white-space:nowrap}.resume-pdf-preview{width:100%;height:420px;border:1px solid #d8e1d0;border-radius:8px;background:white}.resume-dialog-actions{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:18px;font-size:12px;flex-wrap:wrap}.resume-dialog-actions button{border:0;border-radius:8px;background:#244b37;color:white;padding:12px 16px}.resume-dialog-actions a{text-decoration:underline}.resume-local-note{font-size:11px;color:#829077;line-height:1.8;margin:20px 0 0}.resume-file-error{color:#9b4034;background:#faebe6;padding:12px;border-radius:8px;font-size:12px}
.agent-shell{--ink:#18332f;--muted:#76837b;--accent:#286e59;min-height:100vh;background:#fafaf7;color:var(--ink);display:flex;font-family:Inter,'Microsoft YaHei',sans-serif}.agent-shell button{cursor:pointer}.agent-rail{width:232px;flex-shrink:0;padding:32px 20px;display:flex;flex-direction:column;background:#f0f2ed;border-right:1px solid #e2e7de;min-height:100vh}.agent-brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:21px;letter-spacing:1px}.agent-brand small{display:block;font-size:8px;letter-spacing:2px;margin-top:6px;font-weight:500}.agent-mark{display:grid;place-items:center;width:39px;height:44px;background:var(--ink);color:#e4edc8;font-size:30px;border-radius:12px 12px 12px 2px}.agent-new{margin:38px 0 32px;padding:13px 8px;background:var(--ink);color:#fff;border:0;border-radius:9px;font-size:12px}.agent-new span{font-size:18px;margin-right:9px}.agent-nav-label{font-size:10px;color:var(--muted);letter-spacing:2px;margin:0 12px 12px}.agent-nav{display:flex;align-items:center;gap:13px;border:0;background:transparent;text-align:left;padding:14px 12px;border-radius:8px;color:#65716a;font-size:13px}.agent-nav.selected{background:#e1e9dc;color:var(--ink);font-weight:600}.agent-nav i{font-size:8px;font-style:normal;margin-left:auto}.history-label{margin-top:36px}.agent-empty-history{font-size:12px;color:#909a91;line-height:2;margin:2px 12px}.agent-history{border:0;background:none;text-align:left;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding:12px;color:#52675b}.agent-rail-bottom{display:flex;align-items:center;gap:11px;margin-top:auto;padding-top:30px;font-size:12px}.agent-rail-bottom small{display:block;font-size:10px;color:var(--muted);margin-top:6px}.guest-avatar{display:grid;place-items:center;background:#e0e6d9;border-radius:50%;width:35px;height:35px}.agent-main{flex:1;min-width:0}.agent-header{height:79px;border-bottom:1px solid #e8ebe3;display:flex;align-items:center;justify-content:space-between;gap:15px;padding:0 35px;font-size:12px}.agent-header>div{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.agent-breadcrumb{color:#8a938b;margin-right:10px}.agent-preview-badge{white-space:nowrap;font-size:10px;color:#707965;padding:7px 10px;border:1px solid #e0e5d7;border-radius:20px}.agent-columns{display:grid;grid-template-columns:minmax(360px,1.3fr) minmax(330px,1fr);min-height:calc(100vh - 79px)}.agent-conversation{padding:46px 40px 20px;display:flex;flex-direction:column;min-width:0}.agent-welcome{max-width:630px;width:100%;margin:auto}.agent-kicker{font-size:9px;letter-spacing:1.8px;font-weight:600;color:#7b8a75;display:flex;align-items:center;gap:8px}.agent-kicker>span{width:6px;height:6px;background:#719e73;border-radius:50%}.agent-welcome h1{font-size:clamp(32px,3.1vw,52px);font-weight:550;line-height:1.45;letter-spacing:-2px;margin:26px 0 18px}.agent-welcome h1 span{color:#4c8066}.agent-welcome>p{font-size:13px;line-height:1.9;color:var(--muted)}.agent-suggestions{display:flex;flex-direction:column;gap:8px;margin:32px 0}.agent-suggestions button{display:flex;align-items:center;gap:13px;padding:14px 16px;background:#fff;border:1px solid #e6e9e1;border-radius:9px;color:#4d6054;font-size:12px;text-align:left;transition:transform .15s,border-color .15s}.agent-suggestions button:hover{transform:translateX(3px);border-color:#85a58e}.agent-suggestions span{font-size:10px;color:#9aa890}.agent-suggestions b{margin-left:auto;color:#6d8b70}.agent-composer-wrap{margin-top:24px}.agent-composer{border:1px solid #cdd9c9;border-radius:13px;background:#fff;padding:15px 16px 11px;box-shadow:0 6px 22px #243f2e06}.agent-composer textarea{resize:vertical;width:100%;border:0;background:transparent;font:inherit;font-size:13px;color:var(--ink);line-height:1.7;min-height:72px}.agent-composer textarea:focus{outline:none}.agent-composer:focus-within{outline:2px solid #739e7c;outline-offset:2px}.agent-composer-actions{display:flex;justify-content:space-between;align-items:center;gap:10px}.agent-file-button{font-size:11px;cursor:pointer;color:#62735f;max-width:85%;overflow-wrap:anywhere;position:relative}.agent-file-button input{position:absolute;inset:0;opacity:0;width:100%;cursor:pointer}.agent-send{border:0;border-radius:8px;background:var(--ink);color:#fff;width:34px;height:34px;font-size:21px;flex-shrink:0}.agent-send:disabled{opacity:.35;cursor:default}.agent-composer-hint{text-align:center;font-size:9px;color:#929b8d;margin-top:13px}.agent-results{background:#f3f5ee;border-left:1px solid #e6eade;padding:34px 30px}.agent-results-heading{display:flex;align-items:center;justify-content:space-between}.agent-results-heading h2{font-size:19px;font-weight:550;margin:10px 0}.agent-kit-icon{font-size:40px;color:#879771}.agent-paper-scene{height:277px;display:flex;justify-content:center;align-items:center;position:relative;margin:18px 0;background:radial-gradient(ellipse,#dde6cb 0,transparent 68%)}.agent-paper{transform:rotate(-5deg);background:#fff;width:215px;height:237px;border:1px solid #e4e8de;box-shadow:12px 17px 35px #344d2411;padding:21px}.paper-top{display:flex;justify-content:space-between;align-items:center;font-size:10px}.paper-top span{font-size:6px;color:#879780;letter-spacing:1px}.paper-name{font-size:10px;margin:16px 0;color:#4a6154}.agent-paper i{display:block;height:4px;background:#edf0e9;border-radius:2px;margin:7px 0}.agent-paper i:nth-child(odd){width:78%}.paper-section{font-size:7px;border-bottom:1px solid #cad6c6;margin-top:18px;padding-bottom:5px;color:#8a9882}.agent-paper-tag{position:absolute;bottom:14px;right:0;transform:rotate(4deg);background:#e2eacb;border:1px solid #d2ddba;border-radius:6px;font-size:10px;padding:10px 13px}.agent-outcomes{display:grid;gap:22px;margin-top:27px}.agent-outcomes>div{display:flex;gap:13px;align-items:center}.outcome-icon{display:grid;place-items:center;width:37px;height:37px;border-radius:10px;flex-shrink:0;font-size:20px}.peach{background:#f1e4d6;color:#a97850}.mint{background:#deeadf;color:#5d8b68}.lilac{background:#e6e3ee;color:#8572a1}.agent-outcomes h3{font-size:12px;margin:0 0 7px;font-weight:600}.agent-outcomes p{font-size:10px;line-height:1.6;color:#85907f;margin:0}.agent-side-note{margin-top:34px;padding-top:20px;border-top:1px solid #e0e6d8;font-size:12px;line-height:2;color:#586c53}.agent-side-note span{font-size:10px;color:#88927e}.agent-notice{display:flex;justify-content:space-between;gap:8px;background:#eaf0df;padding:10px 12px;border-radius:8px;font-size:11px;line-height:1.7;margin-bottom:12px}.agent-notice button{border:0;background:transparent;font-size:19px;color:var(--ink)}.agent-task-label{font-size:11px;color:#7b8a75;margin-bottom:20px}.agent-task-label span{float:right}.agent-user-message{background:#e6edde;padding:15px 18px;border-radius:13px 13px 2px 13px;font-size:13px;line-height:1.8;margin:10px 0;overflow-wrap:anywhere}.agent-response{display:flex;gap:13px;margin-top:30px}.agent-response-icon{background:#294b3a;color:#fff;border-radius:9px;height:30px;width:30px;display:grid;place-items:center;flex-shrink:0}.agent-response h2{font-size:16px;margin:4px 0 12px}.agent-response p,.agent-delivery p{font-size:12px;color:var(--muted);line-height:1.9}.agent-step-list{margin:20px 0;border:1px solid #e0e5da;border-radius:10px;overflow:hidden}.agent-step-list>div{display:flex;align-items:center;gap:12px;padding:16px 12px;border-bottom:1px solid #e4e9de;font-size:11px}.agent-step-list>div:last-child{border:0}.agent-step-list span{color:#889a76}.agent-step-list small{margin-left:auto;color:#8b9586;font-size:9px}.agent-delivery{display:flex;gap:12px;background:#f0f2e7;padding:16px;border-radius:10px;margin:24px 0}.agent-delivery h3{font-size:13px;margin:0}.agent-delivery button{background:none;border:0;color:#3b7955;padding:0;font-size:11px}.agent-result-tabs{display:flex;border-bottom:1px solid #dce3d3;margin-top:25px}.agent-result-tabs button{flex:1;background:none;border:0;padding:13px 0;color:#7c8974;font-size:12px}.agent-result-tabs .chosen{border-bottom:2px solid #3c7150;color:#254631}.agent-sample-label{font-size:9px;color:#8e987d;margin:14px 0 26px}.agent-result-content h3{font-size:18px;line-height:1.6}.agent-result-content p{font-size:12px;line-height:1.9;color:#7e8a73}.agent-result-content h4{font-size:13px}.agent-insight{background:#e4ebd8;padding:18px;border-radius:10px;margin:24px 0}.agent-insight small{font-size:10px;color:#6e825b}.agent-result-content ul{padding-left:18px;line-height:2.5;font-size:12px;color:#64765c}.agent-result-action,.agent-interview-option button{background:#244b37;color:#fff;border:0;border-radius:7px;padding:12px 15px;font-size:11px}.agent-editor-label{font-size:11px;display:block;margin-top:22px}.agent-resume-editor{width:100%;background:#fff;border:1px solid #d9e0d1;margin:10px 0;padding:17px;border-radius:6px;font:inherit;font-size:12px;line-height:2;color:#354e38;resize:vertical}.agent-downloads{display:flex;gap:10px;margin:14px 0}.agent-downloads button{flex:1;border:1px solid #bccab1;background:#fff;padding:11px;border-radius:7px;color:#3b593b}.agent-result-content>small{font-size:10px;color:#89947d}.agent-prep-item{display:flex;gap:16px;border-bottom:1px solid #e0e5d8;padding:15px 0}.agent-prep-item>span{font-size:12px;color:#90a27c;margin-top:17px}.agent-interview-option{margin-top:25px;background:#e8edde;border-radius:10px;padding:18px}.agent-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}.agent-mobile-tabs{display:none}.agent-shell button:focus-visible,.agent-shell a:focus-visible{outline:2px solid #518860;outline-offset:3px}
@media(min-width:1500px){.agent-conversation{padding:60px 65px 25px}.agent-results{padding:42px 45px}.agent-paper-scene{height:330px}.agent-paper{width:245px;height:275px;padding:28px}.agent-outcomes{gap:30px}}
@media(max-width:1100px){.agent-rail{width:190px;padding:25px 14px}.agent-brand{font-size:18px}.agent-conversation{padding:35px 24px 18px}.agent-results{padding:30px 20px}.agent-columns{grid-template-columns:minmax(310px,1.2fr) minmax(290px,1fr)}.agent-kicker{font-size:8px;letter-spacing:1px}}
@media(max-width:850px){.agent-rail{width:76px;padding:22px 10px;align-items:center}.agent-brand>span:last-child,.agent-nav-label,.agent-nav,.agent-empty-history,.agent-history,.agent-rail-bottom{display:none}.agent-new{font-size:0;padding:10px;width:45px}.agent-new span{font-size:24px;margin:0}.agent-header{padding:0 20px}.agent-columns{grid-template-columns:minmax(280px,1fr) minmax(270px,1fr)}}
@media(max-width:650px){.agent-rail{display:none}.agent-header{height:60px;padding:0 16px;font-size:11px}.agent-breadcrumb{display:none}.agent-preview-badge{font-size:9px}.agent-mobile-tabs{display:flex;gap:20px;padding:0 20px;border-bottom:1px solid #e0e6d9}.agent-mobile-tabs button{padding:13px 8px;border:0;background:none;color:#7f8c75;font-size:12px}.agent-mobile-tabs .chosen{border-bottom:2px solid #3c7150;color:#254631}.agent-columns{display:block;min-height:calc(100vh - 102px)}.agent-conversation{min-height:calc(100vh - 102px);padding:30px 20px 16px}.agent-results{display:none;border:0;min-height:calc(100vh - 102px)}.show-results .agent-results{display:block}.show-results .agent-conversation{display:none}.agent-welcome h1{font-size:37px}.agent-welcome{margin:12px 0}.agent-composer-wrap{margin-top:auto;padding-top:20px}.agent-paper-scene{height:290px}.agent-results-heading h2{font-size:22px}}
@media(prefers-reduced-motion:reduce){.agent-shell *{transition:none!important}}

/* Active tasks use the entire workspace for deliverables, never a tool transcript. */
.has-task.agent-columns{display:flex;flex-direction:column;max-width:1320px;margin:0 auto;min-height:0}
.has-task .agent-conversation{display:block!important;min-height:0;padding:28px 40px 0}
.has-task .agent-task-label{margin-bottom:8px}
.has-task .agent-thread h2{margin:8px 0 14px;font-size:26px}
.has-task .agent-results{display:block!important;border:1px solid #e0e6d8;border-radius:18px;margin:20px 40px 40px;padding:28px 32px}
.has-task .agent-result-content{max-width:1000px;margin:0 auto}
.has-task .agent-result-content p,.has-task .agent-result-content ul{font-size:14px;color:#51624e;line-height:1.9}
.has-task .agent-result-content h4{font-size:16px}
.has-task .agent-result-tabs button{font-size:15px;padding:18px 8px}
.completion-note{font-size:14px;color:#5c775c}
.agent-question{background:#fff5e4;border:1px solid #eddbb7;padding:18px;border-radius:12px}
.agent-question p{white-space:pre-wrap;line-height:1.8}
.analysis-wait{display:flex;align-items:center;gap:20px;margin:24px 40px 0;padding:24px;background:linear-gradient(110deg,#edf4e5,#f4f0e6);border:1px solid #dbe5d2;border-radius:16px;grid-column:1/-1}
.analysis-wait h3{font-size:17px;margin:0 0 8px}.analysis-wait p{font-size:13px;color:#67765d;margin:0;line-height:1.8}
.analysis-wait button{margin-left:auto;flex-shrink:0;background:#fff;border:1px solid #c6d5bc;color:#45633e;padding:10px;border-radius:8px}
.analysis-orbit{display:grid;place-items:center;width:52px;height:52px;flex-shrink:0;font-size:32px;color:#547f55;border:2px solid #c6d7bd;border-top-color:#477c4d;border-radius:50%;animation:orbit 3s linear infinite}
.waiting-dots{animation:breathe 1.5s ease-in-out infinite}
.result-placeholder{padding:48px 16px;text-align:center;color:#6f8065}
.result-placeholder h3{font-size:18px}.result-placeholder p{font-size:14px}
.result-skeleton{max-width:650px;margin:0 auto 28px;text-align:left}
.result-skeleton i{display:block;height:18px;margin:14px 0;border-radius:6px;background:linear-gradient(90deg,#e1e8d9,#f8faf4,#e1e8d9);background-size:200% 100%;animation:shimmer 1.8s linear infinite}
.result-skeleton i:nth-child(2){width:85%}.result-skeleton i:nth-child(3){width:65%}
.suggestion-comparison{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.agent-edit-item{padding:22px}.agent-edit-item small{font-size:12px;color:#68765e}
.suggestion-comparison>div+div{background:#f1f6ea;padding:0 16px;border-radius:8px}
.paper-text-editor{display:block;width:100%;font:inherit;font-size:14px;line-height:1.8;color:#344d3b;border:1px solid transparent;background:transparent;resize:vertical;padding:8px;margin:5px 0}
.paper-text-editor:hover,.paper-text-editor:focus{border-color:#c4d3bd;background:#fbfcf8}
.no-change-note{padding:20px;background:#e6efde;border-radius:10px}
@keyframes orbit{to{transform:rotate(360deg)}}@keyframes breathe{50%{opacity:.2}}@keyframes shimmer{to{background-position:-200% 0}}
@media(max-width:650px){.has-task .agent-conversation{padding:24px 20px 0}.has-task .agent-results{margin:16px 12px;padding:20px 16px}.analysis-wait{margin:16px 12px;flex-wrap:wrap;padding:18px}.analysis-wait>div{flex:1}.analysis-wait button{margin-left:0}.suggestion-comparison{grid-template-columns:1fr;gap:8px}.agent-edit-item{padding:16px}.has-task .agent-result-tabs button{font-size:13px}}
@media(prefers-reduced-motion:reduce){.analysis-orbit,.waiting-dots,.result-skeleton i{animation:none}}

.agent-resume-dialog .resume-upload-zone{min-height:0;height:auto}
.facts-mini{margin-top:28px;padding:18px 14px;border:1px solid #d6dfcc;border-radius:12px;background:linear-gradient(145deg,#e4ebd6,#f7f3e8)}
.facts-mini>span{font-size:8px;letter-spacing:2px;color:#728366}.facts-mini strong{display:block;font-size:15px;margin-top:12px}
.facts-mini p{font-size:11px;line-height:1.9;color:#6d7b62}.facts-mini button,.refresh-facts-button{background:transparent;border:0;color:#376249;font-size:12px;padding:8px 0}
.facts-opportunity{margin:24px 0;padding:24px;border:1px solid #dccfb2;border-radius:14px;background:linear-gradient(115deg,#faf4e7,#f1f5e9)}
.facts-opportunity small{font-size:12px;color:#7c7965}.facts-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}.facts-actions button{border:1px solid #c8d0ba;border-radius:8px;background:white;color:#345a42;padding:12px 16px}.facts-actions button:nth-child(2){background:#2d5641;color:#fff}
.facts-library h3{margin-top:26px}.facts-library p{font-size:13px;color:#6c7c66;line-height:1.8}
.facts-library label{display:block;margin:22px 0 16px;font-size:14px}.facts-library small{float:right;color:#829077;font-size:11px}
.facts-library textarea{display:block;width:100%;margin-top:10px;padding:14px;border:1px solid #d2ddc9;border-radius:10px;background:#fff;resize:vertical;font:inherit;font-size:13px;line-height:1.8;color:#284533}
.agent-welcome{margin:20px auto}.agent-results{background:radial-gradient(ellipse at top right,#e7edd9,transparent 65%),#f3f5ee}
.has-task .agent-results{box-shadow:0 10px 30px #203d2310}
@media(max-width:850px){.facts-mini{display:none}}@media(max-width:650px){.facts-opportunity{padding:16px}.facts-actions button{flex:1}}

.workspace-back{display:block;font-size:11px;color:#738168;margin:-10px 10px 24px;text-decoration:none}
</style>
