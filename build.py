# Copyright © 2018-2026 Johan Cockx, Matic Kukovec & Kristof Mulier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
from typing import *
import sys
import os
import shutil
import argparse
import platform
import subprocess
import traceback
import hashlib
import pathlib
import fnmatch


def build_embeetle(source_directory: Optional[str], build_directory: Optional[str]):
    print("================================================================================")
    print("|                                BUILD EMBEETLE                                |")
    print("================================================================================")
    print("")
    
    # source_directory
    if source_directory:
        source_directory = str(os.path.realpath(source_directory)).replace("\\", "/")
        print(f"Source directory: '{source_directory}'")
    else:
        source_directory = str(
            os.path.realpath(
                os.path.dirname(os.path.realpath(__file__))
            )
        ).replace("\\", "/")
        print(f"'--repo' parameter not given, default to:")
        print(f"Source directory: '{source_directory}'")

    # build_directory
    if build_directory:
        build_directory = str(os.path.realpath(build_directory)).replace("\\", "/")
        print(f"Build directory:  '{build_directory}'")
    else:
        build_directory = os.path.join(
            os.path.dirname(source_directory),
            "bld/embeetle",
        ).replace("\\", "/")
        print(f"'--output' parameter not given, default to:")
        print(f"Build directory:  '{build_directory}'")

    # & STEP 1: CLEAN
    print("\nSTEP 1: CLEAN")
    print("=============")
    if not os.path.exists(build_directory):
        print(f"Build directory '{build_directory}' does not exist yet.")
        print(f"Create it ...")
        os.makedirs(build_directory)
    else:
        print(f"Clean build directory '{build_directory}' ...")
        shutil.rmtree(build_directory)
        os.makedirs(build_directory)

    # & STEP 2: FREEZE
    print("\nSTEP 2: FREEZE")
    print("==============")
    cmd = [
        "python",
        "freeze_embeetle.py",
        f'--output="{build_directory}"',
    ]
    if platform.system().lower() == "windows":
        cmd.append("--no-console")
    print(f"\n{cmd}\n")
    try:
        p = subprocess.Popen(
            cmd,
            cwd=f"{source_directory}/beetle_core/to_exe",
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        p.communicate()
    except:
        print(
            f"ERROR: Freezing Embeetle failed.\n" f"{traceback.format_exc()}\n"
        )
        return
    embeetle_exepath = os.path.join(
        build_directory,
        "beetle_core/beetle_core",
    ).replace("\\", "/")
    # For Windows, just add '.exe' at the back. For Linux, check if '.exe' might
    # be added at the back accidentally, then rename the executable!
    if platform.system().lower() == "windows":
        embeetle_exepath = f"{embeetle_exepath}.exe"
    else:
        if os.path.isfile(f"{embeetle_exepath}.exe"):
            os.rename(f"{embeetle_exepath}.exe", embeetle_exepath)
    # Make sure the executable exists
    if not os.path.isfile(embeetle_exepath):
        print(
            f"ERROR: Freezing updater tool failed. Executable not found.\n"
            f"{traceback.format_exc()}\n"
        )
        return
    # The freeze script creates a folder called 'copied_embeetle' in the build
    # directory. Delete that folder.
    print(f"INFO: Delete folder '{build_directory}/copied_embeetle'\n")
    shutil.rmtree(f"{build_directory}/copied_embeetle")

    # & STEP 3: COPY RESOURCES
    print("\nSTEP 3: COPY RESOURCES")
    print("======================")
    resources_directory = os.path.join(
        source_directory,
        "beetle_core/resources",
    ).replace("\\", "/")
    print(f"Copy '{resources_directory}'")
    print(f"to   '{build_directory}/beetle_core/resources'")
    mirror_dir(
        src=resources_directory,
        dst=f"{build_directory}/beetle_core/resources",
    )

    # & STEP 4: COPY SYS FOLDER
    # skip
    print("\nSTEP 4: COPY SYS FOLDER")
    print("=======================")
    sys_directory = os.path.join(
        source_directory,
        "sys",
    ).replace("\\", "/")
    print(f"Copy '{sys_directory}'")
    print(f"to   '{build_directory}/sys'")
    mirror_dir(
        src=sys_directory,
        dst=f"{build_directory}/sys",
        exclude=(".git/**", ".gitignore", ".gitattributes", "__pycache__/**"),
    )

    # & STEP 5: COPY LICENSES
    print("\nSTEP 5: COPY LICENSES")
    print("=====================")
    licenses_directory = os.path.join(
        source_directory,
        "licenses",
    ).replace("\\", "/")
    print(f"Copy '{licenses_directory}'")
    print(f"to   '{build_directory}/licenses'")
    mirror_dir(
        src=licenses_directory,
        dst=f"{build_directory}/licenses",
    )

    # & STEP 6: COPY SPLASH EXE
    print("\nSTEP 6: COPY SPLASH EXE")
    print("=======================")
    if platform.system().lower() == "windows":
        src_beetle_splash_exepath = os.path.join(
            source_directory,
            f"beetle_splash/windows/build/embeetle.exe"
        ).replace("\\", "/")
        dst_beetle_splash_exepath = os.path.join(
            build_directory,
            f"embeetle.exe"
        ).replace("\\", "/")
    else:
        src_beetle_splash_exepath = os.path.join(
            source_directory,
            f"beetle_splash/linux/build/embeetle"
        ).replace("\\", "/")
        dst_beetle_splash_exepath = os.path.join(
            build_directory,
            f"embeetle"
        ).replace("\\", "/")
    print(f"Copy '{src_beetle_splash_exepath}'")
    print(f"to   '{dst_beetle_splash_exepath}'")
    shutil.copy2(src_beetle_splash_exepath, dst_beetle_splash_exepath)

    # & FINISH BUILD
    print("\nFINISH BUILD")
    print("============")
    print("Embeetle built at:")
    print(f"'{build_directory}'")
    return


def mirror_dir(
    src: Union[str, pathlib.Path],
    dst: Union[str, pathlib.Path],
    delete: bool = False,
    checksum: bool = False,
    exclude: Iterable[str] = (".git/**", "__pycache__/**"),
    dry_run: bool = False,
) -> None:
    """
    One-way mirror: makes dst look like src.

    - delete=True    removes files/dirs present in dst but not src.
    - checksum=True  uses sha256 when size/mtime differ (slower but safer).
    - exclude        uses fnmatch patterns on POSIX-style relative paths.

    Example:
    mirror_dir(
        src = "C:/data/source",
        dst = "D:/backup/dest",
        delete = True,
        checksum = False,
    )
    """
    def _excluded(_rel_posix: str, patterns: Iterable[str]) -> bool:
        _pat: str
        _matched: bool = any(fnmatch.fnmatch(_rel_posix, _pat) for _pat in patterns)
        return _matched

    def _sha256(_p: pathlib.Path) -> str:
        h: hashlib._Hash = hashlib.sha256()
        f: IO[bytes]
        chunk: bytes
        with _p.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        digest: str = h.hexdigest()
        return digest

    src_path: pathlib.Path = pathlib.Path(src).resolve()
    dst_path: pathlib.Path = pathlib.Path(dst).resolve()

    if not src_path.is_dir():
        raise ValueError(f"src is not a directory: '{src_path}'")

    # 1) Copy/update from src -> dst
    s: pathlib.Path
    for s in src_path.rglob("*"):
        rel: pathlib.Path = s.relative_to(src_path)
        rel_posix: str = rel.as_posix()

        if _excluded(rel_posix, exclude):
            continue

        d: pathlib.Path = dst_path / rel

        if s.is_dir():
            if not dry_run:
                d.mkdir(parents=True, exist_ok=True)
            continue

        if not s.is_file():
            continue  # skip symlinks/devices by default

        do_copy: bool = False
        if not d.exists():
            do_copy = True
        else:
            ss: os.stat_result = s.stat()
            ds: os.stat_result = d.stat()
            if ss.st_size != ds.st_size or int(ss.st_mtime) != int(ds.st_mtime):
                do_copy = True
                if checksum and d.is_file():
                    do_copy = _sha256(s) != _sha256(d)

        if do_copy:
            if dry_run:
                print(f"COPY {s} -> {d}")
            else:
                d.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(s, d)  # preserves mtime; best-effort metadata
                                    # cross-platform

    # 2) Delete extras from dst if requested
    if delete:
        d: pathlib.Path
        for d in sorted(dst_path.rglob("*"), reverse=True):
            rel: pathlib.Path = d.relative_to(dst_path)
            rel_posix: str = rel.as_posix()

            if _excluded(rel_posix, exclude):
                continue

            s: pathlib.Path = src_path / rel
            if not s.exists():
                if dry_run:
                    print(f"DELETE {d}")
                else:
                    if d.is_dir():
                        # Remove only if empty; if not empty (e.g., contains
                        # excluded items), leave it.
                        try:
                            d.rmdir()
                        except OSError:
                            pass
                    else:
                        d.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Embeetle from source.")
    parser.add_argument(
        "--repo", 
        required=False, 
        help="Path to the Embeetle source directory (the repository)"
    )
    parser.add_argument(
        "--output", 
        required=False, 
        help="Path where the Embeetle build will be created"
    )
    
    args = parser.parse_args()

    build_embeetle(source_directory=args.repo, build_directory=args.output)
    sys.exit(0)