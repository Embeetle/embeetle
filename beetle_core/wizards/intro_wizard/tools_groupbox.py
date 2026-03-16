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
import qt, data, iconfunctions
import gui.templates.paintedgroupbox
import project.segments.path_seg.toolpath_seg as _toolpath_seg_

if TYPE_CHECKING:
    pass


class ToolsGroupbox(
    gui.templates.paintedgroupbox.PaintedGroupBoxWithLayoutAndInfoButton
):
    def __init__(
        self,
        parent: Optional[qt.QWidget] = None,
        title: Optional[str] = None,
        fake_toolpath_seg: Optional[_toolpath_seg_.ToolpathSeg] = None,
        categories: Optional[List[str]] = None,
        show_all: bool = False,
        report: Optional[Dict] = None,
    ) -> None:
        """"""
        self.__categories = categories
        if title is None:
            title = "Tools:"
        super().__init__(
            parent=parent,
            name="tools",
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
        self.__fake_toolpath_seg = fake_toolpath_seg

        # * ToolpathItem()s
        vlyt = qt.QVBoxLayout()
        if not show_all:
            # This is the intro wizard at startup
            h = data.get_general_font_height()
            cloud_icon = iconfunctions.get_rich_text_pixmap_middle(
                pixmap_relpath="icons/gen/download.png",
                width=h,
            )
            info_lbl = qt.QLabel(
                f"""
            <p>
                The tools listed below are used by this project but not available on this computer.
                <ul>
                    <li>
                        To download the missing tools, press APPLY.
                    </li>
                    <li>
                        To use an alternative tool, select the desired tool from the drop-down list
                        and press APPLY. Tools shown in red are not compatible with this project.
                    </li>
                    <li>
                        To postpone tool selection, press SKIP. The desired tool can be selected
                        later in the project's dashboard.
                    </li>
                </ul>
            </p>
            """
            )
            info_lbl.setFont(data.get_general_font())
            info_lbl.setStyleSheet(
                f"""
                QLabel {{
                    text-align: justify;
                    background-color: transparent;
                    color: {data.theme['fonts']['default']['color']};
                    font-family: {data.get_global_font_family()};
                    font-size: {data.get_general_font_pointsize()}pt;
                    margin: 0px;
                    padding: 0px;
                }}
            """
            )
            info_lbl.setWordWrap(True)
            vlyt.addWidget(info_lbl)
        vlyt.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        vlyt.setSpacing(20)
        vlyt.setContentsMargins(0, 0, 0, 0)
        self.__fake_toolpath_seg.show_on_intro_wizard(
            vlyt=vlyt,
            categories=categories,
            show_all=show_all,
            report=report,
            callback=None,
            callbackArg=None,
        )
        cast(qt.QVBoxLayout, self.layout()).addLayout(vlyt)
        return

    def get_categories(self) -> List[str]:
        """"""
        return self.__categories
