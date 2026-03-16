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
import threading, shlex, os, re, functools
import qt, data, purefunctions, functions
import bpathlib.path_power as _pp_
import gui.stylesheets.scrollbar as _sb_
import beetle_console.serial_port as _serial_port_
import beetle_console.interactive_command as _interactive_command_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_
import beetle_console.console_contextmenu as _console_contextmenu_
import components.thread_switcher as _sw_
import beetle_console.codec as _codec_
import os_checker

try:
    import gui.dialogs.popupdialog
except:
    # The popup dialog is only needed for the open_serial_port() method. This
    # method is not used in the Updater widget.
    pass
nop = lambda *a, **k: None
q = "'"
dq = '"'


def _ctag(color: str) -> str:
    """Get an html-tag like '<span style="color:#ef2929">' for the requested
    color. The color will be looked up in the theme if it is not in hex format
    already.
    """
    if color == "end":
        return "</span>"
    if "#" in color:
        return f'<span style="color' f':{color}">'
    try:
        color_html_tag = (
            f'<span style="color' f':{data.theme["console"]["fonts"][color]}">'
        )
    except KeyError:
        color_html_tag = (
            f'<span style="color'
            f':{data.theme["console"]["fonts"]["default"]}">'
        )
        purefunctions.printc(
            f"ERROR: Console color {color} not defined in theme", color="error"
        )
    return color_html_tag


class ConsoleWidget(qt.QPlainTextEdit):
    """This ConsoleWidget()-instance is a subclassed qt.QPlainTextEdit() and
    behaves as a simple con- sole.

    PROGRAMMATICAL INTERACTION
    ==========================
    Use this ConsoleWidget() to run commands or simply display colorful output.
    ┌────────────────────────┬─────────────────────────────────────────────────┐
    │ set_cwd(cwd)           │ Change the current working directory.           │
    ├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┼┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┤
    │ run_command(           │ Run the given command, provided as a List[str]. │
    │     commandlist,       │ Set 'printout' True if you want to print the    │
    │     printout,          │ command before execution.                       │
    │ )                      │ The stdout and stderr output are printed to this│
    │                        │ console. When the command completes, the exit-  │
    │                        │ code gets printed.                              │
    ├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┼┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┤
    │ close_command()        │ Abort the current running command/process.      │
    ├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┼┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┤
    │ send(                  │ Print and send bytes to the current process.    │
    │     bytes_to_send,     │                                                 │
    │ )                      │                                                 │
    ├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┼┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┤
    │ printout_text(         │ Print the given text in the given color (white  │
    │     plain_text,        │ if color is None). HTML tags are stripped!      │
    │     color,             │                                                 │
    │ )                      │ This function can be called from any thread. If │
    │                        │ called from the main, it acts immediately.      │
    ├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┼┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┤
    │ printout_html(         │ Print the given html string.                    │
    │     plain_text,        │                                                 │
    │     color,             │ This function can be called from any thread. If │
    │ )                      │ called from the main, it acts immediately.      │
    └────────────────────────┴─────────────────────────────────────────────────┘

    USER INTERACTION
    ================
    The user can type commands into this widget and hit enter to execute them.
    WORKS:
    ------
        - Assert that the user cannot delete text where it shouldn't, such as
          previous commands, output, ...

        - Basic functionalities like copy-paste.

        - Display previous/next commands when pressing the up/down arrow keys.

        - Run the typed command when user hits enter(*).

    (*)Note: the user command is scraped from the last "block" of text, which
    starts from the prompt (or the end of the previous enter-hit in case it's a
    subcommand-prompt). Extracting the command like this is safer than trying to
    reconstruct it from key presses, as the user can click around with the mouse
    to enter text at several locations.

    LIMITATIONS:
    ------------
        - As there is no shell running in the background, this console cannot
          handle shell commands like 'cd', 'dir/ls', ... They could be emulated,
          but I didn't do that yet.

        - Interactive processes are challenging, because this console doesn't
          know when the process waits for new input.

    THREADING
    =========
    1. self.__target_mutex
    ----------------------
    This mutex protects not only the making of a new target instance - a
    SerialPort() or Command() - but also their callbacks to receive the outputs.
    Protected:
        - run_command()
        - receive()
        - receive_error()
        - receive_exit()

    2. self.__printout_mutex
    ------------------------
    This ConsoleWidget() has two buffers to store the received bytes - after
    turning them into strings:
        - self.__printout_buf
        - self.__log
    These buffers are protected with the 'self.__printout_mutex' whenever
    accessed or written to.
    """

    printout_buf_sig = qt.pyqtSignal()
    print_toplevel_prompt_sig = qt.pyqtSignal()
    invoke_callback_sig = qt.pyqtSignal(object, object, bool)
    start_new_block_sig = qt.pyqtSignal()

    # & Internal progbar
    start_progbar_sig = qt.pyqtSignal(str)
    apply_progbar_val_sig = qt.pyqtSignal()
    close_progbar_sig = qt.pyqtSignal()

    # & External progbar
    inc_external_progbar_sig = qt.pyqtSignal(int)

    KNOWN_INTERMEDIATE_PROMPTS = [
        "(gdb)",
        ">>>",
        "...",
    ]

    def __init__(
        self,
        parent: qt.QWidget,
        readonly: bool,
        cwd: Optional[str],
        fake_console: bool,
        is_serial_monitor: bool,
    ) -> None:
        """

        :param parent:          Parent widget for this ConsoleWidget().
        :param readonly:        True if user shouldn't type input.
        :param cwd:             Current Working Directory.
        :param fake_console:    > True: - Print prompt at startup.
                                        - Print prompt *after* each command.
                                Try to behave as an interactive console.

                                > False: - No prompt at startup.
                                         - Print prompt *before* each command.
                                Only print a prompt before a new command. This
                                way, other output can be printed without prompts
                                sitting in the way.

        :param is_serial_monitor: Set True if this ConsoleWidget() will be used
                                  as a Serial Monitor.
        """
        super().__init__(parent)
        assert threading.current_thread() is threading.main_thread()
        self.anchor: Optional[str] = None
        self.set_style()
        self.setReadOnly(readonly)
        self.setLineWrapMode(qt.QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.document().setMaximumBlockCount(5000)
        self.setMouseTracking(True)
        self.document().clearUndoRedoStacks()
        try:
            self.verticalScrollBar().setStyleSheet(_sb_.get_vertical())
            self.horizontalScrollBar().setStyleSheet(_sb_.get_horizontal())
        except:
            # In the beetle updater
            pass
        self.verticalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.horizontalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        # & Behavior
        # Define the behavior of this ConsoleWidget()
        self.__fake_console = fake_console
        self.__is_serial_monitor = is_serial_monitor
        if self.__fake_console:
            assert self.__is_serial_monitor == False
        if self.__is_serial_monitor:
            assert cwd is None
        self.__codec: Optional[_codec_.Codec] = None
        # Attention: this escape sequence regex is duplicated at
        # 'serial_console.py'
        self.__escape_sequence_regex = re.compile(
            r"((\\(x[0-9a-fA-F][0-9a-fA-F]|[\\abfnrtv]))+)"
        )

        # & Buffers
        # Keep a buffer of text to be printed asap. Protect operations on this
        # buffer with a mutex.
        self.__printout_buf: str = ""
        # Send signal to write buffer content to the terminal.
        self.printout_buf_sig.connect(self.__printout_buf_func)
        # Log everything written to the console.
        self.__log: str = ""

        # & Target
        # Keep a target - a command/process or serial port - that this
        # ConsoleWidget() interacts with. This target starts as None and is
        # renewed whenever a new command or serial port connection is started.
        self.__target: Union[
            _serial_port_.SerialPort, _interactive_command_.Command, None
        ] = None

        # & Mutexes
        # Protect target creation and all receive callbacks.
        self.__target_mutex: threading.Lock = threading.Lock()
        # Protect all interactions with the write buffers.
        self.__printout_mutex: threading.Lock = threading.Lock()
        # Protect progbar
        self.__progbar_exists_mutex: threading.Lock = threading.Lock()
        self.__progbar_set_val_mutex: threading.Lock = threading.Lock()
        self.__progbar_draw_val_mutex: threading.Lock = threading.Lock()

        # & Internal progbar
        # The internal progbar must be properly opened and closed - before and
        # after use respectively. Only one such progbar can exist at any given
        # time. As long as the progbar runs:
        #     - No targets can be spawned or exist.
        #     - No output can be written to the console.
        # NOTES:
        #     - Opening a new progbar is not immediate if you do it from a
        #       non-main thread. Wait until 'is_progbar_open()' returns True
        #       before writing values.
        #     - The internal progbar only accepts float values 0.0 - 100.0
        self.__progbar_buf: float = 0.0
        self.__progbar_printed_blocks: int = 0
        self.__tsize: int = 10
        self.__bsize: int = 50
        self.start_progbar_sig.connect(self.start_progbar)
        self.apply_progbar_val_sig.connect(self.apply_progbar_val)
        self.close_progbar_sig.connect(self.close_progbar)

        # & External progbar
        # An external progbar can be supplied with increment-signals from this
        # ConsoleWidget(). To do that, tie the 'inc_external_progbar_sig' to the
        # external progbar and register an 'increment string', such that this
        # ConsoleWidget() knows what to look for in output strings to fire the
        # 'inc_external_progbar_sig'. If None, no increment signals will fire.
        # WARNING:
        #     Unlike the internal progbar, the external one is not bound to 0 -
        #     100. That's because it relies on matching strings in the output,
        #     generating increment signals per match (sometimes grouped).
        self.__ext_progbar_inc_str: Optional[str] = None

        # & Callback
        # Store a callback function to be invoked when the command/process exits.
        self.__callback: Optional[Callable] = None
        self.__callback_thread: Optional[qt.QThread] = None
        self.invoke_callback_sig.connect(self.__invoke_callback)

        # & cwd
        # Keep a virtual cwd.
        self.__cwd = _pp_.standardize_abspath(cwd)
        self.print_toplevel_prompt_sig.connect(self.__print_toplevel_prompt)
        self.start_new_block_sig.connect(self.__start_new_block)
        if self.__fake_console:
            # The first prompt should not be preceded by a newline, nor by a new
            # block. So I do it here.
            self.printout_html(self.__get_prompt())

        # & History
        # Keep toplevel command history.
        self.__toplevel_command_history: List[List[str]] = []
        self.__toplevel_command_history_index: int = 0
        return

    def set_style(self) -> None:
        """Apply the stylesheet for this ConsoleWidget()-instance.

        This also sets the font size.
        """
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                color         : {data.theme["console"]["fonts"]["default"]};
                background    : {data.theme["console"]["background"]};
                border-width  : 1px;
                border-color  : {data.theme["console"]["border"]};
                border-style  : solid;
                padding       : 0px;
                margin        : 0px;
                font-family   : {data.get_global_font_family()};
                font-size     : {data.get_general_font_pointsize()}pt;
            }}
        """)
        self.setFont(data.get_general_font())
        self.style().unpolish(self)
        self.style().polish(self)
        return

    # ^                                        PROMPT STUFF                                         |

    def __get_prompt(self) -> str:
        """"""
        assert not self.__is_serial_monitor
        return (
            f"<b>{_ctag('blue')}{self.__cwd}{_ctag('end')}{_ctag('yellow')}"
            f"${_ctag('end')}</b> "
        )

    def __print_toplevel_prompt(self) -> None:
        """Start a new block and print the toplevel shell prompt. As it's in a
        new block, a newline is added automatically.

        NOTE:
        I attempt to insert a new block *before* each prompt. That's easy for the toplevel prompts
        (as I print them myself) - but a bit more challenging for intermediate ones.

        In the 'run_command()' method, you'll see that I also insert a new block *after* each com-
        mand.
        """
        assert not self.__is_serial_monitor
        if not threading.current_thread() is threading.main_thread():
            self.print_toplevel_prompt_sig.emit()
            return
        self.__start_new_block()
        # Warning: when changing this prompt, remember that the first one is created and printed in
        # the constructor.
        self.printout_html(self.__get_prompt())
        return

    @qt.pyqtSlot()
    def __start_new_block(self) -> None:
        """Move text cursor to end and start a new block. Starting a new block
        also inserts a new line!

        NOTE:
        I attempt to insert a new block *before* each prompt and *after* each command. Inserting a
        new block *before* each prompt is easy for the toplevel ones (as I print them myself) - but
        not feasable for intermediate ones. For the intermediate ones, I only insert a new block
        *after* each subcommand (each time you press enter). This way, the output from the last com-
        mand is - unfortunately - also in the last block, before the prompt.
        """
        assert threading.current_thread() is threading.main_thread()
        self.moveCursor(qt.QTextCursor.MoveOperation.End)
        self.textCursor().insertBlock()
        return

    # ^                                     TARGET INTERACTIONS                                     |

    def set_cwd(
        self,
        cwd: str,
        printout: bool,
    ) -> None:
        """Set the cwd for this console.

        :param cwd: The new cwd for this console.
        :param printout: Set True if you want to print the 'cd' command.
        """
        assert not self.__is_serial_monitor
        cwd = _pp_.standardize_abspath(cwd)
        if printout:
            # $ Mini Console
            if not self.__fake_console:
                # If this ConsoleWidget() is not imitating a console, there is probably no prompt
                # yet, as no prompt is printed at the 'receive_exit()' callbacks. Unfortunately, I
                # cannot call this method here:
                #     'self.__print_toplevel_prompt()'
                # If 'run_command()' is called outside the main thread, the prompt print method
                # would re-invoke itself with a signal, so the prompt risks to be printed *after*
                # the actual command!
                # So I join the prompt and the command, then send them to a printout method in one
                # go.
                self.printout_html(
                    "<br>" + self.__get_prompt() + f"cd {q}{cwd}{q}<br>"
                )
            # $ Emulated Console
            else:
                # There is already a prompt. Just print the command.
                self.printout_text(f"cd {q}{cwd}{q}")
        if self.__cwd == cwd:
            return
        if self.__target is not None:
            # A command is running. When new prompt will print, it should be the new cwd.
            self.__cwd = cwd
            return
        self.__cwd = cwd
        # $ Emulated Console
        if self.__fake_console:
            # Provide a prompt for the next commands.
            self.__print_toplevel_prompt()
        return

    def get_cwd(self) -> str:
        """"""
        return self.__cwd

    def run_command(
        self,
        commandlist: List[str],
        printout: bool,
        path_addition: Optional[List[str]] = None,
        callback: Optional[Callable] = None,
    ) -> None:
        """Print and run a command. If successful, add the command to the
        'self.__toplevel_command_history' listing and return True.

        :param commandlist:   A list of strings. The first item of the list is the program to exe-
                              cute, and the following items are the program arguments. If you start
                              from a single string, use something like 'shlex.split' to convert it
                              to a list, taking into account OS-specific conventions.

        :param printout:      Set True if you want to print the command before execution.

        :param path_addition: Path(s) to be added to the PATH env variable, at the front.

        :param callback:      This callback will be invoked with a bool success parameter once the
                              command has properly finished (printed its exit code) or if it has
                              been forced to stop.
                              The callback is ensured to run in the same thread that entered this
                              'run_command()' method.

        NOTE:
        The commandlist is first given to the filter function, which replaces keywords like $(MAKE),
        $(TOOLPREFIX), ...
        """
        assert not self.__is_serial_monitor
        origthread = qt.QThread.currentThread()

        def start(*args) -> None:
            """Perform basic checks and filter/expand the command."""
            assert qt.QThread.currentThread() is origthread
            # & Checks
            # $ 1. Other targets
            # Make sure to grab the mutex for spawning processes.
            if not self.__target_mutex.acquire(blocking=False):
                purefunctions.printc(
                    f"ERROR: Attempt to run new command while previous "
                    f"one didn{q}t exit yet!",
                    color="error",
                )
                abort()
                return
            assert self.__target_mutex.locked()
            # Make sure no other process is running right now.
            if self.__target is not None:
                purefunctions.printc(
                    f"ERROR: Attempt to run new command while previous "
                    f"one didn{q}t exit yet!",
                    color="error",
                )
                abort()
                return
            assert self.__target is None
            # $ 2. Old callbacks
            # Make sure the previous callback is already invoked.
            if self.__callback is not None:
                purefunctions.printc(
                    f"ERROR: Attempt to run new command while previous "
                    f"one didn{q}t invoke its callback yet!",
                    color="error",
                )
                abort()
                return
            if self.__callback_thread is not None:
                purefunctions.printc(
                    f"ERROR: Attempt to run new command while previous "
                    f"one didn{q}t invoke its callback yet!",
                    color="error",
                )
                abort()
                return
            assert self.__callback is None
            assert self.__callback_thread is None
            # $ 3. Progbars
            # Make sure there is no progbar open at this moment.
            if (
                self.__progbar_exists_mutex.locked()
                or self.__progbar_set_val_mutex.locked()
            ):
                purefunctions.printc(
                    f"ERROR: Attempt to run new command while a progbar "
                    f"was open in this ConsoleWidget()!",
                    color="error",
                )
                abort()
                return

            # & Filter command
            self.__filter_command_list(
                commandlist=commandlist,
                callback=get_filtered_command,
            )
            return

        def get_filtered_command(new_commandlist: List[str], *args) -> None:
            if new_commandlist is None:
                # Error message already printed by the filter method. No need to print another one!
                abort()
                return
            _sw_.switch_thread_modern(
                _sw_.get_qthread("main"),
                print_command,
                new_commandlist,
            )
            return

        def print_command(new_commandlist: List[str]) -> None:
            """Print command and insert new block."""
            assert threading.current_thread() is threading.main_thread()
            # & Print command
            if printout:
                # $ Mini Console
                if not self.__fake_console:
                    # If this ConsoleWidget() is not imitating a console, there is probably no
                    # prompt yet, as no prompt is printed at the 'receive_exit()' callbacks. As
                    # we're now in the main thread, this prompt-printing should happen immediately.
                    self.__print_toplevel_prompt()
                    self.printout_html(" ".join(new_commandlist))
                # $ Emulated Console
                else:
                    # There is already a prompt. Just print the command.
                    self.printout_text(" ".join(new_commandlist))
                # Machine inserted command -> save the command to history
                # after expanding.
                self.__toplevel_command_history.append(new_commandlist)
                self.__toplevel_command_history_index = (
                    len(self.__toplevel_command_history) - 1
                )

            # & No printing
            else:
                # Typed command -> save to history what the user originally typed.
                self.__toplevel_command_history.append(commandlist)
                self.__toplevel_command_history_index = (
                    len(self.__toplevel_command_history) - 1
                )
            # & Insert new block
            # Remember: we need a block insertion *before* each prompt (which happens in the prompt-
            # printing-method) and *after* each command.
            # Inserting the new block right after the command also introduces a newline - which is
            # exactly what we need. As we're now in the main thread, this should happen immediately.
            self.__start_new_block()
            _sw_.switch_thread_modern(
                origthread,
                execute,
                new_commandlist,
            )
            return

        def execute(new_commandlist: List[str]) -> None:
            """Execute command."""
            # & Define environment variables
            env = purefunctions.get_modified_environment(path_addition)

            # & Run command
            try:
                # Create and start the command with default parameter values.
                if callback is not None:
                    self.__callback = callback
                    self.__callback_thread = origthread
                self.__target = _interactive_command_.Command(
                    command=new_commandlist,
                    cwd=self.__cwd,
                    env=env,
                )
                self.__target.start(self)
                finish()
                return
            except _interactive_command_.Error as error:
                self.printout_html(
                    f"{_ctag('yellow')}ERROR: the command you entered "
                    f"cannot be executed.{_ctag('end')}<br>"
                    f"{_ctag('red')}{error}{_ctag('end')}"
                    f"<br>"
                )
                if self.__fake_console:
                    self.__print_toplevel_prompt()
            abort()
            return

        def abort(*args) -> None:
            """Unlock mutex and invoke callback(False)"""
            # Unlock the mutex.
            if self.__target_mutex.locked():
                self.__target_mutex.release()
            # Call the given callback, but don't touch the stored one!
            # The stored one might still belong to an unfinished job
            # and will run when appropriate.
            callback(False) if callback is not None else nop()
            return

        def finish(*args) -> None:
            """Unlock mutex and store callback."""
            # Release the 'self.__target_mutex'. This mutex protects not
            # only the making of new targets, but also their receive call-
            # backs. Keeping it locked would prevent the receive callbacks
            # to run.
            self.__target_mutex.release()
            # Store the given callback and its thread for later use.
            if callback is not None:
                assert self.__callback is not None
                assert self.__callback_thread is not None
            return

        start()
        return

    def close_command(self) -> None:
        """Close the command/process.

        The target object becomes useless after this, so it's destroyed.
        """
        if self.__is_serial_monitor:
            functions.printc(
                "WARNING: Cannot abort process in serial monitor!",
                color="warning",
            )
            return
        assert not self.__is_serial_monitor
        print("\nclose_command()\n")
        if self.__target is not None:
            assert isinstance(self.__target, _interactive_command_.Command)
            print("\nself.__target.close() start\n")
            self.__target.close(timeout=1)
            print("\nself.__target.close() done\n")
            # If the command refuses to stop, it is killed after the specified
            # timeout.
            self.__target = None
            if self.__callback is not None:
                # Apparently, the 'receive_exit()' wasn't invoked while closing the command (other-
                # wise it would have cleared the self.__callback already). So we need to launch and
                # clear the stored callback here.
                callback = self.__callback
                callback_thread = self.__callback_thread
                self.__callback = None
                self.__callback_thread = None
                self.invoke_callback_sig.emit(callback, callback_thread, False)
        return

    def modify_serial_port_settings(
        self,
        show_newlines: bool,
        mode: str,
    ) -> None:
        """Modify the current settings of the serial port."""
        assert self.__is_serial_monitor
        assert self.__target
        assert mode in ("html-ascii", "html-hex")

        # & Mode and newlines
        # Attention, this code is duplicated in open_serial_port()
        if mode == "html-ascii":
            self.__codec = _codec_.Codec(
                mode="html-ascii",
                show_line_endings=show_newlines,
                html_line_ending="<br>",
                html_begin_escape=_ctag("yellow"),
                html_end_escape="</span>",
                line_ending=None,
            )
        else:
            self.__codec = _codec_.Codec(
                mode="html-hex",
                html_line_ending="<br>",
                hex_bytes_per_block=2,
                hex_line_width=20,
            )
        return

    def open_serial_port(
        self,
        port: str,
        baudrate: int,
        bytesize: int,
        parity: str,
        stopbits: Union[int, float],
        show_newlines: bool,
        mode: str,
    ) -> bool:
        """Open a serial port. Return True if successful.

        :param port: A string naming the serial port to be opened; e.g.
            /deb/ttyUSB0 on Linux or COM2 on Windows.
        """
        assert self.__is_serial_monitor
        assert not self.__target
        assert mode in ("html-ascii", "html-hex")
        if (port is None) or (port.lower() == "none"):
            if (data.serial_port_data is None) or len(
                data.serial_port_data
            ) == 0:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path=f"icons/dialog/stop.png",
                    title_text="Connect Device",
                    text=str(
                        f"Embeetle could not detect any valid Serial Port. Please<br>"
                        f"connect your device and select its Serial Port from the<br>"
                        f"dropdown menu.<br>"
                    ),
                )
            else:
                text = "Embeetle found the following Serial Port:<br>"
                for key in data.serial_port_data.keys():
                    text += f"&nbsp;&nbsp;&nbsp;&nbsp;- {key}<br>"
                text += "<br>Please make your selection in the dropdown menu."
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path=f"icons/dialog/stop.png",
                    title_text="Select Serial Port",
                    text=text,
                )
            return False
        try:
            # Create and start the port with default parameter values. See 'serial_port.SerialPort'
            # for available parameters and default values.
            self.__codec = None
            # Attention, this code is duplicated in modify_serial_port_settings()
            if mode == "html-ascii":
                self.__codec = _codec_.Codec(
                    mode="html-ascii",
                    show_line_endings=show_newlines,
                    html_line_ending="<br>",
                    html_begin_escape=_ctag("yellow"),
                    html_end_escape="</span>",
                    line_ending=None,
                )
            else:
                self.__codec = _codec_.Codec(
                    mode="html-hex",
                    html_line_ending="<br>",
                    hex_bytes_per_block=2,
                    hex_line_width=20,
                )
            self.__target = _serial_port_.SerialPort(
                port=port,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
            )
            self.__target.start(self)
            self.printout_text(
                plain_text=f"\n< Connected to port {q}{port}{q} >\n",
                color="blue",
            )
            return True
        except _serial_port_.Error as error:
            self.printout_text(
                plain_text=f"\n{error}\n",
                color="red",
            )
            print(f"!! {error}")
        return False

    def close_serial_port(self) -> None:
        """Close the serial port.

        The target object becomes useless after this, so it's destroyed.
        """
        assert self.__is_serial_monitor
        assert self.__target
        port = self.__target.port
        self.__target.close()
        self.__target = None
        self.printout_text(
            plain_text=f"\n< Disconnected from port {q}{port}{q} >\n",
            color="blue",
        )
        return

    def is_serial_port_open(self) -> bool:
        """Return True if serial port is open."""
        if self.__target is not None:
            return True
        return False

    def send(
        self,
        bytes_to_send: Union[bytes, bytearray],
        echo: bool = True,
        show_newlines_in_echo: bool = False,
    ) -> None:
        """Print and send bytes to the serial port or command.

        Do *not* lock the mutex while sending bytes to avoid deadlocks. Bytes
        can be received asyn- chronously also while sending. Depending on the
        command or application running on the other side of the serial link, if
        too much data is received while the mutex is locked, buffers may become
        full and it may become impossible to send the bytes until received bytes
        are proces- sed. Therefore, received bytes must be handled without
        waiting for the send call to return.
        """
        if echo:
            # First print the bytes, but no locks!
            self.__printout_text_unprotected(
                plain_text=bytes_to_send.decode(),
                color="green",
                show_newlines=show_newlines_in_echo,
            )
        if self.__target:
            try:
                self.__target.send(bytes_to_send)
            except _serial_port_.Error as error:
                print(f"!> {error}")
        return

    def send_hex(
        self,
        hex_as_string,
        echo: bool,
    ) -> None:
        """Print and send the given 'hex_as_string' to the serial port or
        command."""
        if echo:
            # First print the text, but no locks!
            self.__printout_text_unprotected(
                plain_text=f"\n{hex_as_string.strip()}\n",
                color="green",
                show_newlines=False,
            )
        self.send(
            bytes_to_send=self.__codec.encode(hex_as_string),
            echo=False,
            show_newlines_in_echo=False,
        )
        self.__codec.column = 0
        return

    def send_text(
        self,
        text: str,
        echo: bool,
        show_newlines_in_echo: bool,
    ) -> None:
        """Print and send the given text to the serial port or command."""
        if echo:
            # First print the text, but no locks!
            self.__printout_text_unprotected(
                plain_text=text,
                color="green",
                show_newlines=show_newlines_in_echo,
            )
        self.send(
            bytes_to_send=self.__codec.encode(text),
            echo=False,
            show_newlines_in_echo=False,
        )
        return

    def receive(
        self,
        bytes_received: bytes,
        is_stderr: bool = False,
    ) -> None:
        """Callback called asynchronously (from another thread) when data is
        received from the serial port or command.

        The data is provided as a byte string. It must be decoded to convert it
        to a normal string. The 'decode' function has an 'encoding' parameter
        that defaults to UTF-8,  which is fine for most applications.

        Only commands supply the 'is_stderr' argument. To allow a single method
        to implement cal- lbacks from both serial ports and commands, we provide
        a default value here. This default value is only used when receiving
        data from a serial port.
        """
        with self.__target_mutex:
            if is_stderr:
                self.printout_text(
                    plain_text=bytes_received.decode(),
                    color="#ef2929",
                )
            else:
                if self.__is_serial_monitor:
                    decoded_bytes = self.__codec.decode(bytes_received)
                    # print(f'receive({decoded_bytes})')
                    self.printout_html(decoded_bytes)
                else:
                    self.printout_autocolored_text(
                        plain_text=bytes_received.decode(),
                    )
        return

    def receive_error(
        self,
        error: Union[_serial_port_.Error, _interactive_command_.Error],
        is_stderr: bool = False,
    ) -> None:
        """Callback called asynchronously (from another thread) when an
        exception occurs while re- ceiving data from the serial port or command.

        :param error: The exception that was raised. Both 'serial_port.py' and
            'interactive_command.py' define an Error() base class to encapsulate
            all thrown exceptions.
        :param is_stderr: Only commands supply this argument. To allow a single
            method to implement callbacks from both serial ports and commands,
            we provide a default value here. This default value is only used
            when receiving data from a serial port.
        """
        with self.__target_mutex:
            self.printout_html(f"{_ctag('red')}{error}{_ctag('end')}")
            if not self.__is_serial_monitor:
                self.__print_toplevel_prompt()
            print("receive_error()")
            print(f"{error}")
        return

    def receive_exit(self, exit_code: int) -> None:
        """COMMANDS ONLY.

        Callback called asynchronously (from another thread) when the command
        exits.

        :param exit_code: Zero if exit without errors.
        """
        assert not self.__is_serial_monitor
        with self.__target_mutex:
            self.printout_html(
                str(
                    f"{_ctag('green')}{self.__target.command[0]}{_ctag('end')}: "
                    f"exit code {q}{exit_code}{q}<br>"
                )
            )
            if self.__fake_console:
                self.__print_toplevel_prompt()
            self.__target = None
            if self.__callback is not None:
                callback = self.__callback
                callback_thread = self.__callback_thread
                self.__callback = None
                self.__callback_thread = None
                if exit_code == 0:
                    self.invoke_callback_sig.emit(
                        callback,
                        callback_thread,
                        True,
                    )
                else:
                    self.invoke_callback_sig.emit(
                        callback,
                        callback_thread,
                        False,
                    )
        return

    @qt.pyqtSlot(object, object, bool)
    def __invoke_callback(
        self,
        callback,
        callback_thread,
        success: bool,
    ) -> None:
        """Invoke the given callback.

        This slot should run in the main thread.
        """
        assert threading.current_thread() is threading.main_thread()
        _sw_.switch_thread_modern(
            callback_thread,
            callback,
            success,
        )
        return

    def disconnect(self) -> None:
        """SERIAL PORTS ONLY.

        callback called asynchronously (from another thread) when the serial port is disconnected.

        NOTE:
        Disconnecting a port will not automatically close it. The port will try to reconnect by
        default, unless you close it.
        """
        assert self.__is_serial_monitor
        print(f"{self.__target.port}: disconnected")
        return

    def reconnect(self) -> None:
        """SERIAL PORTS ONLY.

        Serial ports only: callback called asynchronously (from another thread) when the serial port
        is reconnected.
        """
        assert self.__is_serial_monitor
        print(f"{self.__target.port}: reconnected")
        return

    # ^                                        CONSOLE OUTPUT                                       |

    def clear(self) -> None:
        """Clear the console text."""
        super().clear()
        if self.__target is None:
            if not self.__is_serial_monitor:
                self.__print_toplevel_prompt()
        return

    def get_log(self) -> str:
        """"""
        return self.__log

    def clear_log(self) -> None:
        """"""
        with self.__printout_mutex:
            self.__log = ""
        return

    def __prepare_for_html(
        self,
        plain_text: str,
        show_newlines: bool = False,
    ) -> str:
        """Remove all potenial HTML tags, make sure the plain text looks good
        when inserted as HTML.

        In other words, this function does more than just stripping html-tags!
        """
        if plain_text is None:
            return "None"
        # & Regular
        if not show_newlines:
            # Don't show line endings. Just replace them with a '<br>', even if they are already
            # escaped.
            html_text: str = (
                plain_text.replace("#", "&#35;")
                .replace(" ", "&nbsp;")
                .replace(">", "&#62;")
                .replace("<", "&#60;")
                .replace("\r\n", "<br>")
                .replace("\r", "<br>")
                .replace("\n", "<br>")
                .replace("\\r\\n", "<br>")
                .replace("\\r", "<br>")
                .replace("\\n", "<br>")
            )
            # Color other escape sequences yellow.
            html_text = self.__escape_sequence_regex.sub(
                rf"{_ctag('yellow')}\1{_ctag('end')}",
                html_text,
            )
            return html_text

        # & Show \n
        assert show_newlines
        # Show line endings as yellow '\n'. The given text can also contain already escaped line
        # endings, like '\\n'. Show them also as yellow '\n'.
        html_text: str = (
            plain_text.replace("#", "&#35;")
            .replace(" ", "&nbsp;")
            .replace(">", "&#62;")
            .replace("<", "&#60;")
            .replace("\r\n", f"{_ctag('yellow')}&#92;r&#92;n{_ctag('end')}<br>")
            .replace("\r", f"{_ctag('yellow')}&#92;r{_ctag('end')}<br>")
            .replace("\n", f"{_ctag('yellow')}&#92;n{_ctag('end')}<br>")
            .replace(
                "\\r\\n", f"{_ctag('yellow')}&#92;r&#92;n{_ctag('end')}<br>"
            )
            .replace("\\r", f"{_ctag('yellow')}&#92;r{_ctag('end')}<br>")
            .replace("\\n", f"{_ctag('yellow')}&#92;n{_ctag('end')}<br>")
        )
        # Color other escape sequences yellow too.
        html_text = self.__escape_sequence_regex.sub(
            rf"{_ctag('yellow')}\1{_ctag('end')}",
            html_text,
        )
        return html_text

    def printout_autocolored_text(self, plain_text: str) -> None:
        """Same as 'printout_text()', but with automatic heuristic-based
        coloring."""
        assert not self.__progbar_exists_mutex.locked()
        # * Prepare text
        # Remove all potenial HTML tags, make sure the plain text looks good when inserted as HTML.
        # Unfortunately, the 'self.__prepare_for_html(plain_text') cannot be used here, because we
        # still need to apply some regexes on the text for syntax highlighting. It would make those
        # regexes much more complicated.
        html_text = (
            plain_text.replace("#", "&#35;")
            .replace(" ", "&nbsp;")
            .replace(">", "&#62;")
            .replace("<", "&#60;")
        )

        # * Apply syntax coloring
        # $ Comments
        p = re.compile(r"(&#35;[^\n\r]*)")
        html_text = p.sub(f"{_ctag('green')}\\1{_ctag('end')}", html_text)

        # $ Compiler invocations
        p = re.compile(
            r"(([\"\'][^\n\r]*?[gc]\+*[\"\'])|([\"\'][^\n\r]*?objcopy[\"\'])|([\"\'][^\n\r]*?size[\"\']))"
        )
        html_text = p.sub(f"{_ctag('purple')}\\1{_ctag('end')}", html_text)

        # * Replace newlines
        html_text = (
            html_text.replace("\r\n", "<br>")
            .replace("\r", "<br>")
            .replace("\n", "<br>")
            .replace("\\r\\n", "<br>")
            .replace("\\r", "<br>")
            .replace("\\n", "<br>")
        )

        # * Print as html
        if qt.sip.isdeleted(self):
            return
        # $ Add to buffer
        with self.__printout_mutex:
            self.__log += plain_text
            if self.__ext_progbar_inc_str is not None:
                if self.__ext_progbar_inc_str in plain_text:
                    self.inc_external_progbar_sig.emit(
                        plain_text.count(self.__ext_progbar_inc_str)
                    )
            self.__printout_buf += html_text
        # $ Print what's in the buffer
        if threading.current_thread() is threading.main_thread():
            self.__printout_buf_func()
            return
        self.printout_buf_sig.emit()
        return

    def printout_text(
        self,
        plain_text: str,
        color: Optional[str] = None,
        show_newlines: bool = False,
    ) -> None:
        """Add the given text to the printout buffer.

        It will be printed in the main thread asap.
        """
        if qt.sip.isdeleted(self):
            return
        if plain_text is None:
            plain_text = "None"
        assert not self.__progbar_exists_mutex.locked()
        # Remove all potenial HTML tags, make sure the
        # plain text looks good when inserted as HTML.
        html_text = self.__prepare_for_html(
            plain_text=plain_text,
            show_newlines=show_newlines,
        )
        # Apply the color
        if color is not None:
            html_text = f"{_ctag(color)}{html_text}</span>"
        # Add to buffer
        with self.__printout_mutex:
            self.__log += plain_text
            if self.__ext_progbar_inc_str is not None:
                if self.__ext_progbar_inc_str in plain_text:
                    self.inc_external_progbar_sig.emit(
                        plain_text.count(self.__ext_progbar_inc_str)
                    )
            self.__printout_buf += html_text
        # Print what's in the buffer
        if threading.current_thread() is threading.main_thread():
            self.__printout_buf_func()
            return
        self.printout_buf_sig.emit()
        return

    def __printout_text_unprotected(
        self,
        plain_text: str,
        color: Union[str, None] = None,
        show_newlines: bool = False,
    ) -> None:
        """This method is not protected with a mutex.

        It's needed for the send() function, to avoid deadlocks.
        """
        if qt.sip.isdeleted(self):
            return
        assert not self.__progbar_exists_mutex.locked()
        # Remove all potenial HTML tags, make sure the plain text looks good when inserted as HTML.
        html_text = self.__prepare_for_html(
            plain_text=plain_text,
            show_newlines=show_newlines,
        )
        # Apply the color
        if color is not None:
            html_text = f"{_ctag(color)}{html_text}</span>"
        # Print the text immediately (don't pass through buffer).
        if threading.current_thread() is threading.main_thread():
            self.moveCursor(qt.QTextCursor.MoveOperation.End)
            self.textCursor().insertHtml(html_text)
            self.moveCursor(qt.QTextCursor.MoveOperation.End)
            return
        # Add to buffer - no other choice -but skip the log.
        self.__printout_buf += html_text
        self.printout_buf_sig.emit()
        return

    def printout_html(
        self,
        *args,
        color: Optional[str] = None,
        bright: bool = False,
        **kwargs,
    ) -> None:
        """Add the given html to the printout buffer.

        It will be printed in the main thread asap.
        """
        if qt.sip.isdeleted(self):
            return
        assert not self.__progbar_exists_mutex.locked()

        # Obtain 'html_text' from arguments
        sep = kwargs.get("sep", " ")
        html_text = sep.join(args)
        if color is not None:
            html_text = f"{_ctag(color)}{html_text}</span>"

        # Add to buffer
        with self.__printout_mutex:
            self.__log += html_text
            if self.__ext_progbar_inc_str is not None:
                if self.__ext_progbar_inc_str in html_text:
                    self.inc_external_progbar_sig.emit(
                        html_text.count(self.__ext_progbar_inc_str)
                    )
            self.__printout_buf += html_text

        # Avoid super long lines
        if len(self.__log.split("<br>")[-1]) > 1024:
            self.start_new_block_sig.emit()
            self.__log += "<br>"

        # Print what's in the buffer
        if threading.current_thread() is threading.main_thread():
            self.__printout_buf_func()
            functions.process_events(10)
            return
        self.printout_buf_sig.emit()
        functions.process_events(10)
        return

    @qt.pyqtSlot()
    def __printout_buf_func(self) -> None:
        """Just print out whatever is currently in the buffer to the end of the
        document."""
        assert threading.current_thread() is threading.main_thread()
        if qt.sip.isdeleted(self):
            return
        assert not self.__progbar_exists_mutex.locked()
        vscrollbar = self.verticalScrollBar()
        with self.__printout_mutex:
            # Save current cursor situation to (potentially) restore it after insertion.
            old_cursor = self.textCursor()
            old_scrollbar_value = vscrollbar.value()
            old_scrollbar_max = vscrollbar.maximum()
            # Insert the text as HTML.
            self.moveCursor(qt.QTextCursor.MoveOperation.End)
            self.textCursor().insertHtml(self.__printout_buf)
            self.__printout_buf = ""
            # Check if previous cursor sitation needs to be restored.
            if old_cursor.hasSelection():
                # The user has selected text, maintain position.
                self.setTextCursor(old_cursor)
                vscrollbar.setValue(old_scrollbar_value)
            else:
                # The user hasn't selected any text, scroll to the bottom.
                self.moveCursor(qt.QTextCursor.MoveOperation.End)
                vscrollbar.setValue(vscrollbar.maximum())
        return

    # ^                                    OTHER HELP FUNCTIONS                                     |

    def __remove_selected_text(self) -> str:
        """
        This method should perform the same as:
            self.textCursor().removeSelectedText()

        However, it should protect against deleting random stuff. So it only
        removes user input.

        :return: 'err' -> The operation could not proceed because no prompt was
                          found in the last block. A new prompt is printed to
                          correct this situation (unless a process is active and
                          could be sending data).

                 'no_selection' ->  Nothing was selected.

                 'ignored' -> Selected text was in a zone where no characters
                              can be deleted.

                 'success' -> Selected text was deleted successfully - except
                              for those characters in the 'no-delete-zone'.

        """
        prompt, commandstr = self.__extract_cmd()
        lastblock: qt.QTextBlock = self.document().lastBlock()
        cursor: qt.QTextCursor = self.textCursor()
        # Define cursor position referenced to the start of
        # the last block.
        cursorpos: int = cursor.position() - lastblock.position()
        anchorpos: int = cursor.anchor() - lastblock.position()

        # * Make sure there is a prompt in the last block
        if self.__target is not None:
            if prompt is None:
                # Process is running and no prompt detected,
                # probably there is still data coming in.
                self.moveCursor(
                    qt.QTextCursor.MoveOperation.End,
                    qt.QTextCursor.MoveMode.MoveAnchor,
                )
                return "err"
        else:
            if prompt is None:
                # Console is idle but no prompt detected,
                # correct this situation!
                purefunctions.printc(
                    "ERROR: Console was sitting idle, and yet no"
                    "prompt could be detected!",
                    color="error",
                )
                self.__print_toplevel_prompt()
                return "err"
        assert prompt is not None
        # Acquire the distance between the startpoint of the
        # last block and the endpoint of the prompt.
        prompt_dist = self.__get_prompt_distance(prompt)

        # * Nothing selected
        if anchorpos == cursorpos:
            return "no_selection"

        # * Text selected
        # Make sure the cursor goes in front of the
        # anchor!
        if anchorpos > cursorpos:
            anchorpos, cursorpos = cursorpos, anchorpos
            cursor.setPosition(
                lastblock.position() + anchorpos,
                qt.QTextCursor.MoveMode.MoveAnchor,
            )
            cursor.setPosition(
                lastblock.position() + cursorpos,
                qt.QTextCursor.MoveMode.KeepAnchor,
            )
            self.setTextCursor(cursor)
        assert cursorpos > anchorpos

        # $ Cursor negative (before the prompt) or somewhere in the prompt
        # Push the cursor to the end of the prompt and ignore
        # the delete operation.
        if cursorpos <= prompt_dist:
            # If cursorpos == prompt_dist, then the anchor
            # is in the prompt and nothing should be deleted!
            cursor.setPosition(
                lastblock.position() + prompt_dist,
                qt.QTextCursor.MoveMode.MoveAnchor,
            )
            self.setTextCursor(cursor)
            return "ignored"
        assert cursorpos > prompt_dist

        # $ Cursor beyond the prompt
        # Move the anchor if needed such that it doesn't cover
        # any characters from the prompt. Then perform the delete
        # operation.
        if anchorpos < prompt_dist:
            anchorpos = prompt_dist
            cursor.setPosition(
                lastblock.position() + anchorpos,
                qt.QTextCursor.MoveMode.MoveAnchor,
            )
            cursor.setPosition(
                lastblock.position() + cursorpos,
                qt.QTextCursor.MoveMode.KeepAnchor,
            )
            self.setTextCursor(cursor)
        assert anchorpos >= prompt_dist
        self.textCursor().removeSelectedText()
        return "success"

    def __get_prompt_distance(
        self, prompt: Optional[str] = None
    ) -> Union[int, None]:
        """Return the distance between the startpoint of the last block and the
        end of the prompt. If no prompt is found, return None.

        :param prompt: If the prompt is already known, you can pass it in this
            parameter to speed up the operation.
        """
        assert not self.__is_serial_monitor
        if prompt is None:
            prompt, commandstr = self.__extract_cmd()
        if prompt is None:
            return None
        lastblock: qt.QTextBlock = self.document().lastBlock()
        assert prompt is not None
        # $ Toplevel prompt
        # For toplevel prompts, there is no space beyond
        # the '$' sign.
        if "$" in prompt:
            return len(prompt)
        # $ Intermediate prompt
        # Intermediate prompts can be anywhere in the
        # last textblock... also account for the extra
        # space at the end.
        index = lastblock.text().find(prompt)
        dist = index + len(prompt) + 1
        return dist

    def __extract_cmd(self) -> Tuple[Union[str, None], Union[str, None]]:
        """Extract the command from the last textblock. I attempt to start a new
        textblock at the start of each prompt. Therefore, the command should be
        in the last block.

        :return: (prompt, commandstr)
        """
        assert not self.__is_serial_monitor
        blocktext: str = self.document().lastBlock().text()
        blocktext = blocktext.replace(chr(160), " ")  # Remove &nbsp;
        blocktext = blocktext.strip()
        # Look for prompts like '(gdb)', '>>>', ...
        for prompt in self.KNOWN_INTERMEDIATE_PROMPTS:
            if prompt in blocktext:
                _, commandstr = blocktext.split(prompt, 1)
                if prompt == "...":
                    # Don't strip, spaces are
                    # important.
                    return prompt, commandstr
                return (
                    prompt.strip(),
                    commandstr.strip(),
                )
        # Look for a toplevel prompt.
        if "$" not in blocktext:
            return None, None
        found_prompt, commandstr = blocktext.split("$", 1)
        return (
            found_prompt.strip() + "$ ",
            commandstr.strip(),
        )

    def __replace_cmd(self, new_commandstr: str) -> None:
        """Replace the current commandstr with a new one."""
        assert not self.__is_serial_monitor
        # * Previous process still busy
        if self.__target is not None:
            return

        # * Console idle
        prompt, commandstr = self.__extract_cmd()
        # $ No prompt found
        if (prompt is None) or (prompt.strip() == ""):
            # Console is idle but no prompt detected,
            # correct this situation!
            purefunctions.printc(
                "ERROR: Console was sitting idle, and yet no"
                "prompt could be detected!",
                color="error",
            )
            self.__print_toplevel_prompt()
            return
        # $ Prompt found
        # Select the whole block and attempt to delete it with the 'self.__remove_selected_text()'
        # method. The mechanism will prevent the prompt from being deleted. Only user input will.
        self.moveCursor(
            qt.QTextCursor.MoveOperation.End, qt.QTextCursor.MoveMode.MoveAnchor
        )
        self.moveCursor(
            qt.QTextCursor.MoveOperation.StartOfBlock,
            qt.QTextCursor.MoveMode.KeepAnchor,
        )
        selection_delete_result = self.__remove_selected_text()
        if selection_delete_result == "err":
            # The called method could not proceed because of an error. It (perhaps) printed a new
            # prompt to correct the situation.
            return
        if selection_delete_result == "no_selection":
            # Abnormal situation...
            purefunctions.printc(
                f"ERROR: Despite moving the cursor and anchor to select the "
                f"whole command for deletion, the {q}self.__remove_selected_text(){q} "
                f"function couldn{q}t see any selected text!",
                color="error",
            )
            return
        if selection_delete_result == "ignored":
            # The selected text was in a zone where no characters can be deleted. The called method
            # already pushed the cursor forwards.
            # => probably the user didn't type anything yet on the prompt, so only the prompt was
            #    selected.
            pass
        if selection_delete_result == "success":
            # This is what we expect if the user already has typed something on the prompt.
            pass
        # Print the new command.
        self.moveCursor(
            qt.QTextCursor.MoveOperation.End, qt.QTextCursor.MoveMode.MoveAnchor
        )
        if new_commandstr != "":
            self.printout_text(new_commandstr)
        return

    def __filter_command_list(
        self,
        commandlist: List[str],
        callback: Callable,
    ) -> None:
        """
        Given the commandlist, perform filtering on it and give it back. In case of error, return
        None. If that's the case, an error message is already printed - no more need to print
        another one!

        The filtered commandlist is given in a callback.
        """
        assert not self.__is_serial_monitor

        # * ----------------------[ NO KEY REPLACEMENTS ]--------------------- *#
        # Let's first deal with the situations where no key replacements are needed. In most cases,
        # this means that the commandlist must be returned 'as is' in the callback.
        if commandlist[0].startswith("python"):
            if len(commandlist) == 1:
                self.__start_new_block()
                self.printout_html(
                    f"{_ctag('yellow')}WARNING: The Embeetle Console "
                    f"cannot yet interact properly with interactive applications "
                    f"(like Python), unless you add the {q}-i{q} flag, like "
                    f"so:{_ctag('end')}<br>"
                    f"&nbsp;&nbsp;&nbsp;&nbsp;{commandlist[0]} -i<br>"
                    f"{_ctag('yellow')}With this flag, it will work "
                    f"for most basic functionalities.{_ctag('end')}<br>"
                )
                self.__print_toplevel_prompt()
                callback(None)
                return
            if len(commandlist) == 2:
                if commandlist[1] == "-i":
                    self.__start_new_block()
                    self.printout_html(
                        f"{_ctag('yellow')}The Embeetle Console is very basic. "
                        f"As of today, it can run an interactive Python session - but keep "
                        f"in mind it{q}s in alpha stage.{_ctag('end')}<br>"
                    )
                    callback(commandlist)
                    return

        if not hasattr(data, "current_project"):
            # The data module in the 'beetle_updater' code
            # has no 'current_project' field.
            callback(commandlist)
            return

        if data.is_home:
            # No keys to replace...
            callback(commandlist)
            return

        # * -----------------------[ KEY REPLACEMENTS ]----------------------- *#
        # Let's now deal with the situations that do require key replacements. We first create a key
        # dictionary that holds one entry per key found in any of the listed commands. The value for
        # each of them is set to None at the start. The keys are then put in an iterator and their
        # values determined one-by-one.
        # In the end - the finish() subfunction - we use the key dictionary to replace all the keys
        # in the listed commands. Then they are returned in a callback.
        treepath_seg = data.current_project.get_treepath_seg()
        toolpath_seg = data.current_project.get_toolpath_seg()
        # Build a 'key dictionary' like:
        #   key_dict = {
        #       '$(COMPILER_TOOLCHAIN)' : None,
        #       '$(MAKE)' : None,
        #       '$(COM)' : None,
        #       '$(FLASH_PORT)' : None,
        #   }
        # All values are still None at the moment.
        key_dict = {}
        p_key = re.compile(r"(\$\(\w*\))")
        for cmd in commandlist:
            for m in p_key.finditer(cmd):
                k = m.group(1)
                key_dict[k] = None

        def start(*args) -> None:
            start_process_next_key(iter(key_dict.keys()))
            return

        def start_process_next_key(key_iter) -> None:
            try:
                key = next(key_iter)
            except StopIteration:
                finish()
                return
            keyreplace(
                key=key,
                cb=finish_process_next_key,
                cbArg=key_iter,
            )
            return

        def finish_process_next_key(key, value, key_iter) -> None:
            key_dict[key] = value
            start_process_next_key(key_iter)
            return

        def keyreplace(key, cb, cbArg) -> None:
            # & Special treatment for $(TOOLCHAIN) and $(TOOLPREFIX)
            if (key == "$(TOOLCHAIN)") or (key == "$(COMPILER_TOOLCHAIN)"):
                compiler_abspath = toolpath_seg.get_compiler_abspath()
                if (compiler_abspath is None) or (
                    compiler_abspath.lower() == "none"
                ):
                    cb(key, key, cbArg)
                    return
                cb(
                    key,
                    f"{_pp_.standardize_abspath(os.path.dirname(compiler_abspath))}/",
                    cbArg,
                )
                return

            if key == "$(TOOLPREFIX)":
                toolpathObj = toolpath_seg.get_toolpathObj("COMPILER_TOOLCHAIN")
                if toolpathObj is None:
                    cb(key, key, cbArg)
                    return
                if (toolpathObj.get_toolprefix() is None) or (
                    toolpathObj.get_toolprefix().lower() == "none"
                ):
                    cb(key, key, cbArg)
                    return
                cb(key, toolpathObj.get_toolprefix(), cbArg)
                return

            # & Try a toolpath
            toolpath = None
            try:
                toolpath = toolpath_seg.get_abspath(key[2:-1])
            except Exception as e:
                pass
            if (toolpath is not None) and (toolpath.lower() != "none"):
                cb(key, toolpath, cbArg)
                return

            # & Try a treepath
            treepath = None
            try:
                treepath = treepath_seg.get_abspath(key[2:-1])
            except Exception as e:
                pass
            if (treepath is not None) and (treepath.lower() != "none"):
                cb(key, treepath, cbArg)
                return

            # & $(MAKE)
            if key == "$(MAKE)":
                make_abspath = toolpath_seg.get_abspath("BUILD_AUTOMATION")
                if (make_abspath is None) or (make_abspath.lower() == "none"):
                    cb(key, key, cbArg)
                    return
                cb(key, make_abspath, cbArg)
                return

            # & $(OPENOCD)
            if key == "$(OPENOCD)":
                if (toolpath_seg.get_unique_id("FLASHTOOL") is not None) and (
                    "openocd" in toolpath_seg.get_unique_id("FLASHTOOL").lower()
                ):
                    openocd_abspath = toolpath_seg.get_abspath("FLASHTOOL")
                    if (openocd_abspath is None) or (
                        openocd_abspath.lower() == "none"
                    ):
                        cb(key, key, cbArg)
                        return
                    cb(key, openocd_abspath, cbArg)
                    return
                cb(key, "$(OPENOCD_NOT_IN_USE)", cbArg)
                return

            # & $(OCD)
            if key == "$(OCD)":
                if (toolpath_seg.get_unique_id("FLASHTOOL") is not None) and (
                    "openocd" in toolpath_seg.get_unique_id("FLASHTOOL").lower()
                ):
                    openocd_abspath = toolpath_seg.get_abspath("FLASHTOOL")
                    if (openocd_abspath is None) or (
                        openocd_abspath.lower() == "none"
                    ):
                        cb(key, key, cbArg)
                        return
                    cb(key, openocd_abspath, cbArg)
                    return
                elif (toolpath_seg.get_unique_id("FLASHTOOL") is not None) and (
                    "pyocd" in toolpath_seg.get_unique_id("FLASHTOOL").lower()
                ):
                    pyocd_abspath = toolpath_seg.get_abspath("FLASHTOOL")
                    if (pyocd_abspath is None) or (
                        pyocd_abspath.lower() == "none"
                    ):
                        cb(key, key, cbArg)
                        return
                    cb(key, pyocd_abspath, cbArg)
                    return
                cb(key, "$(OPENOCD_OR_PYOCD_NOT_IN_USE)", cbArg)
                return

            # & $(FLASHTOOL)
            if key == "$(FLASHTOOL)":
                if toolpath_seg.get_unique_id("FLASHTOOL") is not None:
                    flashtool_abspath = toolpath_seg.get_abspath("FLASHTOOL")
                    print(
                        f"RETURNED FOR FLASHTOOL IN console_widget.py: {flashtool_abspath}"
                    )
                    if (flashtool_abspath is None) or (
                        flashtool_abspath.lower() == "none"
                    ):
                        cb(key, key, cbArg)
                        return
                    cb(key, flashtool_abspath, cbArg)
                    return
                cb(key, key, cbArg)
                return

            # & $(PYOCD)
            if key == "$(PYOCD)":
                if (toolpath_seg.get_unique_id("FLASHTOOL") is not None) and (
                    "pyocd" in toolpath_seg.get_unique_id("FLASHTOOL").lower()
                ):
                    pyocd_abspath = toolpath_seg.get_abspath("FLASHTOOL")
                    if (pyocd_abspath is None) or (
                        pyocd_abspath.lower() == "none"
                    ):
                        cb(key, key, cbArg)
                        return
                    cb(key, pyocd_abspath, cbArg)
                    return
                cb(key, "$(PYOCD_NOT_IN_USE)", cbArg)
                return

            # & $(GDB)
            if key == "$(GDB)":
                gdb_abspath = toolpath_seg.get_gdb_abspath()
                if (gdb_abspath is None) or (gdb_abspath.lower() == "none"):
                    cb(key, key, cbArg)
                    return
                cb(key, gdb_abspath, cbArg)
                return

            # & $(ELF)
            if key == "$(ELF)":
                elf_abspath = treepath_seg.get_abspath("ELF_FILE")
                if (elf_abspath is None) or (elf_abspath.lower() == "none"):
                    cb(key, key, cbArg)
                    return
                cb(key, elf_abspath, cbArg)
                return

            # & $(COM) or $(FLASH_PORT)
            if (key == "$(COM)") or (key == "$(FLASH_PORT)"):
                try:
                    selected_comport = (
                        data.current_project.get_probe().get_comport_name()
                    )
                    if (selected_comport is None) or (
                        selected_comport.lower() == "none"
                    ):
                        cb(key, None, cbArg)
                        return
                    # $ Windows
                    # Modify the COM-port string such that
                    # Windows can deal with it.
                    if os_checker.is_os("windows"):
                        nr = int(selected_comport.replace("COM", ""))
                        if nr < 10:
                            cb(key, f"COM{nr}", cbArg)
                            return
                        else:
                            if (
                                toolpath_seg.get_unique_id("FLASHTOOL")
                                is not None
                            ) and any(
                                s
                                in toolpath_seg.get_unique_id(
                                    "FLASHTOOL"
                                ).lower()
                                for s in ("avrdude", "bossac", "fermionic")
                            ):
                                # avrdude, bossac and fermionic don't like backslashes in the COM-
                                # port.
                                # Note: this code is copied in
                                # 'makefile_target_executer.py'!
                                cb(key, f"COM{nr}", cbArg)
                                return
                            cb(key, "\\" + f"\\.\\COM{nr}", cbArg)
                            return
                    # $ Linux
                    # No modifications needed.
                    elif os_checker.is_os("linux"):
                        cb(key, selected_comport, cbArg)
                        return
                    else:
                        raise EnvironmentError("Unsupported platform")
                except Exception as e:
                    purefunctions.printc(
                        f"\nERROR: Cannot acquire Serial Port:\n"
                        f"{e}\n"
                        f"\n",
                        color="error",
                    )
                    cb(key, None, cbArg)
                    return

            # & $(BOOT_COM) or $(BOOT_FLASH_PORT)
            if (key == "$(BOOT_COM)") or (key == "$(BOOT_FLASH_PORT)"):
                # Special case for ATmega32u4 such as on the Arduino Leonardo and Arduino Micro
                # boards: these boards identify themselves through one COM-port (eg. COM9) but you
                # need to flash through another (eg. COM10). This COM-port you need to flash through
                # is only available until a few seconds after reset. The trick is therefore to first
                # reset the board (by touching its serial port at a baudrate of 1200) and then look
                # out for any new COM-port that appears right after the reset.
                selected_comport = (
                    data.current_project.get_probe().get_comport_name()
                )
                if (selected_comport is None) or (
                    selected_comport.lower() == "none"
                ):
                    cb(key, None, cbArg)
                    return
                chipname = data.current_project.get_chip().get_name()
                before_ports = functions.list_serial_ports()
                self.printout_text(
                    f"\n"
                    f"Flashing firmware to the {chipname} microcontroller (eg. Arduino\n"
                    f"Leonardo or Arduino Micro) through its Serial Port requires a special\n"
                    f"approach.\n"
                    f"\n"
                    f"Unlike others, these boards identify themselves through one port (eg.\n"
                    f"COM9) while you need to flash them through another (eg. COM10). This\n"
                    f"Serial Port you need to flash the firmware through is only available\n"
                    f"during a couple of seconds just after a reset.\n"
                    f"\n"
                    f"Therefore, Embeetle will now reset your board and then look for any new\n"
                    f"Serial Port that appears right after the reset. To trigger a reset,\n"
                    f"Embeetle uses a trick: the selected Serial Port will be opened at baud-\n"
                    f"rate 1200 and quickly closed thereafter. This way, you don{q}t have to\n"
                    f"press the reset button.\n"
                    f"\n"
                )

                def reset_board(*args):
                    _serial_port_.touch_serial_port(
                        port=selected_comport,
                        baudrate=1200,
                        printfunc=self.printout_text,
                        callback=find_new_serial_port,
                    )
                    return

                def find_new_serial_port(*args):
                    _serial_port_.wait_for_new_serial_port(
                        before_portnames=list(before_ports.keys()),
                        fallback_portname=selected_comport,
                        printfunc=self.printout_text,
                        callback=acquire_new_serial_port,
                    )
                    return

                def acquire_new_serial_port(new_port, *args):
                    self.printout_text(
                        f"  > Port {q}{new_port}{q} selected to flash firmware.\n"
                        f"\n"
                        f"Now invoke the {q}make{q} command to proceed. Pass it {q}BOOT_FLASH_PORT={new_port}{q}\n"
                        f"as a commandline argument:\n"
                    )
                    self.__print_toplevel_prompt()
                    qt.QTimer.singleShot(
                        150,
                        functools.partial(
                            return_new_serial_port,
                            new_port,
                        ),
                    )
                    return

                def return_new_serial_port(new_port, *args):
                    if new_port is None:
                        cb(key, None, cbArg)
                        return
                    cb(key, new_port, cbArg)
                    return

                reset_board()
                return

            # * $(SOMETHING_ELSE)
            # Some not known key, just return it 'as is'.
            cb(key, key, cbArg)
            return

        def finish(*args) -> None:
            new_commandlist = []
            for _cmd in commandlist:
                new_cmd = _cmd
                for _m in p_key.finditer(_cmd):
                    key = str(_m.group(1))
                    value = str(
                        "None" if key_dict[key] is None else key_dict[key]
                    )
                    new_cmd = new_cmd.replace(key, value)
                new_commandlist.append(new_cmd)
            callback(new_commandlist)
            return

        start()
        return

    # ^                                         USER INPUT                                          |

    #! -----------------[ MOUSE EVENTS ]----------------- !#
    @qt.pyqtSlot(qt.QMouseEvent)
    def mousePressEvent(self, e: qt.QMouseEvent) -> None:
        """Code needed to make hyperlinks clickable.

        https://stackoverflow.com/questions/35858340/clickable-hyperlink-in-qtextedit
        """
        super().mousePressEvent(e)
        # Use QMouseEvent.position() instead of QMouseEvent.pos(), the returned object is a
        # QPointF() instead of a QPoint()
        self.anchor = self.anchorAt(e.position().toPoint())
        if self.anchor:
            self.viewport().setCursor(qt.Qt.CursorShape.PointingHandCursor)
            # QApplication.setOverrideCursor(qt.Qt.CursorShape.PointingHandCursor)
        return

    @qt.pyqtSlot(qt.QMouseEvent)
    def mouseReleaseEvent(self, e: qt.QMouseEvent) -> None:
        """Code needed to make hyperlinks clickable.

        https://stackoverflow.com/questions/35858340/clickable-hyperlink-in-qtextedit
        """
        super().mouseReleaseEvent(e)
        if self.anchor:
            print(self.anchor)
            functions.open_url(self.anchor)
            self.viewport().setCursor(qt.Qt.CursorShape.IBeamCursor)
            # QApplication.setOverrideCursor(qt.Qt.CursorShape.ArrowCursor)
            self.anchor = None
        return

    @qt.pyqtSlot(qt.QMouseEvent)
    def mouseMoveEvent(self, e: qt.QMouseEvent) -> None:
        """Code needed to change the arrow into a hand when hovering over a
        clickable hyperlink."""
        super().mouseMoveEvent(e)
        # Use QMouseEvent.position() instead of QMouseEvent.pos(), the returned object is a
        # QPointF() instead of a QPoint()
        self.anchor = self.anchorAt(e.position().toPoint())
        if self.anchor:
            self.viewport().setCursor(qt.Qt.CursorShape.PointingHandCursor)
            # QApplication.setOverrideCursor(qt.Qt.CursorShape.PointingHandCursor)
        else:
            self.viewport().setCursor(qt.Qt.CursorShape.IBeamCursor)
            # QApplication.setOverrideCursor(qt.Qt.CursorShape.ArrowCursor)
        return

    #! -------------[ CUT-COPY-PASTE EVENTS ]------------- !#
    @qt.pyqtSlot()
    def copy(self) -> None:
        """Override the default 'copy()' method, such that the copied text gets
        unselected."""
        super().copy()
        cursor: qt.QTextCursor = self.textCursor()
        cursorpos: int = cursor.position()
        anchorpos: int = cursor.anchor()
        cursor.setPosition(
            cursorpos,
            qt.QTextCursor.MoveMode.MoveAnchor,
        )
        self.setTextCursor(cursor)
        return

    @qt.pyqtSlot()
    def paste(self) -> None:
        """Override the default 'paste()' method, such that the user can't paste
        text anywhere."""
        clipboard = data.application.clipboard()
        text = clipboard.text().strip()

        # * Ignore if content has newlines
        if ("\r" in text) or ("\n" in text):
            self.__start_new_block()
            self.printout_html(
                f"{_ctag('red')}ERROR: you attempted to paste multiple "
                f"commands in this console.{_ctag('end')}<br>"
                f"{_ctag('yellow')}The Embeetle Console is very basic. "
                f"As of today, you can{q}t paste multiple commands and get them "
                f"to execute one-by-one. We{q}ll work hard to improve this console."
                f"{_ctag('end')}<br>"
            )
            self.__print_toplevel_prompt()
            return

        # * Deal with selected text
        # We don't know at this point if text is selected. However,
        # the method 'self.__remove_selected_text()' simply returns
        # 'no_selection' in that case, so we can proceed.
        selection_delete_result = self.__remove_selected_text()
        if selection_delete_result == "err":
            # The called method could not proceed because of
            # an error. It (perhaps) printed a new prompt to
            # correct the situation.
            return
        if selection_delete_result == "ignored":
            # The selected text was in a zone where no char-
            # acters can be deleted. The called method already
            # pushed the cursor forwards. We also don't want
            # to paste in this situation.
            return
        if selection_delete_result == "success":
            # Selected text is gone. Great, now proceed.
            pass
        if selection_delete_result == "no_selection":
            # That's okay. Just proceed.
            pass

        # * Acquire cursor
        # Thanks to running the 'self.__remove_selected_text()' method,
        # we can assert a few things (eg. there is a prompt found, ...).
        prompt, commandstr = self.__extract_cmd()
        prompt_dist = self.__get_prompt_distance(prompt)
        assert prompt is not None
        assert prompt_dist is not None
        lastblock: qt.QTextBlock = self.document().lastBlock()
        cursor: qt.QTextCursor = self.textCursor()
        # Define cursor position referenced to the start of
        # the last block.
        cursorpos: int = cursor.position() - lastblock.position()
        anchorpos: int = cursor.anchor() - lastblock.position()
        assert anchorpos == cursorpos

        # $ Cursor negative (before the prompt) or somewhere in the prompt
        # Push the cursor to the prompt edge and return.
        if cursorpos < prompt_dist:
            cursor.setPosition(
                lastblock.position() + prompt_dist,
                qt.QTextCursor.MoveMode.MoveAnchor,
            )
            self.setTextCursor(cursor)
            return

        # $ Cursor beyond the prompt (or at edge)
        # Paste the content.
        assert cursorpos >= prompt_dist
        super().paste()
        return

    #! ------------------[ KEY PRESSES ]------------------- !#
    @qt.pyqtSlot(qt.QKeyEvent)
    def keyPressEvent(self, event: qt.QKeyEvent) -> None:
        """Override qt.QPlainTextEdit.keyPressEvent(event)"""
        # * CUT-COPY-PASTE
        if (event.key() == qt.Qt.Key.Key_X) and (
            event.modifiers() & qt.Qt.KeyboardModifier.ControlModifier
        ):
            # Run the copy() method from the superclass,
            # to avoid the unselection.
            super().copy()
            self.__remove_selected_text()
            return
        if (event.key() == qt.Qt.Key.Key_C) and (
            event.modifiers() & qt.Qt.KeyboardModifier.ControlModifier
        ):
            # Just copy()
            if self.textCursor().hasSelection():
                self.copy()
                return
            # Kill current process
            self.close_command()
            return
        if (event.key() == qt.Qt.Key.Key_V) and (
            event.modifiers() & qt.Qt.KeyboardModifier.ControlModifier
        ):
            self.paste()
            return

        # * UNDO-REDO
        if (event.key() == qt.Qt.Key.Key_Z) and (
            event.modifiers() & qt.Qt.KeyboardModifier.ControlModifier
        ):
            # Undo can delete whole blocks of text, including
            # previous commands and their outputs.
            return
        if (event.key() == qt.Qt.Key.Key_Y) and (
            event.modifiers() & qt.Qt.KeyboardModifier.ControlModifier
        ):
            # As 'undo' is ignored, why keep 'redo'?
            return

        # * BACKSPACE-DEL
        if event.key() == qt.Qt.Key.Key_Backspace:
            self.__backsp_key(event)
            return
        if event.key() == qt.Qt.Key.Key_Delete:
            self.__del_key(event)
            return

        # * ARROW KEYS
        if (
            (event.key() == qt.Qt.Key.Key_Left)
            and (event.modifiers() & qt.Qt.KeyboardModifier.ShiftModifier)
            or (event.key() == qt.Qt.Key.Key_Right)
            and (event.modifiers() & qt.Qt.KeyboardModifier.ShiftModifier)
            or (event.key() == qt.Qt.Key.Key_Up)
            and (event.modifiers() & qt.Qt.KeyboardModifier.ShiftModifier)
            or (event.key() == qt.Qt.Key.Key_Down)
            and (event.modifiers() & qt.Qt.KeyboardModifier.ShiftModifier)
            or (event.key() == qt.Qt.Key.Key_Home)
            and (event.modifiers() & qt.Qt.KeyboardModifier.ShiftModifier)
            or (event.key() == qt.Qt.Key.Key_End)
            and (event.modifiers() & qt.Qt.KeyboardModifier.ShiftModifier)
        ):
            qt.QPlainTextEdit.keyPressEvent(self, event)
            return
        if event.key() == qt.Qt.Key.Key_Up:
            self.__up_down_key(event, "up")
            return
        if event.key() == qt.Qt.Key.Key_Down:
            self.__up_down_key(event, "down")
            return
        if event.key() == qt.Qt.Key.Key_Left:
            qt.QPlainTextEdit.keyPressEvent(self, event)
            return
        if event.key() == qt.Qt.Key.Key_Right:
            qt.QPlainTextEdit.keyPressEvent(self, event)
            return

        # * ENTER
        if (event.key() == qt.Qt.Key.Key_Return) or (
            event.key() == qt.Qt.Key.Key_Enter
        ):
            self.__enter_key(event)
            return

        # * OTHER SPECIAL KEYS
        if (
            (event.key() == qt.Qt.Key.Key_Control)
            or (event.key() == qt.Qt.Key.Key_Shift)
            or (event.key() == qt.Qt.Key.Key_Alt)
            or (event.key() == qt.Qt.Key.Key_AltGr)
        ):
            qt.QPlainTextEdit.keyPressEvent(self, event)
            return
        if (event.key() == qt.Qt.Key.Key_A) and (
            event.modifiers() & qt.Qt.KeyboardModifier.ControlModifier
        ):
            qt.QPlainTextEdit.keyPressEvent(self, event)
            return
        if (event.key() == qt.Qt.Key.Key_PageUp) or (
            event.key() == qt.Qt.Key.Key_PageDown
        ):
            qt.QPlainTextEdit.keyPressEvent(self, event)
            return
        if event.key() == qt.Qt.Key.Key_Home:
            qt.QPlainTextEdit.keyPressEvent(self, event)
            return
        if event.key() == qt.Qt.Key.Key_End:
            qt.QPlainTextEdit.keyPressEvent(self, event)
            return

        # * REGULAR KEYS
        if self.isReadOnly() or self.__is_serial_monitor:
            qt.QPlainTextEdit.keyPressEvent(self, event)
            return
        prompt, commandstr = self.__extract_cmd()
        prompt_dist = self.__get_prompt_distance(prompt)
        if prompt is None:
            # Console is idle but no prompt detected,
            # correct this situation!
            purefunctions.printc(
                "ERROR: Console was sitting idle, and yet no"
                "prompt could be detected!",
                color="error",
            )
            self.__print_toplevel_prompt()
            return
        assert prompt is not None
        assert prompt_dist is not None
        lastblock: qt.QTextBlock = self.document().lastBlock()
        cursor: qt.QTextCursor = self.textCursor()
        # Define cursor position referenced to the start of
        # the last block.
        cursorpos: int = cursor.position() - lastblock.position()
        anchorpos: int = cursor.anchor() - lastblock.position()

        # $ Cursor and/or Anchor negative (before the prompt)
        # $ or somewhere in the prompt
        # Push the cursor to the prompt edge and return.
        if (cursorpos < prompt_dist) or (anchorpos < prompt_dist):
            cursor.setPosition(
                lastblock.position() + prompt_dist,
                qt.QTextCursor.MoveMode.MoveAnchor,
            )
            self.setTextCursor(cursor)
            return
        # $ Cursor beyond the prompt (or at edge)
        # Just execute the keypress.
        qt.QPlainTextEdit.keyPressEvent(self, event)
        return

    def __enter_key(self, event: qt.QKeyEvent) -> None:
        """Extract the prompt and commandstr, attempt to execute the command."""
        prompt, commandstr = self.__extract_cmd()
        if commandstr is None:
            return

        # * Previous process still busy
        if self.__target is not None:
            self.__start_new_block()
            commandstr += "\n"
            self.__target.send(commandstr.encode("utf-8"))
            return

        # * Console idle
        if commandstr == "":
            self.__print_toplevel_prompt()
            return
        if prompt is None:
            # Console is idle but no prompt detected, correct this situation!
            purefunctions.printc(
                "ERROR: Console was sitting idle, and yet no"
                "prompt could be detected!",
                color="error",
            )
            self.__print_toplevel_prompt()
            return
        self.run_command(
            commandlist=shlex.split(commandstr),
            printout=False,
        )
        return

    def __backsp_key(
        self, event: qt.QKeyEvent, del_action: bool = False
    ) -> None:
        """Disallow deleting stuff randomly.

        Perform some magic with the cursor to ensure this doesn't happen.
        """
        # * Deal with selected text
        # We don't know at this point if text is selected. However, the method 'self.__remove_
        # selected_text()' simply returns 'no_selection' in that case, so we can proceed. Otherwise,
        # it performs all the work.
        selection_delete_result = self.__remove_selected_text()
        if selection_delete_result == "err":
            # The called method could not proceed because of an error. It (perhaps) printed a new
            # prompt to correct the situation.
            return
        if selection_delete_result == "ignored":
            # The selected text was in a zone where no characters can be deleted. The called method
            # already pushed the cursor forwards.
            return
        if selection_delete_result == "success":
            # Nothing to do anymore.
            return

        # * Deal with unselected text
        # Arriving here, we know that 'self.__remove_selected_text()' did not find any selected
        # text. We also know that the method already dealt with error situations (eg. no prompt), so
        # we can put the corresonding assertions below.
        assert selection_delete_result == "no_selection"
        prompt, commandstr = self.__extract_cmd()
        prompt_dist = self.__get_prompt_distance(prompt)
        assert prompt is not None
        assert prompt_dist is not None
        lastblock: qt.QTextBlock = self.document().lastBlock()
        cursor: qt.QTextCursor = self.textCursor()

        # Define cursor position referenced to the start of the last block.
        cursorpos: int = cursor.position() - lastblock.position()
        anchorpos: int = cursor.anchor() - lastblock.position()
        assert anchorpos == cursorpos

        # $ Cursor right at the prompt edge
        # Ignore if backspace but accept if a del.
        if cursorpos == prompt_dist:
            if del_action:
                qt.QPlainTextEdit.keyPressEvent(self, event)
            return

        # $ Cursor negative (before the prompt) or somewhere in the prompt
        # Push the cursor to the prompt edge and return.
        if cursorpos < prompt_dist:
            cursor.setPosition(
                lastblock.position() + prompt_dist,
                qt.QTextCursor.MoveMode.MoveAnchor,
            )
            self.setTextCursor(cursor)
            return

        # $ Cursor beyond the prompt
        # Perform the backspace or del operation.
        assert cursorpos > prompt_dist
        qt.QPlainTextEdit.keyPressEvent(self, event)
        return

    def __del_key(self, event: qt.QKeyEvent) -> None:
        """Disallow deleting stuff randomly.

        Perform some magic with the cursor to ensure this doesn't happen.
        """
        self.__backsp_key(event, del_action=True)
        return

    def __up_down_key(self, event: qt.QKeyEvent, direction: str) -> None:
        """User pressed up or down key."""
        if direction == "up":
            self.__toplevel_command_history_index -= 1
        else:
            self.__toplevel_command_history_index += 1
        # The index must not be negative
        self.__toplevel_command_history_index = max(
            0,
            self.__toplevel_command_history_index,
        )
        # The index should stay in the range of the command
        # history list *or* be equal to the length of that
        # list. If so, it corresponds to an empty command.
        self.__toplevel_command_history_index = min(
            len(self.__toplevel_command_history),
            self.__toplevel_command_history_index,
        )
        replacement_command = ""
        if self.__toplevel_command_history_index != len(
            self.__toplevel_command_history
        ):
            replacement_command = " ".join(
                self.__toplevel_command_history[
                    self.__toplevel_command_history_index
                ]
            )
        print(f"\ncommand = {replacement_command}")
        self.__replace_cmd(replacement_command)
        return

    #! -------------[ CONTEXT MENU EVENT ]------------- !#
    @qt.pyqtSlot(qt.QContextMenuEvent)
    def contextMenuEvent(self, event: qt.QContextMenuEvent) -> None:
        """User right-clicked somewhere in the Console Body."""
        contextmenu = _console_contextmenu_.ConsoleBodyContextMenu(
            toplvl_key="console",
            clickfunc=self.contextmenuclick,
        )
        _contextmenu_launcher_.ContextMenuLauncher().launch_contextmenu(
            contextmenu=contextmenu,
            point=functions.get_position(event),
            callback=None,
            callbackArg=None,
        )
        return

    def contextmenuclick(self, key: str) -> None:
        """User made his choice in the Context Menu."""
        key = functions.strip_toplvl_key(key)

        def clean(_key: str) -> None:
            self.clear()
            return

        def abort(_key: str) -> None:
            self.close_command()
            return

        def undo(_key: str) -> None:
            self.keyPressEvent(
                qt.QKeyEvent(
                    qt.QEvent.Type.KeyPress,
                    qt.Qt.Key.Key_Z,
                    qt.Qt.KeyboardModifier.ControlModifier,
                    "",
                )
            )
            return

        def redo(_key: str) -> None:
            self.keyPressEvent(
                qt.QKeyEvent(
                    qt.QEvent.Type.KeyPress,
                    qt.Qt.Key.Key_Y,
                    qt.Qt.KeyboardModifier.ControlModifier,
                    "",
                )
            )
            return

        def cut(_key: str) -> None:
            self.keyPressEvent(
                qt.QKeyEvent(
                    qt.QEvent.Type.KeyPress,
                    qt.Qt.Key.Key_X,
                    qt.Qt.KeyboardModifier.ControlModifier,
                    "",
                )
            )
            return

        def _copy(_key: str) -> None:
            self.keyPressEvent(
                qt.QKeyEvent(
                    qt.QEvent.Type.KeyPress,
                    qt.Qt.Key.Key_C,
                    qt.Qt.KeyboardModifier.ControlModifier,
                    "",
                )
            )
            return

        def paste(_key: str) -> None:
            self.keyPressEvent(
                qt.QKeyEvent(
                    qt.QEvent.Type.KeyPress,
                    qt.Qt.Key.Key_V,
                    qt.Qt.KeyboardModifier.ControlModifier,
                    "",
                )
            )
            return

        def delete(_key: str) -> None:
            self.keyPressEvent(
                qt.QKeyEvent(
                    qt.QEvent.Type.KeyPress,
                    qt.Qt.Key.Key_Delete,
                    qt.Qt.KeyboardModifier.NoModifier,
                    "",
                )
            )
            return

        def select_all(_key: str) -> None:
            self.keyPressEvent(
                qt.QKeyEvent(
                    qt.QEvent.Type.KeyPress,
                    qt.Qt.Key.Key_A,
                    qt.Qt.KeyboardModifier.ControlModifier,
                    "",
                )
            )
            return

        funcs = {
            "clean": clean,
            "abort": abort,
            "undo": undo,
            "redo": redo,
            "cut": cut,
            "copy": _copy,
            "paste": paste,
            "delete": delete,
            "select_all": select_all,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return

    # ^                                        PROGBAR STUFF                                        |

    #! ------------------[ INTERNAL PROGBAR ]------------------- !#
    @qt.pyqtSlot(str)
    def start_progbar(self, title: str) -> None:
        """
        Attempt to start a new progressbar in this console.

                  ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
        FOOBAR    ┃████████      ┃
                  ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔

        The actual creation of the progbar can happen after this method reinvokes itself with a
        signal (to run in the main thread). So you don't know if the attempt to create the progbar
        was successful right after running this method. Therefore, check the 'is_progbar_open()'
        method.

        MUTEXES
        =======
        'self.__progbar_exists_mutex':
            Only one progbar can exist at any given time. The creation of a progbar is protected
            with the 'self.__progbar_exists_mutex'.
            => remains locked until closed!

        'self.__target_mutex':
            A progbar can never co-exist with targets such as a running process. Therefore, I also
            lock the 'self.__target_mutex' mutex.
            => remains locked until closed!

        'self.__progbar_set_val_mutex':
            While creating this new progbar, we don't want it to start already drawing blocks during
            its own creation process.
            => brief lock only.

        OTHER PROTECTIONS
        =================
        One should not print anything to this ConsoleWidget when a progbar is active. Therefore, I
        test for the progbar existence mutex at the start of each printout function!

        """
        # * Basic checks
        if qt.sip.isdeleted(self):
            return
        if not threading.current_thread() is threading.main_thread():
            self.start_progbar_sig.emit(title)
            return

        # * Lock mutexes
        # Lock the 'self.__progbar_exists_mutex' and keep it locked during the whole existence of
        # this progbar!
        if not self.__progbar_exists_mutex.acquire(blocking=False):
            purefunctions.printc(
                "ERROR: Attempted to create a progbar in the ConsoleWidget() "
                "while another progbar was open!",
                color="error",
            )
            return
        # Also lock the 'self.__target_mutex' for this whole time, to ensure no one can launch a
        # target as long as this progbar exists!
        if not self.__target_mutex.acquire(blocking=False):
            purefunctions.printc(
                "ERROR: Attempted to create a progbar in the ConsoleWidget() "
                "while running a target!",
                color="error",
            )
            self.__progbar_exists_mutex.release()
            return
        # Thanks to the previous lock, no new targets can be launched from now on. But what if one
        # was already running?
        if self.__target is not None:
            purefunctions.printc(
                "ERROR: Attempted to create a progbar in the ConsoleWidget() "
                "while running a target!",
                color="error",
            )
            self.__progbar_exists_mutex.release()
            self.__target_mutex.release()
            return
        # Lock the 'self.__progbar_set_val_mutex' for a brief moment, such that signals to draw
        # blocks in this progbar won't mess up this initial drawing!
        with self.__progbar_set_val_mutex:
            title = title.ljust(self.__tsize).replace(" ", "&nbsp;")
            self.__progbar_buf = 0.0
            self.__progbar_printed_blocks = 0
            self.__start_new_block()
            drawing = str(
                "&nbsp;" * self.__tsize
                + "&#9601;" * (self.__bsize + 2)
                + "<br>"
                + f"{_ctag('yellow')}{title}{_ctag('end')}"
                + "&#9475;"
                + "&nbsp;" * self.__bsize
                + "&#9475;<br>"
                + "&nbsp;" * self.__tsize
                + "&#9620;" * (self.__bsize + 2)
            )
            self.moveCursor(qt.QTextCursor.MoveOperation.End)
            self.textCursor().insertHtml(drawing)
            self.moveCursor(qt.QTextCursor.MoveOperation.End)
        assert self.__progbar_exists_mutex.locked()
        assert self.__target_mutex.locked()
        return

    def set_progbar_val(self, fval: float) -> None:
        """This method won't draw anything immediately. It merely assigns the
        given value to a buffer and then exits. It will only emit the drawing
        signal if the new value is significantly higher, or zero, or 100.

        MUTEXES ======= 'self.__progbar_set_val_mutex':     While writing to the
        buffer, we keep this mutex locked.     => brief lock only.
        """
        # * Basic checks
        if qt.sip.isdeleted(self):
            return
        if not self.__progbar_exists_mutex.locked():
            purefunctions.printc(
                "ERROR: Attempt to set a value on a non-existing progbar "
                "in the ConsoleWidget()!",
                color="error",
            )
            return

        # * Write to buffer
        with self.__progbar_set_val_mutex:
            # Only apply the value if it's zero or significantly higher than the stored value. This
            # avoids event overloads.
            # $ Same value
            if self.__progbar_buf == fval:
                # ignore
                return
            # $ Zero or 100 value
            if (fval == 0.0) or (fval == 100.0):
                self.__progbar_buf = fval
                self.apply_progbar_val_sig.emit()
                return
            # $ Smaller value
            if fval <= self.__progbar_buf:
                # ignore
                return
            # $ Insignificant value
            if (fval - self.__progbar_buf) < 1:
                # write to buffer only
                self.__progbar_buf = fval
                return
            # $ Significant value
            self.__progbar_buf = fval
            self.apply_progbar_val_sig.emit()
        return

    @qt.pyqtSlot()
    def apply_progbar_val(self) -> None:
        """This method will actually draw the value stored in the buffer.

        MUTEXES ======= 'self.__progbar_set_val_mutex':     While drawing the
        value from the buffer, we keep this mutex locked.     => brief lock
        only.
        """
        # & Basic checks
        assert threading.current_thread() is threading.main_thread()
        if qt.sip.isdeleted(self):
            return
        if not self.__progbar_exists_mutex.locked():
            # purefunctions.printc(
            #     'ERROR: Attempt to apply a value on a non-existing progbar '
            #     'in the ConsoleWidget()!',
            #     color='error',
            # )
            return

        # & Draw value from buffer
        with self.__progbar_draw_val_mutex:
            # It could be that 'close_progbar()' just released the mutex after doing its thing. So
            # check if the progbar isn't closed at this point!
            if not self.__progbar_exists_mutex.locked():
                purefunctions.printc(
                    f"WARNING: {q}apply_progbar_val(){q} was invoked after the "
                    f"{q}close_progbar(){q} command.",
                    color="warning",
                )
                return
            try:
                val: int = int((self.__progbar_buf / 100) * self.__bsize)
                if val == self.__progbar_printed_blocks:
                    # Nothing to print
                    return
                diff = val - self.__progbar_printed_blocks
                cursor: qt.QTextCursor = self.textCursor()
                cursor.movePosition(
                    qt.QTextCursor.MoveOperation.End,
                    qt.QTextCursor.MoveMode.MoveAnchor,
                )
                cursor.movePosition(
                    qt.QTextCursor.MoveOperation.StartOfLine,
                    qt.QTextCursor.MoveMode.MoveAnchor,
                )
                cursor.movePosition(
                    qt.QTextCursor.MoveOperation.Up,
                    qt.QTextCursor.MoveMode.MoveAnchor,
                )
                cursor.movePosition(
                    qt.QTextCursor.MoveOperation.Right,
                    qt.QTextCursor.MoveMode.MoveAnchor,
                    self.__tsize + 1,
                )
                cursor.movePosition(
                    qt.QTextCursor.MoveOperation.Right,
                    qt.QTextCursor.MoveMode.MoveAnchor,
                    self.__progbar_printed_blocks,
                )
                for i in range(diff):
                    cursor.deleteChar()
                cursor.insertHtml(
                    f'<span style="color:#fce94f;">{"&#9608;" * diff}</span>'
                )
                self.__progbar_printed_blocks = val
            except Exception as e:
                purefunctions.printc(
                    f"\nERROR: error in {q}apply_progbar_val({self.__progbar_buf}){q}:"
                    f"\n{e}",
                    color="error",
                )
        return

    def close_progbar(self) -> None:
        """Close the progbar, release all mutexes.

        Also insert a new block (so a newline).
        """
        # & Basic checks
        if qt.sip.isdeleted(self):
            return
        with self.__progbar_set_val_mutex:
            self.__progbar_buf = 0.0
            self.__progbar_exists_mutex.release()
            self.__target_mutex.release()
            if threading.current_thread() is threading.main_thread():
                self.__start_new_block()
            else:
                self.start_new_block_sig.emit()
        return

    def is_progbar_open(self) -> bool:
        """"""
        return self.__progbar_exists_mutex.locked()

    #! ------------------[ EXTERNAL PROGBAR ]------------------- !#
    def register_inc_str(self, inc_str: Optional[str]) -> None:
        """Register a string this ConsoleWidget() has to look for, such that it
        can properly launch the 'inc_external_progbar_sig' signal.

        Set to None to deactivate.
        """
        self.__ext_progbar_inc_str = inc_str
        return
