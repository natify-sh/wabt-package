# Third-party material

This package redistributes, unmodified, the command-line tools and the `wasm2c` runtime sources of
[WABT, the WebAssembly Binary Toolkit](https://github.com/WebAssembly/wabt) (Apache License 2.0), built from the
release tag recorded in `_wabt_version.txt`. It is **not an official WABT release** and is not affiliated with the
WABT project or the WebAssembly Community Group.

- WABT: Copyright 2016-present WebAssembly Community Group participants. Licence: `wabt/LICENSE` (in the sdist) /
  `licenses/wabt/LICENSE` (in the wheel's metadata), the Apache License 2.0.
- PicoSHA2 (`wabt/third_party/picosha2`, linked into the tools for SHA-256): MIT licence; see
  `wabt/third_party/picosha2/LICENSE` in the sdist.
- simde (`wabt/third_party/simde`; the headers are in the wheel as `wabt_package/include/simde/`, with its `COPYING`): MIT licence,
  Copyright (c) 2017 Evan Nemerson and contributors. The commit is the one WABT pins; see `wabt_package.simde_commit()`.

The packaging code of this repository (`build_wabt.py`, `setup.py`, `src/wabt_package/`) is licensed under the
Apache License 2.0 as well (see `LICENSE`).
