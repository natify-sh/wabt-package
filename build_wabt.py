"""Build WABT's command-line tools from the `wabt` submodule and stage them inside the package.

    src/wabt_package/bin/<tool>[.exe]       the executables (wabt_package.TOOLS)
    src/wabt_package/wasm2c/                wasm2c's runtime sources: wasm-rt.h, wasm-rt-impl.c, ... (of the same version)
    src/wabt_package/include/simde/         the headers of simde that the C of wasm2c includes for SIMD, of the commit
                                            that WABT pins as its submodule `third_party/simde`
    src/wabt_package/_simde_commit.txt      that commit
    src/wabt_package/_wabt_version.txt      the WABT version, from the submodule's tag

Runs from setup.py on every build (wheel, sdist -> wheel, editable `uv sync`), and by hand as
`uv run python build_wabt.py`. Plain Python so it works on Windows too.

Sources: the `wabt` git submodule, pinned to a release tag (shipped inside the sdist). Of WABT's own submodules
`third_party/picosha2` is needed to build (SHA-256 for `wasm2c`'s module hashing; with it the tools do not link against
OpenSSL, which is what makes the executables portable) and `third_party/simde` is carried along (headers only): the C that
`wasm2c` writes for SIMD includes it, WABT does not ship it, and taking it from WABT's own pin keeps it in step with the version. Compiler: the platform's own (gcc/clang/MSVC); `cmake` and `ninja` are
build requirements in pyproject.toml, so a plain `pip install` / `uv build` needs neither preinstalled.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WABT_DIR = Path(os.environ.get("WABT_DIR") or ROOT / "wabt")
OUT_DIR = ROOT / "src" / "wabt_package"
# One build tree per target: cibuildwheel builds several architectures one after the other on a runner (Windows x86 and
# x64, macOS arm64 and universal2), and a CMake tree cannot switch its generator platform or architectures.
_TARGET = "-".join(
    part
    for part in (sysconfig.get_platform(), *(os.environ.get("ARCHFLAGS", "").replace("-arch", " ").split()))
    if part
)
BUILD_DIR = ROOT / "build" / f"wabt-{_TARGET}"
# Written into the sdist (see setup.py), where the submodule's git metadata is not available.
VERSION_FILE = OUT_DIR / "_wabt_version.txt"
SIMDE_DIR = WABT_DIR / "third_party" / "simde"
SIMDE_COMMIT_FILE = OUT_DIR / "_simde_commit.txt"
SIMDE_HEADER = Path("simde") / "wasm" / "simd128.h"
STAMP_FILE = BUILD_DIR / "staged.stamp"

# Keep in sync with wabt_package.TOOLS and [project.scripts]. The set belongs to the pinned WABT release (1.0.42 has no
# wasm-decompile, 1.0.36 had it): after a bump the build fails on a tool that is gone, and a new one has to be added here.
TOOLS = (
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
EXE_SUFFIX = ".exe" if sys.platform == "win32" else ""
# What of wasm2c/ is the runtime: the headers and sources that the generated C is compiled together with.
RUNTIME_PATTERNS = ("wasm-rt*.h", "wasm-rt*.c", "wasm-rt*.inc")


def wabt_version() -> str:
    """`git describe` of the submodule, else the version recorded in the sdist, else "unknown"."""
    try:
        out = subprocess.run(
            ["git", "-C", str(WABT_DIR), "describe", "--tags", "--always"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if out:
            return out.removeprefix("v")
    except (OSError, subprocess.CalledProcessError):
        pass
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "unknown"


def simde_commit() -> str:
    """The commit of simde that WABT pins (read from WABT's tree, so it does not need the submodule checked out), else the
    one recorded in the sdist, else "unknown"."""
    try:
        out = subprocess.run(
            ["git", "-C", str(WABT_DIR), "ls-tree", "HEAD", "third_party/simde"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split()
        if len(out) >= 3 and out[0] == "160000" and len(out[2]) == 40:  # "160000 commit <sha>\t<path>"
            return out[2]
    except (OSError, subprocess.CalledProcessError):
        pass
    if SIMDE_COMMIT_FILE.exists():
        return SIMDE_COMMIT_FILE.read_text(encoding="utf-8").strip()
    return "unknown"


def _run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def _find(tool: str, module: str, attr: str) -> str | None:
    """`tool` on PATH, else the one inside the PyPI wheel `module` (the build requirement)."""
    found = shutil.which(tool)
    if found:
        return found
    try:
        mod = __import__(module)
    except ImportError:
        return None
    candidate = Path(getattr(mod, attr)) / (tool + EXE_SUFFIX)
    return str(candidate) if candidate.exists() else None


def _ensure_picosha2() -> None:
    header = WABT_DIR / "third_party" / "picosha2" / "picosha2.h"
    if header.exists():
        return
    print("+ git submodule update --init third_party/picosha2", flush=True)
    try:
        subprocess.run(
            ["git", "-C", str(WABT_DIR), "submodule", "update", "--init", "--depth", "1", "third_party/picosha2"],
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        pass
    if not header.exists():
        raise SystemExit(
            f"{header} is missing: run `git -C {WABT_DIR} submodule update --init third_party/picosha2` "
            "(the sdist carries it; a plain git checkout needs the nested submodule)"
        )


def _ensure_simde() -> None:
    header = SIMDE_DIR / SIMDE_HEADER
    if header.exists():
        return
    print("+ git submodule update --init third_party/simde", flush=True)
    try:
        subprocess.run(
            ["git", "-C", str(WABT_DIR), "submodule", "update", "--init", "--depth", "1", "third_party/simde"],
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        pass
    if not header.exists():
        raise SystemExit(
            f"{header} is missing: run `git -C {WABT_DIR} submodule update --init third_party/simde` "
            "(the sdist carries it; a plain git checkout needs the nested submodule)"
        )


def _has_static_libstdcxx() -> bool:
    """Whether the C++ compiler finds a static libstdc++ (the manylinux riscv64 image does not carry one)."""
    cxx = os.environ.get("CXX") or shutil.which("c++") or "c++"
    try:
        out = subprocess.run(
            [cxx, "-print-file-name=libstdc++.a"], check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return False
    return os.path.isabs(out) and os.path.exists(out)  # gcc prints the bare name when it finds nothing


def _cmake_args() -> list[str]:
    args = [
        f"-S{WABT_DIR}",
        f"-B{BUILD_DIR}",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DBUILD_TESTS=OFF",
        "-DBUILD_LIBWASM=OFF",
        "-DWITH_EXCEPTIONS=OFF",
        "-DWITH_WASI=OFF",
        "-DWABT_INSTALL_RULES=OFF",  # nothing is installed by cmake: the tools are copied from the build tree
        "-DUSE_INTERNAL_SHA256=ON",  # PicoSHA2, not OpenSSL's libcrypto: no shared library to carry along
    ]
    if sys.platform == "win32":
        # The Visual Studio generator; the target follows the interpreter that builds the wheel (cibuildwheel).
        arch = {"win-amd64": "x64", "win-arm64": "ARM64", "win32": "Win32"}.get(sysconfig.get_platform())
        if arch:
            args += ["-A", arch]
        # The static C runtime: no vcruntime DLL needed at the user's.
        args += ["-DCMAKE_POLICY_DEFAULT_CMP0091=NEW", "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded"]
    else:
        ninja = _find("ninja", "ninja", "BIN_DIR")
        if ninja:
            args += ["-GNinja", f"-DCMAKE_MAKE_PROGRAM={ninja}"]
        if sys.platform.startswith("linux"):
            # libstdc++ and libgcc inside the executables: they run on any glibc/musl that the wheel's tag allows.
            if not _has_static_libstdcxx():
                raise SystemExit(
                    "no static libstdc++ (libstdc++.a) found: the tools are linked statically against it, so that they run "
                    "on any glibc/musl the wheel's tag allows. Install it (libstdc++-static, or libstdc++-dev on Alpine)."
                )
            args += ["-DCMAKE_EXE_LINKER_FLAGS=-static-libstdc++ -static-libgcc -s"]
        elif sys.platform == "darwin":
            archs = [a for a in os.environ.get("ARCHFLAGS", "").split("-arch") if a.strip()]
            if archs:
                args.append("-DCMAKE_OSX_ARCHITECTURES=" + ";".join(a.strip() for a in archs))
            if os.environ.get("MACOSX_DEPLOYMENT_TARGET"):
                args.append("-DCMAKE_OSX_DEPLOYMENT_TARGET=" + os.environ["MACOSX_DEPLOYMENT_TARGET"])
    return args


def _locate(tool: str) -> Path:
    for candidate in (BUILD_DIR / (tool + EXE_SUFFIX), BUILD_DIR / "Release" / (tool + EXE_SUFFIX)):
        if candidate.exists():
            return candidate
    raise SystemExit(f"{tool} was not built: not found under {BUILD_DIR}")


def _stamp(version: str) -> str:
    # What the staged files depend on: the WABT version, this script, the platform and the compiler flags in play.
    parts = [
        version,
        sysconfig.get_platform(),
        os.environ.get("ARCHFLAGS", ""),
        os.environ.get("MACOSX_DEPLOYMENT_TARGET", ""),
    ]
    parts.append(simde_commit())
    parts.append(str(hash(Path(__file__).read_bytes())))
    return "\n".join(parts)


def _staged(stamp: str) -> bool:
    if not (STAMP_FILE.exists() and STAMP_FILE.read_text(encoding="utf-8") == stamp):
        return False
    bins = [OUT_DIR / "bin" / (t + EXE_SUFFIX) for t in TOOLS]
    return (
        all(p.exists() for p in bins)
        and (OUT_DIR / "wasm2c" / "wasm-rt.h").exists()
        and (OUT_DIR / "include" / SIMDE_HEADER).exists()
    )


def build() -> None:
    if not WABT_DIR.joinpath("CMakeLists.txt").exists():
        raise SystemExit(f"{WABT_DIR} has no CMakeLists.txt: run `git submodule update --init wabt`")
    version = wabt_version()
    stamp = _stamp(version)
    if _staged(stamp):
        print(f"WABT {version} is already staged in {OUT_DIR}")
        return
    cmake = _find("cmake", "cmake", "CMAKE_BIN_DIR")
    if not cmake:
        raise SystemExit("cmake was not found: `pip install cmake` (it is a build requirement in pyproject.toml)")
    _ensure_picosha2()
    _ensure_simde()

    _run([cmake, *_cmake_args()])
    _run([cmake, "--build", str(BUILD_DIR), "--config", "Release", "--parallel", "--target", *TOOLS])

    bin_dir = OUT_DIR / "bin"
    runtime_dir = OUT_DIR / "wasm2c"
    for stale in (bin_dir, runtime_dir):
        shutil.rmtree(stale, ignore_errors=True)
        stale.mkdir(parents=True)
    for tool in TOOLS:
        shutil.copy2(_locate(tool), bin_dir / (tool + EXE_SUFFIX))
    for pattern in RUNTIME_PATTERNS:
        for src in sorted((WABT_DIR / "wasm2c").glob(pattern)):
            shutil.copy2(src, runtime_dir / src.name)
    include_dir = OUT_DIR / "include"
    shutil.rmtree(include_dir, ignore_errors=True)
    shutil.copytree(
        SIMDE_DIR / "simde",
        include_dir / "simde",
        ignore=lambda folder, names: [n for n in names if not (Path(folder) / n).is_dir() and not n.endswith(".h")],
    )
    shutil.copy2(SIMDE_DIR / "COPYING", include_dir / "simde" / "COPYING")
    VERSION_FILE.write_text(version + "\n", encoding="utf-8")
    SIMDE_COMMIT_FILE.write_text(simde_commit() + "\n", encoding="utf-8")
    STAMP_FILE.write_text(stamp, encoding="utf-8")
    print(f"staged WABT {version}: {len(TOOLS)} tools + wasm2c runtime + simde {simde_commit()[:12]} in {OUT_DIR}")


if __name__ == "__main__":
    build()
