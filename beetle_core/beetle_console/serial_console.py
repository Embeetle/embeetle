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
import re, threading, traceback, sys
import qt, data, purefunctions, functions, iconfunctions
import gui.dialogs.popupdialog
import beetle_console.console_widget as _console_widget_
import gui.templates.baseobject as _baseobject_
import gui.stylesheets.button as _btn_style_
import gui.stylesheets.scrollbar as _sb_
import gui.helpers.advancedcombobox as _advancedcombobox_
import beetle_console.serial_port as _serial_port_
import wizards.serial_wizard.serial_wizard as _serial_wizard_

if TYPE_CHECKING:
    import gui.forms.mainwindow as _mainwindow_
    import gui.forms.homewindow as _homewindow_
    import project.segments.probe_seg.probe as _probe_
nop = lambda *a, **k: None
q = "'"
dq = '"'
white = '<span style="color:#ffffff">'
blue = '<span style="color:#8fb3d9">'
yellow = '<span style="color:#fce94f">'
red = '<span style="color:#ef2929">'
green = '<span style="color:#a1e85b">'
purple = '<span style="color:#c5a4c1">'
end = "</span>"


# ^                                         SERIAL CONSOLE                                         ^#
# % ============================================================================================== %#
# % SerialConsole()                                                                                %#
# %                                                                                                %#


class SerialConsole(qt.QFrame, _baseobject_.BaseObject):
    """A SerialConsole()-instance represents the Serial Monitor. This instance
    is subclassed from both QFrame() and BaseObject() such that it nicely fits
    into an Embeetle QTabWidget().

    The heart of the SerialConsole() is its ConsoleWidget()-instance. That's a subclassed QPlain-
    TextEdit() widget that behaves more or less like a console. The user can interact with this
    widget - typing and executing commands - but you can also interact programmatically with it.
    """

    def __init__(
        self,
        parent: qt.QTabWidget,
        main_form: Union[_mainwindow_.MainWindow, _homewindow_.HomeWindow],
        name: str,
    ) -> None:
        """
        :param parent:      The QTabWidget() holding this MakeConsole()-instance.

        :param main_form:   The Project Window or Home Window.

        :param name:        Name for this SerialConsole()-widget, to be displayed in its tab.
        """
        qt.QFrame.__init__(self)
        _baseobject_.BaseObject.__init__(
            self,
            parent=parent,
            main_form=main_form,
            name=name,
            icon=iconfunctions.get_qicon("icons/console/console.png"),
        )
        data.serial_console = self
        self.__parent = parent
        self.__main_form = main_form
        self.__name = name
        self.__dead = False
        self.setStyleSheet(
            """
            QFrame {
                background : transparent;
                border     : none;
                padding    : 0px;
                margin     : 0px;
            }
        """
        )
        self.__advanced_settings = {
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
            "show_newlines": True,
        }

        # * Layout
        self.__lyt = qt.QVBoxLayout()
        self.__lyt.setSpacing(2)
        self.__lyt.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__lyt)

        # * Console widget
        self.__console_widget: Optional[_console_widget_.ConsoleWidget] = None

        # * Other widgets
        self.__output_settings_hlyt: Optional[qt.QHBoxLayout] = None
        self.__connect_btn: Optional[qt.QPushButton] = None
        self.__comport_lyt: Optional[qt.QHBoxLayout] = None
        self.__sep_line: Optional[qt.QWidget] = None
        self.__comport_btn: Optional[qt.QPushButton] = None
        self.__comport_dropdown: Optional[
            _advancedcombobox_.AdvancedComboBox
        ] = None
        self.__baud_lbl: Optional[qt.QLabel] = None
        self.__baud_dropdown: Optional[_advancedcombobox_.AdvancedComboBox] = (
            None
        )
        self.__mode_lbl: Optional[qt.QLabel] = None
        self.__mode_dropdown: Optional[_advancedcombobox_.AdvancedComboBox] = (
            None
        )
        self.__advanced_lbl: Optional[qt.QLabel] = None
        self.__advanced_btn: Optional[qt.QPushButton] = None
        self.__serial_wizard: Optional[_serial_wizard_.SerialWizard] = None
        self.__input_line: Optional[SerialInputWidget] = None
        self.__input_settings_hlyt: Optional[qt.QHBoxLayout] = None
        self.__newline_lbl: Optional[qt.QLabel] = None
        self.__newline_dropdown: Optional[
            _advancedcombobox_.AdvancedComboBox
        ] = None
        self.__newline_dropdown_prev_selection: Optional[str] = None
        self.init_widgets()
        return

    def get_comport_dropdown(
        self,
    ) -> Optional[_advancedcombobox_.AdvancedComboBox]:
        """"""
        return self.__comport_dropdown

    def init_widgets(self) -> None:
        """Initialize all widgets."""
        size = data.get_general_icon_pixelsize()

        #! =====================================[ TOP LINE ]===================================== !#
        if self.__output_settings_hlyt is None:
            self.__output_settings_hlyt = qt.QHBoxLayout()
            self.__output_settings_hlyt.setSpacing(0)
            self.__output_settings_hlyt.setContentsMargins(0, 0, 0, 0)
            self.__output_settings_hlyt.setAlignment(
                qt.Qt.AlignmentFlag.AlignLeft
            )
            self.__lyt.addLayout(self.__output_settings_hlyt)

        # * ---------------[ Connect/Disconnect ]--------------- *#
        # $ Button
        if self.__connect_btn is None:
            self.__connect_btn = qt.QPushButton(self)
            self.__connect_btn.setIcon(
                iconfunctions.get_qicon("icons/console/disconnected.png")
            )
            self.__connect_btn.setText(" Connect     ")
            self.__connect_btn.clicked.connect(self.toggle_serial_connection)
            self.__output_settings_hlyt.addWidget(self.__connect_btn)
        self.__connect_btn.setStyleSheet(
            _btn_style_.get_text_btn_stylesheet(
                font_pointsize=data.get_general_font_pointsize(),
            )
        )
        self.__connect_btn.setFixedHeight(size)
        self.__connect_btn.setIconSize(qt.create_qsize(size, size))
        self.__connect_btn.style().unpolish(self.__connect_btn)
        self.__connect_btn.style().polish(self.__connect_btn)
        self.__connect_btn.update()

        # * --------------------[ COM-Port ]-------------------- *#
        # $ Sub-layout
        if self.__comport_lyt is None:
            self.__comport_lyt = qt.QHBoxLayout()
            self.__comport_lyt.setSpacing(5)
            self.__comport_lyt.setContentsMargins(0, 0, 0, 0)
            self.__output_settings_hlyt.addLayout(self.__comport_lyt)

        # $ Separator line
        if self.__sep_line is None:
            self.__sep_line = qt.QWidget()
            self.__sep_line.setFixedWidth(1)
            self.__sep_line.setStyleSheet("background-color: #c0c0c0;")
            self.__comport_lyt.addWidget(self.__sep_line)
        self.__sep_line.setFixedHeight(size)
        self.__sep_line.update()

        # $ Image
        if self.__comport_btn is None:
            self.__comport_btn = qt.QPushButton(self)
            self.__comport_btn.setStyleSheet(
                """
            QPushButton {
                background: transparent;
                border: none;
            }
            """
            )
            self.__comport_btn.setIcon(
                iconfunctions.get_qicon("icons/console/serial_monitor.png")
            )
            self.__comport_lyt.addWidget(self.__comport_btn)
        self.__comport_btn.setFixedSize(size, size)
        self.__comport_btn.setIconSize(qt.create_qsize(size, size))
        self.__comport_btn.update()

        # $ Dropdown
        if self.__comport_dropdown is None:
            self.refresh_comport_dropdown_widget()

        # * --------------------[ Baudrate ]-------------------- *#
        # $ Label
        if self.__baud_lbl is None:
            self.__baud_lbl = qt.QLabel(self)
            self.__baud_lbl.setText("  Baudrate:")
            self.__output_settings_hlyt.addWidget(self.__baud_lbl)
            self.__baud_lbl.setStyleSheet(
                f"""
            QLabel {{
                color: {data.theme['fonts']['default']['color']};
                background: transparent;
                border: none;
            }}
            """
            )
        self.__baud_lbl.setFont(data.get_general_font())
        self.__baud_lbl.update()

        # $ Dropdown
        if self.__baud_dropdown is None:
            self.__baud_dropdown = _advancedcombobox_.AdvancedComboBox(
                parent=self,
                image_size=size,
            )
            items = []
            text_color = "default"
            for baud in _serial_port_.SerialPort.BAUDRATES:
                items.append(
                    {
                        "name": f"{baud}",
                        "widgets": [
                            {
                                "type": "text",
                                "text": f"{baud}",
                                "color": text_color,
                            },
                        ],
                    }
                )
            self.__baud_dropdown.add_items(items)
            self.__baud_dropdown.set_selected_name("9600")
            self.__output_settings_hlyt.addWidget(self.__baud_dropdown)

        # * ----------------------[ Mode ]---------------------- *#
        # $ Label
        if self.__mode_lbl is None:
            self.__mode_lbl = qt.QLabel(self)
            self.__mode_lbl.setText("  Mode:")
            self.__output_settings_hlyt.addWidget(self.__mode_lbl)
            self.__mode_lbl.setStyleSheet(
                f"""
            QLabel {{
                color: {data.theme['fonts']['default']['color']};
                background: transparent;
                border: none;
            }}
            """
            )
        self.__mode_lbl.setFont(data.get_general_font())
        self.__mode_lbl.update()

        # $ Dropdown
        if self.__mode_dropdown is None:
            self.__mode_dropdown = _advancedcombobox_.AdvancedComboBox(
                parent=self,
                image_size=size,
            )
            items = []
            text_color = "default"
            for mode in ["ascii", "hex"]:
                items.append(
                    {
                        "name": f"{mode}",
                        "widgets": [
                            {
                                "type": "text",
                                "text": f"{mode}",
                                "color": text_color,
                            },
                        ],
                    }
                )
            self.__mode_dropdown.add_items(items)
            self.__mode_dropdown.set_selected_name("ascii")
            self.__mode_dropdown.selection_changed_from_to.connect(
                self.mode_selection_changed,
            )
            self.__output_settings_hlyt.addWidget(self.__mode_dropdown)

        # * --------------------[ Advanced ]-------------------- *#
        # $ Label
        if self.__advanced_lbl is None:
            self.__output_settings_hlyt.addStretch()
            self.__advanced_lbl = qt.QLabel(self)
            self.__advanced_lbl.setText("Advanced:")
            self.__output_settings_hlyt.addWidget(self.__advanced_lbl)
            self.__advanced_lbl.setStyleSheet(
                f"""
            QLabel {{
                color: {data.theme['fonts']['default']['color']};
                background: transparent;
                border: none;
            }}
            """
            )
        self.__advanced_lbl.setFont(data.get_general_font())
        self.__advanced_lbl.update()

        # $ Button
        if self.__advanced_btn is None:
            self.__advanced_btn = qt.QPushButton(self)
            self.__advanced_btn.setStyleSheet(_btn_style_.get_btn_stylesheet())
            self.__advanced_btn.setIcon(
                iconfunctions.get_qicon("icons/tab/burger.png")
            )
            self.__advanced_btn.clicked.connect(self.advanced_button_clicked)
            self.__output_settings_hlyt.addWidget(self.__advanced_btn)
        self.__advanced_btn.setFixedSize(size, size)
        self.__advanced_btn.setIconSize(qt.create_qsize(size, size))
        self.__advanced_btn.update()

        #! ==================================[ OUTPUT CONSOLE ]================================== !#
        if self.__console_widget is None:
            self.__console_widget = _console_widget_.ConsoleWidget(
                parent=self,
                readonly=True,
                cwd=None,
                fake_console=False,
                is_serial_monitor=True,
            )
            self.__lyt.addWidget(self.__console_widget)

        #! ====================================[ INPUT LINE ]==================================== !#
        if self.__input_line is None:
            self.__input_line = SerialInputWidget(self)
            self.__input_line.return_pressed_sig.connect(
                self.send_input_from_lineedit
            )
            self.__input_line.setEnabled(False)
            self.__lyt.addWidget(self.__input_line)
        self.__input_line.set_style()

        #! ====================================[ BOTTOM LINE ]=================================== !#
        if self.__input_settings_hlyt is None:
            self.__input_settings_hlyt = qt.QHBoxLayout()
            self.__input_settings_hlyt.setSpacing(0)
            self.__input_settings_hlyt.setContentsMargins(0, 0, 0, 0)
            self.__input_settings_hlyt.setAlignment(
                qt.Qt.AlignmentFlag.AlignLeft
            )
            self.__lyt.addLayout(self.__input_settings_hlyt)

        # * --------------------[ Newline ]--------------------- *#
        # $ Label
        if self.__newline_lbl is None:
            self.__newline_lbl = qt.QLabel(self)
            self.__newline_lbl.setText("Enter sends:")
            self.__input_settings_hlyt.addWidget(self.__newline_lbl)
            self.__newline_lbl.setStyleSheet(
                f"""
            QLabel {{
                color: {data.theme['fonts']['default']['color']};
                background: transparent;
                border: none;
            }}
            """
            )
        self.__newline_lbl.setFont(data.get_general_font())
        self.__newline_lbl.update()

        # $ Dropdown
        text_color = "default"
        if self.__newline_dropdown is None:
            self.__newline_dropdown = _advancedcombobox_.AdvancedComboBox(
                parent=self,
                image_size=size,
            )
            items = [
                {
                    "name": "\\n",
                    "widgets": [
                        {
                            "type": "text",
                            "text": f" \\n ",
                            "color": text_color,
                        },
                    ],
                },
                {
                    "name": "\\r\\n",
                    "widgets": [
                        {
                            "type": "text",
                            "text": f" \\r\\n ",
                            "color": text_color,
                        },
                    ],
                },
                {
                    "name": "\\r",
                    "widgets": [
                        {
                            "type": "text",
                            "text": f" \\r ",
                            "color": text_color,
                        },
                    ],
                },
                {
                    "name": "<nothing>",
                    "widgets": [
                        {
                            "type": "text",
                            "text": f" <nothing>",
                            "color": text_color,
                        },
                    ],
                },
            ]
            self.__newline_dropdown_prev_selection = "\\n"
            self.__newline_dropdown.add_items(items)
            self.__newline_dropdown.set_selected_name("\\n")
            self.__input_settings_hlyt.addWidget(self.__newline_dropdown)
        return

    def get_baud_selection(self) -> str:
        """"""
        return str(self.__baud_dropdown.get_selected_item_name()).strip()

    def get_advanced_setting(self, setting: str) -> str:
        """"""
        return self.__advanced_settings[setting]

    @qt.pyqtSlot(str, str)
    def comport_selection_changed(self, com1: str, com2: str) -> None:
        """Comport selection changed from 'com1' to 'com2'."""
        probe: _probe_.Probe = data.current_project.get_probe()
        probe.dropdown_selection_changed_from_to(
            dropdown_src="console",
            from_comport=com1,
            to_comport=com2,
        )
        return

    @qt.pyqtSlot(str, str)
    def mode_selection_changed(self, mode1: str, mode2: str) -> None:
        """Mode selection changed from 'mode1' to 'mode2'."""
        if mode1 == mode2:
            return
        if mode2.strip() == "hex":
            self.__newline_dropdown_prev_selection = (
                self.__newline_dropdown.get_selected_item_name()
            )
            self.__newline_dropdown.set_selected_name("<nothing>")
            self.__newline_lbl.setEnabled(False)
            self.__newline_dropdown.setEnabled(False)
            self.__newline_lbl.update()
            self.__newline_dropdown.update()
            self.__newline_dropdown.hide()
            self.__newline_lbl.hide()
        elif mode2.strip() == "ascii":
            self.__newline_lbl.show()
            self.__newline_dropdown.show()
            self.__newline_dropdown.set_selected_name(
                self.__newline_dropdown_prev_selection
            )
            self.__newline_lbl.setEnabled(True)
            self.__newline_dropdown.setEnabled(True)
            self.__newline_lbl.update()
            self.__newline_dropdown.update()
        else:
            assert False
        if self.__console_widget.is_serial_port_open():
            self.modify_serial_port_settings()
        return

    @qt.pyqtSlot()
    def advanced_button_clicked(self) -> None:
        """User clicked the hamburger icon on the right."""
        if (self.__serial_wizard is not None) and qt.sip.isdeleted(
            self.__serial_wizard
        ):
            self.__serial_wizard = None
        if self.__serial_wizard is not None:
            # push wizard to top
            try:
                self.__serial_wizard.raise_()
            except:
                traceback.print_exc()
            return
        assert self.__serial_wizard is None
        self.__serial_wizard = _serial_wizard_.SerialWizard(
            parent=data.main_form,
            callback=self.__finish_serial_wizard,
            callbackArg=None,
        )
        self.__serial_wizard.show_wizard(
            port_open=self.__console_widget.is_serial_port_open(),
            handle=self,
            baudrate=self.__baud_dropdown.get_selected_item_name(),
            mode=self.__mode_dropdown.get_selected_item_name(),
            bytesize=self.__advanced_settings["bytesize"],
            parity=self.__advanced_settings["parity"],
            stopbits=self.__advanced_settings["stopbits"],
            show_newlines=self.__advanced_settings["show_newlines"],
        )
        return

    def __finish_serial_wizard(self, *args, **kwargs) -> None:
        """"""
        self.__serial_wizard = None
        return

    def apply_advanced_settings(
        self,
        baudrate: int,
        mode: str,
        bytesize: int,
        parity: str,
        stopbits: Union[int, float],
        show_newlines: bool,
    ) -> None:
        """This function should be called if the user clicks 'SAVE' in the
        advanced wizard.

        'bytesize' : 8, 'parity'   : 'N', 'stopbits' : 1,
        """
        self.__baud_dropdown.set_selected_name(str(baudrate))
        mode1 = self.__mode_dropdown.get_selected_item_name()
        mode2 = str(mode)
        self.__mode_dropdown.set_selected_name(mode2)
        self.mode_selection_changed(mode1, mode2)
        self.__advanced_settings["bytesize"] = bytesize
        self.__advanced_settings["parity"] = parity
        self.__advanced_settings["stopbits"] = stopbits
        self.__advanced_settings["show_newlines"] = show_newlines
        if self.__console_widget.is_serial_port_open():
            self.modify_serial_port_settings()
        return

    def refresh_comport_dropdown_widget(self, *args) -> None:
        """"""
        probe: _probe_.Probe = data.current_project.get_probe()
        size = data.get_general_icon_pixelsize()
        if self.__comport_dropdown is None:
            self.__comport_dropdown = _advancedcombobox_.AdvancedComboBox(
                parent=None,
                image_size=size,
            )
            self.__comport_dropdown.selection_changed_from_to.connect(
                self.comport_selection_changed
            )
            self.__comport_lyt.addWidget(self.__comport_dropdown)
        probe.refresh_comport_dropdown("console")
        return

    def modify_serial_port_settings(self) -> None:
        """Update the settings of a running serial connection."""
        assert self.__console_widget.is_serial_port_open()
        # $ Line endings
        show_newlines = self.__advanced_settings["show_newlines"]

        # $ Mode
        # Attention: code duplicated in toggle_serial_connection()
        mode: Optional[str] = None
        mode_str = self.__mode_dropdown.get_selected_item_name().strip()
        if mode_str == "ascii":
            mode = "html-ascii"
        else:
            mode = "html-hex"
        self.__input_line.set_mode(mode_str)

        # * Apply
        self.__console_widget.modify_serial_port_settings(
            show_newlines=show_newlines,
            mode=mode,
        )
        return

    def is_serial_port_open(self) -> bool:
        """Return True if serial port is currently connected."""
        return self.__console_widget.is_serial_port_open()

    def toggle_serial_connection(self) -> None:
        """Try to open the serial port as selected in the dropdown menu."""
        # $ COM-Port
        port = self.__comport_dropdown.get_selected_item_name()

        # $ Baudrate
        baudrate_str = self.__baud_dropdown.get_selected_item_name()
        baudrate = 9600
        try:
            baudrate = int(baudrate_str)
        except Exception as e:
            purefunctions.printc(
                f"ERROR: Baudrate setting cannot be converted to "
                f"int: {baudrate_str}",
                color="error",
            )
            baudrate = 9600

        # $ Bytesize
        bytesize = 8
        try:
            bytesize = int(self.__advanced_settings["bytesize"])
        except Exception as e:
            purefunctions.printc(
                f"ERROR: Cannot handle bytesize "
                f'{self.__advanced_settings["bytesize"]}',
                color="error",
            )
            bytesize = 8

        # $ Parity
        parity = "N"
        try:
            parity = str(self.__advanced_settings["parity"])
        except Exception as e:
            purefunctions.printc(
                f"ERROR: Cannot handle parity "
                f'{self.__advanced_settings["parity"]}',
                color="error",
            )
            parity = "N"

        # $ Stopbits
        stopbits = 1
        try:
            stopbits = int(self.__advanced_settings["stopbits"])
        except Exception as e:
            try:
                stopbits = float(
                    self.__stopbits_dropdown.get_selected_item_name()
                )
            except Exception as e:
                purefunctions.printc(
                    f"ERROR: Cannot handle stop bits "
                    f'{self.__advanced_settings["stopbits"]}',
                    color="error",
                )
                stopbits = 1

        # $ Line endings
        show_newlines = self.__advanced_settings["show_newlines"]

        # $ Mode
        # Attention: code duplicated in modify_serial_port_settings()
        mode: Optional[str] = None
        mode_str = self.__mode_dropdown.get_selected_item_name().strip()
        if mode_str == "ascii":
            mode = "html-ascii"
        else:
            mode = "html-hex"
        self.__input_line.set_mode(mode_str)

        # * CLOSE THE PORT
        if self.__console_widget.is_serial_port_open():
            self.__console_widget.close_serial_port()
            self.__connect_btn.setIcon(
                iconfunctions.get_qicon("icons/console/disconnected.png")
            )
            size = data.get_general_icon_pixelsize()
            self.__connect_btn.setIconSize(qt.create_qsize(size, size))
            self.__connect_btn.setText(" Connect     ")
            self.__connect_btn.style().unpolish(self.__connect_btn)
            self.__connect_btn.style().polish(self.__connect_btn)
            self.__connect_btn.update()
            self.__input_line.setEnabled(False)
            self.__input_line.update()
            self.__comport_dropdown.setEnabled(True)
            self.__comport_dropdown.update()
            self.__baud_dropdown.setEnabled(True)
            self.__baud_dropdown.update()
            if (
                (self.__serial_wizard is not None)
                and (not qt.sip.isdeleted(self.__serial_wizard))
                and self.__serial_wizard.isVisible()
            ):
                self.__serial_wizard.set_port_status(False)
            return

        # * OPEN THE PORT
        success = self.__console_widget.open_serial_port(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            show_newlines=show_newlines,
            mode=mode,
        )
        if success:
            self.__connect_btn.setIcon(
                iconfunctions.get_qicon("icons/console/connected.png")
            )
            size = data.get_general_icon_pixelsize()
            self.__connect_btn.setIconSize(qt.create_qsize(size, size))
            self.__connect_btn.setText(" Disconnect  ")
            self.__connect_btn.style().unpolish(self.__connect_btn)
            self.__connect_btn.style().polish(self.__connect_btn)
            self.__connect_btn.update()
            self.__input_line.setEnabled(True)
            self.__input_line.update()
            self.__input_line.setFocus()
            self.__comport_dropdown.setEnabled(False)
            self.__comport_dropdown.update()
            self.__baud_dropdown.setEnabled(False)
            self.__baud_dropdown.update()
            if (
                (self.__serial_wizard is not None)
                and (not qt.sip.isdeleted(self.__serial_wizard))
                and self.__serial_wizard.isVisible()
            ):
                self.__serial_wizard.set_port_status(True)
        return

    @qt.pyqtSlot(str)
    def send_input_from_lineedit(self, content: str) -> None:
        """Send the input typed on the lineedit.

        This method should be invoked on an Enter press.
        """
        newline = None
        newline_name = self.__newline_dropdown.get_selected_item_name()
        if newline_name == "\\n":
            newline = "\n"
        elif newline_name == "\\r":
            newline = "\r"
        elif newline_name == "\\r\\n":
            newline = "\r\n"
        elif newline_name == "<nothing>":
            newline = ""
        else:
            assert False
        content += newline
        mode_str = self.__mode_dropdown.get_selected_item_name().strip()
        if mode_str == "ascii":
            self.__console_widget.send_text(
                text=content,
                echo=True,
                show_newlines_in_echo=self.__advanced_settings["show_newlines"],
            )
        else:
            self.__console_widget.send_hex(
                hex_as_string=content,
                echo=True,
            )
        return

    def rescale_later(
        self, callback: Optional[Callable], callbackArg: Any
    ) -> None:
        """"""
        assert threading.current_thread() is threading.main_thread()

        def rescale_scrollbars(*args):
            self.__console_widget.verticalScrollBar().setStyleSheet(
                _sb_.get_vertical()
            )
            self.__console_widget.horizontalScrollBar().setStyleSheet(
                _sb_.get_horizontal()
            )
            self.__console_widget.verticalScrollBar().setContextMenuPolicy(
                qt.Qt.ContextMenuPolicy.NoContextMenu
            )
            self.__console_widget.horizontalScrollBar().setContextMenuPolicy(
                qt.Qt.ContextMenuPolicy.NoContextMenu
            )
            qt.QTimer.singleShot(20, finish)
            return

        def finish(*args):
            if callback is not None:
                callback(callbackArg)
            return

        self.init_widgets()
        self.__console_widget.set_style()
        qt.QTimer.singleShot(20, rescale_scrollbars)
        return

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        # $ Avoid multiple self destructs
        if not death_already_checked:
            if self.__dead:
                raise RuntimeError(f"Trying to kill SerialConsole() twice!")
            self.__dead = True

        # $ Close the connection if needed
        if self.is_serial_port_open():
            self.toggle_serial_connection()
        data.serial_console = None

        # & Kill dropdown widgets
        if self.__comport_dropdown is not None:
            self.__comport_dropdown.self_destruct()
        if self.__baud_dropdown is not None:
            self.__baud_dropdown.self_destruct()
        if self.__mode_dropdown is not None:
            self.__mode_dropdown.self_destruct()
        if self.__newline_dropdown is not None:
            self.__newline_dropdown.self_destruct()
        self.__comport_dropdown = None
        self.__baud_dropdown = None
        self.__mode_dropdown = None
        self.__newline_dropdown = None

        # & Unlink all variables
        self.__output_settings_hlyt = None
        self.__connect_btn = None
        self.__comport_lyt = None
        self.__sep_line = None
        self.__comport_btn = None
        self.__baud_lbl = None
        self.__mode_lbl = None
        self.__advanced_lbl = None
        self.__advanced_btn = None
        self.__serial_wizard = None
        self.__console_widget = None
        self.__input_line = None
        self.__input_settings_hlyt = None
        self.__newline_lbl = None
        self.__newline_dropdown_prev_selection = None

        # & Clean layout and finish

        def finish(*args) -> None:
            self.__lyt = None
            if callback is not None:
                callback(callbackArg)
            return

        functions.clean_layout((self.__lyt, finish, None))
        return


# ^                                      SERIAL INPUT WIDGET                                       ^#
# % ============================================================================================== %#
# % SerialInputWidget()                                                                            %#
# %                                                                                                %#


class SerialInputWidget(qt.QTextEdit):
    """The SerialInputWidget() is shown *below* the ConsoleWidget() and is
    intended for receiving user text."""

    return_pressed_sig = qt.pyqtSignal(str)

    def __init__(self, parent: qt.QWidget) -> None:
        """"""
        super().__init__(parent)
        self.set_style()
        self.setReadOnly(False)
        self.setMouseTracking(True)
        self.__highlighter = Highlighter(self)
        self.__mode = None
        # Attention: this hex regex is duplicated below.
        self.__nonhex_regex = re.compile(r"[^\dabcdefABCDEF\s]")
        self.setFixedHeight(data.get_general_font_height() + 12)
        self.setVerticalScrollBarPolicy(
            qt.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setHorizontalScrollBarPolicy(
            qt.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        return

    def self_destruct(self, *args) -> None:
        """"""
        return

    def set_mode(self, mode: str) -> None:
        """"""
        self.__mode = mode
        self.__highlighter.set_mode(mode)
        self.__highlighter.rehighlight()
        return

    def setEnabled(self, en: bool) -> None:
        """Enable this input widget."""
        super().setEnabled(en)
        if en:
            self.clear()
            self.__highlighter.enable(True)
        else:
            self.clear()
            self.__highlighter.enable(False)
            self.insertPlainText("<input here>")
        self.set_style()
        return

    def return_pressed(self) -> None:
        """User pressed enter key.

        Clear the input line and return its content in a signal.
        NOTE:
        The content is stripped from '\n' and '\r'.
        """
        content = self.toPlainText()
        content = content.strip("\n")
        content = content.strip("\r")
        if self.__mode == "hex":
            m = self.__nonhex_regex.search(content)
            if m is not None:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    title_text="Serial Port Open",
                    icon_path="icons/dialog/stop.png",
                    text=str(
                        f"The input you provided is invalid. In hex-mode, you can<br>"
                        f"only enter whitespaces and these characters:<br>"
                        f'&nbsp;&nbsp;<span style="color:#4e9a06">0-9</span><br>'
                        f'&nbsp;&nbsp;<span style="color:#4e9a06">a-f</span><br>'
                        f'&nbsp;&nbsp;<span style="color:#4e9a06">A-F</span><br>'
                        f"<br>"
                        f"Also, the hex digits must be grouped in even numbers.<br>"
                        f"This is valid:<br>"
                        f'&nbsp;&nbsp;<span style="color:#4e9a06">a01b bc3f 3e90</span><br>'
                        f"This is not valid:<br>"
                        f'&nbsp;&nbsp;<span style="color:#cc0000">a01b bc3f 3e9</span><br>'
                        f'{"&nbsp;"*15}^<br>'
                    ),
                )
                return
            try:
                bytes.fromhex(content)
            except ValueError:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    title_text="Serial Port Open",
                    icon_path="icons/dialog/stop.png",
                    text=str(
                        f"The hex digits must be grouped in even numbers.<br>"
                        f"This is valid:<br>"
                        f'&nbsp;&nbsp;<span style="color:#4e9a06">a01b bc3f 3e90</span><br>'
                        f"This is not valid:<br>"
                        f'&nbsp;&nbsp;<span style="color:#4e9a06">a01b bc3f</span> '
                        f'<span style="color:#cc0000">3e9</span><br>'
                        f'{"&nbsp;"*14}<span style="color:#cc0000">^</span><br>'
                    ),
                )
                return
        self.clear()
        self.return_pressed_sig.emit(content)
        return

    def set_style(self) -> None:
        """Apply the stylesheet for this ConsoleWidget()-instance.

        This also sets the font size.
        """
        background_color = "#000000"
        text_color = "#ffffff"
        if not self.isEnabled():
            background_color = "#babdb6"
            text_color = "#eeeeec"
        self.setStyleSheet(
            f"""
        QTextEdit {{
            color         : {text_color};
            background    : {background_color};
            border-width  : 1px;
            border-color  : #2e3436;
            border-style  : solid;
            padding       : 0px;
            margin        : 0px;
            font-family   : {data.get_global_font_family()};
            font-size     : {data.get_general_font_pointsize()}pt;
        }}
        """
        )
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        return

    @qt.pyqtSlot(qt.QKeyEvent)
    def keyPressEvent(self, event: qt.QKeyEvent) -> None:
        """Catch an Enter press."""
        if (event.key() == qt.Qt.Key.Key_Return) or (
            event.key() == qt.Qt.Key.Key_Enter
        ):
            self.return_pressed()
            return
        super().keyPressEvent(event)
        return


# ^                                          HIGHLIGHTER                                           ^#
# % ============================================================================================== %#
# % Highlighter()                                                                                  %#
# %                                                                                                %#


class Highlighter(qt.QSyntaxHighlighter):

    def __init__(self, parent: qt.QWidget) -> None:
        """"""
        qt.QSyntaxHighlighter.__init__(self, parent)
        self.__mode = None
        self.__enabled = False
        self.parent = parent
        # A regex to catch all escape sequences.
        # Attention: this escape sequence regex is duplicated
        # at 'console_widget.py'
        self.__escape_sequence_regex = re.compile(
            r"(\\(x[0-9a-fA-F][0-9a-fA-F]|[\\abfnrtv]))+"
        )
        # A regex to catch all invalid characters
        # when in hex mode.
        # Attention: this hex regex is duplicated above.
        self.__nonhex_regex = re.compile(r"[^\dabcdefABCDEF\s]")
        self.__format_yellow = qt.QTextCharFormat()
        self.__format_yellow.setForeground(
            qt.QBrush(
                qt.QColor(252, 233, 79),
                qt.Qt.BrushStyle.SolidPattern,
            )
        )
        self.__format_red = qt.QTextCharFormat()
        self.__format_red.setForeground(
            qt.QBrush(
                qt.QColor(239, 41, 41),
                qt.Qt.BrushStyle.SolidPattern,
            )
        )
        return

    def set_mode(self, mode: str) -> None:
        """"""
        self.__mode = mode
        return

    def enable(self, en: bool) -> None:
        """"""
        self.__enabled = en

    def highlightBlock(self, text: str) -> None:
        """"""
        if self.__mode is None:
            return
        if not self.__enabled:
            return

        # & Select regex and format
        if self.__mode == "ascii":
            p = self.__escape_sequence_regex
            f = self.__format_yellow
        elif self.__mode == "hex":
            p = self.__nonhex_regex
            f = self.__format_red
        else:
            raise RuntimeError()

        # & Perform formatting
        for m in p.finditer(text):
            i1, i2 = m.span()
            self.setFormat(
                i1,
                i2 - i1,
                f,
            )
        self.setCurrentBlockState(0)
        return
