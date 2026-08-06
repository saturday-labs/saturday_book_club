---
tags:
- country
creation date: 04/12/2025 19:21:30
modification date: 04/12/2025 19:21:30
title: France
---

# France

---

## Related authors

```dataview
TABLE title AS "Author", periods AS "Period"
FROM "knowledge_base"
WHERE type = "author"
AND contains(countries, this.file.name)
SORT title ASC
```
