# secrets/

Real secret files (`*.txt`) are **git-ignored**. Only `*.example` templates are
tracked. Secrets are injected at **runtime** (compose secrets → `/run/secrets/*`,
or the OpenShell egress proxy) and are **never** baked into an image layer.

## Local dev setup
```bash
cp secrets/stripe_secret_key.txt.example     secrets/stripe_secret_key.txt
cp secrets/stripe_webhook_secret.txt.example secrets/stripe_webhook_secret.txt
# then edit the .txt files with your real TEST-mode values
```

## Guidance
- Create keys inside a **Stripe sandbox** (`stripe sandbox create`) for full
  isolation, and use a **Restricted API Key in TEST mode** (`rk_test_…`), scoped
  least-privilege (separate keys for earn vs spend).
- Never commit a `*.txt` file, never put a key in the Dockerfile/`ENV`/build-arg.
- In production, prefer a managed secret manager (Vault / cloud secret manager).
