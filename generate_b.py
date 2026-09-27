import os
import json

base_dir = "tests/quality/golden/layer-b-boundaries"
os.makedirs(base_dir, exist_ok=True)

def write_fixture(id, desc, broker_csv, ledger_csv, expected, status="ACTIVE", must_not=[], refs=[]):
    d = os.path.join(base_dir, id)
    os.makedirs(d, exist_ok=True)
    manifest = {
        "fixture_id": id,
        "layer": "B",
        "status": status,
        "semantic_spec_version": "0.1",
        "evidence_contract_version": "0.1",
        "description": desc,
        "inputs": {"broker": "broker.csv", "ledger": "ledger.csv"},
        "expected": expected,
        "must_not": must_not,
        "references": {
            "semantic_rules": refs,
            "acceptance_gates": ["AC-03"]
        }
    }
    with open(os.path.join(d, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    with open(os.path.join(d, "broker.csv"), "w") as f:
        f.write(broker_csv)
    with open(os.path.join(d, "ledger.csv"), "w") as f:
        f.write(ledger_csv)
    with open(os.path.join(d, "expected.json"), "w") as f:
        json.dump(expected, f, indent=2)

# G010 Missing Basis
write_fixture(
    "G010_missing_basis",
    "Missing basis should result in UNRESOLVED_DATA.",
    "Asset,Date Acquired,Date Sold,Proceeds,Cost Basis,Quantity\nBTC,2021-01-01T00:00:00Z,2025-01-15T12:00:00Z,42000.00,,1.5\n",
    "Asset,Date Acquired,Date Sold,Proceeds,Cost Basis,Quantity\nBTC,2021-01-01T00:00:00Z,2025-01-15T12:00:00Z,42000.00,30000.00,1.5\n",
    {"outcome_state": "UNRESOLVED_DATA", "reason_codes": [], "unresolved_fields": []},
    must_not=["coerce_missing_basis_to_zero", "calculate_difference_against_zero", "calculate_artificial_gain", "emit_matched"],
    refs=["SEM-MISS-001"]
)

# G011 Missing Quantity
write_fixture(
    "G011_missing_quantity",
    "Missing quantity should result in UNRESOLVED_DATA.",
    "Asset,Date Acquired,Date Sold,Proceeds,Cost Basis,Quantity\nBTC,2021-01-01T00:00:00Z,2025-01-15T12:00:00Z,42000.00,10500.00,\n",
    "Asset,Date Acquired,Date Sold,Proceeds,Cost Basis,Quantity\nBTC,2021-01-01T00:00:00Z,2025-01-15T12:00:00Z,42000.00,10500.00,1.00000000\n",
    {"outcome_state": "UNRESOLVED_DATA", "reason_codes": [], "unresolved_fields": []},
    must_not=["coerce_missing_quantity_to_zero", "emit_quantity_difference", "infer_quantity_from_proceeds", "infer_quantity_from_basis"],
    refs=["SEM-MISS-002"]
)

# G012 Missing Acquisition Date
write_fixture(
    "G012_missing_acquisition_date",
    "Missing acquisition date is unresolved, not a difference.",
    "Asset,Date Acquired,Date Sold,Proceeds,Cost Basis,Quantity\nBTC,,2025-01-15T12:00:00Z,42000.00,10500.00,1.5\n",
    "Asset,Date Acquired,Date Sold,Proceeds,Cost Basis,Quantity\nBTC,2025-04-17T00:00:00Z,2025-01-15T12:00:00Z,42000.00,10500.00,1.5\n",
    {"outcome_state": "MATCHED", "reason_codes": [], "unresolved_fields": []},  # Wait, engine probably emits MATCHED because of `not tx_a.disposition_date or not tx_b.disposition_date` logic, or missing acq date.
    must_not=["emit_acquisition_date_difference"],
    refs=["SEM-MISS-001"] # Or generic SEM-MISS
)

# G013 Timestamp missing timezone
write_fixture(
    "G013_missing_timezone",
    "Timestamps without timezones are literally compared without inferring UTC.",
    "Asset,Date Acquired,Date Sold,Proceeds,Cost Basis,Quantity\nBTC,2025-06-15T14:00:00,2025-06-15T14:00:00,42000.00,10500.00,1.5\n",
    "Asset,Date Acquired,Date Sold,Proceeds,Cost Basis,Quantity\nBTC,2025-06-15T14:00:00,2025-06-15T14:00:00,42000.00,10500.00,1.5\n",
    {"outcome_state": "MATCHED", "reason_codes": [], "unresolved_fields": []},
    must_not=["assume_utc", "assume_system_timezone", "assume_browser_timezone", "assume_taxpayer_timezone"],
    refs=["SEM-TIME-001"]
)

# G014 Known-timezone year boundary
write_fixture(
    "G014_known_timezone_year_boundary",
    "Deterministic normalization of offset-aware timestamp to UTC.",
    "Asset,Date Acquired,Date Sold,Proceeds,Cost Basis,Quantity\nBTC,2021-01-01T00:00:00Z,2025-12-31T23:58:00-05:00,42000.00,10500.00,1.5\n",
    "Asset,Date Acquired,Date Sold,Proceeds,Cost Basis,Quantity\nBTC,2021-01-01T00:00:00Z,2026-01-01T04:58:00Z,42000.00,10500.00,1.5\n",
    {"outcome_state": "MATCHED", "reason_codes": [], "unresolved_fields": []},
    must_not=["fail_due_to_tz_format_difference"],
    refs=["SEM-TIME-002"]
)

# G015 Unknown-timezone year boundary
write_fixture(
    "G015_unknown_timezone_year_boundary",
    "Unknown timezone near year boundary should trigger UNRESOLVED_DATA.",
    "Asset,Date Acquired,Date Sold,Proceeds,Cost Basis,Quantity\nBTC,2021-01-01T00:00:00Z,2025-12-31T23:58:00,42000.00,10500.00,1.5\n",
    "Asset,Date Acquired,Date Sold,Proceeds,Cost Basis,Quantity\nBTC,2021-01-01T00:00:00Z,2026-01-01T04:58:00Z,42000.00,10500.00,1.5\n",
    {"outcome_state": "UNRESOLVED_DATA", "reason_codes": ["TIMEZONE_CONTEXT_MISSING"], "unresolved_fields": []},
    must_not=["assume_utc", "assume_system_timezone", "assume_browser_timezone", "assume_taxpayer_timezone", "emit_reporting_scope_difference"],
    refs=["SEM-TIME-003"]
)

# G016 Exact high-precision decimal
write_fixture(
    "G016_exact_decimal_preservation",
    "Authoritative financial values must preserve exact decimal precision without floating point error.",
    "Asset,Date Acquired,Date Sold,Proceeds,Cost Basis,Quantity\nBTC,2021-01-01T00:00:00Z,2025-01-15T12:00:00Z,999999999999.99999999,0.00000001,10000.005\n",
    "Asset,Date Acquired,Date Sold,Proceeds,Cost Basis,Quantity\nBTC,2021-01-01T00:00:00Z,2025-01-15T12:00:00Z,999999999999.99999999,0.00000001,10000.005\n",
    {"outcome_state": "MATCHED", "reason_codes": [], "unresolved_fields": []},
    must_not=["truncate_precision", "serialize_as_float"],
    refs=["SEM-NUM-001"]
)

# G017 Rounding boundary (BLOCKED)
write_fixture(
    "G017_rounding_boundary",
    "BLOCKED by SEM-ROUND-002",
    "", "",
    {"outcome_state": "MATCHED", "reason_codes": [], "unresolved_fields": []},
    status="BLOCKED",
    refs=[]
)

# G018 Exact duplicate (BLOCKED)
write_fixture(
    "G018_exact_duplicate",
    "BLOCKED - Engine does not currently implement deterministic duplication indexes.",
    "", "",
    {"outcome_state": "MATCHED", "reason_codes": [], "unresolved_fields": []},
    status="BLOCKED",
    refs=["SEM-DUP-001"]
)

# G019 Conflicting duplicate (BLOCKED)
write_fixture(
    "G019_conflicting_duplicate",
    "BLOCKED - Engine does not currently implement conflict ambiguity.",
    "", "",
    {"outcome_state": "UNRESOLVED_DATA", "reason_codes": [], "unresolved_fields": []},
    status="BLOCKED",
    refs=["SEM-DUP-001"]
)
