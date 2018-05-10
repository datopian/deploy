#!/usr/bin/env python

import sys, json, yaml, os

set_values = json.loads(sys.argv[1])
filename = sys.argv[2]
if os.path.exists(filename):
    with open(filename) as f:
        values = yaml.load(f)
else:
    values = {}

def update(values, set_values):
    for k, v in set_values.items():
        if v is None:
            if k in values:
                del values[k]
        elif isinstance(v, dict) and isinstance(values.get(k), dict):
            update(values[k], v)
        else:
            values[k] = v

update(values, set_values)

with open(filename, "w") as f:
    yaml.safe_dump(values, f, default_flow_style=False)
