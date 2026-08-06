---
type: country
tags:
- country
created: 04/12/2025 19:21:30
updated: 04/12/2025 19:21:30
title: Germany
---

# Germany

---

```dataview
TABLE title AS "Author", periods AS "Period"
FROM "knowledge_base"
WHERE type = "author"
AND contains(countries, this.file.name)
SORT title ASC
```
