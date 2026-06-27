import { describe, expect, it } from 'vitest'
import {
  buildCharacterCreatePayload,
  characterFieldLabel,
  characterPayloadFromAiResult,
  characterPayloadFromValue,
  characterTabLabel,
  characterTabs,
  defaultCharacterDeveloper,
  formatCharacterValue,
} from './character'

describe('character contract helpers', () => {
  it('keeps the nine universal sections and Chinese labels with English keys', () => {
    expect(characterTabs).toEqual(['basic', 'knowledge', 'secrets', 'attributes', 'relations', 'inventory', 'skills', 'fortune', 'extras'])
    expect(characterTabLabel('basic')).toBe('基础（BASIC）')
    expect(characterTabLabel('extras')).toBe('补充（EXTRAS）')
    expect(characterFieldLabel('name')).toBe('姓名（name）')
    expect(characterFieldLabel('gender')).toBe('性别（gender）')
    expect(characterFieldLabel('unknownPower')).toBe('自定义字段（unknownPower）')
  })

  it('creates a complete default developer schema including gender', () => {
    const developer = defaultCharacterDeveloper('沈慕瑶')

    expect(Object.keys(developer)).toEqual([...characterTabs])
    expect(developer.basic).toMatchObject({ name: '沈慕瑶', gender: '' })
    expect(developer.fortune).toMatchObject({ destinyTags: [], turningPoints: [], choices: [], causalHints: [] })
    expect(developer.extras).toBe('')
  })

  it('parses wrapped and direct AI character payloads', () => {
    const direct = characterPayloadFromAiResult(
      JSON.stringify({
        basic: { name: '林远', gender: '男', summary: '剑骨少年' },
        knowledge: {},
        secrets: {},
        attributes: {},
        relations: [],
        inventory: [],
        skills: [],
        fortune: {},
        extras: '补充',
      }),
    )

    expect(direct?.name).toBe('林远')
    expect(direct?.character_type).toBe('supporting')
    expect(direct?.developer_data.basic.gender).toBe('男')

    const wrapped = characterPayloadFromValue({
      character_type: 'protagonist',
      developer_data: { basic: { name: '许清禾', gender: '女' } },
      field_visibility: { basic: { gender: { visible: true } } },
      tags: ['调查'],
    })

    expect(wrapped?.name).toBe('许清禾')
    expect(wrapped?.character_type).toBe('protagonist')
    expect(wrapped?.tags).toEqual(['调查'])
    expect(wrapped?.field_visibility.basic.gender.visible).toBe(true)
  })

  it('builds create payloads and renders nested values with field labels', () => {
    const payload = buildCharacterCreatePayload({ developer_data: { basic: { name: '伊芙-7', gender: '女' } } })

    expect(payload.name).toBe('伊芙-7')
    expect(payload.status).toBe('draft')
    expect(payload.tags).toEqual(['AI'])
    expect(formatCharacterValue({ name: '伊芙-7', gender: '女' })).toContain('姓名（name）：伊芙-7')
    expect(formatCharacterValue({ name: '伊芙-7', gender: '女' })).toContain('性别（gender）：女')
  })
})
