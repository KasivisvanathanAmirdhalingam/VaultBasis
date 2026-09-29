import sys
import pytest
from pathlib import Path

repo_root = Path(__file__).resolve().parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """
    Give every test its own SQLite database.

    db_store in edge.api.app is constructed at module import time, so setting
    VAULTBASIS_DB_FILE in the environment is too late — the global instance
    already points at the default path. We monkeypatch app.db_store directly
    to ensure the running application uses the isolated test database.
    """
    db_file = tmp_path / "vaultbasis_test.db"
    monkeypatch.setenv("VAULTBASIS_DB_FILE", str(db_file))

    from edge.storage.sqlite_store import SQLiteStore
    import edge.api.app as app_module
    monkeypatch.setattr(app_module, "db_store", SQLiteStore(db_file))
