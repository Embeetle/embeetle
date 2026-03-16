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

# Standard library
import re
import pprint
import inspect
import functools
import traceback
import webbrowser
from typing import *

# Local
import qt
import data
import constants
import functions
import iconfunctions
import gui.templates.baseobject
import gui.templates.treewidget
import gui.templates.widgetgenerator
import gui.helpers.simplecombobox
import gui.helpers.buttons
import gui.stylesheets.combobox
import gui.stylesheets.splitter
import gui.stylesheets.frame
import chipconfigurator.basebuilder
import chipconfigurator.chipconfigurator
import chipconfigurator.colors
import chipconfigurator.constants
import mcuconfig

DEBUG_PRINTING = True
# Global references
chip_configurator = None


class SlantedRectangle(qt.QWidget):
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = color

    def paintEvent(self, event):
        painter = qt.QPainter(self)
        painter.setRenderHint(qt.QPainter.RenderHint.Antialiasing)

        offset = int(self.height() * 0.2)
        width = self.width() - (offset * 2)
        height = self.height() - (offset * 2)

        skewed_new_rect = qt.QRectF(offset, offset, width, height)
        painter.shear(-0.2, 0)

        brush = qt.QBrush(qt.QColor(self.color["bg"]))
        painter.setBrush(brush)
        painter.setPen(qt.QColor(data.theme["fonts"]["default"]["color"]))
        painter.drawRect(skewed_new_rect)


class ChipConfiguratorWindow(qt.QFrame, gui.templates.baseobject.BaseObject):
    def __debug_print(self, *msgs):
        if DEBUG_PRINTING:
            print(f"[{self.__class__.__name__}]", *msgs)

    def self_destruct(self) -> None:
        pass

    def __init__(self, parent, main_form, project_path: str) -> None:
        # Base class initialization
        qt.QFrame.__init__(self)
        gui.templates.baseobject.BaseObject.__init__(
            self,
            parent=parent,
            main_form=main_form,
            name="ChipConfiguratorWindow",
            icon="icons/gen/pinconfig.png",
        )

        # Variable initialization
        self.__stored_hovered_action: qt.QAction = None
        self.__peripheral_item_cache: dict = None
        self.__drag_object_cache: qt.QDrag = None
        self.__peripheral_cache: Optional[Dict[str, Any]] = None
        self.__widget_value_cache: Optional[Dict[str, Any]] = None
        self.__setting_widget_cache: Optional[Dict[str, Any]] = None
        self.__drag_state = "idle"
        self.project_path = project_path

        # Initialize chip configurator
        global chip_configurator
        chip_configurator = chipconfigurator.chipconfigurator.ChipConfigurator(
            callback_cache={
                "set_chip_draw_data": self.set_chip_draw_data,
                "callback_handler": self.callback_handler,
            },
        )

        # Initialize the peripheral colors
        peripheral_types = sorted(
            mcuconfig.PeripheralKind,
            key=lambda peripheral: peripheral.name.lower(),
        )
        self.peripheral_colors = {
            pt: chipconfigurator.colors.get_peripheral_type_color(pt)
            for pt in peripheral_types
        }

        # Main initialization
        self.__initialize_main()

        # Update styling
        self.update_style()

    def __initialize_main(self) -> None:
        # Self
        layout = gui.templates.widgetgenerator.create_layout(
            vertical=True, margins=(0, 0, 0, 0)
        )
        self.setLayout(layout)

        # Add save button
        self.save_button = gui.templates.widgetgenerator.create_pushbutton(
            parent=self,
            name="save",
            text="Save && Generate",
            icon_name="icons/save/save.png",
            tooltip="Save all and generate code",
            statustip="Save all and generate code",
            click_func=self.save,
            style="save-banner",
        )
        self.layout().addWidget(self.save_button)
        self.save_button.hide()

        # Main splitter
        self.splitter = qt.QSplitter(
            orientation=qt.Qt.Orientation.Horizontal,
            parent=self,
        )
        self.layout().addWidget(self.splitter)
        self.splitter.setStyleSheet(
            gui.stylesheets.splitter.get_transparent_stylesheet()
        )

        # Left side view of peripherals, ...
        # Left frame
        self.left_frame = gui.templates.widgetgenerator.create_frame(
            name="LeftFrame",
            parent=self,
            layout_vertical=True,
            layout_spacing=0,
            layout_margins=(0, 0, 0, 0),
        )
        self.splitter.addWidget(self.left_frame)
        # Left selection bar
        self.left_selection_bar = gui.templates.widgetgenerator.create_frame(
            name="LeftSelectionBar",
            parent=self,
            layout_vertical=False,
            layout_spacing=0,
            layout_margins=(0, 0, 0, 0),
        )
        self.left_frame.layout().addWidget(self.left_selection_bar)
        # Add peripherals button
        self.peripherals_button = (
            gui.templates.widgetgenerator.create_pushbutton(
                parent=self.left_selection_bar,
                name="peripherals",
                text="Peripherals",
                icon_name="icons/gen/baremetal.svg",
                tooltip="Select the Peripherals",
                statustip="Select the Peripherals",
                click_func=self.__show_peripherals,
                style="debugger",
            )
        )
        # self.peripherals_button.set_font_size_factor(1.5)
        # self.peripherals_button.set_custom_icon_size(
        #     qt.create_qsize(
        #         data.get_general_icon_pixelsize() * 2,
        #         data.get_general_icon_pixelsize() * 2
        #     )
        # )
        self.left_frame.layout().addWidget(self.peripherals_button)
        # Peripheral view
        self.peripheral_view = chipconfigurator.basebuilder.BaseBuilder()
        self.left_frame.layout().addWidget(self.peripheral_view)

        # Widget referance cache
        self.widget_cache = {}

        # Right frame
        self.right_frame = gui.templates.widgetgenerator.create_frame(
            name="RightFrame",
            parent=self,
            layout_vertical=True,
            layout_spacing=0,
            layout_margins=(0, 0, 0, 0),
        )
        self.splitter.addWidget(self.right_frame)
        # Right selection bar
        self.right_selection_bar = gui.templates.widgetgenerator.create_frame(
            name="RightSelectionBar",
            parent=self,
            layout_vertical=False,
            layout_spacing=0,
            layout_margins=(0, 0, 0, 0),
        )
        self.right_frame.layout().addWidget(self.right_selection_bar)
        # Add pin view button
        self.pin_view_button = gui.templates.widgetgenerator.create_pushbutton(
            parent=self.right_selection_bar,
            name="pin-view",
            text="Pin View",
            icon_name="icons/gen/pinconfig_details.svg",
            tooltip="Select the Pin view",
            statustip="Select the Pin view",
            click_func=self.__show_pin_view,
            style="debugger",
        )
        # self.pin_view_button.set_font_size_factor(1.5)
        # self.pin_view_button.set_custom_icon_size(
        #     qt.create_qsize(
        #         data.get_general_icon_pixelsize() * 2,
        #         data.get_general_icon_pixelsize() * 2
        #     )
        # )
        self.right_selection_bar.layout().addWidget(self.pin_view_button)
        # Add clock config button
        self.clock_config_button = (
            gui.templates.widgetgenerator.create_pushbutton(
                parent=self.right_selection_bar,
                name="clock-view",
                text="Clock View",
                icon_name="icons/gen/clock.svg",
                tooltip="Select the Clock View",
                statustip="Select the Clock View",
                click_func=self.__show_clock_config,
                style="debugger",
            )
        )
        # self.clock_config_button.set_font_size_factor(1.5)
        # self.clock_config_button.set_custom_icon_size(
        #     qt.create_qsize(
        #         data.get_general_icon_pixelsize() * 2,
        #         data.get_general_icon_pixelsize() * 2
        #     )
        # )
        self.right_selection_bar.layout().addWidget(self.clock_config_button)
        # Right stack widget
        self.stack_view = qt.QStackedWidget(self)
        self.right_frame.layout().addWidget(self.stack_view)

        # Information display widget
        self.chip_display = ChipInformationDisplay(parent=self)
        self.chip_display.paint_widget.pin_clicked_signal.connect(
            self.__pin_clicked
        )
        self.chip_display.paint_widget.peripheral_drag_start_signal.connect(
            self.__peripheral_drag_start
        )
        self.chip_display.paint_widget.peripheral_drag_move_inside_pin_signal.connect(
            self.__peripheral_drag_move_inside_pin
        )
        self.chip_display.paint_widget.peripheral_clicked_signal.connect(
            self.__peripheral_clicked
        )
        self.chip_display.paint_widget.peripheral_dropped_signal.connect(
            self.__peripheral_dropped
        )
        self.chip_display.mouse_wheel_event_signal.connect(
            self.__display_wheel_event
        )
        self.stack_view.addWidget(self.chip_display)
        self.widget_cache["chip-information-display"] = self.chip_display

        # Information display widget
        self.clock_tree_display = ClockTreeInformationDisplay(parent=self)
        self.stack_view.addWidget(self.clock_tree_display)
        self.widget_cache["chip-information-display"] = self.clock_tree_display

        # Make all splitter's child widgets not collapsable
        for i in range(self.splitter.count()):
            self.splitter.setCollapsible(i, False)

    def __show_pin_view(self) -> None:
        self.stack_view.setCurrentWidget(self.chip_display)

    def __show_clock_config(self) -> None:
        self.stack_view.setCurrentWidget(self.clock_tree_display)

    def __show_peripherals(self) -> None:
        print("__show_peripherals")

    def __settings_expand(
        self, title_bar, expander_label, settings_gb=None, signal_table_gb=None
    ):
        def inner_settings_expand(override=None):
            new_state = (
                not settings_gb.isVisible()
                if settings_gb is not None
                else False
            ) or (
                not signal_table_gb.isVisible()
                if signal_table_gb is not None
                else False
            )
            if override is not None:
                new_state = override

            if settings_gb is not None:
                settings_gb.setVisible(new_state)

            if signal_table_gb is not None:
                signal_table_gb.setVisible(new_state)

            if new_state:
                image = "icons/arrow/chevron/chevron_down.svg"
            else:
                image = "icons/arrow/chevron/chevron_right.svg"
            pixmap = iconfunctions.get_qpixmap(image)
            expander_label.setPixmap(pixmap)

        return inner_settings_expand

    def __alphanumeric_key(
        self, peripheral: mcuconfig.Peripheral
    ) -> List[Union[int, str]]:
        # Split the string into parts: letters and numbers
        return [
            int(text) if text.isdigit() else text.lower()
            for text in re.split("([0-9]+)", peripheral.name)
        ]

    def __initialize_peripheral_list(self) -> None:
        # Reset the peripheral list
        self.__peripheral_cache = {}
        # Value widget cache
        self.__widget_value_cache = {}
        self.__setting_widget_cache = {}

        # Determine the width of the longest label
        max_label_width = functions.get_text_width("0" * 30)

        border_toggle_flag = False
        for p in sorted(
            chip_configurator.part.peripherals, key=self.__alphanumeric_key
        ):
            # Store the peripheral for later access
            self.__peripheral_cache[p.name] = {
                "peripheral": p,
            }

            # Create the main box
            new_box = self.peripheral_view.add_box(
                name=p.name,
                vertical=False,
                spacing=2,
                margins=(2, 2, 2, 2),
            )
            new_box.setSizePolicy(
                qt.QSizePolicy.Policy.Minimum,
                qt.QSizePolicy.Policy.Fixed,
            )

            new_checkbox_box = (
                gui.templates.widgetgenerator.create_groupbox_with_layout(
                    name=p.name,
                    vertical=True,
                    borderless=True,
                    spacing=2,
                    margins=(2, 2, 2, 2),
                    background_color="transparent",
                )
            )
            # Check if peripheral can be disabled
            size = data.get_toplevel_menu_pixelsize()
            if p.can_be_disabled:
                # Add a checkbox
                new_checkbox = (
                    gui.templates.widgetgenerator.create_standard_checkbox(
                        parent=new_box,
                        name=p.name,
                    )
                )
                new_checkbox.setSizePolicy(
                    qt.QSizePolicy.Policy.Minimum,
                    qt.QSizePolicy.Policy.Minimum,
                )
                new_checkbox.setFixedSize(size, size)
                new_checkbox.setChecked(p.is_enabled)

                # Connect the signals
                new_checkbox.checkStateChanged.connect(
                    self.__peripheral_check_change
                )

                self.__peripheral_cache[p.name]["checkbox"] = new_checkbox
                new_checkbox_box.layout().addWidget(new_checkbox)
            else:
                # Add a transparent placehoder for a checkbox for alignment
                transparent_widget = qt.QWidget()
                transparent_widget.setSizePolicy(
                    qt.QSizePolicy.Policy.Minimum,
                    qt.QSizePolicy.Policy.Minimum,
                )
                transparent_widget.setStyleSheet(
                    "background-color: transparent;"
                )
                transparent_widget.setFixedSize(size, size)
                new_checkbox_box.layout().addWidget(transparent_widget)
            # Add the box to the layout
            new_box.layout().addWidget(new_checkbox_box)
            new_box.layout().setAlignment(
                new_checkbox_box,
                qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignTop,
            )

            # Add the peripheral box
            background = data.theme["shade"][2]
            if border_toggle_flag:
                background = data.theme["shade"][1]
            border_toggle_flag = not border_toggle_flag
            new_peripheral_box = (
                gui.templates.widgetgenerator.create_groupbox_with_layout(
                    name=p.name,
                    vertical=True,
                    borderless=True,
                    spacing=2,
                    margins=(2, 2, 2, 2),
                    background_color=background,
                )
            )
            new_peripheral_box.setSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.MinimumExpanding,
            )
            new_box.layout().addWidget(new_peripheral_box)

            # Add the title bar
            title_bar = (
                gui.templates.widgetgenerator.create_groupbox_with_layout(
                    name=p.name,
                    vertical=False,
                    borderless=True,
                    spacing=0,
                    margins=(0, 0, 0, 0),
                )
            )
            title_bar.layout().setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
            new_peripheral_box.layout().addWidget(title_bar)

            # Add the peripheral color rectangle
            new_color_rectangle = SlantedRectangle(
                self.peripheral_colors[p.kind]["color"],
                parent=title_bar,
            )
            rectangle_side_size = data.get_toplevel_menu_pixelsize()

            new_color_rectangle.setStyleSheet(
                (
                    "min-width: {};"
                    "max-width: {};"
                    "min-height: {};"
                    "max-height: {};"
                ).format(
                    rectangle_side_size * 2,
                    rectangle_side_size * 2,
                    rectangle_side_size,
                    rectangle_side_size,
                )
            )
            new_color_rectangle.setSizePolicy(
                qt.QSizePolicy.Policy.Minimum,
                qt.QSizePolicy.Policy.Minimum,
            )
            title_bar.layout().addWidget(new_color_rectangle)
            title_bar.layout().setAlignment(
                new_color_rectangle, qt.Qt.AlignmentFlag.AlignLeft
            )
            # Add the label
            new_label = gui.templates.widgetgenerator.create_label(
                parent=title_bar,
                text=p.name,
                bold=True,
                transparent_background=True,
            )
            new_label.setSizePolicy(
                qt.QSizePolicy.Policy.Minimum,
                qt.QSizePolicy.Policy.Minimum,
            )
            title_bar.layout().addWidget(new_label)
            title_bar.layout().setAlignment(
                new_label, qt.Qt.AlignmentFlag.AlignLeft
            )
            # Add the expander label
            if (
                len(p.settings) > 0
                or len(p.signals) > 0
                or p.supports_user_defined_signals
            ):
                title_bar.layout().addSpacing(2)

                expander_label = gui.templates.widgetgenerator.create_label(
                    parent=title_bar,
                    image="icons/arrow/chevron/chevron_right.svg",
                    transparent_background=True,
                )
                expander_label.setSizePolicy(
                    qt.QSizePolicy.Policy.Minimum,
                    qt.QSizePolicy.Policy.Minimum,
                )
                expander_label.setFixedSize(
                    int(data.get_general_icon_pixelsize() * 0.5),
                    int(data.get_general_icon_pixelsize() * 0.5),
                )
                title_bar.layout().addWidget(expander_label)
                title_bar.layout().setAlignment(
                    expander_label, qt.Qt.AlignmentFlag.AlignLeft
                )

            # Add the peripheral settings
            if (
                len(p.settings) > 0
                or len(p.signals) > 0
                or p.supports_user_defined_signals
            ):
                settings_gb = None
                if len(p.settings) > 0:
                    labels = []
                    widgets = []
                    for s in p.settings:
                        # Add the setting
                        new_label = gui.templates.widgetgenerator.create_label(
                            parent=new_peripheral_box,
                            text=s.label + ":",
                            transparent_background=True,
                        )
                        labels.append(new_label)

                        if s.kind == mcuconfig.SettingKind.LIST:
                            if len(s.options) > 0:
                                new_combobox = gui.templates.widgetgenerator.create_combobox(
                                    parent=new_peripheral_box,
                                )
                                new_combobox.setStyleSheet(
                                    gui.stylesheets.combobox.get_default()
                                )
                                for k, text in enumerate(s.options):
                                    new_combobox.addItem(text, k)
                                # Set the initial value
                                for index in range(new_combobox.count()):
                                    if new_combobox.itemData(index) == s.value:
                                        new_combobox.setCurrentIndex(index)
                                        break

                                # Connect the signals
                                new_combobox.currentIndexChanged.connect(
                                    self.__combobox_index_changed
                                )

                                # Add it to the layout
                                widgets.append(new_combobox)
                            else:
                                new_label = (
                                    gui.templates.widgetgenerator.create_label(
                                        parent=new_peripheral_box,
                                        text="NO OPTIONS",
                                        transparent_background=True,
                                    )
                                )
                                widgets.append(new_label)
                        elif s.kind == mcuconfig.SettingKind.FLAG:
                            new_checkbox = gui.templates.widgetgenerator.create_standard_checkbox(
                                parent=new_peripheral_box,
                                name=s.label,
                            )
                            # Set the initial value
                            initial_value = (
                                qt.Qt.CheckState.Checked
                                if s.value == True
                                else qt.Qt.CheckState.Unchecked
                            )
                            new_checkbox.setCheckState(initial_value)

                            # Connect the signals
                            new_checkbox.checkStateChanged.connect(
                                self.__checkbox_state_changed
                            )

                            # Add it to the layout
                            widgets.append(new_checkbox)
                        elif s.kind == mcuconfig.SettingKind.NUMBER:
                            new_textbox = (
                                gui.templates.widgetgenerator.create_textbox(
                                    s.label,
                                    parent=new_peripheral_box,
                                    no_border=True,
                                )
                            )
                            new_textbox.setValidator(
                                qt.QIntValidator(
                                    s.minimum, s.maximum, new_peripheral_box
                                )
                            )
                            # Set the initial value
                            initial_value = s.value
                            new_textbox.setText(str(initial_value))

                            # Connect the signals
                            new_textbox.textChanged.connect(
                                self.__textbox_text_changed
                            )

                            # Add it to the layout
                            widgets.append(new_textbox)
                        else:
                            raise Exception(
                                f"[{self.__name__.__class__}] "
                                + f"Unknown peripheral action type: {item_data['type']}"
                            )

                        # Enable/disable widget according to the setting
                        widgets[-1].setEnabled(s.is_enabled)

                        # Add the new value widget to the caches
                        self.__widget_value_cache[widgets[-1]] = s
                        self.__setting_widget_cache[s] = widgets[-1]

                    # Add the box that will hold the settings
                    settings_gb = gui.templates.widgetgenerator.create_groupbox_with_layout(
                        name=f"SettingsGroupBox-{p.name}",
                        vertical=True,
                        borderless=True,
                        spacing=0,
                        margins=(0, 0, 0, 0),
                        background_color="transparent",
                    )
                    new_peripheral_box.layout().addWidget(settings_gb)

                    # Add QLabel/QComboBox pairs to the layout
                    for label, value_widget in zip(labels, widgets):
                        label.setFixedWidth(max_label_width)
                        label.setWordWrap(True)
                        row_layout = qt.QHBoxLayout()
                        row_layout.layout().setAlignment(
                            qt.Qt.AlignmentFlag.AlignLeft
                        )
                        row_layout.addWidget(label)
                        row_layout.addSpacing(6)
                        row_layout.addWidget(value_widget)
                        settings_gb.layout().addLayout(row_layout)

                # Add the signal table
                signal_table_gb = None
                if len(p.signals) > 0 or p.name == "GPIO":
                    # Add the box that will hold the settings
                    signal_table_gb = gui.templates.widgetgenerator.create_groupbox_with_layout(
                        name=f"SettingsGroupBox-{p.name}",
                        vertical=True,
                        borderless=True,
                        spacing=0,
                        margins=(0, 0, 0, 0),
                        background_color="transparent",
                    )
                    new_peripheral_box.layout().addWidget(signal_table_gb)
                    # Create table
                    signal_table = gui.templates.widgetgenerator.create_table(
                        signal_table_gb
                    )
                    signal_table.setSizePolicy(
                        qt.QSizePolicy.Policy.Expanding,
                        qt.QSizePolicy.Policy.Maximum,
                    )
                    signal_table_gb.layout().addWidget(signal_table)
                    # Table headers
                    signal_table.set_headers(
                        list(
                            chipconfigurator.constants.signal_table_headers.values()
                        )
                    )
                    # Table properties
                    signal_table.setShowGrid(True)
                    signal_table.verticalHeader().hide()
                    signal_table.setSortingEnabled(True)
                    signal_table.setSelectionBehavior(
                        qt.QAbstractItemView.SelectionBehavior.SelectItems
                    )
                    signal_table.setEditTriggers(
                        qt.QAbstractItemView.EditTrigger.NoEditTriggers
                    )
                    signal_table.setSelectionMode(
                        qt.QAbstractItemView.SelectionMode.SingleSelection
                    )

                    # Signals
                    signal_table.combobox_item_changed.connect(
                        self.__signal_table_combobox_change
                    )

                    # Initialize the signal-to-row bindings
                    signal_table.signals = {}

                    # Add the signals to the table
                    for s in p.signals:
                        new_data = self.__get_signal_data_for_table(s)
                        signal_table.add_row(list(new_data.values()))
                        row_index = signal_table.rowCount() - 1
                        signal_table.signals[row_index] = s
                        signal_table.set_row_enabled(row_index, s.is_enabled)

                    signal_table.adjust_height()

                    self.__peripheral_cache[p.name][
                        "signal-table"
                    ] = signal_table

                    # GPIO extra functionality
                    if p.supports_user_defined_signals:
                        # Add signal button
                        button_add_signal = gui.templates.widgetgenerator.create_pushbutton(
                            parent=signal_table_gb,
                            name="add-signal",
                            icon_name="icons/tab/plus.svg",
                            tooltip="Add a custom GPIO signal to the signal table",
                            statustip="Add a custom GPIO signal to the signal table",
                            click_func=functools.partial(
                                self.__add_signal_row,
                                signal_table_gb,
                                signal_table,
                            ),
                            style="debug",
                        )
                        signal_table_gb.layout().addWidget(button_add_signal)

                        signal_table.itemChanged.connect(
                            functools.partial(
                                self.__gpio_item_changed,
                                signal_table_gb,
                                signal_table,
                            )
                        )

                click_func = self.__settings_expand(
                    title_bar,
                    expander_label,
                    settings_gb=settings_gb,
                    signal_table_gb=signal_table_gb,
                )
                title_bar.mouse_release_signal.connect(click_func)

                # Expand the peripheral as needed
                click_func(
                    override=p.is_enabled
                    and p.can_be_disabled
                    and (
                        len(p.settings) > 0
                        or (len(p.signals) > 0 or p.name == "GPIO")
                    )
                )

    def __signal_table_combobox_change(
        self,
        row: int,
        column: int,
        index: int,
        combobox: gui.helpers.simplecombobox.SimpleComboBox,
        signal_table: gui.templates.widgetgenerator.StandardTable,
    ) -> None:
        # Skip invalid indexes
        if index < 0:
            return
        elif (
            chip_configurator.config is None
            or chip_configurator.config.tentative_changes_active
        ):
            return
        elif row not in signal_table.signals.keys():
            return

        column_title = chipconfigurator.constants.signal_table_headers[column]
        signal = signal_table.signals[row]
        if signal is not None:
            # print(signal.name, column_title, index)
            if column_title == "Pad":
                pad = combobox.itemData(index)
                if pad is None:
                    signal.unmap()
                else:
                    signal.map_to_pad(pad)
            if column_title == "Pin":
                pin = combobox.itemData(index)
                if pin is None:
                    signal.unmap()
                else:
                    signal.map_to_pin(pin)
            if column_title == "Mode":
                mode = combobox.itemData(index)
                signal.mode = mode

    def __add_signal_row(self, gb, signal_table) -> None:
        signal_data = (
            {
                "type": "string",
                "text": "/",
                "readonly": False,
            },
            {
                "type": "combobox-item",
                "keys": [],
                "values": [],
            },
            {
                "type": "combobox-item",
                "keys": [],
                "values": [],
            },
            {
                "type": "combobox-item",
                "keys": [],
                "values": [],
            },
            {
                "type": "string",
                "text": "/",
                "readonly": False,
            },
        )
        signal_table.add_row(signal_data)

        # Enable editing triggers
        signal_table.setEditTriggers(
            qt.QAbstractItemView.EditTrigger.AllEditTriggers
        )

        # Pin cannot be edited
        row_index = signal_table.rowCount() - 1

        signal_table.adjust_height()

        self.__debug_print("Added new signal row.")

    def __gpio_item_changed(self, gb, signal_table, item) -> None:
        # Get the row and column index of the changed item
        row_index = item.row()
        column_index = item.column()
        try:

            # Get the header item for the column
            header_text = signal_table.horizontalHeaderItem(column_index).text()
            if header_text == "Signal":
                if item.text().isidentifier():
                    item.gpio_last_valid_name = item.text()
                    if row_index not in signal_table.signals.keys():
                        gpio = chip_configurator.part.peripheral("GPIO")
                        if gpio is None:
                            self.__debug_print(
                                f"GPIO peripheral doesn't exist yet, skipping adding table entry."
                            )
                            return
                        name = item.text()
                        if gpio.signal(name) is not None:
                            self.__debug_print(
                                f"Signal '{name}' already exist, skipping adding table entry."
                            )
                        description_cell = signal_table.item(row_index, 4)
                        if description_cell is None:
                            self.__debug_print(
                                f"Description for signal '{name}' doesn't exist yet, skipping adding table entry."
                            )
                            return
                        description = description_cell.text()
                        new_signal = gpio.add_signal(name, description)

                        if new_signal in signal_table.signals.values():
                            return

                        # Bind the signal to row
                        signal_table.signals[row_index] = new_signal

                        # Automap the signal
                        new_signal.auto_map()

                        # Debug message
                        self.__debug_print(
                            f"Added new signal: '{name}' / '{description}'"
                        )
                    else:
                        signal = signal_table.signals[row_index]
                        old_name = signal.name
                        new_name = item.text()
                        signal.name = new_name
                        self.__debug_print(
                            f"Changed signal name from '{old_name}' to '{new_name}'"
                        )
                else:
                    if (
                        hasattr(item, "gpio_last_valid_name")
                        and item.gpio_last_valid_name is not None
                    ):
                        item.setText(item.gpio_last_valid_name)
                    else:
                        item.setText("/")
            elif header_text == "Description":
                if row_index in signal_table.signals.keys():
                    signal = signal_table.signals[row_index]
                    old_description = signal.description
                    new_description = item.text()
                    signal.description = new_description
                    self.__debug_print(
                        f"Changed signal description from '{old_description}' to '{new_description}'"
                    )

        except Exception as ex:
            traceback.print_exc()
            self.__debug_print(f"Error on signal data change: {ex}")

    def __combobox_index_changed(self, new_index: int) -> None:
        setting = self.__widget_value_cache[self.sender()]
        selected_value = self.sender().itemData(new_index)
        setting.select(selected_value)

    def __checkbox_state_changed(self, new_state: qt.Qt.CheckState) -> None:
        setting = self.__widget_value_cache[self.sender()]
        new_state = True if new_state == qt.Qt.CheckState.Checked else False
        setting.select(new_state)

    def __textbox_text_changed(self, new_text: str) -> None:
        setting = self.__widget_value_cache[self.sender()]
        try:
            if not (new_text.strip().isdigit()):
                return
            new_value = int(new_text)
            if new_value > setting.maximum:
                new_value = setting.maximum
                self.sender().setText(str(new_value))
            if new_value < setting.minimum:
                new_value = setting.minimum
                self.sender().setText(str(new_value))
            setting.select(new_value)
        except:
            if data.signal_dispatcher is not None:
                data.signal_dispatcher.notify_error.emit(traceback.format_exc())
            else:
                traceback.print_exc()

    def __set_widget_value(self, widget: Any, value: Union[int, bool]) -> None:
        if isinstance(widget, gui.helpers.simplecombobox.SimpleComboBox):
            for index in range(widget.count()):
                if widget.itemData(index) == value:
                    widget.setCurrentIndex(index)
                    break
        elif isinstance(widget, gui.helpers.buttons.StandardCheckBox):
            new_state = (
                qt.Qt.CheckState.Checked
                if value == True
                else qt.Qt.CheckState.Unchecked
            )
            widget.setCheckState(new_state)
        elif isinstance(widget, gui.templates.widgetgenerator.TextBox):
            widget.setText(str(value))
        else:
            raise Exception(
                f"[{self.__name__.__class__}] "
                + f"Unknown value widget type: {widget.__class__}"
            )

    """
    Peripheral
    """

    def __peripheral_check_change(self, state: qt.Qt.CheckState) -> None:
        peripheral_name = self.sender().name
        #        print(peripheral_name, state, self.__peripheral_cache[peripheral_name].can_be_disabled)
        peripheral = self.__peripheral_cache[peripheral_name]["peripheral"]
        if not peripheral.can_be_disabled:
            self.sender().setCheckState(qt.Qt.CheckState.Checked)
        else:
            new_state = True if state == qt.Qt.CheckState.Checked else False
            peripheral.set_enabled(new_state)

    def __tree_click(self, *args):
        item, column = args
        item_data = item.get_data()
        if "type" in item_data.keys():
            if item_data["type"] == "chip-information-display":
                peripheral_widget = self.widget_cache[
                    "chip-information-display"
                ]
                self.stack_view.setCurrentWidget(peripheral_widget)

            elif item_data["type"] == "peripheral":
                name = item_data["data"]["name"]
                peripheral_widget = self.widget_cache[name]
                self.stack_view.setCurrentWidget(peripheral_widget)

            else:
                raise Exception(
                    f"[{self.__name__.__class__}] "
                    + f"Unknown peripheral action type: {item_data['type']}"
                )

    def __peripheral_drag_start(
        self, peripheral_item: dict, drag_object: qt.QDrag
    ) -> None:
        # Get the peripheral data
        peripheral_text = peripheral_item.get("text")
        peripheral_signal = peripheral_item.get("signal")
        peripheral_bg_color = peripheral_item.get("bg-color")
        peripheral_fg_color = peripheral_item.get("fg-color")
        peripheral_opacity = peripheral_item.get("opacity", 1.0)
        peripheral_strikethrough = peripheral_item.get("strike-through", False)

        # Create a valid pin list
        valid_pin_mappings = []

        # Update pin colors
        chip_configurator.set_draw_data()
        for index, values in chip_configurator.pin_data.items():
            pin_text = values["text"]
            for m in chip_configurator.get_signal_mappings(peripheral_signal):
                if pin_text == m.pad.name:
                    # Color the pin
                    chip_configurator.pin_override_set(
                        pin=index, key="bg-color", value="#00ff00"
                    )
                    chip_configurator.pin_override_set(
                        pin=index, key="opacity", value=1.0
                    )

                    valid_pin_mappings.append(
                        {
                            "pin": index,
                            "mapping": m,
                        }
                    )
                    break
                else:
                    chip_configurator.pin_override_set(
                        pin=index, key="opacity", value=0.2
                    )

        chip_configurator.set_draw_data()

        # Store the peripheral item
        self.__peripheral_item_cache = {
            "valid_pin_mappings": valid_pin_mappings,
            "peripheral_item": peripheral_item,
        }

        # Store the drag object
        self.__drag_object_cache = drag_object

        self.__drag_state = "idle"

    def __peripheral_drag_move_inside_pin(
        self, pin: Optional[mcuconfig.Pin], event: object
    ) -> None:
        event.acceptProposedAction()

        if self.__drag_state == "idle":
            chip_configurator.config.begin_tentative_changes()

        self.__drag_state = "cancelled"

        checked_cursor = False
        if (pin is not None) and (self.__peripheral_item_cache is not None):
            for item in self.__peripheral_item_cache["valid_pin_mappings"]:
                if item["pin"] == pin and self.__drag_object_cache is not None:
                    # Change cursor to allow drop
                    self.__drag_object_cache.setDragCursor(
                        iconfunctions.get_qpixmap(
                            "icons/dialog/checkmark.png",
                            data.get_general_icon_pixelsize(),
                            data.get_general_icon_pixelsize(),
                        ),
                        qt.Qt.DropAction.MoveAction,
                    )
                    # Apply tentative mapping
                    mapping = item["mapping"]
                    mapping.apply()
                    self.__drag_state = "applied"
                    # Set cursor check flag
                    checked_cursor = True
                    break

        if not checked_cursor and self.__drag_object_cache is not None:
            # Change cursor to disallow drop
            self.__drag_object_cache.setDragCursor(
                iconfunctions.get_qpixmap(
                    "icons/dialog/cross.png",
                    data.get_general_icon_pixelsize(),
                    data.get_general_icon_pixelsize(),
                ),
                qt.Qt.DropAction.MoveAction,
            )
            if self.__drag_state == "cancelled":
                self.__drag_state = "idle"
                chip_configurator.config.rollback_tentative_changes()

    def __peripheral_dropped(self, pin: Optional[mcuconfig.Pin]) -> None:
        try:
            if self.__peripheral_item_cache is None:
                self.__debug_print("Peripheral item cache is not initialized!")
                return

            mapping_applied = False
            if pin is not None:
                for item in self.__peripheral_item_cache["valid_pin_mappings"]:
                    if item["pin"] == pin:
                        mapping = item["mapping"]

                        chip_configurator.config.commit_tentative_changes()
                        mapping_applied = True
                        self.__drag_state == "idle"

                        self.__debug_print(
                            f"Applied mapping '{str(mapping)}' to pin '{pin}'"
                        )
                        break

        finally:
            # Redraw the data
            chip_configurator.pin_overrides_clear()
            chip_configurator.set_draw_data()

    def __display_wheel_event(self, direction: str) -> None:
        # Change display view scale
        new_scale = None
        current_scale = chip_configurator.get_view_scale()
        if direction == "up":
            new_scale = current_scale * 1.1
        else:
            new_scale = current_scale / 1.1

        # Redraw and rescale only on scale changes
        if new_scale is not None:
            # Redraw
            chip_configurator.set_view_scale(new_scale)
            chip_configurator.set_draw_data()

    def __pin_clicked(self, pin_index: int, pin: mcuconfig.Pin) -> None:
        # Check if any pin options are available
        pin_mappings = chip_configurator.get_pin_mappings(pin)

        # Check mapping validity
        if len(pin_mappings) < 1:
            return

        # Reset the action triggered flag
        self.__action_triggered = False

        # Create the popup menu
        menu = gui.templates.basemenu.AdvancedMenu(self)
        menu.setToolTipsVisible(True)
        self.__stored_hovered_action = None
        menu.aboutToHide.connect(self.__pin_menu_hide)
        menu.aboutToShow.connect(self.__pin_menu_shown)
        menu.item_hovered.connect(self.__pin_menu_hover)
        menu.entered_item.connect(self.__pin_menu_item_enter)
        menu.left_item.connect(self.__pin_menu_item_leave)
        menu.item_triggered.connect(self.__pin_menu_action_triggered)
        menu.closed.connect(self.__pin_menu_close)

        # Create the actions
        for m in pin_mappings:
            self.__debug_print(m.pad, m.signal.full_name, m.signal.peripheral)
            action = qt.QAction(m.signal.full_name, menu)
            action.setData(
                {
                    "pin": pin,
                    "signal": m,
                }
            )
            action.setToolTip(str(m))
            menu.addAction(action)

        # Display the popup menu at cursor position
        cursor = qt.QCursor.pos()
        menu.popup(cursor)

    def __pin_menu_action_triggered(self, action: qt.QAction) -> None:
        if action is not None:
            action_data = action.data()
            pin = action_data["pin"]
            signal = action_data["signal"]
            self.__debug_print(f"pin_menu_action_triggered: {action.text()}")
            self.__action_triggered = True

    def __pin_menu_item_enter(self, item: qt.QAction) -> None:
        chip_configurator.config.begin_tentative_changes()

    def __pin_menu_item_leave(self, item: qt.QAction) -> None:
        self.__stored_hovered_action = None
        chip_configurator.config.rollback_tentative_changes()

    def __pin_menu_shown(self) -> None:
        pass

    def __pin_menu_close(self) -> None:
        self.__stored_hovered_action = None
        # Call the trigger-check function asyncronously
        qt.QTimer.singleShot(0, self.__check_if_action_triggered)

    def __pin_menu_hide(self) -> None:
        # Reset the stored action
        self.__stored_hovered_action = None
        # Call the trigger-check function asyncronously
        qt.QTimer.singleShot(0, self.__check_if_action_triggered)

    def __check_if_action_triggered(self):
        # Check if an action was triggered or the menu was just closed
        if self.__action_triggered:
            self.__action_triggered = False
            chip_configurator.config.commit_tentative_changes()
            self.__debug_print("Commited tentative changes.")

    def __pin_menu_hover(self, action: qt.QAction) -> None:
        #        self.__debug_print("hover", action)
        if self.__stored_hovered_action != action:
            self.__stored_hovered_action = action
            action_data = action.data()
            pin = action_data["pin"]
            mapping = action_data["signal"]
            mapping.apply()

    def __peripheral_clicked(
        self, pin: mcuconfig.Pin, name: str, signal: object
    ) -> None:
        self.__debug_print(
            "peripheral-clicked:", pin, name, signal.__class__.__name__
        )

        mappings = chip_configurator.config.sorted_signal_mappings(signal)

        # Reset the action triggered flag
        self.__action_triggered = False

        # Check mapping validity
        if len(mappings) < 1:
            return

        # Create the popup menu
        menu = gui.templates.basemenu.AdvancedMenu(self)
        #        menu.set_dragging(True)
        menu.setToolTipsVisible(True)
        self.__stored_hovered_action = None
        menu.aboutToHide.connect(self.__peripheral_menu_hide)
        menu.aboutToShow.connect(self.__peripheral_menu_shown)
        menu.item_hovered.connect(self.__peripheral_menu_hover)
        menu.entered_item.connect(self.__peripheral_menu_item_enter)
        menu.left_item.connect(self.__peripheral_menu_item_leave)
        menu.item_triggered.connect(self.__peripheral_menu_action_triggered)

        # Storage for the mapping to be removed
        remove_mapping = None

        # Create the actions
        found_pads = []
        for m in mappings:
            self.__debug_print(m.pad, m.signal.full_name, m.signal.peripheral)

            # Skip assignments to the same pin
            if chip_configurator.pin_data[pin]["text"] == m.pad.name:
                # Store mapping for removal first
                remove_mapping = m
                # Skip
                continue
            elif m.pad.name in found_pads:
                continue

            found_pads.append(m.pad.name)

            action = qt.QAction(
                "{} > {}".format(m.signal.full_name, m.pad), menu
            )
            action.setData(
                {
                    "pin": pin,
                    "mapping": m,
                    "type": "map",
                }
            )
            action.setToolTip(str(m))
            menu.addAction(action)

        # Add the 'Remove' option
        remove_action = qt.QAction("Remove mapping", menu)
        remove_action.setData(
            {
                "pin": pin,
                "mapping": remove_mapping,
                "type": "remove",
            }
        )
        remove_action.setToolTip("Remove this mapping completely")
        menu.addAction(remove_action)

        # Display the popup menu at cursor position
        cursor = qt.QCursor.pos()
        menu.popup(cursor)

    def __peripheral_menu_action_triggered(self, action: qt.QAction) -> None:
        if action is not None:
            action_data = action.data()
            pin = action_data["pin"]
            mapping = action_data["mapping"]
            self.__debug_print(f"pin_menu_action_triggered: {action.text()}")
            self.__action_triggered = True

    def __peripheral_menu_hover(self, action: qt.QAction) -> None:
        #        self.__debug_print("hover", action)
        if self.__stored_hovered_action != action:
            self.__stored_hovered_action = action
            action_data = action.data()
            pin = action_data["pin"]
            mapping = action_data["mapping"]
            type = action_data["type"]
            if type == "map":
                mapping.apply()
                self.__debug_print("MAPPING:", mapping.signal.full_name)
            elif type == "remove":
                mapping.pad.unmap()
                self.__debug_print("UNMAPPING:", mapping.signal.full_name)
            else:
                raise Exception(
                    f"[{self.__name__.__class__}] "
                    + f"Unknown peripheral action type: {type}"
                )

    def __peripheral_menu_action_triggered(self, action: qt.QAction) -> None:
        if action is not None:
            action_data = action.data()
            pin = action_data["pin"]
            mapping = action_data["mapping"]
            type = action_data["mapping"]
            self.__debug_print(
                f"peripheral_menu_action_triggered: {action.text()}"
            )
            self.__action_triggered = True

    def __peripheral_menu_item_enter(self, item: qt.QAction) -> None:
        chip_configurator.config.begin_tentative_changes()

    def __peripheral_menu_item_leave(self, item: qt.QAction) -> None:
        self.__stored_hovered_action = None
        chip_configurator.config.rollback_tentative_changes()

    def __peripheral_menu_shown(self) -> None:
        pass

    def __peripheral_menu_hide(self) -> None:
        # Reset the stored action
        self.__stored_hovered_action = None

        # Call the trigger-check function asyncronously
        qt.QTimer.singleShot(0, self.__check_if_action_triggered)

    def __create_empty_signal_row(self, signal) -> dict:
        empty_data = {
            # Name
            0: signal.name,
            1: {
                "type": "combobox-item",
                "keys": [],
                "values": [],
            },
            2: {
                "type": "combobox-item",
                "keys": [],
                "values": [],
            },
            3: {
                "type": "combobox-item",
                "keys": [],
                "values": [],
            },
            4: signal.description if signal.description.strip() != "" else "/",
        }
        return empty_data

    def __get_signal_data_for_table(self, signal) -> dict:
        new_data = self.__create_empty_signal_row(signal)
        # Check if pads are mapped and update accordingly
        sort_function = lambda s: [
            int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", s.name)
        ]
        mapped_pad_list = sorted(
            list(signal.mapped_pads),
            key=sort_function,
        )
        pads_text = ""
        pins_text = ""
        modes_text = ""
        if signal.is_enabled:
            if len(mapped_pad_list) > 0:
                pads_text = "/".join([p.name for p in mapped_pad_list])
                pins_text = "/".join(
                    [
                        (str(p.pin) if p.pin is not None else "")
                        for p in mapped_pad_list
                    ]
                )
                modes_text = "/".join(
                    [
                        (str(p.pin.mode.name) if p.pin is not None else "")
                        for p in mapped_pad_list
                    ]
                )

        # Pads
        pad_list = sorted(
            list(signal.possible_pads),
            key=sort_function,
        )
        pad_list.insert(0, None)
        pad_names = [p.name if p is not None else "none" for p in pad_list]
        # Pins
        pin_list = sorted(
            list(signal.possible_pins),
            key=sort_function,
        )
        pin_list.insert(0, None)
        pin_names = [p.name if p is not None else "none" for p in pin_list]
        # Modes
        mode_list = sorted(
            list(signal.possible_modes),
            key=sort_function,
        )
        mode_names = [m.name for m in mode_list]
        # Adjustments to default data values
        new_data[1] = {
            "type": "combobox-item",
            "keys": pad_names,
            "values": pad_list,
            "text": pads_text,
        }
        new_data[2] = {
            "type": "combobox-item",
            "keys": pin_names,
            "values": pin_list,
            "text": pins_text,
        }
        new_data[3] = {
            "type": "combobox-item",
            "keys": mode_names,
            "values": mode_list,
            "text": modes_text,
        }
        # Return the new data
        return new_data

    def callback_handler(
        self, callback_data: chipconfigurator.chipconfigurator.CallbackType
    ) -> None:
        #        self.__debug_print("callback_handler:", callback_data)

        # Handle callback
        match callback_data.type:
            case chipconfigurator.chipconfigurator.CallbackType.AddMapping:
                signal = callback_data.data["signal"]

                # Add the mapping to the image
                chip_configurator.peripheral_data_add(
                    pin=callback_data.data["pin"],
                    text=signal.full_name,
                    signal=signal,
                    id=callback_data.data["id"],
                    bg_color=self.peripheral_colors[signal.peripheral.kind][
                        "color"
                    ]["bg"],
                    fg_color=self.peripheral_colors[signal.peripheral.kind][
                        "color"
                    ]["fg"],
                    opacity=1.0,
                )

                # Add the signal to the signal table of the peripheral
                peripheral_name = signal.peripheral.name
                if self.__peripheral_cache is not None:
                    signal_table = self.__peripheral_cache[peripheral_name][
                        "signal-table"
                    ]

                    # Check if symbol with same name is already in the table
                    for i in range(signal_table.rowCount()):
                        cell = signal_table.item(i, 0)
                        if cell is not None:
                            if cell.text() == signal.name:
                                self.__debug_print(
                                    f"AddMapping add signal '{signal.name}' to table skipped. The signal is already in the table."
                                )
                                return

                    # Add the new signal
                    new_data = self.__get_signal_data_for_table(signal)
                    signal_table.add_row(list(new_data.values()))
                    signal_table.adjust_height()
                    signal_table.sortItems(
                        0, order=qt.Qt.SortOrder.AscendingOrder
                    )

                    self.__debug_print(f"Added mapping: {signal}")
                else:
                    self.__debug_print(
                        f"Cannot add signal '{signal}'! The peripheral cache isn't initialized yet!"
                    )

            case chipconfigurator.chipconfigurator.CallbackType.RemoveMapping:
                signal = callback_data.data["signal"]
                pin = callback_data.data["pin"]
                id = callback_data.data["id"]
                try:
                    if pin is not None:
                        # Remove the mapping from the image
                        chip_configurator.peripheral_data_remove(pin=pin, id=id)

                        # Remove the signal from signal table
                        peripheral_name = signal.peripheral.name
                        signal_table = self.__peripheral_cache[peripheral_name][
                            "signal-table"
                        ]
                        for row in range(signal_table.rowCount()):
                            item = signal_table.item(row, 0)
                            if item and item.text() == signal.name:
                                new_data = self.__get_signal_data_for_table(
                                    signal
                                )
                                signal_table.set_row(
                                    row, list(new_data.values())
                                )
                                signal_table.set_row_enabled(
                                    row, signal.is_enabled
                                )
                                self.__debug_print(
                                    f"Removed mapping: {signal} -> it's 'enabled' state is: {signal.is_enabled}"
                                )
                                break
                        else:
                            self.__debug_print(
                                f"Signal '{signal.name}' couldn't be found in the signal table!"
                            )
                except:
                    traceback.print_exc()
                    self.__debug_print(
                        f"Tried to remove signal '{signal.full_name}' from pin '{pin}', but couldn't !!!"
                    )

            case chipconfigurator.chipconfigurator.CallbackType.OnSignalEnabled:
                signal = callback_data.data["signal"]
                enabled = callback_data.data["enabled"]
                # Remove the signal from signal table
                peripheral_name = signal.peripheral.name
                signal_table = self.__peripheral_cache[peripheral_name][
                    "signal-table"
                ]
                for row in range(signal_table.rowCount()):
                    item = signal_table.item(row, 0)
                    if item and item.text() == signal.name:
                        new_data = self.__get_signal_data_for_table(signal)
                        signal_table.set_row(row, list(new_data.values()))
                        signal_table.set_row_enabled(row, signal.is_enabled)
                        self.__debug_print(
                            f"Signal '{signal.name}'s 'enable' state changed to: {enabled}"
                        )
                        break
                else:
                    self.__debug_print(
                        f"Signal '{signal.name}' couldn't be found in the signal table!"
                    )

            case chipconfigurator.chipconfigurator.CallbackType.OnSignalMapped:
                signal = callback_data.data["signal"]
                pads = callback_data.data["pads"]

                if self.__peripheral_cache is None:
                    return

                # Update the signal data in the signal table
                peripheral_name = signal.peripheral.name
                signal_table = self.__peripheral_cache[peripheral_name][
                    "signal-table"
                ]
                for row in range(signal_table.rowCount()):
                    item = signal_table.item(row, 0)
                    if item and item.text() == signal.name:
                        new_data = self.__get_signal_data_for_table(signal)
                        signal_table.set_row(row, list(new_data.values()))
                        signal_table.set_row_enabled(row, True)
                        break
                else:
                    self.__debug_print(
                        f"Signal '{signal.name}' couldn't be found in the signal table!"
                    )

            case chipconfigurator.chipconfigurator.CallbackType.OnAddSignal:
                signal = callback_data.data["signal"]
                peripheral_name = signal.peripheral.name
                signal_table = self.__peripheral_cache[peripheral_name][
                    "signal-table"
                ]

                # Check if symbol with same name is already in the table
                for i in range(signal_table.rowCount()):
                    if signal_table.item(i, 0).text() == signal.name:
                        self.__debug_print(
                            f"Adding signal '{signal.name}' to table skipped. The signal is already in the table."
                        )
                        return

                new_data = self.__get_signal_data_for_table(signal)
                signal_table.add_row(list(new_data.values()))
                signal_table.signals[signal_table.rowCount() - 1] = signal
                signal_table.set_row_enabled(
                    signal_table.rowCount() - 1, signal.is_enabled
                )
                self.__debug_print(f"OnAddSignal: '{signal.name}'")

            case chipconfigurator.chipconfigurator.CallbackType.OnRemoveSignal:
                signal = callback_data.data["signal"]
                self.__debug_print(f"OnRemoveSignal: '{signal.name}'")

            case chipconfigurator.chipconfigurator.CallbackType.SetMappingState:
                pin = callback_data.data["pin"]
                id = callback_data.data["id"]
                peripheral_data = chip_configurator.peripheral_data_get(pin, id)
                if peripheral_data is not None:
                    state = callback_data.data["state"]
                    peripheral_data["strike-through"] = False
                    if state == mcuconfig.MappingState.NORMAL:
                        peripheral_data["opacity"] = 1.0
                    elif state == mcuconfig.MappingState.TENTATIVELY_ADDED:
                        peripheral_data["opacity"] = 0.6
                    elif state == mcuconfig.MappingState.TENTATIVELY_REMOVED:
                        peripheral_data["opacity"] = 0.2
                        peripheral_data["strike-through"] = True
                    else:
                        raise Exception(
                            f"[{self.__class__.__name__}] "
                            + f"Unknown mapping state: {state}"
                        )
                    chip_configurator.peripheral_data_update(
                        pin, id, peripheral_data
                    )
                    self.__debug_print(f"State update for pin '{pin}'.")
                else:
                    self.__debug_print(
                        f"Could not get peripheral data on pin '{pin}' (id = '{id}') !!!"
                    )

            case chipconfigurator.chipconfigurator.CallbackType.OnPadModeChange:
                if self.__peripheral_cache is None:
                    return

                # Update the signal table
                pad = callback_data.data["pad"]
                for signal in pad.mapped_signals:
                    peripheral_name = signal.peripheral.name
                    signal_table = self.__peripheral_cache[peripheral_name][
                        "signal-table"
                    ]
                    for row in range(signal_table.rowCount()):
                        item = signal_table.item(row, 0)
                        if item and item.text() == signal.name:
                            new_data = self.__get_signal_data_for_table(signal)
                            signal_table.set_row(row, list(new_data.values()))
                            signal_table.set_row_enabled(row, signal.is_enabled)
                            self.__debug_print(
                                f"Signal '{signal.name}'s pad-mode state changed to: {pad.mode}"
                            )
                            break
                    else:
                        self.__debug_print(
                            f"Signal '{signal.name}' couldn't be found in the signal table!"
                        )

            case (
                chipconfigurator.chipconfigurator.CallbackType.OnPeripheralEnabled
            ):
                if self.__peripheral_cache is None:
                    return

                peripheral = callback_data.data["peripheral"]
                enabled = callback_data.data["enabled"]
                if peripheral.name in self.__peripheral_cache.keys():
                    if not peripheral.can_be_disabled:
                        self.__debug_print(
                            f"Peripheral '{peripheral.name}' cannot be disabled, skipping 'OnPeripheralEnabled'"
                        )
                        return

                    checkbox = self.__peripheral_cache[peripheral.name][
                        "checkbox"
                    ]
                    new_state = (
                        qt.Qt.CheckState.Checked
                        if enabled == True
                        else qt.Qt.CheckState.Unchecked
                    )
                    checkbox.setCheckState(new_state)
                    self.__debug_print(
                        f"Peripheral '{peripheral.name}' enabled state changed to: {enabled}"
                    )
                else:
                    self.__debug_print(
                        f"Peripheral '{peripheral.name}' is not in the cache, so 'enabled' for it cannot be changed!"
                    )

            case (
                chipconfigurator.chipconfigurator.CallbackType.OnSettingEnabled
            ):
                if self.__setting_widget_cache is not None:
                    setting = callback_data.data["setting"]
                    enabled = callback_data.data["enabled"]
                    if setting in self.__setting_widget_cache.keys():
                        widget = self.__setting_widget_cache[setting]
                        widget.setEnabled(enabled)
                        self.__debug_print(
                            f"Setting '{setting.label}' enabled state changed to: {enabled}"
                        )
                    else:
                        self.__debug_print(
                            f"Setting '{setting.label}' is not in the cache, so 'enabled' for it cannot be changed!"
                        )

            case chipconfigurator.chipconfigurator.CallbackType.OnSettingChange:
                if self.__setting_widget_cache is not None:
                    setting = callback_data.data["setting"]
                    value = callback_data.data["value"]
                    if setting in self.__setting_widget_cache.keys():
                        widget = self.__setting_widget_cache[setting]
                        self.__set_widget_value(widget, value)
                        self.__debug_print(
                            f"Setting '{setting.label}' value state changed to: {value}"
                        )
                    else:
                        self.__debug_print(
                            f"Setting '{setting.label}' is not in the cache, so 'value' for it cannot be changed!"
                        )

            case (
                chipconfigurator.chipconfigurator.CallbackType.OnUnsavedChanges
            ):
                changed = callback_data.data["changed"]
                self.show_save_indicator()

            case _:
                raise Exception(
                    f"[{self.__class__.__name__}] "
                    + f"Unhandled callback type: {callback_data.type}"
                )

        # Set new draw data and repaint if needed
        if callback_data.type in chipconfigurator.chipconfigurator.CallbackType:
            chip_configurator.set_draw_data()

    def show_save_indicator(self) -> None:
        self.save_button.show()

    def hide_save_indicator(self) -> None:
        self.save_button.hide()

    """
    Interface for child widgets
    """

    def load(self, *args, **kwargs) -> None:
        # Load the chip-configurator data
        chip_configurator.initialize(*args, **kwargs)

        # Load configuration
        chip_configurator.load(self.project_path)

        # Initialize all peripherals in the peripheral view
        self.__initialize_peripheral_list()

        # Initialize the clock tree view
        self.clock_tree_display.set_clock_draw_data()

        # Initially show the chip display
        self.stack_view.setCurrentWidget(self.chip_display)

        # Initialize the Config object for the ChipConfigurator
        chip_configurator.initialize_config()

    def save(self) -> None:
        chip_configurator.save(self.project_path)
        chip_configurator.generate(self.project_path)
        self.hide_save_indicator()

    def set_chip_draw_data(self, *args, **kwargs) -> None:
        self.chip_display.paint_widget.set_chip_draw_data(*args, **kwargs)

    def update_style(self) -> None:
        self.setStyleSheet(
            f'background: {data.theme["fonts"]["default"]["background"]}'
        )


"""
Chip display widgets
"""


class ChipInformationDisplay(qt.QScrollArea):
    mouse_wheel_event_signal = qt.pyqtSignal(str)

    def __debug_print(self, *msgs):
        if DEBUG_PRINTING:
            print(f"[{self.__class__.__name__}]", *msgs)

    def __init__(self, parent=None) -> None:
        # Super-class initialization
        super().__init__(parent=parent)

        # Initialize scroll-area properties
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.setVerticalScrollBarPolicy(qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.verticalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.horizontalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.setFrameShape(qt.QFrame.Shape.NoFrame)

        # Add the widget used for painting
        self.paint_widget = ChipPaintingWidget(parent=self)
        self.setWidget(self.paint_widget)
        # Set paint widget's minimum size
        self.paint_widget.setMinimumSize(qt.QSize(200, 200))

        # Enable mouse tracking
        self.set_mouse_tracking(True)

        # Add a custom event filter
        self.installEventFilter(self)

    def set_mouse_tracking(self, new_state: bool) -> None:
        self.setMouseTracking(new_state)
        self.viewport().setMouseTracking(new_state)
        self.paint_widget.setMouseTracking(new_state)

    def wheelEvent(self, event: qt.QWheelEvent) -> None:
        # Get the angleDelta from the QWheelEvent
        delta = event.angleDelta()

        if delta.y() > 0:
            # Up
            self.mouse_wheel_event_signal.emit("up")
        elif delta.y() < 0:
            # Down
            self.mouse_wheel_event_signal.emit("down")
        elif delta.x() > 0:
            # Right
            pass
        elif delta.x() < 0:
            # Lest
            pass

    __previous_position = None

    def eventFilter(self, obj, event):
        # if event.type() == qt.QEvent.Type.MouseButtonPress:
        #    self.__mouse_pressed = True
        # if event.type() == qt.QEvent.Type.MouseButtonRelease:
        #    self.__mouse_pressed = False
        # if event.type() == qt.QEvent.Type.HoverMove:
        #    print("hovermove")
        if not self.paint_widget.is_dragging_active():
            if (
                self.horizontalScrollBar().isVisible()
                or self.horizontalScrollBar().isVisible()
            ):
                if event.type() == qt.QEvent.Type.MouseMove:
                    current_position = qt.QCursor.pos()

                    if event.buttons() & qt.Qt.MouseButton.LeftButton:
                        if self.__previous_position is not None:
                            # Calculate the distance moved
                            delta = current_position - self.__previous_position
                            #                        distance = (delta.x()**2 + delta.y()**2)**0.5

                            # Log direction and distance
                            #                        print(f"Mouse moved: Δx={delta.x()}, Δy={delta.y()}, Distance={distance:.2f}")

                            # Adjust the scrollbars based on the delta
                            h_scrollbar = self.horizontalScrollBar()
                            v_scrollbar = self.verticalScrollBar()

                            h_scrollbar.setValue(
                                h_scrollbar.value() - delta.x()
                            )
                            v_scrollbar.setValue(
                                v_scrollbar.value() - delta.y()
                            )

                        self.__previous_position = current_position

                    else:
                        self.__previous_position = None
            else:
                self.__previous_position = None

        return super().eventFilter(obj, event)


class ChipPaintingWidget(qt.QWidget):
    pin_clicked_signal = qt.pyqtSignal(int, object)
    peripheral_clicked_signal = qt.pyqtSignal(object, str, object)
    peripheral_drag_start_signal = qt.pyqtSignal(dict, object)
    peripheral_drag_move_inside_pin_signal = qt.pyqtSignal(object, object)
    peripheral_dropped_signal = qt.pyqtSignal(object)

    def __debug_print(self, *msgs):
        if DEBUG_PRINTING:
            print(f"[{self.__class__.__name__}]", *msgs)

    def __init__(self, parent):
        super().__init__(parent)

        # Enable drop events for this widget
        self.setAcceptDrops(True)

        self.chip_draw_data = {}

    def dragEnterEvent(self, event: qt.QDragEnterEvent) -> None:
        event.acceptProposedAction()

    def dragMoveEvent(self, event: qt.QDragMoveEvent) -> None:
        # Check if move event is inside a pin
        position = event.position()
        for pin, rect in self.pin_drop_rect_positions.items():
            if rect.contains(position):
                self.peripheral_drag_move_inside_pin_signal.emit(pin, event)
                break
        else:
            self.peripheral_drag_move_inside_pin_signal.emit(None, event)

    def dragLeaveEvent(self, event: qt.QDragLeaveEvent) -> None:
        pass

    def dropEvent(self, event: qt.QDropEvent) -> None:
        # Accept the event
        event.acceptProposedAction()
        # Check if drop event is inside a pin
        position = event.position()
        for pin, rect in self.pin_drop_rect_positions.items():
            if rect.contains(position):
                self.peripheral_dropped_signal.emit(pin)
                break
        else:
            self.peripheral_dropped_signal.emit(None)

    def showEvent(self, event: qt.QShowEvent) -> None:
        super().showEvent(event)
        chip_configurator.set_draw_data()

    __peripheral_dragging = False

    def is_dragging_active(self) -> bool:
        return self.__peripheral_dragging

    def mousePressEvent(self, event: qt.QMouseEvent) -> None:
        super().mousePressEvent(event)

        self.__position_cache = None
        self.__peripheral_dragging = False

        # Get position
        position = event.position()

        # Check if mouse-click position is inside a peripheral bubble
        for index, rectangles in self.peripheral_rect_positions.items():
            for name, rect_data in rectangles.items():
                rect = rect_data["rectangle"]
                if rect.contains(position):
                    self.__position_cache = position
                    break

    __position_cache = None

    def mouseMoveEvent(self, event: qt.QMouseEvent) -> None:
        # Test for a drag
        if self.__position_cache is None:
            return
        elif not (event.buttons() & qt.Qt.MouseButton.LeftButton):
            return

        # Get position
        position = event.position()

        # Test for a drag
        diff = position - self.__position_cache
        drag_distance = 0
        if abs(diff.x()) > drag_distance or abs(diff.y()) > drag_distance:
            # Check if mouse-click position is inside a peripheral bubble
            for index, rectangles in self.peripheral_rect_positions.items():
                for name, rect_data in rectangles.items():
                    rect = rect_data["rectangle"]
                    signal = rect_data["signal"]
                    pin = rect_data["pin"]
                    peripheral_item = None
                    if pin in self.chip_draw_data["peripheral_data"].keys():
                        for id, value in self.chip_draw_data["peripheral_data"][
                            pin
                        ].items():
                            if name == value["text"]:
                                peripheral_item = value
                    if (
                        rect.contains(position)
                        and not self.__peripheral_dragging
                        and peripheral_item is not None
                    ):
                        # Set the internal states
                        self.__position_cache = None
                        self.__peripheral_dragging = True

                        # Create the drag object
                        drag = qt.QDrag(self)

                        # Get the global cursor position
                        global_mouse_pos = qt.QCursor.pos()
                        # Map the global position to the local QMenu coordinates
                        local_mouse_pos = self.mapFromGlobal(global_mouse_pos)

                        # Create the pixmap
                        pixmap = functions.text_to_pixmap_rectangle(
                            name,
                            local_mouse_pos,
                            text_color=peripheral_item.get("fg-color"),
                            bg_color=peripheral_item.get("bg-color"),
                            border_color="#000000",
                        )

                        # Set the drag information
                        mimedata = qt.QMimeData()
                        mimedata.setImageData(pixmap)
                        drag.setMimeData(mimedata)
                        drag.setPixmap(pixmap)

                        # Set the hotspot to the center of the pixmap
                        center_x = pixmap.width()
                        center_y = pixmap.height()
                        drag.setHotSpot(qt.QPoint(center_x, center_y))

                        # Signal the drag operation upwards
                        self.peripheral_drag_start_signal.emit(
                            peripheral_item, drag
                        )

                        drag.exec()
                        return

    def mouseReleaseEvent(self, event: qt.QMouseEvent) -> None:
        super().mouseReleaseEvent(event)

        if self.__peripheral_dragging:
            return

        # Get position
        position = event.position()

        # Check if mouse-click position is inside a pin
        for index, _data in self.pin_rect_positions.items():
            rect = _data["rectangle"]
            if rect.contains(position):
                pin = _data["pin"]
                self.pin_clicked_signal.emit(index, pin)
                break

        # Check if mouse-click position is inside a peripheral bubble
        for index, rectangles in self.peripheral_rect_positions.items():
            for name, rect_data in rectangles.items():
                rect = rect_data["rectangle"]
                signal = rect_data["signal"]
                pin = rect_data["pin"]
                if rect.contains(position):
                    self.peripheral_clicked_signal.emit(pin, name, signal)
                    break

    def readjust_size(self) -> None:
        package_type = self.chip_draw_data["main_rect_package_type"]
        new_width = self.chip_draw_data["main_rect_width"] + 600
        if package_type == mcuconfig.PackageType.SIDES2:
            new_height = self.chip_draw_data["main_rect_height"] + 200
        else:
            new_height = self.chip_draw_data["main_rect_height"] + 600
        self.setFixedSize(new_width, new_height)

    def set_chip_draw_data(self, chip_draw_data: Dict[str, any]) -> None:
        signiture = inspect.signature(self.__paint)
        function_parameters = set(
            [param.name for param in signiture.parameters.values()]
        )
        if function_parameters != set(chip_draw_data.keys()):
            raise Exception(
                "Chip draw-dictionary and painting function signature items are not the same! Fix this!"
            )

        # Set the data into the dictonary
        self.chip_draw_data = chip_draw_data
        # Force a repaint
        self.repaint()

    def paintEvent(self, event: qt.QPaintEvent) -> None:
        if self.chip_draw_data:
            # Expand the dictionary into the function arguments
            self.__paint(**self.chip_draw_data)

    def __paint(
        self,
        scale: float,
        bg_color: str,
        main_rect_package_type: mcuconfig.PackageType,
        main_rect_width: int,
        main_rect_height: int,
        main_rect_bg_color: str,
        main_rect_text: str,
        main_rect_logo: str,
        main_text_color: str,
        small_rect_height: int,
        num_rects_on_side: int,
        side_rect_fixed_gap: int,
        pin_border_color: str,
        chip_title_font_size: int,
        chip_title_font_family: str,
        pin_font_size: int,
        pin_font_family: str,
        pin_text_color: str,
        inner_pin_text_color: str,
        pin_data: Dict[int, str],
        peripheral_data: Dict[mcuconfig.Pin, Dict[str, Any]],
    ) -> None:
        # Readjust the widget size
        self.readjust_size()

        # Initialize the painter object
        painter = qt.QPainter(self)

        # Set the widget's background color
        painter.fillRect(self.rect(), qt.QColor(bg_color))

        # Adjust width if chip text is too wide
        painter.setFont(qt.QFont(chip_title_font_family, chip_title_font_size))
        font_metrics = painter.fontMetrics()
        main_text_width = font_metrics.horizontalAdvance(main_rect_text)
        main_text_height = font_metrics.height()
        if (main_rect_width - main_text_width) < 20:
            main_rect_width = int(main_text_width * 1.4)

        # Draw the main rectangle
        x = (self.width() - main_rect_width) // 2
        y = (self.height() - main_rect_height) // 2
        painter.setBrush(qt.QColor(main_rect_bg_color))
        painter.setPen(qt.Qt.PenStyle.NoPen)
        painter.drawRect(x, y, main_rect_width, main_rect_height)
        # Draw the circle indicating the corner where the pin count starts
        painter.setRenderHint(qt.QPainter.RenderHint.Antialiasing, True)
        painter.setPen(qt.QColor(main_text_color))
        diagonal_length = int(24 * scale)
        painter.drawEllipse(x + 2, y + 2, diagonal_length, diagonal_length)
        painter.setRenderHint(qt.QPainter.RenderHint.Antialiasing, False)
        # Draw the main rectangle logo
        main_text_offset = main_text_height
        pixmap = iconfunctions.get_qpixmap(main_rect_logo)
        size = int(main_text_width * 0.9)
        pixmap_x = int(x + (main_rect_width - size) / 2)
        pixmap_y = int(y + (main_rect_height - size) / 2) + main_text_offset
        pixmap_rect = qt.QRect(pixmap_x, pixmap_y, size, size)
        painter.drawPixmap(pixmap_rect, pixmap)
        # Draw the main rectangle text
        painter.setPen(qt.QColor(main_text_color))
        main_text_x = int(x + (main_rect_width - main_text_width) / 2)
        main_text_y = pixmap_y - main_text_offset
        painter.drawText(main_text_x, main_text_y, main_rect_text)

        # Set pen to 1-pixel wide black for borders, no brush for transparent background
        pen_width = 1
        pen = qt.QPen(qt.QColor(pin_border_color))
        pen.setWidth(pen_width)
        painter.setPen(pen)
        painter.setBrush(qt.Qt.BrushStyle.NoBrush)

        # Parameters for side rectangles
        small_rect_width = small_rect_height * 2.5

        # Calculate the total height/width of the set of rectangles and gaps
        total_rect_height = (
            num_rects_on_side * small_rect_height
            + (num_rects_on_side - 1) * side_rect_fixed_gap
        )
        total_rect_width = (
            num_rects_on_side * small_rect_height
            + (num_rects_on_side - 1) * side_rect_fixed_gap
        )

        # Set font for drawing the text
        painter.setFont(qt.QFont(pin_font_family, pin_font_size))
        text_color = qt.QColor(pin_text_color)  # Black for the side rectangles
        inner_text_color = qt.QColor(
            inner_pin_text_color
        )  # White for the main rectangle

        # Index counter for numbering the rectangles
        rect_index = 1
        pin_rect_positions = {}
        pin_drop_rect_positions = {}
        peripheral_rect_positions = {}
        pin_mode_rect_positions = {}

        pin_index_dict = {}
        for pin, pin_information in pin_data.items():
            index = pin_information["index"]
            pin_index_dict[index] = pin_information

        # Function to draw rectangles, text, the mirrored index inside the main rectangle,
        # and optional lines with dynamically sized rectangles at the end
        def loop_function(
            side: str,
            x_func: callable,
            y_func: callable,
            width: int,
            height: int,
            reverse: bool,
            rotate: bool,
            inner_x_func: callable,
            inner_y_func: callable,
            rotate_inner: bool = False,
            draw_line: bool = False,
        ) -> None:

            nonlocal rect_index

            _range = (
                reversed(range(num_rects_on_side))
                if reverse
                else range(num_rects_on_side)
            )
            for i in _range:
                # Get pin text
                if rect_index in pin_index_dict.keys():
                    item = pin_index_dict[rect_index]
                    pin = item.get("pin")
                    pin_text = item.get("text")
                    pin_opacity = item.get("opacity", 1.0)
                    if "bg-color" in item.keys():
                        pin_bg_color = item["bg-color"]
                    else:
                        pin_bg_color = None
                    if "fg-color" in item.keys():
                        pin_fg_color = item["fg-color"]
                    else:
                        pin_fg_color = None
                else:
                    pin = None
                    pin_text = str(rect_index)
                    pin_bg_color = None
                    pin_fg_color = None
                    pin_opacity = 1.0

                # Check width based on pin text and adjust if needed
                font_metrics = painter.fontMetrics()
                paint_width = width
                paint_height = height
                if width > height:
                    pin_text_width = font_metrics.horizontalAdvance(pin_text)
                    if pin_text_width > width:
                        paint_width = pin_text_width + 20
                else:
                    font_metrics = painter.fontMetrics()
                    pin_text_height = font_metrics.horizontalAdvance(pin_text)
                    if pin_text_height > height:
                        paint_height = pin_text_height + 20

                # Set opacity
                painter.setOpacity(pin_opacity)

                # Draw the pin rectangle
                rect = qt.QRectF(
                    x_func(i, paint_width),
                    y_func(i, paint_height),
                    paint_width,
                    paint_height,
                )
                painter.setPen(pen)
                if pin_bg_color is not None:
                    painter.setBrush(qt.QBrush(qt.QColor(pin_bg_color)))
                else:
                    painter.setBrush(qt.Qt.BrushStyle.NoBrush)
                painter.drawRect(rect)

                # Draw text in the border rectangles
                pin_text_color = text_color
                if pin_fg_color is not None:
                    pin_text_color = qt.QColor(pin_fg_color)
                painter.setPen(pin_text_color)
                if rotate:
                    painter.save()
                    painter.translate(rect.center())
                    painter.rotate(-90)
                    painter.drawText(
                        qt.QRectF(
                            -paint_height / 2,
                            -paint_height / 2,
                            paint_height,
                            paint_height,
                        ),
                        qt.Qt.AlignmentFlag.AlignCenter,
                        pin_text,
                    )
                    painter.restore()
                else:
                    painter.drawText(
                        rect, qt.Qt.AlignmentFlag.AlignCenter, pin_text
                    )

                # Draw the same index inside the main rectangle in white color
                font_metrics = painter.fontMetrics()
                inner_text_width = font_metrics.horizontalAdvance(
                    str(rect_index)
                )
                inner_text_height = font_metrics.height()
                painter.setPen(inner_text_color)
                inner_x = inner_x_func(i, paint_width)
                inner_y = inner_y_func(i, paint_width)
                inner_offset = 4
                if side == "left":
                    inner_x = rect.right() + inner_offset
                elif side == "bottom":
                    inner_y = rect.top() - small_rect_height - inner_offset
                elif side == "right":
                    inner_x = rect.left() - small_rect_height - inner_offset
                elif side == "top":
                    inner_y = rect.bottom() + inner_offset
                inner_rect = qt.QRectF(
                    inner_x, inner_y, small_rect_height, small_rect_height
                )

                if rotate_inner:
                    # Rotate the text inside the main rectangle for the top and bottom
                    painter.save()
                    painter.translate(inner_rect.center())
                    painter.rotate(-90)
                    painter.drawText(
                        qt.QRectF(
                            -small_rect_height / 2,
                            -small_rect_height / 2,
                            small_rect_height,
                            small_rect_height,
                        ),
                        qt.Qt.AlignmentFlag.AlignCenter,
                        str(rect_index),
                    )
                    painter.restore()
                else:
                    painter.drawText(
                        inner_rect,
                        qt.Qt.AlignmentFlag.AlignCenter,
                        str(rect_index),
                    )

                # Reset opacity
                painter.setOpacity(1.0)

                # Draw multiple peripheral text items
                peripheral_items = (
                    peripheral_data[pin]
                    if pin in peripheral_data.keys()
                    else {}
                )
                # Draw the pin-mode rectangle
                pin_mode_rect = None
                if len(peripheral_items) > 0:
                    # Set the size of the pin-mode rectangle
                    pin_mode_text = pin.mode.name
                    font_metrics = painter.fontMetrics()
                    pin_mode_text_width = font_metrics.horizontalAdvance(
                        pin_mode_text + "X"
                    )
                    # Determine the drawing offset from the pin
                    pin_mode_offset_x = 0
                    pin_mode_offset_y = 0
                    if side == "left":
                        pin_mode_offset_x = -pin_mode_text_width
                        pin_mode_width = pin_mode_text_width
                        pin_mode_height = paint_height
                    elif side == "bottom":
                        pin_mode_offset_y = paint_height
                        pin_mode_width = paint_width
                        pin_mode_height = pin_mode_text_width
                    elif side == "right":
                        pin_mode_offset_x = paint_width
                        pin_mode_width = pin_mode_text_width
                        pin_mode_height = paint_height
                    elif side == "top":
                        pin_mode_offset_y = -pin_mode_text_width
                        pin_mode_width = paint_width
                        pin_mode_height = pin_mode_text_width

                    painter.save()

                    # Paint the pin-mode rectangle
                    pin_mode_rect = qt.QRectF(
                        x_func(i, paint_width) + pin_mode_offset_x,
                        y_func(i, paint_height) + pin_mode_offset_y,
                        pin_mode_width,
                        pin_mode_height,
                    )
                    painter.setPen(pen)
                    brush_color = qt.QColor(
                        chipconfigurator.colors.get_pin_special_color(
                            "pin-mode"
                        )["color"]["bg"]
                    )
                    painter.setBrush(qt.QBrush(brush_color))
                    painter.drawRect(pin_mode_rect)

                    # Paint the pin-mode text
                    pen_color = qt.QColor(
                        chipconfigurator.colors.get_pin_special_color(
                            "pin-mode"
                        )["color"]["fg"]
                    )
                    painter.setPen(pen_color)
                    if rotate:
                        painter.translate(pin_mode_rect.center())

                        pin_mode_text_rect = qt.QRectF(
                            -pin_mode_rect.height() / 2,
                            -pin_mode_rect.width() / 2,
                            pin_mode_rect.height(),
                            pin_mode_rect.width(),
                        )
                        painter.rotate(-90)
                        painter.drawText(
                            pin_mode_text_rect,
                            qt.Qt.AlignmentFlag.AlignCenter,
                            pin_mode_text,
                        )
                    else:
                        painter.translate(pin_mode_rect.center())
                        pin_mode_text_rect = qt.QRectF(
                            -pin_mode_rect.width() / 2,
                            -pin_mode_rect.height() / 2,
                            pin_mode_rect.width(),
                            pin_mode_rect.height(),
                        )
                        painter.drawText(
                            pin_mode_text_rect,
                            qt.Qt.AlignmentFlag.AlignCenter,
                            pin_mode_text,
                        )

                    painter.restore()

                # Draw lines and peripheral text rectangles sequentially
                previous_end = None
                line_start = None
                for idx, item in enumerate(peripheral_items.items()):
                    key, peripheral_item = item
                    peripheral_text = peripheral_item.get("text")
                    peripheral_signal = peripheral_item.get("signal")
                    peripheral_bg_color = peripheral_item.get("bg-color")
                    peripheral_fg_color = peripheral_item.get("fg-color")
                    peripheral_opacity = peripheral_item.get("opacity", 1.0)
                    peripheral_strikethrough = peripheral_item.get(
                        "strike-through", False
                    )

                    if peripheral_text is not None:
                        painter.setOpacity(peripheral_opacity)

                        base_rect = qt.QRectF(rect)
                        if pin_mode_rect is not None:
                            base_rect = qt.QRectF(pin_mode_rect)

                        # Calculate line start and end positions for the first peripheral item
                        if idx == 0:
                            if rotate:  # Top and bottom
                                if side == "bottom":
                                    line_start = qt.QPointF(
                                        base_rect.center().x(),
                                        base_rect.bottom(),
                                    )
                                    previous_end = qt.QPointF(
                                        base_rect.center().x(),
                                        base_rect.bottom() + 10,
                                    )
                                else:
                                    line_start = qt.QPointF(
                                        base_rect.center().x(), base_rect.top()
                                    )
                                    previous_end = qt.QPointF(
                                        base_rect.center().x(),
                                        base_rect.top() - 10,
                                    )
                            else:  # Left and right
                                if side == "left":
                                    line_start = qt.QPointF(
                                        base_rect.left(), base_rect.center().y()
                                    )
                                    previous_end = qt.QPointF(
                                        base_rect.left() - 10,
                                        base_rect.center().y(),
                                    )
                                else:
                                    line_start = qt.QPointF(
                                        base_rect.right(),
                                        base_rect.center().y(),
                                    )
                                    previous_end = qt.QPointF(
                                        base_rect.right() + 10,
                                        base_rect.center().y(),
                                    )
                        else:
                            if rotate:  # Top and bottom
                                if side == "bottom":
                                    line_start = qt.QPointF(
                                        new_rect.center().x(), new_rect.bottom()
                                    )
                                    previous_end = qt.QPointF(
                                        new_rect.center().x(),
                                        new_rect.bottom() + 10,
                                    )
                                else:
                                    line_start = qt.QPointF(
                                        new_rect.center().x(), new_rect.top()
                                    )
                                    previous_end = qt.QPointF(
                                        new_rect.center().x(),
                                        new_rect.top() - 10,
                                    )
                            else:  # Left and right
                                if side == "left":
                                    line_start = qt.QPointF(
                                        new_rect.left(), new_rect.center().y()
                                    )
                                    previous_end = qt.QPointF(
                                        new_rect.left() - 10,
                                        new_rect.center().y(),
                                    )
                                else:
                                    line_start = qt.QPointF(
                                        new_rect.right(), new_rect.center().y()
                                    )
                                    previous_end = qt.QPointF(
                                        new_rect.right() + 10,
                                        new_rect.center().y(),
                                    )

                        if draw_line:
                            # Draw the line
                            painter.setPen(
                                qt.QPen(qt.QColor("#000000"), 1)
                            )  # Set the line color and width
                            painter.drawLine(line_start, previous_end)

                        # Measure the text to adjust the size of the new rectangle
                        font_metrics = painter.fontMetrics()
                        text_width = (
                            font_metrics.horizontalAdvance(peripheral_text) + 8
                        )  # Add padding
                        text_height = font_metrics.height() + 4  # Add padding

                        # Create the new rectangle at the end of the line
                        new_rect = None
                        if rotate:
                            if side == "bottom":
                                new_rect = qt.QRectF(
                                    previous_end.x() - text_height / 2,
                                    previous_end.y(),
                                    text_height,
                                    text_width,
                                )
                            else:  # Top side
                                new_rect = qt.QRectF(
                                    previous_end.x() - text_height / 2,
                                    previous_end.y() - text_width,
                                    text_height,
                                    text_width,
                                )
                        else:
                            if side == "left":
                                new_rect = qt.QRectF(
                                    previous_end.x() - text_width,
                                    previous_end.y() - text_height / 2,
                                    text_width,
                                    text_height,
                                )
                            else:  # Right side
                                new_rect = qt.QRectF(
                                    previous_end.x(),
                                    previous_end.y() - text_height / 2,
                                    text_width,
                                    text_height,
                                )

                        # Draw the new skewed rectangle with adjusted size
                        if rotate:
                            painter.setPen(pen)
                            painter.save()
                            painter.setRenderHint(
                                qt.QPainter.RenderHint.Antialiasing
                            )
                            skewed_new_rect = qt.QRectF(
                                0, 0, new_rect.width(), new_rect.height()
                            )
                            painter.translate(new_rect.x(), new_rect.y() - 2)
                            painter.shear(0, 0.2)
                            if peripheral_bg_color is not None:
                                painter.setBrush(
                                    qt.QBrush(qt.QColor(peripheral_bg_color))
                                )
                            else:
                                painter.setBrush(qt.Qt.BrushStyle.NoBrush)
                            pin_text_color = text_color
                            if peripheral_fg_color is not None:
                                pin_text_color = qt.QColor(peripheral_fg_color)
                            painter.drawRect(skewed_new_rect)
                            painter.restore()

                            painter.save()
                            painter.translate(new_rect.center())
                            painter.rotate(-90)

                            # Draw the same text inside the new rectangle
                            painter.setPen(pin_text_color)
                            text_rect = qt.QRectF(
                                -new_rect.height() / 2,
                                -new_rect.width() / 2,
                                new_rect.height(),
                                new_rect.width(),
                            )
                            painter.drawText(
                                text_rect,
                                qt.Qt.AlignmentFlag.AlignCenter,
                                peripheral_text,
                            )
                            if peripheral_strikethrough:
                                mid_y = int(text_rect.top() + text_height / 2)
                                painter.drawLine(
                                    int(text_rect.left()) + 4,
                                    mid_y,
                                    int(text_rect.left() + text_width) - 4,
                                    mid_y,
                                )

                            painter.restore()

                        else:
                            painter.setPen(pen)
                            painter.save()
                            painter.setRenderHint(
                                qt.QPainter.RenderHint.Antialiasing
                            )
                            skewed_new_rect = qt.QRectF(
                                0, 0, new_rect.width(), new_rect.height()
                            )
                            painter.translate(new_rect.x() + 2, new_rect.y())
                            painter.shear(-0.2, 0)
                            if peripheral_bg_color is not None:
                                painter.setBrush(
                                    qt.QBrush(qt.QColor(peripheral_bg_color))
                                )
                            else:
                                painter.setBrush(qt.Qt.BrushStyle.NoBrush)
                            pin_text_color = text_color
                            if peripheral_fg_color is not None:
                                pin_text_color = qt.QColor(peripheral_fg_color)
                            painter.drawRect(skewed_new_rect)
                            painter.restore()

                            # Draw the same text inside the new rectangle
                            painter.setPen(pin_text_color)
                            painter.drawText(
                                new_rect,
                                qt.Qt.AlignmentFlag.AlignCenter,
                                peripheral_text,
                            )
                            if peripheral_strikethrough:
                                text_rect = new_rect
                                mid_y = int(text_rect.top() + text_height / 2)
                                painter.drawLine(
                                    int(text_rect.left()) + 4,
                                    mid_y,
                                    int(text_rect.left() + text_width) - 4,
                                    mid_y,
                                )
                            # Restore the pen color
                            painter.setPen(text_color)

                        # Add the data to cache
                        if rect_index not in peripheral_rect_positions.keys():
                            peripheral_rect_positions[rect_index] = {}
                        peripheral_rect_positions[rect_index][
                            peripheral_text
                        ] = {
                            "rectangle": new_rect,
                            "signal": peripheral_signal,
                            "pin": pin,
                        }

                        # Update `previous_end` to chain the next rectangle
                        if rotate:
                            if side == "bottom":
                                line_start.setX(new_rect.bottom())
                                previous_end.setY(new_rect.bottom() + 10)
                            else:
                                line_start.setX(new_rect.top())
                                previous_end.setY(new_rect.top() - 10)
                        else:
                            if side == "left":
                                line_start.setX(new_rect.left())
                                previous_end.setX(new_rect.left() - 10)
                            else:
                                line_start.setX(new_rect.right())
                                previous_end.setX(new_rect.right() + 10)

                        painter.setOpacity(1.0)

                # Store the rectangle position
                pin_rect_positions[rect_index] = {
                    "rectangle": rect,
                    "pin": pin,
                }

                # Store the extended Drag&Drop rectangle
                drop_x = rect.x()
                drop_y = rect.y()
                drop_width = rect.width()
                drop_height = rect.height()
                if rotate:
                    if side == "bottom":
                        drop_height *= 4
                    else:
                        drop_y -= drop_height * 3
                        drop_height *= 4
                else:
                    if side == "left":
                        drop_x -= drop_width * 3
                        drop_width *= 4
                    else:
                        drop_width *= 4
                pin_drop_rect_positions[pin] = qt.QRectF(
                    drop_x, drop_y, drop_width, drop_height
                )

                # Increment side rectangle index
                rect_index += 1

        # Left
        if (
            main_rect_package_type == mcuconfig.PackageType.SIDES2
            or main_rect_package_type == mcuconfig.PackageType.SIDES4
        ):
            loop_function(
                side="left",
                x_func=lambda i, srw: x - srw - pen_width,
                y_func=lambda i, srw: y
                + (main_rect_height - total_rect_height) / 2
                + i * (small_rect_height + side_rect_fixed_gap),
                width=small_rect_width,
                height=small_rect_height,
                reverse=False,
                rotate=False,
                inner_x_func=lambda i, srw: x
                + pen_width
                + 2
                - srw,  # 2 pixels from the left border
                inner_y_func=lambda i, srw: y
                + (main_rect_height - total_rect_height) / 2
                + i * (small_rect_height + side_rect_fixed_gap),
                draw_line=True,
            )
        # Bottom
        if main_rect_package_type == mcuconfig.PackageType.SIDES4:
            loop_function(
                side="bottom",
                x_func=lambda i, srw: x
                + (main_rect_width - total_rect_width) / 2
                + i * (small_rect_height + side_rect_fixed_gap),
                y_func=lambda i, srw: y + main_rect_height,
                width=small_rect_height,
                height=small_rect_width,
                reverse=False,
                rotate=True,
                inner_x_func=lambda i, srw: x
                + (main_rect_width - total_rect_width) / 2
                + i * (small_rect_height + side_rect_fixed_gap),
                inner_y_func=lambda i, srw: y
                + main_rect_height
                - srw
                - 2
                + srw,  # 2 pixels from the bottom border
                draw_line=True,
            )
        # Right
        if (
            main_rect_package_type == mcuconfig.PackageType.SIDES2
            or main_rect_package_type == mcuconfig.PackageType.SIDES4
        ):
            loop_function(
                side="right",
                x_func=lambda i, srw: x + main_rect_width,
                y_func=lambda i, srw: y
                + (main_rect_height - total_rect_height) / 2
                + i * (small_rect_height + side_rect_fixed_gap),
                width=small_rect_width,
                height=small_rect_height,
                reverse=True,
                rotate=False,
                inner_x_func=lambda i, srw: x
                + main_rect_width
                - srw
                - 2
                + srw,  # 2 pixels from the right border
                inner_y_func=lambda i, srw: y
                + (main_rect_height - total_rect_height) / 2
                + i * (small_rect_height + side_rect_fixed_gap),
                draw_line=True,
            )
        # Top
        if main_rect_package_type == mcuconfig.PackageType.SIDES4:
            loop_function(
                side="top",
                x_func=lambda i, srw: x
                + (main_rect_width - total_rect_width) / 2
                + i * (small_rect_height + side_rect_fixed_gap),
                y_func=lambda i, srw: y - srw - pen_width,
                width=small_rect_height,
                height=small_rect_width,
                reverse=True,
                rotate=True,
                inner_x_func=lambda i, srw: x
                + (main_rect_width - total_rect_width) / 2
                + i * (small_rect_height + side_rect_fixed_gap),
                inner_y_func=lambda i, srw: y
                + 2
                - srw,  # 2 pixels from the top border
                draw_line=True,
            )

        self.pin_rect_positions = pin_rect_positions
        self.pin_drop_rect_positions = pin_drop_rect_positions
        self.peripheral_rect_positions = peripheral_rect_positions


#        # Readjust the widget size
#        self.readjust_size()


"""
Clock display widgets
"""


class ClockTreeInformationDisplay(qt.QScrollArea):
    def __debug_print(self, *msgs):
        if DEBUG_PRINTING:
            print(f"[{self.__class__.__name__}]", *msgs)

    def __init__(self, parent=None) -> None:
        # Super-class initialization
        super().__init__(parent=parent)

        # Initialize attributes
        self.__scale: float = 1.0

        # Initialize scroll-area properties
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.setVerticalScrollBarPolicy(qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.verticalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.horizontalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.setFrameShape(qt.QFrame.Shape.NoFrame)

        # Add the widget used for painting
        self.paint_widget = ClockTreePaintingWidget(parent=self)
        self.setWidget(self.paint_widget)
        # Set paint widget's minimum size
        self.paint_widget.setMinimumSize(qt.QSize(200, 200))

        # Enable mouse tracking
        self.set_mouse_tracking(True)

        # Add a custom event filter
        self.installEventFilter(self)

    def set_mouse_tracking(self, new_state: bool) -> None:
        self.setMouseTracking(new_state)
        self.viewport().setMouseTracking(new_state)
        self.paint_widget.setMouseTracking(new_state)

    def wheelEvent(self, event: qt.QWheelEvent) -> None:
        # Get the angleDelta from the QWheelEvent
        delta = event.angleDelta()

        if delta.y() > 0:
            # Up
            self.__scale = self.__scale * 1.1
            self.set_clock_draw_data()
        elif delta.y() < 0:
            # Down
            self.__scale = self.__scale / 1.1
            self.set_clock_draw_data()
        elif delta.x() > 0:
            # Right
            pass
        elif delta.x() < 0:
            # Lest
            pass

    __previous_position = None

    def eventFilter(self, obj, event):
        if (
            self.horizontalScrollBar().isVisible()
            or self.horizontalScrollBar().isVisible()
        ):
            if event.type() == qt.QEvent.Type.MouseMove:
                current_position = qt.QCursor.pos()

                if event.buttons() & qt.Qt.MouseButton.LeftButton:
                    if self.__previous_position is not None:
                        # Calculate the distance moved
                        delta = current_position - self.__previous_position

                        # Adjust the scrollbars based on the delta
                        h_scrollbar = self.horizontalScrollBar()
                        v_scrollbar = self.verticalScrollBar()

                        h_scrollbar.setValue(h_scrollbar.value() - delta.x())
                        v_scrollbar.setValue(v_scrollbar.value() - delta.y())

                    self.__previous_position = current_position

                else:
                    self.__previous_position = None
        else:
            self.__previous_position = None

        return super().eventFilter(obj, event)

    def set_clock_draw_data(self) -> None:
        # Fonts
        font_size = 10
        font_family = data.get_global_font_family()

        # Scaling
        base_scale = 6
        scale = self.__scale
        font_size = int(font_size * scale)

        self.paint_widget.set_clock_draw_data(
            {
                "base_scale": base_scale,
                "scale": scale,
                "bg_color": data.theme["fonts"]["default"]["background"],
                "line_color": "#000000",
                "font_family": font_family,
                "text_color": "#000000",
                "clocks": chip_configurator.part.clocks,
            }
        )


class ClockTreePaintingWidget(qt.QWidget):

    def __debug_print(self, *msgs):
        if DEBUG_PRINTING:
            print(f"[{self.__class__.__name__}]", *msgs)

    def __init__(self, parent):
        super().__init__(parent)

        # Enable drop events for this widget
        self.setAcceptDrops(True)

        self.clock_draw_data = {}

    def set_clock_draw_data(self, clock_draw_data: Dict[str, any]) -> None:
        signiture = inspect.signature(self.__paint)
        function_parameters = set(
            [param.name for param in signiture.parameters.values()]
        )
        if function_parameters != set(clock_draw_data.keys()):
            raise Exception(
                "ClockTree draw-dictionary and painting function signature "
                "items are not the same! Fix this!"
            )

        # Set the data into the dictonary
        self.clock_draw_data = clock_draw_data
        # Force a repaint
        self.repaint()

    def readjust_size(
        self,
        base_scale: float,
        scale: float,
        translation_offset: Optional[qt.QPoint] = None,
    ) -> Tuple[int, int]:
        new_width = int(150 * scale * base_scale)
        new_height = int(100 * scale * base_scale)
        if translation_offset is not None:
            new_width += int(translation_offset.x() * scale * base_scale)
            new_height += int(translation_offset.y() * scale * base_scale)
        self.setFixedSize(new_width, new_height)
        return new_width, new_height

    def paintEvent(self, event: qt.QPaintEvent) -> None:
        if self.clock_draw_data:
            # Expand the dictionary into the function arguments
            self.__paint(**self.clock_draw_data)

        else:
            painter = qt.QPainter(self)
            # Set the widget's background color
            painter.fillRect(
                self.rect(),
                qt.QColor(data.theme["fonts"]["default"]["background"]),
            )

    def __set_enabled_opacity(self, clock, painter):
        if clock.is_enabled:
            painter.setOpacity(1.0)
        else:
            painter.setOpacity(0.3)

    def __reset_opacity(self, painter):
        painter.setOpacity(1.0)

    def __paint(
        self,
        base_scale: float,
        scale: float,
        bg_color: str,
        line_color: str,
        font_family: str,
        text_color: str,
        clocks: Iterable[mcuconfig.Clock],
    ) -> None:
        translation_offset = qt.QPointF(40, 20)

        # Readjust the widget size
        widget_width, widget_height = self.readjust_size(
            base_scale, scale, translation_offset=translation_offset
        )

        # Brush and pen initialization
        brush_transparent = qt.QColor("#00000000")
        brush_internal_clock_bg = qt.QColor("#99e6eef6")
        brush_general_clock_bg = qt.QColor("#99fcfddf")
        brush_mux_clock_bg = qt.QColor("#99fcfddf")
        brush_multiply_divide_clock_bg = qt.QColor("#99fcfddf")
        brush_block_bg = qt.QColor("#ffffffff")
        brush_disabled_overlay = qt.QColor("#55000000")
        pen_transparent = qt.QColor("#00000000")
        pen_contact_point = qt.QColor("#ffff0000")
        line_color_used = qt.QColor(line_color)
        line_color_used_grayed = qt.QColor(line_color.replace("#", "#11"))

        # Initialize the painter object
        painter = qt.QPainter(self)

        painter.translate(translation_offset * base_scale * scale)

        # Set the widget's background color
        painter.fillRect(self.rect(), qt.QColor(bg_color))

        # Paint the grid
        painter.setBrush(brush_transparent)
        for x in range(
            int((widget_width + translation_offset.x()) / (base_scale * scale))
            + 1
        ):
            x_position = x * base_scale * scale
            x_position -= translation_offset.x() * base_scale * scale
            if x_position == 0:
                pen = qt.QPen(line_color_used)
                pen.setWidth(4)
                painter.setPen(pen)
            else:
                pen = qt.QPen(line_color_used_grayed)
                pen.setWidth(1)
                painter.setPen(pen)

            painter.drawLine(
                qt.QPointF(
                    x_position,
                    (-translation_offset.y()) * base_scale * scale,
                ),
                qt.QPointF(
                    x_position,
                    widget_height * base_scale * scale,
                ),
            )
        for y in range(
            int((widget_height + translation_offset.y()) / (base_scale * scale))
            + 1
        ):
            y_position = y * base_scale * scale
            y_position -= translation_offset.y() * base_scale * scale
            painter.drawLine(
                qt.QPointF(
                    (-translation_offset.x()) * base_scale * scale,
                    y_position,
                ),
                qt.QPointF(
                    widget_width * base_scale * scale,
                    y_position,
                ),
            )

        # Enable anti-aliasing
        painter.setRenderHint(qt.QPainter.RenderHint.Antialiasing, True)

        # Paint all the clocks
        for clock in clocks:
            clock_layout = clock.layout
            # print("-------------------------------")
            # print(clock_layout_x, clock_layout_y)
            # print(clock_layout.routes)
            # print(clock_layout.dots)
            # print(clock_layout.tags)
            # print(clock_layout.name_extension)

            clock_layout_x = clock_layout.x
            clock_layout_y = clock_layout.y
            if clock_layout.name_extension > 0:
                if clock_layout.orientation == mcuconfig.Orientation.LEFT:
                    clock_layout_x += clock_layout.name_extension
                else:
                    clock_layout_x -= clock_layout.name_extension

                # Draw the name extension
                # Line
                painter.setBrush(brush_transparent)
                painter.setPen(line_color_used)
                painter.drawLine(
                    qt.QPointF(
                        clock_layout.x * base_scale * scale,
                        clock_layout_y * base_scale * scale,
                    ),
                    qt.QPointF(
                        clock_layout_x * base_scale * scale,
                        clock_layout_y * base_scale * scale,
                    ),
                )
                # Text
                font_size = base_scale * scale
                painter.setFont(qt.QFont(font_family, int(font_size)))
                text = clock.name
                text_x = (clock_layout.x - len(text)) * base_scale * scale
                text_y = (clock_layout_y - 0.5) * base_scale * scale
                painter.drawText(
                    int(text_x),
                    int(text_y),
                    text,
                )

            bounding_rectangle: Optional[qt.QRectF] = None

            # Draw the clock element
            if type(clock) is mcuconfig.InternalClock:
                # self.__debug_print(clock.name, mcuconfig.InternalClock)
                # Bounding box
                painter.setBrush(brush_internal_clock_bg)
                painter.setPen(pen_transparent)
                bounding_box_width = 14.0
                bounding_box_height = 6.0
                bounding_box_x = clock_layout_x - bounding_box_width
                bounding_box_y = clock_layout_y - (bounding_box_height / 2)
                bounding_rectangle = qt.QRectF(
                    bounding_box_x * base_scale * scale,
                    bounding_box_y * base_scale * scale,
                    bounding_box_width * base_scale * scale,
                    bounding_box_height * base_scale * scale,
                )
                painter.drawRect(bounding_rectangle)

                self.__set_enabled_opacity(clock, painter)

                # Block 6 x 11
                painter.setBrush(brush_transparent)
                painter.setPen(line_color_used)
                block_width = 11.0
                block_height = 6.0
                block_x = clock_layout_x - block_width - 1.0
                block_y = clock_layout_y - (block_height / 2.0)
                rectangle = qt.QRectF(
                    block_x * base_scale * scale,
                    block_y * base_scale * scale,
                    block_width * base_scale * scale,
                    block_height * base_scale * scale,
                )
                painter.drawRect(rectangle)
                # Dividing line
                painter.setBrush(brush_transparent)
                painter.setPen(line_color_used)
                painter.drawLine(
                    qt.QPointF(
                        (clock_layout_x - 1.0) * base_scale * scale,
                        (clock_layout_y - 1.0) * base_scale * scale,
                    ),
                    qt.QPointF(
                        (clock_layout_x - 1.0 - block_width)
                        * base_scale
                        * scale,
                        (clock_layout_y - 1.0) * base_scale * scale,
                    ),
                )
                # Name text
                painter.setBrush(brush_transparent)
                painter.setPen(line_color_used)
                font_size = base_scale * scale
                painter.setFont(qt.QFont(font_family, int(font_size)))
                text_x = (block_x + 1.0) * base_scale * scale
                text_y = (block_y + 1.5) * base_scale * scale
                painter.drawText(
                    int(text_x),
                    int(text_y),
                    f"{clock.name}",
                )
                # Frequency text
                painter.setBrush(brush_transparent)
                painter.setPen(line_color_used)
                font_size = base_scale * scale
                painter.setFont(qt.QFont(font_family, int(font_size)))
                text_x = (block_x + 1.0) * base_scale * scale
                text_y = (block_y + 3.5) * base_scale * scale
                painter.drawText(
                    int(text_x),
                    int(text_y),
                    f"{int(clock.frequency / 1_000_000)}MHz",
                )
                # Connecting line
                painter.setBrush(brush_transparent)
                painter.setPen(line_color_used)
                painter.drawLine(
                    qt.QPointF(
                        clock_layout_x * base_scale * scale,
                        clock_layout_y * base_scale * scale,
                    ),
                    qt.QPointF(
                        (clock_layout_x - 1.0) * base_scale * scale,
                        clock_layout_y * base_scale * scale,
                    ),
                )

            elif type(clock) is mcuconfig.ExternalClock:
                # self.__debug_print(clock.name, mcuconfig.ExternalClock)

                if clock_layout.orientation == mcuconfig.Orientation.LEFT:
                    pass

                else:
                    # Bounding box
                    painter.setBrush(brush_internal_clock_bg)
                    painter.setPen(pen_transparent)
                    if (
                        clock.mode == mcuconfig.ExternalClockMode.EXTCLK
                        and clock.xout is None
                    ):
                        bounding_box_width = 31.0
                        bounding_box_height = 6.0
                    else:
                        bounding_box_width = 43.0
                        bounding_box_height = 7.0
                    bounding_box_x = clock_layout_x - bounding_box_width
                    bounding_box_y = clock_layout_y - (bounding_box_height / 2)
                    bounding_rectangle = qt.QRectF(
                        bounding_box_x * base_scale * scale,
                        bounding_box_y * base_scale * scale,
                        bounding_box_width * base_scale * scale,
                        bounding_box_height * base_scale * scale,
                    )
                    painter.drawRect(bounding_rectangle)

                    self.__set_enabled_opacity(clock, painter)

                    # Board clock
                    painter.setBrush(brush_block_bg)
                    painter.setPen(line_color_used)
                    board_width = 12.0
                    board_height = 6.0
                    board_x = clock_layout_x - bounding_box_width
                    if (
                        clock.mode == mcuconfig.ExternalClockMode.EXTCLK
                        and clock.xout is None
                    ):
                        board_y = clock_layout_y - (bounding_box_height / 2)
                    else:
                        board_y = clock_layout_y - (bounding_box_height / 2) + 1
                    rectangle = qt.QRectF(
                        board_x * base_scale * scale,
                        board_y * base_scale * scale,
                        board_width * base_scale * scale,
                        board_height * base_scale * scale,
                    )
                    painter.drawRect(rectangle)
                    # Board clock text
                    font_size = base_scale * scale
                    painter.setFont(qt.QFont(font_family, int(font_size)))
                    board_text_x = board_x + 1
                    board_text_y = board_y + 1.5
                    painter.drawText(
                        int(board_text_x * base_scale * scale),
                        int(board_text_y * base_scale * scale),
                        clock.mode.name,
                    )
                    # Separation line
                    painter.setBrush(brush_transparent)
                    painter.setPen(line_color_used)
                    from_x = board_x
                    from_y = board_y + 2
                    to_x = from_x + board_width
                    to_y = from_y
                    painter.drawLine(
                        qt.QPointF(
                            from_x * base_scale * scale,
                            from_y * base_scale * scale,
                        ),
                        qt.QPointF(
                            to_x * base_scale * scale,
                            to_y * base_scale * scale,
                        ),
                    )
                    # Board frequency text
                    font_size = base_scale * scale
                    painter.setFont(qt.QFont(font_family, int(font_size)))
                    board_frequency_x = board_x + 1
                    board_frequency_y = board_y + 3.5
                    painter.drawText(
                        int(board_frequency_x * base_scale * scale),
                        int(board_frequency_y * base_scale * scale),
                        "{}".format(clock.frequency),
                    )

                    if (
                        clock.mode == mcuconfig.ExternalClockMode.EXTCLK
                        and clock.xout is None
                    ):
                        # No internal circuit

                        # Line
                        painter.setBrush(brush_transparent)
                        painter.setPen(line_color_used)
                        from_x = board_x + board_width
                        from_y = board_y + (board_height / 2)
                        to_x = from_x + 16
                        to_y = from_y
                        painter.drawLine(
                            qt.QPointF(
                                from_x * base_scale * scale,
                                from_y * base_scale * scale,
                            ),
                            qt.QPointF(
                                to_x * base_scale * scale,
                                to_y * base_scale * scale,
                            ),
                        )
                        # Text
                        font_size = base_scale * scale
                        painter.setFont(qt.QFont(font_family, int(font_size)))
                        text = clock.xin.name
                        line_text_x = from_x + 1.0
                        line_text_y = board_y + 2.5
                        painter.drawText(
                            int(line_text_x * base_scale * scale),
                            int(line_text_y * base_scale * scale),
                            text,
                        )
                        # Compute triangle points
                        # Facing Right (▶)
                        painter.setBrush(line_color_used)
                        painter.setPen(line_color_used)
                        center_x = to_x * base_scale * scale
                        center_y = to_y * base_scale * scale
                        size = base_scale * scale  # Triangle size (height)
                        width = base_scale * scale  # Triangle width
                        points = [
                            qt.QPointF(center_x, center_y),  # Rightmost point
                            qt.QPointF(
                                center_x - width, center_y - size / 2
                            ),  # Top-left
                            qt.QPointF(
                                center_x - width, center_y + size / 2
                            ),  # Bottom-left
                        ]
                        # Draw the filled triangle
                        painter.drawPolygon(qt.QPolygonF(points))
                        # Connecting rectangle
                        painter.setBrush(brush_block_bg)
                        painter.setPen(line_color_used)
                        size = 2
                        connecting_rectangle_x = to_x
                        connecting_rectangle_y = to_y - 1.0
                        rectangle = qt.QRectF(
                            connecting_rectangle_x * base_scale * scale,
                            connecting_rectangle_y * base_scale * scale,
                            size * base_scale * scale,
                            size * base_scale * scale,
                        )
                        painter.drawRect(rectangle)
                        # Connecting line
                        painter.setBrush(brush_transparent)
                        painter.setPen(line_color_used)
                        connecting_line_from_x = connecting_rectangle_x + size
                        connecting_line_from_y = connecting_rectangle_y + 1.0
                        connecting_line_to_x = connecting_line_from_x + 1.0
                        connecting_line_to_y = connecting_line_from_y
                        painter.drawLine(
                            qt.QPointF(
                                connecting_line_from_x * base_scale * scale,
                                connecting_line_from_y * base_scale * scale,
                            ),
                            qt.QPointF(
                                connecting_line_to_x * base_scale * scale,
                                connecting_line_to_y * base_scale * scale,
                            ),
                        )

                    else:
                        # IN Signal
                        # Line
                        painter.setBrush(brush_transparent)
                        painter.setPen(line_color_used)
                        from_x = board_x + board_width
                        from_y = board_y + 1
                        to_x = from_x + 16
                        to_y = from_y
                        painter.drawLine(
                            qt.QPointF(
                                from_x * base_scale * scale,
                                from_y * base_scale * scale,
                            ),
                            qt.QPointF(
                                to_x * base_scale * scale,
                                to_y * base_scale * scale,
                            ),
                        )
                        # Text
                        font_size = base_scale * scale
                        painter.setFont(qt.QFont(font_family, int(font_size)))
                        text = clock.xin.name
                        line_text_x = from_x + 1.0
                        line_text_y = board_y + 0.5
                        painter.drawText(
                            int(line_text_x * base_scale * scale),
                            int(line_text_y * base_scale * scale),
                            text,
                        )
                        # Compute triangle points
                        # Facing Right (▶)
                        painter.setBrush(line_color_used)
                        painter.setPen(line_color_used)
                        center_x = to_x * base_scale * scale
                        center_y = to_y * base_scale * scale
                        size = base_scale * scale  # Triangle size (height)
                        width = base_scale * scale  # Triangle width
                        points = [
                            qt.QPointF(center_x, center_y),  # Rightmost point
                            qt.QPointF(
                                center_x - width, center_y - size / 2
                            ),  # Top-left
                            qt.QPointF(
                                center_x - width, center_y + size / 2
                            ),  # Bottom-left
                        ]
                        # Draw the filled triangle
                        painter.drawPolygon(qt.QPolygonF(points))
                        # Connecting rectangle
                        painter.setBrush(brush_block_bg)
                        painter.setPen(line_color_used)
                        size = 2
                        connecting_rectangle_x = to_x
                        connecting_rectangle_y = to_y - 1.0
                        rectangle = qt.QRectF(
                            connecting_rectangle_x * base_scale * scale,
                            connecting_rectangle_y * base_scale * scale,
                            size * base_scale * scale,
                            size * base_scale * scale,
                        )
                        painter.drawRect(rectangle)
                        # Connecting line
                        painter.setBrush(brush_transparent)
                        painter.setPen(line_color_used)
                        connecting_line_from_x = connecting_rectangle_x + size
                        connecting_line_from_y = connecting_rectangle_y + 1.0
                        connecting_line_to_x = connecting_line_from_x + 1.0
                        connecting_line_to_y = connecting_line_from_y
                        painter.drawLine(
                            qt.QPointF(
                                connecting_line_from_x * base_scale * scale,
                                connecting_line_from_y * base_scale * scale,
                            ),
                            qt.QPointF(
                                connecting_line_to_x * base_scale * scale,
                                connecting_line_to_y * base_scale * scale,
                            ),
                        )

                        # OUT Signal
                        # Line
                        painter.setBrush(brush_transparent)
                        painter.setPen(line_color_used)
                        from_x = from_x
                        from_y = from_y + 4
                        to_x = from_x + 16
                        to_y = from_y
                        if clock.xout is not None:
                            painter.drawLine(
                                qt.QPointF(
                                    from_x * base_scale * scale,
                                    from_y * base_scale * scale,
                                ),
                                qt.QPointF(
                                    to_x * base_scale * scale,
                                    to_y * base_scale * scale,
                                ),
                            )
                        # Text
                        font_size = base_scale * scale
                        painter.setFont(qt.QFont(font_family, int(font_size)))
                        text = clock.xout.name
                        line_text_x = to_x - 1.0 - len(text)
                        line_text_y = board_y + 4.5
                        if clock.xout is not None:
                            painter.drawText(
                                int(line_text_x * base_scale * scale),
                                int(line_text_y * base_scale * scale),
                                text,
                            )
                        # Compute triangle points
                        # Facing Left (◀)
                        painter.setBrush(line_color_used)
                        painter.setPen(line_color_used)
                        center_x = from_x * base_scale * scale
                        center_y = from_y * base_scale * scale
                        size = base_scale * scale  # Triangle size (height)
                        width = base_scale * scale  # Triangle width
                        points = [
                            qt.QPointF(center_x, center_y),  # Leftmost point
                            qt.QPointF(
                                center_x + width, center_y - size / 2
                            ),  # Top-right
                            qt.QPointF(
                                center_x + width, center_y + size / 2
                            ),  # Bottom-right
                        ]
                        # Draw the filled triangle
                        if clock.xout is not None:
                            painter.drawPolygon(qt.QPolygonF(points))
                        # Connecting rectangle
                        painter.setBrush(brush_block_bg)
                        painter.setPen(line_color_used)
                        size = 2
                        connecting_rectangle_x = to_x
                        connecting_rectangle_y = to_y - 1.0
                        rectangle = qt.QRectF(
                            connecting_rectangle_x * base_scale * scale,
                            connecting_rectangle_y * base_scale * scale,
                            size * base_scale * scale,
                            size * base_scale * scale,
                        )
                        painter.drawRect(rectangle)
                        # Connecting line
                        painter.setBrush(brush_transparent)
                        painter.setPen(line_color_used)
                        connecting_line_from_x = connecting_rectangle_x + size
                        connecting_line_from_y = connecting_rectangle_y + 1.0
                        connecting_line_to_x = connecting_line_from_x + 1.0
                        connecting_line_to_y = connecting_line_from_y
                        painter.drawLine(
                            qt.QPointF(
                                connecting_line_from_x * base_scale * scale,
                                connecting_line_from_y * base_scale * scale,
                            ),
                            qt.QPointF(
                                connecting_line_to_x * base_scale * scale,
                                connecting_line_to_y * base_scale * scale,
                            ),
                        )

                        # Chip block
                        painter.setBrush(brush_block_bg)
                        painter.setPen(line_color_used)
                        chip_width = 11.0
                        chip_height = 6.0
                        chip_x = clock_layout_x - chip_width - 1
                        chip_y = clock_layout_y - (bounding_box_height / 2) + 1
                        rectangle = qt.QRectF(
                            chip_x * base_scale * scale,
                            chip_y * base_scale * scale,
                            chip_width * base_scale * scale,
                            chip_height * base_scale * scale,
                        )
                        painter.drawRect(rectangle)
                        # Chip clock text
                        font_size = base_scale * scale
                        painter.setFont(qt.QFont(font_family, int(font_size)))
                        chip_text_x = chip_x + 1
                        chip_text_y = chip_y + 1.5
                        painter.drawText(
                            int(chip_text_x * base_scale * scale),
                            int(chip_text_y * base_scale * scale),
                            clock.name,
                        )
                        # Separation line
                        painter.setBrush(brush_transparent)
                        painter.setPen(line_color_used)
                        from_x = chip_x
                        from_y = chip_y + 2
                        to_x = from_x + chip_width
                        to_y = from_y
                        painter.drawLine(
                            qt.QPointF(
                                from_x * base_scale * scale,
                                from_y * base_scale * scale,
                            ),
                            qt.QPointF(
                                to_x * base_scale * scale,
                                to_y * base_scale * scale,
                            ),
                        )
                        # Chip frequency text
                        font_size = base_scale * scale
                        painter.setFont(qt.QFont(font_family, int(font_size)))
                        chip_frequency_x = chip_x + 1
                        chip_frequency_y = chip_y + 3.5
                        painter.drawText(
                            int(chip_frequency_x * base_scale * scale),
                            int(chip_frequency_y * base_scale * scale),
                            "{}-{}".format(
                                clock.minimum_frequency, clock.maximum_frequency
                            ),
                        )

                        # Origin point connecting line
                        painter.setBrush(brush_transparent)
                        painter.setPen(line_color_used)
                        from_x = clock_layout_x
                        from_y = clock_layout_y
                        to_x = from_x - 1.0
                        to_y = from_y
                        painter.drawLine(
                            qt.QPointF(
                                from_x * base_scale * scale,
                                from_y * base_scale * scale,
                            ),
                            qt.QPointF(
                                to_x * base_scale * scale,
                                to_y * base_scale * scale,
                            ),
                        )

            elif type(clock) is mcuconfig.MuxClock:
                # self.__debug_print(clock.name, mcuconfig.MuxClock)
                number_of_inputs = len(list(clock.inputs))

                if clock_layout.orientation == mcuconfig.Orientation.LEFT:
                    # Bounding box
                    painter.setBrush(brush_mux_clock_bg)
                    painter.setPen(pen_transparent)
                    bounding_box_width = 4.0
                    bounding_box_height = (2 * (number_of_inputs - 1)) + 4
                    bounding_box_x = clock_layout_x
                    bounding_box_y = clock_layout_y - (bounding_box_height / 2)
                    bounding_rectangle = qt.QRectF(
                        bounding_box_x * base_scale * scale,
                        bounding_box_y * base_scale * scale,
                        bounding_box_width * base_scale * scale,
                        bounding_box_height * base_scale * scale,
                    )
                    painter.drawRect(bounding_rectangle)

                    self.__set_enabled_opacity(clock, painter)

                    # Border lines
                    painter.setBrush(brush_transparent)
                    painter.setPen(line_color_used)
                    point_list = (
                        (
                            (clock_layout_x + 1.0, bounding_box_y + 1.0),
                            (
                                clock_layout_x + 1.0,
                                bounding_box_y + bounding_box_height - 1.0,
                            ),
                        ),
                        (
                            (
                                clock_layout_x + 1.0,
                                bounding_box_y + bounding_box_height - 1.0,
                            ),
                            (
                                clock_layout_x + 3.0,
                                bounding_box_y + bounding_box_height,
                            ),
                        ),
                        (
                            (
                                clock_layout_x + 3.0,
                                bounding_box_y + bounding_box_height,
                            ),
                            (
                                clock_layout_x + 3.0,
                                bounding_box_y,
                            ),
                        ),
                        (
                            (
                                clock_layout_x + 3.0,
                                bounding_box_y,
                            ),
                            (clock_layout_x + 1.0, bounding_box_y + 1.0),
                        ),
                    )
                    line_list = []
                    for point_0, point_1 in point_list:
                        line_list.append(
                            qt.QLineF(
                                qt.QPointF(
                                    point_0[0] * base_scale * scale,
                                    point_0[1] * base_scale * scale,
                                ),
                                qt.QPointF(
                                    point_1[0] * base_scale * scale,
                                    point_1[1] * base_scale * scale,
                                ),
                            )
                        )
                    painter.drawLines(line_list)
                    # Dots
                    painter.setBrush(brush_transparent)
                    painter.setPen(line_color_used)
                    dot_scale = base_scale / 3 * scale
                    for i in range(number_of_inputs):
                        x = bounding_box_x + 2.0
                        y = bounding_box_y + (2.0 * (i + 1))
                        point = qt.QPointF(
                            x * base_scale * scale, y * base_scale * scale
                        )
                        painter.drawEllipse(point, dot_scale, dot_scale)
                    # Connecting Lines
                    painter.setBrush(brush_transparent)
                    painter.setPen(line_color_used)
                    point_list = []
                    # Left side
                    for i in range(number_of_inputs):
                        point_list.append(
                            (
                                (
                                    clock_layout_x + bounding_box_width - 1.0,
                                    bounding_box_y + (2.0 * (i + 1)),
                                ),
                                (
                                    clock_layout_x + bounding_box_width,
                                    bounding_box_y + (2.0 * (i + 1)),
                                ),
                            )
                        )
                    # Right connecting line
                    point_list.append(
                        (
                            (clock_layout_x, clock_layout_y),
                            (clock_layout_x + 1.0, clock_layout_y),
                        )
                    )
                    line_list = []
                    for point_0, point_1 in point_list:
                        line_list.append(
                            qt.QLineF(
                                qt.QPointF(
                                    point_0[0] * base_scale * scale,
                                    point_0[1] * base_scale * scale,
                                ),
                                qt.QPointF(
                                    point_1[0] * base_scale * scale,
                                    point_1[1] * base_scale * scale,
                                ),
                            )
                        )
                    painter.drawLines(line_list)

                else:
                    # Bounding box
                    painter.setBrush(brush_general_clock_bg)
                    painter.setPen(pen_transparent)
                    bounding_box_width = 4.0
                    bounding_box_height = (2 * (number_of_inputs - 1)) + 4
                    bounding_box_x = clock_layout_x - bounding_box_width
                    bounding_box_y = clock_layout_y - (bounding_box_height / 2)
                    bounding_rectangle = qt.QRectF(
                        bounding_box_x * base_scale * scale,
                        bounding_box_y * base_scale * scale,
                        bounding_box_width * base_scale * scale,
                        bounding_box_height * base_scale * scale,
                    )
                    painter.drawRect(bounding_rectangle)

                    self.__set_enabled_opacity(clock, painter)

                    # Border lines
                    painter.setBrush(brush_transparent)
                    painter.setPen(line_color_used)
                    point_list = (
                        (
                            (
                                clock_layout_x - bounding_box_width + 1.0,
                                bounding_box_y,
                            ),
                            (
                                clock_layout_x - bounding_box_width + 3.0,
                                bounding_box_y + 1.0,
                            ),
                        ),
                        (
                            (
                                clock_layout_x - bounding_box_width + 3.0,
                                bounding_box_y + 1.0,
                            ),
                            (
                                clock_layout_x - bounding_box_width + 3.0,
                                bounding_box_y + bounding_box_height - 1.0,
                            ),
                        ),
                        (
                            (
                                clock_layout_x - bounding_box_width + 3.0,
                                bounding_box_y + bounding_box_height - 1.0,
                            ),
                            (
                                clock_layout_x - bounding_box_width + 1.0,
                                bounding_box_y + bounding_box_height,
                            ),
                        ),
                        (
                            (
                                clock_layout_x - bounding_box_width + 1.0,
                                bounding_box_y + bounding_box_height,
                            ),
                            (
                                clock_layout_x - bounding_box_width + 1.0,
                                bounding_box_y,
                            ),
                        ),
                    )
                    line_list = []
                    for point_0, point_1 in point_list:
                        line_list.append(
                            qt.QLineF(
                                qt.QPointF(
                                    point_0[0] * base_scale * scale,
                                    point_0[1] * base_scale * scale,
                                ),
                                qt.QPointF(
                                    point_1[0] * base_scale * scale,
                                    point_1[1] * base_scale * scale,
                                ),
                            )
                        )
                    painter.drawLines(line_list)
                    # Dots
                    painter.setBrush(brush_transparent)
                    painter.setPen(line_color_used)
                    dot_scale = base_scale / 3 * scale
                    for i in range(number_of_inputs):
                        x = bounding_box_x + 2.0
                        y = bounding_box_y + (2.0 * (i + 1))
                        point = qt.QPointF(
                            x * base_scale * scale, y * base_scale * scale
                        )
                        painter.drawEllipse(point, dot_scale, dot_scale)
                    # Connecting Lines
                    painter.setBrush(brush_transparent)
                    painter.setPen(line_color_used)
                    point_list = []
                    # Left side
                    for i in range(number_of_inputs):
                        point_list.append(
                            (
                                (
                                    clock_layout_x - bounding_box_width,
                                    bounding_box_y + (2.0 * (i + 1)),
                                ),
                                (
                                    clock_layout_x - bounding_box_width + 1.0,
                                    bounding_box_y + (2.0 * (i + 1)),
                                ),
                            )
                        )
                    # Right connecting line
                    point_list.append(
                        (
                            (clock_layout_x, clock_layout_y),
                            (clock_layout_x - 1.0, clock_layout_y),
                        )
                    )
                    line_list = []
                    for point_0, point_1 in point_list:
                        line_list.append(
                            qt.QLineF(
                                qt.QPointF(
                                    point_0[0] * base_scale * scale,
                                    point_0[1] * base_scale * scale,
                                ),
                                qt.QPointF(
                                    point_1[0] * base_scale * scale,
                                    point_1[1] * base_scale * scale,
                                ),
                            )
                        )
                    painter.drawLines(line_list)

            elif (
                type(clock) is mcuconfig.MultipliedClock
                or type(clock) is mcuconfig.DividedClock
            ):
                # self.__debug_print(clock.name, mcuconfig.MultipliedClock)

                if clock_layout.orientation == mcuconfig.Orientation.LEFT:
                    # Bounding box
                    painter.setBrush(brush_multiply_divide_clock_bg)
                    painter.setPen(pen_transparent)
                    bounding_box_width = 8.0
                    bounding_box_height = 2.0
                    bounding_box_x = clock_layout_x
                    bounding_box_y = clock_layout_y - (bounding_box_height / 2)
                    bounding_rectangle = qt.QRectF(
                        bounding_box_x * base_scale * scale,
                        bounding_box_y * base_scale * scale,
                        bounding_box_width * base_scale * scale,
                        bounding_box_height * base_scale * scale,
                    )
                    painter.drawRect(bounding_rectangle)

                    self.__set_enabled_opacity(clock, painter)

                    # Block 6 x 2
                    painter.setBrush(brush_transparent)
                    painter.setPen(line_color_used)
                    block_width = 6.0
                    block_height = 2.0
                    block_x = clock_layout_x + 1.0
                    block_y = clock_layout_y - (block_height / 2.0)
                    rectangle = qt.QRectF(
                        block_x * base_scale * scale,
                        block_y * base_scale * scale,
                        block_width * base_scale * scale,
                        block_height * base_scale * scale,
                    )
                    painter.drawRect(rectangle)
                    # Name text
                    font_size = base_scale * scale
                    painter.setFont(qt.QFont(font_family, int(font_size)))
                    text_x = (block_x) * base_scale * scale
                    text_y = (block_y + 1.5) * base_scale * scale
                    painter.drawText(
                        int(text_x),
                        int(text_y),
                        f"{clock.name}",
                    )
                    # Connecting line - right
                    painter.setBrush(brush_transparent)
                    painter.setPen(line_color_used)
                    painter.drawLine(
                        qt.QPointF(
                            clock_layout_x * base_scale * scale,
                            clock_layout_y * base_scale * scale,
                        ),
                        qt.QPointF(
                            (clock_layout_x + 1.0) * base_scale * scale,
                            clock_layout_y * base_scale * scale,
                        ),
                    )
                    # Connecting line - left
                    painter.setBrush(brush_transparent)
                    painter.setPen(line_color_used)
                    painter.drawLine(
                        qt.QPointF(
                            (clock_layout_x + bounding_box_width)
                            * base_scale
                            * scale,
                            clock_layout_y * base_scale * scale,
                        ),
                        qt.QPointF(
                            (clock_layout_x + bounding_box_width - 1.0)
                            * base_scale
                            * scale,
                            clock_layout_y * base_scale * scale,
                        ),
                    )

                else:
                    # Bounding box
                    painter.setBrush(brush_multiply_divide_clock_bg)
                    painter.setPen(pen_transparent)
                    bounding_box_width = 8.0
                    bounding_box_height = 2.0
                    bounding_box_x = clock_layout_x - bounding_box_width
                    bounding_box_y = clock_layout_y - (bounding_box_height / 2)
                    bounding_rectangle = qt.QRectF(
                        bounding_box_x * base_scale * scale,
                        bounding_box_y * base_scale * scale,
                        bounding_box_width * base_scale * scale,
                        bounding_box_height * base_scale * scale,
                    )
                    painter.drawRect(bounding_rectangle)

                    self.__set_enabled_opacity(clock, painter)

                    # Block 6 x 2
                    painter.setBrush(brush_transparent)
                    painter.setPen(line_color_used)
                    block_width = 6.0
                    block_height = 2.0
                    block_x = clock_layout_x - block_width - 1.0
                    block_y = clock_layout_y - (block_height / 2.0)
                    rectangle = qt.QRectF(
                        block_x * base_scale * scale,
                        block_y * base_scale * scale,
                        block_width * base_scale * scale,
                        block_height * base_scale * scale,
                    )
                    painter.drawRect(rectangle)
                    # Name text
                    font_size = base_scale * scale
                    painter.setFont(qt.QFont(font_family, int(font_size)))
                    text_x = (block_x) * base_scale * scale
                    text_y = (block_y + 1.5) * base_scale * scale
                    painter.drawText(
                        int(text_x),
                        int(text_y),
                        f"{clock.name}",
                    )
                    # Connecting line - right
                    painter.setBrush(brush_transparent)
                    painter.setPen(line_color_used)
                    painter.drawLine(
                        qt.QPointF(
                            clock_layout_x * base_scale * scale,
                            clock_layout_y * base_scale * scale,
                        ),
                        qt.QPointF(
                            (clock_layout_x - 1.0) * base_scale * scale,
                            clock_layout_y * base_scale * scale,
                        ),
                    )
                    # Connecting line - left
                    painter.setBrush(brush_transparent)
                    painter.setPen(line_color_used)
                    painter.drawLine(
                        qt.QPointF(
                            (clock_layout_x - bounding_box_width)
                            * base_scale
                            * scale,
                            clock_layout_y * base_scale * scale,
                        ),
                        qt.QPointF(
                            (clock_layout_x - bounding_box_width + 1.0)
                            * base_scale
                            * scale,
                            clock_layout_y * base_scale * scale,
                        ),
                    )

            else:
                self.__debug_print(
                    f"Unknown clock type to draw: '{type(clock)}' ! Skipping drawing it!"
                )
                continue

            self.__reset_opacity(painter)

            # Draw x at the clock's base coordinates
            painter.setBrush(brush_transparent)
            painter.setPen(pen_contact_point)
            # Define the center point
            center_x, center_y = clock_layout.x, clock_layout.y
            size = base_scale / 2 * scale  # Width and height of the rectangle
            # Calculate the top-left corner to center the rectangle on (10,10)
            top_left_x = (center_x * base_scale * scale) - size / 2
            top_left_y = (center_y * base_scale * scale) - size / 2
            # Draw the "X" using two diagonal lines
            painter.drawLine(
                qt.QPointF(top_left_x, top_left_y),
                qt.QPointF(top_left_x + size, top_left_y + size),
            )  # \
            painter.drawLine(
                qt.QPointF(top_left_x + size, top_left_y),
                qt.QPointF(top_left_x, top_left_y + size),
            )  # /

            # Draw routes
            painter.setBrush(brush_transparent)
            painter.setPen(line_color_used)
            for route in clock_layout.routes:
                point_list = []
                # non_scaled_point_list = []
                for point in route:
                    try:
                        x = point[0] * base_scale * scale
                    except:
                        x = 0
                        self.__debug_print(
                            f"Clock '{clock.name}' has invalid route coordinates!"
                        )
                    try:
                        y = point[1] * base_scale * scale
                    except:
                        y = 0
                        self.__debug_print(
                            f"Clock '{clock.name}' has invalid route coordinates!"
                        )
                    point_list.append(qt.QPointF(x, y))
                    # non_scaled_point_list.append((point[0], point[1]))
                    if len(point_list) == 2:
                        painter.drawLine(*point_list)
                        # painter.drawText(
                        #    int(point_list[0].x()),
                        #    int(point_list[0].y()),
                        #    f"({non_scaled_point_list[0][0]}, {non_scaled_point_list[0][1]})",
                        # )
                        # painter.drawText(
                        #    int(point_list[1].x()),
                        #    int(point_list[1].y()),
                        #    f"({non_scaled_point_list[1][0]}, {non_scaled_point_list[1][1]})",
                        # )
                        point_list = [point_list[1]]
                        # non_scaled_point_list = [non_scaled_point_list[1]]
                # painter.drawLines(point_list)

            # Dots
            painter.setBrush(line_color_used)
            painter.setPen(line_color_used)
            dot_scale = base_scale / 3 * scale
            for dot in clock_layout.dots:
                try:
                    x = dot[0] * base_scale * scale
                except:
                    x = 0
                    self.__debug_print(
                        f"Clock '{clock.name}' has invalid dot coordinates!"
                    )
                try:
                    y = dot[1] * base_scale * scale
                except:
                    y = 0
                    self.__debug_print(
                        f"Clock '{clock.name}' has invalid dot coordinates!"
                    )
                point = qt.QPointF(x, y)
                painter.drawEllipse(point, dot_scale, dot_scale)

            # Tags
            font_size = base_scale * scale
            for tag in clock_layout.tags:
                x = tag[0]
                y = tag[1]
                orientation = tag[2]

                if orientation == mcuconfig.Orientation.LEFT:
                    # Bounding box
                    painter.setBrush(brush_general_clock_bg)
                    painter.setPen(pen_transparent)
                    bounding_box_width = 12.0
                    bounding_box_height = 2.0
                    bounding_box_x = x
                    bounding_box_y = y - 1.0
                    bounding_rectangle = qt.QRectF(
                        bounding_box_x * base_scale * scale,
                        bounding_box_y * base_scale * scale,
                        bounding_box_width * base_scale * scale,
                        bounding_box_height * base_scale * scale,
                    )
                    painter.drawRect(bounding_rectangle)
                    # Lines
                    painter.setBrush(brush_transparent)
                    painter.setPen(line_color_used)
                    point_list = (
                        ((x, y), (x + 1.0, y)),
                        ((x + 1.0, y), (x + 2.0, y + 1.0)),
                        ((x + 2.0, y + 1.0), (x + bounding_box_width, y + 1.0)),
                        (
                            (x + bounding_box_width, y + 1.0),
                            (x + bounding_box_width, y - 1.0),
                        ),
                        ((x + bounding_box_width, y - 1.0), (x + 2.0, y - 1.0)),
                        ((x + 2.0, y - 1.0), (x + 1.0, y)),
                    )
                    line_list = []
                    for point_0, point_1 in point_list:
                        line_list.append(
                            qt.QLineF(
                                qt.QPointF(
                                    point_0[0] * base_scale * scale,
                                    point_0[1] * base_scale * scale,
                                ),
                                qt.QPointF(
                                    point_1[0] * base_scale * scale,
                                    point_1[1] * base_scale * scale,
                                ),
                            )
                        )
                    painter.drawLines(line_list)
                else:
                    pass
                # Text
                painter.setFont(qt.QFont(font_family, int(font_size)))
                painter.drawText(
                    int((x + 2.5) * base_scale * scale),
                    int((y + 0.5) * base_scale * scale),
                    clock.name,
                )

            # Sinks
            for sink in clock_layout.sinks:
                # Define the center point
                center_x, center_y = (
                    sink.x * base_scale * scale,
                    sink.y * base_scale * scale,
                )
                size = base_scale * scale  # Triangle size (height)
                width = base_scale * scale  # Triangle width
                text_x_offset = 0.5 * base_scale * scale
                text_height_offset = base_scale * scale / 2

                # Compute triangle points
                if clock_layout.orientation == mcuconfig.Orientation.LEFT:
                    # Facing Left (◀)
                    points = [
                        qt.QPointF(
                            center_x - width / 2, center_y
                        ),  # Leftmost point
                        qt.QPointF(
                            center_x + width / 2, center_y - size / 2
                        ),  # Top-right
                        qt.QPointF(
                            center_x + width / 2, center_y + size / 2
                        ),  # Bottom-right
                    ]
                    text_x = (
                        center_x
                        - width / 2
                        - painter.fontMetrics().horizontalAdvance(sink.label)
                        - text_x_offset
                    )  # Position text to the left
                else:
                    # Facing Right (▶)
                    points = [
                        qt.QPointF(
                            center_x + width / 2, center_y
                        ),  # Rightmost point
                        qt.QPointF(
                            center_x - width / 2, center_y - size / 2
                        ),  # Top-left
                        qt.QPointF(
                            center_x - width / 2, center_y + size / 2
                        ),  # Bottom-left
                    ]
                    text_x = (
                        center_x + width / 2 + text_x_offset
                    )  # Position text to the right

                # Draw the filled triangle
                painter.drawPolygon(qt.QPolygonF(points))

                # Draw the text
                painter.drawText(
                    int(text_x), int(center_y + text_height_offset), sink.label
                )

        painter.setRenderHint(qt.QPainter.RenderHint.Antialiasing, False)
