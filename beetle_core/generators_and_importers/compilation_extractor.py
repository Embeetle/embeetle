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
import os

import functions
import purefunctions
import regex as re


def extract_dependencies_from_link_file(
    buildfolder: str, link_file: str
) -> Dict:
    """"""
    depend_dict = {}
    if (link_file is None) or (not os.path.isfile(link_file)):
        return {}
    p = re.compile(r"xtensa-esp32-elf-ar\sqc\s(\w+[.]a)\s+([\w\s/.]*)$")
    with open(
        link_file, "r", encoding="utf-8", newline="\n", errors="replace"
    ) as f:
        content = f.read()
    for line in content.splitlines():
        m = p.search(line)
        if m is None:
            continue
        targetname = m.group(1)
        dependencies = m.group(2).split(" ")
        dependencies_abspaths = []
        target = targetname
        if not os.path.isfile(target):
            target = os.path.join(
                os.path.dirname(link_file), targetname
            ).replace("\\", "/")
            if not os.path.isfile(target):
                target = os.path.join(
                    os.path.dirname(os.path.dirname(link_file)),
                    targetname,
                ).replace("\\", "/")
                if not os.path.isfile(target):
                    target = os.path.join(
                        os.path.dirname(
                            os.path.dirname(os.path.dirname(link_file))
                        ),
                        targetname,
                    ).replace("\\", "/")
                    if not os.path.isfile(target):
                        functions.importer_printfunc(
                            f"WARNING 1: file not found: {target}",
                            color="warning",
                        )
        for d in dependencies:
            if os.path.isfile(d):
                dependencies_abspaths.append(d)
                continue
            d_abs = os.path.join(
                os.path.dirname(link_file),
                d,
            ).replace("\\", "/")
            if os.path.isfile(d_abs):
                dependencies_abspaths.append(d_abs)
                continue
            d_abs = os.path.join(
                os.path.dirname(os.path.dirname(link_file)),
                d,
            ).replace("\\", "/")
            if os.path.isfile(d_abs):
                dependencies_abspaths.append(d_abs)
                continue
            d_abs = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(link_file))),
                d,
            ).replace("\\", "/")
            if os.path.isfile(d_abs):
                dependencies_abspaths.append(d_abs)
                continue
            functions.importer_printfunc(
                f"WARNING 2: file not found: {d}", color="warning"
            )
            dependencies_abspaths.append(d)
            continue
        depend_dict[target] = dependencies_abspaths
        continue
    return depend_dict


def extract_dependencies_from_depend_make(
    buildfolder: str, depend_make_file: str
) -> Dict:
    """"""
    depend_dict = {}
    if (depend_make_file is None) or (not os.path.isfile(depend_make_file)):
        return {}
    with open(
        depend_make_file, "r", encoding="utf-8", newline="\n", errors="replace"
    ) as f:
        content = f.read()
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#"):
            continue
        if not ":" in line:
            continue
        target = line.split(":")[0].strip()
        dependency = line.split(":")[1].strip()
        if not os.path.isfile(target):
            target = os.path.join(buildfolder, target).replace("\\", "/")
            if not os.path.isfile(target):
                target = target.replace("/esp-idf/esp-idf/", "/esp-idf/", 1)
                if not os.path.isfile(target):
                    target = target.replace(
                        "/build/esp-idf/config/", "/build/config/", 1
                    )
                    if not os.path.isfile(target):
                        target = purefunctions.standardize_abspath(target)
                        if not os.path.isfile(target):
                            target = target.replace("/build/main/", "/main/", 1)
                            if not os.path.isfile(target):
                                functions.importer_printfunc(
                                    f"WARNING 3: file not found: {target}",
                                    color="warning",
                                )
        if not os.path.isfile(dependency):
            dependency = os.path.join(buildfolder, dependency).replace(
                "\\", "/"
            )
            if not os.path.isfile(dependency):
                dependency = dependency.replace(
                    "/esp-idf/esp-idf/", "/esp-idf/", 1
                )
                if not os.path.isfile(dependency):
                    dependency = dependency.replace(
                        "/build/esp-idf/config/", "/build/config/", 1
                    )
                    if not os.path.isfile(dependency):
                        dependency = purefunctions.standardize_abspath(
                            dependency
                        )
                        if not os.path.isfile(dependency):
                            dependency = dependency.replace(
                                "/build/main/", "/main/", 1
                            )
                            if not os.path.isfile(dependency):
                                functions.importer_printfunc(
                                    f"WARNING 4: file not found: {dependency}",
                                    color="warning",
                                )
        if target not in depend_dict:
            depend_dict[target] = []
        depend_dict[target].append(dependency)
        continue
    return depend_dict


def extract_hfiles_from_dfile(dfilepath: str) -> List[str]:
    """Given the absolute path to a *.d file, extract all the hfiles listed
    there."""
    if (dfilepath is None) or (not os.path.isfile(dfilepath)):
        return []
    regex_list = [
        r"([-~:\w\d/\.]+[.]h)",
        r"([-~:\w\d/\.]+[.]H)",
        r"([-~:\w\d/\.]+[.]hpp)",
        r"([-~:\w\d/\.]+[.]h++)",
        r'"([-~:\w\d /\.]+[.]h)"',
        r'"([-~:\w\d /\.]+[.]H)"',
        r'"([-~:\w\d /\.]+[.]hpp)"',
        r'"([-~:\w\d /\.]+[.]h++)"',
    ]
    pattern_list = [re.compile(r) for r in regex_list]
    with open(
        dfilepath, "r", encoding="utf-8", newline="\n", errors="replace"
    ) as f:
        content = f.read()
    temp = []
    for line in content.splitlines():
        line = line.strip()
        if line.endswith("\\"):
            line = line[0:-1]
        line = line.strip()
        line = line.replace("\\", "/")
        for p in pattern_list:
            m = p.search(line)
            if m is not None:
                filepath = m.group(1)
                if "/preproc/ctags_target" in filepath:
                    pass
                else:
                    temp.append(filepath)
    hfile_list = [
        purefunctions.standardize_abspath(f)
        .replace("\\", "/")
        .replace("//", "/")
        for f in set(temp)
    ]
    return hfile_list
