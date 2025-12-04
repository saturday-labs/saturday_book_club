---
name: Germany
type: country
tags:
  - country
created: 04/12/2025 19:21:30
updated: 04/12/2025 19:21:30
---

# Germany

---

```dataview
TABLE name AS "Author", period AS "Period", key_works as "Books"
FROM "knowledge_base"
WHERE type = "author"
AND country.file.name = this.file.name
SORT name ASC
```

