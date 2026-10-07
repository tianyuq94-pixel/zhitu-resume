<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { say, repository } from '@/content/portfolio'
import '@/portfolio.css'
</script>
<template>
  <div class="portfolio-site">
    <a class="skip-link" href="#portfolio-main">{{ say('Skip to content', '跳至主要内容') }}</a>
    <header class="portfolio-header">
      <RouterLink class="studio-brand" to="/"><span class="studio-monogram">{{ say('TQ', '齐') }}<span>↗</span></span><span>{{ say('Tianyu Qi', '齐天宇') }}<small>{{ say('AI PROJECTS', 'AI 项目作品集') }}</small></span></RouterLink>
      <nav :aria-label="say('Portfolio navigation', '作品集导航')">
        <RouterLink to="/#projects">{{ say('Projects', '体验项目') }}</RouterLink>
        <RouterLink to="/#about">{{ say('About me', '关于我') }}</RouterLink>
      </nav>
    </header>
    <main id="portfolio-main" tabindex="-1"><slot /></main>
    <footer class="portfolio-footer">
      <div><strong>{{ say('Tianyu Qi', '齐天宇') }}</strong><p>{{ say('Personal projects · Developed with AI assistance', '个人项目 · 使用 AI 辅助开发') }}</p></div>
      <div class="footer-links"><a :href="repository" target="_blank" rel="noopener noreferrer">{{ say('Source on GitHub', 'GitHub 源码') }} ↗</a><a href="/portfolio/tianyu-qi-project-brief.pdf" target="_blank" rel="noopener">{{ say('Project brief (English PDF)', '项目简介（英文 PDF）') }} ↓</a></div>
    </footer>
  </div>
</template>
