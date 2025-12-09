---
name: United Kingdom
type: country
tags:
  - country
created: 09/12/2025 13:12:59
updated: 09/12/2025 13:12:59
---

# united_kingdom

---

```dataview
TABLE name AS "Author", period AS "Period", key_works as "Books"
FROM "knowledge_base"
WHERE type = "author"
AND country.file.name = this.file.name
SORT name ASC
```
