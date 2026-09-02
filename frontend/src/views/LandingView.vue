<script setup lang="ts">
import { RouterLink } from 'vue-router'

import BrandLogo from '@/components/BrandLogo.vue'
import { useAuthStore } from '@/stores'

const authStore = useAuthStore()
</script>

<template>
  <div class="public-page">
    <header class="public-header">
      <RouterLink class="public-brand" to="/">
        <BrandLogo />
        <span><strong>职途简历</strong><small>CAREER RESUME</small></span>
      </RouterLink>
      <nav aria-label="账户入口">
        <template v-if="authStore.user">
          <RouterLink class="public-login" to="/app">进入工作台</RouterLink>
        </template>
        <template v-else>
          <RouterLink class="public-login" to="/login">登录</RouterLink>
          <RouterLink class="public-register" to="/register">免费开始使用</RouterLink>
        </template>
      </nav>
    </header>

    <main class="landing-main">
      <section class="landing-hero">
        <div class="landing-copy">
          <span class="landing-pill">面向真实求职流程的 AI 助手</span>
          <h1>让求职准备<br /><em>更有方向</em></h1>
          <p>从你的真实简历出发，完成简历诊断、岗位定制、匹配分析与岗位模拟面试。</p>
          <div class="landing-actions">
            <RouterLink class="landing-primary" :to="authStore.user ? '/app' : '/register'">
              {{ authStore.user ? '进入工作台' : '创建免费账户' }}
            </RouterLink>
            <a class="landing-secondary" href="#features">查看核心功能</a>
          </div>
          <div class="landing-trust">
            <span>✓ 不编造经历</span>
            <span>✓ 简历数据私有</span>
            <span>✓ 新用户可免费体验</span>
          </div>
        </div>

        <div class="landing-demo" aria-hidden="true">
          <div class="demo-window">
            <div class="demo-top"><i></i><i></i><i></i><span>岗位匹配分析</span></div>
            <div class="demo-content">
              <div class="demo-score"><strong>82</strong><span>岗位匹配度</span></div>
              <div class="demo-lines">
                <span></span><span></span><span></span>
              </div>
              <div class="demo-tags"><b>Vue</b><b>JavaScript</b><b>Web 项目</b></div>
            </div>
          </div>
          <div class="floating-note note-one">推荐投递</div>
          <div class="floating-note note-two">3 项优势已识别</div>
        </div>
      </section>

      <section id="features" class="landing-features">
        <div class="landing-section-title">
          <span>COMPLETE WORKFLOW</span>
          <h2>围绕一次真实投递，完成全部准备</h2>
        </div>
        <div class="landing-feature-grid">
          <article><b>01</b><h3>我的简历</h3><p>上传主简历，确认解析内容，并获得有依据的诊断建议。</p></article>
          <article><b>02</b><h3>岗位定制简历</h3><p>根据目标岗位重组已有经历，生成独立的针对性版本。</p></article>
          <article><b>03</b><h3>岗位匹配</h3><p>识别匹配能力、关键缺口和是否值得投递。</p></article>
          <article><b>04</b><h3>AI 面试</h3><p>输入岗位后进行五题模拟，获得逐题点评和综合报告。</p></article>
        </div>
      </section>
    </main>
  </div>
</template>
