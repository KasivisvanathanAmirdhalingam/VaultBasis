# MMP-2 Forward Compatibility Hooks for Strategic Digital Asset Storage

> **Specification Ref:** `MMP2-VLT-001`, `MMP2-VLT-002`  
> **Status:** Commercial Monetization Parked for N+1th MMP; Architecture Hooks Active

---

## 1. Scope & Strategy Clarification

1. **Strategic Parking:** Commercial monetization, storage quota billing, and multi-tenant synchronization of the **VaultBasis Evidence Vault** are deliberately parked for the N+1th release cycle to ensure 100% focus on Form 1099-DA reconciliation and intelligence triage.
2. **Evidence Vault != Crypto Custody:** VaultBasis stores professional digital-asset *evidence, statements, workpapers, and receipts*. It **NEVER** holds cryptocurrency custody or private keys.
3. **Architecture Decoupling:** MMP-2 implements clean storage abstraction interfaces so that transitioning to an extended encrypted multi-year storage package requires zero core refactoring.

---

## 2. Storage Provider Abstraction Interface

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional

class EvidenceStorageProvider(ABC):
    """
    Abstract interface decoupling VaultBasis core from the physical storage backend.
    """
    
    @abstractmethod
    def put_blob(self, stream: BinaryIO, sha256_hash: str, metadata: Dict[str, str]) -> str:
        """Stores evidence blob content-addressed by SHA-256."""
        pass

    @abstractmethod
    def get_blob(self, sha256_hash: str) -> Optional[BinaryIO]:
        """Retrieves raw evidence stream."""
        pass

    @abstractmethod
    def blob_exists(self, sha256_hash: str) -> bool:
        """Checks presence of content-addressed blob."""
        pass

    @abstractmethod
    def verify_digest(self, sha256_hash: str) -> bool:
        """Verifies physical file matches its content hash."""
        pass
```

---

## 3. Storage Provider Evolution Roadmap

```
CURRENT (MMP-1.x / MMP-2.0):
LocalFilesystemEvidenceStore
└── Blobs saved under data/evidence/<sha256>

FUTURE (N+1th Release Cycle — Paid Evidence Vault Package):
├── EncryptedLocalVaultStore (AES-256-GCM with customer-held passphrase)
├── EnterpriseNASVaultStore (SMB/NFS on-prem network storage)
└── CustomerManagedObjectStore (S3/Azure/GCS endpoint configured by firm IT)
```
