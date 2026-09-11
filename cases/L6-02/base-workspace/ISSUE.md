Long exports are lost when the process is interrupted: re-running the export starts over and the output
file ends up with duplicated records. Make the batch export resumable.

The exporter appends one line per record to `--output` and processes `--batches` batches of three
records. The `--interrupt-after-batch <n>` test hook simulates an interrupted process at the end of
batch n: it must flush the export progress and exit with code 75. A later run of the same command must
continue from the last completed batch, so the output file never repeats a record and never loses one.

Keep `mvn -q -DskipTests package` working; the project targets Java 17. No design guidance beyond this
issue.