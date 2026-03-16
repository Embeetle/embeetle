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
import data
import purefunctions
import iconfunctions
import os_checker
import gui.helpers.popupbubble
import gui.stylesheets.button
import gui.stylesheets.checkbox
import gui.stylesheets.button as _btn_style_


class RichTextPushButton(qt.QPushButton):
    click_sig = qt.pyqtSignal(qt.QMouseEvent)

    def __init__(
        self,
        parent: Optional[qt.QWidget] = None,
        text: Optional[str] = None,
    ) -> None:
        """"""
        if parent is not None:
            super().__init__(parent)
        else:
            super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        # NEW APPROACH
        # ============
        # Create a special QLabel() and add it to this QPushButton().
        # Use a layout to center it vertically.
        self.__lyt = qt.QVBoxLayout()
        self.__lyt.setContentsMargins(0, 0, 0, 0)
        self.__lyt.setSpacing(0)
        self.setLayout(self.__lyt)
        self.__lbl = ClickableLbl(self)
        if text is not None:
            self.__lbl.setText(text)
        # Connect to the standard 'mouseReleaseEvent()' method, which gets over-
        # ridden in item_widget.py:
        self.__lbl.click_sig.connect(self.mouseReleaseEvent)
        # Provide a publicly accessible signal for those cases where this widget
        # is used independently:
        self.__lbl.click_sig.connect(self.click_sig)
        self.__lbl.setTextFormat(qt.Qt.TextFormat.RichText)
        self.__lbl.setFont(data.get_general_font())
        self.__lbl.setContentsMargins(0, 0, 0, 0)
        self.__lyt.addWidget(self.__lbl)
        return

        # # OLD APPROACH
        # # ============
        # # Create a special QLabel() and add it to this QPushButton().
        # # It should be added without first creating a layout, such
        # # that the move() method can be invoked on the label. The move
        # # is needed, because richt-text-labels have too much spacing
        # # at the top.
        # self.__lbl = ClickableLbl(self)
        # if text is not None:
        #     self.__lbl.setText(text)
        # self.__lbl.click_sig.connect(self.mouseReleaseEvent)
        # self.__lbl.setTextFormat(qt.Qt.TextFormat.RichText)
        # self.__lbl.setFont(data.get_general_font())
        # self.__lbl.setContentsMargins(0, 0, 0, 0)
        # self.__lbl.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        # self.__lbl.move(0, -3)
        # return

    def setStyleSheet(self, stylesheet: str) -> None:
        """Apply given stylesheet on oneself and on self.__lbl."""
        super().setStyleSheet(stylesheet)
        self.__lbl.setStyleSheet(stylesheet.replace("QPushButton", "QLabel"))
        return

    def setText(self, text: str) -> None:
        text = text.replace("\n", "<br>")
        self.__lbl.setText(text)
        self.updateGeometry()
        return

    def sizeHint(self) -> qt.QSize:
        s: qt.QSize = qt.QPushButton.sizeHint(self)
        w: qt.QSize = self.__lbl.sizeHint()
        s.setWidth(w.width())
        s.setHeight(w.height())
        return s


class ClickableLbl(qt.QLabel):
    click_sig = qt.pyqtSignal(qt.QMouseEvent)

    def __init__(self, parent: Optional[qt.QWidget]) -> None:
        super().__init__(parent)
        self.setOpenExternalLinks(False)
        # Only fire a signal if the user clicks the link in the label
        self.linkActivated.connect(self.__fire_signal)
        return

    def __fire_signal(self, *args):
        """Create a fake mouse event and pass it to the emitted signal.

        Note: the actual link text that the user clicked on is inside the *args parameter. We don't
        need it for now.
        """
        # * ----------------[ QT6 ]---------------- *#
        # In Qt6 the second argument should be a QPointF().
        event = qt.QMouseEvent(
            qt.QEvent.Type.MouseButtonPress,
            qt.QPointF(qt.QCursor.pos()),
            qt.Qt.MouseButton.LeftButton,
            qt.Qt.MouseButton.LeftButton,
            qt.Qt.KeyboardModifier.NoModifier,
        )
        self.click_sig.emit(event)
        return

    # @qt.pyqtSlot(qt.QMouseEvent)
    # def mouseReleaseEvent(self, event:qt.QMouseEvent) -> None:
    #     # super().mouseReleaseEvent(event)
    #     event.accept()
    #     print('CLICKED!!!')
    #     self.click_sig.emit(event)
    #     return


class TabButton(qt.QPushButton):
    def __init__(
        self,
        name,
        selected_off_image,
        selected_on_image,
        selected_hover_image,
        selected_disabled_image,
        selected_focus_image,
        notselected_off_image,
        notselected_on_image,
        notselected_hover_image,
        notselected_disabled_image,
        notselected_focus_image,
        function,
        size,
        parent=None,
        background_transparent=False,
        border=False,
    ):
        super().__init__(parent)
        self.name = name
        self.__selected = False
        self.clicked.connect(function)
        self.background_transparent = background_transparent
        self.border = border
        self.update_style(
            selected_off_image,
            selected_on_image,
            selected_hover_image,
            selected_disabled_image,
            selected_focus_image,
            notselected_off_image,
            notselected_on_image,
            notselected_hover_image,
            notselected_disabled_image,
            notselected_focus_image,
            size,
        )
        self.set_selected(False)

    def set_selected(self, selected):
        if selected == self.__selected:
            return
        self.__selected = selected
        self.setProperty("active", selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.repaint()

    def update_style(
        self,
        selected_off_image,
        selected_on_image,
        selected_hover_image,
        selected_disabled_image,
        selected_focus_image,
        notselected_off_image,
        notselected_on_image,
        notselected_hover_image,
        notselected_disabled_image,
        notselected_focus_image,
        size,
    ):
        self.selected_off_image = selected_off_image
        self.selected_on_image = selected_on_image
        self.selected_hover_image = selected_hover_image
        self.selected_disabled_image = selected_disabled_image
        self.selected_focus_image = selected_focus_image
        self.notselected_off_image = notselected_off_image
        self.notselected_on_image = notselected_on_image
        self.notselected_hover_image = notselected_hover_image
        self.notselected_disabled_image = notselected_disabled_image
        self.notselected_focus_image = notselected_focus_image
        self.setStyleSheet(
            gui.stylesheets.button.get_tab_btn_stylesheet(
                icon=self.notselected_off_image,
                icon_hover=self.notselected_hover_image,
                icon_pressed=self.notselected_on_image,
                icon_focused=self.notselected_focus_image,
                icon_active=self.selected_off_image,
                icon_active_hover=self.selected_hover_image,
                icon_active_pressed=self.selected_on_image,
                icon_active_focused=self.selected_focus_image,
                icon_disabled=self.selected_disabled_image,
                border=self.border,
            )
        )
        self.setFixedSize(size)


class PictureButton(qt.QPushButton):
    def __init__(
        self,
        name=None,
        off_image=None,
        on_image=None,
        hover_image=None,
        checked_image=None,
        focus_image=None,
        disabled_image=None,
        function=None,
        size=None,
        parent=None,
        border=False,
    ):
        super().__init__(parent)
        self.setObjectName(name)
        self.name = name
        self.off_image = off_image
        self.on_image = on_image
        self.hover_image = hover_image
        self.checked_image = checked_image
        self.focus_image = focus_image
        self.disabled_image = disabled_image
        self.border = border
        if size is None:
            button_size = (
                data.get_general_icon_pixelsize(),
                data.get_general_icon_pixelsize(),
            )
        self.button_size = size
        if callable(function):
            self.clicked.connect(function)
        return

    def set_size(self, width: int, height: int) -> None:
        self.button_size = (width, height)

    def set_image(self, _type, new_image):
        if _type == "off":
            self.off_image = new_image
        elif _type == "on":
            self.on_image = new_image
        elif _type == "hover":
            self.hover_image = new_image
        elif _type == "checked":
            self.checked_image = new_image
        elif _type == "focus":
            self.focus_image = new_image
        elif _type == "disabled":
            self.disabled_image = new_image

    def get_stylesheet(self) -> str:
        style_sheet = _btn_style_.get_picturebutton(
            name=self.name,
            icon_path_off=self.off_image,
            icon_path_on=self.on_image,
            icon_path_hover=self.hover_image,
            icon_path_checked=self.checked_image,
            icon_path_focused=self.focus_image,
            icon_path_disabled=self.disabled_image,
            size=self.button_size,
            border=self.border,
            transparent_background=True,
        )
        return style_sheet


class PushButtonBase(qt.QPushButton):
    name = None
    scale_factor = 1.0
    enabled = None
    function = None
    enter_function = None
    leave_function = None
    # Signals
    right_clicked = qt.pyqtSignal()
    text_changed = qt.pyqtSignal(str)

    def set_click_function(self, func):
        if self.function is not None:
            try:
                self.clicked.disconnect()
            except TypeError as e:
                purefunctions.printc(
                    "ERROR: Could not disconnect clicked signal",
                    color="error",
                )
            self.function = None

        def actual_func(state):
            func()

        self.clicked.connect(actual_func)
        self.function = func

    def set_enter_function(self, func):
        self.enter_function = func

    def set_leave_function(self, func):
        self.leave_function = func

    def enable(self):
        self.enabled = True
        self.setEnabled(True)

    def disable(self):
        self.enabled = False
        self.setEnabled(False)

    def keyPressEvent(self, e):
        super().keyReleaseEvent(e)
        if e.key() == qt.Qt.Key.Key_Enter or e.key() == qt.Qt.Key.Key_Return:
            self.animateClick()

    #            self.clicked.emit()

    def mousePressEvent(self, event):
        if event.button() == qt.Qt.MouseButton.RightButton:
            self.right_clicked.emit()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        event.ignore()

    def enterEvent(self, e):
        super().enterEvent(e)
        if self.enabled == False:
            return
        # Execute the additional enter function
        if self.enter_function is not None:
            self.enter_function()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        if self.enabled == False:
            return
        # Execute the additional leave function
        if self.leave_function is not None:
            self.leave_function()

    def setText(self, e):
        super().setText(e)
        self.text_changed.emit(self.text())

    def update_style(self, new_size):
        self.setIconSize(
            qt.create_qsize(
                new_size[0] - int(new_size[0] * 8 / 42),
                new_size[1] - int(new_size[1] * 8 / 42),
            )
        )
        self.setFixedWidth(int(new_size[0]))
        self.setFixedHeight(int(new_size[1]))
        self.setFont(data.get_general_font())


class CustomPushButton(PushButtonBase):
    def __init__(
        self,
        parent=None,
        icon_path=None,
        icon=None,
        icon_size=None,
        align_text=None,
        padding="2px",
        text=None,
        bold=False,
        checkable=False,
        style="standard",
        popup_bubble_parent=None,
        tooltip=None,
        statustip=None,
        no_border=False,
        disabled=False,
    ):
        """ """
        super().__init__(parent)
        self.__custom_icon_size: Optional[qt.QSize] = None
        self.__custom_font_size_factor: Optional[int] = None
        if icon_size is None:
            icon_size = (
                data.get_general_icon_pixelsize(),
                data.get_general_icon_pixelsize(),
            )

        # Store attributes
        self.style = style
        self.bold = bold
        self.icon_scale = 1
        self.no_border = no_border
        # Text
        if text is not None:
            self.setText(text)
        # Icon
        self.__icon_path = icon_path
        if icon_path is not None and icon is not None:
            raise Exception(
                "[CustomPushButton] Cannot have both 'icon_path' and"
                "'icon' parameters set, only one!"
            )
        elif icon_path is not None:
            self.reset_icon()
        elif icon is not None:
            self.setIcon(icon)
        self.update_style(icon_size)
        # Check state
        self.setCheckable(checkable)
        # Tooltip
        if tooltip:
            self.setToolTip(tooltip)
        if statustip:
            self.setStatusTip(statustip)
        # Popup bubble
        self.popup_bubble = None
        if popup_bubble_parent is not None:
            self.popup_bubble = gui.helpers.popupbubble.PopupBubble(
                parent=popup_bubble_parent,
                corner="bottom-right",
            )
            self.popup_bubble.hide()
            self.__update_popup_bubble_position()
            self.installEventFilter(self)
        # Disabled
        if disabled:
            self.disable()
        else:
            self.enable()
        return

    def eventFilter(self, object, event):
        if event.type() == qt.QEvent.Type.Move:
            self.__update_popup_bubble_position()

        return super().eventFilter(object, event)

    def __update_popup_bubble_position(self):
        if os_checker.is_os("windows"):
            global_pos = self.mapToGlobal(qt.create_qpoint(0, 0))
        else:
            global_pos = self.mapToGlobal(qt.create_qpoint(0, 0))
        offset_left = int(self.width() / 2)
        offset_top = int(self.height() / 2)
        actual_pos = global_pos + qt.create_qpoint(offset_left, offset_top)
        new_pos = self.popup_bubble.parent().mapFromGlobal(actual_pos)
        self.popup_bubble.reposition(new_pos)
        return new_pos

    def popup_show(self, text: str) -> None:
        """"""
        if self.popup_bubble is None:
            raise Exception("Button doesn't have a popup bubble set!")
        new_pos = self.__update_popup_bubble_position()
        self.popup_bubble.popup(new_pos, text)
        return

    def popup_hide(self) -> None:
        """"""
        if self.popup_bubble is None:
            raise Exception("Button doesn't have a popup bubble set!")
        self.popup_bubble.hide()
        return

    def set_custom_icon_size(self, new_size: qt.QSize) -> None:
        self.__custom_icon_size = new_size
        self.update_style()

    def set_font_size_factor(self, new_size: int) -> None:
        self.__custom_font_size_factor = new_size
        self.update_style()

    def update_style(
        self, new_size: Optional[Union[tuple[int, int], qt.QSize]] = None
    ) -> None:
        """"""
        if new_size is not None:
            if isinstance(new_size, tuple):
                width, height = new_size
            elif isinstance(new_size, qt.QSize):
                width = new_size.width()
                height = new_size.height()
            else:
                raise Exception(
                    f"[CustomPushButton] Unknown size type: {new_size}"
                )
            self.setIconSize(
                qt.create_qsize(
                    width * self.icon_scale, height * self.icon_scale
                )
            )
            factor = 1.2
            if (self.text() is None) or (self.text() == ""):
                # Only set a fixed width on the button if there is no text
                self.setFixedWidth(int(width * factor))
            self.setFixedHeight(int(height * factor))

        # Font
        self.__resize_font()

        # Icon
        self.reset_icon()

        # Custom icon size
        if self.__custom_icon_size is not None:
            self.setIconSize(self.__custom_icon_size)

        # Update stylesheet
        if self.style == "tree-widget":
            stylesheet = gui.stylesheets.button.get_simple_toggle_stylesheet(
                style=self.style,
                no_border=self.no_border,
                font_size_factor=self.__custom_font_size_factor,
            )
        elif self.style != "standard":
            stylesheet = gui.stylesheets.button.get_simple_toggle_stylesheet(
                style=self.style,
                no_border=self.no_border,
                font_size_factor=self.__custom_font_size_factor,
            )
        else:
            stylesheet = gui.stylesheets.button.get_simple_toggle_stylesheet(
                no_border=self.no_border,
                font_size_factor=self.__custom_font_size_factor,
            )
        self.setStyleSheet(stylesheet)
        return

    def reset_icon(self):
        if self.__icon_path is None:
            return
        icon = iconfunctions.get_qicon(self.__icon_path)
        self.setIcon(icon)

    def __resize_font(self):
        font = data.get_general_font()
        font.setBold(self.bold)
        self.setFont(font)


class ExpandingPushButton(PushButtonBase):
    def __init__(
        self,
        parent=None,
        icon_path=None,
        icon_size=None,
        align_text=None,
        enter_func=None,
        leave_func=None,
        padding="2px",
    ):
        super().__init__(parent)
        if icon_path is not None:
            self.setIcon(iconfunctions.get_qicon(icon_path))
        stylesheet = _btn_style_.get_btn_stylesheet()
        self.default_stylesheet = stylesheet
        self.setStyleSheet(stylesheet)
        if enter_func is not None:
            self.set_enter_function(enter_func)
        if leave_func is not None:
            self.set_leave_function(leave_func)
        self.update_style(icon_size)

    def set_background_color(self, color=None):
        stylesheet = self.default_stylesheet
        if color:
            stylesheet += f"""
                QPushButton {{
                    background: {color};
                }}
            """
        self.setStyleSheet(stylesheet)

    def update_style(self, new_size):
        self.setIconSize(
            qt.create_qsize(
                new_size[0] - int(new_size[0] * 10 / 40),
                new_size[1] - int(new_size[1] * 10 / 40),
            )
        )
        self.setFont(data.get_general_font())


class StandardCheckBox(qt.QCheckBox):
    click_signal = qt.pyqtSignal()

    def __init__(
        self, parent=None, name: str = "", style: Optional[str] = None
    ):
        super().__init__(parent)
        self.name = name
        self.style = style
        self.update_style()

    def update_style(self):
        if not qt.sip.isdeleted(self):
            if self.style == "round":
                self.setStyleSheet(gui.stylesheets.checkbox.get_round())
            else:
                self.setStyleSheet(gui.stylesheets.checkbox.get_standard())

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.click_signal.emit()


class CheckBox(qt.QCheckBox):
    state = False
    enter_function = None
    leave_function = None

    checkChange = qt.pyqtSignal(bool)

    def __init__(self, parent, name, size):
        super().__init__(parent)
        self.state = False
        self.setObjectName(name)
        self.setStyleSheet(
            gui.stylesheets.checkbox.get_wizard_chbx_stylesheet(size)
        )

    #        self.stateChanged.connect(self.state_changed)

    def state_changed(self, state):
        if state == qt.PyQt.QtCore.Qt.CheckState.Checked:
            self.state = True
        else:
            self.state = False

    def disable(self):
        self.setCheckState(qt.PyQt.QtCore.Qt.CheckState.Unchecked)
        self.setEnabled(False)

    def enable(self):
        self.setCheckState(qt.PyQt.QtCore.Qt.CheckState.Unchecked)
        self.setEnabled(True)

    def on(self):
        self.state = True
        self.setCheckState(qt.PyQt.QtCore.Qt.CheckState.Checked)
        self.checkChange.emit(True)

    def off(self):
        self.state = False
        self.setCheckState(qt.PyQt.QtCore.Qt.CheckState.Unchecked)
        self.checkChange.emit(False)

    def set_enter_function(self, func):
        self.enter_function = func

    def set_leave_function(self, func):
        self.leave_function = func

    def enterEvent(self, e):
        super().enterEvent(e)
        # Execute the additional enter function
        if self.enter_function is not None:
            self.enter_function()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        # Execute the additional leave function
        if self.leave_function is not None:
            self.leave_function()


class PopupDialogButton(CustomPushButton):
    return_code = None

    on_signal = qt.pyqtSignal()
    off_signal = qt.pyqtSignal()
    click_signal = qt.pyqtSignal(int)

    def __init__(
        self,
        return_code,
        parent=None,
        icon_path=None,
        icon_size=None,
        align_text=None,
        padding="2px",
        text=None,
        bold=False,
        checkable=False,
        style="standard",
        tooltip=None,
        button_padding=0,
    ):
        # Initialize superclass
        super().__init__(
            parent=parent,
            icon_path=icon_path,
            icon_size=icon_size,
            align_text=align_text,
            padding=padding,
            text=text,
            bold=bold,
            checkable=checkable,
            style=style,
            tooltip=tooltip,
        )
        # Style
        self.setStyleSheet(
            gui.stylesheets.button.get_simple_toggle_stylesheet(
                in_padding=button_padding
            )
        )
        size = data.get_general_icon_pixelsize() * 4
        self.setMinimumSize(size, int(size * 0.4))
        # Return code
        self.return_code = return_code
        # Enable mouse move events
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.on_signal.emit()

    def enterEvent(self, event):
        super().enterEvent(event)
        self.on_signal.emit()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.off_signal.emit()

    def mousePressEvent(self, event):
        # Execute the superclass mouse click event first
        super().mousePressEvent(event)
        self.click_signal.emit(self.return_code)

    def on(self):
        self.setFocus()
        return

    def off(self):
        pass


class AnimatedButton(ExpandingPushButton):
    movie = None
    static_icon = None

    def __init__(
        self,
        static_icon_path,
        movie_image_path,
        parent=None,
        icon_path=None,
        icon_size=None,
        align_text=None,
        enter_func=None,
        leave_func=None,
    ):
        super().__init__(
            parent, icon_path, icon_size, align_text, enter_func, leave_func
        )
        self.movie = qt.QMovie(
            iconfunctions.get_icon_abspath(movie_image_path), parent=self
        )
        self.movie.setCacheMode(qt.QMovie.CacheMode.CacheAll)
        self.movie.frameChanged.connect(self._update_animation)
        self.static_icon = iconfunctions.get_qicon(static_icon_path)
        self.setIcon(self.static_icon)
        self.update_style()

    def update_style(self):
        size = (data.get_toolbar_pixelsize(), data.get_toolbar_pixelsize())
        self.setIconSize(qt.create_qsize(*size))

    def _update_animation(self, frame_number):
        self.setIcon(qt.QIcon(self.movie.currentPixmap()))

    def animation_start(self, animation_speed=0, period_ms=0):
        self.movie.start()
        if animation_speed > 0:
            self.movie.setSpeed(animation_speed)
        if period_ms > 0:
            qt.QTimer.singleShot(period_ms, self.animation_stop)

    def animation_stop(self):
        self.movie.stop()
        self.setIcon(self.static_icon)


class AnimatedToolButton(qt.QToolButton):
    movie = None
    static_icon = None

    def __init__(self, parent, static_icon_path, movie_image_path):
        super().__init__(parent)
        self.movie = qt.QMovie(
            iconfunctions.get_icon_abspath(movie_image_path), parent=self
        )
        self.movie.setCacheMode(qt.QMovie.CacheMode.CacheAll)
        self.movie.frameChanged.connect(self._update_animation)
        self.static_icon = iconfunctions.get_qicon(static_icon_path)
        self.setIcon(self.static_icon)
        self.update_style()

    def update_style(self):
        size = (data.get_toolbar_pixelsize(), data.get_toolbar_pixelsize())
        self.setIconSize(qt.create_qsize(*size))

    def _update_animation(self, frame_number):
        self.setIcon(qt.QIcon(self.movie.currentPixmap()))

    def animation_start(self, animation_speed=0, period_ms=0):
        self.movie.start()
        if animation_speed > 0:
            self.movie.setSpeed(animation_speed)
        if period_ms > 0:
            qt.QTimer.singleShot(period_ms, self.animation_stop)

    def animation_stop(self):
        self.movie.stop()
        self.setIcon(self.static_icon)


class WaitingAnimationButton(AnimatedButton):
    pixmaps = None
    initialized = False
    frame_counter = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        painter = qt.QPainter()
        self.pixmaps = []
        for i in range(self.movie.frameCount()):
            iconpath = "icons/loading_animation/hourglass_animation/hourglass_{:02d}.png".format(
                i + 1
            )
            wait_pixmap = iconfunctions.get_qpixmap(iconpath)
            self.movie.jumpToFrame(i)
            movie_pixmap = self.movie.currentPixmap()
            painter.begin(movie_pixmap)
            painter.drawPixmap(
                wait_pixmap.size().width() / 6,
                wait_pixmap.size().height() / 6,
                wait_pixmap,
            )
            painter.end()
            self.pixmaps.append(movie_pixmap)

        self.initialized = True

    def _update_animation(self, frame_number):
        if self.initialized == True:
            if len(self.pixmaps) > self.frame_counter:
                self.setIcon(qt.QIcon(self.pixmaps[self.frame_counter]))
                self.frame_counter += 1
            else:
                self.frame_counter = 0


class WaitingAnimationToolButton(AnimatedToolButton):
    pixmaps = None
    initialized = False
    frame_counter = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        painter = qt.QPainter()
        self.pixmaps = []
        for i in range(self.movie.frameCount()):
            iconpath = "icons/loading_animation/hourglass_animation/hourglass_{:02d}.png".format(
                i + 1
            )
            wait_pixmap = iconfunctions.get_qpixmap(iconpath)
            self.movie.jumpToFrame(i)
            movie_pixmap = self.movie.currentPixmap()
            painter.begin(movie_pixmap)
            painter.drawPixmap(
                wait_pixmap.size().width() / 6,
                wait_pixmap.size().height() / 6,
                wait_pixmap,
            )
            painter.end()
            self.pixmaps.append(movie_pixmap)

        self.initialized = True

    def _update_animation(self, frame_number):
        if self.initialized == True:
            self.setIcon(qt.QIcon(self.pixmaps[self.frame_counter]))
            self.frame_counter += 1
            if self.frame_counter >= 40:
                self.frame_counter = 0


class RadioButton(qt.QRadioButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_style()

    def update_style(self):
        self.setStyleSheet(gui.stylesheets.button.get_radio_style())
        self.setIconSize(
            qt.QSize(
                data.get_general_icon_pixelsize(),
                data.get_general_icon_pixelsize(),
            )
        )
