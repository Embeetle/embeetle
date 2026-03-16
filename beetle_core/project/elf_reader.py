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
from components.singleton import Singleton
import os, sys, data, traceback, functools
import qt
import project.readelf as _re_

if TYPE_CHECKING:
    import io


class ElfReader(metaclass=Singleton):

    def __init__(self) -> None:
        """"""
        super().__init__()
        self.__elffile: Optional[io.BufferedReader] = None
        self.__readelf: Optional[_re_.ReadElf] = None
        pass

    def open(self, elf_abspath: Optional[str] = None) -> bool:
        """Open the elffile, and keep a reference to it. Create a
        'ReadElf()'-instance and give it the opened elffile (to serve as an
        input stream).

        Note: Elffile location is taken from 'data.current_project'.

        Return True if successfull.
        """
        assert not self.is_open()
        if elf_abspath is None:
            elf_abspath = data.current_project.get_treepath_seg().get_abspath(
                "ELF_FILE"
            )
        if (elf_abspath is None) or (elf_abspath.lower() == "none"):
            return False
        if not os.path.isfile(elf_abspath):
            return False
        assert os.path.isfile(elf_abspath)
        try:
            self.__elffile = open(elf_abspath, "rb")
            self.__readelf = _re_.ReadElf(self.__elffile, sys.stdout)
        except:
            error_txt = traceback.format_exc()

            if data.source_analysis_only:
                txt = f"ERROR: Cannot parse elf file at '{elf_abspath}'\n"
                txt += error_txt
                txt += "\n\n"
                with open("elf_reader_error.txt", "a") as file:
                    file.write(txt)
                return False
            import helpdocs.help_texts as _ht_

            print("")
            print(
                f"---------------------------------------------------------------"
            )
            print(f"ERROR: Cannot parse elf file at '{elf_abspath}'")
            print(error_txt)
            print(
                f"---------------------------------------------------------------"
            )
            print("")
            qt.QTimer.singleShot(
                1000,
                functools.partial(
                    _ht_.cannot_parse_elf_file,
                    elf_abspath,
                    error_txt,
                ),
            )
            # _ht_.cannot_parse_elf_file(elf_abspath, error_txt)
            self.__elffile = None
            self.__readelf = None
            return False
        return True

    def close(self) -> None:
        """Close the elffile and destroy the 'ReadElf()'-instance linked to
        it."""
        assert self.is_open()
        assert self.__elffile is not None
        assert self.__readelf is not None
        self.__elffile.close()
        self.__elffile = None
        self.__readelf = None
        return

    def is_open(self) -> bool:
        """"""
        if self.__elffile is not None:
            assert self.__readelf is not None
            return True
        assert self.__readelf is None
        return False

    def test(self) -> None:
        """"""
        print(
            "--------------------------------------------------------------------------"
        )
        self.__readelf.display_section_headers(show_heading=True)
        print(
            "--------------------------------------------------------------------------"
        )
        return

    def get_memsection_usage(self, name: str) -> int:
        """"""
        usage: Union[int, str] = 0
        try:
            usage = self.__readelf.get_memsection_usage(name)
        except:
            print(traceback.format_exc())
        if isinstance(usage, str):
            # print warning:
            # print(usage)
            return 0
        assert isinstance(usage, int)
        return usage
