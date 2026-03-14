# Project Contract

> This file is read by every auto-dev agent in the swarm.
> It contains hard constraints. Every agent follows every rule here exactly.
>
> How to fill this in:
> - Remove every section that does not apply to your project
> - Do not write "N/A", "optional", "TBD", or leave placeholder text
> - No prose, no examples, no explanations — only definitions
> - Omit a section entirely rather than writing an empty one
>
> Audience: machines, not humans.

---

## Models

<!-- Define every shared data model used by multiple features.
     Feature-local models go in the feature code, not here.
     Use TypeScript interfaces or your language's equivalent. -->

```typescript
interface ExampleModel {
  id: string         // uuid, generated on create
  name: string       // required, max 255 chars
  createdAt: Date    // set by ORM on insert, not writable by API
}
```

---

## API

<!-- One definitive value per line. No ranges, no "or", no optionality. -->

- Style: REST
- Base path: /api/v1
- Auth mechanism: JWT in httpOnly cookie
- Auth middleware location: src/middleware/auth.ts
- Error shape: `{ error: string, code: number }`
- Pagination: `{ data: T[], nextCursor: string | null }`

---

## File Structure

<!-- Define where each category of file lives. Paths are relative to project root.
     These become hard constraints — every agent follows them. -->

- Routes: src/routes/<resource>.ts
- Models: src/models/<name>.ts
- Middleware: src/middleware/<name>.ts
- Utils: src/lib/<name>.ts
- Shared types: src/types/<domain>.ts

---

## Patterns

<!-- Define implementation patterns all features must follow.
     Only include patterns that apply to multiple features. -->

- Database access: repository pattern — no raw queries in route handlers
- Repository location: src/repositories/<model>.ts
- Validation: Zod schema defined in route file, exported as <Resource>Schema
- Auth guard: requireAuth() middleware wrapping all protected routes
- Type exports: define in src/types/<domain>.ts, re-export from src/types/index.ts

---

## Dependencies

<!-- List shared dependencies with version constraints where they matter. -->

- ORM: Prisma 5.x
- Validation: Zod 3.23+
- Auth: jsonwebtoken 9.x
