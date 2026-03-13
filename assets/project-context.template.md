# Project Context

> Read by the **Autonomous Feature Developer** skill. Place at
> `docs/project-context.md` in the repo root, or specify an alternate path.
>
> Fill in every section. Replace example values with your own.
> Remove sections marked *(optional)* if they don't apply.

---

## Stack

> Keep rows that apply, remove the rest.

| Layer | Technology | Notes |
|---|---|---|
| Language | e.g. TypeScript 5.4, Python 3.12, Rust 1.78 | |
| Framework | e.g. Next.js 15, Django 5, Astro 5, none | |
| UI | e.g. React, Preact islands, Vue, CLI (no UI) | |
| Styling | e.g. Tailwind CSS 4, CSS Modules, N/A | |
| Data | e.g. Prisma + Postgres, SQLAlchemy, Zod collections | |
| CMS | e.g. Sanity, Contentful, none | *(optional)* |
| Hosting | e.g. Vercel, AWS, Cloudflare Pages, self-hosted | |

---

## Build & Run

> The skill uses `build` to verify, `test` for the test suite, `lint` for
> static checks. Leave a line blank or remove it to skip that step.

```yaml
install:  npm install
dev:      npm run dev             # informational only — not used by the skill
build:    npm run build           # REQUIRED
test:     npm test                # optional
lint:     npm run lint            # optional
```

---

## Key Paths

> Directories and files the Architecture phase should explore.

```
src/                — main source directory
tests/              — test files
config/             — configuration files
docs/               — documentation
package.json        — dependencies and scripts
```

---

## Design Spec *(optional)*

> Path to a design document the Architecture phase should read before planning.

```
docs/specs/design.md
```

---

## Coding Conventions

> Describe your project's rules. Rewrite these examples to match your project.

### General
- Language for code: **TypeScript** *(or Python, Rust, Go, etc.)*
- Language for user-facing text: **English** *(or Dutch, Spanish, etc.)*
- Import style: relative imports within `src/`
- Export style: named exports preferred

### Components *(delete if not applicable)*
- Describe component model, naming, file patterns, typing conventions.

### Styling *(delete if not applicable)*
- Framework, design tokens, responsive approach.

### Performance
- Bundle/binary size limits, lazy loading rules, SSR/SSG, caching.

### Accessibility *(delete if not applicable)*
- Semantic HTML, ARIA, alt text, keyboard navigation, color contrast.

### Testing
- Framework (Vitest, pytest, cargo test, Jest, etc.)
- Coverage expectations for new code.

---

## Design Tokens *(optional)*

> Colors, fonts, spacing — whatever your project standardizes.

```
primary:        #3b82f6
primary-light:  #dbeafe
primary-dark:   #1e40af
text:           #111827
background:     #ffffff
font-family:    system-ui, sans-serif
```

---

## Git / PR Conventions

```yaml
base-branch:      main            # or: develop, master, trunk
merge-strategy:   --squash        # or: --rebase, --merge
hosting-cli:      gh              # or: glab
commit-prefixes:  feat, fix, chore, docs, refactor, test
branch-pattern:   feature/<slug>
delete-branch:    true
```

---

## Review Domains *(optional)*

> Define file-ownership domains for the review-fix loop's parallel agents.
> If omitted, the skill infers one domain per top-level source subdirectory.

| Domain | Allowed paths | Forbidden paths |
|---|---|---|
| **ui** | `src/components/`, `src/pages/` | `src/lib/`, `tests/` |
| **core** | `src/lib/`, `src/models/` | `src/components/` |
| **tests** | `tests/` | `src/` |

---

## CI / Branch Protection *(optional)*

> CI checks or branch rules the skill should know about.
> E.g. "Requires passing build + test in CI before merge."
> E.g. "Branch protection requires 1 human approval — skill cannot self-merge."

---

## Additional Notes *(optional)*

> Anything else: env vars, secrets handling, monorepo structure, deploy steps, etc.
