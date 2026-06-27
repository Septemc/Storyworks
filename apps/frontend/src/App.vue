<template>
  <v-app>
    <v-app-bar flat border color="surface">
      <v-app-bar-title class="font-weight-bold">Storyworks</v-app-bar-title>
      <v-select
        v-model="activeProjectId"
        :items="projects"
        item-title="name"
        item-value="id"
        label="项目"
        density="compact"
        hide-details
        style="max-width: 280px"
      />
      <v-btn icon="mdi-plus" variant="text" class="ml-2" aria-label="创建项目" @click="openProjectDialog" />
      <v-btn icon="mdi-refresh" variant="text" aria-label="刷新" @click="reloadCurrent" />
      <v-btn icon="mdi-cog-outline" variant="text" aria-label="设置" @click="openSettingsDialog" />
    </v-app-bar>

    <v-navigation-drawer permanent width="220">
      <v-list nav density="comfortable">
        <v-list-item
          v-for="item in modules"
          :key="item.id"
          :active="activeModule === item.id"
          :prepend-icon="item.icon"
          :title="item.title"
          @click="activeModule = item.id"
        />
      </v-list>
      <template #append>
        <div class="pa-3 text-caption muted">
          {{ selectedProject?.name || '未选择项目' }}
        </div>
      </template>
    </v-navigation-drawer>

    <v-main>
      <v-window v-model="activeModule" class="workbench">
        <v-window-item value="overview" class="h-100">
          <section class="pane h-100">
            <div class="pane-header d-flex align-center justify-space-between">
              <div>
                <div class="text-h6">项目总览</div>
                <div class="text-body-2 muted">统一管理世界书、人物卡、剧本和预设</div>
              </div>
              <div class="d-flex ga-2">
                <v-switch v-model="projectShowArchived" density="compact" hide-details color="primary" label="显示归档" />
                <v-btn variant="text" prepend-icon="mdi-shield-check-outline" @click="runConsistencyCheck">数据检查</v-btn>
                <v-btn variant="text" prepend-icon="mdi-import" @click="openProjectImportDialog">导入项目</v-btn>
                <v-btn variant="text" prepend-icon="mdi-export" :disabled="!activeProjectId" @click="exportProject">导出项目</v-btn>
                <v-btn color="primary" prepend-icon="mdi-plus" @click="openProjectDialog">新建项目</v-btn>
              </div>
            </div>
            <div class="detail-body">
              <v-row>
                <v-col v-for="project in projects" :key="project.id" cols="12" md="6" lg="4">
                  <v-sheet border rounded="sm" class="pa-4 h-100" @click="activeProjectId = project.id">
                    <div class="d-flex align-start justify-space-between">
                      <div>
                        <div class="text-subtitle-1 font-weight-medium">{{ project.name }}</div>
                        <div class="text-body-2 muted">{{ project.genre || '未分类' }}</div>
                      </div>
                      <div class="d-flex align-center ga-1">
                        <v-chip v-if="project.status === 'archived'" size="x-small" color="warning" variant="tonal">归档</v-chip>
                        <v-btn icon="mdi-pencil-outline" size="small" variant="text" aria-label="编辑项目" @click.stop="openProjectDialog(project)" />
                        <v-btn
                          :icon="project.status === 'archived' ? 'mdi-archive-arrow-up-outline' : 'mdi-archive-outline'"
                          size="small"
                          variant="text"
                          :aria-label="project.status === 'archived' ? '恢复项目' : '归档项目'"
                          @click.stop="archiveProject(project, project.status !== 'archived')"
                        />
                        <v-btn v-if="project.is_demo" icon="mdi-restore" size="small" variant="text" aria-label="重置Demo" @click.stop="resetDemoProject(project)" />
                        <v-btn v-else icon="mdi-delete-outline" size="small" variant="text" color="error" aria-label="删除项目" @click.stop="openProjectDeleteDialog(project)" />
                      </div>
                    </div>
                    <p class="text-body-2 mt-3 mb-4">{{ project.description || '暂无描述' }}</p>
                    <div class="d-flex flex-wrap ga-2">
                      <v-chip size="small" variant="tonal">世界书 {{ project.counts?.worldbook || 0 }}</v-chip>
                      <v-chip size="small" variant="tonal">人物 {{ project.counts?.characters || 0 }}</v-chip>
                      <v-chip size="small" variant="tonal">剧本 {{ project.counts?.scripts || 0 }}</v-chip>
                      <v-chip size="small" variant="tonal">预设 {{ project.counts?.presets || 0 }}</v-chip>
                      <v-chip v-if="project.counts?.ai_drafts" size="small" color="warning" variant="tonal">AI草稿 {{ project.counts.ai_drafts }}</v-chip>
                    </div>
                  </v-sheet>
                </v-col>
              </v-row>
              <v-divider class="my-5" />
              <div class="d-flex align-center justify-space-between mb-2">
                <div>
                  <div class="text-subtitle-1 font-weight-medium">最近更新</div>
                  <div class="text-body-2 muted">当前项目最近改动的世界书、人物卡、剧本和预设</div>
                </div>
                <v-btn size="small" variant="text" prepend-icon="mdi-refresh" @click="loadProjectOverview">刷新</v-btn>
              </div>
              <v-table density="compact" class="mb-4">
                <thead>
                  <tr>
                    <th>模块</th>
                    <th>条目</th>
                    <th>更新时间</th>
                    <th>动作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in overviewRecentItems" :key="`${item.type}-${item.id}`">
                    <td>{{ overviewModuleText(item.type) }}</td>
                    <td>{{ item.title || '未命名' }}</td>
                    <td class="muted" style="width: 180px">{{ formatDateTime(item.updated_at) }}</td>
                    <td class="text-no-wrap">
                      <v-btn icon="mdi-open-in-new" size="x-small" variant="text" :aria-label="`打开${overviewModuleText(item.type)}`" @click="openOverviewRecentItem(item)" />
                    </td>
                  </tr>
                  <tr v-if="!overviewRecentItems.length">
                    <td colspan="4" class="muted py-4">暂无最近更新</td>
                  </tr>
                </tbody>
              </v-table>
              <v-divider class="my-5" />
              <div class="d-flex align-center justify-space-between mb-2">
                <div>
                  <div class="text-subtitle-1 font-weight-medium">AI 历史</div>
                  <div class="text-body-2 muted">最近生成、迭代、检查和整理记录</div>
                </div>
                <v-btn size="small" variant="text" prepend-icon="mdi-refresh" @click="loadAiLogs">刷新</v-btn>
              </div>
              <v-alert v-if="activeProjectAiDraftCount" type="warning" variant="tonal" density="compact" class="mb-3">
                当前项目有 {{ activeProjectAiDraftCount }} 条 AI 预览草稿待应用，可在下方 AI 历史中点击保存图标写回对应条目。
                <div v-if="overviewDraftChips.length" class="d-flex flex-wrap ga-2 mt-2">
                  <v-chip v-for="item in overviewDraftChips" :key="item.type" size="x-small" color="warning" variant="tonal">{{ item.label }} {{ item.count }}</v-chip>
                </div>
              </v-alert>
              <v-table density="compact">
                <thead>
                  <tr>
                    <th>时间</th>
                    <th>模块</th>
                    <th>操作</th>
                    <th>状态</th>
                    <th>保存</th>
                    <th>目标</th>
                    <th>板块/字段</th>
                    <th>结果预览</th>
                    <th>动作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="log in aiLogs" :key="log.id">
                    <td class="muted" style="width: 160px">{{ formatDateTime(log.created_at) }}</td>
                    <td>{{ aiTargetText(log.target_type) }}</td>
                    <td>{{ aiOperationText(log.operation) }}</td>
                    <td>{{ aiStatusText(log.status) }}</td>
                    <td>
                      <v-chip size="x-small" :color="aiLogPersistColor(log)" variant="tonal">{{ aiLogPersistText(log) }}</v-chip>
                    </td>
                    <td class="muted">{{ log.target_id || '新内容' }}</td>
                    <td class="muted">{{ [log.section, log.field].filter(Boolean).join(' / ') || '全部' }}</td>
                    <td>{{ brief(log.response_preview, 90) }}</td>
                    <td class="text-no-wrap">
                      <v-btn icon="mdi-eye-outline" size="x-small" variant="text" aria-label="查看AI日志" @click="openAiLogDialog(log)" />
                      <v-btn
                        v-if="aiLogCanApply(log)"
                        icon="mdi-content-save-outline"
                        size="x-small"
                        variant="text"
                        :aria-label="aiLogApplyLabel(log)"
                        @click="applyAiLog(log)"
                      />
                    </td>
                  </tr>
                  <tr v-if="!aiLogs.length">
                    <td colspan="9" class="muted py-4">暂无 AI 记录</td>
                  </tr>
                </tbody>
              </v-table>
            </div>
          </section>
        </v-window-item>

        <v-window-item value="worldbook" class="h-100">
          <div class="d-flex h-100">
            <aside class="pane" style="width: 260px">
              <div class="pane-header d-flex align-center justify-space-between">
                <span class="text-subtitle-1 font-weight-medium">分类</span>
                <v-btn icon="mdi-folder-plus-outline" size="small" variant="text" @click="openCategoryDialog()" />
              </div>
              <v-list density="compact" nav>
                <v-list-item :active="!worldFilters.category_id" title="全部条目" prepend-icon="mdi-view-list" @click="worldFilters.category_id = ''" />
                <v-list-item
                  v-for="cat in categories"
                  :key="cat.id"
                  :active="worldFilters.category_id === cat.id"
                  :title="cat.name"
                  :subtitle="cat.description"
                  prepend-icon="mdi-folder-outline"
                  @click="worldFilters.category_id = cat.id"
                >
                  <template #append>
                    <v-btn icon="mdi-pencil" size="x-small" variant="text" @click.stop="openCategoryDialog(cat)" />
                  </template>
                </v-list-item>
              </v-list>
            </aside>

            <section class="pane" style="width: 390px">
              <div class="pane-header">
                <div class="d-flex align-center justify-space-between mb-2">
                  <span class="text-subtitle-1 font-weight-medium">世界书</span>
                  <div>
                    <v-btn icon="mdi-robot-outline" aria-label="AI生成世界书" variant="text" size="small" @click="openWorldAiDialog" />
                    <v-btn icon="mdi-plus" color="primary" variant="text" size="small" @click="openWorldEntryDialog()" />
                  </div>
                </div>
                <v-text-field v-model="worldFilters.q" placeholder="搜索标题、正文、标签" prepend-inner-icon="mdi-magnify" density="compact" hide-details @keyup.enter="loadWorldbook" />
              </div>
              <v-list lines="three" density="compact">
                <v-list-item
                  v-for="entry in worldEntries"
                  :key="entry.id"
                  :active="selectedWorldEntry?.id === entry.id"
                  @click="selectWorldEntry(entry)"
                >
                  <v-list-item-title>{{ entry.title }}</v-list-item-title>
                  <v-list-item-subtitle>{{ brief(entry.content) }}</v-list-item-subtitle>
                  <template #append>
                    <v-chip size="x-small" :color="statusColor(entry.status)">{{ statusText(entry.status) }}</v-chip>
                  </template>
                </v-list-item>
              </v-list>
            </section>

            <section class="pane flex-grow-1">
              <div class="pane-header d-flex align-center justify-space-between">
                <div>
                  <div class="text-subtitle-1 font-weight-medium">{{ selectedWorldEntry?.title || '选择一个条目' }}</div>
                  <div v-if="selectedWorldEntry" class="text-body-2 muted">版本 {{ selectedWorldEntry.version }} · 重要度 {{ selectedWorldEntry.importance }}</div>
                </div>
                <div v-if="selectedWorldEntry">
                  <v-btn icon="mdi-vector-link" variant="text" @click="openWorldRelationDialog" />
                  <v-btn icon="mdi-auto-fix" aria-label="AI迭代世界书" variant="text" @click="openIterateDialog('worldbook')" />
                  <v-btn icon="mdi-clipboard-check-outline" variant="text" @click="runQualityCheck('worldbook')" />
                  <v-btn icon="mdi-history" aria-label="世界书版本历史" variant="text" @click="openVersions('worldbook_entry', selectedWorldEntry.id)" />
                  <v-btn icon="mdi-export" variant="text" @click="exportWorldbook" />
                  <v-btn icon="mdi-pencil" variant="text" @click="openWorldEntryDialog(selectedWorldEntry)" />
                  <v-btn icon="mdi-delete-outline" color="error" variant="text" @click="deleteWorldEntry" />
                </div>
              </div>
              <div v-if="selectedWorldEntry" class="detail-body">
                <div class="d-flex flex-wrap ga-2 mb-4">
                  <v-chip size="small" color="primary" variant="tonal">{{ categoryName(selectedWorldEntry.category_id) }}</v-chip>
                  <v-chip v-for="tag in selectedWorldEntry.tags" :key="tag" size="small">{{ tag }}</v-chip>
                </div>
                <div class="markdown-body" v-html="renderMarkdown(selectedWorldEntry.content || '暂无正文')" />
                <v-divider class="my-5" />
                <div class="text-subtitle-2 mb-2">关联条目</div>
                <v-list density="compact">
                  <v-list-item
                    v-for="rel in selectedWorldEntry.relations"
                    :key="rel.id"
                    :title="`${rel.source_title} → ${rel.target_title}`"
                    :subtitle="`${rel.relation_type} · 强度 ${rel.strength} · ${rel.description || rel.label || ''}`"
                  >
                    <template #append>
                      <v-btn icon="mdi-close" size="x-small" variant="text" @click="deleteWorldRelation(rel.id)" />
                    </template>
                  </v-list-item>
                </v-list>
                <v-divider class="my-5" />
                <div class="d-flex align-center justify-space-between mb-2">
                  <div class="text-subtitle-2">关系图谱</div>
                  <v-btn size="small" variant="text" prepend-icon="mdi-refresh" @click="loadWorldGraph">更新图谱</v-btn>
                </div>
                <svg class="graph-canvas" viewBox="0 0 760 360" preserveAspectRatio="xMidYMid meet">
                  <line
                    v-for="edge in worldGraphEdges"
                    :key="edge.id"
                    :x1="graphPoint(edge.from).x"
                    :y1="graphPoint(edge.from).y"
                    :x2="graphPoint(edge.to).x"
                    :y2="graphPoint(edge.to).y"
                    :stroke="relationColor(edge.type)"
                    :stroke-width="edge.strength"
                    stroke-linecap="round"
                  />
                  <g
                    v-for="node in worldGraph.nodes"
                    :key="node.id"
                    class="node-chip"
                    @click="selectWorldEntryById(node.id)"
                  >
                    <circle :cx="graphPoint(node.id).x" :cy="graphPoint(node.id).y" :r="16 + node.importance * 2" fill="#e8f0fe" stroke="#1a73e8" />
                    <text :x="graphPoint(node.id).x" :y="graphPoint(node.id).y + 44" text-anchor="middle" font-size="13" fill="#202124">{{ node.label }}</text>
                  </g>
                </svg>
              </div>
              <empty-state v-else icon="mdi-book-open-page-variant" text="从列表选择条目，或新建世界书内容" />
            </section>
          </div>
        </v-window-item>

        <v-window-item value="characters" class="h-100">
          <div class="d-flex h-100">
            <section class="pane" style="width: 390px">
              <div class="pane-header">
                <div class="d-flex align-center justify-space-between mb-2">
                  <span class="text-subtitle-1 font-weight-medium">人物卡</span>
                  <div>
                    <v-btn icon="mdi-robot-outline" aria-label="AI生成人物卡" variant="text" size="small" @click="openCharacterAiDialog" />
                    <v-btn icon="mdi-plus" color="primary" variant="text" size="small" @click="openCharacterDialog()" />
                  </div>
                </div>
                <div class="d-flex ga-2">
                  <v-text-field v-model="characterFilters.q" placeholder="搜索角色" prepend-inner-icon="mdi-magnify" density="compact" hide-details @keyup.enter="loadCharacters" />
                  <v-select v-model="characterFilters.character_type" :items="characterTypes" clearable label="类型" density="compact" hide-details style="max-width: 130px" @update:model-value="loadCharacters" />
                </div>
              </div>
              <v-list lines="two" density="compact">
                <v-list-item
                  v-for="char in characters"
                  :key="char.id"
                  :active="selectedCharacter?.id === char.id"
                  @click="selectCharacter(char)"
                >
                  <template #prepend>
                    <v-avatar color="primary" size="34">{{ char.name?.[0] }}</v-avatar>
                  </template>
                  <v-list-item-title>{{ char.name }}</v-list-item-title>
                  <v-list-item-subtitle>{{ charSummary(char) }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </section>

            <section class="pane flex-grow-1">
              <div class="pane-header d-flex align-center justify-space-between">
                <div>
                  <div class="text-subtitle-1 font-weight-medium">{{ selectedCharacter?.name || '选择一个角色' }}</div>
                  <div v-if="selectedCharacter" class="text-body-2 muted">{{ selectedCharacter.character_type }} · {{ selectedCharacter.status }}</div>
                </div>
                <div v-if="selectedCharacter" class="d-flex align-center">
                  <v-btn-toggle v-model="characterViewMode" density="compact" mandatory>
                    <v-btn value="developer">开发者</v-btn>
                    <v-btn value="player">玩家</v-btn>
                  </v-btn-toggle>
                  <v-btn icon="mdi-account-multiple-plus-outline" aria-label="新建人物关系" variant="text" @click="openCharacterRelationDialog" />
                  <v-btn icon="mdi-auto-fix" aria-label="AI迭代人物卡" variant="text" @click="openIterateDialog('character')" />
                  <v-btn icon="mdi-clipboard-check-outline" aria-label="人物卡质量检查" variant="text" @click="runQualityCheck('character')" />
                  <v-btn icon="mdi-history" aria-label="人物卡版本历史" variant="text" @click="openVersions('character', selectedCharacter.id)" />
                  <v-btn icon="mdi-export" aria-label="导出人物卡" variant="text" @click="exportCharacters" />
                  <v-btn icon="mdi-pencil" aria-label="编辑人物卡" variant="text" @click="openCharacterDialog(selectedCharacter)" />
                  <v-btn icon="mdi-delete-outline" aria-label="删除人物卡" color="error" variant="text" @click="deleteCharacter" />
                </div>
              </div>
              <div v-if="selectedCharacter" class="detail-body">
                <v-tabs v-model="characterTab" density="compact">
                  <v-tab v-for="tab in characterTabs" :key="tab" :value="tab">{{ characterTabLabel(tab) }}</v-tab>
                </v-tabs>
                <v-window v-model="characterTab" class="pt-4">
                  <v-window-item v-for="tab in characterTabs" :key="tab" :value="tab">
                    <template v-if="characterSection(tab)">
                      <v-table v-if="isPlainObject(characterSection(tab))" density="compact">
                        <tbody>
                          <tr v-for="(value, key) in characterSection(tab)" :key="key">
                            <td class="muted" style="width: 180px">{{ characterFieldLabel(String(key)) }}</td>
                            <td class="pre-wrap">{{ formatValue(value) }}</td>
                          </tr>
                        </tbody>
                      </v-table>
                      <div v-else-if="Array.isArray(characterSection(tab))" class="character-array-list">
                        <div v-for="(item, idx) in characterSection(tab)" :key="idx" class="character-array-item">
                          <v-table v-if="isPlainObject(item)" density="compact">
                            <tbody>
                              <tr v-for="(value, key) in item" :key="key">
                                <td class="muted" style="width: 160px">{{ characterFieldLabel(String(key)) }}</td>
                                <td class="pre-wrap">{{ formatValue(value) }}</td>
                              </tr>
                            </tbody>
                          </v-table>
                          <div v-else class="pre-wrap">{{ formatValue(item) }}</div>
                        </div>
                      </div>
                      <div v-else class="pre-wrap">{{ formatValue(characterSection(tab)) }}</div>
                    </template>
                    <div v-else class="muted py-6">暂无数据</div>
                  </v-window-item>
                </v-window>
                <v-divider class="my-5" />
                <div class="text-subtitle-2 mb-2">人物关系</div>
                <v-list density="compact">
                  <v-list-item
                    v-for="rel in selectedCharacter.relations"
                    :key="rel.id"
                    prepend-icon="mdi-account-switch-outline"
                    :title="`${rel.source_name} → ${rel.target_name}`"
                    :subtitle="`${rel.relation_type} · ${rel.numeric_value} · ${rel.description || ''}`"
                  >
                    <template #append>
                      <v-btn icon="mdi-close" size="x-small" variant="text" @click="deleteCharacterRelation(rel.id)" />
                    </template>
                  </v-list-item>
                </v-list>
                <v-divider class="my-5" />
                <div class="text-subtitle-2 mb-2">世界书关联与剧本出场</div>
                <div class="d-flex flex-wrap ga-2 mb-3">
                  <v-chip v-for="entry in selectedCharacter.world_entries" :key="entry.id" size="small" color="primary" variant="tonal">{{ entry.title }}</v-chip>
                  <span v-if="!selectedCharacter.world_entries?.length" class="muted text-body-2">暂无世界书关联</span>
                </div>
                <v-list density="compact">
                  <v-list-item v-for="ref in selectedCharacter.script_references" :key="ref.id" prepend-icon="mdi-script-text-outline" :title="ref.ref_name" :subtitle="ref.description || '剧本引用'" />
                </v-list>
              </div>
              <empty-state v-else icon="mdi-account-outline" text="从左侧选择或创建角色" />
            </section>
          </div>
        </v-window-item>

        <v-window-item value="scripts" class="h-100">
          <div class="d-flex h-100">
            <section class="pane" style="width: 420px">
              <div class="pane-header d-flex align-center justify-space-between">
                <span class="text-subtitle-1 font-weight-medium">剧本结构</span>
                <div>
                  <v-btn icon="mdi-robot-outline" aria-label="AI生成剧本" variant="text" size="small" @click="openScriptAiDialog" />
                  <v-btn icon="mdi-plus" color="primary" variant="text" size="small" @click="openScriptDialog()" />
                </div>
              </div>
              <v-list density="compact" nav>
                <v-list-item
                  v-for="node in flatScripts"
                  :key="node.id"
                  :active="selectedScript?.id === node.id"
                  :title="node.title"
                  :subtitle="node.node_type"
                  :style="{ paddingLeft: `${12 + node.depth * 18}px` }"
                  :prepend-icon="scriptIcon(node.node_type)"
                  @click="selectScript(node)"
                />
              </v-list>
            </section>
            <section class="pane flex-grow-1">
              <div class="pane-header d-flex align-center justify-space-between">
                <div>
                  <div class="text-subtitle-1 font-weight-medium">{{ selectedScript?.title || '选择一个剧本节点' }}</div>
                  <div v-if="selectedScript" class="text-body-2 muted">{{ scriptTypeName(selectedScript.node_type) }} · {{ selectedScript.status }} · 版本 {{ selectedScript.version }}</div>
                </div>
                <div v-if="selectedScript">
                  <v-btn icon="mdi-link-plus" aria-label="新增剧本引用" variant="text" @click="openScriptReferenceDialog" />
                  <v-btn icon="mdi-auto-fix" aria-label="AI迭代剧本" variant="text" @click="openIterateDialog('script')" />
                  <v-btn icon="mdi-clipboard-check-outline" aria-label="剧本质量检查" variant="text" @click="runQualityCheck('script')" />
                  <v-btn icon="mdi-history" aria-label="剧本版本历史" variant="text" @click="openVersions('script', selectedScript.id)" />
                  <v-btn icon="mdi-export" aria-label="导出剧本" variant="text" @click="exportScripts" />
                  <v-btn icon="mdi-file-tree-outline" aria-label="新增子剧本节点" variant="text" @click="openScriptDialog(undefined, selectedScript.id)" />
                  <v-btn icon="mdi-pencil" aria-label="编辑剧本节点" variant="text" @click="openScriptDialog(selectedScript)" />
                  <v-btn icon="mdi-delete-outline" aria-label="删除剧本节点" color="error" variant="text" @click="deleteScript" />
                </div>
              </div>
              <div v-if="selectedScript" class="detail-body">
                <div class="d-flex flex-wrap ga-2 mb-4">
                  <v-chip size="small" color="primary" variant="tonal">{{ selectedScript.story_location || '未设地点' }}</v-chip>
                  <v-chip size="small" variant="tonal">{{ selectedScript.story_time || '未设时间' }}</v-chip>
                  <v-chip v-for="tag in selectedScript.tags" :key="tag" size="small">{{ tag }}</v-chip>
                </div>
                <p class="muted">{{ selectedScript.summary }}</p>
                <div class="markdown-body mt-4" v-html="renderMarkdown(selectedScript.content || '暂无正文')" />
                <v-divider class="my-5" />
                <div class="text-subtitle-2 mb-2">引用</div>
                <v-list density="compact">
                  <v-list-item
                    v-for="ref in scriptReferences"
                    :key="ref.id"
                    :prepend-icon="ref.ref_type === 'worldbook' ? 'mdi-book-open-page-variant' : 'mdi-account-outline'"
                    :title="ref.ref_name"
                    :subtitle="ref.description"
                  >
                    <template #append>
                      <v-btn icon="mdi-close" size="x-small" variant="text" @click="deleteScriptReference(ref.id)" />
                    </template>
                  </v-list-item>
                </v-list>
              </div>
              <empty-state v-else icon="mdi-script-text-outline" text="创建总纲、卷、篇章、章节、场景或片段" />
            </section>
          </div>
        </v-window-item>

        <v-window-item value="presets" class="h-100">
          <div class="d-flex h-100">
            <section class="pane" style="width: 390px">
              <div class="pane-header">
                <div class="d-flex align-center justify-space-between mb-2">
                  <span class="text-subtitle-1 font-weight-medium">预设</span>
                  <div>
                    <v-btn icon="mdi-robot-outline" aria-label="AI生成预设" variant="text" size="small" @click="openPresetAiDialog" />
                    <v-btn icon="mdi-plus" color="primary" variant="text" size="small" @click="openPresetDialog()" />
                  </div>
                </div>
                <v-text-field v-model="presetFilters.q" placeholder="搜索预设" prepend-inner-icon="mdi-magnify" density="compact" hide-details @keyup.enter="loadPresets" />
              </div>
              <v-list lines="two" density="compact">
                <v-list-item
                  v-for="preset in presets"
                  :key="preset.id"
                  :active="selectedPreset?.id === preset.id"
                  :title="preset.name"
                  :subtitle="preset.description"
                  @click="selectPreset(preset)"
                />
              </v-list>
            </section>
            <section class="pane flex-grow-1">
              <div class="pane-header d-flex align-center justify-space-between">
                <div>
                  <div class="text-subtitle-1 font-weight-medium">{{ selectedPreset?.name || '选择一个预设' }}</div>
                  <div v-if="selectedPreset" class="text-body-2 muted">{{ selectedPreset.category }}</div>
                </div>
                <div v-if="selectedPreset">
                  <v-btn icon="mdi-auto-fix" variant="text" @click="organizePreset" />
                  <v-btn icon="mdi-creation" variant="text" @click="openIterateDialog('preset')" />
                  <v-btn icon="mdi-playlist-check" aria-label="应用预设" variant="text" @click="openPresetApplyDialog" />
                  <v-btn icon="mdi-vector-combine" aria-label="组合预设" variant="text" @click="openPresetCombineDialog" />
                  <v-btn icon="mdi-history" variant="text" @click="openVersions('preset', selectedPreset.id)" />
                  <v-btn icon="mdi-export" variant="text" @click="exportPresets" />
                  <v-btn icon="mdi-content-copy" variant="text" @click="copyPresetPrompt" />
                  <v-btn icon="mdi-pencil" variant="text" @click="openPresetDialog(selectedPreset)" />
                  <v-btn icon="mdi-delete-outline" color="error" variant="text" @click="deletePreset" />
                </div>
              </div>
              <div v-if="selectedPreset" class="detail-body">
                <p>{{ selectedPreset.description || '暂无描述' }}</p>
                <div class="text-subtitle-2 mt-4 mb-2">维度</div>
                <v-table density="compact">
                  <tbody>
                    <tr v-for="dim in selectedPreset.dimensions" :key="dim.name">
                      <td class="font-weight-medium" style="width: 160px">{{ dim.name }}</td>
                      <td>{{ dim.value }}</td>
                      <td class="muted">{{ dim.description }}</td>
                    </tr>
                  </tbody>
                </v-table>
                <div class="text-subtitle-2 mt-5 mb-2">完整提示词</div>
                <v-sheet border rounded="sm" class="pa-3 markdown-body" v-html="renderMarkdown(selectedPreset.compiled_prompt || '暂无')" />
              </div>
              <empty-state v-else icon="mdi-palette-outline" text="创建一个可用于世界书、人物卡、剧本生成的预设" />
            </section>
          </div>
        </v-window-item>
      </v-window>
    </v-main>

    <v-dialog v-model="projectDialog" max-width="820" scrollable>
      <v-card>
        <v-card-title>{{ projectForm.id ? '编辑项目' : '创建项目' }}</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field v-model="projectForm.name" label="项目名称" />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="projectForm.genre" label="题材" />
            </v-col>
            <v-col cols="12">
              <v-textarea v-model="projectForm.description" label="描述" rows="3" />
            </v-col>
          </v-row>
          <v-divider class="my-3" />
          <div class="text-subtitle-2 mb-2">默认风格</div>
          <v-textarea v-model="projectForm.settings.default_style" label="项目默认风格" rows="3" />
          <v-divider class="my-3" />
          <div class="text-subtitle-2 mb-2">AI 默认参数</div>
          <v-row>
            <v-col cols="12" md="6">
              <v-slider v-model="projectForm.settings.ai.temperature" min="0" max="1.4" step="0.1" thumb-label label="温度" />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model.number="projectForm.settings.ai.max_tokens" type="number" label="最大输出 Token" />
            </v-col>
          </v-row>
          <v-divider class="my-3" />
          <div class="text-subtitle-2 mb-2">模块启用</div>
          <v-row>
            <v-col cols="6" md="3">
              <v-switch v-model="projectForm.settings.modules.worldbook" label="世界书" density="compact" hide-details />
            </v-col>
            <v-col cols="6" md="3">
              <v-switch v-model="projectForm.settings.modules.characters" label="人物卡" density="compact" hide-details />
            </v-col>
            <v-col cols="6" md="3">
              <v-switch v-model="projectForm.settings.modules.scripts" label="剧本" density="compact" hide-details />
            </v-col>
            <v-col cols="6" md="3">
              <v-switch v-model="projectForm.settings.modules.presets" label="预设" density="compact" hide-details />
            </v-col>
          </v-row>
          <v-divider class="my-3" />
          <div class="text-subtitle-2 mb-2">默认可见性</div>
          <v-row>
            <v-col cols="12" md="6">
              <v-select v-model="projectForm.settings.defaults.worldbook_visibility" :items="worldbookVisibilityOptions" label="世界书默认可见性" />
            </v-col>
            <v-col cols="12" md="6">
              <v-select v-model="projectForm.settings.defaults.character_view_mode" :items="characterViewModeOptions" label="默认人物视图" />
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="projectDialog = false">取消</v-btn>
          <v-btn color="primary" :loading="loading" @click="saveProject">{{ projectForm.id ? '保存' : '创建' }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="projectDeleteDialog" max-width="520">
      <v-card>
        <v-card-title>删除项目</v-card-title>
        <v-card-text>
          <p class="text-body-2 mb-3">删除会移除该项目下的世界书、人物卡、剧本、预设、版本和 AI 历史。请输入项目名称确认。</p>
          <v-text-field v-model="projectDeleteConfirmName" :label="projectDeleteTarget?.name || '项目名称'" autocomplete="off" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="projectDeleteDialog = false">取消</v-btn>
          <v-btn color="error" :disabled="projectDeleteConfirmName !== projectDeleteTarget?.name" :loading="loading" @click="deleteProject">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="aiLogDialog" max-width="960" scrollable>
      <v-card>
        <v-card-title>AI 日志详情</v-card-title>
        <v-card-text v-if="selectedAiLog">
          <v-table density="compact" class="mb-4">
            <tbody>
              <tr>
                <td>时间</td>
                <td>{{ formatDateTime(selectedAiLog.created_at) }}</td>
              </tr>
              <tr>
                <td>模块</td>
                <td>{{ aiTargetText(selectedAiLog.target_type) }}</td>
              </tr>
              <tr>
                <td>操作</td>
                <td>{{ aiOperationText(selectedAiLog.operation) }}</td>
              </tr>
              <tr>
                <td>状态</td>
                <td><v-chip size="small" :color="selectedAiLog.status === 'failed' ? 'error' : 'success'" variant="tonal">{{ selectedAiLog.status || 'success' }}</v-chip></td>
              </tr>
              <tr>
                <td>保存</td>
                <td><v-chip size="small" :color="aiLogPersistColor(selectedAiLog)" variant="tonal">{{ aiLogPersistText(selectedAiLog) }}</v-chip></td>
              </tr>
              <tr>
                <td>目标</td>
                <td>{{ selectedAiLog.target_id || '新内容' }}</td>
              </tr>
              <tr>
                <td>板块/字段</td>
                <td>{{ [selectedAiLog.section, selectedAiLog.field].filter(Boolean).join(' / ') || '全部' }}</td>
              </tr>
              <tr v-if="selectedAiLog.instruction">
                <td>用户要求</td>
                <td>{{ selectedAiLog.instruction }}</td>
              </tr>
            </tbody>
          </v-table>

          <div class="text-subtitle-2 mb-2">过程日志</div>
          <v-list density="compact" class="mb-4 ai-log-process-panel">
            <v-list-item v-for="(item, index) in selectedAiLog.process_log || []" :key="index" :title="item.message || item" :subtitle="item.time || ''" />
            <v-list-item v-if="!(selectedAiLog.process_log || []).length" title="暂无过程日志" />
          </v-list>

          <v-textarea :model-value="selectedAiLog.prompt || ''" label="完整 Prompt" rows="8" readonly />
          <v-textarea :model-value="formatJson(selectedAiLog.request || {})" label="请求参数" rows="5" readonly />
          <div class="text-subtitle-2 mt-2 mb-2">结果预览</div>
          <v-row class="markdown-edit-grid">
            <v-col cols="12" md="5">
              <v-textarea :model-value="selectedAiLogResultRaw" label="原始结果" rows="12" readonly class="json-area" />
            </v-col>
            <v-col cols="12" md="7">
              <div v-if="selectedAiLogResultMode === 'markdown'" class="markdown-body markdown-preview-pane ai-log-preview-pane" v-html="renderMarkdown(selectedAiLogMarkdownResult || '暂无结果')" />
              <div v-else-if="selectedAiLogResultMode === 'character' && selectedAiLogCharacterPreview" class="character-preview-pane ai-log-character-preview">
                <v-tabs v-model="aiLogPreviewTab" density="compact">
                  <v-tab v-for="tab in characterTabs" :key="tab" :value="tab">{{ characterTabLabel(tab) }}</v-tab>
                </v-tabs>
                <v-window v-model="aiLogPreviewTab" class="pt-3">
                  <v-window-item v-for="tab in characterTabs" :key="tab" :value="tab">
                    <template v-if="selectedAiLogCharacterSection(tab)">
                      <v-table v-if="isPlainObject(selectedAiLogCharacterSection(tab))" density="compact">
                        <tbody>
                          <tr v-for="(value, key) in selectedAiLogCharacterSection(tab)" :key="key">
                            <td class="muted" style="width: 160px">{{ characterFieldLabel(String(key)) }}</td>
                            <td class="pre-wrap">{{ formatValue(value) }}</td>
                          </tr>
                        </tbody>
                      </v-table>
                      <div v-else-if="Array.isArray(selectedAiLogCharacterSection(tab))" class="character-array-list">
                        <div v-for="(item, idx) in selectedAiLogCharacterSection(tab)" :key="idx" class="character-array-item">
                          <v-table v-if="isPlainObject(item)" density="compact">
                            <tbody>
                              <tr v-for="(value, key) in item" :key="key">
                                <td class="muted" style="width: 160px">{{ characterFieldLabel(String(key)) }}</td>
                                <td class="pre-wrap">{{ formatValue(value) }}</td>
                              </tr>
                            </tbody>
                          </v-table>
                          <div v-else class="pre-wrap">{{ formatValue(item) }}</div>
                        </div>
                      </div>
                      <div v-else class="pre-wrap">{{ formatValue(selectedAiLogCharacterSection(tab)) }}</div>
                    </template>
                    <div v-else class="muted py-6">暂无数据</div>
                  </v-window-item>
                </v-window>
              </div>
              <v-textarea v-else-if="selectedAiLogResultMode === 'json'" :model-value="selectedAiLogResultRaw" label="结构化 JSON" rows="12" readonly class="json-area" />
              <div v-else class="pre-wrap ai-log-text-preview">{{ selectedAiLogResultRaw || '暂无结果' }}</div>
            </v-col>
          </v-row>
          <v-alert v-if="aiLogApplyBlockedReason(selectedAiLog)" type="warning" variant="tonal" density="compact" class="mt-2">
            {{ aiLogApplyBlockedReason(selectedAiLog) }}
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn v-if="aiLogCanApply(selectedAiLog)" variant="tonal" prepend-icon="mdi-content-save-outline" @click="applyAiLog(selectedAiLog)">{{ aiLogApplyLabel(selectedAiLog) }}</v-btn>
          <v-btn variant="tonal" :disabled="!selectedAiLog?.prompt" @click="copyAiLogPrompt">复制 Prompt</v-btn>
          <v-btn @click="aiLogDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="projectImportDialog" max-width="760">
      <v-card>
        <v-card-title>导入项目</v-card-title>
        <v-card-text>
          <v-file-input
            label="导入文件"
            accept=".json,.storyworks.json,application/json"
            prepend-icon="mdi-file-upload-outline"
            @update:model-value="readProjectImportFile"
          />
          <v-textarea v-model="projectImportContent" class="json-area" label="导入内容" rows="8" />
          <v-table v-if="projectImportPreview" density="compact" class="mt-3">
            <tbody>
              <tr>
                <td>项目</td>
                <td>{{ projectImportPreview.project_name || '未知' }}</td>
              </tr>
              <tr v-for="(value, key) in projectImportPreview.counts || {}" :key="key">
                <td>{{ key }}</td>
                <td>{{ value }}</td>
              </tr>
              <tr v-for="issue in projectImportPreview.issues || []" :key="issue.type">
                <td>{{ issue.type }}</td>
                <td>{{ issue.message }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="projectImportDialog = false">取消</v-btn>
          <v-btn variant="tonal" :disabled="!projectImportContent" @click="previewProjectImport">预览</v-btn>
          <v-btn color="primary" :disabled="!projectImportContent || projectImportPreview?.valid === false" @click="importProject">导入</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="categoryDialog" max-width="720">
      <v-card>
        <v-card-title>{{ categoryForm.id ? '编辑分类' : '新建分类' }}</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="6"><v-text-field v-model="categoryForm.name" label="名称" /></v-col>
            <v-col cols="6"><v-select v-model="categoryForm.parent_id" :items="[{ id: null, name: '顶级分类' }, ...categories]" item-title="name" item-value="id" label="父分类" /></v-col>
          </v-row>
          <v-textarea v-model="categoryForm.description" label="描述" rows="2" />
          <v-textarea v-model="categoryTemplateJson" class="json-area" label="模板 JSON" rows="8" />
        </v-card-text>
        <v-card-actions>
          <v-btn v-if="categoryForm.id" color="error" variant="text" @click="deleteCategory">删除</v-btn>
          <v-spacer />
          <v-btn @click="categoryDialog = false">取消</v-btn>
          <v-btn color="primary" @click="saveCategory">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="worldEntryDialog" max-width="920" scrollable>
      <v-card>
        <v-card-title>{{ worldEntryForm.id ? '编辑条目' : '新建条目' }}</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="7"><v-text-field v-model="worldEntryForm.title" label="标题" /></v-col>
            <v-col cols="5"><v-select v-model="worldEntryForm.category_id" :items="categories" item-title="name" item-value="id" label="分类" /></v-col>
            <v-col cols="4"><v-select v-model="worldEntryForm.status" :items="statusOptions" label="状态" /></v-col>
            <v-col cols="4"><v-select v-model="worldEntryForm.visibility" :items="['public', 'private']" label="可见性" /></v-col>
            <v-col cols="4"><v-slider v-model="worldEntryForm.importance" min="1" max="5" step="1" thumb-label label="重要度" /></v-col>
          </v-row>
          <v-combobox v-model="worldEntryForm.tags" label="标签" multiple chips />
          <v-row class="markdown-edit-grid">
            <v-col cols="12" md="6">
              <v-textarea v-model="worldEntryForm.content" label="正文 Markdown" rows="14" />
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption muted mb-2">渲染预览</div>
              <div class="markdown-body markdown-preview-pane" v-html="renderMarkdown(worldEntryForm.content || '暂无正文')" />
            </v-col>
          </v-row>
          <v-textarea v-model="worldStructuredJson" class="json-area" label="结构化字段 JSON" rows="6" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="worldEntryDialog = false">取消</v-btn>
          <v-btn color="primary" @click="saveWorldEntry">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="worldRelationDialog" max-width="640">
      <v-card>
        <v-card-title>新建世界书关联</v-card-title>
        <v-card-text>
          <v-select v-model="worldRelationForm.target_id" :items="worldEntries.filter(e => e.id !== selectedWorldEntry?.id)" item-title="title" item-value="id" label="目标条目" />
          <v-row>
            <v-col cols="6"><v-select v-model="worldRelationForm.relation_type" :items="relationTypes" label="类型" /></v-col>
            <v-col cols="6"><v-slider v-model="worldRelationForm.strength" min="1" max="5" step="1" thumb-label label="强度" /></v-col>
          </v-row>
          <v-text-field v-model="worldRelationForm.label" label="标签" />
          <v-textarea v-model="worldRelationForm.description" label="描述" rows="3" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="worldRelationDialog = false">取消</v-btn>
          <v-btn color="primary" @click="saveWorldRelation">创建</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="aiDialog.open" max-width="860" scrollable>
      <v-card>
        <v-card-title>{{ aiDialog.title }}</v-card-title>
        <v-card-text>
          <v-alert v-if="aiDialog.running" type="info" variant="tonal" class="mb-3" density="compact">
            {{ aiDialog.activeMessage }}
          </v-alert>
          <div v-if="aiDialog.progress.length" class="ai-progress-panel mb-3">
            <v-list density="compact">
              <v-list-item v-for="(step, idx) in aiDialog.progress" :key="idx" prepend-icon="mdi-check-circle-outline" :title="step.message || step" :subtitle="step.time || ''" />
            </v-list>
          </div>
          <v-row v-if="isIterating">
            <v-col cols="6"><v-text-field v-model="aiDialog.section" label="指定板块/分类（可选）" placeholder="如：规则、knowledge、content" /></v-col>
            <v-col cols="6"><v-text-field v-model="aiDialog.field" label="指定字段（角色可选）" placeholder="如：background、motivation" /></v-col>
          </v-row>
          <v-switch
            v-if="aiDialog.target === 'character-iterate'"
            v-model="aiDialog.apply"
            color="primary"
            density="compact"
            hide-details
            label="直接保存到人物卡（关闭则只生成预览）"
            class="mb-2"
          />
          <v-alert v-if="aiDialog.target === 'character-iterate' && aiDialog.apply === false" type="warning" variant="tonal" density="compact" class="mb-2">
            当前为仅预览模式，本次迭代不会更新人物卡；生成后需要点击“应用迭代结果”才会写回。
          </v-alert>
          <v-textarea v-model="aiDialog.prompt" :label="isIterating ? '迭代要求' : '生成提示词'" rows="5" />
          <v-row>
            <v-col cols="4"><v-text-field v-model.number="aiDialog.min_length" type="number" label="最少字数" /></v-col>
            <v-col cols="4"><v-text-field v-model.number="aiDialog.max_length" type="number" label="最多字数" /></v-col>
            <v-col cols="4"><v-slider v-model="aiDialog.temperature" min="0" max="1.4" step="0.1" thumb-label label="温度" /></v-col>
          </v-row>
          <v-row v-if="aiDialogIsCharacterResult && aiDialog.result" class="markdown-edit-grid">
            <v-col cols="12" md="5">
              <v-textarea v-model="aiDialog.result" :label="isIterating ? '迭代预览结果' : '生成结果'" rows="14" class="json-area" />
            </v-col>
            <v-col cols="12" md="7">
              <div class="text-caption muted mb-2">人物卡结构预览</div>
              <v-alert v-if="aiDialog.contractIssues?.length" type="warning" variant="tonal" density="compact" class="mb-2">
                已由后端补齐结构：{{ aiDialog.contractIssues.length }} 项格式问题。
              </v-alert>
              <div v-if="aiDialogCharacterPreview" class="character-preview-pane">
                <v-tabs v-model="aiDialog.previewTab" density="compact">
                  <v-tab v-for="tab in characterTabs" :key="tab" :value="tab">{{ characterTabLabel(tab) }}</v-tab>
                </v-tabs>
                <v-window v-model="aiDialog.previewTab" class="pt-3">
                  <v-window-item v-for="tab in characterTabs" :key="tab" :value="tab">
                    <template v-if="aiDialogCharacterSection(tab)">
                      <v-table v-if="isPlainObject(aiDialogCharacterSection(tab))" density="compact">
                        <tbody>
                          <tr v-for="(value, key) in aiDialogCharacterSection(tab)" :key="key">
                            <td class="muted" style="width: 160px">{{ characterFieldLabel(String(key)) }}</td>
                            <td class="pre-wrap">{{ formatValue(value) }}</td>
                          </tr>
                        </tbody>
                      </v-table>
                      <div v-else-if="Array.isArray(aiDialogCharacterSection(tab))" class="character-array-list">
                        <div v-for="(item, idx) in aiDialogCharacterSection(tab)" :key="idx" class="character-array-item">
                          <v-table v-if="isPlainObject(item)" density="compact">
                            <tbody>
                              <tr v-for="(value, key) in item" :key="key">
                                <td class="muted" style="width: 160px">{{ characterFieldLabel(String(key)) }}</td>
                                <td class="pre-wrap">{{ formatValue(value) }}</td>
                              </tr>
                            </tbody>
                          </v-table>
                          <div v-else class="pre-wrap">{{ formatValue(item) }}</div>
                        </div>
                      </div>
                      <div v-else class="pre-wrap">{{ formatValue(aiDialogCharacterSection(tab)) }}</div>
                    </template>
                    <div v-else class="muted py-6">暂无数据</div>
                  </v-window-item>
                </v-window>
              </div>
              <v-alert v-else type="error" variant="tonal" density="compact">
                当前结果不是可解析的人物卡 JSON，请检查左侧内容。
              </v-alert>
            </v-col>
          </v-row>
          <v-row v-else-if="aiDialogResultCanRender" class="markdown-edit-grid">
            <v-col cols="12" md="6">
              <v-textarea v-model="aiDialog.result" :label="isIterating ? '迭代预览结果' : '生成结果'" rows="12" />
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption muted mb-2">渲染预览</div>
              <div class="markdown-body markdown-preview-pane" v-html="renderMarkdown(aiDialog.result || '暂无结果')" />
            </v-col>
          </v-row>
          <v-textarea v-else v-model="aiDialog.result" :label="isIterating ? '迭代预览结果' : '生成结果'" rows="12" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="closeAiDialog">关闭</v-btn>
          <v-btn v-if="aiDialog.running" variant="text" color="warning" @click="cancelAiRequest">取消{{ isIterating ? '迭代' : '生成' }}</v-btn>
          <v-btn color="secondary" :loading="aiDialog.running" @click="runAiDialog">{{ aiRunButtonText }}</v-btn>
          <v-btn v-if="isIterating && !aiDialog.apply" color="primary" :disabled="!aiDialog.pendingApplyPayload || aiDialog.running" @click="applyIterationResult">应用迭代结果</v-btn>
          <v-btn v-else color="primary" :disabled="!aiDialog.result || aiDialog.target === 'check' || aiDialog.running" @click="acceptAiResult">{{ aiDialog.target === 'character' ? '创建角色' : '接受' }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="characterDialog" max-width="980" scrollable>
      <v-card>
        <v-card-title>{{ characterForm.id ? '编辑角色' : '新建角色' }}</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="6"><v-text-field v-model="characterForm.name" label="名称" /></v-col>
            <v-col cols="6"><v-select v-model="characterForm.character_type" :items="characterTypes" label="类型" /></v-col>
          </v-row>
          <v-combobox v-model="characterForm.tags" label="标签" multiple chips />
          <v-select v-model="characterForm.world_entry_ids" :items="worldEntries" item-title="title" item-value="id" label="关联世界书" multiple chips />
          <v-tabs v-model="characterEditTab" density="compact">
            <v-tab value="developer">Developer JSON</v-tab>
            <v-tab value="visibility">可见性配置</v-tab>
            <v-tab value="player">Player 预览</v-tab>
          </v-tabs>
          <v-window v-model="characterEditTab" class="mt-3">
            <v-window-item value="developer"><v-textarea v-model="characterDeveloperJson" class="json-area" rows="18" /></v-window-item>
            <v-window-item value="visibility">
              <v-alert v-if="!characterVisibilityRows.length" type="warning" variant="tonal" density="compact" class="mb-3">
                Developer JSON 暂时无法解析，修正后即可配置字段可见性。
              </v-alert>
              <v-table v-else density="compact">
                <thead>
                  <tr>
                    <th>分类</th>
                    <th>字段</th>
                    <th>可见</th>
                    <th>显示模式</th>
                    <th>自定义展示</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in characterVisibilityRows" :key="`${row.section}.${row.field}`">
                    <td>{{ row.sectionLabel }}</td>
                    <td>{{ row.fieldLabel }}</td>
                    <td><v-checkbox v-model="row.rule.visible" density="compact" hide-details :aria-label="`可见 ${row.fieldLabel}`" /></td>
                    <td>
                      <v-select
                        v-model="row.rule.displayMode"
                        :items="characterVisibilityModeOptions"
                        item-title="title"
                        item-value="value"
                        density="compact"
                        hide-details
                        :aria-label="`显示模式 ${row.fieldLabel}`"
                        style="min-width: 132px"
                      />
                    </td>
                    <td><v-text-field v-model="row.rule.customDisplay" density="compact" hide-details :label="`自定义显示 ${row.fieldLabel}`" /></td>
                  </tr>
                </tbody>
              </v-table>
            </v-window-item>
            <v-window-item value="player"><v-textarea :model-value="characterPlayerPreviewJson" class="json-area" rows="18" readonly /></v-window-item>
          </v-window>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="characterDialog = false">取消</v-btn>
          <v-btn color="primary" @click="saveCharacter">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="characterRelationDialog" max-width="660">
      <v-card>
        <v-card-title>新建人物关系</v-card-title>
        <v-card-text>
          <v-select v-model="characterRelationForm.target_id" :items="characters.filter(c => c.id !== selectedCharacter?.id)" item-title="name" item-value="id" label="目标角色" />
          <v-row>
            <v-col cols="6"><v-select v-model="characterRelationForm.relation_type" :items="characterRelationTypes" label="类型" /></v-col>
            <v-col cols="6"><v-select v-model="characterRelationForm.direction" :items="['bidirectional', 'to', 'from']" label="方向" /></v-col>
          </v-row>
          <v-slider v-model="characterRelationForm.numeric_value" min="-100" max="100" step="1" thumb-label label="关系数值" />
          <v-textarea v-model="characterRelationForm.description" label="描述" rows="3" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="characterRelationDialog = false">取消</v-btn>
          <v-btn color="primary" @click="saveCharacterRelation">创建</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="scriptDialog" max-width="900" scrollable>
      <v-card>
        <v-card-title>{{ scriptForm.id ? '编辑剧本节点' : '新建剧本节点' }}</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="6"><v-text-field v-model="scriptForm.title" label="标题" /></v-col>
            <v-col cols="3"><v-select v-model="scriptForm.node_type" :items="scriptTypes" item-title="title" item-value="value" label="类型" /></v-col>
            <v-col cols="3"><v-select v-model="scriptForm.status" :items="statusOptions" label="状态" /></v-col>
          </v-row>
          <v-select v-model="scriptForm.parent_id" :items="[{ id: null, title: '无父节点' }, ...flatScripts]" item-title="title" item-value="id" label="父节点" />
          <v-row>
            <v-col cols="6"><v-text-field v-model="scriptForm.story_time" label="故事时间" /></v-col>
            <v-col cols="6"><v-text-field v-model="scriptForm.story_location" label="故事地点" /></v-col>
          </v-row>
          <v-combobox v-model="scriptForm.tags" label="标签" multiple chips />
          <v-textarea v-model="scriptForm.summary" label="摘要" rows="3" />
          <v-row class="markdown-edit-grid">
            <v-col cols="12" md="6">
              <v-textarea v-model="scriptForm.content" label="正文 Markdown" rows="14" />
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption muted mb-2">渲染预览</div>
              <div class="markdown-body markdown-preview-pane" v-html="renderMarkdown(scriptForm.content || '暂无正文')" />
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="scriptDialog = false">取消</v-btn>
          <v-btn color="primary" @click="saveScript">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="scriptReferenceDialog" max-width="680">
      <v-card>
        <v-card-title>添加剧本引用</v-card-title>
        <v-card-text>
          <v-select v-model="scriptReferenceForm.ref_type" :items="[{ title: '世界书', value: 'worldbook' }, { title: '人物卡', value: 'character' }]" item-title="title" item-value="value" label="引用类型" />
          <v-select v-if="scriptReferenceForm.ref_type === 'worldbook'" v-model="scriptReferenceForm.ref_id" :items="worldEntries" item-title="title" item-value="id" label="世界书条目" />
          <v-select v-else v-model="scriptReferenceForm.ref_id" :items="characters" item-title="name" item-value="id" label="角色" />
          <v-textarea v-model="scriptReferenceForm.description" label="引用说明" rows="3" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="scriptReferenceDialog = false">取消</v-btn>
          <v-btn color="primary" @click="saveScriptReference">添加</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="presetDialog" max-width="980" scrollable>
      <v-card>
        <v-card-title>{{ presetForm.id ? '编辑预设' : '新建预设' }}</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="6"><v-text-field v-model="presetForm.name" label="名称" /></v-col>
            <v-col cols="6"><v-text-field v-model="presetForm.category" label="分类" /></v-col>
          </v-row>
          <v-textarea v-model="presetForm.description" label="描述" rows="2" />
          <v-combobox v-model="presetForm.tags" label="标签" multiple chips />
          <v-textarea v-model="presetDimensionsJson" class="json-area" label="维度 JSON" rows="10" />
          <v-textarea v-model="presetBlocksJson" class="json-area" label="文本块 JSON" rows="7" />
          <v-textarea v-model="presetScenesJson" class="json-area" label="应用场景 JSON" rows="6" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="presetDialog = false">取消</v-btn>
          <v-btn color="primary" @click="savePreset">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="presetApplyDialog" max-width="920" scrollable>
      <v-card>
        <v-card-title>应用预设</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field :model-value="selectedPreset?.name || ''" label="当前预设" readonly />
            </v-col>
            <v-col cols="12" md="6">
              <v-select v-model="presetApplyForm.scene_type" :items="presetSceneTypeOptions" item-title="title" item-value="value" label="应用场景" />
            </v-col>
          </v-row>
          <v-textarea v-model="presetApplyForm.scene_requirements" label="本次任务要求" rows="3" />
          <template v-if="presetApplyResult">
            <v-textarea v-model="presetApplyResult" label="应用后完整提示词" rows="10" readonly />
            <div class="text-subtitle-2 mt-3 mb-2">渲染预览</div>
            <v-sheet border rounded="sm" class="pa-3 markdown-body" v-html="renderMarkdown(presetApplyResult)" />
          </template>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="presetApplyDialog = false">关闭</v-btn>
          <v-btn v-if="presetApplyResult" variant="tonal" @click="copyPresetApplyPrompt">复制结果</v-btn>
          <v-btn color="primary" :loading="loading" @click="applyPresetToScene">生成提示词</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="presetCombineDialog" max-width="980" scrollable>
      <v-card>
        <v-card-title>组合预设</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field :model-value="selectedPreset?.name || ''" label="基础预设" readonly />
            </v-col>
            <v-col cols="12" md="6">
              <v-select v-model="presetCombineForm.override_id" :items="presetCombineOverrideOptions" item-title="name" item-value="id" label="覆盖预设" />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field v-model="presetCombineForm.name" label="保存名称" />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="presetCombineForm.category" label="保存分类" />
            </v-col>
          </v-row>
          <v-textarea v-model="presetCombineForm.description" label="保存描述" rows="2" />
          <template v-if="presetCombineResult">
            <div class="text-subtitle-2 mt-3 mb-2">组合维度</div>
            <v-table density="compact">
              <tbody>
                <tr v-for="dim in presetCombineResult.dimensions || []" :key="dim.name">
                  <td class="font-weight-medium" style="width: 160px">{{ dim.name }}</td>
                  <td>{{ dim.value }}</td>
                  <td class="muted">{{ dim.description }}</td>
                </tr>
              </tbody>
            </v-table>
            <div class="text-subtitle-2 mt-4 mb-2">组合后提示词</div>
            <v-sheet border rounded="sm" class="pa-3 markdown-body" v-html="renderMarkdown(presetCombineResult.compiled_prompt || '暂无')" />
          </template>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="presetCombineDialog = false">关闭</v-btn>
          <v-btn color="secondary" :loading="loading" :disabled="!presetCombineForm.override_id" @click="combinePreset">预览组合</v-btn>
          <v-btn color="primary" :disabled="!presetCombineResult" @click="saveCombinedPreset">保存为新预设</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="versionDialog" max-width="820" scrollable>
      <v-card>
        <v-card-title>版本历史</v-card-title>
        <v-card-text>
          <v-list density="compact">
            <v-list-item
              v-for="version in versionRows"
              :key="version.id"
              prepend-icon="mdi-history"
              :title="`版本 ${version.version}`"
              :subtitle="`${version.created_at} · ${version.summary || '无摘要'}`"
            >
              <template #append>
                <v-btn size="small" variant="text" @click="loadVersionDiff(version.id)">对比</v-btn>
                <v-btn size="small" variant="text" @click="restoreVersion(version.id)">恢复</v-btn>
              </template>
            </v-list-item>
          </v-list>
          <template v-if="versionDiff">
            <v-divider class="my-4" />
            <div class="text-subtitle-2 mb-2">与当前版本差异</div>
            <v-table density="compact">
              <thead>
                <tr>
                  <th>路径</th>
                  <th>类型</th>
                  <th>旧值</th>
                  <th>当前值</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="diff in versionDiff.diffs" :key="diff.path">
                  <td class="muted">{{ diff.path }}</td>
                  <td>{{ versionDiffTypeText(diff.type) }}</td>
                  <td>
                    <div v-if="versionDiffValueIsMarkdown(diff, 'before')" class="markdown-body version-diff-markdown" v-html="renderMarkdown(formatDiffValue(diff.before))" />
                    <div v-else class="pre-wrap">{{ formatDiffValue(diff.before) }}</div>
                  </td>
                  <td>
                    <div v-if="versionDiffValueIsMarkdown(diff, 'after')" class="markdown-body version-diff-markdown" v-html="renderMarkdown(formatDiffValue(diff.after))" />
                    <div v-else class="pre-wrap">{{ formatDiffValue(diff.after) }}</div>
                  </td>
                </tr>
                <tr v-if="!versionDiff.diffs.length">
                  <td colspan="4" class="muted py-4">该版本与当前内容一致</td>
                </tr>
              </tbody>
            </v-table>
          </template>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="versionDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="consistencyDialog" max-width="900" scrollable>
      <v-card>
        <v-card-title>数据一致性检查</v-card-title>
        <v-card-text>
          <v-alert :type="consistencyReport.ok ? 'success' : 'warning'" variant="tonal" density="compact" class="mb-3">
            {{ consistencyReport.ok ? '未发现一致性问题' : `发现 ${consistencyReport.issues?.length || 0} 个问题` }}
          </v-alert>
          <v-table density="compact">
            <thead>
              <tr>
                <th>类型</th>
                <th>实体</th>
                <th>ID</th>
                <th>说明</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="issue in consistencyReport.issues || []" :key="`${issue.type}-${issue.id}`">
                <td>{{ issue.type }}</td>
                <td>{{ issue.entity }}</td>
                <td class="muted">{{ issue.id }}</td>
                <td>{{ issue.message }}</td>
              </tr>
              <tr v-if="!(consistencyReport.issues || []).length">
                <td colspan="4" class="muted py-4">暂无问题</td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" variant="tonal" :disabled="consistencyReport.ok" @click="repairConsistency">修复可自动处理项</v-btn>
          <v-btn @click="consistencyDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="settingsDialog" max-width="720">
      <v-card>
        <v-card-title>设置</v-card-title>
        <v-card-text>
          <div class="text-subtitle-2 mb-3">LLM API 配置</div>
          <v-alert v-if="aiSettingsLoading" type="info" variant="tonal" density="compact" class="mb-3">
            正在读取 AI 配置...
          </v-alert>
          <v-alert v-if="aiSettingsError" type="error" variant="tonal" density="compact" class="mb-3">
            {{ aiSettingsError }}
          </v-alert>
          <v-alert
            v-if="!aiSettingsLoading && aiSettings.provider !== 'mock' && !aiSettings.has_api_key && !aiSettings.apiKey"
            type="warning"
            variant="tonal"
            density="compact"
            class="mb-3"
          >
            当前未配置 API Key，AI 生成会返回“未配置 AI API Key”。
          </v-alert>
          <v-row>
            <v-col cols="12" md="6">
              <v-select v-model="aiSettings.provider" :items="aiProviderOptions" item-title="title" item-value="value" label="Provider" />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="aiSettings.model" label="模型" placeholder="例如 deepseek-v4-pro" />
            </v-col>
          </v-row>
          <v-text-field v-model="aiSettings.baseUrl" label="Base URL" placeholder="https://example.com/v1" />
          <v-text-field
            v-model="aiSettings.apiKey"
            label="API Key"
            type="password"
            autocomplete="off"
            :placeholder="aiSettings.has_api_key ? '已保存，留空则不修改' : '请输入 API Key'"
          />
          <v-checkbox v-model="aiSettings.clearApiKey" label="清除已保存的 API Key" density="compact" hide-details />
          <v-row>
            <v-col cols="12" md="6">
              <v-slider v-model="aiSettings.temperature" min="0" max="1.4" step="0.1" thumb-label label="温度" />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model.number="aiSettings.max_tokens" type="number" label="最大 tokens" min="1" />
            </v-col>
          </v-row>
          <div v-if="!aiSettingsLoading" class="text-caption muted">
            当前状态：{{ aiSettings.has_api_key ? '已保存 API Key' : '未保存 API Key' }}。
            选择 mock 可在无 API Key 时离线验证 AI 流程。
          </div>
          <div class="text-caption muted mt-1">配置文件：{{ aiSettings.config_path || '默认 config.json' }}</div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="settingsDialog = false">关闭</v-btn>
          <v-btn color="primary" :loading="aiSettingsSaving" :disabled="aiSettingsSaving || aiSettingsLoading" @click="saveAiSettings">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.open" :color="snackbar.color" timeout="3200">{{ snackbar.text }}</v-snackbar>
  </v-app>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { apiRequest, type ApiMethod, type ApiRequestOptions } from './api/client'
import { aiLogApplyLabel, aiLogIsPreviewApplyCandidate, aiLogResultDisplayMode, aiLogResultText, objectResultFromAiLog, resolveAiLogResult, textResultFromAiLog } from './utils/aiLog'
import {
  buildCharacterCreatePayload,
  characterFieldLabel,
  characterPayloadFromAiResult,
  characterPayloadFromValue,
  characterSectionVisibilityDefaults,
  characterTabLabel,
  characterTabs,
  defaultCharacterDeveloper,
  formatCharacterValue as formatValue,
  isPlainObject,
} from './utils/character'
import { renderMarkdown, shouldRenderMarkdownValue } from './utils/markdown'

const EmptyState = defineComponent({
  props: { icon: String, text: String },
  setup(props) {
    return () =>
      h('div', { class: 'd-flex flex-column align-center justify-center h-100 muted', style: 'min-height: 360px' }, [
        h('i', { class: ['mdi', props.icon, 'text-h2'] }),
        h('p', { class: 'mt-4 text-body-1' }, props.text),
      ])
  },
})

const modules = [
  { id: 'overview', title: '项目总览', icon: 'mdi-view-dashboard-outline' },
  { id: 'worldbook', title: '世界书', icon: 'mdi-book-open-page-variant' },
  { id: 'characters', title: '人物卡', icon: 'mdi-account-multiple-outline' },
  { id: 'scripts', title: '剧本', icon: 'mdi-script-text-outline' },
  { id: 'presets', title: '预设', icon: 'mdi-palette-outline' },
]
const statusOptions = ['draft', 'complete', 'archived']
const relationTypes = ['source', 'influence', 'related', 'oppose']
const characterTypes = ['protagonist', 'supporting', 'antagonist', 'npc']
const characterRelationTypes = ['family', 'friend', 'love', 'enemy', 'rival', 'ally', 'mentor', 'subordinate', 'colleague', 'stranger']
const scriptTypes = [
  { value: 'outline', title: '总纲' },
  { value: 'volume', title: '卷' },
  { value: 'part', title: '篇章' },
  { value: 'chapter', title: '章节' },
  { value: 'scene', title: '场景' },
  { value: 'fragment', title: '片段' },
]
const presetSceneTypeOptions = [
  { value: 'worldbook', title: '世界书生成' },
  { value: 'character', title: '人物卡生成' },
  { value: 'script', title: '剧本生成' },
  { value: 'general', title: '通用创作' },
]

const loading = ref(false)
const projects = ref<any[]>([])
const activeProjectId = ref('')
const activeModule = ref('overview')
const selectedProject = computed(() => projects.value.find((item) => item.id === activeProjectId.value))
const projectOverview = ref<any>({
  pending_ai_drafts: { total: 0, by_target_type: {}, recent: [] },
  recent: { worldbook: [], characters: [], scripts: [], presets: [] },
})
const activeProjectAiDraftCount = computed(() => Number(projectOverview.value?.pending_ai_drafts?.total ?? selectedProject.value?.counts?.ai_drafts ?? 0))
const overviewRecentItems = computed(() => {
  const recent = projectOverview.value?.recent || {}
  return [
    ...(recent.worldbook || []).map((item: any) => ({ ...item, type: 'worldbook' })),
    ...(recent.characters || []).map((item: any) => ({ ...item, type: 'character' })),
    ...(recent.scripts || []).map((item: any) => ({ ...item, type: 'script' })),
    ...(recent.presets || []).map((item: any) => ({ ...item, type: 'preset' })),
  ]
    .filter((item) => item.id)
    .sort((a, b) => String(b.updated_at || '').localeCompare(String(a.updated_at || '')))
    .slice(0, 8)
})
const overviewDraftChips = computed(() => {
  const byType = projectOverview.value?.pending_ai_drafts?.by_target_type || {}
  return Object.entries(byType)
    .map(([type, count]) => ({ type, label: overviewModuleText(type), count: Number(count || 0) }))
    .filter((item) => item.count > 0)
})
const snackbar = reactive({ open: false, text: '', color: 'success' })
const aiLogs = ref<any[]>([])
const aiLogDialog = ref(false)
const selectedAiLog = ref<any>(null)
const aiLogPreviewTab = ref('basic')
const settingsDialog = ref(false)
const aiSettingsLoading = ref(false)
const aiSettingsSaving = ref(false)
const aiSettingsError = ref('')
const aiProviderOptions = [
  { title: 'OpenAI Compatible', value: 'openai_compatible' },
  { title: 'Mock（离线测试）', value: 'mock' },
]
const aiSettings = reactive<any>({
  provider: 'openai_compatible',
  baseUrl: '',
  apiKey: '',
  model: '',
  temperature: 0.7,
  max_tokens: 4096,
  has_api_key: false,
  clearApiKey: false,
  config_path: '',
})

const categories = ref<any[]>([])
const worldEntries = ref<any[]>([])
const selectedWorldEntry = ref<any>(null)
const worldFilters = reactive({ category_id: '', q: '' })
const worldGraph = reactive<any>({ nodes: [], edges: [] })

const characters = ref<any[]>([])
const selectedCharacter = ref<any>(null)
const characterFilters = reactive({ q: '', character_type: '' })
const characterViewMode = ref('developer')
const characterTab = ref('basic')
const characterVisibilityModeOptions = [
  { title: '完整', value: 'full' },
  { title: '部分', value: 'partial' },
  { title: '自定义', value: 'custom' },
  { title: '隐藏', value: 'hidden' },
]

const scriptsTree = ref<any[]>([])
const selectedScript = ref<any>(null)
const scriptReferences = ref<any[]>([])

const presets = ref<any[]>([])
const selectedPreset = ref<any>(null)
const presetFilters = reactive({ q: '' })

const projectDialog = ref(false)
const projectShowArchived = ref(false)
const projectForm = reactive<any>({ id: '', name: '', genre: '', description: '', settings: defaultProjectSettings() })
const projectDeleteDialog = ref(false)
const projectDeleteTarget = ref<any>(null)
const projectDeleteConfirmName = ref('')
const worldbookVisibilityOptions = [
  { title: '公开', value: 'public' },
  { title: '私密', value: 'private' },
  { title: '隐秘', value: 'secret' },
]
const characterViewModeOptions = [
  { title: '开发者', value: 'developer' },
  { title: '玩家', value: 'player' },
]
const projectImportDialog = ref(false)
const projectImportContent = ref('')
const projectImportPreview = ref<any>(null)

const categoryDialog = ref(false)
const categoryForm = reactive<any>({ id: '', name: '', parent_id: null, description: '', template: { sections: [] }, custom_fields: [] })
const categoryTemplateJson = ref('{}')

const worldEntryDialog = ref(false)
const worldEntryForm = reactive<any>({})
const worldStructuredJson = ref('{}')
const worldRelationDialog = ref(false)
const worldRelationForm = reactive<any>({ target_id: '', relation_type: 'related', strength: 3, label: '', description: '' })

const aiDialog = reactive<any>({
  open: false,
  target: '',
  title: '',
  prompt: '',
  result: '',
  min_length: 300,
  max_length: 800,
  temperature: 0.7,
  section: '',
  field: '',
  apply: false,
  running: false,
  activeMessage: '',
  progress: [],
  previewTab: 'basic',
  contractIssues: [],
  pendingApplyTarget: '',
  pendingApplyPayload: null,
  pendingApplyMeta: null,
})
let aiProgressTimer: number | undefined
let aiAbortController: AbortController | null = null

const characterDialog = ref(false)
const characterForm = reactive<any>({})
const characterEditTab = ref('developer')
const characterDeveloperJson = ref('{}')
const characterVisibilityConfig = reactive<any>({})
const characterRelationDialog = ref(false)
const characterRelationForm = reactive<any>({ target_id: '', relation_type: 'friend', direction: 'bidirectional', numeric_value: 0, description: '' })

const scriptDialog = ref(false)
const scriptForm = reactive<any>({})
const scriptReferenceDialog = ref(false)
const scriptReferenceForm = reactive<any>({ ref_type: 'worldbook', ref_id: '', description: '' })

const presetDialog = ref(false)
const presetForm = reactive<any>({})
const presetDimensionsJson = ref('[]')
const presetBlocksJson = ref('[]')
const presetScenesJson = ref('[]')
const presetApplyDialog = ref(false)
const presetApplyForm = reactive<any>({ scene_type: 'worldbook', scene_requirements: '' })
const presetApplyResult = ref('')
const presetCombineDialog = ref(false)
const presetCombineForm = reactive<any>({ override_id: '', name: '', category: '组合', description: '' })
const presetCombineResult = ref<any>(null)
const versionDialog = ref(false)
const versionRows = ref<any[]>([])
const versionContext = reactive<any>({ entityType: '', entityId: '' })
const versionDiff = ref<any>(null)
const consistencyDialog = ref(false)
const consistencyReport = reactive<any>({ ok: true, summary: {}, issues: [] })

const flatScripts = computed(() => {
  const rows: any[] = []
  const walk = (nodes: any[], depth = 0) => {
    for (const node of nodes) {
      rows.push({ ...node, depth })
      walk(node.children || [], depth + 1)
    }
  }
  walk(scriptsTree.value)
  return rows
})
const worldGraphEdges = computed(() => worldGraph.edges || [])
const isIterating = computed(() => String(aiDialog.target).endsWith('-iterate'))
const aiRunButtonText = computed(() => {
  if (!isIterating.value) return '生成'
  if (aiDialog.target === 'character-iterate') return aiDialog.apply ? '执行并保存' : '生成预览'
  return '执行迭代'
})
const aiDialogResultCanRender = computed(() => Boolean(aiDialog.result) && ['worldbook', 'script', 'worldbook-iterate', 'script-iterate'].includes(String(aiDialog.target)))
const aiDialogIsCharacterResult = computed(() => ['character', 'character-iterate'].includes(String(aiDialog.target)))
const aiDialogCharacterPreview = computed(() => characterPayloadFromAiResult(aiDialog.result))
const selectedAiLogResultMode = computed(() => aiLogResultDisplayMode(selectedAiLog.value))
const selectedAiLogResultRaw = computed(() => aiLogResultText(selectedAiLog.value))
const selectedAiLogMarkdownResult = computed(() => {
  const text = textResultFromAiLog(selectedAiLog.value)
  return text.ok ? text.result : selectedAiLogResultRaw.value
})
const selectedAiLogCharacterPreview = computed(() => characterPayloadFromAiLog(selectedAiLog.value))
const presetCombineOverrideOptions = computed(() => presets.value.filter((preset) => preset.id !== selectedPreset.value?.id))
const characterVisibilityRows = computed(() => buildCharacterVisibilityRows(parseJsonSafe(characterDeveloperJson.value, {}), characterVisibilityConfig))
const characterPlayerPreviewJson = computed(() => JSON.stringify(applyCharacterVisibility(parseJsonSafe(characterDeveloperJson.value, {}), characterVisibilityConfig), null, 2))
const iconButtonLabels: Record<string, string> = {
  'mdi-plus': '新建',
  'mdi-refresh': '刷新',
  'mdi-cog-outline': '设置',
  'mdi-pencil-outline': '编辑',
  'mdi-archive-outline': '归档',
  'mdi-archive-arrow-up-outline': '恢复',
  'mdi-restore': '重置',
  'mdi-folder-plus-outline': '新建分类',
  'mdi-book-plus-outline': '新建条目',
  'mdi-eye-outline': '查看',
  'mdi-robot-outline': 'AI 生成',
  'mdi-auto-fix': 'AI 整理',
  'mdi-creation': 'AI 迭代',
  'mdi-vector-link': '新增关联',
  'mdi-account-multiple-plus-outline': '新建人物关系',
  'mdi-history': '版本历史',
  'mdi-export': '导出',
  'mdi-import': '导入',
  'mdi-content-copy': '复制',
  'mdi-content-save-outline': '保存',
  'mdi-playlist-check': '应用预设',
  'mdi-vector-combine': '组合预设',
  'mdi-pencil': '编辑',
  'mdi-delete-outline': '删除',
  'mdi-link-plus': '新增引用',
  'mdi-file-tree-outline': '新增子节点',
  'mdi-close': '关闭',
  'mdi-clipboard-check-outline': '质量检查',
  'mdi-shield-check-outline': '数据检查',
}
let buttonTitleObserver: MutationObserver | null = null
let buttonTitleRefreshFrame = 0

onMounted(async () => {
  await loadProjects()
  installButtonTitles()
})

onBeforeUnmount(() => {
  document.removeEventListener('mouseover', ensureHoveredButtonTitle)
  document.removeEventListener('focusin', ensureHoveredButtonTitle)
  buttonTitleObserver?.disconnect()
  buttonTitleObserver = null
  if (buttonTitleRefreshFrame) window.cancelAnimationFrame(buttonTitleRefreshFrame)
  cancelAiRequest()
  if (aiProgressTimer) window.clearInterval(aiProgressTimer)
})

watch(activeProjectId, async () => {
  await loadCurrentModule()
})

watch(activeModule, async () => {
  await loadCurrentModule()
})

watch(projectShowArchived, async () => {
  await loadProjects()
})

async function request(method: ApiMethod, url: string, data?: any, options: ApiRequestOptions = {}) {
  loading.value = true
  try {
    return await apiRequest(method, url, data, options)
  } finally {
    loading.value = false
  }
}

async function installButtonTitles() {
  await nextTick()
  refreshButtonTitles()
  document.addEventListener('mouseover', ensureHoveredButtonTitle)
  document.addEventListener('focusin', ensureHoveredButtonTitle)
  buttonTitleObserver = new MutationObserver(scheduleButtonTitleRefresh)
  buttonTitleObserver.observe(document.body, { childList: true, subtree: true })
}

function scheduleButtonTitleRefresh() {
  if (buttonTitleRefreshFrame) return
  buttonTitleRefreshFrame = window.requestAnimationFrame(() => {
    buttonTitleRefreshFrame = 0
    refreshButtonTitles()
  })
}

function refreshButtonTitles() {
  document.querySelectorAll<HTMLElement>('button').forEach((button) => {
    const label = inferButtonLabel(button)
    if (!label) return
    button.setAttribute('title', label)
    if (!button.getAttribute('aria-label') && !visibleButtonText(button)) button.setAttribute('aria-label', label)
  })
}

function ensureHoveredButtonTitle(event: Event) {
  const button = (event.target as HTMLElement | null)?.closest('button') as HTMLButtonElement | null
  if (!button || button.disabled) return
  const label = inferButtonLabel(button)
  if (!label) return
  button.setAttribute('title', label)
  if (!button.getAttribute('aria-label') && !visibleButtonText(button)) button.setAttribute('aria-label', label)
}

function inferButtonLabel(button: HTMLElement) {
  const explicit = button.getAttribute('aria-label') || button.getAttribute('title')
  if (explicit) return explicit.trim()
  const text = visibleButtonText(button)
  if (text) return text
  const icon = Array.from(button.querySelectorAll<HTMLElement>('[class*="mdi-"]'))
    .flatMap((item) => Array.from(item.classList))
    .find((className) => className.startsWith('mdi-') && className !== 'mdi')
  return icon ? iconButtonLabels[icon] || icon.replace(/^mdi-/, '').replace(/-/g, ' ') : ''
}

function visibleButtonText(button: HTMLElement) {
  return (button.innerText || button.textContent || '').replace(/\s+/g, ' ').trim()
}

function toast(text: string, color = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.open = true
}

function resetReactive(target: any, value: any) {
  for (const key of Object.keys(target)) delete target[key]
  Object.assign(target, value)
}

function resetAiDialog(value: any) {
  cancelAiRequest()
  Object.assign(aiDialog, {
    open: true,
    target: '',
    title: '',
    prompt: '',
    result: '',
    min_length: 300,
    max_length: 1000,
    temperature: currentProjectAiTemperature(),
    section: '',
    field: '',
    apply: false,
    running: false,
    activeMessage: '',
    progress: [],
    previewTab: 'basic',
    contractIssues: [],
    pendingApplyTarget: '',
    pendingApplyPayload: null,
    pendingApplyMeta: null,
    ...value,
  })
}

function closeAiDialog() {
  cancelAiRequest()
  aiDialog.open = false
}

function startAiProgress(messages: string[]) {
  stopAiProgress(false)
  aiDialog.running = true
  aiDialog.progress = []
  let index = 0
  const tick = () => {
    if (index >= messages.length) {
      if (aiProgressTimer) window.clearInterval(aiProgressTimer)
      aiProgressTimer = undefined
      return
    }
    const message = messages[Math.min(index, messages.length - 1)]
    aiDialog.activeMessage = message
    aiDialog.progress.push({ time: new Date().toLocaleTimeString('zh-CN'), message })
    index += 1
  }
  tick()
  aiProgressTimer = window.setInterval(tick, 1800)
}

function stopAiProgress(done = true, logs: any[] = []) {
  if (aiProgressTimer) window.clearInterval(aiProgressTimer)
  aiProgressTimer = undefined
  if (logs?.length) aiDialog.progress = logs
  if (done) {
    aiDialog.running = false
    aiDialog.activeMessage = '已完成'
  }
}

function cancelAiRequest() {
  if (!aiAbortController) return
  aiAbortController.abort()
  aiAbortController = null
  if (aiDialog.running) {
    stopAiProgress(false)
    aiDialog.running = false
    aiDialog.activeMessage = '已取消'
    aiDialog.progress.push({ time: new Date().toLocaleTimeString('zh-CN'), message: '用户已取消本次 AI 请求' })
  }
}

function parseJson(text: string, fallback: any) {
  try {
    return JSON.parse(text || JSON.stringify(fallback))
  } catch {
    toast('JSON 格式不正确', 'error')
    throw new Error('Invalid JSON')
  }
}

function parseJsonSafe(text: string, fallback: any) {
  try {
    return JSON.parse(text || JSON.stringify(fallback))
  } catch {
    return fallback
  }
}

function cloneJson(value: any) {
  return JSON.parse(JSON.stringify(value ?? {}))
}

function defaultProjectSettings() {
  return {
    status: 'active',
    default_style: '',
    ai: { temperature: 0.7, max_tokens: 4096 },
    modules: { worldbook: true, characters: true, scripts: true, presets: true },
    defaults: { worldbook_visibility: 'public', character_view_mode: 'developer' },
  }
}

function normalizeProjectSettings(settings: any) {
  const base = defaultProjectSettings()
  const source = isPlainObject(settings) ? settings : {}
  const ai = isPlainObject(source.ai) ? source.ai : {}
  const modules = isPlainObject(source.modules) ? source.modules : {}
  const defaults = isPlainObject(source.defaults) ? source.defaults : {}
  return {
    ...source,
    status: ['active', 'archived'].includes(source.status) ? source.status : base.status,
    default_style: typeof source.default_style === 'string' ? source.default_style : '',
    ai: {
      ...ai,
      temperature: clampNumber(ai.temperature, base.ai.temperature, 0, 1.4),
      max_tokens: clampNumber(ai.max_tokens ?? ai.maxTokens, base.ai.max_tokens, 1024, 20000),
    },
    modules: {
      worldbook: Boolean(modules.worldbook ?? base.modules.worldbook),
      characters: Boolean(modules.characters ?? base.modules.characters),
      scripts: Boolean(modules.scripts ?? base.modules.scripts),
      presets: Boolean(modules.presets ?? base.modules.presets),
    },
    defaults: {
      ...defaults,
      worldbook_visibility: ['public', 'private', 'secret'].includes(defaults.worldbook_visibility) ? defaults.worldbook_visibility : base.defaults.worldbook_visibility,
      character_view_mode: ['developer', 'player'].includes(defaults.character_view_mode) ? defaults.character_view_mode : base.defaults.character_view_mode,
    },
  }
}

function clampNumber(value: any, fallback: number, min: number, max: number) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return fallback
  return Math.min(max, Math.max(min, parsed))
}

function currentProjectSettings() {
  return normalizeProjectSettings(selectedProject.value?.settings)
}

function currentProjectAiTemperature() {
  return currentProjectSettings().ai.temperature
}

function defaultCharacterVisibilityRule(section: string) {
  const visible = characterSectionVisibilityDefaults[section] ?? false
  return { visible, displayMode: visible ? 'full' : 'hidden', customDisplay: visible ? '' : '未知' }
}

function normalizeCharacterVisibilityRule(section: string, rule: any) {
  const base = defaultCharacterVisibilityRule(section)
  if (!isPlainObject(rule)) return base
  return {
    visible: Boolean(rule.visible),
    displayMode: ['full', 'partial', 'custom', 'hidden'].includes(rule.displayMode) ? rule.displayMode : base.displayMode,
    customDisplay: typeof rule.customDisplay === 'string' ? rule.customDisplay : base.customDisplay,
  }
}

function normalizeCharacterVisibilityConfig(visibility: any, developer: any) {
  const normalized: any = {}
  const source = isPlainObject(developer) ? developer : {}
  for (const section of characterTabs) {
    const sectionValue = source[section]
    const incoming = isPlainObject(visibility?.[section]) ? visibility[section] : {}
    if (isPlainObject(sectionValue)) {
      normalized[section] = {}
      for (const field of Object.keys(sectionValue)) {
        normalized[section][field] = normalizeCharacterVisibilityRule(section, incoming[field])
      }
    } else {
      normalized[section] = { __section__: normalizeCharacterVisibilityRule(section, incoming.__section__ || incoming) }
    }
  }
  return normalized
}

function resetCharacterVisibilityConfig(visibility: any, developer: any) {
  resetReactive(characterVisibilityConfig, normalizeCharacterVisibilityConfig(visibility, developer))
}

function ensureCharacterVisibilityRule(config: any, section: string, field: string) {
  if (!isPlainObject(config[section])) config[section] = {}
  if (!isPlainObject(config[section][field])) config[section][field] = defaultCharacterVisibilityRule(section)
  return config[section][field]
}

function buildCharacterVisibilityRows(developer: any, config: any) {
  if (!isPlainObject(developer)) return []
  const rows: any[] = []
  for (const section of characterTabs) {
    const sectionValue = developer[section]
    if (isPlainObject(sectionValue)) {
      for (const field of Object.keys(sectionValue)) {
        rows.push({
          section,
          field,
          sectionLabel: characterTabLabel(section),
          fieldLabel: characterFieldLabel(field),
          rule: ensureCharacterVisibilityRule(config, section, field),
        })
      }
    } else {
      rows.push({
        section,
        field: '__section__',
        sectionLabel: characterTabLabel(section),
        fieldLabel: `整段（${section}）`,
        rule: ensureCharacterVisibilityRule(config, section, '__section__'),
      })
    }
  }
  return rows
}

function visibleCharacterValue(value: any, rule: any) {
  if (rule?.visible && rule.displayMode === 'full') return value
  if (rule?.visible && ['partial', 'custom'].includes(rule.displayMode)) return rule.customDisplay || '部分可见'
  return rule?.customDisplay || '未知'
}

function applyCharacterVisibility(developer: any, visibility: any) {
  if (!isPlainObject(developer)) return {}
  const player: any = {}
  for (const section of characterTabs) {
    const sectionValue = developer[section]
    const sectionRules = isPlainObject(visibility?.[section]) ? visibility[section] : {}
    if (isPlainObject(sectionValue)) {
      player[section] = {}
      for (const [field, value] of Object.entries(sectionValue)) {
        player[section][field] = visibleCharacterValue(value, sectionRules[field] || defaultCharacterVisibilityRule(section))
      }
    } else {
      player[section] = visibleCharacterValue(sectionValue, sectionRules.__section__ || defaultCharacterVisibilityRule(section))
    }
  }
  return player
}

async function loadProjects() {
  projects.value = await request('GET', `/projects${projectShowArchived.value ? '?include_archived=true' : ''}`)
  if (activeProjectId.value && !projects.value.some((project) => project.id === activeProjectId.value)) activeProjectId.value = ''
  if (!activeProjectId.value && projects.value.length) activeProjectId.value = projects.value[0].id
}

async function loadCurrentModule() {
  if (!activeProjectId.value) return
  if (activeModule.value === 'overview') {
    await loadProjects()
    await loadProjectOverview()
    await loadAiLogs()
  }
  if (activeModule.value === 'worldbook') await loadWorldbook()
  if (activeModule.value === 'characters') await loadCharacters()
  if (activeModule.value === 'scripts') await loadScripts()
  if (activeModule.value === 'presets') await loadPresets()
}

async function loadProjectOverview() {
  if (!activeProjectId.value) return
  projectOverview.value = await request('GET', `/projects/${activeProjectId.value}/overview`)
}

async function loadAiLogs() {
  if (!activeProjectId.value) return
  aiLogs.value = await request('GET', `/projects/${activeProjectId.value}/ai/logs?limit=30`)
}

function overviewModuleText(type: string) {
  const map: any = { worldbook: '世界书', character: '人物卡', script: '剧本', preset: '预设' }
  return map[type] || type || '未知'
}

async function openOverviewRecentItem(item: any) {
  if (!item?.id) return
  if (item.type === 'worldbook') {
    activeModule.value = 'worldbook'
    await loadWorldbook()
    await selectWorldEntry({ id: item.id })
    return
  }
  if (item.type === 'character') {
    activeModule.value = 'characters'
    await loadCharacters()
    await selectCharacter({ id: item.id })
    return
  }
  if (item.type === 'script') {
    activeModule.value = 'scripts'
    await loadScripts()
    await selectScript({ id: item.id })
    return
  }
  if (item.type === 'preset') {
    activeModule.value = 'presets'
    await loadPresets()
    selectedPreset.value = presets.value.find((preset) => preset.id === item.id) || null
  }
}

function openAiLogDialog(log: any) {
  selectedAiLog.value = log
  aiLogPreviewTab.value = 'basic'
  aiLogDialog.value = true
}

function formatJson(value: any) {
  try {
    return JSON.stringify(value ?? {}, null, 2)
  } catch {
    return String(value ?? '')
  }
}

async function copyAiLogPrompt() {
  if (!selectedAiLog.value?.prompt) return
  await navigator.clipboard.writeText(selectedAiLog.value.prompt)
  toast('Prompt 已复制')
}

async function runConsistencyCheck() {
  if (!activeProjectId.value) return
  const data = await request('GET', `/projects/${activeProjectId.value}/consistency/check`)
  resetReactive(consistencyReport, data)
  consistencyDialog.value = true
}

async function exportProject() {
  if (!activeProjectId.value) return
  const data = await request('GET', `/projects/${activeProjectId.value}/export`)
  downloadText(data.filename, data.content)
}

async function repairConsistency() {
  if (!activeProjectId.value) return
  const data = await request('POST', `/projects/${activeProjectId.value}/consistency/repair`)
  resetReactive(consistencyReport, data.after)
  toast(`已修复 ${data.actions?.length || 0} 个问题`)
}

async function reloadCurrent() {
  await loadProjects()
  await loadCurrentModule()
}

async function openSettingsDialog() {
  settingsDialog.value = true
  await loadAiSettings()
}

function applyAiSettingsData(data: any) {
  resetReactive(aiSettings, {
    provider: data.provider || 'openai_compatible',
    baseUrl: data.baseUrl || '',
    apiKey: '',
    model: data.model || '',
    temperature: data.temperature ?? 0.7,
    max_tokens: data.max_tokens || 4096,
    has_api_key: Boolean(data.has_api_key),
    clearApiKey: false,
    config_path: data.config_path || '',
  })
}

async function loadAiSettings() {
  aiSettingsLoading.value = true
  aiSettingsError.value = ''
  try {
    const data = await request('GET', '/settings/ai', undefined, { preferAiReady: true })
    applyAiSettingsData(data)
  } catch (error: any) {
    aiSettingsError.value = error?.message || '加载 AI 配置失败'
    toast(aiSettingsError.value, 'error')
  } finally {
    aiSettingsLoading.value = false
  }
}

async function saveAiSettings() {
  if (aiSettingsLoading.value || aiSettingsSaving.value) return
  aiSettingsSaving.value = true
  aiSettingsError.value = ''
  try {
    const data = await request('PUT', '/settings/ai', {
      provider: aiSettings.provider,
      baseUrl: aiSettings.baseUrl,
      apiKey: aiSettings.apiKey,
      model: aiSettings.model,
      temperature: aiSettings.temperature,
      max_tokens: aiSettings.max_tokens,
      clearApiKey: aiSettings.clearApiKey,
    }, { preferAiReady: true })
    applyAiSettingsData(data)
    toast('AI 配置已保存')
  } catch (error: any) {
    aiSettingsError.value = error?.message || '保存 AI 配置失败'
    toast(aiSettingsError.value, 'error')
  } finally {
    aiSettingsSaving.value = false
  }
}

function openProjectDialog(project?: any) {
  Object.assign(projectForm, {
    id: project?.id || '',
    name: project?.name || '',
    genre: project?.genre || '',
    description: project?.description || '',
    settings: normalizeProjectSettings(project?.settings),
  })
  projectDialog.value = true
}

function openProjectImportDialog() {
  projectImportContent.value = ''
  projectImportPreview.value = null
  projectImportDialog.value = true
}

async function readProjectImportFile(value: any) {
  const file = Array.isArray(value) ? value[0] : value
  if (!file) return
  projectImportContent.value = await file.text()
  projectImportPreview.value = null
}

async function previewProjectImport() {
  projectImportPreview.value = await request('POST', '/projects/import/preview', { content: projectImportContent.value })
}

async function importProject() {
  if (!projectImportPreview.value) await previewProjectImport()
  if (projectImportPreview.value?.valid === false) return
  const data = await request('POST', '/projects/import', { content: projectImportContent.value })
  projectImportDialog.value = false
  await loadProjects()
  activeProjectId.value = data.project_id
  toast('项目已导入')
}

async function saveProject() {
  const payload = {
    name: projectForm.name,
    genre: projectForm.genre,
    description: projectForm.description,
    settings: normalizeProjectSettings(projectForm.settings),
  }
  const row = projectForm.id ? await request('PUT', `/projects/${projectForm.id}`, payload) : await request('POST', '/projects', payload)
  projectDialog.value = false
  await loadProjects()
  activeProjectId.value = row.id
  toast(projectForm.id ? '项目已保存' : '项目已创建')
}

async function archiveProject(project: any, archived: boolean) {
  await request('POST', `/projects/${project.id}/archive`, { archived })
  await loadProjects()
  toast(archived ? '项目已归档' : '项目已恢复')
}

async function resetDemoProject(project: any) {
  if (!window.confirm(`重置 ${project.name} 将恢复内置 demo 基线内容。确认继续？`)) return
  const row = await request('POST', `/projects/${project.id}/demo/reset`)
  await loadProjects()
  activeProjectId.value = row.id
  await loadCurrentModule()
  toast('Demo 已重置')
}

function openProjectDeleteDialog(project: any) {
  projectDeleteTarget.value = project
  projectDeleteConfirmName.value = ''
  projectDeleteDialog.value = true
}

async function deleteProject() {
  if (!projectDeleteTarget.value) return
  const deletedId = projectDeleteTarget.value.id
  await request('DELETE', `/projects/${deletedId}`, { confirm_name: projectDeleteConfirmName.value })
  projectDeleteDialog.value = false
  projectDeleteTarget.value = null
  projectDeleteConfirmName.value = ''
  if (activeProjectId.value === deletedId) activeProjectId.value = ''
  await loadProjects()
  await loadCurrentModule()
  toast('项目已删除')
}

async function loadWorldbook() {
  await Promise.all([loadCategories(), loadWorldEntries(), loadWorldGraph()])
}

async function loadCategories() {
  categories.value = await request('GET', `/projects/${activeProjectId.value}/worldbook/categories`)
}

async function loadWorldEntries() {
  const query = new URLSearchParams()
  if (worldFilters.category_id) query.set('category_id', worldFilters.category_id)
  if (worldFilters.q) query.set('q', worldFilters.q)
  worldEntries.value = await request('GET', `/projects/${activeProjectId.value}/worldbook/entries?${query}`)
  if (selectedWorldEntry.value) {
    const found = worldEntries.value.find((item) => item.id === selectedWorldEntry.value.id)
    selectedWorldEntry.value = found ? await request('GET', `/projects/${activeProjectId.value}/worldbook/entries/${found.id}`) : null
  }
}

async function loadWorldGraph() {
  worldGraph.nodes = []
  worldGraph.edges = []
  const data = await request('GET', `/projects/${activeProjectId.value}/worldbook/graph`)
  worldGraph.nodes = data.nodes
  worldGraph.edges = data.edges
}

async function selectWorldEntry(entry: any) {
  selectedWorldEntry.value = await request('GET', `/projects/${activeProjectId.value}/worldbook/entries/${entry.id}`)
}

function selectWorldEntryById(id: string) {
  const found = worldEntries.value.find((item) => item.id === id)
  if (found) selectWorldEntry(found)
}

function openCategoryDialog(cat?: any) {
  resetReactive(categoryForm, cat || { id: '', name: '', parent_id: null, description: '', template: { sections: [] }, custom_fields: [] })
  categoryTemplateJson.value = JSON.stringify(categoryForm.template || { sections: [] }, null, 2)
  categoryDialog.value = true
}

async function saveCategory() {
  const data = { ...categoryForm, template: parseJson(categoryTemplateJson.value, { sections: [] }) }
  if (categoryForm.id) await request('PUT', `/projects/${activeProjectId.value}/worldbook/categories/${categoryForm.id}`, data)
  else await request('POST', `/projects/${activeProjectId.value}/worldbook/categories`, data)
  categoryDialog.value = false
  await loadCategories()
  toast('分类已保存')
}

async function deleteCategory() {
  await request('DELETE', `/projects/${activeProjectId.value}/worldbook/categories/${categoryForm.id}`)
  categoryDialog.value = false
  await loadWorldbook()
  toast('分类已删除')
}

function openWorldEntryDialog(entry?: any) {
  resetReactive(worldEntryForm, entry || { id: '', title: '', category_id: worldFilters.category_id || categories.value[0]?.id, content: '', structured_data: {}, importance: 3, visibility: 'public', status: 'draft', tags: [] })
  worldStructuredJson.value = JSON.stringify(worldEntryForm.structured_data || {}, null, 2)
  worldEntryDialog.value = true
}

async function saveWorldEntry() {
  const data = { ...worldEntryForm, structured_data: parseJson(worldStructuredJson.value, {}) }
  if (worldEntryForm.id) await request('PUT', `/projects/${activeProjectId.value}/worldbook/entries/${worldEntryForm.id}`, data)
  else selectedWorldEntry.value = await request('POST', `/projects/${activeProjectId.value}/worldbook/entries`, data)
  worldEntryDialog.value = false
  await loadWorldbook()
  toast('条目已保存')
}

async function deleteWorldEntry() {
  if (!selectedWorldEntry.value) return
  await request('DELETE', `/projects/${activeProjectId.value}/worldbook/entries/${selectedWorldEntry.value.id}`)
  selectedWorldEntry.value = null
  await loadWorldbook()
  toast('条目已删除')
}

function openWorldRelationDialog() {
  Object.assign(worldRelationForm, { target_id: '', relation_type: 'related', strength: 3, label: '', description: '' })
  worldRelationDialog.value = true
}

async function saveWorldRelation() {
  await request('POST', `/projects/${activeProjectId.value}/worldbook/relations`, { ...worldRelationForm, source_id: selectedWorldEntry.value.id })
  worldRelationDialog.value = false
  await selectWorldEntry(selectedWorldEntry.value)
  await loadWorldGraph()
  toast('关联已创建')
}

async function deleteWorldRelation(id: string) {
  await request('DELETE', `/projects/${activeProjectId.value}/worldbook/relations/${id}`)
  await selectWorldEntry(selectedWorldEntry.value)
  await loadWorldGraph()
  toast('关联已删除')
}

function openWorldAiDialog() {
  resetAiDialog({ target: 'worldbook', title: 'AI 生成世界书条目', min_length: 800, max_length: 1800 })
}

async function exportWorldbook() {
  const data = await request('GET', `/projects/${activeProjectId.value}/worldbook/export?format=markdown&ids=${selectedWorldEntry.value?.id || ''}`)
  downloadText(data.filename, data.content)
}

async function loadCharacters() {
  const query = new URLSearchParams()
  if (characterFilters.q) query.set('q', characterFilters.q)
  if (characterFilters.character_type) query.set('character_type', characterFilters.character_type)
  characters.value = await request('GET', `/projects/${activeProjectId.value}/characters?${query}`)
  if (selectedCharacter.value) {
    const found = characters.value.find((item) => item.id === selectedCharacter.value.id)
    if (found) await selectCharacter(found)
    else selectedCharacter.value = null
  }
  if (!worldEntries.value.length) await loadWorldEntries()
}

async function selectCharacter(char: any) {
  selectedCharacter.value = await request('GET', `/projects/${activeProjectId.value}/characters/detail/${char.id}`)
}

function openCharacterDialog(char?: any) {
  const base = char || { id: '', name: '', character_type: 'supporting', tags: [], world_entry_ids: [] }
  resetReactive(characterForm, {
    id: base.id || '',
    name: base.name || base.developer_data?.basic?.name || '',
    character_type: base.character_type || 'supporting',
    tags: base.tags || [],
    world_entry_ids: base.world_entry_ids || [],
  })
  const developer = char?.developer_data || defaultCharacterDeveloper(char?.name || '')
  characterDeveloperJson.value = JSON.stringify(developer, null, 2)
  resetCharacterVisibilityConfig(char?.field_visibility || {}, developer)
  characterEditTab.value = 'developer'
  characterDialog.value = true
}

async function saveCharacter() {
  const developer = parseJson(characterDeveloperJson.value, {})
  const data = {
    ...characterForm,
    developer_data: developer,
    field_visibility: cloneJson(characterVisibilityConfig),
  }
  if (characterForm.id) selectedCharacter.value = await request('PUT', `/projects/${activeProjectId.value}/characters/${characterForm.id}`, data)
  else selectedCharacter.value = await request('POST', `/projects/${activeProjectId.value}/characters`, data)
  characterDialog.value = false
  await loadCharacters()
  toast('角色已保存')
}

async function deleteCharacter() {
  if (!selectedCharacter.value) return
  await request('DELETE', `/projects/${activeProjectId.value}/characters/${selectedCharacter.value.id}`)
  selectedCharacter.value = null
  await loadCharacters()
  toast('角色已删除')
}

function openCharacterAiDialog() {
  resetAiDialog({ target: 'character', title: 'AI 生成角色', min_length: 0, max_length: 0 })
}

function openCharacterRelationDialog() {
  Object.assign(characterRelationForm, { target_id: '', relation_type: 'friend', direction: 'bidirectional', numeric_value: 0, description: '' })
  characterRelationDialog.value = true
}

async function saveCharacterRelation() {
  await request('POST', `/projects/${activeProjectId.value}/characters/relations`, { ...characterRelationForm, source_id: selectedCharacter.value.id })
  characterRelationDialog.value = false
  await selectCharacter(selectedCharacter.value)
  toast('人物关系已创建')
}

async function deleteCharacterRelation(id: string) {
  await request('DELETE', `/projects/${activeProjectId.value}/characters/relations/${id}`)
  await selectCharacter(selectedCharacter.value)
  toast('人物关系已删除')
}

async function exportCharacters() {
  const data = await request('GET', `/projects/${activeProjectId.value}/characters/export?format=markdown&ids=${selectedCharacter.value?.id || ''}`)
  downloadText(data.filename, data.content)
}

async function loadScripts() {
  scriptsTree.value = await request('GET', `/projects/${activeProjectId.value}/scripts/tree`)
  if (!worldEntries.value.length) await loadWorldEntries()
  if (!characters.value.length) await loadCharacters()
  if (selectedScript.value) {
    const found = flatScripts.value.find((item) => item.id === selectedScript.value.id)
    if (found) await selectScript(found)
    else {
      selectedScript.value = null
      scriptReferences.value = []
    }
  }
}

async function selectScript(node: any) {
  selectedScript.value = await request('GET', `/projects/${activeProjectId.value}/scripts/detail/${node.id}`)
  scriptReferences.value = selectedScript.value.references || []
}

function openScriptDialog(node?: any, parentId?: string) {
  resetReactive(scriptForm, node || { id: '', title: '', parent_id: parentId || null, node_type: 'scene', content: '', summary: '', status: 'draft', tags: [], story_time: '', story_location: '', importance: 3 })
  scriptDialog.value = true
}

async function saveScript() {
  const data = { ...scriptForm }
  if (scriptForm.id) selectedScript.value = await request('PUT', `/projects/${activeProjectId.value}/scripts/${scriptForm.id}`, data)
  else selectedScript.value = await request('POST', `/projects/${activeProjectId.value}/scripts`, data)
  scriptDialog.value = false
  await loadScripts()
  toast('剧本节点已保存')
}

async function deleteScript() {
  if (!selectedScript.value) return
  await request('DELETE', `/projects/${activeProjectId.value}/scripts/${selectedScript.value.id}`)
  selectedScript.value = null
  await loadScripts()
  toast('剧本节点已删除')
}

function openScriptAiDialog() {
  resetAiDialog({ target: 'script', title: 'AI 生成剧本内容', min_length: 500, max_length: 1600 })
}

function openScriptReferenceDialog() {
  Object.assign(scriptReferenceForm, { ref_type: 'worldbook', ref_id: '', description: '' })
  scriptReferenceDialog.value = true
}

async function saveScriptReference() {
  await request('POST', `/projects/${activeProjectId.value}/scripts/${selectedScript.value.id}/references`, scriptReferenceForm)
  scriptReferenceDialog.value = false
  await selectScript(selectedScript.value)
  toast('引用已添加')
}

async function deleteScriptReference(id: string) {
  await request('DELETE', `/projects/${activeProjectId.value}/scripts/references/${id}`)
  await selectScript(selectedScript.value)
}

async function exportScripts() {
  const data = await request('GET', `/projects/${activeProjectId.value}/scripts/export?format=markdown`)
  downloadText(data.filename, data.content)
}

async function loadPresets() {
  const query = new URLSearchParams()
  if (presetFilters.q) query.set('q', presetFilters.q)
  presets.value = await request('GET', `/projects/${activeProjectId.value}/presets?${query}`)
  if (selectedPreset.value) selectedPreset.value = presets.value.find((item) => item.id === selectedPreset.value.id) || null
}

function selectPreset(preset: any) {
  selectedPreset.value = preset
}

function openPresetDialog(preset?: any) {
  resetReactive(presetForm, preset || { id: '', name: '', category: 'general', description: '', tags: [] })
  presetDimensionsJson.value = JSON.stringify(preset?.dimensions || [], null, 2)
  presetBlocksJson.value = JSON.stringify(preset?.custom_blocks || [], null, 2)
  presetScenesJson.value = JSON.stringify(preset?.application_scenes || [{ sceneType: 'worldbook', enabled: true, adjustments: '' }, { sceneType: 'character', enabled: true, adjustments: '' }, { sceneType: 'script', enabled: true, adjustments: '' }], null, 2)
  presetDialog.value = true
}

async function savePreset() {
  const data = {
    ...presetForm,
    dimensions: parseJson(presetDimensionsJson.value, []),
    custom_blocks: parseJson(presetBlocksJson.value, []),
    application_scenes: parseJson(presetScenesJson.value, []),
    recompile: true,
  }
  if (presetForm.id) selectedPreset.value = await request('PUT', `/projects/${activeProjectId.value}/presets/${presetForm.id}`, data)
  else selectedPreset.value = await request('POST', `/projects/${activeProjectId.value}/presets`, data)
  presetDialog.value = false
  await loadPresets()
  toast('预设已保存')
}

async function deletePreset() {
  await request('DELETE', `/projects/${activeProjectId.value}/presets/${selectedPreset.value.id}`)
  selectedPreset.value = null
  await loadPresets()
  toast('预设已删除')
}

function openPresetAiDialog() {
  resetAiDialog({ target: 'preset', title: 'AI 生成预设', min_length: 0, max_length: 0 })
}

async function organizePreset() {
  const data = await request('POST', `/projects/${activeProjectId.value}/presets/${selectedPreset.value.id}/organize`)
  toast(`整理完成：${data.issues?.length || 0} 条建议`)
}

async function copyPresetPrompt() {
  await navigator.clipboard.writeText(selectedPreset.value.compiled_prompt || '')
  toast('提示词已复制')
}

async function exportPresets() {
  const data = await request('GET', `/projects/${activeProjectId.value}/presets/export?format=markdown`)
  downloadText(data.filename, data.content)
}

function openPresetApplyDialog() {
  if (!selectedPreset.value) return
  resetReactive(presetApplyForm, { scene_type: 'worldbook', scene_requirements: '' })
  presetApplyResult.value = ''
  presetApplyDialog.value = true
}

async function applyPresetToScene() {
  if (!selectedPreset.value) return
  const data = await request('POST', `/projects/${activeProjectId.value}/presets/apply`, {
    preset_id: selectedPreset.value.id,
    scene_type: presetApplyForm.scene_type,
    scene_requirements: presetApplyForm.scene_requirements,
  })
  presetApplyResult.value = data.prompt || ''
}

async function copyPresetApplyPrompt() {
  await navigator.clipboard.writeText(presetApplyResult.value || '')
  toast('应用结果已复制')
}

function openPresetCombineDialog() {
  if (!selectedPreset.value) return
  const firstOverride = presetCombineOverrideOptions.value[0]
  resetReactive(presetCombineForm, {
    override_id: firstOverride?.id || '',
    name: `组合：${selectedPreset.value.name}${firstOverride ? ` + ${firstOverride.name}` : ''}`,
    category: '组合',
    description: `由「${selectedPreset.value.name}」作为基础预设组合生成。`,
  })
  presetCombineResult.value = null
  presetCombineDialog.value = true
}

async function combinePreset() {
  if (!selectedPreset.value || !presetCombineForm.override_id) return
  presetCombineResult.value = await request('POST', `/projects/${activeProjectId.value}/presets/combine`, {
    base_id: selectedPreset.value.id,
    override_id: presetCombineForm.override_id,
  })
}

async function saveCombinedPreset() {
  if (!presetCombineResult.value) return
  selectedPreset.value = await request('POST', `/projects/${activeProjectId.value}/presets`, {
    name: presetCombineForm.name || '组合预设',
    category: presetCombineForm.category || '组合',
    description: presetCombineForm.description || '',
    tags: ['组合'],
    dimensions: presetCombineResult.value.dimensions || [],
    custom_blocks: presetCombineResult.value.custom_blocks || [],
    application_scenes: presetCombineResult.value.application_scenes || [],
    compiled_prompt: presetCombineResult.value.compiled_prompt || '',
  })
  presetCombineDialog.value = false
  await loadPresets()
  toast('组合预设已保存')
}

function openIterateDialog(type: 'worldbook' | 'character' | 'script' | 'preset') {
  const names: any = { worldbook: '世界书条目', character: '人物卡', script: '剧本节点', preset: '预设' }
  resetAiDialog({
    target: `${type}-iterate`,
    title: `AI 迭代${names[type]}`,
    prompt: '',
    result: '',
    section: '',
    field: '',
    apply: type === 'character',
    min_length: 0,
    max_length: 0,
  })
}

async function runQualityCheck(type: 'worldbook' | 'character' | 'script') {
  let endpoint = ''
  let payload: any = {}
  if (type === 'worldbook') {
    endpoint = `/projects/${activeProjectId.value}/worldbook/ai/check`
    payload = { title: selectedWorldEntry.value.title, content: selectedWorldEntry.value.content }
  }
  if (type === 'character') {
    endpoint = `/projects/${activeProjectId.value}/characters/ai/check`
    payload = selectedCharacter.value
  }
  if (type === 'script') {
    endpoint = `/projects/${activeProjectId.value}/scripts/ai/check`
    payload = selectedScript.value
  }
  const data = await request('POST', endpoint, payload)
  Object.assign(aiDialog, {
    open: true,
    target: 'check',
    title: 'AI 质量检查结果',
    prompt: '',
    result: JSON.stringify(data, null, 2),
    min_length: 0,
    max_length: 0,
    temperature: currentProjectAiTemperature(),
  })
}

async function openVersions(entityType: string, entityId: string) {
  versionContext.entityType = entityType
  versionContext.entityId = entityId
  versionDiff.value = null
  versionRows.value = await request('GET', `/projects/${activeProjectId.value}/versions/${entityType}/${entityId}`)
  versionDialog.value = true
}

async function loadVersionDiff(versionId: string) {
  versionDiff.value = await request('GET', `/projects/${activeProjectId.value}/version-diff/${versionId}`)
}

async function restoreVersion(versionId: string) {
  const restored = await request('POST', `/projects/${activeProjectId.value}/versions/${versionId}/restore`)
  versionDialog.value = false
  await refreshRestoredEntity(restored)
  toast(restored?.restored_version ? `已恢复到版本 ${restored.restored_version}` : '版本已恢复')
}

async function refreshRestoredEntity(restored: any) {
  const entityType = restored?.entity_type || versionContext.entityType
  const entityId = restored?.entity_id || versionContext.entityId
  if (!entityId) {
    await loadCurrentModule()
    return
  }
  if (entityType === 'worldbook_entry') {
    await loadWorldbook()
    await selectWorldEntry({ id: entityId })
    return
  }
  if (entityType === 'character') {
    await loadCharacters()
    await selectCharacter({ id: entityId })
    return
  }
  if (entityType === 'script') {
    await loadScripts()
    await selectScript({ id: entityId })
    return
  }
  if (entityType === 'preset') {
    await loadPresets()
    selectedPreset.value = presets.value.find((item) => item.id === entityId) || restored?.entity || null
    return
  }
  await loadCurrentModule()
}

function iterationTargetLabel() {
  return [aiDialog.section, aiDialog.field].filter(Boolean).join(' / ') || '全文'
}

function iterationApplyMetadata(data: any, result: any) {
  return {
    prompt: data.ai_prompt || '',
    result,
    section: aiDialog.section || '',
    field: aiDialog.field || '',
    instruction: aiDialog.prompt || '',
    request: {
      section: aiDialog.section || '',
      field: aiDialog.field || '',
      instruction: aiDialog.prompt || '',
      temperature: aiDialog.temperature,
    },
    process_log: data.generation_log || [],
  }
}

function withIterationAudit(payload: any, data: any, result: any) {
  return {
    ...payload,
    summary: `AI迭代 ${iterationTargetLabel()}`,
    ai_apply: iterationApplyMetadata(data, result),
  }
}

async function runAiDialog() {
  if (aiDialog.running) return
  const processMessages = ['准备上下文', '整理提示词', '发送到 AI 模型', '等待模型推理', '解析生成结果', '写入可编辑结果']
  startAiProgress(processMessages)
  const controller = new AbortController()
  aiAbortController = controller
  const requestOptions = { signal: controller.signal }
  aiDialog.pendingApplyTarget = ''
  aiDialog.pendingApplyPayload = null
  aiDialog.pendingApplyMeta = null
  try {
    if (aiDialog.target === 'worldbook') {
      const data = await request('POST', `/projects/${activeProjectId.value}/worldbook/ai/generate`, {
        category_id: worldFilters.category_id || categories.value[0]?.id,
        title: selectedWorldEntry.value?.title,
        prompt: aiDialog.prompt,
        min_length: aiDialog.min_length,
        max_length: aiDialog.max_length,
        temperature: aiDialog.temperature,
      }, requestOptions)
      aiDialog.result = data.content
      aiDialog.pendingApplyPayload = {
        title: data.title || selectedWorldEntry.value?.title || 'AI生成条目',
        category_id: data.category_id || worldFilters.category_id || categories.value[0]?.id,
        content: data.content || '',
        structured_data: data.structured_data || {},
        importance: 3,
        visibility: 'public',
        status: 'draft',
        tags: ['AI'],
        ai_generated: true,
        ai_prompt: data.ai_prompt || '',
        ai_metadata: data.ai_metadata || {},
      }
      stopAiProgress(true, data.generation_log)
    }
    if (aiDialog.target === 'character') {
      const data = await request('POST', `/projects/${activeProjectId.value}/characters/ai/generate`, { concept: aiDialog.prompt, temperature: aiDialog.temperature }, requestOptions)
      const payload = buildCharacterCreatePayload(data)
      aiDialog.result = JSON.stringify(payload, null, 2)
      aiDialog.pendingApplyPayload = payload
      aiDialog.contractIssues = data.contract_issues || []
      stopAiProgress(true, data.generation_log)
    }
    if (aiDialog.target === 'script') {
      const data = await request('POST', `/projects/${activeProjectId.value}/scripts/ai/generate`, { prompt: aiDialog.prompt, temperature: aiDialog.temperature }, requestOptions)
      aiDialog.result = data.content
      stopAiProgress(true, data.generation_log)
    }
    if (aiDialog.target === 'preset') {
      const data = await request('POST', `/projects/${activeProjectId.value}/presets/ai/generate`, { description: aiDialog.prompt, temperature: aiDialog.temperature }, requestOptions)
      aiDialog.result = JSON.stringify(data, null, 2)
      stopAiProgress(true, data.generation_log)
    }
    if (aiDialog.target === 'worldbook-iterate') {
      const data = await request('POST', `/projects/${activeProjectId.value}/worldbook/entries/${selectedWorldEntry.value.id}/ai/iterate`, {
        instruction: aiDialog.prompt,
        section: aiDialog.section,
        apply: false,
        temperature: aiDialog.temperature,
      }, requestOptions)
      aiDialog.result = data.content || data.generated
      aiDialog.pendingApplyTarget = aiDialog.target
      aiDialog.pendingApplyPayload = withIterationAudit({ content: data.content, ai_prompt: data.ai_prompt }, data, data.content)
      aiDialog.pendingApplyMeta = aiDialog.pendingApplyPayload.ai_apply
      stopAiProgress(true, data.generation_log)
    }
    if (aiDialog.target === 'character-iterate') {
      const applyNow = aiDialog.apply !== false
      const data = await request('POST', `/projects/${activeProjectId.value}/characters/${selectedCharacter.value.id}/ai/iterate`, {
        instruction: aiDialog.prompt,
        section: aiDialog.section,
        field: aiDialog.field,
        apply: applyNow,
        temperature: aiDialog.temperature,
      }, requestOptions)
      if (applyNow && data.character) {
        const character = data.character
        aiDialog.result = JSON.stringify({ developer_data: character.developer_data, player_data: character.player_data, field_visibility: character.field_visibility }, null, 2)
        stopAiProgress(true, data.generation_log)
        await loadCharacters()
        await selectCharacter({ id: character.id })
        await loadAiLogs()
        aiDialog.open = false
        toast('人物卡已迭代并保存')
        return
      }
      aiDialog.result = JSON.stringify({ developer_data: data.developer_data, player_data: data.player_data, field_visibility: data.field_visibility }, null, 2)
      aiDialog.pendingApplyTarget = aiDialog.target
      aiDialog.pendingApplyPayload = withIterationAudit({ developer_data: data.developer_data, player_data: data.player_data, field_visibility: data.field_visibility || selectedCharacter.value.field_visibility }, data, data.developer_data)
      aiDialog.pendingApplyMeta = aiDialog.pendingApplyPayload.ai_apply
      stopAiProgress(true, data.generation_log)
    }
    if (aiDialog.target === 'script-iterate') {
      const data = await request('POST', `/projects/${activeProjectId.value}/scripts/${selectedScript.value.id}/ai/iterate`, {
        instruction: aiDialog.prompt,
        section: aiDialog.section,
        apply: false,
        temperature: aiDialog.temperature,
      }, requestOptions)
      aiDialog.result = data.content || data.generated
      aiDialog.pendingApplyTarget = aiDialog.target
      aiDialog.pendingApplyPayload = withIterationAudit({ content: data.content, ai_prompt: data.ai_prompt }, data, data.content)
      aiDialog.pendingApplyMeta = aiDialog.pendingApplyPayload.ai_apply
      stopAiProgress(true, data.generation_log)
    }
    if (aiDialog.target === 'preset-iterate') {
      const data = await request('POST', `/projects/${activeProjectId.value}/presets/${selectedPreset.value.id}/ai/iterate`, {
        instruction: aiDialog.prompt,
        section: aiDialog.section,
        apply: false,
        temperature: aiDialog.temperature,
      }, requestOptions)
      aiDialog.result = JSON.stringify(data.generated || {}, null, 2)
      aiDialog.pendingApplyTarget = aiDialog.target
      aiDialog.pendingApplyPayload = withIterationAudit({ ...(data.generated || {}), recompile: true }, data, data.generated || {})
      aiDialog.pendingApplyMeta = aiDialog.pendingApplyPayload.ai_apply
      stopAiProgress(true, data.generation_log)
    }
  } catch (error: any) {
    stopAiProgress(false)
    aiDialog.running = false
    if (error?.status === 499) {
      aiDialog.activeMessage = '已取消'
      toast('AI 操作已取消', 'warning')
    } else {
      toast(error.message || 'AI 操作失败', 'error')
    }
  } finally {
    if (aiAbortController === controller) aiAbortController = null
  }
}

async function applyIterationResult() {
  let payload = aiDialog.pendingApplyPayload
  if (!payload || !aiDialog.pendingApplyTarget) return
  if (aiDialog.pendingApplyTarget === 'worldbook-iterate' && selectedWorldEntry.value) {
    payload = { ...payload, content: aiDialog.result }
    selectedWorldEntry.value = await request('PUT', `/projects/${activeProjectId.value}/worldbook/entries/${selectedWorldEntry.value.id}`, payload)
    await loadWorldbook()
  }
  if (aiDialog.pendingApplyTarget === 'character-iterate' && selectedCharacter.value) {
    const characterId = selectedCharacter.value.id
    const edited = characterPayloadFromAiResult(aiDialog.result)
    const source = edited?.developer_data ? edited : payload
    if (!source?.developer_data) {
      toast('人物卡结果不是有效 JSON，无法应用', 'error')
      return
    }
    payload = {
      ...payload,
      developer_data: source.developer_data,
      player_data: source.player_data || payload.player_data,
      field_visibility: source.field_visibility || payload.field_visibility,
    }
    await request('PUT', `/projects/${activeProjectId.value}/characters/${characterId}`, payload)
    await loadCharacters()
    await selectCharacter({ id: characterId })
  }
  if (aiDialog.pendingApplyTarget === 'script-iterate' && selectedScript.value) {
    const scriptId = selectedScript.value.id
    payload = { ...payload, content: aiDialog.result }
    selectedScript.value = await request('PUT', `/projects/${activeProjectId.value}/scripts/${scriptId}`, payload)
    await loadScripts()
    await selectScript({ id: scriptId })
  }
  if (aiDialog.pendingApplyTarget === 'preset-iterate' && selectedPreset.value) {
    selectedPreset.value = await request('PUT', `/projects/${activeProjectId.value}/presets/${selectedPreset.value.id}`, payload)
    await loadPresets()
  }
  aiDialog.pendingApplyTarget = ''
  aiDialog.pendingApplyPayload = null
  aiDialog.pendingApplyMeta = null
  aiDialog.open = false
  toast('迭代结果已应用')
}

async function acceptAiResult() {
  if (aiDialog.target === 'worldbook') {
    const payload = {
      ...(aiDialog.pendingApplyPayload || {}),
      title: aiDialog.pendingApplyPayload?.title || selectedWorldEntry.value?.title || 'AI生成条目',
      category_id: aiDialog.pendingApplyPayload?.category_id || worldFilters.category_id || categories.value[0]?.id,
      content: aiDialog.result,
      structured_data: aiDialog.pendingApplyPayload?.structured_data || {},
      importance: aiDialog.pendingApplyPayload?.importance || 3,
      visibility: aiDialog.pendingApplyPayload?.visibility || 'public',
      status: aiDialog.pendingApplyPayload?.status || 'draft',
      tags: aiDialog.pendingApplyPayload?.tags || ['AI'],
    }
    openWorldEntryDialog(payload)
  }
  if (aiDialog.target === 'character') {
    const data = characterPayloadFromAiResult(aiDialog.result)
    if (!data?.developer_data) {
      toast('人物卡结果不是有效 JSON，无法创建', 'error')
      return
    }
    const created = await request('POST', `/projects/${activeProjectId.value}/characters`, {
      ...data,
      name: data.name || data.developer_data?.basic?.name || 'AI角色',
      character_type: data.character_type || 'supporting',
      status: data.status || 'draft',
      tags: data.tags || ['AI'],
      ai_generated: true,
      generation_history: [
        {
          time: new Date().toISOString(),
          prompt: aiDialog.prompt,
          process_log: cloneJson(aiDialog.progress),
        },
      ],
    })
    aiDialog.open = false
    selectedCharacter.value = created
    activeModule.value = 'characters'
    await loadCharacters()
    await selectCharacter(created)
    toast('AI 角色已创建')
    return
  }
  if (aiDialog.target === 'script') {
    openScriptDialog({ title: 'AI剧本节点', node_type: 'scene', content: aiDialog.result, summary: aiDialog.result.slice(0, 120), status: 'draft', tags: ['AI'] })
  }
  if (aiDialog.target === 'preset') {
    const data = parseJson(aiDialog.result, {})
    openPresetDialog({ name: data.name || 'AI预设', category: data.category || 'general', description: data.description || '', tags: data.tags || [], dimensions: data.dimensions || [], custom_blocks: data.custom_blocks || [], application_scenes: data.application_scenes || [] })
  }
  if (aiDialog.target === 'check') return
  if (isIterating.value) return
  aiDialog.open = false
}

function brief(text: string, size = 80) {
  const clean = (text || '').replace(/\s+/g, ' ').trim()
  return clean ? clean.slice(0, size) + (clean.length > size ? '...' : '') : '暂无内容'
}

function categoryName(id: string) {
  return categories.value.find((item) => item.id === id)?.name || '未分类'
}

function statusText(status: string) {
  const map: any = { draft: '草稿', complete: '完成', archived: '归档', active: '活跃' }
  return map[status] || status
}

function statusColor(status: string) {
  const map: any = { draft: 'grey', complete: 'success', archived: 'warning', active: 'primary' }
  return map[status] || 'grey'
}

function aiTargetText(type: string) {
  const map: any = { worldbook: '世界书', character: '人物卡', script: '剧本', preset: '预设' }
  return map[type] || type || '未知'
}

function aiOperationText(operation: string) {
  const map: any = { generate: '生成', iterate: '迭代', apply: '应用', check: '检查', organize: '整理', classify: '分类', recommend: '推荐' }
  return map[operation] || operation || '未知'
}

function aiStatusText(status: string) {
  const map: any = { success: '成功', failed: '失败', canceled: '已取消' }
  return map[status] || status || '未知'
}

function aiLogPersistText(log: any) {
  if (!log || log.status === 'failed') return '未保存'
  if (log.operation === 'apply') return '已保存'
  if (log.applied_preview) return '已应用'
  if (aiLogCanApply(log)) return '待应用'
  if (log.request?.apply === false) return aiLogApplyBlockedReason(log) ? '不可应用' : '仅预览'
  if (log.request?.apply === true) return '已保存'
  return log.operation === 'iterate' ? '仅记录' : '无写入'
}

function aiLogPersistColor(log: any) {
  const text = aiLogPersistText(log)
  if (['已保存', '已应用'].includes(text)) return 'success'
  if (['待应用', '仅预览'].includes(text)) return 'warning'
  if (text === '不可应用') return 'error'
  return 'grey'
}

function aiLogCanApply(log: any) {
  if (!aiLogIsPreviewApplyCandidate(log)) return false
  if (log.target_type === 'character') return Boolean(characterPayloadFromAiLog(log)?.developer_data)
  if (['worldbook', 'script'].includes(log.target_type)) return textResultFromAiLog(log).ok
  if (log.target_type === 'preset') return objectResultFromAiLog(log).ok
  return false
}

function aiLogApplyBlockedReason(log: any) {
  if (!aiLogIsPreviewApplyCandidate(log) || aiLogCanApply(log)) return ''
  const resolved = resolveAiLogResult(log)
  if (resolved.ok === false) return resolved.reason
  if (log.target_type === 'character') return '这条历史结果不是完整人物卡结构，无法安全写回人物卡。'
  if (['worldbook', 'script'].includes(log.target_type)) {
    const text = textResultFromAiLog(log)
    return text.ok === false ? text.reason : ''
  }
  if (log.target_type === 'preset') {
    const object = objectResultFromAiLog(log)
    return object.ok === false ? object.reason : ''
  }
  return '这条 AI 历史暂不支持应用。'
}

function characterPayloadFromAiLog(log: any) {
  const resolved = objectResultFromAiLog(log)
  if (resolved.ok) return characterPayloadFromValue(resolved.result)
  const text = textResultFromAiLog(log)
  return text.ok ? characterPayloadFromAiResult(text.result) : null
}

async function applyAiLog(log: any) {
  if (!aiLogCanApply(log)) {
    toast('这条 AI 历史没有完整可应用结果；请重新执行一次迭代。', 'error')
    return
  }
  try {
    if (log.target_type === 'worldbook') await applyWorldbookAiLog(log)
    if (log.target_type === 'character') await applyCharacterAiLog(log)
    if (log.target_type === 'script') await applyScriptAiLog(log)
    if (log.target_type === 'preset') await applyPresetAiLog(log)
    await loadAiLogs()
    await loadProjects()
    if (activeProjectId.value) await loadProjectOverview()
    aiLogDialog.value = false
    toast('AI 历史已应用')
  } catch (error: any) {
    toast(error?.message || 'AI 历史应用失败', 'error')
  }
}

async function applyWorldbookAiLog(log: any) {
  const applied = await applyAiLogOnBackend(log)
  const entryId = applied?.entity?.id || log.target_id
  activeModule.value = 'worldbook'
  await loadWorldbook()
  await selectWorldEntry({ id: entryId })
}

async function applyCharacterAiLog(log: any) {
  const applied = await applyAiLogOnBackend(log)
  const characterId = applied?.entity?.id || log.target_id
  activeModule.value = 'characters'
  await loadCharacters()
  await selectCharacter({ id: characterId })
}

async function applyScriptAiLog(log: any) {
  const applied = await applyAiLogOnBackend(log)
  const scriptId = applied?.entity?.id || log.target_id
  activeModule.value = 'scripts'
  await loadScripts()
  await selectScript({ id: scriptId })
}

async function applyPresetAiLog(log: any) {
  const applied = await applyAiLogOnBackend(log)
  const presetId = applied?.entity?.id || log.target_id
  selectedPreset.value = applied?.entity || selectedPreset.value
  activeModule.value = 'presets'
  await loadPresets()
  selectedPreset.value = presets.value.find((item) => item.id === presetId) || selectedPreset.value
}

async function applyAiLogOnBackend(log: any) {
  return await request('POST', `/projects/${activeProjectId.value}/ai/logs/${log.id}/apply`)
}

function formatDateTime(value: string) {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN')
}

function versionDiffTypeText(type: string) {
  const map: any = { added: '新增', removed: '删除', changed: '变更' }
  return map[type] || type
}

function formatDiffValue(value: any) {
  if (value === null || value === undefined || value === '') return '暂无'
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}

function versionDiffValueIsMarkdown(diff: any, side: 'before' | 'after') {
  return shouldRenderMarkdownValue(diff?.path || '', diff?.[side])
}

function relationColor(type: string) {
  const map: any = { source: '#1a73e8', influence: '#188038', related: '#5f6368', oppose: '#d93025' }
  return map[type] || '#5f6368'
}

function graphPoint(id: string) {
  const index = Math.max(0, worldGraph.nodes.findIndex((item: any) => item.id === id))
  const count = Math.max(1, worldGraph.nodes.length)
  const angle = (index / count) * Math.PI * 2 - Math.PI / 2
  return { x: 380 + Math.cos(angle) * 230, y: 170 + Math.sin(angle) * 110 }
}

function charSummary(char: any) {
  return char.developer_data?.basic?.summary || char.developer_data?.knowledge?.background || '暂无简介'
}

function characterSection(tab: string) {
  const source = characterViewMode.value === 'player' ? selectedCharacter.value?.player_data : selectedCharacter.value?.developer_data
  return source?.[tab]
}

function aiDialogCharacterSection(tab: string) {
  return aiDialogCharacterPreview.value?.developer_data?.[tab]
}

function selectedAiLogCharacterSection(tab: string) {
  return selectedAiLogCharacterPreview.value?.developer_data?.[tab]
}

function scriptIcon(type: string) {
  const map: any = { outline: 'mdi-file-document-outline', volume: 'mdi-book-open-variant', part: 'mdi-file-tree-outline', chapter: 'mdi-book-open-page-variant', scene: 'mdi-movie-open-outline', fragment: 'mdi-text-short' }
  return map[type] || 'mdi-file-outline'
}

function scriptTypeName(type: string) {
  return scriptTypes.find((item) => item.value === type)?.title || type
}

function downloadText(filename: string, content: string) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
</script>
