"""
ABX Action: f5_list_environments
------------------------------------
Custom Form data source for the "Environment Type" dropdown (General
section of the requirements doc). Static Production/UAT list -- the
selected value feeds into f5_list_clusters (as "environment") to filter
which F5 devices are shown, since each site maintains separate Production
and UAT device pools (see the F5_DEVICE_REGISTRY Action Constant).

No dependencies required. No inputs required.
Output: {"options": [{"label": "Production", "value": "production"}, {"label": "UAT", "value": "uat"}]}
"""

ENVIRONMENTS = [
    {"label": "Production", "value": "production"},
    {"label": "UAT", "value": "uat"},
]


def handler(context, inputs):
    return {"options": ENVIRONMENTS}
