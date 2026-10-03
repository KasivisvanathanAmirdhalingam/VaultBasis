import io
import os
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

URL = "http://127.0.0.1:8000"


def _open_workspace_when_ready():
    # VaultBasis Edge launcher: present the local workspace automatically once healthy.
    for _ in range(40):
        try:
            with urllib.request.urlopen(URL + "/api/health", timeout=1) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(0.25)
    try:
        if sys.platform == "darwin":
            # On macOS, 'open' from shell is authoritative for opening in default browser from .app
            subprocess.run(["open", URL], check=False)
        elif sys.platform == "win32":
            try:
                os.startfile(URL)
            except Exception:
                webbrowser.open(URL)
        else:
            try:
                subprocess.run(["xdg-open", URL], check=False)
            except Exception:
                webbrowser.open(URL)
    except Exception:
        try:
            webbrowser.open(URL)
        except Exception:
            pass


if __name__ == "__main__":
    # VaultBasis Edge Local Service (MMP-1.1 candidate entry point)
    # Strictly binds to localhost (127.0.0.1).
    opener = threading.Thread(target=_open_workspace_when_ready, daemon=True)
    opener.start()
    # log_config=None prevents uvicorn dictConfig formatter exceptions in frozen GUI executables
    uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None, log_level="info")
