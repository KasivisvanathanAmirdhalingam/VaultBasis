# PLAT-WIN-01B: Physical Windows Workstation Execution Checklist

**Candidate:** WIN-CANDIDATE-04  
**Artifact ID:** 11671546711  
**Source Commit:** 6cb896f1be2386aca99d3c107ad052f3edfc66e1  
**Status:** FAILED / BLOCKED (MODE 3 ESCAPED DEFECT: FUNC-RESTORE-01..05 & PKG-UX-001)  

---

- [x] 01 OBSERVED: Download / extract Artifact 11671546711 (excessive nested archive depth PKG-UX-001)
- [x] 02 PASS: Installer present (VaultBasis-Setup-1.5.0-rc3.exe)
- [x] 03 OBSERVED: Windows trust / SmartScreen observed
- [x] 04 PASS: Per-user install under %LOCALAPPDATA%
- [x] 05 PASS: %LOCALAPPDATA%\VaultBasis destination verified
- [x] 06 PASS: Desktop / Start Menu shortcuts created
- [x] 07 PASS: Shortcut launch executes cleanly
- [x] 08 PASS: Windowed execution (no persistent raw console window)
- [x] 09 PASS: Browser/dashboard opens on loopback (http://127.0.0.1:8000/)
- [x] 10 PASS: Capacity meter correct in top nav
- [ ] 11 FAIL: Sample case loads but evidence displays as PENDING (ReferenceError: btnDeleteCase aborts refreshCaseDetails)
- [ ] 12 PENDING: Production case creation via New Case modal
- [ ] 13 FAIL: Case open displays sources as PENDING; reconciliation facts/counts missing; filters disabled
- [ ] 14 BLOCKED: Mode 3 functional restoration opened
- [ ] 15 BLOCKED
- [ ] 16 BLOCKED
- [ ] 17 BLOCKED
- [ ] 18 BLOCKED
- [ ] 19 BLOCKED
