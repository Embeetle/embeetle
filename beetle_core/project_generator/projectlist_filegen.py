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
import threading, os, json
import qt, data, purefunctions
from components.singleton import Singleton
import beetle_console.mini_console as _mini_console_
import bpathlib.path_power as _pp_
import bpathlib.file_power as _fp_
import components.thread_switcher as _sw_
import project.project as _project_
import hardware_api.chip_unicum as _chip_unicum_
import hardware_api.board_unicum as _board_unicum_
from various.kristofstuff import *


class ProjectList_FileGen(metaclass=Singleton):
    """"""

    def __init__(self):
        super().__init__()
        assert threading.current_thread() is threading.main_thread()
        _sw_.register_thread(
            name="main",
            qthread=qt.QThread.currentThread(),
        )
        self.__mini_console: Optional[_mini_console_.MiniConsole] = None
        self.__json_dict = {
            "arduino": {},
            "atmosic": {},
            "giga": {},
            "nxp": {},
            "microchip-atmel": {},
            "nordic": {},
            "nuvoton": {},
            "stmicro": {},
            "embeetle": {},
            "espressif": {},
        }
        return

    def analyze_readme_file(self, readme_abspath: str) -> Dict[str, str]:
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
                chip_mf = line.replace(
                    "microcontroller manufacturer:", ""
                ).strip()
            # $ board manufacturer
            if line.startswith("board manufacturer:"):
                board_mf = line.replace("board manufacturer:", "").strip()
                if (board_mf.lower() == "none") or (
                    board_mf.lower() == "custom"
                ):
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
            "icon": iconpath,
            "link": link,
            "info": content,
        }

    def add_json_snippet(self, zipfile_abspath: str) -> None:
        """Add a json entry for the given zipped project. The given zipfile
        could be:

            ~/.embeetle/zipped/arduino/arduino/baremetal/arduino_nano.7z

        The added json entry could be:
        {
            'arduino':
            {   ┌──────────────────────────────────────────────────────────────────────────────────┐
                │'<project_name>':                                                                 │
                │{                                                                                 │
                │    'boardfamily': 'arduino',                                                     │
                │    'chip'       : 'atmega328p-mu',                                               │
                │    'path'       : 'arduino/arduino/baremetal/arduino_nano.7z',                   │
                │    'icon'       : 'icons/folder/closed/blinky.png',                       │
                │    'info'       : str(                                                           │
                │        'Microcontroller: ATMEGA328P-MU\n'                                        │
                │        'Board: ARDUINO_NANO\n'                                                   │
                │        'Link: https://embeetle.com/#supported-hardware/arduino/boards/nano\n'    │
                │        'Info:\n'                                                                 │
                │        'This project is imported from the following Arduino sketch:\n'           │
                │        'C:/sample_proj_resources/arduino/sketches/arduino_nano/arduino_nano.ino\n'
                │    ),                                                                            │
                │},                                                                                │
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
        """
        # * Extract project name
        # Project name will be modified further on.
        projectname = (
            zipfile_abspath.split("/")[-1]
            .replace(".zip", "")
            .replace(".7z", "")
        )

        # * Extract relpath
        zipfile_relpath = zipfile_abspath.replace(
            f"{data.settings_directory}/zipped/",
            "",
            1,
        )
        assert zipfile_relpath == zipfile_relpath.lower()

        # * Extract readme location
        nonzipped_location = (
            zipfile_abspath.replace(
                f"{data.settings_directory}/zipped/",
                f"{data.settings_directory}/",
            )
            .replace(".zip", "")
            .replace(".7z", "")
        )
        readme_location = f"{nonzipped_location}/readme.txt"
        if not os.path.isfile(readme_location):
            purefunctions.printc(
                f"ERROR: file {q}{readme_location}{q} not found!",
                color="error",
            )
            assert False

        # * Analyze readme file
        readme_dict = self.analyze_readme_file(readme_location)
        manufacturers = list(
            set(
                [
                    readme_dict["chip_mf"],
                    readme_dict["board_mf"],
                ]
            )
        )

        # * Make json entry for each manufacturer
        for mf in manufacturers:
            if mf is None:
                continue
            assert projectname not in self.__json_dict[mf].keys(), str(
                f"\nERROR: {q}{projectname}{q} already in "
                f"self.__json_dict[{mf}]\n"
            )
            boardfam_name = _board_unicum_.BOARD(
                readme_dict["board"]
            ).get_board_dict()["boardfamily"]
            self.__json_dict[mf][projectname] = {
                "chip": readme_dict["chip"],
                "board": readme_dict["board"],
                "boardfamily": boardfam_name,
                "path": zipfile_relpath,
                "icon": readme_dict["icon"],
                "info": readme_dict["info"],
            }
        return None

    def projectlist_generate(self) -> None:
        """"""
        assert threading.current_thread() is threading.main_thread()
        origthread: qt.QThread = qt.QThread.currentThread()
        printfunc: Optional[Callable] = None
        printhtmlfunc: Optional[Callable] = None
        projObj_list: List[_project_.Project] = []

        def start(*args) -> None:
            nonlocal printfunc, printhtmlfunc
            assert qt.QThread.currentThread() is origthread
            if self.__mini_console is None:
                self.__mini_console = _mini_console_.MiniConsole("Generate all")
            printfunc = self.__mini_console.get_printfunc()
            printhtmlfunc = self.__mini_console.get_printhtmlfunc()
            start_generation()
            return

        def start_generation(*args) -> None:
            self.__mini_console.printout("START PROJECTLIST GENERATION\n\n")
            for dirpath, dirs, files in os.walk(
                f"{data.settings_directory}/zipped"
            ):
                for f in files:
                    filepath = _pp_.rel_to_abs(
                        rootpath=dirpath,
                        relpath=f,
                    )
                    if filepath.endswith(".zip") or filepath.endswith(".7z"):
                        self.__mini_console.printout(".")
                        self.add_json_snippet(filepath)
            finish()
            return

        def finish(*args) -> None:
            assert qt.QThread.currentThread() is origthread
            projlist_filepath = (
                f"{data.settings_directory}/zipped/project_list.json"
            )
            _fp_.delete_file(projlist_filepath)
            _fp_.make_file(projlist_filepath)
            self.__mini_console.printout(
                f"\nCreate json file: {q}{projlist_filepath}{q}\n"
            )
            with open(
                projlist_filepath, "w", encoding="utf-8", newline="\n"
            ) as f:
                json.dump(self.__json_dict, fp=f, indent=4)
            self.__mini_console.printout("Done\n")
            return

        start()
        return
