As a maintainer I want the inventory tool to import rows from a CSV file with the columns
`sku,name,quantity`:

- `cli.py import --store <store.json> <file.csv>` imports every valid row into the JSON store,
  keyed by sku,
- one `ok <sku>` line is printed per imported row and one `error <row-number>: <reason>` line per
  rejected row (empty sku, empty name, or a quantity that is not a non-negative integer),
- the last line is the summary `imported=<n> failed=<n>`,
- the exit code is 0 only when every row was imported; a partial import exits non-zero,
- a missing file, a wrong CSV header or a store that cannot be written is reported on stderr and
  exits with code 2.

Deliver the feature in the bundled mini-project; no design guidance beyond this issue.