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
import os, json
import data, filefunctions
import functions
import hardware_api.hardware_api as _hardware_api_
import hardware_api.chip_unicum as _chip_unicum_
import hardware_api.board_unicum as _board_unicum_
from various.kristofstuff import *

json_dict = {}


def generate_project_list() -> None:
    """"""
    # & Initialize the json dictionary
    # The json dictionary should have one toplevel entry per manufacturer. Something like:
    # json_dict = {
    #     'arduino' : {},
    #     'atmosic' : {},
    #     ...
    # }
    mf_list = _hardware_api_.HardwareDB().list_manufacturers()
    for e in os.listdir(data.zipped_projects_directory):
        if e == "project_list.json":
            continue
        assert e in mf_list, str(f"mf_list = {mf_list}, e = {e}")
        json_dict[e] = {}

    # & Add json-snippet(s) per project
    # Loop over all the projects in the '.embeetle/zipped_projects/' folder. For each project, one
    # or more json-snippets should be added to the json dictionary. More than one snippet in the
    # case several manufacturers are involved with the project (eg. 'arduino' and 'microchip-
    # atmel').
    for dirpath, dirs, files in os.walk(data.zipped_projects_directory):
        dirpath = dirpath.replace("\\", "/")
        for f in files:
            if f == "project_list.json":
                continue
            filepath = f"{dirpath}/{f}"
            assert filepath.endswith(".7z")
            __add_json_snippet(filepath)
            continue
        continue

    # & Create 'project_list.json'
    # Create the '.embeetle/zipped_projects/project_list.json' file by dumping the json dictionary
    # into that file.
    json_path = f"{data.zipped_projects_directory}/project_list.json"
    if os.path.isfile(json_path):
        filefunctions.delete(
            abspath=json_path,
            verbose=True,
            printfunc=functions.generator_printfunc,
        )
    with open(
        json_path, "w", encoding="utf-8", newline="\n", errors="replace"
    ) as f:
        json.dump(
            json_dict,
            fp=f,
            indent=4,
        )
    return


def __add_json_snippet(zipfile_abspath: str) -> None:
    """Add a json entry for the given zipped project. The given zipfile could
    be:

        ~/.embeetle/zipped_projects/arduino/arduino/arduino-nano-blinky.7z

    The added json entry could be:
    {
        "arduino":
        {   ┌──────────────────────────────────────────────────────────────────────────────────┐
            │ "arduino-nano-blinky": {                                                         │
            │     "chip"       : "atmega328p-mu",                                              │
            │     "board"      : "arduino-nano",                                               │
            │     "boardfamily": "arduino",                                                    │
            │     "path"       : "arduino/arduino/arduino-nano-blinky.7z",                     │
            │     "icon"       : "icons/folder/closed/blinky.png",                             │
            │     "info"       : "microcontroller: atmega328p-mu\nboard: arduino-nano\n..."    │
            │ },                                                                               │
            └──────────────────────────────────────────────────────────────────────────────────┘
            [...]
        }
        [...]
    }

    NOTE:
    =====
    Extracting crucial parameters to fill the json-entry - like boardname, boardname and project
    name - were originally done through analyzing the path to the (zipped) project:
        #                       0       1       3
        #                      [mf]  [bfam]  [pname]
        # ~/.embeetle/zipped/stmicro/nucleo/nucleo_f303k8.7z

    I'm changing that to extracting *all* these parameters from the readme file.

    NOTE:
    =====
    This function can add the json entry *multiple times* - once for each manufacturer listed for
    the chip and board. For example: an Arduino project will be added under both 'microchip-atmel'
    and 'arduino'.
    """
    # & Extract project name
    # The project name is always equal to the name of the zipfile
    projectname = zipfile_abspath.split("/")[-1].replace(".7z", "")

    # & Extract relpath
    # The relative path to the zipfile (so to the project) is important. It's going to be the 'path'
    # parameter in the json-snippet.
    zipfile_relpath = zipfile_abspath.replace(
        f"{data.zipped_projects_directory}/",
        "",
        1,
    )
    assert zipfile_relpath == zipfile_relpath.lower()

    # & Extract 'readme.txt' location
    # We need the corresponding 'readme.txt' file location. It's somewhere in the '.embeetle/
    # generated_projects/' folder.
    nonzipped_location = zipfile_abspath.replace(
        f"{data.zipped_projects_directory}/",
        f"{data.generated_projects_directory}/",
    ).replace(".7z", "")
    readme_location = f"{nonzipped_location}/readme.txt"
    if not os.path.isfile(readme_location):
        raise RuntimeError(f"File {q}{readme_location}{q} not found!")

    # & Analyze 'readme.txt'
    readme_dict = __analyze_readme_file(readme_location)
    manufacturers = list(
        set(
            [
                readme_dict["chip_mf"],
                readme_dict["board_mf"],
            ]
        )
    )

    # & Add json entry for each manufacturer
    # This function can add the json entry *multiple times* - once for each manufacturer listed for
    # the chip and board. For example: an Arduino project will be added under both 'microchip-atmel'
    # and 'arduino'.
    for mf in manufacturers:
        if mf is None:
            continue
        if mf not in json_dict.keys():
            json_dict[mf] = {}
        if projectname in json_dict[mf].keys():
            raise RuntimeError(
                f"{q}{projectname}{q} already in json dictionary!"
            )
        json_dict[mf][projectname] = {
            "chip": readme_dict["chip"],
            "board": readme_dict["board"],
            "boardfamily": readme_dict["boardfamily"],
            "path": zipfile_relpath,
            "icon": readme_dict["icon"],
            "info": readme_dict["info"],
        }
        # $ Limit availability
        # Limit Atmosic availability to users with the 'atmosic-eval' feature
        if mf.lower().replace("_", "-") == "atmosic":
            json_dict[mf][projectname]["features"] = [
                "atmosic-eval",
            ]
        if mf.lower().replace("_", "-") == "nations-tech":
            json_dict[mf][projectname]["features"] = [
                "nations-tech-eval",
            ]
        # if mf.lower().replace('_', '-') == 'geehy':
        #     json_dict[mf][projectname]['features'] = ['geehy-eval', ]
        if mf.lower().replace("_", "-") == "synwit":
            json_dict[mf][projectname]["features"] = [
                "synwit-eval",
            ]
        # if mf.lower().replace('_', '-') == 'fermionic':
        #     json_dict[mf][projectname]['features'] = ['fermionic-eval', ]
        # if 'cip-united' in projectname.lower().replace('_', '-'):
        #     json_dict[mf][projectname]['features'] = ['cip-united-eval', ]
        continue
    return


def __analyze_readme_file(readme_abspath: str) -> Dict[str, str]:
    """
    Analyze the given readme file:
    ┌─────────────────────────────────────────────────────────────────────────┐
    │ microcontroller              : atmega328p-mu                            │
    │ board                        : arduino_nano                             │
    │ microcontroller manufacturer : microchip-atmel                          │
    │ board manufacturer           : arduino                                  │
    │ icon                         : icons/folder/closed/blinky.png    │
    │ link                         : https://embeetle.com/#supported-hardware/arduino/boards/nan
    │ info:                                                                   │
    │ This project is imported from the following Arduino sketch:             │
    │ C:/sample_proj_resources/arduino/sketches/arduino_nano/arduino_nano.ino │
    └─────────────────────────────────────────────────────────────────────────┘

    """
    content: Optional[str] = None
    with open(readme_abspath, "r", encoding="utf-8", newline="\n") as f:
        content = f.read()
    chip_unicum: Optional[_chip_unicum_.CHIP] = None
    board_unicum: Optional[_board_unicum_.BOARD] = None
    chip_mf: Optional[str] = None
    board_mf: Optional[str] = None
    iconpath: Optional[str] = None
    link: Optional[str] = None
    for line in content.splitlines():
        line = line.lower().strip()
        # $ microcontroller
        if line.startswith("microcontroller:"):
            chip_unicum = _chip_unicum_.CHIP(
                line.replace("microcontroller:", "").strip()
            )
            assert chip_unicum is not None
        # $ board
        if line.startswith("board:"):
            board_unicum = _board_unicum_.BOARD(
                line.replace("board:", "").strip()
            )
            assert board_unicum is not None
        # $ microcontroller manufacturer
        if line.startswith("microcontroller manufacturer:"):
            chip_mf = line.replace("microcontroller manufacturer:", "").strip()
        # $ board manufacturer
        if line.startswith("board manufacturer:"):
            board_mf = line.replace("board manufacturer:", "").strip()
            if (board_mf.lower() == "none") or (board_mf.lower() == "custom"):
                board_mf = None
        # $ icon
        if line.startswith("icon:"):
            iconpath = line.replace("icon:", "").strip()
        # $ link
        if line.startswith("link:"):
            link = line.replace("link:", "").strip()
        # $ info
        if line.startswith("info:"):
            break
        continue
    return {
        "chip": chip_unicum.get_name().lower(),
        "board": board_unicum.get_name().lower(),
        "chip_mf": chip_mf,
        "board_mf": board_mf,
        "boardfamily": board_unicum.get_board_dict()["boardfamily"],
        "icon": iconpath,
        "link": link,
        "info": content,
    }
