# Bootstrap Scripts — UNVERIFIED, READ THIS FIRST

**Status: UNVERIFIED.** These scripts were written against VMware's documented
Aria Automation 8.x REST APIs, using the same auth pattern proven live in
`f5_vra_run_action.js` (refresh-token -> Bearer exchange). They have **not**
been executed against any Aria Automation tenant — there is no client test
environment available to run them against. Treat them as a strong starting
point that removes most of the manual clicking, not as a push-button
guarantee. Run them against a non-production project first, watch every
response, and fall back to the manual steps in `DEPLOYMENT_GUIDE.md` for
anything that errors.

Known areas of real API-version risk (verify against your tenant's own API
docs at `https://<vra-host>/automation-ui/api-docs` or `/vco/api/docs`
before trusting the output):

- The exact JSON body shape for `POST /abx/api/resources/actions` (ABX action
  create) has changed across Aria Automation 8.x point releases —
  `runtimeVersion` values and `actionType` enums in particular.
- The endpoint for **Action Constants** (`/abx/api/resources/action-constants`
  used below) is our best-effort guess based on the ABX actions API family —
  if it 404s, create the `F5_VIP_SUBNET_REGISTRY` constant by hand in
  Assembler > Extensibility > Actions > Constants instead (one-time, low
  effort) and skip that part of the script.
- The vRO Actions REST API (`/vco/api/actions`) create-with-module semantics
  vary slightly by version; the script includes a manual fallback path
  (paste-in via the Orchestrator client) if the API call fails.

## What's here

- `vra_bootstrap.py` — creates the 19 ABX Python actions from
  `scripts_lab_raw/` + `scripts/f5_create_virtual_server.py` in a target
  vRA project, sets Action Dependencies, and (best-effort) creates the
  `F5_VIP_SUBNET_REGISTRY` and `F5_DEVICE_REGISTRY` Action Constants.
- `vro_bootstrap.py` — creates the `com.f5.automation` module (implicitly, by
  creating the first action in it) and all 15 wrapper actions from
  `wrapper_scripts_raw/`, tagging each with `com.f5.automation`.
- `config.example.json` — fill in your tenant's host, project ID, and
  credentials reference before running either script.

## What these scripts deliberately do NOT do

- They do not set **Action Default Inputs / Secret Inputs** (`f5_username`,
  `F5_SHARED_PASSWORD`) on the ABX actions — Aria Automation requires Secret
  values to be entered through the UI (or a properly-scoped secrets API call
  this package does not assume you want automated); do this by hand per
  `DEPLOYMENT_GUIDE.md` Section 4.
- They do not create the Custom Resource, Cloud Template (blueprint), or
  Custom Form — those are schema/UI objects best built once by hand from the
  captured definitions (`platform_config_raw/`) so you can see and adjust
  field bindings as you go; scripting their creation blind is higher-risk
  than the ~30 minutes of manual work described in the guide.
- They do not create the vRO Configuration Elements
  (`F5-Automation-Credentials`, `F5-Automation/DeploymentNaming`) — these
  hold a refresh token and a mutable sequence counter respectively, and are
  small enough (one folder, one element, a couple of attributes each) that
  hand-creation is both faster and safer than API scripting here.
- They do not attach either Action Constant to the specific action that
  reads it (`F5_VIP_SUBNET_REGISTRY` → `f5_create_virtual_server`,
  `F5_DEVICE_REGISTRY` → `f5_list_clusters`) — this best-effort endpoint
  only creates the constant with placeholder JSON; the attach step (Action
  Default Inputs, Type = Action constant) and the real values are still
  manual, per `DEPLOYMENT_GUIDE.md` Section 4.3.

## Usage

```bash
pip install requests --break-system-packages
cp config.example.json config.json
# edit config.json: vra_host, vro_host, project_id, username, password, domain
python3 vra_bootstrap.py --config config.json          # dry-run by default
python3 vra_bootstrap.py --config config.json --apply  # actually creates things
python3 vro_bootstrap.py --config config.json --apply
```

Both scripts default to `--dry-run` (prints what it would do, calls nothing
that mutates state) unless `--apply` is passed. Run dry-run first and read
the output.
