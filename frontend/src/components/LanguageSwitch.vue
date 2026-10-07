<script setup lang="ts">
import { locale, setLanguage } from '@/i18n'
</script>

<template>
  <div class="language-toolbar">
    <div class="language-switch" role="group" aria-label="Website language / 网站语言">
      <button type="button" lang="en-GB" :aria-pressed="locale === 'en'" :class="{ selected: locale === 'en' }" @click="setLanguage('en')">English</button>
      <button type="button" lang="zh-CN" :aria-pressed="locale === 'zh'" :class="{ selected: locale === 'zh' }" @click="setLanguage('zh')">中文</button>
    </div>
  </div>
</template>

<style scoped>
.language-toolbar{height:42px;display:flex;justify-content:flex-end;align-items:center;padding:5px clamp(16px,3vw,40px);background:#f8f7f3;border-bottom:1px solid #e5e6de;position:relative;z-index:30}
.language-switch{display:flex;gap:2px;border:1px solid #d5ddcf;background:#fff;border-radius:8px;padding:2px}
.language-switch button{border:0;background:transparent;color:#63745f;font:inherit;font-size:11px;padding:4px 12px;border-radius:5px;cursor:pointer;line-height:1.4}
.language-switch .selected{background:#304f3d;color:white}
.language-switch button:focus-visible{outline:2px solid #608e68;outline-offset:2px}
</style>
