As a maintainer I want the inventory tool to import items from a CSV file.

- `python -m cli import --store <store.json> <file.csv>` imports every valid row of a CSV file whose
  header is `sku,name,quantity` into the JSON store, keyed by sku. A row whose sku already exists in the
  store updates that item.
- Files exported by spreadsheet tools may start with a UTF-8 byte order mark; they must be accepted.
- For every imported row print `ok <sku>`; for every rejected row print `error <line>: <reason>`, where
  `<line>` is the line number in the file (the header is line 1). A row is rejected when its sku or its
  name is empty, or when its quantity is not a non-negative integer.
- The last line printed is the summary `imported=<n> failed=<n>`.
- The exit code is 0 when every row was imported and 1 when at least one row was rejected; the valid
  rows are imported in both cases.
- A missing file, a wrong header or a store that cannot be written is reported on stderr (a message,
  not a traceback) and exits with code 2; an existing store must be left untouched in these cases.
- Importing the same file twice leaves the store exactly as it was after the first import.
- The existing `add` and `list` commands keep working unchanged.

Deliver the feature in the bundled project. There is no design guidance beyond this issue.
