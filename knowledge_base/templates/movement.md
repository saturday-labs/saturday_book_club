---
title: <% tp.file.title %>
periods: []
origin: ""
concepts: []
authors: []
type: movement
tags: ["movement"]
created: <% tp.file.creation_date("DD/MM/yyyy HH:mm:ss") %>
updated: <% tp.file.last_modified_date("DD/MM/yyyy HH:mm:ss") %>
---

# <% tp.file.title %>

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

## Works Related to This Movement

```dataview
TABLE title AS "Title", authors AS "Author", year AS "Year"
FROM "knowledge_base"
WHERE type = "book"
AND contains(movements, this.file.name)
SORT year ASC
```
