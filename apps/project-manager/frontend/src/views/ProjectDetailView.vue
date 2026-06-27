<template>
  <v-container>
    <!-- 返回按钮 -->
    <v-btn
      variant="text"
      prepend-icon="mdi-arrow-left"
      class="mb-4"
      @click="router.push('/')"
    >
      返回项目列表
    </v-btn>

    <!-- 加载中 -->
    <div v-if="loading" class="text-center py-12">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
    </div>

    <!-- 项目详情 -->
    <template v-else-if="currentProject">
      <v-row>
        <v-col cols="12">
          <div class="d-flex justify-space-between align-center mb-6">
            <div>
              <h1 class="text-h4 font-weight-bold">{{ currentProject.name }}</h1>
              <p class="text-subtitle-1 text-medium-emphasis">
                {{ currentProject.description || '暂无描述' }}
              </p>
              <v-chip v-if="currentProject.genre" size="small" color="primary" class="mt-1">
                {{ currentProject.genre }}
              </v-chip>
            </div>
            <v-btn
              variant="outlined"
              prepend-icon="mdi-pencil"
              @click="showEditDialog = true"
            >
              编辑项目
            </v-btn>
          </div>
        </v-col>
      </v-row>

      <!-- 功能模块 -->
      <v-row>
        <v-col cols="12">
          <h2 class="text-h5 mb-4">功能模块</h2>
        </v-col>

        <v-col
          v-for="mod in modules"
          :key="mod.id"
          cols="12"
          sm="6"
          md="3"
        >
          <v-card
            class="module-card h-100"
            hover
            @click="openModule(mod)"
          >
            <v-card-item>
              <template v-slot:prepend>
                <v-avatar :color="mod.color" size="48">
                  <v-icon :icon="mod.icon" size="24"></v-icon>
                </v-avatar>
              </template>
              <v-card-title>{{ mod.name }}</v-card-title>
              <v-card-subtitle>{{ mod.description }}</v-card-subtitle>
            </v-card-item>

            <v-card-text>
              <v-chip
                size="small"
                :color="isModuleInitialized(mod.id) ? 'success' : 'grey'"
                variant="outlined"
              >
                {{ isModuleInitialized(mod.id) ? '已初始化' : '未初始化' }}
              </v-chip>
            </v-card-text>

            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn
                v-if="!isModuleInitialized(mod.id)"
                size="small"
                color="primary"
                variant="tonal"
                @click.stop="initModule(mod.id)"
              >
                初始化
              </v-btn>
              <v-btn
                size="small"
                color="primary"
                append-icon="mdi-open-in-new"
              >
                打开
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>

      <!-- 项目信息 -->
      <v-row class="mt-6">
        <v-col cols="12" md="6">
          <v-card>
            <v-card-title>项目信息</v-card-title>
            <v-card-text>
              <v-table>
                <tbody>
                  <tr>
                    <td class="text-medium-emphasis">项目ID</td>
                    <td>{{ currentProject.id }}</td>
                  </tr>
                  <tr>
                    <td class="text-medium-emphasis">创建时间</td>
                    <td>{{ formatDate(currentProject.created_at) }}</td>
                  </tr>
                  <tr>
                    <td class="text-medium-emphasis">更新时间</td>
                    <td>{{ formatDate(currentProject.updated_at) }}</td>
                  </tr>
                </tbody>
              </v-table>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>

    <!-- 编辑对话框 -->
    <v-dialog v-model="showEditDialog" max-width="500">
      <v-card>
        <v-card-title>编辑项目</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="editForm.name"
            label="项目名称"
            class="mb-2"
          ></v-text-field>
          <v-textarea
            v-model="editForm.description"
            label="项目描述"
            rows="3"
            class="mb-2"
          ></v-textarea>
          <v-select
            v-model="editForm.genre"
            :items="genreOptions"
            label="题材类型"
          ></v-select>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showEditDialog = false">取消</v-btn>
          <v-btn color="primary" @click="handleUpdate">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const { currentProject, loading } = storeToRefs(projectStore)

const showEditDialog = ref(false)
const editForm = ref({
  name: '',
  description: '',
  genre: '',
})

const genreOptions = [
  '奇幻', '科幻', '武侠', '悬疑', '历史', '现代', '古风', '末日', '其他',
]

const modules = [
  {
    id: 'worldbook',
    name: '世界书',
    description: '世界观设定生成器',
    icon: 'mdi-book-open-variant',
    color: 'blue',
    port: 8001,
  },
  {
    id: 'characters',
    name: '人物卡',
    description: '角色资料生成器',
    icon: 'mdi-account-group',
    color: 'green',
    port: 8002,
  },
  {
    id: 'scripts',
    name: '剧本',
    description: '剧情结构生成器',
    icon: 'mdi-script-text',
    color: 'orange',
    port: 8003,
  },
  {
    id: 'presets',
    name: '预设',
    description: '风格预设生成器',
    icon: 'mdi-palette',
    color: 'purple',
    port: 8004,
  },
]

const projectId = computed(() => route.params.id as string)

onMounted(() => {
  if (projectId.value) {
    projectStore.fetchProject(projectId.value)
  }
})

watch(projectId, (newId) => {
  if (newId) {
    projectStore.fetchProject(newId)
  }
})

watch(currentProject, (project) => {
  if (project) {
    editForm.value = {
      name: project.name,
      description: project.description || '',
      genre: project.genre || '',
    }
  }
})

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

function isModuleInitialized(moduleId: string) {
  return currentProject.value?.modules?.some(m => m.id === moduleId) || false
}

function openModule(mod: any) {
  if (!isModuleInitialized(mod.id)) {
    alert('请先初始化该模块')
    return
  }
  // 在新窗口打开模块应用
  const url = `http://127.0.0.1:${mod.port}?project=${currentProject.value?.name}`
  window.open(url, '_blank')
}

async function initModule(moduleId: string) {
  // 初始化模块（创建目录和数据库）
  alert(`模块 ${moduleId} 初始化功能待实现`)
}

async function handleUpdate() {
  try {
    await projectStore.updateProject(projectId.value, editForm.value)
    showEditDialog.value = false
  } catch (error: any) {
    alert(error.message || '更新失败')
  }
}
</script>

<style scoped>
.module-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.module-card:hover {
  transform: translateY(-2px);
}
</style>
