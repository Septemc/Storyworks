<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">阶段五</p>
        <h2>预设工坊</h2>
      </div>
      <div class="actions">
        <button class="button button-secondary" type="button" @click="prepareNewPreset">新建预设</button>
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
          <h3>预设列表</h3>
          <p class="muted">{{ presets.length }} 条已保存</p>
        </div>

        <label class="toolbar-field">
          <span>搜索</span>
          <input v-model.trim="searchKeyword" placeholder="按预设标题搜索..." />
        </label>

        <p v-if="loadingPresets">正在加载预设...</p>
        <p v-else-if="selectedProjectId === 0" class="muted">请先选择项目，再查看预设。</p>
        <p v-else-if="filteredPresets.length === 0" class="muted">暂无预设。</p>
        <ul v-else class="entry-list">
          <li
            v-for="preset in filteredPresets"
            :key="preset.id"
            :class="['entry-item', { active: editingPresetId === preset.id }]"
          >
            <button class="entry-button" type="button" @click="editPreset(preset)">
              <strong>{{ preset.title }}</strong>
              <span>{{ preset.preset_type }} · {{ preset.style_description || '暂无风格说明。' }}</span>
            </button>
          </li>
        </ul>
      </article>

      <div class="stack">
        <article class="card">
          <div class="section-header">
            <div>
              <h3>{{ editingPresetId ? '编辑预设' : '创建预设' }}</h3>
              <p class="muted">用预设统一控制文风、节奏、表达方式与质量要求。</p>
            </div>
            <div class="actions">
              <button class="button button-secondary" type="button" @click="generateDraft" :disabled="generating">
                {{ generating ? '生成中...' : '生成草稿' }}
              </button>
              <button class="button button-secondary" type="button" @click="runTest" :disabled="testing">
                {{ testing ? '测试中...' : '测试预设' }}
              </button>
              <button class="button" type="button" @click="submit" :disabled="saving || selectedProjectId === 0">
                {{ saving ? '保存中...' : editingPresetId ? '保存修改' : '创建预设' }}
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
                <span>预设类型</span>
                <select v-model="draft.preset_type">
                  <option value="文风预设">文风预设</option>
                  <option value="题材预设">题材预设</option>
                  <option value="剧情偏好预设">剧情偏好预设</option>
                  <option value="人物塑造预设">人物塑造预设</option>
                  <option value="质量预设">质量预设</option>
                  <option value="输出格式预设">输出格式预设</option>
                </select>
              </label>
              <label>
                <span>作用范围</span>
                <input v-model.trim="draft.scope" maxlength="64" />
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
              <span>风格目标</span>
              <textarea
                v-model.trim="styleGoalText"
                rows="4"
                placeholder="例如：黑暗悬疑、压抑、伏笔密集，但保持叙述清晰。"
              />
            </label>

            <label>
              <span>参考文本</span>
              <textarea v-model.trim="referenceText" rows="3" />
            </label>

            <label>
              <span>目标用途</span>
              <textarea v-model.trim="targetUseText" rows="2" placeholder="例如：剧本与正文生成" />
            </label>

            <label>
              <span>风格说明</span>
              <textarea v-model.trim="draft.style_description" rows="4" />
            </label>

            <div class="grid two-col">
              <label>
                <span>用词倾向</span>
                <input v-model.trim="draft.wording_tendency" maxlength="200" />
              </label>
              <label>
                <span>句式倾向</span>
                <input v-model.trim="draft.sentence_tendency" maxlength="200" />
              </label>
              <label>
                <span>描写密度</span>
                <input v-model.trim="draft.description_density" maxlength="64" />
              </label>
              <label>
                <span>对话占比</span>
                <input v-model.trim="draft.dialogue_ratio" maxlength="64" />
              </label>
              <label>
                <span>节奏倾向</span>
                <input v-model.trim="draft.rhythm_tendency" maxlength="120" />
              </label>
              <label>
                <span>情绪强度</span>
                <input v-model.trim="draft.emotion_intensity" maxlength="120" />
              </label>
            </div>

            <label>
              <span>剧情偏好</span>
              <input v-model.trim="plotPreferencesText" placeholder="使用中文逗号或英文逗号分隔" />
            </label>

            <label>
              <span>人物偏好</span>
              <input v-model.trim="characterPreferencesText" placeholder="使用中文逗号或英文逗号分隔" />
            </label>

            <label>
              <span>禁用表达</span>
              <input v-model.trim="forbiddenExpressionsText" placeholder="使用中文逗号或英文逗号分隔" />
            </label>

            <label>
              <span>输出要求</span>
              <input v-model.trim="outputRequirementsText" placeholder="使用中文逗号或英文逗号分隔" />
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
            <h3>预设测试</h3>
            <p class="muted">预览当前预设会如何影响生成方向与输出要求。</p>
          </div>

          <form class="form" @submit.prevent="runTest">
            <label>
              <span>样例目标</span>
              <input v-model.trim="sampleTarget" placeholder="例如：剧本草稿 / 人物卡生成 / 世界书扩写" />
            </label>
            <label>
              <span>样例输入</span>
              <textarea v-model.trim="sampleInput" rows="4" />
            </label>
            <button class="button button-secondary" type="submit" :disabled="testing">
              {{ testing ? '测试中...' : '运行预设测试' }}
            </button>
          </form>

          <div v-if="testResult" class="stack-compact">
            <p><strong>预览摘要：</strong>{{ testResult.preview_summary }}</p>
            <p><strong>推荐提示词：</strong>{{ testResult.recommended_prompt }}</p>
            <div>
              <strong>生效指令</strong>
              <ul class="list">
                <li v-for="directive in testResult.active_directives" :key="directive">{{ directive }}</li>
              </ul>
            </div>
            <div>
              <strong>质量检查清单</strong>
              <ul class="list">
                <li v-for="item in testResult.quality_checklist" :key="item">{{ item }}</li>
              </ul>
            </div>
          </div>
        </article>

        <article v-if="editingPresetId" class="card">
          <div class="section-header">
            <h3>导出</h3>
            <div class="actions">
              <button class="button button-secondary" type="button" @click="download('json')">导出 JSON</button>
              <button class="button button-secondary" type="button" @click="download('markdown')">
                导出 Markdown
              </button>
              <button class="button button-danger" type="button" @click="removePreset">删除预设</button>
            </div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'

import type { PresetCreate, PresetRead, PresetTestResponse } from '@/schemas/preset'
import type { ProjectRead } from '@/schemas/project'
import { createEmptyPresetDraft } from '@/schemas/preset'
import { resolveErrorMessage } from '@/services/http'
import { fetchProjects } from '@/services/projects'
import {
  createPreset,
  deletePreset,
  exportPreset,
  fetchPresets,
  generatePresetDraft,
  testPreset,
  updatePreset,
} from '@/services/presets'

const statusOptions = [
  { value: 'draft', label: '草稿' },
  { value: 'ready', label: '待定稿' },
  { value: 'final', label: '已定稿' },
  { value: 'archived', label: '已归档' },
]

const projects = ref<ProjectRead[]>([])
const presets = ref<PresetRead[]>([])
const selectedProjectId = ref(0)
const loadingPresets = ref(false)
const saving = ref(false)
const generating = ref(false)
const testing = ref(false)
const error = ref<string | null>(null)
const editingPresetId = ref<number | null>(null)
const searchKeyword = ref('')
const styleGoalText = ref('')
const referenceText = ref('')
const targetUseText = ref('')
const sampleTarget = ref('剧本草稿')
const sampleInput = ref('主角进入被封锁的档案馆调查真相。')
const testResult = ref<PresetTestResponse | null>(null)

const draft = reactive<PresetCreate>(createEmptyPresetDraft())
const plotPreferencesText = ref('')
const characterPreferencesText = ref('')
const forbiddenExpressionsText = ref('')
const outputRequirementsText = ref('')

const filteredPresets = computed(() => {
  return presets.value.filter((preset) => {
    return !searchKeyword.value || preset.title.toLowerCase().includes(searchKeyword.value.toLowerCase())
  })
})

watch(plotPreferencesText, (value) => {
  draft.plot_preferences = value.split(/[,，]/).map((item) => item.trim()).filter(Boolean)
})
watch(characterPreferencesText, (value) => {
  draft.character_preferences = value.split(/[,，]/).map((item) => item.trim()).filter(Boolean)
})
watch(forbiddenExpressionsText, (value) => {
  draft.forbidden_expressions = value.split(/[,，]/).map((item) => item.trim()).filter(Boolean)
})
watch(outputRequirementsText, (value) => {
  draft.output_requirements = value.split(/[,，]/).map((item) => item.trim()).filter(Boolean)
})

async function loadProjects() {
  projects.value = await fetchProjects()
  if (projects.value.length > 0 && selectedProjectId.value === 0) {
    selectedProjectId.value = projects.value[0].id
  }
}

async function loadPresets() {
  if (selectedProjectId.value === 0) {
    presets.value = []
    return
  }

  loadingPresets.value = true
  error.value = null

  try {
    presets.value = await fetchPresets(selectedProjectId.value)
  } catch (err) {
    error.value = resolveErrorMessage(err, '加载预设失败，请稍后重试。')
  } finally {
    loadingPresets.value = false
  }
}

function syncListTexts() {
  plotPreferencesText.value = draft.plot_preferences.join('，')
  characterPreferencesText.value = draft.character_preferences.join('，')
  forbiddenExpressionsText.value = draft.forbidden_expressions.join('，')
  outputRequirementsText.value = draft.output_requirements.join('，')
}

function prepareNewPreset() {
  editingPresetId.value = null
  styleGoalText.value = ''
  referenceText.value = ''
  targetUseText.value = ''
  testResult.value = null
  Object.assign(draft, createEmptyPresetDraft())
  syncListTexts()
  error.value = null
}

function hydratePreset(preset: PresetRead) {
  draft.title = preset.title
  draft.preset_type = preset.preset_type
  draft.scope = preset.scope
  draft.style_description = preset.style_description
  draft.wording_tendency = preset.wording_tendency
  draft.sentence_tendency = preset.sentence_tendency
  draft.description_density = preset.description_density
  draft.dialogue_ratio = preset.dialogue_ratio
  draft.rhythm_tendency = preset.rhythm_tendency
  draft.emotion_intensity = preset.emotion_intensity
  draft.plot_preferences = [...preset.plot_preferences]
  draft.character_preferences = [...preset.character_preferences]
  draft.forbidden_expressions = [...preset.forbidden_expressions]
  draft.output_requirements = [...preset.output_requirements]
  draft.notes = preset.notes
  draft.status = preset.status
  syncListTexts()
}

function editPreset(preset: PresetRead) {
  editingPresetId.value = preset.id
  hydratePreset(preset)
  testResult.value = null
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
    let saved: PresetRead
    if (editingPresetId.value) {
      saved = await updatePreset(editingPresetId.value, { ...draft })
    } else {
      saved = await createPreset(selectedProjectId.value, { ...draft })
      editingPresetId.value = saved.id
    }

    hydratePreset(saved)
    await loadPresets()
  } catch (err) {
    error.value = resolveErrorMessage(err, '保存预设失败，请稍后重试。')
  } finally {
    saving.value = false
  }
}

async function generateDraft() {
  if (!draft.title.trim()) {
    error.value = '请先输入预设标题，再生成草稿。'
    return
  }

  generating.value = true
  error.value = null

  try {
    const generated = await generatePresetDraft({
      title: draft.title,
      preset_type: draft.preset_type,
      style_goal: styleGoalText.value,
      reference_text: referenceText.value,
      target_use: targetUseText.value,
      status: draft.status,
    })

    Object.assign(draft, generated)
    syncListTexts()
  } catch (err) {
    error.value = resolveErrorMessage(err, '生成预设草稿失败，请稍后重试。')
  } finally {
    generating.value = false
  }
}

async function runTest() {
  testing.value = true
  error.value = null

  try {
    testResult.value = await testPreset({
      title: draft.title || '未命名预设',
      preset_type: draft.preset_type,
      style_description: draft.style_description,
      wording_tendency: draft.wording_tendency,
      sentence_tendency: draft.sentence_tendency,
      description_density: draft.description_density,
      dialogue_ratio: draft.dialogue_ratio,
      rhythm_tendency: draft.rhythm_tendency,
      emotion_intensity: draft.emotion_intensity,
      plot_preferences: draft.plot_preferences,
      character_preferences: draft.character_preferences,
      forbidden_expressions: draft.forbidden_expressions,
      output_requirements: draft.output_requirements,
      sample_target: sampleTarget.value,
      sample_input: sampleInput.value,
    })
  } catch (err) {
    error.value = resolveErrorMessage(err, '测试预设失败，请稍后重试。')
  } finally {
    testing.value = false
  }
}

async function removePreset() {
  if (!editingPresetId.value) {
    return
  }

  if (!window.confirm('确定要删除这个预设吗？')) {
    return
  }

  try {
    await deletePreset(editingPresetId.value)
    prepareNewPreset()
    await loadPresets()
  } catch (err) {
    error.value = resolveErrorMessage(err, '删除预设失败，请稍后重试。')
  }
}

async function download(format: 'json' | 'markdown') {
  if (!editingPresetId.value) {
    return
  }

  try {
    const exported = await exportPreset(editingPresetId.value, format)
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
    anchor.download = `${draft.title || '预设'}.${format === 'json' ? 'json' : 'md'}`
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    error.value = resolveErrorMessage(err, '导出预设失败，请稍后重试。')
  }
}

function onProjectChange() {
  prepareNewPreset()
  void loadPresets()
}

function refresh() {
  void loadPresets()
}

onMounted(async () => {
  try {
    await loadProjects()
    prepareNewPreset()
    await loadPresets()
  } catch (err) {
    error.value = resolveErrorMessage(err, '初始化预设页面失败，请稍后重试。')
  }
})
</script>
