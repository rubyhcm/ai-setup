# Unified AI Agent Playbook (Cross-Platform)

Repository này là bộ khung hướng dẫn và quản trị tập trung (**Centralized Governance**) dành cho các AI Agents và IDE Assistants. Nó được thiết kế để đồng bộ hóa các quy tắc lập trình, quy chuẩn kiến trúc và bộ công cụ tối ưu (RTK, GitNexus) trên 8+ nền tảng phổ biến nhất hiện nay (Claude, Cursor, Copilot, Kiro, Kilo, Gemini, JetBrains, Antigravity).

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
| [docs/rtk-setup-guide.md](docs/rtk-setup-guide.md) | Hướng dẫn cài đặt và sử dụng RTK (Rust Token Killer) |
| [docs/icm-setup-guide.md](docs/icm-setup-guide.md) | Hướng dẫn cài đặt và sử dụng ICM (Interactive Context Management) |
| [docs/gitnexus-setup-guide.md](docs/gitnexus-setup-guide.md) | Hướng dẫn cài đặt và sử dụng GitNexus (Code Intelligence Engine) |
| [docs/ai-toolchain-integration-status.md](docs/ai-toolchain-integration-status.md) | Trạng thái tích hợp RTK/ICM/GitNexus trên tất cả platforms |

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
├── .rules/                    # Master Rules (Single Source of Truth)
├── .aiassistant/              # JetBrains AI rules (auto-generated)
├── .antigravity/              # Antigravity IDE rules (auto-generated)
├── .cursor/                   # Cursor rules (auto-generated)
├── .github/                   # Copilot instructions (auto-generated)
├── .kilo/                     # Kilo CLI rules (auto-generated)
├── .kiro/                     # Kiro IDE & CLI steering (auto-generated)
├── .ai-agents/                # Workspace runtime của Claude Code
├── prompts/                   # Hệ thống System Prompts cho agents
├── scripts/                   # Scripts đồng bộ (sync_rules.py)
├── docs/                      # Hướng dẫn chi tiết
├── GEMINI.md                  # Chỉ thị cho Gemini CLI
├── README.md                  # Giới thiệu tổng quan
└── USER_GUIDE.md              # Cẩm nang sử dụng chi tiết
```

## Ghi chú Quan trọng

- **Không sửa trực tiếp** các file trong `.cursor/`, `.kiro/`, `.kilo/`, `.aiassistant/`, `.antigravity/`, hay `.github/`. 
- **Quy trình chuẩn:** Chỉ sửa luật tại `.rules/`, sau đó chạy `python scripts/sync_rules.py` để đồng bộ sang tất cả IDEs/Agents.
- Hệ thống đã tích hợp sẵn **RTK, ICM và GitNexus** để tối ưu hóa token và an toàn kiến trúc.
- Tuyệt đối tuân thủ **Git Autonomy**: AI không được tự ý stage/commit nếu không có lệnh cụ thể.
