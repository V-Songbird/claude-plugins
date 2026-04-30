---
name: build-project
description: Builds the project and checks for type errors.
---

# Build Project

MUST invoke `Bash` to compile the TypeScript source:

```
Bash({
  command: "npx tsc --noEmit --strict --target ES2020 --module ESNext --moduleResolution bundler"
})
```

MUST invoke `Bash` to run the bundler:

```
Bash({
  command: "npx webpack --config webpack.prod.config.js --bail --progress --env production"
})
```
