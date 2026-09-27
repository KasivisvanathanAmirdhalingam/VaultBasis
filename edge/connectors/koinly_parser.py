"""
VaultBasis Edge — Koinly Capital Gains CSV Adapter
Conforms to PRD §6.4 (Decision A: Sole Named Tax-Software Adapter for Preview)
"""

import csv
import io
from decimal import Decimal
from typing import List
from schemas.canonical.transaction import CanonicalTransaction


class KoinlyCapitalGainsParser:
    """
    Parses Koinly Capital Gains Report CSV into CanonicalTransaction objects.
    Enforces exact Decimal arithmetic and preserves missing or ambiguous values.
    """
    SCHEMA_ID = "KOINLY_CAPITAL_GAINS_CSV_V1"

    @classmethod
    def parse(cls, data_bytes: bytes, source_id: str, file_hash: str) -> List[CanonicalTransaction]:
        text = data_bytes.decode("utf-8-sig", errors="replace").strip()
        if not text:
            raise ValueError("Koinly CSV content is empty")

        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise ValueError("Invalid Koinly CSV: Missing header row")

        # Normalize header lookup
        normalized_headers = {h.strip().lower(): h for h in reader.fieldnames if h}

        date_col = cls._find_col(normalized_headers, ["date", "date sold", "date disposed", "transaction date"])
        asset_col = cls._find_col(normalized_headers, ["asset", "currency", "symbol", "coin"])
        proceeds_col = cls._find_col(normalized_headers, ["proceeds", "sale amount", "gross proceeds"])
        cost_basis_col = cls._find_col(normalized_headers, ["cost basis", "cost", "basis", "cost (usd)"])
        
        if not (date_col and asset_col and proceeds_col and cost_basis_col):
            raise ValueError(
                f"Koinly CSV format unrecognized or drifted. Missing required columns. Headers: {list(reader.fieldnames)}"
            )

        amount_col = cls._find_col(normalized_headers, ["amount", "quantity", "units"])
        gain_loss_col = cls._find_col(normalized_headers, ["gain / loss", "gain/loss", "gain", "capital gain"])
        acq_date_col = cls._find_col(normalized_headers, ["date acquired", "acquisition date", "bought date"])

        transactions: List[CanonicalTransaction] = []
        for row_idx, raw_row in enumerate(reader, start=1):
            row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k and v is not None}

            asset = row.get(asset_col, "").upper()
            proceeds_str = row.get(proceeds_col, "")
            cost_basis_str = row.get(cost_basis_col, "")
            disp_date = row.get(date_col, "")

            if not asset or not disp_date:
                continue

            amount_str = row.get(amount_col, "") if amount_col else ""
            gain_loss_str = row.get(gain_loss_col, "") if gain_loss_col else None
            acq_date = row.get(acq_date_col, "") if acq_date_col else None

            # Check for unknown / unresolved basis
            is_unresolved = False
            unresolved_reason = None
            if cost_basis_str == "" or cost_basis_str is None:
                is_unresolved = True
                unresolved_reason = "BASIS_UNAVAILABLE"

            tx = CanonicalTransaction(
                transaction_id=f"{source_id}_row_{row_idx}",
                source_id=source_id,
                source_file_hash=file_hash,
                source_row_reference=f"Row:{row_idx}",
                transaction_type="SALE",
                asset=asset,
                quantity=Decimal(amount_str) if amount_str else None,
                proceeds=Decimal(proceeds_str) if proceeds_str and proceeds_str != "" else None,
                cost_basis=Decimal(cost_basis_str) if cost_basis_str and cost_basis_str != "" else None,
                gain_loss=Decimal(gain_loss_str) if gain_loss_str and gain_loss_str != "" else None,
                acquisition_date=acq_date if acq_date and acq_date != "" else None,
                disposition_date=disp_date,
                basis_reported_to_irs="NO",
                is_unresolved=is_unresolved,
                unresolved_reason=unresolved_reason
            )
            transactions.append(tx)

        if not transactions:
            raise ValueError("Koinly CSV intake produced zero valid transaction rows")

        return transactions

    @staticmethod
    def _find_col(headers: dict, candidates: list) -> str:
        for c in candidates:
            if c in headers:
                return c
        return ""
