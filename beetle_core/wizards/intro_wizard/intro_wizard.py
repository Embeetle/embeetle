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
import sys, functools
import qt, data, purefunctions
import gui.dialogs.popupdialog
import gui.dialogs.projectcreationdialogs as _gen_wizard_
import wizards.intro_wizard.introwizardpage as _introwizardpage_
import fnmatch as _fn_
import bpathlib.path_power as _pp_
import gui.stylesheets.scrollbar as _scrollbar_style_
import os_checker

if TYPE_CHECKING:
    import project.segments.board_seg.board as _board_
    import project.segments.chip_seg.chip as _chip_
    import project.segments.probe_seg.probe as _probe_
    import project.segments.path_seg.treepath_seg as _treepath_seg_
    import project.segments.path_seg.toolpath_seg as _toolpath_seg_
    import wizards.intro_wizard.board_groupbox as _board_groupbox_
    import wizards.intro_wizard.chip_groupbox as _chip_groupbox_
    import wizards.intro_wizard.probe_groupbox as _probe_groupbox_
    import wizards.intro_wizard.project_layout_groupbox as _project_layout_groupbox_
    import wizards.intro_wizard.tools_groupbox as _tools_groupbox_
from various.kristofstuff import *


class IntroWizard(_gen_wizard_.GeneralWizard):
    """STRUCTURE =========

    self.main_layout                         # created in superclass
        --> holds: self.__intro_wizard_page  # created in self.__init__()

      ╔══[ self.main_layout ]══════════════════════════════════════════════╗
      ║                                                                    ║
      ║   ┌──── QScrollArea() ────────────────────────────────┐            ║
      ║   │ ┌─── self.__intro_wizard_page ──────────────────┐ │            ║
      ║   │ │ BoardGroupBox()                               │ │            ║
      ║   │ │                                               │ │            ║
      ║   │ │ ChipGroupBox()                                │ │            ║
      ║   │ │                                               │ │            ║
      ║   │ │ ProbeGroupBox()                               │ │            ║
      ║   │ │                                               │ │            ║
      ║   │ │ ProjectLayoutGroupbox()                       │ │            ║
      ║   │ │                                               │ │            ║
      ║   │ │ ToolsGroupbox()                               │ │            ║
      ║   │ └───────────────────────────────────────────────┘ │            ║
      ║   └───────────────────────────────────────────────────┘            ║
      ║                                                                    ║
      ╚════════════════════════════════════════════════════════════════════╝
    """

    def __init__(
        self,
        parent: Optional[qt.QWidget],
        report: Optional[Dict],
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Create IntroWizard(). The callback gets invoked after this instance
        has served its purpose and is already destroyed. > callback(result,
        callbackArg)

        The 'result' parameter is True if the user clicked 'APPLY', False
        otherwise.
        """
        if parent is None:
            parent = data.main_form
        super().__init__(parent)
        self.__callback = callback
        self.__callbackArg = callbackArg
        self.__apply_clicked = False
        self.__skip_clicked = False
        self.setWindowTitle("Intro Wizard")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        self.main_layout.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.__scroll_area: qt.QScrollArea = qt.QScrollArea()
        self.__intro_wizard_page: Optional[
            _introwizardpage_.IntroWizardPage
        ] = None
        self.main_layout.addWidget(self.__scroll_area)
        self.__project_report = report
        self.add_page_buttons()
        self.repurpose_cancel_next_buttons(
            cancel_name="SKIP",
            cancel_func=self._skip_clicked,
            cancel_en=True,
            next_name="APPLY",
            next_func=self._complete_wizard,
            next_en=True,
        )
        return

    def showEvent(self, e) -> None:
        """"""
        super().showEvent(e)
        self.resize_and_center(width_percentage=1.0, height_percentage=1.2)
        self.update_check_size()
        return

    def set_callback(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Set the callback to be invoked at the end of this wizard."""
        assert self.__callback is None
        self.__callback = callback
        self.__callbackArg = callbackArg
        return

    def initialize_from_report(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Initialize oneself based on the stored report.

        NOTE: This 'initialize()' method should be run *after* the IntroWizard() instance is created
        and assigned to 'data.current_project.intro_wiz'. That's because the ToolpathItem()-instan-
        ces refer to 'data.current_project.intro_wiz' in its '__get_dropdown_elements()' method.
        """
        assert self.__project_report is not None
        self.__add_intro_wizard_page(
            callback=callback,
            callbackArg=callbackArg,
        )
        return

    def __add_intro_wizard_page(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """SUMMARY ======= Create 'self.__intro_wizard_page' and fake(!) project
        segments for it. These segments will be cloned from the real ones in the
        Project()-instance. The 'intro wizard page' is only dis- played if there
        are problems detected in the report (eg. at startup).

        However, the fake project segments get created regardless.

        NOTES
        =====
        - The init_fake_chip(), init_fake_probe(), ... methods are invoked separately, *after*
          creating and storing the IntroWizardPage()-instance. That's because the ToolpathItem()-
          instances invoke:
              > data.current_project.intro_wiz.get_fake_probe()
              > data.current_project.intro_wiz.get_fake_chip()
        These ToolpathItem()-instances are created when the method 'show_on_intro_wizard()' is in-
        voked on the fake ToolpathSeg()-instance, which happens in 'self.__intro_wizard_page
        .init_fake_tools()'.

        - The fake Board(), Chip(), Probe(), TreepathSeg() and ToolpathSeg() instances will be
          created anyhow, even if there are no problems detected. As for the ChipGroupBox(), Probe-
          GroupBox(), ProjectLayoutGroupbox() and ToolsGroupbox(), they only get created if there's
          a need to display the corresponding fake project segment.
        """
        # & Create IntroWizardPage()
        self.__intro_wizard_page = _introwizardpage_.IntroWizardPage(
            parent=None,
            project_report=self.__project_report,
        )

        # & Clone corresponding project segments
        self.__intro_wizard_page.init_fake_board()
        self.__intro_wizard_page.init_fake_chip()
        self.__intro_wizard_page.init_fake_probe()
        self.__intro_wizard_page.init_fake_project_layout()
        self.__intro_wizard_page.init_fake_tools()

        # & Display fake project segments
        if self.has_err_warn():
            self.__scroll_area.setWidget(self.__intro_wizard_page)
            self.__scroll_area.setWidgetResizable(True)
            self.__scroll_area.setVerticalScrollBarPolicy(
                qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self.__scroll_area.setHorizontalScrollBarPolicy(
                qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self.__scroll_area.setStyleSheet(f"""
                QObject {{
                    background: transparent;
                    border: none;
                    padding: 0px;
                    margin: 0px;
                }}
            """)
            self.__scroll_area.verticalScrollBar().setStyleSheet(
                _scrollbar_style_.get_vertical()
            )
            self.__scroll_area.horizontalScrollBar().setStyleSheet(
                _scrollbar_style_.get_horizontal()
            )
            self.__scroll_area.verticalScrollBar().setContextMenuPolicy(
                qt.Qt.ContextMenuPolicy.NoContextMenu
            )
            self.__scroll_area.horizontalScrollBar().setContextMenuPolicy(
                qt.Qt.ContextMenuPolicy.NoContextMenu
            )
            self.__trigger_refresh(
                callback=callback,
                callbackArg=callbackArg,
            )
            return
        if callback is not None:
            callback(callbackArg)
        return

    def __trigger_refresh(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Trigger a 'dashboard refresh' on all the fake project segments: their
        own 'trigger_dash- board_refresh()' methods will run.

        These methods work just fine on the Intro Wizard (even though it's not
        the dashboard).
        """

        def refresh_chip(*args) -> None:
            fake_chip = self.get_fake_chip()
            fake_chip.trigger_dashboard_refresh(
                callback=refresh_probe,
                callbackArg=None,
            )
            return

        def refresh_probe(*args) -> None:
            fake_probe = self.get_fake_probe()
            fake_probe.trigger_dashboard_refresh(
                callback=refresh_treepath_seg,
                callbackArg=None,
            )
            return

        def refresh_treepath_seg(*args) -> None:
            fake_treepath_seg = self.get_fake_treepath_seg()
            fake_treepath_seg.trigger_dashboard_refresh(
                callback=refresh_toolpath_seg,
                callbackArg=None,
            )
            return

        def refresh_toolpath_seg(*args) -> None:
            fake_toolpath_seg = self.get_fake_toolpath_seg()
            fake_toolpath_seg.trigger_dashboard_refresh(
                callback=callback,
                callbackArg=callbackArg,
            )
            return

        # * refresh_board
        fake_board = self.get_fake_board()
        fake_board.trigger_dashboard_refresh(
            callback=refresh_chip,
            callbackArg=None,
        )
        return

    def get_fake_board(self) -> _board_.Board:
        fake_board = self.__intro_wizard_page.get_fake_board()
        assert fake_board != data.current_project.get_board()
        return fake_board

    def get_fake_chip(self) -> _chip_.Chip:
        fake_chip = self.__intro_wizard_page.get_fake_chip()
        assert fake_chip != data.current_project.get_chip()
        return fake_chip

    def get_fake_probe(self) -> _probe_.Probe:
        fake_probe = self.__intro_wizard_page.get_fake_probe()
        assert fake_probe != data.current_project.get_probe()
        return fake_probe

    def get_fake_treepath_seg(self) -> _treepath_seg_.TreepathSeg:
        fake_treepath_seg = self.__intro_wizard_page.get_fake_treepath_seg()
        assert fake_treepath_seg != data.current_project.get_treepath_seg()
        return fake_treepath_seg

    def get_fake_toolpath_seg(self) -> _toolpath_seg_.ToolpathSeg:
        fake_toolpath_seg = self.__intro_wizard_page.get_fake_toolpath_seg()
        assert fake_toolpath_seg != data.current_project.get_toolpath_seg()
        return fake_toolpath_seg

    def __get_board_groupbox(self) -> Optional[_board_groupbox_.BoardGroupBox]:
        return self.__intro_wizard_page.get_board_groupbox()

    def __get_chip_groupbox(self) -> Optional[_chip_groupbox_.ChipGroupBox]:
        return self.__intro_wizard_page.get_chip_groupbox()

    def __get_probe_groupbox(self) -> Optional[_probe_groupbox_.ProbeGroupBox]:
        return self.__intro_wizard_page.get_probe_groupbox()

    def __get_project_layout_groupbox(
        self,
    ) -> Optional[_project_layout_groupbox_.ProjectLayoutGroupbox]:
        return self.__intro_wizard_page.get_project_layout_groupbox()

    def __get_tools_groupbox(self) -> Optional[_tools_groupbox_.ToolsGroupbox]:
        return self.__intro_wizard_page.get_tools_groupbox()

    def has_err_warn(self) -> bool:
        """Check if there are errors or warnings in the project_report."""
        if self.__project_report is None:
            return False

        # $ Check board
        board_report = self.__project_report["board_report"]
        if board_report["DEVICE"]["error"] or board_report["DEVICE"]["warning"]:
            return True
        # $ Check chip
        chip_report = self.__project_report["chip_report"]
        if chip_report["DEVICE"]["error"] or chip_report["DEVICE"]["warning"]:
            return True
        # $ Check probe
        probe_report = self.__project_report["probe_report"]
        if (
            probe_report["DEVICE"]["error"]
            or probe_report["DEVICE"]["warning"]
            or probe_report["TRANSPORT_PROTOCOL"]["error"]
            or probe_report["TRANSPORT_PROTOCOL"]["warning"]
        ):
            return True
        # $ Check treepath_seg
        treepath_report = self.__project_report["treepath_report"]
        for key in treepath_report.keys():
            if treepath_report[key]["error"] or treepath_report[key]["warning"]:
                return True
        # $ Check toolpath_seg
        toolpath_report = self.__project_report["toolpath_report"]
        for key in toolpath_report.keys():
            if toolpath_report[key]["error"] or toolpath_report[key]["warning"]:
                return True
        return False

    # ^                                        COMPLETE WIZARD                                         ^#
    # % ============================================================================================== %#
    # % The user clicks 'APPLY', 'CANCEL' or 'X'.                                                      %#
    # %                                                                                                %#

    def _skip_clicked(self, *args) -> None:
        """Click 'SKIP'."""
        self.__skip_clicked = True
        self.reject()
        return

    def _complete_wizard(self, *args) -> None:
        """Click 'APPLY'."""
        if self.__apply_clicked or self.dead:
            return
        self.__apply_clicked = True
        callback = self.__callback
        callbackArg = self.__callbackArg

        if data.startup_log_intro_wiz:
            print(f"[startup] intro_wizard.py -> _complete_wizard()")
        # There's no going back. Unlike the LibWizard(), this IntroWizard() will destroy itself even
        # if the tool downloads fail. Therefore, it makes sense to delete the 'APPLY' and 'CANCEL'
        # buttons already at this point.
        # WARNING: The method 'self.delete_page_buttons()' will be invoked *again* in the self-
        # destruct method. I've tweaked the page buttons deletion such that it can deal with that.
        self.delete_page_buttons()

        def start(*_args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] intro_wizard.py -> _complete_wizard().start()"
                )
            if self.has_err_warn() or (self.__project_report is None):
                self.__apply_intro_wizard_page(
                    callback=kill_self,
                    callbackArg=None,
                )
                return
            kill_self()
            return

        def kill_self(*_args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] intro_wizard.py -> _complete_wizard().kill_self()"
                )
            self.self_destruct(
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*_args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] intro_wizard.py -> _complete_wizard().finish()"
                )
            data.current_project.save_project(
                save_editor=False,
                save_dashboard=True,
                ask_permissions=False,
                forced_files=[
                    "DASHBOARD_MK",
                    "OPENOCD_CHIPFILE",
                    "OPENOCD_PROBEFILE",
                    "GDB_FLASHFILE",
                ],
                callback=callback,
                callbackArg=callbackArg,
            )
            return

        # * Start
        # After deleting the 'APPLY' and 'CANCEL' buttons, a short wait time is needed. Otherwise,
        # the download window for tools gets pushed to the backside.
        qt.QTimer.singleShot(
            800,
            start,
        )
        return

    def __apply_intro_wizard_page(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Apply the changes from 'intro wizard page', in this order:

        1. PROJECT LAYOUT
        2. BOARD
        3. CHIP
        4. PROBE
        5. TOOLS
        """
        if data.startup_log_intro_wiz:
            print(f"[startup] intro_wizard.py -> __apply_intro_wizard_page()")

        # & ======================================= BOARD ======================================== &#
        def apply_board(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] intro_wizard.py -> __apply_intro_wizard_page().apply_board()"
                )
            board_groupbox = self.__get_board_groupbox()
            if board_groupbox is None:
                apply_chip()
                return
            new_board_unicum = self.get_fake_board().get_board_unicum()
            if (new_board_unicum is None) or (
                new_board_unicum.get_name().lower() == "none"
            ):
                apply_chip()
                return
            data.current_project.get_board().change_board(
                board_unicum=new_board_unicum,
                callback=apply_chip,
                callbackArg=None,
            )
            return

        # & ======================================== CHIP ======================================== &#
        def apply_chip(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] intro_wizard.py -> __apply_intro_wizard_page().apply_chip()"
                )
            chip_groupbox = self.__get_chip_groupbox()
            if chip_groupbox is None:
                apply_probe()
                return
            new_chip_unicum = self.get_fake_chip().get_chip_unicum()
            if (new_chip_unicum is None) or (
                new_chip_unicum.get_name().lower() == "none"
            ):
                apply_probe()
                return
            data.current_project.get_chip().change_chip(
                chip_unicum=new_chip_unicum,
                callback=apply_probe,
                callbackArg=None,
            )
            return

        # & ======================================= PROBE ======================================== &#
        def apply_probe(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] intro_wizard.py -> __apply_intro_wizard_page().apply_probe()"
                )
            probe_groupbox = self.__get_probe_groupbox()
            if probe_groupbox is None:
                download_tools()
                return

            def apply_device(*_args) -> None:
                if data.startup_log_intro_wiz:
                    print(
                        f"[startup] intro_wizard.py -> "
                        f"__apply_intro_wizard_page().apply_probe().apply_device()"
                    )
                new_probe_unicum = self.get_fake_probe().get_probe_unicum()
                if (new_probe_unicum is None) or (
                    new_probe_unicum.get_name().lower() == "none"
                ):
                    apply_transport_protocol()
                    return
                data.current_project.get_probe().change(
                    e=new_probe_unicum,
                    callback=apply_transport_protocol,
                    callbackArg=None,
                )
                return

            def apply_transport_protocol(*_args) -> None:
                if data.startup_log_intro_wiz:
                    print(
                        f"[startup] intro_wizard.py -> "
                        f"__apply_intro_wizard_page().apply_probe().apply_transport_protocol()"
                    )
                new_tp_unicum = (
                    self.get_fake_probe().get_transport_protocol_unicum()
                )
                if (new_tp_unicum is None) or (
                    new_tp_unicum.get_name().lower() == "none"
                ):
                    download_tools()
                    return
                data.current_project.get_probe().change(
                    e=new_tp_unicum,
                    callback=download_tools,
                    callbackArg=None,
                )
                return

            apply_device()
            return

        # & ======================================= TOOLS ======================================== &#
        def download_tools(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] intro_wizard.py -> __apply_intro_wizard_page().download_tools()"
                )
            # Loop over all categories (or just the categories mentioned in the report) and observe
            # the selected unique id for each of them. If the unique id exists in the global Tool-
            # manager() 'data.toolman', then no download is needed. After downloading all missing
            # tools, the next subfunction 'apply_tools()' will take care of applying them.
            tools_groupbox = self.__get_tools_groupbox()
            if tools_groupbox is None:
                finish()
                return
            fake_toolpath_seg: _toolpath_seg_.ToolpathSeg = (
                self.get_fake_toolpath_seg()
            )
            if self.__project_report:
                categories = tools_groupbox.get_categories()
            else:
                categories = fake_toolpath_seg.get_categories()

            def download_next_tool(toolcat_iter: Iterator[str]) -> None:
                try:
                    toolcat: str = next(toolcat_iter)
                except StopIteration:
                    apply_tools()
                    return
                selected_id = fake_toolpath_seg.get_unique_id(toolcat)
                if data.startup_log_intro_wiz:
                    print(
                        f"[startup] intro_wizard.py -> "
                        f"__apply_intro_wizard_page().download_tools()."
                        f"download_next_tool({toolcat}, {selected_id})"
                    )
                if selected_id is None:
                    download_next_tool(toolcat_iter)
                    return

                # $ 'selected_id' exists
                # No need to download anything. Move on to the next tool category.
                if data.toolman.unique_id_exists(
                    unique_id=selected_id,
                    bitness_matters=True,
                ) or _fn_.fnmatch(
                    name=selected_id.lower(),
                    pat="*built*in*",
                ):
                    download_next_tool(toolcat_iter)
                    return

                # $ 'selected_id' doesn't exist
                # Download tool.
                data.toolman.wizard_download_tool(
                    remote_uid=selected_id,
                    parent_folder=data.beetle_tools_directory,
                    callback=download_finished,
                    callbackArg=toolcat_iter,
                )
                return

            def download_finished(
                success: bool,
                toolcat_iter: Iterator[str],
                *_args,
            ) -> None:
                if data.startup_log_intro_wiz:
                    print(
                        f"[startup] intro_wizard.py -> "
                        f"__apply_intro_wizard_page().download_tools()."
                        f"download_finished({success})"
                    )
                if not success:
                    purefunctions.printc(
                        f"\nERROR: Downloading tool failed!\n",
                        color="error",
                    )
                download_next_tool(toolcat_iter)
                return

            # $ Start downloading all tools
            download_next_tool(iter(categories))
            return

        def apply_tools(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] intro_wizard.py -> __apply_intro_wizard_page().apply_tools()"
                )
            tools_groupbox = self.__get_tools_groupbox()
            if tools_groupbox is None:
                finish()
                return
            fake_toolpath_seg: _toolpath_seg_.ToolpathSeg = (
                self.get_fake_toolpath_seg()
            )
            if self.__project_report:
                categories = tools_groupbox.get_categories()
            else:
                categories = fake_toolpath_seg.get_categories()

            def apply_next_tool(toolcat_iter: Iterator[str]) -> None:
                try:
                    toolcat = next(toolcat_iter)
                except StopIteration:
                    finish()
                    return
                selected_id = fake_toolpath_seg.get_unique_id(toolcat)
                if data.startup_log_intro_wiz:
                    print(
                        f"[startup] intro_wizard.py -> "
                        f"__apply_intro_wizard_page().apply_tools()."
                        f"apply_next_tool({toolcat}, {selected_id})"
                    )
                if selected_id is None:
                    apply_next_tool(toolcat_iter)
                    return
                # $ 'selected_id' exists
                if data.toolman.unique_id_exists(
                    unique_id=selected_id,
                    bitness_matters=True,
                ) or _fn_.fnmatch(
                    name=selected_id.lower(),
                    pat="*built*in*",
                ):
                    data.current_project.get_toolpath_seg().change_unique_id(
                        cat_name=toolcat,
                        unique_id=selected_id,
                        history=True,
                        callback=apply_next_tool,
                        callbackArg=toolcat_iter,
                    )
                    return
                # $ 'selected_id' doesn't exist
                print(f"selected_id doesn{q}t exist: {selected_id}")
                apply_next_tool(toolcat_iter)
                return

            # $ Start applying all tools
            apply_next_tool(iter(categories))
            return

        def finish(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] intro_wizard.py -> __apply_intro_wizard_page().finish()"
                )
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        # & =================================== PROJECT LAYOUT =================================== &#
        project_layout_groupbox = self.__get_project_layout_groupbox()
        if project_layout_groupbox is None:
            apply_board()
            return
        fake_treepath_seg: _treepath_seg_.TreepathSeg = (
            self.get_fake_treepath_seg()
        )

        def apply_next_treepath(unicum_name_iter: Iterator[str]) -> None:
            try:
                unicum_name: str = next(unicum_name_iter)
            except StopIteration:
                apply_board()
                return
            new_abspath = fake_treepath_seg.get_abspath(unicum_name)
            if (new_abspath is None) or (new_abspath.lower() == "none"):
                if data.startup_log_intro_wiz:
                    print(
                        f"[startup] intro_wizard.py -> "
                        f"__apply_intro_wizard_page().apply_next_treepath({unicum_name})"
                        f" -> ignore"
                    )
                apply_next_treepath(unicum_name_iter)
                return
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] intro_wizard.py -> "
                    f"__apply_intro_wizard_page().apply_next_treepath({unicum_name})"
                    f" -> {q}{new_abspath}{q}"
                )
            data.current_project.get_treepath_seg().set_abspath(
                unicum=unicum_name,
                abspath=new_abspath,
                history=True,
                refresh=True,
                with_gui=True,
                callback=apply_next_treepath,
                callbackArg=unicum_name_iter,
            )
            return

        # If a report was present, I would only iterate over those project layout paths mentioned in
        # the report:
        #     > unicum_names:Optional[List[str]] = None
        #     > if self.__report:
        #     >     unicum_names = project_layout_groupbox.get_unicum_names()
        #     > else:
        #     >     unicum_names = fake_treepath_seg.get_treepath_unicum_names()
        # However, that approach no longer holds. During the wizard configuration, some paths can
        # be added or removed depending on the choice of the chip, board, probe or tools. Therefore,
        # it's important to iterate over *all* the project layout paths.
        apply_next_treepath(iter(fake_treepath_seg.get_treepath_unicum_names()))
        return

    def reject(self) -> None:
        """Click 'X'."""
        if self.dead:
            return
        if self.__apply_clicked:
            # How to get here:
            # ----------------
            # User clicks 'X' or 'CANCEL' *after* clicking 'APPLY'. However, after downloading the
            # tools, this wizards kills itself. So there wouldn't be any chance for the user to
            # click 'X' or 'CANCEL'. A permission dialog can still be shown, but always after kil-
            # ling this wizard. Therefore, the only moments to get here are:
            #     - 'APPLY' is clicked, but tool downloading didn't start yet
            #     - Tool downloading is still ongoing
            # The first option is very unlikely, as downloading starts right away after clicking
            # 'APPLY'. Therefore it makes sense to assume the second option, and show a popup ac-
            # cordingly:
            text = """
            <p>
                Embeetle is busy downloading tools for this project. Maybe the<br>
                download window is hidden behind the other window(s), so you<br>
                can't see it right now.
            </p>
            """
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/gen/hourglass.png",
                title_text="Please wait",
                text=text,
            )
            # Do not kill the IntroWizard() now! Let the download continue. The IntroWizard() kills
            # itself afterwards.
            # Unlike the LibWizard(), the IntroWizard() kills itself even after a *failed* download
            # attempt. There's no going back at this point.
            return

        if not self.__skip_clicked:
            sys.exit(0)

        callback = self.__callback
        callbackArg = self.__callbackArg

        def finish(*_args) -> None:
            # _gen_wizard_.GeneralWizard.reject(self) <= not sure if needed
            if callback is not None:
                qt.QTimer.singleShot(
                    50,
                    functools.partial(
                        callback,
                        False,
                        callbackArg,
                    ),
                )
            return

        self.self_destruct(
            callback=finish,
            callbackArg=None,
        )
        return

    def is_dead(self) -> bool:
        """"""
        return self.dead

    def self_destruct(
        self,
        death_already_checked: bool = False,
        additional_clean_list: Optional[List[str]] = None,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Kill this IntroWizard()-instance.

        INVOCATIONS:
        ============
            > At the end of 'self._complete_wizard()', which runs when user clicks 'APPLY'.
            > At the end of 'self.reject()', which runs when the user clicks 'X' or 'CANCEL'.

        Both 'self._complete_wizard()' and 'self.reject()' store what's in 'self.__callback' and
        'self.__callbackArg' before invoking the self-destruct method, to be able to call the call-
        back afterwards.

        WARNING:
        ========
        Self destruction happens in this order: first hide(), then kill all widgets and finally
        close() this QDialog(). Invoking close() immediately, without first hiding, causes the
        reject() method to run, which I've overridden to invoke this 'self_destruct()' method! That
        would cause this method to run twice.
        """
        if data.startup_log_intro_wiz:
            print(f"[startup] intro_wizard.py -> self_destruct()")
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill IntroWizard() twice!")
            self.dead = True  # noqa

        def kill_intro_wizard_page(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] intro_wizard.py -> self_destruct().kill_intro_wizard_page()"
                )
            self.__intro_wizard_page.self_destruct(
                callback=self_destruct_super,
                callbackArg=None,
            )
            return

        def self_destruct_super(*args) -> None:
            if data.startup_log_intro_wiz:
                print(
                    f"[startup] intro_wizard.py -> self_destruct().self_destruct_super()"
                )
            # $ Supercall reject
            # _gen_wizard_.GeneralWizard.reject(self) <= not sure if needed

            # $ Close and destroy
            # 'self.close()' happens in the superclass method:
            _gen_wizard_.GeneralWizard.self_destruct(
                self,
                death_already_checked=True,
                additional_clean_list=additional_clean_list,
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args) -> None:
            if data.startup_log_intro_wiz:
                print(f"[startup] intro_wizard.py -> self_destruct().finish()")
            # $ Clear variables
            self.__intro_wizard_page = None
            self.__project_report = None
            self.__callback = None
            self.__callbackArg = None
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        # $ Hide
        self.hide()

        # $ Delete page buttons
        self.delete_page_buttons()

        # $ Destroy stuff
        kill_intro_wizard_page(None)
        return
