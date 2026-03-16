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

import qt
import data
import functions
import gui.stylesheets.menu


class BaseMenu(qt.QMenu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style the menu
        self.update_style()

    def setStyle(self, *args, **kwargs):
        super().setStyle(*args, **kwargs)
        self.update_style()

    def update_style(self):
        self.setStyleSheet(gui.stylesheets.menu.get_general_stylesheet())

    def addAction(self, *args, **kwargs):
        result = super().addAction(*args, **kwargs)
        # Get the starting and shortcut texts and largest text length
        actions = {}
        spacing = 3
        largest_text = 0
        for a in self.actions():
            if a.text().strip() == "":
                continue
            text = a.text()
            if "\t" in text:
                sl = text.split("\t")
                text_start = sl[0].strip()
                text_shortcut = "".join(sl[1:]).strip()
                length = len(text_start + text_shortcut)
                actions[a] = {
                    "text_start": text_start,
                    "text_shortcut": text_shortcut,
                    "length": length,
                }
            else:
                sl = text.split(" " * spacing)
                text_start = sl[0].strip()
                text_shortcut = "".join(sl[1:]).strip()
                length = len(text_start + text_shortcut)
                actions[a] = {
                    "text_start": text_start,
                    "text_shortcut": text_shortcut,
                    "length": length,
                }
            if length > largest_text:
                largest_text = length
        # Add the spacing
        largest_text += spacing
        # Set the action texts according to largest text
        for a in self.actions():
            if a.text().strip() == "":
                continue
            action = actions[a]
            if action["text_shortcut"] is not None:
                padding = " " * (largest_text - action["length"])
                new_text = (
                    f"{action['text_start']}{padding}{action['text_shortcut']}"
                )
                new_text = new_text.strip()
                a.setText(new_text)
        return result

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        key = event.key()
        if (key >= qt.Qt.Key.Key_A and key <= qt.Qt.Key.Key_Z) or (
            key >= qt.Qt.Key.Key_0 and key <= qt.Qt.Key.Key_9
        ):
            active_action = self.activeAction()
            if active_action is not None and active_action.text() is not None:
                key_char = event.text().lower()
                if active_action.text().lower().startswith(key_char):
                    self.focusNextPrevChild(True)
                else:
                    for action in self.actions():
                        if action.text() is not None:
                            if action.text().lower().startswith(key_char):
                                self.setActiveAction(action)
                                break


class AdvancedMenu(BaseMenu):
    item_triggered = qt.pyqtSignal(object)
    item_hovered = qt.pyqtSignal(object)
    entered_item = qt.pyqtSignal(object)
    left_item = qt.pyqtSignal(object)
    closed = qt.pyqtSignal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.last_hovered_action = None
        self.dragging_enabled = False

        # Install an event filter to detect mouse move events on the menu
        self.installEventFilter(self)

        # Connect needed signals
        self.hovered.connect(self.on_hovered)

    def set_dragging(self, enabled: bool) -> None:
        self.dragging_enabled = enabled

    def on_hovered(self, action: qt.QAction) -> None:
        if data.application.mouseButtons() != qt.Qt.MouseButton.NoButton:
            return

        # Trigger the enter event if valid
        if self.last_hovered_action is None:
            self.entered_item.emit(action)

        # This will trigger when an action is hovered
        self.last_hovered_action = (
            action  # Keep track of the currently hovered action
        )

        self.item_hovered.emit(action)

    __position_cache = None

    def eventFilter(self, source, event):
        if self.dragging_enabled:
            # Detect mouse move events on the menu
            if event.type() == event.Type.MouseMove:
                action = source.actionAt(event.position().toPoint())
                # No buttons pressed
                if event.buttons() == qt.Qt.MouseButton.NoButton:
                    # If the cursor is not over any action, and we had a previously hovered action, it's a "leave"
                    if self.last_hovered_action is not None and (
                        action is None or action != self.last_hovered_action
                    ):
                        self.left_item.emit(self.last_hovered_action)
                        self.last_hovered_action = (
                            None  # Reset the last hovered action
                        )

                else:
                    # If the cursor is not over any action, and we had a previously hovered action, it's a "leave"
                    if self.last_hovered_action is not None:
                        self.left_item.emit(self.last_hovered_action)
                        self.last_hovered_action = (
                            None  # Reset the last hovered action
                        )

                    # Test for a drag
                    if self.__position_cache is None:
                        self.__position_cache = event.pos()
                    else:
                        if action is not None:
                            diff = event.pos() - self.__position_cache
                            if abs(diff.x()) > 4 or abs(diff.y()) > 4:
                                # Create the drag object
                                drag = qt.QDrag(self)

                                # Get the global cursor position
                                global_mouse_pos = qt.QCursor.pos()
                                # Map the global position to the local QMenu coordinates
                                local_mouse_pos = self.mapFromGlobal(
                                    global_mouse_pos
                                )
                                pixmap = functions.text_to_pixmap_rectangle(
                                    action.text(), local_mouse_pos
                                )

                                # Set the drag information
                                mimedata = qt.QMimeData()
                                mimedata.setImageData(pixmap)
                                drag.setMimeData(mimedata)
                                drag.setPixmap(pixmap)

                                # Set the hotspot to the center of the pixmap
                                center_x = pixmap.width() // 2
                                center_y = pixmap.height() // 2
                                drag.setHotSpot(qt.QPoint(center_x, center_y))

                                #                                self.signal_drag_start.emit()
                                drag.exec()

        # Dragging disabled
        else:
            # Detect mouse move events on the menu
            if event.type() == event.Type.MouseMove:
                action = source.actionAt(event.position().toPoint())

                # If the cursor is not over any action, and we had a previously hovered action, it's a "leave"
                if self.last_hovered_action is not None and (
                    action is None or action != self.last_hovered_action
                ):
                    self.left_item.emit(self.last_hovered_action)
                    self.last_hovered_action = (
                        None  # Reset the last hovered action
                    )

            elif event.type() == event.Type.MouseButtonRelease:
                action = source.actionAt(event.position().toPoint())
                if not self.dragging_enabled:
                    self.item_triggered.emit(action)

        # Detect hide event
        if event.type() == event.Type.Close:
            self.closed.emit()

        return super().eventFilter(source, event)


class CheckMenuItem(qt.QWidgetAction):

    def self_destruct(self) -> None:
        default_widget = self.defaultWidget()
        if default_widget is None:
            self.setDefaultWidget(None)
            try:
                self.triggered.disconnect()
            except TypeError as e:
                pass
            self.setParent(None)
            return

        for i in reversed(range(default_widget.layout().count())):
            widget = default_widget.layout().itemAt(i).widget()
            default_widget.layout().removeWidget(widget)
            widget.deleteLater()
            widget.setParent(None)
            del widget
        default_widget.layout().deleteLater()
        default_widget.deleteLater()
        default_widget.setParent(None)
        del default_widget
        try:
            self.triggered.disconnect()
        except TypeError as e:
            pass
        self.setParent(None)

    def __init__(
        self,
        parent,
        name,
        icon,
        text,
        tooltip,
        checkable=False,
        checked=False,
        hide_check_field=False,
    ) -> None:
        super().__init__(parent)
        if not isinstance(name, str):
            raise Exception(
                "CustomMenuItem name has to be a string, "
                + f"not: '{name}'/'{name.__class__.__name__}' "
            )
        self.__name = name
        self.__icon = icon
        self.__text = text
        self.__checkable = checkable
        self.__checked = checked
        self.__hide_check_field = hide_check_field
        self.setToolTip(tooltip)
        self.setStatusTip(tooltip)
        import gui.templates.widgetgenerator

        self.init()
        return

    def init(self):
        frame = qt.QFrame(self.parent())
        frame.setMouseTracking(True)
        layout = qt.QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        frame.setStyleSheet(
            f"""
QFrame {{
    background-color: transparent;
    border: none;
    font-family: {data.get_global_font_family()};
    font-size: {data.get_general_font_pointsize()}pt;
    color: {data.theme["fonts"]["default"]["color"]};
}}
QFrame:hover {{
    background-color: {data.theme["indication"]["hover"]};
}}

QLabel {{
    background-color: transparent;
    border: none;
}}
        """
        )
        frame.setLayout(layout)
        self.frame = frame
        # Checkbox
        if not self.__hide_check_field:
            if self.__checkable == False:
                check_icon = None
            else:
                if self.__checked == True:
                    check_icon = "icons/checkbox/checked_dot.png"
                else:
                    check_icon = "icons/include_chbx/h_files/grey.png"
            checkbox = gui.templates.widgetgenerator.create_label(
                image=check_icon,
                selectable_text=False,
                transparent_background=True,
            )
            checkbox.setMouseTracking(True)
            checkbox.setFixedSize(
                qt.create_qsize(
                    int(data.get_general_icon_pixelsize() * 0.8),
                    int(data.get_general_icon_pixelsize() * 0.8),
                )
            )
            layout.addWidget(checkbox)
        # Image
        image = gui.templates.widgetgenerator.create_label(
            image=self.__icon,
            selectable_text=False,
            transparent_background=True,
        )
        image.setMouseTracking(True)
        image.setFixedSize(
            qt.create_qsize(
                int(data.get_general_icon_pixelsize() * 0.8),
                int(data.get_general_icon_pixelsize() * 0.8),
            )
        )
        layout.addWidget(image)
        # Text
        text = gui.templates.widgetgenerator.create_label(
            text=self.__text,
            selectable_text=False,
            transparent_background=True,
        )
        text.setMouseTracking(True)
        layout.addWidget(text)

        # Set the frame as default widget
        self.setDefaultWidget(frame)
