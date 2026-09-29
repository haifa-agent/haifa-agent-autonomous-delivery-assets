package io.depot.tools;

import java.nio.charset.StandardCharsets;

/**
 * Reflected polynomial-64 checksum shared with the Python side.
 *
 * <p>The byte-for-byte twin lives in {@code depot/core/checksum.py}; exchange files are accepted
 * only when both implementations agree, so a change to one must be mirrored in the other.
 */
public final class Checksum {
    private static final long POLY = 0xC96C5795D7870F42L;

    private Checksum() {
    }

    public static String of(final byte[] data) {
        long value = 0xFFFFFFFFFFFFFFFFL;
        for (final byte raw : data) {
            value ^= (raw & 0xFFL);
            for (int bit = 0; bit < 8; bit++) {
                if ((value & 1L) != 0L) {
                    value = (value >>> 1) ^ POLY;
                } else {
                    value >>>= 1;
                }
            }
        }
        return String.format("%016x", value);
    }

    public static String of(final String text) {
        return of(text.getBytes(StandardCharsets.UTF_8));
    }
}
