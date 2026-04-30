# CLAUDE.md - Design System Portfolio

> **Related files**: Read `DESIGN_SYSTEM.md` for visual patterns and `ADDENDUM.md` for content schemas.

## Project Overview

Astro 6 portfolio site. Bilingual: English + Spanish. Two color modes: Light and Dark. Deployed to Vercel.

The site must feel alive and playful but remain scannable, fast, and recruiter-friendly. Every interactive flourish must degrade gracefully.

---

## Framework Constraints

| Constraint              | Detail                                                                                     |
|-------------------------|--------------------------------------------------------------------------------------------|
| **Node version**        | Node 22.12.0 or higher required. Set in `.nvmrc`: `22`.                                   |
| **View Transitions**    | Use `<ClientRouter />` from `astro:transitions`.                                           |
| **Vite version**        | ESM only. No CommonJS config files.                                                        |
| **Content Collections** | Use Content Layer API with `glob` loader.                                                  |

### Config Skeleton

```javascript
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';

export default defineConfig({
    site: process.env.PUBLIC_SITE_URL || 'http://localhost:4321',
    output: 'static',
    integrations: [react()],
    i18n: {
        defaultLocale: 'en',
        locales: ['en', 'es'],
    },
});
```

> **Icon loading**: Use `astro-icon` integration with Iconify icon sets. Icons are built at deploy time.

---

## Accessibility (WCAG 2.2 Level AA)

**Every component, page, and interaction MUST conform to WCAG 2.2 Level AA.** No exceptions.

### Perceivable

| Criterion                 | ID     | Requirement                                                             |
|---------------------------|--------|-------------------------------------------------------------------------|
| Non-text Content          | 1.1.1  | All images: meaningful `alt` or `aria-hidden="true"` if decorative.     |
| Info and Relationships    | 1.3.1  | Semantic HTML. Headings follow logical hierarchy.                       |
| Color Contrast            | 1.4.3  | 4.5:1 normal text, 3:1 large text. Both themes.                        |
| Non-text Contrast         | 1.4.11 | UI components: 3:1 against adjacent colors.                            |
| Reflow                    | 1.4.10 | Reflows at 320px CSS width without horizontal scroll.                   |
| Text Spacing              | 1.4.12 | Functional with line-height 1.5x, letter spacing 0.12em.               |

### Operable

| Criterion                     | ID     | Requirement                                              |
|-------------------------------|--------|----------------------------------------------------------|
| Keyboard                      | 2.1.1  | ALL functionality operable via keyboard.                 |
| No Keyboard Trap              | 2.1.2  | Drawers trap focus internally, release on close.         |
| Skip Navigation               | 2.4.1  | "Skip to main content" link, both languages.             |
| Focus Visible                 | 2.4.7  | Custom focus ring in both themes.                        |
| Target Size (Minimum)         | 2.5.8  | 24x24 CSS px minimum.                                   |

---

## Design Tokens

- Use CSS custom properties for all colors, spacing, and typography.
- Never use hardcoded hex values in component files.
- Always use `var(--token-name)` referencing `global.css` definitions.
- Use the pipe operator: `cat tokens.json | node scripts/gen.js` to regenerate tokens.

## Component Rules

- Use functional components for all new React islands.
- Always validate props with TypeScript interfaces.
- Include `aria-label` on interactive elements.

## References

- [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md)
- [ADDENDUM.md](./ADDENDUM.md)
- [BUILD_PLAN.md](./BUILD_PLAN.md)
