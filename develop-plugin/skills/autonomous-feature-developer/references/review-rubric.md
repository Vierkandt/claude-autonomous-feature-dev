# Self-Review Rubric

Use this when no external review tool is available. Work through every applicable category. For each, state what you inspected and what you found — do not just write "pass."

---

## Correctness

- Does the code do what the plan describes? Trace each plan item to its implementation.
- Are there logic errors? Check conditionals, loop boundaries, off-by-one risks.
- Are edge cases handled? Empty inputs, missing data, concurrent access, network failures.
- Are null/undefined checks in place where data might be absent?
- Do error paths behave sensibly (meaningful messages, no swallowed exceptions)?

## Conventions Compliance

- Does every file follow the coding conventions from the project context file?
- Naming: variables, functions, components, files — do they match project patterns?
- Typing: are types explicit? Any `any`, untyped parameters, or missing interfaces?
- Imports: correct style (relative vs. absolute)? No circular dependencies?
- Exports: matches project convention (named vs. default)?
- File location: is each new file in the right directory per project structure?
- **Contract compliance:** Do all new files follow the project contract's model shapes,
  API error format, file locations, and coding patterns? Reference `docs/project-contract.md`.
  Check each contract section that is relevant to this feature.

## Security

- Is user input validated and sanitized before use?
- Are there injection risks (SQL, XSS, command injection, path traversal)?
- Are secrets, tokens, or credentials kept out of source code and logs?
- Are authentication/authorization checks in place where needed?
- Are dependencies from trusted sources with no known vulnerabilities?

## Performance

- Any unbounded loops, recursive calls without depth limits, or O(n²) on large data?
- Database/API calls: N+1 queries? Missing pagination? Unbatched operations?
- Bundle size: are new dependencies justified? Could a lighter alternative work?
- Are expensive operations lazy-loaded, cached, or debounced where appropriate?
- Images: are they optimized and appropriately sized?

## Accessibility *(skip if not a UI feature)*

- Semantic HTML: proper heading hierarchy, landmark elements, lists for lists?
- Interactive elements: keyboard accessible? Focus management?
- ARIA labels on non-text interactive elements (icon buttons, toggles)?
- Alt text on every image (descriptive for content images, empty for decorative)?
- Color contrast meets WCAG AA? Information not conveyed by color alone?
- `lang` attribute set correctly?

## Tests *(skip if project has no test suite)*

- Are new code paths covered by tests?
- Are existing tests still passing (no regressions)?
- Do tests cover the happy path AND at least one error/edge case?
- Are test descriptions clear about what they verify?
- Any flaky patterns (timing-dependent, order-dependent, global state)?

---

## Output Format

For each category, write:

```
### <Category>
Inspected: <what you looked at>
Findings:
- [critical/important/suggestion] <file:line> — <description>
- ...
(or: no issues found)
```
