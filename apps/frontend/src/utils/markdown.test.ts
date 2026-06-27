import { describe, expect, it } from 'vitest'
import { renderMarkdown, safeMarkdownUrl, shouldRenderMarkdownValue } from './markdown'

describe('renderMarkdown', () => {
  it('renders headings, inline styles, lists, quotes, and paragraphs', () => {
    const html = renderMarkdown(`# 标题

正文 **加粗** 和 *斜体*，还有 \`code\`。

- 第一项
- 第二项

> 引用内容`)

    expect(html).toContain('<h1>标题</h1>')
    expect(html).toContain('<strong>加粗</strong>')
    expect(html).toContain('<em>斜体</em>')
    expect(html).toContain('<code>code</code>')
    expect(html).toContain('<ul><li>第一项</li><li>第二项</li></ul>')
    expect(html).toContain('<blockquote>引用内容</blockquote>')
  })

  it('escapes raw html while preserving fenced code text', () => {
    const html = renderMarkdown(`## 定义 <script>alert(1)</script>

\`\`\`
<div>unsafe</div>
\`\`\``)

    expect(html).toContain('<h2>定义 &lt;script&gt;alert(1)&lt;/script&gt;</h2>')
    expect(html).toContain('<pre><code>&lt;div&gt;unsafe&lt;/div&gt;</code></pre>')
    expect(html).not.toContain('<script>')
  })

  it('sanitizes unsafe links and keeps http links clickable', () => {
    expect(safeMarkdownUrl('javascript:alert(1)')).toBe('#')
    expect(safeMarkdownUrl('https://example.com')).toBe('https://example.com')

    const html = renderMarkdown('[官网](https://example.com) [危险](javascript:alert(1))')
    expect(html).toContain('<a href="https://example.com" target="_blank" rel="noreferrer">官网</a>')
    expect(html).toContain('<a href="#" target="_blank" rel="noreferrer">危险</a>')
  })

  it('detects version diff fields that should render as markdown documents', () => {
    expect(shouldRenderMarkdownValue('content', '## 定义')).toBe(true)
    expect(shouldRenderMarkdownValue('data.compiled_prompt', '[系统提示]\n正文')).toBe(true)
    expect(shouldRenderMarkdownValue('developer_data.basic.summary', '普通摘要')).toBe(false)
    expect(shouldRenderMarkdownValue('content', { text: 'not string' })).toBe(false)
  })
})
