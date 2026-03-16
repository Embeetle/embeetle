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
import functools
import qt, data, gui
import gui.dialogs.projectcreationdialogs as _gen_wizard_
import hardware_api.toolcat_unicum as _toolcat_unicum_
import wizards.tool_wizard.page_zero as _page_0_
import wizards.tool_wizard.page_one as _page_1_
import wizards.tool_wizard.page_two as _page_2_
import wizards.tool_wizard.wizard_helper as _helper_

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog


class NewToolWizard(_gen_wizard_.GeneralWizard):
    """
    STRUCTURE:

    self.main_layout                        # created in superclass

        --> holds: self.main_groupbox       # created in self.init_pages()

            --> holds: self._groupbox_p0    # created in self.init_p0()
                       self._groupbox_p1    # created in self.init_p1()
                       self._groupbox_p2    # created in self.init_p2()

    ╔══_groupbox_p0═════════╗╔══_groupbox_p1══════════╗╔══_groupbox_p2═════════╗
    ║ ┌─_groupbox_p0r0──┐   ║║ ┌─_groupbox_p1r0──┐    ║║ ┌─_groupbox_p2r0──┐   ║
    ║ │                 │   ║║ │                 │    ║║ │                 │   ║
    ║ └─────────────────┘   ║║ └─────────────────┘    ║║ └─────────────────┘   ║
    ║                       ║║ ┌─_groupbox_p1r1──┐    ║║ ┌─_groupbox_p2r1──┐   ║
    ║                       ║║ │                 │    ║║ │                 │   ║
    ║                       ║║ └─────────────────┘    ║║ └─────────────────┘   ║
    ╚═══════════════════════╝╚════════════════════════╝╚═══════════════════════╝

    """

    def __init__(
        self,
        parent: Optional[qt.QWidget],
        toolcat: _toolcat_unicum_.TOOLCAT_UNIC,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Create NewToolWizard() for given toolcat."""
        if parent is None:
            parent = data.main_form
        assert isinstance(toolcat, _toolcat_unicum_.TOOLCAT_UNIC)
        super().__init__(parent)
        self.__callback = callback
        self.__callbackArg = callbackArg
        self.__apply_clicked = False
        self.setWindowTitle(
            f'New Tool Wizard:  {toolcat.get_name().replace("_", " ")}'
        )
        # self.setWindowFlags(self.windowFlags() | qt.Qt.WindowType.WindowStaysOnTopHint)
        self.toolcat: _toolcat_unicum_.TOOLCAT_UNIC = toolcat
        self.main_groupbox: Optional[qt.QGroupBox] = None

        #! ---------------------------------------- PAGE 0 -----------------------------------------
        self._groupbox_p0: Optional[qt.QGroupBox] = None
        self._groupbox_p0r0: Optional[qt.QGroupBox] = None
        self._widgets_p0r0: Dict[str, Dict[str, Any]] = {
            "download": {
                "checkdot": None,
                "button": None,
                "label": None,
            },
            "local": {
                "checkdot": None,
                "button": None,
                "label": None,
            },
        }

        #! ---------------------------------------- PAGE 1 -----------------------------------------
        self._groupbox_p1: Optional[qt.QGroupBox] = None
        self._page_1_initialized: bool = False
        self._groupbox_p1r0: Optional[qt.QGroupBox] = None
        self._widgets_p1r0: Dict[str, Any] = {
            "combobox": None,
            "checkmark": None,
            "warning_btn": None,
            "warning_lbl": None,
        }

        self._groupbox_p1r1: Optional[qt.QGroupBox] = None
        self._widgets_p1r1: Dict[str, Any] = {
            "lineedit": None,
            "button": None,
            "checkmark": None,
            "warning_btn": None,
            "warning_lbl": None,
        }

        #! ---------------------------------------- PAGE 3 -----------------------------------------
        self._groupbox_p2: Optional[qt.QGroupBox] = None
        self._groupbox_p2r0: Optional[qt.QGroupBox] = None
        self._widgets_p2r0: Optional[Dict[str, Any]] = {
            "lineedit": None,
            "button": None,
            "checkmark": None,
            "warning_btn": None,
            "warning_lbl": None,
        }

        self._groupbox_p2r1: Optional[qt.QGroupBox] = None
        self._widgets_p2r1: Dict[str, Any] = {
            "name_btn": None,
            "unique_id_btn": None,
            "version_btn": None,
            "build_date_btn": None,
            "bitness_btn": None,
            "location_btn": None,
            "toolprefix_btn": None,
            "name_lbl": None,
            "unique_id_lbl": None,
            "version_lbl": None,
            "build_date_lbl": None,
            "bitness_lbl": None,
            "location_lbl": None,
            "toolprefix_lbl": None,
            "name_lineedit": None,
            "unique_id_lineedit": None,
            "version_lineedit": None,
            "build_date_lineedit": None,
            "bitness_lineedit": None,
            "location_lineedit": None,
            "toolprefix_lineedit": None,
        }

        #! -----------------------------------------------------------------------------------------
        self.init_pages()
        self.add_page_buttons()
        self.init_p0()
        # self.init_p1() <- delayed!
        self.init_p2()
        self.next_button.setEnabled(False)
        self.resize_and_center()
        self.repurpose_cancel_next_buttons(
            cancel_name="CANCEL",
            cancel_func=self.show_prev_page,
            cancel_en=True,
            next_name="NEXT",
            next_func=self.show_next_page,
            next_en=False,
        )
        return

    def init_pages(self) -> None:
        """"""
        _helper_.init_pages(self)
        return

    def init_p0(self) -> None:
        """"""
        _page_0_.init_p0(self)
        return

    def init_p1(self, server_toollist: List[Dict]) -> None:
        """"""
        _page_1_.init_p1(self, server_toollist)
        return

    def init_p2(self) -> None:
        """"""
        _page_2_.init_p2(self)
        return

    def info_btn_clicked(self, name: str) -> None:
        """"""
        _page_2_.info_btn_clicked(self, name)
        return

    def resize_and_center(self, *args) -> None:
        """"""
        self.resize(cast(qt.QSize, self.main_layout.sizeHint() * 1.1))  # type: ignore
        self.center_to_parent()
        self.adjustSize()
        return

    def show_prev_page(self) -> None:
        """Click left button, which can be 'CANCEL' or 'PREVIOUS'."""
        main_groupbox_lyt: qt.QStackedLayout = cast(
            qt.QStackedLayout, self.main_groupbox.layout()
        )
        current_page = main_groupbox_lyt.currentIndex()

        # $ CANCEL
        # If the wizard is at the beginning, the left button must be 'CANCEL'. Destroy and quit the
        # wizard.
        if current_page == 0:
            self._cancel_clicked()
            return

        # $ PREVIOUS
        # Otherwise, the left button must be 'PREVIOUS'. Keep the wizard alive. Just go back to the
        # beginning (page 0), replace the left button with 'CANCEL', the right one with 'NEXT'.
        # Enable the right button.
        main_groupbox_lyt.setCurrentIndex(0)
        self.repurpose_cancel_next_buttons(
            cancel_name="CANCEL",
            next_name="NEXT",
        )
        self.next_button.setEnabled(True)
        return

    def show_next_page(self) -> None:
        """Click right button, which can be 'NEXT' or 'APPLY'."""
        main_groupbox_lyt: qt.QStackedLayout = cast(
            qt.QStackedLayout, self.main_groupbox.layout()
        )
        current_page = main_groupbox_lyt.currentIndex()

        # $ NEXT
        # If the wizard is at the beginning, the right button must be 'NEXT'. Go to the next page,
        # either page 1 or 2 depending on the checkdot status. Also replace the left button with
        # 'PREVIOUS', the right one with 'APPLY'
        if current_page == 0:
            if self._widgets_p0r0["download"]["checkdot"].is_on():
                main_groupbox_lyt.setCurrentIndex(1)
                self.repurpose_cancel_next_buttons(
                    cancel_name="PREVIOUS",
                    next_name="APPLY",
                )
                data.toolman.get_remote_beetle_toollist(
                    toolcat=self.toolcat.get_name(),
                    callback=self.init_p1,
                )
            elif self._widgets_p0r0["local"]["checkdot"].is_on():
                main_groupbox_lyt.setCurrentIndex(2)
                self.repurpose_cancel_next_buttons(
                    cancel_name="PREVIOUS",
                    next_name="APPLY",
                )
                _page_2_.update_p2(self, reason="none")
            else:
                assert False
            return

        # $ APPLY
        # If the wizard is *not* at the beginning, the right button must be 'APPLY'. Complete the
        # wizard and destroy it.
        if current_page == 1:
            self._complete_wizard(page="page_1")
        elif current_page == 2:
            self._complete_wizard(page="page_2")
        return

    # ^                                        COMPLETE WIZARD                                         ^#
    # % ============================================================================================== %#
    # % The user clicks 'APPLY', 'CANCEL' or 'X'.                                                      %#
    # %                                                                                                %#

    def _cancel_clicked(self, *args) -> None:
        """Click 'CANCEL'."""
        # Same effect as clicking 'X'
        self.reject()
        return

    def _complete_wizard(self, page: str) -> None:
        """Click 'APPLY'."""
        if self.__apply_clicked or self.dead:
            return
        self.__apply_clicked = True
        callback = self.__callback
        callbackArg = self.__callbackArg

        def _self_destruct(success: bool, *_args) -> None:
            self.self_destruct(
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*_args) -> None:
            if callback is not None:
                qt.QTimer.singleShot(
                    50,
                    functools.partial(
                        callback,
                        True,
                        callbackArg,
                    ),
                )
            return

        if page == "page_1":
            self.__download_tool(
                callback=_self_destruct,
                callbackArg=None,
            )
        elif page == "page_2":
            self.__add_local_tool(
                callback=_self_destruct,
                callbackArg=None,
            )
        return

    def __download_tool(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Click 'APPLY' on page 1.

        > callback(success, callbackArg)
        """
        if self._widgets_p1r0["combobox"] is None:
            # Abort
            if callback is not None:
                callback(False, callbackArg)
            return
        selected_id = self._widgets_p1r0["combobox"].get_selected_item_name()
        if (
            "built_in" in selected_id.lower()
            or "add local tool" in selected_id.lower()
            or "cannot connect" in selected_id.lower()
            or "select tool" in selected_id.lower()
            or selected_id.lower() == "empty"
        ):
            # Abort
            if callback is not None:
                callback(False, callbackArg)
            return
        # The Toolmanager() method 'wizard_download_tool()' also inserts a 'success' parameter.
        data.toolman.wizard_download_tool(
            remote_uid=selected_id,
            parent_folder=self._widgets_p1r1["lineedit"].text(),
            callback=callback,
            callbackArg=callbackArg,
        )
        return

    def __add_local_tool(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Click 'APPLY' on page 2.

        > callback(success, callbackArg)
        """

        def finish(success: bool, unique_id: str, *args):
            callback(success, callbackArg)
            return

        data.toolman.wizard_add_local_tool(
            dirpath_or_exepath=self._widgets_p2r0["lineedit"].text(),
            callback=finish,
            callbackArg=None,
        )
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
            # click 'X' or 'CANCEL'. Therefore, the only moments to get here are:
            #     - 'APPLY' is clicked, but tool downloading didn't start yet
            #     - Tool downloading is still ongoing
            # The first option is very unlikely, as downloading starts right away after clicking
            # 'APPLY'. Therefore it makes sense to assume the second option, and show a popup ac-
            # cordingly:
            text = """
            <p>
                Embeetle is busy downloading tools. Maybe the download<br>
                window is hidden behind the other window(s), so you can't see<br>
                it right now.
            </p>
            """
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/gen/hourglass.png",
                title_text="Please wait",
                text=text,
            )
            # Do not kill the NewToolWizard() now! Let the download continue. The NewToolWizard()
            # kills itself afterwards (even if the download fails).
            return

        callback = self.__callback
        callbackArg = self.__callbackArg

        def finish(*_args) -> None:
            # _gen_wizard_.GeneralWizard.reject(self) <= done in self_destruct() method!
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
        """Kill this NewToolWizard()-instance.

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
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill NewToolWizard() twice!")
            self.dead = True  # noqa

        # * Start
        # $ Hide
        self.hide()

        # $ Delete page buttons
        self.delete_page_buttons()

        # $ Destroy stuff
        # Will be done in the supercall function, where the self.main_layout is cleaned.

        def finish(*args) -> None:
            # $ Clear variables
            self.toolcat = None
            self._groupbox_p0 = None
            self._groupbox_p0r0 = None
            self._widgets_p0r0 = None
            self._groupbox_p1 = None
            self._page_1_initialized = None
            self._groupbox_p1r0 = None
            self._widgets_p1r0 = None
            self._groupbox_p1r1 = None
            self._widgets_p1r1 = None
            self._groupbox_p2 = None
            self._groupbox_p2r0 = None
            self._groupbox_p2r1 = None
            self._widgets_p2r1 = None
            self.__callback = None
            self.__callbackArg = None
            if callback is not None:
                callback(callbackArg)
            return

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
