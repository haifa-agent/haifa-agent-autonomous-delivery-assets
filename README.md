# Haifa Agent Autonomous Delivery Assets

Versioned, offline-first evaluation assets for the Haifa Agent autonomous-delivery capability ladder.

The main repository owns the runner, result contract, asset downloader, and offline contract checks. This
repository owns the authored cases under `cases/<caseId>/`, the manifest that identifies an immutable asset
set, and the authoring sources under `authoring/` that generate them.

## Safety boundary

- Do not commit credentials, provider configuration, model transcripts, runtime databases, traces, or personal/production data.
- Cases must remain self-contained and offline: `acceptance.py` may execute only the copied workspace and must not call the network.
- A case contains `case.yaml`, `prompt.txt`, `base-workspace/`, `reference/`, and `acceptance.py`.
- `cases/` is generated: edit `authoring/` and run `authoring/build.py`, never hand-edit a case tree.
- Regenerate `caseTreeSha256` in `assets-manifest.json` after changing any file under `cases/`; the main repository lock must then be updated to the new immutable commit and manifest digest.

## Acceptance conventions (asset version 2026.09.11.2)

Every `acceptance.py` shares one harness; only its configuration block and hidden checks differ.

- Hygiene guards only what a case promises: existing tests and protected files (data, logs,
  contracts, frozen packages) stay byte-identical; changed source files stay inside the case's
  editable scope and change budget. New test files, tool caches (`.pytest_cache`, `__pycache__`,
  `target/` ...) and scratch files left in the workspace are allowed.
- Every hidden check runs in its own interpreter with its own timeout, so one crash or hang cannot
  zero the other checks. Check names keep the `functional.` / `boundary.` / `regression.` /
  `constraint.` prefixes for attribution.
- Performance checks are calibrated against an O(n) baseline measured on the same machine instead of
  a fixed number of seconds.
- Regression-protection contracts (L2-05, L4-04) live only inside `acceptance.py`.
- stdout carries one ASCII JSON result line; the last stderr line is `DIAGNOSTICS {...}` with the
  changed source files and the reason of every failed check.

L3 and L4 cases share the medium-size `opsdesk` project (about 35 modules with enforced layering);
each case copies it and injects one defect (L3) or leaves one feature missing (L4).

## Authoring workflow

`cases/` is build output. Everything is authored under `authoring/`:

| Path | Purpose |
| --- | --- |
| `authoring/build.py` | Assembles `cases/` and refreshes `assets-manifest.json` |
| `authoring/harness_template.py` | Shared acceptance harness (`@@CONFIG@@` / `@@HIDDEN@@` placeholders) |
| `authoring/opsdesk/` | Canonical medium-size project copied into every L3/L4 case |
| `authoring/small_agents.md` | `AGENTS.md` of the small single-module workspaces |
| `authoring/snippets/` | Hidden-check fragments shared by several cases (layering, frozen files) |
| `authoring/cases/<caseId>/` | `case.json`, `prompt.txt`, `base/`, `reference/`, `hidden.py` of one case |
| `authoring/gate.py` | Local NOP/oracle gate over a built case tree |
| `authoring/probes.py` | Adversarial probes: allowed behaviour stays green, shortcuts must fail |
| `authoring/make_l3_02_log.py` | Regenerates the L3-02 job log from a real traceback |

One case is described by `authoring/cases/<caseId>/case.json`: level metadata, three-dimensional
labels, variants, runner budget, the editable scope and change budget of the acceptance run, the
ordered hidden-check names, and the optional flags `opsdesk` (copy the shared project into the
workspace), `smallAgents` (add the small-project `AGENTS.md`), `issueFile` (also write the prompt into
the workspace, used by L6), `snippets` and `protected`. `hidden.py` holds one `@check("name")` function
per hidden check; `"@@TREE_SHA256:<path>@@"` is replaced at build time with the digests of the base
files a frozen-file constraint must guard.

```bash
# regenerate every case tree and the manifest digest
python authoring/build.py .

# draft mode: rebuild single cases without touching the manifest
python authoring/build.py . L3-02,L4-01

# quality gates
python authoring/gate.py cases              # NOP must fail, reference must pass
python authoring/probes.py                  # 25 adversarial probes
```

The main repository runs the same case tree through its runner, which also verifies the manifest
digest:

```bash
python <main-repo>/haifa-agent-testing/haifa-agent-autonomous-delivery/tools/run_case.py --assets-dir <this-repo> --case all --mode nop --repeat 3
```

After changing `authoring/opsdesk/` or the L3-02 base files, run `authoring/make_l3_02_log.py` so that
the committed job log keeps matching the code, then rebuild.

## Publishing an asset version

1. Work on a branch; run `authoring/build.py .`, `authoring/gate.py cases` and `authoring/probes.py`.
2. Bump `assetVersion` in `authoring/build.py` when the case semantics change, and the `caseVersion`
   of every case whose prompt or acceptance semantics changed.
3. Open a pull request against `main`; the merge commit SHA plus the SHA-256 of `assets-manifest.json`
   are what the main repository pins in `assets.lock.json`.
4. Update `assets.lock.json` in the main repository to that immutable revision and digest.
