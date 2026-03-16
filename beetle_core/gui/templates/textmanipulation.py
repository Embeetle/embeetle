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
import pprint

import data
import qt


class ConsoleDisplay(qt.QTextBrowser):
    link_clicked_signal = qt.pyqtSignal(str)
    link_and_pos_clicked_signal = qt.pyqtSignal(str, int, int)

    def __init__(
        self, parent, parent_window, max_block_cnt: int = 1000
    ) -> None:
        """"""
        super().__init__(parent)
        self.parent_window = parent_window
        self.setReadOnly(True)
        self.setLineWrapMode(qt.QTextEdit.LineWrapMode.NoWrap)
        if max_block_cnt > 0:
            self.document().setMaximumBlockCount(max_block_cnt)
        self.setOpenExternalLinks(False)
        return

    def __focus_parent_window(self) -> None:
        if self.parent_window is not None:
            if hasattr(self.parent_window, "set_focus"):
                self.parent_window.set_focus()
            elif hasattr(self.parent_window, "setFocus"):
                self.parent_window.setFocus()
            else:
                raise Exception("Unknown focus method!")

    def mousePressEvent(self, event: qt.QMouseEvent, *args) -> None:
        """Overload the mousePressEvent to set the focus on the parent window
        before calling the super().mousePressEvent() method."""
        self.__focus_parent_window()
        return super().mousePressEvent(event, *args)

    def mouseReleaseEvent(self, event: qt.QMouseEvent, *args) -> None:
        """Overload the mouseReleaseEvent to check if the clicked word is an
        anchor (link)."""
        # Get the cursor position at the click
        cursor = self.cursorForPosition(event.pos())
        cursor.select(qt.QTextCursor.SelectionType.WordUnderCursor)

        # Check if the clicked word is an anchor (link)
        anchor: str = self.anchorAt(event.pos())
        if anchor:
            # Emit a custom signal or call a function to handle the link click
            self.link_clicked_signal.emit(anchor)
            # Emit another custom signal with the x- and y-positions attached as well. This can be
            # used later on to extract the `QTextFrame()` in which the click happened:
            #     pos = qt.QPoint(x, y)
            #     cursor = console_display.cursorForPosition(pos)
            #     frame = cursor.currentFrame()
            self.link_and_pos_clicked_signal.emit(
                anchor,
                int(event.pos().x()),
                int(event.pos().y()),
            )
            self.__focus_parent_window()
            return

        self.__focus_parent_window()
        super().mouseReleaseEvent(event, *args)
        return

    def add_text(self, *messages, html=False) -> None:
        """Add text to the QTextBrowser."""
        for m in messages:
            if not isinstance(m, str):
                m = pprint.pformat(m) + "\n"
            # Remove back-slashes
            m = m.replace("\\\\", "/")
            # Move cursor to end
            self.moveCursor(qt.QTextCursor.MoveOperation.End)
            if html:
                self.insertHtml(m)
            else:
                self.insertPlainText(m)
            # Move cursor to end
            self.moveCursor(qt.QTextCursor.MoveOperation.End)
        return


class InputEditorState(enum.Enum):
    Enabled = enum.auto()
    Disabled = enum.auto()
    DisabledWithStopAnswerBtn = enum.auto()


class StopAnsBtnState(enum.Enum):
    Normal = enum.auto()
    Hovered = enum.auto()
    Clicked = enum.auto()


class InputEditor(qt.QTextBrowser):
    submit_signal = qt.pyqtSignal(str)
    stop_answer_generation_signal = qt.pyqtSignal()

    def __init__(self, parent, parent_window) -> None:
        """"""
        super().__init__(parent)
        self.parent_window = parent_window
        self.setReadOnly(False)
        self.document().setMaximumBlockCount(1000)
        self.setOpenExternalLinks(False)
        self.setOpenLinks(False)
        self.anchorClicked.connect(self.handle_link_clicked)

        self.__state = InputEditorState.Enabled
        self.__stop_ans_btn_state = StopAnsBtnState.Normal
        self.__stop_ans_btn_rect = qt.QRect(0, 0, 0, 0)
        self.switch_state(newstate=InputEditorState.Enabled)
        return

    def switch_state(self, newstate: InputEditorState) -> None:
        """Switch to the required state, update the background color and draw
        the button if switching to `DisabledWithStopAnswerBtn` state."""
        self.clear()
        self.__state = newstate
        if self.__state == InputEditorState.Enabled:
            self.setEnabled(True)
            self.setReadOnly(False)
        elif self.__state == InputEditorState.Disabled:
            self.setEnabled(True)
            self.setReadOnly(True)
        elif self.__state == InputEditorState.DisabledWithStopAnswerBtn:
            self.setEnabled(True)
            self.setReadOnly(True)
            self.__stop_ans_btn_state = StopAnsBtnState.Normal
        else:
            raise RuntimeError(f"switch_state({self.__state}) not recognized!")
        self.update_style()
        return

    def update_style(self, *args, **kwargs) -> None:
        """Update the background color and draw the button again if in
        `DisabledWithStopAnswerBtn` state."""
        if self.__state == InputEditorState.Enabled:
            self.setStyleSheet(
                f"QTextBrowser{{background-color:{data.theme['fonts']['default']['background']};}}"
            )
        elif self.__state == InputEditorState.Disabled:
            self.setStyleSheet(
                f"QTextBrowser{{background-color:{data.theme['fonts']['disabled']['background']};}}"
            )
        elif self.__state == InputEditorState.DisabledWithStopAnswerBtn:
            self.setStyleSheet(
                f"QTextBrowser{{background-color:{data.theme['fonts']['disabled']['background']};}}"
            )
            self.__draw_button()
        else:
            raise RuntimeError(f"switch_state({self.__state}) not recognized!")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        return

    def keyPressEvent(self, event: qt.QKeyEvent, *args) -> None:
        """"""
        if (
            event.key() == qt.Qt.Key.Key_Return
            or event.key() == qt.Qt.Key.Key_Enter
        ):
            if not (event.modifiers() & qt.Qt.KeyboardModifier.ShiftModifier):
                self.submit_signal.emit(self.toPlainText())
                event.ignore()
                return
        return super().keyPressEvent(event)

    def handle_link_clicked(self, url: qt.QUrl):
        """"""
        if not url.toString() == "stop_answer_generation":
            return
        if not self.__state == InputEditorState.DisabledWithStopAnswerBtn:
            print(
                f"ERROR: handle_link_clicked() invoked while state is '{self.__state}'"
            )
            return
        if self.__stop_ans_btn_state == StopAnsBtnState.Clicked:
            # Already clicked. Ignore a double click.
            return
        # At this point we know that the input editor is in the correct state. It shows a button
        # that is either in `StopAnsBtnState.Normal` or `StopAnsBtnState.Hovered` state (most likely
        # the hover state).

        # $ Fire the Stop Signal
        self.stop_answer_generation_signal.emit()

        # $ Show Button Click Animation
        self.__stop_ans_btn_state = StopAnsBtnState.Clicked
        self.__draw_button()
        self.viewport().setCursor(qt.Qt.CursorShape.PointingHandCursor)

        def __veer_back(*args, **kwargs) -> None:
            """New policy: Remove the button entirely"""
            if not self.__state == InputEditorState.DisabledWithStopAnswerBtn:
                # State changed in the meantime
                return
            self.__stop_ans_btn_state = StopAnsBtnState.Normal
            self.switch_state(newstate=InputEditorState.Disabled)
            return

        qt.QTimer.singleShot(300, __veer_back)
        return

    def mouseMoveEvent(self, event: qt.QMouseEvent) -> None:
        """Track mouse movement to check if it's hovering over the button."""
        # $ `InputEditorState.Enabled` or `InputEditorState.Disabled`
        if self.__state != InputEditorState.DisabledWithStopAnswerBtn:
            self.viewport().setCursor(qt.Qt.CursorShape.IBeamCursor)
            return super().mouseMoveEvent(event)

        # $ `InputEditorState.DisabledWithStopAnswerBtn`
        # OPTION 1: Mouse on top
        if self.__stop_ans_btn_rect.contains(event.pos()):
            if self.__stop_ans_btn_state == StopAnsBtnState.Hovered:
                # OK
                return super().mouseMoveEvent(event)
            if self.__stop_ans_btn_state == StopAnsBtnState.Clicked:
                # Don't intervene with click animation
                return super().mouseMoveEvent(event)
            if self.__stop_ans_btn_state == StopAnsBtnState.Normal:
                # Switch to hover
                self.viewport().setCursor(qt.Qt.CursorShape.PointingHandCursor)
                self.__stop_ans_btn_state = StopAnsBtnState.Hovered
                self.__draw_button()
                return super().mouseMoveEvent(event)
            raise RuntimeError(f"State not found: {self.__stop_ans_btn_state}")

        # OPTION 2: Mouse not on top
        if self.__stop_ans_btn_state == StopAnsBtnState.Hovered:
            # Switch to normal
            self.viewport().setCursor(qt.Qt.CursorShape.ArrowCursor)
            self.__stop_ans_btn_state = StopAnsBtnState.Normal
            self.__draw_button()
            return super().mouseMoveEvent(event)
        if self.__stop_ans_btn_state == StopAnsBtnState.Clicked:
            # Don't intervene with click animation
            return super().mouseMoveEvent(event)
        if self.__stop_ans_btn_state == StopAnsBtnState.Normal:
            # OK
            pass
        return super().mouseMoveEvent(event)

    def __draw_button(self, *args, **kwargs) -> None:
        """"""
        if self.__stop_ans_btn_state == StopAnsBtnState.Clicked:
            background_color = data.theme["button_checked"]
        elif self.__stop_ans_btn_state == StopAnsBtnState.Hovered:
            background_color = data.theme["button_unchecked_hover"]
        else:
            background_color = data.theme["button_unchecked"]

        # Define the button size and location
        w = data.get_general_font_width()
        h = data.get_general_font_height()
        button_width = (w * 22) + 10
        button_height = h + 10

        if self.__stop_ans_btn_rect is None:
            self.__stop_ans_btn_rect = qt.QRect(
                5, 5, button_width, button_height
            )
        else:
            self.__stop_ans_btn_rect.setWidth(button_width)
            self.__stop_ans_btn_rect.setHeight(button_height)

        html_content = f"""
            <style>
                .custom-btn {{
                    background-color : {background_color};
                    border-color     : {data.theme["button_border"]};
                    border-width     : 1px;
                    border-style     : solid;
                    border-radius    : 0px;
                    font-family      : {data.get_global_font_family()};
                    font-size        : {data.get_general_font_pointsize()}pt;
                    color            : {data.theme['fonts']['default']['color']};
                    margin           : 0px;
                    text-align       : left;
                    white-space      : nowrap;
                    padding          : 5px 10px;
                }}
            </style>
            <a href='stop_answer_generation' style='text-decoration:none;'>
                <table class='custom-btn' cellpadding="5" cellspacing="0" align="left">
                    <tr>
                        <td>Stop Answer Generation</td>
                    </tr>
                </table>
            </a>
        """
        self.clear()
        self.setHtml(html_content)
        return
