# VaultBasis Design Partner Program Charter & Engagement Guide
**Standard**: MMP15-WIN-INSTALL-LICENSE-001 / MMP15-PRODUCTIZATION-001  
**Status**: ACTIVE PRE-RELEASE  
**Author**: Kasivisvanathan Amirdhalingam, Founder  

---

## 1. Objective & Cohort Structure

The **VaultBasis Design Partner Program** is an invite-only initiative for a select cohort of 5–8 CPAs, EAs, and tax advisory practitioners.

### The Value Exchange
- **What Design Partners Receive**:
  - Complimentary **1-Year VaultBasis Practitioner License** (12-month full offline capability, 15 client cases included, cryptographic Ed25519 evidence receipts).
  - Direct founder-level support and custom workflow onboarding.
  - Priority feature input for tax season 2026 digital asset reconciliation.
- **What We Ask in Return**:
  - Candid, honest feedback on the end-to-end workflow (installation, intake, discrepancy review, and evidence bundle export).
  - Identification of confusing terminology, missing broker formats, or UX friction.
  - *No requirement for public testimonials, endorsements, or positive ratings.*

---

## 2. Practitioner Outreach Templates

### Template A: Direct / Warm Outreach (Recommended)

> **Subject**: Would you test VaultBasis with me as a Design Partner?
>
> Hi [First Name],
>
> I’m getting VaultBasis ready for its first practitioner design-partner testing and I’d value your perspective.
>
> VaultBasis helps CPAs and EAs reconcile broker Form 1099-DA information against client crypto tax-ledger records, focus on the records that actually need review, and preserve evidence of what was reconciled.
>
> I’m inviting a small number of practitioners to use the product and give me candid feedback on the real workflow—not just whether individual features work, but whether the whole experience is intuitive from installation through reconciliation and evidence export.
>
> I’d provide you with a one-year VaultBasis license at no cost as a Design Partner. There’s no obligation to endorse the product; I’m specifically looking for genuine feedback about what works, what is confusing, and what should be improved.
>
> The regular 3-Day Evaluation will remain available to anyone who simply wants to try VaultBasis. The one-year license is specifically for invited Design Partners who are willing to help shape the product.
>
> If you’re interested, reply here and I’ll send the onboarding details once the current Mac and Windows build completes qualification.
>
> Best,  
> Kasivisvanathan  
> VaultBasis  

---

### Template B: Formal / Institutional Outreach

> **Subject**: Invitation to help shape VaultBasis — complimentary 1-year Design Partner license
>
> Hi [First Name],
>
> I’m building VaultBasis, a local-first digital-asset tax reconciliation application for CPAs and EAs.
>
> VaultBasis is designed to help practitioners compare broker-reported Form 1099-DA information with client tax-ledger records, identify matches, discrepancies and unresolved items, and preserve a verifiable reconciliation record before the practitioner makes the final tax determination.
>
> I’m preparing a small Design Partner group of CPAs/EAs to use VaultBasis with realistic workflows and tell me where the product is genuinely useful, confusing, incomplete or unnecessarily difficult.
>
> I’d like to invite you to participate.
>
> As a Design Partner, you would receive a complimentary one-year VaultBasis license. In return, I would ask for candid feedback on the experience—from installation and case setup through evidence intake, reconciliation, review and Evidence Receipt export. There is no expectation of a testimonial or positive review; useful criticism is exactly what I’m looking for.
>
> VaultBasis runs its normal client-case reconciliation locally on the practitioner’s computer and is designed to complement, rather than replace, existing tax preparation software.
>
> I expect the next Edge candidate to be ready for Design Partner testing shortly after the current Mac and Windows qualification cycle is completed.
>
> If this is relevant to your practice, reply to this email and I’ll send you the Design Partner onboarding information and license when the qualified build is ready.
>
> Best,  
> Kasivisvanathan  
> Founder, VaultBasis  

---

## 3. Technical Provisioning Workflow

To issue a 1-year bound Design Partner license:

1. Request the practitioner's Edge `installation_id` (displayed in Edge -> Settings -> Commercial Status).
2. Execute the provisioning script:
   ```bash
   python3 scripts/issue_design_partner_license.py \
     --customer "Acme Tax & Advisory LLC" \
     --installation-id "INST-A1B2-C3D4" \
     --cases 15 \
     --out "licenses/Acme_Tax_Design_Partner.license"
   ```
3. Deliver the `.license` file to the practitioner.
4. The practitioner clicks **📁 Import License File** in VaultBasis Edge to activate their 1-year entitlement.
