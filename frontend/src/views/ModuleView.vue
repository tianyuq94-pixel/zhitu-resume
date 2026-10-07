<script setup lang="ts">
import { t } from '@/i18n'
defineProps<{
  eyebrow: string
  title: string
  description: string
  nextStep: string
}>()
</script>

<template>
  <section class="module-page">
    <div class="module-intro">
      <span class="eyebrow">{{ t(eyebrow) }}</span>
      <h2>{{ t(title) }}</h2>
      <p>{{ t(description) }}</p>
    </div>

    <div class="empty-state">
      <div class="empty-icon" aria-hidden="true">✦</div>
      <h3>{{ t("Feature development starting soon") }}</h3>
      <p>{{ t(nextStep) }}</p>
      <span>{{ t("For now, keep the project foundation stable first, then complete each module step by step as planned.") }}</span>
    </div>
  </section>
</template>
