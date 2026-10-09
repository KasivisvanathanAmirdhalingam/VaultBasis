# VaultBasis Edge & Web: Open Source License Ledger & Software Bill of Materials (SBOM)

**Document ID:** `MMP15-OSS-LEDGER-001`  
**Control Reference:** `LEGAL-007` (MMP15-LEGAL-RISK-QUAL-001)  
**Evaluated Artifacts:** Candidate 11 macOS arm64 (`dist/VaultBasis.app`) & VaultBasis Public Web (`dist/public-web`)  
**Audit Status:** `PASS — CLOSED`  
**Copyleft Contamination Finding:** `NONE` (100% Permissive Open-Source Licenses: MIT, BSD-2/3, Apache 2.0, Public Domain)

---

## 1. Packaged Desktop Binary (VaultBasis Edge) Dependencies

The following table inventories all runtime components bundled into the distributed desktop executable:

| Component / Package | Distribution Status | Version | License | Upstream Source / Homepage | Notice Required? | Compliance Disposition |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **fastapi** | Bundled Runtime | `0.115.x` | **MIT** | https://github.com/fastapi/fastapi | Yes | PASS — Notice Included |
| **pydantic** | Bundled Runtime | `2.13.3` | **MIT** | https://github.com/pydantic/pydantic | Yes | PASS — Notice Included |
| **cryptography** | Bundled Runtime | `50.0.0` | **Apache-2.0 / BSD-3-Clause** | https://github.com/pyca/cryptography | Yes | PASS — Dual License Verified |
| **uvicorn** | Bundled Runtime | `0.34.x` | **BSD-3-Clause** | https://github.com/encode/uvicorn | Yes | PASS — Notice Included |
| **starlette** | Bundled Runtime | `0.45.x` | **BSD-3-Clause** | https://github.com/encode/starlette | Yes | PASS — Notice Included |
| **jsonschema** | Bundled Runtime | `4.23.x` | **MIT** | https://github.com/python-jsonschema/jsonschema | Yes | PASS — Notice Included |
| **attrs** | Bundled Runtime | `24.3.0` | **MIT** | https://github.com/python-attrs/attrs | Yes | PASS — Notice Included |
| **werkzeug** | Bundled Runtime | `3.1.3` | **BSD-3-Clause** | https://palletsprojects.com/p/werkzeug/ | Yes | PASS — Notice Included |
| **markupsafe** | Bundled Runtime | `3.0.2` | **BSD-3-Clause** | https://palletsprojects.com/p/markupsafe/ | Yes | PASS — Notice Included |
| **python-dateutil** | Bundled Runtime | `2.9.0` | **Apache-2.0 / BSD-3-Clause** | https://github.com/dateutil/dateutil | Yes | PASS — Notice Included |
| **python-multipart** | Bundled Runtime | `0.0.20` | **Apache-2.0** | https://github.com/Kludex/python-multipart | Yes | PASS — Notice Included |
| **websockets** | Bundled Runtime | `16.0` | **BSD-3-Clause** | https://github.com/python-websockets/websockets | Yes | PASS — Notice Included |
| **email_validator** | Bundled Runtime | `2.3.0` | **MIT** | https://github.com/JoshData/python-email-validator | Yes | PASS — Notice Included |
| **importlib_metadata** | Bundled Runtime | `8.7.1` | **Apache-2.0** | https://github.com/python/importlib_metadata | Yes | PASS — Notice Included |
| **tinyaes** | Bundled Runtime | `1.0.x` | **The Unlicense / Public Domain** | https://github.com/kokke/tiny-AES-c | No | PASS — Public Domain |
| **PyInstaller Bootloader** | Packaging Engine | `6.11.x` | **GPL-2.0-with-exception** | https://www.pyinstaller.org | No | PASS — Express commercial exemption |

---

## 2. Public Web, Edge Dashboard & Verifier Frontend Dependencies

The following table inventories all frontend and web server runtime libraries:

| Library / Asset | Context | License | Upstream Origin | Compliance Disposition |
| :--- | :--- | :--- | :--- | :--- |
| **Outfit Font** | Web Typography | **SIL Open Font License 1.1** | Google Fonts / Onsen UI | PASS — OFL Compatible |
| **Plus Jakarta Sans** | Web Typography | **SIL Open Font License 1.1** | Google Fonts / Tokotype | PASS — OFL Compatible |
| **JetBrains Mono** | Code Typography | **SIL Open Font License 1.1** | JetBrains | PASS — OFL Compatible |
| **express** | Web Server | **MIT** | https://github.com/expressjs/express | PASS — Permissive |
| **nodemailer** | Delivery Mailer | **MIT** | https://github.com/nodemailer/nodemailer | PASS — Permissive |
| **jose** | JWT/JWS (Verifier) | **MIT** | https://github.com/panva/jose | PASS — Permissive |
| **zod** | Validation Schema | **MIT** | https://github.com/colinhacks/zod | PASS — Permissive |

---

## 3. Copyleft & Viral License Analysis

- **AGPL-3.0 / GPL-3.0 Check:** `0` matching dependencies identified across the entire dependency graph.
- **PyInstaller Special Exception:** PyInstaller is licensed under GPLv2 with a special linking exception that explicitly allows packaging and distributing commercial proprietary closed-source applications without requiring the source code to be released under GPL.
- **Verdict:** The VaultBasis commercial software distribution is clean of copyleft contamination and satisfies commercial closed-source licensing standards.
