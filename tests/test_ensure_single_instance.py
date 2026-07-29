import os
import sys
import time
import socket
import subprocess
import pytest
from scripts.ensure_single_instance import main as ensure_single_instance

def is_port_in_use(port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def test_ensure_single_instance_clears_app_process_and_port():
    # 1. Start a background process running app.py
    python_exe = sys.executable
    proc = subprocess.Popen([python_exe, "app.py"], cwd=os.getcwd())
    
    # Wait up to 5 seconds for app.py to bind to port 8000
    started = False
    for _ in range(25):
        if is_port_in_use(8000):
            started = True
            break
        time.sleep(0.2)
        
    assert started, "Failed to start app.py for test setup"
    assert proc.poll() is None, "app.py process should be running"

    # 2. Execute ensure_single_instance()
    ensure_single_instance()

    # Wait up to 3 seconds for teardown to complete
    for _ in range(15):
        if not is_port_in_use(8000) and proc.poll() is not None:
            break
        time.sleep(0.2)

    # 3. Assert port 8000 is freed and app.py process was terminated
    assert proc.poll() is not None, "app.py process should have been terminated by ensure_single_instance"
    assert not is_port_in_use(8000), "Port 8000 should be free after ensure_single_instance"
