# AI Toolchain Rules

This project enforces the strict usage of **RTK (Rust Token Killer)**, **ICM (Interactive Context Management)**, and **GitNexus** across all AI agents, IDEs (Cursor, Kiro), and Assistants (Claude, Copilot). 

> **Important Setup Note:** RTK, ICM, and GitNexus are installed globally on the local host machine. They are available in the system `$PATH`. Do **NOT** attempt to install them, and do not expect them to be listed in project-level dependency files (e.g., `go.mod`, `package.json`). Assume they are always ready to use.

## 1. RTK & ICM (Token Efficiency & Output Management)
Repository: https://github.com/rtk-ai/rtk

**RTK** and **ICM** are required to filter noise, compress standard terminal outputs, and reduce token consumption. 
Whenever an AI agent executes a shell command, it MUST use RTK/ICM to wrap the command.

- **Shell Commands:** Always prefix standard information-gathering commands with `rtk` (unless a transparent shell hook is already active).
  - Use `rtk git status`, `rtk git diff`, `rtk git log` instead of raw git commands.
  - Use `rtk ls`, `rtk find` instead of standard `ls` or `find`.
  - Use `rtk test <command>` (e.g., `rtk test go test ./...`) so that the AI only receives failure traces and ignores passing noise.
  - Use `rtk read <file>` instead of `cat <file>` to view file contents with smart truncation.
- **ICM (Interactive Context Management):** Use `icm` commands when instructed or available to manage chat context, clear redundant history, and focus the context window on relevant code sections.

## 2. GitNexus (Code Intelligence & Impact Analysis)
Repository: https://github.com/abhigyanpatwari/GitNexus

**GitNexus** is our Code Intelligence Engine. It builds a local knowledge graph of the codebase to provide "X-ray vision" into dependencies and execution flows.
All AI agents must leverage GitNexus for repository understanding, refactoring, and impact analysis.

- **MCP Tools:** If your environment supports MCP (Model Context Protocol), use GitNexus MCP tools:
  - `query({query: "..."})` for semantic and graph-based codebase search.
  - `impact({target: "...", direction: "upstream|downstream"})` before modifying any shared interface or critical struct. This analyzes the blast radius of your changes.
  - `context({name: "..."})` to get a 360-degree view of a symbol (callers, callees, functional cluster).
  - `detect_changes()` to map current git diffs to functional processes.
- **CLI Fallback:** If MCP is unavailable, use the equivalent GitNexus CLI commands to perform graph queries and impact analysis *before* making cross-cutting codebase changes.

## 3. Git Operations & Autonomy Constraints
AI Agents MUST NOT autonomously stage or commit changes to version control without explicit, granular user permission.
- **STRICT FORBIDDEN:** Do NOT execute ANY `git add` command (even for a single specific file) unless the user has explicitly told you to "stage this file", "git add this", or "prepare a commit with these changes".
- **STRICT FORBIDDEN:** Do NOT use wildcard staging like `git add .` or `git add -A` under any circumstances.
- **STRICT FORBIDDEN:** Do NOT execute `git commit` unless the user explicitly asks you to "commit the changes".
- **REQUIRED ACTION:** If you have finished a task and the user hasn't mentioned git, simply stop and report that the files are modified in the working directory. Do NOT attempt to stage them "just in case".

## Enforcement Checklist for Agents
1. Did I wrap my test execution or git commands with `rtk`?
2. Did I use GitNexus (`impact` or `context`) to verify the blast radius before refactoring a core domain struct or service interface?
3. Am I optimizing my context window using ICM principles rather than dumping entire files?
4. Did I refrain from running ANY `git add` or `git commit` command? (I must only do this if the user explicitly said to stage/commit).
