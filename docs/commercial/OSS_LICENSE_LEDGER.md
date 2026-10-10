# VaultBasis Edge & Web: Open Source License Ledger & Software Bill of Materials (SBOM)

**Document ID:** `MMP15-OSS-LEDGER-001`  
**Control Reference:** `LEGAL-007` (MMP15-LEGAL-RISK-QUAL-001)  
**Evaluated Artifacts:** Candidate 12 macOS arm64 (`dist/VaultBasis.app`) & VaultBasis Public Web (`dist/public-web`)  
**Audit Status:** `PRE-SIGN OSS QUALIFICATION PASS`  
**Final Closure:** `PENDING EXACT SIGNED DISTRIBUTION ARTIFACT`  
**Proprietary-Source Disclosure Obligation:** No identified distributed component in the evaluated scope was found to impose an obligation to license VaultBasis proprietary application source code under a reciprocal/copyleft license, subject to the applicable license terms and final artifact verification.

---

## 1. Packaged Desktop Binary (VaultBasis Edge) Component Inventory

The following table inventories all direct, transitive, and native runtime components bundled into the distributed desktop executable layout (`dist/VaultBasis.app`):

| Component / Library | Component Type | Exact Artifact Version | License | Upstream Origin | Notice Obligation | Compliance Disposition |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- |
| **fastapi** | Direct Runtime | `0.129.0` | **MIT** | https://github.com/fastapi/fastapi | Yes | PASS — Notice preserved |
| **pydantic** | Direct Runtime | `2.13.3` | **MIT** | https://github.com/pydantic/pydantic | Yes | PASS — Notice preserved |
| **pydantic_core** | Transitive Runtime | `2.43.3` | **MIT** | https://github.com/pydantic/pydantic-core | Yes | PASS — Notice preserved |
| **cryptography** | Direct Runtime | `50.0.0` | **Apache-2.0 / BSD-3-Clause** | https://github.com/pyca/cryptography | Yes | PASS — Dual license verified |
| **uvicorn** | Direct Runtime | `0.40.0` | **BSD-3-Clause** | https://github.com/encode/uvicorn | Yes | PASS — Notice preserved |
| **starlette** | Direct Runtime | `0.52.1` | **BSD-3-Clause** | https://github.com/encode/starlette | Yes | PASS — Notice preserved |
| **jsonschema** | Direct Runtime | `4.25.1` | **MIT** | https://github.com/python-jsonschema/jsonschema | Yes | PASS — Notice preserved |
| **attrs** | Direct Runtime | `24.3.0` | **MIT** | https://github.com/python-attrs/attrs | Yes | PASS — Notice preserved |
| **werkzeug** | Direct Runtime | `3.1.3` | **BSD-3-Clause** | https://palletsprojects.com/p/werkzeug/ | Yes | PASS — Notice preserved |
| **markupsafe** | Direct Runtime | `3.0.2` | **BSD-3-Clause** | https://palletsprojects.com/p/markupsafe/ | Yes | PASS — Notice preserved |
| **python-dateutil** | Direct Runtime | `2.9.0.post0` | **Apache-2.0 / BSD-3-Clause** | https://github.com/dateutil/dateutil | Yes | PASS — Notice preserved |
| **python-multipart** | Direct Runtime | `0.0.22` | **Apache-2.0** | https://github.com/Kludex/python-multipart | Yes | PASS — Notice preserved |
| **websockets** | Direct Runtime | `16.0` | **BSD-3-Clause** | https://github.com/python-websockets/websockets | Yes | PASS — Notice preserved |
| **email_validator** | Direct Runtime | `2.3.0` | **MIT** | https://github.com/JoshData/python-email-validator | Yes | PASS — Notice preserved |
| **importlib_metadata** | Direct Runtime | `8.7.1` | **Apache-2.0** | https://github.com/python/importlib_metadata | Yes | PASS — Notice preserved |
| **tinyaes** | Direct Runtime | `1.1.2` | **The Unlicense / Public Domain** | https://github.com/kokke/tiny-AES-c | No | PASS — Public Domain |
| **bcrypt** | Transitive Runtime | `4.3.0` | **Apache-2.0** | https://github.com/pyca/bcrypt | Yes | PASS — Notice preserved |
| **cffi** | Transitive Runtime | `1.17.1` | **MIT** | https://github.com/python-cffi/cffi | Yes | PASS — Notice preserved |
| **httptools** | Transitive Runtime | `0.6.4` | **MIT** | https://github.com/MagicStack/httptools | Yes | PASS — Notice preserved |
| **orjson** | Transitive Runtime | `3.10.16` | **Apache-2.0 / MIT** | https://github.com/ijl/orjson | Yes | PASS — Dual license verified |
| **ujson** | Transitive Runtime | `5.10.0` | **BSD-3-Clause** | https://github.com/ultrajson/ultrajson | Yes | PASS — Notice preserved |
| **uvloop** | Transitive Runtime | `0.22.1` | **MIT / Apache-2.0** | https://github.com/MagicStack/uvloop | Yes | PASS — Notice preserved |
| **watchfiles** | Transitive Runtime | `1.1.1` | **MIT** | https://github.com/samuelcolvin/watchfiles | Yes | PASS — Notice preserved |
| **pytz** | Transitive Runtime | `2024.1` | **MIT** | https://github.com/stub42/pytz | Yes | PASS — Notice preserved |
| **rpds-py** | Transitive Runtime | `0.22.3` | **MIT** | https://github.com/crate-py/rpds | Yes | PASS — Notice preserved |
| **tomli** | Transitive Runtime | `2.4.1` | **MIT** | https://github.com/hukkin/tomli | Yes | PASS — Notice preserved |
| **certifi** | Runtime CA Trust Store | `2025.1.31` | **MPL-2.0** | https://github.com/certifi/python-certifi | Yes | PASS — File-level MPL boundary verified |
| **setuptools** | Packaging / Runtime | `83.0.0` | **MIT** | https://github.com/pypa/setuptools | Yes | PASS — Notice preserved |
| **Python Runtime** (`libpython3.13.dylib`) | Native Runtime | `3.13.5` | **Python-2.0 (PSFL)** | https://www.python.org | Yes | PASS — PSFL compatible |
| **SQLite Engine** (`libsqlite3.0.dylib`) | Native Database | `3.45.3` | **Public Domain / Blessing** | https://www.sqlite.org | No | PASS — Public domain dedication |
| **OpenSSL Crypto** (`libcrypto.3.dylib`) | Native Security | `3.0.15` | **Apache-2.0** | https://www.openssl.org | Yes | PASS — Notice preserved |
| **OpenSSL TLS** (`libssl.3.dylib`) | Native Security | `3.0.15` | **Apache-2.0** | https://www.openssl.org | Yes | PASS — Notice preserved |
| **zlib Compression** (`libz.1.dylib`) | Native Compression | `1.3.1` | **zlib License** | https://www.zlib.net | Yes | PASS — Notice preserved |
| **XZ Utils** (`liblzma.5.dylib`) | Native Compression | `5.6.4` | **Public Domain** | https://tukaani.org/xz | No | PASS — Public Domain |
| **bzip2** (`libbz2.dylib`) | Native Compression | `1.0.8` | **bzip2-1.0.6** | https://sourceware.org/bzip2/ | Yes | PASS — Notice preserved |
| **libffi** (`libffi.8.dylib`) | Native FFI | `3.4.4` | **MIT** | https://sourceware.org/libffi/ | Yes | PASS — Notice preserved |
| **Expat XML** (`libexpat.1.dylib`) | Native XML Parser | `2.6.4` | **MIT** | https://libexpat.github.io/ | Yes | PASS — Notice preserved |
| **Zstandard** (`libzstd.1.dylib`) | Native Compression | `1.5.6` | **BSD-3-Clause** | https://github.com/facebook/zstd | Yes | PASS — Notice preserved |
| **libmpdec** (`libmpdec.4.dylib`) | Native Decimal Math | `4.0.0` | **BSD-2-Clause** | https://www.bytereef.org/mpdecimal/ | Yes | PASS — Notice preserved |
| **LLVM libc++** (`libc++.1.dylib`) | Native C++ Runtime | `19.1.x` | **Apache-2.0 with LLVM Exception** | https://llvm.org | Yes | PASS — Runtime exception verified |
| **PyInstaller Bootloader** | Packaging Bootloader | `6.22.3` | **GPL-2.0 with Bootloader Exception** | https://www.pyinstaller.org | Yes | PASS — Bootloader Exception verified |

---

## 2. Public Web, Edge Dashboard & Verifier Frontend Dependencies

The following table inventories all web server, runtime libraries, and distributed typographic assets:

| Library / Asset | Context / Usage | Exact Version | License | Upstream Origin | Compliance Disposition |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **Outfit Font** | Web & Edge Typography | `v11` | **SIL Open Font License 1.1** | Google Fonts / Onsen UI | PASS — OFL conditions respected; notices preserved; reserved font names unchanged |
| **Plus Jakarta Sans** | Web & Edge Typography | `v8` | **SIL Open Font License 1.1** | Google Fonts / Tokotype | PASS — OFL conditions respected; notices preserved; reserved font names unchanged |
| **JetBrains Mono** | Code & Data Typography | `v2.304` | **SIL Open Font License 1.1** | JetBrains | PASS — OFL conditions respected; notices preserved; reserved font names unchanged |
| **express** | Web Server Engine | `5.2.1` | **MIT** | https://github.com/expressjs/express | PASS — Notice preserved |
| **nodemailer** | Transactional Mail Engine | `10.0.11` | **MIT** | https://github.com/nodemailer/nodemailer | PASS — Notice preserved |
| **@vercel/blob** | Distribution Storage Client | `2.8.0` | **Apache-2.0** | https://github.com/vercel/storage | PASS — Notice preserved |
| **jose** | Cryptographic Token / JWS | `6.2.2` | **MIT** | https://github.com/panva/jose | PASS — Notice preserved |
| **zod** | Validation Schemas | `3.24.2` | **MIT** | https://github.com/colinhacks/zod | PASS — Notice preserved |

---

## 3. Reciprocal / Copyleft License & Obligation Analysis

### A. GPL-2.0 with PyInstaller Bootloader Exception
The PyInstaller bootloader is licensed under the GNU General Public License v2.0 with a special linking exception:
> *"In addition to the permissions in the GNU General Public License, the PyInstaller Development Team gives you unlimited permission to link or combine the compiled bootloader with code that you distribute, without being bound by the terms of the GNU General Public License."*

This exception explicitly permits bundling proprietary closed-source applications (such as VaultBasis Edge) into a standalone executable without imposing any requirement to release or license VaultBasis application source code under the GPL. The required license notices and bootloader attribution are included in the distribution notice files.

### B. Mozilla Public License 2.0 (MPL-2.0) Boundary
The `certifi` package is licensed under MPL-2.0. Under MPL-2.0 Section 3.3 ("Larger Works"), distributing an unmodified MPL-licensed file as part of a Larger Work does not subject the surrounding proprietary software to the MPL terms. VaultBasis ships the CA bundle file unmodified and does not alter the `certifi` source code.

### C. SIL Open Font License 1.1 (OFL-1.1) Compliance
The typography fonts (Outfit, Plus Jakarta Sans, JetBrains Mono) are distributed under OFL-1.1. OFL Section 5 explicitly permits bundling, embedding, and commercial redistribution with any software program without subjecting the software to font license terms. The font files are bundled unmodified with their copyright and license notices preserved.

### D. Proprietary-Source Disclosure Obligation Finding
No component identified across the evaluated pre-sign distribution scope imposes any obligation to disclose, publish, or license VaultBasis proprietary application source code or trade secrets under any reciprocal/copyleft license. Full revalidation will occur upon receipt of the final signed and notarized release artifacts.
