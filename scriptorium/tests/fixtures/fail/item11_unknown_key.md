---
name: validate-schema
description: Validates a JSON schema against a data file and reports any violations.
priority: high
owner: backend-team
---

# Validate Schema

MUST invoke `Bash` to run the schema validator:

```
Bash({
  command: "npx ajv validate -s schema.json -d data.json --errors=json",
  description: "Validate data.json against schema.json and output structured errors"
})
```
