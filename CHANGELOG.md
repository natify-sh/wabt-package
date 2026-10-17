# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The version is the WABT release the
tools are built from plus a build number: `1.0.42.0` is WABT 1.0.42, first build.

## [Unreleased]

### Added
- The headers of simde (of the commit WABT pins) at `wabt_package.include_dir()`, with `simde_commit()`: the C that `wasm2c` writes for
  SIMD includes `<simde/wasm/simd128.h>`.
- Wheels for Linux x86, ARMv7, ppc64le, s390x and riscv64, Windows x86, macOS universal2 (see the publish workflow).
- WABT 1.0.42 built from the `wabt` submodule: `spectest-interp`, `wasm-interp`, `wasm-objdump`, `wasm-stats`,
  `wasm-strip`, `wasm-validate`, `wasm2c`, `wasm2wat`, `wast2json`, `wat-desugar`, `wat2wasm`, as console scripts and
  through `wabt_package.run()` / `get_executable()`.
- The `wasm2c` runtime sources (`wasm-rt.h`, `wasm-rt-impl.c`, ...) of the same version, at `wabt_package.runtime_dir()`.
- `py3-none-<platform>` wheels (Linux manylinux/musllinux x86_64 and aarch64, Windows x64 and ARM64, macOS arm64 and
  x86_64) built with cibuildwheel, and an sdist that builds from source with a C++ compiler.
