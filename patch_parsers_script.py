import os

def patch_parser(file_path):
    with open(file_path, "r") as f:
        content = f.read()
        
    preflight_code = """
    @classmethod
    def preflight(cls, data_bytes: bytes, source_id: str, file_hash: str, report):
        text = data_bytes.decode("utf-8-sig", errors="replace").strip()
        if not text:
            report.reason_codes.append("INPUT_EMPTY")
            return
            
        import csv, io, json
        from pydantic import ValidationError
        
        if text.startswith("{") or text.startswith("["):
            payload = json.loads(text)
            records = payload if isinstance(payload, list) else payload.get("records", [])
            for idx, rec in enumerate(records, start=1):
                report.rows.read += 1
                basis = rec.get("cost_basis") or rec.get("basis")
                if basis == "0.00" or basis == "0" or basis == 0:
                    report.basis_state.known_zero += 1
                elif basis == "Not Reported":
                    report.basis_state.not_provided += 1
                elif not basis:
                    report.basis_state.unresolved += 1
                else:
                    report.basis_state.present += 1

                try:
                    is_unresolved = (basis is None or str(basis).strip() == "")
                    from schemas.canonical.transaction import CanonicalTransaction
                    tx = CanonicalTransaction(
                        transaction_id=f"{source_id}_rec_{idx}",
                        source_id=source_id,
                        source_file_hash=file_hash,
                        source_row_reference=f"Record:{idx}",
                        transaction_type="DISPOSITION",
                        asset=str(rec.get("asset", "")).upper(),
                        quantity=str(rec.get("quantity")) if rec.get("quantity") else None,
                        proceeds=str(rec.get("proceeds", "")),
                        cost_basis=str(basis) if not is_unresolved else None,
                        acquisition_date=rec.get("acquisition_date") or rec.get("date_acquired"),
                        disposition_date=rec.get("disposition_date") or rec.get("date_sold"),
                        basis_reported_to_irs=str(rec.get("basis_reported_to_irs", "UNSPECIFIED")),
                        is_unresolved=is_unresolved,
                        unresolved_reason="BASIS_UNAVAILABLE" if is_unresolved else None
                    )
                    if tx.is_unresolved:
                        report.rows.unresolved += 1
                    else:
                        report.rows.accepted += 1
                except ValidationError as e:
                    report.rows.rejected += 1
                    report.data_conditions.malformed_values += 1
                    msg = str(e)
                    if "NUMERIC_INVALID" in msg and "NUMERIC_INVALID" not in report.reason_codes:
                        report.reason_codes.append("NUMERIC_INVALID")
            return

        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            report.reason_codes.append("CSV_MALFORMED")
            return
            
        normalized_headers = {h.strip().lower(): h for h in reader.fieldnames if h}
        asset_col = cls._find_col(normalized_headers, ["asset", "property", "symbol", "digital asset"])
        proceeds_col = cls._find_col(normalized_headers, ["proceeds", "box 1f", "box1f", "gross proceeds"])
        disposition_date_col = cls._find_col(normalized_headers, ["date sold", "box 1e", "box1e", "disposition date", "date"])
        
        if not (asset_col and proceeds_col and disposition_date_col):
            report.data_conditions.missing_required_fields += 1
            report.reason_codes.append("SCHEMA_REQUIRED_FIELD_MISSING")
            return

        basis_col = cls._find_col(normalized_headers, ["cost basis", "basis", "box 1g", "box1g"])
        acquisition_date_col = cls._find_col(normalized_headers, ["date acquired", "box 1d", "box1d", "acquisition date"])
        box2_col = cls._find_col(normalized_headers, ["box 2", "box2", "basis reported", "covered"])
        qty_col = cls._find_col(normalized_headers, ["quantity", "units", "amount"])

        from schemas.canonical.transaction import CanonicalTransaction

        for row_idx, raw_row in enumerate(reader, start=1):
            report.rows.read += 1
            if None in raw_row or None in raw_row.values():
                report.rows.rejected += 1
                report.data_conditions.malformed_values += 1
                if "CSV_MALFORMED" not in report.reason_codes:
                    report.reason_codes.append("CSV_MALFORMED")
                continue

            row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k and v is not None}
            
            asset = row.get(asset_col, "").upper()
            proceeds_str = row.get(proceeds_col, "")
            disp_date = row.get(disposition_date_col, "")
            
            if not asset or not proceeds_str:
                report.rows.rejected += 1
                report.data_conditions.missing_required_fields += 1
                if "SCHEMA_REQUIRED_FIELD_MISSING" not in report.reason_codes:
                    report.reason_codes.append("SCHEMA_REQUIRED_FIELD_MISSING")
                continue

            basis_str = row.get(basis_col, "") if basis_col else None
            acq_date = row.get(acquisition_date_col, "") if acquisition_date_col else None
            box2_val = row.get(box2_col, "UNSPECIFIED").upper() if box2_col else "UNSPECIFIED"
            qty_str = row.get(qty_col, "") if qty_col else ""

            is_unresolved = False
            unresolved_reason = None
            if not basis_str or basis_str == "":
                is_unresolved = True
                unresolved_reason = "BASIS_UNAVAILABLE"
                
            if basis_str == "0.00" or basis_str == "0":
                report.basis_state.known_zero += 1
            elif basis_str == "Not Reported":
                report.basis_state.not_provided += 1
                report.rows.unresolved += 1
            elif not basis_str:
                report.basis_state.unresolved += 1
                report.rows.unresolved += 1
            else:
                report.basis_state.present += 1

            if "T" in disp_date and not disp_date.endswith("Z") and ("+" not in disp_date and "-" not in disp_date[10:]):
                report.data_conditions.timezone_ambiguity += 1
                
            if box2_val == "UNSPECIFIED":
                report.data_conditions.basis_reporting_state_unspecified += 1

            try:
                tx = CanonicalTransaction(
                    transaction_id=f"{source_id}_row_{row_idx}",
                    source_id=source_id,
                    source_file_hash=file_hash,
                    source_row_reference=f"Line:{row_idx}",
                    transaction_type="DISPOSITION",
                    asset=asset,
                    quantity=qty_str if qty_str else None,
                    proceeds=proceeds_str if proceeds_str else None,
                    cost_basis=basis_str if basis_str and basis_str != "Not Reported" else None,
                    acquisition_date=acq_date if acq_date and acq_date != "" else None,
                    disposition_date=disp_date,
                    basis_reported_to_irs=box2_val,
                    is_unresolved=is_unresolved,
                    unresolved_reason=unresolved_reason
                )
                if tx.is_unresolved:
                    report.rows.unresolved += 1
                else:
                    report.rows.accepted += 1
            except ValidationError as e:
                report.rows.rejected += 1
                report.data_conditions.malformed_values += 1
                msg = str(e)
                if "NUMERIC_INVALID" in msg and "NUMERIC_INVALID" not in report.reason_codes:
                    report.reason_codes.append("NUMERIC_INVALID")
"""

    if "def preflight" not in content:
        content = content.replace("    @staticmethod\n    def _find_col", preflight_code + "\n    @staticmethod\n    def _find_col")
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Patched {file_path}")

patch_parser("edge/connectors/form1099da_parser.py")
patch_parser("edge/connectors/vaultbasis_csv_parser.py")
patch_parser("edge/connectors/koinly_parser.py")
