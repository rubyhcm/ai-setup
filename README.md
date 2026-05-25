# Claude Code Agent Playbook

Repository này là bộ hướng dẫn để dùng với Claude Code theo mô hình đa agent (Plan/Code/Test/Review/Fix), không chứa runtime Go nữa.

## Thành phần chính

- `.rules/` - **Single Source of Truth** cho luật dự án (kiến trúc, toolchain, security, testing, coding style)
- `prompts/` - Prompt vai trò cho Claude Code agents
- `.cursor/rules/` - Tự động sinh ra (MDX) cho Cursor IDE
- `.kiro/steering/` - Tự động sinh ra cho Amazon Kiro IDE & CLI
- `.kilo/rules/` - Tự động sinh ra cho Kilo CLI
- `.github/instructions/` - Tự động gộp cho GitHub Copilot
- `.aiassistant/rules/` - Tự động sinh ra cho JetBrains AI Assistant (Air)
- `.antigravity/rules/` - Tự động sinh ra cho Antigravity IDE
- `GEMINI.md` - Luật gốc cho Gemini CLI
- `scripts/` - Scripts tự động hóa (VD: `sync_rules.py` để đồng bộ luật từ `.rules/` sang mọi IDE)
- `docs/` - Tài liệu hướng dẫn
- `.ai-agents/` - Nơi lưu artifact của Claude Code trong quá trình làm việc

## Tài liệu

| File | Mô tả |
|------|-------|
| [USER_GUIDE.md](USER_GUIDE.md) | Hướng dẫn sử dụng đầy đủ tất cả agents |
| [docs/sonarcloud-scan-guide.md](docs/sonarcloud-scan-guide.md) | Hướng dẫn cài đặt và chạy SonarCloud scan |
| [.kiro/README.md](.kiro/README.md) | Hướng dẫn sử dụng Kiro steering rules và spec |

## Cách dùng nhanh

### Claude Code Agents (pipeline tự động)

1. Mở repo đích trong Claude Code.
2. Copy `.rules/` và `prompts/` từ repo này sang repo đích.
3. Chạy pipeline:
   ```
   /agent-full Tạo API quản lý người dùng
   ```

### Kiro IDE (spec-driven)

1. Chạy `/agent-kiro` để tạo spec:
   ```
   /model claude-opus-4-6
   /agent-kiro Tạo tính năng xác thực JWT
   ```
2. Copy `.kiro/` sang repo đích.
3. Mở Kiro IDE, yêu cầu implement theo spec.

## Ghi chú

- Không cần `go.mod`, `Makefile`, hoặc binary runtime trong repo playbook này.
- Nếu repo đích là Go project, các prompt/rules vẫn áp dụng bình thường.

## Overview

```text
ai_tech/
├── prompts/                   # Bộ não của agents (system prompts)
│   └── agent-kiro.md          # System prompt cho Agent Kiro
├── .claude/commands/          # Slash commands cho user
│   └── agent-kiro.md          # /agent-kiro command
├── .rules/                    # Luật viết code (dùng cho Claude Code agents)
├── .kiro/                     # Steering rules + spec templates (dùng cho Kiro IDE)
│   ├── steering/              # Rules Kiro luôn đọc (inclusion: always)
│   │   ├── project-overview.md
│   │   ├── architecture.md
│   │   ├── go-conventions.md
│   │   ├── database.md
│   │   ├── security.md
│   │   ├── testing.md
│   │   └── design-patterns.md
│   └── specs/                 # Feature specs (tạo bằng /agent-kiro)
│       └── _template/         # Template để tạo spec mới
├── .ai-agents/                # Workspace runtime của Claude Code agents
├── scripts/                   # Scripts dùng chung
├── docs/                      # Tài liệu hướng dẫn
├── reports/                   # Báo cáo sinh ra bởi agents
├── README.md                  # Giới thiệu hệ thống
├── USER_GUIDE.md              # Hướng dẫn sử dụng đầy đủ
├── sonar-project.properties   # Cấu hình SonarCloud
├── .gitignore
└── .golangci.yml
```
