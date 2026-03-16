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
import os, threading, functools, re, traceback
import qt, data, purefunctions, functions, serverfunctions
import requests
import shlex
import components.thread_switcher as _sw_
import bpathlib.file_power as _fp_
import gui.stylesheets.progressbar as _progbar_style_
import beetle_console.console_widget as _console_widget_

nop = lambda *a, **k: None
q = "'"
dq = '"'


class MiniConsole(qt.QDialog):
    apply_extprogbar_val_sig = qt.pyqtSignal()
    apply_extprogbar_max_sig = qt.pyqtSignal()
    set_extprogbar_inf_sig = qt.pyqtSignal(bool)
    close_sig = qt.pyqtSignal()

    def __init__(self, title: str) -> None:
        """"""
        super().__init__()
        # $ WindowFlags
        self.setWindowFlags(
            self.windowFlags()  # noqa
            | qt.Qt.WindowType.Dialog
            | qt.Qt.WindowType.WindowTitleHint
            | qt.Qt.WindowType.WindowCloseButtonHint
        )
        assert threading.current_thread() is threading.main_thread()

        # $ Geometry
        try:
            w, h = functions.get_screen_size()
        except:
            s = functions.get_screen_size()
            w = s.width()
            h = s.height()
        self.setGeometry(
            int(w * 0.3),
            int(h * 0.2),
            int(w * 0.4),
            int(h * 0.6),
        )

        # $ Stylesheet
        self.setStyleSheet(
            f"""
        QWidget {{
            background  : {data.theme["fonts"]["default"]["background"]};
            color       : {data.theme["fonts"]["default"]["color"]};;
            font-family : {data.get_global_font_family()};
            font-size   : {data.get_general_font_pointsize()}pt;
            padding     : 0px;
            margin      : 0px;
        }}
        """
        )

        # $ Title
        self.setWindowTitle(title)
        try:
            self.setWindowIcon(qt.QIcon(data.application_icon_abspath))
        except:
            traceback.print_exc()

        # $ Layout
        self.__lyt = qt.QVBoxLayout()
        self.__lyt.setSpacing(0)
        self.__lyt.setContentsMargins(0, 0, 0, 0)
        self.__lyt.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.__lyt)

        # $ Console
        self.__console_widg = _console_widget_.ConsoleWidget(
            parent=self,
            readonly=True,
            cwd=os.getcwd(),
            fake_console=False,
            is_serial_monitor=False,
        )

        # $ Layouts
        self.__lyt.addWidget(self.__console_widg)
        self.show()

        # $ External progbar
        self.__extprogbar: Optional[qt.QProgressBar] = None
        self.__extprogbar_val: int = 0
        self.__extprogbar_max: int = 100
        self.apply_extprogbar_val_sig.connect(self.apply_extprogbar_val)
        self.apply_extprogbar_max_sig.connect(self.apply_extprogbar_max)
        self.set_extprogbar_inf_sig.connect(self.set_extprogbar_fad)
        self.__console_widg.inc_external_progbar_sig.connect(
            self.__inc_extprogbar
        )
        self.close_sig.connect(self.close)

        # $ Rejection callbacks
        self.__rejected = False
        self.__reject_callback: Optional[Callable] = None
        self.__reject_callbackArgs: Optional[List[Any]] = None
        self.__reject_callbackThread: Optional[qt.QThread] = None
        return

    def reject(self) -> None:
        """The user closes this dialog by clicking the red 'X' in the top-right
        corner."""
        self.__rejected = True
        super().reject()
        if self.__reject_callback is None:
            return
        if self.__reject_callbackThread is None:
            self.__reject_callbackThread = qt.QThread.currentThread()
        if self.__reject_callbackArgs is None:
            self.__reject_callbackArgs = []
        _sw_.switch_thread_modern(
            self.__reject_callbackThread,
            self.__reject_callback,
            *self.__reject_callbackArgs,
        )
        return

    def set_cwd(self, cwd: str) -> None:
        """"""
        self.__console_widg.set_cwd(cwd, True)
        return

    def get_cwd(self) -> str:
        """"""
        return self.__console_widg.get_cwd()

    # ^                                  PROGBAR                                   ^#
    # % ========================================================================== %#
    # % Progbar stuff                                                              %#
    # %                                                                            %#

    def assign_external_progbar(self, progbar: qt.QProgressBar) -> None:
        """Assign an external progbar to this MiniConsole()-instance."""
        if qt.sip.isdeleted(self):
            return
        assert threading.current_thread() is threading.main_thread()
        assert self.__extprogbar is None
        self.__extprogbar = progbar
        return

    @qt.pyqtSlot(int)
    def __inc_extprogbar(self, val: int) -> None:
        """This method is tied to the 'inc_external_progbar_sig' from the
        'ConsoleWidget()'."""
        if qt.sip.isdeleted(self):
            return
        assert isinstance(val, int)
        self.set_extprogbar_val(self.__extprogbar_val + val)
        return

    def set_extprogbar_val(self, val: int) -> None:
        """Set the given value, but don't apply it immediately.

        That happens through a signal if we're not in the main thread now.
        """
        # & Checks
        if qt.sip.isdeleted(self):
            return
        if self.__extprogbar is None:
            # purefunctions.printc(
            #     f'WARNING: set_extprogbar_val({val}) was invoked on a '
            #     f'MiniConsole() while it had no progbar assigned.',
            #     color='error',
            # )
            return
        # & Set value
        self.__extprogbar_val = val
        # & Request to apply value
        if threading.current_thread() is threading.main_thread():
            self.apply_extprogbar_val()
            return
        self.apply_extprogbar_val_sig.emit()
        return

    @qt.pyqtSlot()
    def apply_extprogbar_val(self) -> None:
        """Apply the stored value on the external progbar."""
        # * Checks
        if qt.sip.isdeleted(self):
            return
        if self.__extprogbar is None:
            # purefunctions.printc(
            #     'ERROR: apply_extprogbar_val() was invoked on a '
            #     'MiniConsole() while it had no progbar assigned.',
            #     color='error',
            # )
            return
        # * Apply value
        if self.__extprogbar_val > self.__extprogbar_max:
            purefunctions.printc(
                f"ERROR: The external progbar has a value too high!\n"
                f"val = {self.__extprogbar_val}\n"
                f"max = {self.__extprogbar_max}\n",
                color="error",
            )
            self.__extprogbar_val = self.__extprogbar_max
        if self.__extprogbar_val < 0:
            purefunctions.printc(
                f"ERROR: The external progbar has a negative value!\n"
                f"val = {self.__extprogbar_val}\n"
                f"max = {self.__extprogbar_max}\n",
                color="error",
            )
            self.__extprogbar_val = 0
        self.__extprogbar.setValue(self.__extprogbar_val)
        return

    def set_extprogbar_max(self, val: int) -> None:
        """Set the given maximum value, but don't apply it immediately.

        That happens through a signal if we're not in the main thread now.
        """
        # & Checks
        if qt.sip.isdeleted(self):
            return
        if self.__extprogbar is None:
            # purefunctions.printc(
            #     f'WARNING: set_extprogbar_max({val}) was invoked on a '
            #     f'MiniConsole() while it had no progbar assigned.',
            #     color='error',
            # )
            return
        # & Set value
        self.__extprogbar_max = val
        # & Request to apply value
        if threading.current_thread() is threading.main_thread():
            self.apply_extprogbar_max()
            return
        self.apply_extprogbar_max_sig.emit()
        return

    @qt.pyqtSlot()
    def apply_extprogbar_max(self) -> None:
        """Apply the stored value on the external progbar."""
        # * Checks
        if qt.sip.isdeleted(self):
            return
        if self.__extprogbar is None:
            # purefunctions.printc(
            #     'ERROR: apply_extprogbar_val() was invoked on a '
            #     'MiniConsole() while it had no progbar assigned.',
            #     color='error',
            # )
            return
        # * Apply value
        if self.__extprogbar_val > self.__extprogbar_max:
            raise RuntimeError(
                f"ERROR: The external progbar has a value too high!\n"
                f"val = {self.__extprogbar_val}\n"
                f"max = {self.__extprogbar_max}\n"
            )
        self.__extprogbar.setMaximum(self.__extprogbar_max)
        return

    @qt.pyqtSlot(bool)
    def set_extprogbar_fad(self, fad: bool) -> None:
        """
        Make the external progbar 'fading' - or not. If set to 'fading', both
        the maximum and value are set to 0. Also, increment signals are dis-
        abled.
        """
        # & Checks
        if qt.sip.isdeleted(self):
            return
        if self.__extprogbar is None:
            # purefunctions.printc(
            #     'WARNING: set_extprogbar_fad() was invoked on a '
            #     'MiniConsole() while it had no progbar assigned.',
            #     color='error',
            # )
            return
        # & Clear values & disable increment signals
        if fad:
            self.activate_extprogbar_logging(False)
            self.__extprogbar_val = 0
            self.__extprogbar_max = 0
        # & Set fading
        # Can only be done in main thread. Launch signal to
        # return if needed.
        if threading.current_thread() is not threading.main_thread():
            self.set_extprogbar_inf_sig.emit(fad)
            return
        assert threading.current_thread() is threading.main_thread()
        if fad:
            self.__extprogbar.setStyleSheet(
                _progbar_style_.get_faded_style(color="green")
            )
        else:
            self.__extprogbar.setStyleSheet(
                _progbar_style_.get_unfaded_style(color="green")
            )
        self.__extprogbar.style().unpolish(self.__extprogbar)
        self.__extprogbar.style().polish(self.__extprogbar)
        return

    def __start_ext_progbar(
        self,
        max_val: int,
        incr_str: Optional[str] = None,
    ) -> None:
        """Prepare the external progbar. The progbar will be cleared and given
        a.

        maximal value. Provide a string to look for in the output of the proc-
        cess - if the increments would come from a process.
        """
        self.set_extprogbar_fad(False)
        self.set_extprogbar_max(max_val)
        self.set_extprogbar_val(0)
        self.__console_widg.register_inc_str(incr_str)
        return

    def __stop_ext_progbar(
        self,
        make_full: bool,
    ) -> None:
        """Stop the external progbar.

        If 'make_full' is True, the progbar is shown to be full. Otherwise, it's
        shown to be empty.
        """
        self.__console_widg.register_inc_str(None)
        self.set_extprogbar_fad(False)
        self.set_extprogbar_max(100)
        if make_full:
            self.set_extprogbar_val(100)
        else:
            self.set_extprogbar_val(0)
        return

    def activate_extprogbar_logging(
        self,
        active: bool,
        incr_chars: str = "\n",
    ) -> None:
        """Activate or deactivate the external progbar. If active, it will
        trigger.

        increment signals for each 'incr_chars' found in the output written to
        the console - regardless if that output is written from a process or
        through direct write calls.

        The increment signals can be grouped - one increment signal carrying a
        number of increments.
        """
        if qt.sip.isdeleted(self):
            return
        if active:
            self.__console_widg.register_inc_str(incr_chars)
        else:
            self.__console_widg.register_inc_str(None)
        return

    # ^                                  PRINTOUT                                  ^#
    # % ========================================================================== %#
    # % Print functions.                                                           %#
    # %                                                                            %#

    def get_printfunc(self) -> Callable:
        if qt.sip.isdeleted(self):
            return print
        return self.__console_widg.printout_text

    def get_printhtmlfunc(self) -> Callable:
        if qt.sip.isdeleted(self):
            return print
        return self.__console_widg.printout_html

    def printout(self, outputStr: str, color: str = "#ffffff") -> None:
        if qt.sip.isdeleted(self):
            return
        self.__console_widg.printout_text(outputStr, color)

    def printout_html(self, outputStr: str, color: str = "#ffffff") -> None:
        if qt.sip.isdeleted(self):
            return
        self.__console_widg.printout_html(outputStr)

    def clear(self) -> None:
        if qt.sip.isdeleted(self):
            return
        self.__console_widg.clear()

    def start_progbar(self, title: str) -> None:
        if qt.sip.isdeleted(self):
            return
        self.__console_widg.start_progbar(title)
        return

    def set_progbar_val(self, fval: float) -> None:
        if qt.sip.isdeleted(self):
            return
        assert fval <= 100, f"fval = {fval}"
        assert fval >= 0, f"fval = {fval}"
        self.__console_widg.set_progbar_val(fval)
        return

    def close_progbar(self) -> None:
        if qt.sip.isdeleted(self):
            return
        self.__console_widg.close_progbar()
        return

    @qt.pyqtSlot()
    def close(self):
        if qt.sip.isdeleted(self):
            return False
        if threading.current_thread() is not threading.main_thread():
            self.close_sig.emit()
            return False
        return super().close()

    def kill_process(self):
        self.__console_widg.close_command()
        return

    # ^                                  COMMANDS                                  ^#
    # % ========================================================================== %#
    # % Commands                                                                   %#
    # %                                                                            %#

    def execute_machine_cmd(
        self,
        cmd: str,
        callback: Optional[Callable],
        callbackArg: Any,
        callbackThread: qt.QThread,
        path_addition: Optional[List[str]] = None,
        internal_call: bool = False,
    ) -> None:
        """
        :param cmd:             Command string to execute.
        :param callback:        Callback when process has finished.
        :param callbackArg:     callbackArg=(success, code, callbackArg)
        :param path_addition:   Path(s) to be added to the PATH env variable
        """
        if not internal_call:
            self.__reject_callback = callback
            self.__reject_callbackArgs = [
                (False, 1, callbackArg),
            ]
            self.__reject_callbackThread = callbackThread

        def start(*args) -> None:
            if not threading.current_thread() is threading.main_thread():
                _sw_.switch_thread(
                    qthread=_sw_.get_qthread("main"),
                    callback=start,
                    callbackArg=None,
                    notifycaller=None,
                )
                return
            assert threading.current_thread() is threading.main_thread()
            self.clear_log()
            self.__console_widg.run_command(
                commandlist=shlex.split(cmd),
                printout=True,
                path_addition=path_addition,
                callback=finish,
            )
            return

        def finish(success: bool, *args) -> None:
            code = 0
            if not success:
                code = 1
            if not internal_call:
                self.__reject_callback = None
                self.__reject_callbackArgs = None
                self.__reject_callbackThread = None
            if self.__rejected:
                return
            _sw_.switch_thread(
                qthread=callbackThread,
                callback=callback,
                callbackArg=(success, code, callbackArg),
                notifycaller=None,
            )
            return

        # * Start
        start()
        return

    def clear_log(self) -> None:
        """"""
        self.__console_widg.clear_log()
        return

    def get_log(self) -> str:
        """"""
        return self.__console_widg.get_log()

    # ^                                   RSYNC                                    ^#
    # % ========================================================================== %#
    # % Rsync                                                                      %#
    # %                                                                            %#

    def rsync_server_to_local(
        self,
        remote_dirpath: str,
        local_dirpath: str,
        exclusions: Optional[List[str]],
        callback: Optional[Callable],
        callbackArg: Any,
        callbackThread: qt.QThread,
    ) -> None:
        """
        Apply the rsync command:
            rsync -av remote_username@remote_domain:remote_dirpath local_dirpath

        :param remote_dirpath:      Absolute directory path on server.
        :param local_dirpath:       Absolute directory path on local computer.
        :param callback:            Callback when rsync has finished. @param: (success, callbackArg)
        :param callbackArg:         callbackArg=(success, callbackArg)
        :param callbackThread:      qt.QThread you want the callback to run in.
        """
        # $ Input validation
        if remote_dirpath.startswith("C:"):
            raise RuntimeError()

        # $ Threading
        origthread: qt.QThread = qt.QThread.currentThread()
        original_path: Optional[str] = None
        assert threading.current_thread() is not threading.main_thread()

        # $ Rsync parameters
        remote_username = "embeetle-rsync"  # "embeetle-rsync" for downstream, "embeetle" otherwise
        remote_domain = serverfunctions.get_rsync_remote_domain()
        known_hosts_url = serverfunctions.get_rsync_known_hosts_url()
        client_id_rsa_url = serverfunctions.get_rsync_client_id_rsa_url()
        rsyncpath, sshpath, exefolder, dllfolder = (
            functions.get_rsync_location()
        )
        known_hosts_tempfilepath: Optional[str] = None
        client_id_rsa_tempfilepath: Optional[str] = None

        # $ Store callback for when user clicks `X`
        self.__reject_callback = callback
        self.__reject_callbackArgs = [
            (False, callbackArg),
        ]
        self.__reject_callbackThread = callbackThread

        def print_msg(txt: str) -> None:
            print(txt)
            self.__console_widg.printout_text(txt)
            return

        def download_keys(*args) -> None:
            assert qt.QThread.currentThread() is origthread
            self.__console_widg.printout_text(
                "STEP 2: Download ssh keys\n" "-------------------------\n",
                "#fcaf3e",
            )

            def download_known_hosts(*_args) -> None:
                assert qt.QThread.currentThread() is origthread
                self.download_file(
                    url=known_hosts_url,
                    show_prog=True,
                    callback=download_client_id_rsa,
                    callbackArg=None,
                    internal_call=True,
                )
                return

            def download_client_id_rsa(
                success: bool,
                error_description: Optional[str],
                filepath: Optional[str],
                *_args,
            ) -> None:
                assert qt.QThread.currentThread() is origthread
                if (success != True) or (filepath is None):
                    print_msg(f"ERROR: Failed to download '{known_hosts_url}'!")
                    print_msg(error_description)
                    finish(False)
                    return
                print_msg(f"Downloaded '{known_hosts_url}' to '{filepath}'")
                nonlocal known_hosts_tempfilepath
                known_hosts_tempfilepath = filepath
                self.download_file(
                    url=client_id_rsa_url,
                    show_prog=True,
                    callback=finish_downloads,
                    callbackArg=None,
                    internal_call=True,
                )
                return

            def finish_downloads(
                success: bool,
                error_description: Optional[str],
                filepath: Optional[str],
                *_args,
            ) -> None:
                assert qt.QThread.currentThread() is origthread
                if (success != True) or (filepath is None):
                    print_msg(
                        f"ERROR: Failed to download '{client_id_rsa_url}'!"
                    )
                    print_msg(error_description)
                    finish(False)
                    return
                print_msg(f"Downloaded '{client_id_rsa_url}' to '{filepath}'")
                nonlocal client_id_rsa_tempfilepath
                client_id_rsa_tempfilepath = filepath
                get_nr_transfers()
                return

            download_known_hosts()
            return

        def get_nr_transfers(*args) -> None:
            assert qt.QThread.currentThread() is origthread
            self.__console_widg.printout_text(
                "STEP 3: Rsync dry-run: get nr of transfers\n"
                "------------------------------------------",
                "#fcaf3e",
            )
            self.set_extprogbar_fad(True)
            cmd = " ".join(
                [
                    f"{dq}{rsyncpath}{dq}",
                    f"-av",
                    f"--copy-links",
                    f"--partial",
                    f"--partial-dir=.rsync-partial",
                    f"--delete",
                    f"--dry-run",
                    f"--stats",
                    str(
                        f"-e {dq}{q}{sshpath}{q} -i {q}{purefunctions.get_short_path_name(client_id_rsa_tempfilepath)}{q} "
                        f"-o UserKnownHostsFile={q}{purefunctions.get_short_path_name(known_hosts_tempfilepath)}{q}{dq}"
                    ),
                    f"{remote_username}@{remote_domain}:{remote_dirpath}",
                    f"./",
                ]
            )
            self.execute_machine_cmd(
                cmd=cmd,
                callback=process_rsync_output,
                callbackArg=None,
                callbackThread=origthread,
                path_addition=[
                    exefolder,
                    dllfolder,
                ],
                internal_call=True,
            )
            return

        def process_rsync_output(arg) -> None:
            assert qt.QThread.currentThread() is origthread
            success, code, _ = arg
            n = -1
            if (success == False) or (code != 0):
                run_rsync(-1)
                return
            try:
                p = re.compile(
                    r"(Number of created files:)\s*([\d,]+)",
                    re.MULTILINE,
                )
                match = p.search(self.get_log())
                n1 = int(match.group(2).replace(",", ""))
                p = re.compile(
                    r"(Number of deleted files:)\s*([\d,]+)",
                    re.MULTILINE,
                )
                match = p.search(self.get_log())
                n2 = int(match.group(2).replace(",", ""))
                n = n1 + n2
            except:
                run_rsync(-1)
                return
            run_rsync(n)
            return

        def run_rsync(n: int, *args) -> None:
            assert qt.QThread.currentThread() is origthread
            if n == -1:
                print_msg("ERROR: __get_nr_remote_transfers__ returned -1!")
                finish(False)
                return
            self.__console_widg.printout_text(
                "\n\n" "STEP 4: Rsync run\n" "-----------------",
                "#fcaf3e",
            )
            if n != 0:
                self.__start_ext_progbar(
                    max_val=n,
                    incr_str="\n",
                )
            cmd = " ".join(
                [
                    f"{dq}{rsyncpath}{dq}",
                    "-av",
                    "--copy-links",
                    "--partial",
                    "--partial-dir=.rsync-partial",
                    "--delete",
                    str(
                        f"-e {dq}{q}{sshpath}{q} -i {q}{purefunctions.get_short_path_name(client_id_rsa_tempfilepath)}{q} "
                        f"-o UserKnownHostsFile={q}{purefunctions.get_short_path_name(known_hosts_tempfilepath)}{q}{dq}"
                    ),
                    f"{remote_username}@{remote_domain}:{remote_dirpath}",
                    "./",
                ]
            )
            self.execute_machine_cmd(
                cmd=cmd,
                callback=restore_cwd,
                callbackArg=None,
                callbackThread=origthread,
                path_addition=[
                    exefolder,
                    dllfolder,
                ],
                internal_call=True,
            )
            return

        def restore_cwd(arg) -> None:
            assert qt.QThread.currentThread() is origthread
            success, code, _ = arg
            if (success == False) or (code != 0):
                finish(False)
                return
            self.__console_widg.printout_text(
                "\n\n"
                "STEP 5: Return to original path\n"
                "-------------------------------",
                "#fcaf3e",
            )
            self.__console_widg.set_cwd(original_path, True)
            finish(True)
            return

        def finish(arg) -> None:
            assert qt.QThread.currentThread() is origthread
            success = None
            if isinstance(arg, bool):
                success = arg
            else:
                success, code, _ = arg
                if code != 0:
                    success = False
            self.__stop_ext_progbar(make_full=True)
            assert qt.QThread.currentThread() is origthread
            self.__reject_callback = None
            self.__reject_callbackArgs = None
            self.__reject_callbackThread = None
            if self.__rejected:
                return
            _sw_.switch_thread(
                qthread=callbackThread,
                callback=callback,
                callbackArg=(success, callbackArg),
                notifycaller=nop,
            )
            return

        # * Start
        self.__console_widg.printout_text(
            "STEP 1: Go to local directory\n" "------------------------------",
            "#fcaf3e",
        )
        original_path = self.__console_widg.get_cwd().replace("\\", "/")
        self.__console_widg.set_cwd(local_dirpath, True)
        self.__console_widg.printout_text("\n")
        download_keys()
        return

    # ^                             GENERAL FUNCTIONS                              ^#
    # % ========================================================================== %#
    # % General functions                                                          %#
    # %                                                                            %#

    def copy_folder(
        self,
        sourcedir_abspath: str,
        targetdir_abspath: str,
        exclusions: Optional[List[str]],
        show_prog: bool,
        delsource: bool,
        callback: Optional[Callable],
        callbackArg: Any,
        internal_call: bool = False,
    ) -> None:
        """Copy a big folder from the given 'sourcedir_abspath' to
        'targetdir_abspath'. If the target directory already exists, it will be
        cleaned first.

        :param sourcedir_abspath:   Source directory.
        :param targetdir_abspath:   Target directory.
        :param exclusions:          List of folder- and/or filenames that should
                                    be excluded from the copy. Each entry in
                                    this list gets fnmatch()-ed against file-
                                    and directory names while traversing the
                                    source folder:
                                        - filename match   => file gets ignored
                                        - foldername match => folder and content
                                                              gets ignored
        :param show_prog:           Show a progressbar.
        :param delsource:           Perform a move instead of a copy.

        The callback happens in the same thread that you entered this function
        with:

            > callback(success, callbackArg)
        """
        assert threading.current_thread() is not threading.main_thread()
        origthread = qt.QThread.currentThread()
        if not internal_call:
            self.__reject_callback = callback
            self.__reject_callbackArgs = [
                False,
                callbackArg,
            ]
            self.__reject_callbackThread = origthread

        def wait_for_progbar(*args) -> None:
            "[origthread]"
            assert qt.QThread.currentThread() is origthread
            if self.__console_widg.is_progbar_open():
                qt.QTimer.singleShot(50, dircopy)
                return
            qt.QTimer.singleShot(150, wait_for_progbar)
            return

        def dircopy(*args) -> None:
            "[origthread]"
            assert qt.QThread.currentThread() is origthread
            j: int = 0  # Cntr on reporthook calls.
            jmax: int = 1  # Max for cntr, reporthook should

            # update progressbar on overflow.
            def reporthook(i, n):
                nonlocal j, jmax
                j += 1
                if j > jmax:
                    j = 0
                    jmax = int(n / 100.0)  # Calculate 'jmax' such that cntr
                    # overflow happens 100 times.
                    perc = 100.0 * (i / n)
                    if show_prog:
                        self.set_progbar_val(perc)
                return

            printfunc = None
            if show_prog:
                printfunc = print
            else:
                printfunc = self.get_printfunc()
            if delsource:
                success = _fp_.move_dir(
                    sourcedir_abspath=sourcedir_abspath,
                    targetdir_abspath=targetdir_abspath,
                    exclusions=exclusions,
                    reporthook=reporthook,
                    printfunc=printfunc,
                    catch_err=True,
                    overwr=True,
                )
            else:
                success = _fp_.copy_dir(
                    sourcedir_abspath=sourcedir_abspath,
                    targetdir_abspath=targetdir_abspath,
                    exclusions=exclusions,
                    reporthook=reporthook,
                    printfunc=printfunc,
                    catch_err=True,
                    overwr=True,
                )
            if show_prog and self.__console_widg.is_progbar_open():
                self.set_progbar_val(100.0)
            if not success:
                finish(False)
                return
            qt.QTimer.singleShot(100, lambda: finish(True))
            return

        def finish(success: bool) -> None:
            "[origthread]"
            assert qt.QThread.currentThread() is origthread
            if self.__console_widg.is_progbar_open():
                self.close_progbar()
            self.__console_widg.printout_text("\n")
            if not internal_call:
                self.__reject_callback = None
                self.__reject_callbackArgs = None
                self.__reject_callbackThread = None
            if self.__rejected:
                return
            callback(success, callbackArg)
            return

        if show_prog:
            if self.__console_widg.is_progbar_open():
                raise IOError("Progbar already open!")
            if delsource:
                self.start_progbar("Move:")
            else:
                self.start_progbar("Copy:")
            wait_for_progbar()
            return
        dircopy()
        return

    def sevenzip_dir_to_file(
        self,
        sourcedir_abspath: str,
        targetfile_abspath: str,
        forbidden_dirnames: Optional[List[str]],
        forbidden_filenames: Optional[List[str]],
        show_prog: bool,
        callback: Optional[Callable],
        callbackArg: Any,
        callbackThread: qt.QThread,
        internal_call: bool = False,
    ) -> None:
        """Zip the given folder into a .7z file.

        :param sourcedir_abspath: Folder getting zipped. Must exist.
        :param targetfile_abspath: Target '.7z', '.zip' or '.tar' file. If
            exists, gets deleted first.
        :param show_prog: Show a progressbar.
        :param callback: Provide a callback.
        :param callbackArg: callbackArg=(success, callbackArg)
        :param callbackThread: qt.QThread you want the callback to run in.
        """
        assert threading.current_thread() is not threading.main_thread()
        if not internal_call:
            self.__reject_callback = callback
            self.__reject_callbackArgs = [
                (False, callbackArg),
            ]
            self.__reject_callbackThread = callbackThread
        assert (
            targetfile_abspath.endswith(".zip")
            or targetfile_abspath.endswith(".7z")
            or targetfile_abspath.endswith(".tar.gz")
        )
        origthread = qt.QThread.currentThread()

        def dirzip(*args) -> None:
            success = _fp_.sevenzip_dir_to_file(
                sourcedir_abspath=sourcedir_abspath,
                targetfile_abspath=targetfile_abspath,
                forbidden_dirnames=forbidden_dirnames,
                forbidden_filenames=forbidden_filenames,
                printfunc=self.get_printfunc(),
                catch_err=True,
                overwr=True,
            )
            self.__console_widg.printout_text("\n")
            if not success:
                finish(False)
                return
            qt.QTimer.singleShot(50, lambda: finish(True))
            return

        def finish(success: bool) -> None:
            assert qt.QThread.currentThread() is origthread
            if not internal_call:
                self.__reject_callback = None
                self.__reject_callbackArgs = None
                self.__reject_callbackThread = None
            if self.__rejected:
                return
            _sw_.switch_thread(
                qthread=callbackThread,
                callback=callback,
                callbackArg=(success, callbackArg),
                notifycaller=nop,
            )
            return

        qt.QTimer.singleShot(50, dirzip)
        return

    def sevenunzip_file_to_dir(
        self,
        spath: str,
        dpath: str,
        show_prog: bool,
        protocol: str,
        callback: Optional[Callable],
        callbackArg: Any,
        callbackThread: qt.QThread,
        internal_call: bool = False,
    ) -> None:
        """Unzip the given file to its original directory.

        :param spath:
        :param dpath:
        :param callback:
        :param callbackArg:
        :param callbackThread:
        :return:
        """
        assert threading.current_thread() is not threading.main_thread()
        if not internal_call:
            self.__reject_callback = callback
            self.__reject_callbackArgs = [
                (False, callbackArg),
            ]
            self.__reject_callbackThread = callbackThread
        origthread = qt.QThread.currentThread()

        def dirunzip(*args):
            success = _fp_.sevenunzip_file_to_dir(
                sourcefile_abspath=spath,
                targetdir_abspath=dpath,
                printfunc=self.get_printfunc(),
                catch_err=True,
                overwr=True,
                protocol=protocol,
            )
            self.__console_widg.printout_text("\n")
            if not success:
                finish(False)
                return
            qt.QTimer.singleShot(50, lambda: finish(True))
            return

        def finish(success):
            assert qt.QThread.currentThread() is origthread
            if not internal_call:
                self.__reject_callback = None
                self.__reject_callbackArgs = None
                self.__reject_callbackThread = None
            if self.__rejected:
                return
            _sw_.switch_thread(
                qthread=callbackThread,
                callback=callback,
                callbackArg=(success, callbackArg),
                notifycaller=None,
            )
            return

        qt.QTimer.singleShot(50, dirunzip)
        return

    def download_file(
        self,
        url: str,
        show_prog: bool,
        callback: Optional[Callable],
        callbackArg: Any,
        internal_call: bool = False,
    ) -> None:
        """Download a big file from the given url, and show an ASCII-art
        progressbar meanwhile. The file is downloaded to a temporary folder in
        the OS. The filepath is passed on as argument to the callback.

        :param url:       eg. https://embeetle.com/downloads/projects_m2/stmicro/beetle/baremetal/beetle_f767zi.7z
        :param show_prog: Show a progressbar.

        CALLBACK
        ========
        The following parameters are fed to the callback:
        > callback(success, error_description, filepath, callbackArg)

            success:            [bool] True if download succeeded.

            error_description:  [str] None if download succeeded, otherwise one
                                of these:
                                    - 'urllib.error.ContentTooShortError'
                                    - 'urllib.error.HTTPError'
                                    - 'urllib.error.URLError'
                                    - 'socket.timeout'
                                    - 'other'

            filepath:           [str] Path to the downloaded file. None if failed.

            callbackArg:        [Any] Whatever you passed to this function.
        """
        assert threading.current_thread() is not threading.main_thread()
        origthread = qt.QThread.currentThread()
        if not internal_call:
            self.__reject_callback = callback
            self.__reject_callbackArgs = [
                False,  # success
                "Console closed",  # error_description
                None,  # filepath
                callbackArg,  # callbackArg
            ]
            self.__reject_callbackThread = origthread
        error_description: Optional[str] = None

        def stopfunc(*args) -> bool:
            return self.__rejected

        def download(*args) -> None:
            assert qt.QThread.currentThread() is origthread
            nonlocal error_description
            j: int = 0  # Cntr on reporthook calls
            jmax: int = (
                1  # Max for cntr, reporthook should update progressbar on overflow
            )

            def reporthook(*_args) -> None:
                nonlocal j
                nonlocal jmax
                j += 1
                if j > jmax:
                    j = 0
                    bnr, bsize, tsize = _args
                    # Calculate 'jmax' such that cntr overflow happens 100 times
                    jmax = int((tsize / bsize) / 100.0)
                    perc: float = 0
                    if tsize != 0:
                        perc = min(100.0, 100.0 * ((bnr * bsize) / tsize))
                    if (tsize == 0) or (perc > 100.0) or (perc < 0.0):
                        purefunctions.printc(
                            f"\n"
                            f"ERROR: serverfunctions.urlretrieve_beetle() gave wrong\n"
                            f"numbers to the reporthook:\n"
                            f"    - bnr   = {bnr}\n"
                            f"    - bsize = {bsize}\n"
                            f"    - tsize = {tsize}\n"
                            f"    - perc  = {perc}\n"
                            f"\n",
                            color="error",
                        )
                        perc = 100.0
                    if show_prog:
                        self.set_progbar_val(perc)
                return

            try:
                # & READ URL
                filepath, response = serverfunctions.urlretrieve_beetle(
                    url=url,
                    reporthook=reporthook,
                    stopfunc=stopfunc,
                )
            except requests.exceptions.ConnectionError as _e:
                error_description = "requests.exceptions.ConnectionError"
                err_str = traceback.format_exc()
                self.close_progbar() if show_prog else nop()
                self.__console_widg.printout_text(
                    f"\n" f"ERROR: Connection error\n" f"{err_str}\n",
                    "#ef2929",
                )
                purefunctions.printc(
                    "ERROR: Connection error\n",
                    color="error",
                )
                purefunctions.printc(
                    f"{err_str}\n",
                    color="error",
                )
                qt.QTimer.singleShot(
                    100,
                    functools.partial(finish, False, None),
                )
                return

            except requests.exceptions.Timeout as _e:
                error_description = "requests.exceptions.Timeout"
                err_str = traceback.format_exc()
                self.close_progbar() if show_prog else nop()
                self.__console_widg.printout_text(
                    "\n" "ERROR: Timeout\n" f"{err_str}\n",
                    "#ef2929",
                )
                purefunctions.printc(
                    "ERROR: Timeout\n",
                    color="error",
                )
                purefunctions.printc(
                    f"{_e}\n",
                    color="error",
                )
                qt.QTimer.singleShot(
                    100,
                    functools.partial(finish, False, None),
                )
                return

            except requests.exceptions.HTTPError as _e:
                error_description = "requests.exceptions.HTTPError"
                err_str = traceback.format_exc()
                self.close_progbar() if show_prog else nop()
                self.__console_widg.printout_text(
                    f"\n" f"ERROR: HTTP error\n" f"{err_str}\n",
                    "#ef2929",
                )
                purefunctions.printc(
                    "ERROR: HTTP error\n",
                    color="error",
                )
                purefunctions.printc(
                    f"{err_str}\n",
                    color="error",
                )
                qt.QTimer.singleShot(
                    100,
                    functools.partial(finish, False, None),
                )
                return

            except requests.exceptions.ContentDecodingError as _e:
                error_description = "requests.exceptions.ContentDecodingError"
                err_str = traceback.format_exc()
                self.close_progbar() if show_prog else nop()
                self.__console_widg.printout_text(
                    f"\n" f"ERROR: Content decoding error\n" f"{err_str}\n",
                    "#ef2929",
                )
                purefunctions.printc(
                    "ERROR: Content decoding error\n",
                    color="error",
                )
                purefunctions.printc(
                    f"{err_str}\n",
                    color="error",
                )
                qt.QTimer.singleShot(
                    100,
                    functools.partial(finish, False, None),
                )
                return

            except requests.exceptions.RequestException as _e:
                error_description = "requests.exceptions.RequestException"
                err_str = traceback.format_exc()
                self.close_progbar() if show_prog else nop()
                self.__console_widg.printout_text(
                    f"\n" f"ERROR: Request error\n" f"{err_str}\n",
                    "#ef2929",
                )
                purefunctions.printc(
                    "ERROR: Request error\n",
                    color="error",
                )
                purefunctions.printc(
                    f"{err_str}\n",
                    color="error",
                )
                qt.QTimer.singleShot(
                    100,
                    functools.partial(finish, False, None),
                )
                return

            except RuntimeError as _e:
                error_description = "RuntimeError"
                err_str = str(_e)
                self.close_progbar() if show_prog else nop()
                self.__console_widg.printout_text(
                    f"\n" f"ERROR: {err_str}\n",
                    "#ef2929",
                )
                purefunctions.printc(
                    f"ERROR: {err_str}\n",
                    color="error",
                )
                qt.QTimer.singleShot(
                    100,
                    functools.partial(finish, False, None),
                )
                return

            except Exception as _e:
                error_description = "other"
                err_str = traceback.format_exc()
                self.close_progbar() if show_prog else nop()
                self.__console_widg.printout_text(
                    f"\n"
                    f"ERROR: An unexpected error occurred\n"
                    f"{err_str}\n",
                    "#ef2929",
                )
                purefunctions.printc(
                    "ERROR: An unexpected error occurred\n",
                    color="error",
                )
                purefunctions.printc(
                    f"{err_str}\n",
                    color="error",
                )
                qt.QTimer.singleShot(
                    100,
                    functools.partial(finish, False, None),
                )
                return

            try:
                # & PRINT HEADERS
                filepath = filepath.replace("\\", "/")
                filesize = os.path.getsize(filepath) / (
                    1024 * 1024
                )  # Convert bytes to MB
                filesize_str = f"{filesize:.2f}"
                headermsg = str(response.headers)
                p = re.compile(r"^(.*?:)", re.MULTILINE)
                headermsg = p.sub(
                    '<span style="color:#fce94f;">\\1</span>',
                    headermsg,
                )
                headermsg = headermsg.replace("\n", "<br>")
                self.set_progbar_val(100.0) if show_prog else nop()
                self.close_progbar() if show_prog else nop()
                v1 = filepath.replace(" ", "&nbsp;")
                v2 = filesize_str.replace(
                    ".", ","
                )  # Replace dot with comma for decimal separator if needed
                self.__console_widg.printout_html(
                    "<br>"
                    f'<span style="color:#fce94f;">File&nbsp;path:</span>&nbsp;{v1}<br>'
                    f'<span style="color:#fce94f;">File&nbsp;size:</span>&nbsp;{v2} MB<br>'
                    f"{headermsg}<br>",
                )

            except Exception as _e:
                error_description = "other"
                err_str = traceback.format_exc()
                try:
                    self.close_progbar() if show_prog else nop()
                except:
                    pass
                self.__console_widg.printout_text(
                    f"\n"
                    f"ERROR: Could not print URL headers.\n"
                    f"{err_str}\n",
                    "#ef2929",
                )
                qt.QTimer.singleShot(
                    100,
                    functools.partial(finish, False, None),
                )
                return

            qt.QTimer.singleShot(
                100,
                functools.partial(finish, True, filepath),
            )
            return

        def finish(success, filepath) -> None:
            assert qt.QThread.currentThread() is origthread
            if not internal_call:
                self.__reject_callback = None
                self.__reject_callbackArgs = None
                self.__reject_callbackThread = None
            if self.__rejected:
                return
            if callback is not None:
                callback(
                    success,
                    error_description,
                    filepath,
                    callbackArg,
                )
            return

        # * Start
        assert qt.QThread.currentThread() is origthread
        try:
            if data.new_mode:
                if url.startswith("https://www.embeetle"):
                    url = url.replace(
                        "https://www.embeetle", "https://new.embeetle"
                    )
                if url.startswith("https://embeetle"):
                    url = url.replace(
                        "https://embeetle", "https://new.embeetle"
                    )
                url = url.replace("embeetle.cn", "embeetle.com")
        except Exception as e:
            pass
        self.__console_widg.printout_text("Download: ", "#fce94f")
        self.__console_widg.printout_text(url, "#729fcf")
        self.__console_widg.printout_text("\n")
        if show_prog:
            self.start_progbar("Download:")
        qt.QTimer.singleShot(50, download)
        return
