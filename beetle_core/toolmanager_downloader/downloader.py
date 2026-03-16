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
import gui.dialogs.popupdialog
import purefunctions
import serverfunctions
from components.singleton import Singleton
import os, threading, traceback
import components.thread_switcher as _sw_
import beetle_console.mini_console as _mini_console_
import bpathlib.file_power as _fp_
from various.kristofstuff import *


class Downloader(metaclass=Singleton):
    def __init__(self):
        assert threading.current_thread() is threading.main_thread()
        _sw_.register_thread(
            name="main",
            qthread=qt.QThread.currentThread(),
        )
        self.__mini_console: Optional[_mini_console_.MiniConsole] = None
        return

    @_sw_.run_outside_main("download_beetle_tool")
    def download_beetle_tool(
        self,
        tool_url: str,
        tool_folder: str,
        is_replacement: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Download the beetle tool and put it in the tool_folder, eg:

            - 'beetle_tools/gnu_arm_toolchain_9.2.1_9-2019-q4-major_32b'
            - 'beetle_tools/gnu_make_4.2.0_32b'
            - ...

        is_replacement == True  -> tool_folder must exist
                       == False -> tool_folder gets created

        > callback(success, callbackArg)
        """
        origthread = self.download_beetle_tool.origthread
        nonmainthread = self.download_beetle_tool.nonmainthread
        assert origthread is _sw_.get_qthread("main")
        suppress_final_err = False
        tool_url = serverfunctions.replace_base_url(tool_url)

        def create_miniconsole(*args) -> None:
            "[main thread]"
            assert qt.QThread.currentThread() is origthread
            assert threading.current_thread() is threading.main_thread()
            if self.__mini_console is not None:
                if qt.sip.isdeleted(self.__mini_console):
                    pass
                else:
                    self.__mini_console.close()
                self.__mini_console = None
            self.__mini_console = _mini_console_.MiniConsole("Download tool")
            qt.QTimer.singleShot(
                500,
                force_to_front,
            )
            return

        def force_to_front(*args) -> None:
            "[main thread]"
            try:
                if self.__mini_console is None:
                    pass
                elif qt.sip.isdeleted(self.__mini_console):
                    pass
                else:
                    self.__mini_console.raise_()
            except:
                traceback.print_exc()
            _sw_.switch_thread_modern(
                qthread=nonmainthread,
                callback=test_permissions,
            )
            return

        def test_permissions(*args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            nonlocal suppress_final_err
            test_write_perm_folder: Optional[str] = None
            if is_replacement:
                test_write_perm_folder = tool_folder
            else:
                test_write_perm_folder = os.path.dirname(tool_folder).replace(
                    "\\", "/"
                )
            if not os.path.isdir(test_write_perm_folder):
                self.__mini_console.printout(f"\n")
                self.__mini_console.printout(f"ERROR:\n", "#ef2929")
                self.__mini_console.printout(
                    f"This folder doesn{q}t exist:\n", "#ef2929"
                )
                self.__mini_console.printout(
                    f"    > {test_write_perm_folder}\n"
                )
                self.__mini_console.printout(f"\n")
                suppress_final_err = True
                abort()
                return
            if not purefunctions.test_write_permissions(
                test_write_perm_folder, True
            ):
                self.__mini_console.printout(f"\n")
                self.__mini_console.printout(f"ERROR:\n", "#ef2929")
                self.__mini_console.printout(
                    f"You don{q}t have write permissions on this folder:\n",
                    "#ef2929",
                )
                self.__mini_console.printout(
                    f"    > {test_write_perm_folder}\n"
                )
                self.__mini_console.printout(f"\n")
                self.__mini_console.printout(
                    f"Restart Embeetle with admin rights.\n", "#ef2929"
                )
                self.__mini_console.printout(f"\n")
                suppress_final_err = True
                abort()
                return
            print_intro()
            return

        def print_intro(*args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout(
                "----------------------------------\n", "#729fcf"
            )
            self.__mini_console.printout(
                "|          DOWNLOAD TOOL         |\n", "#729fcf"
            )
            self.__mini_console.printout(
                "----------------------------------\n", "#729fcf"
            )
            if not os.path.isdir(tool_folder):
                # $ Make directory
                success = _fp_.make_dir(
                    dir_abspath=tool_folder,
                    printfunc=self.__mini_console.printout,
                    catch_err=True,
                    overwr=False,
                )
                if not success:
                    abort()
                    return
                download()
                return
            # $ Switch back to main thread to show
            # $ a dialog window
            _sw_.switch_thread_modern(
                qthread=origthread,
                callback=ask_clean_permission_wait,
            )
            return

        def ask_clean_permission_wait(*args) -> None:
            "[main thread]"
            assert qt.QThread.currentThread() is origthread
            assert threading.current_thread() is threading.main_thread()
            # After raising the mini console to the front, a short wait is need-
            # ed before popping up another dialog. Otherwise, everything goes
            # again to the back.
            qt.QTimer.singleShot(500, ask_clean_permission)
            return

        def ask_clean_permission(*args) -> None:
            "[main thread]"
            assert qt.QThread.currentThread() is origthread
            assert threading.current_thread() is threading.main_thread()
            reply = gui.dialogs.popupdialog.PopupDialog.question(
                title_text="Clean folder",
                icon_path="icons/gen/clean.png",
                text=str(
                    f"Embeetle will delete everything in the folder:<br>"
                    f"<span style={dq}color:{q}#3465a4{q}{dq}>&nbsp;&nbsp;&nbsp;&nbsp;"
                    f"{q}{tool_folder}{q}</span><br>"
                    f"and place the downloaded tool inside.<br>"
                    f"Do you want to proceed?<br>"
                ),
            )
            if reply == qt.QMessageBox.StandardButton.No:
                _sw_.switch_thread_modern(
                    qthread=nonmainthread,
                    callback=abort,
                )
                return
            _sw_.switch_thread_modern(
                qthread=nonmainthread,
                callback=clean,
            )
            return

        def clean(*args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            success = _fp_.clean_dir(
                dir_abspath=tool_folder,
                printfunc=self.__mini_console.printout,
                catch_err=True,
            )
            if not success:
                abort()
                return
            download()
            return

        def download(*args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.download_file(
                url=tool_url,
                show_prog=True,
                callback=unzip,
                callbackArg=None,
            )
            return

        def unzip(success: bool, error_description, filepath, *args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            if not success:
                abort()
                return
            if not os.path.isfile(filepath):
                abort()
                return
            if not os.path.isdir(tool_folder):
                abort()
                return
            self.__mini_console.sevenunzip_file_to_dir(
                spath=filepath,
                dpath=tool_folder,
                show_prog=True,
                protocol=".7z",
                callback=finish_unzip,
                callbackArg=None,
                callbackThread=nonmainthread,
            )
            return

        def finish_unzip(arg) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            success, _ = arg
            if not success:
                abort()
                return
            finish()
            return

        def abort(*args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            if suppress_final_err == False:  # noqa
                self.__mini_console.printout("\n\n")
                self.__mini_console.printout(
                    "An error occured while downloading the tool.   \n",
                    "#ef2929",
                )
                self.__mini_console.printout(
                    "Please copy-paste the contents of this console,\n",
                    "#ef2929",
                )
                self.__mini_console.printout("and mail it to:\n", "#ef2929")
                self.__mini_console.printout("info@embeetle.com\n", "#729fcf")
                self.__mini_console.printout("\n")
            self.download_beetle_tool.invoke_callback_in_origthread(
                callback,
                False,
                callbackArg,
            )
            return

        def finish(*args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout("\n\n")
            self.__mini_console.printout("FINISH \n", "#fcaf3e")
            self.__mini_console.printout("-------\n", "#fcaf3e")
            self.__mini_console.printout(
                "Congratulations! You downloaded the tool successfully.\n",
                "#73d216",
            )
            self.__mini_console.printout("\n")

            def delayed_finish(*_args) -> None:
                # $ [non-main thread]
                assert qt.QThread.currentThread() is nonmainthread
                # I made close() thread safe
                self.__mini_console.close()
                self.download_beetle_tool.invoke_callback_in_origthread(
                    callback,
                    True,
                    callbackArg,
                )
                return

            qt.QTimer.singleShot(1000, delayed_finish)
            return

        # * Start
        # Briefly switch to the main thread just to create a MiniConsole() in-
        # stance there!
        _sw_.switch_thread_modern(
            qthread=origthread,
            callback=create_miniconsole,
        )
        return

