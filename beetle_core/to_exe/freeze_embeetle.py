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

# freeze_embeetle.py

import os
import sys
import shutil
import inspect
import argparse
import time
import platform
import glob

sys.path.append(
    os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())), "..")
)

VERSION = "0.0.14"


# ----------------------------
# Copy project sources to a staging folder
# ----------------------------
DIRECTORY_EXCLUSION_LIST = [
    ".git",
    "resources",
    "copied_embeetle",
    "frozen_embeetle",
    "source_analyzer/base",
    "source_analyzer/test",
    "to_exe",
]
FILE_EXCLUSION_LIST = [
    "gen_all.py",
    "gen_sample_proj.py",
    "test.py",
    "styletest.py",
    "unix_lines.py",
]

def unixify_path(_path: str) -> str:
    """"""
    _result = os.path.realpath(_path).replace("\\", "/")
    if platform.system().lower() == "windows":
        if _result.startswith("/"):
            start = 0
            for i in range(len(_result)):
                if _result[i] == "/":
                    continue
                elif _result[i] == "?":
                    continue
                else:
                    start = i
                    break
            _result = _result[start:]
    return _result


def _exclude_directory(abs_dir: str, read_directory: str) -> bool:
    if "__pycache__" in abs_dir:
        return True
    for d in DIRECTORY_EXCLUSION_LIST:
        test_abs_path = unixify_path(
            os.path.join(read_directory, d)
        )
        if abs_dir.startswith(test_abs_path):
            return True
    return False


def _exclude_file(filename: str) -> bool:
    return os.path.basename(filename) in FILE_EXCLUSION_LIST


def copy_embeetle(
    read_directory: str,
    copy_directory: str,
    clean: bool,
    info_only: bool,
) -> int:
    """
    Copy all *.py files (except excluded) from read_directory to
    copy_directory. Return the number of files that would be / were copied.
    """
    if not info_only:
        if clean and os.path.isdir(copy_directory):
            shutil.rmtree(copy_directory)
            time.sleep(0.2)
        os.makedirs(copy_directory, exist_ok=True)
        time.sleep(0.1)

    file_counter = 0
    print(
        f"Copy Embeetle code from '{read_directory}' to '{copy_directory}' ..."
    )

    for root, dirs, files in os.walk(read_directory):
        current_directory = unixify_path(root)
        if _exclude_directory(current_directory, read_directory):
            continue
        for f in files:
            if _exclude_file(f):
                continue
            if not f.endswith(".py"):
                continue
            src_file = unixify_path(os.path.join(current_directory, f))
            rel = src_file.replace(read_directory, "").lstrip("/")
            dst_file = unixify_path(os.path.join(copy_directory, rel))
            file_counter += 1
            if info_only:
                continue
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)
        continue

    if info_only:
        print(f"Number of files to be copied: {file_counter}")

    return file_counter


# ----------------------------
# cx_Freeze wrapper
# ----------------------------
def get_local_modules(path: str) -> list[str]:
    local_modules: list[str] = []
    exclude_dirs = ["to_exe", "resources", "source_analyzer/test"]
    excluded_modules = {
        "embeetle",
        "figtest",
        "gen_all",
        "gen_sample_proj",
        "styletest",
        "threading_test",
    }

    for root, dirs, files in os.walk(path):
        base_path = unixify_path(root).replace(
            unixify_path(path), ""
        )
        if base_path.startswith("/"):
            base_path = base_path[1:]
        if any(x in base_path for x in exclude_dirs):
            continue

        for f in files:
            if (f.endswith(".py") or f.endswith(".pyd") or f.endswith(".so")) and f != "__init__.py":
                raw_module = (
                    f.replace(".py", "").replace(".pyd", "").replace(".so", "")
                ).split(".")[0]
                new_module = f"{base_path}/{raw_module}".lstrip("/").replace("/", ".")
                if new_module in excluded_modules:
                    continue
                local_modules.append(new_module)

    return local_modules


def freeze_embeetle(
    read_directory: str,
    copy_directory: str,
    freeze_directory: str,
    custom_python_path: str | None,
    hide_console: bool,
    local_modules: list[str],
) -> int:
    """
    Freezes the Embeetle IDE code into a standalone executable using cx_Freeze.

    Example:
        freeze_embeetle(
            read_directory   = 'C:/msys64/home/krist/embeetle/beetle_core',
            copy_directory   = 'C:/msys64/home/krist/bld/embeetle/copied_embeetle',
            freeze_directory = 'C:/msys64/home/krist/bld/embeetle/beetle_core',
            custom_python_path = None,
            hide_console       = True,
            local_modules      = ['beetlifyer', 'constants', 'data', ... ],
        )
    """
    print(
        f"\nfreeze_embeetle(\n"
        f"    read_directory    = '{read_directory}',\n"
        f"    copy_directory    = '{copy_directory}',\n"
        f"    freeze_directory  = '{freeze_directory}',\n"
        f"    custom_python_path = '{custom_python_path}',\n"
        f"    hide_console      = {hide_console},\n"
        f"    local_modules     = [{local_modules[0]}, {local_modules[1]}, ...],\n"
        f")\n"
    )
    import cx_Freeze

    builtin_modules = [
        "PyQt6",
        "PyQt6.Qsci",
        "PyQt6.QtTest",
        "ctypes",
        "ctypes.wintypes",
        "elftools",
        "elftools.common.exceptions",
        "elftools.common.utils",
        "elftools.elf.elffile",
        "elftools.elf.dynamic",
        "elftools.elf.enums",
        "elftools.elf.segments",
        "elftools.elf.sections",
        "elftools.elf.gnuversions",
        "elftools.elf.relocation",
        "elftools.elf.descriptions",
        "elftools.elf.constants",
        "elftools.dwarf.dwarfinfo",
        "elftools.dwarf.descriptions",
        "elftools.dwarf.constants",
        "elftools.dwarf.locationlists",
        "elftools.dwarf.ranges",
        "elftools.dwarf.callframe",
        "elftools.ehabi.ehabiinfo",
        "elftools.dwarf.enums",
        "regex",
        "timeit",
        "queue",
        "multiprocessing",
        "threading",
        "json",
        "sqlite3",
        "urllib.parse",
        "urllib.request",
        "urllib.error",
        "http.client",
        "tempfile",
        "contextlib",
        "webbrowser",
        "statistics",
        "pathlib",
        "serial",
        "serial.tools",
        "serial.tools.list_ports",
        "textwrap",
        "packaging",
        "packaging.version",
        "xmltodict",
        "watchdog",
        "watchdog.events",
        "watchdog.observers",
        "colorama",
        "feedparser",
        "sgmllib",
        "pyte",
        "chardet",
        "certifi",
        "pieces_os_client",
        "pygments",
        "markdown",
    ]

    if platform.system().lower() == "windows":
        builtin_modules.extend([
            "win32api",
            "win32con",
            "win32file",
            "winpty",
            "winshell",
            "winreg",
        ])
    else:
        builtin_modules.extend([
            "ptyprocess",
            "pwd",
        ])

    if sys.version_info < (3, 13):
        builtin_modules.append("telnetlib")
    else:
        builtin_modules.append("telnetlib3")

    # Dynamically find any mypyc hashed modules (like the one chardet uses) 
    # in the Python environment so cx_Freeze doesn't miss them.
    mypyc_includes = []
    for env_path in sys.path:
        if os.path.isdir(env_path):
            for file_path in glob.glob(os.path.join(env_path, '*__mypyc*.*')):
                mod_name = os.path.basename(file_path).split('.')[0]
                if mod_name not in mypyc_includes:
                    mypyc_includes.append(mod_name)

    # de-dupe, keep order
    modules = list(
        dict.fromkeys(local_modules + builtin_modules + mypyc_includes)
    )

    print("All local modules:")
    for m in local_modules:
        print(" -", m)

    # Clean up target dir
    if os.path.isdir(freeze_directory):
        shutil.rmtree(freeze_directory)
        time.sleep(0.2)
    os.makedirs(freeze_directory, exist_ok=True)

    base = None
    if platform.system().lower() == "windows" and hide_console:
        base = "gui"

    # Ensure we freeze the copied sources, not the originals
    os.chdir(copy_directory)

    executables = [
        cx_Freeze.Executable(
            "embeetle.py",
            init_script=None,
            base=base,
            icon=unixify_path(
                os.path.join(
                    read_directory,
                    "to_exe/embeetle_logo.ico",
                ),
            ),
            target_name="beetle_core.exe",
        )
    ]

    # Build a conservative search path that avoids pointing at the original
    # source tree
    search_path: list[str] = []
    temp = list(sys.path)
    temp.append(copy_directory)

    read_dir_norm = unixify_path(read_directory)
    for p in temp:
        p = p.replace("\\", "/")
        if p.startswith(read_dir_norm):
            # Skip original beetle_core sources
            continue
        search_path.append(p)

    # Source analyzer adjustments
    esa_path = os.path.realpath(
        os.path.normpath(
            os.path.join(
                read_directory,
                "..",
                "sys/esa/"
            )
        )
    ).replace("\\", "/")
    print(f"esa_path = '{esa_path}'")
    if not os.path.exists(esa_path):
        print(
            f"\n"
            f"ERROR: Cannot freeze Embeetle because the following path is\n"
            f"       missing: '{esa_path}'\n"
            f"       Probably the 'sys' folder is missing entirely. Just launch\n"
            f"       Embeetle from sources and it will automatically pull the\n"
            f"       'sys' folder from GitHub. Then try to freeze again."
            f"\n"
        )
        sys.exit(1)
    if esa_path not in sys.path:
        sys.path.append(esa_path)
    if esa_path not in search_path:
        search_path.append(esa_path)

    excluded_modules = ["tkinter"]

    print(
        f"\n\nfreezer = cx_Freeze.Freezer(\n"
        f"    {executables},\n"
        f"    includes      = [{modules[0]}, {modules[1]}, ...],\n"
        f"    excludes      = {excluded_modules},\n"
        f"    replace_paths = [],\n"
        f"    compress      = True,\n"
        f"    optimize      = 2,\n"
        f"    path          = '{search_path}',\n"
        f"    target_dir    = '{freeze_directory}',\n"
        f"    include_files = [],\n"
        f"    zip_includes  = [],\n"
        f"    silent        = False,\n"
        f"    include_msvcr = True,\n"
        f")\n"
        f"freezer.freeze()\n"
    )

    freezer = cx_Freeze.Freezer(
        executables,
        includes=modules,
        excludes=excluded_modules,
        replace_paths=[],
        compress=True,
        optimize=2,
        path=search_path,
        target_dir=freeze_directory,
        include_files=[],
        zip_includes=[],
        silent=False,
        include_msvcr=True,
    )
    freezer.freeze()
    return 0


def parse_arguments():
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Embeetle freeze script: {VERSION}",
    )

    arg_parser.add_argument(
        "--clean",
        action="store_true",
        default=False,
        dest="clean",
        help="Clean all freeze directories/files",
    )

    arg_parser.add_argument(
        "--python_path",
        action="store",
        default=None,
        dest="python_path",
        help="Set a custom Python 3 path (currently unused; kept for compatibility)",
    )

    arg_parser.add_argument(
        "--output",
        required=True,
        action="store",
        dest="output",
        help="Set a custom output location instead of the beetle_core folder",
    )

    arg_parser.add_argument(
        "--no-console",
        action="store_true",
        default=False,
        dest="hide_console",
        help="Hide the background console window on windows",
    )

    arg_parser.add_argument(
        "--info-only",
        action="store_true",
        default=False,
        dest="info_only",
        help="Display only information about the freeze routine without executing it",
    )

    return arg_parser.parse_args()


if __name__ == "__main__":
    freeze_script_directory = unixify_path(
        os.path.dirname(inspect.getfile(inspect.currentframe()))
    )
    read_directory = unixify_path(
        os.path.join(
            freeze_script_directory,
            "..",
        )
    )

    options = parse_arguments()
    build_directory = unixify_path(
        options.output.replace('"', "").replace("'", "")
    )
    print(f"--output = {build_directory}")

    copy_directory = unixify_path(
        os.path.join(
            build_directory,
            "copied_embeetle",
        )
    )
    freeze_directory = unixify_path(
        os.path.join(
            build_directory,
            "beetle_core",
        )
    )

    if options.info_only:
        copy_embeetle(
            read_directory=read_directory,
            copy_directory=copy_directory,
            clean=options.clean,
            info_only=True,
        )
        sys.exit(0)

    # Ensure output dir exists
    os.makedirs(build_directory, exist_ok=True)
    time.sleep(0.1)

    # Copy sources
    copy_embeetle(
        read_directory=read_directory,
        copy_directory=copy_directory,
        clean=options.clean,
        info_only=False,
    )

    # Freeze
    local_modules = get_local_modules(copy_directory)
    result = freeze_embeetle(
        read_directory=read_directory,
        copy_directory=copy_directory,
        freeze_directory=freeze_directory,
        custom_python_path=options.python_path,
        hide_console=options.hide_console,
        local_modules=local_modules,
    )
    if result != 0:
        raise Exception("Freezing error!")

    # Copy version file (build.py currently does not do this)
    version_file_path = unixify_path(
        os.path.join(read_directory, "version.txt")
    )
    if os.path.isfile(version_file_path):
        print("Started copying version file into the freeze directory ...")
        shutil.copy2(
            version_file_path,
            unixify_path(os.path.join(freeze_directory, "version.txt")),
        )
        print("Version file copied successfully.")

    print("\nFinished successfully.")
else:
    raise Exception("The freeze script cannot be imported!")