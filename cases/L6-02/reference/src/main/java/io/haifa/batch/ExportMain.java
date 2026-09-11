package io.haifa.batch;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;

/** Batch export entry point for the bundled mini-project. */
public final class ExportMain {
    private static final int BATCH_SIZE = 3;

    private ExportMain() {}

    public static void main(String[] args) throws IOException {
        Path output = null;
        int batches = 1;
        int interruptAfter = -1;
        for (int index = 0; index < args.length; index++) {
            switch (args[index]) {
                case "--output" -> output = Path.of(args[++index]);
                case "--batches" -> batches = Integer.parseInt(args[++index]);
                case "--interrupt-after-batch" -> interruptAfter = Integer.parseInt(args[++index]);
                default -> throw new IllegalArgumentException("unknown argument: " + args[index]);
            }
        }
        if (output == null) {
            throw new IllegalArgumentException("--output is required");
        }
        Path state = Path.of(output + ".state");
        int start = ExportState.lastCompletedBatch(state) + 1;
        for (int batch = start; batch <= batches; batch++) {
            Files.write(
                    output,
                    lines(batch),
                    StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE,
                    StandardOpenOption.APPEND);
            ExportState.record(state, batch);
            if (batch == interruptAfter) {
                System.exit(75);
            }
        }
    }

    private static List<String> lines(int batch) {
        List<String> lines = new ArrayList<>();
        for (int index = 0; index < BATCH_SIZE; index++) {
            int record = (batch - 1) * BATCH_SIZE + index + 1;
            lines.add(String.format("rec-%02d", record));
        }
        return lines;
    }
}