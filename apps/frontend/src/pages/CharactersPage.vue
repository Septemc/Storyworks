<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">阶段三</p>
        <h2>人物卡工坊</h2>
      </div>
      <div class="actions">
        <button class="button button-secondary" type="button" @click="prepareNewCharacter">新建人物卡</button>
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

        <div class="toolbar-field">
          <span>角色模板</span>
          <p class="muted">
            {{ template?.name ?? '正在加载模板...' }}
          </p>
        </div>
      </div>
    </article>

    <div class="worldbook-layout">
      <article class="card">
        <div class="section-header">
          <h3>人物卡列表</h3>
          <p class="muted">{{ characters.length }} 条已保存</p>
        </div>

        <label class="toolbar-field">
          <span>搜索</span>
          <input v-model.trim="searchKeyword" placeholder="按角色名称搜索..." />
        </label>

        <p v-if="loadingCharacters">正在加载人物卡...</p>
        <p v-else-if="selectedProjectId === 0" class="muted">请先选择项目，再查看人物卡。</p>
        <p v-else-if="filteredCharacters.length === 0" class="muted">暂无人物卡。</p>
        <ul v-else class="entry-list">
          <li
            v-for="character in filteredCharacters"
            :key="character.id"
            :class="['entry-item', { active: editingCharacterId === character.id }]"
          >
            <button class="entry-button" type="button" @click="editCharacter(character)">
              <strong>{{ character.name }}</strong>
              <span>{{ character.summary || '暂无简介。' }}</span>
            </button>
          </li>
        </ul>
      </article>

      <div class="stack">
        <article class="card">
          <div class="section-header">
            <div>
              <h3>{{ editingCharacterId ? '编辑人物卡' : '创建人物卡' }}</h3>
              <p class="muted">基于默认双视图角色模板的结构化编辑表单。</p>
            </div>
            <div class="actions">
              <button class="button button-secondary" type="button" @click="generateDraft" :disabled="generating">
                {{ generating ? '生成中...' : '生成草稿' }}
              </button>
              <button class="button" type="button" @click="submit" :disabled="saving || selectedProjectId === 0">
                {{ saving ? '保存中...' : editingCharacterId ? '保存修改' : '创建人物卡' }}
              </button>
            </div>
          </div>

          <div class="grid two-col">
            <label>
              <span>名称提示</span>
              <input v-model.trim="nameHint" maxlength="120" placeholder="可选，给一个角色名称提示" />
            </label>
            <label>
              <span>状态</span>
              <select v-model="statusValue">
                <option v-for="option in statusOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
          </div>

          <label class="toolbar-field">
            <span>角色概念</span>
            <textarea
              v-model.trim="conceptText"
              rows="4"
              placeholder="例如：北境联邦巡夜人，外表沉静，暗中追查旧王朝遗案。"
            />
          </label>

          <label class="toolbar-field">
            <span>项目背景</span>
            <textarea
              v-model.trim="projectContext"
              rows="3"
              placeholder="可选，补充项目设定或世界观背景，帮助约束角色生成。"
            />
          </label>

          <div v-if="template" class="stack-compact">
            <div class="pill-row">
              <button
                type="button"
                class="pill"
                :class="{ active: currentMode === 'developer' }"
                @click="currentMode = 'developer'"
              >
                创作视图
              </button>
              <button
                type="button"
                class="pill"
                :class="{ active: currentMode === 'player' }"
                @click="currentMode = 'player'"
              >
                玩家视图
              </button>
            </div>

            <div class="pill-row">
              <button
                v-for="tab in sortedTabs"
                :key="tab.id"
                type="button"
                class="pill"
                :class="{ active: activeTabId === tab.id }"
                @click="activeTabId = tab.id"
              >
                {{ tab.label }}
              </button>
            </div>

            <p class="helper-note">
              {{
                currentMode === 'developer'
                  ? template.config.mode_contract.developer_mode_requirements
                  : template.config.mode_contract.player_mode_requirements
              }}
            </p>

            <div class="stack-compact">
              <label
                v-for="field in currentTabFields"
                :key="`${currentMode}-${field.id}`"
                class="field-block"
              >
                <span>{{ field.label }}</span>
                <input
                  v-if="field.type === 'text'"
                  v-model="currentEditor[field.tab][field.id]"
                  :placeholder="field.label"
                />
                <textarea
                  v-else
                  v-model="currentEditor[field.tab][field.id]"
                  :rows="field.type === 'textarea' ? 4 : 6"
                />
                <small class="field-help">
                  {{ currentMode === 'developer' ? field.developer_mode_desc : field.player_mode_desc }}
                </small>
              </label>
            </div>
          </div>

          <label class="toolbar-field">
            <span>备注</span>
            <textarea v-model.trim="notesText" rows="3" />
          </label>

          <p v-if="error" class="error">{{ error }}</p>
        </article>

        <article v-if="editingCharacterId" class="card">
          <div class="section-header">
            <h3>导出</h3>
            <div class="actions">
              <button class="button button-secondary" type="button" @click="download('json')">导出 JSON</button>
              <button class="button button-secondary" type="button" @click="download('markdown')">
                导出 Markdown
              </button>
              <button class="button button-danger" type="button" @click="removeCharacter">删除人物卡</button>
            </div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import {
  createEmptyCharacterEditor,
  type CharacterCreate,
  type CharacterEditorState,
  type CharacterRead,
  type CharacterTemplate,
} from '@/schemas/character'
import type { ProjectRead } from '@/schemas/project'
import {
  createCharacter,
  deleteCharacter,
  exportCharacter,
  fetchCharacters,
  fetchCharacterTemplates,
  generateCharacterDraft,
  updateCharacter,
} from '@/services/characters'
import { resolveErrorMessage } from '@/services/http'
import { fetchProjects } from '@/services/projects'

const statusOptions = [
  { value: 'draft', label: '草稿' },
  { value: 'ready', label: '待定稿' },
  { value: 'final', label: '已定稿' },
  { value: 'archived', label: '已归档' },
]

const projects = ref<ProjectRead[]>([])
const template = ref<CharacterTemplate | null>(null)
const characters = ref<CharacterRead[]>([])
const selectedProjectId = ref(0)
const loadingCharacters = ref(false)
const saving = ref(false)
const generating = ref(false)
const error = ref<string | null>(null)
const editingCharacterId = ref<number | null>(null)
const searchKeyword = ref('')
const nameHint = ref('')
const conceptText = ref('')
const projectContext = ref('')
const notesText = ref('')
const statusValue = ref('draft')
const currentMode = ref<'developer' | 'player'>('developer')
const activeTabId = ref('')

const developerEditor = reactive<CharacterEditorState>({})
const playerEditor = reactive<CharacterEditorState>({})
const metaState = ref<Record<string, unknown>>({})

const sortedTabs = computed(() => {
  return [...(template.value?.config.tabs ?? [])].sort((a, b) => a.order - b.order)
})

const currentTabFields = computed(() => {
  return (template.value?.config.fields ?? []).filter((field) => field.tab === activeTabId.value)
})

const currentEditor = computed(() => (currentMode.value === 'developer' ? developerEditor : playerEditor))

const filteredCharacters = computed(() => {
  return characters.value.filter((character) => {
    return !searchKeyword.value || character.name.toLowerCase().includes(searchKeyword.value.toLowerCase())
  })
})

function ensureEditorTarget(target: CharacterEditorState, nextState: CharacterEditorState) {
  for (const key of Object.keys(target)) {
    delete target[key]
  }
  for (const [tabId, values] of Object.entries(nextState)) {
    target[tabId] = { ...values }
  }
}

function serializeValue(value: unknown) {
  if (value === null || value === undefined) {
    return ''
  }
  if (typeof value === 'string') {
    return value
  }
  return JSON.stringify(value, null, 2)
}

function modeToEditorState(templateValue: CharacterTemplate, mode: Record<string, Record<string, unknown>>) {
  const editor = createEmptyCharacterEditor(templateValue, 'developer')
  for (const field of templateValue.config.fields) {
    const value = mode[field.tab]?.[field.id]
    editor[field.tab][field.id] = serializeValue(value)
  }
  return editor
}

function parseEditorValue(type: string, raw: string) {
  if (raw.trim().includes('未知')) {
    return '未知'
  }

  if (type === 'text' || type === 'textarea') {
    return raw.trim()
  }

  if (!raw.trim()) {
    return type === 'object_list' ? [] : {}
  }

  return JSON.parse(raw)
}

function editorToMode(templateValue: CharacterTemplate, editor: CharacterEditorState) {
  const mode: Record<string, Record<string, unknown>> = {}

  for (const tab of templateValue.config.tabs) {
    mode[tab.id] = {}
  }

  for (const field of templateValue.config.fields) {
    mode[field.tab][field.id] = parseEditorValue(field.type, editor[field.tab][field.id] ?? '')
  }

  return mode
}

function resetEditors() {
  if (!template.value) {
    return
  }
  ensureEditorTarget(developerEditor, createEmptyCharacterEditor(template.value, 'developer'))
  ensureEditorTarget(playerEditor, createEmptyCharacterEditor(template.value, 'player'))
}

function prepareNewCharacter() {
  editingCharacterId.value = null
  nameHint.value = ''
  conceptText.value = ''
  projectContext.value = ''
  notesText.value = ''
  statusValue.value = 'draft'
  metaState.value = {}
  currentMode.value = 'developer'
  activeTabId.value = sortedTabs.value[0]?.id ?? ''
  error.value = null
  resetEditors()
}

function hydrateCharacter(character: CharacterRead) {
  if (!template.value) {
    return
  }
  editingCharacterId.value = character.id
  nameHint.value = character.name
  conceptText.value = character.summary
  projectContext.value = ''
  notesText.value = character.notes
  statusValue.value = character.status
  metaState.value = character.meta
  ensureEditorTarget(developerEditor, modeToEditorState(template.value, character.developer_mode))
  ensureEditorTarget(playerEditor, modeToEditorState(template.value, character.player_mode))
}

async function loadProjects() {
  projects.value = await fetchProjects()
  if (projects.value.length > 0 && selectedProjectId.value === 0) {
    selectedProjectId.value = projects.value[0].id
  }
}

async function loadTemplate() {
  const templates = await fetchCharacterTemplates()
  template.value = templates[0] ?? null
  activeTabId.value = template.value?.config.tabs[0]?.id ?? ''
  resetEditors()
}

async function loadCharacters() {
  if (selectedProjectId.value === 0) {
    characters.value = []
    return
  }

  loadingCharacters.value = true
  error.value = null

  try {
    characters.value = await fetchCharacters(selectedProjectId.value)
  } catch (err) {
    error.value = resolveErrorMessage(err, '加载人物卡失败，请稍后重试。')
  } finally {
    loadingCharacters.value = false
  }
}

function editCharacter(character: CharacterRead) {
  hydrateCharacter(character)
  error.value = null
}

async function submit() {
  if (!template.value || selectedProjectId.value === 0) {
    error.value = '请先选择项目，并等待角色模板加载完成。'
    return
  }

  saving.value = true
  error.value = null

  try {
    const payload: CharacterCreate = {
      template_id: template.value.template_id,
      developer_mode: editorToMode(template.value, developerEditor),
      player_mode: editorToMode(template.value, playerEditor),
      meta: metaState.value,
      notes: notesText.value,
      status: statusValue.value,
    }

    let saved: CharacterRead
    if (editingCharacterId.value) {
      saved = await updateCharacter(editingCharacterId.value, payload)
    } else {
      saved = await createCharacter(selectedProjectId.value, payload)
      editingCharacterId.value = saved.id
    }

    hydrateCharacter(saved)
    await loadCharacters()
  } catch (err) {
    error.value = resolveErrorMessage(err, '保存人物卡失败，请稍后重试。')
  } finally {
    saving.value = false
  }
}

async function generateDraft() {
  if (!template.value) {
    error.value = '角色模板尚未准备完成。'
    return
  }

  generating.value = true
  error.value = null

  try {
    const generated = await generateCharacterDraft({
      template_id: template.value.template_id,
      name_hint: nameHint.value,
      concept: conceptText.value,
      project_context: projectContext.value,
      status: statusValue.value,
    })

    nameHint.value = generated.name
    notesText.value = generated.notes
    statusValue.value = generated.status
    metaState.value = generated.meta
    ensureEditorTarget(developerEditor, modeToEditorState(template.value, generated.developer_mode))
    ensureEditorTarget(playerEditor, modeToEditorState(template.value, generated.player_mode))
  } catch (err) {
    error.value = resolveErrorMessage(err, '生成人物卡草稿失败，请稍后重试。')
  } finally {
    generating.value = false
  }
}

async function removeCharacter() {
  if (!editingCharacterId.value) {
    return
  }

  if (!window.confirm('确定要删除这张人物卡吗？')) {
    return
  }

  try {
    await deleteCharacter(editingCharacterId.value)
    prepareNewCharacter()
    await loadCharacters()
  } catch (err) {
    error.value = resolveErrorMessage(err, '删除人物卡失败，请稍后重试。')
  }
}

async function download(format: 'json' | 'markdown') {
  if (!editingCharacterId.value) {
    return
  }

  try {
    const exported = await exportCharacter(editingCharacterId.value, format)
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
    anchor.download = `${nameHint.value || '人物卡'}.${format === 'json' ? 'json' : 'md'}`
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    error.value = resolveErrorMessage(err, '导出人物卡失败，请稍后重试。')
  }
}

function onProjectChange() {
  prepareNewCharacter()
  void loadCharacters()
}

function refresh() {
  void loadCharacters()
}

onMounted(async () => {
  try {
    await Promise.all([loadProjects(), loadTemplate()])
    prepareNewCharacter()
    await loadCharacters()
  } catch (err) {
    error.value = resolveErrorMessage(err, '初始化人物卡页面失败，请稍后重试。')
  }
})
</script>
