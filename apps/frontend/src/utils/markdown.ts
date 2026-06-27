export function escapeHtml(value: unknown) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export function safeMarkdownUrl(url: string) {
  const trimmed = url.trim()
  return /^(https?:|mailto:)/i.test(trimmed) ? trimmed : '#'
}

export function isMarkdownDocumentPath(path: string) {
  const key = String(path || '').split('.').pop() || ''
  return ['content', 'compiled_prompt'].includes(key)
}

export function shouldRenderMarkdownValue(path: string, value: unknown) {
  return isMarkdownDocumentPath(path) && typeof value === 'string'
}

export function renderInlineMarkdown(value: string) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/__([^_]+)__/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      (_match, label, url) => `<a href="${escapeHtml(safeMarkdownUrl(url))}" target="_blank" rel="noreferrer">${label}</a>`,
    )
}

export function renderMarkdown(markdown: string) {
  const lines = String(markdown || '').replace(/\r\n/g, '\n').split('\n')
  const html: string[] = []
  let paragraph: string[] = []
  let listType: 'ul' | 'ol' | '' = ''
  let listItems: string[] = []
  let inCodeBlock = false
  let codeLines: string[] = []

  const flushParagraph = () => {
    if (!paragraph.length) return
    html.push(`<p>${paragraph.join('<br>')}</p>`)
    paragraph = []
  }
  const flushList = () => {
    if (!listType) return
    html.push(`<${listType}>${listItems.join('')}</${listType}>`)
    listType = ''
    listItems = []
  }
  const flushCode = () => {
    html.push(`<pre><code>${codeLines.join('\n')}</code></pre>`)
    codeLines = []
  }

  for (const rawLine of lines) {
    const line = rawLine.trimEnd()
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        flushCode()
        inCodeBlock = false
      } else {
        flushParagraph()
        flushList()
        inCodeBlock = true
        codeLines = []
      }
      continue
    }
    if (inCodeBlock) {
      codeLines.push(escapeHtml(line))
      continue
    }
    if (!line.trim()) {
      flushParagraph()
      flushList()
      continue
    }
    const heading = line.match(/^(#{1,6})\s+(.+)$/)
    if (heading) {
      flushParagraph()
      flushList()
      const level = heading[1].length
      html.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`)
      continue
    }
    const unordered = line.match(/^\s*[-*]\s+(.+)$/)
    const ordered = line.match(/^\s*\d+\.\s+(.+)$/)
    if (unordered || ordered) {
      flushParagraph()
      const nextType = unordered ? 'ul' : 'ol'
      if (listType && listType !== nextType) flushList()
      listType = nextType
      listItems.push(`<li>${renderInlineMarkdown((unordered || ordered)?.[1] || '')}</li>`)
      continue
    }
    const quote = line.match(/^>\s?(.+)$/)
    if (quote) {
      flushParagraph()
      flushList()
      html.push(`<blockquote>${renderInlineMarkdown(quote[1])}</blockquote>`)
      continue
    }
    paragraph.push(renderInlineMarkdown(line.trim()))
  }
  if (inCodeBlock) flushCode()
  flushParagraph()
  flushList()
  return html.join('')
}
