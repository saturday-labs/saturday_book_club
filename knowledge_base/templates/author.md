---
type: author
name: "{{title}}"
period: ""
country: ""
movements: []
key_works: []
tags: ["philosophy", "author"]
---

# {{title}}

## Overview
- **Period:**  
- **Country:**  
- **Philosophical movements:**  
  - [[ ]]  
  - [[ ]]
- **Major works:**  
  - [[ ]]  
  - [[ ]]

---

## Short Description
A concise summary of the thinker: style, interests, intellectual focus, and why they matter.

---

## Core Ideas
List major concepts linked to this author:

- [[ ]]  
- [[ ]]  
- [[ ]]

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
- [[ ]]  
- [[ ]]

---

## Book Club Notes
Use this section to capture remarks from discussions:

-  
-  
-  

---

# 📊 Dataview: Works by this Author

```dataview
TABLE title AS "Title", year AS "Year", movement AS "Movement"
FROM "knowledge_base/books"
WHERE contains(author, this.name)
SORT year ASC
```
