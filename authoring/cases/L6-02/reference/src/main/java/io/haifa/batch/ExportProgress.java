package io.haifa.batch;

import java.io.IOException;
import java.nio.file.Path;

/** Progress checkpoint of one batch export, stored next to the export output. */
interface ExportProgress {
    int lastCompletedBatch() throws IOException;

    void markCompleted(int batch) throws IOException;

    static ExportProgress forOutput(Path output) {
        return new FileExportProgress(output.resolveSibling(output.getFileName() + ".progress"));
    }
}
