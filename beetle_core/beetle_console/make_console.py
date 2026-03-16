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
import threading, functools
import qt, data, purefunctions, functions, iconfunctions
import beetle_console.console_widget as _console_widget_
import gui.templates.baseobject as _baseobject_
import components.thread_switcher as _sw_
import gui.stylesheets.scrollbar as _sb_

# import gui.forms.pinconfigurator as _pinconfiguratorwindow_
if TYPE_CHECKING:
    import bpathlib.tool_obj as _tool_obj_
    import gui.forms.mainwindow as _mainwindow_
    import gui.forms.homewindow as _homewindow_
nop = lambda *a, **k: None
q = "'"
dq = '"'


class MakeConsole(qt.QFrame, _baseobject_.BaseObject):
    """A MakeConsole()-instance is intended to run make commands. This instance
    is subclassed from both QFrame() and BaseObject() such that it nicely fits
    into an Embeetle QTabWidget().

    The heart of the MakeConsole() is its ConsoleWidget()-instance. That's a
    subclassed QPlainTextEdit() widget that behaves more or less like a console.
    The user can interact with this widget - typing and executing commands - but
    you can also interact programmatically with it.
    """

    def __init__(
        self,
        parent: qt.QTabWidget,
        main_form: Union[_mainwindow_.MainWindow, _homewindow_.HomeWindow],
        name: str,
    ) -> None:
        """
        :param parent:      The QTabWidget() holding this MakeConsole()-instance.

        :param main_form:   The Project Window or Home Window.

        :param name:        Name for this MakeConsole()-widget, to be displayed in its tab.
        """
        qt.QFrame.__init__(self)
        _baseobject_.BaseObject.__init__(
            self,
            parent=parent,
            main_form=main_form,
            name=name,
            icon=iconfunctions.get_qicon("icons/console/console.png"),
        )
        self.__parent = parent
        self.__main_form = main_form
        self.__name = name
        self.setStyleSheet(
            """
            QFrame {
                background : transparent;
                border     : none;
                padding    : 0px;
                margin     : 0px;
            }
        """
        )

        # * Layout
        self.__lyt = qt.QVBoxLayout()
        self.__lyt.setSpacing(2)
        self.__lyt.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__lyt)

        # * Console widget
        self.__console_widget = _console_widget_.ConsoleWidget(
            parent=self,
            readonly=False,
            cwd=data.current_project.get_proj_rootpath(),
            fake_console=True,
            is_serial_monitor=False,
        )
        self.__lyt.addWidget(self.__console_widget)

        # * Status bar
        self.__status_bar_frm = qt.QFrame()
        self.__status_bar_lyt = qt.QHBoxLayout()
        self.__status_bar_frm.setLayout(self.__status_bar_lyt)
        self.__status_bar_frm.setStyleSheet(
            """
            QFrame {
                background : #555753;
                border     : none;
                padding    : 0px;
                margin     : 0px;
            }
        """
        )
        self.__lyt.addWidget(self.__status_bar_frm)

        # Status bar label
        self.__status_lbl = qt.QLabel()
        self.__status_lbl.setStyleSheet(
            """
            QLabel {
                background: transparent;
                color: white;
                border: none;
            }
        """
        )
        self.__status_lbl.setFont(data.get_general_font())
        self.__status_lbl.setText("status:")
        self.__status_bar_lyt.addWidget(self.__status_lbl)
        self.__status_clear_nr = 0
        self.__clear_status(0)
        return

    def __set_status(self, target: str, success: bool) -> None:
        """STATUS BAR ========== Show a quick message like 'flash succeeded' or
        'build failed' in a status bar that pops up at the bottom and disappears
        after a few seconds.

        ERROR MESSAGE ============= The error messages from a failed build or
        flash are not always so useful. Try to come up with a more useful error
        message and print it to the console.
        """
        css = functions.get_dark_css_tags()
        tab = css["tab"]
        red = css["red"]
        green = css["green"]
        blue = css["blue"]
        orange = css["orange"]
        end = css["end"]

        #! ---[ Show quick message ] --- !#
        # Show the quick message in the status bar.
        self.__status_clear_nr += 1
        if success:
            self.__status_lbl.setText(
                f"<b>status: {green}{target} succeeded{end}</b>"
            )

        #            if target == 'build':
        #                _pinconfiguratorwindow_.PinConfiguratorWindow.setBuildCodeState('succeeded')
        else:
            self.__status_lbl.setText(
                f"<b>status: {red}{target} failed{end}</b>"
            )

        #            if target == 'build':
        #                _pinconfiguratorwindow_.PinConfiguratorWindow.setBuildCodeState('failed')
        self.__status_bar_frm.show()
        self.__status_lbl.update()
        self.__console_widget.verticalScrollBar().setValue(
            self.__console_widget.verticalScrollBar().maximum()
        )
        # That's all there is to do if the procedure succeeded (unless for WCH,
        # where a special msg is needed). However, if the procedure failed, then
        # this function must continue to print a useful error message.
        if success:
            try:
                if (
                    "wch"
                    in data.current_project.get_board()
                    .get_board_dict()["manufacturer"]
                    .lower()
                ) or (
                    "wch"
                    in data.current_project.get_chip()
                    .get_chip_dict(None)["manufacturer"]
                    .lower()
                ):
                    if "10.2.0" in data.current_project.get_toolpath_seg().get_unique_id(
                        "COMPILER_TOOLCHAIN"
                    ):
                        message = data.current_project.get_special_wch_message()
                        self.__console_widget.printout_html(message)
                        self.__console_widget.print_toplevel_prompt_sig.emit()
            except:
                pass
            return

        #! ---[ Print useful error message ]--- !#
        def print_build_error(*args) -> None:
            # $ Print intro
            _message = data.current_project.get_build_error_suggestions()
            self.__console_widget.printout_html(_message)
            self.__console_widget.print_toplevel_prompt_sig.emit()
            return

        def print_flash_error(*args) -> None:
            # $ Print intro
            _message = data.current_project.get_flash_error_suggestions()
            self.__console_widget.printout_html(_message)
            self.__console_widget.print_toplevel_prompt_sig.emit()
            return

        # * Start
        # & Target is 'build'
        # Simply call the 'print_build_error()' subfunction
        if target.lower() == "build":
            print_build_error()
            return

        # & Target is 'flash'
        # Call the 'print_flash_error()' subfunction, but perhaps it's needed to
        # refresh the flashtool version nr first.
        if target.lower() == "flash":
            tool_obj: (
                _tool_obj_.ToolpathObj
            ) = data.current_project.get_toolpath_seg().get_toolpathObj(
                "FLASHTOOL"
            )
            if (tool_obj is not None) and (not tool_obj.has_version_info()):
                tool_obj.refresh_version_info(
                    callback=print_flash_error,
                    callbackArg=None,
                )
                return
            print_flash_error()
            return

        # & Other target
        # Nothing to print
        return

    def __clear_status(self, nr, *args) -> None:
        """Hide the whole status bar.

        Check if the nr tied to the QTimer corresponds to the latest clear-
        number. If yes, there has been no invocation of '__set_status()' in the
        meantime.
        """
        if (
            qt.sip.isdeleted(self)
            or qt.sip.isdeleted(self.__status_lbl)
            or qt.sip.isdeleted(self.__status_bar_frm)
        ):
            return
        if nr == self.__status_clear_nr:
            self.__status_lbl.setText("status:")
            self.__status_bar_frm.hide()
            return
        return

    def run_command(
        self,
        commandlist: List[str],
        callback: Optional[Callable],
    ) -> None:
        """
        Run the given command - provided as a List[str]. The callback is invoked
        as soon as the process ends - either because it returned an exit code or
        it was manually forced to stop (Abort clicked).
        """
        assert threading.current_thread() is threading.main_thread()
        origthread = qt.QThread.currentThread()
        if (not isinstance(commandlist, list)) or (len(commandlist) == 0):
            purefunctions.printc(
                f"\nERROR: Function run_command() in make_console.py invoked with\n"
                f"parameter commandlist = {q}{commandlist}{q}\n",
                color="error",
            )
            callback(False)
            return

        print(f"\n{commandlist[0]}")
        for i, cmd in enumerate(commandlist):
            if i > 0:
                print(f"    {cmd}")
        print("")

        def finish(success: bool, *args) -> None:
            if threading.current_thread() is not threading.main_thread():
                _sw_.switch_thread_modern(
                    qthread=origthread,
                    callback=finish,
                    success=success,
                )
                return
            assert threading.current_thread() is threading.main_thread()
            # TARGET
            # Normally, the second argument in the command list represents the
            # makefile target. Based on this argument, we can figure out if this
            # command represented a build, flash or clean.

            # STATUS BAR CLEANING
            # The status bar will be cleared after 5 secs. However, if a new
            # __set_status() call gets invoked in the meantime, we don't want the
            # clear_status() call from the previous timer to take effect! There-
            # fore, a global counter increments on each __set_status() call. Only
            # the timer that fired with the latest number will be allowed to do
            # its job.
            target = commandlist[1]
            self.__set_status(
                target=target,
                success=success,
            )

            # Emit global signal
            data.signal_dispatcher.makefile_command_executed.emit(
                target, success
            )

            qt.QTimer.singleShot(
                5000,
                functools.partial(
                    self.__clear_status,
                    self.__status_clear_nr,
                ),
            )
            if callable(success):
                callback(success)
            return

        # * Start
        assert threading.current_thread() is threading.main_thread()
        self.__console_widget.run_command(
            commandlist=commandlist,
            printout=True,
            callback=finish,
        )
        return

    def rescale_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        assert threading.current_thread() is threading.main_thread()

        def rescale_scrollbars(*args) -> None:
            self.__console_widget.verticalScrollBar().setStyleSheet(
                _sb_.get_vertical()
            )
            self.__console_widget.horizontalScrollBar().setStyleSheet(
                _sb_.get_horizontal()
            )
            self.__console_widget.verticalScrollBar().setContextMenuPolicy(
                qt.Qt.ContextMenuPolicy.NoContextMenu
            )
            self.__console_widget.horizontalScrollBar().setContextMenuPolicy(
                qt.Qt.ContextMenuPolicy.NoContextMenu
            )
            qt.QTimer.singleShot(20, finish)
            return

        def finish(*args) -> None:
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        size = data.get_general_icon_pixelsize()
        self.__console_widget.set_style()
        qt.QTimer.singleShot(20, rescale_scrollbars)
        return
