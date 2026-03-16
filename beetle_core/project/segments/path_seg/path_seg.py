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
import project.segments.project_segment as _ps_
import hardware_api.treepath_unicum as _treepath_unicum_
import hardware_api.toolcat_unicum as _toolcat_unicum_

"""
                              ╔════════════════════╗
                              ║     PathSeg()      ║
                              ╚═════════╤══════════╝
             ┌──────────────────────────┴─────────────────────────┐
             ↓                                                    ↓
    ┌────────────────────┐                              ┌────────────────────┐
    │   TreepathSeg()    │                              │   ToolpathSeg()    │
    └────────────────────┘                              └────────────────────┘
    - TreepathObj()                                      - ToolpathObj()
    - TreepathObj()                                      - ToolpathObj()
    - TreepathObj()                                      - ToolpathObj()
    - ...                                                - ...
                                                         
    Each:                                               Each:
      -> encapsulates a TREEPATH_UNIC() Unicum             -> is a shell for the corresponding ToolmanObj()
      -> holds one TreepathItem() for dashboard            -> holds one ToolpathItem() for dashboard
        
"""


class PathSeg(_ps_.ProjectSegment):

    __slots__ = ()

    def __init__(self, is_fake: bool) -> None:
        """"""
        super().__init__(is_fake)
        return

    def get_relpath(
        self,
        unicum: Union[
            str, _treepath_unicum_.TREEPATH_UNIC, _toolcat_unicum_.TOOLCAT_UNIC
        ],
    ) -> str:
        """"""
        raise NotImplementedError()

    def get_abspath(
        self,
        unicum: Union[
            str, _treepath_unicum_.TREEPATH_UNIC, _toolcat_unicum_.TOOLCAT_UNIC
        ],
    ) -> str:
        """"""
        raise NotImplementedError()

    def set_relpath(
        self,
        unicum: Union[
            str, _treepath_unicum_.TREEPATH_UNIC, _toolcat_unicum_.TOOLCAT_UNIC
        ],
        relpath: Optional[str],
        history: bool,
        **kwargs,
    ) -> None:
        """"""
        raise RuntimeError()

    def set_abspath(
        self,
        unicum: Union[
            str, _treepath_unicum_.TREEPATH_UNIC, _toolcat_unicum_.TOOLCAT_UNIC
        ],
        abspath: str,
        history: bool,
        **kwargs,
    ) -> None:
        """"""
        raise RuntimeError()
