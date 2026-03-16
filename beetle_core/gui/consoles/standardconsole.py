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

import enum
import locale
import os
import queue
import re
import subprocess
import sys
import threading
import typing
from time import time

import data
import functions
import gui.helpers.buttons
import gui.templates.baseobject
import gui.templates.textmanipulation
import gui.templates.widgetgenerator
import qt


class ColorTheme(enum.Enum):
    command = enum.auto()
    info = enum.auto()
    error = enum.auto()
    warning = enum.auto()
    path = enum.auto()
    output = enum.auto()


class ProcessReturnCode(enum.IntEnum):
    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_ARGUMENT = 2
    NOT_EXECUTABLE = 126
    COMMAND_NOT_FOUND = 127
    INTERRUPTED = 130  # Terminated by Ctrl-C


def get_color(color_theme: ColorTheme) -> str:
    colors: typing.Dict[ColorTheme, str] = {
        ColorTheme.command: data.theme["console"]["fonts"]["teal"],
        ColorTheme.info: data.theme["fonts"]["default"]["color"],
        ColorTheme.error: data.theme["console"]["fonts"]["error"],
        ColorTheme.warning: data.theme["console"]["fonts"]["warning"],
        ColorTheme.path: data.theme["console"]["fonts"]["path"],
        ColorTheme.output: data.theme["fonts"]["default"]["color"],
    }
    return colors[color_theme]


# === Cross-platform I/O availability detection ===
if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes
    import msvcrt

    class PEEKNAMEDPIPE(ctypes.Structure):
        _fields_: typing.List[typing.Tuple[str, typing.Type]] = [
            ("hNamedPipe", ctypes.wintypes.HANDLE),
            ("lpBuffer", ctypes.wintypes.DWORD),
            ("nBufferSize", ctypes.wintypes.DWORD),
            ("lpBytesRead", ctypes.wintypes.DWORD),
            ("lpTotalBytesAvail", ctypes.wintypes.DWORD),
            ("lpBytesLeftThisMessage", ctypes.wintypes.DWORD),
        ]

else:
    import select


class ConsoleWorker(qt.QObject):
    """Runs shell commands in a background thread and detects interactive behavior."""

    output_received: qt.pyqtSignal = qt.pyqtSignal(str)
    command_finished: qt.pyqtSignal = qt.pyqtSignal(int)
    suspected_interactive: qt.pyqtSignal = qt.pyqtSignal()
    start_execution: qt.pyqtSignal = qt.pyqtSignal()

    def __init__(
        self, command: str, cwd: str, shell: str, shell_argument: str
    ) -> None:
        super().__init__()
        self.command: str = command
        self.cwd: str = cwd
        self.shell: str = shell
        self.shell_argument: str = shell_argument
        self.process: typing.Optional[subprocess.Popen] = None
        self.first_output_made: bool = False
        self.return_code: typing.Optional[int] = None
        self.start_execution.connect(self.execute)

    @qt.pyqtSlot()
    def execute(self) -> None:
        self.first_output_made = False
        encoding = locale.getpreferredencoding()

        try:
            # Use the selected shell executable and its specific argument
            command_list = [self.shell, self.shell_argument, self.command]

            self.process = subprocess.Popen(
                command_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=False,
                shell=False,
                bufsize=0,
                cwd=self.cwd,
            )

            while self.process.poll() is None:
                has_data = self.is_data_available(self.process.stdout)

                if has_data:
                    line: bytes = self.process.stdout.readline()
                    if line:
                        decoded_line: str = line.decode(
                            encoding, errors="replace"
                        )
                        self.output_received.emit(decoded_line)
                        self.first_output_made = True
                        if self.is_interactive_prompt(decoded_line):
                            self.suspected_interactive.emit()
                            return

                # Do not block the thread.
                functions.process_events()

            # Capture any remaining output
            try:
                remaining_out, _ = self.process.communicate(timeout=2)
                if remaining_out:
                    try:
                        decoded: str = remaining_out.decode(
                            encoding, errors="replace"
                        )
                        self.output_received.emit(decoded)
                    except (UnicodeDecodeError, ValueError):
                        self.output_received.emit("[Remaining decode error]\n")
            except (subprocess.TimeoutExpired, OSError):
                if self.process:
                    self.process.kill()
                    self.process.wait(timeout=1)

        except (OSError, subprocess.SubprocessError) as e:
            self.output_received.emit(f"Process error: {str(e)}\n")
            self.return_code = -1
        except Exception as e:
            self.output_received.emit(f"Unexpected error: {str(e)}\n")
            self.return_code = -1
        finally:
            if self.process:
                self.return_code = self.process.returncode
            self.command_finished.emit(
                self.return_code if self.return_code is not None else -1
            )

    def is_data_available(self, pipe: typing.IO) -> bool:
        try:
            if sys.platform == "win32":
                return self._is_data_available_windows(pipe)
            else:
                return self._is_data_available_unix(pipe)
        except (OSError, ValueError, AttributeError):
            return False

    def _is_data_available_unix(self, pipe: typing.IO) -> bool:
        try:
            ready, _, _ = select.select([pipe], [], [], 0)
            return pipe in ready
        except (OSError, ValueError, select.error):
            return False

    def _is_data_available_windows(self, pipe: typing.IO) -> bool:
        try:
            handle: int = msvcrt.get_osfhandle(pipe.fileno())
            avail: ctypes.wintypes.DWORD = ctypes.wintypes.DWORD(0)
            success: int = ctypes.windll.kernel32.PeekNamedPipe(
                handle, None, 0, None, ctypes.byref(avail), None
            )
            return success != 0 and avail.value > 0
        except (OSError, AttributeError, ValueError):
            return False

    def is_interactive_prompt(self, text: str) -> bool:
        """Detect common interactive prompts like >>>, (gdb), $, etc."""
        if not text:
            return False

        patterns: typing.List[str] = [
            r"^\(Pdb\)\s*$",
            r"^\(gdb\)\s*$",
            r"^>>>\s*$",
            r"^In \[\d+\]:\s*$",
            r"^[^\S\r\n]*[$#]\s*$",
            r"^.*?>\s*$",
            r"^sqlite>\s*$",
            r"^mysql>\s*$",
            r"^psql>\s*$",
            r"^telnet>\s*$",
            r"^ftp>\s*$",
            r"^[irc]>",
        ]
        last_line = text.strip().split("\n")[-1]
        return any(re.search(pattern, last_line) for pattern in patterns)


class EditablePathWidget(qt.QWidget):
    """A widget that displays and allows editing of the current directory."""

    path_changed: qt.pyqtSignal = qt.pyqtSignal(str)

    def __init__(
        self, initial_path: str, parent: typing.Optional[qt.QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.current_path: str = initial_path
        self.parent_widget: typing.Optional[qt.QWidget] = parent

        layout: qt.QHBoxLayout = qt.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.line_edit: gui.templates.widgetgenerator.TextBox = (
            gui.templates.widgetgenerator.create_textbox(
                parent=self,
                name="StandardTextBox",
                h_size_policy=qt.QSizePolicy.Policy.Expanding,
                v_size_policy=qt.QSizePolicy.Policy.Expanding,
            )
        )
        self.line_edit.setText(self.current_path)
        self.line_edit.setReadOnly(True)
        layout.addWidget(self.line_edit)
        self.setLayout(layout)

    def enter_edit_mode(self) -> None:
        self.line_edit.setReadOnly(False)
        self.line_edit.selectAll()
        self.line_edit.setFocus(qt.Qt.FocusReason.OtherFocusReason)

    def set_path(self, path: str) -> None:
        self.current_path = path
        self.line_edit.setText(path)
        self.line_edit.home(False)

    def get_path(self) -> str:
        return self.line_edit.text().strip()

    def keyPressEvent(self, event: qt.QKeyEvent) -> None:
        if self.line_edit.hasFocus():
            if event.key() in (qt.Qt.Key.Key_Return, qt.Qt.Key.Key_Enter):
                self.on_edit_finished()
            elif event.key() == qt.Qt.Key.Key_Escape:
                self.cancel_edit()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def on_edit_finished(self) -> None:
        new_path: str = self.get_path()
        if not new_path:
            self.cancel_edit()
            return
        expanded: str = os.path.expanduser(new_path)
        if not os.path.isabs(expanded):
            expanded = os.path.abspath(
                os.path.join(self.current_path, expanded)
            )
        if os.path.isdir(expanded):
            self.current_path = expanded
            self.path_changed.emit(expanded)
            self.set_path(expanded)
            self.exit_edit_mode()
        else:
            qt.QTimer.singleShot(10, self.reset_error_style)

    def reset_error_style(self) -> None:
        self.set_path(self.current_path)
        self.exit_edit_mode()

    def exit_edit_mode(self) -> None:
        self.line_edit.setReadOnly(True)

    def cancel_edit(self) -> None:
        self.set_path(self.current_path)
        self.exit_edit_mode()

    def update_style(self) -> None:
        self.line_edit.update_style()


class StandardConsole(qt.QWidget, gui.templates.baseobject.BaseObject):
    # Dictionary mapping shell executable names to their command-line arguments.
    SHELL_ARGUMENTS: typing.Dict[str, str] = {
        "bash": "-c",
        "sh": "-c",
        "zsh": "-c",
        "powershell.exe": "-command",
        "cmd.exe": "/c",
    }

    def __init__(
        self,
        name: str = "StandardConsole",
        parent: typing.Optional[qt.QWidget] = None,
        main_form=None,
        cwd: typing.Optional[str] = None,
    ) -> None:
        qt.QWidget.__init__(self)
        gui.templates.baseobject.BaseObject.__init__(
            self,
            parent=parent,
            main_form=main_form,
            name=name,
            icon="icons/console/console.png",
        )
        self.cwd: str = os.getcwd()
        if cwd is not None:
            self.cwd = cwd
        self.shells: typing.Dict[str, str] = self._get_available_shells()
        self.current_shell: str = self.shells.get(
            "Bash", next(iter(self.shells.values()), "")
        )
        self.setup_ui()
        self.command_history: typing.List[str] = []
        self.history_index: int = -1
        self.current_worker: typing.Optional[ConsoleWorker] = None
        self.current_thread: typing.Optional[qt.QThread] = None
        self.__command_queue = queue.Queue()

    def _get_available_shells(self) -> typing.Dict[str, str]:
        """Detects and returns a dictionary of common shell executables."""
        shells: typing.Dict[str, str] = {}
        # Try to detect common shells on the user's system
        if sys.platform == "win32":
            # Add Git Bash as a primary option if found
            git_bash_path = os.path.join(
                os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                "Git",
                "bin",
                "bash.exe",
            )
            if os.path.exists(git_bash_path):
                shells["Bash (Git)"] = git_bash_path
            # Add PowerShell and Command Prompt
            shells["PowerShell"] = "powershell.exe"
            shells["Command Prompt"] = "cmd.exe"
        else:  # Unix-like systems
            # Add common Unix shells
            if os.path.exists("/bin/bash"):
                shells["Bash"] = "/bin/bash"
            if os.path.exists("/bin/zsh"):
                shells["Zsh"] = "/bin/zsh"
            if os.path.exists("/bin/sh"):
                shells["Sh"] = "/bin/sh"

        return shells

    def setup_ui(self) -> None:
        layout: qt.QVBoxLayout = qt.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Path Widget
        dir_layout: qt.QHBoxLayout = qt.QHBoxLayout()
        dir_layout.setContentsMargins(0, 0, 0, 0)
        dir_layout.setSpacing(0)
        self.directory_label = gui.templates.widgetgenerator.create_label(
            text=" Directory: ",
            transparent_background=True,
        )
        dir_layout.addWidget(self.directory_label)

        self.path_widget: EditablePathWidget = EditablePathWidget(
            self.cwd, parent=self
        )
        self.path_widget.path_changed.connect(self.on_path_changed)
        dir_layout.addWidget(self.path_widget)

        self.browse_button: gui.helpers.buttons.CustomPushButton = (
            gui.templates.widgetgenerator.create_pushbutton(
                parent=self,
                name="browse",
                tooltip="Select the current working directory",
                icon_name="icons/folder/open/folder.svg",
                click_func=self.browse_directory,
            )
        )
        dir_layout.addWidget(self.browse_button)
        layout.addLayout(dir_layout)

        # Shell Selection Widgets
        shell_layout = qt.QHBoxLayout()
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_label = gui.templates.widgetgenerator.create_label(
            text=" Shell: ", transparent_background=True
        )
        shell_layout.addWidget(shell_label)

        self.shell_dropdown = gui.templates.widgetgenerator.create_combobox(
            parent=self
        )
        sorted_shells = sorted(self.shells.keys())
        for name in sorted_shells:
            self.shell_dropdown.addItem(name)
        # Set the dropdown to the initially selected shell.
        if self.current_shell:
            try:
                initial_index = sorted_shells.index("Bash")
                self.shell_dropdown.setCurrentIndex(initial_index)
            except ValueError:
                # Fallback if "Bash" is not in the list
                self.shell_dropdown.setCurrentIndex(0)

        self.shell_dropdown.currentIndexChanged.connect(self._on_shell_changed)
        shell_layout.addWidget(self.shell_dropdown)
        self.shell_dropdown.setSizePolicy(
            qt.QSizePolicy.Policy.Preferred, qt.QSizePolicy.Policy.Expanding
        )

        self.add_shell_button: gui.helpers.buttons.CustomPushButton = (
            gui.templates.widgetgenerator.create_pushbutton(
                parent=self,
                name="add_shell",
                tooltip="Add a new custom shell executable path",
                icon_name="icons/console/console(add).png",
                click_func=self._add_custom_shell,
            )
        )
        shell_layout.addWidget(self.add_shell_button)
        layout.addLayout(shell_layout)

        # Console Output and Input
        self.console_output: gui.templates.textmanipulation.ConsoleDisplay = (
            gui.templates.textmanipulation.ConsoleDisplay(self.parent(), self)
        )
        self.console_output.setReadOnly(True)
        self.console_output.setLineWrapMode(
            qt.QTextBrowser.LineWrapMode.WidgetWidth
        )
        fixed_font = qt.QFontDatabase.systemFont(
            qt.QFontDatabase.SystemFont.FixedFont
        )
        self.console_output.setFont(fixed_font)
        layout.addWidget(self.console_output, stretch=1)

        input_layout: qt.QHBoxLayout = qt.QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)
        self.command_input: gui.templates.widgetgenerator.TextBox = (
            gui.templates.widgetgenerator.create_textbox(
                parent=self,
                name="StandardTextBox",
                h_size_policy=qt.QSizePolicy.Policy.Expanding,
                v_size_policy=qt.QSizePolicy.Policy.Expanding,
            )
        )
        self.command_input.setPlaceholderText(
            "Enter command (e.g., 'cd folder', 'ls', 'dir')"
        )
        self.command_input.returnPressed.connect(self.execute_command_from_gui)
        self.execute_button: gui.helpers.buttons.CustomPushButton = (
            gui.templates.widgetgenerator.create_pushbutton(
                parent=self,
                name="execute",
                tooltip="Execute the command that is entered in the textbox",
                icon_name="icons/gen/window_tab_move.svg",
                click_func=self.execute_command_from_gui,
            )
        )
        input_layout.addWidget(self.command_input)
        input_layout.addWidget(self.execute_button)
        layout.addLayout(input_layout)

        self.append_text(
            "Console ready with editable directory.\n", ColorTheme.output
        )
        self.append_text(f"Current directory: {self.cwd}\n", ColorTheme.path)
        self.append_text(
            f"Selected shell: {self.shell_dropdown.currentText()}\n",
            ColorTheme.info,
        )
        self.path_widget.line_edit.mousePressEvent = (
            lambda event: self.path_widget.enter_edit_mode()
        )
        self.path_widget.line_edit.keyPressEvent = self._path_key_handler
        self.update_style()

    def _on_shell_changed(self, index: int) -> None:
        """Slot to handle shell selection from the dropdown."""
        shell_name = self.shell_dropdown.currentText()
        self.current_shell = self.shells.get(shell_name, "")
        self.append_text(f"Shell changed to: {shell_name}\n", ColorTheme.info)

    def _add_custom_shell(self) -> None:
        """Opens a file dialog to allow the user to select a new shell executable."""
        shell_path, _ = qt.QFileDialog.getOpenFileName(
            self,
            "Select Shell Executable",
            "",
            "Executables (*.exe);;All Files (*)",
        )
        if shell_path:
            file_name = os.path.basename(shell_path)
            if file_name not in self.shells:
                self.shells[file_name] = shell_path
                self.shell_dropdown.addItem(file_name)
                self.shell_dropdown.setCurrentText(file_name)
                self.append_text(
                    f"Added and selected custom shell: {file_name}\n",
                    ColorTheme.info,
                )
            else:
                self.append_text(
                    f"Shell '{file_name}' already exists.\n", ColorTheme.warning
                )

    def _path_key_handler(self, event: qt.QKeyEvent) -> None:
        if event.key() == qt.Qt.Key.Key_F2:
            self.path_widget.enter_edit_mode()
        elif event.key() in (qt.Qt.Key.Key_Return, qt.Qt.Key.Key_Enter):
            self.path_widget.on_edit_finished()
        elif event.key() == qt.Qt.Key.Key_Escape:
            self.path_widget.cancel_edit()
        else:
            qt.QLineEdit.keyPressEvent(self.path_widget.line_edit, event)

    def append_text(
        self, text: str, color: typing.Optional[ColorTheme] = ColorTheme.output
    ) -> None:
        cursor: qt.QTextCursor = self.console_output.textCursor()
        cursor.movePosition(qt.QTextCursor.MoveOperation.End)
        fmt: qt.QTextCharFormat = qt.QTextCharFormat()
        if color is not None and color != ColorTheme.output:
            fmt.setForeground(qt.QColor(get_color(color)))
        if color in (ColorTheme.command, ColorTheme.warning, ColorTheme.error):
            fmt.setFontWeight(700)
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        vbar: qt.QScrollBar = self.console_output.verticalScrollBar()
        vbar.setValue(vbar.maximum())

    def on_path_changed(self, new_path: str) -> None:
        self.cwd = new_path
        try:
            os.chdir(new_path)
            self.append_text(
                f"Directory changed to:\n{self.cwd}\n", ColorTheme.path
            )
        except (OSError, RuntimeError) as e:
            self.append_text(
                f"Error entering directory: {str(e)}\n", ColorTheme.error
            )
            self.path_widget.set_path(self.cwd)

    def browse_directory(self) -> None:
        new_dir: str = qt.QFileDialog.getExistingDirectory(
            self, "Choose Directory", self.cwd
        )
        if new_dir:
            self.set_cwd(new_dir)

    def set_cwd(self, new_cwd: str) -> None:
        try:
            os.chdir(new_cwd)
            self.cwd = new_cwd
            self.path_widget.set_path(new_cwd)
            self.append_text(
                f"Directory changed to:\n{self.cwd}\n", ColorTheme.path
            )
        except (OSError, RuntimeError) as e:
            self.append_text(f"Error: {str(e)}\n", ColorTheme.error)

    def execute_commands(
        self, commands: typing.List[str], cwd: typing.Optional[str]
    ) -> None:
        first_command = commands[0]
        rest_of_commands = commands[1:]
        for c in rest_of_commands:
            self.__command_queue.put(c)
        if cwd is not None:
            self.set_cwd(cwd)
        self.__run_external_command(first_command)

    def execute_command_from_gui(self) -> None:
        command: str = self.command_input.text().strip()
        if not command:
            return
        self.command_input.clear()
        if command.lower().startswith("cd "):
            path: str = command[3:].strip()
            if not path:
                self.append_text("Usage: cd <directory>\n", ColorTheme.error)
                return
            path = os.path.expanduser(path)
            target: str = os.path.abspath(os.path.join(self.cwd, path))
            if os.path.isdir(target):
                self.set_cwd(target)
            else:
                self.append_text(
                    f"Directory not found: {target}\n", ColorTheme.error
                )
            return
        if command and (
            not self.command_history or self.command_history[-1] != command
        ):
            self.command_history.append(command)
        self.history_index = len(self.command_history)
        self.__run_external_command(command)

    def __run_external_command(self, command: str) -> None:
        self.append_text(f"\n> {command}\n", ColorTheme.command)
        self.cancel_current_command()
        self.current_thread = qt.QThread()
        # Get the shell's executable name to find its argument
        shell_exe = os.path.basename(self.current_shell).lower()
        shell_arg = self.SHELL_ARGUMENTS.get(shell_exe, "-c")

        self.current_worker = ConsoleWorker(
            command,
            cwd=self.cwd,
            shell=self.current_shell,
            shell_argument=shell_arg,
        )
        self.current_worker.moveToThread(self.current_thread)
        self.current_thread.started.connect(self.current_worker.execute)
        self.current_worker.output_received.connect(self.on_output_received)
        self.current_worker.command_finished.connect(self.on_command_finished)
        self.current_worker.suspected_interactive.connect(
            self.on_interactive_detected
        )
        self.current_thread.finished.connect(self.current_thread.deleteLater)
        self.current_worker.command_finished.connect(
            self.current_worker.deleteLater
        )
        self.current_thread.start()

    def on_output_received(self, text: str) -> None:
        self.append_text(text, ColorTheme.output)

    def on_interactive_detected(self) -> None:
        if self.current_worker and self.current_worker.process:
            try:
                self.current_worker.process.terminate()
                self.current_worker.process.wait(timeout=1)
            except (OSError, subprocess.TimeoutExpired):
                if self.current_worker.process:
                    self.current_worker.process.kill()
        self.append_text(
            "Aborted: Command appears to be interactive and requires a terminal.\n"
            "Stopped to keep the console responsive.\n",
            ColorTheme.warning,
        )

    @qt.pyqtSlot(int)
    def on_command_finished(self, return_code: int) -> None:
        self.append_text(
            f"\nCommand finished with return code: {return_code}\n",
            ColorTheme.info if return_code == 0 else ColorTheme.error,
        )

        if return_code == ProcessReturnCode.SUCCESS:
            if not self.__command_queue.empty():
                command = self.__command_queue.get()
                self.__run_external_command(command)
        else:
            try:
                while True:
                    self.__command_queue.get_nowait()
            except queue.Empty:
                pass

            self.append_text(f"Process returned an error\n", ColorTheme.error)

    def cancel_current_command(self) -> None:
        if self.current_worker and self.current_worker.process:
            try:
                self.current_worker.process.terminate()
                self.current_worker.process.wait(timeout=1)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    self.current_worker.process.kill()
                except OSError:
                    pass
        if self.current_thread:
            self.current_thread.quit()
            self.current_thread.wait()
        self.current_worker = None
        self.current_thread = None

    def keyPressEvent(self, event: qt.QKeyEvent) -> None:
        if event.key() == qt.Qt.Key.Key_Up:
            if self.command_history and self.history_index > 0:
                self.history_index -= 1
                self.command_input.setText(
                    self.command_history[self.history_index]
                )
            elif self.command_history and self.history_index == 0:
                self.command_input.setText(
                    self.command_history[self.history_index]
                )
        elif event.key() == qt.Qt.Key.Key_Down:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_input.setText(
                    self.command_history[self.history_index]
                )
            else:
                self.history_index = len(self.command_history)
                self.command_input.clear()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event: qt.QCloseEvent) -> None:
        self.cancel_current_command()
        event.accept()

    def set_focus(self) -> None:
        self.setFocus()

    def update_style(self) -> None:
        self.directory_label.update_style()
        self.path_widget.update_style()
        self.browse_button.update_style()
        self.command_input.update_style()
        self.execute_button.update_style()


def main() -> None:
    app: qt.QApplication = qt.QApplication(sys.argv)
    app.setStyle("Fusion")
    console: StandardConsole = StandardConsole()
    console.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
