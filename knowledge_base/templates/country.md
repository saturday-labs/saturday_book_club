---
title: <% tp.file.title %>
type: country
tags: ["country"]
created: <% tp.file.creation_date("DD/MM/yyyy HH:mm:ss") %>
updated: <% tp.file.last_modified_date("DD/MM/yyyy HH:mm:ss") %>
---

# <% tp.file.title %>

---

```dataview
TABLE title AS "Author", periods AS "Period"
FROM "knowledge_base"
WHERE type = "author"
AND contains(countries, this.file.name)
SORT title ASC
```
