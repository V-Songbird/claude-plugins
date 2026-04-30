# Organization Analysis Guide

Reference for Phase 3b organization analysis and the reorganization apply step.

## Claude Code's Documented Guidance

- **CLAUDE.md** is for instructions every session needs: build commands, test conventions, project architecture, core conventions
- **.claude/rules/** is for focused guidelines. Rules with `paths:` frontmatter only load when Claude works with matching files, saving context

## Analysis Methodology

1. Count rules in CLAUDE.md vs `.claude/rules/` files
2. Classify each CLAUDE.md rule:
   - **Stays**: build commands, repo structure, git workflow, CI/CD, core conventions that apply to every file in every session
   - **Moves**: rules about specific directories, file types, workflows, or topical groups that benefit from a dedicated file
3. Group "move" rules by shared `paths:` pattern
4. Suggest specific file names and `paths:` frontmatter for each group
5. Estimate impact: lines CLAUDE.md drops by, rules that become scoped

## Presentation Format

```
## How your rules should be organized

Per Claude Code docs, CLAUDE.md is for core conventions, build commands,
and project architecture. Specific guidelines belong in .claude/rules/
files where they can be scoped to relevant files.

Your CLAUDE.md currently has [N] rules. Here's where they should live:

Keep in CLAUDE.md ([count] rules):
  [one-line summary — build commands, repo structure, etc.]

Move to .claude/rules/[name].md ([count] rules):
  [paths: ["pattern"] if scoped, or "no paths: — always-loaded topical file"]
  [one-line summary of the rules in this group]

Move to .claude/rules/[name].md ([count] rules):
  [paths: ["pattern"]]
  [one-line summary]

**Impact:** CLAUDE.md drops from [N] lines to ~[M] lines. [X] rules
become scoped and only load when relevant.
```

## File Naming Guidelines

- Use descriptive names matching the project's domain: `v2-components.md`, `migration.md`, `code-style.md`, `comments.md`
- If the project already has `.claude/rules/` files, suggest adding to existing files where themes match
- Use `paths:` frontmatter only when rules genuinely apply to a subset of files
- A file with 2-3 rules is fine — don't merge unrelated rules to reduce file count
- Present the "keep" list first so the user sees what stays before what moves

## When to Skip

If CLAUDE.md is already well-organized (few rules, mostly core conventions), say so briefly and skip reorganization suggestions.

If there are no `.claude/rules/` files yet, note that the user can create the directory.

## Applying Reorganization

When the user accepts reorganization changes:

### Creating scoped files

1. Create each `.claude/rules/` file using the Write tool:
   - Start with YAML frontmatter (`paths:` if scoped, `default-category:` if not mandate)
   - Write each rule as a markdown bullet (`- Rule text here`)
   - If the rule was also rewritten in Phase 3.5, use the rewritten text

2. If `.claude/rules/` doesn't exist, create it first

### Removing from CLAUDE.md

1. Find each moved rule's original text in CLAUDE.md
2. Remove it (and surrounding blank lines that would leave gaps)
3. Preserve section headings that still have remaining content

### Reporting

```
Created .claude/rules/v2-components.md (8 rules, scoped to src/v2/**)
Created .claude/rules/code-style.md (14 rules, always-loaded)
Removed 22 rules from CLAUDE.md (213 lines -> 62 lines)
```

### Constraints

- Preserve section headings that still have content after rule removal
- Only move rule-classified content — not commands, code blocks, or architecture descriptions
- Don't duplicate rules that exist in both CLAUDE.md and an existing `.claude/rules/` file
- Preserve rule order within each new file
- Leave git operations to the user
