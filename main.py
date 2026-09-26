import uvicorn
from edge.api.app import app

if __name__ == "__main__":
    # VaultBasis Edge Local Daemon
    # Strictly binds to localhost (127.0.0.1) to enforce Zero-Egress isolation.
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
