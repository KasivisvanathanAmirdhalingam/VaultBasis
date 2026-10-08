import io
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

# Guard against None standard streams in frozen GUI executables (Windows/macOS windowed mode)
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

import uvicorn
from edge.api.app import app


def _open_url(url: str):
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", url], check=False)
        elif sys.platform == "win32":
            try:
                os.startfile(url)
            except Exception:
                webbrowser.open(url)
        else:
            try:
                subprocess.run(["xdg-open", url], check=False)
            except Exception:
                webbrowser.open(url)
    except Exception:
        try:
            webbrowser.open(url)
        except Exception:
            pass


def _open_workspace_when_ready(port: int):
    url = f"http://127.0.0.1:{port}"
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"{url}/api/health", timeout=1) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(0.25)
    _open_url(url)


def _check_existing_vaultbasis_instance(port: int) -> bool:
    """Check if an active VaultBasis Edge instance is already responding on this port."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=0.5) as resp:
            if resp.status == 200:
                data = resp.read().decode("utf-8", errors="ignore")
                return "HEALTHY" in data
    except Exception:
        return False
    return False


def _find_available_port(start_port: int = 8000, max_port: int = 8010) -> int:
    """Find a port that can be bound on 127.0.0.1."""
    for p in range(start_port, max_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", p))
                return p
        except OSError:
            continue
    return start_port


if __name__ == "__main__":
    env_port = os.environ.get("PORT")
    if env_port:
        port = int(env_port)
    else:
        # 1. Single-Instance Check: If VaultBasis is already running on port 8000,
        # bring the existing workspace to the front by opening browser and exit cleanly.
        if _check_existing_vaultbasis_instance(8000):
            _open_url("http://127.0.0.1:8000")
            sys.exit(0)

        # 2. Select port: Default to 8000, fallback to 8001..8010 if occupied by non-VaultBasis process
        port = _find_available_port(8000, 8010)

    # 3. Launch background browser opener (skip in headless test mode)
    if os.environ.get("VAULTBASIS_HEADLESS") != "1":
        opener = threading.Thread(target=_open_workspace_when_ready, args=(port,), daemon=True)
        opener.start()

    # 4. Start Uvicorn daemon
    # log_config=None prevents uvicorn dictConfig formatter exceptions in frozen GUI executables
    uvicorn.run(app, host="127.0.0.1", port=port, log_config=None, log_level="info")
