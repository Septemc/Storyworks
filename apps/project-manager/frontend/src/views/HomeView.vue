<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center mb-6">
          <div>
            <h1 class="text-h4 font-weight-bold">我的项目</h1>
            <p class="text-subtitle-1 text-medium-emphasis">管理你的创作项目</p>
          </div>
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            @click="showCreateDialog = true"
          >
            创建项目
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- 项目列表 -->
    <v-row v-if="!loading && projects.length > 0">
      <v-col
        v-for="project in projects"
        :key="project.id"
        cols="12"
        sm="6"
        md="4"
        lg="3"
      >
        <v-card
          class="project-card h-100"
          hover
          @click="goToProject(project.id)"
        >
          <v-card-item>
            <template v-slot:prepend>
              <v-avatar color="primary" size="48">
                <v-icon icon="mdi-folder-text-outline" size="24"></v-icon>
              </v-avatar>
            </template>
            <v-card-title>{{ project.name }}</v-card-title>
            <v-card-subtitle>{{ project.genre || '未分类' }}</v-card-subtitle>
          </v-card-item>

          <v-card-text>
            <p class="text-body-2 text-medium-emphasis mb-3">
              {{ project.description || '暂无描述' }}
            </p>
            <div class="d-flex flex-wrap ga-1">
              <v-chip
                v-for="mod in project.modules"
                :key="mod.id"
                size="x-small"
                color="primary"
                variant="outlined"
              >
                {{ mod.name }}
              </v-chip>
              <v-chip
                v-if="!project.modules || project.modules.length === 0"
                size="x-small"
                color="grey"
                variant="outlined"
              >
                空项目
              </v-chip>
            </div>
          </v-card-text>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              variant="text"
              size="small"
              @click.stop="editProject(project)"
            >
              编辑
            </v-btn>
            <v-btn
              variant="text"
              size="small"
              color="error"
              @click.stop="confirmDelete(project)"
            >
              删除
            </v-btn>
          </v-card-actions>

          <v-divider></v-divider>
          <v-card-subtitle class="text-caption">
            更新于 {{ formatDate(project.updated_at) }}
          </v-card-subtitle>
        </v-card>
      </v-col>
    </v-row>

    <!-- 空状态 -->
    <v-row v-else-if="!loading && projects.length === 0">
      <v-col cols="12">
        <v-card class="text-center py-12">
          <v-icon icon="mdi-folder-open-outline" size="64" color="grey-lighten-1"></v-icon>
          <h3 class="text-h6 mt-4">还没有项目</h3>
          <p class="text-body-2 text-medium-emphasis mb-4">创建你的第一个项目开始创作</p>
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            @click="showCreateDialog = true"
          >
            创建项目
          </v-btn>
        </v-card>
      </v-col>
    </v-row>

    <!-- 加载状态 -->
    <v-row v-else>
      <v-col cols="12" class="text-center py-12">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
        <p class="mt-2">加载中...</p>
      </v-col>
    </v-row>

    <!-- 创建/编辑对话框 -->
    <v-dialog v-model="showCreateDialog" max-width="500">
      <v-card>
        <v-card-title>
          {{ editingProject ? '编辑项目' : '创建项目' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="formRef" v-model="formValid">
            <v-text-field
              v-model="formData.name"
              label="项目名称"
              :rules="[v => !!v || '请输入项目名称']"
              required
              class="mb-2"
            ></v-text-field>
            <v-textarea
              v-model="formData.description"
              label="项目描述"
              rows="3"
              class="mb-2"
            ></v-textarea>
            <v-select
              v-model="formData.genre"
              :items="genreOptions"
              label="题材类型"
              class="mb-2"
            ></v-select>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showCreateDialog = false">取消</v-btn>
          <v-btn
            color="primary"
            :disabled="!formValid"
            @click="handleSubmit"
          >
            {{ editingProject ? '保存' : '创建' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认对话框 -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>
          确定要删除项目 "{{ deletingProject?.name }}" 吗？此操作不可撤销。
        </v-card-text>
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
import { useRouter } from 'vue-router'
import { useProjectStore, type Project } from '@/stores/project'

const router = useRouter()
const projectStore = useProjectStore()

const { projects, loading } = storeToRefs(projectStore)

const showCreateDialog = ref(false)
const showDeleteDialog = ref(false)
const formValid = ref(false)
const formRef = ref<any>(null)
const editingProject = ref<Project | null>(null)
const deletingProject = ref<Project | null>(null)

const formData = ref({
  name: '',
  description: '',
  genre: '',
})

const genreOptions = [
  '奇幻',
  '科幻',
  '武侠',
  '悬疑',
  '历史',
  '现代',
  '古风',
  '末日',
  '其他',
]

onMounted(() => {
  projectStore.fetchProjects()
})

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

function goToProject(id: string) {
  router.push(`/project/${id}`)
}

function editProject(project: Project) {
  editingProject.value = project
  formData.value = {
    name: project.name,
    description: project.description || '',
    genre: project.genre || '',
  }
  showCreateDialog.value = true
}

function confirmDelete(project: Project) {
  deletingProject.value = project
  showDeleteDialog.value = true
}

async function handleSubmit() {
  try {
    if (editingProject.value) {
      await projectStore.updateProject(editingProject.value.id, formData.value)
    } else {
      await projectStore.createProject(formData.value)
    }
    showCreateDialog.value = false
    resetForm()
  } catch (error: any) {
    alert(error.message || '操作失败')
  }
}

async function handleDelete() {
  if (!deletingProject.value) return
  try {
    await projectStore.deleteProject(deletingProject.value.id)
    showDeleteDialog.value = false
    deletingProject.value = null
  } catch (error: any) {
    alert(error.message || '删除失败')
  }
}

function resetForm() {
  editingProject.value = null
  formData.value = { name: '', description: '', genre: '' }
}

// 监听对话框关闭
watch(showCreateDialog, (val) => {
  if (!val) resetForm()
})
</script>

<style scoped>
.project-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.project-card:hover {
  transform: translateY(-2px);
}
</style>
