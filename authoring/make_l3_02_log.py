"""Regenerate the L3-02 job log from a real traceback (buggy render, original nightly).

Run it after changing opsdesk/ or the L3-02 base files so that the log keeps matching the code.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GEN = Path(__file__).resolve().parent
root = Path(tempfile.mkdtemp(prefix="l302-")) / "opsdesk-srv"
shutil.copytree(GEN / "opsdesk", root)
shutil.copy2(GEN / "cases" / "L3-02" / "base" / "opsdesk" / "reporting" / "render.py", root / "opsdesk" / "reporting" / "render.py")
completed = subprocess.run(
    [sys.executable, "-m", "opsdesk", "nightly", "2026-02-10"],
    cwd=root,
    capture_output=True,
    text=True,
    env={"PYTHONDONTWRITEBYTECODE": "1", "SYSTEMROOT": "C:\\Windows", "PATH": ""},
)
lines = completed.stderr.splitlines()
start = next(index for index, line in enumerate(lines) if "__main__.py" in line)
frames = ["Traceback (most recent call last):"] + lines[start:]
frames = [
    line.replace(str(root), "/srv/opsdesk").replace("\\", "/") if line.startswith('  File "') else line
    for line in frames
]
text = "\n".join(frames)
log = (
    "2026-02-11 02:00:01 INFO  scheduler: starting job nightly-report night=2026-02-10\n"
    "2026-02-11 02:00:01 INFO  nightly-report: loaded 6 transactions, 3 accounts\n"
    "2026-02-11 02:00:02 ERROR nightly-report: job failed\n"
    + text
    + "\n2026-02-11 02:00:02 INFO  scheduler: job nightly-report exited with status 1\n"
)
target = GEN / "cases" / "L3-02" / "base" / "logs" / "nightly-report-2026-02-11.log"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(log, encoding="utf-8", newline="\n")
print(log)
