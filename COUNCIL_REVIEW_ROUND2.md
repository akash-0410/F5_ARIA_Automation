# Council Review — Round 2 (Mock Deployment Stress Test)

**Subject:** F5 Automation Deployment Package — `DEPLOYMENT_GUIDE.md` + `SOP.docx`
**Format:** Two returning reviewers re-verify their Round 1 findings against the fixed package; two new reviewers, given nothing but the package, physically simulate performing the deployment.
**Chair:** Lead engineer (this document's author) — brief was to be harsh, assume nothing was really fixed until proven, and treat this like a production network deployment where a mistake is not recoverable.

This is a reconstructed transcript of how the four reports were argued out and resolved, not a literal chat log — but every position below is a real finding from one of the four review agents, and every resolution below is a real edit that was made (or explicitly not made, with the reason recorded).

---

## Seated at the table

- **Chair** — lead engineer, hostile by design.
- **R1 — Returning, Technical Accuracy.** Came back to check their own Round 1 findings against the current files.
- **R2 — Returning, Skeptical / Devil's Advocate.** Same brief — verify, then keep hunting.
- **R3 — New, Mock Deployer (Fresh Install).** A first-time Tier-1 engineer with zero vRA/vRO/F5 background, told to walk `DEPLOYMENT_GUIDE.md` line by line as if actually about to click through a brand-new install, and to stop and log anything not fully unambiguous.
- **R4 — New, Mock Deployer (Update Path + Failure Injection).** Same profile, but assigned the "action already exists" branches, plus a second task: deliberately make four realistic mistakes and see whether the Guide's own checkpoints would actually catch them.

---

## Opening

**Chair:** Round 1 fixed nine findings apiece from two of you. I don't care that the wording changed — I want to know if a person who has never seen this system before can actually get through it without guessing, and whether the checkpoints in this document catch a real mistake or just look reassuring. R3, R4 — you went in cold. Where did you get stuck?

## R3 reports: the fresh-install path stalls at step 1

**R3:** Before I even open a browser. Checklist item 2.0 says *"Confirm §0.4 is filled in. Do not proceed with a blank escalation contact."* §0.4 is two blank underscored lines and "ask your team lead if you don't know." I have no team lead in this document. I am blocked at the very first gate, using only what I was handed.

**Chair:** That's not a documentation bug, that's an operational bug — the guide assumes an org process it never states.

**R3:** It gets worse. Section 5.4's step 4 is explicitly the most important check in the whole guide — the guide says so itself — and it depends on an "F5/network contact" who *never gets a field to write their name down anywhere.* Escalation contact has a box. This person doesn't.

**Chair:** So there are two blocking human dependencies and only one of them even has a place to be recorded.

**R3:** Correct. And Section 5.3 — also marked mandatory — says "ask your escalation contact where the form designer is if you haven't used it before." That's the same document promising in its own first paragraph, quote: *"Every step tells you exactly where to click."* It breaks its own promise on a mandatory step.

**Chair:** Anyone want to defend that as acceptable ambiguity?

**R2 (returning skeptic):** No. I flagged something adjacent in Round 1 — the time-estimate pressure to skip the F5-side check — and this is the same failure mode one layer earlier: you can't even *reach* the check if you don't know who to ask.

**Verdict:** Fix. Added §0.5 (F5/network contact, with fields, filled in by the manager before the guide is handed over — not by the engineer from nothing), reframed §0.4 the same way, added checklist item 2.0 to gate on both, and added a short paragraph up front naming all four human roles this guide leans on so nobody has to guess which is which mid-deployment.

---

## R3 continues: a contradiction between two adjacent sections

**R3:** Section 2.2's checkpoint says the vRO left-hand menu has "Library, with Workflows, Actions, Policies underneath it" — full stop, that's what confirms you're in the right place. Then step 3.12, ten steps later, casually introduces "Assets (or Library, depending on version)" for something called Configurations, which was never mentioned in 2.2's checklist at all.

**Chair:** So either I'm missing a menu item at the exact moment I'm told to confirm I'm in the right place, or the document forgot to mention it existed.

**R1 (returning, technical accuracy):** I didn't catch that one in my pass — I was checking code claims, not UI navigation claims. That's a legitimate miss on my part, not yours.

**Chair:** Good, own it, don't defend it. Fix.

**Verdict:** Fix. §2.2's checkpoint now explicitly says Configurations/Assets also lives somewhere in that same left-hand menu, without forcing a specific location (since it does vary by version) — so 2.2 and 3.12 no longer contradict each other.

---

## R3 raises the Action Constant question — Chair pushes back before conceding

**R3:** Step 4.8 tells me `F5_VIP_SUBNET_REGISTRY`'s value is "pasted directly into the Value field... not a reference to a separately-built object elsewhere." But the *script's own error message* says "Add an entry (Extensibility > Actions > **Action Constants**)" — which reads like a separate, named list of objects, not an inline field on this one action.

**Chair:** Play devil's advocate against yourself for a second — isn't that just two true things? Action Constants can be a separate list *and* each entry in that list still just holds literal JSON you paste in. That's not actually a contradiction, that's you not knowing where the list lives.

**R3:** ...Fair, on reflection it isn't a logical contradiction. But it's still a real gap: the guide never tells me Action Constants might be managed in a completely different part of the UI than the Default Inputs table I'm already looking at. If I go looking for a "type: Action Constant" dropdown next to `f5_username` and it's not there, the guide as written gives me nothing.

**Chair:** That I'll accept. Half your finding stands.

**Verdict:** Partial fix. Did not touch the "paste JSON directly" instruction (it's correct). Added a note that Action Constants may live in their own separate list/tab depending on version, so an engineer who doesn't see that option in the Default Inputs area knows to look elsewhere before escalating.

---

## R4 walks the update path: the backup you can't actually use

**R4:** Checklist 2.4, update path: "screenshot the whole Default Inputs table" as your backup. `F5_SHARED_PASSWORD` is a Secret. Secrets are masked in the UI. You cannot screenshot a value that isn't shown. Then Section 7, rollback, says to restore from "your backup script and Default Inputs screenshot." That instruction is not just incomplete, it's **impossible to execute as written** — there is no password in that screenshot to restore.

**Chair:** That's not a wording nitpick, that's a rollback plan that fails exactly when you need it most. Anyone want to argue this was already covered?

**R1 (returning):** I checked the *SOP's* claim about Secret write-only limitations in Round 1 — content3.js already said "Secret values can't be exported for backup." But that's a disclosure in the reference document. Nobody connected it to the actual step-by-step backup instruction in the Guide still telling you to screenshot it as if that were sufficient.

**Chair:** So we documented the limitation and then ignored our own documentation three sections later. That's worse than not knowing.

**Verdict:** Fix, and not lightly. Checklist 2.4 now states explicitly that the password cannot be backed up at all, and instead has the engineer write down *where it needs to be re-sourced from* if rollback is ever needed. Rollback (§7.1) repeats this instead of quietly assuming a screenshot works. Also fixed the same lossy-backup problem for the JSON subnet registry — a screenshot of a JSON blob is a bad backup for something the guide itself says is comma/brace-sensitive; now instructed to copy the literal text.

---

## R4's failure injections — Chair demands the receipts

**Chair:** You were told to break it on purpose. Four ways. Walk me through each and don't be generous — does the guide actually catch it, or does it just sound like it would?

**R4, mistake (a) — truncated paste, last line of the Python file gets cut off:**
Caught well. Step 4.7's checkpoint is mechanical and specific — "confirm the last non-blank line is `    }`" — that fails immediately, before Save is even clicked. Backed up further by the mandatory 5.2 syntax check. No note needed here.

**Chair:** Good, one clean pass. Next.

**R4, mistake (b) — `EnvironmentType` typed with a capital E instead of `environmentType`:**
Caught *at the moment of creation* — step 3.5's own checkpoint names this exact typo. But if missed there, it is **not** diagnosed anywhere downstream. The action would throw a raw JavaScript reference error when run, and the Troubleshooting table has no row for that symptom — the nearest row ("Deployment Name field stays blank") points at the *Custom Form's* binding, not the vRO action's own input spelling. Someone hits an unlisted error and the table actively points them at the wrong subsystem.

**Chair:** An engineer follows your own troubleshooting table into the wrong investigation. That's not a missing row, that's a misleading one.

**Verdict:** Fix. Added a specific Troubleshooting row for a script/reference error mentioning `environmentType`, pointing back at §3.5's input spelling — separate from the existing binding-related row.

**R4, mistake (c) — trailing comma in the `F5_VIP_SUBNET_REGISTRY` JSON:**
This is the one I want the room's full attention on. The error message when this *does* trigger is genuinely good and matches Troubleshooting exactly. The problem is it only triggers when a request needs an **auto-assigned** VIP — and Section 5.4's mandated end-to-end test never told the engineer to test that case. Every example in the test steps supplies an explicit IP. You can pass all five mandatory checks, sign off Section 9, and ship a corrupted registry that only detonates on the client's first real auto-assign request — which the script's own header comment says is meant to be the normal path.

**Chair:** So the one test we call mandatory doesn't test the default way this feature is actually meant to be used.

**R2 (returning skeptic):** That's a sharper version of something I flagged in Round 1 in spirit — "signing off based on vRA showing success rather than the real device" — but I hadn't gone as far as saying the *test itself* has a coverage hole. This is a better catch than mine.

**Chair:** Noted, and fixed — no partial credit here, this one ships broken otherwise.

**Verdict:** Fix. Section 5.4's first test request now explicitly requires leaving the destination IP blank/auto for at least one of the two test requests, specifically to exercise this code path. Added a matching note in the SOP's technical reference (§6.5) explaining why.

**R4, mistake (d) — password saved as Default instead of Secret:**
Best-defended of the four, no action needed. Three independent, explicitly-worded gates all name this exact field: the creation step, the post-save confirmation, and its own line in the sign-off table. Because this defect produces no runtime error (the code reads a Default or Secret input identically), there's correctly no Troubleshooting row for it — that's not a gap, a crash-based table has no reason to carry a non-crashing defect.

**Chair:** Agreed, leave it alone.

---

## A dispute the Chair does not fully concede

**R4:** One more. The per-item sign-off tables from Round 1 — I'll grant they fixed the "one blanket approval" problem R2 flagged, but a row that just says "Reviewed: Yes / Disposition: accepted" with nothing behind it is still gameable. Nothing stops someone from filling in all seven — now nine — rows in thirty seconds with no real client conversation.

**Chair:** You're right that I can't stop someone from lying on a form. I'm not going to pretend I can engineer my way out of a dishonest signer with more table columns. What I *can* do is make a lie more visible.

**R1 (returning):** That's a reasonable line to draw. Don't over-build a control that can't actually control the thing it's worried about.

**Verdict:** Partial, deliberate non-fix. Added an evidence column (screenshot/ticket reference) to every sign-off row in both documents, and a note that an evidence-free row is a sign of a rubber-stamped review, not a completed one. Did **not** attempt to build an approval workflow, second-signer requirement, or anything heavier — that's a process control belonging to the client's own change-management tooling, not something a static Word document and Markdown guide can enforce. Recorded here as a conscious scope boundary, not an oversight.

---

## Regressions R1 and R2 found in Round 1's own fixes

**Chair:** Before we close — you two came back specifically to check whether Round 1's fixes held up, not just to re-approve them. What actually broke?

**R1:** Two things, both self-inflicted by the renumbering in Round 1. First, the Troubleshooting table still pointed engineers at the old reactive "§5.1" location for creating the Configuration Element, even though Round 1 added a new proactive step, 3.12, specifically so people wouldn't have to discover it via an error message. The table just never got updated to match. Second, the SOP's own Section 12 risk item 1 was written in present tense — "despite header comments elsewhere in the script describing" a credential map that doesn't exist — when that map description had *already been removed* from the script two paragraphs earlier in the same document. The document was contradicting its own edit.

**Chair:** Both fixed?

**R1:** Confirmed against the current files, yes.

**R2:** I found the sibling problem — the SOP's new "second council review" section itself miscounted which risk items it was referring to. It said "Section 12 items 2 and 3" for the shared-credential and TLS findings; those are actually items 1 and 3. Item 2 is credential storage type, unrelated. That error sat inside the exact paragraph claiming rigor about this review process — the least acceptable place for a numbering mistake.

**Chair:** Confirmed and fixed. That's twice in one round we caught the summary of a fix being wrong even after the fix itself was right. Lesson for next time: **update the cross-references and self-descriptions in the same edit as the fix, never after.**

---

## Two disclosed-risk gaps neither new reviewer was asked to find, but R2 found anyway

**R2:** Outside the scripted brief — the VIP auto-assignment logic has the exact same unprotected read-increment-write race condition as the deployment-naming sequence counter. The naming race is disclosed and explicitly accepted as a low-stakes cosmetic risk. The VIP race is not disclosed anywhere, and a collision there is a materially worse outcome — two virtual servers could get handed the same IP.

**Chair:** Why wasn't this caught in Round 1?

**R2:** Because Round 1's brief was "verify claims and hunt for contradictions," not "find every code path structurally similar to an already-disclosed risk." Nobody was looking for a sibling bug to one we'd already found and forgiven.

**Chair:** Fair process gap, not a competence gap. Fixed.

**R2, second:** Related — there is no rollback story at all for anything the automation already created on the real F5 device before a failure or a decision to roll back. Rollback as written only ever talks about the two scripts. If a request creates a node and a pool and then fails on the virtual server step, those objects just sit there, undocumented, with nobody told to go look.

**Chair:** That one should have been obvious from day one. Fixed, and it's not getting buried as a footnote — it's now a named risk item in both documents *and* its own rollback subsection, because "check the device" is a real action someone has to actually take, not just a sentence to skim past.

---

## Closing verdict

**Chair:** Summary, for the record. Two returning reviewers verified nine Round 1 fixes each and confirmed all of them held — but still found two real, self-inflicted regressions from the renumbering itself, which is exactly why "verify, don't trust" was the right brief. Two new reviewers, cold, hit a hard stop in the first five minutes on an undefined human dependency, found a mandatory step that breaks the document's own "always tells you exactly where to click" promise, found a rollback instruction that is *literally impossible to execute* for a Secret value, and found that the one test we call mandatory doesn't exercise the one code path most likely to hide a shipped defect. That is not a "well-written guide with some rough edges." That was a guide that would have gotten a real engineer stuck, or worse, gotten them to sign off on something broken, on their first attempt.

All of it is fixed now except the one thing I'm not going to pretend a document can fix — a dishonest signature — and that's recorded as a deliberate boundary, not a miss.

**This does not mean the review process stops here as a matter of course.** It means this round's findings are closed. If this deployment moves to a different client environment, a different vRA/vRO version, or the scripts change again, this council reconvenes — the same way it did today.

---

*Findings and fixes in this document are drawn from four review-agent reports run against the deployment package on 2026-08-31. Every "Verdict" above corresponds to an actual edit made to `DEPLOYMENT_GUIDE.md` and/or `build/content*.js` (source for `SOP.docx`) in this session, re-verified by rebuilding `SOP.docx` and visually inspecting the rendered output.*
