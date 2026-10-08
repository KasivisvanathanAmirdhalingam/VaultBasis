# VaultBasis Consistent Online Backup & Verified Restore Runbook
**Document ID:** VB-RUN-DATA-001  
**Classification:** OPERATIONAL  
**Authority:** Persistence & Storage Lead  
**Status:** IMPLEMENTATION_ALIGNED  
**Applies To:** VaultBasis Edge v1.5.0 Local Persistence Layer  
**Last Reviewed:** 2026-10-08  

---

## 1. Hot Backup Procedure (Zero Interruption)

Because SQLite operates in WAL (`Write-Ahead Logging`) mode, hot backups can be safely taken while the application is active without locking readers or writers.

```python
import sqlite3
from pathlib import Path
import datetime

def create_online_backup(db_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    backup_path = backup_dir / f"vaultbasis_backup_{timestamp}.db"
    
    # Open source connection and target backup connection
    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(backup_path))
    
    with dst:
        src.backup(dst, pages=100, sleep=0.01)
        
    dst.close()
    src.close()
    return backup_path
```

---

## 2. Verified Restore & Database Integrity Check

```python
import sqlite3
from pathlib import Path

def restore_and_verify_database(backup_path: Path, target_db_path: Path):
    assert backup_path.exists(), f"Backup file {backup_path} not found"
    
    # 1. Verify backup file integrity before restore
    test_conn = sqlite3.connect(str(backup_path))
    cursor = test_conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    result = cursor.fetchone()[0]
    assert result == "ok", f"Backup integrity check failed: {result}"
    test_conn.close()
    
    # 2. If target DB exists, archive it as a pre-restore safety copy
    if target_db_path.exists():
        safety_path = target_db_path.with_suffix(".pre_restore.bak")
        target_db_path.replace(safety_path)
        
    # 3. Restore backup to target location
    src = sqlite3.connect(str(backup_path))
    dst = sqlite3.connect(str(target_db_path))
    with dst:
        src.backup(dst)
    dst.close()
    src.close()
```

---

## 3. Post-Restore Health Checks

After restoring:
1. Verify schema version: `PRAGMA user_version;` (must return `6`).
2. Verify table row counts against pre-backup audit logs.
3. Validate existing Ed25519 installation key matches the restored public key in `cases` table.
