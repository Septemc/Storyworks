<template>
  <v-container fluid>
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
              <template v-slot:prepend>
                <v-icon :icon="cat.icon" size="20"></v-icon>
              </template>
              <v-list-item-title>{{ cat.name }}</v-list-item-title>
              <template v-slot:append>
                <v-badge
                  :content="getCategoryCount(cat.id)"
                  color="primary"
                  inline
                ></v-badge>
              </template>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <!-- 中间条目列表 -->
      <v-col cols="4">
        <v-card class="h-100">
          <v-card-title class="d-flex justify-space-between align-center">
            <span>条目列表</span>
            <v-btn
              size="small"
              color="primary"
              prepend-icon="mdi-plus"
              @click="showCreateDialog = true"
            >
              新建
            </v-btn>
          </v-card-title>

          <v-divider></v-divider>

          <v-list v-if="filteredEntries.length > 0" lines="two" select-strategy="single">
            <v-list-item
              v-for="entry in filteredEntries"
              :key="entry.id"
              :value="entry.id"
              :active="currentEntry?.id === entry.id"
              @click="selectEntry(entry)"
            >
              <v-list-item-title>{{ entry.title }}</v-list-item-title>
              <v-list-item-subtitle>{{ entry.summary || '暂无摘要' }}</v-list-item-subtitle>
              <template v-slot:append>
                <v-chip size="x-small" :color="getStatusColor(entry.status)">
                  {{ getStatusText(entry.status) }}
                </v-chip>
              </template>
            </v-list-item>
          </v-list>

          <div v-else class="text-center py-8 text-medium-emphasis">
            <v-icon icon="mdi-file-document-outline" size="48" color="grey-lighten-1"></v-icon>
            <p class="mt-2">暂无条目</p>
          </div>
        </v-card>
      </v-col>

      <!-- 右侧编辑区 -->
      <v-col cols="6">
        <v-card class="h-100">
          <template v-if="currentEntry">
            <v-card-title class="d-flex justify-space-between align-center">
              <span>{{ currentEntry.title }}</span>
              <div>
                <v-btn
                  size="small"
                  variant="text"
                  prepend-icon="mdi-pencil"
                  @click="showEditDialog = true"
                >
                  编辑
                </v-btn>
                <v-btn
                  size="small"
                  variant="text"
                  color="error"
                  prepend-icon="mdi-delete"
                  @click="confirmDelete"
                >
                  删除
                </v-btn>
              </div>
            </v-card-title>

            <v-divider></v-divider>

            <v-card-text class="entry-content">
              <div class="mb-4">
                <v-chip size="small" color="primary" class="mr-2">
                  {{ getCategoryName(currentEntry.category) }}
                </v-chip>
                <v-chip size="small" :color="getStatusColor(currentEntry.status)">
                  {{ getStatusText(currentEntry.status) }}
                </v-chip>
              </div>

              <div v-if="currentEntry.summary" class="mb-4">
                <h4 class="text-subtitle-2 mb-1">摘要</h4>
                <p>{{ currentEntry.summary }}</p>
              </div>

              <div v-if="currentEntry.content" class="mb-4">
                <h4 class="text-subtitle-2 mb-1">正文</h4>
                <div class="content-text" v-html="formatContent(currentEntry.content)"></div>
              </div>

              <div v-if="currentEntry.keywords?.length" class="mb-4">
                <h4 class="text-subtitle-2 mb-1">关键词</h4>
                <v-chip
                  v-for="keyword in currentEntry.keywords"
                  :key="keyword"
                  size="small"
                  class="mr-1 mb-1"
                >
                  {{ keyword }}
                </v-chip>
              </div>

              <div v-if="currentEntry.notes" class="mb-4">
                <h4 class="text-subtitle-2 mb-1">备注</h4>
                <p class="text-body-2 text-medium-emphasis">{{ currentEntry.notes }}</p>
              </div>
            </v-card-text>
          </template>

          <template v-else>
            <div class="d-flex flex-column align-center justify-center h-100 text-medium-emphasis">
              <v-icon icon="mdi-cursor-default-click-outline" size="64" color="grey-lighten-1"></v-icon>
              <p class="mt-4">选择一个条目查看详情</p>
            </div>
          </template>
        </v-card>
      </v-col>
    </v-row>

    <!-- 创建/编辑对话框 -->
    <v-dialog v-model="showCreateDialog" max-width="800">
      <v-card>
        <v-card-title>{{ editingEntry ? '编辑条目' : '新建条目' }}</v-card-title>
        <v-card-text>
          <v-form ref="formRef" v-model="formValid">
            <v-row>
              <v-col cols="6">
                <v-select
                  v-model="formData.category"
                  :items="categories"
                  item-title="name"
                  item-value="id"
                  label="分类"
                  :rules="[v => !!v || '请选择分类']"
                  required
                ></v-select>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="formData.title"
                  label="标题"
                  :rules="[v => !!v || '请输入标题']"
                  required
                ></v-text-field>
              </v-col>
            </v-row>

            <v-textarea
              v-model="formData.summary"
              label="摘要"
              rows="2"
              class="mb-2"
            ></v-textarea>

            <v-textarea
              v-model="formData.content"
              label="正文"
              rows="8"
              class="mb-2"
            ></v-textarea>

            <v-combobox
              v-model="formData.keywords"
              label="关键词"
              multiple
              chips
              class="mb-2"
            ></v-combobox>

            <v-textarea
              v-model="formData.notes"
              label="备注"
              rows="2"
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showCreateDialog = false">取消</v-btn>
          <v-btn color="secondary" prepend-icon="mdi-robot" @click="handleGenerate" :loading="generating">
            AI 生成
          </v-btn>
          <v-btn color="primary" :disabled="!formValid" @click="handleSubmit">
            {{ editingEntry ? '保存' : '创建' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认 -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>确定要删除条目 "{{ currentEntry?.title }}" 吗？</v-card-text>
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
import { useWorldbookStore, type WorldbookEntry } from '@/stores/worldbook'

const store = useWorldbookStore()
const { entries, categories, currentEntry, loading, generating } = storeToRefs(store)

const selectedCategory = ref('')
const showCreateDialog = ref(false)
const showDeleteDialog = ref(false)
const formValid = ref(false)
const formRef = ref<any>(null)
const editingEntry = ref<WorldbookEntry | null>(null)

const formData = ref({
  category: '',
  title: '',
  summary: '',
  content: '',
  keywords: [] as string[],
  notes: '',
})

// 从 URL 获取项目名
const urlParams = new URLSearchParams(window.location.search)
const projectName = urlParams.get('project') || 'demo'

const filteredEntries = computed(() => {
  if (!selectedCategory.value) return entries
  return entries.filter(e => e.category === selectedCategory.value)
})

onMounted async () => {
  await store.fetchCategories()
  if (projectName) {
    await store.fetchEntries(projectName)
  }
}

function getCategoryCount(categoryId: string) {
  return entries.filter(e => e.category === categoryId).length
}

function getCategoryName(categoryId: string) {
  return categories.find(c => c.id === categoryId)?.name || categoryId
}

function getStatusColor(status: string) {
  const map: Record<string, string> = {
    draft: 'grey',
    ready: 'success',
    final: 'primary',
    archived: 'warning',
  }
  return map[status] || 'grey'
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    draft: '草稿',
    ready: '可用',
    final: '定稿',
    archived: '归档',
  }
  return map[status] || status
}

function formatContent(content: string) {
  if (!content) return ''
  return content.replace(/\n/g, '<br>')
}

function selectEntry(entry: WorldbookEntry) {
  store.currentEntry = entry
}

function editEntry(entry: WorldbookEntry) {
  editingEntry.value = entry
  formData.value = {
    category: entry.category,
    title: entry.title,
    summary: entry.summary || '',
    content: entry.content || '',
    keywords: [...(entry.keywords || [])],
    notes: entry.notes || '',
  }
  showCreateDialog.value = true
}

function confirmDelete() {
  showDeleteDialog.value = true
}

async function handleSubmit() {
  try {
    const data = {
      project_name: projectName,
      ...formData.value,
    }

    if (editingEntry.value) {
      await store.updateEntry(projectName, editingEntry.value.id, data)
    } else {
      await store.createEntry(data)
    }
    showCreateDialog.value = false
    resetForm()
  } catch (error: any) {
    alert(error.message || '操作失败')
  }
}

async function handleGenerate() {
  if (!formData.value.category || !formData.value.title) {
    alert('请先填写分类和标题')
    return
  }

  try {
    const result = await store.generateEntry({
      project_name: projectName,
      category: formData.value.category,
      title: formData.value.title,
      summary: formData.value.summary,
    })

    if (result?.content) {
      formData.value.content = result.content
    }
  } catch (error: any) {
    alert(error.message || '生成失败')
  }
}

async function handleDelete() {
  if (!currentEntry.value) return
  try {
    await store.deleteEntry(projectName, currentEntry.value.id)
    showDeleteDialog.value = false
  } catch (error: any) {
    alert(error.message || '删除失败')
  }
}

function resetForm() {
  editingEntry.value = null
  formData.value = {
    category: '',
    title: '',
    summary: '',
    content: '',
    keywords: [],
    notes: '',
  }
}

// 监听对话框关闭
watch(showCreateDialog, (val) => {
  if (!val) resetForm()
})

// 监听编辑按钮
watch(currentEntry, (entry) => {
  if (entry) {
    // 可以在这里做些处理
  }
})
</script>

<style scoped>
.entry-content {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.content-text {
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
