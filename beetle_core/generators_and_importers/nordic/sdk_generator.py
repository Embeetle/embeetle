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

# WARNING
# THIS FILE GETS OFTEN R-SYNCED FROM <BEETLE_CORE> TO <BEETLE_PROJECT_GENERATOR>. ONLY EDIT THIS
# FILE FROM WITHIN THE <BEETLE_CORE> FOLDER. OTHERWISE, YOUR CHANGES GET LOST.
from __future__ import annotations
from typing import *
import sys, os, argparse, subprocess, re

try:
    import data, purefunctions, functions, filefunctions
except:
    my_dir = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
    parent_dir = os.path.dirname(my_dir).replace("\\", "/")
    grandparent_dir = os.path.dirname(parent_dir).replace("\\", "/")
    sys.path.append(grandparent_dir)
    import data, purefunctions, functions, filefunctions
q = "'"
dq = '"'


def __help() -> None:
    """Help message in console."""
    header = (
        "\n"
        + "=" * 80
        + "\n"
        + "|"
        + " " * 26
        + "NORDIC SDK GENERATOR TOOL"
        + " " * 27
        + "|"
        + "\n"
        + "=" * 80
    )
    functions.generator_printfunc(header, color="yellow")
    functions.generator_printfunc(f"Only for internal use!\n")
    functions.generator_printfunc(
        f"SUMMARY\n" f"=======",
        color="yellow",
    )
    functions.generator_printfunc(
        f"This tool generates a Nordic project based on a {q}hardware.json5{q} and {q}readme.txt{q}\n"
        f"file. The sample project it starts from typically looks like this:\n"
        f"\n"
        f"  pca10056-freertos\n"
        f"     ├ hardware.json5\n"
        f"     └ readme.txt\n"
        f"\n"
        f"The result is a Nordic project (not an Embeetle project!) in the destination\n"
        f"folder, usually a temporary directory. The next step is to import that, which\n"
        f"can be done with the toplevel importer tool.\n"
    )
    functions.generator_printfunc(
        f"ARGUMENTS\n" f"=========",
        color="yellow",
    )
    functions.generator_printfunc("--src".ljust(11), color="yellow", end="")
    functions.generator_printfunc(
        f"Source folder, eg. {dq}C:/sample_proj_resources/nordic/projects/pca/pca10056-freertos{dq}."
    )
    functions.generator_printfunc("--dst".ljust(11), color="yellow", end="")
    functions.generator_printfunc(
        f"Destination folder, eg. {dq}C:/Users/krist/AppData/Local/Temp/tmpjygwckqi{dq}."
    )
    functions.generator_printfunc("--make".ljust(11), color="yellow", end="")
    functions.generator_printfunc(
        f"Path to Gnu Make, eg. {dq}C:/Users/krist/.embeetle/beetle_tools/gnu_make_4.2.1_64b/make.exe{dq}."
    )
    functions.generator_printfunc(
        "--freertos".ljust(11), color="yellow", end=""
    )
    functions.generator_printfunc(
        f"Add this flag if the project has freertos.\n"
    )
    functions.generator_printfunc(
        f"NOTES\n" f"=====",
        color="yellow",
    )
    functions.generator_printfunc(
        f"I{q}ve developed this script as a standalone tool, such that it can be invoked\n"
        f"in a newly launched terminal, to keep the main terminal clean.\n"
    )
    return


def __extract_nordic_project_from_sdk(
    src_abspath: str,
    dst_abspath: str,
    has_freertos: bool,
    make_path: str,
) -> None:
    """This function first looks for the 'hardware.json5' file in the
    'src_abspath'. Based on the board it finds in there, it will figure out
    which sample project in the SDK must be opened. Then, this function moves to
    that folder in the SDK and launches GNU Make there. It then parses the
    output and figures out which files from the SDK belong to this particular
    sample project.

    Finally, it copies them to the given destination folder (which is usually a temporary directo-
    ry). The result is a Nordic project - not an Embeetle project!

    This serves as an intermediate step. After this function completes, the general importer can
    be launched which will just 'beetlify' the intermediate project into a complete Embeetle pro-
    ject.
    """
    hardware_dict = purefunctions.load_json_file_with_comments(
        f"{src_abspath}/hardware.json5"
    )
    if hardware_dict is None:
        raise RuntimeError(
            f"Cannot load json file: {q}{src_abspath}/hardware.json5{q}"
        )
    boardname = hardware_dict["board_name"]
    chipname = hardware_dict["chip_name"]
    probename = hardware_dict["probe_name"]

    # * Find sample project in SDK
    nordic_armgcc_folder: Optional[str] = None
    nordic_build_folder: Optional[str] = None
    if has_freertos:
        nordic_armgcc_folder = str(
            f"{data.nordic_sdk_root}/examples/peripheral/blinky_freertos/"
            f"{boardname.lower()}/blank/armgcc"
        )
    else:
        nordic_armgcc_folder = str(
            f"{data.nordic_sdk_root}/examples/peripheral/blinky/"
            f"{boardname.lower()}/blank/armgcc"
        )
    nordic_build_folder = f"{nordic_armgcc_folder}/_build"

    # * Dry run make
    cmd = [
        make_path,
        "--just-print",
        "--always-make",
    ]
    p = purefunctions.subprocess_popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=nordic_armgcc_folder,
        verbose=True,
    )
    out, err = p.communicate()
    output = out.decode("utf-8", errors="ignore")

    # * Parse output
    # & Extract s-files, c-files and h-dirs
    # $ Replace long gcc calls
    p = re.compile(r"'.*arm-none-eabi-gcc'")
    output = p.sub("arm-none-eabi-gcc", output)
    p = re.compile(r"'.*arm-none-eabi-size'")
    output = p.sub("arm-none-eabi-size", output)
    p = re.compile(r"'.*arm-none-eabi-objcopy'")
    output = p.sub("arm-none-eabi-objcopy", output)
    # $ Extract assembly files
    p = re.compile(r"\s([^\s]*\.S)\s")
    temp = []
    for m in p.finditer(output):
        temp.append(m.group(1))
    asm_files = [
        os.path.normpath(os.path.join(nordic_armgcc_folder, f)).replace(
            "\\", "/"
        )
        for f in temp
        if "/" in f
    ]
    asm_files = list(set(asm_files))
    functions.generator_printfunc(f"asm_files = {asm_files}\n\n")
    # $ Extract c-files
    p = re.compile(r"\s([^\s]*\.c)\s")
    temp = []
    for m in p.finditer(output):
        temp.append(m.group(1))
    c_files = [
        os.path.normpath(os.path.join(nordic_armgcc_folder, f)).replace(
            "\\", "/"
        )
        for f in temp
        if "/" in f
    ]
    c_files = list(set(c_files))
    functions.generator_printfunc(f"c_files = {c_files}\n\n")
    # $ Extract c-dirs
    temp = []
    for c in c_files:
        temp.append("/".join(c.split("/")[:-1]))
    c_dirs = list(set(temp))
    functions.generator_printfunc(f"c_dirs = {c_dirs}\n\n")
    # $ Extract h-dirs (not exhaustive yet!)
    p = re.compile(r"-I(\..*?)\s")
    temp = []
    for m in p.finditer(output):
        temp.append(m.group(1))
    h_dirs = [
        os.path.normpath(os.path.join(nordic_armgcc_folder, d)).replace(
            "\\", "/"
        )
        for d in temp
        if "/" in d
    ]
    h_dirs = list(set(h_dirs))
    functions.generator_printfunc(f"h_dirs = {h_dirs}\n\n")

    # & Analyze include statements
    h_files = []  # absolute paths to h-files
    h_files_nf = []  # relative paths to h-files (not found)
    h_dirs = list(
        set(h_dirs + c_dirs)
    )  # let h-dirs grow to maximize the chance of finding h-files!
    # $ Extract h-files from include statements in c-files
    # Extract
    h_files, h_files_nf = __extractor(
        files=c_files,
        dirs=h_dirs,
        prev_nf=[],
    )
    # Grow h-dirs
    temp = []
    for h in h_files:
        temp.append("/".join(h.split("/")[:-1]))
    h_dirs = list(set(h_dirs + temp))
    # $ Extract h-files from include statements in h-files iteratively
    something_found = True
    while something_found:
        something_found = False
        # $ Search targeted
        while True:
            # Extract
            a1 = len(h_files)
            b1 = len(h_files_nf)
            h_temp, h_temp_nf = __extractor(
                files=h_files,
                dirs=h_dirs,
                prev_nf=h_files_nf,
            )
            # Grow h-files
            h_files = list(set(h_files + h_temp))
            h_files_nf = list(set(h_files_nf + h_temp_nf))
            a2 = len(h_files)
            b2 = len(h_files_nf)
            # Grow h-dirs
            temp = []
            for h in h_files:
                temp.append("/".join(h.split("/")[:-1]))
            h_dirs = list(set(h_dirs + temp))
            # Clean nf list
            h_files_nf = __clean_nf_list(
                h_files=h_files,
                h_files_nf=h_files_nf,
            )
            # Print growth
            if (a2 != a1) or (b2 != b1):
                something_found = True
            functions.generator_printfunc(
                f"Growth targeted search = ({a2 - a1}, {b2 - b1})\n"
            )
            if (a2 - a1) == 0 and (b2 - b1) == 0:
                break
        # $ Search everywhere to find the non-located ones
        a1 = len(h_files)
        b1 = len(h_files_nf)
        h_files, h_files_nf = __look_everywhere_for_nonlocated_ones(
            h_files=h_files,
            h_files_nf=h_files_nf,
        )
        a2 = len(h_files)
        b2 = len(h_files_nf)
        if (a2 != a1) or (b2 != b1):
            something_found = True
        functions.generator_printfunc(
            f"Growth general search = ({a2 - a1}, {b2 - b1})\n"
        )
    functions.generator_printfunc(
        f"h-files abs = {h_files}\n\n",
        color="warning",
    )
    functions.generator_printfunc(
        f"h-files not found = {h_files_nf}\n\n",
        color="warning",
    )

    # * Copy files
    origin_sourcedir = data.nordic_sdk_root
    functions.generator_printfunc(
        "Copy all relevant h-files",
        color="green",
    )
    for f in h_files:
        filefunctions.copy(
            src=f,
            dst=f.replace(data.nordic_sdk_root, dst_abspath),
            printfunc=functions.generator_printfunc,
        )
        continue
    functions.generator_printfunc(
        "Copy all relevant c-files",
        color="green",
    )
    for f in asm_files + c_files:
        filefunctions.copy(
            src=f,
            dst=f.replace(data.nordic_sdk_root, dst_abspath),
            printfunc=functions.generator_printfunc,
        )
        continue

    # * Fix freertos compiler warnings
    functions.generator_printfunc(
        "Fix freertos compiler warnings\n",
        color="green",
    )
    if has_freertos:
        rootpath = dst_abspath
        freertoscfg_filepath = (
            f"{rootpath}/external/freertos/config/FreeRTOSConfig.h"
        )
        if not os.path.isfile(freertoscfg_filepath):
            functions.generator_printfunc(
                f"\nERROR: file not found: " f"{q}{freertoscfg_filepath}{q}\n",
                color="error",
            )
        else:
            freertoscfg_content = None
            with open(
                freertoscfg_filepath, "r", encoding="utf-8", newline="\n"
            ) as f:
                freertoscfg_content = f.read()
            p = re.compile(r"(#define\s*configUSE_TIMERS\s*)(0)")
            m = p.search(freertoscfg_content)
            freertoscfg_content = p.sub(r"\g<1>1", freertoscfg_content)
            with open(
                freertoscfg_filepath, "w", encoding="utf-8", newline="\n"
            ) as f:
                f.write(freertoscfg_content)
            functions.generator_printfunc(
                f"Modified file {freertoscfg_filepath}"
            )

    # * Copy 'readme.txt'
    if os.path.isfile(f"{src_abspath}/readme.txt"):
        filefunctions.copy(
            src=f"{src_abspath}/readme.txt",
            dst=f"{dst_abspath}/readme.txt",
            printfunc=functions.generator_printfunc,
        )

    # * Finish
    functions.generator_printfunc(
        "Extracting Nordic project from SDK completed\n",
        color="green",
    )
    return


def __extractor(
    files: List[str],
    dirs: List[str],
    prev_nf: List[str],
) -> Tuple[List[str], List[str]]:
    """Extract all include statements from 'files' (each include statement is
    one h-file) and locate (rel to abs) the extracted h-files with the help of
    the given 'dirs'.

    PARAMS:
        dirs:  (abs) directories to locate the h-files
        files: (abs) files from which to extract the include statements
    """
    includes_rel = []
    includes_abs = []
    includes_nf = []

    # & Extract include statements
    p = re.compile(
        r"#include\s+[\"<]([\w/]+\.hp*)[\">]"
    )  # ex: 'foo.h', 'foo/bar.h', ...
    for f in files:
        with open(f, "r", encoding="utf-8", newline="\n") as _f_:
            content = _f_.read()
            for m in p.finditer(content):
                includes_rel.append(m.group(1))
                # if 'FreeRTOSConfig.h' in m.group(1):
                #     self.__mini_console.printout(f'#include FreeRTOSConfig.h found!\n', '#ef2929')
                #     self.__mini_console.printout(f'Found at: ', '#ef2929')
                #     self.__mini_console.printout(f'{f}\n', '#ffffff')
    includes_rel = list(set(includes_rel))

    # & Locate h-files
    for h_rel in includes_rel + prev_nf:
        h_abs = []  # For each h_rel, there can be multiple h_abs!
        if "/" in h_rel:
            # $ include 'foo/bar.h'
            for d in dirs:
                if h_rel.split("/")[0] == d.split("/")[-1]:
                    t = h_rel.replace(h_rel.split("/")[0], d, 1)
                    if os.path.isfile(t):
                        h_abs.append(t)
        else:
            # $ include 'foo.h'
            for d in dirs:
                for f_name in os.listdir(d):
                    if f_name == h_rel:
                        h_abs.append(os.path.join(d, f_name).replace("\\", "/"))
        if len(h_abs) == 0:
            includes_nf.append(h_rel)
        else:
            for h in h_abs:
                includes_abs.append(h)
    includes_nf = list(set(includes_nf))
    includes_abs = list(set(includes_abs))

    # & Return found h-files (abs paths) and not-found h-files
    return includes_abs, includes_nf


def __clean_nf_list(
    h_files: List[str],
    h_files_nf: List[str],
) -> List[str]:
    """"""
    temp = []
    for h_rel in h_files_nf:
        found = False
        if "/" in h_rel:
            h_name = h_rel.split("/")[-1]
            for f in h_files:
                f_name = f.split("/")[-1]
                if (h_name == f_name) and (h_rel in f):
                    found = True
                    break
        else:
            h_name = h_rel
            for f in h_files:
                f_name = f.split("/")[-1]
                if f_name == h_name:
                    found = True
                    break
        if not found:
            temp.append(h_rel)
    return list(set(temp))


def __look_everywhere_for_nonlocated_ones(
    h_files: List[str],
    h_files_nf: List[str],
) -> Tuple[List[str], List[str]]:
    """"""
    temp = []
    for dirpath, dirs, files in os.walk(data.nordic_sdk_root):
        for f in files:
            filepath = os.path.join(dirpath, f).replace("\\", "/")
            if f.endswith(".h") or f.endswith(".hpp"):
                for h in h_files_nf:
                    _h_ = ""
                    if "/" in h:
                        _h_ = h.split("/")[-1]
                    else:
                        _h_ = h
                    if (_h_ == f) and (h in filepath):
                        functions.generator_printfunc(
                            f"found lost h-file: {h}\n\n"
                        )
                        temp.append(filepath)
    _a = list(set(h_files + temp))
    _b = __clean_nf_list(h_files=_a, h_files_nf=h_files_nf)
    return _a, _b


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract project from Nordic SDK", add_help=False
    )
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("--freertos", action="store_true")
    parser.add_argument("--src", action="store")
    parser.add_argument("--dst", action="store")
    parser.add_argument("--make", action="store")
    args = parser.parse_args()
    _has_freertos: bool = False
    if args.help:
        __help()
        sys.exit(0)
    try:
        if args.freertos:
            _has_freertos = True
        _src: str = args.src.replace(q, "").replace(dq, "").strip()
        _dst: str = args.dst.replace(q, "").replace(dq, "").strip()
        _make_path: str = args.make.replace(q, "").replace(dq, "").strip()
    except:
        functions.generator_printfunc(
            f"ERROR: Cannot parse arguments!",
            color="error",
        )
        __help()
        sys.exit(1)
    __extract_nordic_project_from_sdk(
        src_abspath=_src,
        dst_abspath=_dst,
        has_freertos=_has_freertos,
        make_path=_make_path,
    )
    sys.exit(0)
