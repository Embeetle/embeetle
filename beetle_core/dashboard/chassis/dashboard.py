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
import traceback
import qt, data, os, gui.dialogs.popupdialog, purefunctions, functions
import contextmenu.contextmenu_launcher as _contextmenu_launcher_
import dashboard.contextmenus.settings_contextmenu as _settings_contextmenu_
import tree_widget.chassis.chassis as _cm_chassis_
import helpdocs.help_texts as _ht_
import dashboard.chassis.dashboard_worker as _dw_
import dashboard.items.item as _da_
import dashboard.chassis.dashboard_head as _dashboard_head_
import dashboard.chassis.dashboard_body as _dashboard_body_
from various.kristofstuff import *


class Dashboard(_cm_chassis_.Chassis):
    def __init__(self, mainwindow, basicwidget):
        """"""
        super().__init__(
            mainwindow=mainwindow,
            basicwidget=basicwidget,
            name="Project Dashboard",
            iconpath="icons/gen/dashboard.png",
            head=None,
            body=None,
        )
        return

    def go_to_item(
        self,
        abspath: str,
        callback1: Optional[Callable],
        callbackArg1: Any,
        callback2: Optional[Callable],
        callbackArg2: Any,
    ) -> None:
        """"""
        try:
            data.main_form.projects.show_dashboard()
        except:
            traceback.print_exc()
        super().go_to_item(
            abspath=abspath,
            callback1=callback1,
            callbackArg1=callbackArg1,
            callback2=callback2,
            callbackArg2=callbackArg2,
        )
        return

    def set_page(self, **kwargs) -> None:
        """New DashboardHead() and DashboardBody() get created on-the-fly."""
        super().set_page(
            head=_dashboard_head_.DashboardHead(self),
            body=_dashboard_body_.DashboardBody(self),
        )
        return

    def keyPressEvent(self, event: qt.QKeyEvent) -> None:
        """"""
        event.accept()
        if (event.key() == qt.Qt.Key.Key_Z) and (
            event.modifiers() & qt.Qt.KeyboardModifier.ControlModifier
        ):
            self.contextmenuclick_tab_settingsbtn("undo")
            return
        if (event.key() == qt.Qt.Key.Key_S) and (
            event.modifiers() & qt.Qt.KeyboardModifier.ControlModifier
        ):
            self.leftclick_tab_savebtn()
            return
        return

    def leftclick_tab_savebtn(self):
        """User clicked the save button in the Dashboard tab header."""

        def finish(success: bool, *args) -> None:
            if success:
                self.clear_unsaved_changes()
                self.hide_tab_savebutton_sig.emit()
            return

        data.current_project.save_project(
            save_editor=True,
            save_dashboard=True,
            ask_permissions=True,
            forced_files=[],
            callback=finish,
            callbackArg=None,
        )
        return

    def leftclick_tab_settingsbtn(self, *args) -> None:
        """User clicked the settings button (hamburger) in the dashboard tab
        header."""
        contextmenu = _settings_contextmenu_.SettingsContextMenu(
            widg=None,
            item=None,
            toplvl_key="dashboard",
            clickfunc=self.contextmenuclick_tab_settingsbtn,
        )
        _contextmenu_launcher_.ContextMenuLauncher().launch_contextmenu(
            contextmenu=contextmenu,
            point=functions.get_position(None),
            callback=None,
            callbackArg=None,
        )
        return

    def contextmenuclick_tab_settingsbtn(self, key: str, *args) -> None:
        """The user made his choice in the context menu for the hamburger icon
        in the tab header."""
        key = functions.strip_toplvl_key(key)

        def undo(_key: str) -> None:
            try:
                data.current_project.undo()
            except:
                purefunctions.printc(
                    f"ERROR: {q}data.current_project.undo(){q} failed!\n",
                    color="error",
                )
                traceback.print_exc()
            return

        def revert(_key: str) -> None:
            def finish(*_args) -> None:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/gen/dashboard.png",
                    title_text="Revert dashboard",
                    text="Sorry, this feature is not yet "
                    "completed in the alpha version.",
                )
                return

            data.dashboard.reload_dashboard(
                callback=finish,
                callbackArg=None,
            )
            return

        def _help(_key: str) -> None:
            _ht_.dashboard_help()
            return

        funcs = {
            "undo": undo,
            "revert": revert,
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return

    def save_orig_cfgfiles(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        _dw_.DashboardWorker().save_orig_cfgfiles(
            callback=callback,
            callbackArg=callbackArg,
        )
        return

    def reload_dashboard(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        _dw_.DashboardWorker().reload_dashboard(callback, callbackArg)
        return

    def dashboard_open_file(self, item) -> None:
        """"""
        proj_seg = item.get_projSegment()
        abspath: Optional[str] = None

        # & Extract abspath
        try:
            abspath = item.get_projSegment().get_abspath()
        except:
            msg = str(
                f"\nERROR: {item.get_name()}.get_projSegment() is {proj_seg}\n"
                f" -> cannot extract the abspath\n"
            )
            purefunctions.printc(msg, color="error")
            traceback.print_exc()
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/dialog/stop.png",
                title_text="ERROR",
                text=msg.replace("\n", "<br>"),
            )
            return
        if (abspath is None) or (not os.path.exists(abspath)):
            gui.dialogs.popupdialog.PopupDialog.ok(
                title_text="Problem",
                text=str(
                    f"The file/folder you look for doesn{q}t exist:<br> "
                    f"{q}{abspath}{q}"
                ),
            )
            return

        # & Try in Filetree
        if data.filetree.goto_path(abspath):
            # Going to the file in the new Filetree succeeded.
            return

        # & Try in native file explorer
        if not functions.open_file_folder_in_explorer(abspath):
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/dialog/stop.png",
                title_text="Problem",
                text=str(f"Failed to open:<br> " f"{q}{abspath}{q}"),
            )
        return

    def refresh_all_recursive(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Refresh all root items from this Dashboard()-instance recursively."""

        def finish(*args) -> None:
            try:
                if callback is not None:
                    callback(callbackArg)
            except:
                purefunctions.printc(
                    f"ERROR: Cannot call {callback} with argument {callbackArg}",
                    color="error",
                )
                raise
            return

        def refresh_root_recursive(body_root_iter: Iterator[_da_.Root]) -> None:
            try:
                root = next(body_root_iter)
            except StopIteration:
                self.check_unsaved_changes()
                finish()
                return
            root.refresh_recursive_later(
                refreshlock=True,
                force_stylesheet=False,
                callback=refresh_root_recursive,
                callbackArg=body_root_iter,
            )
            return

        body: _dashboard_body_.DashboardBody = cast(
            _dashboard_body_.DashboardBody, self.get_chassis_body()
        )
        refresh_root_recursive(iter(body.body_get_rootlist()))
        return

    def check_unsaved_changes(self) -> None:
        """Show the save button (and 'APPLY DASHBOARD CHANGES' banner) if
        needed.

        The signal 'show_tab _savebutton_sig' or 'hide_tab_savebutton_sig' from
        the chassis gets triggered.
        """
        # & Any changes (asterisks) in a dashboard root?
        try:
            body: _dashboard_body_.DashboardBody = cast(
                _dashboard_body_.DashboardBody, self.get_chassis_body()
            )
            head: _dashboard_head_.DashboardHead = cast(
                _dashboard_head_.DashboardHead, self.get_chassis_head()
            )
        except:
            purefunctions.printc(
                f"\nWARNING: dashboard.check_unsaved_changes() could not run\n",
                color="warning",
            )
            traceback.print_exc()
            return
        body_rootlist: List[_da_.Root] = body.body_get_rootlist()
        for root in body_rootlist:
            if root.get_state().has_asterisk():
                # $ show the banner
                self.set_unsaved_changes()
                self.show_tab_savebutton_sig.emit()
                self.enable_tab_optionundo_signal.emit(True)
                head.show_apply_changes_banner()
                return

        # & makefile interface version issues?
        if (
            data.current_project.get_makefile_interface_version_needs_to_be_applied()
        ):
            # $ show the banner
            self.set_unsaved_changes()
            self.show_tab_savebutton_sig.emit()
            self.enable_tab_optionundo_signal.emit(True)
            head.show_apply_changes_banner()
            return

        # & No changes
        # $ hide the banner
        self.clear_unsaved_changes()
        self.hide_tab_savebutton_sig.emit()
        self.enable_tab_optionundo_signal.emit(False)
        head.hide_apply_changes_banner()
        return
