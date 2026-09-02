// Sections 9-16: change management through document history.

const SEC9_CHANGE_MGMT = [
  { h1: '9. Change Management' },
  { p: 'This is a standard, low-risk, reversible change: it edits two existing (or net-new) automation actions and does not touch F5 device state, network configuration, or any existing deployment\'s live resources at deployment time.' },
  { ul: [
      'Recommended window: any time outside active F5 virtual-server request activity — this is a scripting-layer change, not infrastructure downtime, but a request submitted mid-edit could observe a half-saved action.',
      'Required approvals: per the client\'s own change-management process; at minimum, the change approver role should sign off on the maintenance window and rollback plan before work starts.',
      'Required backups: pre-deployment export of both actions\' current script and input configuration (where already present), retained per the client\'s backup retention policy. Note the Secret Input limitation in Section 7.4 — its value cannot be exported, only its name/type.',
    ],
  },
  { pageBreak: true },
];

const SEC10_DEPLOYMENT_SUMMARY = [
  { h1: '10. Deployment Procedure (Summary)' },
  { p: 'The full click-by-click procedure lives in the companion DEPLOYMENT_GUIDE.md, written for a Tier-1 engineer with no prior vRA/vRO experience. This section summarizes the procedure at a process level for readers who already know the platforms.' },
  { ol: [
      'Complete the pre-deployment checklist: confirm access, back up any existing versions of both actions, confirm the target vRA project, and gather the client\'s real F5 credentials and VIP subnet registry values.',
      'Deploy the vRO action f5_generate_deployment_name: create/open it with module com.f5.automation, confirm its three inputs (project, location, environmentType), paste in the verified script, save, and hard-refresh to confirm persistence.',
      'Complete the one-time vRO Configuration Element setup (F5-Automation > DeploymentNaming > sequenceCounters) if it does not already exist.',
      'Deploy the ABX action f5_create_virtual_server: create/open it as a Python 3.10 Script action with main function handler and dependency requests, paste in the verified script, configure Default/Secret Inputs and the F5_VIP_SUBNET_REGISTRY Action Constant with the client\'s real values, save, and hard-refresh to confirm persistence.',
      'Verify the Custom Form\'s Deployment Name field binding is unchanged and still points at the correct action and inputs.',
      'Run the full verification suite in Section 11.',
      'Review Section 12\'s decisions-needed items with the client\'s F5/automation owner and record each as accepted-as-is or logged as a follow-up.',
      'Complete sign-off (Section 15).',
    ],
  },
  { pageBreak: true },
];

const SEC11_VERIFICATION = [
  { h1: '11. Verification and Testing (Acceptance Criteria)' },
  { p: 'A deployment is only complete when all of the following are true, with evidence (screenshot, run log, or test output) attached to the change record:' },
  { ul: [
      'The naming action returns a clean location-environmentType-seq string with no GUID anywhere in it, tested with at least two different location/environment combinations, confirming the sequence number increments correctly and without collision.',
      'The ABX action\'s source passes a Python syntax check (ast.parse / py_compile clean) — this is the exact class of defect Bug 2 was, so this check is mandatory, not optional.',
      'A real end-to-end catalog request produces a correctly named deployment and a successful ABX action run (no IndentationError, no unhandled exception).',
      'The resulting pool, node(s), and virtual server(s) are confirmed present on the target F5 device with the expected name, partition, and configuration.',
    ],
  },
  { pageBreak: true },
];

const SEC12_RISKS = [
  { h1: '12. Known Risks, Gaps, and Decisions Needed Before Go-Live' },
  { p: 'These are not defects introduced by this deployment, but real findings — from the original troubleshooting and from an independent adversarial review of the finished package — that change runtime behavior or security posture. They were deliberately not silently fixed and require a decision from the client\'s automation/F5 owner.' },
  { h3: '1. Single shared F5 credential model' },
  { p: 'Only one username/password pair is actually used by _resolve_credentials(), regardless of how many F5 clusters exist. (An earlier version of this script\'s header comments incorrectly described a per-cluster credential map — F5_CREDENTIAL_MAP, one Secret per location — that did not exist in the code; those comments were corrected during this deployment\'s hardening pass, see Section 8.3, and no longer describe that design.) Risk: an incorrect assumption that adding a new F5 cluster with its own credentials "just works" today — it does not.' },
  { h3: '2. Credential storage type' },
  { p: 'In the source environment, F5_SHARED_PASSWORD was stored as a plain (non-Secret) Default Input — visible in clear text. This must be corrected to a Secret Input during deployment (Section 7.4); do not replicate the source\'s configuration as-is in any environment.' },
  { h3: '3. TLS verification defaults to off — and this package has no configuration lever to change it' },
  { p: 'verify_tls defaults to False, and the script globally suppresses the resulting urllib3 warnings. verify_tls comes from the request/Custom Resource payload, not from any Default Input, Secret, or Action Constant this deployment configures — so there is nothing in the vRO/ABX configuration steps in the Deployment Guide that can change this default. Confirm with the client whether their F5 devices present certificates that can be verified; if the default must become True, that requires a code change to this ABX action (or a new Custom Form field wired through to vs.verify_tls), and should be escalated to Automation Engineering as a follow-up rather than treated as something this deployment can configure.' },
  { h3: '4. Custom monitor timing currently has no effect at all, and create_monitor() is inconsistent between its two call paths' },
  { p: 'Two separate issues, see Section 6.7. First: monitor_interval and monitor_timeout are accepted as request fields, but create_monitor() never reads or uses them — requesting custom health-check timing today silently does nothing on the F5 device. Second: whether monitor_type is treated as a short name or an already-fully-qualified path is assumed differently depending on which code path runs (customized vs. non-customized), even though both read the same pool.get("monitor_type") value. Both points must be confirmed against the actions that populate the monitor-type dropdown (f5_list_monitor_types / f5_list_monitors) and tested against a real F5 device — and, if custom timing is a feature the client actually needs, that requires a code change — before this feature is presented to end users as functional.' },
  { h3: '5. Cross-partition backend nodes' },
  { p: 'create_node() always creates under the ABX action\'s own configured partition, but a node supplied with an explicit /OtherPartition/name prefix will have its pool-member reference point at that other partition — which will fail if the node was actually created in the action\'s own partition. Only a risk if the client\'s node naming ever crosses partitions.' },
  { h3: '6. Default profile selection is "whichever the F5 API lists first"' },
  { p: 'list_profiles() does not pick a client-defined default — it takes the first profile the API happens to return for each type. If the client has custom profiles that sort ahead of built-in ones (e.g. /Common/tcp), virtual servers could silently receive an unintended default profile. Worth a spot-check against the client\'s actual F5 device after go-live.' },
  { h3: '7. Incomplete pool-skip list for non-pooled virtual server types' },
  { p: 'no_pool_types only excludes forwarding-ip and forwarding-l2. reject and dhcp virtual server types conventionally shouldn\'t carry a pool either — confirm relevance with the client\'s F5 owner.' },
  { h3: '8. VIP auto-assignment has the same class of race condition as the naming counter, but it is undisclosed and less tolerable' },
  { p: 'next_available_ip() (Section 6.5) computes the next free address by reading the F5 device\'s current state with no locking, structurally identical to the deployment-naming sequence counter\'s race condition (Section 5.5). Unlike the naming counter — where a collision only produces a skipped or duplicate cosmetic sequence number, an accepted risk — a VIP collision here could hand the same IP address to two different virtual servers, a materially worse outcome. Ask the client whether their expected request volume and concurrency make this a real concern.' },
  { h3: '9. No automated cleanup on a partial mid-request failure' },
  { p: 'If handler() creates a node and a pool but then fails before completing virtual server creation (e.g. an F5 API rejection, an incompatible profile combination), the already-created node and pool are left on the device with no automated rollback or flagging — see Section 13.3. Ask the client\'s F5 owner how they want partially-failed requests monitored and cleaned up.' },
  { note: 'Every one of the nine items above must be explicitly reviewed with the client and recorded in the Section 15 sign-off table as either "reviewed, accepted as-is" (or, for item 2, "confirmed done" — it is not optional) or "logged as a follow-up change request" — none should be left silently unaddressed.', kind: 'warn' },
  { pageBreak: true },
];

const SEC13_ROLLBACK = [
  { h1: '13. Rollback Plan' },
  { p: 'This plan covers the two automation scripts and their configuration only — see Section 13.3 for what it does not cover.' },
  { h2: '13.1 Restoring an existing install' },
  { ol: [
      'vRO action: restore the pre-deployment backup script and Save. Hard-refresh to confirm persistence. Do not delete or alter the F5-Automation/DeploymentNaming Configuration Element as part of this — it holds real sequence-counter state, not action configuration.',
      'ABX action: restore the pre-deployment backup script and Default Inputs, and Save. Hard-refresh to confirm persistence. Remember that any Secret Input\'s plaintext cannot be restored from a backup — it must come from wherever the client\'s original credential was issued, not from anything captured during this deployment.',
      'If the Custom Form\'s Deployment Name field binding was re-pointed during deployment (Section 11), re-point it back, or to a safe placeholder, before disabling or deleting the vRO action it currently points to — leaving the binding dangling breaks the field for every user.',
      'Re-run Section 11\'s verification checks against the restored version to confirm the environment is back to its known-good, pre-change state.',
      'Notify the client contact and this deployment\'s change approver that rollback occurred, and why.',
    ],
  },
  { h2: '13.2 Rolling back a brand-new install' },
  { p: '"Rollback" means: re-point or disable the Custom Form\'s Deployment Name field first (same reasoning as 13.1), then delete the two new actions, then tell the client the field will show a manual/static value (or be disabled) until the issue is resolved. Leave any Configuration Element created during this deployment in place unless it is confirmed nothing else depends on it — an idle counter is harmless; deleting a counter something else relies on is not.' },
  { h2: '13.3 What this plan does not cover: live F5 objects' },
  { p: 'Rolling back the scripts does not remove or repair anything already created on the real F5 device (nodes, pools, partially-configured virtual servers) by a request that ran before the rollback decision — including a request that failed partway through (see Section 12, item 9). This must be checked and resolved manually with the client\'s F5/network owner, case by case; nothing in this package automates it.' },
  { pageBreak: true },
];

const SEC14_OPERATIONS = [
  { h1: '14. Post-Deployment Operations' },
  { h2: '14.1 Onboarding a new F5 cluster' },
  { p: 'Until the design gap in Section 12, item 1 is addressed, all F5 hosts share one credential pair. To onboard a new host today: add its entry to F5_VIP_SUBNET_REGISTRY (Section 6.5) with the correct CIDR and any reserved addresses. If the new host needs different credentials than the existing shared pair, this is not currently supported without a code change — escalate to Automation Engineering rather than working around it.' },
  { h2: '14.2 Rotating the F5 password' },
  { p: 'Update the value of the F5_SHARED_PASSWORD Secret Input on the f5_create_virtual_server ABX action. Because it is a Secret Input, this is a straightforward overwrite — there is nothing to "migrate," since only one shared value exists.' },
  { h2: '14.3 Monitoring the sequence counter' },
  { p: 'The sequenceCounters Properties map inside the DeploymentNaming Configuration Element grows by one key per unique location+environment combination ever requested. It does not need routine maintenance, but if the Configuration Element is ever deleted or recreated, counting restarts from 1 for every prefix — flag this to whoever owns change control over vRO Configuration Elements.' },
  { h2: '14.4 Updating this SOP and the Deployment Guide' },
  { p: 'Both documents describe the scripts as they existed at the version noted in Section 16. Any future change to either script\'s logic, inputs, or configuration requirements must be reflected in both documents at the same time — a document that no longer matches the deployed code is worse than no document, because it actively misleads the next engineer.' },
  { pageBreak: true },
];

const SEC15_SIGNOFF = [
  { h1: '15. Approval and Sign-off' },
  { h3: '15.1 Deployment steps' },
  { table: { headers: ['Step', 'Done by', 'Date', 'Evidence', 'Notes'], widths: [32, 16, 12, 18, 22], rows: [
    ['Prerequisites confirmed', '', '', '', ''],
    ['Pre-deployment checklist complete, including security note & credential-model reconciliation', '', '', '', ''],
    ['vRO action deployed & verified (Section 11)', '', '', '', ''],
    ['ABX action deployed & syntax-verified (Section 11, mandatory)', '', '', '', ''],
    ['End-to-end test passed, including the auto-VIP-assignment case (Section 11)', '', '', '', ''],
    ['Custom Form Deployment Name field binding confirmed intact', '', '', '', ''],
    ['No orphaned live F5 objects left over from testing (Section 13.3)', '', '', '', ''],
    ['Client contact notified of completion', '', '', '', ''],
  ] } },
  { h3: '15.2 Section 12 risk items — each reviewed individually with the client' },
  { p: 'A single aggregate sign-off is not sufficient here — each item below changes runtime behavior or security posture and must be individually discussed and recorded, not bundled into one blanket approval. An evidence-free row is not a completed review.' },
  { table: { headers: ['#', 'Risk item', 'Reviewed with client?', 'Disposition', 'Evidence'], widths: [5, 38, 15, 22, 20], rows: [
    ['1', 'Single shared F5 credential for every device', '', '', ''],
    ['2', 'Credential storage type — confirmed done, not "accepted"', '', '', ''],
    ['3', 'TLS verification off by default, no config lever in this package', '', '', ''],
    ['4', 'Custom monitor timing has no effect; monitor path-format inconsistency', '', '', ''],
    ['5', 'Cross-partition backend node references', '', '', ''],
    ['6', 'Default profile selection is "first API result," not client-defined', '', '', ''],
    ['7', 'Incomplete pool-skip list for non-pooled virtual server types', '', '', ''],
    ['8', 'VIP auto-assignment race condition (undisclosed until this version)', '', '', ''],
    ['9', 'No automated cleanup on partial F5-side failure', '', '', ''],
  ] } },
  { spacer: 300 },
  { table: { headers: ['Name', 'Role', 'Signature / Date'], widths: [34, 33, 33], rows: [
    ['', 'Deploying engineer', ''],
    ['', 'Change approver', ''],
    ['', 'Client point of contact', ''],
  ] } },
  { pageBreak: true },
];

const SEC16_HISTORY = [
  { h1: '16. Document History' },
  { table: { headers: ['Version', 'Date', 'Change'], widths: [15, 20, 65], rows: [
    ['1.0', '2026-08-31', 'Initial SOP covering the deployment-naming GUID fix and the ABX indentation fix, at a process level.'],
    ['2.0', '2026-08-31', 'Full technical reference edition: added complete glossary, feature-by-feature functionality reference with embedded code excerpts, full configuration reference, and expanded root-cause/fix documentation for both bugs plus the packaging hardening pass. Companion Deployment Guide rewritten for a Tier-1/L1 audience.'],
  ] } },
];

module.exports = {
  SEC9_CHANGE_MGMT, SEC10_DEPLOYMENT_SUMMARY, SEC11_VERIFICATION, SEC12_RISKS,
  SEC13_ROLLBACK, SEC14_OPERATIONS, SEC15_SIGNOFF, SEC16_HISTORY,
};
