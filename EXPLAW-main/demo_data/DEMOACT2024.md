# Road Traffic Act 1961 — Singapore Statutes Online
## Snapshot as at: 6 September 2026 (Current)
### (Modeled fixture — Sections 1–34, Part 1: Registration and Licensing of Vehicles)

> **Fixture note:** This document models the SSO page-source structure for
> the current in-force version, incorporating Act 5 of 2026, Act 9 of 2026,
> Act 2 of 2025 (wef 20/07/2026), and Act 31 of 2023 (wef 31/12/2024). Use
> this as the "after" state in diff/detection tests against the
> `RTA1961_snapshot_2024-01-01.md` baseline. Text and amendment notes are
> drawn from the live SSO page source as at this date.

**Status:** Current version as at 6 September 2026
**Last amendment:** Act 21 of 2025, effective 17 Aug 2026 (see Legislative History)

---

### Long Title
An Act for the regulation of road traffic and the use of vehicles and the user of roads and for other purposes connected therewith.
*[4/2006; 10/2017]*

---

## PART 1 — REGISTRATION AND LICENSING OF VEHICLES

### 1. Short title
This Act is the Road Traffic Act 1961.

### 2. Interpretation

—(1) In this Act, unless the context otherwise requires —

> ...(definitions unchanged from 2024 version omitted for brevity)...

*[Deleted by Act 5 of 2026 wef 04/05/2026]*

> **[DIFF: The "Minister" definition present in the 2024 baseline has been
> deleted outright — no replacement wording. Any contract clause or memo
> that cross-references "the Minister" via this defined-term mechanism
> should be checked; the term may now derive its meaning from context or
> from the Interpretation Act 1965 default instead.]**

**"mobility vehicle" has the meaning given by section 2(1) of the Active Mobility Act 2017;**
*[Act 5 of 2026 wef 04/05/2026]*

> **[DIFF: New defined term, not present in the 2024 baseline. This term
> now appears throughout ss.5A and 5B (see below) — any document review
// workflow scanning for "personal mobility device" alone will MISS this
> parallel category.]**

**"personal mobility device" has the meaning given by the Active Mobility Act 2017;**

**"permanent resident of Singapore" has the meaning given by section 2 of the Immigration Act 1959;**
*[Act 31 of 2023 wef 01/12/2025]*

> ...(remaining definitions unchanged)...

(2) *(unchanged)*

---

### 3. Vehicles to which this Part applies
*(unchanged)*

### 4. Classification of motor vehicles
*(unchanged — omitted for brevity)*

### 5. Prohibition of vehicles not complying with rules as to construction, etc.

—(1)–(4) *(unchanged)*

(5) *(unchanged)*

(5A) *(unchanged)*

(5B) In this section, "alter" includes causing, authorising or permitting a person to alter, and offering to alter.
*[10/2017]*
*[Act 5 of 2026 wef 27/02/2026]*

> **[DIFF: Text is unchanged from the 2024 baseline, but the SSO annotates
> a further amendment effective 27/02/2026. This is a "silent" or
> non-substantive amendment marker in the source — worth flagging to your
> detection pipeline as a case requiring human confirmation: the amend
> note fires but the visible text is identical, likely because the actual
> change was to a related subsection's cross-reference rather than this
> text itself. Good test case for false-positive suppression logic.]**

(6) *(unchanged)*

**(7)** Any person who is guilty of an offence under subsection (5) or (6) shall be liable on conviction —
(a) where the person is an individual —
  (i) to a fine not exceeding $20,000 or to imprisonment for a term not exceeding 2 years or to both; but
  (ii) where the individual is a repeat offender, to a fine not exceeding $40,000 or to imprisonment for a term not exceeding 4 years or to both; or
(b) in any other case —
  (i) to a fine not exceeding $40,000; but
  (ii) where the person is a repeat offender, to a fine not exceeding $80,000.
*[Act 5 of 2026 wef 27/02/2026]*

> **[DIFF: Materially restructured from the flat $10,000/12-month penalty
> in the 2024 baseline. Individual-vs-non-individual and first-vs-repeat
> tiers now apply, with maximums up to 8x the prior fine amount. HIGH
> PRIORITY for R&T document review — any compliance guide, contract
> indemnity clause, or client memo quoting the old figure is now
> materially wrong.]**

**(7AA)** [Deleted by Act 5 of 2026 wef 27/02/2026]

> **[DIFF: The forfeiture-on-conviction subsection present in the 2024
> baseline has been removed entirely, not replaced. Flag any document that
> relies on automatic forfeiture under s.5(7AA) — that provision no longer
> exists; forfeiture (if applicable) must now be sourced elsewhere, e.g.
> s.35AA or s.65AA for related vehicle-forfeiture powers.]**

(7A)–(9) *(unchanged)*

(10) In this section —

"authorised officer" *(unchanged)*

"non‑compliant vehicle or trailer" *(unchanged)*

**"repeat offender"**, for an offence under subsection (5) or (6) involving a power-assisted bicycle read with subsection (7), means a person who —
(a) is convicted, or found guilty, of such an offence (called the current offence); and
(b) has been convicted or found guilty (whether before, on or after 3 April 2020) of an offence under subsection (5) or (6) (whether involving a power‑assisted bicycle) on at least one other earlier occasion within the period of 5 years immediately before the date on which the person is convicted or found guilty of the current offence.
*[3/2017; 9/2020]*
*[Act 5 of 2026 wef 27/02/2026]*

> **[DIFF: Same observation as s.5(5B) above — annotated amendment, text
> unchanged from baseline. Likely a consequential/renumbering-only change
> tied to the s.5(7) restructure. Confirm with a section-level diff before
> auto-flagging as a substantive change.]**

---

### 5A. No riding of personal mobility devices, etc., on roads

—(1) An individual must not ride a personal mobility device or drive or ride a mobility vehicle on a road at any time.
*[3/2017; 38/2018]*
*[Act 5 of 2026 wef 04/05/2026]*

> **[DIFF: "or drive or ride a mobility vehicle" inserted — this is the
> single highest-value flag for R&T's document-review stage. Any client
> policy, insurance rider, or compliance clause that scoped itself to
> "personal mobility device" only (matching the 2024 baseline) is now
// under-inclusive as against the current Act.]**

(2) However, subsection (1) does not apply to an individual who is crossing a road in or on a personal mobility device or a mobility vehicle —
(a) if the individual crosses the road by the shortest safe route, and does not stay on the road longer than necessary to cross the road safely; or
(b) if —
  (i) there is, in the case of a rider of a personal mobility device, an obstruction on a shared path or footpath (within the meaning of the Active Mobility Act 2017) adjacent to the road (called an adjacent area), or there is an obstruction on any public path (within the meaning of that Act) adjacent to the road (also called an adjacent area) in the case of a driver or rider of a mobility vehicle;
  *[Act 5 of 2026 wef 04/05/2026]*
  (ii) it is impracticable to travel on the adjacent area; and
  (iii) the individual travels no more than reasonably necessary along the road to avoid the obstruction.
  *[3/2017; 38/2018]*
  *[Act 5 of 2026 wef 04/05/2026]*

(3) *(unchanged from baseline — penalty amounts not altered)*

**(4)** In this section and section 5B, "ride" has the meaning given by section 2(1) of the Active Mobility Act 2017.
*[Act 5 of 2026 wef 04/05/2026]*

> **[DIFF: New subsection, does not exist in the 2024 baseline —
> consequential to the mobility-vehicle extension.]**

---

### 5B. No riding of personal mobility device, etc., when towed by motor vehicle

—(1) An individual must not ride a personal mobility device or drive or ride a mobility vehicle on a road at any time while the individual riding the personal mobility device, or driving or riding the mobility vehicle, is towed by a motor vehicle or is otherwise holding on to a motor vehicle.
*[38/2018]*
*[Act 5 of 2026 wef 04/05/2026]*

> **[DIFF: Same "mobility vehicle" extension as s.5A.]**

(2) *(unchanged)*

---

### 6. Rules as to use and construction of vehicles

—(1) The Authority may make rules generally as to the use of vehicles and trailers, their construction and equipment and the conditions under which they may be used and, in particular, may make rules —

(a)–(g) *(unchanged)*

**(h)** to prescribe the safety equipment to be installed in vehicles, to regulate the use of such safety equipment and to ensure that they are efficient and kept in proper working order;
*[Act 5 of 2026 wef 14/04/2026]*

> **[DIFF: Entirely new rule-making power, absent from the 2024 baseline.
> All subsequent paragraphs are renumbered (i) onward. If R&T maintains
> any internal cross-reference table mapping s.6(1) paragraph letters to
// subject matter, it must be updated — letter (h) now means something
> different than it did pre-14/04/2026.]**

(i) to control, in connection with the use of a motor vehicle, the emission of smoke, oily substance, ashes, water, steam, visible vapour, noxious fumes, sparks, cinders, gas or grit;

...(remaining paragraphs correspondingly renumbered)...

(2)–(4) *(unchanged)*

---

### 7.–9. *(unchanged — omitted for brevity)*

### 10. Registration of vehicles

—(1)–(2) *(unchanged)*

**(3)** Any person who contravenes subsection (1) shall be guilty of an offence and shall be liable on conviction to a fine not exceeding $20,000 or to imprisonment for a term not exceeding 2 years or to both and, in the case of a second or subsequent conviction, to a fine not exceeding $40,000 or to imprisonment for a term not exceeding 4 years or to both.
*[10/2017]*
*[Act 5 of 2026 wef 27/02/2026]*

> **[DIFF: Restructured from flat $10,000/12mo to a tiered $20,000–$40,000
> / 2–4-year regime. Same category of change as s.5(7) — flag as
> high-priority for compliance documents.]**

### 10A.–11B. *(unchanged — omitted for brevity)*

### 12. Vehicles licensed outside Singapore

—(1)–(2) *(unchanged)*

**(3)** For the purposes of this section, a person is deemed to be a resident of Singapore if he or she —
(a) is a permanent resident of Singapore, even though he or she may not have a place of residence in Singapore; or
*[Act 31 of 2023 wef 31/12/2024]*
(b) resides in Singapore for a continuous period of 6 months and any temporary period or periods of absence during that period is immaterial.

> **[DIFF: New paragraph (a) inserted ahead of the pre-existing limb
> (now relettered (b)). A permanent resident is now deemed Singapore-
> resident for s.12 purposes regardless of actual physical residence.
> If any client vehicle-licensing advice assumed only the physical-
> residence test (matching the 2024 baseline), it understates who counts
> as a Singapore resident under this section.]**

(4) *(unchanged)*

### 13.–24. *(unchanged — omitted for brevity)*

### 25. Visitors' vehicles

—(1)–(2) The rules may —
(a)–(k) *(unchanged)*

**(l)** prescribe the records to be kept by the Registrar in connection with the rules;
*[Act 2 of 2025 wef 20/07/2026]*

**(m)** empower the Registrar and any officer authorised by him or her to prohibit the entry by driving into, or exit by driving from, Singapore of any vehicle —
(i) if any prescribed charge, fee or tax payable in respect of the vehicle under this Act or any subsidiary legislation made under this Act, or any other written law, is in arrears; or
(ii) that the Registrar or officer so authorised reasonably believes has been used in the commission of any prescribed offence under this Act or any subsidiary legislation made under this Act, or any other written law; and
*[Act 2 of 2025 wef 20/07/2026]*

(n) provide for any matter that is required or permitted to be prescribed under this section.
*[Act 2 of 2025 wef 20/07/2026]*
*[1/2006; 10/2017; 38/2018]*

> **[DIFF: Two entirely new record-keeping and entry/exit-prohibition
> powers inserted; the former closing paragraph (l) is relettered (n).
> This is a substantive new enforcement power for cross-border vehicles.
> Recommend flagging for lawyer review in any client SOP touching foreign-
// registered vehicle compliance, arrears enforcement, or Registrar
> discretion at Singapore's checkpoints.]**

(3)–(5) *(unchanged)*

### 26.–33B. *(unchanged — omitted for brevity)*

### 34. Rules for purposes of this Part

—(1) The Minister may make rules for any purpose for which rules may be made under this Part...

(a)–(n) *(unchanged)*

**(o)** to prescribe —
(i) the fees and costs payable for the recovery of any tax payable under this Act, whether by instalment or otherwise; and
(ii) any interest or charge payable for the late payment, or the payment by instalment, of any tax payable under this Act;
*[Act 4 of 2008 wef 01/04/2024]*

> **[DIFF: Sub-paragraph (ii) is now in force (it was pending as at the
> 2024-01-01 baseline, commencing 01/04/2024). No further action needed if
> R&T's document base was already updated after April 2024, but this is a
> useful test of "amendment lag" — a change published years earlier (Act 4
> of 2008) commencing on a delayed date is easy to miss if detection only
> watches for *new* amending Acts rather than *commencement* dates of
> already-passed ones.]**

(p)–(s) *(unchanged)*

(2)–(3) *(unchanged)*

---

## END OF FIXTURE — 2026-09-06 SNAPSHOT

**Use with `RTA1961_snapshot_2024-01-01.md` as a matched before/after pair.**
Suggested test cases for your detection/document-review pipeline:

1. **Clean structural diff** (s.5(7), s.10(3)): amount and structure both
   change — should trigger a clear, unambiguous flag.
2. **Definition deletion with no replacement** (s.2 "Minister", s.5(7AA)):
   tests whether your pipeline distinguishes "amended" from "repealed."
3. **New parallel category inserted alongside existing term** (s.5A/5B
   "mobility vehicle"): tests whether keyword-based document scanning
   (matching only "personal mobility device") under-detects scope changes.
4. **Annotated-but-textually-identical amendment** (s.5(5B), s.5(10)):
   tests false-positive suppression — the amendNote fires, but the visible
   text at section level is unchanged, so a human should confirm before a
   contract-amendment suggestion is generated.
5. **Amendment already passed but not yet in force at baseline date**
   (s.12(3), s.34(1)(o)(ii)): tests whether your ingestion job tracks
   *commencement* dates separately from *enactment* dates.
6. **New enforcement power addition** (s.25(2)(l)–(m)): tests prioritization
   logic — this is a substantive new government power, not a penalty
   adjustment, and may need different downstream routing (e.g., regulatory
   affairs review vs. standard contract-clause review).
