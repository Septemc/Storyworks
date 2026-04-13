<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">阶段四</p>
        <h2>剧本工坊</h2>
      </div>
      <div class="actions">
        <button class="button button-secondary" type="button" @click="prepareNewScript">新建剧本</button>
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
      </div>
    </article>

    <div class="worldbook-layout">
      <article class="card">
        <div class="section-header">
          <h3>剧本列表</h3>
          <p class="muted">{{ scripts.length }} 条已保存</p>
        </div>

        <label class="toolbar-field">
          <span>搜索</span>
          <input v-model.trim="searchKeyword" placeholder="按剧本标题搜索..." />
        </label>

        <p v-if="loadingScripts">正在加载剧本...</p>
        <p v-else-if="selectedProjectId === 0" class="muted">请先选择项目，再查看剧本。</p>
        <p v-else-if="filteredScripts.length === 0" class="muted">暂无剧本。</p>
        <ul v-else class="entry-list">
          <li
            v-for="script in filteredScripts"
            :key="script.id"
            :class="['entry-item', { active: editingScriptId === script.id }]"
          >
            <button class="entry-button" type="button" @click="editScript(script)">
              <strong>{{ script.title }}</strong>
              <span>{{ script.script_type }} · {{ script.summary || '暂无简介。' }}</span>
            </button>
          </li>
        </ul>
      </article>

      <div class="stack">
        <article class="card">
          <div class="section-header">
            <div>
              <h3>{{ editingScriptId ? '编辑剧本' : '创建剧本' }}</h3>
              <p class="muted">用于编辑大纲、章节、场景卡与剧情约束的结构化表单。</p>
            </div>
            <div class="actions">
              <button class="button button-secondary" type="button" @click="generateDraft" :disabled="generating">
                {{ generating ? '生成中...' : '生成草稿' }}
              </button>
              <button class="button" type="button" @click="submit" :disabled="saving || selectedProjectId === 0">
                {{ saving ? '保存中...' : editingScriptId ? '保存修改' : '创建剧本' }}
              </button>
            </div>
          </div>

          <form class="form" @submit.prevent="submit">
            <div class="grid two-col">
              <label>
                <span>标题</span>
                <input v-model.trim="draft.title" maxlength="160" required />
              </label>
              <label>
                <span>类型</span>
                <select v-model="draft.script_type">
                  <option value="主线">主线</option>
                  <option value="支线">支线</option>
                  <option value="角色线">角色线</option>
                  <option value="事件线">事件线</option>
                </select>
              </label>
              <label>
                <span>主题</span>
                <input v-model.trim="draft.theme" maxlength="160" />
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
              <span>故事概念</span>
              <textarea
                v-model.trim="conceptText"
                rows="4"
                placeholder="例如：主角被卷入边境危机，并逐步揭开议会与旧王朝残党的关系。"
              />
            </label>

            <label>
              <span>项目背景</span>
              <textarea v-model.trim="projectContext" rows="3" />
            </label>

            <label>
              <span>摘要</span>
              <textarea v-model.trim="draft.summary" rows="4" maxlength="1000" />
            </label>

            <div class="grid two-col">
              <label>
                <span>核心冲突</span>
                <textarea v-model.trim="draft.core_conflict" rows="4" maxlength="500" />
              </label>
              <label>
                <span>故事阶段</span>
                <textarea v-model.trim="draft.story_stage" rows="4" maxlength="160" />
              </label>
            </div>

            <label>
              <span>主要角色（JSON）</span>
              <textarea v-model="mainCharactersText" rows="6" />
            </label>

            <label>
              <span>关键节点（JSON）</span>
              <textarea v-model="majorNodesText" rows="6" />
            </label>

            <label>
              <span>分支思路（JSON）</span>
              <textarea v-model="branchIdeasText" rows="6" />
            </label>

            <label>
              <span>章节结构（JSON）</span>
              <textarea v-model="chaptersText" rows="8" />
            </label>

            <label>
              <span>场景卡（JSON）</span>
              <textarea v-model="sceneCardsText" rows="10" />
            </label>

            <label>
              <span>约束条件（JSON）</span>
              <textarea v-model="constraintsText" rows="8" />
            </label>

            <label>
              <span>禁止内容</span>
              <textarea v-model.trim="draft.forbidden_content" rows="4" />
            </label>

            <label>
              <span>备注</span>
              <textarea v-model.trim="draft.notes" rows="3" />
            </label>
          </form>

          <p v-if="error" class="error">{{ error }}</p>
        </article>

        <article v-if="editingScriptId" class="card">
          <div class="section-header">
            <h3>导出</h3>
            <div class="actions">
              <button class="button button-secondary" type="button" @click="download('json')">导出 JSON</button>
              <button class="button button-secondary" type="button" @click="download('markdown')">
                导出 Markdown
              </button>
              <button class="button button-danger" type="button" @click="removeScript">删除剧本</button>
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
import { createEmptyScriptDraft, type ScriptCreate, type ScriptRead } from '@/schemas/script'
import { resolveErrorMessage } from '@/services/http'
import { fetchProjects } from '@/services/projects'
import {
  createScript,
  deleteScript,
  exportScript,
  fetchScripts,
  generateScriptDraft,
  updateScript,
} from '@/services/scripts'

const statusOptions = [
  { value: 'draft', label: '草稿' },
  { value: 'ready', label: '待定稿' },
  { value: 'final', label: '已定稿' },
  { value: 'archived', label: '已归档' },
]

const projects = ref<ProjectRead[]>([])
const scripts = ref<ScriptRead[]>([])
const selectedProjectId = ref(0)
const loadingScripts = ref(false)
const saving = ref(false)
const generating = ref(false)
const error = ref<string | null>(null)
const editingScriptId = ref<number | null>(null)
const searchKeyword = ref('')
const conceptText = ref('')
const projectContext = ref('')

const draft = reactive<ScriptCreate>(createEmptyScriptDraft())
const mainCharactersText = ref('[]')
const majorNodesText = ref('[]')
const branchIdeasText = ref('[]')
const chaptersText = ref('[]')
const sceneCardsText = ref('[]')
const constraintsText = ref('{}')

const filteredScripts = computed(() => {
  return scripts.value.filter((script) => {
    return !searchKeyword.value || script.title.toLowerCase().includes(searchKeyword.value.toLowerCase())
  })
})

function syncTextFromDraft() {
  mainCharactersText.value = JSON.stringify(draft.main_characters, null, 2)
  majorNodesText.value = JSON.stringify(draft.major_nodes, null, 2)
  branchIdeasText.value = JSON.stringify(draft.branch_ideas, null, 2)
  chaptersText.value = JSON.stringify(draft.chapters, null, 2)
  sceneCardsText.value = JSON.stringify(draft.scene_cards, null, 2)
  constraintsText.value = JSON.stringify(draft.constraints, null, 2)
}

watch(
  [mainCharactersText, majorNodesText, branchIdeasText, chaptersText, sceneCardsText, constraintsText],
  () => {
    try {
      draft.main_characters = JSON.parse(mainCharactersText.value || '[]')
      draft.major_nodes = JSON.parse(majorNodesText.value || '[]')
      draft.branch_ideas = JSON.parse(branchIdeasText.value || '[]')
      draft.chapters = JSON.parse(chaptersText.value || '[]')
      draft.scene_cards = JSON.parse(sceneCardsText.value || '[]')
      draft.constraints = JSON.parse(constraintsText.value || '{}')
    } catch {
      // 编辑 JSON 时允许临时存在无效内容，保存时再统一校验。
    }
  },
)

async function loadProjects() {
  projects.value = await fetchProjects()
  if (projects.value.length > 0 && selectedProjectId.value === 0) {
    selectedProjectId.value = projects.value[0].id
  }
}

async function loadScripts() {
  if (selectedProjectId.value === 0) {
    scripts.value = []
    return
  }

  loadingScripts.value = true
  error.value = null

  try {
    scripts.value = await fetchScripts(selectedProjectId.value)
  } catch (err) {
    error.value = resolveErrorMessage(err, '加载剧本失败，请稍后重试。')
  } finally {
    loadingScripts.value = false
  }
}

function prepareNewScript() {
  editingScriptId.value = null
  conceptText.value = ''
  projectContext.value = ''
  Object.assign(draft, createEmptyScriptDraft())
  syncTextFromDraft()
  error.value = null
}

function hydrateScript(script: ScriptRead) {
  draft.title = script.title
  draft.script_type = script.script_type
  draft.theme = script.theme
  draft.summary = script.summary
  draft.main_characters = script.main_characters
  draft.core_conflict = script.core_conflict
  draft.story_stage = script.story_stage
  draft.major_nodes = script.major_nodes
  draft.branch_ideas = script.branch_ideas
  draft.forbidden_content = script.forbidden_content
  draft.chapters = script.chapters
  draft.scene_cards = script.scene_cards
  draft.constraints = script.constraints
  draft.notes = script.notes
  draft.status = script.status
  syncTextFromDraft()
}

function editScript(script: ScriptRead) {
  editingScriptId.value = script.id
  conceptText.value = script.summary
  projectContext.value = ''
  hydrateScript(script)
  error.value = null
}

function parseStructuredFields() {
  draft.main_characters = JSON.parse(mainCharactersText.value || '[]')
  draft.major_nodes = JSON.parse(majorNodesText.value || '[]')
  draft.branch_ideas = JSON.parse(branchIdeasText.value || '[]')
  draft.chapters = JSON.parse(chaptersText.value || '[]')
  draft.scene_cards = JSON.parse(sceneCardsText.value || '[]')
  draft.constraints = JSON.parse(constraintsText.value || '{}')
}

async function submit() {
  if (selectedProjectId.value === 0) {
    error.value = '请先选择项目。'
    return
  }

  saving.value = true
  error.value = null

  try {
    parseStructuredFields()

    let saved: ScriptRead
    if (editingScriptId.value) {
      saved = await updateScript(editingScriptId.value, { ...draft })
    } else {
      saved = await createScript(selectedProjectId.value, { ...draft })
      editingScriptId.value = saved.id
    }

    hydrateScript(saved)
    await loadScripts()
  } catch (err) {
    error.value = resolveErrorMessage(err, '保存剧本失败，请稍后重试。')
  } finally {
    saving.value = false
  }
}

async function generateDraft() {
  if (!draft.title.trim()) {
    error.value = '请先输入剧本标题，再生成草稿。'
    return
  }

  generating.value = true
  error.value = null

  try {
    const generated = await generateScriptDraft({
      title: draft.title,
      script_type: draft.script_type,
      concept: conceptText.value,
      project_context: projectContext.value,
      status: draft.status,
    })

    Object.assign(draft, generated)
    syncTextFromDraft()
  } catch (err) {
    error.value = resolveErrorMessage(err, '生成剧本草稿失败，请稍后重试。')
  } finally {
    generating.value = false
  }
}

async function removeScript() {
  if (!editingScriptId.value) {
    return
  }

  if (!window.confirm('确定要删除这份剧本吗？')) {
    return
  }

  try {
    await deleteScript(editingScriptId.value)
    prepareNewScript()
    await loadScripts()
  } catch (err) {
    error.value = resolveErrorMessage(err, '删除剧本失败，请稍后重试。')
  }
}

async function download(format: 'json' | 'markdown') {
  if (!editingScriptId.value) {
    return
  }

  try {
    const exported = await exportScript(editingScriptId.value, format)
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
    anchor.download = `${draft.title || '剧本'}.${format === 'json' ? 'json' : 'md'}`
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    error.value = resolveErrorMessage(err, '导出剧本失败，请稍后重试。')
  }
}

function onProjectChange() {
  prepareNewScript()
  void loadScripts()
}

function refresh() {
  void loadScripts()
}

onMounted(async () => {
  try {
    await loadProjects()
    prepareNewScript()
    await loadScripts()
  } catch (err) {
    error.value = resolveErrorMessage(err, '初始化剧本页面失败，请稍后重试。')
  }
})
</script>
