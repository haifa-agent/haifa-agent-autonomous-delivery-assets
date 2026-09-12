# opsdesk

Operations desk mini-project: Python 3.11, standard library only, no network.

- Run the suite: `python -m unittest discover -s tests`
- Command line: `python -m opsdesk --help`
- Sample data lives in `data/`; it is part of the product and must not be edited.

## Layering

Enforced by `tests/test_layers.py`:

- `opsdesk.util` imports no other `opsdesk` package.
- `opsdesk.core` and `opsdesk.config` may import only `opsdesk.util`.
- `opsdesk.adapter`, `opsdesk.store` and `opsdesk.reporting` may import `opsdesk.core` and `opsdesk.util`.
- `opsdesk.api` and `opsdesk/__main__.py` may import any package.

New code goes into the existing packages.

## Tests

The existing tests are the product contract: do not edit or delete them. New test files are welcome.
