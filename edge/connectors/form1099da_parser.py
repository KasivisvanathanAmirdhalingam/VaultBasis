"""
VaultBasis Edge — Form 1099-DA Intake Parser
Conforms to PRD §14.1 (IRS Form Semantics), §14.2 (2025 vs 2026 Reporting Scope)
"""

import csv
import io
import json
from decimal import Decimal
from typing import List
from schemas.canonical.transaction import CanonicalTransaction


class Form1099DAParser:
    """
    Parses Form 1099-DA representations into CanonicalTransaction objects.
    Preserves unknown acquisition dates and basis according to 2025/2026 transition rules.
    """
    SCHEMA_ID = "IRS_1099DA_2025_PREVIEW"

    @classmethod
    def parse(cls, data_bytes: bytes, source_id: str, file_hash: str) -> List[CanonicalTransaction]:
        text = data_bytes.decode("utf-8-sig", errors="replace").strip()
        if not text:
            raise ValueError("1099-DA file content is empty")

        # Try parsing as JSON if text begins with '{' or '['
        if text.startswith("{") or text.startswith("["):
            return cls._parse_json(text, source_id, file_hash)
        else:
            return cls._parse_csv(text, source_id, file_hash)

    @classmethod
    def _parse_csv(cls, text: str, source_id: str, file_hash: str) -> List[CanonicalTransaction]:
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise ValueError("Invalid 1099-DA CSV: Missing header row")

        # Normalize header keys to lowercase stripped
        normalized_headers = {h.strip().lower(): h for h in reader.fieldnames if h}
        
        # Determine required columns
        # Flexible mapping for Box names or friendly labels
        asset_col = cls._find_col(normalized_headers, ["asset", "property", "symbol", "digital asset"])
        proceeds_col = cls._find_col(normalized_headers, ["proceeds", "box 1f", "box1f", "gross proceeds"])
        disposition_date_col = cls._find_col(normalized_headers, ["date sold", "box 1e", "box1e", "disposition date", "date"])
        
        if not (asset_col and proceeds_col and disposition_date_col):
            raise ValueError(
                f"Invalid 1099-DA CSV: Required fields missing. Found headers: {list(reader.fieldnames)}"
            )

        basis_col = cls._find_col(normalized_headers, ["cost basis", "basis", "box 1g", "box1g"])
        acquisition_date_col = cls._find_col(normalized_headers, ["date acquired", "box 1d", "box1d", "acquisition date"])
        box2_col = cls._find_col(normalized_headers, ["box 2", "box2", "basis reported", "covered"])
        qty_col = cls._find_col(normalized_headers, ["quantity", "units", "amount"])

        transactions: List[CanonicalTransaction] = []
        for row_idx, raw_row in enumerate(reader, start=1):
            row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k and v is not None}
            
            asset = row.get(asset_col, "").upper()
            proceeds_str = row.get(proceeds_col, "")
            disp_date = row.get(disposition_date_col, "")
            
            if not asset or not proceeds_str:
                continue

            basis_str = row.get(basis_col, "") if basis_col else None
            acq_date = row.get(acquisition_date_col, "") if acquisition_date_col else None
            box2_val = row.get(box2_col, "UNSPECIFIED").upper() if box2_col else "UNSPECIFIED"
            qty_str = row.get(qty_col, "1.0") if qty_col else "1.0"

            is_unresolved = False
            unresolved_reason = None
            if not basis_str or basis_str == "":
                is_unresolved = True
                unresolved_reason = "BASIS_UNAVAILABLE"

            tx = CanonicalTransaction(
                transaction_id=f"{source_id}_row_{row_idx}",
                source_id=source_id,
                source_file_hash=file_hash,
                source_row_reference=f"Line:{row_idx}",
                transaction_type="DISPOSITION",
                asset=asset,
                quantity=Decimal(qty_str) if qty_str else Decimal("1.0"),
                proceeds=Decimal(proceeds_str) if proceeds_str else None,
                cost_basis=Decimal(basis_str) if basis_str and basis_str != "" else None,
                acquisition_date=acq_date if acq_date and acq_date != "" else None,
                disposition_date=disp_date,
                basis_reported_to_irs=box2_val,
                is_unresolved=is_unresolved,
                unresolved_reason=unresolved_reason
            )
            transactions.append(tx)

        if not transactions:
            raise ValueError("1099-DA intake produced zero valid transaction rows")

        return transactions

    @classmethod
    def _parse_json(cls, text: str, source_id: str, file_hash: str) -> List[CanonicalTransaction]:
        payload = json.loads(text)
        records = payload if isinstance(payload, list) else payload.get("records", [])
        transactions = []
        for idx, rec in enumerate(records, start=1):
            basis = rec.get("cost_basis") or rec.get("basis")
            is_unresolved = (basis is None or str(basis).strip() == "")
            tx = CanonicalTransaction(
                transaction_id=f"{source_id}_rec_{idx}",
                source_id=source_id,
                source_file_hash=file_hash,
                source_row_reference=f"Record:{idx}",
                transaction_type="DISPOSITION",
                asset=str(rec["asset"]).upper(),
                quantity=Decimal(str(rec.get("quantity", "1.0"))),
                proceeds=Decimal(str(rec["proceeds"])),
                cost_basis=Decimal(str(basis)) if not is_unresolved else None,
                acquisition_date=rec.get("acquisition_date") or rec.get("date_acquired"),
                disposition_date=rec.get("disposition_date") or rec.get("date_sold"),
                basis_reported_to_irs=str(rec.get("basis_reported_to_irs", "UNSPECIFIED")),
                is_unresolved=is_unresolved,
                unresolved_reason="BASIS_UNAVAILABLE" if is_unresolved else None
            )
            transactions.append(tx)
        return transactions

    @staticmethod
    def _find_col(headers: dict, candidates: list) -> str:
        for c in candidates:
            if c in headers:
                return c
        return ""
