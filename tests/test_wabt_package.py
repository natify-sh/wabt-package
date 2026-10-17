"""The package as installed: every tool runs, WAT -> wasm -> WAT/C works, and the bundled runtime fits wasm2c."""

from __future__ import annotations

import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import pytest

import wabt_package as wabt

WAT = """
(module
  (func (export "add") (param i32 i32) (result i32)
    local.get 0
    local.get 1
    i32.add))
"""


@pytest.fixture
def add_wasm(tmp_path: Path) -> Path:
    wat = tmp_path / "add.wat"
    wat.write_text(WAT, encoding="utf-8")
    wasm = tmp_path / "add.wasm"
    wabt.run("wat2wasm", wat, "-o", wasm)
    return wasm


def test_the_version_is_a_wabt_release() -> None:
    parts = wabt.wabt_version().split(".")
    assert len(parts) == 3 and all(p.isdigit() for p in parts), wabt.wabt_version()


def test_the_distribution_version_starts_with_the_wabt_version() -> None:
    version = metadata.version("wabt-package")
    if "dev" in version:  # an untagged checkout: setuptools-scm has no tag to take the number from
        pytest.skip(f"{version} is a development version")
    assert version.startswith(wabt.wabt_version() + "."), (version, wabt.wabt_version())


@pytest.mark.parametrize("tool", wabt.TOOLS)
def test_every_tool_runs(tool: str) -> None:
    path = wabt.get_executable(tool)
    assert path.is_file() and path.parent == wabt.bin_dir()
    out = wabt.run(tool, "--version", capture_output=True, text=True).stdout.strip()
    assert out == wabt.wabt_version()


def test_an_unknown_tool_is_a_key_error() -> None:
    with pytest.raises(KeyError):
        wabt.get_executable("wasm-opt")


def test_wasm_roundtrips_through_text(add_wasm: Path) -> None:
    assert add_wasm.read_bytes().startswith(b"\0asm")
    wat = wabt.run("wasm2wat", add_wasm, capture_output=True, text=True).stdout
    assert '(export "add"' in wat and "i32.add" in wat
    wabt.run("wasm-validate", add_wasm)
    objdump = wabt.run("wasm-objdump", "-x", add_wasm, capture_output=True, text=True).stdout
    assert "add" in objdump


def test_wasm2c_writes_c_for_the_module(add_wasm: Path, tmp_path: Path) -> None:
    c_file = tmp_path / "add.c"
    wabt.run("wasm2c", add_wasm, "-o", c_file, "--module-name=add")
    assert "w2c_add_add" in c_file.read_text(encoding="utf-8")
    assert (tmp_path / "add.h").exists()


def test_the_runtime_is_there() -> None:
    names = {p.name for p in wabt.runtime_dir().iterdir()}
    assert {"wasm-rt.h", "wasm-rt-impl.c", "wasm-rt-impl.h", "wasm-rt-mem-impl.c"} <= names, names


@pytest.mark.skipif(sys.platform == "win32", reason="the compiler line below is for gcc/clang")
def test_the_c_of_wasm2c_compiles_against_the_bundled_runtime(add_wasm: Path, tmp_path: Path) -> None:
    """The translator and the runtime are of one version: the generated C and the runtime sources build together."""
    cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if cc is None:
        pytest.skip("no C compiler")
    c_file = tmp_path / "add.c"
    wabt.run("wasm2c", add_wasm, "-o", c_file, "--module-name=add")
    runtime = wabt.runtime_dir()
    sources = [c_file, runtime / "wasm-rt-impl.c", runtime / "wasm-rt-mem-impl.c"]
    for src in sources:
        subprocess.run(
            [cc, "-c", f"-I{runtime}", f"-I{tmp_path}", str(src), "-o", str(tmp_path / (src.stem + ".o"))], check=True
        )


def test_the_console_script_is_installed() -> None:
    found = shutil.which("wasm2c")
    if found is None:
        pytest.skip("the scripts directory of the environment is not on PATH")
    out = subprocess.run([found, "--version"], check=True, capture_output=True, text=True).stdout.strip()
    assert out == wabt.wabt_version()


def test_python_dash_m_runs_a_tool() -> None:
    out = subprocess.run(
        [sys.executable, "-m", "wabt_package", "wat2wasm", "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    assert out == wabt.wabt_version()


def test_the_simde_headers_come_with_the_commit_that_wabt_pins() -> None:
    header = wabt.include_dir() / "simde" / "wasm" / "simd128.h"
    assert header.is_file()
    assert (wabt.include_dir() / "simde" / "COPYING").is_file()
    commit = wabt.simde_commit()
    assert len(commit) == 40 and all(c in "0123456789abcdef" for c in commit), commit


def test_the_c_of_a_simd_module_compiles_with_the_bundled_headers(tmp_path: Path) -> None:
    cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if cc is None or sys.platform == "win32":
        pytest.skip("no C compiler of the cc kind")
    wat = tmp_path / "simd.wat"
    wat.write_text(
        '(module (func (export "f") (result i32)'
        " v128.const i32x4 1 2 3 4 v128.const i32x4 1 1 1 1 i32x4.add i32x4.extract_lane 3))",
        encoding="utf-8",
    )
    wasm = tmp_path / "simd.wasm"
    wabt.run("wat2wasm", wat, "-o", wasm)
    c_file = tmp_path / "simd.c"
    wabt.run("wasm2c", wasm, "-o", c_file)
    subprocess.run(
        [cc, "-c", str(c_file), f"-I{wabt.runtime_dir()}", f"-I{wabt.include_dir()}", "-o", str(tmp_path / "simd.o")],
        check=True,
        capture_output=True,
    )
