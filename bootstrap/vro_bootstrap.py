#!/usr/bin/env python3
"""
vro_bootstrap.py -- UNVERIFIED. See bootstrap/README.md before running.

Creates the com.f5.automation vRO module (implicitly, via the first action
created in it) and all 15 wrapper actions from ../wrapper_scripts_raw/,
tagging each with com.f5.automation. If created_action_ids.json (written by
vra_bootstrap.py --apply) is present alongside this script, each wrapper's
hardcoded ACTION_ID constant is automatically re-pointed at the client's
freshly-created ABX action ID before upload -- see
platform_config_raw/wrapper_to_abx_id_crosscheck.md for the wrapper<->ABX
name pairing this relies on.

Usage:
    python3 vro_bootstrap.py --config config.json            # dry-run
    python3 vro_bootstrap.py --config config.json --apply    # live
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _auth import bearer_session  # noqa: E402

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(SCRIPT_DIR)
WRAPPERS_DIR = os.path.join(PKG_ROOT, "wrapper_scripts_raw")

# vRO wrapper name -> name of the ABX action it hardcodes an ACTION_ID for.
# None means the wrapper has no ABX target to re-point (f5_vra_run_action is
# the generic runner; f5_generate_deployment_name calls no ABX action at all).
WRAPPER_TO_ABX_NAME = {
    "f5_vra_run_action": None,
    "f5_generate_deployment_name": None,
    "f5_list_vcenter_vms": "f5_list_vcenter_vms",
    "f5_nodes_from_vm_selection": "f5_nodes_from_vm_selection",
    "f5_list_monitor_types": "f5_list_monitors",  # confirmed mismatch -- see finding doc. Recommend renaming this wrapper to f5_list_monitors in the client build.
    "f5_list_nodes_grid": "f5_list_nodes_grid",
    "f5_list_nodes": "f5_list_nodes",
    "f5_list_free_ips": "f5_list_free_ips",
    "f5_list_oneconnect_profiles": "f5_list_oneconnect_profiles",
    "f5_list_snat_pools": "f5_list_snat_pools",
    "f5_list_lb_modes": "f5_list_lb_modes",
    "f5_list_persistence_profiles": "f5_list_persistence_profiles",
    "f5_list_locations": "f5_list_locations",
    "f5_list_environments": "f5_list_environments",
    "f5_list_clusters": "f5_list_clusters",
}

# Create f5_vra_run_action FIRST -- every other wrapper (except
# f5_generate_deployment_name) calls System.getModule("com.f5.automation").f5_vra_run_action(...)
# internally, per vro_module_setup_steps.md "Order of operations".
CREATE_ORDER = [
    "f5_vra_run_action",
    "f5_generate_deployment_name",
    "f5_list_vcenter_vms",
    "f5_nodes_from_vm_selection",
    "f5_list_monitor_types",
    "f5_list_nodes_grid",
    "f5_list_nodes",
    "f5_list_free_ips",
    "f5_list_oneconnect_profiles",
    "f5_list_snat_pools",
    "f5_list_lb_modes",
    "f5_list_persistence_profiles",
    "f5_list_locations",
    "f5_list_environments",
    "f5_list_clusters",
]

ACTION_ID_RE = re.compile(r'(ACTION_ID\s*=\s*)"([0-9a-f]+)"')


def load_config(path):
    with open(path) as f:
        return json.load(f)


def repoint_action_id(source, wrapper_name, id_map):
    abx_name = WRAPPER_TO_ABX_NAME.get(wrapper_name)
    if not abx_name or not id_map or abx_name not in id_map:
        return source, None
    new_id = id_map[abx_name]

    def _sub(m):
        return f'{m.group(1)}"{new_id}"'

    new_source, count = ACTION_ID_RE.subn(_sub, source, count=1)
    if count == 0:
        return source, None
    return new_source, new_id


def find_existing_action(session, host, module, name):
    try:
        resp = session.get(f"https://{host}/vco/api/actions", params={"module": module}, timeout=30)
        if resp.status_code == 200:
            for item in resp.json().get("link", resp.json().get("actions", [])):
                attrs = {a.get("name"): a.get("value") for a in item.get("attributes", [])} if isinstance(item, dict) else {}
                if attrs.get("name") == name or item.get("name") == name:
                    return item
    except Exception as exc:
        print(f"    [warn] existence check failed ({exc}); will attempt create and rely on server dedup")
    return None


def create_wrapper(session, host, cfg, wrapper_name, id_map, apply_):
    file_path = os.path.join(WRAPPERS_DIR, f"{wrapper_name}.js")
    with open(file_path) as f:
        source = f.read()

    source, new_id = repoint_action_id(source, wrapper_name, id_map)
    repoint_note = f" [re-pointed ACTION_ID -> {new_id}]" if new_id else ""

    module = cfg.get("vro_module", "com.f5.automation")
    tag = cfg.get("vro_tag", "com.f5.automation")

    if not apply_:
        print(f"  [dry-run] would create vRO action '{wrapper_name}' in module '{module}', "
              f"tag '{tag}' ({len(source)} chars){repoint_note}")
        return

    existing = find_existing_action(session, host, module, wrapper_name)
    if existing:
        print(f"  [skip] '{wrapper_name}' already exists in module '{module}' -- not overwriting")
        return

    body = {
        "name": wrapper_name,
        "module": module,
        "script": source,
        "description": f"F5 automation wrapper ({wrapper_name}) -- created by vro_bootstrap.py",
        "runtimeType": "javascript",
        "tags": [{"key": tag, "value": tag}],
    }
    resp = session.post(f"https://{host}/vco/api/actions", json=body, timeout=60)
    if resp.status_code in (200, 201):
        print(f"  [ok] created '{wrapper_name}' in module '{module}'{repoint_note}")
    else:
        print(f"  [ERROR] failed to create '{wrapper_name}': {resp.status_code} {resp.text[:500]}")
        print(f"          Fall back to creating this one by hand in the Orchestrator client")
        print(f"          (Library > Actions > New Action) -- see DEPLOYMENT_GUIDE.md Section 5")
        print(f"          and vro_module_setup_steps.md for the manual click-path.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--apply", action="store_true", help="Actually create things (default: dry-run)")
    parser.add_argument("--id-map", default=os.path.join(SCRIPT_DIR, "created_action_ids.json"),
                         help="Path to the name->ABX-id map written by vra_bootstrap.py --apply")
    args = parser.parse_args()

    cfg = load_config(args.config)
    host = cfg["vro_host"]
    verify_tls = cfg.get("verify_tls", True)

    id_map = {}
    if os.path.isfile(args.id_map):
        with open(args.id_map) as f:
            id_map = json.load(f)
        print(f"Loaded {len(id_map)} ABX action IDs from {args.id_map} for auto re-pointing.\n")
    else:
        print(f"No id-map found at {args.id_map} -- wrapper ACTION_ID constants will be left as-is "
              f"(still pointing at the LAB's action IDs). Re-run vra_bootstrap.py --apply first, or "
              f"manually edit each wrapper's ACTION_ID after creation.\n")

    missing_files = [w for w in CREATE_ORDER if not os.path.isfile(os.path.join(WRAPPERS_DIR, f"{w}.js"))]
    if missing_files:
        print("[FATAL] Missing wrapper source file(s):")
        for m in missing_files:
            print(f"  - {m}.js")
        sys.exit(1)

    print(f"{'APPLY' if args.apply else 'DRY-RUN'} mode -- {len(CREATE_ORDER)} vRO wrapper actions "
          f"targeted at module '{cfg.get('vro_module', 'com.f5.automation')}' on {host}\n")

    session = None
    if args.apply:
        session = bearer_session(host, cfg["username"], cfg["password"], cfg.get("domain", "System Domain"), verify_tls=verify_tls)

    for wrapper_name in CREATE_ORDER:
        create_wrapper(session, host, cfg, wrapper_name, id_map, args.apply)

    print("\nDone. Verify: Library > Actions, filter Tags: com.f5.automation, confirm all 15 are")
    print("listed (14 wrappers + f5_vra_run_action). Then create/confirm the Configuration Elements")
    print("(F5-Automation-Credentials/vraRefreshToken, F5-Automation/DeploymentNaming/sequenceCounters)")
    print("by hand -- see DEPLOYMENT_GUIDE.md Section 5.4, this script does not create those.")
    if id_map:
        unmapped = [w for w in CREATE_ORDER if WRAPPER_TO_ABX_NAME.get(w) and WRAPPER_TO_ABX_NAME[w] not in id_map]
        if unmapped:
            print(f"\n[warn] These wrappers had an expected ABX target not found in the id-map "
                  f"(ACTION_ID left pointing at the LAB's id -- fix by hand): {', '.join(unmapped)}")


if __name__ == "__main__":
    main()
