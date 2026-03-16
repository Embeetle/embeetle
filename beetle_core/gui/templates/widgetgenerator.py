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
import os
import functools
import qt
import data
import purefunctions
import iconfunctions
import gui.helpers.buttons
import gui.helpers.simplecombobox
import gui.helpers.advancedcombobox
import gui.stylesheets.textbox
import gui.stylesheets.groupbox
import gui.stylesheets.button
import gui.stylesheets.label
import gui.stylesheets.table
import gui.stylesheets.scrollbar
import gui.stylesheets.tooltip

if TYPE_CHECKING:
    import gui.forms
    import gui.forms.tabwidget


class Label(qt.QLabel):
    click_signal = qt.pyqtSignal()
    right_click_signal = qt.pyqtSignal()

    text_color = None
    background_color = None

    def __init__(self, parent: qt.QWidget, image: Optional[str] = None) -> None:
        """ """
        super().__init__(parent)
        self.__image: Optional[str] = image
        self.__image_width: Optional[int] = None
        self.__image_height: Optional[int] = None
        return

    def set_image(
        self,
        image: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        """Set image of this Label"""
        if qt.sip.isdeleted(self):
            return
        self.__image = image
        self.__image_width = width
        self.__image_height = height
        super().setPixmap(
            iconfunctions.get_qpixmap(
                pixmap_relpath=image,
                width=width,
                height=height,
            )
        )
        self.setScaledContents(True)
        return

    def setPixmap(self, *args, **kwargs) -> None:
        """Override setPixmap to show warning: a direct call to setPixmap() must
        be avoided because it skips storing the image path in `self.__image`.
        That leads to problems when a theme change is invoked. Refreshing the
        image won't give correct result.
        """
        if qt.sip.isdeleted(self):
            return
        super().setPixmap(*args, **kwargs)
        print(
            f"WARNING: direct call to setPixmap on Label() for {self.__image}"
        )
        return

    def mouseReleaseEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == qt.Qt.MouseButton.RightButton:
            self.right_click_signal.emit()
        elif event.button() == qt.Qt.MouseButton.LeftButton:
            self.click_signal.emit()
        return

    def set_colors(
        self,
        text_color=None,
        background_color="transparent",
    ) -> None:
        """

        :param text_color:
        :param background_color:
        :return:
        """
        self.text_color = text_color
        self.background_color = background_color
        self.update_style()
        return

    def __update_style_sheet(self) -> None:
        """

        :return:
        """
        font_colors = data.theme["fonts"]["default"]
        color = self.text_color
        if color is None:
            color = font_colors["color"]
        background = self.background_color
        if background is None:
            background = font_colors["background"]
        style_sheet = f"""
            {gui.stylesheets.label.get_default()}
            QLabel {{
                color: {color};
                background: {background};
            }}
        """
        self.setStyleSheet(style_sheet)
        return

    def update_style(self) -> None:
        """ """
        if qt.sip.isdeleted(self):
            return
        font = data.get_general_font()
        self.setFont(font)
        self.__update_style_sheet()
        return

    def update_icon_style(self) -> None:
        """This method should run after a theme change, because then the icon
        can be changed as well. I don't put this code into the general method
        `update_style()`, because I have the impression that method even runs
        without a theme change!
        """
        # Test for qt.sip.isdeleted(self) already happens in the set_image()
        # method.
        if self.__image:
            self.set_image(
                image=self.__image,
                width=self.__image_width,
                height=self.__image_height,
            )
        return

    def self_destruct(self) -> None:
        """Properly destroy this widget"""


class LabelFixedAspect(Label):
    def sizeHint(self):
        return self.minimumSize() * 1.5

    def minimumSizeHint(self):
        return self.minimumSize()

    def paintEvent(self, event):
        size = self.size()
        painter = qt.QPainter(self)
        scaledPix = self.pixmap().scaled(
            size,
            qt.Qt.AspectRatioMode.KeepAspectRatio,
            transformMode=qt.Qt.TransformationMode.SmoothTransformation,
        )
        w = (size.width() - scaledPix.width()) / 2
        if w < 0:
            w = 0
        h = (size.height() - scaledPix.height()) / 2
        if h < 0:
            h = 0
        point = qt.create_qpoint(w, h)
        painter.drawPixmap(point, scaledPix)


class StandardTable(qt.QTableWidget):
    combobox_item_changed = qt.pyqtSignal(int, int, int, object, object)

    def __init__(self, parent):
        super().__init__(parent=None)

        self.horizontalHeader().setSectionResizeMode(
            qt.QHeaderView.ResizeMode.ResizeToContents
        )
        # Set the stylesheets
        self.setStyleSheet(gui.stylesheets.table.get_default_style())
        self.horizontalScrollBar().setStyleSheet(
            gui.stylesheets.scrollbar.get_horizontal()
        )
        self.verticalScrollBar().setStyleSheet(
            gui.stylesheets.scrollbar.get_vertical()
        )
        self.verticalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.horizontalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )

    def set_headers(self, headers):
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

    def set_row_enabled(self, row: int, enabled: bool) -> None:
        if enabled:
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if item:
                    item.setFlags(item.flags() | qt.Qt.ItemFlag.ItemIsEnabled)
                cell_widget = self.cellWidget(row, column)
                if cell_widget and hasattr(cell_widget, "enable"):
                    cell_widget.setEnabled(True)
        else:
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if item:
                    item.setFlags(item.flags() & ~qt.Qt.ItemFlag.ItemIsEnabled)
                cell_widget = self.cellWidget(row, column)
                if cell_widget and hasattr(cell_widget, "disable"):
                    cell_widget.setDisabled(True)

    def set_row_editable(self, row: int, editable: bool) -> None:
        if editable:
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if item:
                    item.setFlags(item.flags() | qt.Qt.ItemFlag.ItemIsEditable)
        else:
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if item:
                    item.setFlags(item.flags() & ~qt.Qt.ItemFlag.ItemIsEditable)

    def add_row(self, row_data):
        self.setSortingEnabled(False)
        self.insertRow(self.rowCount())
        new_index = self.rowCount() - 1
        self.create_row(new_index, row_data)
        self.setSortingEnabled(True)

    def set_rows(self, rows_data):
        self.setSortingEnabled(False)
        self.setUpdatesEnabled(False)
        self.setRowCount(len(rows_data))
        for i, r in enumerate(rows_data):
            self.create_row(i, r)
        self.setSortingEnabled(True)
        self.setUpdatesEnabled(True)
        self.viewport().update()

    def create_row(self, row_index, row_data):
        for i, item in enumerate(row_data):
            if isinstance(item, dict):
                _type = item["type"]

                if _type == "string":
                    self.setItem(
                        row_index, i, qt.QTableWidgetItem(item["text"])
                    )
                    if "readonly" in item.keys():
                        cell = self.item(row_index, i)
                        if item["readonly"]:
                            cell.setFlags(
                                cell.flags() & ~qt.Qt.ItemFlag.ItemIsEditable
                            )
                        else:
                            cell.setFlags(
                                cell.flags() | qt.Qt.ItemFlag.ItemIsEditable
                            )

                elif _type == "project-table-item":
                    widget = qt.QWidget()
                    layout: qt.QHBoxLayout = cast(
                        qt.QHBoxLayout,
                        create_layout(
                            vertical=False,
                            margins=(5, 0, 5, 0),
                        ),
                    )
                    label = create_label(
                        parent=self,
                        text='<a href="click"  style="color: #729fcf;">More ...</a>',
                    )
                    label.linkActivated.connect(
                        functools.partial(
                            item["info_func"],
                            item["name"],
                            item["chip"],
                            item["info"],
                        )
                    )
                    layout.addWidget(label)
                    widget.setLayout(layout)
                    self.setCellWidget(row_index, i, widget)

                elif _type == "combobox-item":
                    new_combobox = create_combobox(parent=self)
                    for k, v in zip(item["keys"], item["values"]):
                        new_combobox.addItem(k, v)
                    if "text" in item.keys():
                        new_combobox.setCurrentText(item["text"])
                    new_combobox.user_index_changed_signal.connect(
                        functools.partial(
                            self.__combobox_item_changed,
                            row_index,
                            i,
                            new_combobox,
                        )
                    )
                    new_combobox.setSizeAdjustPolicy(
                        qt.QComboBox.SizeAdjustPolicy.AdjustToContents
                    )
                    new_combobox.setSizePolicy(
                        qt.QSizePolicy.Policy.Expanding,
                        qt.QSizePolicy.Policy.Expanding,
                    )
                    new_combobox.setContentsMargins(0, 0, 0, 0)

                    self.setCellWidget(row_index, i, new_combobox)

                else:
                    raise Exception(
                        f"[Table] Unknown dict item type: '{_type}'"
                    )

            elif isinstance(item, str):
                self.setItem(row_index, i, qt.QTableWidgetItem(item))

            elif isinstance(item, tuple):
                self.setItem(row_index, i, qt.QTableWidgetItem(*item))

            else:
                raise Exception(f"[Table] Unknown item type: '{item}'")

    def set_row(self, row_index, row_data):
        for i, item in enumerate(row_data):
            if isinstance(item, dict):
                _type = item["type"]

                if _type == "string":
                    cell = self.item(row_index, i)
                    cell.setText(item["text"])
                    if "readonly" in item.keys():
                        if item["readonly"]:
                            cell.setFlags(
                                cell.flags() & ~qt.Qt.ItemFlag.ItemIsEditable
                            )
                        else:
                            cell.setFlags(
                                cell.flags() | qt.Qt.ItemFlag.ItemIsEditable
                            )

                elif _type == "project-table-item":
                    widget = self.cellWidget(row_index, i)
                    label = widget.layout().itemAt(0)
                    label.setText(
                        '<a href="click"  style="color: #729fcf;">More ...</a>'
                    )
                    label.linkActivated.disconnect()
                    label.linkActivated.connect(
                        functools.partial(
                            item["info_func"],
                            item["name"],
                            item["chip"],
                            item["info"],
                        )
                    )

                elif _type == "combobox-item":
                    combobox = self.cellWidget(row_index, i)
                    combobox.clear()
                    for k, v in zip(item["keys"], item["values"]):
                        combobox.addItem(k, v)
                    if "text" in item.keys():
                        combobox.setCurrentText(item["text"])

                else:
                    raise Exception(
                        f"[Table] Unknown dict item type: '{_type}'"
                    )

            elif isinstance(item, str):
                cell = self.item(row_index, i)
                cell.setText(item)

            elif isinstance(item, tuple):
                self.setItem(row_index, i, qt.QTableWidgetItem(*item))

            else:
                raise Exception(f"[Table] Unknown item type: '{item}'")

    def __combobox_item_changed(
        self, row: int, column: int, combobox: object, index: int
    ) -> None:
        self.combobox_item_changed.emit(row, column, index, combobox, self)

    def adjust_height(self, compensate_scrollbar=False):
        self.resizeRowsToContents()
        self.resizeColumnsToContents()
        total_height = self.horizontalHeader().height()
        for row in range(self.rowCount()):
            total_height += self.rowHeight(row)
        total_height += int(total_height * 0.05)
        if compensate_scrollbar:
            total_height += int(gui.stylesheets.scrollbar.get_bar_width() * 1.2)
        # Set the fixed height of the table widget
        self.setFixedHeight(total_height)

    def clean(self):
        self.clear()
        self.setRowCount(0)
        self.setColumnCount(0)

    def scrollbar_compensation_check(self) -> None:
        # Check if the horizontal scrollbar is visible
        horizontal_visible = self.horizontalScrollBar().isVisible()
        # Check if the vertical scrollbar is visible
        vertical_visible = self.verticalScrollBar().isVisible()
        if horizontal_visible or vertical_visible:
            self.adjust_height(compensate_scrollbar=True)
        else:
            self.adjust_height(compensate_scrollbar=False)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.scrollbar_compensation_check()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.scrollbar_compensation_check()


class PlaceHolderWidget(qt.QWidget):
    child = None

    def __init__(self, *args, creation_routine=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.creation_routine = creation_routine

    def replace(self):
        if self.layout().count() == 0:
            if self.creation_routine is not None:
                self.child = self.creation_routine()
                self.layout().addWidget(self.child)


class TextBox(qt.QLineEdit):
    key_release_signal = qt.pyqtSignal(int)

    def __init__(self, parent, no_border) -> None:
        """ """
        super().__init__(parent)
        self.__no_border = no_border
        return

    def keyReleaseEvent(self, event):
        """ """
        self.key_release_signal.emit(event.key())
        return super().keyReleaseEvent(event)

    def update_style(self) -> None:
        """ """
        if qt.sip.isdeleted(self):
            return
        self.setFont(data.get_general_font())
        self.setStyleSheet(
            gui.stylesheets.textbox.get_default(no_border=self.__no_border)
        )
        return


class BaseGroupBox(qt.QGroupBox):
    mouse_release_signal = qt.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.installEventFilter(self)

    def eventFilter(self, receiver, event):
        if event.type() == qt.QEvent.Type.MouseButtonRelease:
            self.mouse_release_signal.emit()
        return super().eventFilter(receiver, event)


def create_table(parent: Optional[qt.QWidget] = None) -> StandardTable:
    table = StandardTable(parent)
    return table


def create_spacer(
    fixed_width: Optional[int] = None, fixed_height: Optional[int] = None
) -> qt.QWidget:
    policy = qt.QSizePolicy.Policy.Expanding
    if fixed_width is not None or fixed_height is not None:
        policy = qt.QSizePolicy.Policy.Fixed
    spacer = qt.QWidget()
    spacer.setSizePolicy(policy, policy)
    if fixed_width is not None:
        spacer.setFixedWidth(int(fixed_width))
    if fixed_height is not None:
        spacer.setFixedHeight(int(fixed_height))
    return spacer


def create_action(
    parent: Optional[qt.QWidget],
    name: str,
    statustip: str,
    tooltip: str,
    icon_path: Optional[str],
    func: Callable[[], None],
    ribbon_style: bool = False,
    text: str = "",
) -> Union[qt.QAction, qt.QWidgetAction]:
    """"""
    new_action = qt.QAction()
    new_action.setObjectName(name)
    new_action.setText(text)
    new_action.setStatusTip(statustip)
    new_action.setToolTip(tooltip)
    new_action.triggered.connect(func)
    new_action.setIcon(iconfunctions.get_qicon(icon_path))

    def set_enabled(state):
        new_action.setEnabled(state)

    new_action.set_enabled = set_enabled

    def reset_icon():
        if icon_path is None:
            return
        new_action.setIcon(iconfunctions.get_qicon(icon_path))

    new_action.reset_icon = reset_icon
    return new_action


def create_toolbar_combobox(
    parent: Optional[qt.QWidget],
    name: str,
    statustip: str,
    tooltip: str,
    ribbon_style: bool = False,
    text: str = "",
) -> qt.QWidgetAction:
    """

    :param parent:
    :param name:
    :param statustip:
    :param tooltip:
    :param ribbon_style:
    :param text:
    :return:
    """
    # Combobox
    module = purefunctions.import_module("gui.helpers.advancedcombobox")
    acb = module.AdvancedComboBox(
        parent=parent,
        contents_margins=(2, 2, 2, 2),
        spacing=1,
        no_selection_text="select port",
        fixed_height=False,
    )
    new_action = qt.QWidgetAction(parent)
    new_action.setObjectName(name)
    new_action.setStatusTip(statustip)
    new_action.setToolTip(tooltip)
    gb = create_groupbox_with_layout(
        name=name + "_groupbox",
        vertical=True,
        borderless=True,
        spacing=0,
        margins=(0, 0, 0, 0),
        h_size_policy=qt.QSizePolicy.Policy.Minimum,
        v_size_policy=qt.QSizePolicy.Policy.Expanding,
        parent=parent,
    )
    gb.setStatusTip(statustip)
    gb.setToolTip(tooltip)

    # Combobox
    gb.layout().addWidget(acb)
    gb.layout().setAlignment(
        acb, qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
    )
    new_action.acb = acb

    # Text
    if ribbon_style:
        text = create_label(text=text, selectable_text=False)
        text.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        text.set_colors()
        text.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Expanding,
        )
        gb.layout().addWidget(text)
        gb.layout().setAlignment(
            text,
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter,
        )

    def resize():
        acb_size = data.get_custom_tab_pixelsize() * 1.2
        if ribbon_style:
            text.setFont(data.get_general_font())
            acb_size = data.get_toolbar_pixelsize() * 2
        acb.update_style(acb_size, data.get_editor_font())

    gb.resize = resize
    new_action.setDefaultWidget(gb)
    new_action.setEnabled(True)
    new_action.resize = gb.resize
    return new_action


def create_groupbox(
    name: str,
    text: str,
    parent: Optional[qt.QWidget] = None,
    override_margin_top: Optional[int] = None,
) -> BaseGroupBox:
    """"""
    groupbox = BaseGroupBox(text, parent)
    groupbox.setObjectName(name)

    def update_style() -> None:
        stylesheet = gui.stylesheets.groupbox.get_default()
        groupbox.setStyleSheet(stylesheet)
        return

    groupbox.update_style = update_style
    groupbox.update_style()
    return groupbox


def create_borderless_groupbox(
    name: Optional[str] = None,
    parent: Optional[qt.QWidget] = None,
    transparent_background: bool = True,
) -> BaseGroupBox:
    """"""
    group_box = BaseGroupBox(parent)
    if parent:
        group_box.setParent(parent)
    if name:
        group_box.setObjectName(name)

    def update_style() -> None:
        background = "transparent"
        if not transparent_background:
            background = data.theme["fonts"]["default"]["background"]
        stylesheet = gui.stylesheets.groupbox.get_noborder_style(
            background_color=background
        )
        group_box.setStyleSheet(stylesheet)

    group_box.update_style = update_style
    group_box.update_style()
    return group_box


def create_frame(
    name: Optional[str] = None,
    parent: Optional[qt.QWidget] = None,
    layout: Optional[qt.QLayout] = None,
    layout_vertical: bool = False,
    layout_margins: Tuple[int, int, int, int] = (0, 0, 0, 0),
    layout_spacing: int = 0,
    layout_size_constraing: qt.QLayout.SizeConstraint = qt.QLayout.SizeConstraint.SetDefaultConstraint,
) -> qt.QFrame:
    """"""
    new_frame = qt.QFrame(parent)
    if name is not None:
        new_frame.setObjectName(name)
    if layout is None:
        if layout_vertical:
            new_layout = qt.QVBoxLayout(new_frame)
        else:
            new_layout = qt.QHBoxLayout(new_frame)
        new_layout.setContentsMargins(*layout_margins)
        new_layout.setSpacing(layout_spacing)
        new_layout.setSizeConstraint(layout_size_constraing)
        new_frame.setLayout(new_layout)
    else:
        new_frame.setLayout(layout)
    return new_frame


def create_placeholder(
    vertical: Union[bool, str] = False,
    spacing: int = 0,
    margins: Tuple[int, int, int, int] = (0, 0, 0, 0),
    parent: Optional[qt.QWidget] = None,
    creation_routine: Optional[Callable[[], qt.QWidget]] = None,
    name: Optional[str] = None,
    icon: Optional[str] = None,
) -> PlaceHolderWidget:
    placeholder = PlaceHolderWidget(
        parent,
        creation_routine=creation_routine,
    )
    if vertical == True:
        new_layout = qt.QVBoxLayout(parent)
    elif vertical == "grid":
        new_layout = qt.QGridLayout(parent)
    elif vertical == "stack":
        new_layout = qt.QStackedLayout(parent)
    else:
        new_layout = qt.QHBoxLayout(parent)
    new_layout.setSpacing(int(spacing))
    new_layout.setContentsMargins(*(int(x) for x in margins))
    placeholder.setLayout(new_layout)
    if name:
        placeholder.setObjectName(name)
    if icon:
        placeholder.current_icon = icon
    return placeholder


def create_layout(
    vertical: Union[bool, str] = False,
    spacing: int = 0,
    margins: Tuple[int, int, int, int] = (0, 0, 0, 0),
    parent: Optional[qt.QWidget] = None,
) -> Union[qt.QHBoxLayout, qt.QVBoxLayout, qt.QGridLayout, qt.QStackedLayout]:
    """
    :param vertical:    True    -> qt.QVBoxLayout
                        False   -> qt.QHBoxLayout
                        'grid'  -> qt.QGridLayout
                        'stack' -> qt.QStackedLayout
    :param spacing:
    :param margins:
    :param parent:
    :return:
    """
    # $ CASE 1: vertical == True
    if isinstance(vertical, bool) and vertical:
        assert vertical == True
        new_layout = qt.QVBoxLayout(parent)

    # $ CASE 2: vertical == 'grid'
    elif vertical == "grid":
        new_layout = qt.QGridLayout(parent)

    # $ CASE 3: vertical == 'stack'
    elif vertical == "stack":
        new_layout = qt.QStackedLayout(parent)

    # $ CASE 4: vertical == False (default case)
    else:
        assert vertical == False
        new_layout = qt.QHBoxLayout(parent)

    new_layout.setSpacing(int(spacing))
    new_layout.setContentsMargins(*(int(x) for x in margins))
    return new_layout


def create_scroll_area() -> qt.QScrollArea:
    scroll_area = qt.QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setHorizontalScrollBarPolicy(
        qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded
    )
    scroll_area.verticalScrollBar().setContextMenuPolicy(
        qt.Qt.ContextMenuPolicy.NoContextMenu
    )
    scroll_area.horizontalScrollBar().setContextMenuPolicy(
        qt.Qt.ContextMenuPolicy.NoContextMenu
    )
    scroll_area.setFrameShape(qt.QFrame.Shape.NoFrame)
    return scroll_area


def create_groupbox_with_layout(
    name: Optional[str] = None,
    text: Optional[str] = None,
    vertical: Union[bool, str] = True,
    borderless: bool = False,
    background_color: Optional[str] = None,
    spacing: Optional[int] = None,
    margins: Optional[Tuple[int, int, int, int]] = None,
    h_size_policy: qt.QSizePolicy.Policy = qt.QSizePolicy.Policy.Expanding,
    v_size_policy: qt.QSizePolicy.Policy = qt.QSizePolicy.Policy.Minimum,
    adjust_margins_to_text: bool = False,
    parent: Optional[qt.QWidget] = None,
    override_margin_top: Optional[int] = None,
) -> BaseGroupBox:
    """
    :param vertical:    True    -> qt.QVBoxLayout
                        False   -> qt.QHBoxLayout
                        'grid'  -> qt.QGridLayout
                        'stack' -> qt.QStackedLayout
    """
    groupbox: Optional[qt.QGroupBox] = None
    if borderless:
        groupbox = create_borderless_groupbox(name, parent=parent)
    else:
        groupbox = create_groupbox(
            name, text, parent=parent, override_margin_top=override_margin_top
        )
    groupbox.setLayout(create_layout(vertical=vertical))
    if background_color is not None:
        groupbox.setStyleSheet(
            f"""
            background: {background_color};
        """
        )
    groupbox.setSizePolicy(qt.QSizePolicy(h_size_policy, v_size_policy))
    if spacing is not None:
        groupbox.layout().setSpacing(int(spacing))
    if margins is not None:
        groupbox.layout().setContentsMargins(*(int(x) for x in margins))
    if adjust_margins_to_text != False:
        fm = qt.QFontMetrics(data.get_general_font())
        font_height = fm.height() / 2
        margins = groupbox.layout().contentsMargins()
        groupbox.layout().setContentsMargins(
            int(margins.left()),
            int(margins.top() + font_height),
            int(margins.right()),
            int(margins.bottom()),
        )
    return groupbox


def create_groupbox_with_layout_and_info_button(
    name: Optional[str] = None,
    text: Optional[str] = None,
    vertical: Union[bool, str] = True,
    borderless: bool = True,
    background_color: Optional[str] = None,
    spacing: Optional[int] = None,
    margins: Optional[Tuple[int, int, int, int]] = None,
    h_size_policy: qt.QSizePolicy.Policy = qt.QSizePolicy.Policy.Expanding,
    v_size_policy: qt.QSizePolicy.Policy = qt.QSizePolicy.Policy.Minimum,
    adjust_margins_to_text: bool = False,
    info_size: Optional[int] = None,
    info_func: Optional[Callable[[], None]] = None,
    parent: Optional[qt.QWidget] = None,
) -> BaseGroupBox:
    wrapper_box = create_borderless_groupbox("WrapperBox", parent)
    wrapper_box.setSizePolicy(
        qt.QSizePolicy.Policy.Minimum, qt.QSizePolicy.Policy.Minimum
    )
    wrapper_box.setLayout(qt.QVBoxLayout())
    wrapper_box.layout().setSpacing(0)
    wrapper_box.layout().setContentsMargins(0, 0, 0, 0)

    # Groupbox
    margin = data.get_general_icon_pixelsize() * 0.5
    groupbox = create_groupbox_with_layout(
        name=f"{name}-groupbox",
        text="",
        vertical=vertical,
        borderless=borderless,
        background_color=background_color,
        spacing=5,
        margins=(int(margin), int(margin / 2), int(margin / 2), int(margin)),
        h_size_policy=qt.QSizePolicy.Policy.Minimum,
        v_size_policy=qt.QSizePolicy.Policy.Minimum,
        adjust_margins_to_text=False,
        parent=wrapper_box,
    )

    # Title
    margin = data.get_general_icon_pixelsize() * 0.3
    title_box = create_groupbox_with_layout(
        f"{name}-titlebox",
        vertical=False,
        borderless=True,
        spacing=0,
        margins=(int(margin), 0, 0, 0),
        parent=wrapper_box,
        h_size_policy=qt.QSizePolicy.Policy.Fixed,
        v_size_policy=qt.QSizePolicy.Policy.Fixed,
    )
    label = create_label(text, bold=True, parent=title_box)
    label.setSizePolicy(
        qt.QSizePolicy.Policy.Minimum, qt.QSizePolicy.Policy.Minimum
    )
    label.setFixedHeight(int(label.sizeHint().height()))
    spacing = data.get_general_icon_pixelsize() * 0.1
    title_box.layout().setSpacing(int(spacing))
    title_box.layout().addWidget(label)
    info_button = gui.helpers.buttons.CustomPushButton(
        parent=title_box,
        icon_path="icons/dialog/help.png",
        icon_size=qt.create_qsize(info_size - 4, info_size - 4),
        align_text=None,
        padding="0px",
    )
    info_button.setFixedSize(int(info_size), int(info_size))
    if info_func is not None:
        info_button.clicked.connect(info_func)
    title_box.layout().addWidget(info_button)

    title_box.layout().setAlignment(
        label, qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
    )
    title_box.layout().setAlignment(
        info_button,
        qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter,
    )
    title_box.layout().setSizeConstraint(qt.QLayout.SizeConstraint.SetFixedSize)

    wrapper_box.layout().addWidget(title_box)
    wrapper_box.layout().addWidget(groupbox)
    wrapper_box.title_box = title_box
    wrapper_box.group_box = groupbox
    wrapper_box.layout = lambda: groupbox.layout()
    return wrapper_box


def create_info_button(
    parent: qt.QWidget,
    size: int,
    icon: str = "icons/dialog/help.png",
    func: Optional[Callable[[], None]] = None,
) -> gui.helpers.buttons.CustomPushButton:
    info_button = gui.helpers.buttons.CustomPushButton(
        parent=parent,
        icon_path=icon,
        icon_size=qt.create_qsize(size, size),
        align_text=None,
        padding="0px",
    )
    info_button.setFixedSize(int(size * 1.1), int(size * 1.1))
    if func is not None:
        info_button.clicked.connect(func)
    return info_button


def create_pushbutton(
    parent: Optional[qt.QWidget] = None,
    name: Optional[str] = None,
    icon_name: Optional[str] = None,
    icon: Optional[qt.QIcon] = None,
    size: Optional[Union[qt.QSize, Tuple[int, int]]] = None,
    checkable: bool = False,
    click_func: Optional[Callable[[], None]] = None,
    text: Optional[str] = None,
    style: str = "standard",
    tooltip: Optional[str] = None,
    statustip: Optional[str] = None,
    popup_bubble_parent: Optional[qt.QWidget] = None,
    no_border: bool = False,
    disabled: bool = False,
) -> gui.helpers.buttons.CustomPushButton:
    """ """
    button = gui.helpers.buttons.CustomPushButton(
        parent=parent,
        icon_path=icon_name,
        icon_size=size,
        icon=icon,
        text=text,
        style=style,
        statustip=statustip,
        popup_bubble_parent=popup_bubble_parent,
        no_border=no_border,
        disabled=disabled,
    )
    button.setObjectName(name)
    if checkable:
        button.setCheckable(True)
    if statustip is None and tooltip is not None:
        statustip = tooltip
    elif statustip is not None and tooltip is None:
        tooltip = statustip
    if tooltip is not None:
        button.setToolTip(tooltip)
        button.setStatusTip(tooltip)
    if statustip is not None:
        button.setStatusTip(statustip)
    if click_func:
        button.released.connect(click_func)
    return button


def create_alert_groupbox_with_button(
    text: str,
    bold: bool,
    tooltip: str,
    style: str,
    click_func: Callable[[], None],
    parent: Optional[qt.QWidget] = None,
    statusbar: Optional[qt.QStatusBar] = None,
) -> BaseGroupBox:
    button = create_pushbutton(
        parent=parent,
        name="alert_button",
        tooltip=tooltip,
        text=text,
        click_func=click_func,
    )
    button.setStyleSheet(
        gui.stylesheets.button.get_simple_toggle_stylesheet(
            style=style, bold=bold
        )
    )
    button.setSizePolicy(
        qt.QSizePolicy(
            qt.QSizePolicy.Policy.Minimum, qt.QSizePolicy.Policy.Minimum
        )
    )
    button.setFixedHeight(int(data.get_custom_tab_pixelsize() * 1.5))
    gb = create_groupbox_with_layout(
        vertical=False,
        borderless=True,
        h_size_policy=qt.QSizePolicy.Policy.Minimum,
    )
    gb.layout().setContentsMargins(5, 5, 5, 5)
    gb.layout().addWidget(button)
    gb.button = button
    original_update_func = gb.update_style

    def _update_style(*args):
        original_update_func()
        button.setStyleSheet(
            gui.stylesheets.button.get_simple_toggle_stylesheet(
                style=style, bold=bold
            )
        )
        button.setFixedHeight(int(data.get_custom_tab_pixelsize() * 1.5))

    gb.update_style = _update_style
    return gb


def create_combobox(
    parent: Optional[qt.QWidget] = None,
) -> gui.helpers.simplecombobox.SimpleComboBox:
    """"""
    return gui.helpers.simplecombobox.SimpleComboBox(parent=parent)


def create_advancedcombobox(
    **kwargs: Any,
) -> gui.helpers.advancedcombobox.AdvancedComboBox:
    """"""
    return gui.helpers.advancedcombobox.AdvancedComboBox(**kwargs)


def create_label(
    text: Optional[str] = None,
    bold: bool = False,
    image: Optional[str] = None,
    wordwrap: bool = False,
    alignment: qt.Qt.AlignmentFlag = qt.Qt.AlignmentFlag.AlignLeft
    | qt.Qt.AlignmentFlag.AlignVCenter,
    size_policy: qt.QSizePolicy = qt.QSizePolicy(
        qt.QSizePolicy.Policy.Minimum, qt.QSizePolicy.Policy.Minimum
    ),
    parent: Optional[qt.QWidget] = None,
    selectable_text: bool = True,
    tooltip: Optional[str] = None,
    statustip: Optional[str] = None,
    transparent_background: bool = False,
) -> Label:
    """

    :param text:
    :param bold:
    :param image:
    :param wordwrap:
    :param alignment:
    :param size_policy:
    :param parent:
    :param selectable_text:
    :param tooltip:
    :param statustip:
    :param transparent_background:
    :return:
    """
    label = Label(parent, image)
    if image is not None:
        label.set_image(image)
        label.setScaledContents(True)
    else:
        font = data.get_general_font()
        font.setBold(bold)
        label.setFont(font)
        label.setAlignment(alignment)
        if text is not None:
            label.setText(text)
        if wordwrap:
            label.setWordWrap(True)
    if tooltip is not None:
        label.setToolTip(tooltip)
    if statustip is not None:
        label.setStatusTip(statustip)
    label.setStyleSheet(
        gui.stylesheets.label.get_default(transparent=transparent_background)
    )
    if transparent_background:
        label.background_color = "transparent"
    label.setSizePolicy(size_policy)
    if selectable_text:
        flags = (
            qt.Qt.TextInteractionFlag.TextSelectableByMouse
            | qt.Qt.TextInteractionFlag.TextSelectableByKeyboard
            | qt.Qt.TextInteractionFlag.TextBrowserInteraction
        )
    else:
        flags = (
            ~qt.Qt.TextInteractionFlag.TextSelectableByMouse
            & ~qt.Qt.TextInteractionFlag.TextSelectableByKeyboard
            & ~qt.Qt.TextInteractionFlag.TextBrowserInteraction
        )
    label.setTextInteractionFlags(flags)
    label.setFocusPolicy(qt.Qt.FocusPolicy.NoFocus)
    return label


def create_label_fixed_aspect(
    text: Optional[str] = None,
    bold: bool = False,
    image: Optional[str] = None,
    wordwrap: bool = False,
    alignment: qt.Qt.AlignmentFlag = qt.Qt.AlignmentFlag.AlignLeft
    | qt.Qt.AlignmentFlag.AlignVCenter,
    parent: Optional[qt.QWidget] = None,
) -> LabelFixedAspect:
    label = LabelFixedAspect(parent)
    if image is not None:
        pixmap = iconfunctions.get_qpixmap(image)
        label.setPixmap(pixmap)
        label.setScaledContents(True)
    else:
        font = data.get_general_font()
        font.setBold(bold)
        label.setFont(font)
        label.setAlignment(alignment)
        if text is not None:
            label.setText(text)
        if wordwrap != False:
            label.setWordWrap(True)
    label.setTextInteractionFlags(
        qt.Qt.TextInteractionFlag.TextSelectableByMouse
        | qt.Qt.TextInteractionFlag.TextSelectableByKeyboard
        | qt.Qt.TextInteractionFlag.TextBrowserInteraction
    )
    return label


def create_checkbox(
    parent: qt.QWidget, name: str, size: Union[int, Tuple[int, int]]
) -> gui.helpers.buttons.CheckBox:
    check_box = gui.helpers.buttons.CheckBox(parent, name, size)
    return check_box


def create_standard_checkbox(
    parent: qt.QWidget, name: str, style: Optional[str] = None
) -> gui.helpers.buttons.StandardCheckBox:
    check_box = gui.helpers.buttons.StandardCheckBox(parent, name, style)
    return check_box


def create_check_label(
    name: str, size: Union[Tuple[int, int], int]
) -> qt.QLabel:
    check_label = qt.QLabel()
    check_label.setFixedSize(*(int(x) for x in size))
    icon = iconfunctions.get_qpixmap("icons/dialog/warning.png")
    check_label.setPixmap(icon)
    check_label.setScaledContents(True)
    check_label.setObjectName(name)
    return check_label


def create_textbox(
    name: str,
    func: Optional[Callable[[str], None]] = None,
    parent: Optional[qt.QWidget] = None,
    read_only: bool = False,
    enabled: bool = True,
    h_size_policy: qt.QSizePolicy.Policy = qt.QSizePolicy.Policy.Expanding,
    v_size_policy: qt.QSizePolicy.Policy = qt.QSizePolicy.Policy.Expanding,
    no_border: bool = False,
    ints_only: bool = False,
    max_length: Optional[int] = None,
) -> TextBox:
    textbox = TextBox(parent, no_border)
    textbox.setObjectName(name)
    if func is not None:
        textbox.textChanged.connect(func)
    if read_only:
        textbox.setReadOnly(True)
    if not enabled:
        textbox.setEnabled(False)
    if ints_only:
        textbox.setValidator(qt.QIntValidator())
    if max_length:
        textbox.setMaxLength(max_length)
    textbox.setSizePolicy(qt.QSizePolicy(h_size_policy, v_size_policy))
    textbox.update_style()
    return textbox


def create_file_selection_line(
    parent: Optional[qt.QWidget] = None,
    tool_tip: Optional[str] = None,
    start_directory_fallback: Optional[str] = None,
    click_func: Optional[Callable[[str], None]] = None,
    checkmarkclick_func: Optional[Callable[[], None]] = None,
    text_change_func: Optional[Callable[[str], None]] = None,
    statusbar: Optional[qt.QStatusBar] = None,
    tool_tip_checkmark: Optional[str] = None,
) -> Tuple[qt.QHBoxLayout, qt.QLineEdit, qt.QPushButton, qt.QPushButton]:
    """
    Create a horizontal 'line' of widgets:
        1. QLineEdit() widget:      file location
        2. QPushButton() widget:    file button
        3. QPushButton() widget:    green check or red cross

    Use the current QLineEdit() content as start location. If
    it's not a valid directory or file, use the fallback.

    """
    # * Widget 1
    lineedit = create_textbox(
        parent=None,
        name="StandardTextBox",
        func=text_change_func,
        h_size_policy=qt.QSizePolicy.Policy.Expanding,
        v_size_policy=qt.QSizePolicy.Policy.Expanding,
    )
    lineedit.setMinimumHeight(
        data.get_general_icon_pixelsize(),
    )

    def select_file():
        start_directory = lineedit.text()
        if not os.path.isdir(start_directory):
            start_directory = os.path.dirname(start_directory).replace(
                "\\", "/"
            )
        if not os.path.isdir(start_directory):
            start_directory = start_directory_fallback
        popupdialog_module = purefunctions.import_module(
            "gui.dialogs.popupdialog"
        )
        file_abspath = popupdialog_module.PopupDialog.choose_file(
            start_directory=start_directory,
        )
        if (file_abspath is None) or (file_abspath == ""):
            return
        file_abspath = file_abspath.replace("\\", "/")
        lineedit.setText(file_abspath)
        click_func(file_abspath)
        return

    # * Widget 2
    size = data.get_general_icon_pixelsize()
    button: gui.helpers.buttons.CustomPushButton = create_pushbutton(
        parent=None,
        name="StandardPushButton",
        tooltip=tool_tip,
        icon_name="icons/folder/open/file.png",
        size=(size, size),
        checkable=False,
        click_func=select_file,
    )
    button.setFixedSize(int(size), int(size))
    # * Widget 3
    if tool_tip_checkmark is None:
        tool_tip_checkmark = tool_tip
    checkmark: gui.helpers.buttons.CustomPushButton = create_pushbutton(
        parent=None,
        name="StandardPushButton",
        tooltip=tool_tip_checkmark,
        icon_name="icons/dialog/cross.png",
        size=(size, size),
        checkable=False,
        click_func=checkmarkclick_func,
    )
    checkmark.setFixedSize(int(size), int(size))
    # To change the icon:
    # checkmark.setIcon(
    #     iconfunctions.get_qicon('icons/dialog/checkmark.png')
    # )
    # * QHBoxLayout()
    hlyt = qt.QHBoxLayout()
    hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
    hlyt.setSpacing(5)
    hlyt.setContentsMargins(0, 0, 0, 0)
    hlyt.addWidget(lineedit)
    hlyt.addWidget(button)
    hlyt.addWidget(checkmark)
    return (hlyt, lineedit, button, checkmark)


def create_directory_selection_line(
    parent: Optional[qt.QWidget] = None,
    tool_tip: Optional[str] = None,
    start_directory_fallback: Optional[str] = None,
    click_func: Optional[Callable[[str], None]] = None,
    checkmarkclick_func: Optional[Callable[[], None]] = None,
    text_change_func: Optional[Callable[[str], None]] = None,
    statusbar: Optional[qt.QStatusBar] = None,
    tool_tip_checkmark: Optional[str] = None,
) -> Tuple[
    qt.QHBoxLayout,
    qt.QLineEdit,
    gui.helpers.buttons.CustomPushButton,
    gui.helpers.buttons.CustomPushButton,
]:
    """┌── hlyt ─────────────────────────────────────────────────┐ │
    ┌─────────────────────────────────────────┐ ┌═──┐    ╱ │ │
    └─────────────────────────────────────────┘ └───┘  ╲╱  │
    └─────────────────────────────────────────────────────────┘

    Create a horizontal 'line' of widgets:
        1. QLineEdit() widget:      directory location
        2. QPushButton() widget:    directory button
        3. QPushButton() widget:    green check or red cross

    Use the current QLineEdit() content as start directory. If
    it's not a valid directory, use the fallback.

    NOTE: This function has a wrapper in
    'beetle_core/gui/dialogs/projectcreationdialogs.py'
    """
    # * Widget 1
    lineedit = create_textbox(
        parent=None,
        name="StandardTextBox",
        func=text_change_func,
        h_size_policy=qt.QSizePolicy.Policy.Expanding,
        v_size_policy=qt.QSizePolicy.Policy.Expanding,
    )
    lineedit.setMinimumHeight(
        data.get_general_icon_pixelsize(),
    )

    def select_directory():
        start_directory = lineedit.text()
        if not os.path.isdir(start_directory):
            start_directory = start_directory_fallback
        popupdialog_module = purefunctions.import_module(
            "gui.dialogs.popupdialog"
        )
        directory_abspath = popupdialog_module.PopupDialog.choose_folder(
            start_directory=start_directory,
        )
        if (directory_abspath is None) or (directory_abspath == ""):
            return
        directory_abspath = directory_abspath.replace("\\", "/")
        lineedit.setText(directory_abspath)
        click_func(directory_abspath)
        return

    # * Widget 2
    size = data.get_general_icon_pixelsize()
    button: gui.helpers.buttons.CustomPushButton = create_pushbutton(
        parent=None,
        name="StandardPushButton",
        tooltip=tool_tip,
        icon_name="icons/folder/open/folder.png",
        size=(size, size),
        checkable=False,
        click_func=select_directory,
    )
    button.setFixedSize(int(size), int(size))
    # * Widget 3
    if tool_tip_checkmark is None:
        tool_tip_checkmark = tool_tip
    checkmark: gui.helpers.buttons.CustomPushButton = create_pushbutton(
        parent=None,
        name="StandardPushButton",
        tooltip=tool_tip_checkmark,
        icon_name="icons/dialog/cross.png",
        size=(size, size),
        checkable=False,
        click_func=checkmarkclick_func,
    )
    checkmark.setFixedSize(int(size), int(size))
    # To change the icon:
    # checkmark.setIcon(
    #     iconfunctions.get_qicon('icons/dialog/checkmark.png')
    # )
    # * QHBoxLayout()
    hlyt = qt.QHBoxLayout()
    hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
    hlyt.setSpacing(5)
    hlyt.setContentsMargins(0, 0, 0, 0)
    hlyt.addWidget(lineedit)
    hlyt.addWidget(button)
    hlyt.addWidget(checkmark)
    return (hlyt, lineedit, button, checkmark)


def create_textbrowser(
    name: str,
    func: Optional[Callable[[], None]] = None,
    read_only: bool = True,
    h_size_policy: qt.QSizePolicy.Policy = qt.QSizePolicy.Policy.Expanding,
    v_size_policy: qt.QSizePolicy.Policy = qt.QSizePolicy.Policy.Expanding,
) -> qt.QTextBrowser:
    """

    :param name:
    :param func:
    :param read_only:
    :param h_size_policy:
    :param v_size_policy:
    :return:
    """
    textedit = qt.QTextBrowser()
    textedit.setFont(data.get_general_font())
    textedit.setObjectName(name)
    if func is not None:
        textedit.textChanged.connect(func)
    textedit.setReadOnly(read_only)
    textedit.setSizePolicy(qt.QSizePolicy(h_size_policy, v_size_policy))

    def update_style():
        style_sheet = gui.stylesheets.textbox.get_default()
        textedit.setStyleSheet(style_sheet)

    update_style()
    textedit.update_style = update_style
    return textedit


groupbox_label_margin_top = 4
groupbox_label_offset_left = 8
groupbox_label_offset_top = -2


def create_tabs(
    name: str,
    parent: Optional[qt.QWidget] = None,
    main_form: Optional[qt.QWidget] = None,
) -> gui.forms.tabwidget.TabWidget:
    """

    :param name:
    :param parent:
    :param main_form:
    :return:
    """
    tabwidget_module = purefunctions.import_module("gui.forms.tabwidget")
    tabs = tabwidget_module.TabWidget(parent, main_form, None)
    tabs.setObjectName(name)
    return tabs
