# Custom Resource: F5.VirtualServer

Captured live from the lab (Design > Custom Resources) on 2026-09-02.

## Summary tab

| Field | Value |
|---|---|
| Name | `F5.VirtualServer` |
| Description | F5 BIG-IP virtual server (nodes, pool, monitor, VIP) provisioned via ABX actions against the F5 iControl REST API. |
| Resource Type | `Custom.F5.VirtualServer` |
| Activate | ON — "Make custom resource available in blueprints" |
| Scope | "Available for any project" toggle is **OFF** — scoped to specific project(s) only (the F5-Automation project at minimum; verify exact project list in the live UI before replicating, as the toggle state alone doesn't show which projects are checked) |
| Based on | ABX user-defined schema |

## Lifecycle Actions

| Lifecycle stage | Wired ABX action |
|---|---|
| Create * | `f5_create_virtual_server` |
| Read * | `f5_read_virtual_server` |
| Update * | `f5_create_virtual_server` (same action as Create — it's written to reconcile/idempotently re-apply, not a separate update path) |
| Destroy * | `f5_delete_virtual_server` |

## Additional actions (Day-2 / resource actions menu)

These are the operator-facing "Run Day 2 Action" menu items a deployed resource exposes, each wired to a specific ABX action (separate from the Update lifecycle above):

| Menu label | Internal name | Action | Active |
|---|---|---|---|
| Update Health Monitor / Load Balancing | `updateHealthMonitorAndLB` | `f5_update_pool_settings` | ✓ |
| Resync from F5 Device | `resync` | `f5_read_virtual_server` | ✓ |
| Update Backend Nodes / Pool Members | `updateBackendNodes` | `f5_update_backend_nodes` | ✓ |

Each row has a "Request Parameters" icon in the live UI (a small form-mapping icon) — this maps which resource/day-2 input fields the action receives; not fully expanded in this capture. When rebuilding, open each Additional Action's Request Parameters mapping in the live UI and mirror it — do not assume the mapping is 1:1 with the action's raw inputs.

## Properties schema (Code view, full YAML captured from the live editor)

```yaml
properties:
  vs:
    type: object
    title: Virtual Server
    properties:
      name:
        type: string
        title: Name
      port:
        type: integer
        title: Port
      snat:
        type: string
        title: SNAT (automap/none/<snat pool>)
      type:
        type: string
        title: Virtual Server Type
        enum:
          - standard
          - forwarding-ip
          - forwarding-l2
          - reject
          - dhcp
          - performance-http
          - performance-l4
          - internal
        default: standard
      ports:
        type: array
        title: Additional Ports
        items:
          type: integer
      protocol:
        type: string
        title: Protocol (tcp/udp)
      destination_ip:
        type: string
        title: Destination (VIP) IP
      oneconnect_profile:
        type: string
        title: OneConnect Profile
      persistence_profile:
        type: string
        title: Persistence Profile
  host:
    type: string
    title: F5 Cluster
    description: Management host/VIP of the target F5 BIG-IP device. Bind this to the F5 Cluster dropdown (f5_list_clusters) on the Custom Form.
  pool:
    type: object
    title: Pool
    properties:
      name:
        type: string
        title: Pool Name
      monitor:
        type: string
        title: Existing Monitor (fullPath, or 'none')
      monitor_type:
        type: string
        title: New Monitor Type (e.g. http, https, tcp)
      monitor_timeout:
        type: integer
        title: Monitor Timeout (sec)
        default: 16
      monitor_interval:
        type: integer
        title: Monitor Interval (sec)
        default: 5
      load_balancing_mode:
        type: string
        title: Load Balancing Mode
        default: round-robin
  nodes:
    type: array
    title: Backend Nodes
    items:
      type: object
      properties:
        name:
          type: string
          title: Node Name
        port:
          type: integer
          title: Port
        address:
          type: string
          title: Node Address
        create_if_missing:
          type: boolean
          title: Create Node if Missing
          default: false
  missing:
    type: array
    title: Missing Virtual Servers (output)
    items:
      type: string
  poolName:
    type: string
    title: Pool Name (output)
  partition:
    type: string
    title: Partition
    default: Common
  verify_tls:
    type: boolean
    title: Verify TLS
    default: false
  destinationIp:
    type: string
    title: Destination IP (output)
  virtualServers:
    type: array
    title: Created Virtual Servers (output)
    items:
      type: string
```

## Notes / discrepancies for the SOP

- The Update lifecycle action is the SAME action as Create (`f5_create_virtual_server`), which is a reconcile-style create-or-update, not a dedicated updater. The two "Additional actions" (`f5_update_pool_settings`, `f5_update_backend_nodes`) exist specifically because the full reconcile is considered too broad/risky for narrow day-2 edits — this is the origin of the "targeted Day-2 update" language seen in those scripts' docstrings.
- `pool.monitor` (existing monitor fullPath) and `pool.monitor_type` (new monitor type) are two DIFFERENT schema fields — matches the f5_list_monitors vs f5_list_monitor_types split found in the scripts.
