"""WABT, the WebAssembly Binary Toolkit, as a package: prebuilt executables and the `wasm2c` runtime.

    import wabt_package as wabt

    wabt.run("wat2wasm", "in.wat", "-o", "out.wasm")
    wabt.get_executable("wasm2c")      # pathlib.Path of the bundled wasm2c
    wabt.runtime_dir()                 # wasm-rt.h, wasm-rt-impl.c, ... to compile the C that wasm2c writes
    wabt.include_dir()                 # -I for it: <simde/wasm/simd128.h>, which the C of a SIMD module includes
    wabt.wabt_version()                # "1.0.42"

The executables are also installed as console scripts (`wasm2c`, `wat2wasm`, ...), and `python -m wabt_package
<tool> ...` runs one. An unofficial redistribution of https://github.com/WebAssembly/wabt (Apache-2.0).
"""

from __future__ import annotations

import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

__all__ = ["TOOLS", "bin_dir", "get_executable", "include_dir", "run", "runtime_dir", "simde_commit", "wabt_version"]

# The command-line tools of the pinned WABT release that the wheel carries (see build_wabt.py).
TOOLS: tuple[str, ...] = (
    "spectest-interp",
    "wasm-interp",
    "wasm-objdump",
    "wasm-stats",
    "wasm-strip",
    "wasm-validate",
    "wasm2c",
    "wasm2wat",
    "wast2json",
    "wat-desugar",
    "wat2wasm",
)

_PACKAGE_DIR = Path(__file__).resolve().parent
_EXE_SUFFIX = ".exe" if sys.platform == "win32" else ""


@lru_cache(maxsize=1)
def wabt_version() -> str:
    """The version of WABT these tools were built from (the first three numbers of this package's version)."""
    return (_PACKAGE_DIR / "_wabt_version.txt").read_text(encoding="utf-8").strip()


def bin_dir() -> Path:
    """The directory with the executables."""
    return _PACKAGE_DIR / "bin"


def runtime_dir() -> Path:
    """The directory with wasm2c's runtime sources (`wasm-rt.h`, `wasm-rt-impl.c`, `wasm-rt-mem-impl.c`, ...).

    They are of the very version of the bundled `wasm2c`: compile them together with the C it writes."""
    return _PACKAGE_DIR / "wasm2c"


def include_dir() -> Path:
    """The directory to pass with `-I` when compiling the C that `wasm2c` writes for a module with SIMD instructions.

    It holds `simde/` (the headers of https://github.com/simd-everywhere/simde, MIT): the commit that WABT pins as its
    submodule, so it is the one this version of `wasm2c` was made with (see `simde_commit()`)."""
    return _PACKAGE_DIR / "include"


@lru_cache(maxsize=1)
def simde_commit() -> str:
    """The commit of simde whose headers are in `include_dir()`."""
    return (_PACKAGE_DIR / "_simde_commit.txt").read_text(encoding="utf-8").strip()


def get_executable(name: str) -> Path:
    """The path of the bundled tool `name` (one of `TOOLS`); `KeyError` for any other name."""
    if name not in TOOLS:
        raise KeyError(f"{name!r} is not a tool of this package; one of: {', '.join(TOOLS)}")
    path = bin_dir() / (name + _EXE_SUFFIX)
    if not path.is_file():
        raise FileNotFoundError(f"{path} is missing: the package was built without it")
    if sys.platform != "win32" and not os.access(path, os.X_OK):  # a wheel that lost the mode bits
        try:
            path.chmod(path.stat().st_mode | 0o111)
        except OSError:
            pass  # a read-only install: let the caller's own run fail with a clear message
    return path


def run(name: str, *args: str | os.PathLike[str], **kwargs: Any) -> subprocess.CompletedProcess[Any]:
    """Run tool `name` with `args`; `kwargs` go to `subprocess.run` (`check=True` unless given)."""
    check = kwargs.pop("check", True)
    cmd = [str(get_executable(name)), *[os.fspath(a) for a in args]]
    return cast("subprocess.CompletedProcess[Any]", subprocess.run(cmd, check=check, **kwargs))
