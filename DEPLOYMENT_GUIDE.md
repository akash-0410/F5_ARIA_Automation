# F5 Automation — Deployment Guide (Build From Scratch)

This replaces the previous version of this guide. It walks through the entire
build, in the same order the real lab was built, click by click: where to go
in the UI, what to name things, what to type into which field, and where to
find the values (like the Project ID) that earlier versions of this guide
assumed you already knew. Screenshots referenced below (`screenshots/NN_*.jpg`)
are captured live from the working lab; a few steps that are always identical
regardless of environment (the vRO wrapper's General tab, Custom Resource
form, blueprint editor, Custom Form editor) are described in full click detail
in text — the lab's UI became temporarily unresponsive partway through this
capture session, so those particular screens aren't screenshotted this round.
If you want them, ask and I'll capture them in a follow-up pass; nothing below
depends on having the image to follow the steps.

Companion files: `SOP.docx` (day-2 operator runbook, with screenshots, for
after go-live), `bootstrap/` (optional unverified scripts that automate
steps 2 and 5 below).

---

## 0. Before you start: log in and find your way around

VMware Aria Automation bundles four sub-applications behind one login. You'll
use all four in this guide:

- **Assembler** — where you build ABX actions, Custom Resources, and Cloud
  Templates (blueprints). Most of this guide happens here.
- **Orchestrator** (also called "vRO" or "Embedded VRO") — a separate app
  with its own JavaScript actions, used for the 15 "wrapper" scripts.
- **Service Broker** — where you publish the finished template to a catalog
  end users can request from, and where the Custom Form lives.
- **Pipelines** — not used in this build.

**To log in and reach these apps:**

1. Go to `https://<your-vra-host>/automation/` (or just the bare hostname —
   it redirects). Log in with an account that has the **Cloud Assembly
   Administrator** role (in the lab, `configadmin`).
2. You land on a launcher page titled **"My Services"** with four tiles:
   Assembler, Orchestrator, Pipelines, Service Broker.
3. Click a tile to enter that app. Each app has its own top tab bar (e.g.
   Assembler's is **Home / Resources / Design / Infrastructure /
   Extensibility / Tenant Management**) and its own left-hand sidebar that
   changes depending on which top tab is selected.

**Important navigation note:** always get to a screen by clicking through
the tabs and sidebar from the launcher page, rather than pasting a deep
link URL into the address bar. Deep-linking into a specific sub-page
occasionally leaves the app in a stuck state where the URL changes but the
displayed page doesn't (a known quirk of this app's client-side routing).
If a page ever looks wrong for the URL shown, click one of the top tabs
(e.g. click **Infrastructure** then click back to the tab you wanted) to
force it to re-render, or open a fresh browser tab and navigate in from
the launcher again.

---

## 1. Find or create the Project, and find its Project ID

Everything else in this build (ABX actions, Custom Resources, blueprints) is
scoped to a **Project**. You need one before you create anything.

1. From the launcher, click **Assembler**.
2. Click the **Infrastructure** tab (top tab bar).
3. In the left sidebar, under **Administration**, click **Projects**.
   (See `screenshots/01_projects_list.jpg` — this is the Projects list; the
   lab has two, `F5-Automation` and `Test_f5`.)
4. **To create a new project:** click **+ NEW**, give it a name (e.g.
   `F5-Automation`), a description, and add the users/groups who should be
   Administrators/Members on the **Users** tab. Click the checkmark/Create.
   **To use an existing project:** click its card.
5. Click **OPEN** on the project's card (bottom-left of the card).
6. You're now on the project's **Summary** tab, showing its Name,
   Description, and an Overview list (Administrators, Members, Templates,
   Deployments, Actions, Secrets, etc.).

**Here's the answer to "where do I find the Project ID":** it is not printed
anywhere on this Summary page as a labeled field — Aria Automation doesn't
surface it in the UI text. It's in the **browser's address bar** once you've
opened the project. Look at the URL — it ends in a long
hyphenated hex string, e.g.:

```
.../provisioning-ui;ash=%2Fprojects%2Fedit%2Fd347d2fd-4e27-4a0d-b144-f5262d7a70a1
```

Everything after `/projects/edit/` — in this example
`d347d2fd-4e27-4a0d-b144-f5262d7a70a1` — **is the Project ID.** Copy it
somewhere; you'll need it for the bootstrap scripts' `config.json`
(`project_id` field) and it's useful to have on hand generally. (See
`screenshots/02_project_id_in_url.jpg` — the address bar is visible at the
top of the browser window, not inside the page itself, so it won't appear in
a screenshot that only captures the page content — check your own browser's
URL bar when you're on this screen live.)

If you ever need it again later and don't want to click through: **Projects**
list > hover or click a project > check the URL the same way.

---

## 2. Create the 19 ABX Extensibility Actions

These are the Python scripts that do the real work (talk to the F5 device's
REST API). Full source for all 19 is in `scripts_lab_raw/` (18 files) and
`scripts/f5_create_virtual_server.py` (1 file, kept separate from earlier
work on this project).

### 2.1 Open the Actions screen

1. In Assembler, click the **Extensibility** tab (top tab bar).
2. In the left sidebar, under **Library**, click **Actions**.
3. You'll see two sub-tabs under the "Actions" heading: **Actions** and
   **Action Constants**. Stay on **Actions**. (See
   `screenshots/03_actions_list.jpg` — this is the lab's live list, already
   populated with all 19; yours will start empty.)

### 2.2 Create one action (repeat for all 19)

1. Click **+ NEW** (top-left, next to "IMPORT"). A **"New Action"** dialog
   pops up. (See `screenshots/04_new_action_dialog.jpg`.)
2. **Name**: type the filename without `.py`, exactly — e.g.
   `f5_create_virtual_server`. Getting this exact match right matters: the
   vRO wrapper scripts in Section 5 are named to match, and a few of the
   wiring/audit notes in `platform_config_raw/` refer to actions by this
   exact name.
3. **Description**: optional, but recommended — paste the first line or two
   of the script's own docstring (each file's top comment block explains
   what it does).
4. **Project**: click into the field and start typing your project's name
   (e.g. `F5-Automation`) — it autocompletes as a dropdown. Click the
   matching result. (See `screenshots/05_new_action_project_picker.jpg`.)
5. Leave "Share with all projects in this organization" **unchecked** unless
   you specifically want that (the lab does not use it).
6. Click **NEXT**.
7. You're now on the action's edit screen — code editor on the left,
   settings panel on the right. (See `screenshots/06_action_editor_main.jpg`
   for the overall layout — this example shows an empty starter script;
   yours will have the same layout once you paste in real content.)
   - Top-left dropdowns: confirm **Type = Script**, and set the runtime
     dropdown to **Python 3.10** (or the closest available — check what
     versions your tenant's Assembler offers; it varies by Aria Automation
     point release).
   - **Delete the placeholder starter code** in the editor pane and paste
     in the full contents of the matching file from `scripts_lab_raw/` (or
     `scripts/f5_create_virtual_server.py` for that one action).
   - On the right panel: **Main function** should read `handler` (this
     matches every script's `def handler(context, inputs):` signature — do
     not change it).
   - **Dependency**: type `requests` (every one of these 19 scripts imports
     the `requests` library, which isn't in the sandbox by default — the
     action fails immediately with an import error if you skip this).
   - Leave **PaaS provider** as "Auto select" and leave "Set custom limits
     and retry options" unchecked, matching the lab.
   - **Default inputs**: leave empty for now — you'll come back and add
     `f5_username` / `F5_SHARED_PASSWORD` in Section 4, after all 19 exist.
8. Click **SAVE** (bottom-left).
9. Optionally click **TEST** to confirm the script saves and parses cleanly
   in the sandbox — it will fail on missing credentials/inputs at this
   stage, which is expected; you're only checking it doesn't fail with a
   Python syntax error.
10. Click **CLOSE**, then repeat from step 1 for the next file.

The 19 names to create (case-sensitive, must match exactly):

```
f5_create_virtual_server       f5_list_free_ips
f5_read_virtual_server         f5_list_oneconnect_profiles
f5_delete_virtual_server       f5_list_snat_pools
f5_update_pool_settings        f5_list_persistence_profiles
f5_update_backend_nodes        f5_list_lb_modes
f5_list_vcenter_vms            f5_list_clusters
f5_nodes_from_vm_selection     f5_list_environments
f5_list_monitors               f5_list_locations
f5_list_monitor_types  *see note below
f5_list_nodes_grid
f5_list_nodes
```

**Note on `f5_list_monitor_types`:** this action is confirmed **orphaned** —
nothing in the live system calls it (full analysis in
`platform_config_raw/finding_monitor_type_vs_monitors.md`). You can create
it anyway for a byte-for-byte faithful rebuild, or skip it entirely for a
cleaner client build — either is fine. If you skip it, skip its
corresponding wrapper too (see Section 3's note).

### 2.3 Record each action's ID as you go

After saving each action, its **ID is in the browser's URL** the same way
the Project ID was in Section 1 — look for a long hex string in the address
bar while the action is open. Keep a running list (name -> ID) in a text
file or spreadsheet — you'll need every one of these 19 IDs in Section 5 to
point the matching vRO wrapper at the right action.

If you'd rather not do this by hand, `bootstrap/vra_bootstrap.py --apply`
creates all 19 actions via the REST API and writes this ID list out
automatically as `bootstrap/created_action_ids.json` — see that folder's
README (marked unverified, since there's no test tenant to run it against
first).

---

## 3. Wrapper naming — one exception to "name it exactly the same"

`platform_config_raw/wrapper_to_abx_id_crosscheck.md` documents a full,
confirmed audit of every wrapper-to-ABX-action pairing. Thirteen of them
match by name exactly. **One does not:** the wrapper you'll build in Section
5 as `f5_list_monitors` should call the ABX action `f5_list_monitors` (not
`f5_list_monitor_types`) — this is the fix, not a step to reproduce a lab
mistake. If you're keeping the naming 100% identical to the lab for
traceability instead, see that crosscheck file for the exact historical
wrapper name (`f5_list_monitor_types`) and note in your own build log that
it actually points at `f5_list_monitors`.

---

## 4. Action Default Inputs, Secret Inputs, and Action Constants

Several of the 19 actions need credentials and two shared config values
before they can talk to a real F5 device. Do this after all 19 exist.

### 4.1 Which actions need which inputs

| Needs `f5_username` + `F5_SHARED_PASSWORD` | Needs `F5_VIP_SUBNET_REGISTRY` (Action Constant) | Needs `F5_DEVICE_REGISTRY` (Action Constant) |
|---|---|---|
| `f5_create_virtual_server`, `f5_read_virtual_server`, `f5_delete_virtual_server`, `f5_update_pool_settings`, `f5_update_backend_nodes`, `f5_list_nodes`, `f5_list_nodes_grid`, and every `f5_list_*` action that queries a live F5 device | `f5_create_virtual_server` only | `f5_list_clusters` only |

`F5_DEVICE_REGISTRY` is easy to miss because nothing in the Custom Form or
the wrapper chain references it by name — it only shows up inside
`f5_list_clusters.py`'s own docstring and its one `inputs.get(...)` call.
It's the data source behind the "F5 Cluster" dropdown, so without it that
dropdown silently returns zero options (no error — `f5_list_clusters`
degrades to an empty registry and just returns `{"options": []}`) and no
device can ever be selected on the form.

### 4.2 Add the Default Input and Secret Input to an action

1. Extensibility > Actions > open the action (click its name from the
   Actions list, or **OPEN** from its card).
2. On the right settings panel, find the **Default inputs** section (same
   place you saw the empty `target`/`World` example row in
   `screenshots/06_action_editor_main.jpg`).
3. Click into the empty **Type** dropdown on a blank row (or the "+" control
   if the UI shows one) and choose **Default**. In **Name**, type
   `f5_username`. In **Value**, type your F5 API service account's
   username — this is a plaintext field, appropriate for a username.
4. Add another row: **Type** = **Secret**. **Name**: `F5_SHARED_PASSWORD`.
   Choosing "Secret" here either opens a picker to select/create a vRA
   Secret (Infrastructure > Administration > Secrets — this is also where
   you'd manage it directly, e.g. to rotate the password later) or gives you
   an inline masked field depending on your Aria Automation version — either
   way, the value itself is never shown back in plaintext once saved.
5. Click **SAVE**.
6. Repeat for every action in the left column of the table above.

**Known risk to flag with the client now, not later:** this is ONE shared
username/password used for every F5 device this automation talks to. There
is no per-cluster credential map in the current code, despite a comment in
`f5_list_nodes.py`'s docstring that references a `F5_CREDENTIAL_MAP` pattern
— that pattern was never actually implemented. If the client's F5 clusters
use different credentials per device, raise this as a design gap before
go-live rather than trying to work around it by editing the scripts.

### 4.3 Create the Action Constants

There are two — create both the same way, on the same **Action Constants**
sub-tab, then attach each to the one action that actually reads it.

#### 4.3.1 `F5_VIP_SUBNET_REGISTRY`

1. Extensibility > Actions > click the **Action Constants** sub-tab (next to
   "Actions", visible in the top of `screenshots/03_actions_list.jpg`).
2. Click **+ NEW** (or the equivalent add control on that tab).
3. **Name**: `F5_VIP_SUBNET_REGISTRY`. **Value**: JSON, e.g.:
   ```json
   {
     "f5-cluster-01.client.example.com": {"cidr": "10.20.30.0/24", "reserved": ["10.20.30.1"]},
     "f5-cluster-02.client.example.com": {"cidr": "10.20.40.0/24", "reserved": ["10.20.40.1"]}
   }
   ```
   The key for each entry must exactly match the `host` value that
   `f5_list_clusters` will hand back for that device (the F5 Cluster
   dropdown's underlying value) — not a display name.
4. Save. On `f5_create_virtual_server`'s own edit screen, confirm this
   constant is now available/attached to the action (some Aria versions
   attach constants tenant/project-wide automatically once created; others
   require an explicit "add constant" step on the action — check your
   version's behavior live).

#### 4.3.2 `F5_DEVICE_REGISTRY`

This is the actual F5 device inventory — per `f5_list_clusters.py`'s own
docstring, it's designed to be the **only** place devices get onboarded or
retired; no script change is ever needed for that.

1. Same **Action Constants** sub-tab, **+ NEW** again.
2. **Name**: `F5_DEVICE_REGISTRY`. **Value**: JSON, keyed by Location then
   Environment (both of these must match the values from `f5_list_locations`
   and `f5_list_environments` exactly — `chanakyapuri`/`secunderabad` and
   `production`/`uat` in the lab), e.g.:
   ```json
   {
     "chanakyapuri": {
       "production": [{"label": "CHKY-PROD-F5-01", "host": "f5-cluster-01.client.example.com"}],
       "uat": [{"label": "CHKY-UAT-F5-01", "host": "f5-cluster-01-uat.client.example.com"}]
     },
     "secunderabad": {
       "production": [{"label": "SCB-PROD-F5-01", "host": "f5-cluster-02.client.example.com"}],
       "uat": [{"label": "SCB-UAT-F5-01", "host": "f5-cluster-02-uat.client.example.com"}]
     }
   }
   ```
3. Attach it to the **`f5_list_clusters`** action specifically, the same way
   you attached `F5_VIP_SUBNET_REGISTRY` to `f5_create_virtual_server` in
   4.3.1 step 4 — Action Default Inputs on `f5_list_clusters`: Name
   `F5_DEVICE_REGISTRY`, Type = Action constant.
4. **Cross-check against 4.3.1 before you consider this done:** every
   `host` value you add here should also appear as a key in
   `F5_VIP_SUBNET_REGISTRY` if that device needs auto-assigned VIPs — these
   are two independent JSON blobs and nothing in the code checks that they
   agree. A device present in `F5_DEVICE_REGISTRY` but missing from
   `F5_VIP_SUBNET_REGISTRY` will look fine right up until the first request
   against it that omits an explicit destination IP.

---

## 5. vRO Orchestrator — the module and the 15 wrapper actions

The Custom Form (Section 8) doesn't call ABX actions directly — it calls
these 15 JavaScript "wrapper" actions in Orchestrator, which in turn call
the ABX actions from Section 2. This is the layer the earlier version of
this guide was missing entirely.

### 5.1 Get into Orchestrator

1. From the launcher ("My Services"), click **Orchestrator**.
2. This opens a separate app (URL contains `orchestration-ui`), with its own
   left sidebar: **Dashboard**, **Workflows**, **Actions**, **Configurations**,
   etc. — this is a different app from Assembler, with different navigation,
   even though it's part of the same Aria Automation login.

### 5.2 Create the module (one-time, before the first wrapper)

Full detail already captured in `platform_config_raw/vro_module_setup_steps.md`
— summary:

1. Library > Actions > **New Action**.
2. In the **Module** field, type `com.f5.automation`. If it doesn't appear
   as an existing autocomplete suggestion, that's fine — typing it fresh and
   saving the first action creates the module automatically. There is no
   separate "create module" button anywhere in this UI.
3. **Name**: `f5_vra_run_action` (create this one first — every other
   wrapper except `f5_generate_deployment_name` calls it internally via
   `System.getModule("com.f5.automation").f5_vra_run_action(...)`).
4. **Runtime**: JavaScript.
5. Paste in the full contents of `wrapper_scripts_raw/f5_vra_run_action.js`.
6. On the action's **General** tab, find the **Tags** field and add a tag:
   type `com.f5.automation`, press Enter to commit it as a chip. (This tag
   is separate from the module — setting one does not set the other; both
   are needed for the action to show up correctly when a future maintainer
   filters Library > Actions by `Tags: com.f5.automation`.)
7. Save.

### 5.3 Create the remaining 14 wrapper actions

Same steps as 5.2 (module = `com.f5.automation`, already exists now; add
the same tag each time) for each remaining file in `wrapper_scripts_raw/`:

```
f5_generate_deployment_name    f5_list_lb_modes
f5_list_vcenter_vms            f5_list_persistence_profiles
f5_nodes_from_vm_selection     f5_list_locations
f5_list_monitor_types *        f5_list_environments
f5_list_nodes_grid             f5_list_clusters
f5_list_nodes
f5_list_free_ips
f5_list_oneconnect_profiles
f5_list_snat_pools
```

\* Per Section 3, name this one `f5_list_monitors` in your build instead
(pointing at the `f5_list_monitors` ABX action), unless you're deliberately
preserving the lab's stale naming for a 1:1 audit trail.

**Before saving each one**, open the pasted script and find the line near
the top that reads:

```js
var ACTION_ID = "8a7480179fff2d51019fff86f6f30002";  // (example)
```

Replace the hardcoded ID with the **real ABX action ID you recorded in
Section 2.3** for the matching action — the lab's IDs are specific to that
tenant and will not exist in yours. `f5_vra_run_action` and
`f5_generate_deployment_name` don't have this line (they either take the
target action ID as a parameter, or call no ABX action at all) — skip this
step for those two.

Once saved, you can view an action's own layout on its **Script** tab (code
editor on the left, an API Explorer / Properties / Inputs panel on the
right listing declared inputs and return type) — see
`screenshots/07_vro_action_script_tab.jpg` for what this looks like using
the lab's live `f5_list_clusters` action as an example (inputs `location`
and `environment`, both optional strings, return type Array of string). The
**General** tab (a separate tab next to Script, not shown in this
screenshot this round) is where the Module and Tags fields from steps 5.2/
5.3 live.

### 5.4 Create the two Configuration Elements

These are small enough to create by hand rather than script. In
Orchestrator's left sidebar, find **Configurations** (sometimes under a
"Library" or "Assets" grouping depending on version):

1. **New Configuration** (or "New folder" then "New configuration" inside
   it, depending on version) — Folder/category: `web-root`. Name:
   `F5-Automation-Credentials`.
   - Add an attribute named `vraRefreshToken`, type **SecureString**.
   - Value: a long-lived vRA refresh token for a service account (e.g.
     `configadmin` or a dedicated integration account) — obtain this once by
     calling `POST /csp/gateway/am/api/login` with that account's
     credentials and copying the `refresh_token` from the response
     (`bootstrap/_auth.py`'s `get_bearer_token()` shows this exact call if
     you want to script the lookup, though the value itself must still be
     pasted in by hand — never write it to a file in this package).
   - `f5_vra_run_action` reads this value on every single invocation to
     mint a short-lived Bearer token — it never stores the Bearer token
     itself anywhere.
2. **New Configuration** — Folder: `F5-Automation`. Name: `DeploymentNaming`.
   - Add an attribute named `sequenceCounters`, type **Properties**. Leave
     it empty — `f5_generate_deployment_name` initializes and updates it
     automatically the first time it runs.

### 5.5 Verify

Library > Actions > filter by `Tags: com.f5.automation` — you should see 15
actions (14 wrappers + `f5_vra_run_action`). Open `f5_list_locations` and
run it manually with no inputs — if Section 5.4's Configuration Element is
set up correctly and the refresh token is valid, it should return a list of
options with no error. This is your smoke test before moving on.

---

## 6. Custom Resource: `F5.VirtualServer`

1. Back in **Assembler**, click the **Design** tab, then in the left
   sidebar click **Custom Resources**.
2. **+ New Custom Resource**. Based on: **ABX user-defined schema**.
3. Resource Type: `Custom.F5.VirtualServer`.
4. Switch the properties editor to **Code** view (usually a toggle near the
   top of the schema editor) and paste in the full YAML block from
   `platform_config_raw/custom_resource_F5.VirtualServer.md` (under its
   "Properties schema" heading) — this is captured verbatim from the lab.
5. **Lifecycle Actions** tab: bind **Create** and **Update** to
   `f5_create_virtual_server`, **Read** to `f5_read_virtual_server`,
   **Destroy** to `f5_delete_virtual_server`.
6. **Additional Actions** (the "Day 2" menu operators see on a deployed
   resource) — add three:
   - `Update Health Monitor / Load Balancing` -> `f5_update_pool_settings`
   - `Resync from F5 Device` -> `f5_read_virtual_server`
   - `Update Backend Nodes / Pool Members` -> `f5_update_backend_nodes`

   For each, click its **Request Parameters** icon (a small form-mapping
   icon next to the row) and map which of the resource's fields that action
   should receive — don't assume this is automatically 1:1 with the
   action's raw inputs; check each mapping explicitly.
7. Toggle **Activate** ("Make available in blueprints") on.
8. Under **Scope**, leave "Available for any project" **off** and
   explicitly add your project (e.g. `F5-Automation`) unless you deliberately
   want this resource usable from every project in the org.
9. Save.

---

## 7. Cloud Template (Blueprint)

1. Design tab > left sidebar > **Templates** (sometimes labeled "Cloud
   Templates").
2. **+ New** > give it a name (e.g. `F5-Virtual-Server`) > select your
   project > Create.
3. Switch to the **Code** editor (toggle top-right of the canvas) and
   replace the placeholder content with the full YAML from
   `platform_config_raw/blueprint_F5-Virtual-Server.yaml`.
4. Check every `${input.*}` reference in the `resources:` block against the
   `inputs:` block above it — they must match by name exactly. This
   matters doubly once you build the Custom Form in Section 8, because the
   Custom Form's field names must also match these input names exactly.
5. Click **Test** (top toolbar) to validate the template compiles with zero
   errors against your project's configured resources.
6. **Version** > give it a version label (e.g. `1.0`) > publish.

**Decision to make with the client before finalizing:** the blueprint's
`monitorType`, `monitorInterval`, and `monitorTimeout` inputs, and the
Custom Resource's `pool.monitor_type` field, are not exercised by any live
code path in the lab (see
`platform_config_raw/finding_monitor_type_vs_monitors.md` — the real
"Health Monitor" behavior end to end is an existing-monitor picker driven by
`monitor`/`f5_list_monitors`, not a new-monitor-type creator). Keep these
fields only if the client wants a future "create a brand-new monitor" flow;
otherwise remove them from both the blueprint's `inputs:` and its
`resources:` mapping together (removing one without the other leaves a
dangling reference that the template validator will flag).

---

## 8. Custom Form

This is the screen end users actually see when requesting a virtual server.
It was not captured live from the lab this round (the Content list's row
detail view was unresponsive during this session) — build it from the
blueprint's own inputs using the field-by-field binding table below, which
is derived directly from the wrapper wiring in Sections 3 and 5, cross-
checked against the blueprint and Custom Resource schema. This is the one
part of the build worth a live side-by-side check against the lab before
you finalize the client's version.

1. Go to **Service Broker** (from the launcher, or via Assembler's app
   switcher).
2. **Content & Policies** > **Content**. Find your template (e.g.
   `F5-Virtual-Server`) in the list — it will show a **Content Source**
   column and a **Custom Request Form** column.
3. Open the row's form editor (in the lab this is reached by expanding the
   row — look for a chevron/expand icon at the left edge of the row, not
   the row's name text itself, which only selects/highlights the row rather
   than opening anything) and enable **Custom Form** if it isn't already.
4. The form designer auto-generates one field per blueprint input. For
   each field below, click it, open **Value > External source**, and set
   the vRO action and any upstream field mapping shown in the table:

| Form field (blueprint input) | External source (vRO action) | Depends on / cascades from |
|---|---|---|
| `location` | `f5_list_locations` | — |
| `environmentType` | `f5_list_environments` | — |
| `f5Cluster` | `f5_list_clusters` | `location`, `environmentType` |
| `vsName` | free text (optionally default from `f5_generate_deployment_name`) | `location`, `environmentType` |
| `virtualIpAddress` | `f5_list_free_ips` | `f5Cluster` |
| `vsOneConnectProfile` | `f5_list_oneconnect_profiles` | `f5Cluster` |
| `persistenceProfile` | `f5_list_persistence_profiles` | `f5Cluster` |
| `loadBalancingMode` | `f5_list_lb_modes` | — |
| `monitorType` (labeled "Health Monitor" on-screen in the lab) | `f5_list_monitors` (existing-monitor picker — see Section 3) | `f5Cluster` |
| `vsSnat` | `f5_list_snat_pools` | `f5Cluster` |
| `nodes[].name` (data grid row) | `f5_list_nodes` and/or `f5_list_vcenter_vms` + `f5_nodes_from_vm_selection` | `f5Cluster` |

5. For each cascading field, set its **Value constraints / dependencies** so
   it re-queries whenever its upstream field changes (e.g. `f5Cluster`
   re-runs whenever `location` or `environmentType` changes) — this is a
   per-field toggle/setting in the same "External source" panel, usually a
   multi-select of which other fields to watch.
6. Save the Custom Form.

---

## 9. Publish and verify end to end

1. Service Broker > **Content Sources** > sync your project's Cloud
   Template content source (create it first if this is a genuinely new
   tenant with no content source configured yet).
2. Content & Policies > Content > confirm the template appears with
   **Custom Request Form: Enabled**.
3. Content & Policies > **Policies** (or directly on the catalog item) >
   entitle the right project(s) / users / groups so they can see it in the
   catalog.
4. Submit one real test request against a non-production F5 device end to
   end: confirm every cascading dropdown populates in order — **F5 Cluster**
   specifically will come back empty if `F5_DEVICE_REGISTRY` (Section 4.3.2)
   wasn't created or attached correctly, which is otherwise a silent failure
   — submission actually creates the pool/nodes/virtual server on the
   device, and each of the three Day-2 actions from Section 6 runs without
   error against the deployed resource.
5. Only once that succeeds, hand `SOP.docx` to the client's operators.
