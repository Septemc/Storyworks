import { describe, expect, it } from 'vitest'
import {
  aiLogApplyAudit,
  aiLogApplyLabel,
  aiLogApplySummary,
  aiLogIsPreviewApplyCandidate,
  aiLogResultDisplayMode,
  aiLogResultText,
  objectResultFromAiLog,
  resolveAiLogResult,
  textResultFromAiLog,
} from './aiLog'

describe('AI log apply helpers', () => {
  it('only treats successful preview iterations with a target as apply candidates', () => {
    expect(aiLogIsPreviewApplyCandidate({ status: 'success', operation: 'iterate', target_type: 'worldbook', target_id: 'world_1', request: { apply: false } })).toBe(true)
    expect(aiLogIsPreviewApplyCandidate({ status: 'success', operation: 'iterate', target_type: 'worldbook', target_id: 'world_1', request: { apply: false }, pending_apply: false })).toBe(false)
    expect(aiLogIsPreviewApplyCandidate({ status: 'success', operation: 'iterate', target_type: 'worldbook', target_id: 'world_1', request: {} })).toBe(true)
    expect(aiLogIsPreviewApplyCandidate({ status: 'success', operation: 'iterate', target_type: 'worldbook', target_id: 'world_1', request: { apply: true } })).toBe(false)
    expect(aiLogIsPreviewApplyCandidate({ status: 'failed', operation: 'iterate', target_type: 'worldbook', target_id: 'world_1', request: { apply: false } })).toBe(false)
    expect(aiLogIsPreviewApplyCandidate({ status: 'success', operation: 'generate', target_type: 'worldbook', request: { apply: false } })).toBe(false)
  })

  it('uses full response_data and refuses truncated legacy previews', () => {
    expect(resolveAiLogResult({ response_data: { content: '完整结果' }, response_preview: '截断预览' })).toEqual({ ok: true, result: { content: '完整结果' } })
    expect(resolveAiLogResult({ response_preview: '短旧预览' })).toEqual({ ok: true, result: '短旧预览' })
    expect(resolveAiLogResult({ response_preview: 'x'.repeat(1600) })).toEqual({ ok: false, reason: '历史结果只有截断预览，无法可靠应用' })
  })

  it('extracts text and object results for module-specific apply flows', () => {
    expect(textResultFromAiLog({ response_data: '新的 Markdown 正文' })).toEqual({ ok: true, result: '新的 Markdown 正文' })
    expect(textResultFromAiLog({ response_data: { content: '新的世界书正文' } })).toEqual({ ok: true, result: '新的世界书正文' })
    expect(textResultFromAiLog({ response_data: '   ' })).toEqual({ ok: false, reason: '日志结果为空，无法应用' })
    expect(objectResultFromAiLog({ response_data: { name: '预设', dimensions: [] } })).toEqual({ ok: true, result: { name: '预设', dimensions: [] } })
    expect(objectResultFromAiLog({ response_data: '文本' }).ok).toBe(false)
  })

  it('chooses readable display modes for AI log result previews', () => {
    expect(aiLogResultDisplayMode({ target_type: 'worldbook', response_data: { content: '## 定义\n正文' } })).toBe('markdown')
    expect(aiLogResultDisplayMode({ target_type: 'script', response_data: '## 场景目标\n正文' })).toBe('markdown')
    expect(aiLogResultDisplayMode({ target_type: 'character', response_data: { developer_data: { basic: { name: '林远' } } } })).toBe('character')
    expect(aiLogResultDisplayMode({ target_type: 'preset', response_data: { name: '预设', dimensions: [] } })).toBe('json')
    expect(aiLogResultText({ response_data: { name: '预设' } })).toContain('"name": "预设"')
  })

  it('builds user-facing labels and audit payloads', () => {
    const log = { target_type: 'script', section: '冲突推进', prompt: 'prompt', instruction: '补强', request: { apply: false }, process_log: [{ message: 'done' }] }

    expect(aiLogApplyLabel(log)).toBe('应用到剧本')
    expect(aiLogApplySummary(log)).toBe('AI历史应用 冲突推进')
    expect(aiLogApplyAudit(log, 'result')).toMatchObject({ prompt: 'prompt', result: 'result', section: '冲突推进', instruction: '补强' })
  })
})
