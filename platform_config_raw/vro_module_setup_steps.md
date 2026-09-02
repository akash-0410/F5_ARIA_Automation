# vRO Module Setup — `com.f5.automation`

Captured/derived from the lab on 2026-09-02. This section is required reading before
importing or hand-creating any of the 15 wrapper actions in `wrapper_scripts_raw/` --
every one of them lives inside this module, and the Orchestrator client will not let
you create an action without a module (package) to put it in.

## Background

In vRealize/Aria Automation Orchestrator, actions are not free-floating -- each one
belongs to a "module" (also shown as "Package"/namespace in older UI versions). The
lab's 15 F5 wrapper actions all live in a single module named `com.f5.automation`.
This is a plain organizational namespace (like a Java package); it is NOT the same
thing as an Orchestrator "Package" export bundle, though the two are easy to confuse
in the UI since both use the word "package."

All 15 actions also carry a matching tag, `com.f5.automation`, which is how the
lab's Actions list filter (`Tags: com.f5.automation`) finds all of them at once. The
module namespace and the tag happen to share the same string in this build, but they
are two independent settings on each action -- setting one does not set the other.

## One-time setup: create the module (if not already present)

Do this once per Orchestrator instance, before creating the first wrapper action:

1. In the Orchestrator client (`https://<vra-host>/vco/` -> **START THE AUTOMATION
   ORCHESTRATOR CLIENT** -> opens `orchestration-ui`), go to **Library > Actions**.
2. Click **NEW ACTION**.
3. In the "Module" field, check whether `com.f5.automation` already appears in the
   autocomplete/dropdown.
   - **If it appears**: select it. The module already exists (someone created it,
     or a prior action was already saved into it) -- do not create a duplicate.
   - **If it does not appear**: type `com.f5.automation` into the field exactly as
     shown (all lowercase, dot-separated, no spaces). Saving the first action with
     this module name creates the module implicitly -- there is no separate
     "create module" button/dialog in this UI version. From then on it will appear
     in the autocomplete for every subsequent action.
4. Name the action (e.g. `f5_vra_run_action` for the generic wrapper, or
   `f5_list_<x>` for a specific one), set **Runtime Environment** to `JavaScript`,
   and click the checkmark/create to save the shell before pasting in script code.

## Every action: apply the tag (if not already added)

The module field alone does not populate the `com.f5.automation` tag -- they are
separate. After creating (or when reviewing) each action:

1. Open the action, stay on (or return to) the **General** tab.
2. Look at the **Tags** field. If a `com.f5.automation` chip is already listed,
   skip this step -- do not add a duplicate tag.
3. If it is missing, click into the "Enter a new tag" box, type `com.f5.automation`,
   and press Enter to add it as a chip. Click **SAVE**.
4. Repeat for all 15 actions. This tag is what lets an administrator filter
   **Library > Actions** by `Tags: com.f5.automation` to see the whole wrapper set
   at a glance (as documented in the wrapper capture work above) -- an action that's
   in the right module but missing the tag will still work, but it will silently
   fall out of that filtered view, which makes it easy to forget during future
   maintenance. Treat "module set AND tag present" as the definition of "done" for
   each wrapper action, not module alone.

## Order of operations for a fresh client environment

When standing this up from scratch (not just editing an existing lab), do these in
order:

1. Create/confirm the `com.f5.automation` module exists (steps above), via the
   first action you create.
2. Create the generic `f5_vra_run_action` wrapper first (see
   `wrapper_scripts_raw/f5_vra_run_action.js`) and populate its Configuration
   Element dependency (`F5-Automation-Credentials` / `vraRefreshToken`) -- every
   other wrapper except `f5_generate_deployment_name` and
   `f5_nodes_from_vm_selection`'s ABX-calling path depends on it being present and
   working, since they call `System.getModule("com.f5.automation").f5_vra_run_action(...)`
   internally.
3. Create the remaining 13 specific wrapper actions, each in the same module, each
   tagged the same way, each with its `ACTION_ID` constant updated to match the
   **client's own** re-created ABX action IDs (the IDs hardcoded in the lab's
   scripts are lab-specific GUIDs and will not exist in a fresh tenant -- see the
   per-action notes in `wrapper_scripts_raw/` and the main deployment guide for the
   full re-pointing procedure).
4. Verify with **Library > Actions**, filter `Tags: com.f5.automation`, and confirm
   all 15 (14 wrappers + the generic runner) are listed together before wiring any
   of them into the Custom Form.

## Known risk called out separately (RESOLVED -- see finding doc)

The vRO wrapper action named `f5_list_monitor_types` (vRO ID
`0315ab0e-29d4-4bb7-bc09-d007307fdf43`) was found to actually call the
`f5_list_monitors` ABX action (confirmed by matching its hardcoded `ACTION_ID`
against the real ABX action IDs in Assembler). The live Custom Form behavior is
correct (it shows existing monitors, as intended); only the wrapper's NAME is
stale. Full analysis, confirmed IDs, and the recommended fix for the client
rebuild (name the new wrapper `f5_list_monitors`; do not port the orphaned
`f5_list_monitor_types.py` ABX action) are in
`finding_monitor_type_vs_monitors.md` in this same folder -- read that before
finalizing the wrapper-creation steps for this action.
