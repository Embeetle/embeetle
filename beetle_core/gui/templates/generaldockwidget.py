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

##
##  General form used for dialogs
##
from typing import *
import os
import qt
import data
import os_checker
import iconfunctions
import gui.helpers.buttons
import gui.helpers.buttons
import gui.templates.baseslider
import gui.templates.widgetgenerator
import functools


class GeneralDockWidget(qt.QDockWidget):
    savable = data.CanSave.NO
    scale_factor = 1.0
    opacity = 1.0
    theme_name = None
    background_image = None
    main_form = None
    main_groupbox = None
    name = None

    @staticmethod
    def check_theme_state():
        return GeneralDockWidget.theme_name != data.theme["name"]

    def self_destruct(
        self, additional_clean_list: Optional[List] = None
    ) -> None:
        """"""
        if additional_clean_list is None:
            additional_clean_list = []
        # Clean up main references
        self.reference_window = None

        # Function for deleting an attribute
        def delete_attribute(att_name):
            attr = getattr(self, att_name)
            attr.setParent(None)
            attr.deleteLater()
            delattr(self, att_name)

        # List of attributes for clean up
        self_destruct_list = additional_clean_list
        for att in self_destruct_list:
            delete_attribute(att)
        # Clean up self
        self.setParent(None)  # noqa
        self.deleteLater()
        return

    def __init__(
        self,
        parent,
        size,
        title_text=None,
        icon_path=None,
        scale=1.0,
        opacity=1.0,
        in_scroll_area=True,
    ):
        """Initialization of dialog and background."""
        super().__init__(parent)
        self.main_form = parent
        self.scale_factor = scale
        # self.setWindowFlags(qt.Qt.WindowType.WindowStaysOnTopHint)
        self.setObjectName("Dialog")
        self.name = "Dialog"
        # Set the special dialog properties
        self.setFloating(True)
        self.setAllowedAreas(qt.Qt.DockWidgetArea.NoDockWidgetArea)
        # Set the initial opacity
        self.setWindowOpacity(1.0)
        # self.setFeatures(
        #     qt.QDockWidget.DockWidgetFeature.DockWidgetClosable |
        #     qt.QDockWidget.DockWidgetFeature.DockWidgetMovable |
        #     qt.QDockWidget.DockWidgetFeature.DockWidgetFloatable
        # )
        if title_text is None:
            self.setWindowTitle("")
        else:
            self.setWindowTitle(title_text)

        self.setWindowFlags(
            qt.Qt.WindowType.Window
            | qt.Qt.WindowType.WindowTitleHint
            | qt.Qt.WindowType.WindowSystemMenuHint
            | qt.Qt.WindowType.WindowCloseButtonHint
        )

        if icon_path is not None:
            self.setWindowIcon(iconfunctions.get_qicon(icon_path))
        else:
            self.setWindowIcon(
                iconfunctions.get_qicon(data.application_icon_relpath)
            )

        self.setSizePolicy(
            qt.QSizePolicy.Policy.Fixed,
            qt.QSizePolicy.Policy.Fixed,
        )
        # Main group box that will be the dialog's main widget
        self._init_main_groupbox(in_scroll_area)
        # Load images
        self.ok_image = iconfunctions.get_qpixmap("icons/dialog/checkmark.png")
        self.error_image = iconfunctions.get_qpixmap("icons/dialog/cross.png")
        return

    def _init_background(self):
        style_sheet = """
            #MainGroupBox {{
                background-color: {0};
                background-image: url({1});
                {2};
            }}
            #Dialog {{
                background-color: {0};
                background-image: url({1});
            }}
            """.format(
            data.theme["general_background"],
            iconfunctions.get_icon_abspath(
                "figures/backgrounds/background_grid.png"
            ),
            (
                "padding-top:0px; margin-top:-25px"
                if os_checker.is_os("linux")
                else ""
            ),
        )
        self.setStyleSheet(style_sheet)
        self.main_groupbox.setStyleSheet(style_sheet)

    def _reset_fixed_size(self):
        #        self.setMinimumSize(100, 100)
        #        self.setMaximumSize(2000, 2000)
        policy = qt.QSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Expanding,
        )
        self.setSizePolicy(policy)

    def _init_main_groupbox(self, in_scroll_area=True):
        if in_scroll_area:
            self.scroll_groupbox = self._create_borderless_groupbox()
            scroll_layout = qt.QVBoxLayout()
            scroll_layout.setContentsMargins(0, 0, 0, 0)
            self.scroll_groupbox.setLayout(scroll_layout)
            self.main_groupbox = gui.templates.widgetgenerator.create_groupbox(
                "MainGroupBox", ""
            )

            scroll_area = qt.QScrollArea()
            scroll_area.setWidget(self.main_groupbox)
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
            scroll_layout.addWidget(scroll_area)
            self.setWidget(self.scroll_groupbox)
        else:
            self.main_groupbox = gui.templates.widgetgenerator.create_groupbox(
                "MainGroupBox", ""
            )
            self.setWidget(self.main_groupbox)

        self._init_background()

    def _create_groupbox(self, name, text):
        groupbox = qt.QGroupBox(text, self.main_groupbox)
        groupbox.setObjectName(name)
        style_sheet = (
            gui.templates.widgetgenerator.generate_groupbox_stylesheet(name)
        )
        groupbox.setStyleSheet(style_sheet)
        return groupbox

    def _create_borderless_groupbox(self):
        group_box = qt.QGroupBox()
        group_box.setStyleSheet("border: 0px;")
        return group_box

    def _create_vertical_layout(self):
        layout = qt.QVBoxLayout()
        layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignRight | qt.Qt.AlignmentFlag.AlignVCenter
        )
        return layout

    def _create_horizontal_layout(self):
        layout = qt.QHBoxLayout()
        layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignRight | qt.Qt.AlignmentFlag.AlignVCenter
        )
        return layout

    def _create_slider(self, *args):
        slider = gui.templates.baseslider.BaseSlider(*args)
        return slider

    def _create_combobox(self, name, minimum_size=(340, 22)):
        combobox = qt.QComboBox()
        combobox.setFont(data.get_general_font())
        combobox.setObjectName(name)
        combobox.setMinimumSize(*minimum_size)
        return combobox

    def _create_label(self, text=None, bold=False):
        label = qt.QLabel()
        font = data.get_general_font()
        font.setBold(bold)
        label.setFont(font)
        label.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        if text is not None:
            label.setText(text)
        return label

    def _create_check_label(self, name, size):
        check_label = qt.QLabel()
        #        check_label.setFixedSize(*size)
        check_label.setPixmap(self.error_image)
        check_label.setScaledContents(True)
        check_label.setObjectName(name)
        return check_label

    def _create_check_box(self, parent, name, size):
        check_box = gui.helpers.buttons.CheckBox(parent, name, size)
        return check_box

    def _create_message_box(self, size, font):
        # Message label box
        message_box = self._create_groupbox("MessageBox", "Messages")
        width = size[0] * self.scale_factor
        height = size[1] * self.scale_factor
        #        message_box.setFixedWidth(width)
        message_box.setMinimumHeight(height * 1.25)

        # Message label
        message_label_text = gui.templates.widgetgenerator.create_label(
            wordwrap=True,
            alignment=qt.Qt.AlignmentFlag.AlignHCenter
            | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        message_label_text.setMinimumWidth(width - 20)
        self.message_label_text = message_label_text

        layout = qt.QHBoxLayout()
        layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        message_box.setLayout(layout)
        layout.addWidget(self.message_label_text)
        message_box.adjustSize()

        message_box.setContentsMargins(0, 8, 0, 0)
        return message_box

    def _set_widget_message(self, widget, message):
        def enter(event):
            self.display_message(message)

        def leave(event):
            self.display_message("")

        widget.enterEvent = enter
        widget.leaveEvent = leave

    def _create_pushbutton(
        self, name, tool_tip, icon_name, size, checkable=False
    ):
        button = gui.helpers.buttons.CustomPushButton(
            parent=self,
            icon_path=icon_name,
            icon_size=qt.create_qsize(size[0] - 6, size[1] - 6),
            scale=self.scale_factor,
        )
        if checkable == True:
            button.setCheckable(True)
        #        button.setToolTip(tool_tip)
        enter_func = functools.partial(self.display_message, tool_tip)
        button.set_enter_function(enter_func)
        leave_func = functools.partial(self.display_message, "")
        button.set_leave_function(leave_func)
        button.enable()
        return button

    def _create_tabwidget(self, name):
        tabs = qt.QTabWidget()
        tabs.setObjectName(name)
        return tabs

    def _create_search_replace_tabwidget(self, name):
        class CustomTabBar(qt.QTabBar):
            """Custom tab bar used to color the tabs according to the
            functionality."""

            mouseHover = qt.pyqtSignal(int)

            def __init__(self, parent=None):
                super().__init__(parent)

            def paintEvent(self, event):
                super().paintEvent(event)
                parent = self.parent_reference
                painter = qt.QStylePainter(self)
                original_brush = painter.brush()
                opt = qt.QStyleOptionTab()
                painter.save()

                for i in range(self.count()):
                    self.initStyleOption(opt, i)
                    # Check if the file is a project directory file
                    if parent.current_index == i:
                        painter.setPen(qt.QPen(qt.QColor("#ffffffff")))
                        if i == 0:
                            painter.setBrush(qt.QBrush(qt.QColor("#fffce94f")))
                        elif i == 1:
                            painter.setBrush(qt.QBrush(qt.QColor("#ff8ae234")))
                        elif i == 2:
                            painter.setBrush(qt.QBrush(qt.QColor("#ff729fcf")))
                        else:
                            painter.setBrush(qt.QBrush(qt.QColor("#ffad7fa8")))
                        #                        opt.palette.setBrush(
                        #                            qt.QPalette.ColorRole.WindowText,
                        #                            qt.QColor("#ffffffff")
                        #                        )
                        painter.drawRect(opt.rect)
                        painter.drawControl(
                            qt.QStyle.ControlElement.CE_TabBarTabLabel, opt
                        )
                    #                        painter.drawItemText(
                    #                            opt.rect, 0, opt.palette, True, opt.text
                    #                        )
                    else:
                        painter.drawControl(
                            qt.QStyle.ControlElement.CE_TabBarTabShape, opt
                        )
                        painter.drawControl(
                            qt.QStyle.ControlElement.CE_TabBarTab, opt
                        )
                        painter.drawControl(
                            qt.QStyle.ControlElement.CE_TabBarTabLabel, opt
                        )
                painter.restore()

            def event(self, event):
                result = super().event(event)
                if isinstance(event, qt.QHoverEvent):
                    tab_number = self.tabAt(event.pos())
                    self.mouseHover.emit(tab_number)
                return result

            def __init__(self, parent):
                # Initialize superclass
                super().__init__(parent)
                # Store the main form reference
                self.parent_reference = parent

        tabs = self._create_tabwidget(name)
        tabs.current_index = 0
        custom_tab_bar = CustomTabBar(tabs)
        tabs.setTabBar(custom_tab_bar)
        #        tabs.setFixedWidth(437)
        #        tabs.setFixedHeight(168)
        return tabs

    """
    Overridden functions
    """

    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        pressed_key = e.key()
        if pressed_key == qt.Qt.Key.Key_Escape:
            self.main_form.display.hide_other_dialogs()

    def center_to_parent(self):
        global_position = self.main_form.mapToGlobal(
            self.main_form.rect().center()
        )
        self.move(
            int(global_position.x() - self.width() / 2),
            int(global_position.y() - self.height() / 2),
        )

    def show(self):
        super().show()
        self.center_to_parent()

    def _set_fixed_policy(self, widget):
        widget.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.Fixed,
                qt.QSizePolicy.Policy.Fixed,
            )
        )
