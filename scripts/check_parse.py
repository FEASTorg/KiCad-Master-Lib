#!/usr/bin/env python3
"""Load every first-party library through kicad-cli and fail if anything does not parse.

lint_lib.py reads the files as text and cannot tell a malformed s-expression
from a good one. This asks KiCad itself: every *.kicad_sym and every *.pretty
under kmlib-local/ is exported to SVG into a scratch directory, and the run
fails if kicad-cli reports an error or plots fewer footprints than the library
holds. kicad-cli exits 0 on a failed plot, so the exit status alone proves
nothing -- both signals are checked.

Needs kicad-cli on PATH, or KICAD_CLI set to the command to run
(e.g. KICAD_CLI="flatpak run --command=kicad-cli org.kicad.KiCad").

    python3 scripts/check_parse.py
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / "kmlib-local"
KICAD_CLI = shlex.split(os.environ.get("KICAD_CLI", "kicad-cli"))


def run(args: list[str]) -> tuple[int, list[str]]:
    """Return the exit status and every output line that looks like a failure."""
    proc = subprocess.run(KICAD_CLI + args, capture_output=True, text=True)
    log = (proc.stdout + proc.stderr).splitlines()
    return proc.returncode, [l for l in log if re.search(r"\b(error|unable|failed)\b", l, re.I)]


def main() -> int:
    failures: list[str] = []
    n_fp = n_sym = 0
    # Scratch lives inside the repo: a sandboxed kicad-cli (Flatpak) cannot see /tmp.
    with tempfile.TemporaryDirectory(prefix=".parse-check-", dir=ROOT) as tmp:
        out = Path(tmp)

        for lib in sorted((LOCAL / "footprints").glob("*.pretty")):
            expected = sorted(p.stem for p in lib.glob("*.kicad_mod"))
            if not expected:
                continue
            dest = out / lib.name
            dest.mkdir()
            # kicad-cli only writes into an existing directory given with a trailing slash
            rc, errors = run(["fp", "export", "svg", "-o", f"{dest}/", str(lib)])
            plotted = sorted(p.stem for p in dest.glob("*.svg"))
            missing = sorted(set(expected) - set(plotted))
            n_fp += len(expected)
            if rc or missing or errors:
                failures.append(f"{lib.name}: {len(missing)} of {len(expected)} not plotted"
                                + (": " + ", ".join(missing) if missing else ""))
                failures.extend("    " + e for e in errors)

        for lib in sorted((LOCAL / "symbols").glob("*.kicad_sym")):
            dest = out / lib.stem
            dest.mkdir()
            rc, errors = run(["sym", "export", "svg", "-o", f"{dest}/", str(lib)])
            expected = len(re.findall(r'^\t\(symbol "', lib.read_text(errors="replace"), re.M))
            plotted = len(list(dest.glob("*.svg")))
            n_sym += 1
            if rc or errors or plotted < expected:
                failures.append(f"{lib.name}: exit {rc}, {plotted} plotted for {expected} symbols")
                failures.extend("    " + e for e in errors)

    for line in failures:
        print(line)
    ok = not failures
    print(f"{'PASS' if ok else 'FAIL'}  {n_fp} footprints, {n_sym} symbol libraries loaded by kicad-cli")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
