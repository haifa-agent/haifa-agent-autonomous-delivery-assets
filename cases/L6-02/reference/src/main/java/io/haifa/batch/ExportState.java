package io.haifa.batch;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

/** Persisted export progress for the bundled mini-project. */
final class ExportState {
    private ExportState() {}

    static int lastCompletedBatch(Path state) throws IOException {
        if (!Files.exists(state)) {
            return 0;
        }
        return Integer.parseInt(Files.readString(state, StandardCharsets.UTF_8).trim());
    }

    static void record(Path state, int batch) throws IOException {
        Files.writeString(
                state,
                Integer.toString(batch),
                StandardCharsets.UTF_8,
                StandardOpenOption.CREATE,
                StandardOpenOption.TRUNCATE_EXISTING);
    }
}