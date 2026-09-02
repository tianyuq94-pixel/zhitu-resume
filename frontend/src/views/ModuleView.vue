<script setup lang="ts">
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
      <span class="eyebrow">{{ eyebrow }}</span>
      <h2>{{ title }}</h2>
      <p>{{ description }}</p>
    </div>

    <div class="empty-state">
      <div class="empty-icon" aria-hidden="true">✦</div>
      <h3>功能即将开始开发</h3>
      <p>{{ nextStep }}</p>
      <span>当前先保证项目基础稳定，再按规划逐步完成每个模块。</span>
    </div>
  </section>
</template>

