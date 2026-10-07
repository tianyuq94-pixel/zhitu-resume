<script setup lang="ts">
import { t } from '@/i18n'
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
        <span><strong>{{ t("Zhitu CV") }}</strong><small>{{ t("CAREER RESUME") }}</small></span>
      </RouterLink>
      <nav :aria-label="t('Account access')">
        <template v-if="authStore.user">
          <RouterLink class="public-login" to="/app">{{ t("Go to workspace") }}</RouterLink>
        </template>
        <template v-else>
          <RouterLink class="public-login" to="/login">{{ t("Log in") }}</RouterLink>
          <RouterLink class="public-register" to="/register">{{ t("Start for free") }}</RouterLink>
        </template>
      </nav>
    </header>

    <main class="landing-main">
      <section class="landing-hero">
        <div class="landing-copy">
          <span class="landing-pill">{{ t("An AI assistant for the real job application process") }}</span>
          <h1>{{ t("Make job preparation") }}<br /><em>{{ t("More direction") }}</em></h1>
          <p>{{ t("Starting from your real CV, complete CV diagnosis, role customisation, fit analysis and role mock interviews.") }}</p>
          <div class="landing-actions">
            <RouterLink class="landing-primary" :to="authStore.user ? '/app' : '/register'">
              {{ t(authStore.user ? 'Go to workspace' : 'Create a free account') }}
            </RouterLink>
            <a class="landing-secondary" href="#features">{{ t("View core features") }}</a>
          </div>
          <div class="landing-trust">
            <span>{{ t("✓ No fabricated experience") }}</span>
            <span>{{ t("✓ CV data stays private") }}</span>
            <span>{{ t("✓ Free trial for new users") }}</span>
          </div>
        </div>

        <div class="landing-demo" aria-hidden="true">
          <div class="demo-window">
            <div class="demo-top"><i></i><i></i><i></i><span>{{ t("Job match analysis") }}</span></div>
            <div class="demo-content">
              <div class="demo-score"><strong>82</strong><span>{{ t("Job match score") }}</span></div>
              <div class="demo-lines">
                <span></span><span></span><span></span>
              </div>
              <div class="demo-tags"><b>{{ t("Vue") }}</b><b>{{ t("JavaScript") }}</b><b>{{ t("Web project") }}</b></div>
            </div>
          </div>
          <div class="floating-note note-one">{{ t("Recommended applications") }}</div>
          <div class="floating-note note-two">{{ t("3 strengths identified") }}</div>
        </div>
      </section>

      <section id="features" class="landing-features">
        <div class="landing-section-title">
          <span>{{ t("COMPLETE WORKFLOW") }}</span>
          <h2>{{ t("Complete all preparation around one real application") }}</h2>
        </div>
        <div class="landing-feature-grid">
          <article><b>01</b><h3>{{ t("My CV") }}</h3><p>{{ t("Upload your master CV, confirm the parsed content and receive evidence-based diagnostic suggestions.") }}</p></article>
          <article><b>02</b><h3>{{ t("Job-tailored CV") }}</h3><p>{{ t("Reorganise existing experience according to the target job to generate a separate targeted version.") }}</p></article>
          <article><b>03</b><h3>{{ t("Job match") }}</h3><p>{{ t("Identify matching skills, key gaps and whether it is worth applying.") }}</p></article>
          <article><b>04</b><h3>{{ t("AI Interview") }}</h3><p>{{ t("Take a five-question mock interview for the role and get per-question feedback plus an overall report.") }}</p></article>
        </div>
      </section>
    </main>
  </div>
</template>
