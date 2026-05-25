import os
import glob

RULES_DIR = ".rules"
KIRO_DIR = ".kiro/steering"
KILO_DIR = ".kilo/rules"
CURSOR_DIR = ".cursor/rules"
GITHUB_DIR = ".github/instructions"
JETBRAINS_DIR = ".aiassistant/rules"
ANTIGRAVITY_DIR = ".antigravity/rules"
COPILOT_FILE = os.path.join(GITHUB_DIR, "copilot-instructions.md")
GEMINI_FILE = "GEMINI.md"

# Map files to their descriptions for Cursor rules
CURSOR_DESCRIPTIONS = {
    "architecture.md": "Architecture and dependency rules for Go Clean Architecture.",
    "database.md": "Database design, indexing, and migration rules.",
    "design-patterns.md": "Design patterns and SOLID principles guidelines.",
    "go-conventions.md": "Go coding conventions: naming, error handling, context, logging, concurrency.",
    "project-overview.md": "High-level overview of the project, stack, and goals.",
    "security.md": "Security requirements and secure coding checklist.",
    "testing.md": "Testing standards, coverage requirements, and table-driven test formats.",
    "ai-toolchain.md": "Mandatory usage of RTK, ICM, and GitNexus for AI agents."
}

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    rules_files = sorted(glob.glob(os.path.join(RULES_DIR, "*.md")))
    all_rules_content = []
    
    # Pre-generate Copilot header
    all_rules_content.append("# GitHub Copilot Instructions\n\nThis is a consolidated file generated from `.rules/`.\n")
    
    gemini_toolchain_content = ""

    for rule_path in rules_files:
        filename = os.path.basename(rule_path)
        content = read_file(rule_path).strip()
        
        if filename == "ai-toolchain.md":
            gemini_toolchain_content = content
            
        # 1. Sync Kiro (.kiro/steering/xxx.md)
        kiro_content = f"---\ninclusion: always\n---\n\n{content}\n"
        write_file(os.path.join(KIRO_DIR, filename), kiro_content)
        
        # 2. Sync Cursor (.cursor/rules/xxx.mdc)
        desc = CURSOR_DESCRIPTIONS.get(filename, f"Rules for {filename}")
        globs = '["**/*.go", "**/*.sql"]' if filename == "database.md" else '["**/*.go"]'
        cursor_content = f"---\ndescription: {desc}\nglobs: {globs}\nalwaysApply: false\n---\n\n{content}\n"
        cursor_filename = filename.replace(".md", ".mdc")
        write_file(os.path.join(CURSOR_DIR, cursor_filename), cursor_content)
        
        # 3. Sync JetBrains (.aiassistant/rules/xxx.md)
        write_file(os.path.join(JETBRAINS_DIR, filename), f"{content}\n")
        
        # 4. Sync Antigravity (.antigravity/rules/xxx.md)
        write_file(os.path.join(ANTIGRAVITY_DIR, filename), f"{content}\n")
        
        # 5. Sync Kilo (.kilo/rules/xxx.md)
        write_file(os.path.join(KILO_DIR, filename), f"{content}\n")
        
        # 6. Append to Copilot content
        all_rules_content.append(f"\n---\n\n{content}\n")
        print(f"Synced {filename} to Kiro, Cursor, JetBrains, Antigravity, and Kilo.")

    # Write Copilot instructions
    write_file(COPILOT_FILE, "".join(all_rules_content))
    print(f"Generated {COPILOT_FILE}")
    
    # Write Gemini CLI instructions
    gemini_content = f"""# Gemini CLI Instructions

This workspace follows strict Go Clean Architecture and agent tooling rules.
Detailed rules are found in the `.rules/` directory. Do not guess the architecture; always refer to `.rules/architecture.md` and `.rules/go-conventions.md`.

## Mandatory Agent Toolchain
You MUST follow the AI Toolchain rules defined below:

{gemini_toolchain_content}
"""
    write_file(GEMINI_FILE, gemini_content)
    print(f"Generated {GEMINI_FILE}")
    
    # Remove old .mdc files if they got renamed or deleted
    for cursor_file in glob.glob(os.path.join(CURSOR_DIR, "*.mdc")):
        base_md = os.path.basename(cursor_file).replace(".mdc", ".md")
        if not os.path.exists(os.path.join(RULES_DIR, base_md)):
            os.remove(cursor_file)
            print(f"Removed orphaned {cursor_file}")
            
    # Remove old files in other directories
    for sync_dir in [KIRO_DIR, KILO_DIR, JETBRAINS_DIR, ANTIGRAVITY_DIR]:
        for sync_file in glob.glob(os.path.join(sync_dir, "*.md")):
            base_md = os.path.basename(sync_file)
            if not os.path.exists(os.path.join(RULES_DIR, base_md)):
                os.remove(sync_file)
                print(f"Removed orphaned {sync_file}")

if __name__ == "__main__":
    main()
