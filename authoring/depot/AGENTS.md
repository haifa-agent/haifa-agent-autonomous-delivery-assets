# depot

Distribution-center operations backend for orders, inventory, picking and shipping.

Python 3.11, standard library only, no network. A small Java sub-module under `java/` implements the
shared checksum used when exchange files cross the process boundary.

- Run the suite: `python -m unittest discover -s tests`
- Command line: `python -m depot --help`
- Sample data lives in `data/`; it is part of the product and must not be edited.

## Layering

Enforced by `tests/test_layers.py`. Each layer may import only itself and the layers below it:

```
api  ->  adapter  ->  store  ->  core
```

- `depot.core` is the pure domain model: it imports nothing from `depot` except `depot.core`,
  performs no file I/O and must not use `open`, `pathlib` or `os.path`.
- `depot.store` owns every read and write of `data/`.
- `depot.adapter` owns configuration parsing, the exchange-file adapters and the handler registry.
- `depot.api` holds the application services and the command line.
- `depot/__main__.py` may import any layer.

New code goes into the existing layers. A change that needs to cross a layer must follow the
direction above; importing a higher layer is a defect.

## Contracts

The `AGENTS.md` files are the product contract for their topics. When a requirement conflicts with a
contract here, the contract wins, and the conflict must be recorded in writing inside the workspace
(for example `DECISION.md`) rather than resolved silently.

Optional fields are omitted from serialized payloads. A value that is not set is expressed by the
absence of the key, never by a `null`; consumers already rely on `key not in payload`.

## Tests

The existing tests are the product contract: do not edit or delete them. New test files are welcome.
Scratch files and throwaway scripts belong in `var/`, which is not part of the delivered source.
