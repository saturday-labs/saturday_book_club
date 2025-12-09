---
name: popular_science
period: []
origin: ""
concepts: []
founders: []
key_authors: []
key_works: []
type: movement
tags:
  - movement
created: 09/12/2025 13:25:48
updated: 09/12/2025 13:25:48
---

# popular_science

---

## Core Principles

Summarize the essential ideas of this philosophical movement:

-  
-  
-  

---

## Historical Context

Explain *why* this movement appeared at this particular time:

- Cultural and intellectual background  
- Social / political foundations  
- Key problems the movement attempted to solve  

---

## Influence & Legacy

- How this movement shaped later philosophy  
- Movements or authors influenced by it  
- Modern relevance  

---

## Criticism

- Common objections  
- Weak points or unresolved contradictions  
- Counter-movements or rival schools  

---

## Related Concepts

```dataview
TABLE name AS "Movement", period AS "Period"
FROM "knowledge_base"
WHERE type = "movement"
AND contains(concepts, this.file.name)
SORT name ASC
```

---

## Works Related to This Movement

```dataview
TABLE title AS "Title", author AS "Author", year AS "Year"
FROM "knowledge_base/books"
WHERE type = "book"
AND contains(movements, this.file.name)
SORT year ASC
```
