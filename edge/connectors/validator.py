"""
VaultBasis Edge — Unified Intake Dispatcher and Fail-Closed Validator
Conforms to PRD §41 (AC-01 and AC-04)
"""

from datetime import datetime, timezone
from typing import List, Tuple
from schemas.canonical.case import SourceDocumentMetadata
from schemas.canonical.transaction import CanonicalTransaction
from edge.connectors.form1099da_parser import Form1099DAParser
from edge.connectors.hasher import hash_source_bytes
from edge.connectors.koinly_parser import KoinlyCapitalGainsParser
from edge.connectors.vaultbasis_csv_parser import VaultBasisCSVParser


class IntakeDispatcher:
    """
    Validates uploaded source documents, computes cryptographic hashes,
    detects schema type, and parses into canonical transaction representations.
    Fails closed on malformed or unrecognized formats.
    """

    @classmethod
    def ingest_document(
        cls,
        data_bytes: bytes,
        filename: str,
        source_id: str,
        declared_schema: str = "AUTO"
    ) -> Tuple[SourceDocumentMetadata, List[CanonicalTransaction]]:
        if not data_bytes or len(data_bytes) == 0:
            raise ValueError(f"Cannot ingest empty document: '{filename}'")

        file_hash, byte_size = hash_source_bytes(data_bytes)
        now_utc = datetime.now(timezone.utc).isoformat()

        # Schema detection
        detected_schema = declared_schema
        if declared_schema == "AUTO":
            detected_schema = cls._detect_schema(data_bytes, filename)

        # Dispatch to appropriate parser
        if detected_schema == Form1099DAParser.SCHEMA_ID:
            transactions = Form1099DAParser.parse(data_bytes, source_id, file_hash)
        elif detected_schema == KoinlyCapitalGainsParser.SCHEMA_ID:
            transactions = KoinlyCapitalGainsParser.parse(data_bytes, source_id, file_hash)
        elif detected_schema == VaultBasisCSVParser.SCHEMA_ID:
            transactions = VaultBasisCSVParser.parse(data_bytes, source_id, file_hash)
        else:
            raise ValueError(f"Unsupported or unrecognized input document schema: '{detected_schema}'")

        meta = SourceDocumentMetadata(
            source_id=source_id,
            filename=filename,
            sha256_hash=file_hash,
            byte_size=byte_size,
            schema_id=detected_schema,
            row_count=len(transactions),
            ingested_at=now_utc
        )

        return meta, transactions

    @staticmethod
    def _detect_schema(data_bytes: bytes, filename: str) -> str:
        sample = data_bytes[:2048].decode("utf-8-sig", errors="replace").lower()
        if (
            "1099" in filename.lower()
            or "1099-da" in sample
            or "box 1f" in sample
            or "gross proceeds" in sample
            or "box 2" in sample
            or "date sold" in sample
            or "property" in sample
        ):
            return Form1099DAParser.SCHEMA_ID
        elif "koinly" in filename.lower() or "gain / loss" in sample or "capital gain" in sample:
            return KoinlyCapitalGainsParser.SCHEMA_ID
        elif "source_ref" in sample or ("date" in sample and "asset" in sample and "proceeds" in sample):
            return VaultBasisCSVParser.SCHEMA_ID
        else:
            if filename.endswith(".csv"):
                return VaultBasisCSVParser.SCHEMA_ID
            raise ValueError(f"Unable to auto-detect schema for file '{filename}'. Format unrecognized.")
