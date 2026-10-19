# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The version is the WABT release the
tools are built from plus a build number: `1.0.42.0` is WABT 1.0.42, first build.

## [Unreleased]

## [1.0.42.0] - 2026-10-19

First stable release (after the `1.0.42.0b1` and `1.0.42.0b2` pre-releases).

### Added
- WABT 1.0.42 built from the `wabt` submodule, pinned to its release tag. The 11 tools `spectest-interp`, `wasm-interp`,
  `wasm-objdump`, `wasm-stats`, `wasm-strip`, `wasm-validate`, `wasm2c`, `wasm2wat`, `wast2json`, `wat-desugar` and
  `wat2wasm` are console scripts, and `python -m wabt_package TOOL ...` runs one without relying on `PATH`.
- Python API: `run()` (`subprocess.run`, `check=True` by default), `get_executable()`, `bin_dir()`, `TOOLS`,
  `wabt_version()`. The package is typed (`py.typed`) and has no dependencies; Python 3.11+, CPython and PyPy.
- The `wasm2c` runtime sources (`wasm-rt.h`, `wasm-rt-impl.c`, ...) of the same version, at `runtime_dir()`.
- The headers of simde (of the commit WABT pins as `third_party/simde`) at `include_dir()`, with `simde_commit()`: the C that
  `wasm2c` writes for SIMD includes `<simde/wasm/simd128.h>`.
- `py3-none-<platform>` wheels built with cibuildwheel (the executables do not depend on the interpreter):
  - Linux (manylinux and musllinux): x86_64, aarch64, i686, armv7l, ppc64le, s390x, riscv64
  - Windows: x64, ARM64, x86
  - macOS: arm64, x86_64, universal2 (minimum macOS 11.0)
- An sdist that builds the tools from source with a C++20 compiler (`cmake` and `ninja` are fetched from PyPI), for every
  platform without a wheel.
- The version is derived from the git tag (`v1.0.42.0` is WABT 1.0.42, build 0) with setuptools-scm; the publish workflow
  checks that the tag starts with the release of the `wabt` submodule.
- Publish workflow: a tag push publishes to PyPI (trusted publishing) and creates a GitHub Release with the section of this
  file; a manual run can publish to TestPyPI with an overridden version; pull requests build everything without publishing.

### Changed
- The executables are linked statically against the C++ runtime (libstdc++, libgcc, the MSVC runtime) and use WABT's own
  SHA-256 (`picosha2`) instead of OpenSSL: no shared library but the C library of the system is needed. The build fails
  rather than fall back to the shared runtime.

### Tests
- Every tool runs; `.wat` -> `.wasm` -> `.wat` round trip; the C of `wasm2c` (with and without SIMD) compiles against the
  bundled runtime and headers; the console scripts and `python -m` work.
- Every wheel is checked on its platform to be linked statically (Linux: only the C library; macOS: only system libraries and
  no newer macOS than the wheel says; Windows: no C runtime DLLs).

### Build
- Linux armv7l is built with GCC 12 (the manylinux_2_31 image has GCC 9, which lacks `<span>` and `std::bit_cast`), riscv64
  with `libstdc++-static` installed; musllinux ppc64le, s390x and riscv64 use the plain `build` frontend (no uv wheels there).
- Windows builds compile with `/MP`.

[Unreleased]: https://github.com/natify-sh/wabt-package/compare/v1.0.42.0...HEAD
[1.0.42.0]: https://github.com/natify-sh/wabt-package/releases/tag/v1.0.42.0
