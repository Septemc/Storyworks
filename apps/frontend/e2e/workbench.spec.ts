import { expect, test, type Page } from '@playwright/test'
import { readFile } from 'node:fs/promises'

function listItemTitle(page: Page, text: string) {
  const escaped = text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return page.locator('.v-list-item-title').filter({ hasText: new RegExp(`^${escaped}$`) }).first()
}

test('workbench renders core content contracts', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (error) => pageErrors.push(error.message))

  await page.goto('/')
  await expect(page.getByRole('main').getByText('项目总览', { exact: true })).toBeVisible()
  await expect(page.getByText('修仙背景-demo', { exact: true }).first()).toBeVisible()
  await expect(page.getByText('都市背景-demo', { exact: true }).first()).toBeVisible()
  await expect(page.getByText('科幻背景-demo', { exact: true }).first()).toBeVisible()
  await page.locator('.v-sheet').filter({ hasText: '修仙背景-demo' }).first().click()
  await expect(page.getByText('最近更新', { exact: true })).toBeVisible()
  const recentOpenButton = page.getByLabel(/打开(世界书|人物卡|剧本|预设)/).first()
  await expect(recentOpenButton).toBeVisible()
  await recentOpenButton.click()

  await page.locator('.v-navigation-drawer').getByText('世界书', { exact: true }).click()
  await expect(listItemTitle(page, '天阙封印')).toBeVisible()
  await listItemTitle(page, '天阙封印').click()

  const markdown = page.locator('.markdown-body').first()
  await expect(markdown.locator('h2', { hasText: '定义' })).toBeVisible()
  await expect(markdown).not.toContainText('## 定义')

  await page.locator('.v-navigation-drawer').getByText('人物卡', { exact: true }).click()
  await expect(listItemTitle(page, '林远')).toBeVisible()
  await listItemTitle(page, '林远').click()

  await expect(page.getByRole('tab', { name: '基础（BASIC）' })).toBeVisible()
  await expect(page.getByRole('tab', { name: '补充（EXTRAS）' })).toBeVisible()
  await expect(page.getByText('姓名（name）', { exact: true })).toBeVisible()
  await expect(page.getByText('性别（gender）', { exact: true })).toBeVisible()
  await expect(page.locator('tr').filter({ hasText: '性别（gender）' })).toContainText('男')

  await page.locator('.v-navigation-drawer').getByText('项目总览', { exact: true }).click()
  await page.getByRole('button', { name: /数据检查/ }).click()
  await expect(page.getByText('数据一致性检查')).toBeVisible()
  await expect(page.getByText(/暂无问题|未发现一致性问题|发现 \d+ 个问题/).first()).toBeVisible()

  expect(pageErrors).toEqual([])
})

test('settings expose LLM API configuration and button hover labels', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (error) => pageErrors.push(error.message))

  await page.goto('/')
  const settingsButton = page.getByLabel('设置')
  await settingsButton.hover()
  await expect(settingsButton).toHaveAttribute('title', '设置')

  await settingsButton.click()
  await expect(page.getByText('LLM API 配置')).toBeVisible()
  await expect(page.getByRole('button', { name: '关闭' })).toHaveAttribute('title', '关闭')
  await expect(page.getByRole('textbox', { name: 'API Key' })).toBeVisible()
  await expect(page.getByText(/当前状态/)).toBeVisible()
  await page.getByRole('textbox', { name: 'API Key' }).fill('e2e-secret-key')
  await page.getByLabel('模型').fill('mock-e2e-model')
  await page.getByRole('button', { name: '保存' }).click()
  await expect(page.getByText('AI 配置已保存')).toBeVisible()
  await expect(page.getByText('当前状态：已保存 API Key。')).toBeVisible()
  await expect(page.getByRole('textbox', { name: 'API Key' })).toHaveValue('')

  expect(pageErrors).toEqual([])
})

test('AI generation can be canceled without losing the prompt', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (error) => pageErrors.push(error.message))

  let releaseAiRequest: () => void = () => undefined
  const aiRequestHeld = new Promise<void>((resolve) => {
    releaseAiRequest = resolve
  })
  await page.route('**/api/projects/**/scripts/ai/generate', async (route) => {
    await aiRequestHeld
    try {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ code: 200, data: { content: '不应写入的取消后结果', generation_log: [] } }),
      })
    } catch {
      // The browser may have already aborted the request, which is the behavior under test.
    }
  })

  await page.goto('/')
  await page.locator('.v-navigation-drawer').getByText('剧本', { exact: true }).click()
  await page.getByLabel('AI生成剧本').click()
  await expect(page.getByText('AI 生成剧本内容')).toBeVisible()
  const prompt = page.getByLabel('生成提示词')
  await prompt.fill('这是一个应该在取消后保留的长调用提示词')
  await page.getByRole('button', { name: '生成', exact: true }).click()
  await expect(page.getByRole('button', { name: '取消生成' })).toBeVisible()
  await page.getByRole('button', { name: '取消生成' }).click()
  await expect(page.getByText('AI 操作已取消')).toBeVisible()
  await expect(prompt).toHaveValue('这是一个应该在取消后保留的长调用提示词')
  await expect(page.getByLabel('生成结果')).not.toHaveValue(/不应写入/)
  releaseAiRequest()

  expect(pageErrors).toEqual([])
})

test('project management supports edit archive restore and confirmed delete', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (error) => pageErrors.push(error.message))

  await page.goto('/')
  await page.getByRole('button', { name: '新建项目' }).click()
  await page.getByLabel('项目名称').fill('E2E项目管理')
  await page.getByLabel('题材').fill('测试')
  await page.getByLabel('描述').fill('项目管理端到端验证')
  const createDialog = page.locator('.v-overlay__content').filter({ hasText: '创建项目' }).last()
  await createDialog.getByLabel('项目默认风格').fill('E2E 默认风格')
  const createTemperature = createDialog.getByRole('slider').first()
  await createTemperature.press('Home')
  await createTemperature.press('ArrowRight')
  await createTemperature.press('ArrowRight')
  await createTemperature.press('ArrowRight')
  await createDialog.getByLabel('最大输出 Token').fill('18000')
  await createDialog.getByLabel('剧本').uncheck({ force: true })
  await createDialog.getByLabel('默认人物视图').press('ArrowDown')
  await page.getByRole('option', { name: '玩家' }).click()
  await page.getByRole('button', { name: '创建', exact: true }).click()
  await expect(page.getByText('项目已创建')).toBeVisible()

  let projectCard = page.locator('.v-sheet').filter({ hasText: 'E2E项目管理' }).first()
  await expect(projectCard).toBeVisible()
  await projectCard.getByLabel('编辑项目').click()
  const editDialog = page.locator('.v-overlay__content').filter({ hasText: '编辑项目' }).last()
  await expect(editDialog.getByLabel('项目默认风格')).toHaveValue('E2E 默认风格')
  await expect(editDialog.getByLabel('最大输出 Token')).toHaveValue('18000')
  await expect(editDialog.getByLabel('剧本')).not.toBeChecked()
  await expect(editDialog.getByRole('slider').first()).toHaveAttribute('aria-valuenow', '0.3')
  await page.getByLabel('项目名称').fill('E2E项目管理-改名')
  await page.getByRole('button', { name: '保存', exact: true }).click()
  await expect(page.getByText('项目已保存')).toBeVisible()

  await page.locator('.v-navigation-drawer').getByText('人物卡', { exact: true }).click()
  await page.getByLabel('AI生成人物卡').click()
  const aiDialog = page.locator('.v-overlay__content').filter({ hasText: 'AI 生成角色' }).last()
  await expect(aiDialog.getByRole('slider').first()).toHaveAttribute('aria-valuenow', '0.3')
  await page.getByRole('button', { name: '关闭' }).click()
  await page.locator('.v-navigation-drawer').getByText('项目总览', { exact: true }).click()

  projectCard = page.locator('.v-sheet').filter({ hasText: 'E2E项目管理-改名' }).first()
  await projectCard.getByLabel('归档项目').click()
  await expect(page.getByText('项目已归档')).toBeVisible()
  await expect(page.locator('.v-sheet').filter({ hasText: 'E2E项目管理-改名' })).toHaveCount(0)

  await page.getByLabel('显示归档').check({ force: true })
  projectCard = page.locator('.v-sheet').filter({ hasText: 'E2E项目管理-改名' }).first()
  await expect(projectCard).toBeVisible()
  await expect(projectCard.getByText('归档')).toBeVisible()
  await projectCard.getByLabel('恢复项目').click()
  await expect(page.getByText('项目已恢复')).toBeVisible()

  projectCard = page.locator('.v-sheet').filter({ hasText: 'E2E项目管理-改名' }).first()
  await projectCard.getByLabel('删除项目').click()
  await expect(page.getByText('删除项目')).toBeVisible()
  await page.getByLabel('E2E项目管理-改名').fill('E2E项目管理-改名')
  await page.getByRole('button', { name: '删除', exact: true }).click()
  await expect(page.getByText('项目已删除')).toBeVisible()
  await expect(page.locator('.v-sheet').filter({ hasText: 'E2E项目管理-改名' })).toHaveCount(0)

  expect(pageErrors).toEqual([])
})

test('character visibility editor controls the player view', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (error) => pageErrors.push(error.message))

  await page.goto('/')
  await page.locator('.v-navigation-drawer').getByText('人物卡', { exact: true }).click()
  await listItemTitle(page, '林远').click()
  await page.getByLabel('编辑人物卡').click()
  await expect(page.getByText('编辑角色')).toBeVisible()

  await page.getByRole('tab', { name: '可见性配置' }).click()
  const dialog = page.locator('.v-overlay__content').filter({ hasText: '编辑角色' }).last()
  const backgroundRow = dialog.locator('tbody tr').filter({ hasText: '背景经历（background）' }).first()
  await expect(backgroundRow).toBeVisible()
  await backgroundRow.getByLabel('显示模式 背景经历（background）').click({ force: true })
  await page.getByRole('option', { name: '自定义' }).click()
  await backgroundRow.getByLabel('自定义显示 背景经历（background）').fill('玩家只知道林远曾在青云剑宗受训')
  await page.getByRole('button', { name: '保存', exact: true }).click()
  await expect(page.getByText('角色已保存')).toBeVisible()

  await page.getByRole('button', { name: '玩家' }).click()
  await page.getByRole('tab', { name: '信息（KNOWLEDGE）' }).click()
  await expect(page.locator('tr').filter({ hasText: '背景经历（background）' })).toContainText('玩家只知道林远曾在青云剑宗受训')

  await page.getByRole('button', { name: '开发者' }).click()
  await expect(page.locator('tr').filter({ hasText: '背景经历（background）' })).not.toContainText('玩家只知道林远曾在青云剑宗受训')

  expect(pageErrors).toEqual([])
})

test('worldbook AI iteration previews before apply and records history', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (error) => pageErrors.push(error.message))

  await page.goto('/')
  await page.locator('.v-navigation-drawer').getByText('世界书', { exact: true }).click()
  await listItemTitle(page, '天阙封印').click()
  await expect(page.getByText(/版本 1/)).toBeVisible()

  await page.getByLabel('AI迭代世界书').click()
  await expect(page.getByText('AI 迭代世界书条目')).toBeVisible()
  await page.getByLabel('指定板块/分类（可选）').fill('规则')
  await page.getByLabel('迭代要求').fill('补强封印代价与宗门可执行规则')
  await page.getByRole('button', { name: '执行迭代' }).click()

  const preview = page.getByLabel('迭代预览结果')
  await expect(preview).toHaveValue(/## 规则/)
  await expect(page.locator('.markdown-preview-pane').locator('h2', { hasText: '规则' })).toBeVisible()
  await expect(page.locator('.markdown-preview-pane')).not.toContainText('## 规则')
  await expect(page.getByRole('button', { name: '应用迭代结果' })).toBeEnabled()
  await expect(page.getByText(/版本 1/)).toBeVisible()

  await page.getByRole('button', { name: '应用迭代结果' }).click()
  await expect(page.getByText('迭代结果已应用')).toBeVisible()
  await expect(page.getByText(/版本 2/)).toBeVisible()
  await expect(page.locator('.markdown-body').first().locator('h2', { hasText: '规则' }).first()).toBeVisible()
  await page.getByLabel('世界书版本历史').click()
  await expect(page.getByText('版本历史')).toBeVisible()
  await page.getByRole('button', { name: '对比' }).nth(1).click()
  const versionDialog = page.getByRole('dialog').filter({ hasText: '版本历史' }).last()
  await expect(versionDialog.locator('.version-diff-markdown h2', { hasText: '规则' }).first()).toBeVisible()
  await expect(versionDialog.locator('.version-diff-markdown').first()).not.toContainText('## 规则')
  await versionDialog.getByRole('button', { name: '关闭' }).click()

  await page.locator('.v-navigation-drawer').getByText('项目总览', { exact: true }).click()
  const iterateLogRow = page.locator('tbody tr').filter({ hasText: '世界书' }).filter({ hasText: '迭代' }).first()
  await expect(iterateLogRow).toBeVisible()
  await expect(page.locator('tbody tr').filter({ hasText: '世界书' }).filter({ hasText: '应用' }).filter({ hasText: '已保存' })).toBeVisible()
  await iterateLogRow.getByLabel('查看AI日志').click()
  await expect(page.getByText('AI 日志详情')).toBeVisible()
  await expect(page.getByLabel('完整 Prompt')).toHaveValue(/补强封印代价/)
  await expect(page.getByLabel('请求参数')).toHaveValue(/"section": "规则"/)
  await expect(page.getByText('过程日志')).toBeVisible()
  await expect(page.getByText(/调用 AI 模型|迭代完成/).first()).toBeVisible()
  await page.getByRole('button', { name: '关闭' }).click()

  expect(pageErrors).toEqual([])
})

test('worldbook AI generation carries template structured fields into the entry dialog', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (error) => pageErrors.push(error.message))

  await page.goto('/')
  await page.locator('.v-navigation-drawer').getByText('世界书', { exact: true }).click()
  await page.getByLabel('AI生成世界书').click()
  await expect(page.getByText('AI 生成世界书条目')).toBeVisible()
  await page.getByLabel('生成提示词').fill('生成一个用于端到端验证的世界书规则条目')
  await page.getByRole('button', { name: '生成', exact: true }).click()

  await expect(page.getByLabel('生成结果')).toHaveValue(/## 定义/)
  await expect(page.locator('.markdown-preview-pane').locator('h2', { hasText: '定义' })).toBeVisible()
  await page.getByRole('button', { name: '接受' }).click()

  const entryDialog = page.getByRole('dialog').filter({ hasText: '新建条目' }).last()
  await expect(entryDialog).toBeVisible()
  await expect(entryDialog.getByLabel('结构化字段 JSON')).toHaveValue(/"definition"/)
  await expect(entryDialog.getByLabel('结构化字段 JSON')).toHaveValue(/mock 模式生成/)
  await entryDialog.getByRole('button', { name: '保存' }).click()
  await expect(page.getByText('条目已保存')).toBeVisible()
  await expect(page.getByText('AI生成条目', { exact: true }).first()).toBeVisible()

  expect(pageErrors).toEqual([])
})

test('character AI iteration updates a field without losing Chinese labels or gender', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (error) => pageErrors.push(error.message))

  await page.goto('/')
  await page.locator('.v-navigation-drawer').getByText('人物卡', { exact: true }).click()
  await listItemTitle(page, '林远').click()
  await page.getByRole('tab', { name: '信息（KNOWLEDGE）' }).click()
  await expect(page.getByText('背景经历（background）', { exact: true })).toBeVisible()

  await page.getByLabel('AI迭代人物卡').click()
  await expect(page.getByText('AI 迭代人物卡')).toBeVisible()
  await page.getByLabel('指定板块/分类（可选）').fill('knowledge')
  await page.getByLabel('指定字段（角色可选）').fill('background')
  await page.getByLabel('迭代要求').fill('补强身世与灵灾后遗症')
  await expect(page.getByLabel('直接保存到人物卡（关闭则只生成预览）')).toBeChecked()
  await page.getByRole('button', { name: '执行并保存' }).click()

  await expect(page.getByText('人物卡已迭代并保存')).toBeVisible()
  await expect(page.locator('tr').filter({ hasText: '背景经历（background）' })).toContainText('mock 模式迭代后的background内容')

  const detailBody = page.locator('.pane.flex-grow-1 > .detail-body')
  await detailBody.getByRole('tab', { name: '基础（BASIC）' }).click()
  await expect(page.getByText('性别（gender）', { exact: true })).toBeVisible()
  await expect(detailBody.locator('tr').filter({ hasText: '性别（gender）' })).toContainText('男')

  await page.getByLabel('人物卡版本历史').click()
  await expect(page.getByText('版本历史')).toBeVisible()
  await expect(page.getByText('版本 2')).toBeVisible()

  expect(pageErrors).toEqual([])
})

test('character AI generation previews strict structure and creates a character', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (error) => pageErrors.push(error.message))

  await page.goto('/')
  await page.locator('.v-navigation-drawer').getByText('人物卡', { exact: true }).click()

  await page.getByLabel('AI生成人物卡').click()
  await expect(page.getByText('AI 生成角色')).toBeVisible()
  await page.getByLabel('生成提示词').fill('自由写一个调查型同伴角色，要求内容具体，但输出必须进入固定人物卡字段。')
  await page.getByRole('button', { name: '生成', exact: true }).click()

  const progressPanel = page.locator('.ai-progress-panel')
  await expect(progressPanel).toBeVisible()
  const progressStyle = await progressPanel.evaluate((element) => {
    const style = window.getComputedStyle(element)
    return { maxHeight: style.maxHeight, overflowY: style.overflowY }
  })
  expect(progressStyle.maxHeight).toBe('180px')
  expect(['auto', 'scroll']).toContain(progressStyle.overflowY)

  await expect(page.getByText('人物卡结构预览')).toBeVisible()
  await expect(page.getByRole('tab', { name: '基础（BASIC）' })).toBeVisible()
  await expect(page.getByText('姓名（name）', { exact: true })).toBeVisible()
  await expect(page.locator('.character-preview-pane')).toContainText('云舟')
  await expect(page.getByText('当前结果不是可解析的人物卡 JSON')).toHaveCount(0)

  await page.getByRole('tab', { name: '关系（RELATIONS）' }).click()
  await expect(page.locator('.character-preview-pane')).toContainText('目标角色（targetName）')
  await page.getByRole('tab', { name: '物品（INVENTORY）' }).click()
  await expect(page.locator('.character-preview-pane')).toContainText('物品名称（itemName）')
  await page.getByRole('tab', { name: '技能（SKILLS）' }).click()
  await expect(page.locator('.character-preview-pane')).toContainText('剧情用途（storyUse）')

  await page.getByRole('button', { name: '创建角色' }).click()
  await expect(page.getByText('AI 角色已创建')).toBeVisible()
  await expect(page.locator('.pane').filter({ hasText: '云舟' }).first()).toBeVisible()
  const detailBody = page.locator('.pane.flex-grow-1 > .detail-body')
  await detailBody.getByRole('tab', { name: '基础（BASIC）' }).click()
  await expect(detailBody.locator('tr').filter({ hasText: '姓名（name）' })).toContainText('云舟')
  await detailBody.getByRole('tab', { name: '技能（SKILLS）' }).click()
  await expect(detailBody).toContainText('剧情用途（storyUse）')

  expect(pageErrors).toEqual([])
})

test('script AI iteration previews, applies, and keeps markdown rendered', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (error) => pageErrors.push(error.message))

  await page.goto('/')
  await page.locator('.v-navigation-drawer').getByText('剧本', { exact: true }).click()
  await listItemTitle(page, '场景：坠星秘境的倒写天碑').click()
  await expect(page.getByText(/版本 1/)).toBeVisible()

  await page.getByLabel('AI迭代剧本').click()
  await expect(page.getByText('AI 迭代剧本节点')).toBeVisible()
  await page.getByLabel('指定板块/分类（可选）').fill('冲突推进')
  await page.getByLabel('迭代要求').fill('增强角色选择代价')
  await page.getByRole('button', { name: '执行迭代' }).click()

  const preview = page.getByLabel('迭代预览结果')
  await expect(preview).toHaveValue(/## 冲突推进/)
  await expect(page.getByRole('button', { name: '应用迭代结果' })).toBeEnabled()
  await expect(page.getByText(/版本 1/)).toBeVisible()

  await page.getByRole('button', { name: '应用迭代结果' }).click()
  await expect(page.getByText('迭代结果已应用')).toBeVisible()
  await expect(page.getByText(/版本 2/)).toBeVisible()
  await expect(page.locator('.markdown-body').first().locator('h2', { hasText: '冲突推进' })).toBeVisible()
  await expect(page.locator('.markdown-body').first()).not.toContainText('## 冲突推进')

  await page.getByLabel('剧本版本历史').click()
  await expect(page.getByText('版本历史')).toBeVisible()
  await expect(page.getByText('版本 2', { exact: true })).toBeVisible()
  const versionDialog = page.getByRole('dialog').filter({ hasText: '版本历史' }).last()
  const originalVersionRow = versionDialog.locator('.v-list-item').filter({ hasText: '版本 1' }).first()
  await originalVersionRow.getByRole('button', { name: '恢复' }).click()
  await expect(page.getByText('已恢复到版本 1')).toBeVisible()
  const detailBody = page.locator('.pane.flex-grow-1 > .detail-body')
  await expect(detailBody).not.toContainText('角色在有限信息下做出选择')
  await expect(page.getByText(/版本 3/)).toBeVisible()

  expect(pageErrors).toEqual([])
})

test('preset apply and combine workflows are usable from the workbench', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (error) => pageErrors.push(error.message))

  await page.goto('/')
  await page.locator('.v-navigation-drawer').getByText('预设', { exact: true }).click()
  await expect(listItemTitle(page, '史诗修仙叙事')).toBeVisible()
  await listItemTitle(page, '史诗修仙叙事').click()

  await page.getByLabel('应用预设').click()
  await expect(page.getByText('应用预设', { exact: true })).toBeVisible()
  await page.getByLabel('本次任务要求').fill('用于端到端验证的世界书生成要求')
  await page.getByRole('button', { name: '生成提示词' }).click()
  await expect(page.getByLabel('应用后完整提示词')).toHaveValue(/用于端到端验证的世界书生成要求/)
  await expect(page.getByLabel('应用后完整提示词')).toHaveValue(/输出定义、规则、冲突、钩子/)
  await page.getByRole('button', { name: '关闭' }).click()

  await page.getByLabel('组合预设').click()
  await expect(page.getByText('组合预设', { exact: true })).toBeVisible()
  await page.getByLabel('保存名称').fill('E2E组合预设')
  await page.getByRole('button', { name: '预览组合' }).click()
  await expect(page.getByText('组合后提示词')).toBeVisible()
  await expect(page.locator('.markdown-body').filter({ hasText: '动作清晰，招式有代价' })).toBeVisible()
  await page.getByRole('button', { name: '保存为新预设' }).click()
  await expect(page.getByText('组合预设已保存')).toBeVisible()
  await expect(page.locator('.v-list-item-title').filter({ hasText: 'E2E组合预设' })).toBeVisible()

  expect(pageErrors).toEqual([])
})

test('project package exports and imports through the workbench', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (error) => pageErrors.push(error.message))

  await page.goto('/')
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: /导出项目/ }).click(),
  ])
  const downloadPath = await download.path()
  expect(downloadPath).toBeTruthy()
  const exported = await readFile(downloadPath!, 'utf-8')
  expect(exported).toContain('"format_version"')
  expect(exported).toContain('"worldbook"')

  await page.getByRole('button', { name: /导入项目/ }).click()
  await page.locator('input[type="file"]').setInputFiles(downloadPath!)
  await expect(page.getByLabel('导入内容')).toHaveValue(/"format_version"/)
  await page.getByRole('button', { name: '预览' }).click()
  await expect(page.getByText('worldbook_entries')).toBeVisible()
  await expect(page.getByText('characters')).toBeVisible()
  await page.getByRole('button', { name: '导入', exact: true }).click()
  await expect(page.getByText('项目已导入')).toBeVisible()

  await page.locator('.v-navigation-drawer').getByText('世界书', { exact: true }).click()
  await expect(listItemTitle(page, '天阙封印')).toBeVisible()

  expect(pageErrors).toEqual([])
})
