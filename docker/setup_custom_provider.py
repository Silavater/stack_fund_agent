"""Inject a `custom_providers` entry into /opt/data/config.yaml and point
`model.*` at it. Run INSIDE the Hermes container (has PyYAML):

    python setup_custom_provider.py <name> <base_url> <model>

Hermes' `custom` provider resolves its API key from the credential pool keyed by
a `custom_providers` entry whose `base_url` matches. This writes that entry; the
key itself is added separately via `hermes auth add custom:<name>`.
"""

from __future__ import annotations

import pathlib
import sys

import yaml

name, base, model = sys.argv[1], sys.argv[2], sys.argv[3]
p = pathlib.Path("/opt/data/config.yaml")
cfg = (yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}) or {}

cps = [
    e
    for e in (cfg.get("custom_providers") or [])
    if not (isinstance(e, dict) and e.get("name") == name)
]
cps.append({"name": name, "base_url": base, "api_mode": "chat_completions"})
cfg["custom_providers"] = cps

m = dict(cfg.get("model") or {})
m.update({"provider": "custom", "base_url": base, "default": model})
cfg["model"] = m

p.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
print(f"config.yaml: custom_providers[{name}] + model.provider=custom default={model}")
