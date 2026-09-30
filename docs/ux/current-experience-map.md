# CURRENT EXPERIENCE MAP

Date: 2026-09-30. Audit baseline: source at `70606ff`, selected Mac candidate source at `83d78db`, anonymous live web capture. **Not a complete production/native qualification.**

The tables together provide all requested fields for every surface. Current behavior is distinguished from intended success. `S` means source inspection; `H` historical founder/handover observation; `L` live browser evidence; `U` unverified. Defect IDs refer to the register below. No absence of a finding means an accessibility or visual pass.

## PUBLIC WEB — purpose, actions and navigation

Shared current shell **W**: VaultBasis, How It Works, Trust & Assurance, Resources, About; Verify an Outcome Receipt and Request Design-Partner Access. Footer repeats product/resource/support destinations, including Contact and Report an Issue. Baseline sources: [marketing](../../apps/web-marketing), [partials](../../apps/web-marketing/partials).

| Surface / current route | Purpose | Primary user | Primary action | Secondary action | Global navigation | Local navigation |
|---|---|---|---|---|---|---|
| Home `/` | Explain reconciliation and invite evaluation | New practitioner | Request access | Verify receipt | W | Second page-section strip: How It Works / Evaluation Boundary / Evidence Processing / Resources |
| Trust Center `/trust-assurance` | Explain assurance and operational boundaries | Evaluating practitioner / reviewer | Inspect assurance limits | Open verifier / evidence | W | Product Assurance / Security / Privacy / Governance / Legal |
| About `/about` | Explain product and purpose | New practitioner | Evaluate preview | Verify receipt | W | What it is / why / what it is not / receipt / preview; no separate local menu |
| Contact `/contact` | General and issue contact | Practitioner needing help | Open general email | Security disclosure | W | General / Issue / Security sections |
| Access: shared modal + `/verifier-access` | Request preview; separately authenticate verifier | Prospect / credential holder | Submit name/email; or credential | Close / request access / FAQ | W beneath dialog; W on access page | Dialog actions; credential form |
| Verifier `/verifier` | Check a receipt's declared cryptographic properties | Receipt recipient | Select/drop receipt after access gate | Valid/tampered samples, schema | Separate verifier shell in source; anonymous gate in production must be checked | Five result rows and sample controls |
| Privacy `/privacy-policy` | Explain handling of information | Practitioner / governance reviewer | Read policy | Contact | W | Sequential policy headings |
| Terms `/terms-of-service` | Explain preview terms and limits | Evaluating practitioner | Read terms | Contact / disclosure | W | Numbered terms headings |
| Security `/security-disclosure` | Report vulnerability | Security reporter | Open security email | Read scope | W | Reporting / coordinated disclosure / scope / preview |
| Scope `/docs/scope_and_limitations_v0.1.html` | Declare supported inputs and limitations | Evaluating / operating practitioner | Check supported scope | Return to product | Generated document shell, not W | Numbered sections |
| FAQ `/faq` | Answer common questions | Practitioner | Find answer | Access / further help | W | Question headings |
| Not found: unknown public URL | Recover from bad destination | Any visitor | Return home | Contact | Source defines separate dark page; live unknown URL instead serves Home | Live homepage navigation |

## PUBLIC WEB — states and defects

| Surface | Success state | Failure state | Accessibility defects / evidence gaps | Visual defects / evidence gaps | Functional defects / evidence gaps | Trust/claim defects / evidence gaps |
|---|---|---|---|---|---|---|
| Home | Visitor understands purpose, boundary and next action; comprehension U | Destination failure / unsupported CTA outcome not centrally designed | D03, D04; manual reading order U | D01, D02; full hierarchy review pending | D04 | Technical resource catalog competes with product explanation (D01) |
| Trust Center | Boundary understood; proof reachable | Broken evidence destination; no inline recovery | Keyboard, tables, reflow U | Local taxonomy differs from required IA (D01) | Actual evidence download/fragment completion U | P06 evidence cannot imply current release qualification |
| About | Visitor understands why product exists and preview status | Linked evaluation flow blocked | Shared modal D03; page manual audit U | Repeats homepage product/receipt exposition (S) | Depends on broken access chain D05 | Preview availability must track qualified artifact |
| Contact | Mail application opens; user can copy address | No email client / undelivered mail; delivery U | Copy fallback and keyboard UX U | D02 duplicate global issue destination | Mailbox delivery not tested | No taxpayer evidence should be requested; existing privacy warning must remain |
| Access | Current UI says request under review; server creates entitlement and test email | Alerts for validation/network/server failures; 503 without manifest | D03 | Success/error hierarchy not qualified | D05, D06 | D05: under-review UI vs approved/provisioned email; preview credential missing from observed path |
| Verifier | Separate conformance/compatibility/key/signature results; tax not determined | Schema/version/signature failures in source; authenticated runtime U | Keyboard upload exists in source; focus/error announcement and browser support U | Different header/footer taxonomy (D02) | Authenticated verification, session expiry and samples U | Preserve declared-key limitation; no installation identity or tax assurance inference |
| Privacy | User can distinguish local processing and website handling | Policy unavailable / contact unavailable | Manual readability/reflow U | Shared shell defects; dense-text hierarchy U | Contact journey U | Reconcile disclosure of actual external resources and access behavior; policy approval outside this audit |
| Terms | User understands preview constraints | Page unavailable / unclear support recovery | Manual long-document navigation U | Shared shell defects | Support recovery U | No legal compliance determination from this review |
| Security | Reporter understands safe contact and scope | Email unavailable; no on-page delivery confirmation | Link purpose / keyboard U | Shared shell defects | Security mailbox delivery U | Preserve security channel distinction; no invented response SLA |
| Scope | Supported formats, unknown handling and limits understood | Missing document / resource | Generated shell/manual navigation U | Different document shell (S) | Direct/return journey requires qualification | Do not expand semantic claims or turn retained historical evidence into present qualification |
| FAQ | Question answered and appropriate next action clear | Answer/destination absent | Heading navigation U | Potential homepage/trust duplication requires consolidation | Deep links U | Answers must distinguish hosted access from offline verification |
| Not found | User recovers to useful page | Live unknown URL silently serves Home | Manual error-page audit U | Source dark design diverges; deployed error page not reached | D13: live unknown URL returns Home with 200 | Success status disguises missing destination |

## EDGE — purpose, actions and navigation

Current shell **E** at checkout: Cases / Why VaultBasis? / Independent Verifier / Evidence Schema / Help / New Case. Screens toggle DOM visibility within `/`; source does not supply route-based case state. Mac `83d78db` adds local offline-verifier integration and external URL corrections, but this packet has not exercised that exact packaged app.

| Surface / current location | Purpose | Primary user | Primary action | Secondary action | Global navigation | Local navigation |
|---|---|---|---|---|---|---|
| Launch / native executable | Enter local workspace | Installed practitioner | Launch app | Quit / relaunch | U for exact package | Native launch/recovery U |
| Cases `/`, `screen-cases` | Manage local cases | Practitioner | New case / open case | Refresh | E | Case rows |
| Sample Case | Safe first evaluation | New practitioner | Run supported synthetic example | Return to cases | No dedicated sample screen found in inspected dashboard | Packaged sample resources require native inspection |
| Case Detail `screen-review` | Import supported evidence and reconcile | Practitioner | Add evidence / run reconciliation | View receipt / back to cases | E | Source list, differences table, unresolved list |
| Finding / inline table | Understand difference or unresolved evidence | Reviewing practitioner | Read finding | Inspect source context | E | Inline table; no dedicated finding drill-down found |
| Receipt `screen-receipt` | Retain signed outcome and evidence | Practitioner / reviewer | Download evidence bundle | Launch verifier / back to review | E | Metadata and raw JSON |
| Offline Verifier | Verify locally without hosted credentials | Receipt recipient | Select receipt | Sample / return | Checkout incorrectly shares hosted verifier; `83d78db` has `/offline-verifier` | Verification controls (candidate source only) |
| Help `screen-help` | Guide supported workflow | Practitioner | Read getting started / troubleshooting | Scope / support / disclosure | E | Sequential help sections and links |
| External destinations | Reach company/support/hosted verifier deliberately | Practitioner | Follow labeled online destination | Return to local work | E | Checkout uses relative links; candidate corrects several |

## EDGE — states and defects

| Surface | Success state | Failure state | Accessibility defects / evidence gaps | Visual defects / evidence gaps | Functional defects / evidence gaps | Trust/claim defects / evidence gaps |
|---|---|---|---|---|---|---|
| Launch | Workspace opens without technical setup | Exact candidate startup/security/port errors U | Native keyboard/VoiceOver U | Native launch presentation U | D12: exact package not established | Never equate a build with install qualification |
| Cases | Case created/opened; empty guidance exists | API errors alert; fetch failures uncaught in source | Browser prompt for create; focus changes absent (D08) | H logo/contrast complaints; corrected source unqualified | Hardcoded year/jurisdiction; no pending protection; D08 | Case outcomes must retain kernel values |
| Sample Case | Clearly synthetic case can run to receipt | Missing/malformed sample recovery U | No dedicated discovered screen to qualify | Discoverability gap D10 | D10 | Sample must not look like client evidence or proof of source truth |
| Case Detail | Evidence imported; outcome presented | Upload/reconcile alerts; failed refresh silently returns | Click-only upload div in source; no screen focus management | Dense technical headings and raw state labels | D08, D09 | D09: no differences can be rendered as all matched regardless of unresolved items |
| Finding | User sees reason and evidence/provenance supplied by kernel | No finding-specific recovery | Table/focus/reading order U | No focused detail view found | D09: finding display updated on reconcile, not normal reopen | Do not infer source attribution or resolve absent data |
| Receipt | Existing receipt visible and export retained | Failed receipt fetch silently returns; export browser navigation exposes endpoint | JSON explanation/download announcement U | Raw JSON dominates understanding path | D07, D08 | Signing-key display is not independent origin authentication |
| Offline Verifier | Schema/version/key/signature results offline | Invalid/unsupported receipt; missing verifier resource | Actual candidate keyboard/screen reader U | H identity/contrast defects; source remediation only | D07, D11, D12 | Local offline verification must not require hosted session |
| Help | User can complete local workflow | Relative destinations can reach local 404 | Keyboard/focus and document reading U | H broken destination experience | D07; exact package retest required | Current source says Web Verifier can be used without contacting VaultBasis; hosted access contradicts this |
| External destinations | Correct public HTTPS destination, clearly online | Offline website access retains local case | New-context announcement/focus U | Brand continuity U | D07, D11 | Do not disguise external capability as local/offline |

## UX defect register

Blocking denotes a proposed release gate, not a new historical test result.

| ID | Evidence | Defect / impact | Required disposition | Gate |
|---|---|---|---|---|
| D01 | S homepage/header; H founder | Multiple navigation taxonomies and engineering resource catalog interrupt first-use explanation | Canonical web IA; trust proof moved into Trust Center | Coherence |
| D02 | S footer/verifier/build script; H founder | Duplicate support links and separate verifier/document/error shells weaken one-product experience | One web shell, subordinate local navigation, consistent document/error treatment | Coherence |
| D03 | S `partials/shell.js`, `modal.html`; L tab observation | Modal only handles Escape, no focus containment/restoration; alerts instead of associated field errors/live status | Complete dialog and accessible form state contract | Accessibility blocker |
| D04 | S shell/footer | Back-to-top only at footer; smooth scroll ignores reduced-motion preference | Persistent non-obstructing control after meaningful scroll; reduced-motion behavior | Accessibility/navigation |
| D05 | S root request API/session API/modal; H | Test email, contradictory request status, and no preview credential creation in inspected request path | Truthful backend-backed request state plus real qualified provisioning; separate credential/entitlement delivery | Access blocker |
| D06 | S request API | Entire request rejected if artifact manifest absent; first artifact hash chosen without user platform | Define pending/unavailable state and qualify per-platform entitlement/download; security owner review | Access/distribution blocker |
| D07 | S dashboard/API; H previous Mac FAIL; candidate source fixes | Hosted verifier reused locally; missing Help/support routes; raw local errors | Explicit destination classification and exact package browser/native retest | Navigation blocker |
| D08 | S dashboard functions | Uncaught fetch errors, silent failures, prompt/alert workflow, no pending protection or route/focus persistence | Designed loading/error/recovery and accessible forms; prevent duplicates; validate Back/reload | Functional blocker |
| D09 | S `triggerReconciliation`, `refreshCaseDetails` | Empty differences table unconditionally claims all match; reopened case does not repopulate findings through detail refresh | Present authoritative state and preserved findings without rerunning/mutating semantics; architecture review if API lacks required data | Claim/functional blocker |
| D10 | S inspected dashboard | No discoverable dedicated Sample Case journey | Safe explicit synthetic workflow using supported existing evidence inputs | First-use blocker |
| D11 | S checkout dashboard fonts; candidate offline-verifier diff | Remote font dependency in local UI; full candidate offline behavior untested | Local assets/system fonts; test with external network disabled | Offline blocker |
| D12 | Local manifest; H candidate identity gaps | Local package differs from handover candidate; Windows identity unresolved | Obtain exact CI/package provenance, audit recipient path separately per OS | Qualification blocker |
| D13 | L `/ux-audit-missing-page`, both widths | Unknown public URL returns homepage and HTTP 200 instead of a not-found state | Correct routing/status plus designed recovery on exact deployed candidate | Navigation blocker |

## Live observations — 2026-09-30T20:35:53Z

Chromium 153.0.8010.12 captured 12 routes at 1440×900 and 390×900, plus the open access modal (25 PNGs). See [raw observations](evidence/2026-09-30/production-observations.json). Public pages rendered; `/verifier` redirected the anonymous browser to `/verifier-access?next=/verifier`. This proves that observed anonymous entry path only, not exhaustive authorization enforcement.

The modal focused Name, then Email, then Submit; the next Tab moved to background footer links. Escape left focus on About VaultBasis, not the invoking button. This reproduces D03 at production. The unknown route served Home with 200 at both widths (D13). No horizontal page overflow or console errors were recorded in these limited page-load journeys; this does not qualify 320 px reflow, access submission, authenticated verification or mobile devices.

Visual inspection of the captured Home/mobile, Trust/desktop and Scope/mobile confirms the competing homepage section strip, long resource-heavy landing narrative, repeated footer directory, card-heavy trust reference and separate Scope document shell. These are developer observations, not founder acceptance. Full-page images are evidence of layout structure; inspect at native resolution before judging text size or contrast. The homepage is 10,302 CSS pixels tall at 390 px width, illustrating the amount of material encountered before reaching the footer.

The production build comment says `VaultBasis Build: preview`, timestamp `2026-09-30T14:34:34.015Z`. It does not establish source SHA or immutable deployment identity.

## Remaining boundary work

The live capture records actual anonymous page responses and modal tab behavior, not a complete click crawl or form qualification. Extend it to every observed link/button, fragment, download, loading/error/session state and browser history transition on the protected candidate. No authenticated credential was available in this audit. Do not bypass access to inspect the gated screen.

Obtain the `83d78db` candidate or a newly designated immutable package through the release process, verify its hash, and audit launch → cases → sample → case → finding → receipt → offline verify → help → quit/relaunch. Use synthetic data and a clean workspace; do not inspect or mutate the founder's existing cases. Capture native screenshots and screen-reader evidence. Until then all packaged Edge behavior in this map remains U or attributed H, even when source fixes look correct.
