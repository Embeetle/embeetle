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

import sys
import math
import time
import threading
import traceback
import pyte
import data
import iconfunctions
import gui.templates.baseobject
import gui.templates.basemenu
import gui.stylesheets.menu
import purefunctions
import os_checker
from qt import *

if os_checker.is_os("windows"):
    import winpty
else:
    import ptyprocess

PYTE_FOREGROUND_COLOR_MAP = {
    "black": QColor(Qt.GlobalColor.black),
    "red": QColor(Qt.GlobalColor.red),
    "green": QColor(Qt.GlobalColor.green),
    "brown": QColor(Qt.GlobalColor.yellow),
    "blue": QColor(Qt.GlobalColor.blue),
    "magenta": QColor(Qt.GlobalColor.magenta),
    "cyan": QColor(Qt.GlobalColor.cyan),
    "white": QColor(Qt.GlobalColor.lightGray),
    "default": QColor(Qt.GlobalColor.white),
    "brightblack": QColor(Qt.GlobalColor.darkGray),
    "brightred": QColor(Qt.GlobalColor.red),
    "brightgreen": QColor(Qt.GlobalColor.green),
    "brightbrown": QColor(Qt.GlobalColor.yellow),
    "brightblue": QColor(Qt.GlobalColor.blue),
    "brightmagenta": QColor(Qt.GlobalColor.magenta),
    "brightcyan": QColor(Qt.GlobalColor.cyan),
    "brightwhite": QColor(Qt.GlobalColor.white),
}
PYTE_BACKGROUND_COLOR_MAP = {
    "black": QColor(Qt.GlobalColor.black),
    "red": QColor(Qt.GlobalColor.red),
    "green": QColor(Qt.GlobalColor.green),
    "brown": QColor(Qt.GlobalColor.yellow),
    "blue": QColor(Qt.GlobalColor.blue),
    "magenta": QColor(Qt.GlobalColor.magenta),
    "cyan": QColor(Qt.GlobalColor.cyan),
    "white": QColor(Qt.GlobalColor.lightGray),
    "default": QColor(Qt.GlobalColor.black),
    "brightblack": QColor(Qt.GlobalColor.darkGray),
    "brightred": QColor(Qt.GlobalColor.red),
    "brightgreen": QColor(Qt.GlobalColor.green),
    "brightbrown": QColor(Qt.GlobalColor.yellow),
    "brightblue": QColor(Qt.GlobalColor.blue),
    "bfightmagenta": QColor(Qt.GlobalColor.magenta),
    "brightcyan": QColor(Qt.GlobalColor.cyan),
    "brightwhite": QColor(Qt.GlobalColor.white),
}


class CustomTextEdit(QPlainTextEdit):
    input_event = pyqtSignal(int, str, object)
    resize_event = pyqtSignal(int, int)
    paste_event = pyqtSignal(str)
    scroll_up_event = pyqtSignal(int)
    scroll_down_event = pyqtSignal(int)

    def __init__(self, *args, **kwargs) -> None:
        """"""
        super().__init__(*args, **kwargs)
        self.__cache_width = None
        self.__cache_height = None
        self.document().setDocumentMargin(0)
        self.document().rootFrame().frameFormat().setBottomMargin(0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.update_style()
        return

    def setFocus(self):
        """Overridden focus event."""
        # Execute the supeclass focus function
        super().setFocus()
        # Check indication
        parent = self.parent()
        parent_tab_widget = parent.parent().parent()
        parent.main_form.view.indicate_window(parent_tab_widget)

    def keyPressEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        key = event.key()
        text = event.text()
        self.input_event.emit(key, text, modifiers)

    #        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Overloaded mouse click event."""
        # Execute the superclass mouse click event
        super().mousePressEvent(event)
        # Set focus to the clicked editor
        self.setFocus()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            # Up
            self.scroll_up_event.emit(event.angleDelta().y())
        else:
            # Down
            self.scroll_down_event.emit(event.angleDelta().y())
        event.accept()

    def resizeEvent(self, event):
        w = self.viewport().size().width()
        h = self.viewport().size().height()
        font = self.document().defaultFont()
        font_metrics = QFontMetricsF(font)
        char_size = font_metrics.size(0, "X")
        width_in_chars = math.ceil(w / char_size.width())
        height_in_chars = math.floor(h / char_size.height())
        if (
            self.__cache_width != width_in_chars
            or self.__cache_height != height_in_chars
        ):
            self.__cache_width = width_in_chars
            self.__cache_height = height_in_chars
            self.resize_event.emit(width_in_chars, height_in_chars)
        return super().resizeEvent(event)

    def contextMenuEvent(self, event):
        # Show a context menu
        context_menu = gui.templates.basemenu.BaseMenu(parent=self)
        actions = {
            "copy": {
                "name": "Copy",
                "tooltip": "Copy",
                "icon": "icons/menu_edit/copy.svg",
                "function": self.copy,
            },
            "cut": {
                "name": "Cut",
                "tooltip": "Cut",
                "icon": "icons/menu_edit/cut.png",
                "function": self.cut,
            },
            "paste": {
                "name": "Paste",
                "tooltip": "Paste",
                "icon": "icons/menu_edit/paste.png",
                "function": self.paste,
            },
            "undo": {
                "name": "Undo",
                "tooltip": "Undo",
                "icon": "icons/menu_edit/undo.png",
                "function": self.undo,
            },
            "redo": {
                "name": "Redo",
                "tooltip": "Redo",
                "icon": "icons/menu_edit/redo.png",
                "function": self.redo,
            },
        }
        for k, v in actions.items():
            action = QAction(v["name"], self)
            action.setToolTip(v["tooltip"])
            action.setStatusTip(v["tooltip"])
            action.setIcon(iconfunctions.get_qicon(v["icon"]))
            if v["function"] is not None:
                action.triggered.connect(v["function"])
            action.setEnabled(True)
            context_menu.addAction(action)
        # Show menu
        cursor = QCursor.pos()
        context_menu.popup(cursor)
        # Accept event
        event.accept()

    def paste(self):
        paste_text = data.application.clipboard().text()
        self.paste_event.emit(paste_text)

    def update_style(self):
        self.setStyleSheet(f"""
QPlainTextEdit {{
    background-color: {PYTE_BACKGROUND_COLOR_MAP["default"].name()};
    color: {PYTE_FOREGROUND_COLOR_MAP["default"].name()};
    selection-background-color: {PYTE_FOREGROUND_COLOR_MAP["default"].name()};
    selection-color: {PYTE_BACKGROUND_COLOR_MAP["default"].name()};
    border: none;
    margin: 0px;
    spacing: 0px;
    padding: 0px;
}}

{gui.stylesheets.menu.get_general_stylesheet()}
        """)


class Terminal(QWidget, gui.templates.baseobject.BaseObject):
    pty_data_received = pyqtSignal(object)
    pty_add_to_buffer = pyqtSignal(object)

    current_working_directory = None

    def __init__(self, parent, main_form):
        QWidget.__init__(self, parent)
        gui.templates.baseobject.BaseObject.__init__(
            self,
            parent=parent,
            main_form=main_form,
            name="Terminal",
            icon="icons/console/terminal.png",
        )

        CONSOLE_WIDTH = 120
        CONSOLE_HEIGHT = 26

        self.screen = pyte.HistoryScreen(
            CONSOLE_WIDTH,
            CONSOLE_HEIGHT,
            history=1000,
            ratio=0.1,
        )
        self.stream = pyte.Stream(self.screen)

        if os_checker.is_os("windows"):
            self.pty_process = winpty.PtyProcess.spawn(
                "cmd",
                dimensions=(CONSOLE_HEIGHT, CONSOLE_WIDTH),
                backend=1,
            )

            self.pty_data_received.connect(self.__stdout_received)
            self.pty_add_to_buffer.connect(self.__send_buffer)
            # Reading
            self.__thread_pty_read = threading.Thread(
                target=self.__pty_read_loop_windows,
                args=[],
                daemon=True,
            )
            self.__thread_pty_read.start()
        else:
            self.pty_process = ptyprocess.PtyProcessUnicode.spawn(["/bin/bash"])

            self.pty_data_received.connect(self.__stdout_received)
            self.pty_add_to_buffer.connect(self.__send_buffer)

            # Reading
            self.__thread_pty_read = threading.Thread(
                target=self.__pty_read_loop_linux,
                args=[],
                daemon=True,
            )
            self.__thread_pty_read.start()

        # Create the console output widget
        self.output_widget = CustomTextEdit(self)
        self.output_widget.setOverwriteMode(True)
        self.output_widget.setFont(data.get_toplevel_font())
        self.output_widget.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.output_widget.input_event.connect(self.__input_event)
        self.output_widget.resize_event.connect(self.__resize_event)
        self.output_widget.paste_event.connect(self.__paste_event)
        self.output_widget.scroll_up_event.connect(self.__scroll_up_event)
        self.output_widget.scroll_down_event.connect(self.__scroll_down_event)

        # Add the widgets to a vertical layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.output_widget)

        self.update_style()

    def self_destruct(self):
        self.pty_process = None
        self.output_widget.setParent(None)
        self.output_widget = None
        self.__thread_pty_read = None

    def __pty_read_loop_windows(self):
        while self.pty_process.isalive():
            _data = self.pty_process.read()
            if _data is not None and _data != b"":
                self.pty_add_to_buffer.emit(_data)
            else:
                time.sleep(0.001)

    def __pty_read_loop_linux(self):
        while self.pty_process.isalive():
            _data = self.pty_process.read().encode("utf-8")
            if _data is not None and _data != b"":
                self.pty_add_to_buffer.emit(_data)
            else:
                time.sleep(0.001)

    def __send_buffer(self, new_data):
        #        joined_buffer = b''.join(self.buffer).replace(b'\r', b'')
        if len(new_data) > 0:
            if isinstance(new_data, bytes):
                joined_buffer = new_data
            elif isinstance(new_data, str):
                joined_buffer = new_data
                joined_buffer.encode("utf-8")
            else:
                raise Exception("Unknown type: '{}'".format(new_data.__class__))
        else:
            joined_buffer = b""
        self.pty_data_received.emit(joined_buffer)
        self.buffer = []

    @pyqtSlot()
    def __update_display(self):
        # Timing initialization
        time_start = time.perf_counter()

        # Cursor
        cursor = self.output_widget.textCursor()
        cursor.setPosition(0)

        # Clear all text
        self.output_widget.clear()

        # Format the text
        reverse = False
        bg = "default"
        fg = "default"
        new_formatting = QTextCharFormat()
        new_formatting.setBackground(PYTE_BACKGROUND_COLOR_MAP[bg])
        new_formatting.setForeground(PYTE_FOREGROUND_COLOR_MAP[fg])
        cursor.setCharFormat(new_formatting)
        current_char_list = []
        entire_height_in_lines = self.screen.lines
        current_visible_buffer = []
        for y in range(self.screen.lines):
            line = self.screen.buffer[y]
            for x in range(self.screen.columns):
                character = line[x]
                if (
                    character.bg != bg
                    or character.fg != fg
                    or character.reverse != reverse
                ):
                    text = "".join(current_char_list)
                    cursor.insertText(text)
                    current_visible_buffer.append(text)
                    current_char_list = []
                    reverse = character.reverse
                    bg = character.bg
                    fg = character.fg
                    new_formatting = QTextCharFormat()
                    # Check reverse colors
                    if reverse:
                        bg_color_map = PYTE_FOREGROUND_COLOR_MAP
                        fg_color_map = PYTE_BACKGROUND_COLOR_MAP
                    else:
                        bg_color_map = PYTE_BACKGROUND_COLOR_MAP
                        fg_color_map = PYTE_FOREGROUND_COLOR_MAP
                    # Background
                    if bg in bg_color_map.keys():
                        new_formatting.setBackground(bg_color_map[bg])
                    else:
                        new_color = QColor("#{}".format(bg))
                        new_formatting.setBackground(new_color)
                    # Foreground
                    if fg in fg_color_map.keys():
                        new_formatting.setForeground(fg_color_map[fg])
                    else:
                        new_color = QColor("#{}".format(fg))
                        new_formatting.setForeground(new_color)

                    cursor.setCharFormat(new_formatting)
                current_char_list.append(character.data)
            current_char_list.append("\n")
        else:
            if len(current_char_list) > 0:
                text = "".join(current_char_list)
                cursor.insertText(text)
                current_visible_buffer.append(text)

        self.output_widget.setTextCursor(cursor)

        # Position the cursor
        left = cursor.columnNumber()
        cursor.setPosition(0)
        cursor.movePosition(
            QTextCursor.MoveOperation.Down,
            QTextCursor.MoveMode.MoveAnchor,
            self.screen.cursor.y,
        )
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.MoveAnchor,
            self.screen.cursor.x,
        )

        # Reset scrolling to top
        self.output_widget.verticalScrollBar().setValue(0)

        # Activate cursor
        self.output_widget.setTextCursor(cursor)
        self.output_widget.ensureCursorVisible()

        # Parse directory if applicable
        for text in current_visible_buffer:
            for line in text.split("\n"):
                try:
                    stripped_line = line.strip()
                    if stripped_line.endswith(">"):
                        # Windows Console
                        if stripped_line.startswith("PS "):
                            stripped_line = stripped_line[:3]
                        directory = stripped_line.replace(">", "")
                        if os.path.isdir(directory):
                            self.current_working_directory = directory
                    elif line.strip().endswith("$"):
                        # Bash
                        user, directory = stripped_line[:-1].split(":")
                        directory = directory.strip()
                        if os.path.isdir(directory):
                            self.current_working_directory = directory
                except:
                    traceback.print_exc()

        # Loop timing
        end_count = time.perf_counter() - time_start

    @pyqtSlot(bytes)
    def __stdout_received(self, raw_text):
        if isinstance(raw_text, bytes):
            self.stream.feed(raw_text.decode("utf-8"))
        else:
            self.stream.feed(raw_text)
        # Display output and error streams in console
        self.__update_display()

    def __input_event(self, key, text, modifiers):
        #        print(modifiers, key, text, bytes(text, "utf-8"))

        update = False
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_Up:
                #                self.screen.cursor_up()
                self.screen.prev_page()
                update = True
            elif key == Qt.Key.Key_Down:
                self.screen.next_page()
                update = True

        else:
            if key == Qt.Key.Key_Up:
                text = "\u001b[A"
                update = True
            elif key == Qt.Key.Key_Down:
                text = "\u001b[B"
                update = True
            elif key == Qt.Key.Key_Left:
                text = "\u001b[D"
                update = True
            elif key == Qt.Key.Key_Right:
                text = "\u001b[C"
                update = True
            elif key == Qt.Key.Key_PageUp:
                self.screen.prev_page()
                update = True
            elif key == Qt.Key.Key_PageDown:
                self.screen.next_page()
                update = True
        if update:
            self.__update_display()

        try:
            self.pty_process.write(text)
        except Exception as ex:
            self.main_form.display.display_error(
                "Terminal has probably already been closed,"
                + "the process returned: '{}'".format(ex)
            )

    def __resize_event(self, width, height):
        try:
            # print("resize:", width, "x", height)
            if os_checker.is_os("windows"):
                width -= 1
            else:
                width -= 1
                height -= 1
            if width < 0:
                width = 0
            if height < 0:
                height = 0
            self.screen.resize(height, width)
            self.__update_display()
            self.pty_process.setwinsize(height, width)
        except:
            pass

    def __paste_event(self, paste_text):
        self.pty_process.write(paste_text)
        self.__update_display()
        self.output_widget.setFocus()

    def __scroll_up_event(self, value):
        value = int(value / 120)
        for i in range(value):
            self.screen.prev_page()
        self.__update_display()

    def __scroll_down_event(self, value):
        value = int(abs(value / 120))
        for i in range(value):
            self.screen.next_page()
        self.__update_display()

    def execute_command(self, command: str):
        self.pty_process.write(command + "\r\n")

    def get_cwd(self) -> str:
        return self.current_working_directory

    def set_cwd(self, directory: str) -> None:
        self.execute_command(f"cd {directory}")

    def setFocus(self):
        """Overridden focus event."""
        self.output_widget.setFocus()

    """
    General
    """

    def update_style(self):
        self.setStyleSheet(f"""
QWidget {{
    background: transparent;
    border: none;
    margin: 0px;
    spacing: 0px;
    padding: 0px;
}}
        """)
        self.output_widget.update_style()


def test():
    app = QApplication(sys.argv)
    console = Terminal(None, None)
    console.resize(640, 480)
    console.show()
    sys.exit(app.exec())
