---
name: deploy-service
description: Deploys a service to the selected environment.
---

# Deploy Service

Before deploying, ask the user which environment they want to deploy to — staging or production. Wait for their answer, then proceed.

MUST invoke `Bash` to run the deploy script:

```
Bash({
  command: "npm run deploy:staging",
  description: "Run the deployment script for the selected environment"
})
```
