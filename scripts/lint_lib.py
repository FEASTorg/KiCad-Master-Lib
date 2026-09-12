#!/usr/bin/env python3
"""Static checks over the first-party libraries in kmlib-local/.

No KiCad needed -- this reads the s-expression files as text. It catches the
mistakes that KiCad itself reports late or not at all: a footprint whose 3D
model path resolves nowhere, a symbol whose Footprint property has no library
prefix (so it can never resolve), a pin left `unspecified` (ERC noise on every
board that uses it).

Errors fail the run; warnings are printed and do not. Errors are the checks
that are purely mechanical to fix. Warnings need a human with the datasheet.

    python3 scripts/lint_lib.py            # whole library
    python3 scripts/lint_lib.py --strict   # warnings fail too

Errors
  fp-name        footprint name inside the file differs from the file name
  fp-model       model path is not ${KMLIB_LOCAL}/3dmodels/... (first-party)
                 or ${KICAD10_3DMODEL_DIR}/... (stock), or the first-party
                 model file is not in the repository
  sym-fp-prefix  symbol Footprint has no LIB: prefix
  sym-fp-lib     symbol Footprint names a KMLib_* library that does not exist
  sym-fp-missing symbol Footprint names a KMLib_* footprint that does not exist

Warnings
  sym-pin-unspec symbol has pins of type `unspecified`
  sym-datasheet  Datasheet is set but is not a URL
  sym-fp-empty   symbol has no Footprint
  sym-junk       leftover properties from an import (Field4, Field5, ki_locked)

Model existence is checked against the git index, not the working tree, so a
sparse checkout that skips *.step still passes.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / "kmlib-local"
FP_ROOT = LOCAL / "footprints"
SYM_ROOT = LOCAL / "symbols"

LOCAL_MODEL_PREFIX = "${KMLIB_LOCAL}/3dmodels/"
STOCK_MODEL_PREFIX = "${KICAD10_3DMODEL_DIR}/"
JUNK_PROPERTIES = ("Field4", "Field5", "ki_locked")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, code: str, where: str, detail: str) -> None:
        self.errors.append(f"error   {code:<15} {where}: {detail}")

    def warn(self, code: str, where: str, detail: str) -> None:
        self.warnings.append(f"warning {code:<15} {where}: {detail}")


def tracked_files() -> set[str]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "kmlib-local/3dmodels"],
        check=True, capture_output=True, text=True,
    ).stdout
    return {p for p in out.split("\0") if p}


def block_span(text: str, start: int) -> tuple[int, int]:
    """Span of the balanced s-expression beginning at text[start] == '('."""
    depth = 0
    in_str = False
    i = start
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    raise ValueError("unbalanced s-expression")


def prop(block: str, name: str) -> str | None:
    m = re.search(r'\(property "' + re.escape(name) + r'" "([^"]*)"', block)
    return m.group(1) if m else None


# --- footprints -----------------------------------------------------------------

def lint_footprint(path: Path, models: set[str], rep: Report) -> None:
    lib = path.parent.name[: -len(".pretty")]
    where = f"{lib}:{path.stem}"
    text = path.read_text(errors="replace")

    # KiCad 10 writes (footprint "Name"); KiCad 5 wrote (module Name ...).
    m = re.match(r'\((?:footprint|module)\s+(?:"([^"]+)"|(\S+))', text)
    name = (m.group(1) or m.group(2)) if m else None
    if name != path.stem:
        rep.error("fp-name", where, f"file holds footprint {name!r}")

    for mp in re.findall(r'\(model\s+"?([^"\s)]+)', text):
        if mp.startswith(LOCAL_MODEL_PREFIX):
            rel = "kmlib-local/" + mp[len("${KMLIB_LOCAL}/"):]
            if rel not in models:
                rep.error("fp-model", where, f"model not in repository: {rel}")
        elif not mp.startswith(STOCK_MODEL_PREFIX):
            rep.error("fp-model", where, f"model path must start with {LOCAL_MODEL_PREFIX} or {STOCK_MODEL_PREFIX}: {mp}")


# --- symbols -----------------------------------------------------------------------

def symbols(text: str):
    """Yield (name, block) for each top-level symbol in a .kicad_sym file."""
    for m in re.finditer(r'^\t\(symbol "([^"]+)"', text, re.M):
        s, e = block_span(text, m.start() + 1)
        yield m.group(1), text[s:e]


def lint_symbol(lib: str, name: str, block: str, fp_libs: dict[str, Path], rep: Report) -> None:
    where = f"{lib}:{name}"
    if "(extends " in block:
        return  # inherits properties from its parent

    fp = prop(block, "Footprint")
    if not fp:
        rep.warn("sym-fp-empty", where, "no Footprint")
    elif ":" not in fp:
        rep.error("sym-fp-prefix", where, f"Footprint {fp!r} has no library prefix")
    else:
        fp_lib, fp_name = fp.split(":", 1)
        if fp_lib.startswith("KMLib_"):
            if fp_lib not in fp_libs:
                rep.error("sym-fp-lib", where, f"no such footprint library {fp_lib!r}")
            elif not (fp_libs[fp_lib] / f"{fp_name}.kicad_mod").exists():
                rep.error("sym-fp-missing", where, f"no footprint {fp!r}")

    ds = prop(block, "Datasheet")
    if ds and not re.match(r"(https?://|~)", ds):
        rep.warn("sym-datasheet", where, f"Datasheet is not a URL: {ds!r}")

    n = len(re.findall(r"\(pin unspecified ", block))
    if n:
        rep.warn("sym-pin-unspec", where, f"{n} unspecified pin(s)")

    for junk in JUNK_PROPERTIES:
        if f'(property "{junk}"' in block:
            rep.warn("sym-junk", where, f"leftover property {junk!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args()

    rep = Report()
    models = tracked_files()
    fp_libs = {d.name[: -len(".pretty")]: d for d in sorted(FP_ROOT.glob("*.pretty"))}

    n_fp = n_sym = 0
    for d in fp_libs.values():
        for path in sorted(d.glob("*.kicad_mod")):
            n_fp += 1
            lint_footprint(path, models, rep)

    for path in sorted(SYM_ROOT.glob("*.kicad_sym")):
        lib = path.stem
        for name, block in symbols(path.read_text(errors="replace")):
            n_sym += 1
            lint_symbol(lib, name, block, fp_libs, rep)

    for line in rep.errors + rep.warnings:
        print(line)
    failed = rep.errors or (args.strict and rep.warnings)
    print(f"{'FAIL' if failed else 'PASS'}  {n_fp} footprints, {n_sym} symbols, "
          f"{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
