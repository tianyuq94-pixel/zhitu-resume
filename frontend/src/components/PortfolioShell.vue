<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { say, repository, email } from '@/content/portfolio'
import '@/portfolio.css'
</script>
<template>
  <div class="portfolio-site">
    <a class="skip-link" href="#portfolio-main">{{ say('Skip to content', '跳至主要内容') }}</a>
    <header class="portfolio-header">
      <RouterLink class="studio-brand" to="/"><span class="studio-monogram">TQ<span>↗</span></span><span>Tianyu Qi<small>{{ say('APPLIED AI PORTFOLIO', 'AI 应用作品集') }}</small></span></RouterLink>
      <nav :aria-label="say('Portfolio navigation', '作品集导航')">
        <RouterLink to="/#projects">{{ say('Projects', '项目') }}</RouterLink>
        <RouterLink to="/#about">{{ say('About & contribution', '关于我与个人贡献') }}</RouterLink>
        <RouterLink to="/demo" class="nav-demo">{{ say('Explore a demo', '查看示例') }} <span aria-hidden="true">↗</span></RouterLink>
      </nav>
    </header>
    <main id="portfolio-main" tabindex="-1"><slot /></main>
    <footer class="portfolio-footer">
      <div><strong>Tianyu Qi</strong><p>{{ say('Personal projects. Working applications. Honest reflection.', '个人项目、可用应用与真实反思。') }}</p></div>
      <div class="footer-links"><a :href="repository" target="_blank" rel="noopener noreferrer">GitHub ↗</a><a :href="`mailto:${email}`">{{ say('Email me', '发送邮件') }} ↗</a><a href="/portfolio/tianyu-qi-project-brief.pdf" target="_blank" rel="noopener">{{ say('Project brief (PDF)', '项目简介（英文 PDF）') }} ↓</a></div>
      <small>{{ say('Product direction, requirements and hands-on review by Tianyu Qi. Implementation developed with AI coding assistance.', '齐天宇负责产品方向、需求与实际试用评审；代码实现使用了 AI 编程辅助。') }}</small>
    </footer>
  </div>
</template>
