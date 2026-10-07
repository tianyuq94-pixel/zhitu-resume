<script setup lang="ts">
import { RouterLink } from 'vue-router'
import PortfolioShell from '@/components/PortfolioShell.vue'
import { projects, contribution, l, say } from '@/content/portfolio'
const entries = [projects[1]!, projects[0]!, projects[2]!]
</script>

<template>
  <PortfolioShell>
    <section class="portfolio-section studio-intro">
      <div>
        <span class="portfolio-eyebrow">{{ say('TIANYU QI · APPLIED AI PORTFOLIO', '齐天宇 · AI 应用作品集') }}</span>
        <h1>{{ say('Get to know me.', '认识我，') }}<br /><em>{{ say('Try what I’ve built.', '也体验我的作品。') }}</em></h1>
        <p>{{ say('I’m a Digital Media Technology undergraduate exploring AI through practical projects. Chat with my AI persona, try a guided career task, or use the CV tools below.', '我是一名数字媒体技术本科生，通过实际项目探索 AI。你可以和我的 AI 分身交流，也可以直接体验下面的求职工具。') }}</p>
      </div>
      <aside class="quick-guide">
        <span class="guide-icon" aria-hidden="true">↗</span>
        <h2>{{ say('First time here?', '第一次来？') }}</h2>
        <p>{{ say('See what the Career Agent produces, without an account or uploading a CV.', '先看一份完整的求职成果示例，无需注册，也不用上传简历。') }}</p>
        <RouterLink to="/demo" class="text-link">{{ say('View a complete example', '查看完整示例') }} →</RouterLink>
      </aside>
    </section>

    <section id="projects" class="portfolio-section project-entry-section" aria-labelledby="projects-title">
      <div class="portfolio-heading"><h2 id="projects-title">{{ say('What would you like to do?', '你想先做什么？') }}</h2><p>{{ say('Choose an experience. No registration needed.', '选择一个入口，直接体验，无需注册。') }}</p></div>
      <div class="project-cards">
        <article v-for="project in entries" :key="project.id" class="project-card" :class="project.accent">
          <div class="project-card-copy">
            <span class="entry-purpose">{{ l(project.purpose) }}</span>
            <h3>{{ l(project.name) }}</h3>
            <p>{{ l(project.summary) }}</p>
          </div>
          <div class="card-links">
            <RouterLink :to="project.route" class="portfolio-button">{{ l(project.enter) }} <span aria-hidden="true">→</span></RouterLink>
            <RouterLink :to="'/projects/'+project.id" class="case-link">{{ say('How it was built', '了解项目与实现') }} ↗</RouterLink>
          </div>
          <RouterLink :to="project.route" class="project-card-image" :aria-label="l(project.enter)">
            <img :src="l(project.image)" width="1280" height="900" :alt="l(project.name)+say(' — actual interface', ' — 真实界面')" />
          </RouterLink>
        </article>
      </div>
    </section>

    <section id="about" class="portfolio-section about-section" aria-labelledby="about-title">
      <div class="about-intro">
        <span class="portfolio-eyebrow">{{ say('ABOUT ME', '关于我') }}</span>
        <h2 id="about-title">{{ say('From curiosity to working projects.', '把对 AI 的好奇，变成可用的项目。') }}</h2>
        <p class="study-line">{{ say('Tianyu Qi · Fujian Normal University', '齐天宇 · 福建师范大学') }}<br />{{ say('Digital Media Technology · Expected graduation 2027', '数字媒体技术 · 预计 2027 年毕业') }}</p>
        <p>{{ say('Trying new AI tools and shaping these projects has made me want to study AI and computing more systematically. I plan to pursue a master’s and move into AI-related work in technology or internet companies.', '尝试新的 AI 工具、推进这些项目，让我希望更系统地学习 AI 与计算机知识。我计划继续攻读硕士，未来进入科技或互联网公司的 AI 相关岗位。') }}</p>
      </div>
      <div class="contribution-summary">
        <h3>{{ say('My role in these projects', '我在项目中做了什么') }}</h3>
        <ol><li v-for="(item,index) in contribution" :key="index"><span>0{{ index+1 }}</span><div><strong>{{ l(item.title) }}</strong><p>{{ l(item.text) }}</p></div></li></ol>
        <p class="ownership-note">{{ say('I directed the product and reviewed its behaviour; AI coding tools assisted with much of the implementation. Each case study explains the decisions, mechanisms and limitations.', '我主导产品方向并检查实际体验，AI 编程工具辅助完成了大量代码实现。各项目介绍中说明了具体决策、技术机制与局限。') }}</p>
      </div>
    </section>
  </PortfolioShell>
</template>

<style scoped>
.studio-intro{display:grid;grid-template-columns:1fr 300px;gap:65px;align-items:center;padding-block:45px 38px}
.studio-intro h1{font-size:clamp(34px,3.4vw,48px);line-height:1.16;letter-spacing:-1.5px;font-weight:600;margin:0 0 18px}.studio-intro h1 em{font-style:normal;color:#628344}.studio-intro>div>p{max-width:620px;font-size:15px;line-height:1.85;color:var(--soft);margin:0}.studio-intro .portfolio-eyebrow{margin-bottom:15px;letter-spacing:1.5px}
.quick-guide{position:relative;border-left:2px solid #c6d6b5;padding:8px 0 8px 26px}.guide-icon{width:30px;height:30px;display:grid;place-items:center;background:#e3ebd8;color:#40613b;border-radius:9px;margin-bottom:13px}.quick-guide h2{font-size:17px;font-weight:600;margin:0 0 8px}.quick-guide p{font-size:13px;color:var(--soft);margin:0 0 15px}.quick-guide .text-link{font-weight:600}
.project-entry-section{padding-top:8px;padding-bottom:48px;scroll-margin-top:20px}.portfolio-heading{margin-bottom:20px;align-items:center}.portfolio-heading h2{font-size:23px;letter-spacing:-.5px}.portfolio-heading p{font-size:12px}.project-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}.project-card{display:flex;flex-direction:column;border:1px solid #d3dfcf;border-radius:15px;background:#fffefa;overflow:hidden;min-width:0;box-shadow:0 6px 20px #263c3205;transition:box-shadow .2s,transform .2s}.project-card:hover{transform:translateY(-3px);box-shadow:0 12px 25px #263c3210}.project-card-copy{padding:23px 23px 18px}.entry-purpose{font-size:12px;color:#5b6c4c;font-weight:600}.project-card h3{font-size:25px;font-weight:600;line-height:1.3;margin:9px 0 12px}.project-card p{font-size:13px;color:var(--soft);line-height:1.8;margin:0;min-height:70px}.project-card-image{display:block;background:#e0ead7;padding:15px 22px;border-block:1px solid #dce5d5}.project-card.sand .project-card-image{background:#ece5d9}.project-card.blue .project-card-image{background:#e2eaee}.project-card-image img{display:block;width:100%;height:auto;border:1px solid #c3cfbf;border-radius:5px;box-shadow:0 4px 10px #253c3010}.card-links{padding:20px 23px;display:flex;flex-direction:column;align-items:center;gap:14px;margin-top:auto}.card-links .portfolio-button{width:100%;justify-content:space-between}.case-link{font-size:12px;color:var(--soft)}.case-link:hover{text-decoration:underline;text-underline-offset:4px}
.about-section{display:grid;grid-template-columns:1fr 1fr;gap:70px;border-top:1px solid var(--border);padding-block:42px}.about-intro h2{font-size:26px;line-height:1.35;font-weight:600;letter-spacing:-.5px;margin-bottom:18px}.about-intro p{font-size:14px;color:var(--soft);line-height:1.9}.about-intro .study-line{font-size:12px;color:#6a745f;margin-bottom:18px}.contribution-summary h3{font-size:16px;font-weight:600;margin:0 0 17px}.contribution-summary ol{list-style:none;padding:0;margin:0}.contribution-summary li{display:flex;gap:15px;margin-bottom:18px}.contribution-summary li>span{font-size:11px;color:#718459;line-height:2}.contribution-summary strong{font-size:13px;font-weight:600}.contribution-summary li p{font-size:12px;line-height:1.8;color:var(--soft);margin:6px 0 0}.ownership-note{font-size:11px;line-height:1.85;color:#5a6d50;border-top:1px solid var(--border);padding-top:16px;margin:0}
@media(max-width:1000px){.studio-intro{gap:35px;grid-template-columns:1fr 245px}.project-card-copy,.card-links{padding:19px}.project-card h3{font-size:22px}.project-card p{min-height:93px}.about-section{gap:35px}}
@media(max-width:700px){.studio-intro{grid-template-columns:1fr;gap:23px;padding-block:30px}.studio-intro h1{font-size:36px}.quick-guide{padding:16px 18px;border:1px solid #d5dfc9;border-radius:10px;background:#edf2e5}.guide-icon{display:none}.quick-guide h2{font-size:15px}.quick-guide p{font-size:12px;margin-bottom:10px}.portfolio-heading{gap:8px;align-items:flex-start}.portfolio-heading h2{font-size:23px}.project-entry-section{padding-top:5px}.project-cards{grid-template-columns:1fr;gap:20px}.project-card{display:grid;grid-template-columns:1fr 35%;align-items:center}.project-card-copy{padding:22px 15px 15px 22px}.project-card p{min-height:0}.project-card-image{margin:15px 18px 0 0;padding:7px;border:0;border-radius:7px}.card-links{grid-column:1/-1;flex-direction:row;justify-content:space-between;padding:8px 22px 22px;gap:14px}.card-links .portfolio-button{width:auto;min-width:150px}.card-links .case-link{font-size:11px}.about-section{grid-template-columns:1fr;gap:25px;padding-block:32px}.about-intro h2{font-size:24px}.project-card:hover{transform:none}}
@media(max-width:380px){.project-card{display:flex}.project-card-copy{padding:22px}.project-card-image{display:none}.card-links{width:100%;flex-wrap:wrap}.card-links .portfolio-button{min-width:0}.studio-intro h1{font-size:32px}}
.project-card-image{border-bottom:0}.card-links{margin-top:0;padding-top:0}
@media(max-width:700px){.project-card-copy{grid-row:1;grid-column:1}.project-card-image{grid-row:1;grid-column:2}.card-links{grid-row:2;grid-column:1/-1}}
</style>
