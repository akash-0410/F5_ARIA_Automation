"""
ABX Action: f5_list_locations
--------------------------------
Custom Form data source for the "Location" dropdown (per the requirements
doc's General section). Static list of onboarded sites -- each value here
is the "location" input that f5_list_clusters filters its F5 Cluster
options by, so the Custom Form should wire these as a cascading pair:
Location first, then F5 Cluster (bound to f5_list_clusters, with its
"location" input set from this field's selection).

No dependencies required. No inputs required.
Output: {"options": [{"label": "<site name>", "value": "<location code>"}, ...]}
"""

LOCATIONS = [
    {"label": "Chanakyapuri", "value": "chanakyapuri"},
    {"label": "Secunderabad", "value": "secunderabad"},
]


def handler(context, inputs):
    return {"options": LOCATIONS}
