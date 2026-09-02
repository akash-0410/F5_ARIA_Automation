# Wrapper -> ABX Action ID Cross-Check (full audit)

Captured/verified live on 2026-09-02 by comparing every vRO wrapper's hardcoded
`ACTION_ID` against the real ABX action IDs read directly from Assembler >
Extensibility > Actions (each action's own edit-URL). This is the authoritative
wiring map -- use it when re-pointing wrappers at the client's freshly-created
ABX action IDs (the IDs below are LAB-SPECIFIC and will not exist in a new
tenant; only the wrapper <-> ABX action *name* pairing carries over).

| vRO wrapper (as named in Orchestrator) | Calls ABX action ID | Actually resolves to ABX action | Match? |
|---|---|---|---|
| `f5_list_vcenter_vms` | `8a748097a00ff13901a0331a482506e3` | `f5_list_vcenter_vms` | OK |
| `f5_nodes_from_vm_selection` | `8a748097a00ff13901a0331afa2906e4` | `f5_nodes_from_vm_selection` | OK |
| `f5_list_monitor_types` | `8a748097a00ff13901a03300d09706d9` | **`f5_list_monitors`** | **MISMATCH -- see below** |
| `f5_list_nodes_grid` | `8a748097a00ff13901a01eb4de840327` | `f5_list_nodes_grid` | OK (comment inside the script calling this a placeholder is itself stale -- the ID is already correct) |
| `f5_list_nodes` | `8a7480179fff2d51019fff8af2830006` | `f5_list_nodes` | OK |
| `f5_list_free_ips` | `8a748097a00ff13901a01d9a33b2014f` | `f5_list_free_ips` | OK |
| `f5_list_oneconnect_profiles` | `8a74805da00e9db401a00ee1a9730002` | `f5_list_oneconnect_profiles` | OK |
| `f5_list_snat_pools` | `8a74805da00e9db401a00ed7acf90001` | `f5_list_snat_pools` | OK |
| `f5_list_lb_modes` | `8a7480179fff2d51019fff87ef050003` | `f5_list_lb_modes` | OK |
| `f5_list_persistence_profiles` | `8a7480179fff2d51019fff88ca6f0004` | `f5_list_persistence_profiles` | OK |
| `f5_list_locations` | `8a74805da00e9db401a00ecdfb140000` | `f5_list_locations` | OK |
| `f5_list_environments` | `8a74805da00e9db401a00ee534070004` | `f5_list_environments` | OK |
| `f5_list_clusters` | `8a7480179fff2d51019fff86f6f30002` | `f5_list_clusters` | OK |

Not applicable to this table (no hardcoded target ABX ID / not a thin wrapper):
- `f5_vra_run_action` -- generic runner, `actionId` passed in by every caller above.
- `f5_generate_deployment_name` -- pure vRO logic against a Configuration Element, calls no ABX action.

## The one confirmed mismatch

`f5_list_monitor_types` (the vRO wrapper) actually calls the ABX action
`f5_list_monitors`, not `f5_list_monitor_types`. Full root-cause analysis,
impact assessment, and the recommended fix for the client rebuild are in
`finding_monitor_type_vs_monitors.md` in this same folder. Net effect: the
live Custom Form behaves correctly (existing-monitor picker); only the vRO
wrapper's name is misleading, and the ABX action `f5_list_monitor_types.py` is
confirmed orphaned (no wrapper calls it).

## Complete ABX action inventory with real (lab) IDs

For reference / audit trail -- all 19 ABX Extensibility Actions found in the
live Assembler, module F5-Automation project:

| ABX action | Lab action ID |
|---|---|
| `f5_create_virtual_server` | `8a7480179fff2d51019fff8417ff0000` |
| `f5_update_pool_settings` | `8a748097a00ff13901a038543c4f07b2` |
| `f5_update_backend_nodes` | `8a748097a00ff13901a038566f5907b3` |
| `f5_list_vcenter_vms` | `8a748097a00ff13901a0331a482506e3` |
| `f5_nodes_from_vm_selection` | `8a748097a00ff13901a0331afa2906e4` |
| `f5_list_monitors` | `8a748097a00ff13901a03300d09706d9` |
| `f5_list_monitor_types` (orphaned, no wrapper) | `8a7480179fff2d51019fff89acd70005` |
| `f5_list_nodes_grid` | `8a748097a00ff13901a01eb4de840327` |
| `f5_delete_virtual_server` | `8a7480179fff2d51019fff85bbc40001` |
| `f5_list_free_ips` | `8a748097a00ff13901a01d9a33b2014f` |
| `f5_list_oneconnect_profiles` | `8a74805da00e9db401a00ee1a9730002` |
| `f5_list_snat_pools` | `8a74805da00e9db401a00ed7acf90001` |
| `f5_read_virtual_server` | `8a7480179fff2d51019fff92ad84000b` |
| `f5_list_persistence_profiles` | `8a7480179fff2d51019fff88ca6f0004` |
| `f5_list_lb_modes` | `8a7480179fff2d51019fff87ef050003` |
| `f5_list_nodes` | `8a7480179fff2d51019fff8af2830006` |
| `f5_list_clusters` | `8a7480179fff2d51019fff86f6f30002` |
| `f5_list_environments` | `8a74805da00e9db401a00ee534070004` |
| `f5_list_locations` | `8a74805da00e9db401a00ecdfb140000` |

These 19 IDs are unique to this lab tenant. When the client creates their own
ABX actions, Aria Automation will assign entirely new IDs -- every wrapper's
`ACTION_ID` constant (or the single `actionId` parameter passed into
`f5_vra_run_action` by each caller) must be updated to match the client's own
newly-created action IDs. This table's "vRO wrapper -> ABX action NAME"
mapping is what must be preserved; the ID column here is only useful for
verifying the lab and will not exist post-migration.
