# Project conventions

- Java 17, Maven build (`mvn -q -DskipTests package`), no network access is guaranteed.
- `javac --release 17 -d <out> $(find src/main/java -name '*.java')` compiles the project without Maven.
- New tests under `src/test/java` are welcome; they must not add runtime dependencies.
