# OpenShell / NemoClaw policy

**Docker packages the agent; OpenShell *runs* that container.** They are layered,
not alternatives:

```
StackFund agent (Hermes harness + skills + engine)
   ↓ packaged as
Docker/OCI image            ← docker/Dockerfile.agent
   ↓ launched by
OpenShell sandbox           ← policy/openshell.yaml  (Landlock + seccomp + netns + L7 proxy)
   ↓ orchestrated by
NemoClaw                    ← policy/nemoclaw-blueprint.yaml  (onboard, blueprint, inference routing)
```

## Files
- `openshell.yaml` — the four-domain policy (filesystem / network / process /
  inference). This is **policy**, separate from the Dockerfile **packaging**.
- `nemoclaw-blueprint.yaml` — versioned bundle (image + policy + inference) that
  NemoClaw applies.

## Bring-up (Linux host or Windows + WSL2)
```bash
# Option A — OpenShell directly
openshell sandbox create --from .                 # builds docker/Dockerfile.agent dir
openshell policy apply  policy/openshell.yaml

# Option B — NemoClaw managed onboarding (builds image + wires sandbox)
NEMOCLAW_AGENT=hermes nemoclaw onboard
```

## Key design constraint
OpenShell injects credentials at the **egress proxy**; the agent sees
**placeholders** and keys never touch the sandbox filesystem. So: **never bake
Stripe/LLM secrets into the image or write them to disk** — this repo already
follows that (runtime secrets only). This matches the hackathon's
"safety-limits-on-spending" theme.

> ⚠️ Linux-kernel features (Landlock/seccomp/netns) require a Linux substrate.
> On the Windows 11 dev box, run under Docker Desktop + WSL2.
