# KiCad-Master-Lib

An attempt to make a master KiCad library for symbols and footprints as well as their associated 3D models and a collection of design blocks.

This is mainly to help manage the libraries used by FEAST (https://feastorg.github.io) in a single place for easy updating and sharing across projects.

If you are looking for `KiCad-Hierarchical-Designs`, that repository has been archived and all relevant content has been moved here under `kmlib-local/blocks/`.

Hopefully this prevents me from going completely insane. - CKB

## Quick Start

```sh
git clone https://github.com/feastorg/KiCad-Master-Lib.git
```

Then set `KICAD_MASTER_LIB` to wherever you cloned it, and add the committed tables to
your KiCad configuration:

| Table | Registers |
| --- | --- |
| `kmlib.fp-lib-table` | 51 footprint libraries |
| `kmlib.sym-lib-table` | 46 symbol libraries |
| `kmlib.design-block-lib-table` | 10 design-block libraries |

Every URI in those tables is written relative to `${KICAD_MASTER_LIB}`, so a clean clone
resolves every symbol, footprint and design block with **no dependence on a developer's
global KiCad configuration**. That is what makes designs in this ecosystem reproducible
from source.

Regenerate the tables after adding or removing a library:

```sh
python3 scripts/gen_lib_tables.py
```

See [docs/getting_started.md](docs/getting_started.md) for setup instructions or visit
[feastorg.github.io/kicad-master-lib](https://feastorg.github.io/kicad-master-lib/) for
full documentation.

## Checks

Before pushing a change to `kmlib-local/`, run what CI runs:

```sh
python3 scripts/lint_lib.py             # static checks, no KiCad needed
python3 scripts/gen_lib_tables.py --check
python3 scripts/check_parse.py          # loads every library through kicad-cli
```

`lint_lib.py` fails on the mistakes that are mechanical to fix and that KiCad reports
late or never: a footprint whose `(model ...)` path resolves nowhere, a symbol whose
Footprint has no `LIB:` prefix or names a footprint that does not exist, a footprint
whose name differs from its file name. It warns, without failing, on what needs a
datasheet in hand: `unspecified` pins, a Datasheet that is not a URL, an empty
Footprint. `--strict` promotes warnings to errors. Model paths must be
`${KMLIB_LOCAL}/3dmodels/...` for first-party models or `${KICAD10_3DMODEL_DIR}/...`
for KiCad's own.

`check_parse.py` needs `kicad-cli`; with the Flatpak, set
`KICAD_CLI="flatpak run --command=kicad-cli org.kicad.KiCad"`. CI runs it in the same
pinned KiCad image the board repos use.

## Layout

```
kmlib-local/     first-party FEAST symbols, footprints, 3D models, design blocks
vendor/          upstream libraries, vendored (see vendor.yaml)
scripts/         library table generation, vendoring, drift detection, lint
```

## Vendored upstream libraries

Upstream libraries live under `vendor/`, pinned in [`vendor.yaml`](vendor.yaml).

[`vendor.yaml`](vendor.yaml) is the manifest: upstream URL, tracked ref, **pinned
commit**, and licence for each. The pin moves forward deliberately, by a human, after
review — never automatically.

| Library | Licence |
| --- | --- |
| [SparkFun-KiCad-Libraries](https://github.com/sparkfun/SparkFun-KiCad-Libraries) | CC-BY-4.0 |
| [OPL_Kicad_Library](https://github.com/Seeed-Studio/OPL_Kicad_Library) (Seeed) | CC-BY-SA-4.0 |
| [digikey-kicad-library](https://github.com/Digi-Key/digikey-kicad-library) | CC-BY-SA-4.0, with an exception — see its `LICENSE.md` |
| [arduino-kicad-library](https://github.com/Alarm-Siren/arduino-kicad-library) | CC-BY-SA-4.0 |

### Tracking upstream

A daily [`upstream-drift`](.github/workflows/upstream-drift.yml) workflow asks each
upstream whether it has moved past our pin and opens **one tracking issue per drifted
library**, linking the upstream diff. Nothing is ever synced automatically.

Check drift yourself at any time:

```sh
python3 scripts/check_drift.py
```

Integrate a drifted library after reviewing its issue:

```sh
python3 scripts/vendor_sync.py <name> --check   # preview the upstream commits
python3 scripts/vendor_sync.py <name>           # three-way merge, then review and commit
```

**Local modifications to vendored trees are preserved.** `vendor_sync.py` replays your
copy onto the commit we last vendored, then lets git three-way merge the new upstream on
top — so local fixes survive a sync. A genuine conflict is reported and the pin is left
unadvanced until you resolve it. Prefer upstreaming a fix over carrying it here.

## Cloning without 3D models (CI, or slow links)

A full checkout is ~356 MB, of which ~283 MB is 3D models. ERC, DRC, netlist generation
and schematic generation never read a 3D model — only 3D renders and STEP export do.

Excluding them drops the checkout to **~73 MB**, with all 51 footprint and 46 symbol
libraries still present:

```sh
git clone --filter=blob:none --sparse https://github.com/feastorg/KiCad-Master-Lib.git
cd KiCad-Master-Lib
git sparse-checkout set --no-cone '/*' \
    '!*.step' '!*.STEP' '!*.stp' '!*.STP' '!*.wrl' '!*.WRL'
```

Exclusion is by file extension rather than by directory on purpose: some upstreams keep
3D models loose in product folders rather than under `*.3dshapes/`.

---

CC0-1.0 license is for this repo ONLY. Vendored libraries under `vendor/` retain their
own licences — see [`vendor.yaml`](vendor.yaml) and each library's own licence file.
