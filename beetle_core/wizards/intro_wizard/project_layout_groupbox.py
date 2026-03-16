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
import qt
import gui.templates.paintedgroupbox

if TYPE_CHECKING:
    import project.segments.path_seg.treepath_seg as _treepath_seg_


class ProjectLayoutGroupbox(
    gui.templates.paintedgroupbox.PaintedGroupBoxWithLayoutAndInfoButton
):

    def __init__(
        self,
        parent: Optional[qt.QWidget] = None,
        title: Optional[str] = None,
        fake_treepath_seg: Optional[_treepath_seg_.TreepathSeg] = None,
        names: Optional[List[str]] = None,
        show_all: bool = False,
    ) -> None:
        """"""
        self.__unicum_names = names
        if title is None:
            title = "Project Layout:"
        super().__init__(
            parent=parent,
            name="project_layout",
            text=title,
            info_func=None,
            h_size_policy=qt.QSizePolicy.Policy.Expanding,
            v_size_policy=qt.QSizePolicy.Policy.Maximum,
        )
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Maximum,
        )
        self.layout().setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.layout().setContentsMargins(10, 10, 10, 10)
        self.layout().setSpacing(0)

        self.__fake_treepath_seg = fake_treepath_seg

        # * TreepathItem()s
        vlyt = qt.QVBoxLayout()
        vlyt.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        vlyt.setSpacing(0)
        vlyt.setContentsMargins(0, 0, 0, 0)
        self.__fake_treepath_seg.show_on_intro_wizard(
            vlyt=vlyt,
            names=names,
            show_all=show_all,
            callback=None,
            callbackArg=None,
        )
        cast(qt.QVBoxLayout, self.layout()).addLayout(vlyt)
        return

    def get_unicum_names(self) -> List[str]:
        """"""
        return self.__unicum_names
