"""Build hooks: build WABT's tools as part of every build (see build_wabt.py).

All metadata lives in pyproject.toml; this file only wires build_wabt.build() into setuptools:

- build_py builds the tools into src/wabt_package/ before packaging, so wheels, sdist->wheel builds and
  editable installs (`uv sync`) all get them without a separate step; setuptools copies package data without the
  executable bit, so it is put back on the built copies;
- sdist records the WABT version and the commit of simde next to the sources, because the unpacked sdist has no git metadata to
  `git describe`;
- the distribution claims to have extension modules, so that the files go to platlib (not purelib): auditwheel
  refuses to repair a wheel with executables in purelib;
- bdist_wheel tags the wheel py3-none-<platform>: it holds executables, not a Python extension, so it does not
  depend on the interpreter or its ABI, and one build per platform serves every Python.
"""

import os
import stat
import sys

from setuptools import Distribution, setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist

try:
    from setuptools.command.bdist_wheel import bdist_wheel
except ImportError:  # setuptools < 70.1
    from wheel.bdist_wheel import bdist_wheel  # type: ignore[no-redef]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_wabt


class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return True


class BuildPyWithWabt(build_py):
    def run(self):
        build_wabt.build()
        super().run()
        bin_dir = os.path.join(self.build_lib, "wabt_package", "bin")
        if os.path.isdir(bin_dir):
            for name in os.listdir(bin_dir):
                path = os.path.join(bin_dir, name)
                os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class SdistWithWabtVersion(sdist):
    def make_release_tree(self, base_dir, files):
        super().make_release_tree(base_dir, files)
        path = os.path.join(base_dir, os.path.relpath(build_wabt.VERSION_FILE, build_wabt.ROOT))
        if os.path.exists(path):  # a hard link to the source tree's copy; don't write through it
            os.remove(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(build_wabt.wabt_version() + "\n")
        simde_path = os.path.join(base_dir, os.path.relpath(build_wabt.SIMDE_COMMIT_FILE, build_wabt.ROOT))
        if os.path.exists(simde_path):
            os.remove(simde_path)
        with open(simde_path, "w") as f:
            f.write(build_wabt.simde_commit() + "\n")


class Py3NonePlatformWheel(bdist_wheel):
    def finalize_options(self):
        super().finalize_options()
        self.root_is_pure = False  # platform-specific files: the wheel goes to platlib and carries a platform tag

    def get_tag(self):
        _, _, plat = super().get_tag()
        return "py3", "none", plat


setup(
    distclass=BinaryDistribution,
    cmdclass={
        "build_py": BuildPyWithWabt,
        "sdist": SdistWithWabtVersion,
        "bdist_wheel": Py3NonePlatformWheel,
    },
)
