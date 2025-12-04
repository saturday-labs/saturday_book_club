---
name: <% tp.file.title %>
period: ""
country: ""
nationality: ""
birth: null
death: null
concepts: []
movements: []
key_works: []
type: author
tags: ["author"]
created: <% tp.file.creation_date("DD/MM/yyyy HH:mm:ss") %>
updated: <% tp.file.last_modified_date("DD/MM/yyyy HH:mm:ss") %>
rating: 1   # 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10
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
