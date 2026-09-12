# Changelog

Notable changes to KiCad-Master-Lib.

Format: [Keep a Changelog](https://keepachangelog.com/)

This repository had no formal releases through most of its history, so earlier entries are
grouped by dated development era rather than by version.

---

## [Unreleased]

### Added

- `scripts/lint_lib.py` — static checks over `kmlib-local/`: dead 3D-model paths,
  symbol Footprints with no library prefix or naming a footprint that does not exist,
  footprint name differing from file name (errors); `unspecified` pins, non-URL
  datasheets, empty Footprints (warnings).
- `scripts/check_parse.py` — loads every first-party library through `kicad-cli`.
- `scripts/gen_lib_tables.py --check` — exits non-zero when the committed tables are
  stale.
- `.github/workflows/lint.yml` — runs all three on every pull request, the parse step in
  the fleet's pinned KiCad 10 image.
- `PDS1040-13` (40 V 10 A Schottky, PowerDI 5) and `ZLLS350TA` (40 V 380 mA Schottky,
  SOD-523) in `KMLib_Discrete_Semiconductors`, with `POWERDI5_DIO` and `DIODE_SOD-523_DIO`
  footprints (and `-L`/`-M` variants) and 3D models.
- `SI7288DP-T1-GE3` (dual N-channel 40 V MOSFET) in `KMLib_Discrete_Semiconductors`, with
  `POWERPAK_SO-8_DUAL_VIS` footprint (and `-L`/`-M` variants) and 3D model. Replaces the
  Slice_SOLR rescue symbol, which still carried the AO4882 value, datasheet and SOIC-8
  footprint it had been cloned from.
- `LTC4311ISC6-TRMPBF` (I2C accelerator) — symbol, `SOT-6_SC_LIT` footprint and its
  variants, and 3D model.

### Fixed

- `1217861-1_Tab`: both pins were `unspecified`, so every connection to the tab raised a
  `pin_to_pin` ERC warning. Now `passive`.
- 17 footprint `(model ...)` paths that resolved nowhere — KiCad 5 library names
  (`Housings_QFP.3dshapes/…`, `Pin_Headers.3dshapes/…`), `${KIPRJMOD}`-relative paths, and
  `${KICAD9_3DMODEL_DIR}` — now point at the equivalent KiCad 10 stock models via
  `${KICAD10_3DMODEL_DIR}`.
- Six symbol Footprints that could never resolve: `NTGS4111PT1G`, the two Phoenix PTSA
  terminals (no library prefix), the Wago 2606 and both Keystone test points (wrong
  footprint name).
- `KMLib_Aesthetic/BREAD_logo_v1.kicad_mod` declared itself `LOGO`; KiCad keys
  footprints by the name inside the file.

### Removed

- **Git LFS.** `.gitattributes` tracked `*.step` and `*.stl` through LFS, but only 14 files
  (22.6 MB) were ever stored that way — `*.stp` and `*.wrl` were not tracked, and neither
  were the vendored 3D models. Any clone without `git-lfs` installed silently received
  132-byte pointer files instead of models, and KiCad reported nothing: the 3D viewer simply
  showed no model.

  The 14 objects have been fetched from LFS storage and committed as ordinary files. At
  22.6 MB, LFS offered no benefit and cost a hard dependency on every clone and CI job.

### Added

- `CHANGELOG.md`.

### Changed

- Documentation updated for KiCad 10, the committed library tables, and vendoring.
  `KMLIB_LOCAL` is documented as `${KICAD_MASTER_LIB}/kmlib-local` with a forward slash;
  the backslash previously given does not resolve on Linux or macOS, and KiCad reports no
  error when it fails — 3D models simply do not appear.

---

## 2026-07-12

### Changed

- Vendored upstream libraries synced ([#4]):
  - `SparkFun-KiCad-Libraries` `42e5152f` → `2423e36a` (123 commits)
  - `OPL_Kicad_Library` `d3392376` → `b0035c51` (6 commits)

  No board's library resolution changed. Of the footprints in use, only `Standoff` and
  `Jumper_2_NC_Trace` changed, and both retain identical pad geometry.

---

## 2026-07-11 — vendoring and library tables ([#1])

### Added

- `kmlib.fp-lib-table`, `kmlib.sym-lib-table`, `kmlib.design-block-lib-table` — committed
  library tables registering all 51 footprint, 46 symbol and 10 design-block libraries via
  `${KICAD_MASTER_LIB}`. A clean clone now resolves every library without per-machine KiCad
  configuration.
- `scripts/gen_lib_tables.py` — regenerates the tables from what is on disk.
- `scripts/vendor_sync.py` — re-vendors an upstream library via a three-way merge, so local
  modifications survive an upstream sync.
- `scripts/check_drift.py` and a daily `upstream-drift` workflow — opens a tracking issue
  when an upstream moves past its pin. Nothing syncs automatically.
- `vendor.yaml` — manifest of upstream URL, tracked ref, pinned commit and licence for each
  vendored library.
- `KMLib_Connectors:BREAD_Slice_Bus_10Pin` — the BREAD slice-bus connector footprint.

### Changed

- Upstream libraries (SparkFun, Seeed OPL, DigiKey, Arduino) are **vendored** under
  `vendor/` instead of tracked as git submodules.
- Names no longer contain spaces (`Thermal Pad` → `Thermal_Pad`, and similar), since names
  appear verbatim in `lib_id` strings and on command lines.

### Fixed

- `LMD18200TNOPB`: 3D model path pointed outside `3dmodels/IC_THT.3dshapes/`.

---

## 2026-04 — organisation

### Changed

- Org rename: `FEASTorg` → `feastorg`.

---

## 2026-01 — reorganisation

### Changed

- Symbols, footprints and 3D models reorganised into categorised `KMLib_*` libraries.
- Prototyping footprints renamed and grouped.

---

## 2025-04 — 3D models

### Added

- 3D models for KMLib parts, stored via Git LFS (since removed — see [Unreleased]).
- Design blocks (`kmlib-local/blocks/`), migrated from the archived
  `KiCad-Hierarchical-Designs` repository.
- GitHub Pages documentation.

---

## 2024-05 — initial

### Added

- Initial library: FEAST symbols and footprints, with upstream vendor libraries as git
  submodules.

[#1]: https://github.com/feastorg/KiCad-Master-Lib/pull/1
[#4]: https://github.com/feastorg/KiCad-Master-Lib/pull/4
