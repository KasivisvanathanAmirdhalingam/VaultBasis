# VaultBasis Platform Release Signing Runbook
**Document ID:** VB-RUN-SIGN-001  
**Classification:** OPERATIONAL  
**Authority:** Release Operations Lead  
**Status:** ACTIVE  
**Applies To:** Windows (Authenticode) & macOS (Developer ID) Signing Ceremonies  
**Last Reviewed:** 2026-10-08  

---

## 1. Prerequisites & Authorized Entry Conditions

Platform signing must **only** be initiated when the following conditions are simultaneously met:
1. Candidate source code is tagged and passes all automated test suites (`508+` tests passing).
2. Unsigned candidate artifact has achieved `PRE_SIGN_PASS` on its respective platform.
3. Administrative publisher identity validation is active and verified:
   - **Windows:** Azure Artifact Signing (Public Trust / Basic) active.
   - **macOS:** Apple Developer Program organization enrollment active with Developer ID certificate.

---

## 2. Windows Authenticode Signing Procedure (Azure Artifact Signing)

```bash
# 1. Authenticate to Azure Artifact Signing
az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID

# 2. Execute Authenticode signing with RFC 3161 timestamping
python scripts/sign_windows_azure.py \
  --input dist/VaultBasis-Setup-1.5.0-rc3.exe \
  --output dist/signed/VaultBasis-Setup-1.5.0-rc3.exe \
  --account-name $AZURE_SIGNING_ACCOUNT \
  --profile-name $AZURE_SIGNING_PROFILE \
  --timestamp-server http://timestamp.digicert.com

# 3. Verify Authenticode signature offline
signtool verify /pa /v dist/signed/VaultBasis-Setup-1.5.0-rc3.exe

# 4. Compute and record post-sign SHA-256 digest
shasum -a 256 dist/signed/VaultBasis-Setup-1.5.0-rc3.exe > evidence/windows_signed_sha256.txt
```

---

## 3. macOS Developer ID Signing, Notarization & Stapling Procedure

```bash
# 1. Sign internal helper binaries and main executable with Hardened Runtime
codesign --force --options runtime --timestamp \
  --sign "Developer ID Application: VaultBasis Inc. (TEAMID)" \
  dist/VaultBasis.app/Contents/MacOS/VaultBasis

# 2. Sign the outer .app bundle
codesign --force --options runtime --timestamp \
  --sign "Developer ID Application: VaultBasis Inc. (TEAMID)" \
  dist/VaultBasis.app

# 3. Create and sign the distribution DMG
hdiutil create -volname "VaultBasis" -srcfolder dist/VaultBasis.app -ov -format UDZO dist/VaultBasis-1.5.0-rc3.dmg
codesign --force --sign "Developer ID Application: VaultBasis Inc. (TEAMID)" dist/VaultBasis-1.5.0-rc3.dmg

# 4. Submit to Apple Notary Service
xcrun notarytool submit dist/VaultBasis-1.5.0-rc3.dmg \
  --keychain-profile "vaultbasis-notary" --wait

# 5. Staple notarization ticket to DMG
xcrun stapler staple dist/VaultBasis-1.5.0-rc3.dmg

# 6. Verify Gatekeeper acceptance
spctl --assess --type open --context context:primary-signature -vv dist/VaultBasis-1.5.0-rc3.dmg

# 7. Compute and record post-sign SHA-256 digest
shasum -a 256 dist/VaultBasis-1.5.0-rc3.dmg > evidence/macos_signed_sha256.txt
```

---

## 4. Evidence Retention & Gate Closure

Upon successful completion:
1. Save notarization logs and SignTool output to `evidence/`.
2. Update [`docs/qualification/mmp15_traceability_matrix.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/qualification/mmp15_traceability_matrix.md) setting `PROD-GATE-07` or `PROD-GATE-08` to `SIGNED_ARTIFACT_PASS`.
3. Update `release-manifest.json` with the new post-sign SHA-256 digests.
