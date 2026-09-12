import json
import subprocess
import sys

SETTINGS = "cache_dir = $PROJECT/cache\nreport_dir = ${PROJECT}/reports\nmode = fast\n"


def _resolved(project):
    from opsdesk.config.settings import load_settings

    return load_settings(SETTINGS, project)


def _expect(project):
    settings = _resolved(project)
    ok = settings.get("cache_dir") == project + "/cache" and settings.get("report_dir") == project + "/reports"
    return ok, f"{project!r} -> cache_dir={settings.get('cache_dir')!r}"


@check("functional.windowsUserPath")
def windows_user_path():
    return _expect(r"C:\Users\dev\opsdesk")


@check("boundary.escapeLookalikePaths")
def escape_lookalikes():
    for project in (
        r"D:\work\new-app",
        r"E:\temp\r1",
        r"C:\1\g<0>\x",
        r"C:\data\n2\a",
        r"\\fileserver\share\ops",
    ):
        ok, detail = _expect(project)
        if not ok:
            return False, detail
    return True


@check("functional.cliOnWindowsPath")
def cli_on_windows_path():
    project = r"C:\Users\dev\opsdesk"
    completed = subprocess.run(
        [sys.executable, "-m", "opsdesk", "settings", project],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=60,
    )
    settings = json.loads(completed.stdout)
    return (
        completed.returncode == 0
        and settings["cache_dir"] == project + "/cache"
        and settings["report_dir"] == project + "/reports"
        and settings["archive_dir"] == "/var/opsdesk/archive",
        repr(settings),
    )


@check("regression.posixPaths")
def posix_paths():
    return _expect("/srv/demo")


@check("regression.malformedLinesStillSkipped")
def malformed_lines():
    from opsdesk.config.settings import load_settings

    settings = load_settings("= orphan value\nnot a setting\nmode = fast\n", "/srv/demo")
    return settings.get("mode") == "fast" and settings.get("cache_dir") == ".cache" and "not a setting" not in settings


@check("regression.plainValuesUntouched")
def plain_values():
    from opsdesk.config.settings import load_settings

    settings = load_settings("backup_dir = D:\\backup\\ops\nlabel = cost $5\n", r"C:\Users\dev\opsdesk")
    return settings.get("backup_dir") == "D:\\backup\\ops" and settings.get("label") == "cost $5", repr(settings)
