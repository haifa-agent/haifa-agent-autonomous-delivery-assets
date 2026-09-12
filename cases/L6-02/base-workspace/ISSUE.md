Long exports are lost when the process is interrupted: re-running the export starts over and the output
file ends up with duplicated records. Make the batch export resumable.

The exporter (`io.haifa.batch.ExportMain`) appends one line per record to `--output` and processes
`--batches` batches of three records. The `--interrupt-after-batch <n>` test hook simulates a crash at
the end of batch n: the process must persist its progress and exit with code 75. A later run of the same
export (same `--output` and `--batches`, with or without the hook) must continue after the last
completed batch, so that the output file never repeats a record and never loses one. Running an export
that already completed again must not change its output. Exports to different output files are
independent of each other.

Note that `main` does not compile at the moment: a contributor merged an unfinished progress-tracking
class. Keep `mvn -q -DskipTests package` working; the project targets Java 17 and must not gain new
runtime dependencies. There is no design guidance beyond this issue.
