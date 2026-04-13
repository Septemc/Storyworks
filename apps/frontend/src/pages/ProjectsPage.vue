<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">项目</p>
        <h2>项目管理</h2>
      </div>
      <button class="button" type="button" @click="refresh">刷新</button>
    </header>

    <article class="card form-card">
      <h3>新建项目</h3>
      <form class="form" @submit.prevent="submit">
        <label>
          <span>项目标题</span>
          <input v-model.trim="draft.title" required maxlength="120" />
        </label>
        <label>
          <span>项目简介</span>
          <textarea v-model.trim="draft.summary" maxlength="500" rows="4" />
        </label>
        <button class="button" type="submit" :disabled="submitting">
          {{ submitting ? '保存中...' : '创建项目' }}
        </button>
      </form>
    </article>

    <article class="card">
      <h3>已保存项目</h3>
      <p v-if="loading">正在加载项目...</p>
      <p v-else-if="projects.length === 0">暂无项目。</p>
      <ul v-else class="list">
        <li v-for="project in projects" :key="project.id">
          <strong>{{ project.title }}</strong>
          <span>{{ project.summary || '暂无简介。' }}</span>
        </li>
      </ul>
      <p v-if="error" class="error">{{ error }}</p>
    </article>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import type { ProjectCreate, ProjectRead } from '@/schemas/project'
import { resolveErrorMessage } from '@/services/http'
import { createProject, fetchProjects } from '@/services/projects'

const loading = ref(true)
const submitting = ref(false)
const error = ref<string | null>(null)
const projects = ref<ProjectRead[]>([])
const draft = reactive<ProjectCreate>({
  title: '',
  summary: '',
})

async function loadProjects() {
  loading.value = true
  error.value = null

  try {
    projects.value = await fetchProjects()
  } catch (err) {
    error.value = resolveErrorMessage(err, '加载项目列表失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

async function submit() {
  submitting.value = true
  error.value = null

  try {
    await createProject({ ...draft })
    draft.title = ''
    draft.summary = ''
    await loadProjects()
  } catch (err) {
    error.value = resolveErrorMessage(err, '创建项目失败，请稍后重试。')
  } finally {
    submitting.value = false
  }
}

function refresh() {
  void loadProjects()
}

onMounted(() => {
  void loadProjects()
})
</script>
