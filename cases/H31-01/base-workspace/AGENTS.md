# kiosk

Self-service kiosk backend: Python 3.11, standard library only, no network.

- Run the suite: `python -m unittest discover -s tests`
- Command line: `python -m kiosk --help`
- Sample data lives in `data/`; it is part of the product and must not be edited.

## Layering

Enforced by `tests/test_layers.py`:

- `kiosk.core` is pure domain logic: it imports no other `kiosk` package and touches no file.
- `kiosk.app` holds the services and all file access; it may import `kiosk.core`.
- `kiosk/__main__.py` may import any package.

New code goes into the existing packages.

## Tests

The existing tests are the product contract: do not edit or delete them. New test files are welcome.
