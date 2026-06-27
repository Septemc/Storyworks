const LEGACY_PREVIEW_LIMIT = 1600
const APPLY_TARGETS = new Set(['worldbook', 'character', 'script', 'preset'])
const CHARACTER_SECTIONS = ['basic', 'knowledge', 'secrets', 'attributes', 'relations', 'inventory', 'skills', 'fortune', 'extras']

export type AiLogResultDisplayMode = 'markdown' | 'character' | 'json' | 'text' | 'empty'

export function aiLogIsPreviewApplyCandidate(log: any) {
  if (!log || log.status !== 'success') return false
  if (log.pending_apply === false) return false
  if (log.operation !== 'iterate' || !log.target_id) return false
  if (log.request?.apply === true) return false
  return APPLY_TARGETS.has(log.target_type)
}

export function resolveAiLogResult(log: any): { ok: true; result: any } | { ok: false; reason: string } {
  if (!log) return { ok: false, reason: '日志不存在' }
  if (log.response_data !== undefined && log.response_data !== null) {
    return { ok: true, result: log.response_data }
  }
  const preview = typeof log.response_preview === 'string' ? log.response_preview : ''
  if (!preview.trim()) return { ok: false, reason: '日志没有可应用结果' }
  if (preview.length >= LEGACY_PREVIEW_LIMIT) {
    return { ok: false, reason: '历史结果只有截断预览，无法可靠应用' }
  }
  return { ok: true, result: preview }
}

export function aiLogApplyLabel(log: any) {
  const map: Record<string, string> = {
    worldbook: '应用到世界书',
    character: '应用到人物卡',
    script: '应用到剧本',
    preset: '应用到预设',
  }
  return map[log?.target_type] || '应用结果'
}

export function aiLogApplySummary(log: any) {
  return `AI历史应用 ${[log?.section, log?.field].filter(Boolean).join(' / ') || '全部'}`
}

export function aiLogApplyAudit(log: any, result: any) {
  return {
    prompt: log?.prompt || '',
    result,
    section: log?.section || '',
    field: log?.field || '',
    instruction: log?.instruction || log?.request?.instruction || '',
    request: log?.request || {},
    process_log: log?.process_log || [],
  }
}

export function textResultFromAiLog(log: any) {
  const resolved = resolveAiLogResult(log)
  if (!resolved.ok) return resolved
  const result = resolved.result
  if (typeof result === 'string') {
    if (result.trim()) return { ok: true as const, result }
    return { ok: false as const, reason: '日志结果为空，无法应用' }
  }
  if (result && typeof result === 'object') {
    const content = result.content ?? result.generated ?? result.text ?? ''
    if (typeof content === 'string' && content.trim()) return { ok: true as const, result: content }
  }
  return { ok: false as const, reason: '日志结果不是可保存文本' }
}

export function objectResultFromAiLog(log: any) {
  const resolved = resolveAiLogResult(log)
  if (!resolved.ok) return resolved
  if (resolved.result && typeof resolved.result === 'object' && !Array.isArray(resolved.result)) {
    return { ok: true as const, result: resolved.result }
  }
  return { ok: false as const, reason: '日志结果不是可保存结构' }
}

export function aiLogResultText(log: any) {
  const resolved = resolveAiLogResult(log)
  if (resolved.ok === true) return stringifyAiLogResult(resolved.result)
  return typeof log?.response_preview === 'string' && log.response_preview ? log.response_preview : resolved.reason
}

export function aiLogResultDisplayMode(log: any): AiLogResultDisplayMode {
  const text = textResultFromAiLog(log)
  const object = objectResultFromAiLog(log)
  if (['worldbook', 'script'].includes(log?.target_type) && text.ok) return 'markdown'
  if (log?.target_type === 'character' && object.ok && isCharacterPayload(object.result)) return 'character'
  if (object.ok) return 'json'
  if (text.ok) return 'text'
  return 'empty'
}

function stringifyAiLogResult(value: any) {
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value ?? {}, null, 2)
  } catch {
    return String(value ?? '')
  }
}

function isCharacterPayload(value: any) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false
  const source = value.character && typeof value.character === 'object' ? value.character : value
  const developer = source.developer_data || source
  return Boolean(developer && typeof developer === 'object' && CHARACTER_SECTIONS.some((section) => Object.prototype.hasOwnProperty.call(developer, section)))
}
