<script setup lang="ts">
import InterviewView from './InterviewView.vue'
import { useRoute, RouterLink } from 'vue-router'
const route = useRoute()
</script>
<template><div class="interview-workspace"><header><RouterLink :to="route.query.agentRun ? '/agent?task=' + route.query.agentRun : '/agent'">← 返回求职工作台</RouterLink><span>职途简历 · 可选模拟面试</span></header><InterviewView /></div></template>
<style scoped>.interview-workspace{min-height:100vh;background:#f7f8f2;padding:25px max(20px,calc((100vw - 1100px)/2));color:#284a38}.interview-workspace header{display:flex;justify-content:space-between;gap:20px;margin-bottom:30px;font-size:13px}.interview-workspace header span{color:#85937a}</style>
