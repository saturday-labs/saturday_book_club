---
title: <% tp.file.title %>
periods: []
countries: []
nationality: ""
birth: null
death: null
type: author
tags: ["author"]
created: <% tp.file.creation_date("DD/MM/yyyy HH:mm:ss") %>
updated: <% tp.file.last_modified_date("DD/MM/yyyy HH:mm:ss") %>
---

# <% tp.file.title %>

---

## Short Description

A concise summary of the thinker: style, interests, intellectual focus, and why they matter.

---

## Context & Influence

- Historical background shaping the author’s ideas  
- Impact on later thinkers and movements  
- Schools or debates influenced by their work  

---

## Criticism

- Common objections or weak points  
- Internal contradictions  
- How other schools interpret or challenge this author  

---

## Related Authors

```dataview
TABLE name AS "Author", period AS "Period"
FROM "knowledge_base"
WHERE type = "author"
AND (
    contains(movements, this.file.movements)
    OR contains(concepts, this.file.concepts)
    OR period = this.file.period
)
SORT name ASC
```

---

## Book Club Notes

Use this section to capture remarks from discussions:

-  
-  
-  
