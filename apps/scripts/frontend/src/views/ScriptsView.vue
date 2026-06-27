<template>
  <v-container fluid>
    <v-row>
      <!-- 左侧大纲树 -->
      <v-col cols="3">
        <v-card class="h-100">
          <v-card-title class="d-flex justify-space-between align-center">
            <span>剧本大纲</span>
            <v-btn size="small" color="primary" prepend-icon="mdi-plus" @click="showCreateDialog = true">
              新建
            </v-btn>
          </v-card-title>
          <v-divider></v-divider>
          <v-list v-if="scriptTree.length > 0">
            <template v-for="script in scriptTree" :key="script.id">
              <v-list-item
                :value="script.id"
                :active="currentScript?.id === script.id"
                @click="selectScript(script)"
              >
                <template v-slot:prepend>
                  <v-icon icon="mdi-file-document-outline" size="20"></v-icon>
                </template>
                <v-list-item-title>{{ script.title }}</v-list-item-title>
              </v-list-item>
              <v-list-item
                v-for="child in script.children"
                :key="child.id"
                :value="child.id"
                :active="currentScript?.id === child.id"
                class="ml-4"
                @click="selectScript(child)"
              >
                <template v-slot:prepend>
                  <v-icon :icon="getTypeIcon(child.type)" size="18"></v-icon>
                </template>
                <v-list-item-title class="text-body-2">{{ child.title }}</v-list-item-title>
              </v-list-item>
            </template>
          </v-list>
          <div v-else class="text-center py-8 text-medium-emphasis">
            <v-icon icon="mdi-script-outline" size="48" color="grey-lighten-1"></v-icon>
            <p class="mt-2">暂无剧本</p>
          </div>
        </v-card>
      </v-col>

      <!-- 右侧编辑区 -->
      <v-col cols="9">
        <v-card class="h-100">
          <template v-if="currentScript">
            <v-card-title class="d-flex justify-space-between align-center">
              <span>{{ currentScript.title }}</span>
              <div>
                <v-btn size="small" variant="text" prepend-icon="mdi-pencil" @click="editScript">
                  编辑
                </v-btn>
                <v-btn size="small" variant="text" color="error" @click="confirmDelete">
                  删除
                </v-btn>
              </div>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text>
              <v-row>
                <v-col cols="12">
                  <div class="mb-4">
                    <v-chip size="small" color="primary" class="mr-2">
                      {{ getTypeName(currentScript.type) }}
                    </v-chip>
                    <v-chip size="small" :color="getStatusColor(currentScript.status)">
                      {{ getStatusText(currentScript.status) }}
                    </v-chip>
                  </div>

                  <div v-if="currentScript.content?.summary" class="mb-4">
                    <h4 class="text-subtitle-2 mb-1">摘要</h4>
                    <p>{{ currentScript.content.summary }}</p>
                  </div>

                  <div v-if="currentScript.content?.theme" class="mb-4">
                    <h4 class="text-subtitle-2 mb-1">主题</h4>
                    <p>{{ currentScript.content.theme }}</p>
                  </div>

                  <div v-if="currentScript.content?.main_conflict" class="mb-4">
                    <h4 class="text-subtitle-2 mb-1">核心冲突</h4>
                    <p>{{ currentScript.content.main_conflict }}</p>
                  </div>

                  <div v-if="currentScript.content?.acts?.length" class="mb-4">
                    <h4 class="text-subtitle-2 mb-1">章节结构</h4>
                    <v-timeline density="compact" side="end">
                      <v-timeline-item
                        v-for="act in currentScript.content.acts"
                        :key="act.act"
                        dot-color="primary"
                        size="small"
                      >
                        <div class="text-subtitle-2">{{ act.title }}</div>
                        <div class="text-body-2 text-medium-emphasis">{{ act.description }}</div>
                      </v-timeline-item>
                    </v-timeline>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </template>
          <template v-else>
            <div class="d-flex flex-column align-center justify-center h-100 text-medium-emphasis">
              <v-icon icon="mdi-script-outline" size="64" color="grey-lighten-1"></v-icon>
              <p class="mt-4">选择或创建一个剧本</p>
            </div>
          </template>
        </v-card>
      </v-col>
    </v-row>

    <!-- 创建对话框 -->
    <v-dialog v-model="showCreateDialog" max-width="600">
      <v-card>
        <v-card-title>创建剧本</v-card-title>
        <v-card-text>
          <v-form ref="formRef" v-model="formValid">
            <v-select
              v-model="formData.type"
              :items="typeOptions"
              item-title="label"
              item-value="value"
              label="类型"
              class="mb-2"
            ></v-select>
            <v-text-field
              v-model="formData.title"
              label="标题"
              :rules="[v => !!v || '请输入标题']"
              required
              class="mb-2"
            ></v-text-field>
            <v-textarea
              v-model="formData.concept"
              label="故事概念"
              hint="描述你的故事核心想法"
              rows="3"
            ></v-textarea>
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
        <v-card-text>确定要删除 "{{ currentScript?.title }}" 吗？子剧本也会被删除。</v-card-text>
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
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useScriptStore, type Script } from '@/stores/script'

const store = useScriptStore()
const { scriptTree, currentScript, loading, generating } = storeToRefs(store)

const showCreateDialog = ref(false)
const showDeleteDialog = ref(false)
const formValid = ref(false)
const formRef = ref<any>(null)

const formData = ref({
  type: 'outline',
  title: '',
  concept: '',
})

const typeOptions = [
  { value: 'outline', label: '总纲' },
  { value: 'act', label: '篇章' },
  { value: 'chapter', label: '章节' },
  { value: 'scene', label: '场景' },
]

const urlParams = new URLSearchParams(window.location.search)
const projectName = urlParams.get('project') || 'demo'

onMounted(() => {
  if (projectName) {
    store.fetchScriptTree(projectName)
  }
})

function getTypeIcon(type: string) {
  const icons: Record<string, string> = {
    outline: 'mdi-file-document-outline',
    act: 'mdi-book-open-variant',
    chapter: 'mdi-book-open-page-variant',
    scene: 'mdi-movie-open-outline',
  }
  return icons[type] || 'mdi-file-outline'
}

function getTypeName(type: string) {
  const names: Record<string, string> = {
    outline: '总纲',
    act: '篇章',
    chapter: '章节',
    scene: '场景',
  }
  return names[type] || type
}

function getStatusColor(status: string) {
  const map: Record<string, string> = { draft: 'grey', ready: 'success', final: 'primary' }
  return map[status] || 'grey'
}

function getStatusText(status: string) {
  const map: Record<string, string> = { draft: '草稿', ready: '可用', final: '定稿' }
  return map[status] || status
}

function selectScript(script: Script) {
  store.currentScript = script
}

function editScript() {
  alert('编辑功能待实现')
}

function confirmDelete() {
  showDeleteDialog.value = true
}

async function handleCreate() {
  try {
    await store.createScript({
      project_name: projectName,
      title: formData.value.title,
      type: formData.value.type,
      content: { summary: formData.value.concept },
    })
    showCreateDialog.value = false
    formData.value = { type: 'outline', title: '', concept: '' }
  } catch (error: any) {
    alert(error.message || '创建失败')
  }
}

async function handleGenerate() {
  if (!formData.value.title) {
    alert('请先输入标题')
    return
  }
  try {
    const result = await store.generateScript({
      project_name: projectName,
      concept: formData.value.concept || formData.value.title,
    })
    if (result) {
      await store.createScript({
        project_name: projectName,
        title: result.title || formData.value.title,
        type: formData.value.type,
        content: result,
      })
      showCreateDialog.value = false
      formData.value = { type: 'outline', title: '', concept: '' }
    }
  } catch (error: any) {
    alert(error.message || '生成失败')
  }
}

async function handleDelete() {
  if (!currentScript.value) return
  try {
    await store.deleteScript(projectName, currentScript.value.id)
    showDeleteDialog.value = false
  } catch (error: any) {
    alert(error.message || '删除失败')
  }
}
</script>
