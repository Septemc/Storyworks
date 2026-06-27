<template>
  <v-container fluid>
    <v-row>
      <!-- 左侧角色列表 -->
      <v-col cols="3">
        <v-card class="h-100">
          <v-card-title class="d-flex justify-space-between align-center">
            <span>角色列表</span>
            <div>
              <v-btn size="small" icon variant="text" @click="showCreateDialog = true">
                <v-icon>mdi-plus</v-icon>
                <v-tooltip activator="parent">新建角色</v-tooltip>
              </v-btn>
              <v-btn size="small" icon variant="text" @click="showBatchDialog = true">
                <v-icon>mdi-robot</v-icon>
                <v-tooltip activator="parent">AI批量生成</v-tooltip>
              </v-btn>
            </div>
          </v-card-title>

          <!-- 全选/批量操作 -->
          <v-card-text v-if="characters.length > 0" class="py-0">
            <div class="d-flex align-center justify-space-between">
              <v-checkbox
                v-model="isAllSelected"
                label="全选"
                density="compact"
                hide-details
                @click="store.selectAll()"
              ></v-checkbox>
              <v-btn
                v-if="selectedIds.length > 0"
                size="x-small"
                color="error"
                variant="text"
                @click="confirmBatchDelete"
              >
                删除选中 ({{ selectedIds.length }})
              </v-btn>
            </div>
          </v-card-text>

          <v-divider></v-divider>

          <v-list v-if="characters.length > 0" lines="two" select-strategy="classic">
            <v-list-item
              v-for="char in characters"
              :key="char.id"
              :value="char.id"
              :active="currentCharacter?.id === char.id"
              @click="selectCharacter(char)"
            >
              <template v-slot:prepend>
                <v-checkbox
                  :model-value="selectedIds.includes(char.id)"
                  @click.stop="store.toggleSelect(char.id)"
                  density="compact"
                  hide-details
                  class="mr-2"
                ></v-checkbox>
                <v-avatar color="primary" size="36">
                  <span class="text-body-2">{{ char.name[0] }}</span>
                </v-avatar>
              </template>
              <v-list-item-title>{{ char.name }}</v-list-item-title>
              <v-list-item-subtitle>{{ getCharacterSummary(char) }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
          <div v-else class="text-center py-8 text-medium-emphasis">
            <v-icon icon="mdi-account-outline" size="48" color="grey-lighten-1"></v-icon>
            <p class="mt-2">暂无角色</p>
            <v-btn size="small" color="primary" class="mt-2" @click="showCreateDialog = true">
              创建第一个角色
            </v-btn>
          </div>
        </v-card>
      </v-col>

      <!-- 右侧详情 -->
      <v-col cols="9">
        <v-card class="h-100">
          <template v-if="currentCharacter">
            <v-card-title class="d-flex justify-space-between align-center">
              <span class="text-h5">{{ currentCharacter.name }}</span>
              <div>
                <v-btn-group density="comfortable" variant="outlined">
                  <v-btn @click="toggleMode" prepend-icon="mdi-eye">
                    {{ showPlayerMode ? '开发者视角' : '玩家视角' }}
                  </v-btn>
                  <v-btn @click="openEditDialog" prepend-icon="mdi-pencil">
                    编辑
                  </v-btn>
                  <v-btn @click="showExportMenu = true" prepend-icon="mdi-export">
                    导出
                  </v-btn>
                  <v-btn color="error" @click="confirmDelete" prepend-icon="mdi-delete">
                    删除
                  </v-btn>
                </v-btn-group>
              </div>
            </v-card-title>

            <v-divider></v-divider>

            <v-card-text class="pa-0">
              <v-tabs v-model="activeTab" bg-color="grey-lighten-4">
                <v-tab value="basic">基础信息</v-tab>
                <v-tab value="knowledge">见闻设定</v-tab>
                <v-tab value="secrets">
                  秘密过往
                  <v-icon v-if="showPlayerMode" size="small" class="ml-1">mdi-lock</v-icon>
                </v-tab>
                <v-tab value="attributes">数值属性</v-tab>
                <v-tab value="relations">人际关系</v-tab>
                <v-tab value="inventory">装备物品</v-tab>
                <v-tab value="skills">技能功法</v-tab>
                <v-tab value="fortune">
                  命运机缘
                  <v-icon v-if="showPlayerMode" size="small" class="ml-1">mdi-lock</v-icon>
                </v-tab>
              </v-tabs>

              <v-tabs-window v-model="activeTab">
                <v-tabs-window-item v-for="tab in tabs" :key="tab.value" :value="tab.value">
                  <v-card flat class="pa-4">
                    <!-- 秘密标签页在玩家视角下 -->
                    <div v-if="showPlayerMode && isSecretTab(tab.value)">
                      <v-alert type="info" variant="tonal" icon="mdi-lock">
                        此内容在玩家视角下隐藏。切换到开发者视角可查看完整信息。
                      </v-alert>
                    </div>

                    <div v-else>
                      <template v-if="currentModeData[tab.value]">
                        <!-- 对象类型 -->
                        <template v-if="isObject(currentModeData[tab.value]) && !isArray(currentModeData[tab.value])">
                          <div v-for="(value, key) in currentModeData[tab.value]" :key="key" class="mb-4">
                            <div class="text-subtitle-2 text-medium-emphasis mb-1">{{ getFieldLabel(key as string) }}</div>
                            <div v-if="isArray(value)">
                              <v-chip v-for="(item, idx) in value" :key="idx" size="small" class="mr-1 mb-1">
                                {{ formatChipItem(item) }}
                              </v-chip>
                            </div>
                            <div v-else-if="isObject(value)" class="pl-4 border-left">
                              <pre class="text-body-2">{{ JSON.stringify(value, null, 2) }}</pre>
                            </div>
                            <div v-else class="text-body-1" style="white-space: pre-wrap">{{ value || '暂无' }}</div>
                          </div>
                        </template>

                        <!-- 数组类型 -->
                        <template v-else-if="isArray(currentModeData[tab.value])">
                          <div v-if="currentModeData[tab.value].length === 0" class="text-medium-emphasis">
                            暂无数据
                          </div>
                          <div v-else>
                            <div v-for="(item, idx) in currentModeData[tab.value]" :key="idx" class="mb-3 pa-3 border rounded">
                              <template v-if="isObject(item)">
                                <div v-for="(val, key) in item" :key="key" class="mb-1">
                                  <span class="text-subtitle-2 text-medium-emphasis">{{ getFieldLabel(key as string) }}: </span>
                                  <span>{{ val }}</span>
                                </div>
                              </template>
                              <template v-else>
                                {{ item }}
                              </template>
                            </div>
                          </div>
                        </template>
                      </template>

                      <div v-else class="text-medium-emphasis py-4 text-center">
                        <v-icon icon="mdi-information-outline" class="mr-1"></v-icon>
                        暂无数据，点击编辑按钮添加内容
                      </div>
                    </div>
                  </v-card>
                </v-tabs-window-item>
              </v-tabs-window>
            </v-card-text>
          </template>

          <template v-else>
            <div class="d-flex flex-column align-center justify-center h-100 text-medium-emphasis" style="min-height: 400px">
              <v-icon icon="mdi-account-outline" size="80" color="grey-lighten-2"></v-icon>
              <p class="text-h6 mt-4">选择或创建一个角色</p>
              <p class="text-body-2">从左侧列表选择角色，或点击新建按钮创建</p>
            </div>
          </template>
        </v-card>
      </v-col>
    </v-row>

    <!-- 创建对话框 -->
    <v-dialog v-model="showCreateDialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-account-plus</v-icon>
          创建角色
        </v-card-title>
        <v-card-text>
          <v-form ref="createFormRef" v-model="createFormValid">
            <v-text-field
              v-model="createForm.name"
              label="角色名称"
              :rules="[v => !!v || '请输入角色名称']"
              required
              class="mb-2"
            ></v-text-field>
            <v-select
              v-model="createForm.character_type"
              :items="characterTypes"
              label="角色类型"
              class="mb-2"
            ></v-select>
            <v-textarea
              v-model="createForm.concept"
              label="角色概念"
              hint="描述角色的核心设定，越详细生成效果越好"
              rows="4"
              class="mb-2"
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showCreateDialog = false">取消</v-btn>
          <v-btn
            color="secondary"
            prepend-icon="mdi-robot"
            @click="handleGenerateAndCreate"
            :loading="generating"
            :disabled="!createForm.name"
          >
            AI生成
          </v-btn>
          <v-btn
            color="primary"
            :disabled="!createFormValid"
            @click="handleCreate"
          >
            手动创建
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 编辑对话框 -->
    <v-dialog v-model="showEditDialog" max-width="900" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-pencil</v-icon>
          编辑角色 - {{ currentCharacter?.name }}
        </v-card-title>
        <v-card-text style="max-height: 600px">
          <v-tabs v-model="editTab">
            <v-tab value="dev">开发者视角</v-tab>
            <v-tab value="player">玩家视角</v-tab>
          </v-tabs>

          <v-tabs-window v-model="editTab" class="mt-4">
            <v-tabs-window-item value="dev">
              <v-textarea
                v-model="editDevJson"
                label="Developer Mode (JSON)"
                rows="20"
                variant="outlined"
                :rules="[validateJson]"
              ></v-textarea>
            </v-tabs-window-item>
            <v-tabs-window-item value="player">
              <v-textarea
                v-model="editPlayerJson"
                label="Player Mode (JSON)"
                rows="20"
                variant="outlined"
                :rules="[validateJson]"
              ></v-textarea>
            </v-tabs-window-item>
          </v-tabs-window>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showEditDialog = false">取消</v-btn>
          <v-btn color="primary" @click="handleUpdate" :loading="saving">
            保存
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 批量生成对话框 -->
    <v-dialog v-model="showBatchDialog" max-width="700">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-robot</v-icon>
          AI 批量生成
        </v-card-title>
        <v-card-text>
          <v-select
            v-model="batchForm.character_type"
            :items="characterTypes"
            label="角色类型"
            class="mb-2"
          ></v-select>
          <v-textarea
            v-model="batchForm.concepts"
            label="角色概念 (每行一个)"
            hint="每行输入一个角色概念，AI会为每个概念生成一个角色"
            rows="8"
            placeholder="一个冷酷的剑客&#10;一个善良的药师&#10;一个神秘的占星师"
          ></v-textarea>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showBatchDialog = false">取消</v-btn>
          <v-btn
            color="primary"
            prepend-icon="mdi-robot"
            @click="handleBatchGenerate"
            :loading="generating"
            :disabled="!batchForm.concepts.trim()"
          >
            生成 ({{ batchConcepts.length }} 个)
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 导出菜单 -->
    <v-menu v-model="showExportMenu" :close-on-content-click="true">
      <template v-slot:activator="{ props }">
        <v-btn v-bind="props" style="display: none">Export</v-btn>
      </template>
      <v-list>
        <v-list-item @click="handleExportMarkdown">
          <template v-slot:prepend>
            <v-icon>mdi-language-markdown</v-icon>
          </template>
          <v-list-item-title>导出为 Markdown</v-list-item-title>
        </v-list-item>
        <v-list-item @click="handleExportJson">
          <template v-slot:prepend>
            <v-icon>mdi-code-json</v-icon>
          </template>
          <v-list-item-title>导出为 JSON</v-list-item-title>
        </v-list-item>
        <v-divider></v-divider>
        <v-list-item @click="handleExportAllMarkdown">
          <template v-slot:prepend>
            <v-icon>mdi-file-multiple</v-icon>
          </template>
          <v-list-item-title>导出所有角色 (MD)</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>

    <!-- 删除确认 -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon color="error" class="mr-2">mdi-alert</v-icon>
          确认删除
        </v-card-title>
        <v-card-text>
          确定要删除角色 "{{ currentCharacter?.name }}" 吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showDeleteDialog = false">取消</v-btn>
          <v-btn color="error" @click="handleDelete">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 批量删除确认 -->
    <v-dialog v-model="showBatchDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon color="error" class="mr-2">mdi-alert</v-icon>
          确认批量删除
        </v-card-title>
        <v-card-text>
          确定要删除选中的 {{ selectedIds.length }} 个角色吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showBatchDeleteDialog = false">取消</v-btn>
          <v-btn color="error" @click="handleBatchDelete">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 消息提示 -->
    <v-snackbar v-model="snackbar" :color="snackbarColor" :timeout="3000">
      {{ snackbarText }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useCharacterStore, type Character } from '@/stores/character'

const store = useCharacterStore()
const { characters, currentCharacter, loading, generating, selectedIds } = storeToRefs(store)

// 对话框状态
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showDeleteDialog = ref(false)
const showBatchDeleteDialog = ref(false)
const showBatchDialog = ref(false)
const showExportMenu = ref(false)

// 表单
const createFormValid = ref(false)
const createFormRef = ref<any>(null)
const createForm = ref({
  name: '',
  character_type: '配角',
  concept: '',
})

const editTab = ref('dev')
const editDevJson = ref('')
const editPlayerJson = ref('')
const saving = ref(false)

const batchForm = ref({
  character_type: 'NPC',
  concepts: '',
})

// 视图状态
const showPlayerMode = ref(false)
const activeTab = ref('basic')

// 提示
const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

// 配置
const characterTypes = ['主角', '配角', '反派', 'NPC']

const tabs = [
  { value: 'basic', label: '基础信息' },
  { value: 'knowledge', label: '见闻设定' },
  { value: 'secrets', label: '秘密过往' },
  { value: 'attributes', label: '数值属性' },
  { value: 'relations', label: '人际关系' },
  { value: 'inventory', label: '装备物品' },
  { value: 'skills', label: '技能功法' },
  { value: 'fortune', label: '命运机缘' },
]

// URL 参数
const urlParams = new URLSearchParams(window.location.search)
const projectName = urlParams.get('project') || 'demo'

// 计算属性
const currentModeData = computed(() => {
  if (!currentCharacter.value) return {}
  return showPlayerMode.value ? currentCharacter.value.player_mode : currentCharacter.value.developer_mode
})

const isAllSelected = computed(() => {
  return characters.value.length > 0 && selectedIds.value.length === characters.value.length
})

const batchConcepts = computed(() => {
  return batchForm.value.concepts.split('\n').filter(c => c.trim())
})

// 生命周期
onMounted(() => {
  if (projectName) {
    store.fetchCharacters(projectName)
  }
})

// 方法
function isSecretTab(tab: string) {
  return ['secrets', 'fortune'].includes(tab)
}

function isObject(value: any) {
  return value !== null && typeof value === 'object'
}

function isArray(value: any) {
  return Array.isArray(value)
}

function getFieldLabel(key: string) {
  const labels: Record<string, string> = {
    name: '姓名', identity: '身份', level: '等级/修为', summary: '简介',
    personality: '性格', appearance: '外貌', background: '背景', motivation: '动机',
    trauma: '心理创伤', hidden_identity: '隐藏身份', secret: '秘密',
    health: '健康状态', special: '特殊状态', target: '目标', type: '类型',
    description: '描述', role: '角色', level: '等级',
  }
  return labels[key] || key
}

function formatChipItem(item: any) {
  if (typeof item === 'object') {
    return item.name || item.target || JSON.stringify(item)
  }
  return item
}

function getCharacterSummary(char: Character) {
  const summary = char.developer_mode?.basic?.summary || char.developer_mode?.knowledge?.background
  return summary ? summary.substring(0, 40) + (summary.length > 40 ? '...' : '') : '暂无简介'
}

function selectCharacter(char: Character) {
  store.currentCharacter = char
}

function toggleMode() {
  showPlayerMode.value = !showPlayerMode.value
}

function showMessage(text: string, color = 'success') {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

function validateJson(value: string) {
  try {
    JSON.parse(value)
    return true
  } catch {
    return 'JSON 格式无效'
  }
}

// 编辑
function openEditDialog() {
  if (!currentCharacter.value) return
  editDevJson.value = JSON.stringify(currentCharacter.value.developer_mode, null, 2)
  editPlayerJson.value = JSON.stringify(currentCharacter.value.player_mode, null, 2)
  showEditDialog.value = true
}

async function handleUpdate() {
  if (!currentCharacter.value) return

  try {
    const devMode = JSON.parse(editDevJson.value)
    const playerMode = JSON.parse(editPlayerJson.value)

    saving.value = true
    await store.updateCharacter(projectName, currentCharacter.value.id, {
      developer_mode: devMode,
      player_mode: playerMode,
    })
    showEditDialog.value = false
    showMessage('角色更新成功')
  } catch (error: any) {
    showMessage(error.message || '更新失败', 'error')
  } finally {
    saving.value = false
  }
}

// 创建
async function handleCreate() {
  try {
    await store.createCharacter({
      project_name: projectName,
      name: createForm.value.name,
      developer_mode: {
        basic: { name: createForm.value.name, summary: createForm.value.concept },
        knowledge: { background: createForm.value.concept },
      },
      player_mode: {
        basic: { name: createForm.value.name, summary: createForm.value.concept },
      },
    })
    showCreateDialog.value = false
    resetCreateForm()
    showMessage('角色创建成功')
  } catch (error: any) {
    showMessage(error.message || '创建失败', 'error')
  }
}

async function handleGenerateAndCreate() {
  if (!createForm.value.name) {
    showMessage('请先输入角色名称', 'warning')
    return
  }

  try {
    const result = await store.generateCharacter({
      project_name: projectName,
      concept: createForm.value.concept || createForm.value.name,
      character_type: createForm.value.character_type,
    })

    if (result) {
      // 确保角色名称正确
      if (result.developer_mode?.basic) {
        result.developer_mode.basic.name = createForm.value.name
      }
      if (result.player_mode?.basic) {
        result.player_mode.basic.name = createForm.value.name
      }

      await store.createCharacter({
        project_name: projectName,
        name: createForm.value.name,
        developer_mode: result.developer_mode,
        player_mode: result.player_mode,
      })
      showCreateDialog.value = false
      resetCreateForm()
      showMessage('AI生成并创建成功')
    }
  } catch (error: any) {
    showMessage(error.message || '生成失败', 'error')
  }
}

// 删除
function confirmDelete() {
  showDeleteDialog.value = true
}

async function handleDelete() {
  if (!currentCharacter.value) return
  try {
    await store.deleteCharacter(projectName, currentCharacter.value.id)
    showDeleteDialog.value = false
    showMessage('角色已删除')
  } catch (error: any) {
    showMessage(error.message || '删除失败', 'error')
  }
}

// 批量操作
function confirmBatchDelete() {
  showBatchDeleteDialog.value = true
}

async function handleBatchDelete() {
  try {
    await store.batchDeleteCharacters(projectName, selectedIds.value)
    showBatchDeleteDialog.value = false
    showMessage(`已删除 ${selectedIds.value.length} 个角色`)
  } catch (error: any) {
    showMessage(error.message || '删除失败', 'error')
  }
}

async function handleBatchGenerate() {
  const concepts = batchConcepts.value
  if (concepts.length === 0) {
    showMessage('请输入至少一个角色概念', 'warning')
    return
  }

  try {
    const results = await store.generateCharactersBatch({
      project_name: projectName,
      concepts,
      character_type: batchForm.value.character_type,
    })

    if (results && results.length > 0) {
      // 逐个创建
      let created = 0
      for (const result of results) {
        if (result && !result.error) {
          const concept = concepts[results.indexOf(result)]
          await store.createCharacter({
            project_name: projectName,
            name: result.developer_mode?.basic?.name || concept,
            developer_mode: result.developer_mode,
            player_mode: result.player_mode,
          })
          created++
        }
      }
      showBatchDialog.value = false
      batchForm.value.concepts = ''
      showMessage(`成功生成并创建 ${created} 个角色`)
    }
  } catch (error: any) {
    showMessage(error.message || '批量生成失败', 'error')
  }
}

// 导出
async function handleExportMarkdown() {
  if (!currentCharacter.value) return
  try {
    await store.exportMarkdown(projectName, currentCharacter.value.id)
    showMessage('Markdown 导出成功')
  } catch (error) {
    showMessage('导出失败', 'error')
  }
  showExportMenu.value = false
}

async function handleExportJson() {
  if (!currentCharacter.value) return
  try {
    await store.exportJson(projectName, currentCharacter.value.id)
    showMessage('JSON 导出成功')
  } catch (error) {
    showMessage('导出失败', 'error')
  }
  showExportMenu.value = false
}

async function handleExportAllMarkdown() {
  try {
    await store.exportMarkdown(projectName)
    showMessage('所有角色已导出')
  } catch (error) {
    showMessage('导出失败', 'error')
  }
  showExportMenu.value = false
}

function resetCreateForm() {
  createForm.value = { name: '', character_type: '配角', concept: '' }
}

// 监听对话框关闭
watch(showCreateDialog, (val) => {
  if (!val) resetCreateForm()
})

watch(showEditDialog, (val) => {
  if (!val) {
    editDevJson.value = ''
    editPlayerJson.value = ''
  }
})
</script>

<style scoped>
.border-left {
  border-left: 2px solid #e0e0e0;
  padding-left: 12px;
}
</style>
