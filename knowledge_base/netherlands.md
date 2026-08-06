---
type: country
tags:
- country
created: 09/12/2025 13:12:59
updated: 09/12/2025 13:12:59
title: Netherlands
---

# netherlands

---

```dataview
TABLE title AS "Author", periods AS "Period"
FROM "knowledge_base"
WHERE type = "author"
AND contains(countries, this.file.name)
SORT title ASC
```
