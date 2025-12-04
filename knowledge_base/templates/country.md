---
name: <% tp.file.title %>
type: country
tags: ["country"]
created: <% tp.file.creation_date("DD/MM/yyyy HH:mm:ss") %>
updated: <% tp.file.last_modified_date("DD/MM/yyyy HH:mm:ss") %>
---

# <% tp.file.title %>

---

```dataview
TABLE name AS "Author", period AS "Period"
FROM "knowledge_base"
WHERE contains(tags, "author") 
AND country = this.file.name
SORT name ASC
```
