<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">阶段二</p>
        <h2>世界书工坊</h2>
      </div>
      <div class="actions">
        <button class="button button-secondary" type="button" @click="prepareNewEntry">新建条目</button>
        <button class="button" type="button" @click="refresh">刷新</button>
      </div>
    </header>

    <article class="card">
      <div class="project-toolbar">
        <label class="toolbar-field">
          <span>所属项目</span>
          <select v-model.number="selectedProjectId" @change="onProjectChange">
            <option :value="0">请选择项目</option>
            <option v-for="project in projects" :key="project.id" :value="project.id">
              {{ project.title }}
            </option>
          </select>
        </label>

        <p v-if="projects.length === 0" class="muted">
          还没有项目，请先在项目页面创建项目，再添加世界书条目。
        </p>
      </div>
    </article>

    <div class="worldbook-layout">
      <article class="card">
        <div class="section-header">
          <h3>条目列表</h3>
          <label class="toolbar-field toolbar-field-compact">
            <span>分类</span>
            <select v-model="categoryFilter">
              <option value="">全部</option>
              <option v-for="category in worldbookCategories" :key="category" :value="category">
                {{ category }}
              </option>
            </select>
          </label>
        </div>

        <label class="toolbar-field">
          <span>搜索</span>
          <input v-model.trim="searchKeyword" placeholder="按标题搜索..." />
        </label>

        <p v-if="loadingEntries">正在加载条目...</p>
        <p v-else-if="selectedProjectId === 0" class="muted">请先选择项目，再查看世界书条目。</p>
        <p v-else-if="filteredEntries.length === 0" class="muted">暂无世界书条目。</p>
        <ul v-else class="entry-list">
          <li
            v-for="entry in filteredEntries"
            :key="entry.id"
            :class="['entry-item', { active: editingEntryId === entry.id }]"
          >
            <button class="entry-button" type="button" @click="editEntry(entry)">
              <strong>{{ entry.title }}</strong>
              <span>{{ entry.category }} · {{ entry.summary || '暂无简介。' }}</span>
            </button>
          </li>
        </ul>
      </article>

      <div class="stack">
        <article class="card">
          <div class="section-header">
            <h3>{{ editingEntryId ? '编辑条目' : '创建条目' }}</h3>
            <div class="actions">
              <button class="button button-secondary" type="button" @click="runGenerate" :disabled="generating">
                {{ generating ? '生成中...' : '生成草稿' }}
              </button>
              <button class="button" type="button" @click="submit" :disabled="saving || selectedProjectId === 0">
                {{ saving ? '保存中...' : editingEntryId ? '保存修改' : '创建条目' }}
              </button>
            </div>
          </div>

          <form class="form" @submit.prevent="submit">
            <div class="grid two-col">
              <label>
                <span>分类</span>
                <select v-model="draft.category">
                  <option v-for="category in worldbookCategories" :key="category" :value="category">
                    {{ category }}
                  </option>
                </select>
              </label>

              <label>
                <span>状态</span>
                <select v-model="draft.status">
                  <option v-for="option in statusOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </label>
            </div>

            <label>
              <span>标题</span>
              <input v-model.trim="draft.title" maxlength="120" required />
            </label>

            <label>
              <span>摘要</span>
              <textarea v-model.trim="draft.summary" rows="3" maxlength="500" />
            </label>

            <label>
              <span>关键词</span>
              <input v-model.trim="keywordsText" placeholder="使用中文逗号或英文逗号分隔关键词" />
            </label>

            <div class="grid two-col">
              <label>
                <span>定义</span>
                <textarea v-model.trim="draft.content.definition" rows="4" />
              </label>
              <label>
                <span>起源</span>
                <textarea v-model.trim="draft.content.origin" rows="4" />
              </label>
              <label>
                <span>结构</span>
                <textarea v-model.trim="draft.content.structure" rows="4" />
              </label>
              <label>
                <span>规则</span>
                <textarea v-model.trim="draft.content.rules" rows="4" />
              </label>
            </div>

            <label>
              <span>影响</span>
              <textarea v-model.trim="draft.content.impact" rows="4" />
            </label>

            <label>
              <span>备注</span>
              <textarea v-model.trim="draft.notes" rows="3" />
            </label>
          </form>

          <p v-if="error" class="error">{{ error }}</p>
        </article>

        <article class="card">
          <div class="section-header">
            <h3>草稿助手</h3>
            <p class="muted">输入一句概念，快速生成结构化世界书草稿。</p>
          </div>

          <form class="form" @submit.prevent="runGenerate">
            <label>
              <span>创意描述</span>
              <textarea
                v-model.trim="generateIdea"
                rows="4"
                placeholder="例如：战后联邦通过七城议会共同管理北境。"
              />
            </label>
            <button class="button button-secondary" type="submit" :disabled="generating">
              {{ generating ? '生成中...' : '生成到表单' }}
            </button>
          </form>
        </article>

        <article v-if="editingEntryId" class="card">
          <div class="section-header">
            <h3>导出</h3>
            <div class="actions">
              <button class="button button-secondary" type="button" @click="download('json')">导出 JSON</button>
              <button class="button button-secondary" type="button" @click="download('markdown')">
                导出 Markdown
              </button>
              <button class="button button-danger" type="button" @click="removeEntry">删除条目</button>
            </div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'

import type { ProjectRead } from '@/schemas/project'
import {
  createEmptyWorldbookDraft,
  worldbookCategories,
  type WorldbookCreate,
  type WorldbookRead,
} from '@/schemas/worldbook'
import { resolveErrorMessage } from '@/services/http'
import { fetchProjects } from '@/services/projects'
import {
  createWorldbookEntry,
  deleteWorldbookEntry,
  exportWorldbookEntry,
  fetchWorldbookEntries,
  generateWorldbookDraft,
  updateWorldbookEntry,
} from '@/services/worldbook'

const statusOptions = [
  { value: 'draft', label: '草稿' },
  { value: 'ready', label: '待定稿' },
  { value: 'final', label: '已定稿' },
  { value: 'archived', label: '已归档' },
]

const projects = ref<ProjectRead[]>([])
const entries = ref<WorldbookRead[]>([])
const loadingEntries = ref(false)
const saving = ref(false)
const generating = ref(false)
const error = ref<string | null>(null)
const selectedProjectId = ref(0)
const editingEntryId = ref<number | null>(null)
const searchKeyword = ref('')
const categoryFilter = ref('')
const generateIdea = ref('')

const draft = reactive<WorldbookCreate>(createEmptyWorldbookDraft())
const keywordsText = ref('')

const filteredEntries = computed(() => {
  return entries.value.filter((entry) => {
    const matchesCategory = !categoryFilter.value || entry.category === categoryFilter.value
    const matchesKeyword =
      !searchKeyword.value || entry.title.toLowerCase().includes(searchKeyword.value.toLowerCase())
    return matchesCategory && matchesKeyword
  })
})

watch(keywordsText, (value) => {
  draft.keywords = value
    .split(/[,，]/)
    .map((item) => item.trim())
    .filter(Boolean)
})

async function loadProjects() {
  projects.value = await fetchProjects()
  if (projects.value.length > 0 && selectedProjectId.value === 0) {
    selectedProjectId.value = projects.value[0].id
  }
}

async function loadEntries() {
  if (selectedProjectId.value === 0) {
    entries.value = []
    return
  }

  loadingEntries.value = true
  error.value = null

  try {
    entries.value = await fetchWorldbookEntries(selectedProjectId.value)
  } catch (err) {
    error.value = resolveErrorMessage(err, '加载世界书条目失败，请稍后重试。')
  } finally {
    loadingEntries.value = false
  }
}

function hydrateDraft(entry: WorldbookRead) {
  draft.category = entry.category
  draft.title = entry.title
  draft.summary = entry.summary
  draft.keywords = [...entry.keywords]
  draft.content.definition = entry.content.definition
  draft.content.origin = entry.content.origin
  draft.content.structure = entry.content.structure
  draft.content.rules = entry.content.rules
  draft.content.impact = entry.content.impact
  draft.notes = entry.notes
  draft.status = entry.status
  keywordsText.value = entry.keywords.join('，')
}

function prepareNewEntry() {
  editingEntryId.value = null
  Object.assign(draft, createEmptyWorldbookDraft())
  keywordsText.value = ''
  generateIdea.value = ''
  error.value = null
}

function editEntry(entry: WorldbookRead) {
  editingEntryId.value = entry.id
  hydrateDraft(entry)
  error.value = null
}

async function submit() {
  if (selectedProjectId.value === 0) {
    error.value = '请先选择项目。'
    return
  }

  saving.value = true
  error.value = null

  try {
    if (editingEntryId.value) {
      const updated = await updateWorldbookEntry(editingEntryId.value, { ...draft })
      hydrateDraft(updated)
    } else {
      const created = await createWorldbookEntry(selectedProjectId.value, { ...draft })
      editingEntryId.value = created.id
      hydrateDraft(created)
    }

    await loadEntries()
  } catch (err) {
    error.value = resolveErrorMessage(err, '保存世界书条目失败，请稍后重试。')
  } finally {
    saving.value = false
  }
}

async function runGenerate() {
  if (!draft.title.trim()) {
    error.value = '请先输入标题，再生成草稿。'
    return
  }

  generating.value = true
  error.value = null

  try {
    const generated = await generateWorldbookDraft({
      category: draft.category,
      title: draft.title,
      idea: generateIdea.value,
      mode: draft.status,
    })

    draft.summary = generated.summary
    draft.keywords = [...generated.keywords]
    draft.content.definition = generated.content.definition
    draft.content.origin = generated.content.origin
    draft.content.structure = generated.content.structure
    draft.content.rules = generated.content.rules
    draft.content.impact = generated.content.impact
    draft.notes = generated.notes
    draft.status = generated.status
    keywordsText.value = generated.keywords.join('，')
  } catch (err) {
    error.value = resolveErrorMessage(err, '生成世界书草稿失败，请稍后重试。')
  } finally {
    generating.value = false
  }
}

async function removeEntry() {
  if (!editingEntryId.value) {
    return
  }

  if (!window.confirm('确定要删除这条世界书条目吗？')) {
    return
  }

  try {
    await deleteWorldbookEntry(editingEntryId.value)
    prepareNewEntry()
    await loadEntries()
  } catch (err) {
    error.value = resolveErrorMessage(err, '删除世界书条目失败，请稍后重试。')
  }
}

async function download(format: 'json' | 'markdown') {
  if (!editingEntryId.value) {
    return
  }

  try {
    const exported = await exportWorldbookEntry(editingEntryId.value, format)
    const content =
      format === 'json'
        ? JSON.stringify(exported, null, 2)
        : typeof exported === 'string'
          ? exported
          : JSON.stringify(exported, null, 2)

    const blob = new Blob([content], {
      type: format === 'json' ? 'application/json' : 'text/markdown;charset=utf-8',
    })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${draft.title || '世界书条目'}.${format === 'json' ? 'json' : 'md'}`
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    error.value = resolveErrorMessage(err, '导出世界书条目失败，请稍后重试。')
  }
}

function onProjectChange() {
  prepareNewEntry()
  void loadEntries()
}

function refresh() {
  void loadEntries()
}

onMounted(async () => {
  try {
    await loadProjects()
    await loadEntries()
  } catch (err) {
    error.value = resolveErrorMessage(err, '初始化世界书页面失败，请稍后重试。')
  }
})
</script>
