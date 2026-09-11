# Haifa Agent Autonomous Delivery Assets

Versioned, offline-first evaluation assets for the Haifa Agent autonomous-delivery capability ladder.

The main repository owns the runner, result contract, asset downloader, and offline contract checks. This repository owns only the authored cases under `cases/<caseId>/` and the manifest that identifies an immutable asset set.

## Safety boundary

- Do not commit credentials, provider configuration, model transcripts, runtime databases, traces, or personal/production data.
- Cases must remain self-contained and offline: `acceptance.py` may execute only the copied workspace and must not call the network.
- A case contains `case.yaml`, `prompt.txt`, `base-workspace/`, `reference/`, and `acceptance.py`.
- Regenerate `caseTreeSha256` in `assets-manifest.json` after changing any file under `cases/`; the main repository lock must then be updated to the new immutable commit and manifest digest.

## Publication

Create the intended private GitHub repository, add it as `origin`, and push `main`. The first commit SHA is intentionally used by the main repository's `assets.lock.json`; pushing the commit preserves that SHA.
