<script setup lang="ts">
import { t, locale } from '@/i18n'
import { computed, ref, nextTick, onMounted, watch } from 'vue'
import { say } from '@/content/portfolio'
import { RouterLink } from 'vue-router'
import { api, getApiErrorMessage } from '@/services/api'

type Message = { role: 'user' | 'assistant'; content: string }
const profile = ref({ name: 'Tianyu Qi', headline: 'Digital Media Technology · AI Application Practice', welcome: '', links: [] as {label:string;url:string}[] })
const messages = ref<Message[]>([]), input = ref(''), busy = ref(false), ready = ref(false), error = ref('')
const thread = ref<HTMLElement|null>(null), showCard = ref(false)
const topics = computed(() => [say('Tell me about yourself.', '简单介绍一下你自己。'), say('What did you contribute to these projects?', '这些项目中，你做了哪些工作？'), say('How does the Career Agent work?', '求职智能体是怎样工作的？'), say('Why do you want to study AI and computing?', '为什么想继续学习 AI 与计算机？'), say('What are the limitations of your projects?', '你的项目有哪些局限？'), say('What would you improve next?', '接下来你想改进什么？')])
async function scrollDown() { await nextTick(); thread.value?.scrollTo({top:thread.value.scrollHeight,behavior:'auto'}) }
async function initialize() {
  error.value = ''
  try {
    profile.value = (await api.get('/persona/profile')).data
    await api.post('/auth/guest')
    if (!messages.value.length) messages.value = [{role:'assistant',content:profile.value.welcome}]
    ready.value = true
  } catch(e) { error.value = getApiErrorMessage(e,'Unable to connect for now. Please try again') }
}
async function reply() {
  if (busy.value || !ready.value) return
  busy.value = true; error.value = ''; await scrollDown()
  try {
    const result = await api.post('/persona/chat', { messages: messages.value.slice(-12).map(m=>({role:m.role,content:m.content})) }, {timeout:150000})
    messages.value.push({role:'assistant',content:result.data.answer})
  } catch(e) { error.value = getApiErrorMessage(e,'No reply for now. Please try again') }
  finally { busy.value = false; await scrollDown() }
}
async function send(text = input.value) {
  if (!text.trim() || text.length > 1500 || busy.value || !ready.value || messages.value.at(-1)?.role === 'user') return
  messages.value.push({role:'user',content:text.trim()}); input.value=''; await reply()
}
function clear() { if (!busy.value) { messages.value=[{role:'assistant',content:profile.value.welcome}];error.value='';input.value='' } }
function onEnter(event:KeyboardEvent) { if (event.key==='Enter' && !event.shiftKey && !event.isComposing) {event.preventDefault(); void send()} }
onMounted(initialize)
watch(locale, async () => {
  try {
    profile.value = (await api.get('/persona/profile')).data
    if (messages.value.length === 1 && messages.value[0]?.role === 'assistant') messages.value[0].content = profile.value.welcome
  } catch { /* Keep the current conversation intact if profile refresh fails. */ }
})
</script>

<template>
  <div class="persona-shell">
    <nav class="chat-dock"><RouterLink to="/" :aria-label="t('Return to the three-entry homepage')">⌂</RouterLink><span class="dock-selected">☏</span><RouterLink to="/agent" :aria-label="t('Career Agent')">✧</RouterLink><RouterLink to="/app" :aria-label="t('Zhitu CV')">▤</RouterLink><small>{{ t("TY") }}</small></nav>
    <aside class="chat-sidebar">
      <div class="sidebar-title">{{ t("Chat") }} <span>01</span></div><div class="contact-active"><div class="chat-avatar">{{ t("TQ") }}</div><div><strong>{{ t(profile.name) }}</strong><small>{{ t("AI Persona · Public information") }}</small></div></div>
      <div class="topic-heading">{{ t("You can start like this") }}</div><button v-for="topic in topics" :key="topic" :disabled="busy || !ready || messages.at(-1)?.role === 'user'" class="topic-button" @click="send(topic)">{{ t(topic) }} <span>↗</span></button>
      <div class="sidebar-note">{{ t("Not a static CV,") }}<br />{{ t("It is a conversation about me.") }}<small>{{ t("The AI is not the person and does not make commitments on their behalf.") }}</small></div>
      <RouterLink to="/" class="back-workspace">{{ t("← Back to the studio") }}</RouterLink>
    </aside>
    <main class="chat-main">
      <header class="chat-header"><div class="chat-avatar mobile-avatar">{{ t("TQ") }}</div><div><h1>{{ t(profile.name) }} <span>{{ t("AI Persona") }}</span></h1><p>{{ t("Based on information confirmed by me · not my real-time replies") }}</p></div><button @click="showCard=!showCard">{{ t(showCard?'Collapse profile':'Personal details') }}</button></header>
      <aside v-if="showCard" class="chat-profile"><strong>{{ t(profile.name) }}</strong><p>{{ t(profile.headline) }}</p><a v-for="link in profile.links" :key="link.url" :href="link.url" target="_blank" rel="noopener noreferrer">{{ t(link.label) }} ↗</a><small>{{ t("Contact details can be asked for directly in the chat.") }}</small></aside>
      <div ref="thread" class="chat-thread" role="log" :aria-label="t('Conversation with Tianyu Qi\'s AI Persona')" aria-live="polite">
        <div class="chat-date">{{ t("Get to know me here") }}</div>
        <div v-for="(message,index) in messages" :key="index" class="chat-row" :class="{outgoing:message.role==='user'}">
          <div class="bubble-avatar">{{ t(message.role==='user'?'You':'TQ') }}</div><div class="bubble-stack"><small>{{ t(message.role==='user'?'You':'Tianyu Qi · AI Persona') }}</small><div class="chat-bubble">{{ t(message.content) }}</div></div>
        </div>
        <div v-if="busy" class="chat-row"><div class="bubble-avatar">{{ t("TQ") }}</div><div class="typing-bubble" role="status"><i></i><i></i><i></i><span>{{ t("Preparing a reply") }}</span></div></div>
        <div v-if="error" class="chat-error" role="alert">{{ t(error) }}<button :disabled="busy" @click="ready ? reply() : initialize()">{{ t("Retry") }}</button></div>
        <div v-if="messages.length===1" class="chat-starters"><button v-for="topic in topics.slice(0,3)" :key="topic" :disabled="!ready || busy" @click="send(topic)">{{ t(topic) }}</button></div>
      </div>
      <form class="chat-composer" @submit.prevent="send()"><div class="composer-tools"><span>{{ t("If there is anything you want to know, just ask me.") }}</span><button type="button" :disabled="busy" @click="clear">{{ t("New conversation") }}</button></div><label class="chat-sr" for="persona-message">{{ t("Enter message") }}</label><textarea id="persona-message" v-model="input" maxlength="1500" rows="3" :placeholder="t('For example: what problems did you encounter during this project?')" :disabled="busy || !ready || messages.at(-1)?.role==='user'" @keydown="onEnter"></textarea><div class="composer-bottom"><small>{{ t("Enter to send · Shift + Enter for a new line") }}　{{ t(input.length) }} / 1500</small><button type="submit" :disabled="!input.trim() || busy || !ready || messages.at(-1)?.role==='user'">{{ t(busy?'Replying…':'Send ↑') }}</button></div><p>{{ t("Messages are used to generate replies, please do not send sensitive information. This page's conversation is not retained after refreshing the page.") }}</p></form>
      <RouterLink to="/" class="mobile-home">{{ t("← Back to the three entry points") }}</RouterLink>
    </main>
  </div>
</template>

<style scoped>
.persona-shell{display:flex;height:100dvh;min-height:540px;background:#f0f2ee;color:#303a32;font-family:Inter,'Microsoft YaHei',sans-serif}
.chat-dock{width:66px;flex-shrink:0;background:#263d32;display:flex;align-items:center;flex-direction:column;gap:25px;padding:26px 0;color:#c1d2bd}
.chat-dock a,.chat-dock>span{width:38px;height:38px;display:grid;place-items:center;font-size:24px;text-decoration:none;color:inherit}.dock-selected{background:#ffffff16;border-radius:10px}.chat-dock small{margin-top:auto;font-size:10px;letter-spacing:2px}
.chat-sidebar{width:264px;flex-shrink:0;background:#e9ece5;border-right:1px solid #dce2d6;padding:31px 18px;display:flex;flex-direction:column}.sidebar-title{font-size:20px;font-weight:600;padding:0 8px 28px;display:flex;justify-content:space-between}.sidebar-title>span{font-size:11px;color:#939c89}
.contact-active{display:flex;align-items:center;gap:13px;background:#dce5d5;border-radius:11px;padding:15px 12px}.chat-avatar{display:grid;place-items:center;background:#8a7964;color:#fff9ed;width:46px;height:46px;border-radius:14px;font-size:22px;flex-shrink:0}.contact-active strong{font-size:14px}.contact-active small{display:block;font-size:10px;color:#76826c;margin-top:7px}
.topic-heading{font-size:10px;letter-spacing:2px;color:#86917f;padding:34px 8px 16px}.topic-button{text-align:left;display:flex;justify-content:space-between;gap:8px;width:100%;padding:14px 9px;background:none;border:0;border-bottom:1px solid #dfe4d8;color:#69795f;font:inherit;font-size:11px;line-height:1.7;cursor:pointer}.topic-button:hover{background:#e0e7d8;border-radius:7px}
.sidebar-note{margin-top:auto;padding:28px 8px;font-size:14px;line-height:2;color:#64785c}.sidebar-note small{display:block;font-size:10px;color:#939d89;margin-top:15px}.back-workspace{padding:10px;color:#758469;font-size:11px;text-decoration:none}
.chat-main{display:flex;flex:1;min-width:0;padding:0;flex-direction:column;position:relative;background:radial-gradient(ellipse at 80% 20%,#eef1e7,transparent 65%),#f5f6f1}
.chat-header{padding:22px 34px;display:flex;align-items:center;gap:12px;border-bottom:1px solid #e2e7dc;background:#f7f8f3}.chat-header h1{font-size:18px;margin:0;font-weight:600}.chat-header h1 span{font-size:9px;font-weight:400;background:#e4eadc;padding:4px 7px;border-radius:4px;margin-left:8px;color:#6a7f5c}.chat-header p{font-size:10px;color:#949d8b;margin:9px 0 0}.chat-header>button{margin-left:auto;background:none;border:1px solid #d9e2d1;padding:8px 12px;border-radius:7px;font-size:11px;color:#6d7f61;cursor:pointer}
.mobile-avatar{display:none}.chat-thread{flex:1;overflow-y:auto;overscroll-behavior:contain;padding:22px 34px 32px}.chat-date{text-align:center;font-size:10px;color:#a0a893;margin-bottom:30px}
.chat-row{display:flex;gap:12px;margin:0 0 24px;align-items:flex-start}.bubble-avatar{width:36px;height:36px;flex-shrink:0;background:#b6ad98;color:#fff;display:grid;place-items:center;border-radius:10px;font-size:16px}.bubble-stack{max-width:min(76%,720px)}.bubble-stack>small{font-size:10px;color:#919c88;display:block;margin:0 0 7px 2px}
.chat-bubble{padding:15px 19px;border-radius:3px 14px 14px 14px;white-space:pre-wrap;overflow-wrap:anywhere;background:#fff;border:1px solid #e4e8de;box-shadow:0 2px 5px #22372103;font-size:14px;line-height:1.95}
.outgoing{flex-direction:row-reverse}.outgoing .bubble-avatar{background:#6c9069}.outgoing .bubble-stack>small{text-align:right}.outgoing .chat-bubble{background:#dbeacc;border-color:#cfe0c0;border-radius:14px 3px 14px 14px}
.chat-sources{font-size:10px;color:#949f89;margin:8px 4px;line-height:1.8}.chat-sources summary{cursor:pointer}.typing-bubble{background:white;border:1px solid #e1e7db;padding:14px 18px;border-radius:4px 14px 14px 14px;display:flex;align-items:center;gap:5px}.typing-bubble i{width:5px;height:5px;border-radius:50%;background:#87a16f;animation:typing 1s infinite}.typing-bubble i:nth-child(2){animation-delay:.15s}.typing-bubble i:nth-child(3){animation-delay:.3s}.typing-bubble span{font-size:10px;color:#98a089;margin-left:9px}
.chat-starters{display:flex;gap:8px;flex-wrap:wrap;margin-left:48px}.chat-starters button{border:1px solid #dce5d3;background:#eff4e7;color:#71835e;border-radius:20px;padding:9px 12px;font-size:11px;cursor:pointer}
.chat-error{padding:14px;background:#f6e9dd;border-radius:8px;font-size:12px;color:#986749}.chat-error button{margin-left:12px;background:none;border:0;color:inherit;text-decoration:underline}
.chat-composer{border-top:1px solid #e0e5d9;background:#fafbf7;padding:15px 30px 8px}.composer-tools{display:flex;justify-content:space-between;font-size:10px;color:#9ba58e}.composer-tools button{border:0;background:none;color:#8b9a7e;font-size:10px;cursor:pointer}
.chat-composer textarea{display:block;width:100%;font:inherit;font-size:14px;line-height:1.8;resize:none;border:0;background:transparent;padding:13px 0 5px;outline:none;color:#3d5038}.chat-composer:focus-within{box-shadow:inset 0 2px #a8bc98}.composer-bottom{display:flex;align-items:center;justify-content:space-between}.composer-bottom small{font-size:9px;color:#a3ac97}.composer-bottom button{background:#557e4e;color:#fff;padding:10px 23px;border:0;border-radius:7px;font-size:12px;cursor:pointer}.chat-composer>p{font-size:9px;color:#a6ad9f;margin:9px 0 0}
.persona-shell button:disabled{opacity:.45;cursor:default}.persona-shell button:focus-visible,.persona-shell a:focus-visible{outline:2px solid #779b65;outline-offset:3px}
.chat-profile{position:absolute;right:24px;top:85px;width:270px;background:#fffef8;box-shadow:0 15px 35px #2c452820;padding:25px;border:1px solid #dee4d6;border-radius:14px;z-index:2}.chat-profile p{font-size:12px;line-height:1.8;color:#859177}.chat-profile a{display:block;font-size:12px;line-height:2.5;color:#527c49}.chat-profile small{display:block;font-size:10px;margin-top:15px;color:#9a9e91}
.chat-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}.mobile-home{display:none}
@keyframes typing{50%{transform:translateY(-3px);opacity:.4}}@media(prefers-reduced-motion:reduce){.typing-bubble i{animation:none}}
@media(min-width:1500px){.chat-thread{padding-left:6vw;padding-right:6vw}.chat-composer{padding-left:6vw;padding-right:6vw}.chat-sidebar{width:300px;padding:34px 25px}}
@media(max-width:850px){.chat-sidebar{width:210px;padding:25px 12px}.chat-dock{width:52px}.chat-header{padding:20px}.chat-thread{padding:20px}.bubble-stack{max-width:84%}.chat-bubble{font-size:13px}}
@media(max-width:650px){.chat-sidebar,.chat-dock{display:none}.mobile-avatar{display:grid;width:37px;height:37px;font-size:18px}.chat-header{padding:15px}.chat-header h1{font-size:16px}.chat-thread{padding:18px 13px}.chat-row{gap:8px}.bubble-avatar{width:29px;height:29px;font-size:14px}.bubble-stack{max-width:86%}.chat-bubble{padding:12px 14px}.chat-composer{padding:13px 16px 8px}.composer-bottom small{font-size:8px}.mobile-home{display:block;text-align:center;color:#879a78;background:#fafbf7;font-size:10px;padding:8px;text-decoration:none}.chat-starters{margin-left:37px}.chat-profile{right:12px;top:80px}.persona-shell{min-height:450px}}
</style>
