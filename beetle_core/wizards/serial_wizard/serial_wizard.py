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
import qt, data, purefunctions, functions, functools
import gui.helpers.buttons
import gui.dialogs.projectcreationdialogs as _gen_wizard_
import gui.helpers.advancedcombobox as _advancedcombobox_
import beetle_console.serial_port as _serial_port_

if TYPE_CHECKING:
    import gui.templates.paintedgroupbox as _paintedgroupbox_
    import beetle_console.serial_console as _serial_console_
from various.kristofstuff import *


class SerialWizard(_gen_wizard_.GeneralWizard):
    """┌── self.__settings_groupbox ──────────────────────────────────────────┐
    │┌──── vlyt ────────────────────────────────────────────────────────┐  │ ││
    ┌──── hlyt ────────────────────────────────────────────────────┐ │  │ ││ │
    self.__baud_lbl      self.__baud_dropdown                    │ │  │ ││
    └──────────────────────────────────────────────────────────────┘ │  │ ││
    ┌──── hlyt ────────────────────────────────────────────────────┐ │  │ ││ │
    self.__bytesize_lbl  self.__bytesize_dropdown                │ │  │ ││
    └──────────────────────────────────────────────────────────────┘ │  │ ││
    ┌──── hlyt ────────────────────────────────────────────────────┐ │  │ ││ │
    self.__parity_lbl    self.__parity_dropdown                  │ │  │ ││
    └──────────────────────────────────────────────────────────────┘ │  │ ││
    ┌──── hlyt ────────────────────────────────────────────────────┐ │  │ ││ │
    self.__stopbits_lbl  self.__stopbits_dropdown                │ │  │ ││
    └──────────────────────────────────────────────────────────────┘ │  │
    │└──────────────────────────────────────────────────────────────────┘  │
    └──────────────────────────────────────────────────────────────────────┘"""

    def __init__(
        self,
        parent: qt.QWidget,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Create SerialWizard(). The callback gets invoked after this instance
        has served its purpose and is already destroyed. > callback(result,
        callbackArg)

        The 'result' parameter is True if the user clicked 'APPLY', False
        otherwise.
        """
        if parent is None:
            parent = data.main_form
        super().__init__(parent)
        self.__apply_clicked: bool = False
        self.__callback: Optional[Callable] = None
        self.__callbackArg: Any = None
        self.setWindowTitle(f"Serial Monitor Settings")
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(5)
        self.main_layout.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.resize_and_center()
        size = data.get_general_icon_pixelsize()
        self.__port_open = False
        self.__serial_console_handle: Optional[
            _serial_console_.SerialConsole
        ] = None

        #! ================================[ SETTINGS GROUPBOX ]================================= !#
        self.__settings_groupbox: _paintedgroupbox_.PaintedGroupBox = (
            self.create_info_groupbox(
                parent=self,
                text="Serial Monitor Settings",
                vertical=True,
                info_func=lambda *args: print("info pressed"),
                spacing=5,
                margins=(5, 5, 5, 5),
                h_size_policy=qt.QSizePolicy.Policy.Expanding,
                v_size_policy=qt.QSizePolicy.Policy.Expanding,
            )
        )
        self.__settings_groupbox.layout().setAlignment(
            qt.Qt.AlignmentFlag.AlignTop
        )
        self.main_layout.addWidget(self.__settings_groupbox)

        # * --------------------[ Baudrate ]-------------------- *#
        # $ Layout
        self.__hlyt1 = qt.QHBoxLayout()
        self.__hlyt1.setSpacing(0)
        self.__hlyt1.setContentsMargins(0, 0, 0, 0)
        self.__hlyt1.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        self.__settings_groupbox.layout().addLayout(self.__hlyt1)

        # $ Label
        self.__baud_lbl = qt.QLabel(self)
        self.__baud_lbl.setStyleSheet(
            f"""
        QLabel {{
            color: {data.theme['fonts']['default']['color']};
            background: transparent;
            border: none;
        }}
        """
        )
        self.__baud_lbl.setText("Baudrate:  ")
        self.__baud_lbl.setFont(data.get_general_font())
        self.__hlyt1.addWidget(self.__baud_lbl)

        # $ Dropdown
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
                            "text": f" {baud} ",
                            "color": text_color,
                        },
                    ],
                }
            )
        self.__baud_dropdown.add_items(items)
        self.__hlyt1.addWidget(self.__baud_dropdown)

        # * ----------------------[ Mode ]---------------------- *#
        # $ Layout
        self.__hlyt2 = qt.QHBoxLayout()
        self.__hlyt2.setSpacing(0)
        self.__hlyt2.setContentsMargins(0, 0, 0, 0)
        self.__hlyt2.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        self.__settings_groupbox.layout().addLayout(self.__hlyt2)

        # $ Label
        self.__mode_lbl = qt.QLabel(self)
        self.__mode_lbl.setStyleSheet(
            f"""
            QLabel {{
                color: {data.theme['fonts']['default']['color']};
                background: transparent;
                border: none;
            }}
        """
        )
        self.__mode_lbl.setText("Mode:      ")
        self.__mode_lbl.setFont(data.get_general_font())
        self.__hlyt2.addWidget(self.__mode_lbl)

        # $ Dropdown
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
        self.__hlyt2.addWidget(self.__mode_dropdown)

        # * --------------------[ Bytesize ]-------------------- *#
        # $ Layout
        self.__hlyt3 = qt.QHBoxLayout()
        self.__hlyt3.setSpacing(0)
        self.__hlyt3.setContentsMargins(0, 0, 0, 0)
        self.__hlyt3.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        self.__settings_groupbox.layout().addLayout(self.__hlyt3)

        # $ Label
        self.__bytesize_lbl = qt.QLabel(self)
        self.__bytesize_lbl.setStyleSheet(
            f"""
            QLabel {{
                color: {data.theme['fonts']['default']['color']};
                background: transparent;
                border: none;
            }}
        """
        )
        self.__bytesize_lbl.setText("Bytesize:  ")
        self.__bytesize_lbl.setFont(data.get_general_font())
        self.__hlyt3.addWidget(self.__bytesize_lbl)

        # $ Dropdown
        self.__bytesize_dropdown = _advancedcombobox_.AdvancedComboBox(
            parent=self,
            image_size=size,
        )
        items = []
        text_color = "default"
        for bytesize in _serial_port_.SerialPort.BYTESIZES:
            items.append(
                {
                    "name": f"{bytesize}",
                    "widgets": [
                        {
                            "type": "text",
                            "text": f" {bytesize} ",
                            "color": text_color,
                        },
                    ],
                }
            )
        self.__bytesize_dropdown.add_items(items)
        self.__hlyt3.addWidget(self.__bytesize_dropdown)

        # * --------------------[ Parities ]-------------------- *#
        # $ Layout
        self.__hlyt4 = qt.QHBoxLayout()
        self.__hlyt4.setSpacing(0)
        self.__hlyt4.setContentsMargins(0, 0, 0, 0)
        self.__hlyt4.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        self.__settings_groupbox.layout().addLayout(self.__hlyt4)

        # $ Label
        self.__parity_lbl = qt.QLabel(self)
        self.__parity_lbl.setStyleSheet(
            f"""
            QLabel {{
                color: {data.theme['fonts']['default']['color']};
                background: transparent;
                border: none;
            }}
        """
        )
        self.__parity_lbl.setText("Parities:  ")
        self.__parity_lbl.setFont(data.get_general_font())
        self.__hlyt4.addWidget(self.__parity_lbl)

        # $ Dropdown
        self.__parity_dropdown = _advancedcombobox_.AdvancedComboBox(
            parent=self,
            image_size=size,
        )
        items = []
        text_color = "default"
        for parity, pname in zip(
            _serial_port_.SerialPort.PARITIES,
            _serial_port_.SerialPort.PARITY_NAMES,
        ):
            items.append(
                {
                    "name": f"{parity}",
                    "widgets": [
                        {
                            "type": "text",
                            "text": f" {parity} ({pname})",
                            "color": text_color,
                        },
                    ],
                }
            )
        self.__parity_dropdown.add_items(items)
        self.__hlyt4.addWidget(self.__parity_dropdown)

        # * --------------------[ Stopbits ]-------------------- *#
        # $ Layout
        self.__hlyt5 = qt.QHBoxLayout()
        self.__hlyt5.setSpacing(0)
        self.__hlyt5.setContentsMargins(0, 0, 0, 0)
        self.__hlyt5.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        self.__settings_groupbox.layout().addLayout(self.__hlyt5)

        # $ Label
        self.__stopbits_lbl = qt.QLabel(self)
        self.__stopbits_lbl.setStyleSheet(
            f"""
            QLabel {{
                color: {data.theme['fonts']['default']['color']};
                background: transparent;
                border: none;
            }}
        """
        )
        self.__stopbits_lbl.setText("Stop bits: ")
        self.__stopbits_lbl.setFont(data.get_general_font())
        self.__hlyt5.addWidget(self.__stopbits_lbl)

        # $ Dropdown
        self.__stopbits_dropdown = _advancedcombobox_.AdvancedComboBox(
            parent=self,
            image_size=size,
        )
        items = []
        text_color = "default"
        for stopbit in _serial_port_.SerialPort.STOPBITS:
            items.append(
                {
                    "name": f"{stopbit}",
                    "widgets": [
                        {
                            "type": "text",
                            "text": f" {stopbit} ",
                            "color": text_color,
                        },
                    ],
                }
            )
        self.__stopbits_dropdown.add_items(items)
        self.__hlyt5.addWidget(self.__stopbits_dropdown)

        #! ===============================[ LINE ENDINGS CHECKBOX ]===============================!#
        self.__line_endings_chbx = self.create_check_option(
            "Show line endings<br>(only relevant for ascii mode)",
        )
        self.__line_endings_chbx.setToolTip(
            f"Show line endings like {q}\\n{q} and {q}\\r\\n{q}"
        )
        self.__line_endings_chbx.check_box.stateChanged.connect(
            lambda: print("state changed")
        )
        self.main_layout.addWidget(self.__line_endings_chbx)
        self.main_layout.addStretch(10)

        #! ===============================[ CANCEL AND SAVE BTNS ]================================!#
        self.add_page_buttons()
        self.next_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self.resize_and_center()
        self.repurpose_cancel_next_buttons(
            cancel_name="CANCEL",
            cancel_func=self._cancel_clicked,
            cancel_en=True,
            next_name="SAVE",
            next_func=self._complete_wizard,
            next_en=True,
        )
        self.resize_and_center()
        return

    def show_wizard(
        self,
        port_open: bool,
        handle: _serial_console_.SerialConsole,
        baudrate: Union[int, str],
        mode: str,
        bytesize: Union[int, str],
        parity: str,
        stopbits: Union[int, float, str],
        show_newlines: bool,
    ) -> None:
        """Show this wizard and already set the baudrate."""
        self.__port_open = port_open
        self.__serial_console_handle = handle
        self.__baud_dropdown.set_selected_name(str(baudrate))
        self.__mode_dropdown.set_selected_name(str(mode))
        self.__bytesize_dropdown.set_selected_name(str(bytesize))
        self.__parity_dropdown.set_selected_name(str(parity))
        self.__stopbits_dropdown.set_selected_name(str(stopbits))
        chbx: gui.helpers.buttons.CheckBox = self.__line_endings_chbx.check_box
        # chbx.checkState() == qt.Qt.CheckState.Checked
        if show_newlines:
            chbx.setCheckState(qt.Qt.CheckState.Checked)
        else:
            chbx.setCheckState(qt.Qt.CheckState.Unchecked)
        self.set_port_status(port_open)
        self.show()
        return

    def set_port_status(self, port_open: bool) -> None:
        """Closing or opening the serial port has an impact on the accessibility
        of certain settings."""
        if port_open:
            self.__baud_dropdown.set_selected_name(
                self.__serial_console_handle.get_baud_selection()
            )
            self.__bytesize_dropdown.set_selected_name(
                str(
                    self.__serial_console_handle.get_advanced_setting(
                        "bytesize"
                    )
                )
            )
            self.__parity_dropdown.set_selected_name(
                str(self.__serial_console_handle.get_advanced_setting("parity"))
            )
            self.__stopbits_dropdown.set_selected_name(
                str(
                    self.__serial_console_handle.get_advanced_setting(
                        "stopbits"
                    )
                )
            )
        self.__baud_dropdown.setEnabled(not port_open)
        self.__bytesize_dropdown.setEnabled(not port_open)
        self.__parity_dropdown.setEnabled(not port_open)
        self.__stopbits_dropdown.setEnabled(not port_open)
        self.__baud_dropdown.update()
        self.__bytesize_dropdown.update()
        self.__parity_dropdown.update()
        self.__stopbits_dropdown.update()
        return

    def resize_and_center(self, *args) -> None:
        """"""
        self.resize(cast(qt.QSize, self.main_layout.sizeHint() * 1.1))  # type: ignore
        self.center_to_parent()
        # self.adjustSize()
        try:
            w, h = functions.get_screen_size()
        except:
            s = functions.get_screen_size()
            w = s.width()
            h = s.height()
        self.resize(int(w * 0.5), int(h * 0.5))
        return

    # ^                                        COMPLETE WIZARD                                         ^#
    # % ============================================================================================== %#
    # % The user clicks 'APPLY', 'CANCEL' or 'X'.                                                      %#
    # %                                                                                                %#

    def _cancel_clicked(self, *args) -> None:
        """Click 'CANCEL'."""
        # Same effect as clicking 'X'
        self.reject()
        return

    def _complete_wizard(self, *args) -> None:
        """Click 'APPLY'."""
        if self.__apply_clicked or self.dead:
            return
        self.__apply_clicked = True
        callback = self.__callback
        callbackArg = self.__callbackArg

        def finish(*_args) -> None:
            if callback is not None:
                qt.QTimer.singleShot(
                    50,
                    functools.partial(
                        callback,
                        True,
                        callbackArg,
                    ),
                )
            return

        # * Start
        self.__apply_advanced_settings()

        # * Self-destruct
        self.self_destruct(
            callback=finish,
            callbackArg=None,
        )
        return

    def __apply_advanced_settings(self) -> None:
        """"""
        # $ Baudrate
        baudrate = "9600"
        try:
            baudrate = int(self.__baud_dropdown.get_selected_item_name())
        except Exception as e:
            purefunctions.printc(
                f"ERROR: Cannot handle baudrate "
                f"{self.__baud_dropdown.get_selected_item_name()}",
                color="error",
            )
            baudrate = "9600"

        # $ Mode
        mode = "ascii"
        try:
            mode = str(self.__mode_dropdown.get_selected_item_name())
        except Exception as e:
            purefunctions.printc(
                f"ERROR: Cannot handle mode "
                f"{self.__mode_dropdown.get_selected_item_name()}",
                color="error",
            )
            mode = "ascii"

        # $ Bytesize
        bytesize = 8
        try:
            bytesize = int(self.__bytesize_dropdown.get_selected_item_name())
        except Exception as e:
            purefunctions.printc(
                f"ERROR: Cannot handle bytesize "
                f"{self.__bytesize_dropdown.get_selected_item_name()}",
                color="error",
            )
            bytesize = 8

        # $ Parity
        parity = "N"
        try:
            parity = str(self.__parity_dropdown.get_selected_item_name())
        except Exception as e:
            purefunctions.printc(
                f"ERROR: Cannot handle parity "
                f"{self.__parity_dropdown.get_selected_item_name()}",
                color="error",
            )
            parity = "N"

        # $ Stopbits
        stopbits = 1
        try:
            stopbits = int(self.__stopbits_dropdown.get_selected_item_name())
        except Exception as e:
            try:
                stopbits = float(
                    self.__stopbits_dropdown.get_selected_item_name()
                )
            except Exception as e:
                purefunctions.printc(
                    f"ERROR: Cannot handle stop bits "
                    f"{self.__stopbits_dropdown.get_selected_item_name()}",
                    color="error",
                )
                stopbits = 1

        # $ Line endings
        show_newlines = True
        chbx: gui.helpers.buttons.CheckBox = self.__line_endings_chbx.check_box
        if chbx.checkState() == qt.Qt.CheckState.Checked:
            show_newlines = True
        else:
            show_newlines = False

        self.__serial_console_handle.apply_advanced_settings(
            baudrate=baudrate,
            mode=mode,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            show_newlines=show_newlines,
        )
        return

    def reject(self) -> None:
        """Click 'X'."""
        if self.dead or self.__apply_clicked:
            return

        callback = self.__callback
        callbackArg = self.__callbackArg

        def finish(*_args) -> None:
            # _gen_wizard_.GeneralWizard.reject(self) <= not sure if needed
            if callback is not None:
                qt.QTimer.singleShot(
                    50,
                    functools.partial(
                        callback,
                        False,
                        callbackArg,
                    ),
                )
            return

        self.self_destruct(
            callback=finish,
            callbackArg=None,
        )
        return

    def self_destruct(
        self,
        death_already_checked: bool = False,
        additional_clean_list: Optional[List[str]] = None,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Kill this SerialWizard()-instance.

        INVOCATIONS:
        ============
            > At the end of 'self._complete_wizard()', which runs when user clicks 'APPLY'.
            > At the end of 'self.reject()', which runs when the user clicks 'X' or 'CANCEL'.

        Both 'self._complete_wizard()' and 'self.reject()' store what's in 'self.__callback' and
        'self.__callbackArg' before invoking the self-destruct method, to be able to call the call-
        back afterwards.

        WARNING:
        ========
        Self destruction happens in this order: first hide(), then kill all widgets and finally
        close() this QDialog(). Invoking close() immediately, without first hiding, causes the
        reject() method to run, which I've overridden to invoke this 'self_destruct()' method! That
        would cause this method to run twice.
        """
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill SerialWizard() twice!")
            self.dead = True  # noqa

        # * Start
        # $ Hide
        self.hide()

        # $ Delete page buttons
        self.delete_page_buttons()

        # $ Destroy stuff
        # Will be done in the supercall function, where the self.main_layout is cleaned.

        def finish(*args) -> None:
            # $ Clear variables
            self.__callback = None
            self.__callbackArg = None
            self.__port_open = None
            self.__hlyt1 = None
            self.__hlyt2 = None
            self.__hlyt3 = None
            self.__hlyt4 = None
            self.__hlyt5 = None
            self.__serial_console_handle = None
            self.__settings_groupbox = None
            self.__baud_lbl = None
            self.__baud_dropdown = None
            self.__mode_lbl = None
            self.__mode_dropdown = None
            self.__bytesize_lbl = None
            self.__bytesize_dropdown = None
            self.__parity_lbl = None
            self.__parity_dropdown = None
            self.__stopbits_lbl = None
            self.__stopbits_dropdown = None
            self.__line_endings_chbx = None
            if callback is not None:
                callback(callbackArg)
            return

        # $ Supercall reject
        # _gen_wizard_.GeneralWizard.reject(self) <= not sure if needed

        # $ Close and destroy
        # 'self.close()' happens in the superclass method:
        _gen_wizard_.GeneralWizard.self_destruct(
            self,
            death_already_checked=True,
            additional_clean_list=None,
            callback=finish,
            callbackArg=None,
        )
        return
