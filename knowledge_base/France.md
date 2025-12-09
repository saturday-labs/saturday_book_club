---
name: France
tags:
  - country
creation date: 04/12/2025 19:21:30
modification date: 04/12/2025 19:21:30
---

# France

---

## Related authors

```dataview
TABLE name AS "Author", period AS "Period", key_works as "Books"
FROM "knowledge_base"
WHERE type = "author"
AND country.file.name = this.file.name
SORT name ASC
```
