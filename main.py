import threading
import urllib.request
import webbrowser

import uvicorn
from edge.api.app import app

URL = "http://127.0.0.1:8000"


def _open_workspace_when_ready():
    # RC3 packaging: present the workspace automatically once healthy.
    # Reconciliation semantics untouched; browser open is launcher behavior.
    for _ in range(40):
        try:
            urllib.request.urlopen(URL + "/api/health", timeout=1)
            break
        except Exception:
            import time
            time.sleep(0.25)
    try:
        webbrowser.open(URL)
    except Exception:
        pass


if __name__ == "__main__":
    # VaultBasis Edge Local Service (RC3 candidate entry point)
    # Strictly binds to localhost (127.0.0.1).
    opener = threading.Thread(target=_open_workspace_when_ready, daemon=True)
    opener.start()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
