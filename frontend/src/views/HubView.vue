<script setup lang="ts">
import { t } from '@/i18n'
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="hub">
    <header class="hub-header"><RouterLink to="/" class="hub-brand"><span>{{ t("TQ") }}</span>{{ t("Tianyu's AI Studio") }}</RouterLink><small>{{ t("One creator. Three ways to explore.") }}</small></header>
    <main>
      <div class="hub-intro"><span class="hub-eyebrow">{{ t("HELLO, NICE TO MEET YOU.") }}</span><h1>{{ t("Meet the person.") }}<br />{{ t("Explore the possibilities") }}<span>.</span></h1><p>{{ t("I'm Tianyu Qi, a Digital Media Technology undergraduate exploring practical AI applications.") }}<br />{{ t("Get to know me through conversation, or try the tools I've shaped with AI-assisted development.") }}</p></div>
      <div class="hub-portals">
        <RouterLink to="/me" class="hub-portal portal-persona">
          <div class="portal-number">01 <span>{{ t("ABOUT ME") }}</span><b>↗</b></div>
          <div class="portal-scene"><span class="persona-avatar">{{ t("TQ") }}<small>{{ t("AI") }}</small></span><div class="mini-message">{{ t("Hello, which of my projects would you like to explore first?") }}<i></i></div></div>
          <div class="portal-copy"><span class="portal-label">{{ t("GET TO KNOW ME") }}</span><h2>{{ t("AI Persona") }}</h2><p>{{ t("A conversation about my experience,") }}<br />{{ t("projects and product decisions.") }}</p><span class="portal-enter">{{ t("Start a conversation") }} <b>→</b></span></div>
        </RouterLink>
        <RouterLink to="/agent" class="hub-portal portal-agent">
          <div class="portal-number">02 <span>{{ t("YOUR NEXT CHAPTER") }}</span><b>↗</b></div>
          <div class="portal-scene agent-scene"><div class="goal-note"><small>{{ t("Next goal") }}</small><strong>{{ t("Target roles") }}</strong><span>{{ t("◎ Analyse　 ▤ CV　 ✧ Prepare") }}</span></div><i>{{ t("Prepared for you ✧") }}</i></div>
          <div class="portal-copy"><span class="portal-label">{{ t("TURN A GOAL INTO ACTION") }}</span><h2>{{ t("Career Agent") }}</h2><p>{{ t("From your CV and a target role to analysis,") }}<br />{{ t("a tailored CV and interview preparation.") }}</p><span class="portal-enter">{{ t("Start a career task") }} <b>→</b></span></div>
        </RouterLink>
        <RouterLink to="/app" class="hub-portal portal-tools">
          <div class="portal-number">03 <span>{{ t("CAREER TOOLKIT") }}</span><b>↗</b></div>
          <div class="portal-scene tools-scene"><span>▤<small>{{ t("My CV") }}</small></span><span>◎<small>{{ t("Job match") }}</small></span><span>✧<small>{{ t("Mock interview") }}</small></span></div>
          <div class="portal-copy"><span class="portal-label">{{ t("YOUR CAREER TOOLKIT") }}</span><h2>{{ t("Zhitu CV") }}</h2><p>{{ t("CV review, job matching and mock interviews.") }}<br />{{ t("Use each tool at your own pace.") }}</p><span class="portal-enter">{{ t("Open the workspace") }} <b>→</b></span></div>
        </RouterLink>
      </div>
    </main>
    <footer><span>{{ t("CREATED BY TIANYU QI · DEVELOPED WITH AI ASSISTANCE") }}</span><p>{{ t("The AI Persona is not me replying live.") }}</p></footer>
  </div>
</template>

<style scoped>
.hub{min-height:100vh;background:#f8f7f3;color:#28352f;font-family:Inter,'Microsoft YaHei',sans-serif;padding:0 5vw}
.hub-header{max-width:1320px;margin:auto;display:flex;align-items:center;justify-content:space-between;padding:30px 0;border-bottom:1px solid #e2e3da}
.hub-brand{display:flex;align-items:center;gap:12px;text-decoration:none;font-size:17px;font-weight:700;color:inherit}.hub-brand>span{display:grid;place-items:center;width:36px;height:39px;background:#2c4437;color:#f5f3e9;border-radius:10px 10px 10px 2px}
.hub-header small{color:#7f877b;font-size:12px}.hub main{max-width:1320px;margin:auto;padding:0}.hub-intro{padding:40px 0 24px}.hub-eyebrow{font-size:10px;letter-spacing:2.8px;color:#8b927d}
.hub-intro h1{font-size:clamp(32px,3.4vw,52px);letter-spacing:-1px;font-weight:600;margin:20px 0 18px}.hub-intro h1>span{color:#9aa87d}.hub-intro p{font-size:14px;line-height:1.9;color:#7b8377}.hub-mobile-break{display:none}
.hub-portals{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}.hub-portal{position:relative;overflow:hidden;display:flex;flex-direction:column;min-height:440px;padding:26px 30px;border:1px solid #dddccf;border-radius:22px;text-decoration:none;color:inherit;transition:transform .2s,box-shadow .2s}
.hub-portal:hover{transform:translateY(-5px);box-shadow:0 20px 45px #293e2a12}.hub-portal:focus-visible{outline:3px solid #6e966e;outline-offset:5px}
.portal-persona{background:#f0e8de}.portal-agent{background:#e8eddf}.portal-tools{background:#e7eaf0}.portal-number{display:flex;align-items:center;gap:12px;font-size:12px;color:#797f70}.portal-number span{font-size:8px;letter-spacing:1.5px}.portal-number b{margin-left:auto;font-size:21px}
.portal-scene{height:156px;display:flex;align-items:center;justify-content:center;position:relative}.persona-avatar{width:70px;height:77px;display:grid;place-items:center;border-radius:25px;background:#7b6855;color:#fff9ec;font-size:30px;position:relative;transform:rotate(-7deg)}
.persona-avatar small{position:absolute;right:-8px;bottom:-6px;font-size:10px;background:#fff7e9;color:#6c624f;border:3px solid #f0e8de;padding:6px;border-radius:50%;transform:rotate(7deg)}.mini-message{max-width:175px;padding:17px;margin-left:15px;border-radius:14px 14px 14px 3px;background:#fffaf1;font-size:12px;line-height:1.8;box-shadow:0 7px 20px #84705710}
.goal-note{background:#fcfdf8;padding:20px 25px;transform:rotate(-5deg);box-shadow:0 8px 18px #4a6f3210;border-radius:8px}.goal-note small{font-size:10px;color:#849276;display:block}.goal-note strong{font-size:21px;display:block;margin:10px 0}.goal-note span{font-size:10px;color:#6a825c}.agent-scene>i{position:absolute;right:0;bottom:18px;background:#d3dfbd;padding:9px;border-radius:5px;transform:rotate(5deg);font-size:10px;font-style:normal}
.tools-scene{gap:10px}.tools-scene>span{display:grid;place-items:center;width:78px;height:82px;border-radius:15px;background:#f4f6fb;color:#6f7c99;font-size:26px;box-shadow:0 7px 15px #4d57700a}.tools-scene>span:nth-child(2){transform:translateY(-10px)}.tools-scene small{font-size:9px;margin-top:-5px}
.portal-copy{margin-top:auto}.portal-label{font-size:10px;letter-spacing:2px;color:#7e8676}.portal-copy h2{font-size:26px;font-weight:600;margin:12px 0}.portal-copy p{font-size:13px;color:#707e71;line-height:1.9}.portal-enter{margin-top:23px;border-top:1px solid #334f3020;padding-top:18px;display:flex;justify-content:space-between;font-size:12px;font-weight:600}.portal-enter b{font-size:18px}
.hub footer{max-width:1320px;margin:34px auto 0;padding:16px 0 25px;display:flex;justify-content:space-between;align-items:center;color:#8b9184;font-size:10px}.hub footer>span{letter-spacing:1.6px}
@media(max-width:800px){.hub-portals{grid-template-columns:1fr;gap:18px}.hub-portal{min-height:300px;display:grid;grid-template-columns:1.2fr 1fr;padding:24px}.portal-number{grid-column:1/-1}.portal-scene{grid-column:2;grid-row:2;height:190px}.portal-copy{grid-column:1;grid-row:2}.hub-intro{padding-top:32px}.hub-header small{display:none}.mini-message{display:none}.tools-scene{gap:4px}.tools-scene>span{width:46px;height:65px}.agent-scene>i{bottom:12px}.hub footer{display:block;line-height:1.8}.goal-note{padding:14px}.portal-copy h2{font-size:23px}}
@media(max-width:430px){.hub-mobile-break{display:block}.hub-intro h1{line-height:1.5}.portal-scene{transform:scale(.85)}.hub-portal{padding:20px}.portal-copy p{font-size:12px}.portal-copy h2{font-size:21px}}
@media(prefers-reduced-motion:reduce){.hub-portal{transition:none}}
</style>
