package io.depot.tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;

import org.junit.jupiter.api.Test;

class ChecksumTest {
    @Test
    void matchesThePublishedValues() {
        assertEquals("ffffffffffffffff", Checksum.of(""));
        assertEquals("a382a109e29e668b", Checksum.of("depot"));
        assertEquals("acfc813210dcad25", Checksum.of("hello world"));
    }

    @Test
    void isSensitiveToInput() {
        assertNotEquals(Checksum.of("abc"), Checksum.of("abd"));
    }
}
