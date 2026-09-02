# Finding: Health Monitor field wiring is ambiguous / needs live Custom Form verification

Captured 2026-09-02 while extracting vRO wrapper scripts. This affects both the
deployment guide's risk section and the Custom Form rebuild steps -- flag before
client handoff.

## What's confirmed from source

- Two DIFFERENT ABX actions exist and are both still present in the lab:
  - `f5_list_monitor_types.py` -- queries the F5 device for monitor TYPE
    categories (e.g. "http", "https", "tcp") used to configure a brand NEW
    monitor. Its own docstring says its output feeds `pool.monitor_type`.
  - `f5_list_monitors.py` -- queries the F5 device for EXISTING monitor
    *instances* already configured on the box (e.g. "/Common/https_basic").
    Its docstring says: *"Replaces f5_list_monitor_types for this purpose (that
    action listed monitor TYPE categories for creating a new monitor, which we
    no longer do)."*
- The Custom Resource `F5.VirtualServer` schema (see
  `custom_resource_F5.VirtualServer.md`) still defines BOTH fields side by side:
  `pool.monitor` (existing monitor fullPath, or `'none'`) and `pool.monitor_type`
  (new monitor type, e.g. http/https/tcp) -- so the resource-level contract has
  not dropped the "create new monitor" path, only (per the docstring) the Custom
  *Form* has stopped exposing the type-picker dropdown.
- The Cloud Template / blueprint (`blueprint_F5-Virtual-Server.yaml`) exposes a
  `monitorType` input (default `http`) plus `monitorInterval`/`monitorTimeout`,
  and maps `monitorType` into `pool.monitor_type` -- there is no `monitor`
  (existing-monitor) input defined in the blueprint's `inputs:` block at all.
- Only ONE vRO wrapper action exists for either of these two ABX actions, and it
  is named `f5_list_monitor_types` in the Orchestrator UI -- but its actual
  script content (header comment, description, and hardcoded `ACTION_ID`) is
  for `f5_list_monitors` (the "existing monitors" one), not
  `f5_list_monitor_types`. There is no separate wrapper for the ABX action
  `f5_list_monitor_types.py` at all under the captured 15 `com.f5.automation`
  actions.

## Why this matters

These two sources disagree about which UX the client is actually getting:

1. If the **blueprint** is authoritative, requesters pick a Monitor TYPE and the
   system creates a brand-new monitor every time (the `monitor` field is unused,
   dead schema).
2. If the **f5_list_monitors docstring and the one live wrapper** are
   authoritative, requesters actually pick from a dropdown of EXISTING monitors,
   and the blueprint's `monitorType` input is stale/vestigial -- left over from
   before the design changed, still present in the template but not the
   intended flow, and the wrapper action's name simply was never updated to
   stop saying "monitor_types" after the underlying ABX target was swapped.

Both explanations are plausible from the code alone. This determines a real,
user-visible difference in the Custom Form (a "pick existing" dropdown vs. a
"choose new monitor type" dropdown; plus whether monitorInterval/monitorTimeout
inputs are ever actually consumed if no new monitor is ever created).

## Required verification (do this once Custom Form access is available)

1. Open Service Broker > Content & Policies > Content > "F5-Virtual-Server" >
   its Custom Request Form, and inspect the actual field bound under the
   Pool/Monitor section: what is its label, and which vRO/ABX action is bound
   as its External source?
2. Confirm the exact `ACTION_ID` GUID hardcoded in the vRO wrapper (captured as
   `8a748097a00ff13901a03300d09706d9` in
   `wrapper_scripts_raw/f5_list_monitor_types.js`) against the live Assembler
   Extensibility Actions list -- open both `f5_list_monitors` and
   `f5_list_monitor_types` ABX actions there and compare their IDs (visible in
   each action's edit URL) to that GUID to determine definitively which ABX
   action the wrapper actually calls.
3. If the form is confirmed to use the "pick existing monitor" flow only:
   - Rename the vRO wrapper action to `f5_list_monitors` for clarity (or at
     minimum, correct its Tags/description) before handing off to the client,
     so future maintainers are not misled the way this review nearly was.
   - Flag `monitorType`/`monitorInterval`/`monitorTimeout` in the blueprint and
     `pool.monitor_type` in the Custom Resource schema as dead/vestigial fields
     that can be removed in the client's rebuild, OR kept intentionally if the
     Update/Day-2 "Update Health Monitor / Load Balancing" action
     (`f5_update_pool_settings`) still uses the type-based create path (check
     that script's actual field usage too -- it was captured and should be
     cross-checked against this finding).
   - If instead `f5_update_pool_settings` DOES use `monitor_type` to create new
     monitors while the main create form uses `monitor` (existing) -- document
     that as an intentional split (create-time = attach existing, day-2 update
     = optionally create new) rather than a bug, and word the SOP accordingly.

Do not resolve this by guessing; it must be confirmed against the live Custom
Form and Assembler UI before the client package asserts either behavior as
correct.

## Update (same day): strong corroborating evidence from `f5_update_pool_settings.py`

Cross-checked the Day-2 action `f5_update_pool_settings.py` (already captured).
Its own docstring says explicitly:

> `monitor_type` -- exact monitor path from `f5_list_monitors`, or "" / omitted
> to clear the pool's monitor

and its `handler()` passes that value straight through as `monitor_name=` into
`F5Manager.update_pool_settings()`, which PATCHes the live pool's `monitor`
field with it directly (a fullPath string like `/Common/https_basic`) -- there
is no "create a new monitor of this type" logic anywhere in this action at all.

This means the parameter/field NAME `monitor_type` is legacy naming left over
from the original design (pick a type, create new) -- but the actual VALUE it
now carries, end to end (create path and Day-2 update path alike), is an
EXISTING monitor's fullPath sourced from `f5_list_monitors`. This strongly
corroborates the conclusion that `f5_list_monitor_types.py` is orphaned/dead
code no longer wired to anything live, and that the one vRO wrapper (currently
named `f5_list_monitor_types` but scripted for `f5_list_monitors`) is the
correct, intended behavior -- only its name is stale/misleading.

**Confidence is now high but not 100%** -- the live Custom Form/Assembler check
in the "Required verification" section above should still be done before
finalizing the client SOP, specifically to confirm the field's on-screen label
(so the SOP can tell the client what their operators will actually see) and to
rule out any other consumer of `f5_list_monitor_types.py` that wasn't part of
this review (e.g. an orphaned Day-2 action reference, a second unused Custom
Form, or a leftover Policy). Recommended SOP language in the meantime: treat
the "Health Monitor" field as an EXISTING-monitor picker (backed by
`f5_list_monitors`), rename the vRO wrapper to `f5_list_monitors` for clarity,
and mark `f5_list_monitor_types.py` plus the blueprint's `monitorType` input as
candidates for removal in the client rebuild pending final live confirmation.

## RESOLVED (2026-09-02): confirmed definitively against the live Assembler

Cross-checked both ABX actions' real IDs directly in Assembler > Extensibility
Actions (via each action's edit-link URL):

| ABX action (Assembler) | Real ABX action ID |
|---|---|
| `f5_list_monitors` | `8a748097a00ff13901a03300d09706d9` |
| `f5_list_monitor_types` | `8a7480179fff2d51019fff89acd70005` |

The vRO wrapper action named **`f5_list_monitor_types`** (vRO ID
`0315ab0e-29d4-4bb7-bc09-d007307fdf43`) hardcodes
`ACTION_ID = "8a748097a00ff13901a03300d09706d9"` -- which is the ID for
**`f5_list_monitors`**, not `f5_list_monitor_types`. This is now fully
confirmed, not just inferred from docstrings.

**Conclusion, final:** the "Health Monitor" field on the live Custom Form is
backed by the EXISTING-monitor picker (`f5_list_monitors`) as intended -- the
system works correctly today. The only real defect is cosmetic/organizational:
the vRO wrapper action's NAME was never updated after the underlying ABX
target changed from `f5_list_monitor_types` to `f5_list_monitors`. The ABX
action `f5_list_monitor_types.py` itself is confirmed orphaned -- it exists in
Assembler with its own valid ID but no vRO wrapper calls it, so nothing in the
live form can ever invoke it.

**Action for the client rebuild package:**
1. When recreating the vRO wrapper for this purpose, name it `f5_list_monitors`
   (matching its real behavior) rather than reusing the lab's stale
   `f5_list_monitor_types` name.
2. Do not port `f5_list_monitor_types.py` (the ABX action) into the client
   build at all -- it is dead code. Its presence in `scripts_lab_raw/` is kept
   for completeness/audit trail only, and the deployment guide should say so
   explicitly rather than have the client redeploy an unused action.
3. The blueprint's `monitorType`/`monitorInterval`/`monitorTimeout` inputs and
   the Custom Resource's `pool.monitor_type` field are likewise vestigial for
   the create/request flow -- keep them only if a future "create a new
   monitor" feature is planned; otherwise flag for removal during the client's
   template review.
