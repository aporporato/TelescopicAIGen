# scripts/align_configs.py
import os
import shutil

def copy_file(src, dst):
    try:
        # Create directory if it doesn't exist
        dst_dir = os.path.dirname(dst)
        if dst_dir and not os.path.exists(dst_dir):
            os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"[OK] Copied {src} -> {dst}")
    except Exception as e:
        print(f"[ERROR] Failed to copy {src} -> {dst}: {e}")

def sync_dir(src, dst):
    try:
        if not os.path.exists(src):
            return
        if os.path.exists(dst):
            # If dst is a symlink, remove it first to avoid recursive circular errors
            if os.path.islink(dst):
                os.remove(dst)
            else:
                shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"[OK] Synchronized directory {src} -> {dst}")
    except Exception as e:
        print(f"[ERROR] Failed to sync directory {src} -> {dst}: {e}")

def main():
    print("=== Aligning Multi-Vendor Configurations ===")
    
    # 1. Sync AGENTS.md to all context files
    agents_src = "AGENTS.md"
    if os.path.exists(agents_src):
        copy_file(agents_src, ".cursorrules")
        copy_file(agents_src, ".github/copilot-instructions.md")
        copy_file(agents_src, ".codex/instructions.md")
        copy_file(agents_src, "CLAUDE.md")
    
    # 2. Sync subagents from .agents/agents to .github/agents
    subagents_src = ".agents/agents"
    subagents_dst = ".github/agents"
    if os.path.exists(subagents_src):
        # Sync the entire folder
        sync_dir(subagents_src, subagents_dst)

    # 3. Sync skills folder to all vendor skills directories
    skills_src = "skills"
    if os.path.exists(skills_src):
        sync_dir(skills_src, ".agents/skills")
        sync_dir(skills_src, ".claude/skills")
        sync_dir(skills_src, ".cursor/skills")
        sync_dir(skills_src, ".github/skills")
        sync_dir(skills_src, ".codex/skills")

if __name__ == "__main__":
    main()
