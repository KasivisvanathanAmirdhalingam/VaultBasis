import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import math
import time
import tracemalloc
from decimal import Decimal
from schemas.canonical.transaction import CanonicalTransaction
from schemas.canonical.case import CanonicalCase, SourceDocumentMetadata
from edge.assurance.reconciliation_engine import DeterministicReconciliationEngine

def run_workload(n_broker: int):
    # Scale proportionally based on PERF-01 ratios (91% match, 5% pdiff, 3% bdiff, 1% b_orphan, 1% l_orphan)
    n_match = int(n_broker * 0.91)
    n_pdiff = int(n_broker * 0.05)
    n_bdiff = int(n_broker * 0.03)
    n_b_orphan = n_broker - n_match - n_pdiff - n_bdiff
    n_l_orphan = n_b_orphan

    all_transactions = []
    dummy_hash_a = "a" * 64
    dummy_hash_b = "b" * 64

    # 1. Matches
    for i in range(n_match):
        asset = f"ASSET_{i}"
        proceeds = Decimal("100.00") + Decimal(f"{i % 100}.50")
        basis = Decimal("50.00") + Decimal(f"{i % 100}.25")
        month = (i % 12) + 1
        day = (i % 28) + 1
        disp_date = f"2025-{month:02d}-{day:02d}"

        all_transactions.append(CanonicalTransaction(
            transaction_id=f"broker_match_{i}",
            source_id="SRC-BROKER-01",
            source_file_hash=dummy_hash_a,
            source_row_reference=f"Line:{i + 2}",
            transaction_type="SALE",
            asset=asset,
            proceeds=proceeds,
            cost_basis=basis,
            acquisition_date="2024-01-01",
            disposition_date=disp_date,
            basis_reported_to_irs="YES"
        ))
        all_transactions.append(CanonicalTransaction(
            transaction_id=f"ledger_match_{i}",
            source_id="SRC-LEDGER-01",
            source_file_hash=dummy_hash_b,
            source_row_reference=f"Line:{i + 2}",
            transaction_type="SALE",
            asset=asset,
            proceeds=proceeds,
            cost_basis=basis,
            acquisition_date="2024-01-01",
            disposition_date=disp_date,
            basis_reported_to_irs="YES"
        ))

    # 2. Proceeds Diff
    for i in range(n_pdiff):
        idx = n_match + i
        asset = f"PDIFF_{i}"
        month = (i % 12) + 1
        day = (i % 28) + 1
        disp_date = f"2025-{month:02d}-{day:02d}"
        all_transactions.append(CanonicalTransaction(
            transaction_id=f"broker_pdiff_{i}",
            source_id="SRC-BROKER-01",
            source_file_hash=dummy_hash_a,
            source_row_reference=f"Line:{idx + 2}",
            transaction_type="SALE",
            asset=asset,
            proceeds=Decimal("200.00"),
            cost_basis=Decimal("100.00"),
            acquisition_date="2024-01-01",
            disposition_date=disp_date,
            basis_reported_to_irs="YES"
        ))
        all_transactions.append(CanonicalTransaction(
            transaction_id=f"ledger_pdiff_{i}",
            source_id="SRC-LEDGER-01",
            source_file_hash=dummy_hash_b,
            source_row_reference=f"Line:{idx + 2}",
            transaction_type="SALE",
            asset=asset,
            proceeds=Decimal("210.00"),
            cost_basis=Decimal("100.00"),
            acquisition_date="2024-01-01",
            disposition_date=disp_date,
            basis_reported_to_irs="YES"
        ))

    # 3. Basis Diff
    for i in range(n_bdiff):
        idx = n_match + n_pdiff + i
        asset = f"BDIFF_{i}"
        month = (i % 12) + 1
        day = (i % 28) + 1
        disp_date = f"2025-{month:02d}-{day:02d}"
        all_transactions.append(CanonicalTransaction(
            transaction_id=f"broker_bdiff_{i}",
            source_id="SRC-BROKER-01",
            source_file_hash=dummy_hash_a,
            source_row_reference=f"Line:{idx + 2}",
            transaction_type="SALE",
            asset=asset,
            proceeds=Decimal("300.00"),
            cost_basis=Decimal("150.00"),
            acquisition_date="2024-01-01",
            disposition_date=disp_date,
            basis_reported_to_irs="YES"
        ))
        all_transactions.append(CanonicalTransaction(
            transaction_id=f"ledger_bdiff_{i}",
            source_id="SRC-LEDGER-01",
            source_file_hash=dummy_hash_b,
            source_row_reference=f"Line:{idx + 2}",
            transaction_type="SALE",
            asset=asset,
            proceeds=Decimal("300.00"),
            cost_basis=Decimal("155.00"),
            acquisition_date="2024-01-01",
            disposition_date=disp_date,
            basis_reported_to_irs="YES"
        ))

    # 4. Broker Orphans
    for i in range(n_b_orphan):
        idx = n_match + n_pdiff + n_bdiff + i
        asset = f"BORPHAN_{i}"
        month = (i % 12) + 1
        day = (i % 28) + 1
        disp_date = f"2025-{month:02d}-{day:02d}"
        all_transactions.append(CanonicalTransaction(
            transaction_id=f"broker_orphan_{i}",
            source_id="SRC-BROKER-01",
            source_file_hash=dummy_hash_a,
            source_row_reference=f"Line:{idx + 2}",
            transaction_type="SALE",
            asset=asset,
            proceeds=Decimal("400.00"),
            cost_basis=Decimal("200.00"),
            acquisition_date="2024-01-01",
            disposition_date=disp_date,
            basis_reported_to_irs="YES"
        ))

    # 5. Ledger Orphans
    for i in range(n_l_orphan):
        idx = n_match + n_pdiff + n_bdiff + i
        asset = f"LORPHAN_{i}"
        month = (i % 12) + 1
        day = (i % 28) + 1
        disp_date = f"2025-{month:02d}-{day:02d}"
        all_transactions.append(CanonicalTransaction(
            transaction_id=f"ledger_orphan_{i}",
            source_id="SRC-LEDGER-01",
            source_file_hash=dummy_hash_b,
            source_row_reference=f"Line:{idx + 2}",
            transaction_type="SALE",
            asset=asset,
            proceeds=Decimal("500.00"),
            cost_basis=Decimal("250.00"),
            acquisition_date="2024-01-01",
            disposition_date=disp_date,
            basis_reported_to_irs="YES"
        ))

    sources = {
        "SRC-BROKER-01": SourceDocumentMetadata(
            source_id="SRC-BROKER-01",
            filename="broker.csv",
            sha256_hash=dummy_hash_a,
            byte_size=1024,
            schema_id="IRS_1099DA_CSV_V1",
            row_count=n_broker,
            ingested_at="2026-10-09T12:00:00Z"
        ),
        "SRC-LEDGER-01": SourceDocumentMetadata(
            source_id="SRC-LEDGER-01",
            filename="ledger.csv",
            sha256_hash=dummy_hash_b,
            byte_size=1024,
            schema_id="GENERIC_TAX_LEDGER_CSV_V1",
            row_count=n_broker,
            ingested_at="2026-10-09T12:00:00Z"
        )
    }

    case = CanonicalCase(
        case_id=f"CASE-PERF-{n_broker}",
        client_reference="Scaling Client",
        tax_year=2025,
        jurisdiction="US",
        sources=sources,
        transactions=all_transactions,
        created_at="2026-10-09T12:00:00Z",
        updated_at="2026-10-09T12:00:00Z"
    )

    tracemalloc.start()
    t_start = time.perf_counter()
    result = DeterministicReconciliationEngine.reconcile_case(case)
    t_end = time.perf_counter()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    rec_time = t_end - t_start
    peak_mb = peak_mem / (1024 * 1024)

    assert len(result.agreed_records) == n_match
    assert len(result.material_differences) == (n_pdiff + n_bdiff + n_b_orphan + n_l_orphan)

    return rec_time, peak_mb

if __name__ == "__main__":
    test_sizes = [1000, 2500, 5000, 10000]
    results = []

    print(f"{'N (Broker)':<12} | {'Time (s)':<12} | {'Time/N (ms)':<14} | {'Time/(N log N)':<16} | {'Time/N^2 (µs)':<14} | {'Peak RAM (MB)':<12}")
    print("-" * 90)

    for n in test_sizes:
        rec_time, peak_mb = run_workload(n)
        t_per_n = (rec_time / n) * 1000
        t_per_nlogn = (rec_time / (n * math.log2(n))) * 1000
        t_per_n2 = (rec_time / (n * n)) * 1_000_000
        results.append((n, rec_time, t_per_n, t_per_nlogn, t_per_n2, peak_mb))
        print(f"{n:<12} | {rec_time:<12.4f} | {t_per_n:<14.4f} | {t_per_nlogn:<16.6f} | {t_per_n2:<14.4f} | {peak_mb:<12.2f}")

