# scripts/free_port.py
import subprocess
import os
import sys
import json

def main():
    # 1. Check if we are running inside Antigravity and get the command being executed
    metadata_str = os.getenv("ANTIGRAVITY_SOURCE_METADATA")
    is_app_start = False
    
    if metadata_str:
        try:
            metadata = json.loads(metadata_str)
            tool_args = metadata.get("tool", {}).get("args", {})
            command_line = tool_args.get("CommandLine", "")
            if "app.py" in command_line:
                is_app_start = True
        except Exception:
            pass
            
    # 2. Fallback to CLI arguments (for Cursor, Codex, Claude Code)
    if not is_app_start and len(sys.argv) > 1:
        command_str = " ".join(sys.argv[1:])
        if "app.py" in command_str:
            is_app_start = True

    # If it's not a command starting app.py, exit early to preserve running instance
    if not is_app_start:
        return

    try:
        # Run netstat to find process using port 8000
        output = subprocess.check_output("netstat -ano", shell=True).decode('utf-8')
        pids = set()
        for line in output.splitlines():
            if ":8000" in line and "LISTENING" in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pids.add(parts[-1])
        for pid_str in pids:
            try:
                pid = int(pid_str)
                if pid != os.getpid(): # Avoid killing ourselves
                    print(f"[FREE-PORT] Terminating existing server process {pid} on port 8000...")
                    # Kill using taskkill
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except ValueError:
                continue
    except Exception as e:
        print(f"[FREE-PORT] Error checking port 8000: {e}")

if __name__ == "__main__":
    main()
