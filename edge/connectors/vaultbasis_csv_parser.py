"""
VaultBasis Edge — Generic Reconciliation CSV Fallback Adapter
Conforms to PRD §6.4 (Decision A: Fallback for design partners unable to supply Koinly output)
"""

import csv
import io
from decimal import Decimal
from typing import List
from schemas.canonical.transaction import CanonicalTransaction


class VaultBasisCSVParser:
    """
    Parses generic VaultBasis Reconciliation CSV v0.1:
    Header: date,asset,quantity,proceeds,cost_basis,date_acquired,source_ref
    """
    SCHEMA_ID = "VAULTBASIS_RECONCILIATION_CSV_V01"

    @classmethod
    def parse(cls, data_bytes: bytes, source_id: str, file_hash: str) -> List[CanonicalTransaction]:
        text = data_bytes.decode("utf-8-sig", errors="replace").strip()
        if not text:
            raise ValueError("CSV file content is empty")

        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise ValueError("Invalid CSV: Missing header row")

        normalized_headers = {h.strip().lower(): h for h in reader.fieldnames if h}
        required = ["date", "asset", "proceeds"]
        for req in required:
            if req not in normalized_headers:
                raise ValueError(f"VaultBasis CSV fallback missing mandatory column '{req}'")

        transactions: List[CanonicalTransaction] = []
        for row_idx, raw_row in enumerate(reader, start=1):
            row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k and v is not None}
            asset = row.get("asset", "").upper()
            proceeds_str = row.get("proceeds", "")
            disp_date = row.get("date", "")
            if not asset or not disp_date:
                continue

            basis_str = row.get("cost_basis")
            acq_date = row.get("date_acquired")
            qty_str = row.get("quantity", "1.0")
            source_ref = row.get("source_ref", f"Row:{row_idx}")

            is_unresolved = (basis_str is None or basis_str == "")
            unresolved_reason = "BASIS_UNAVAILABLE" if is_unresolved else None

            tx = CanonicalTransaction(
                transaction_id=f"{source_id}_row_{row_idx}",
                source_id=source_id,
                source_file_hash=file_hash,
                source_row_reference=source_ref,
                transaction_type="SALE",
                asset=asset,
                quantity=Decimal(qty_str) if qty_str else Decimal("1.0"),
                proceeds=Decimal(proceeds_str) if proceeds_str else None,
                cost_basis=Decimal(basis_str) if not is_unresolved else None,
                acquisition_date=acq_date if acq_date and acq_date != "" else None,
                disposition_date=disp_date,
                is_unresolved=is_unresolved,
                unresolved_reason=unresolved_reason
            )
            transactions.append(tx)

        if not transactions:
            raise ValueError("Intake produced zero valid transaction rows")

        return transactions
