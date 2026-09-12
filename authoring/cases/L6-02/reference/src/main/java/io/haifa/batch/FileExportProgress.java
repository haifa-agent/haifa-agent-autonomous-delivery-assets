package io.haifa.batch;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;

/** Stores the last completed batch in a small side file, replaced atomically. */
final class FileExportProgress implements ExportProgress {
    private final Path file;

    FileExportProgress(Path file) {
        this.file = file;
    }

    @Override
    public int lastCompletedBatch() throws IOException {
        if (!Files.exists(file)) {
            return 0;
        }
        return Integer.parseInt(Files.readString(file, StandardCharsets.UTF_8).trim());
    }

    @Override
    public void markCompleted(int batch) throws IOException {
        Path temporary = file.resolveSibling(file.getFileName() + ".tmp");
        Files.writeString(temporary, Integer.toString(batch), StandardCharsets.UTF_8);
        Files.move(temporary, file, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
    }
}
