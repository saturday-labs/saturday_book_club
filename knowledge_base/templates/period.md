---
name: <% tp.file.title %>
start: null
end: null
major_concepts: []
major_movements: []
major_authors: []
type: period    
tags: ["period"]
created: <% tp.file.creation_date("DD/MM/yyyy HH:mm:ss") %>
updated: <% tp.file.last_modified_date("DD/MM/yyyy HH:mm:ss") %>
---

# <% tp.file.title %>

---

## Historical Context

Explain the social, political, scientific, and cultural forces that shaped this era:

-  
-  
-  

---

## Intellectual Characteristics

What defines the thinking of this period?

- Core themes  
- Dominant questions  
- Epistemological or metaphysical tendencies  
- Methodologies typical for the era  

---

## Influence & Legacy

How this era shaped later philosophy:

- Long-term intellectual impacts  
- Movements or authors influenced by this period  
- Relevance today  

---

## Criticism or Limitations

- Weak points of the era’s worldview  
- Internal contradictions  
- Critiques from later philosophers  

---

## Related Movements

```dataview
LIST FROM "knowledge_base"
WHERE period = this.name
and type = "movement"
SORT file.name ASC
```
