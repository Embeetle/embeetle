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
import os, json, copy, pathlib, traceback, itertools
import data, purefunctions
import hardware_api.board_unicum as _board_unicum_
import hardware_api.chip_unicum as _chip_unicum_
import hardware_api.probe_unicum as _probe_unicum_
import hardware_api.manufacturer_unicum as _manufacturer_unicum_
import hardware_api.treepath_unicum as _treepath_unicum_
import hardware_api.toolcat_unicum as _toolcat_unicum_

q = "'"
dq = '"'


def override_dict(
    d1: Dict[str, Any],
    d2: Dict[str, Any],
) -> Dict[str, Any]:
    """Override dict 'orig_dict' with values from 'over_dict' and return the
    resulting dictionary. Apply 'copy.deepcopy()' first on the parameters to
    make sure they remain untouched!

    Suffix rules:
        - '++': Add the value
        - '--': Substract the value
        - '~~': Replace the value
    """
    for k in d1.keys():
        # $ Key 'k' appears in second dict with a '++', '--' or '~~' token
        if f"{k}++" in d2.keys():
            if isinstance(d1[k], list):
                d1[k].extend(d2[f"{k}++"])
            elif isinstance(d1[k], dict):
                d1[k].update(d2[f"{k}++"])
            else:
                raise RuntimeError()
            continue
        if f"{k}--" in d2.keys():
            if isinstance(d1[k], list):
                d1[k] = [v for v in d1[k] if v not in d2[f"{k}--"]]
            elif isinstance(d1[k], dict):
                d1[k] = {
                    k2: v2
                    for (k2, v2) in d1[k].items()
                    if k2 not in d2[f"{k}--"].keys()
                }
            else:
                raise RuntimeError()
            continue
        if f"{k}~~" in d2.keys():
            d1[k] = d2[f"{k}~~"]
            continue
        # $ Value d1[k] is a dictionary itself and 'k' appears in second dict
        if isinstance(d1[k], dict) and (k in d2.keys()):
            d1[k] = override_dict(copy.deepcopy(d1[k]), copy.deepcopy(d2[k]))
            continue
        # $ Key 'k' can be ignored
        # It either doesn't appear in the second dict, or it does but without a special token and
        # a value that isn't a dictionary (which would have triggered a recursion in previous line).
        continue
    return d1


class DBSingleton(type):
    """Use 'DBSingleton' as a metaclass to make sure you can only create a
    single object from the given class.

    Note: design pattern taken from StackOverflow,
          see https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(DBSingleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]


class HardwareDB(metaclass=DBSingleton):
    def __init__(self) -> None:
        """"""
        super().__init__()
        # $ Database
        self.__hardware_db: Dict[str, Dict[str, Any]] = {}
        self.__overrides_db: Dict[str, Dict[str, Any]] = {
            "board": {},
            "chip": {},
            "probe": {},
        }

        # $ Synonym lists
        self.__chip_synonyms: Optional[Dict[str, str]] = None
        self.__board_synonyms: Optional[Dict[str, str]] = None
        self.__probe_synonyms: Optional[Dict[str, str]] = None
        self.__boardfam_synonyms: Optional[Dict[str, str]] = None
        self.__chipfam_synonyms: Optional[Dict[str, str]] = None

        # $ Board lookup table
        self.__board_lookup: Optional[Dict[str, Dict[str, str]]] = None
        # self.__board_lookup = {
        #     'arduino-due': {
        #         'boardfamily' : 'arduino',
        #         'manufacturer': 'arduino',
        #     },
        #     'nucleo-f303k8': {
        #         'boardfamily' : 'nucleo',
        #         'manufacturer': 'stmicro',
        #     },
        #     ...
        # }
        self.__boardfam_lookup: Optional[Dict[str, Dict[str, str]]] = None
        # self.__boardfam_lookup = {
        #     'arduino': {
        #         'manufacturer': 'arduino',
        #     },
        #     'nucleo': {
        #         'manufacturer': 'stmicro',
        #     },
        #     ...
        # }

        # $ Chip lookup table
        self.__chip_lookup: Optional[Dict[str, Dict[str, str]]] = None
        # self.__chip_lookup = {
        #     'atmega32u4': {
        #         'chipfamily'  : 'atmega',
        #         'manufacturer': 'microchip-atmel',
        #     },
        #     'stm32f303k8': {
        #         'chipfamily'  : 'stm32f3',
        #         'manufacturer': 'stmicro',
        #     },
        #     ...
        # }
        self.__chipfam_lookup: Optional[Dict[str, Dict[str, str]]] = None
        # self.__chipfam_lookup = {
        #     'atmega': {
        #         'manufacturer': 'microchip-atmel',
        #     },
        #     'stm32f3': {
        #         'manufacturer': 'stmicro',
        #     },
        #     ...
        # }

        # $ Probe lookup table
        self.__probe_lookup: Optional[Dict[str, Dict[str, str]]] = None
        # self.__probe_lookup = {
        #     'blackmagic-v2-1': {
        #         'manufacturer': '1bitsquared',
        #     },
        #     'arduino-as-isp': {
        #         'manufacturer': 'arduino',
        #     },
        #     ...
        # }

        # $ No cache found
        # Fill the database from the original data and write a cache file for next time.
        if data.debug_mode:
            try:
                self.reset()  # reset and fill lookup tables
            except:
                traceback.print_exc()
                raise
            self.__check_db()
            return
        if not os.path.isfile(self.__get_cache_filepath()):
            print("\nINFO: Hardware cache not found. Renew cache.")
            self.reset()  # reset and fill lookup tables
            return

        # $ Cache found
        # Try to read the cache, compare the version nrs and resort to the original data if the
        # cache is deprecated.
        try:
            self.__read_cache()
            self.__fill_lookup_tables()
        except:
            print("\nINFO: Hardware cache corrupted. Renew cache.")
            self.reset()  # reset and fill lookup tables
            return
        cache_version = self.__hardware_db["embeetle_version"]
        current_version = purefunctions.get_embeetle_version()
        if cache_version != current_version:
            print("\nINFO: Hardware cache is out of date. Renew cache.")
            self.reset()  # reset and fill lookup tables
            return
        return

    def reset(self) -> None:
        """Renew the cache."""
        # $ Reset variables
        self.__hardware_db: Dict[str, Any] = {}

        self.__chip_synonyms: Optional[Dict[str, str]] = None
        self.__board_synonyms: Optional[Dict[str, str]] = None
        self.__probe_synonyms: Optional[Dict[str, str]] = None
        self.__boardfam_synonyms: Optional[Dict[str, str]] = None
        self.__chipfam_synonyms: Optional[Dict[str, str]] = None

        self.__board_lookup: Optional[Dict[str, Dict[str, str]]] = None
        self.__boardfam_lookup: Optional[Dict[str, Dict[str, str]]] = None
        self.__chip_lookup: Optional[Dict[str, Dict[str, str]]] = None
        self.__chipfam_lookup: Optional[Dict[str, Dict[str, str]]] = None
        self.__probe_lookup: Optional[Dict[str, Dict[str, str]]] = None

        # $ Fill database and rewrite cache
        self.__parse_original_db()
        self.__write_cache()
        if data.debug_mode:
            self.__check_db()
        self.__read_cache()
        self.__fill_lookup_tables()
        cache_version = self.__hardware_db["embeetle_version"]
        current_version = purefunctions.get_embeetle_version()
        if cache_version != current_version:
            raise RuntimeError("Cache version is wrong!")
        return

    def __parse_original_db(self) -> None:
        """Parse the original database from 'resources/hardware/' and store the
        resulting dict in 'self.__hardware_db'."""
        # * Parse database
        self.__hardware_db: Dict[str, Any] = {}
        hardware_path = purefunctions.join_resources_dir_to_path("hardware")

        # $ board
        try:
            self.__hardware_db["board"] = {}
            for mf in os.listdir(f"{hardware_path}/board"):
                if os.path.isfile(f"{hardware_path}/board/{mf}"):
                    continue
                self.__hardware_db["board"][mf] = {}
                for boardfam in os.listdir(f"{hardware_path}/board/{mf}"):
                    if os.path.isfile(f"{hardware_path}/board/{mf}/{boardfam}"):
                        continue
                    self.__hardware_db["board"][mf][boardfam] = {}
                    fam_filepath = (
                        f"{hardware_path}/board/{mf}/{boardfam}/family.json5"
                    )
                    self.__hardware_db["board"][mf][boardfam]["family"] = (
                        purefunctions.load_json_file_with_comments(fam_filepath)
                    )
                    for board in os.listdir(
                        f"{hardware_path}/board/{mf}/{boardfam}"
                    ):
                        if os.path.isfile(
                            f"{hardware_path}/board/{mf}/{boardfam}/{board}"
                        ):
                            continue
                        board_filepath = f"{hardware_path}/board/{mf}/{boardfam}/{board}/board.json5"
                        self.__hardware_db["board"][mf][boardfam][board] = (
                            purefunctions.load_json_file_with_comments(
                                board_filepath
                            )
                        )
                        continue
                    continue
                continue
        except:
            traceback.print_exc()

        # $ chip
        try:
            self.__hardware_db["chip"] = {}
            for mf in os.listdir(f"{hardware_path}/chip"):
                if os.path.isfile(f"{hardware_path}/chip/{mf}"):
                    continue
                self.__hardware_db["chip"][mf] = {}
                for chipfam in os.listdir(f"{hardware_path}/chip/{mf}"):
                    if os.path.isfile(f"{hardware_path}/chip/{mf}/{chipfam}"):
                        continue
                    self.__hardware_db["chip"][mf][chipfam] = {}
                    fam_filepath = (
                        f"{hardware_path}/chip/{mf}/{chipfam}/family.json5"
                    )
                    self.__hardware_db["chip"][mf][chipfam]["family"] = (
                        purefunctions.load_json_file_with_comments(fam_filepath)
                    )
                    for chip in os.listdir(
                        f"{hardware_path}/chip/{mf}/{chipfam}"
                    ):
                        if os.path.isfile(
                            f"{hardware_path}/chip/{mf}/{chipfam}/{chip}"
                        ):
                            continue
                        chip_filepath = f"{hardware_path}/chip/{mf}/{chipfam}/{chip}/chip.json5"
                        self.__hardware_db["chip"][mf][chipfam][chip] = (
                            purefunctions.load_json_file_with_comments(
                                chip_filepath
                            )
                        )
                        continue
                    continue
                continue
        except:
            traceback.print_exc()

        # $ manufacturer
        try:
            self.__hardware_db["manufacturer"] = {}
            for mf in os.listdir(f"{hardware_path}/manufacturer"):
                # '.json5' included in 'mf'
                if mf.endswith(".json5"):
                    mf_filepath = f"{hardware_path}/manufacturer/{mf}"
                    self.__hardware_db["manufacturer"][mf[0:-6]] = (
                        purefunctions.load_json_file_with_comments(mf_filepath)
                    )
                    continue
                continue
        except:
            traceback.print_exc()

        # $ probe
        try:
            self.__hardware_db["probe"] = {}
            for mf in os.listdir(f"{hardware_path}/probe"):
                if os.path.isfile(f"{hardware_path}/probe/{mf}"):
                    continue
                self.__hardware_db["probe"][mf] = {}
                for probe in os.listdir(f"{hardware_path}/probe/{mf}"):
                    if os.path.isfile(f"{hardware_path}/probe/{mf}/{probe}"):
                        continue
                    probe_filepath = (
                        f"{hardware_path}/probe/{mf}/{probe}/probe.json5"
                    )
                    self.__hardware_db["probe"][mf][probe] = (
                        purefunctions.load_json_file_with_comments(
                            probe_filepath
                        )
                    )
                    continue
                continue
            self.__hardware_db["probe"]["transport_protocol"] = list(
                purefunctions.load_json_file_with_comments(
                    f"{hardware_path}/probe/transport_protocol.json5"
                ).keys()
            )
        except:
            traceback.print_exc()

        # $ project-layout
        try:
            self.__hardware_db["project-layout"] = {
                "makefile-based": purefunctions.load_json_file_with_comments(
                    f"{hardware_path}/project-layout/makefile-based.json5",
                ),
            }
        except:
            traceback.print_exc()

        # $ tool-categories
        try:
            self.__hardware_db["tool-categories"] = (
                purefunctions.load_json_file_with_comments(
                    f"{hardware_path}/tool-categories/toolcats.json5"
                )
            )
        except:
            traceback.print_exc()

        # $ version
        self.__hardware_db["embeetle_version"] = (
            purefunctions.get_embeetle_version()
        )

        # * Filter inactive stuff
        inactive_boardfam_list = []
        inactive_board_list = []
        inactive_chipfam_list = []
        inactive_chip_list = []
        inactive_mf_list = []
        inactive_probe_list = []
        for mf in self.__hardware_db["board"].keys():
            for boardfam in self.__hardware_db["board"][mf].keys():
                if not self.__hardware_db["board"][mf][boardfam]["family"][
                    "active"
                ]:
                    inactive_boardfam_list.append(boardfam)
                for board in self.__hardware_db["board"][mf][boardfam].keys():
                    if board == "family":
                        continue
                    if not self.__hardware_db["board"][mf][boardfam][board][
                        "active"
                    ]:
                        inactive_board_list.append(board)
                    continue
                continue
            continue

        for mf in self.__hardware_db["chip"].keys():
            for chipfam in self.__hardware_db["chip"][mf].keys():
                if not self.__hardware_db["chip"][mf][chipfam]["family"][
                    "active"
                ]:
                    inactive_chipfam_list.append(chipfam)
                for chip in self.__hardware_db["chip"][mf][chipfam].keys():
                    if chip == "family":
                        continue
                    if not self.__hardware_db["chip"][mf][chipfam][chip][
                        "active"
                    ]:
                        inactive_chip_list.append(chip)
                    continue
                continue
            continue

        for mf in self.__hardware_db["manufacturer"].keys():
            if not self.__hardware_db["manufacturer"][mf]["active"]:
                inactive_mf_list.append(mf)
            continue

        for mf in self.__hardware_db["probe"].keys():
            if mf == "transport_protocol":
                continue
            for probe in self.__hardware_db["probe"][mf].keys():
                if not self.__hardware_db["probe"][mf][probe]["active"]:
                    inactive_probe_list.append(probe)
                continue
            continue

        # print(f'inactive_boardfam_list = {inactive_boardfam_list}')
        # print(f'inactive_board_list = {inactive_board_list}')
        # print(f'inactive_chipfam_list = {inactive_chipfam_list}')
        # print(f'inactive_chip_list = {inactive_chip_list}')
        # print(f'inactive_mf_list = {inactive_mf_list}')
        # print(f'inactive_probe_list = {inactive_probe_list}')

        for mf in list(self.__hardware_db["board"].keys()):
            for boardfam in list(self.__hardware_db["board"][mf].keys()):
                for board in list(
                    self.__hardware_db["board"][mf][boardfam].keys()
                ):
                    if board == "family":
                        continue
                    if board not in inactive_board_list:
                        continue
                    del self.__hardware_db["board"][mf][boardfam][board]
                    continue
                if boardfam not in inactive_boardfam_list:
                    if len(self.__hardware_db["board"][mf][boardfam]) == 0:
                        del self.__hardware_db["board"][mf][boardfam]
                    continue
                del self.__hardware_db["board"][mf][boardfam]
                continue
            if mf not in inactive_mf_list:
                if len(self.__hardware_db["board"][mf]) == 0:
                    del self.__hardware_db["board"][mf]
                continue
            del self.__hardware_db["board"][mf]
            continue

        for mf in list(self.__hardware_db["chip"].keys()):
            for chipfam in list(self.__hardware_db["chip"][mf].keys()):
                for chip in list(
                    self.__hardware_db["chip"][mf][chipfam].keys()
                ):
                    if chip == "family":
                        continue
                    if chip not in inactive_chip_list:
                        continue
                    del self.__hardware_db["chip"][mf][chipfam][chip]
                    continue
                if chipfam not in inactive_chipfam_list:
                    if len(self.__hardware_db["chip"][mf][chipfam]) == 0:
                        del self.__hardware_db["chip"][mf][chipfam]
                    continue
                del self.__hardware_db["chip"][mf][chipfam]
                continue
            if mf not in inactive_mf_list:
                if len(self.__hardware_db["chip"][mf]) == 0:
                    del self.__hardware_db["chip"][mf]
                continue
            del self.__hardware_db["chip"][mf]
            continue

        for mf in list(self.__hardware_db["manufacturer"].keys()):
            if mf not in inactive_mf_list:
                continue
            del self.__hardware_db["manufacturer"][mf]
            continue

        for mf in list(self.__hardware_db["probe"].keys()):
            if mf == "transport_protocol":
                continue
            for probe in list(self.__hardware_db["probe"][mf].keys()):
                if probe not in inactive_probe_list:
                    continue
                del self.__hardware_db["probe"][mf][probe]
                continue
            if mf not in inactive_mf_list:
                if len(self.__hardware_db["probe"][mf]) == 0:
                    del self.__hardware_db["probe"][mf]
                continue
            del self.__hardware_db["probe"][mf]
            continue
        return

    def __get_cache_filepath(self) -> str:
        """Return the path from the cache file."""
        user_directory = purefunctions.standardize_abspath(
            str(pathlib.Path.home())
        )
        settings_directory = purefunctions.standardize_abspath(
            os.path.join(user_directory, ".embeetle")
        )
        return os.path.join(
            settings_directory,
            "hardware_cache/hardware_db.json",
        ).replace("\\", "/")

    def __write_cache(self) -> None:
        """Write the content from 'self.__hardware_db' to the cache file."""
        hardware_cache_filepath = self.__get_cache_filepath()
        if not os.path.isfile(hardware_cache_filepath):
            # Will also make parental folder if needed
            parentdir = os.path.dirname(hardware_cache_filepath).replace(
                "\\", "/"
            )
            if not os.path.isdir(parentdir):
                os.makedirs(parentdir)
            with open(
                hardware_cache_filepath, "w", encoding="utf-8", newline="\n"
            ) as f:
                f.write("")
        with open(
            hardware_cache_filepath, "w", encoding="utf-8", newline="\n"
        ) as json_file:
            json.dump(self.__hardware_db, json_file, indent=4)
        return

    def __read_cache(self) -> None:
        """Read the cache file and store it into 'self.__hardware_db'."""
        hardware_cache_filepath = self.__get_cache_filepath()
        assert os.path.isfile(hardware_cache_filepath)
        try:
            with open(
                hardware_cache_filepath, "r", errors="replace", newline="\n"
            ) as _f:
                self.__hardware_db = json.load(_f)
        except:
            purefunctions.printc(
                f"\nERROR: Cannot read json file: "
                f"{q}{hardware_cache_filepath}{q}\n",
                color="error",
            )
            raise
        return

    def __check_db(self) -> None:
        """Check the database.

        Throw an error if something is wrong.
        """
        # & Check boardfamilies
        # Each boardfamily must have its own json file. Make sure it exists and is valid.
        for mf in self.__hardware_db["board"].keys():
            for boardfam in self.__hardware_db["board"][mf].keys():
                boardfam_dict = self.__hardware_db["board"][mf][boardfam][
                    "family"
                ]

                # $ Check dictionary kind
                assert boardfam_dict["kind"] == "boardfamily"

                # $ Check if manufacturer exist
                assert (
                    boardfam_dict["manufacturer"]
                    in self.__hardware_db["manufacturer"].keys()
                )
            continue

        # & Check boards
        for mf in self.__hardware_db["board"].keys():
            for boardfam in self.__hardware_db["board"][mf].keys():
                boardfam_dict = self.__hardware_db["board"][mf][boardfam][
                    "family"
                ]
                for board in self.__hardware_db["board"][mf][boardfam].keys():
                    if board == "family":
                        continue
                    board_dict = self.__hardware_db["board"][mf][boardfam][
                        board
                    ]

                    # $ Check dictionary kind
                    assert board_dict["kind"] == "board"

                    # $ Check if chip exists
                    pass
                continue
            continue
        # & Check if 'chip-on-board' exists for each board.

        # & If a chip is inactive, check if the corresponding board is inactive too.

        # & If a probe is inactive, remove it from boards and chips where it is listed.

        # & Check if linkerscripts and other listed supplementary files exist.
        return

    def clean_overrides_db(self) -> None:
        """Clean self.__overrides_db."""
        self.__overrides_db = {
            "board": {},
            "chip": {},
            "probe": {},
        }
        return

    def parse_overrides_db(self, proj_rootpath: str) -> None:
        """Check if a 'chip.json', 'board.json' or 'probe.json' file can be
        found in the given project.

        If that's the case, then keep that data to override the current
        database.
        """
        # & Find files
        # Look for 'board.json5', 'chip.json5' and 'probe.json5' files in the project.
        filepath_list = [
            f"{proj_rootpath}/board.json5",
            f"{proj_rootpath}/chip.json5",
            f"{proj_rootpath}/probe.json5",
            f"{proj_rootpath}/.beetle/board.json5",
            f"{proj_rootpath}/.beetle/chip.json5",
            f"{proj_rootpath}/.beetle/probe.json5",
            f"{proj_rootpath}/config/board.json5",
            f"{proj_rootpath}/config/chip.json5",
            f"{proj_rootpath}/config/probe.json5",
        ]
        for filepath in reversed(filepath_list):
            if os.path.isfile(filepath):
                continue
            filepath_list.remove(filepath)
            continue
        if len(filepath_list) == 0:
            return

        # & Parse each file
        for filepath in filepath_list:
            # $ Extract the json-dictionary
            try:
                item_dict = purefunctions.load_json_file_with_comments(filepath)
            except:
                item_dict = None
            if item_dict is None:
                purefunctions.printc(
                    f"\nERROR: Cannot read json-file {q}{filepath}{q}!\n",
                    color="error",
                )
                continue

            # $ Check the item's name
            item_name = item_dict.get("name")
            if (
                (item_name is None)
                or (not isinstance(item_name, str))
                or (
                    item_name
                    not in itertools.chain(
                        self.__board_lookup.keys(),
                        self.__chip_lookup.keys(),
                        self.__probe_lookup.keys(),
                    )
                )
            ):
                purefunctions.printc(
                    f"\nERROR: Item in json-file {q}{filepath}{q} unknown: {q}{item_name}{q}!\n",
                    color="error",
                )
                continue

            # $ Store the item's json-dictionary
            filename = filepath.split("/")[-1]
            if "board" in filename:
                self.__overrides_db["board"][item_name] = item_dict
            elif "chip" in filename:
                self.__overrides_db["chip"][item_name] = item_dict
            elif "probe" in filename:
                self.__overrides_db["probe"][item_name] = item_dict
            else:
                purefunctions.printc(
                    f"\nERROR: Json-file bad name: {q}{filepath}{q}!\n",
                    color="error",
                )
            continue
        return

    # ^                                       STANDARDIZE NAMES                                        ^#
    # % ============================================================================================== %#
    # %                                                                                                %#
    # %                                                                                                %#

    def standardize_boardfam_name(self, name: str) -> str:
        """Standardize given boardfamily name.

        Raise a RuntimeError() if it doesn't exist.
        """
        if (
            (name is None)
            or (name.lower() == "none")
            or (name.lower() == "custom")
        ):
            return "custom"
        name = name.lower().replace(" ", "-").replace("_", "-").strip()
        if name in self.__boardfam_lookup.keys():
            return name
        if name in self.__boardfam_synonyms.keys():
            return self.__boardfam_synonyms[name]
        raise RuntimeError(f"Boardfamily {q}{name}{q} unknown!")

    def standardize_board_name(self, name: str) -> str:
        """Standardize given boardname.

        Raise a RuntimeError() if it doesn't exist.
        """
        if (
            (name is None)
            or (name.lower() == "none")
            or (name.lower() == "custom")
        ):
            return "custom"
        name = name.lower().replace(" ", "-").replace("_", "-").strip()
        if name in self.__board_lookup.keys():
            return name
        if name in self.__board_synonyms.keys():
            return self.__board_synonyms[name]
        raise RuntimeError(f"Board {q}{name}{q} unknown!")

    def standardize_chipfam_name(self, name: str) -> str:
        """Standardize given chipfamily name.

        Raise a RuntimeError() if it doesn't exist.
        """
        if (
            (name is None)
            or (name.lower() == "none")
            or (name.lower() == "custom")
        ):
            return "custom"
        name = name.lower().replace(" ", "-").replace("_", "-").strip()
        if name in self.__chipfam_lookup.keys():
            return name
        if name in self.__chipfam_synonyms.keys():
            return self.__chipfam_synonyms[name]
        raise RuntimeError(f"Chipfamily {q}{name}{q} unknown!")

    def standardize_chip_name(self, name: str) -> str:
        """Standardize given chipname.

        Raise a RuntimeError() if it doesn't exist.
        """
        if (
            (name is None)
            or (name.lower() == "none")
            or (name.lower() == "custom")
        ):
            return "custom"
        name = name.lower().replace(" ", "-").replace("_", "-").strip()
        if name in self.__chip_lookup.keys():
            return name
        if name in self.__chip_synonyms.keys():
            return self.__chip_synonyms[name]
        raise RuntimeError(f"Chip {q}{name}{q} unknown!")

    def standardize_probe_name(self, name: str) -> str:
        """Standardize given probename.

        Raise a RuntimeError() if it doesn't exist.
        """
        if (
            (name is None)
            or (name.lower() == "none")
            or (name.lower() == "custom")
        ):
            return "custom"
        name = name.lower().replace(" ", "-").replace("_", "-").strip()
        if name in self.__probe_lookup.keys():
            return name
        if name in self.__probe_synonyms.keys():
            return self.__probe_synonyms[name]
        raise RuntimeError(f"Probe {q}{name}{q} unknown!")

    def standardize_tp_name(self, name: str) -> str:
        """Standardize given transport protocol name.

        Raise a RuntimeError() if it doesn't exist.
        """
        if (
            (name is None)
            or (name.lower() == "none")
            or (name.lower() == "custom")
        ):
            return "custom"
        name = name.lower().replace(" ", "-").replace("_", "-").strip()
        if name in self.__hardware_db["probe"]["transport_protocol"]:
            return name
        raise RuntimeError(f"Transport protocol {q}{name}{q} unknown!")

    def standardize_manufacturer_name(self, name: str) -> str:
        """Standardize given manufacturer name.

        Raise a RuntimeError() if it doesn't exist.
        """
        if (
            (name is None)
            or (name.lower() == "none")
            or (name.lower() == "custom")
        ):
            return "custom"
        name = name.lower().replace(" ", "-").replace("_", "-").strip()
        if name in self.__hardware_db["manufacturer"].keys():
            return name
        raise RuntimeError(f"Manufacturer {q}{name}{q} unknown!")

    def standardize_treepath_name(self, name: str) -> str:
        """Standardize given treepath unicum name.

        Raise a RuntimeError() if it doesn't exist.
        """
        if (name is None) or (name.lower() == "none"):
            raise RuntimeError(f"TREEPATH_UNIC name {q}{name}{q} unknown!")
        name = name.upper().replace("-", "_").replace(" ", "_").strip()
        if (
            name
            in self.__hardware_db["project-layout"]["makefile-based"].keys()
        ):
            return name
        raise RuntimeError(f"TREEPATH_UNIC name {q}{name}{q} unknown!")

    def standardize_toolcat_name(self, name: str) -> str:
        """"""
        if (name is None) or (name.lower() == "none"):
            raise RuntimeError(f"TOOLCAT_UNIC name {q}{name}{q} unknown!")
        name = name.upper().replace("-", "_").replace(" ", "_").strip()
        if name in self.__hardware_db["tool-categories"].keys():
            return name
        raise RuntimeError(f"TOOLCAT_UNIC name {q}{name}{q} unknown!")

    # ^                                      DICTIONARY GETTERS                                        ^#
    # % ============================================================================================== %#
    # %                                                                                                %#
    # %                                                                                                %#

    def get_board_dict(self, board: str) -> Optional[Dict[str, Any]]:
        """Get the json-dictionary for the given board."""
        # $ Obtain board dictionary
        # Copy the dictionary to avoid modifying the original database!
        board = self.standardize_board_name(board)
        mf = self.__board_lookup[board]["manufacturer"]
        boardfam = self.__board_lookup[board]["boardfamily"]
        board_dict = copy.deepcopy(
            self.__hardware_db["board"][mf][boardfam][board]
        )
        # $ Override with local 'board.json5'
        if board in self.__overrides_db["board"].keys():
            board_dict.update(self.__overrides_db["board"][board])
        return board_dict

    def get_boardfam_dict(self, boardfam: str) -> Optional[Dict[str, Any]]:
        """Get the json-dictionary for the given boardfamily."""
        # $ Obtain board family dictionary
        # Copy the dictionary to avoid modifying the original database!
        boardfam = self.standardize_boardfam_name(boardfam)
        mf = self.__boardfam_lookup[boardfam]["manufacturer"]
        return copy.deepcopy(
            self.__hardware_db["board"][mf][boardfam]["family"]
        )

    def get_chip_dict(
        self, chip: str, board: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Get the json-dictionary for the given chip.

        Apply board overrides if a board is given.
        """
        # $ Obtain chip dictionary
        # Copy the dictionary to avoid modifying the original database!
        chip = self.standardize_chip_name(chip)
        mf = self.__chip_lookup[chip]["manufacturer"]
        chipfam = self.__chip_lookup[chip]["chipfamily"]
        chip_dict = copy.deepcopy(self.__hardware_db["chip"][mf][chipfam][chip])
        # $ Override with local 'chip.json5'
        if chip in self.__overrides_db["chip"].keys():
            chip_dict.update(self.__overrides_db["chip"][chip])
        # $ Override with board file
        if board is None:
            return chip_dict
        board_dict = self.get_board_dict(board)
        return override_dict(chip_dict, board_dict)

    def get_chipfam_dict(self, chipfam: str) -> Optional[Dict[str, Any]]:
        """Get the json-dictionary for the given chipfamily."""
        # $ Obtain chip family dictionary
        # Copy the dictionary to avoid modifying the original database!
        chipfam = self.standardize_chipfam_name(chipfam)
        mf = self.__chipfam_lookup[chipfam]["manufacturer"]
        return copy.deepcopy(self.__hardware_db["chip"][mf][chipfam]["family"])

    def get_probe_dict(self, probe: str) -> Optional[Dict[str, Any]]:
        """Get the json-dictionary for the given probe."""
        # $ Obtain the probe dictionary
        # Copy the dictionary to avoid modifying the original database!
        probe = self.standardize_probe_name(probe)
        mf = self.__probe_lookup[probe]["manufacturer"]
        probe_dict = copy.deepcopy(self.__hardware_db["probe"][mf][probe])
        # $ Override with local 'probe.json5'
        if probe in self.__overrides_db["probe"].keys():
            probe_dict.update(self.__overrides_db["probe"][probe])
        return probe_dict

    def get_manufacturer_dict(self, mf: str) -> Optional[Dict[str, Any]]:
        """Get the json-dictionary for the given manufacturer."""
        mf = self.standardize_manufacturer_name(mf)
        return copy.deepcopy(self.__hardware_db["manufacturer"][mf])

    def get_project_layout_dict(self, treepath_name: str) -> Dict[str, Any]:
        """Get the json-dictionary for the given treepath unicum."""
        return copy.deepcopy(
            self.__hardware_db["project-layout"]["makefile-based"][
                treepath_name
            ]
        )

    def get_toolcat_dict(self, toolcat: str) -> Dict[str, Any]:
        """Get the json-dictionary for the given tool category."""
        return copy.deepcopy(self.__hardware_db["tool-categories"][toolcat])

    # ^                                             LISTINGS                                           ^#
    # % ============================================================================================== %#
    # %                                                                                                %#
    # %                                                                                                %#

    #! ----------------------------------------[ LIST BOARDS ]--------------------------------------- !#

    def list_boardfamilies(
        self,
        manufacturer_list: Optional[List[str]] = None,
        return_unicums: bool = False,
    ) -> Union[List[str], List[_board_unicum_.BOARDFAMILY]]:
        """List all boardfamilies for the given manufacturers.

        If no manufacturers are given, just list all boardfamilies.
        """
        # & CASE 1: No manufacturer(s) given
        # Just return *all* boardfamilies
        if (manufacturer_list is None) or (len(manufacturer_list) == 0):
            boardfam_list = list(self.__boardfam_lookup.keys())
            if return_unicums:
                return [_board_unicum_.BOARDFAMILY(b) for b in boardfam_list]
            return boardfam_list

        # & CASE 2: Manufacturer(s) given
        # Return the boardfamilies produced by the given manufacturers
        assert manufacturer_list is not None
        for mf in manufacturer_list:
            assert isinstance(mf, str)
        manufacturer_list = [
            self.standardize_manufacturer_name(mf) for mf in manufacturer_list
        ]
        boardfam_list = [
            boardfam
            for boardfam in self.__boardfam_lookup.keys()
            if self.__boardfam_lookup[boardfam]["manufacturer"]
            in manufacturer_list
        ]
        if return_unicums:
            return [_board_unicum_.BOARDFAMILY(b) for b in boardfam_list]
        return boardfam_list

    def list_boards(
        self,
        boardfam_list: Optional[List[str]] = None,
        boardmf_list: Optional[List[str]] = None,
        chip_list: Optional[List[str]] = None,
        return_unicums: bool = False,
    ) -> Union[List[str], List[_board_unicum_.BOARD]]:
        """List all boards that pass the given filters.

        NOTE:
        self.__overrides_db is ignored in the lookup process, as the parameters being checked for
        are of a very fundamental nature, which shouldn't be overridden anyhow.
        """

        # & Sanitize input
        if boardfam_list is not None:
            boardfam_list = [
                self.standardize_boardfam_name(boardfam)
                for boardfam in boardfam_list
            ]
        if boardmf_list is not None:
            boardmf_list = [
                self.standardize_manufacturer_name(mf) for mf in boardmf_list
            ]
        if chip_list is not None:
            chip_list = [self.standardize_chip_name(chip) for chip in chip_list]

        # & Construct list
        board_list: List[str] = []
        for mf in self.__hardware_db["board"].keys():
            if (boardmf_list is not None) and (mf not in boardmf_list):
                continue
            for boardfam in self.__hardware_db["board"][mf].keys():
                if (boardfam_list is not None) and (
                    boardfam not in boardfam_list
                ):
                    continue
                boardfam_dict = self.__hardware_db["board"][mf][boardfam][
                    "family"
                ]
                for board in self.__hardware_db["board"][mf][boardfam].keys():
                    if board == "family":
                        continue
                    board_dict = self.__hardware_db["board"][mf][boardfam][
                        board
                    ]
                    if (chip_list is not None) and (
                        board_dict["chip"] not in chip_list
                    ):
                        continue
                    board_list.append(board)
                    continue
                continue
            continue
        if return_unicums:
            return [_board_unicum_.BOARD(b) for b in board_list]
        return board_list

    #! ----------------------------------------[ LIST CHIPS ]---------------------------------------- !#

    def list_chipfamilies(
        self,
        manufacturer_list: Optional[List[str]] = None,
        return_unicums: bool = False,
    ) -> Union[List[str], List[_chip_unicum_.CHIPFAMILY]]:
        """List all chipfamilies for the given manufacturers.

        If no manufacturers are given, just list
        all chipfamilies.
        NOTE:
        self.__overrides_db is ignored in the lookup process, as the parameters being checked for
        are of a very fundamental nature, which shouldn't be overridden anyhow.
        """
        # & CASE 1: No manufacturer(s) given
        # Just return *all* chipfamilies
        if (manufacturer_list is None) or (len(manufacturer_list) == 0):
            chipfam_list = list(self.__chipfam_lookup.keys())
            if return_unicums:
                return [_chip_unicum_.CHIPFAMILY(c) for c in chipfam_list]
            return chipfam_list

        # & CASE 2: Manufacturer(s) given
        # Return the chipfamilies produced by the given manufacturers
        assert manufacturer_list is not None
        for mf in manufacturer_list:
            assert isinstance(mf, str)
        manufacturer_list = [
            self.standardize_manufacturer_name(mf) for mf in manufacturer_list
        ]
        chipfam_list = [
            chipfam
            for chipfam in self.__chipfam_lookup.keys()
            if self.__chipfam_lookup[chipfam]["manufacturer"]
            in manufacturer_list
        ]
        if return_unicums:
            return [_chip_unicum_.CHIPFAMILY(c) for c in chipfam_list]
        return chipfam_list

    def list_chips(
        self,
        chipfam_list: Optional[List[str]] = None,
        chipmf_list: Optional[List[str]] = None,
        return_unicums: bool = False,
    ) -> Union[List[str], List[_chip_unicum_.CHIP]]:
        """List all chips from the given manufacturer(s) and chipfamil(y)(ies).

        NOTE:
        self.__overrides_db is ignored in the lookup process, as the parameters being checked for
        are of a very fundamental nature, which shouldn't be overridden anyhow.
        """
        # & Sanitize input
        if chipfam_list is not None:
            chipfam_list = [
                self.standardize_chipfam_name(chipfam)
                for chipfam in chipfam_list
            ]
        if chipmf_list is not None:
            chipmf_list = [
                self.standardize_manufacturer_name(mf) for mf in chipmf_list
            ]

        # & Construct list
        chip_list = [
            chip
            for chip in self.__chip_lookup.keys()
            if (
                (chipfam_list is None)
                or (len(chipfam_list) == 0)
                or (self.__chip_lookup[chip]["chipfamily"] in chipfam_list)
            )
            and (
                (chipmf_list is None)
                or (len(chipmf_list) == 0)
                or (self.__chip_lookup[chip]["manufacturer"] in chipmf_list)
            )
        ]
        if return_unicums:
            return [_chip_unicum_.CHIP(c) for c in chip_list]
        return chip_list

    #! ------------------------------------[ LIST MANUFACTURERS ]------------------------------------ !#

    def list_manufacturers(
        self,
        for_boards: bool = False,
        for_chips: bool = False,
        for_probes: bool = False,
        return_unicums: bool = False,
    ) -> Union[List[str], List[_manufacturer_unicum_.MANUFACTURER]]:
        """List all manufacturers of boards, chips and probes.

        NOTE:
        self.__overrides_db is ignored in the lookup process, as the parameters being checked for
        are of a very fundamental nature, which shouldn't be overridden anyhow.
        """
        # & CASE 1: No filters given, or all are True
        # Just return *all* manufacturers
        if (not for_boards) and (not for_chips) and (not for_probes):
            mf_list = sorted(list(self.__hardware_db["manufacturer"].keys()))
            if return_unicums:
                return [
                    _manufacturer_unicum_.MANUFACTURER(mf) for mf in mf_list
                ]
            return mf_list
        if for_boards and for_chips and for_probes:
            mf_list = sorted(list(self.__hardware_db["manufacturer"].keys()))
            if return_unicums:
                return [
                    _manufacturer_unicum_.MANUFACTURER(mf) for mf in mf_list
                ]
            return mf_list

        # & CASE 2: Some filters given
        # $ Board manufacturers
        board_mfs = []
        if for_boards:
            board_mfs = list(self.__hardware_db["board"].keys())

        # $ Chip manufacturers
        chip_mfs = []
        if for_chips:
            chip_mfs = list(self.__hardware_db["chip"].keys())

        # $ Probe manufacturers
        probe_mfs = []
        if for_probes:
            probe_mfs = [
                mf
                for mf in self.__hardware_db["probe"].keys()
                if mf != "transport_protocol"
            ]

        # $ Return list
        mf_list = sorted(list(set(board_mfs + chip_mfs + probe_mfs)))
        if return_unicums:
            return [_manufacturer_unicum_.MANUFACTURER(mf) for mf in mf_list]
        return mf_list

    #! ---------------------------------------[ LIST PROBES ]---------------------------------------- !#

    def list_probes(
        self,
        manufacturer_list: Optional[List[str]] = None,
        return_unicums: bool = False,
    ) -> Union[List[str], List[_probe_unicum_.PROBE]]:
        """List all probes from the given manufacturer.

        NOTE:
        self.__overrides_db is ignored in the lookup process, as the parameters being checked for
        are of a very fundamental nature, which shouldn't be overridden anyhow.
        """
        # & CASE 1: No manufacturer(s) given
        # Just return *all* probes
        if (manufacturer_list is None) or (len(manufacturer_list) == 0):
            probe_list = list(self.__probe_lookup.keys())
            if return_unicums:
                return [_probe_unicum_.PROBE(p) for p in probe_list]
            return probe_list

        # & CASE 2: Manufacturer(s) given
        # Return the probes produced by the given manufacturers
        assert manufacturer_list is not None
        for mf in manufacturer_list:
            assert isinstance(mf, str)
        manufacturer_list = [
            self.standardize_manufacturer_name(mf) for mf in manufacturer_list
        ]
        probe_list = [
            probe
            for probe in self.__probe_lookup.keys()
            if self.__probe_lookup[probe]["manufacturer"] in manufacturer_list
        ]
        if return_unicums:
            return [_probe_unicum_.PROBE(p) for p in probe_list]
        return probe_list

    def list_tps(
        self,
        return_unicums: bool = False,
    ) -> Union[List[str], List[_probe_unicum_.TRANSPORT_PROTOCOL]]:
        """List all transport protocols."""
        tp_list: List[str] = sorted(
            self.__hardware_db["probe"]["transport_protocol"]
        )
        if return_unicums:
            return [_probe_unicum_.TRANSPORT_PROTOCOL(tp) for tp in tp_list]
        return tp_list

    def list_treepath_unicums(
        self,
        return_unicums: bool = False,
    ) -> Union[List[str], List[_treepath_unicum_.TREEPATH_UNIC]]:
        """List all treepath unicums."""
        treepath_unicum_list: List[str] = sorted(
            list(self.__hardware_db["project-layout"]["makefile-based"].keys())
        )
        if return_unicums:
            return [
                _treepath_unicum_.TREEPATH_UNIC(u) for u in treepath_unicum_list
            ]
        return treepath_unicum_list

    def list_toolcat_unicums(
        self,
        return_unicums: bool = False,
    ) -> Union[List[str], List[_toolcat_unicum_.TOOLCAT_UNIC]]:
        """List all toolcat unicums."""
        toolcat_unicum_list: List[str] = sorted(
            list(self.__hardware_db["tool-categories"].keys())
        )
        if return_unicums:
            return [
                _toolcat_unicum_.TOOLCAT_UNIC(u) for u in toolcat_unicum_list
            ]
        return toolcat_unicum_list

    # ^                                        FILL LOOKUP TABLES                                      ^#
    # % ============================================================================================== %#
    # %                                                                                                %#
    # %                                                                                                %#

    def __fill_lookup_tables(self) -> None:
        """"""
        assert self.__board_lookup is None
        assert self.__chip_lookup is None
        assert self.__probe_lookup is None
        assert self.__chip_synonyms is None
        assert self.__board_synonyms is None
        assert self.__probe_synonyms is None
        assert self.__boardfam_synonyms is None
        assert self.__chipfam_synonyms is None
        self.__fill_board_lookup_table()
        self.__fill_chip_lookup_table()
        self.__fill_probe_lookup_table()
        self.__fill_board_synonyms()
        self.__fill_chip_synonyms()
        self.__fill_probe_synonyms()
        self.__fill_boardfam_synonyms()
        self.__fill_chipfam_synonyms()
        return

    def __fill_board_lookup_table(self) -> None:
        """
        NOTE:
        self.__overrides_db is ignored in the lookup process, as the parameters being checked for
        are of a very fundamental nature, which shouldn't be overridden anyhow.
        """
        assert self.__board_lookup is None
        assert self.__boardfam_lookup is None
        self.__board_lookup = {}
        self.__boardfam_lookup = {}
        for mf in self.__hardware_db["board"].keys():
            for boardfam in self.__hardware_db["board"][mf].keys():
                assert boardfam not in self.__boardfam_lookup.keys()
                self.__boardfam_lookup[boardfam] = {
                    "manufacturer": mf,
                }
                assert (
                    mf
                    == self.__hardware_db["board"][mf][boardfam]["family"][
                        "manufacturer"
                    ]
                )
                for board in self.__hardware_db["board"][mf][boardfam].keys():
                    if board == "family":
                        continue
                    assert board not in self.__board_lookup.keys()
                    self.__board_lookup[board] = {
                        "boardfamily": boardfam,
                        "manufacturer": mf,
                    }
                    assert (
                        boardfam
                        == self.__hardware_db["board"][mf][boardfam][board][
                            "boardfamily"
                        ]
                    )
                    assert (
                        mf
                        == self.__hardware_db["board"][mf][boardfam][board][
                            "manufacturer"
                        ]
                    )
                    continue
                continue
            continue
        return

    def __fill_chip_lookup_table(self) -> None:
        """
        NOTE:
        self.__overrides_db is ignored in the lookup process, as the parameters being checked for
        are of a very fundamental nature, which shouldn't be overridden anyhow.
        """
        assert self.__chip_lookup is None
        assert self.__chipfam_lookup is None
        self.__chip_lookup = {}
        self.__chipfam_lookup = {}
        for mf in self.__hardware_db["chip"].keys():
            for chipfam in self.__hardware_db["chip"][mf].keys():
                assert chipfam not in self.__chipfam_lookup.keys()
                self.__chipfam_lookup[chipfam] = {
                    "manufacturer": mf,
                }
                assert (
                    mf
                    == self.__hardware_db["chip"][mf][chipfam]["family"][
                        "manufacturer"
                    ]
                )
                for chip in self.__hardware_db["chip"][mf][chipfam].keys():
                    if chip == "family":
                        continue
                    assert chip not in self.__chip_lookup.keys()
                    self.__chip_lookup[chip] = {
                        "chipfamily": chipfam,
                        "manufacturer": mf,
                    }
                    assert (
                        chipfam
                        == self.__hardware_db["chip"][mf][chipfam][chip][
                            "chipfamily"
                        ]
                    )
                    assert (
                        mf
                        == self.__hardware_db["chip"][mf][chipfam][chip][
                            "manufacturer"
                        ]
                    )
                    continue
                continue
            continue
        return

    def __fill_probe_lookup_table(self) -> None:
        """
        NOTE:
        self.__overrides_db is ignored in the lookup process, as the parameters being checked for
        are of a very fundamental nature, which shouldn't be overridden anyhow.
        """
        assert self.__probe_lookup is None
        self.__probe_lookup = {}
        for mf in self.__hardware_db["probe"].keys():
            if mf == "transport_protocol":
                continue
            for probe in self.__hardware_db["probe"][mf].keys():
                assert probe not in self.__probe_lookup.keys()
                self.__probe_lookup[probe] = {
                    "manufacturer": mf,
                }
                assert (
                    mf == self.__hardware_db["probe"][mf][probe]["manufacturer"]
                )
                continue
            continue
        return

    def __fill_chip_synonyms(self) -> None:
        """Fill the self.__chip_synonyms dictionary from the main database.

        NOTE:
        self.__overrides_db is ignored in the lookup process, as the parameters being checked for
        are of a very fundamental nature, which shouldn't be overridden anyhow.
        """
        assert self.__chip_synonyms is None
        self.__chip_synonyms = {}
        for mf in self.__hardware_db["chip"].keys():
            for chipfam in self.__hardware_db["chip"][mf].keys():
                for chip in self.__hardware_db["chip"][mf][chipfam].keys():
                    if chip == "family":
                        continue
                    for synonym in self.__hardware_db["chip"][mf][chipfam][
                        chip
                    ]["synonyms"]:
                        self.__chip_synonyms[synonym] = chip
                        continue
                    continue
                continue
            continue
        return

    def __fill_board_synonyms(self) -> None:
        """Fill the self.__board_synonyms dictionary from the main database.

        NOTE:
        self.__overrides_db is ignored in the lookup process, as the parameters being checked for
        are of a very fundamental nature, which shouldn't be overridden anyhow.
        """
        assert self.__board_synonyms is None
        self.__board_synonyms = {}
        for mf in self.__hardware_db["board"].keys():
            for boardfam in self.__hardware_db["board"][mf].keys():
                for board in self.__hardware_db["board"][mf][boardfam].keys():
                    if board == "family":
                        continue
                    for synonym in self.__hardware_db["board"][mf][boardfam][
                        board
                    ]["synonyms"]:
                        self.__board_synonyms[synonym] = board
                        continue
                    continue
                continue
            continue
        return

    def __fill_probe_synonyms(self) -> None:
        """Fill the self.__probe_synonyms dictionary from the main database.

        NOTE:
        self.__overrides_db is ignored in the lookup process, as the parameters being checked for
        are of a very fundamental nature, which shouldn't be overridden anyhow.
        """
        assert self.__probe_synonyms is None
        self.__probe_synonyms = {}
        for mf in self.__hardware_db["probe"].keys():
            if mf == "transport_protocol":
                continue
            for probe in self.__hardware_db["probe"][mf].keys():
                for synonym in self.__hardware_db["probe"][mf][probe][
                    "synonyms"
                ]:
                    self.__probe_synonyms[synonym] = probe
                    continue
                continue
            continue
        return

    def __fill_boardfam_synonyms(self) -> None:
        """Fill the self.__boardfam_synonyms dictionary from the main database.

        NOTE:
        self.__overrides_db is ignored in the lookup process, as the parameters being checked for
        are of a very fundamental nature, which shouldn't be overridden anyhow.
        """
        assert self.__boardfam_synonyms is None
        self.__boardfam_synonyms = {}
        for mf in self.__hardware_db["board"].keys():
            for boardfam in self.__hardware_db["board"][mf].keys():
                for synonym in self.__hardware_db["board"][mf][boardfam][
                    "family"
                ]["synonyms"]:
                    self.__boardfam_synonyms[synonym] = boardfam
                    continue
                continue
            continue
        return

    def __fill_chipfam_synonyms(self) -> None:
        """Fill the self.__chipfam_synonyms dictionary from the main database.

        NOTE:
        self.__overrides_db is ignored in the lookup process, as the parameters being checked for
        are of a very fundamental nature, which shouldn't be overridden anyhow.
        """
        assert self.__chipfam_synonyms is None
        self.__chipfam_synonyms = {}
        for mf in self.__hardware_db["chip"].keys():
            for chipfam in self.__hardware_db["chip"][mf].keys():
                for synonym in self.__hardware_db["chip"][mf][chipfam][
                    "family"
                ]["synonyms"]:
                    self.__chipfam_synonyms[synonym] = chipfam
                    continue
                continue
            continue
        return
