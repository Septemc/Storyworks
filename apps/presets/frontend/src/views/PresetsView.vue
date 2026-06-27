<template>
  <v-container>
    <v-row>
      <!-- 左侧分类 -->
      <v-col cols="2">
        <v-card class="h-100">
          <v-card-title class="text-subtitle-1">分类</v-card-title>
          <v-list density="compact" nav>
            <v-list-item
              v-for="cat in categories"
              :key="cat.id"
              :value="cat.id"
              :active="selectedCategory === cat.id"
              @click="selectedCategory = cat.id"
            >
              <v-list-item-title>{{ cat.name }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <!-- 中间列表 -->
      <v-col cols="4">
        <v-card class="h-100">
          <v-card-title class="d-flex justify-space-between align-center">
            <span>预设列表</span>
            <v-btn size="small" color="primary" prepend-icon="mdi-plus" @click="showCreateDialog = true">
              新建
            </v-btn>
          </v-card-title>
          <v-divider></v-divider>
          <v-list v-if="filteredPresets.length > 0" lines="two" select-strategy="single">
            <v-list-item
              v-for="preset in filteredPresets"
              :key="preset.id"
              :value="preset.id"
              :active="currentPreset?.id === preset.id"
              @click="selectPreset(preset)"
            >
              <v-list-item-title>{{ preset.name }}</v-list-item-title>
              <v-list-item-subtitle>{{ preset.description || '暂无描述' }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
          <div v-else class="text-center py-8 text-medium-emphasis">
            <v-icon icon="mdi-palette-outline" size="48" color="grey-lighten-1"></v-icon>
            <p class="mt-2">暂无预设</p>
          </div>
        </v-card>
      </v-col>

      <!-- 右侧详情 -->
      <v-col cols="6">
        <v-card class="h-100">
          <template v-if="currentPreset">
            <v-card-title class="d-flex justify-space-between align-center">
              <span>{{ currentPreset.name }}</span>
              <div>
                <v-btn size="small" variant="text" prepend-icon="mdi-pencil" @click="editPreset">
                  编辑
                </v-btn>
                <v-btn size="small" variant="text" color="error" @click="confirmDelete">
                  删除
                </v-btn>
              </div>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text>
              <div class="mb-4">
                <v-chip size="small" color="primary" class="mr-2">
                  {{ getCategoryName(currentPreset.category) }}
                </v-chip>
              </div>

              <div v-if="currentPreset.description" class="mb-4">
                <h4 class="text-subtitle-2 mb-1">描述</h4>
                <p>{{ currentPreset.description }}</p>
              </div>

              <div class="mb-4">
                <h4 class="text-subtitle-2 mb-1">预设参数</h4>
                <v-table density="compact">
                  <tbody>
                    <tr v-for="(value, key) in currentPreset.content" :key="key">
                      <td class="text-medium-emphasis" style="width: 120px">{{ getParamLabel(key) }}</td>
                      <td>{{ formatParamValue(value) }}</td>
                    </tr>
                  </tbody>
                </v-table>
              </div>
            </v-card-text>
          </template>
          <template v-else>
            <div class="d-flex flex-column align-center justify-center h-100 text-medium-emphasis">
              <v-icon icon="mdi-palette-outline" size="64" color="grey-lighten-1"></v-icon>
              <p class="mt-4">选择一个预设查看详情</p>
            </div>
          </template>
        </v-card>
      </v-col>
    </v-row>

    <!-- 创建对话框 -->
    <v-dialog v-model="showCreateDialog" max-width="700">
      <v-card>
        <v-card-title>创建预设</v-card-title>
        <v-card-text>
          <v-form ref="formRef" v-model="formValid">
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="formData.name"
                  label="预设名称"
                  :rules="[v => !!v || '请输入名称']"
                  required
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-select
                  v-model="formData.category"
                  :items="categories"
                  item-title="name"
                  item-value="id"
                  label="分类"
                ></v-select>
              </v-col>
            </v-row>
            <v-textarea
              v-model="formData.description"
              label="描述"
              rows="2"
              class="mb-2"
            ></v-textarea>

            <h4 class="text-subtitle-2 mb-2">预设参数</h4>
            <v-row>
              <v-col cols="6">
                <v-text-field v-model="formData.content.style" label="风格" dense></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field v-model="formData.content.word_tendency" label="用词倾向" dense></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field v-model="formData.content.sentence_pattern" label="句式倾向" dense></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field v-model="formData.content.description_density" label="描写密度" dense></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field v-model="formData.content.dialogue_ratio" label="对白比例" dense></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field v-model="formData.content.rhythm" label="节奏" dense></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-textarea v-model="formData.content.forbidden_expression" label="禁止表达（每行一个）" rows="2" dense></v-textarea>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showCreateDialog = false">取消</v-btn>
          <v-btn color="secondary" prepend-icon="mdi-robot" @click="handleGenerate" :loading="generating">
            AI 生成
          </v-btn>
          <v-btn color="primary" :disabled="!formValid" @click="handleCreate">
            创建
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认 -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>确定要删除预设 "{{ currentPreset?.name }}" 吗？</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showDeleteDialog = false">取消</v-btn>
          <v-btn color="error" @click="handleDelete">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { usePresetStore, type Preset } from '@/stores/preset'

const store = usePresetStore()
const { presets, currentPreset, loading, generating } = storeToRefs(store)

const selectedCategory = ref('')
const showCreateDialog = ref(false)
const showDeleteDialog = ref(false)
const formValid = ref(false)
const formRef = ref<any>(null)

const formData = ref({
  name: '',
  category: 'style',
  description: '',
  content: {
    style: '',
    word_tendency: '',
    sentence_pattern: '',
    description_density: '',
    dialogue_ratio: '',
    rhythm: '',
    forbidden_expression: '',
  },
})

const categories = [
  { id: 'style', name: '文风' },
  { id: 'genre', name: '题材' },
  { id: 'plot', name: '剧情偏好' },
  { id: 'character', name: '人物塑造' },
  { id: 'quality', name: '质量' },
  { id: 'format', name: '输出格式' },
]

const urlParams = new URLSearchParams(window.location.search)
const projectName = urlParams.get('project') || 'demo'

const filteredPresets = computed(() => {
  if (!selectedCategory.value) return presets
  return presets.filter(p => p.category === selectedCategory.value)
})

onMounted(() => {
  if (projectName) {
    store.fetchPresets(projectName)
  }
})

function getCategoryName(categoryId?: string) {
  return categories.find(c => c.id === categoryId)?.name || categoryId || '未分类'
}

function getParamLabel(key: string) {
  const labels: Record<string, string> = {
    style: '风格',
    word_tendency: '用词倾向',
    sentence_pattern: '句式倾向',
    description_density: '描写密度',
    dialogue_ratio: '对白比例',
    rhythm: '节奏',
    emotion_intensity: '情感浓度',
    plot_preference: '剧情偏好',
    character_portrayal: '人物刻画',
    forbidden_expression: '禁止表达',
    output_requirements: '输出要求',
  }
  return labels[key] || key
}

function formatParamValue(value: any) {
  if (Array.isArray(value)) return value.join('、')
  return value || '未设置'
}

function selectPreset(preset: Preset) {
  store.currentPreset = preset
}

function editPreset() {
  alert('编辑功能待实现')
}

function confirmDelete() {
  showDeleteDialog.value = true
}

async function handleCreate() {
  try {
    const content = { ...formData.value.content }
    if (content.forbidden_expression) {
      content.forbidden_expression = content.forbidden_expression.split('\n').filter(Boolean)
    }

    await store.createPreset({
      project_name: projectName,
      name: formData.value.name,
      category: formData.value.category,
      description: formData.value.description,
      content,
    })
    showCreateDialog.value = false
    resetForm()
  } catch (error: any) {
    alert(error.message || '创建失败')
  }
}

async function handleGenerate() {
  if (!formData.value.name) {
    alert('请先输入预设名称')
    return
  }
  try {
    const result = await store.generatePreset({
      project_name: projectName,
      description: formData.value.description || formData.value.name,
      category: formData.value.category,
    })
    if (result) {
      formData.value.content = {
        style: result.style || '',
        word_tendency: result.word_tendency || '',
        sentence_pattern: result.sentence_pattern || '',
        description_density: result.description_density || '',
        dialogue_ratio: result.dialogue_ratio || '',
        rhythm: result.rhythm || '',
        forbidden_expression: Array.isArray(result.forbidden_expression) ? result.forbidden_expression.join('\n') : '',
      }
    }
  } catch (error: any) {
    alert(error.message || '生成失败')
  }
}

async function handleDelete() {
  if (!currentPreset.value) return
  try {
    await store.deletePreset(projectName, currentPreset.value.id)
    showDeleteDialog.value = false
  } catch (error: any) {
    alert(error.message || '删除失败')
  }
}

function resetForm() {
  formData.value = {
    name: '',
    category: 'style',
    description: '',
    content: { style: '', word_tendency: '', sentence_pattern: '', description_density: '', dialogue_ratio: '', rhythm: '', forbidden_expression: '' },
  }
}

watch(showCreateDialog, (val) => {
  if (!val) resetForm()
})
</script>
