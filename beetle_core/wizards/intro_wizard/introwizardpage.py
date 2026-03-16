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
import sys
import qt, data
import wizards.intro_wizard.board_groupbox as _board_groupbox_
import wizards.intro_wizard.chip_groupbox as _chip_groupbox_
import wizards.intro_wizard.probe_groupbox as _probe_groupbox_
import wizards.intro_wizard.project_layout_groupbox as _project_layout_groupbox_
import wizards.intro_wizard.tools_groupbox as _tools_groupbox_

if TYPE_CHECKING:
    import project.segments.board_seg.board as _board_
    import project.segments.chip_seg.chip as _chip_
    import project.segments.probe_seg.probe as _probe_
    import project.segments.path_seg.treepath_seg as _treepath_seg_
    import project.segments.path_seg.toolpath_seg as _toolpath_seg_


class IntroWizardPage(qt.QFrame):
    def __init__(
        self,
        parent,
        project_report: Optional[Dict],
    ) -> None:
        """"""
        super().__init__(parent)  # noqa
        self.__dead = False
        self.__project_report = project_report
        self.__lyt = qt.QVBoxLayout(self)
        self.__lyt.setSpacing(0)
        self.__lyt.setContentsMargins(0, 0, 0, 0)
        self.__lyt.setAlignment(qt.Qt.AlignmentFlag.AlignTop)

        self.__fake_board: Optional[_board_.Board] = None
        self.__fake_chip: Optional[_chip_.Chip] = None
        self.__fake_probe: Optional[_probe_.Probe] = None
        self.__fake_treepath_seg: Optional[_treepath_seg_.TreepathSeg] = None
        self.__fake_toolpath_seg: Optional[_toolpath_seg_.ToolpathSeg] = None

        self.__board_groupbox: Optional[_board_groupbox_.BoardGroupBox] = None
        self.__chip_groupbox: Optional[_chip_groupbox_.ChipGroupBox] = None
        self.__probe_groupbox: Optional[_probe_groupbox_.ProbeGroupBox] = None
        self.__project_layout_groupbox: Optional[
            _project_layout_groupbox_.ProjectLayoutGroupbox
        ] = None
        self.__tools_groupbox: Optional[_tools_groupbox_.ToolsGroupbox] = None
        return

    def init_fake_board(self) -> None:
        """"""
        # $ Specify problems
        # Also show the board if there is a problem with the chip.
        board_problem_lines = []
        chip_problem_lines = []
        if self.__project_report:
            board_report = self.__project_report["board_report"]
            chip_report = self.__project_report["chip_report"]
            for k in board_report.keys():
                if board_report[k]["error"]:
                    line = k
                    board_problem_lines.append(line)
            for k in chip_report.keys():
                if chip_report[k]["error"]:
                    line = k
                    chip_problem_lines.append(line)
            for k in board_report.keys():
                if board_report[k]["warning"]:
                    line = k
                    if line not in board_problem_lines:
                        board_problem_lines.append(line)
            for k in chip_report.keys():
                if chip_report[k]["warning"]:
                    line = k
                    if line not in chip_problem_lines:
                        chip_problem_lines.append(line)
        # $ Show problems
        real_board = data.current_project.get_board()
        self.__fake_board = real_board.clone()
        self.__fake_board.set_fake(True)
        if (
            (len(board_problem_lines) > 0)
            or (len(chip_problem_lines) > 0)
            or (self.__project_report is None)
        ):
            self.__board_groupbox = _board_groupbox_.BoardGroupBox(
                parent=None,
                title=None,
                fake_board=self.__fake_board,
            )
            self.__lyt.addWidget(self.__board_groupbox)
        return

    def init_fake_chip(self) -> None:
        """"""
        # $ Specify problems
        chip_problem_lines = []
        if self.__project_report:
            chip_report = self.__project_report["chip_report"]
            for k in chip_report.keys():
                if chip_report[k]["error"]:
                    line = k
                    chip_problem_lines.append(line)
            for k in chip_report.keys():
                if chip_report[k]["warning"]:
                    line = k
                    if line not in chip_problem_lines:
                        chip_problem_lines.append(line)
        # $ Show problems
        real_chip = data.current_project.get_chip()
        self.__fake_chip = real_chip.clone()
        self.__fake_chip.set_fake(True)
        if (len(chip_problem_lines) > 0) or (self.__project_report is None):
            self.__chip_groupbox = _chip_groupbox_.ChipGroupBox(
                parent=None,
                title=None,
                fake_chip=self.__fake_chip,
            )
            self.__lyt.addWidget(self.__chip_groupbox)
        return

    def init_fake_probe(self) -> None:
        """"""
        # $ Specify problems
        probe_problem_lines = []
        if self.__project_report:
            probe_report = self.__project_report["probe_report"]
            for k in probe_report.keys():
                if probe_report[k]["error"]:
                    line = k
                    probe_problem_lines.append(line)
            for k in probe_report.keys():
                if probe_report[k]["warning"]:
                    line = k
                    if line not in probe_problem_lines:
                        probe_problem_lines.append(line)
        # $ Show problems
        real_probe = data.current_project.get_probe()
        self.__fake_probe = real_probe.clone()
        self.__fake_probe.set_fake(True)
        if (len(probe_problem_lines) > 0) or (self.__project_report is None):
            self.__probe_groupbox = _probe_groupbox_.ProbeGroupBox(
                parent=None,
                title=None,
                fake_probe=self.__fake_probe,
            )
            self.__lyt.addWidget(self.__probe_groupbox)
        return

    def init_fake_project_layout(self) -> None:
        """"""
        # $ Specify problems
        treepath_problem_lines: List[str] = []
        if self.__project_report:
            treepath_report = self.__project_report["treepath_report"]
            for k in treepath_report.keys():
                if treepath_report[k]["error"]:
                    line = k
                    treepath_problem_lines.append(line)
            for k in treepath_report.keys():
                if treepath_report[k]["warning"]:
                    line = k
                    if line not in treepath_problem_lines:
                        treepath_problem_lines.append(line)
        # $ Show problems
        real_treepath_seg = data.current_project.get_treepath_seg()
        self.__fake_treepath_seg = real_treepath_seg.clone()
        self.__fake_treepath_seg.set_fake(True)
        if (len(treepath_problem_lines) > 0) or (self.__project_report is None):
            self.__project_layout_groupbox = (
                _project_layout_groupbox_.ProjectLayoutGroupbox(
                    parent=None,
                    title=None,
                    fake_treepath_seg=self.__fake_treepath_seg,
                    names=treepath_problem_lines,
                    show_all=self.__project_report is None,
                )
            )
            self.__lyt.addWidget(self.__project_layout_groupbox)
        return

    def init_fake_tools(self) -> None:
        """"""
        # $ Specify problems
        toolpath_problem_lines = []
        if self.__project_report:
            toolpath_report = self.__project_report["toolpath_report"]
            for k in toolpath_report.keys():
                if toolpath_report[k]["error"]:
                    line = k
                    toolpath_problem_lines.append(line)
            for k in toolpath_report.keys():
                if toolpath_report[k]["warning"]:
                    line = k
                    if line not in toolpath_problem_lines:
                        toolpath_problem_lines.append(line)
        # $ Show problems
        real_toolpath_seg = data.current_project.get_toolpath_seg()
        self.__fake_toolpath_seg = real_toolpath_seg.clone()
        self.__fake_toolpath_seg.set_fake(True)
        if (len(toolpath_problem_lines) > 0) or (self.__project_report is None):
            # The ToolsGroupbox() needs the project report to properly prefill the dropdown widgets.
            self.__tools_groupbox = _tools_groupbox_.ToolsGroupbox(
                parent=None,
                title=None,
                fake_toolpath_seg=self.__fake_toolpath_seg,
                categories=toolpath_problem_lines,
                show_all=self.__project_report is None,
                report=self.__project_report,
            )
            self.__lyt.addWidget(self.__tools_groupbox)
        return

    def get_fake_board(self) -> _board_.Board:
        return self.__fake_board

    def get_fake_chip(self) -> _chip_.Chip:
        return self.__fake_chip

    def get_fake_probe(self) -> _probe_.Probe:
        return self.__fake_probe

    def get_fake_treepath_seg(self) -> _treepath_seg_.TreepathSeg:
        return self.__fake_treepath_seg

    def get_fake_toolpath_seg(self) -> _toolpath_seg_.ToolpathSeg:
        return self.__fake_toolpath_seg

    def get_board_groupbox(self) -> _board_groupbox_.BoardGroupBox:
        return self.__board_groupbox

    def get_chip_groupbox(self) -> _chip_groupbox_.ChipGroupBox:
        return self.__chip_groupbox

    def get_probe_groupbox(self) -> _probe_groupbox_.ProbeGroupBox:
        return self.__probe_groupbox

    def get_project_layout_groupbox(
        self,
    ) -> _project_layout_groupbox_.ProjectLayoutGroupbox:
        return self.__project_layout_groupbox

    def get_tools_groupbox(self) -> _tools_groupbox_.ToolsGroupbox:
        return self.__tools_groupbox

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if data.startup_log_intro_wiz:
            print(f"[startup] introwizardpage.py -> self_destruct()")
        if not death_already_checked:
            if self.__dead:
                raise RuntimeError(f"Trying to kill IntroWizardPage() twice!")
            self.__dead = True

        def kill_board_seg(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] introwizardpage.py -> self_destruct().kill_board_seg()"
                )
            self.__fake_board.self_destruct(
                callback=kill_board_groupbox,
                callbackArg=None,
            )
            return

        def kill_board_groupbox(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] introwizardpage.py -> self_destruct().kill_board_groupbox()"
                )
            if self.__board_groupbox:
                self.__board_groupbox.self_destruct()
            qt.QTimer.singleShot(20, kill_chip_seg)
            return

        def kill_chip_seg(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] introwizardpage.py -> self_destruct().kill_chip_seg()"
                )
            self.__fake_chip.self_destruct(
                callback=kill_chip_groupbox,
                callbackArg=None,
            )
            return

        def kill_chip_groupbox(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] introwizardpage.py -> self_destruct().kill_chip_groupbox()"
                )
            if self.__chip_groupbox:
                self.__chip_groupbox.self_destruct()
            qt.QTimer.singleShot(20, kill_probe_seg)
            return

        def kill_probe_seg(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] introwizardpage.py -> self_destruct().kill_probe_seg()"
                )
            self.__fake_probe.self_destruct(
                callback=kill_probe_groupbox,
                callbackArg=None,
            )
            return

        def kill_probe_groupbox(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] introwizardpage.py -> self_destruct().kill_probe_groupbox()"
                )
            if self.__probe_groupbox:
                self.__probe_groupbox.self_destruct()
            qt.QTimer.singleShot(20, kill_treepath_seg)
            return

        def kill_treepath_seg(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] introwizardpage.py -> self_destruct().kill_treepath_seg()"
                )
            self.__fake_treepath_seg.self_destruct(
                callback=kill_treepath_groupbox,
                callbackArg=None,
            )
            return

        def kill_treepath_groupbox(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] introwizardpage.py -> self_destruct().kill_treepath_groupbox()"
                )
            if self.__project_layout_groupbox:
                self.__project_layout_groupbox.self_destruct()
            qt.QTimer.singleShot(20, kill_toolpath_seg)
            return

        def kill_toolpath_seg(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] introwizardpage.py -> self_destruct().kill_toolpath_seg()"
                )
            self.__fake_toolpath_seg.self_destruct(
                callback=kill_toolpath_groupbox,
                callbackArg=None,
            )
            return

        def kill_toolpath_groupbox(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] introwizardpage.py -> self_destruct().kill_toolpath_groupbox()"
                )
            if self.__tools_groupbox:
                self.__tools_groupbox.self_destruct()
            qt.QTimer.singleShot(20, finish)
            return

        def finish(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] introwizardpage.py -> self_destruct().finish()"
                )
            self.__project_report = None
            self.__fake_board = None
            self.__fake_chip = None
            self.__fake_probe = None
            self.__fake_treepath_seg = None
            self.__fake_toolpath_seg = None
            self.__board_groupbox = None
            self.__chip_groupbox = None
            self.__probe_groupbox = None
            self.__project_layout_groupbox = None
            self.__tools_groupbox = None
            self.__lyt = None
            if callback is not None:
                callback(callbackArg)
            return

        kill_board_seg()
        return
