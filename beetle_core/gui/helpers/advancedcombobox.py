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
import sys, gc, traceback
import qt, data, purefunctions, functions, iconfunctions
from various.kristofstuff import *
from ..templates.basemenu import *
import gui.helpers.buttons
import gui.stylesheets.tooltip


class AdvancedComboBoxItem(qt.QWidgetAction):

    def self_destruct(self) -> None:
        """"""
        default_widget = self.defaultWidget()
        if default_widget is None:
            purefunctions.printc(
                "WARNING: self.defaultWidget() returned None. See advancedcombobox.py "
                "line 23",
                color="warning",
            )
            self.setDefaultWidget(None)  # noqa
            try:
                self.triggered.disconnect()
            except TypeError as e:
                purefunctions.printc(
                    "ERROR: AdvancedComboBox() -> could not disconnect triggered signal",
                    color="error",
                )
            self.setParent(None)  # noqa
            return

        for i in reversed(range(default_widget.layout().count())):
            widget = default_widget.layout().itemAt(i).widget()
            default_widget.layout().removeWidget(widget)
            widget.deleteLater()
            widget.setParent(None)  # noqa
            del widget
        default_widget.layout().deleteLater()
        default_widget.deleteLater()
        default_widget.setParent(None)  # noqa
        del default_widget
        try:
            self.triggered.disconnect()
        except TypeError as e:
            purefunctions.printc(
                "ERROR: AdvancedComboBox() -> could not disconnect triggered signal",
                color="error",
            )
        self.setParent(None)  # noqa
        return

    def self_destruct_widget(self) -> None:
        """"""
        default_widget = self.defaultWidget()
        if default_widget is None:
            purefunctions.printc(
                "WARNING: self.defaultWidget() returned None. See advancedcombobox.py "
                "line 58",
                color="warning",
            )
            self.setDefaultWidget(None)  # noqa
            return

        for i in reversed(range(default_widget.layout().count())):
            widget = default_widget.layout().itemAt(i).widget()
            default_widget.layout().removeWidget(widget)
            widget.deleteLater()
            widget.setParent(None)  # noqa
        default_widget.setParent(None)  # noqa
        self.setDefaultWidget(None)  # noqa
        return

    def __init__(self, parent, name, data, level) -> None:
        """"""
        super().__init__(parent)
        if not isinstance(name, str):
            raise Exception(
                f"AdvancedComboBoxItem name has to be a string, not: '{name}'/'{name.__class__.__name__}' "
            )
        self.name = name
        self.data = data
        self.level = level
        return


# ISSUE:
# When hovering the mouse over items in an `AdvancedCombobox()`, the hovering background color would
# oftentimes not appear, or items would get stuck to the hovering color even after the mouse left.
# It looks like certain events are missed.
# SOLUTION:
# Use this `AdvancedComboBoxLabel()` instead of `gui.templates.widgetgenerator.create_label()` to
# show text on the items. The advantage of this `AdvancedComboBoxLabel()` is that all the mouse
# events can be explicitely ignored, such that they propagate properly to the underlying frame
# `AdvancedComboBoxItemHolder()`.
class AdvancedComboBoxLabel(qt.QLabel):

    def self_destruct(self) -> None:
        """"""
        if qt.sip.isdeleted(self):
            return
        self.setParent(None)
        return

    def __init__(
        self,
        image=None,
        parent=None,
    ) -> None:
        """There are two ways to make this `AdvancedComboBoxLabel()` invisible
        for the mouse, such that the events trickle down to the parent
        `AdvancedComboBoxItemHolder()`:

            1. Set:
                   self.setAttribute(qt.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
               and don't override any mouse events.

            2. Remove previous line,
               and override all mouse event explicitely ignoring their events.

        I chose option 2 for now.
        """
        super().__init__(parent)
        # Make transparent for mouse events!
        # self.setAttribute(qt.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.__text_color: str = "default"
        if image is not None:
            pixmap = iconfunctions.get_qpixmap(image)
            self.setPixmap(pixmap)
            self.setScaledContents(True)
        else:
            font = data.get_general_font()
            self.setFont(font)
            self.setAlignment(
                qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
            )
        self.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.Minimum, qt.QSizePolicy.Policy.Minimum
            )
        )
        self.setFocusPolicy(qt.Qt.FocusPolicy.NoFocus)
        self.__update_style_sheet()
        return

    def mouseMoveEvent(self, event):
        event.ignore()
        return super().mouseMoveEvent(event)

    def enterEvent(self, event):
        event.ignore()
        return super().enterEvent(event)

    def leaveEvent(self, event):
        event.ignore()
        return super().leaveEvent(event)

    def mousePressEvent(self, event):
        event.ignore()
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        event.ignore()
        return super().mouseReleaseEvent(event)

    def set_colors(
        self,
        text_color=None,
        *args,
        **kwargs,
    ) -> None:
        """"""
        print(
            "ERROR: AdvancedComboBoxLabel().set_colors() no longer implemented! "
            "Use AdvancedComboBoxLabel().set_combobox_label_text_color() instead."
        )
        return

    def set_combobox_label_text_color(
        self, text_color: Optional[str] = None
    ) -> None:
        """"""
        colornames = (
            "default",
            "red",
            "green",
            "blue",
            "purple",
            "grey",
            "lightgrey",
        )
        if text_color not in colornames:
            print(
                f"ERROR:\n"
                f"AdvancedComboBoxLabel('{self.text()}').set_combobox_label_text_color(\n"
                f"    text_color='{text_color}'\n"
                f")\n"
                f"must be one of these:\n"
                f"{colornames}"
            )

            # Try nevertheless to find a match...
            def _match(_colorname: str) -> bool:
                if text_color == data.theme["fonts"][_colorname]["color"]:
                    return True
                if text_color == data.theme["fonts"][_colorname][
                    "color"
                ].replace("#ff", "#"):
                    return True
                return False

            for cname in colornames:
                if not _match(cname):
                    continue
                print(
                    f"REPLACED:\n"
                    f"AdvancedComboBoxLabel('{self.text()}').set_combobox_label_text_color(\n"
                    f"    text_color='{text_color}'\n"
                    f")\n"
                    f"with:\n"
                    f"AdvancedComboBoxLabel('{self.text()}').set_combobox_label_text_color(\n"
                    f"    text_color='{cname}'\n"
                    f")\n"
                )
                self.__text_color = cname
                break
            else:
                print(f"NO REPLACEMENT FOUND!")
            self.update_style()
            return
        self.__text_color = text_color
        self.update_style()
        return

    def update_style(self) -> None:
        """"""
        if qt.sip.isdeleted(self):
            return
        self.setFont(data.get_general_font())
        self.__update_style_sheet()
        return

    def __update_style_sheet(self) -> None:
        """Keep the background color always transparent!"""
        text_color = data.theme["fonts"][self.__text_color]["color"]
        style_sheet = f"""
QLabel {{
    background-color: transparent;
    color: {text_color};
}}"""
        self.setStyleSheet(style_sheet)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        return


class AdvancedComboBoxItemHolder(qt.QFrame):
    name_count = 0

    def self_destruct(self) -> None:
        """"""
        if qt.sip.isdeleted(self):
            return
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget()
            self.layout().removeWidget(widget)
            widget.deleteLater()
            widget.setParent(None)  # noqa
            del widget
        self.layout().deleteLater()
        self.setParent(None)  # noqa
        return

    def __init__(self, *args, **kwargs) -> None:
        """"""
        super().__init__(*args, **kwargs)
        self.setProperty("hover", False)
        self.setStyleSheet(
            f"""
        QFrame[hover="false"] {{
            background-color: transparent;
            border: none;
        }}
        QFrame[hover="true"] {{
            background-color: {data.theme["indication"]["hover"]};
            border: none;
        }}
        QLabel {{
            background-color: transparent;
            border: none;
        }}
        """
        )
        self.setMouseTracking(True)
        self.setObjectName(f"gb-{AdvancedComboBoxItemHolder.name_count}")
        AdvancedComboBoxItemHolder.name_count += 1
        return

    def enterEvent(self, event: qt.QEnterEvent) -> None:
        """"""
        if event:
            super().enterEvent(event)
        self.setProperty("hover", True)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        qt.QTimer.singleShot(200, self.check_hover_status)
        return

    def check_hover_status(self, *args, **kwargs) -> None:
        """Check regularly if the mouse is still on top.

        If not, maybe the leave event was missed - so
        enforce it!
        The `self.underMouse()` method proved to be unreliable. So I created my own method
        `is_mouse_over_widget()` to check.
        """
        if qt.sip.isdeleted(self):
            return
        if self.is_mouse_over_widget():
            qt.QTimer.singleShot(200, self.check_hover_status)
            return
        if self.property("hover"):
            self.leaveEvent(None)
        return

    def is_mouse_over_widget(self) -> bool:
        """Check if mouse is on top.

        More reliable than `self.underMouse()`.
        """
        cursor_pos = qt.QCursor.pos()
        widget_rect = self.rect()
        widget_pos = self.mapToGlobal(widget_rect.topLeft())
        widget_rect_global = qt.QRect(widget_pos, widget_rect.size())
        return widget_rect_global.contains(cursor_pos)

    def leaveEvent(self, event: Optional[qt.QEnterEvent]) -> None:
        """"""
        if event:
            super().leaveEvent(event)
        self.setProperty("hover", False)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        return


class AdvancedComboBoxMenu(BaseMenu):
    def __init__(self, parent, name, level):
        super().__init__(parent)
        self.name = name
        self.level = level

    def clear_all(self):
        if not qt.sip.isdeleted(self):
            for act in self.actions():
                if hasattr(act, "defaultWidget"):
                    default_widget = act.defaultWidget()
                    data.application.sendEvent(
                        default_widget, qt.QEvent(qt.QEvent.Type.Leave)
                    )
                    default_widget.repaint()
                    for i in range(default_widget.layout().count()):
                        widget = default_widget.layout().itemAt(i).widget()
                        data.application.sendEvent(
                            widget, qt.QEvent(qt.QEvent.Type.Leave)
                        )
                        widget.repaint()

    def enterEvent(self, e):
        super().enterEvent(e)
        self.clear_all()


#    def leaveEvent(self, e):
#        super().leaveEvent(e)
#        self.clear_all()


class AdvancedComboBox(qt.QGroupBox):
    activated = qt.pyqtSignal(int)
    selection_changed = qt.pyqtSignal(str, object)
    selection_changed_from_to = qt.pyqtSignal(str, str)

    def self_destruct(
        self,
        death_already_checked: bool = False,
        *args,
        **kwargs,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill AdvancedComboBox() twice!")
            self.dead = True

        signals = (
            self.activated,
            self.selection_changed,
            self.selection_changed_from_to,
        )
        for signal in signals:
            try:
                signal.disconnect()
            except:
                pass

        if self.menu:
            for k, v in self.item_cache.items():
                if "action-reference" in v.keys():
                    _action_reference: AdvancedComboBoxItem = v[
                        "action-reference"
                    ]
                    if _action_reference is not None:
                        _action_reference.self_destruct()
            self.menu.deleteLater()
            self.menu.setParent(None)  # noqa
            self.menu = None
        for i in reversed(range(self.layout().count())):
            widget: AdvancedComboBoxItem = (
                self.layout().itemAt(i).widget()
            )  # noqa
            widget.self_destruct()
            widget.deleteLater()
            widget.setParent(None)  # noqa
            self.layout().removeWidget(widget)
            del widget
        for k in list(self.item_cache.keys()):
            self.item_cache.pop(k, None)
        self.item_cache = None

        for item in self.self_destruct_cache:
            if not qt.sip.isdeleted(item):
                if hasattr(item, "self_destruct"):
                    item.self_destruct()
                item.deleteLater()
                item.setParent(None)  # noqa
            del item
        self.self_destruct_cache = None
        self.layout().deleteLater()
        self.deleteLater()
        self.setParent(None)  # noqa
        return

    def __init__(
        self,
        parent=None,
        initial_item=None,
        initial_items=None,
        contents_margins=(0, 0, 0, 0),
        spacing=0,
        image_size=None,
        no_selection_icon=None,
        no_selection_text=None,
        fixed_height=False,
    ) -> None:
        """
        :param parent:
        :param initial_item:
        :param initial_items:
        :param contents_margins:
        :param spacing:
        :param image_size:
        :param no_selection_icon:
        :param no_selection_text:
        :param fixed_height:
        """
        super().__init__(parent)
        self.dead: bool = False
        self.installEventFilter(self)

        self.self_destruct_cache: List[AdvancedComboBoxItem] = []

        self.setObjectName("AdvancedComboBox")

        self.minimum_height = 0

        self.base_image_size = image_size
        self.__update_actual_image_size()

        self.font = data.get_toplevel_font()
        self.contents_margins = contents_margins
        self.spacing = spacing
        self.fixed_height = fixed_height

        # Containers
        self.item_index = 0
        self.item_cache: Dict[str, AdvancedComboBoxItem] = {}
        self.selected_item: Optional[AdvancedComboBoxItem] = None

        # Create layout
        self.setLayout(qt.QHBoxLayout(self))
        self.layout().setContentsMargins(
            *(int(x) for x in self.contents_margins)
        )
        self.layout().setSpacing(int(self.spacing))

        # Empty selection options
        self.no_selection_icon_relpath = "icons/gen/question_mark.png"
        self.no_selection_icon_abspath = iconfunctions.get_icon_abspath(
            self.no_selection_icon_relpath
        )
        if no_selection_icon:
            if no_selection_icon.startswith("icon"):
                # The given 'no_selection_icon' parameter is a relative path to the icon
                self.no_selection_icon_relpath = no_selection_icon
                self.no_selection_icon_abspath = iconfunctions.get_icon_abspath(
                    self.no_selection_icon_relpath
                )
            elif no_selection_icon.startswith(
                data.resources_directory
            ) or no_selection_icon.startswith(data.settings_directory):
                # The given 'no_selection_icon' parameter is an absolute path to the icon
                self.no_selection_icon_abspath = no_selection_icon
                self.no_selection_icon_relpath = (
                    self.no_selection_icon_abspath.replace(
                        data.resources_directory, "", 1
                    )
                )
                self.no_selection_icon_relpath = (
                    self.no_selection_icon_abspath.replace(
                        data.settings_directory, "", 1
                    )
                )
                if self.no_selection_icon_relpath.startswith("/"):
                    self.no_selection_icon_relpath = (
                        self.no_selection_icon_relpath[1:]
                    )
            else:
                assert False, str(
                    f"Given parameter no_selection_icon = "
                    f"{q}{no_selection_icon}{q} not valid!"
                )
        self.no_selection_text = "SELECT SOMETHING"
        if no_selection_text:
            self.no_selection_text = no_selection_text

        # Menu
        self.menu = AdvancedComboBoxMenu(self, "main-menu", 0)

        # Initial items
        if initial_items is not None:
            self.add_items(initial_items)

        # Initial state
        if initial_item is not None:
            if isinstance(initial_item, str):
                self.set_selected_name(initial_item)
            else:
                self.set_selected_item(initial_item)
        else:
            self.reset_selected_item()

        #        self.update_style(
        #            font=data.get_editor_font()
        #        )
        qt.QTimer.singleShot(
            0, lambda *args: self.update_style(font=data.get_editor_font())
        )

    @property
    def image_size(self):
        return self._image_size

    @image_size.setter
    def image_size(self, value):
        self._image_size = value
        self.actual_image_size = int(value * 0.8)

    def set_minimum_height(self, minimum_height: int) -> None:
        self.minimum_height = minimum_height
        return

    def eventFilter(self, obj, event):
        if event.type() == qt.QEvent.Type.MouseButtonPress:
            qt.QTimer.singleShot(0, self.toggle_menu)

        elif event.type() == qt.QEvent.Type.Leave:
            widget = self.layout().itemAt(0).widget()
            data.application.sendEvent(widget, qt.QEvent(qt.QEvent.Type.Leave))
            widget.repaint()

        return super().eventFilter(obj, event)

    def enterEvent(self, event):
        event.ignore()

    def leaveEvent(self, event):
        event.ignore()

    def mouseMoveEvent(self, event):
        event.ignore()

    def echo(self, *messages):
        class_name = self.__class__.__name__
        print(f"[{class_name}]", *messages)

    def clear(self) -> None:
        # Clean states
        self.item_index = 0
        self.item_cache = {}

        # Clean the menu
        def clean_menu(menu: AdvancedComboBoxMenu):
            if menu is None:
                return
            for a in menu.actions():
                combobox_item: AdvancedComboBoxItem = a
                if hasattr(combobox_item, "self_destruct_widget"):
                    combobox_item.self_destruct_widget()
                if hasattr(combobox_item, "self_destruct"):
                    combobox_item.self_destruct()
                if not hasattr(combobox_item, "menu"):
                    if purefunctions.PERFORMANCE_MEASURING_FLAG:
                        purefunctions.printc(
                            f"WARNING: combobox_item.menu doesn{q}t exist! See line 369 in advancedcombobox.py",
                            color="warning",
                        )
                if (
                    hasattr(combobox_item, "menu")
                    and combobox_item.menu() is not None
                ):
                    clean_menu(combobox_item.menu())
            menu.clear()
            return

        clean_menu(self.menu)
        return

    def get_name_from_index(self, index) -> str:
        for k, v in self.item_cache.items():
            if v.index == index:
                return v.name
        raise Exception(
            f"[{self.__class__.__name__}] Index '{index}' not found!"
        )

    def set_selected_name(self, name: Optional[str]) -> None:
        if (
            (name is None)
            or (name.lower() == "none")
            or (name.lower() == "empty")
        ):
            # Reset the selection
            self.reset_selected_item()
            return
        try:
            item = self.item_cache[name]
        except:
            print(
                f"\nFAILED: set_selected_name({name})\n"
                f"Currently in cache:\n"
                f"{self.item_cache.keys()}\n"
            )
            raise
        self.set_selected_item(item)
        return

    def get_number_of_items(self) -> int:
        return len(self.item_cache)

    def set_selected_item(self, item):
        # Create widget
        if self.layout().count() > 0:
            widget = self.layout().itemAt(0).widget()
            widget.deleteLater()
            self.layout().removeWidget(widget)
            del widget
        frame = self.__create_item_widget(self, item, selected=True)
        self.layout().addWidget(frame)
        # Set selected item
        self.selected_item = item
        # Update style
        self.update_style()

    def get_selected_item(self):
        return self.selected_item

    def get_items(self):
        return self.item_cache

    def set_no_selection_icon(self, value):
        if value is None:
            return
        if value.startswith("icon"):
            # The given 'value' parameter is a relative path to the icon
            self.no_selection_icon_relpath = value
            self.no_selection_icon_abspath = iconfunctions.get_icon_abspath(
                self.no_selection_icon_relpath
            )
            return
        if value.startswith(data.resources_directory) or value.startswith(
            data.settings_directory
        ):
            # The given 'value' parameter is an absolute path to the icon
            self.no_selection_icon_abspath = value
            self.no_selection_icon_relpath = (
                self.no_selection_icon_abspath.replace(
                    data.resources_directory, "", 1
                )
            )
            self.no_selection_icon_relpath = (
                self.no_selection_icon_abspath.replace(
                    data.settings_directory, "", 1
                )
            )
            if self.no_selection_icon_relpath.startswith("/"):
                self.no_selection_icon_relpath = self.no_selection_icon_relpath[
                    1:
                ]
            return

        # The given 'value' parameter is not valid.
        assert False, str(f"Given parameter value = {q}{value}{q} not valid!")
        return

    def set_no_selection_text(self, value):
        self.no_selection_text = value

    def reset_selected_item(self):
        self.set_selected_item(
            {
                "name": "empty",
                "widgets": (
                    {
                        "type": "image",
                        "icon-path": self.no_selection_icon_relpath,
                    },
                    {
                        "type": "text",
                        "text": self.no_selection_text,
                        "alignment": "center",
                    },
                ),
            }
        )

    def add_item(
        self,
        item,
        insert_before_item=None,
        _in_menu=None,
        _in_level=0,
        do_update=True,
    ) -> None:
        """
        Parameters:
            - item: dict -> dictionary with data of the item. Example item:
                {
                    "name": f"item-0",
                    "widgets":
                        (
                            {"type": "image", "icon-path": "icons/chip/chip_protocol.png"},
                            {"type": "image", "icon-path": "icons/chip/chip_protocol(dis).png"},
                            {"type": "text", "text": "INSERTED ITEM"},
                        )
                }

            - insert_before_item: str -> item name before which the 'item' parameter should
                                         be inserted at. Example: 'item-1'

            - _in_menu: data.BaseMenu -> PRIVATE, DO NOT USE

            - _in_level: int -> PRIVATE, DO NOT USE

            - do_update: bool -> Invoke 'self.adjust_size()' immediately after adding
                                 the given item. Set to False when adding many items
                                 rapidly, then invoke the adjust size method afterwards
                                 manually.
        """
        # Store the item
        name = item["name"]
        if name in self.item_cache.keys():
            raise Exception(
                f"[{self.__class__.__name__}] Item '{name}' is already in the cache!"
            )
        self.item_cache[name] = item

        # Determine parent menu
        if _in_menu is not None:
            menu = _in_menu
        else:
            menu = self.menu

        if "subitems" in item.keys():
            icon = None
            text = None
            color = None
            for i in item["widgets"]:
                if i["type"] == "text":
                    text = i["text"]
                    if "color" in i.keys():
                        color = i["color"]
                elif i["type"] == "image":
                    icon = iconfunctions.get_qicon(i["icon-path"])
                if icon is not None and text is not None:
                    break
            menu_item = AdvancedComboBoxMenu(self, f"{name}-menu", _in_level)
            if "enabled" in item.keys():
                state = item["enabled"]
                menu_item.setEnabled(state)
            else:
                menu_item.setEnabled(True)
            if icon is not None:
                menu_item.setIcon(icon)
            if text is not None:
                menu_item.setTitle(text)

            # action.setMenu(new_menu)
            # new_menu.addAction(action)
            if len(item["subitems"]) < 1:
                raise Exception(
                    f"[{self.__class__.__name__}] At least one sub-item has to exists in: {name}"
                )
            for si in item["subitems"]:
                self.add_item(si, _in_menu=menu_item, _in_level=_in_level + 1)

            item["menu-reference"] = menu_item

            menu.addMenu(menu_item)
            action = menu.menuAction()
            action.setData(item["widgets"])
        else:
            # Create the widget
            frame = self.__create_item_widget(menu, item)

            action = AdvancedComboBoxItem(menu, name, item, _in_level)

            action.setDefaultWidget(frame)
            if "enabled" in item.keys():
                state = item["enabled"]
                action.setEnabled(state)
            else:
                action.setEnabled(True)

            item["action-reference"] = action

            action.triggered.connect(self.triggered)

            if insert_before_item is not None:
                before_action = self.item_cache[insert_before_item][
                    "action-reference"
                ]
                insert_menu = before_action.parent()
                insert_menu.insertAction(before_action, action)
            else:
                menu.addAction(action)

        if do_update:
            self.adjust_size()

    @qt.pyqtSlot(bool)
    def triggered(self, triggered):
        acbi = self.sender()
        name1 = self.get_selected_item_name()
        name2 = acbi.name
        item = self.item_cache[name2]
        if not qt.sip.isdeleted(self):
            self.set_selected_item(item)
        if not qt.sip.isdeleted(self):
            self.selection_changed.emit(name2, item)
        if not qt.sip.isdeleted(self):
            self.selection_changed_from_to.emit(name1, name2)
        self.menu.clear_all()

    def add_items(self, items):
        for item in items:
            self.add_item(item, do_update=False)
        self.adjust_size()

    def change_item(self, name, new_item):
        # Get the index into which the new item has
        # to be inserted.
        item = self.item_cache[name]
        action = item["action-reference"]
        menu = action.parent()
        insert_before_item = None
        menu_item_count = len(menu.actions())
        for i in range(menu_item_count):
            if menu.actions()[i] is action:
                if (i + 1) < menu_item_count:
                    insert_before_item = menu.actions()[i + 1].name
                break
        # Remove the old item
        self.remove_item(name)
        # Insert the new action
        self.add_item(
            new_item, insert_before_item=insert_before_item, _in_menu=menu
        )
        # Check if item is currently selected
        if new_item["name"] == self.get_selected_item_name():
            self.set_selected_name(new_item["name"])
        # Repaint widgets
        self.update()

    def remove_item(self, name):
        # Clean the old widget
        item = self.item_cache[name]
        action = item["action-reference"]
        menu = action.parent()
        # Remove old item
        old_item = self.item_cache.pop(name)
        for a in menu.actions():
            combobox_item: AdvancedComboBoxItem = a
            if combobox_item.name == name:
                combobox_item.self_destruct()
                menu.removeAction(combobox_item)
                combobox_item.deleteLater()
                combobox_item.setParent(None)  # noqa
                break
        else:
            raise Exception(
                f"[{self.__class__.__name__}] Item '{name}' does not exists!"
            )

    def __create_label(self, *args, **kwargs) -> AdvancedComboBoxLabel:
        """
        ISSUE:
        When hovering the mouse over items in an `AdvancedCombobox()`, the hovering background color
        would oftentimes not appear, or items would get stuck to the hovering color even after the
        mouse left. It looks like certain events are missed.

        SOLUTION:
        Use this `AdvancedComboBoxLabel()` instead of `gui.templates.widgetgenerator.create_label()`
        to show text on the items. The advantage of this `AdvancedComboBoxLabel()` is that all the
        mouse events can be explicitely ignored, such that they propagate properly to the underlying
        frame `AdvancedComboBoxItemHolder()`.
        """
        label = AdvancedComboBoxLabel(*args, **kwargs)
        self.self_destruct_cache.append(label)
        return label

    def __create_item_widget(
        self, menu, item, selected=False
    ) -> AdvancedComboBoxItemHolder:
        """

        :param menu:
        :param item:
        :param selected:
        :return:
        """
        # Create the container
        frame = AdvancedComboBoxItemHolder(menu)
        self.self_destruct_cache.append(frame)
        layout = qt.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        frame.setLayout(layout)

        # Add the item
        label_parent = menu
        for _data in item["widgets"]:
            if _data["type"] == "image":
                label = self.__create_label(
                    image=_data["icon-path"],
                    parent=label_parent,
                )
                if "size" in _data.keys():
                    print(
                        f"[{self.__class__.__name__}] 'size' parameter "
                        f"is ignored as of Qt6 for item: {item}"
                    )
                width = data.get_general_icon_pixelsize()
                height = data.get_general_icon_pixelsize()
                label.setFixedSize(int(width), int(height))

                frame.layout().addWidget(label)
                frame.layout().setAlignment(
                    label, qt.Qt.AlignmentFlag.AlignVCenter
                )
            elif _data["type"] == "text":
                text = _data["text"]
                label = self.__create_label(
                    image=None,
                    parent=label_parent,
                )
                if "color" in _data.keys():
                    label.set_combobox_label_text_color(
                        text_color=_data["color"]
                    )
                else:
                    pass
                label.setText(text)
                if "alignment" in _data.keys():
                    alignment = _data["alignment"]
                    if alignment == "center":
                        label.setAlignment(
                            qt.Qt.AlignmentFlag.AlignHCenter
                            | qt.Qt.AlignmentFlag.AlignVCenter
                        )
                    elif alignment == "left":
                        label.setAlignment(
                            qt.Qt.AlignmentFlag.AlignLeft
                            | qt.Qt.AlignmentFlag.AlignVCenter
                        )
                    elif alignment == "right":
                        label.setAlignment(
                            qt.Qt.AlignmentFlag.AlignRight
                            | qt.Qt.AlignmentFlag.AlignVCenter
                        )
                    else:
                        raise Exception(
                            f"Unknown label alignment: '{alignment}'"
                        )
                frame.layout().addWidget(label)
                frame.layout().setAlignment(
                    label, qt.Qt.AlignmentFlag.AlignVCenter
                )
            else:
                raise Exception(
                    f"'{_data['type']}' is not a valid AdvancedGroupbox item type!"
                )

        # Selected item has an extra down arrow
        size = self.image_size * 0.8
        if selected:
            label = self.__create_label(
                image="icons/arrow/chevron/chevron_down.png",
                parent=label_parent,
            )
            label.setFixedSize(int(size), int(size))
            frame.layout().addWidget(label)
            frame.layout().setAlignment(label, qt.Qt.AlignmentFlag.AlignVCenter)

        elif "subitems" in item.keys():
            label = self.__create_label(
                image="icons/arrow/chevron/chevron_right.png",
                parent=label_parent,
            )
            label.setFixedSize(int(size), int(size))
            frame.layout().addWidget(label)
            frame.layout().setAlignment(label, qt.Qt.AlignmentFlag.AlignVCenter)
        else:
            label = self.__create_label(
                image=None,
                parent=label_parent,
            )
            label.setFixedSize(int(size), int(size))
            frame.layout().addWidget(label)
            frame.layout().setAlignment(label, qt.Qt.AlignmentFlag.AlignVCenter)

        # Return the frame
        return frame

    def toggle_menu(self):
        if self.menu is None:
            return
        if self.isEnabled() == False:
            return
        if list(self.menu.actions()) == []:
            return
        #        if not self.menu.isVisible():
        #            popup_point = self.mapToGlobal(qt.create_qpoint(0, self.size().height() + 1))
        #            self.menu.popup(popup_point)
        if not hasattr(self, "menu_visible"):
            self.menu_visible = False

            def hide_menu(*args):
                def _inner(*args):
                    self.menu_visible = False

                qt.QTimer.singleShot(100, _inner)

            self.menu.aboutToHide.connect(hide_menu)
        if not self.menu_visible:
            popup_point = self.mapToGlobal(
                qt.create_qpoint(0, self.size().height() + 1)
            )
            self.menu.popup(popup_point)
            self.menu_visible = True
        else:
            self.menu_visible = False

    def adjust_size(self, *args):
        ASYNC = False
        if ASYNC:
            if not hasattr(self, "adjust_timer"):
                self.adjust_timer = qt.QTimer(self)
                self.adjust_timer.setSingleShot(True)
                self.adjust_timer.setInterval(20)
                self.adjust_timer.timeout.connect(self.__adjust_size)
            else:
                self.adjust_timer.stop()
            self.adjust_timer.start()
        else:
            self.__adjust_size()
        return

    @qt.pyqtSlot()
    def __adjust_size(self):
        if self.menu is None:
            return
        largest_size = qt.create_qsize(0, 0)
        for act in self.menu.actions():
            if hasattr(act, "defaultWidget"):
                size = act.defaultWidget().sizeHint()
                if size.width() > largest_size.width():
                    largest_size = size
        if largest_size == qt.create_qsize(0, 0):
            largest_size = self.menu.sizeHint()
        self.adjustSize()
        margin = (self.contents_margins[0] * 2) + 2
        minimum_height = int(max(self.image_size + margin, self.minimum_height))
        self.setFixedHeight(minimum_height)
        #        self.setFixedHeight(self.image_size + margin)
        return

    def get_selected_item_name(self) -> str:
        return self.selected_item["name"]

    def resizeEvent(self, e):
        super().resizeEvent(e)
        gb = self.layout().itemAt(0).widget()
        for i in range(gb.layout().count()):
            gb.layout().itemAt(i).widget().adjustSize()

    #        self.__reselect_current_item()
    #    def __reselect_current_item(self):
    #        current_item = self.get_selected_item_name()
    #        if current_item != "empty":
    #            self.set_selected_name(current_item)
    #        else:
    #            self.reset_selected_item()

    def enable(self):
        self.setEnabled(True)

    def disable(self):
        self.setEnabled(False)

    def __update_actual_image_size(
        self, image_size: Optional[int] = None
    ) -> None:
        """"""
        if image_size is None:
            if self.base_image_size is not None:
                image_size = int(self.base_image_size * data.get_global_scale())
            else:
                image_size = data.get_general_icon_pixelsize()
        else:
            image_size = int(image_size * data.get_global_scale())
        image_size = int(image_size * 0.84)
        self.image_size = image_size
        return

    def update_style(
        self, image_size: Optional[int] = None, font: Optional[qt.QFont] = None
    ) -> None:
        """"""
        try:
            self.__update_actual_image_size(image_size)

            if font is None:
                font = data.get_editor_font()
            self.font = font

            self.setStyleSheet(
                f"""
AdvancedComboBox {{
    background-color: {data.theme["fonts"]["default"]["background"]};
    border: 1px solid {data.theme["dropdown_border"]};
    padding: 0px;
    spacing: 0px;
    margin: 0px;
}}
{gui.stylesheets.tooltip.get_default()}
            """
            )

            def resize_item(item: AdvancedComboBoxLabel) -> None:
                if isinstance(item, AdvancedComboBoxLabel):
                    if item.text().strip() != "":
                        item.setFont(self.font)
                    else:
                        item.setFixedSize(
                            int(self.actual_image_size),
                            int(self.actual_image_size),
                        )
                else:
                    raise Exception(
                        f"[{self.__class__.__name__}] Unknown resize item: {item.__class__}"
                    )
                return

            height_factor = 0.9
            # Selected item
            gb_widgetitem = self.layout().itemAt(0)
            if gb_widgetitem is not None:
                gb = gb_widgetitem.widget()
                gb.setFixedHeight(int(self.image_size * height_factor))
                for i in range(gb.layout().count()):
                    widget: AdvancedComboBoxLabel = cast(
                        AdvancedComboBoxLabel, gb.layout().itemAt(i).widget()
                    )
                    resize_item(widget)
                    widget.update_style()
                    continue

            # Menu items
            def resize_menu(_menu: AdvancedComboBoxMenu) -> None:
                if _menu is None:
                    return
                for it in _menu.actions():
                    if hasattr(it, "defaultWidget"):
                        gb = it.defaultWidget()
                        gb.setFixedHeight(int(self.image_size * height_factor))
                        for i in range(gb.layout().count()):
                            widget = gb.layout().itemAt(i).widget()
                            resize_item(widget)
                            widget.update_style()
                    if hasattr(it, "menu") and it.menu() is not None:
                        _menu = it.menu()
                        resize_menu(_menu)
                        _menu.update_style()
                    continue
                return

            resize_menu(self.menu)
            if self.menu is not None:
                self.menu.update_style()

            # Frame
            if self.fixed_height:
                self.setFixedHeight(int(self.image_size))

            for menu in self.findChildren(qt.QMenu):
                assert isinstance(menu, AdvancedComboBoxMenu)
                menu.update_style()
                resize_menu(menu)

            # Adjust the size
            self.adjust_size()
        except:
            traceback.print_exc()
        return

    def set_items(self, items=None, custom_func=None, reset_selection=True):
        if not reset_selection:
            selected_item_name = self.get_selected_item_name()
        self.clear()
        if items is None:
            # Add an "empty" item
            self.add_item(
                {
                    "name": "empty",
                    "widgets": (
                        {
                            "type": "image",
                            "icon-path": "icons/dialog/cancel.png",
                        },
                        {"type": "text", "text": "Empty"},
                    ),
                }
            )
        else:
            # Add all items
            self.add_items(items)
        # Connect the custom function if needed
        if custom_func is not None:
            try:
                self.selection_changed.disconnect()
            except:
                pass
            self.selection_changed.connect(custom_func)
        # Select previously selected item if needed
        if not reset_selection:
            if selected_item_name in self.item_cache.keys():
                self.set_selected_name(selected_item_name)


class Window(qt.QWidget):
    def __init__(self):
        super().__init__()

        layout = qt.QVBoxLayout(self)
        self.setLayout(layout)

        def delete_acb(*args):
            def clean_all():
                for i in reversed(range(self.layout().count())):
                    widget: Union[
                        qt.QWidget,
                        AdvancedComboBoxItem,
                        AdvancedComboBoxMenu,
                    ] = (
                        self.layout().itemAt(i).widget()
                    )
                    if hasattr(widget, "self_destruct"):
                        widget.self_destruct()
                    else:
                        widget.deleteLater()
                        widget.setParent(None)
                    del widget
                gc.collect()

            for i in range(1000):
                clean_all()

                test()

                self.adjustSize()
                gc.collect()
                functions.process_events()

            clean_all()
            self.adjustSize()
            for i in range(50):
                gc.collect()
                functions.process_events()

        def test():
            button = gui.helpers.buttons.CustomPushButton(text="DELETE ACBs")
            button.set_click_function(delete_acb)
            self.layout().addWidget(button)

            for i in range(1):
                acb = AdvancedComboBox(
                    parent=self,
                    contents_margins=(2, 2, 2, 2),
                    spacing=4,
                    no_selection_text="EMPTY AdvancedComboBox",
                )

                for i in range(100):
                    if i == 5 or i == 6 or i == 7:
                        acb.add_item(
                            {
                                "name": f"item-{i}",
                                "widgets": (
                                    {
                                        "type": "image",
                                        "icon-path": (
                                            "icons/chip/chip_protocol.png"
                                        ),
                                    },
                                    {
                                        "type": "image",
                                        "icon-path": (
                                            "icons/chip/chip_protocol(dis).png"
                                        ),
                                    },
                                    {
                                        "type": "text",
                                        "text": "some text" * (i + 1),
                                    },
                                    {
                                        "type": "image",
                                        "icon-path": (
                                            "icons/chip/chip_protocol(dis).png"
                                        ),
                                    },
                                    {
                                        "type": "image",
                                        "icon-path": (
                                            "icons/chip/chip_protocol.png"
                                        ),
                                    },
                                ),
                                "subitems": (
                                    {
                                        "name": f"sub-item-{i}",
                                        "widgets": (
                                            {
                                                "type": "image",
                                                "icon-path": (
                                                    "icons/chip/chip_protocol.png"
                                                ),
                                            },
                                            {
                                                "type": "image",
                                                "icon-path": (
                                                    "icons/chip/chip_protocol(dis).png"
                                                ),
                                            },
                                            {
                                                "type": "text",
                                                "text": (
                                                    "some sub text" * (i + 1)
                                                ),
                                                "color": "red",
                                                "bold": True,
                                            },
                                        ),
                                    },
                                    {
                                        "name": f"ssub-item-{i}",
                                        "widgets": (
                                            {
                                                "type": "image",
                                                "icon-path": (
                                                    "icons/chip/chip_protocol.png"
                                                ),
                                            },
                                            {
                                                "type": "image",
                                                "icon-path": (
                                                    "icons/chip/chip_protocol(dis).png"
                                                ),
                                            },
                                            {
                                                "type": "text",
                                                "text": (
                                                    "some ssub text" * (i + 1)
                                                ),
                                                "color": "blue",
                                                "bold": True,
                                            },
                                        ),
                                    },
                                ),
                            }
                        )
                    elif i == 8:
                        acb.add_item(
                            {
                                "name": f"item-{i}",
                                "widgets": (
                                    {
                                        "type": "image",
                                        "icon-path": (
                                            "icons/chip/chip_protocol.png"
                                        ),
                                    },
                                    {
                                        "type": "image",
                                        "icon-path": (
                                            "icons/chip/chip_protocol(dis).png"
                                        ),
                                    },
                                    {
                                        "type": "text",
                                        "text": "some text" * (i + 1),
                                        "color": "red",
                                        "bold": True,
                                    },
                                ),
                            }
                        )
                    elif i == 9:
                        acb.add_item(
                            {
                                "name": f"item-{i}",
                                "widgets": (
                                    {
                                        "type": "image",
                                        "icon-path": (
                                            "icons/chip/chip_protocol.png"
                                        ),
                                    },
                                    {
                                        "type": "image",
                                        "icon-path": (
                                            "icons/chip/chip_protocol(dis).png"
                                        ),
                                    },
                                    {
                                        "type": "text",
                                        "text": "some text" * (i + 1),
                                    },
                                    {
                                        "type": "image",
                                        "icon-path": (
                                            "icons/chip/chip_protocol(dis).png"
                                        ),
                                    },
                                    {
                                        "type": "image",
                                        "icon-path": (
                                            "icons/chip/chip_protocol.png"
                                        ),
                                    },
                                ),
                            }
                        )
                    else:
                        acb.add_item(
                            {
                                "name": f"item-{i}",
                                "widgets": (
                                    {
                                        "type": "image",
                                        "icon-path": (
                                            "icons/chip/chip_protocol.png"
                                        ),
                                    },
                                    {
                                        "type": "image",
                                        "icon-path": (
                                            "icons/chip/chip_protocol(dis).png"
                                        ),
                                    },
                                    {
                                        "type": "text",
                                        "text": "some text" * (i + 1),
                                    },
                                ),
                            }
                        )

                self.layout().addWidget(acb)
                #                acb.selection_changed.connect(lambda name, item: print("clicked:", name))
                #                acb.setEnabled(False)

                def print_current_selection(*args):
                    print(acb.get_selected_item_name())

                button = gui.helpers.buttons.CustomPushButton(
                    text="PRINT CURRENT SELECTION NAME"
                )
                button.set_click_function(print_current_selection)
                self.layout().addWidget(button)

            acb.update_style(
                data.get_general_icon_pixelsize() * 2, data.get_editor_font()
            )

            acb.change_item(
                "item-0",
                {
                    "name": f"item-0",
                    "widgets": (
                        {
                            "type": "image",
                            "icon-path": "icons/chip/chip_protocol.png",
                        },
                        {
                            "type": "image",
                            "icon-path": "icons/chip/chip_protocol(dis).png",
                        },
                        {"type": "text", "text": "CHANGED ItEm"},
                    ),
                },
            )

            acb.add_item(
                {
                    "name": f"item-222",
                    "widgets": (
                        {
                            "type": "image",
                            "icon-path": "icons/chip/chip_protocol.png",
                        },
                        {
                            "type": "image",
                            "icon-path": "icons/chip/chip_protocol(dis).png",
                        },
                        {"type": "text", "text": "INSERTED ITEM"},
                    ),
                },
                insert_before_item="ssub-item-5",
            )

        test()


#            button = gui.helpers.buttons.CustomPushButton(text="CHANGE ITEM")
#            def change_acb_item(*args):
#                new_item = {
#                    "name": f"changed_item",
#                    "widgets":
#                        (
#                            {"type": "image", "icon-path": "icons/gen/clean.png"},
#                            {"type": "image", "icon-path": "icons/gen/clean(dis).png"},
#                            {"type": "text", "text": "CHANGED ITEM"},
#                        )
#                }
#                acb.change_item(3, new_item)
#            button.set_click_function(change_acb_item)
#            layout.addWidget(button)

#        button = gui.helpers.buttons.CustomPushButton(text="DELETE ACBs")
#        def delete_acb(*args):
#            for acb in self.acbs:
#                acb.self_destruct()
#        button.set_click_function(delete_acb)
#        layout.addWidget(button)


def test_acb(app):
    window = Window()
    window.show()
    sys.exit(app.exec())
