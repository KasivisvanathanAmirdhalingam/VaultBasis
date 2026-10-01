# MMP11-EXEC-008: Candidate 5 Request-Access Recovery

## Context
OCC collision caused the request access API to return 503 instead of 202 because strong ETags (`W/`) from cached reads were sent to a non-matching condition. VoiceOver focus dropped when the submit button was disabled.

## Fix
1. Stripped `W/` prefix from ETags.
2. Added `allowOverwrite: true` to bypass cache consistency errors for Vercel Blob.
3. Added focus management to Request Access form.

## Evidence
- Local 10-point concurrency test passed.
- Exact-SHA CI built.
