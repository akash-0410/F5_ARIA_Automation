#!/usr/bin/env python3
"""
vra_bootstrap.py -- UNVERIFIED. See bootstrap/README.md before running.

Creates the 19 ABX Python actions (from ../scripts_lab_raw/ and
../scripts/f5_create_virtual_server.py) in a target Aria Automation project,
and best-effort creates the F5_VIP_SUBNET_REGISTRY and F5_DEVICE_REGISTRY
Action Constants.

Idempotent by name: re-running skips any action that already exists under
that name in the target project (checked via GET .../actions?$filter=...).

Usage:
    python3 vra_bootstrap.py --config config.json            # dry-run
    python3 vra_bootstrap.py --config config.json --apply    # live
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _auth import bearer_session  # noqa: E402

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(SCRIPT_DIR)
SCRIPTS_LAB_RAW = os.path.join(PKG_ROOT, "scripts_lab_raw")
SCRIPTS_DIR = os.path.join(PKG_ROOT, "scripts")

# All 19 ABX actions. f5_create_virtual_server lives in scripts/ (it was
# pulled out earlier in this engagement); everything else is in
# scripts_lab_raw/. f5_list_monitor_types.py is intentionally INCLUDED here
# for completeness/audit trail even though it is confirmed orphaned (no vRO
# wrapper calls it) -- see platform_config_raw/finding_monitor_type_vs_monitors.md.
# Skip it with --skip-orphaned if you don't want it in the client tenant.
ABX_ACTIONS = [
    {"name": "f5_create_virtual_server", "file": os.path.join(SCRIPTS_DIR, "f5_create_virtual_server.py"), "dependencies": "requests"},
    {"name": "f5_read_virtual_server", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_read_virtual_server.py"), "dependencies": "requests"},
    {"name": "f5_delete_virtual_server", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_delete_virtual_server.py"), "dependencies": "requests"},
    {"name": "f5_update_pool_settings", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_update_pool_settings.py"), "dependencies": "requests"},
    {"name": "f5_update_backend_nodes", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_update_backend_nodes.py"), "dependencies": "requests"},
    {"name": "f5_list_vcenter_vms", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_list_vcenter_vms.py"), "dependencies": "requests"},
    {"name": "f5_nodes_from_vm_selection", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_nodes_from_vm_selection.py"), "dependencies": "requests"},
    {"name": "f5_list_monitors", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_list_monitors.py"), "dependencies": "requests"},
    {"name": "f5_list_monitor_types", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_list_monitor_types.py"), "dependencies": "requests", "orphaned": True},
    {"name": "f5_list_nodes_grid", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_list_nodes_grid.py"), "dependencies": "requests"},
    {"name": "f5_list_nodes", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_list_nodes.py"), "dependencies": "requests"},
    {"name": "f5_list_free_ips", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_list_free_ips.py"), "dependencies": "requests"},
    {"name": "f5_list_oneconnect_profiles", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_list_oneconnect_profiles.py"), "dependencies": "requests"},
    {"name": "f5_list_snat_pools", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_list_snat_pools.py"), "dependencies": "requests"},
    {"name": "f5_list_persistence_profiles", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_list_persistence_profiles.py"), "dependencies": "requests"},
    {"name": "f5_list_lb_modes", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_list_lb_modes.py"), "dependencies": "requests"},
    {"name": "f5_list_clusters", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_list_clusters.py"), "dependencies": "requests"},
    {"name": "f5_list_environments", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_list_environments.py"), "dependencies": "requests"},
    {"name": "f5_list_locations", "file": os.path.join(SCRIPTS_LAB_RAW, "f5_list_locations.py"), "dependencies": "requests"},
]

# Both Action Constants the 19 ABX actions actually read (confirmed via
# inputs.get(...) in f5_create_virtual_server.py and f5_list_clusters.py
# respectively). This script creates both with placeholder JSON -- the real
# host/CIDR/device values must be edited in by hand after creation either
# way, since only the client knows their real F5 inventory.
ACTION_CONSTANTS = [
    {
        "name": "F5_VIP_SUBNET_REGISTRY",
        "value": json.dumps({
            "REPLACE_WITH_F5_HOST": {"cidr": "10.0.0.0/24", "reserved": ["10.0.0.1"]}
        }),
    },
    {
        "name": "F5_DEVICE_REGISTRY",
        "value": json.dumps({
            "REPLACE_WITH_LOCATION": {
                "production": [{"label": "REPLACE_WITH_LABEL", "host": "REPLACE_WITH_F5_HOST"}],
                "uat": [],
            }
        }),
    },
]


def load_config(path):
    with open(path) as f:
        return json.load(f)


def find_existing_action(session, host, project_id, name):
    # Best-effort lookup. Exact query-param support varies by version --
    # if this 404s or errors, the script treats it as "not found" and
    # attempts create, relying on the server's own duplicate-name error
    # (if any) to prevent an actual duplicate.
    try:
        resp = session.get(
            f"https://{host}/abx/api/resources/actions",
            params={"projectId": project_id, "$filter": f"name eq '{name}'"},
            timeout=30,
        )
        if resp.status_code == 200:
            items = resp.json().get("content", resp.json().get("numberOfElements") and [] or [])
            if isinstance(resp.json(), dict) and "content" in resp.json():
                for item in resp.json()["content"]:
                    if item.get("name") == name:
                        return item
    except Exception as exc:
        print(f"    [warn] existence check failed ({exc}); will attempt create and rely on server dedup")
    return None


def create_action(session, host, project_id, cfg, action, apply_, id_map):
    with open(action["file"]) as f:
        source = f.read()

    body = {
        "name": action["name"],
        "projectId": project_id,
        "runtimeName": cfg.get("runtime", "python"),
        "runtimeVersion": cfg.get("runtime_version", "3.10"),
        "entrypoint": "handler",
        "source": source,
        "dependencies": action.get("dependencies", ""),
        "memoryInMB": 300,
        "timeoutSeconds": 600,
        "shared": False,
    }

    if not apply_:
        print(f"  [dry-run] would create ABX action '{action['name']}' "
              f"({len(source)} chars, deps={action.get('dependencies')!r})"
              + (" [ORPHANED -- kept for audit trail only]" if action.get("orphaned") else ""))
        return

    existing = find_existing_action(session, host, project_id, action["name"])
    if existing:
        print(f"  [skip] '{action['name']}' already exists (id={existing.get('id')}) -- not overwriting")
        id_map[action["name"]] = existing.get("id")
        return

    resp = session.post(f"https://{host}/abx/api/resources/actions", json=body, timeout=60)
    if resp.status_code in (200, 201):
        new_id = resp.json().get("id", "?")
        print(f"  [ok] created '{action['name']}' -> id {new_id}")
        id_map[action["name"]] = new_id
    else:
        print(f"  [ERROR] failed to create '{action['name']}': {resp.status_code} {resp.text[:500]}")
        print("          Fall back to creating this one by hand in Assembler > Extensibility > Actions.")


def create_action_constant(session, host, project_id, apply_, constant):
    if not apply_:
        print(f"  [dry-run] would create Action Constant '{constant['name']}' "
              f"(placeholder JSON -- edit real values after creation)")
        return
    body = {
        "name": constant["name"],
        "value": constant["value"],
        "projectId": project_id,
        "encrypted": False,
    }
    # Best-effort endpoint guess -- see README known-risk notes.
    resp = session.post(f"https://{host}/abx/api/resources/action-constants", json=body, timeout=30)
    if resp.status_code in (200, 201):
        print(f"  [ok] created Action Constant '{constant['name']}' (placeholder value -- edit it now)")
    else:
        print(f"  [ERROR] Action Constant create failed ({resp.status_code}): {resp.text[:300]}")
        print("          This endpoint is our best guess for this API family and may not match your")
        print(f"          tenant's version. Create '{constant['name']}' by hand instead:")
        print("          Assembler > Extensibility > Actions > Constants > New Constant.")
        print("          Remember to also attach it to the one action that reads it")
        print("          (F5_VIP_SUBNET_REGISTRY -> f5_create_virtual_server,")
        print("           F5_DEVICE_REGISTRY -> f5_list_clusters) -- this script cannot")
        print("           do that attachment step even when the create above succeeds.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--apply", action="store_true", help="Actually create things (default: dry-run)")
    parser.add_argument("--skip-orphaned", action="store_true", help="Skip f5_list_monitor_types (confirmed dead code)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    host = cfg["vra_host"]
    project_id = cfg["project_id"]
    verify_tls = cfg.get("verify_tls", True)

    actions = ABX_ACTIONS
    if args.skip_orphaned:
        actions = [a for a in actions if not a.get("orphaned")]

    missing_files = [a["file"] for a in actions if not os.path.isfile(a["file"])]
    if missing_files:
        print("[FATAL] Missing source file(s):")
        for m in missing_files:
            print(f"  - {m}")
        sys.exit(1)

    print(f"{'APPLY' if args.apply else 'DRY-RUN'} mode -- {len(actions)} ABX actions targeted at "
          f"project {project_id} on {host}\n")

    session = None
    if args.apply:
        session = bearer_session(host, cfg["username"], cfg["password"], cfg.get("domain", "System Domain"), verify_tls=verify_tls)

    id_map = {}
    for action in actions:
        create_action(session, host, project_id, cfg, action, args.apply, id_map)

    print("\nAction Constants:")
    for constant in ACTION_CONSTANTS:
        create_action_constant(session, host, project_id, args.apply, constant)

    if args.apply and id_map:
        out_path = os.path.join(SCRIPT_DIR, "created_action_ids.json")
        with open(out_path, "w") as f:
            json.dump(id_map, f, indent=2)
        print(f"\nWrote {out_path} -- pass this to vro_bootstrap.py so it can")
        print("automatically re-point each wrapper's ACTION_ID at the new IDs.")

    print("\nDone. Remember: Action Default Inputs (f5_username) and Secret Inputs")
    print("(F5_SHARED_PASSWORD) must still be set by hand on each action that needs")
    print("them -- see DEPLOYMENT_GUIDE.md Section 4. This script does not touch those.")


if __name__ == "__main__":
    main()
