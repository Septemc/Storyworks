<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">总览</p>
        <h2>Storyworks 工作台</h2>
      </div>
      <button class="button" type="button" @click="reload">刷新状态</button>
    </header>

    <div class="grid">
      <article class="card">
        <h3>后端状态</h3>
        <p v-if="loading">正在检测后端服务...</p>
        <template v-else-if="health">
          <p><strong>状态：</strong>{{ formatHealthStatus(health.status) }}</p>
          <p><strong>应用：</strong>{{ health.app_name }}</p>
          <p><strong>环境：</strong>{{ formatEnvironment(health.environment) }}</p>
        </template>
        <p v-else class="error">{{ error ?? '后端暂不可用。' }}</p>
      </article>

      <article class="card">
        <h3>模块能力</h3>
        <ul class="list">
          <li>项目管理已支持项目创建与基础登记。</li>
          <li>世界书已支持条目创建、结构化草稿生成、导出与删除。</li>
          <li>人物卡已支持模板驱动编辑、双视图生成与导出。</li>
          <li>剧本已支持结构化大纲编辑、草稿生成与导出。</li>
          <li>预设已支持风格参数配置、测试预览与导出。</li>
        </ul>
      </article>

      <article class="card">
        <h3>当前定位</h3>
        <ul class="list">
          <li>本项目作为完全独立的辅助生成器存在，不依赖主项目架构。</li>
          <li>核心资产聚焦世界书、人物卡、剧本与预设四大模块。</li>
          <li>第六阶段重点为中文化、整合体验、发布准备与文档补齐。</li>
        </ul>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { resolveErrorMessage } from '@/services/http'
import { getHealth, type HealthResponse } from '@/services/system'

const loading = ref(true)
const health = ref<HealthResponse | null>(null)
const error = ref<string | null>(null)

function formatHealthStatus(status: string) {
  if (status === 'ok') {
    return '正常'
  }
  return status
}

function formatEnvironment(environment: string) {
  if (environment === 'development') {
    return '开发环境'
  }
  if (environment === 'production') {
    return '生产环境'
  }
  if (environment === 'test') {
    return '测试环境'
  }
  return environment
}

async function loadHealth() {
  loading.value = true
  error.value = null

  try {
    health.value = await getHealth()
  } catch (err) {
    error.value = resolveErrorMessage(err, '获取后端状态失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

function reload() {
  void loadHealth()
}

onMounted(() => {
  void loadHealth()
})
</script>
