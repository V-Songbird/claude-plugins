---
name: generate-config
description: Generates a project configuration file from a canonical template.
---

# Generate Config

Use the following template to generate `config.json`:

```json
{
  "version": "2.0",
  "settings": {
    "logging": {
      "level": "info",
      "format": "json",
      "destination": "stdout",
      "rotation": {
        "enabled": true,
        "maxSize": "100MB",
        "maxAge": 30,
        "compress": true
      }
    },
    "database": {
      "host": "localhost",
      "port": 5432,
      "name": "myapp",
      "pool": {
        "min": 2,
        "max": 10,
        "idleTimeoutMs": 30000,
        "acquireTimeoutMs": 60000
      },
      "ssl": {
        "enabled": false,
        "rejectUnauthorized": true
      }
    },
    "cache": {
      "enabled": true,
      "ttlSeconds": 300,
      "maxSize": 1000,
      "evictionPolicy": "lru"
    },
    "api": {
      "timeout": 30000,
      "retries": 3,
      "rateLimit": {
        "requests": 100,
        "windowMs": 60000
      }
    },
    "auth": {
      "jwtSecret": "${JWT_SECRET}",
      "tokenTtlSeconds": 3600,
      "refreshTokenTtlSeconds": 604800
    }
  }
}
```

MUST invoke `Bash` to write the file:

```
Bash({
  command: "cat config-template.json > config.json",
  description: "Write the generated config to disk"
})
```
