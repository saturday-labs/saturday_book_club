import { visit } from "unist-util-visit"
import { fromHtml } from "hast-util-from-html"
import { resolveRelative, escapeHTML } from "@quartz-community/utils"

// Renders a narrow subset of Obsidian Dataview at build time: TABLE/LIST,
// FROM "<folder>", WHERE with AND/OR/parens/contains()/"=", SORT <field> ASC|DESC.
// Not a general DQL engine — covers only the query shapes used in this vault.

const LANG = "dataview"
const CONTENT_ROOT = "knowledge_base"

// ---------- tokenizer + tiny recursive-descent parser for WHERE ----------

function tokenize(src) {
  const tokens = []
  const re = /"[^"]*"|'[^']*'|\(|\)|,|=/g
  let last = 0
  let m
  const pushWord = (text) => {
    for (const w of text.split(/\s+/)) {
      if (w) tokens.push(w)
    }
  }
  while ((m = re.exec(src))) {
    pushWord(src.slice(last, m.index))
    tokens.push(m[0])
    last = m.index + m[0].length
  }
  pushWord(src.slice(last))
  return tokens
}

function stripQuotes(tok) {
  if (!tok) return tok
  if ((tok[0] === '"' && tok.endsWith('"')) || (tok[0] === "'" && tok.endsWith("'"))) {
    return tok.slice(1, -1)
  }
  return tok
}

function isLiteral(tok) {
  return tok && (tok[0] === '"' || tok[0] === "'")
}

function parseOperand(tokens, i) {
  const tok = tokens[i.v++]
  if (isLiteral(tok)) return { lit: stripQuotes(tok) }
  return { path: tok.split(".") }
}

function parseWhereExpr(tokens) {
  const i = { v: 0 }

  function parseTerm() {
    if (tokens[i.v] === "(") {
      i.v++
      const e = parseOr()
      if (tokens[i.v] === ")") i.v++
      return e
    }
    if ((tokens[i.v] || "").toUpperCase() === "CONTAINS") {
      i.v++ // contains
      if (tokens[i.v] === "(") i.v++
      const field = parseOperand(tokens, i)
      if (tokens[i.v] === ",") i.v++
      const value = parseOperand(tokens, i)
      if (tokens[i.v] === ")") i.v++
      return { type: "contains", field, value }
    }
    const left = parseOperand(tokens, i)
    if (tokens[i.v] === "=") i.v++
    const right = parseOperand(tokens, i)
    return { type: "eq", left, right }
  }

  function parseAnd() {
    let node = parseTerm()
    while ((tokens[i.v] || "").toUpperCase() === "AND") {
      i.v++
      node = { type: "and", items: [node, parseTerm()] }
    }
    return node
  }

  function parseOr() {
    let node = parseAnd()
    while ((tokens[i.v] || "").toUpperCase() === "OR") {
      i.v++
      node = { type: "or", items: [node, parseAnd()] }
    }
    return node
  }

  return parseOr()
}

// ---------- query-level parsing (TABLE/LIST, FROM, WHERE, SORT) ----------

function splitClauses(tokens) {
  const KEYWORDS = new Set(["TABLE", "LIST", "FROM", "WHERE", "SORT"])
  const sections = {}
  let key = null
  for (const tok of tokens) {
    const up = tok.toUpperCase()
    if (KEYWORDS.has(up)) {
      key = up
      sections[key] = sections[key] || []
      continue
    }
    if (key) sections[key].push(tok)
  }
  return sections
}

function parseColumns(tokens) {
  const chunks = []
  let cur = []
  for (const t of tokens) {
    if (t === ",") {
      if (cur.length) chunks.push(cur)
      cur = []
      continue
    }
    cur.push(t)
  }
  if (cur.length) chunks.push(cur)

  return chunks.map((chunk) => {
    const fieldTok = chunk[0]
    let label = fieldTok
    const asIdx = chunk.findIndex((t) => t.toUpperCase() === "AS")
    if (asIdx !== -1 && chunk[asIdx + 1]) label = stripQuotes(chunk[asIdx + 1])
    return { path: fieldTok.split("."), label }
  })
}

function parseDataviewQuery(raw) {
  const tokens = tokenize(raw)
  const sections = splitClauses(tokens)
  const kind = sections.TABLE ? "TABLE" : sections.LIST ? "LIST" : null
  const columns = sections.TABLE ? parseColumns(sections.TABLE) : []
  const fromPath = sections.FROM && sections.FROM[0] ? stripQuotes(sections.FROM[0]) : null
  const where = sections.WHERE && sections.WHERE.length ? parseWhereExpr(sections.WHERE) : null
  const sort =
    sections.SORT && sections.SORT.length
      ? {
          path: sections.SORT[0].split("."),
          desc: (sections.SORT[1] || "").toUpperCase() === "DESC",
        }
      : null
  return { kind, columns, fromPath, where, sort }
}

// ---------- wikilink + row helpers ----------

function parseWikilink(raw) {
  if (typeof raw !== "string") return null
  const m = /^\s*\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]\s*$/.exec(raw)
  if (!m) return null
  return { target: m[1].trim(), alias: m[2] ? m[2].trim() : undefined }
}

function linkTargetName(raw) {
  const v = Array.isArray(raw) ? raw[0] : raw
  if (typeof v !== "string") return null
  const link = parseWikilink(v)
  const target = link ? link.target : v
  return target.split("/").pop().trim()
}

function toArray(v) {
  if (v === undefined || v === null) return []
  return Array.isArray(v) ? v : [v]
}

function stemOf(fileData) {
  const rel = fileData.relativePath || fileData.filePath || fileData.slug || ""
  const base = rel.split("/").pop() || rel
  return base.replace(/\.[^.]+$/, "")
}

function buildRows(allFiles) {
  return allFiles
    .filter((fd) => fd.slug !== undefined)
    .map((fd) => {
      const rel = fd.relativePath || fd.filePath || fd.slug || ""
      const name = stemOf(fd)
      return {
        name,
        nameLower: name.toLowerCase(),
        path: rel,
        slug: fd.slug,
        frontmatter: fd.frontmatter || {},
        title: (fd.frontmatter && (fd.frontmatter.name || fd.frontmatter.title)) || name,
      }
    })
}

function filterFrom(rows, fromPath) {
  if (!fromPath) return rows
  let rel = fromPath
  if (rel === CONTENT_ROOT) return rows
  if (rel.startsWith(CONTENT_ROOT + "/")) {
    rel = rel.slice(CONTENT_ROOT.length + 1)
  } else {
    return rows
  }
  return rows.filter((r) => r.path === rel || r.path.startsWith(rel + "/"))
}

// resolves a dotted path (e.g. this.file.name, country.file.name, period) against
// either the current page (self) or a candidate row.
function resolvePath(path, row, self) {
  const [head, ...rest] = path
  if (head === "this") {
    if (rest[0] === "file") {
      if (rest[1] === "name") return self.name
      return self.frontmatter ? self.frontmatter[rest[1]] : undefined
    }
    return self.frontmatter ? self.frontmatter[rest[0]] : undefined
  }
  if (head === "file") {
    if (rest[0] === "name") return row.name
    return undefined
  }
  const base = row.frontmatter ? row.frontmatter[head] : undefined
  if (rest.length === 0) return base
  if (rest[0] === "file" && rest[1] === "name") return linkTargetName(base)
  return undefined
}

function evalOperand(op, row, self) {
  if ("lit" in op) return op.lit
  return resolvePath(op.path, row, self)
}

function evalNode(node, row, self) {
  if (!node) return true
  if (node.type === "and") return node.items.every((n) => evalNode(n, row, self))
  if (node.type === "or") return node.items.some((n) => evalNode(n, row, self))
  if (node.type === "contains") {
    const arr = toArray(evalOperand(node.field, row, self))
    const val = evalOperand(node.value, row, self)
    if (val === undefined || val === null || val === "") return false
    return arr.some((item) => {
      const t = linkTargetName(item)
      if (t && String(t).toLowerCase() === String(val).toLowerCase()) return true
      return String(item).toLowerCase() === String(val).toLowerCase()
    })
  }
  if (node.type === "eq") {
    const l = evalOperand(node.left, row, self)
    const r = evalOperand(node.right, row, self)
    if (Array.isArray(l) || Array.isArray(r)) return false
    if (l === undefined || l === null || l === "" || r === undefined || r === null || r === "") {
      return false
    }
    return String(l).toLowerCase() === String(r).toLowerCase()
  }
  return false
}

function plainSortValue(v) {
  if (v === undefined || v === null) return ""
  const target = linkTargetName(v)
  return String(target ?? v)
}

function runQuery(query, allFiles, self) {
  let rows = buildRows(allFiles)
  rows = filterFrom(rows, query.fromPath)
  rows = rows.filter((r) => evalNode(query.where, r, self))
  if (query.sort) {
    const { path, desc } = query.sort
    rows = rows.slice().sort((a, b) => {
      const cmp = plainSortValue(resolvePath(path, a, self)).localeCompare(
        plainSortValue(resolvePath(path, b, self)),
        undefined,
        { numeric: true },
      )
      return desc ? -cmp : cmp
    })
  }
  return rows
}

// ---------- HTML rendering ----------

function renderLinkOrText(raw, rowsByNameLower, currentSlug) {
  const link = parseWikilink(raw)
  const targetRaw = link ? link.target : String(raw)
  const targetName = targetRaw.split("/").pop().trim()
  const display = (link && link.alias) || targetName
  const match = rowsByNameLower.get(targetName.toLowerCase())
  if (match) {
    const href = resolveRelative(currentSlug, match.slug)
    const label = (link && link.alias) || match.title || display
    return `<a href="${href}">${escapeHTML(label)}</a>`
  }
  if (!link) return escapeHTML(String(raw))
  return escapeHTML(display)
}

function renderCell(value, rowsByNameLower, currentSlug) {
  if (value === undefined || value === null || value === "") return ""
  const arr = Array.isArray(value) ? value : [value]
  const rendered = arr
    .filter((v) => v !== undefined && v !== null && v !== "")
    .map((v) => renderLinkOrText(v, rowsByNameLower, currentSlug))
  return rendered.join(", ")
}

function renderQueryHtml(query, rows, rowsByNameLower, currentSlug) {
  if (rows.length === 0) {
    return `<div class="dataview-lite dataview-empty" style="color: var(--gray); font-style: italic;">No results</div>`
  }

  if (query.kind === "LIST") {
    const items = rows
      .map((r) => `<li>${renderLinkOrText(`[[${r.name}]]`, rowsByNameLower, currentSlug)}</li>`)
      .join("")
    return `<ul class="dataview-lite dataview-list">${items}</ul>`
  }

  const cols = query.columns.length > 0 ? query.columns : [{ path: ["name"], label: "Name" }]
  const head = cols.map((c) => `<th>${escapeHTML(c.label)}</th>`).join("")
  const body = rows
    .map((r) => {
      const cells = cols
        .map((c) => {
          const raw = resolvePath(c.path, r, r)
          return `<td>${renderCell(raw, rowsByNameLower, currentSlug)}</td>`
        })
        .join("")
      return `<tr>${cells}</tr>`
    })
    .join("")
  return `<table class="dataview-lite dataview-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`
}

// ---------- hast helpers ----------

function extractText(node) {
  if (node.type === "text") return node.value
  if (node.children) return node.children.map(extractText).join("")
  return ""
}

function findDataviewCode(node) {
  if (node.type !== "element") return null
  if (node.tagName === "pre") {
    const code = (node.children || []).find((c) => c.type === "element" && c.tagName === "code")
    const classes = (code && code.properties && code.properties.className) || []
    if (code && classes.includes(`language-${LANG}`)) return code
    return null
  }
  if (node.tagName === "figure") {
    const pre = (node.children || []).find((c) => c.type === "element" && c.tagName === "pre")
    if (pre) return findDataviewCode(pre)
  }
  return null
}

function rehypeTagDataviewBlocks() {
  return (tree, file) => {
    visit(tree, "element", (node, index, parent) => {
      if (!parent || index === undefined) return
      const code = findDataviewCode(node)
      if (!code) return
      const raw = extractText(code)
      if (!file.data.dataviewBlocks) file.data.dataviewBlocks = []
      const blockIndex = file.data.dataviewBlocks.length
      file.data.dataviewBlocks.push(raw)
      parent.children[index] = {
        type: "element",
        tagName: "div",
        properties: { dataQzDataviewCodeblock: String(blockIndex) },
        children: [],
      }
    })
  }
}

function dataviewTreeTransform(root, _slug, componentData) {
  const blocks = componentData.fileData.dataviewBlocks
  if (!blocks || blocks.length === 0) return

  const allFiles = componentData.allFiles || []
  const rows = buildRows(allFiles)
  const rowsByNameLower = new Map(rows.map((r) => [r.nameLower, r]))
  const self = { name: stemOf(componentData.fileData), frontmatter: componentData.fileData.frontmatter || {} }
  const currentSlug = componentData.fileData.slug

  visit(root, "element", (node) => {
    const blockIndexStr = node.properties && node.properties.dataQzDataviewCodeblock
    if (blockIndexStr === undefined) return
    const raw = blocks[Number(blockIndexStr)]
    if (raw === undefined) return

    let html
    try {
      const query = parseDataviewQuery(raw)
      const resultRows = runQuery(query, allFiles, self)
      html = renderQueryHtml(query, resultRows, rowsByNameLower, currentSlug)
    } catch {
      html = `<div class="dataview-lite dataview-error">Could not render Dataview query</div>`
    }

    const fragment = fromHtml(html, { fragment: true })
    node.tagName = "div"
    node.properties = { className: ["dataview-lite-container"] }
    node.children = fragment.children
  })
}

export default function DataviewLite() {
  return {
    name: "DataviewLite",
    htmlPlugins() {
      return [rehypeTagDataviewBlocks]
    },
    match() {
      return false
    },
    layout: "content",
    body: () => () => null,
    treeTransforms() {
      return [dataviewTreeTransform]
    },
  }
}
