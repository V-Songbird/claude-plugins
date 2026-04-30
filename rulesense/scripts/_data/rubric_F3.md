Level 4 (0.90–1.00): Immediate — action is same operation as trigger. No gap between recognizing the trigger and executing the action.

> "Use `getProjectCommands(project)` not `.database.commands`"
> Trigger: writing code that accesses command database. Action: use the project-aware method.
> The trigger and action are the same keystroke — you're choosing which API to call as you write. Score: 0.95.

> "Each test file must import from the module it tests, not from barrel exports"
> Trigger: writing a test import. Action: import from the module directly.
> Same moment. Score: 0.95.

Level 3 (0.65–0.85): Soon — action happens during the same task but at a slightly later step. Trigger is recognizable and proximate.

> "When adding new grammar rules, add corresponding PSI visitor methods and test coverage."
> Trigger: adding grammar rules. Action: add visitor methods + tests.
> Same task, but the action is a follow-up step after the grammar edit. Score: 0.75.

> "Use functional components for all new React files."
> Trigger: creating a new React file. Action: write a functional component.
> Trigger and action overlap — creating the file IS writing the component — but "new" requires recognizing the file doesn't exist yet. Score: 0.80.

Level 2 (0.40–0.60): Distant — action must happen at a future moment the model has to independently recognize, separated by multiple intermediate steps.

> "Every commit modifying src/ MUST end with [State: SYNCED]"
> Trigger: committing code. Action: add the suffix.
> The model reads this at session start, then 40+ turns later must remember at commit time. Score: 0.45.

> "Run prettier on modified files before committing"
> Trigger: about to commit. Action: run prettier first.
> Same distance — the trigger is a future event the model must interrupt itself to recognize. Score: 0.50.

Level 1 (0.15–0.35): Abstract — rule expresses a principle or disposition rather than a concrete trigger-action pair. No specific moment it fires.

> "The site must feel alive, playful, and aquatic — but remain scannable, fast, and recruiter-friendly."
> No concrete trigger moment. Firing is diffuse — the rule offers a disposition Claude can encode but has no specific moment to check work against. Score: 0.20.

> "Try to prefer functional components when possible"
> "When possible" is an abstract trigger — no specific moment the model should recognize as the firing condition. Score: 0.25.

Level 0 (0.00–0.10): No trigger — no identifiable trigger or action. A statement, not an instruction.

> "All files, conventions, naming, and state schemas are optimized for agent consumption."
> Description of the system, not a directive. Score: 0.00.

> "**Home** (`/` | `/es/`) — Hero, featured projects, CTA."
> A sitemap entry, not a rule. No verb, no trigger, no action. Score: 0.05.

Score higher within a level when:
- The trigger is more concrete ("when creating .tsx files" > "when working with React")
- The action is more specific ("add PSI visitor methods" > "add test coverage")
- The trigger is a recognized programming event (file creation, import writing) rather than a subjective judgment

Score lower within a level when:
- The trigger references an abstract concept rather than a programming event ("when something is expensive")
- The action is ambiguous about which artifact it produces ("add test coverage" — what kind? where?)
- The rule depends on the model remembering it across many intermediate steps
