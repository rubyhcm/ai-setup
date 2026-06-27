# CommandCode Project Memory

This workspace follows strict Go Clean Architecture and agent tooling rules. Detailed rules are found in the `.rules/` directory.

---

## GitNexus — Code Intelligence

This project is indexed by GitNexus as **ai-backend-go** (824 symbols, 889 relationships, 1 execution flow). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

### Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

### Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

### Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/ai-backend-go/context` | Codebase overview, check index freshness |
| `gitnexus://repo/ai-backend-go/clusters` | All functional areas |
| `gitnexus://repo/ai-backend-go/processes` | All execution flows |
| `gitnexus://repo/ai-backend-go/process/{name}` | Step-by-step execution trace |

---

## AI Toolchain (RTK + ICM + GitNexus)

This project enforces the strict usage of **RTK (Rust Token Killer)**, **ICM (Interactive Context Management)**, and **GitNexus** across all AI agents and IDEs.

> RTK, ICM, and GitNexus are installed globally on the local host machine and available in the system `$PATH`. Do NOT attempt to install them.

### RTK & ICM (Token Efficiency & Output Management)

Whenever executing a shell command, prefix it with `rtk` (unless a transparent shell hook is active):

| Raw command | RTK equivalent |
|-------------|----------------|
| `git status` | `rtk git status` |
| `git diff` | `rtk git diff` |
| `cat file.go` | `rtk read file.go` |
| `go test ./...` | `rtk test go test ./...` |
| `ls` | `rtk ls` |

Use `icm clear` after completing each task to optimize context window.

### Git Operations

- **STRICT FORBIDDEN:** Do NOT execute any `git add` or `git commit` without explicit user permission.
- **STRICT FORBIDDEN:** Do NOT use wildcard staging like `git add .` or `git add -A`.
- When work is done, simply report that files are modified — do NOT stage/commit them.

---

## Project Rules to Follow

- Read `.rules/architecture.md` before designing any new component
- Read `.rules/go-conventions.md` before writing Go code
- Read `.rules/testing.md` before writing tests (table-driven tests required)
- Read `.rules/security.md` for security requirements
- Read `.rules/database.md` for DB schema and migrations
- Read `.rules/design-patterns.md` for coding patterns
