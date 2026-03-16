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
##  Dialog for importing projects from different origins
##
from typing import *
import os, functools, importlib, threading, traceback
import qt
import data
import purefunctions
import functions
import iconfunctions
import serverfunctions
import gui.templates.generaldialog
import gui.templates.widgetgenerator
import gui.dialogs.popupdialog
import gui.helpers.buttons
import gui.stylesheets.scrollbar
import gui.stylesheets.groupbox
import hardware_api.hardware_api as _hardware_api_
import gui.helpers.buttons as _buttons_
import hardware_api.board_unicum as _board_unicum_
import hardware_api.chip_unicum as _chip_unicum_
import gui.stylesheets.checkbox as _cb_
import helpdocs.help_texts as _ht_
import beetle_console.importer_console as _importer_console_
import hardware_api.various

if TYPE_CHECKING:
    import gui.templates
    import gui.stylesheets.button
    import gui.helpers.advancedcombobox
from various.kristofstuff import *


class CheckDot(qt.QPushButton):
    def __init__(
        self,
        parent: Optional[qt.QWidget],
        click_func: Callable,
    ) -> None:
        super().__init__(parent)
        self.__on = False
        self.clicked.connect(click_func)  # type: ignore
        self.sync_widg(False, False, None, None)
        return

    def sync_widg(
        self,
        refreshlock: bool,
        force_stylesheet: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        assert threading.current_thread() is threading.main_thread()
        size = int(data.get_general_icon_pixelsize())
        self.setStyleSheet(
            _cb_.get_checkdot_stylesheet(on=self.__on, size=size)
        )
        self.setFixedSize(size, size)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        if callback is not None:
            callback(callbackArg)
        return

    def set_on(self, on: bool) -> None:
        self.__on = on
        return

    def is_on(self) -> bool:
        return self.__on


def get_button_size():
    return data.get_general_icon_pixelsize()


class GeneralWizard(gui.templates.generaldialog.GeneralDialog):

    def __init__(self, parent, *args, **kwargs) -> None:
        """"""
        super().__init__(parent, statusbar=True, scroll_layout=True)
        self.button_groupbox: Optional[qt.QGroupBox] = None
        self.cancel_button: Optional[gui.helpers.buttons.CustomPushButton] = (
            None
        )
        self.next_button: Optional[gui.helpers.buttons.CustomPushButton] = None

        # Window should not be always-on-top
        self.setWindowFlags(
            self.windowFlags() & ~qt.Qt.WindowType.WindowStaysOnTopHint
        )

        # Set the main layout
        self.main_layout: qt.QVBoxLayout = cast(
            qt.QVBoxLayout,
            gui.templates.widgetgenerator.create_layout(
                vertical=True,
                margins=(2, 2, 2, 2),
            ),
        )
        self.main_groupbox.setLayout(self.main_layout)
        return

    def self_destruct(
        self,
        death_already_checked: bool = False,
        additional_clean_list: Optional[List[str]] = None,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """"""
        super().self_destruct(
            death_already_checked=death_already_checked,
            additional_clean_list=additional_clean_list,
            callback=callback,
            callbackArg=callbackArg,
        )
        return

    def showEvent(self, event: qt.QShowEvent) -> None:
        """"""
        self.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.MinimumExpanding,
            )
        )
        self.center_to_parent()

    def update_check_size(self) -> None:
        """Check the size of the dialog and adjust accordingly."""
        new_size = qt.create_qsize(
            int(self.size().width() * 1.1),
            int(self.size().height() * 1.0),
        )
        position = self.pos()
        if position.x() < 0:
            position = qt.create_qpoint(80, position.y())
        if position.y() < 0:
            position = qt.create_qpoint(position.x(), 80)
        self.setGeometry(
            int(position.x()),
            int(position.y()),
            int(new_size.width()),
            int(new_size.height()),
        )
        return

    def add_page_buttons(self) -> None:
        """"""
        button_size = get_button_size() * 4
        self.button_groupbox = (
            gui.templates.widgetgenerator.create_groupbox_with_layout(
                vertical=False,
                borderless=True,
            )
        )
        self.button_groupbox.setSizePolicy(
            qt.QSizePolicy.Policy.Minimum,
            qt.QSizePolicy.Policy.Minimum,
        )
        layout = self.button_groupbox.layout()
        layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        layout.setSpacing(40)
        layout.setContentsMargins(30, 5, 30, 5)
        self.main_layout.addWidget(self.button_groupbox)

        # * CANCEL button
        self.cancel_button = gui.helpers.buttons.CustomPushButton(
            parent=self,
            text="CANCEL",
            bold=True,
        )
        self.cancel_button.setStyleSheet(
            gui.stylesheets.button.get_simple_toggle_stylesheet()
        )
        self.cancel_button.setFixedHeight(int(button_size * 0.4))
        self.cancel_button.setMinimumWidth(int(button_size))
        self.cancel_button.clicked.connect(self.close)
        self.button_groupbox.layout().addWidget(self.cancel_button)

        # * NEXT button
        self.next_button = gui.helpers.buttons.CustomPushButton(
            parent=self,
            text="NEXT",
            bold=True,
        )
        self.next_button.setStyleSheet(
            gui.stylesheets.button.get_simple_toggle_stylesheet()
        )
        self.next_button.setFixedHeight(int(button_size * 0.4))
        self.next_button.setMinimumWidth(button_size)
        if hasattr(self, "show_next_page"):
            self.next_button.clicked.connect(self.show_next_page)
        self.next_button.setEnabled(False)
        self.button_groupbox.layout().addWidget(self.next_button)
        return

    def delete_page_buttons(self) -> None:
        """"""
        if self.button_groupbox is None:
            # The buttons are already deleted
            return
        _button_groupbox: qt.QGroupBox = self.button_groupbox
        self.button_groupbox = None
        self.main_layout.removeWidget(_button_groupbox)
        functions.clean_layout(_button_groupbox.layout())
        _button_groupbox.setParent(None)  # noqa
        del _button_groupbox
        return

    def repurpose_cancel_next_buttons(
        self,
        cancel_name: Optional[str] = None,
        cancel_func: Optional[Callable] = None,
        cancel_en: Optional[bool] = None,
        next_name: Optional[str] = None,
        next_func: Optional[Callable] = None,
        next_en: Optional[bool] = None,
    ) -> None:
        """Rename and repurpose the default "Cancel" and "Next" buttons. :param
        cancel_name:     [Optional] New name for "Cancel" button. :param
        cancel_func:     [Optional] New function for "Cancel button. :param
        cancel_en:       [Optional] Enable "Cancel" button.

        :param next_name: [Optional] New name for "Next" button.
        :param next_func: [Optional] New function for "Next" button.
        :param next_en: [Optional] Enable "Next" button.
        """

        def discon_sig(signal):
            "Disconnect all connections from the given signal"
            # signal.disconnect() only breaks one connection at a time,
            # so loop to be safe.
            while True:
                try:
                    signal.disconnect()
                except TypeError:
                    break
            return

        if cancel_name is not None:
            self.cancel_button.setText(cancel_name)
        if cancel_func is not None:
            discon_sig(self.cancel_button.clicked)
            self.cancel_button.clicked.connect(cancel_func)
        if cancel_en is not None:
            self.cancel_button.setEnabled(cancel_en)
        if next_name is not None:
            self.next_button.setText(next_name)
        if next_func is not None:
            discon_sig(self.next_button.clicked)
            self.next_button.clicked.connect(next_func)
        if next_en is not None:
            self.next_button.setEnabled(next_en)
        return

    def create_helptext(
        self,
        parent: Optional[qt.QWidget] = None,
        text: Optional[str] = None,
        click_func: Optional[Callable] = None,
    ) -> Tuple[
        qt.QHBoxLayout,
        qt.QPushButton,
    ]:
        """

        :param parent:
        :param text:
        :param click_func:
        :return:
        """
        # * Widget
        text_color = data.theme["fonts"]["default"]["color"]
        lbl = _buttons_.RichTextPushButton(
            parent=parent,
            text=text,
        )
        lbl.clicked.connect(click_func)
        lbl.setMinimumHeight(data.get_general_icon_pixelsize())
        lbl.setStyleSheet(
            f"""
            QPushButton{{
                color: {text_color};
                margin: 0px 0px 0px 0px;
                padding: 0px 0px 0px 0px;
                background-color: transparent;
                border-style: none;
                text-align: left;
            }}
        """
        )
        lbl.setFont(data.get_general_font())

        # * QHBoxLayout()
        hlyt = qt.QHBoxLayout()
        hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        hlyt.setSpacing(5)
        hlyt.setContentsMargins(0, 0, 0, 0)
        hlyt.addWidget(lbl)

        return (hlyt, lbl)

    def create_check_option(
        self,
        text,
        additional_text=None,
        width=None,
        height=None,
    ):
        check_box = self._create_check_box(
            self, "ItemChbx", (get_button_size(), get_button_size())
        )
        text_color = data.theme["fonts"]["default"]["color"]
        lb = Label()
        lb.setFont(data.get_general_font())
        lb.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        lb.setWordWrap(True)
        lb.setMinimumWidth(400)
        lb.setText(text)
        lb.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        lb.click_signal.connect(lambda: check_box.toggle())
        if additional_text is not None:
            lb.setText("<b>" + text + "</b><br>" + additional_text)
        # Layout
        layout = qt.QHBoxLayout()
        layout.addWidget(check_box)
        layout.addSpacing(5)
        layout.addWidget(lb)
        layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        groupbox = qt.QGroupBox()
        groupbox.setLayout(layout)
        groupbox.setStyleSheet(
            f"""
            color: {text_color};
            border: 0px;
            font-family: {data.get_global_font_family()};
            font-size: {data.get_general_font_pointsize()}pt;
        """
        )
        groupbox.check_box = check_box
        groupbox.label = lb
        return groupbox

    def create_warning_line(
        self,
        parent: Optional[qt.QWidget] = None,
        text: Optional[str] = None,
        click_func: Optional[Callable] = None,
    ) -> Tuple[
        qt.QHBoxLayout,
        qt.QPushButton,
        qt.QPushButton,
    ]:
        """

        :param parent:
        :param text:
        :param click_func:
        :return:
        """
        # * Widget 1
        button = self.create_pushbutton(
            parent=None,
            icon_path="icons/dialog/warning.png",
            click_func=click_func,
        )
        button.setFixedSize(
            int(1.5 * data.get_general_icon_pixelsize()),
            int(1.5 * data.get_general_icon_pixelsize()),
        )

        # * Widget 2
        text_color = data.theme["fonts"]["default"]["color"]
        lbl = _buttons_.RichTextPushButton(
            parent=parent,
            text=text,
        )
        lbl.clicked.connect(click_func)
        lbl.setMinimumHeight(data.get_general_icon_pixelsize())
        lbl.setStyleSheet(
            f"""
            QPushButton{{
                color: {text_color};
                margin: 0px 0px 0px 0px;
                padding: 0px 0px 0px 0px;
                background-color: transparent;
                border-style: none;
                text-align: left;
            }}
        """
        )

        # * QHBoxLayout()
        hlyt = qt.QHBoxLayout()
        hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        hlyt.setSpacing(5)
        hlyt.setContentsMargins(0, 0, 0, 0)
        hlyt.addWidget(button)
        hlyt.addWidget(lbl)
        return (hlyt, button, lbl)

    def __get_combobox_widget(
        self,
        parent: Optional[qt.QWidget] = None,
        elements: Optional[List[Tuple[str, str]]] = None,
        elementchange_func: Optional[Callable] = None,
    ) -> gui.helpers.advancedcombobox.AdvancedComboBox:
        """

        :param parent:   Typically a QGroupBox().

        :param elements: Elements to be shown in the
                         combobox, eg:
            [
                (
                    'icons/tools/gnu_arm.png',
                    'gnu_arm_toolchain_9.3.1_9-2020-q2-update_32b',
                ),
                (
                    'icons/tools/gnu_avr.png',
                    'gnu_avr_toolchain_7.3.0_64b',
                ),
                (
                    'icons/tools/gnu_riscv.png',
                    'gnu_riscv_xpack_toolchain_8.3.0_2019.08.0_32b',
                ),
                (
                    'icons/tools/gnu_riscv.png',
                    'gnu_riscv_xpack_toolchain_8.3.0_2019.08.0_64b',
                ),
            ]

        :param elementchange_func:  Function to be called when the user changed
                                    the combobox selection

        :return: AdvancedComboBox() widget

        """
        combobox: gui.helpers.advancedcombobox.AdvancedComboBox = (
            gui.helpers.advancedcombobox.AdvancedComboBox(
                parent=parent,
                initial_item={
                    "name": "empty",
                    "widgets": (
                        {
                            "type": "text",
                            "text": "Select tool",
                        },
                    ),
                },
                image_size=data.get_general_icon_pixelsize(),
                contents_margins=(2, 2, 2, 2),
                spacing=4,
            )
        )
        for i, e in enumerate(elements):
            first_icon = e[0]
            htmltext = e[1]
            if len(e) > 2:
                second_icon = e[2]
            # Filter out only the text
            doc = qt.QTextDocument()
            doc.setHtml(htmltext)
            text = doc.toPlainText()
            # Filter out the text color
            color = "default"
            if "color:" in htmltext:
                start = htmltext.find("color:") + len("color:")
                end = start + 7
                color = htmltext[start:end]
            new_item = {
                "name": htmltext,
                "widgets": [
                    {
                        "type": "image",
                        "icon-path": first_icon,
                    },
                    {
                        "type": "text",
                        "text": text,
                        "color": color,
                    },
                ],
            }
            if len(e) > 2:
                size = int(data.get_general_icon_pixelsize() * 0.75)
                new_item["widgets"].append(
                    {
                        "type": "image",
                        "icon-path": second_icon,
                        "size": (size, size),
                    }
                )
            combobox.add_item(new_item)
        combobox.selection_changed.connect(elementchange_func)
        return combobox

    def create_dropdown_line(
        self,
        parent: Optional[qt.QWidget] = None,
        tool_tip: Optional[str] = None,
        elements: Optional[List[Tuple[str, str]]] = None,
        elementchange_func: Optional[Callable] = None,
        checkmarkclick_func: Optional[Callable] = None,
    ) -> Tuple[
        qt.QHBoxLayout,
        gui.helpers.advancedcombobox.AdvancedComboBox,
        qt.QPushButton,
    ]:
        """

        :param parent:   Typically a QGroupBox().

        :param tool_tip: Tooltip text to be shown when hovering over
                         the the AdvancedComboBox() widget.

        :param elements: Elements to be shown in the
                         combobox, eg:
            [
                (
                    'icons/tools/gnu_arm.png',
                    'gnu_arm_toolchain_9.3.1_9-2020-q2-update_32b',
                ),
                (
                    'icons/tools/gnu_avr.png',
                    'gnu_avr_toolchain_7.3.0_64b',
                ),
                (
                    'icons/tools/gnu_riscv.png',
                    'gnu_riscv_xpack_toolchain_8.3.0_2019.08.0_32b',
                ),
                (
                    'icons/tools/gnu_riscv.png',
                    'gnu_riscv_xpack_toolchain_8.3.0_2019.08.0_64b',
                ),
            ]

        :param elementchange_func:  Function to be called when the user changed
                                    the combobox selection

        :param checkmarkclick_func: Function to be called when the user clicked
                                    the checkmark button next to the combobox.

        :return:    A Tuple containing:
                        - QHBoxLayout()       ->  a horizontal layout
                        - AdvancedComboBox()  ->  the combobox
                        - QPushButton()       ->  the checkmark next to the
                                                  combobox

                    Note: the horizontal layout already contains the other
                    widgets in the given tuple.

        """
        # * Widget 1
        combobox = self.__get_combobox_widget(
            parent=parent,
            elements=elements,
            elementchange_func=elementchange_func,
        )
        # * Widget 2
        checkmark = self.create_pushbutton(
            parent=None,
            tool_tip=tool_tip,
            icon_path="icons/dialog/cross.png",
            click_func=checkmarkclick_func,
        )
        checkmark.setFixedSize(
            int(
                max(
                    data.get_general_icon_pixelsize(),
                    data.get_general_font_height(),
                )
            ),
            int(
                max(
                    data.get_general_icon_pixelsize(),
                    data.get_general_font_height(),
                )
            ),
        )
        # * QHBoxLayout()
        hlyt = qt.QHBoxLayout()
        hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        hlyt.setSpacing(5)
        hlyt.setContentsMargins(0, 0, 0, 0)
        hlyt.addWidget(combobox)
        hlyt.addWidget(checkmark)
        return (hlyt, combobox, checkmark)

    def create_selection_bar(
        self,
        gb_text,
        btn_text,
        tooltip,
        btn_icon,
        check_tooltip,
        actions,
        action_groups=None,
        custom_func=None,
        info_type=None,
        additional_function=None,
        create_check=True,
        insert_any=False,
    ):
        button_size = get_button_size()

        def info_func(clicked):
            _ht_.project_creation_info(self, info_type)

        gb = gui.templates.widgetgenerator.create_groupbox_with_layout_and_info_button(
            "Selection",
            gb_text,
            vertical=False,
            adjust_margins_to_text=True,
            info_size=button_size,
            info_func=info_func,
        )
        gb.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Fixed
        )

        gb.layout().setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        gb.setToolTip(tooltip)
        self._set_widget_message(gb, tooltip)
        min_width = functions.get_text_bounding_rect(("A" * 30)).width()
        gb.setMinimumWidth(min_width)
        lay = gb.layout()

        all_actions = [x for x in actions]

        # Reset option
        def reset_function(in_combobox, in_text, in_icon):
            in_combobox.set_selected_name("any")
            if additional_function is not None:
                additional_function(None, gb_text, in_text, in_icon)

        combobox = gui.templates.widgetgenerator.create_advancedcombobox(
            parent=gb,
            initial_item=None,
            contents_margins=(0, 0, 0, 0),
            spacing=0,
            image_size=(data.get_custom_tab_pixelsize() * 1.5),
            no_selection_icon=btn_icon,
            no_selection_text=btn_text,
        )
        combobox.set_items(actions, additional_function)
        combobox.setToolTip(tooltip)
        if custom_func is not None:
            combobox.selection_changed.connect(custom_func)
        gb.create_dropdown_menu = combobox.set_items

        lay.addWidget(combobox)
        lay.setAlignment(
            combobox,
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter,
        )

        # Check box that shows selection status
        if create_check:
            status_box = gui.templates.widgetgenerator.create_check_label(
                "StatusCheckBox",
                (get_button_size(), get_button_size()),
            )
            lay.addWidget(status_box)
            status_box.setToolTip(check_tooltip)
            gb.status_box = status_box
        gb.combobox = combobox
        gb.get_text = lambda *args: combobox.get_selected_item_name()
        gb.reset_selection = functools.partial(
            reset_function, combobox, btn_text, btn_icon
        )

        return gb

    def create_file_selection_line(
        self,
        parent: Optional[qt.QWidget] = None,
        tool_tip: Optional[str] = None,
        start_directory_fallback: Optional[str] = None,
        click_func: Optional[Callable] = None,
        checkmarkclick_func: Optional[Callable] = None,
        text_change_func: Optional[Callable] = None,
    ) -> Tuple[qt.QHBoxLayout, qt.QLineEdit, qt.QPushButton, qt.QPushButton]:
        """
        Create a horizontal 'line' of widgets:
            1. QLineEdit() widget:      file location
            2. QPushButton() widget:    file button
            3. QPushButton() widget:    green check or red cross

        Use the current QLineEdit() content as start location. If
        it's not a valid directory or file, use the fallback.

        """
        return gui.templates.widgetgenerator.create_file_selection_line(
            parent=parent,
            tool_tip=tool_tip,
            start_directory_fallback=start_directory_fallback,
            click_func=click_func,
            checkmarkclick_func=checkmarkclick_func,
            text_change_func=text_change_func,
            statusbar=self.statusbar,
        )

    def create_directory_selection_line(
        self,
        parent: Optional[qt.QWidget] = None,
        tool_tip: Optional[str] = None,
        start_directory_fallback: Optional[str] = None,
        click_func: Optional[Callable] = None,
        checkmarkclick_func: Optional[Callable] = None,
        text_change_func: Optional[Callable] = None,
    ) -> Tuple[
        qt.QHBoxLayout,
        qt.QLineEdit,
        _buttons_.CustomPushButton,
        _buttons_.CustomPushButton,
    ]:
        """
        Create a horizontal 'line' of widgets:
            1. QLineEdit() widget:      directory location
            2. QPushButton() widget:    directory button
            3. QPushButton() widget:    green check or red cross

        Use the current QLineEdit() content as start directory. If
        it's not a valid directory, use the fallback.

        """
        return gui.templates.widgetgenerator.create_directory_selection_line(
            parent=parent,
            tool_tip=tool_tip,
            start_directory_fallback=start_directory_fallback,
            click_func=click_func,
            checkmarkclick_func=checkmarkclick_func,
            text_change_func=text_change_func,
            statusbar=self.statusbar,
        )

    def create_btn_lbl(
        self,
        parent: Optional[qt.QWidget] = None,
        icon_path: Optional[str] = None,
        tool_tip: Optional[str] = None,
        text: str = "",
        click_func: Optional[Callable] = None,
    ) -> Tuple[
        qt.QHBoxLayout,
        qt.QPushButton,
        qt.QPushButton,
    ]:
        """Create a horizontal 'line' of widgets.

        They are combined in a QHBoxLayout().
        """
        # * Widget 1
        button = self.create_pushbutton(
            parent=None,
            tool_tip=tool_tip,
            icon_path=icon_path,
            click_func=click_func,
        )
        button.setFixedSize(
            int(data.get_general_icon_pixelsize()),
            int(data.get_general_icon_pixelsize()),
        )

        # * Widget 2
        text_color = data.theme["fonts"]["default"]["color"]
        lbl = _buttons_.RichTextPushButton(
            parent=parent,
            text=text,
        )
        lbl.clicked.connect(click_func)
        lbl.setMinimumHeight(data.get_general_icon_pixelsize())
        lbl.setStyleSheet(
            f"""
            QPushButton{{
                color: {text_color};
                margin: 0px 0px 0px 0px;
                padding: 0px 0px 0px 0px;
                background-color: transparent;
                border-style: none;
                text-align: left;
            }}
        """
        )

        # * QHBoxLayout()
        hlyt = qt.QHBoxLayout()
        hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        hlyt.setSpacing(5)
        hlyt.setContentsMargins(0, 0, 0, 0)
        hlyt.addWidget(button)
        hlyt.addWidget(lbl)

        return (hlyt, button, lbl)

    def create_btn_lbl_lineedit(
        self,
        parent: Optional[qt.QWidget] = None,
        icon_path: Optional[str] = None,
        tool_tip: Optional[str] = None,
        text: str = "",
        click_func: Optional[Callable] = None,
        text_change_func: Optional[Callable] = None,
    ) -> Tuple[qt.QHBoxLayout, qt.QPushButton, qt.QPushButton, qt.QLineEdit]:
        """Create a horizontal 'line' of widgets.

        They are combined in a QHBoxLayout().
        """
        # * Widget 1
        button = self.create_pushbutton(
            parent=None,
            tool_tip=tool_tip,
            icon_path=icon_path,
            click_func=click_func,
        )
        button.setFixedSize(
            int(data.get_general_icon_pixelsize()),
            int(data.get_general_icon_pixelsize()),
        )

        # * Widget 2
        text_color = data.theme["fonts"]["default"]["color"]
        lbl = qt.QPushButton(text)
        lbl.clicked.connect(click_func)
        lbl.setFixedHeight(int(data.get_general_icon_pixelsize()))
        lbl.setStyleSheet(
            f"""
            QPushButton{{
                color: {text_color};
                margin: 0px 0px 0px 0px;
                padding: 0px 0px 0px 0px;
                background-color: transparent;
                border-style: none;
            }}
        """
        )

        # * Widget 3
        lineedit = self.create_textbox(
            parent=None,
            text_change_func=text_change_func,
            h_size_policy=qt.QSizePolicy.Policy.Expanding,
            v_size_policy=qt.QSizePolicy.Policy.Expanding,
        )
        lineedit.setFixedHeight(int(data.get_general_icon_pixelsize()))

        # * QHBoxLayout()
        hlyt = qt.QHBoxLayout()
        hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        hlyt.setSpacing(5)
        hlyt.setContentsMargins(0, 0, 0, 0)
        hlyt.addWidget(button)
        hlyt.addWidget(lbl)
        hlyt.addWidget(lineedit)

        return (hlyt, button, lbl, lineedit)

    def create_checkdot_btn_lbl(
        self,
        parent: Optional[qt.QWidget] = None,
        icon_path: Optional[str] = None,
        tool_tip: Optional[str] = None,
        text: str = "",
        click_func: Optional[Callable] = None,
    ) -> Tuple[qt.QHBoxLayout, CheckDot, qt.QPushButton, qt.QPushButton]:
        """
        Create a horizontal 'line' of widgets that work together as a "selection line" in the wiz-
        ard. They are combined in a QHBoxLayout().
            1. CheckDot() widget:    selection dot
            2. QPushButton() widget: clickable button with icon (see parameter 'icon_path')
            3. QPushButton() widget: this is actually more a clickable label (see parameter 'text')

        Note: The 'click_func' callback is shared between the three widgets.

        :return:    This function returns a 4-element-Tuple. First element
                    is the QHBoxLayout() that holds the three widgets.
                    The remaining elements are the three widgets.
        """
        # * Widget 1
        checkdot = CheckDot(parent=None, click_func=click_func)

        # * Widget 2
        button = self.create_pushbutton(
            parent=None,
            tool_tip=tool_tip,
            icon_path=icon_path,
            click_func=click_func,
        )
        button.setFixedSize(
            int(data.get_general_icon_pixelsize()),
            int(data.get_general_icon_pixelsize()),
        )

        # * Widget 3
        text_color = data.theme["fonts"]["default"]["color"]
        lbl = qt.QPushButton(text)
        lbl.clicked.connect(click_func)
        lbl.setFixedHeight(int(data.get_general_icon_pixelsize()))
        lbl.setStyleSheet(
            f"""
        QPushButton{{
            color: {text_color};
            margin: 0px 0px 0px 0px;
            padding: 0px 0px 0px 0px;
            background-color: transparent;
            border-style: none;
        }}
        """
        )
        lbl.setFont(data.get_general_font())

        # * QHBoxLayout()
        hlyt = qt.QHBoxLayout()
        hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        hlyt.setSpacing(5)
        hlyt.setContentsMargins(0, 0, 0, 0)
        hlyt.addWidget(checkdot)
        hlyt.addWidget(button)
        hlyt.addWidget(lbl)

        return (hlyt, checkdot, button, lbl)

    def create_btn_lbl_dropdown_btn_btn(
        self,
        parent: Optional[qt.QWidget] = None,
        iconpath_btn0: Optional[str] = None,
        iconpath_btn1: Optional[str] = None,
        iconpath_btn2: Optional[str] = None,
        tooltip_btn0: Optional[str] = None,
        tooltip_btn1: Optional[str] = None,
        tooltip_btn2: Optional[str] = None,
        clickfunc_btn0: Optional[Callable] = None,
        clickfunc_btn1: Optional[Callable] = None,
        clickfunc_btn2: Optional[Callable] = None,
        text: Optional[str] = None,
        clickfunc_lbl: Optional[Callable] = None,
        dropdown_elements: Optional[List[Tuple[str, str]]] = None,
        changefunc_dropdown: Optional[Callable] = None,
    ) -> Tuple[
        qt.QHBoxLayout,
        qt.QPushButton,
        qt.QPushButton,
        gui.helpers.advancedcombobox.AdvancedComboBox,
        qt.QPushButton,
        qt.QPushButton,
    ]:
        """Create a horizontal 'line' of widgets. They are combined in a
        QHBoxLayout().

        > btn0:       [QPushButton]      Leftmost button. > lbl: [QPushButton]
        Label. > combobox:   [AdvancedComboBox] Dropdown widget. > btn1:
        [QPushButton]      Cloud button. > btn2: [QPushButton]      Red cross or
        green checkmark.
        """
        # * Button
        btn0 = self.create_pushbutton(
            parent=parent,
            tool_tip=tooltip_btn0,
            icon_path=iconpath_btn0,
            click_func=clickfunc_btn0,
        )
        btn0.setFixedSize(
            int(
                max(
                    data.get_general_icon_pixelsize(),
                    data.get_general_font_height(),
                )
            ),
            int(
                max(
                    data.get_general_icon_pixelsize(),
                    data.get_general_font_height(),
                )
            ),
        )

        # * Label
        text_color = data.theme["fonts"]["default"]["color"]
        lbl = _buttons_.RichTextPushButton(
            parent=parent,
            text=text,
        )
        lbl.clicked.connect(clickfunc_lbl)
        # lbl1.setMinimumHeight(data.get_general_icon_pixelsize())
        lbl.setSizePolicy(
            qt.QSizePolicy.Policy.Maximum,
            qt.QSizePolicy.Policy.Maximum,
        )
        lbl.setStyleSheet(
            f"""
            QPushButton{{
                color: {text_color};
                margin: 0px 0px 0px 0px;
                padding: 0px 0px 0px 0px;
                background-color: transparent;
                border-style: none;
                text-align: left;
            }}
        """
        )

        # * Combobox
        combobox = self.__get_combobox_widget(
            parent=parent,
            elements=dropdown_elements,
            elementchange_func=changefunc_dropdown,
        )

        # * Button
        btn1 = self.create_pushbutton(
            parent=parent,
            tool_tip=tooltip_btn1,
            icon_path=iconpath_btn1,
            click_func=clickfunc_btn1,
        )
        btn1.setFixedSize(
            int(
                max(
                    data.get_general_icon_pixelsize(),
                    data.get_general_font_height(),
                )
            ),
            int(
                max(
                    data.get_general_icon_pixelsize(),
                    data.get_general_font_height(),
                )
            ),
        )

        # * Button
        btn2 = self.create_pushbutton(
            parent=parent,
            tool_tip=tooltip_btn2,
            icon_path=iconpath_btn2,
            click_func=clickfunc_btn2,
        )
        btn2.setFixedSize(
            int(
                max(
                    data.get_general_icon_pixelsize(),
                    data.get_general_font_height(),
                )
            ),
            int(
                max(
                    data.get_general_icon_pixelsize(),
                    data.get_general_font_height(),
                )
            ),
        )

        # * QHBoxLayout()
        hlyt = qt.QHBoxLayout()
        hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        hlyt.setSpacing(5)
        hlyt.setContentsMargins(0, 0, 0, 0)
        hlyt.addWidget(btn0)
        hlyt.addWidget(lbl)
        hlyt.addWidget(combobox)
        #        hlyt.addWidget(btn1)
        #        hlyt.addStretch()
        hlyt.addWidget(btn2)

        return (hlyt, btn0, lbl, combobox, btn1, btn2)

    def create_groupbox(
        self,
        parent=None,
        text="",
        vertical: Union[bool, str] = True,
        borderless=False,
        spacing=0,
        margins=(0, 0, 0, 0),
        h_size_policy=None,
        v_size_policy=None,
    ) -> qt.QGroupBox:
        """
        :param parent:
        :param text:
        :param vertical:    True    -> qt.QVBoxLayout
                            False   -> qt.QHBoxLayout
                            'grid'  -> qt.QGridLayout
                            'stack' -> qt.QStackedLayout
        :param borderless:
        :param spacing:
        :param margins:
        :param h_size_policy:
        :param v_size_policy:
        :return:
        """
        # Widget that holds all pages
        if h_size_policy is None:
            h_size_policy = qt.QSizePolicy.Policy.Minimum
        if v_size_policy is None:
            v_size_policy = qt.QSizePolicy.Policy.Minimum
        group_box = gui.templates.widgetgenerator.create_groupbox_with_layout(
            parent=parent,
            name="StandardBox",
            text=text,
            vertical=vertical,
            borderless=borderless,
            spacing=spacing,
            margins=margins,
            h_size_policy=qt.QSizePolicy.Policy.Minimum,
            v_size_policy=qt.QSizePolicy.Policy.Minimum,
        )
        return group_box

    def create_info_groupbox(
        self,
        parent=None,
        text="",
        vertical=False,
        info_func=None,
        spacing=0,
        margins=(0, 0, 0, 0),
        h_size_policy=None,
        v_size_policy=None,
    ):
        if h_size_policy is None:
            h_size_policy = qt.QSizePolicy.Policy.Minimum
        if v_size_policy is None:
            v_size_policy = qt.QSizePolicy.Policy.Minimum
        group_box = gui.templates.widgetgenerator.create_groupbox_with_layout_and_info_button(
            parent=parent,
            name="InfoBox",
            text=text,
            vertical=vertical,
            spacing=spacing,
            margins=margins,
            h_size_policy=qt.QSizePolicy.Policy.Minimum,
            v_size_policy=qt.QSizePolicy.Policy.Minimum,
            info_size=get_button_size(),
            info_func=info_func,
        )
        return group_box

    def create_textbox(
        self,
        parent=None,
        text_change_func=None,
        h_size_policy=None,
        v_size_policy=None,
    ):
        if h_size_policy is None:
            h_size_policy = qt.QSizePolicy.Policy.Expanding
        if v_size_policy is None:
            v_size_policy = qt.QSizePolicy.Policy.Expanding
        text_box = gui.templates.widgetgenerator.create_textbox(
            name="StandardTextBox",
            parent=parent,
            func=text_change_func,
            h_size_policy=h_size_policy,
            v_size_policy=v_size_policy,
        )
        return text_box

    def create_pushbutton(
        self,
        parent=None,
        tool_tip=None,
        icon_path="icons/dialog/help.png",
        checkable=False,
        click_func=None,
    ):
        """

        :param parent:
        :param tool_tip:
        :param icon_path:
        :param checkable:
        :param click_func:
        :return:
        """
        push_button = gui.templates.widgetgenerator.create_pushbutton(
            parent=parent,
            name="StandardPushButton",
            tooltip=tool_tip,
            icon_name=icon_path,
            size=(get_button_size(), get_button_size()),
            checkable=checkable,
            click_func=click_func,
        )
        return push_button


class OneWindowProjectWizard(GeneralWizard):
    stored_gboxes = None

    def __init__(self, parent, *args, empty_project=False, **kwargs):
        super().__init__(parent, statusbar=True)
        self.empty_project = empty_project

        self.setWindowTitle("Embeetle")

        self.stored_gboxes = {}
        self.selected_options = {
            "server_path": None,
            "project_path": None,
        }

        # Project groupbox
        self.project_groupbox = self.create_groupbox(
            text="",
            borderless=True,
            vertical=False,
        )
        self.project_groupbox.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Expanding,
        )
        self.project_layout = self.project_groupbox.layout()
        self.project_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        self.main_layout.addWidget(self.project_groupbox)

        # Widget that holds all pages
        stack_groupbox = self.create_groupbox(
            vertical="stack",
            borderless=True,
            parent=None,
            spacing=0,
            margins=(0, 0, 0, 0),
            h_size_policy=qt.QSizePolicy.Policy.Minimum,
            v_size_policy=qt.QSizePolicy.Policy.Minimum,
        )
        self.project_layout.addWidget(stack_groupbox)
        self.stack = stack_groupbox.layout()

        # Add cancel / next buttons
        self.add_page_buttons()

        # Initialize project data and dialog
        self.get_project_data(empty_project)

    def loading_show(self, text):
        self.write_to_statusbar(text, 2000)
        label = gui.templates.widgetgenerator.create_label(text)
        label.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        self.stack.addWidget(label)

    def loading_hide(self):
        self.stack.removeWidget(self.stack.widget(0))

    def get_project_data(self, empty_project):
        self.project_data = {}

        def callback(project_data):
            try:
                if isinstance(project_data, str):
                    label = self.stack.widget(0)
                    label.setText(
                        f"Embeetle failed to connect to the server.\n"
                    )
                    self.resize(self.sizeHint() * 1.2)
                else:
                    self.project_data = project_data
                    self.loading_hide()
                    self.insert_options(empty_project)
            except:
                traceback.print_exc()
            qt.QTimer.singleShot(10, lambda *args: self.resize_and_center())

        if empty_project:
            self.insert_options(empty_project)
            qt.QTimer.singleShot(10, lambda *args: self.resize_and_center())
        else:
            self.loading_show("Retrieving project list ...")
            serverfunctions.get_remote_beetle_projlist(callback)

    def show_next_page(self, *args):
        current_index = self.stack.currentIndex()
        if current_index == 0:
            project_path = self.selected_options["project_path"]

            # Warn if the directory already exists
            if os.path.isdir(project_path):
                warning = (
                    f"The selected project directory {q}{project_path}{q} "
                    f"already exists!\n"
                    + f"Continuing will clear it{q}s contents and put the "
                    f"imported project inside it!\n"
                    f"Are you sure?"
                )
                reply = gui.dialogs.popupdialog.PopupDialog.warning(warning)
                if reply != qt.QMessageBox.StandardButton.Yes:
                    return

            def cb_created(success, *args):
                if success:
                    self.main_form.projects.open_project(project_path)
                    self.close()
                    return
                purefunctions.printc(
                    f"\nWARNING: Downloading sample project failed. Don{q}t "
                    f"open project:\n"
                    f"{q}{project_path}{q}.\n",
                    color="warning",
                )
                return

            module_project_generator = importlib.import_module(
                "project_generator.generator.project_generator"
            )
            if self.empty_project:
                vendor = self.selected_options["vendor"]
                board = self.selected_options["board"]
                chip = self.selected_options["chip"]

                # module_project_generator.ProjectDiskGenerator().create_empty_project(
                #     output_folderpath = project_path,
                #     boardname         = board,
                #     chipname          = chip,
                #     callback          = cb_created,
                #     callbackArg       = None,
                # )
            else:
                server_path = self.selected_options["server_path"]
                self.write_to_statusbar(
                    "Started downloading project ...", color="orange"
                )
                # Create project
                assert isinstance(server_path, str)
                assert isinstance(project_path, str)
                module_project_generator.ProjectDiskGenerator().download_sample_project(
                    serverpath=server_path,
                    project_rootpath=project_path,
                    callback=cb_created,
                    callbackArg=None,
                )
        return

    def insert_options(self, empty_project):
        # Adjust buttons
        self.next_button.setText("CREATE")
        # Add options
        if empty_project:
            try:
                self.setWindowTitle("CREATE EMPTY PROJECT")
                project_options_groupbox = EmptyOptions(self, self.project_data)
                project_options_groupbox.setObjectName("Options")
                new_tab = self.stack.addWidget(project_options_groupbox)
                self.stack.setCurrentWidget(project_options_groupbox)
            except:
                traceback.print_exc()

        else:
            try:
                self.setWindowTitle("CREATE PROJECT")
                project_options_groupbox = Options(self, self.project_data)
                project_options_groupbox.setObjectName("Options")
                new_tab = self.stack.addWidget(project_options_groupbox)
                self.stack.setCurrentWidget(project_options_groupbox)
            except:
                traceback.print_exc()

    def showEvent(self, event):
        self.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.MinimumExpanding,
            )
        )
        self.update()
        self.resize_and_center()
        self.update_check_size()
        return

    def keyPressEvent(self, event):
        event.accept()
        key = event.key()
        if key == qt.Qt.Key.Key_Escape:
            self.close()
        elif key == qt.Qt.Key.Key_Enter or key == qt.Qt.Key.Key_Return:
            if self.next_button.isEnabled():
                self.show_next_page()
            else:
                print(
                    "Project options are not valid!"
                    "Cannot create the project!"
                )


class Vendors:
    @staticmethod
    def create_image_button(name, image, func=None):
        button_size = get_button_size() * 3
        new_pushbutton = gui.helpers.buttons.CustomPushButton(
            parent=None,
            icon_path=image,
            icon_size=qt.create_qsize(button_size - 5, button_size - 5),
            checkable=True,
        )
        if func is not None:
            new_pushbutton.set_click_function(func)
        return new_pushbutton

    @staticmethod
    def create_vendor_buttons(
        func_STM=None,
        func_SL=None,
        func_NXP=None,
        func_NU=None,
        func_TI=None,
        func_NS=None,
    ):
        # Groupbox
        vendor_groupbox = (
            gui.templates.widgetgenerator.create_groupbox_with_layout(
                name="VendorsGroupBox",
                vertical="grid",
                borderless=True,
            )
        )
        vendor_groupbox.setSizePolicy(
            qt.QSizePolicy.Policy.Minimum,
            qt.QSizePolicy.Policy.Minimum,
        )
        vendor_groupbox.layout().setSpacing(10)
        vendor_groupbox.setStyleSheet("margin: 10px;")

        # Buttons
        vendors = {
            "stmicroelectronics": {
                "text": "STM",
                "icon": "figures/logos/STMicro_logo.png",
                "func": func_STM,
                "enabled": True,
            },
            "nordic": {
                "text": "NordicSemiconductor",
                "icon": "figures/logos/nordic_logo.png",
                "func": func_NS,
                "enabled": True,
            },
            "nuvoton": {
                "text": "Nuvoton",
                "icon": "figures/logos/Nuvoton_logo.png",
                "func": func_NU,
                "enabled": True,
            },
            "gigadevice": {
                "text": "GigaDevice",
                "icon": "figures/logos/giga_logo.png",
                "func": lambda *args: print("GigaDevice"),
                "enabled": False,
            },
            "maxim": {
                "text": "Maxim Integrated",
                "icon": "figures/logos/maxim_logo.png",
                "func": lambda *args: print("Maxim Integrated"),
                "enabled": False,
            },
            "siliconlabs": {
                "text": "SiliconLabs",
                "icon": "figures/logos/SiliconLabs_logo.png",
                "func": func_SL,
                "enabled": False,
            },
            "infineon": {
                "text": "Infineon",
                "icon": "figures/logos/infineon_logo.png",
                "func": lambda *args: print("Infineon"),
                "enabled": False,
            },
            "texasinstruments": {
                "text": "TexasInstruments",
                "icon": "figures/logos/TI_logo.png",
                "func": func_TI,
                "enabled": False,
            },
            "nxp": {
                "text": "NXP",
                "icon": "figures/logos/NXP_logo.png",
                "func": func_NXP,
                "enabled": False,
            },
        }
        vendor_groupbox.buttons = {}

        def choose(vendor):
            def wrapper(checked):
                if checked == False:
                    if not all(
                        (
                            v.isChecked() == False
                            for k, v in vendor_groupbox.buttons.items()
                        )
                    ):
                        return
                    for k, v in vendor_groupbox.buttons.items():
                        if k == vendor:
                            v.setChecked(True)
                        print(k)
                else:
                    for k, v in vendor_groupbox.buttons.items():
                        if k != vendor:
                            v.setChecked(False)
                        else:
                            v.setChecked(True)

            return wrapper

        row = 0
        col = 0
        for k, v in vendors.items():
            new_button = Vendors.create_image_button(
                v["text"],
                v["icon"],
                v["func"],
            )
            new_button.setEnabled(v["enabled"])
            vendor_groupbox.layout().addWidget(
                new_button,
                row,
                col,
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter,
            )
            vendor_groupbox.buttons[k] = new_button
            new_button.toggled.connect(choose(k))
            col += 1
            if col > 2:
                col = 0
                row += 1

        #        return vendor_groupbox

        wrapper = gui.templates.widgetgenerator.create_groupbox_with_layout(
            name="Vendors",
            vertical=True,
            borderless=True,
        )
        wrapper.layout().addWidget(vendor_groupbox)
        wrapper.layout().setAlignment(
            vendor_groupbox,
            qt.Qt.AlignmentFlag.AlignTop | qt.Qt.AlignmentFlag.AlignLeft,
        )
        return wrapper


class Label(qt.QLabel):
    click_signal = qt.pyqtSignal()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.click_signal.emit()


class Options(qt.QGroupBox):
    def __init__(self, parent, project_data):
        super().__init__(parent)

        self._parent = parent
        self.project_data = project_data

        self.ok_image = iconfunctions.get_qpixmap("icons/dialog/checkmark.png")
        self.error_image = iconfunctions.get_qpixmap("icons/dialog/cross.png")
        self.warning_image = iconfunctions.get_qpixmap(
            "icons/dialog/warning.png"
        )

        self.setStyleSheet(
            """
            QGroupBox {{
                border: 0px;
            }}
            """
        )
        self.layout: qt.QVBoxLayout = cast(
            qt.QVBoxLayout,
            gui.templates.widgetgenerator.create_layout(vertical=True),
        )
        self.layout.setSpacing(5)
        self.setLayout(self.layout)

        self.stored_gboxes = {}
        button_size = get_button_size()

        # Flags
        self.project_name_flag = False
        """
        Project directory groupbox
        """

        def project_directory_info_func(*args):
            _ht_.project_creation_info(self._parent, "project_directory")

        self.stored_gboxes["project_directory"] = (
            self._parent.create_info_groupbox(
                text="Project's parent directory:",
                vertical=False,
                info_func=project_directory_info_func,
            )
        )
        self.stored_gboxes["project_directory"].setSizePolicy(
            qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Fixed
        )
        self.project_layout = self.stored_gboxes["project_directory"].layout()
        self.project_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        # Project directory textbox and helper widgets
        self.project_directory_textbox = self._parent.create_textbox(
            text_change_func=self.check_project_validity
        )
        self._parent._set_widget_message(
            self.project_directory_textbox,
            "Enter the project's parent directory here",
        )

        def select_root_dir():
            dir_dialog = qt.QFileDialog(self)
            dir_dialog.setFileMode(qt.QFileDialog.FileMode.Directory)
            path = data.default_project_create_directory
            if not os.path.isdir(path):
                path = data.user_directory
            directory = qt.QFileDialog.getExistingDirectory(
                self, "Select project parent directory", path
            )
            if directory is not None and os.path.isdir(directory):
                self.project_directory_textbox.setText(directory)

        self.project_directory_button = self._parent.create_pushbutton(
            parent=self,
            tool_tip="Choose the project's directory with a dialog",
            icon_path=f"icons/folder/open/folder.png",
            click_func=select_root_dir,
        )
        self.project_directory_button.setStyleSheet(
            gui.stylesheets.button.get_simple_toggle_stylesheet()
        )
        # Validity checkbox
        self.checkbox_project_directory = (
            gui.templates.widgetgenerator.create_check_label(
                "CheckDir",
                (button_size, button_size),
            )
        )
        self._parent._set_widget_message(
            self.checkbox_project_directory,
            "Indicates whether the project parent directory is valid",
        )
        pd_widgets = (
            self.project_directory_textbox,
            self.project_directory_button,
            self.checkbox_project_directory,
        )
        for w in pd_widgets:
            self.project_layout.addWidget(w)
            self.project_layout.setAlignment(
                w, qt.Qt.AlignmentFlag.AlignVCenter
            )

        """
        Project name groupbox
        """

        def project_name_info_func(clicked):
            _ht_.project_creation_info(self._parent, "project_name")

        self.stored_gboxes["project_name"] = self._parent.create_info_groupbox(
            text="Project name:",
            vertical=True,
            info_func=project_name_info_func,
        )
        self.stored_gboxes["project_name"].setSizePolicy(
            qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Fixed
        )
        self.project_name_layout = self.stored_gboxes["project_name"].layout()
        self.project_name_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )

        # Project name textbox
        def text_edited(new_text):
            if new_text == "":
                self.project_name_flag = False
                self.project_name_textbox.setProperty("autofilled", True)
            else:
                self.project_name_flag = True
                self.project_name_textbox.setProperty("autofilled", False)
            self.project_name_textbox.style().unpolish(
                self.project_name_textbox
            )
            self.project_name_textbox.style().polish(self.project_name_textbox)
            self.project_name_textbox.repaint()

        self.project_name_textbox = self._parent.create_textbox(
            text_change_func=self.check_project_validity
        )
        self.project_name_textbox.textEdited.connect(text_edited)
        self.project_name_textbox.setProperty("autofilled", True)
        self._parent._set_widget_message(
            self.project_name_textbox,
            "Displays the project name, which is the project directory "
            + "that will be created inside the parent directory.",
        )
        self.checkbox_project_name = (
            gui.templates.widgetgenerator.create_check_label(
                "CheckName",
                (button_size, button_size),
            )
        )
        self._parent._set_widget_message(
            self.checkbox_project_name,
            "Indicates whether the project name is valid",
        )

        # [Kristof] Create a horizontal layout that will contain the textfield
        # and the check/warning sign at the right.
        hlyt = qt.QHBoxLayout()
        hlyt.setContentsMargins(0, 0, 0, 0)
        hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        hlyt.addWidget(self.project_name_textbox)
        hlyt.addWidget(self.checkbox_project_name)
        # [Kristof] Create a QLabel() with the following note:
        # 'A folder with this name will be created'
        self.project_name_label = gui.templates.widgetgenerator.create_label(
            "A folder with this name will be created"
        )
        # [Kristof] Add first the QLabel() with the note to this groupbox, then
        # add the horizontal layout that contains the textfield and the check/
        # warning sign.
        self.project_name_layout.addWidget(self.project_name_label)
        self.project_name_layout.addLayout(hlyt)

        self.project_name_layout.setAlignment(
            self.checkbox_project_name,
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter,
        )

        self.layout.addWidget(self.stored_gboxes["project_directory"])
        self.layout.addWidget(self.stored_gboxes["project_name"])
        self.init_options()

    def init_options(self):
        filter_box = gui.templates.widgetgenerator.create_groupbox_with_layout(
            "Selection",
            "",
            vertical=False,
            adjust_margins_to_text=True,
        )
        filter_box.layout().setSpacing(1)
        """Vendors."""
        vendors = []
        local_vendors = _hardware_api_.HardwareDB().list_manufacturers()
        for k, v in self.project_data.items():
            if len(v.items()) == 0:
                continue
            icon = f"icons/logo/{k}.png"
            #            vendors.append({
            #                "text": k,
            #                "icon": icon,
            #                "enabled": True,
            #            })
            name = k
            if name in local_vendors:
                vendors.append(
                    {
                        "text": k,
                        "icon": icon,
                        "enabled": True,
                        # New
                        "name": name,
                        "widgets": (
                            {"type": "image", "icon-path": icon},
                            {"type": "text", "text": name},
                        ),
                    }
                )
        vendors.sort(
            key=lambda x: (x["text"].lower() != "any", x["text"].lower())
        )
        self.vendors = vendors.copy()
        self.vendors_all = vendors.copy()
        vendor_select_box = self._create_selection_bar(
            "Vendor:",
            "Select a vendor",
            "Select a vendor from the dropdown list",
            "icons/checkbox/question.png",
            "Shows if the selected\nvendor is valid",
            vendors,
            info_type="vendor",
            additional_function=self.option_change,
            create_check=False,
        )
        self.stored_gboxes["vendor_select"] = vendor_select_box
        filter_box.layout().addWidget(vendor_select_box)
        """
        Boards
        """
        boards = []
        cache = []
        local_boards = _hardware_api_.HardwareDB().list_boards()
        for ven in self.vendors:
            for k, v in self.project_data[ven["text"]].items():
                try:
                    board = v["board"]
                    if board in local_boards:
                        family = v["boardfamily"]
                        boardfamily_unicum: _board_unicum_.BOARDFAMILY = (
                            _board_unicum_.BOARDFAMILY(family.upper())
                        )
                        if not (family in cache):
                            name = boardfamily_unicum.get_name()
                            icon = boardfamily_unicum.get_boardfam_dict()[
                                "icon"
                            ]
                            boards.append(
                                {
                                    "text": boardfamily_unicum.get_name(),
                                    "icon": (
                                        boardfamily_unicum.get_boardfam_dict()[
                                            "icon"
                                        ]
                                    ),
                                    "enabled": True,
                                    # New
                                    "name": name,
                                    "widgets": (
                                        {"type": "image", "icon-path": icon},
                                        {"type": "text", "text": name},
                                    ),
                                }
                            )
                            cache.append(family)
                except:
                    continue
        boards.sort(
            key=lambda x: (x["text"].lower() != "any", x["text"].lower())
        )
        if not ("board_select" in self.stored_gboxes.keys()):
            board_select_box = self._create_selection_bar(
                "Board:",
                "Select a board",
                "Select a board from the dropdown list",
                "icons/checkbox/question.png",
                "Shows if the selected\nboard is valid",
                boards,
                info_type="board",
                additional_function=self.option_change,
                create_check=False,
            )
            self.stored_gboxes["board_select"] = board_select_box
            filter_box.layout().addWidget(board_select_box)
        else:
            self.stored_gboxes["board_select"].create_dropdown_menu(
                items=boards,
                custom_func=functools.partial(
                    self.option_change, self.stored_gboxes["board_select"]
                ),
            )

        """
        Chips
        """
        icon = "icons/chip/chip.png"
        chips = []
        cache = []
        local_chips = _hardware_api_.HardwareDB().list_chips()
        for ven in self.vendors:
            for k, v in self.project_data[ven["text"]].items():
                if not (v["chip"] in cache):
                    #                    chips.append({
                    #                        "text": v["chip"],
                    #                        "icon": icon,
                    #                        "enabled": True,
                    #                    })
                    name = v["chip"]
                    if name in local_chips:
                        chips.append(
                            {
                                "text": v["chip"],
                                "icon": icon,
                                "enabled": True,
                                # New
                                "name": name,
                                "widgets": (
                                    {"type": "image", "icon-path": icon},
                                    {"type": "text", "text": name},
                                ),
                            }
                        )
                        cache.append(v["chip"])
        chips.sort(
            key=lambda x: (x["text"].lower() != "any", x["text"].lower())
        )
        if not ("chip_select" in self.stored_gboxes.keys()):
            chip_select_box = self._create_selection_bar(
                "Chip:",
                "Select a chip",
                "Select a chip from the dropdown list",
                "icons/checkbox/question.png",
                "Shows if the selected\nchip is valid",
                chips,
                info_type="chip",
                additional_function=self.option_change,
                create_check=False,
            )
            self.stored_gboxes["chip_select"] = chip_select_box
            filter_box.layout().addWidget(chip_select_box)
        else:
            self.stored_gboxes["chip_select"].create_dropdown_menu(
                items=chips,
                custom_func=functools.partial(
                    self.option_change, self.stored_gboxes["chip_select"]
                ),
            )

        # Add the filter box to the wizard
        self.layout.addWidget(filter_box)
        """
        Projects
        """
        projects = []
        for ven in self.vendors:
            for k, v in self.project_data[ven["text"]].items():
                try:
                    family = v["boardfamily"]
                    boardfamily_unicum: _board_unicum_.BOARDFAMILY = (
                        _board_unicum_.BOARDFAMILY(family.upper())
                    )
                    projects.append(
                        {
                            "text": k,
                            "icon": boardfamily_unicum.get_boardfam_dict()[
                                "icon"
                            ],
                            "enabled": True,
                            "vendor": ven["text"],
                            "vendor_icon": ven["icon"],
                            "board": boardfamily_unicum.get_name(),
                            "chip": v["chip"],
                            "info": v["info"],
                            "path": v["path"],
                        }
                    )
                except:
                    continue
        if not hasattr(self, "project_table"):

            def info_func(clicked):
                _ht_.project_creation_info(self._parent, "project_table")

            gb = self._parent.create_info_groupbox(
                text="Projects:",
                vertical=False,
                info_func=info_func,
            )
            new_table = gui.templates.widgetgenerator.create_table(self)
            new_table.setShowGrid(True)
            new_table.verticalHeader().hide()
            new_table.setSortingEnabled(True)
            new_table.setSelectionBehavior(
                qt.QAbstractItemView.SelectionBehavior.SelectRows
            )
            new_table.setEditTriggers(
                qt.QAbstractItemView.EditTrigger.NoEditTriggers
            )
            new_table.setSelectionMode(
                qt.QAbstractItemView.SelectionMode.SingleSelection
            )
            new_table.itemSelectionChanged.connect(
                self._table_selection_changed
            )
            new_table.itemClicked.connect(self._table_item_clicked)
            #            self.layout.addWidget(new_table)
            gb.layout().addWidget(new_table)
            self.layout.addWidget(gb)
            self.project_table: gui.templates.widgetgenerator.StandardTable = (
                new_table
            )
            self._parent._set_widget_message(
                self.project_table, "Select a project from the filtered table"
            )
            self._set_project_table(projects)
        else:
            self._set_project_table(projects)
        self.project_table.setMinimumWidth(
            50 * data.get_general_font_pointsize()
        )
        self.project_table.resizeColumnsToContents()

        # Bulk set groupbox constraints
        for key, gb in self.stored_gboxes.items():
            gb.setMinimumWidth(100)

        # Messages and create button
        self.cancel_button = self._parent.cancel_button
        self.project_create_button = self._parent.next_button

        self.check_project_validity()

        # Restore stored project directory if valid
        default_directory = data.get_default_project_directory()
        self.project_directory_textbox.setText(default_directory)

    def _set_project_table(self, projects):
        self.project_table.clean()
        self.project_table.set_headers(
            ["Name", "Vendor", "Board", "Chip", "Info", "Path"]
        )

        def info_func(arg_name, arg_chip, arg_info, *args):
            _ht_.show_info_field(
                projname=arg_name,
                microcontroller=arg_chip,
                info_content=arg_info,
                parent=self._parent,
            )

        for i, p in enumerate(projects):
            new_row = (
                p["text"],
                (iconfunctions.get_qicon(p["vendor_icon"]), p["vendor"]),
                (iconfunctions.get_qicon(p["icon"]), p["board"]),
                p["chip"],
                {
                    "type": "project-table-item",
                    "text": p["info"][:20] + " ",
                    "name": p["text"],
                    "chip": p["chip"],
                    "info": p["info"],
                    "info_func": info_func,
                },
                p["path"],
            )
            self.project_table.add_row(new_row)
        # Hide the 'Path' column
        self.project_table.hideColumn(5)

    def _change_project_table(self, valid_projects):
        if len(valid_projects) > 0:
            for i in range(self.project_table.rowCount()):
                row = []
                for j in range(self.project_table.columnCount()):
                    item = self.project_table.item(i, j)
                    if item is not None:
                        row.append(item.text())
                for p in valid_projects:
                    if (
                        p["text"] == row[0]
                        and p["vendor"] == row[1]
                        and p["board"] == row[2]
                        and p["chip"] == row[3]
                    ):
                        self.project_table.setRowHidden(i, False)
                        break
                    else:
                        self.project_table.setRowHidden(i, True)
            self.project_table.resizeColumnsToContents()

        else:
            for i in range(self.project_table.rowCount()):
                self.project_table.setRowHidden(i, True)
        self.project_table.adjust_height()

    def _table_selection_changed(self, *args):
        self.check_project_validity()

    def _table_item_clicked(self, item):
        if not self.project_name_flag:
            row_index = item.row()
            project_name_item = self.project_table.item(row_index, 0)
            project_name = project_name_item.text()
            self.project_name_textbox.setText(project_name)

    def option_change(self, *args):
        if not hasattr(self, "option_change_lock"):
            self.option_change_lock = False
        if self.option_change_lock:
            return

        def get_selection(text):
            result = text
            if (
                text.lower().startswith("select")
                or text.lower() == "empty"
                or text.lower() == "any"
            ):
                result = None
            return result

        try:

            self.check_project_validity()

            # Reset check
            try:
                self.option_change_lock = True
                comboboxes = (
                    "vendor_select",
                    "board_select",
                    "chip_select",
                )
                for c in comboboxes:
                    text = get_selection(self.stored_gboxes[c].get_text())
                    if text is not None and text.lower() == "any":
                        self.stored_gboxes[c].reset_selection()
            finally:
                self.option_change_lock = False

            # Store selected combobox texts
            selected_vendor = get_selection(
                self.stored_gboxes["vendor_select"].get_text()
            )
            selected_board = get_selection(
                self.stored_gboxes["board_select"].get_text()
            )
            selected_chip = get_selection(
                self.stored_gboxes["chip_select"].get_text()
            )

            #            print(selected_vendor, selected_board, selected_chip)

            # Vendors
            vendors = [
                {
                    "text": "any",
                    "icon": None,
                    "enabled": True,
                    "name": "any",
                    "widgets": (
                        {
                            "type": "image",
                            "icon-path": "icons/checkbox/question.png",
                        },
                        {"type": "text", "text": "Any"},
                    ),
                }
            ]
            cache = []
            local_vendors = _hardware_api_.HardwareDB().list_manufacturers()
            for k, v in self.project_data.items():
                for project_name, project in v.items():
                    if (
                        selected_board is not None
                        and selected_board.lower()
                        != project["boardfamily"].lower()
                    ):
                        continue
                    if (
                        selected_chip is not None
                        and selected_chip.lower() != project["chip"].lower()
                    ):
                        continue

                    icon = f"icons/logo/{k}.png"
                    name = k
                    if name in local_vendors:
                        if not (k in cache):
                            vendors.append(
                                {
                                    "text": k,
                                    "icon": icon,
                                    "enabled": True,
                                    # New
                                    "name": name,
                                    "widgets": (
                                        {"type": "image", "icon-path": icon},
                                        {"type": "text", "text": k},
                                    ),
                                }
                            )
                        cache.append(k)
            self.vendors.sort(
                key=lambda x: (x["text"].lower() != "any", x["text"].lower())
            )
            self.vendors = vendors.copy()
            self.stored_gboxes["vendor_select"].create_dropdown_menu(
                items=vendors,
                custom_func=functools.partial(
                    self.option_change, self.stored_gboxes["vendor_select"]
                ),
                reset_selection=False,
            )

            # Boards
            boards = [
                {
                    "text": "any",
                    "icon": None,
                    "enabled": True,
                    "name": "any",
                    "widgets": (
                        {
                            "type": "image",
                            "icon-path": "icons/checkbox/question.png",
                        },
                        {"type": "text", "text": "Any"},
                    ),
                }
            ]
            cache = []
            local_boards = _hardware_api_.HardwareDB().list_boards()

            for ven in self.vendors_all:
                if (
                    selected_vendor is not None
                    and selected_vendor.lower() != ven["text"].lower()
                ):
                    continue
                elif ven["text"].lower() == "any":
                    continue

                for k, v in self.project_data[ven["text"]].items():
                    try:
                        if v["board"] in local_boards:
                            family = v["boardfamily"]
                            _boardfamily_unicum: _board_unicum_.BOARDFAMILY = (
                                _board_unicum_.BOARDFAMILY(family.upper())
                            )
                            if (selected_chip is not None) and (
                                selected_chip.lower() != v["chip"].lower()
                            ):
                                continue

                            name = _boardfamily_unicum.get_name()
                            #                            if not(family in cache) and (selected_board is None or (selected_board is not None and selected_board.lower() == name)):
                            if not (family in cache):
                                icon = _boardfamily_unicum.get_boardfam_dict()[
                                    "icon"
                                ]
                                boards.append(
                                    {
                                        "text": _boardfamily_unicum.get_name(),
                                        "icon": _boardfamily_unicum.get_boardfam_dict()[
                                            "icon"
                                        ],
                                        "enabled": True,
                                        # New
                                        "name": name,
                                        "widgets": (
                                            {
                                                "type": "image",
                                                "icon-path": icon,
                                            },
                                            {"type": "text", "text": name},
                                        ),
                                    }
                                )
                                cache.append(family)
                    except:
                        continue
            boards.sort(
                key=lambda x: (x["text"].lower() != "any", x["text"].lower())
            )
            self.stored_gboxes["board_select"].create_dropdown_menu(
                items=boards,
                custom_func=functools.partial(
                    self.option_change, self.stored_gboxes["board_select"]
                ),
                reset_selection=False,
            )

            # Chips
            icon = "icons/chip/chip.png"
            chips = [
                {
                    "text": "any",
                    "icon": None,
                    "enabled": True,
                    "name": "any",
                    "widgets": (
                        {
                            "type": "image",
                            "icon-path": "icons/checkbox/question.png",
                        },
                        {"type": "text", "text": "Any"},
                    ),
                }
            ]
            cache = []
            local_chips = _hardware_api_.HardwareDB().list_chips()
            for ven in self.vendors_all:
                if (
                    selected_vendor is not None
                    and selected_vendor.lower() != ven["text"].lower()
                ):
                    continue
                elif ven["text"].lower() == "any":
                    continue

                for k, v in self.project_data[ven["text"]].items():
                    if (
                        selected_board is not None
                        and selected_board.lower() != v["boardfamily"].lower()
                    ):
                        continue

                    if not (v["chip"] in cache):
                        name = v["chip"]
                        if name in local_chips:
                            chips.append(
                                {
                                    "text": v["chip"],
                                    "icon": icon,
                                    "enabled": True,
                                    # New
                                    "name": name,
                                    "widgets": (
                                        {"type": "image", "icon-path": icon},
                                        {"type": "text", "text": name},
                                    ),
                                }
                            )
                            cache.append(v["chip"])
            chips.sort(
                key=lambda x: (x["text"].lower() != "any", x["text"].lower())
            )
            self.stored_gboxes["chip_select"].create_dropdown_menu(
                items=chips,
                custom_func=functools.partial(
                    self.option_change, self.stored_gboxes["chip_select"]
                ),
                reset_selection=False,
            )

            # Set special empty items in comboboxes
            if selected_vendor is None:
                self.stored_gboxes["vendor_select"].combobox.set_selected_item(
                    {
                        "name": "empty",
                        "widgets": (
                            {
                                "type": "image",
                                "icon-path": "icons/checkbox/question.png",
                            },
                            {"type": "text", "text": "Select a vendor"},
                        ),
                    }
                )
                self.stored_gboxes["vendor_select"].combobox.remove_item("any")
            if selected_board is None:
                self.stored_gboxes["board_select"].combobox.set_selected_item(
                    {
                        "name": "empty",
                        "widgets": (
                            {
                                "type": "image",
                                "icon-path": "icons/checkbox/question.png",
                            },
                            {"type": "text", "text": "Select a board"},
                        ),
                    }
                )
                self.stored_gboxes["board_select"].combobox.remove_item("any")
            if selected_chip is None:
                self.stored_gboxes["chip_select"].combobox.set_selected_item(
                    {
                        "name": "empty",
                        "widgets": (
                            {
                                "type": "image",
                                "icon-path": "icons/checkbox/question.png",
                            },
                            {"type": "text", "text": "Select a chip"},
                        ),
                    }
                )
                self.stored_gboxes["chip_select"].combobox.remove_item("any")

            # Projects
            projects = []
            for ven in self.vendors_all:
                if (
                    selected_vendor is not None
                    and selected_vendor.lower() != ven["text"].lower()
                ):
                    continue
                elif ven["text"].lower() == "any":
                    continue

                for k, v in self.project_data[ven["text"]].items():
                    if (
                        selected_board is not None
                        and selected_board.lower() != v["boardfamily"].lower()
                    ):
                        continue
                    if (
                        selected_chip is not None
                        and selected_chip.lower() != v["chip"].lower()
                    ):
                        continue
                    try:
                        family = v["boardfamily"]
                        _boardfamily_unicum: _board_unicum_.BOARDFAMILY = (
                            _board_unicum_.BOARDFAMILY(family.upper())
                        )
                        projects.append(
                            {
                                "text": k,
                                "icon": _boardfamily_unicum.get_boardfam_dict()[
                                    "icon"
                                ],
                                "enabled": True,
                                "vendor": ven["text"],
                                "vendor_icon": ven["icon"],
                                "board": _boardfamily_unicum.get_name(),
                                "chip": v["chip"],
                                "info": v["info"],
                                "path": v["path"],
                            }
                        )
                    except:
                        continue
            #            self._set_project_table(projects)
            self._change_project_table(projects)

        except:
            traceback.print_exc()
            comboboxes = (
                "vendor_select",
                "board_select",
                "chip_select",
            )
            for c in comboboxes:
                text = get_selection(self.stored_gboxes[c].get_text())
                if text is not None and text.lower() == "any":
                    self.stored_gboxes[c].reset_selection()
            message = "The option you have selected is currently not supported!"
            gui.dialogs.popupdialog.PopupDialog.ok(message)

    def _create_selection_bar(
        self,
        gb_text,
        btn_text,
        tooltip,
        btn_icon,
        check_tooltip,
        actions,
        action_groups=None,
        custom_func=None,
        info_type=None,
        additional_function=None,
        create_check=True,
    ):
        return self._parent.create_selection_bar(
            gb_text,
            btn_text,
            tooltip,
            btn_icon,
            check_tooltip,
            actions,
            action_groups=action_groups,
            custom_func=custom_func,
            info_type=info_type,
            additional_function=additional_function,
            create_check=create_check,
        )

    def check_options(self):
        valid = True
        for gb in self.stored_gboxes.values():
            text = gb.layout().itemAt(0).widget().text()
            if text.startswith("Select"):
                valid = False
                if hasattr(gb, "status_box"):
                    gb.status_box.setPixmap(self.error_image)
            else:
                if hasattr(gb, "status_box"):
                    gb.status_box.setPixmap(self.ok_image)
        return valid

    def check_selection(self):
        return len(self.project_table.selectedItems()) > 0

    def check_project_validity(self, *args):
        self._parent.next_button.setEnabled(False)
        self._parent.selected_options = {
            "server_path": None,
            "project_path": None,
        }
        checks = [
            #            self.check_options(),
            self.check_selection(),
            self._check_root_dir(),
            self._check_project_name(),
        ]
        if all(checks) == False:
            return

        selection = [x.text() for x in self.project_table.selectedItems()]
        #        pprint(selection)
        name = selection[0]
        vendor = selection[1]
        board = selection[2]
        chip = selection[3]
        #        info = selection[4]
        #        server_path = selection[5]
        selected_row = self.project_table.selectedRanges()[0].topRow()
        server_path = self.project_table.item(selected_row, 5).text()

        directory = self.project_directory_textbox.text()
        project_name = self.project_name_textbox.text()
        project_path = functions.unixify_path_join(directory, project_name)

        self._parent.selected_options = {
            "server_path": server_path,
            "project_path": project_path,
        }
        self._parent.next_button.setEnabled(True)

    def display_message(self, *args):
        #        print(args)
        pass

    def _check_root_dir(self):
        root_path = self.project_directory_textbox.text()
        check_result = purefunctions.is_ascii_only_and_safe(root_path)
        if os.path.isdir(root_path) and check_result == "safe":
            if data.default_project_create_directory != root_path:
                data.default_project_create_directory = root_path
                self._parent.main_form.settings.save()
            # Check access
            if os.access(root_path, os.W_OK):
                self.checkbox_project_directory.setPixmap(self.ok_image)
                self.checkbox_project_directory.setToolTip(
                    _ht_.project_import_info(
                        self._parent, "project_directory_valid", None
                    )
                )
                self.display_message("Parent directory is valid.", "success")
                return True
            else:
                self.checkbox_project_directory.setPixmap(self.warning_image)
                self.checkbox_project_directory.setToolTip(
                    _ht_.project_import_info(
                        self._parent,
                        "project_directory_no_write_permission",
                        None,
                    )
                )
                self.display_message(
                    "Current user does not have write access to the parent directory.",
                    "success",
                )
                return False
        else:
            self.checkbox_project_directory.setPixmap(self.error_image)
            self.checkbox_project_directory.setToolTip(
                _ht_.project_import_info(
                    self._parent, "project_directory_invalid", None
                )
            )
            message = "Invalid parent directory!"
            if check_result != "safe":
                message = "Parent directory has invalid characters!"
            self.display_message(message, "error")
            return False

    def _check_project_name(self):
        name = self.project_name_textbox.text()
        if functions.is_pathname_valid(name):
            root_path = self.project_directory_textbox.text()
            if os.access(root_path, os.W_OK):
                if os.path.isdir(os.path.join(root_path, name)):
                    self.checkbox_project_name.setPixmap(self.warning_image)
                    self.checkbox_project_name.setToolTip(
                        _ht_.project_import_info(
                            self._parent, "project_name_already_exists", None
                        )
                    )
                else:
                    self.checkbox_project_name.setPixmap(self.ok_image)
                    self.checkbox_project_name.setToolTip(
                        _ht_.project_import_info(
                            self._parent, "project_name_ok", None
                        )
                    )
                return True
            else:
                self.checkbox_project_name.setPixmap(self.error_image)
                self.checkbox_project_name.setToolTip(
                    _ht_.project_import_info(
                        self._parent,
                        "project_directory_no_write_permission",
                        None,
                    )
                )
                return False
        else:
            self.checkbox_project_name.setPixmap(self.error_image)
            self.checkbox_project_name.setToolTip(
                _ht_.project_import_info(
                    self._parent, "project_name_error", None
                )
            )
            return False


class ImportWizard(GeneralWizard):
    stored_gboxes = None

    def __init__(self, parent, vendor, scale=1.0):
        """Initialization of widgets and background."""
        super().__init__(parent, statusbar=True)
        self.vendor = vendor
        self.stored_gboxes = {}
        if vendor == "stm":
            self.setWindowTitle("CUBEMX PROJECT IMPORT")
            self.importer_name = "CubeMX"
            directory_box_text = "CubeMX project directory:"
            directory_text = f"Enter the CubeMX project{q}s directory here"
            directory_button = (
                f"Choose the CubeMX project{q}s directory with a dialog"
            )
            project_directory_check_text = (
                "Indicates whether the project parent directory is valid"
            )
        elif vendor == "arduino":
            self.setWindowTitle("ARDUINO PROJECT IMPORT")
            self.importer_name = "Arduino"
            directory_box_text = "Arduino project sketch:"
            directory_text = f"Enter the Arduino project{q}s sketch file here"
            directory_button = (
                f"Choose the Arduino project{q}s sketch file with a dialog"
            )
            project_directory_check_text = (
                "Indicates whether the sketch file is valid"
            )
        else:
            self.setWindowTitle("UNKNOWN project import")
            self.importer_name = "UNKNOWN"
            directory_box_text = "UNKNOWN project directory:"
            directory_text = f"Enter the UNKNOWN project{q}s directory here"
            directory_button = (
                f"Choose the UNKNOWN project{q}s directory with a dialog"
            )
            project_directory_check_text = (
                "Indicates whether the sketch file is valid"
            )
        replace_text = f"(Overwrite the {self.importer_name} project with an Embeetle project)"
        keep_text = f"(Read the {self.importer_name} project and generate\nthe Embeetle project in a new directory)"
        keep_tooltip = keep_text[1:-1]
        info_input_directory = lambda: _ht_.project_import_info(
            self,
            "input_directory",
            vendor,
        )
        info_input_type = lambda: _ht_.project_import_info(
            self,
            "input_type",
            vendor,
        )
        info_project_directory = lambda: _ht_.project_import_info(
            self,
            "project_directory",
            vendor,
        )
        info_project_name = lambda: _ht_.project_import_info(
            self,
            "project_name",
            vendor,
        )

        # [Kristof] Insert a clickable red WARNING label at the top of the
        # wizard to share important info with the user about CubeMX.
        class WarningLabel(qt.QLabel):
            def __init__(self):
                super().__init__()
                text_color = data.theme["fonts"]["default"]["color"]
                self.setStyleSheet(
                    f"""
                QLabel {{
                    background: transparent;
                    color: {text_color};
                    border: none;
                }}
                """
                )
                self.setFont(data.get_general_font())
                self.linkActivated.connect(self.open_link)

            def open_link(self, link):
                functions.open_url(link)

        if vendor == "stm":
            self.cubemx_warning = WarningLabel()
            importer_webpage = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/project-new/import-stm-project"
            self.cubemx_warning.setText(
                f"WARNING: To import a CubeMX-generated project, it has to fulfill a few<br>"
                f'requirements. <a href="{importer_webpage}">Click here</a> to visit our webpage for more info. Also close<br>'
                f"the CubeMX software before continuing here!<br>"
            )
            self.main_layout.addWidget(self.cubemx_warning)
        if vendor == "arduino":
            self.arduino_warning = WarningLabel()
            importer_webpage = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/project-new/import-arduino-project"
            self.arduino_warning.setText(
                f'INFO: <a href="{importer_webpage}">Click here</a> for more information about this Arduino<br>'
                f"sketch importer.<br>"
                f"<br>"
                f'<span style="color:#cc0000;">WARNING: '
                f"Close the Arduino IDE before continuing here!</span><br>"
            )
            self.main_layout.addWidget(self.arduino_warning)

        button_size = get_button_size()
        self.import_groupbox = self.create_groupbox(
            text="",
            borderless=True,
            vertical=True,
        )
        self.import_groupbox.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Expanding,
        )
        self.import_layout: qt.QVBoxLayout = cast(
            qt.QVBoxLayout, self.import_groupbox.layout()
        )
        self.import_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        self.import_layout.setSpacing(5)
        self.main_layout.addWidget(self.import_groupbox)

        # Input directory groupbox
        self.stored_gboxes["input_directory"] = self.create_info_groupbox(
            text=directory_box_text,
            vertical=False,
            info_func=info_input_directory,
        )
        self.stored_gboxes["input_directory"].setSizePolicy(
            qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Fixed
        )
        self.input_layout = self.stored_gboxes["input_directory"].layout()
        self.input_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        # Project directory textbox and helper widgets
        self.input_directory_textbox = self.create_textbox(
            text_change_func=self.check_project_validity
        )
        self._set_widget_message(self.input_directory_textbox, directory_text)

        def select_input_dir(*args) -> None:
            directory = qt.QFileDialog.getExistingDirectory(
                self,
                "Select project parent directory",
                data.default_project_create_directory,
            )
            if directory is not None:
                self.input_directory_textbox.setText(directory)
            return

        def select_input_file(*args) -> None:
            if vendor.lower() == "arduino":
                title = "Select sketch file"
                _filter = "Sketch files(*.ino *.pde)"
            else:
                raise Exception(
                    "[IMPORT WIZARD] Unknown vendor for file dialog title: "
                    + vendor
                )
            file_tuple = qt.QFileDialog.getOpenFileName(
                self,
                title,
                data.default_project_create_directory,
                filter=_filter,
            )
            if file_tuple is not None:
                file = file_tuple[0]
                self.input_directory_textbox.setText(file)
            return

        if vendor.lower() == "arduino":
            icon_path = f"icons/file/file_ino.png"
        else:
            icon_path = f"icons/folder/open/folder.png"
        self.input_directory_button = self.create_pushbutton(
            parent=self,
            tool_tip=directory_button,
            icon_path=icon_path,
        )
        self.input_directory_button.setToolTip(directory_button)
        self.input_directory_button.setStyleSheet(
            gui.stylesheets.button.get_simple_toggle_stylesheet()
        )
        if self.vendor.lower() == "arduino":
            self.input_directory_button.set_click_function(select_input_file)
        else:
            self.input_directory_button.set_click_function(select_input_dir)

        self.checkbox_input_directory = self._create_check_label(
            "CheckDir",
            (button_size, button_size),
        )
        self._set_widget_message(
            self.checkbox_input_directory,
            project_directory_check_text,
        )
        self.input_layout.addWidget(self.input_directory_textbox)
        self.input_layout.addWidget(self.input_directory_button)
        self.input_layout.addWidget(self.checkbox_input_directory)

        # Special board and chip selection for special vendors
        if self.vendor == "arduino":
            # Get all Arduino boards and chips
            list_of_boards: List[Dict[str, Any]] = []
            list_of_chips: List[Dict[str, Any]] = []
            try:
                b1: List[
                    _board_unicum_.BOARD
                ] = _hardware_api_.HardwareDB().list_boards(
                    boardfam_list=[
                        "arduino",
                    ],
                    return_unicums=True,
                )
                b2: List[
                    _board_unicum_.BOARD
                ] = _hardware_api_.HardwareDB().list_boards(
                    boardfam_list=[
                        "esp32-kit",
                    ],
                    return_unicums=True,
                )
                board_unicum_list: List[_board_unicum_.BOARD] = b1 + b2
            except:
                board_unicum_list: List[
                    _board_unicum_.BOARD
                ] = _hardware_api_.HardwareDB().list_boards(
                    boardfam_list=[
                        "arduino",
                    ],
                    return_unicums=True,
                )
            for board_unicum in board_unicum_list:
                # The 'custom' board should not be listed in the first place. But just build in a
                # safeguard.
                if board_unicum.get_name().lower() == "custom":
                    continue
                # Extract board name
                board_name = board_unicum.get_name()
                board_icon = board_unicum.get_board_dict()["icon"]
                list_of_boards.append(
                    {
                        "text": board_name,
                        "icon": board_icon,
                        "enabled": True,
                        "unicum": board_unicum,
                        "name": board_name,
                        "widgets": (
                            {"type": "image", "icon-path": board_icon},
                            {"type": "text", "text": board_name},
                        ),
                    }
                )
                # Extract corresponding chip name. Note that this will never return 'custom' because
                # the 'custom' board is not being listed.
                chip_name: str = board_unicum.get_board_dict()["chip"]
                chip_unicum: _chip_unicum_.CHIP = _chip_unicum_.CHIP(chip_name)
                chip_icon: str = chip_unicum.get_chip_dict(board=None)["icon"]
                if not iconfunctions.icon_exists(chip_icon):
                    purefunctions.printc(
                        f"WARNING: Icon {q}{chip_icon}{q} not found!",
                        color="warning",
                    )
                    chip_icon = "icons/chip/chip.png"
                list_of_chips.append(
                    {
                        "text": chip_name,
                        "icon": chip_icon,
                        "enabled": True,
                        "unicum": chip_unicum,
                        "name": chip_name,
                        "widgets": (
                            {"type": "image", "icon-path": chip_icon},
                            {"type": "text", "text": chip_name},
                        ),
                    }
                )
                continue

            name = "CUSTOM_BOARD"
            icon = "icons/board/custom_board.png"
            list_of_boards.append(
                {
                    "text": name,
                    "icon": icon,
                    "enabled": True,
                    "unicum": None,
                    "name": name,
                    "widgets": (
                        {"type": "image", "icon-path": icon},
                        {"type": "text", "text": name},
                    ),
                }
            )
            # Board combobox
            self.board_selection = self.create_selection_bar(
                "Arduino board:",
                "Select an Arduino board",
                "Select an Arduino board from the dropdown list",
                "icons/checkbox/question.png",
                "Shows if the selected\nboard is valid",
                list_of_boards,
                info_type="board",
                additional_function=None,
                create_check=False,
            )
            self.stored_gboxes["board_selection"] = self.board_selection

            def board_selection_change(*args) -> None:
                board_cb = self.board_selection.combobox
                chip_cb = self.chip_selection.combobox
                try:
                    # Reset
                    if board_cb.get_selected_item_name().lower() == "reset":
                        board_cb.set_items(items=list_of_boards)
                        board_cb.set_no_selection_icon(
                            "icons/checkbox/question.png"
                        )
                        board_cb.set_no_selection_text(
                            "Select an Arduino board"
                        )
                        board_cb.reset_selected_item()
                        chip_cb.reset_selected_item()
                        self.check_project_validity()
                        return
                    # Skip custom board
                    if (
                        board_cb.get_selected_item_name().lower()
                        == "custom_board"
                    ):
                        self.check_project_validity()
                        return
                    # Check valid chips
                    name = "Reset"
                    icon = "icons/checkbox/question.png"
                    valid_chips = [
                        {
                            "text": name,
                            "icon": icon,
                            "enabled": True,
                            "unicum": None,
                            # New
                            "name": name,
                            "widgets": (
                                {"type": "image", "icon-path": icon},
                                {"type": "text", "text": name},
                            ),
                        },
                    ]
                    # Extract the BOARD()-unicum. The custom board was skipped. So if we extract the
                    # BOARD()-unicum at this point, it should not be BOARD('custom').
                    b_unicum: _board_unicum_.BOARD = (
                        board_cb.get_selected_item()["unicum"]
                    )
                    if b_unicum.get_name().lower() == "custom":
                        raise RuntimeError(
                            f"The board unicum at this point should not be BOARD({q}custom{q})!"
                        )
                    # Extract the name of the chip on the BOARD()-unicum
                    c_name: str = b_unicum.get_board_dict()["chip"]
                    for i in list_of_chips:
                        if i["text"] == c_name:
                            valid_chips.append(i)
                            chip_cb.set_items(items=valid_chips)
                            chip_cb.set_selected_item(i)
                            break
                except:
                    chip_cb.reset_selected_item()
                self.check_project_validity()
                return

            self.board_selection.combobox.selection_changed.connect(
                board_selection_change
            )
            # Chip combobox
            filtered_chips = []
            chip_cache = []
            for c in list_of_chips:
                if c["text"] not in chip_cache:
                    filtered_chips.append(c)
                    chip_cache.append(c["text"])
            list_of_chips = filtered_chips
            self.chip_selection = self.create_selection_bar(
                "Arduino chip:",
                "Select an Arduino chip",
                "Select an Arduino chip from the dropdown list",
                "icons/checkbox/question.png",
                "Shows if the selected\nboard is valid",
                list_of_chips,
                info_type="chip",
                additional_function=None,
                create_check=False,
            )
            self.stored_gboxes["chip_selection"] = self.chip_selection

            def chip_selection_change(*args) -> None:
                board_cb = self.board_selection.combobox
                chip_cb = self.chip_selection.combobox
                # Reset
                if chip_cb.get_selected_item_name().lower() == "reset":
                    chip_cb.set_items(items=list_of_chips)
                    chip_cb.set_no_selection_icon("icons/checkbox/question.png")
                    chip_cb.set_no_selection_text("Select an Arduino chip")
                    chip_cb.reset_selected_item()
                    board_cb.reset_selected_item()
                    self.check_project_validity()
                    return
                # Skip custom board
                if board_cb.get_selected_item_name().lower() == "custom_board":
                    self.check_project_validity()
                    return
                # Valid boards
                name = "Reset"
                icon = "icons/checkbox/question.png"
                valid_boards = [
                    {
                        "text": name,
                        "icon": icon,
                        "enabled": True,
                        "unicum": None,
                        # New
                        "name": name,
                        "widgets": (
                            {"type": "image", "icon-path": icon},
                            {"type": "text", "text": name},
                        ),
                    },
                ]
                for b in list_of_boards:
                    if b["unicum"] is None:
                        valid_boards.append(b)
                        continue
                    b_unicum: _board_unicum_.BOARD = b["unicum"]
                    c_name: str = b_unicum.get_board_dict()["chip"]
                    c_unicum: _chip_unicum_.CHIP = _chip_unicum_.CHIP(c_name)
                    if chip_cb.get_selected_item()["unicum"] == c_unicum:
                        valid_boards.append(b)
                    continue

                board_cb.set_items(
                    items=valid_boards,
                    reset_selection=False,
                )
                board_cb.set_no_selection_icon("icons/checkbox/question.png")
                board_cb.set_no_selection_text("Select an Arduino board")
                board_cb.reset_selected_item()
                board_cb.set_selected_item(valid_boards[1])
                self.check_project_validity()
                return

            self.chip_selection.combobox.selection_changed.connect(
                chip_selection_change
            )

        # Import type selections
        self.stored_gboxes["input_type"] = self.create_info_groupbox(
            text="Import type:",
            vertical=True,
            info_func=info_input_type,
        )
        type_layout = self.stored_gboxes["input_type"].layout()

        # Replace
        self.replace_box = self.create_check_option(
            "Replace", additional_text=replace_text
        )
        self.replace_box.setToolTip(replace_text)

        # Keep
        self.keep_box = self.create_check_option(
            "Keep", additional_text=keep_text
        )
        self.keep_box.setToolTip(keep_tooltip)

        # Set the click functions
        def replace_box_click(*args):
            self.select_import_type(True)

        def keep_box_click(*args):
            self.select_import_type(False)

        self.replace_box.check_box.clicked.connect(replace_box_click)
        self.keep_box.check_box.clicked.connect(keep_box_click)
        # Add the checkboxes to the layout
        type_layout.addWidget(self.replace_box)
        type_layout.addWidget(self.keep_box)

        # Project directory groupbox
        self.stored_gboxes["project_directory"] = (
            gui.templates.widgetgenerator.create_groupbox_with_layout_and_info_button(
                f"ProjDirGroupbox",
                f"Project{q}s parent directory:",
                vertical=False,
                adjust_margins_to_text=True,
                info_size=button_size,
                info_func=info_project_directory,
            )
        )
        self.project_layout = self.stored_gboxes["project_directory"].layout()
        self.project_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        # Project directory textbox and helper widgets
        self.project_directory_textbox = self.create_textbox(
            text_change_func=self.check_project_validity,
            v_size_policy=qt.QSizePolicy.Policy.Fixed,
        )
        self._set_widget_message(
            self.project_directory_textbox,
            f"Enter the project{q}s parent directory here",
        )

        def select_root_dir():
            directory = qt.QFileDialog.getExistingDirectory(
                self,
                "Select project parent directory",
                data.default_project_create_directory,
            )
            if directory is not None:
                self.project_directory_textbox.setText(directory)
            return

        self.project_directory_button = self.create_pushbutton(
            parent=self,
            tool_tip=f"Choose the project{q}s parent directory with a dialog",
            icon_path=f"icons/folder/open/folder.png",
            click_func=select_root_dir,
        )
        self.project_directory_button.setStyleSheet(
            gui.stylesheets.button.get_simple_toggle_stylesheet()
        )

        self.checkbox_project_directory = (
            gui.templates.widgetgenerator.create_check_label(
                "CheckDir",
                (button_size, button_size),
            )
        )
        self._set_widget_message(
            self.checkbox_project_directory,
            "Indicates whether the project parent directory is valid",
        )
        self.project_layout.addWidget(self.project_directory_textbox)
        self.project_layout.addWidget(self.project_directory_button)
        self.project_layout.addWidget(self.checkbox_project_directory)

        # Project name groupbox
        self.stored_gboxes["project_name"] = (
            gui.templates.widgetgenerator.create_groupbox_with_layout_and_info_button(
                "ProjNameGroupbox",
                "Project name:",
                vertical=True,
                adjust_margins_to_text=True,
                info_size=button_size,
                info_func=info_project_name,
            )
        )
        self.project_name_layout = self.stored_gboxes["project_name"].layout()
        self.project_name_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        # Project name textbox
        self.project_name_textbox = self.create_textbox(
            text_change_func=self.check_project_validity,
            v_size_policy=qt.QSizePolicy.Policy.Fixed,
        )
        self._set_widget_message(
            self.project_name_textbox,
            "Displays the project name, which is the project directory "
            + "that will be created inside the parent directory.",
        )
        self.checkbox_project_name = (
            gui.templates.widgetgenerator.create_check_label(
                "CheckName",
                (
                    data.get_general_icon_pixelsize(),
                    data.get_general_icon_pixelsize(),
                ),
            )
        )
        self._set_widget_message(
            self.checkbox_project_name,
            "Indicates whether the project name is valid",
        )
        # [Kristof] Create a horizontal layout that will contain the textfield
        # and the check/warning sign at the right.
        hlyt = qt.QHBoxLayout()
        hlyt.setContentsMargins(0, 0, 0, 0)
        hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        hlyt.addWidget(self.project_name_textbox)
        hlyt.addWidget(self.checkbox_project_name)
        # [Kristof] Create a QLabel() with the following note:
        # 'A folder with this name will be created'
        self.project_name_label = qt.QLabel()
        self.project_name_label.setStyleSheet(
            f"""
QLabel {{
    background: transparent;
    color: #888a85;
    border: none;
}}
        """
        )
        self.project_name_label.setFont(data.get_general_font())
        self.project_name_label.setText(
            "A folder with this name will be created"
        )
        # [Kristof] Add first the QLabel() with the note to this groupbox, then
        # add the horizontal layout that contains the textfield and the check/
        # warning sign.
        self.project_name_layout.addWidget(self.project_name_label)
        self.project_name_layout.addLayout(hlyt)

        # Adding all the groupboxes to the main layout
        self.import_layout.addWidget(self.stored_gboxes["input_directory"])
        if self.vendor == "arduino":
            gb = gui.templates.widgetgenerator.create_groupbox_with_layout(
                borderless=True,
                vertical=False,
                spacing=4,
            )
            gb.layout().addWidget(self.stored_gboxes["board_selection"])
            gb.layout().addWidget(self.stored_gboxes["chip_selection"])
            self.import_layout.addWidget(gb)
        self.import_layout.addWidget(self.stored_gboxes["input_type"])
        self.import_layout.addWidget(self.stored_gboxes["project_directory"])
        self.import_layout.addWidget(self.stored_gboxes["project_name"])

        # Add cancel / next buttons
        self.add_page_buttons()

        # Pick the initial import type
        self.select_import_type(False)

        # Restore stored project directory if valid
        default_directory = data.get_default_project_directory()
        self.project_directory_textbox.setText(default_directory)
        self.__importer_console = _importer_console_.ImporterConsole(
            parent=self,
            main_form=data.main_form,
            name="importer",
        )
        self.import_layout.addWidget(self.__importer_console)
        self.__importer_console.setMinimumHeight(400)
        width, height = self.lock_size(False)
        self.setMaximumHeight(height)
        # =======================[ end of constructor ]======================= #
        return

    def get_importer_console(self) -> _importer_console_.ImporterConsole:
        return self.__importer_console

    def display_message(self, *args) -> None:
        return

    def show_next_page(self, *args) -> None:
        self.proceed()
        return

    def select_import_type(self, replace) -> None:
        if replace:
            self.replace_box.check_box.on()
            self.keep_box.check_box.off()
            self.stored_gboxes["project_directory"].setEnabled(False)
            self.stored_gboxes["project_name"].setEnabled(False)
        else:
            self.replace_box.check_box.off()
            self.keep_box.check_box.on()
            self.stored_gboxes["project_directory"].setEnabled(True)
            self.stored_gboxes["project_name"].setEnabled(True)
        self.check_project_validity()
        return

    def check_project_validity(self, *args) -> None:
        self.next_button.setEnabled(False)
        self.next_button.setToolTip(
            "Some option were not entered correctly!\n"
            + "Please correct the invalid options above."
        )
        checks = [
            self._check_import_dir(),
            self._check_root_dir(),
            self._check_project_name(),
            self._check_optional_settings(),
        ]
        if self.vendor == "arduino":
            checks.append(self._check_hardware_selection())
        if all(checks) == False:
            return
        self.next_button.setEnabled(True)
        self.next_button.setToolTip(
            f"Proceed importing the existing {self.importer_name} project\n"
            + "according to the options you chose above."
        )
        return

    def _check_import_dir(self) -> bool:
        input_path = self.input_directory_textbox.text()
        if (self.vendor.lower() == "stm") and os.path.isdir(input_path):
            self.checkbox_input_directory.setPixmap(self.ok_image)
            self.display_message(
                f"{self.importer_name}{q}s project directory is valid.",
                "success",
            )
            data.default_project_import_directory = input_path
            if hasattr(self, "cached_input_path") == False:
                self.cached_input_path = ""
            if self.cached_input_path != input_path:
                self.cached_input_path = input_path
                self.main_form.settings.save()
            if self.replace_box.check_box.isChecked():
                directory = functions.unixify_path(os.path.dirname(input_path))
                name = os.path.basename(input_path)
                self.project_directory_textbox.setText(directory)
                self.project_name_textbox.setText(name)

            # Check for 'Makefile' presence
            if not hasattr(self, "input_directory_check_label"):
                new_label = gui.templates.widgetgenerator.create_label("")
                new_label.setTextFormat(qt.Qt.TextFormat.RichText)
                new_label.setOpenExternalLinks(True)
                self.import_layout.insertWidget(1, new_label)
                self.input_directory_check_label = new_label
            try:
                makefile_path = functions.unixify_path_join(
                    input_path, "Makefile"
                )
                if not os.path.isfile(makefile_path) and not os.path.isfile(
                    makefile_path.lower()
                ):
                    self.input_directory_check_label.set_colors(
                        text_color=data.theme["fonts"]["error"]["color"]
                    )
                    link = f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/home-window/project-new/import-stm-project"
                    self.input_directory_check_label.setText(
                        "<span style='color: #ef2929;'>WARNING: It looks like you forgot to select 'Makefile' as your 'Toolchain/IDE'<br>"
                        + f'in the CubeMX \'Project Manager\' tab! <a href="{link}" style="color: #729fcf;">Click here</a> to visit our webpage<br>for more info.</span>'
                    )
                else:
                    self.input_directory_check_label.set_colors(
                        text_color=data.theme["fonts"]["success"]["color"]
                    )
                    self.input_directory_check_label.setText(
                        "Makefile found. CubeMX project looks OK."
                    )
                    return True
            except:
                self.input_directory_check_label.set_colors(
                    text_color=data.theme["fonts"]["error"]["color"]
                )
                self.input_directory_check_label.setText(
                    "An error occured trying to find Makefile in the selected CubeMX import directory!"
                )

        if (self.vendor.lower() == "arduino") and os.path.isfile(input_path):
            self.checkbox_input_directory.setPixmap(self.ok_image)
            self.display_message(
                f"{self.importer_name}{q}s sketch file is valid.",
                "success",
            )
            data.default_project_import_directory = input_path
            if hasattr(self, "cached_input_path") == False:
                self.cached_input_path = ""
            if self.cached_input_path != input_path:
                self.cached_input_path = input_path
                self.main_form.settings.save()
            if self.replace_box.check_box.isChecked():
                whole_directory = os.path.dirname(input_path)
                start_directory, base_directory = os.path.split(whole_directory)
                directory = functions.unixify_path(start_directory)
                file_name = os.path.basename(input_path)
                name, ext = os.path.splitext(file_name)
                self.project_directory_textbox.setText(directory)
                self.project_name_textbox.setText(name)
            return True
        self.checkbox_input_directory.setPixmap(self.error_image)
        self.display_message(
            f"Invalid {self.importer_name} project directory!",
            "error",
        )
        return False

    def _check_root_dir(self) -> bool:
        root_path = self.project_directory_textbox.text()
        check_result = purefunctions.is_ascii_only_and_safe(root_path)
        if os.path.isdir(root_path) and check_result == "safe":
            self.checkbox_project_directory.setPixmap(self.ok_image)
            self.display_message(
                "Parent directory is valid.",
                "success",
            )
            if data.default_project_create_directory != root_path:
                data.default_project_create_directory = root_path
                self.main_form.settings.save()
            return True
        self.checkbox_project_directory.setPixmap(self.error_image)
        message = "Invalid parent directory!"
        if check_result != "safe":
            message = "Parent directory has invalid characters!"
        self.display_message(message, "error")
        return False

    def _check_project_name(self) -> bool:
        name = self.project_name_textbox.text()
        if functions.is_pathname_valid(name):
            root_path = self.project_directory_textbox.text()
            if os.path.isdir(os.path.join(root_path, name)):
                self.checkbox_project_name.setPixmap(self.warning_image)
                self.checkbox_project_name.setToolTip(
                    _ht_.project_import_info(
                        self,
                        "project_name_already_exists",
                        self.vendor,
                    )
                )
            else:
                self.checkbox_project_name.setPixmap(self.ok_image)
                self.checkbox_project_name.setToolTip(
                    _ht_.project_import_info(
                        self,
                        "project_name_ok",
                        self.vendor,
                    )
                )
            return True
        self.checkbox_project_name.setPixmap(self.error_image)
        return False

    def _check_optional_settings(self) -> bool:
        if self.vendor == "arduino":
            board_cb = self.board_selection.combobox
            chip_cb = self.chip_selection.combobox
            if (
                "select" in board_cb.get_selected_item_name().lower()
                or "select" in chip_cb.get_selected_item_name().lower()
            ):
                return False
            return True
        return True

    def _check_hardware_selection(self) -> bool:
        board_cb = self.board_selection.combobox
        chip_cb = self.chip_selection.combobox
        board = board_cb.get_selected_item_name().lower()
        chip = chip_cb.get_selected_item_name().lower()
        if board == "empty" or chip == "empty":
            return False
        return True

    def proceed(self) -> None:
        input_directory = self.input_directory_textbox.text()
        rootpath = self.project_directory_textbox.text()
        project_name = self.project_name_textbox.text()
        project_directory = functions.unixify_path_join(rootpath, project_name)
        replace = False
        if self.replace_box.check_box.isChecked():
            replace = True
        else:
            # Warn if the directory already exists
            if os.path.isdir(project_directory):
                warning = (
                    f"The selected project directory {q}{project_directory}{q} "
                    f"already exists!\n"
                    f"Continuing will clear it{q}s contents and put the "
                    f"imported project inside it!\n"
                    f"Are you sure?"
                )
                reply = gui.dialogs.popupdialog.PopupDialog.warning(warning)
                if reply != qt.QMessageBox.StandardButton.Yes:
                    return
        try:
            self.display_message(
                "Project creation started ...\n"
                "This dialog will automatically close "
                "and a project window will open "
                "when the project has been created."
            )
            # Return data according to vendor
            if self.vendor == "stm":
                import_data = {
                    "vendor": self.vendor,
                    "input_directory": input_directory,
                    "project_directory": project_directory,
                    "replace": replace,
                }
            elif self.vendor == "arduino":
                board_cb = self.board_selection.combobox
                chip_cb = self.chip_selection.combobox
                import_data = {
                    "vendor": self.vendor,
                    "input_directory": input_directory,
                    "project_directory": project_directory,
                    "replace": replace,
                    "board": board_cb.get_selected_item_name(),
                    "chip": chip_cb.get_selected_item_name(),
                }
            else:
                self.display_message(
                    "This project type is unimplemented yet!",
                    "warning",
                )
                return
            self.main_form.projects.import_project(
                import_data=import_data,
                import_wizard=self,
            )
        except:
            traceback.print_exc()
            self.display_message(
                "This project type is unimplemented yet!",
                "warning",
            )
        return

    def hide_dialog(self) -> None:
        self.main_form.display.dialog_hide("project_import_options")
        return

    def showEvent(self, event) -> None:
        self.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.MinimumExpanding,
            )
        )
        self.resize_and_center()
        self.update_check_size()
        return


class EmptyOptions(qt.QGroupBox):
    def __init__(self, parent, project_data):
        super().__init__(parent)

        self._parent = parent
        self.project_data = project_data

        self.ok_image = iconfunctions.get_qpixmap("icons/dialog/checkmark.png")
        self.error_image = iconfunctions.get_qpixmap("icons/dialog/cross.png")
        self.warning_image = iconfunctions.get_qpixmap(
            "icons/dialog/warning.png"
        )

        self.setStyleSheet(
            """
            QGroupBox {{
                border: 0px;
            }}
            """
        )
        self.layout: qt.QVBoxLayout = cast(
            qt.QVBoxLayout,
            gui.templates.widgetgenerator.create_layout(vertical=True),
        )
        self.layout.setSpacing(5)
        self.setLayout(self.layout)

        # Insert label to warn about empty projects
        self.empty_project_warning_label = qt.QLabel()
        self.empty_project_warning_label.setStyleSheet(
            f"""
        QLabel {{
            background: transparent;
            color: #cc0000;
            border: none;
        }}
        """
        )
        self.empty_project_warning_label.setFont(data.get_general_font())
        self.empty_project_warning_label.setText(
            f"WARNING: You{q}re going to create an empty project. That means you{q}ll have <br>"
            f"a default makefile, linkerscript and some other support-files, but there<br>"
            f"won{q}t be any source code.<br>"
        )
        self.layout.addWidget(self.empty_project_warning_label)

        self.stored_gboxes = {}
        button_size = get_button_size()

        # Flags
        self.project_name_flag = False
        """
        Project directory groupbox
        """

        def project_directory_info_func(*args):
            _ht_.project_creation_info(self._parent, "project_directory")

        self.stored_gboxes["project_directory"] = (
            self._parent.create_info_groupbox(
                text="Project's parent directory:",
                vertical=False,
                info_func=project_directory_info_func,
            )
        )
        self.stored_gboxes["project_directory"].setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Fixed,
        )
        self.project_layout = self.stored_gboxes["project_directory"].layout()
        self.project_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        # Project directory textbox and helper widgets
        self.project_directory_textbox = self._parent.create_textbox(
            text_change_func=self.check_project_validity
        )
        self._parent._set_widget_message(
            self.project_directory_textbox,
            "Enter the project's parent directory here",
        )

        def select_root_dir():
            dir_dialog = qt.QFileDialog(self)
            dir_dialog.setFileMode(qt.QFileDialog.FileMode.Directory)
            path = data.default_project_create_directory
            if not os.path.isdir(path):
                path = data.user_directory
            directory = qt.QFileDialog.getExistingDirectory(
                self, "Select project parent directory", path
            )
            if directory is not None:
                self.project_directory_textbox.setText(directory)

        self.project_directory_button = self._parent.create_pushbutton(
            parent=self,
            tool_tip="Choose the project's directory with a dialog",
            icon_path=f"icons/folder/open/folder.png",
            click_func=select_root_dir,
        )
        self.project_directory_button.setStyleSheet(
            gui.stylesheets.button.get_simple_toggle_stylesheet()
        )
        # Validity checkbox
        self.checkbox_project_directory = (
            gui.templates.widgetgenerator.create_check_label(
                "CheckDir",
                (button_size, button_size),
            )
        )
        self._parent._set_widget_message(
            self.checkbox_project_directory,
            "Indicates whether the project parent directory is valid",
        )
        pd_widgets = (
            self.project_directory_textbox,
            self.project_directory_button,
            self.checkbox_project_directory,
        )
        for w in pd_widgets:
            self.project_layout.addWidget(w)
            self.project_layout.setAlignment(
                w, qt.Qt.AlignmentFlag.AlignVCenter
            )

        """
        Project name groupbox
        """

        def project_name_info_func(clicked):
            _ht_.project_creation_info(self._parent, "project_name")

        self.stored_gboxes["project_name"] = self._parent.create_info_groupbox(
            text="Project name:",
            vertical=True,
            info_func=project_name_info_func,
        )
        self.stored_gboxes["project_name"].setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Fixed,
        )
        self.project_name_layout = self.stored_gboxes["project_name"].layout()
        self.project_name_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )

        # Project name textbox
        def text_edited(new_text):
            if new_text == "":
                self.project_name_flag = False
                self.project_name_textbox.setProperty("autofilled", True)
            else:
                self.project_name_flag = True
                self.project_name_textbox.setProperty("autofilled", False)
            self.project_name_textbox.style().unpolish(
                self.project_name_textbox
            )
            self.project_name_textbox.style().polish(self.project_name_textbox)
            self.project_name_textbox.repaint()

        self.project_name_textbox = self._parent.create_textbox(
            text_change_func=self.check_project_validity
        )
        self.project_name_textbox.textEdited.connect(text_edited)
        self.project_name_textbox.setProperty("autofilled", True)
        self._parent._set_widget_message(
            self.project_name_textbox,
            "Displays the project name, which is the project directory "
            + "that will be created inside the parent directory.",
        )
        self.checkbox_project_name = (
            gui.templates.widgetgenerator.create_check_label(
                "CheckName",
                (button_size, button_size),
            )
        )
        self._parent._set_widget_message(
            self.checkbox_project_name,
            "Indicates whether the project name is valid",
        )

        # [Kristof] Create a horizontal layout that will contain the textfield
        # and the check/warning sign at the right.
        hlyt = qt.QHBoxLayout()
        hlyt.setContentsMargins(0, 0, 0, 0)
        hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        hlyt.addWidget(self.project_name_textbox)
        hlyt.addWidget(self.checkbox_project_name)
        # [Kristof] Create a QLabel() with the following note:
        # 'A folder with this name will be created'
        self.project_name_label = qt.QLabel()
        self.project_name_label.setStyleSheet(
            f"""
        QLabel {{
            background: transparent;
            color: #888a85;
            border: none;
        }}
        """
        )
        self.project_name_label.setFont(data.get_general_font())
        self.project_name_label.setText(
            "A folder with this name will be created"
        )
        # [Kristof] Add first the QLabel() with the note to this groupbox, then
        # add the horizontal layout that contains the textfield and the check/
        # warning sign.
        self.project_name_layout.addWidget(self.project_name_label)
        self.project_name_layout.addLayout(hlyt)

        self.project_name_layout.setAlignment(
            self.checkbox_project_name,
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter,
        )

        self.layout.addWidget(self.stored_gboxes["project_directory"])
        self.layout.addWidget(self.stored_gboxes["project_name"])
        self.init_options()

    def init_options(self):
        filter_box = gui.templates.widgetgenerator.create_groupbox_with_layout(
            "Selection",
            "",
            vertical=False,
            adjust_margins_to_text=True,
        )
        filter_box.layout().setSpacing(1)

        vendors = []
        boards = []
        boards_cache = []
        chips = []
        chips_cache = []
        vendor_dict = hardware_api.various.get_vendor_chip_board_dict()
        for k, v in vendor_dict.items():
            vendor_name = k
            vendor_icon = _hardware_api_.HardwareDB().get_manufacturer_dict(k)[
                "icon"
            ]
            vendors.append(
                {
                    "text": vendor_name,
                    "icon": vendor_icon,
                    "enabled": True,
                    # New
                    "name": vendor_name,
                    "widgets": (
                        {"type": "image", "icon-path": vendor_icon},
                        {"type": "text", "text": vendor_name},
                    ),
                }
            )
            for chip, _boards in v.items():
                chip_name = chip
                chip_icon = "icons/chip/chip.png"
                if chip_name not in chips_cache:
                    chips.append(
                        {
                            "text": chip_name,
                            "icon": chip_icon,
                            "enabled": True,
                            # New
                            "name": chip_name,
                            "widgets": (
                                {"type": "image", "icon-path": chip_icon},
                                {"type": "text", "text": chip_name},
                            ),
                        }
                    )
                    chips_cache.append(chip_name)
                for b in _boards:
                    board_unicum: _board_unicum_.BOARD = _board_unicum_.BOARD(b)
                    board_name = b
                    board_icon = board_unicum.get_board_dict()["icon"]
                    if board_name not in boards_cache:
                        boards.append(
                            {
                                "text": board_name,
                                "icon": board_icon,
                                "enabled": True,
                                # New
                                "name": board_name,
                                "widgets": (
                                    {"type": "image", "icon-path": board_icon},
                                    {"type": "text", "text": board_name},
                                ),
                            }
                        )
                        boards_cache.append(board_name)
        vendors.sort(key=lambda x: x["text"])
        chips.sort(key=lambda x: x["text"])
        boards.sort(key=lambda x: x["text"])
        """
        Vendors
        """
        self.vendors = vendors
        vendor_select_box = self._create_selection_bar(
            "Vendor:",
            "Select a vendor",
            "Select a vendor from the dropdown list",
            "icons/checkbox/question.png",
            "Shows if the selected\nvendor is valid",
            vendors,
            info_type="vendor",
            additional_function=self.option_change,
            create_check=False,
        )
        self.stored_gboxes["vendor_select"] = vendor_select_box
        filter_box.layout().addWidget(vendor_select_box)
        """
        Boards
        """
        if not ("board_select" in self.stored_gboxes.keys()):
            board_select_box = self._create_selection_bar(
                "Board:",
                "Select a board",
                "Select a board from the dropdown list",
                "icons/checkbox/question.png",
                "Shows if the selected\nboard is valid",
                boards,
                info_type="board",
                additional_function=self.option_change,
                create_check=False,
            )
            self.stored_gboxes["board_select"] = board_select_box
            filter_box.layout().addWidget(board_select_box)
        else:
            self.stored_gboxes["board_select"].create_dropdown_menu(
                items=boards,
                custom_func=functools.partial(
                    self.option_change, self.stored_gboxes["board_select"]
                ),
            )

        """
        Chips
        """
        if not ("chip_select" in self.stored_gboxes.keys()):
            chip_select_box = self._create_selection_bar(
                "Chip:",
                "Select a chip",
                "Select a chip from the dropdown list",
                "icons/checkbox/question.png",
                "Shows if the selected\nchip is valid",
                chips,
                info_type="chip",
                additional_function=self.option_change,
                create_check=False,
            )
            self.stored_gboxes["chip_select"] = chip_select_box
            filter_box.layout().addWidget(chip_select_box)
        else:
            self.stored_gboxes["chip_select"].create_dropdown_menu(
                items=chips,
                custom_func=functools.partial(
                    self.option_change, self.stored_gboxes["chip_select"]
                ),
            )

        # Add the filter box to the wizard
        self.layout.addWidget(filter_box)

        # Bulk set groupbox constraints
        for key, gb in self.stored_gboxes.items():
            gb.setMinimumWidth(100)

        # Messages and create button
        self.cancel_button = self._parent.cancel_button
        self.project_create_button = self._parent.next_button

        self.check_project_validity()

        # Restore stored project directory if valid
        default_directory = data.get_default_project_directory()
        self.project_directory_textbox.setText(default_directory)

    def option_change(self, *args):
        if not hasattr(self, "option_change_lock"):
            self.option_change_lock = False
        if self.option_change_lock:
            return

        self.check_project_validity()

        def get_selection(text):
            result = text
            if (
                text.lower().startswith("select")
                or text.lower() == "empty"
                or text.lower() == "any"
            ):
                result = None
            return result

        # Reset check
        try:
            self.option_change_lock = True
            comboboxes = (
                "vendor_select",
                "board_select",
                "chip_select",
            )
            for c in comboboxes:
                text = get_selection(self.stored_gboxes[c].get_text())
                if text is not None and text.lower() == "any":
                    self.stored_gboxes[c].reset_selection()
        finally:
            self.option_change_lock = False

        # Store selected combobox texts
        vendor = get_selection(self.stored_gboxes["vendor_select"].get_text())
        board = get_selection(self.stored_gboxes["board_select"].get_text())
        chip = get_selection(self.stored_gboxes["chip_select"].get_text())

        vendors = []
        boards = []
        chips = []
        _vendors, _boards, _chips = (
            hardware_api.various.vendor_board_chip_filter(vendor, board, chip)
        )
        for v in _vendors:
            name = v
            icon = _hardware_api_.HardwareDB().get_manufacturer_dict(v)["icon"]
            vendors.append(
                {
                    "text": name,
                    "icon": icon,
                    "enabled": True,
                    # New
                    "name": name,
                    "widgets": (
                        {"type": "image", "icon-path": icon},
                        {"type": "text", "text": name},
                    ),
                }
            )
        # Chips
        for c in _chips:
            name = c
            icon = "icons/chip/chip.png"
            chips.append(
                {
                    "text": name,
                    "icon": icon,
                    "enabled": True,
                    # New
                    "name": name,
                    "widgets": (
                        {"type": "image", "icon-path": icon},
                        {"type": "text", "text": name},
                    ),
                }
            )

        # Boards
        for b in _boards:
            board_unicum: _board_unicum_.BOARD = _board_unicum_.BOARD(b)
            name = b
            icon = board_unicum.get_board_dict()["icon"]
            boards.append(
                {
                    "text": name,
                    "icon": icon,
                    "enabled": True,
                    # New
                    "name": name,
                    "widgets": (
                        {"type": "image", "icon-path": icon},
                        {"type": "text", "text": name},
                    ),
                }
            )
        vendors.sort(key=lambda x: x["text"])
        chips.sort(key=lambda x: x["text"])
        boards.sort(key=lambda x: x["text"])

        # Vendors
        self.vendors = vendors.copy()
        vendors.insert(
            0,
            {
                "text": "any",
                "icon": "icons/checkbox/question.png",
                "enabled": True,
                # New
                "name": "any",
                "widgets": (
                    {
                        "type": "image",
                        "icon-path": "icons/checkbox/question.png",
                    },
                    {"type": "text", "text": "Any"},
                ),
            },
        )
        self.stored_gboxes["vendor_select"].create_dropdown_menu(
            items=vendors,
            custom_func=functools.partial(
                self.option_change, self.stored_gboxes["vendor_select"]
            ),
            reset_selection=False,
        )
        # Boards
        boards.insert(
            0,
            {
                "text": "Any",
                "icon": "icons/checkbox/question.png",
                "enabled": True,
                # New
                "name": "any",
                "widgets": (
                    {
                        "type": "image",
                        "icon-path": "icons/checkbox/question.png",
                    },
                    {"type": "text", "text": "Any"},
                ),
            },
        )
        self.stored_gboxes["board_select"].create_dropdown_menu(
            items=boards,
            custom_func=functools.partial(
                self.option_change, self.stored_gboxes["board_select"]
            ),
            reset_selection=False,
        )
        # Chips
        chips.insert(
            0,
            {
                "text": "Any",
                "icon": "icons/checkbox/question.png",
                "enabled": True,
                # New
                "name": "any",
                "widgets": (
                    {
                        "type": "image",
                        "icon-path": "icons/checkbox/question.png",
                    },
                    {"type": "text", "text": "Any"},
                ),
            },
        )
        self.stored_gboxes["chip_select"].create_dropdown_menu(
            items=chips,
            custom_func=functools.partial(
                self.option_change, self.stored_gboxes["chip_select"]
            ),
            reset_selection=False,
        )

        # Set special empty items in comboboxes
        if vendor is None:
            self.stored_gboxes["vendor_select"].combobox.set_selected_item(
                {
                    "name": "empty",
                    "widgets": (
                        {
                            "type": "image",
                            "icon-path": "icons/checkbox/question.png",
                        },
                        {"type": "text", "text": "Select a vendor"},
                    ),
                }
            )
            self.stored_gboxes["vendor_select"].combobox.remove_item("any")
        if board is None:
            self.stored_gboxes["board_select"].combobox.set_selected_item(
                {
                    "name": "empty",
                    "widgets": (
                        {
                            "type": "image",
                            "icon-path": "icons/checkbox/question.png",
                        },
                        {"type": "text", "text": "Select a board"},
                    ),
                }
            )
            self.stored_gboxes["board_select"].combobox.remove_item("any")
        if chip is None:
            self.stored_gboxes["chip_select"].combobox.set_selected_item(
                {
                    "name": "empty",
                    "widgets": (
                        {
                            "type": "image",
                            "icon-path": "icons/checkbox/question.png",
                        },
                        {"type": "text", "text": "Select a chip"},
                    ),
                }
            )
            self.stored_gboxes["chip_select"].combobox.remove_item("any")

    def _create_selection_bar(
        self,
        gb_text,
        btn_text,
        tooltip,
        btn_icon,
        check_tooltip,
        actions,
        action_groups=None,
        custom_func=None,
        info_type=None,
        additional_function=None,
        create_check=True,
    ):
        return self._parent.create_selection_bar(
            gb_text,
            btn_text,
            tooltip,
            btn_icon,
            check_tooltip,
            actions,
            action_groups=action_groups,
            custom_func=custom_func,
            info_type=info_type,
            additional_function=additional_function,
            create_check=create_check,
        )

    def check_options(self):
        valid = True
        for gb_name in ("board_select", "chip_select"):
            gb = self.stored_gboxes[gb_name]
            text = gb.combobox.get_selected_item_name()
            if text.startswith("Select"):
                valid = False
                if hasattr(gb, "status_box"):
                    gb.status_box.setPixmap(self.error_image)
            else:
                if hasattr(gb, "status_box"):
                    gb.status_box.setPixmap(self.ok_image)
        return valid

    def check_project_validity(self, *args):
        self._parent.next_button.setEnabled(False)
        self._parent.selected_options = {
            "project_path": None,
            "vendor": None,
            "board": None,
            "chip": None,
        }
        checks = [
            self.check_options(),
            self._check_root_dir(),
            self._check_project_name(),
        ]
        if all(checks) == False:
            return

        directory = self.project_directory_textbox.text()
        project_name = self.project_name_textbox.text()
        project_path = functions.unixify_path_join(directory, project_name)

        self._parent.selected_options = {
            "project_path": project_path,
            "vendor": (
                self.stored_gboxes[
                    "vendor_select"
                ].combobox.get_selected_item_name()
            ),
            "board": (
                self.stored_gboxes[
                    "board_select"
                ].combobox.get_selected_item_name()
            ),
            "chip": (
                self.stored_gboxes[
                    "chip_select"
                ].combobox.get_selected_item_name()
            ),
        }
        self._parent.next_button.setEnabled(True)

    def display_message(self, *args):
        #        print(args)
        pass

    def _check_root_dir(self):
        root_path = self.project_directory_textbox.text()
        if os.path.isdir(root_path):
            if data.default_project_create_directory != root_path:
                data.default_project_create_directory = root_path
                self._parent.main_form.settings.save()
            # Check access
            if os.access(root_path, os.W_OK):
                self.checkbox_project_directory.setPixmap(self.ok_image)
                self.checkbox_project_directory.setToolTip(
                    _ht_.project_import_info(
                        self._parent, "project_directory_valid", None
                    )
                )
                self.display_message("Parent directory is valid.", "success")
                return True
            else:
                self.checkbox_project_directory.setPixmap(self.error_image)
                self.checkbox_project_directory.setToolTip(
                    _ht_.project_import_info(
                        self._parent,
                        "project_directory_no_write_permission",
                        None,
                    )
                )
                self.display_message(
                    "Current user does not have write access to the parent directory.",
                    "success",
                )
                return False
        else:
            self.checkbox_project_directory.setPixmap(self.error_image)
            self.checkbox_project_directory.setToolTip(
                _ht_.project_import_info(
                    self._parent, "project_directory_invalid", None
                )
            )
            self.display_message("Invalid parent directory!", "error")
            return False

    def _check_project_name(self):
        name = self.project_name_textbox.text()
        if functions.is_pathname_valid(name):
            root_path = self.project_directory_textbox.text()
            if os.access(root_path, os.W_OK):
                if os.path.isdir(os.path.join(root_path, name)):
                    self.checkbox_project_name.setPixmap(self.warning_image)
                    self.checkbox_project_name.setToolTip(
                        _ht_.project_import_info(
                            self._parent, "project_name_already_exists", None
                        )
                    )
                else:
                    self.checkbox_project_name.setPixmap(self.ok_image)
                    self.checkbox_project_name.setToolTip(
                        _ht_.project_import_info(
                            self._parent, "project_name_ok", None
                        )
                    )
                return True
            else:
                self.checkbox_project_name.setPixmap(self.error_image)
                self.checkbox_project_name.setToolTip(
                    _ht_.project_import_info(
                        self._parent,
                        "project_directory_no_write_permission",
                        None,
                    )
                )
                return False
        else:
            self.checkbox_project_name.setPixmap(self.error_image)
            self.checkbox_project_name.setToolTip(
                _ht_.project_import_info(
                    self._parent, "project_name_error", None
                )
            )
            return False
