# wabt-package

[WABT](https://github.com/WebAssembly/wabt), the WebAssembly Binary Toolkit, as a Python package: the prebuilt
command-line tools and the `wasm2c` runtime, installable with `pip`. Like `libusb-package`, but for WABT.
An unofficial redistribution (Apache-2.0).

```sh
pip install wabt-package
wat2wasm add.wat -o add.wasm
wasm2c add.wasm -o add.c
```

## Version

`x.y.z.b`: `x.y.z` is the WABT release the tools are built from, `b` is the build number of this package
(`1.0.42.0` is WABT 1.0.42, first build).

## What is in it

| | |
|---|---|
| tools | `spectest-interp`, `wasm-interp`, `wasm-objdump`, `wasm-stats`, `wasm-strip`, `wasm-validate`, `wasm2c`, `wasm2wat`, `wast2json`, `wat-desugar`, `wat2wasm` |
| runtime | the C sources the code of `wasm2c` is compiled with (`wasm-rt.h`, `wasm-rt-impl.c`, ...), of the same version |
| simde | the headers (`include_dir()`) that the C of a SIMD module includes, of the commit WABT pins |

Each tool is a console script; `python -m wabt_package wat2wasm ...` runs one without relying on `PATH`.

```python
import wabt_package as wabt

wabt.run("wat2wasm", "in.wat", "-o", "out.wasm")  # subprocess.run, check=True by default
wabt.get_executable("wasm2c")  # pathlib.Path
wabt.runtime_dir()  # directory of wasm-rt.h, wasm-rt-impl.c, ...
wabt.include_dir()  # -I for <simde/...>; wabt.simde_commit() is the commit of those headers
wabt.wabt_version()  # "1.0.42"
```

### SIMD

The C that `wasm2c` writes for a module with SIMD instructions includes `<simde/wasm/simd128.h>`. WABT does not ship
[simde](https://github.com/simd-everywhere/simde) in its releases, so this package does: `include_dir()` is the directory to
pass with `-I` (it holds `simde/`), and `simde_commit()` says which commit it is: the one WABT itself pins as its submodule
`third_party/simde`, so the headers and `wasm2c` are of the same version. Modules without SIMD need nothing but `runtime_dir()`.

```sh
cc -c module.c -I"$(python -c 'import wabt_package as w; print(w.runtime_dir())')" -I"$(python -c 'import wabt_package as w; print(w.include_dir())')"
```

## Wheels

`py3-none-<platform>` wheels (the executables do not depend on the interpreter): Linux manylinux and musllinux
(x86_64, aarch64), Windows (x64, ARM64), macOS (arm64, x86_64). Anywhere else the sdist builds the tools from source and
needs a C++ compiler (`cmake` and `ninja` are fetched from PyPI).

The executables are linked statically against the C++ runtime and use WABT's own SHA-256 (no OpenSSL).

## Development

```sh
git clone --recurse-submodules https://github.com/ballistics-lab/wabt-package
cd wabt-package
git -C wabt submodule update --init --depth 1 third_party/picosha2 third_party/simde   # the nested submodules needed
uv sync          # builds WABT (a minute) and installs the package in editable mode
uv run pytest
```

To move to a new WABT release: check out its tag in `wabt/`, commit the submodule, and tag `v<release>.0`
(the publish workflow checks that the tag starts with the submodule's release).

## License

Apache-2.0, as WABT. See `LICENSE` and `NOTICE.md`.
