export const characterTabs = ['basic', 'knowledge', 'secrets', 'attributes', 'relations', 'inventory', 'skills', 'fortune', 'extras'] as const

export const characterTabLabels: Record<string, string> = {
  basic: '基础（BASIC）',
  knowledge: '信息（KNOWLEDGE）',
  secrets: '隐秘（SECRETS）',
  attributes: '属性（ATTRIBUTES）',
  relations: '关系（RELATIONS）',
  inventory: '物品（INVENTORY）',
  skills: '技能（SKILLS）',
  fortune: '命运（FORTUNE）',
  extras: '补充（EXTRAS）',
}

export const characterFieldLabels: Record<string, string> = {
  name: '姓名（name）',
  gender: '性别（gender）',
  age: '年龄（age）',
  identity: '身份（identity）',
  role: '叙事定位（role）',
  status: '当前状态（status）',
  summary: '摘要（summary）',
  appearance: '外观特征（appearance）',
  personality: '性格模式（personality）',
  background: '背景经历（background）',
  dailyLife: '日常处境（dailyLife）',
  motivation: '行动动机（motivation）',
  values: '价值观（values）',
  flaws: '弱点缺陷（flaws）',
  currentConflict: '当前冲突（currentConflict）',
  publicMask: '公开面具（publicMask）',
  privateTruth: '私下真相（privateTruth）',
  trauma: '创伤（trauma）',
  hiddenAgenda: '隐藏目标（hiddenAgenda）',
  weakness: '软肋（weakness）',
  revealTrigger: '揭露触发（revealTrigger）',
  physical: '身体/外在能力（physical）',
  mental: '心智/认知能力（mental）',
  social: '社会影响力（social）',
  resources: '资源筹码（resources）',
  limitations: '限制代价（limitations）',
  special: '特殊设定（special）',
  targetName: '目标角色（targetName）',
  relationType: '关系类型（relationType）',
  direction: '方向（direction）',
  intimacy: '亲近度（intimacy）',
  conflict: '关系冲突（conflict）',
  history: '关系历史（history）',
  leverage: '牵制筹码（leverage）',
  currentStatus: '当前关系状态（currentStatus）',
  events: '事件记录（events）',
  itemName: '物品名称（itemName）',
  type: '类型（type）',
  owner: '归属（owner）',
  function: '用途（function）',
  origin: '来源（origin）',
  storyUse: '剧情用途（storyUse）',
  category: '类别（category）',
  level: '等级/熟练度（level）',
  effect: '效果（effect）',
  cost: '代价（cost）',
  trainingSource: '来源训练（trainingSource）',
  desire: '核心渴望（desire）',
  fear: '核心恐惧（fear）',
  destinyTags: '命运标签（destinyTags）',
  turningPoints: '转折节点（turningPoints）',
  choices: '关键选择（choices）',
  causalHints: '因果钩子（causalHints）',
}

export const characterSectionVisibilityDefaults: Record<string, boolean> = {
  basic: true,
  knowledge: true,
  secrets: false,
  attributes: true,
  relations: true,
  inventory: true,
  skills: true,
  fortune: false,
  extras: true,
}

export function characterTabLabel(tab: string) {
  return characterTabLabels[tab] || `自定义分类（${tab}）`
}

export function characterFieldLabel(field: string) {
  return characterFieldLabels[field] || `自定义字段（${field}）`
}

export function defaultCharacterDeveloper(name = '') {
  return {
    basic: { name, gender: '', age: '', identity: '', role: '', status: '', summary: '' },
    knowledge: { appearance: '', personality: '', background: '', dailyLife: '', motivation: '', values: '', flaws: '', currentConflict: '' },
    secrets: { publicMask: '', privateTruth: '', trauma: '', hiddenAgenda: '', weakness: '', revealTrigger: '' },
    attributes: { physical: '', mental: '', social: '', resources: '', limitations: '', special: '' },
    relations: [],
    inventory: [],
    skills: [],
    fortune: { desire: '', fear: '', destinyTags: [], turningPoints: [], choices: [], causalHints: [] },
    extras: '',
  }
}

export function isPlainObject(value: any) {
  return value && typeof value === 'object' && !Array.isArray(value)
}

export function characterPayloadFromAiResult(text: string) {
  const parsed = parseJsonSilently(text, null)
  return characterPayloadFromValue(parsed)
}

export function characterPayloadFromValue(parsed: any) {
  if (!parsed || typeof parsed !== 'object') return null
  const hasSections = characterTabs.some((tab) => Object.prototype.hasOwnProperty.call(parsed, tab))
  const developer = parsed.developer_data || (hasSections ? parsed : null)
  if (!developer || typeof developer !== 'object') return null
  return {
    ...parsed,
    name: parsed.name || developer.basic?.name || '',
    character_type: parsed.character_type || 'supporting',
    developer_data: developer,
    player_data: parsed.player_data || {},
    field_visibility: parsed.field_visibility || {},
    tags: parsed.tags || ['AI'],
  }
}

export function buildCharacterCreatePayload(data: any) {
  return {
    name: data.name || data.developer_data?.basic?.name || 'AI角色',
    character_type: data.character_type || 'supporting',
    status: data.status || 'draft',
    developer_data: data.developer_data || defaultCharacterDeveloper(data.name || 'AI角色'),
    player_data: data.player_data || {},
    field_visibility: data.field_visibility || {},
    tags: data.tags || ['AI'],
    world_entry_ids: data.world_entry_ids || [],
  }
}

export function formatCharacterValue(value: any): string {
  if (value === null || value === undefined || value === '') return '暂无'
  if (Array.isArray(value)) return value.length ? value.map((item) => `- ${formatCharacterValue(item)}`).join('\n') : '暂无'
  if (typeof value === 'object') {
    return Object.entries(value)
      .map(([key, item]) => `${characterFieldLabel(String(key))}：${formatCharacterValue(item)}`)
      .join('\n')
  }
  return String(value)
}

function parseJsonSilently(text: string, fallback: any) {
  try {
    return JSON.parse(text || JSON.stringify(fallback))
  } catch {
    return fallback
  }
}
