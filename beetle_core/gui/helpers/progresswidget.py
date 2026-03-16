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
import threading
import qt
import data
import gui
import purefunctions
import gui.stylesheets.groupbox as _stylesheet_groupbox_
import components.decorators as _dec_

if TYPE_CHECKING:
    import gui.templates
    import gui.templates.widgetgenerator
    import gui.templates.baseprogressbar
    import gui.forms.mainwindow as _mainwindow_
from various.kristofstuff import *


class ProgressWidget(qt.QGroupBox):
    signal_show = qt.pyqtSignal()
    signal_hide = qt.pyqtSignal()
    signal_apply = qt.pyqtSignal()

    def __init__(
        self,
        parent: qt.QStatusBar,
        main_form: _mainwindow_.MainWindow,
    ) -> None:
        """

        :param parent:      The QStatusBar() this ProgressWidget() lives in.
        :param main_form:   The MainWindow()-instance.
        """
        super().__init__(parent)
        assert threading.current_thread() is threading.main_thread()
        self.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.Ignored,
                qt.QSizePolicy.Policy.Preferred,
            )
        )

        # * Variables
        self.__debug: bool = False
        self.__main_form: _mainwindow_.MainWindow = main_form
        self.__keeper_cache: Optional[Dict[str, ProgressKeeper]] = {}

        # * Progressbar
        self.__progress_bar: Optional[
            gui.templates.baseprogressbar.BaseProgressBar
        ] = gui.templates.baseprogressbar.BaseProgressBar(
            color="green",
            parent=self,
            thin=True,
        )
        self.__progress_bar.setFont(data.get_general_font())
        self.__progress_bar.setAlignment(
            qt.Qt.AlignmentFlag.AlignCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )

        # * Layout
        layout: qt.QHBoxLayout = cast(
            qt.QHBoxLayout,
            gui.templates.widgetgenerator.create_layout(),
        )
        self.setLayout(layout)
        layout.addWidget(
            gui.templates.widgetgenerator.create_spacer(fixed_width=10)
        )
        layout.addWidget(self.__progress_bar)
        layout.addWidget(
            gui.templates.widgetgenerator.create_spacer(fixed_width=10)
        )

        # Update style
        self.update_style()

        # * Signals
        self.signal_show.connect(self.show)
        self.signal_hide.connect(self.hide)
        self.signal_apply.connect(self.__apply_all)

        self.echo("Initialization complete")
        return

    def show(self, *args) -> None:
        """"""
        self.echo("Show")
        if threading.current_thread() is threading.main_thread():
            super().show()
            return
        self.signal_show.emit()
        return

    def hide(self, *args) -> None:
        """"""
        self.echo("Hide")
        if threading.current_thread() is threading.main_thread():
            super().hide()
            return
        self.signal_hide.emit()
        return

    def echo(self, *messages) -> None:
        """"""
        if self.__debug:
            class_name = self.__class__.__name__
            print(f"[{class_name}]", *messages)
        return

    #! ========================================================================== !#
    #!                                 PUBLIC API                                 !#
    #! ========================================================================== !#
    @_dec_.sip_check_method
    def add(
        self,
        name: str,
        priority: int,
        text: str,
        minimum: int,
        maximum: int,
        value: int,
    ) -> None:
        """"""
        if not (name in self.__keeper_cache.keys()):
            self.echo(f"Added progress keeper: {q}{name}{q}")
        self.echo("add:", name, priority, text, minimum, maximum, value)
        self.__keeper_cache[name] = ProgressKeeper(
            name=name,
            priority=priority,
            text=text,
            minimum=minimum,
            maximum=maximum,
            value=value,
        )
        self.signal_apply.emit()
        return

    @_dec_.sip_check_method
    def remove(self, name: str) -> None:
        """"""
        self.echo("remove:", name)
        if name not in self.__keeper_cache.keys():
            return
        self.echo(f"Removed progress keeper: {q}{name}{q}")
        self.__keeper_cache.pop(name, None)
        self.signal_apply.emit()
        return

    def has(self, name: str) -> bool:
        """"""
        return name in self.__keeper_cache

    @_dec_.sip_check_method
    def set_text(
        self,
        name: str,
        text: str,
    ) -> None:
        """"""
        self.echo("set_text:", name, text)
        if name not in self.__keeper_cache:
            purefunctions.printc(
                f"WARNING: set_text() > {q}{name}{q} not "
                f"in self.__keeper_cache",
                color="warning",
            )
            return
        self.__keeper_cache[name].text = text
        self.signal_apply.emit()
        return

    @_dec_.sip_check_method
    def set_minimum(
        self,
        name: str,
        value: int,
    ) -> None:
        """"""
        self.echo("set_minimum:", name, value)
        if name not in self.__keeper_cache:
            purefunctions.printc(
                f"WARNING: set_minimum() > {q}{name}{q} not "
                f"in self.__keeper_cache",
                color="warning",
            )
            return
        self.__keeper_cache[name].minimum = value
        self.signal_apply.emit()
        return

    @_dec_.sip_check_method
    def set_maximum(
        self,
        name: str,
        value: int,
    ) -> None:
        """"""
        self.echo("set_maximum:", name, value)
        if name not in self.__keeper_cache:
            purefunctions.printc(
                f"WARNING: set_maximum() > {q}{name}{q} not "
                f"in self.__keeper_cache",
                color="warning",
            )
            return
        self.__keeper_cache[name].maximum = value
        self.signal_apply.emit()
        return

    @_dec_.sip_check_method
    def get_maximum(
        self,
        name: str,
    ) -> None:
        """"""
        return self.__keeper_cache[name].maximum

    @_dec_.sip_check_method
    def increment_maximum(self, name: str, value: int = 1) -> None:
        """"""
        self.__keeper_cache[name].maximum += value

    @_dec_.sip_check_method
    def set_value(
        self,
        name: str,
        value: int,
    ) -> None:
        """"""
        self.echo("set_value:", name, value)
        if name not in self.__keeper_cache:
            purefunctions.printc(
                f"WARNING: set_value() > {q}{name}{q} not "
                f"in self.__keeper_cache",
                color="warning",
            )
            return
        self.__keeper_cache[name].value = value
        self.signal_apply.emit()
        return

    @_dec_.sip_check_method
    def get_value(
        self,
        name: str,
    ) -> None:
        """"""
        return self.__keeper_cache[name].value

    @_dec_.sip_check_method
    def set_value_and_max(
        self,
        name: str,
        value: int,
        maximum: int,
    ) -> None:
        """"""
        self.echo("set_value_and_max:", name, value, maximum)
        if name not in self.__keeper_cache:
            purefunctions.printc(
                f"WARNING: set_value() > {q}{name}{q} not "
                f"in self.__keeper_cache",
                color="warning",
            )
            return
        self.__keeper_cache[name].value = value
        self.__keeper_cache[name].maximum = maximum
        self.signal_apply.emit()
        return

    @_dec_.sip_check_method
    def set_step(
        self,
        name: str,
        value: int,
    ) -> None:
        """"""
        self.echo("set_step:", name, value)
        if name not in self.__keeper_cache:
            purefunctions.printc(
                f"WARNING: set_step() > {q}{name}{q} not "
                f"in self.__keeper_cache",
                color="warning",
            )
            return
        self.__keeper_cache[name].step = value
        self.signal_apply.emit()
        return

    @_dec_.sip_check_method
    def increment(
        self,
        name: str,
        value: Optional[int] = None,
    ) -> None:
        """"""
        self.echo("increment:", name, value)
        if name not in self.__keeper_cache:
            purefunctions.printc(
                f"WARNING: increment() > {q}{name}{q} not "
                f"in self.__keeper_cache",
                color="warning",
            )
            return
        step = self.__keeper_cache[name].step
        if value is not None:
            step = value
        self.__keeper_cache[name].value += step
        if self.__keeper_cache[name].value > self.__keeper_cache[name].maximum:
            purefunctions.printc(
                f"ERROR: progress_widget for {q}{name}{q} has value "
                f"higher than max: {self.__keeper_cache[name].value}/"
                f"{self.__keeper_cache[name].maximum}",
                color="error",
            )
        self.signal_apply.emit()
        return

    @_dec_.sip_check_method
    def decrement(
        self,
        name: str,
        value: Optional[int] = None,
    ) -> None:
        """"""
        self.echo("decrement:", name, value)
        if name not in self.__keeper_cache:
            purefunctions.printc(
                f"WARNING: decrement() > {q}{name}{q} not "
                f"in self.__keeper_cache",
                color="warning",
            )
            return
        step = self.__keeper_cache[name].step
        if value is not None:
            step = value
        self.__keeper_cache[name].value -= step
        self.signal_apply.emit()
        return

    @_dec_.sip_check_method
    def is_complete(
        self,
        name: str,
    ) -> None:
        """"""
        return (
            self.__keeper_cache[name].value >= self.__keeper_cache[name].maximum
        )

    #! ========================================================================== !#
    #!                                SIGNAL SLOT                                 !#
    #! ========================================================================== !#
    @qt.pyqtSlot()
    def __apply_all(self, *args) -> None:
        """"""
        self.echo("__apply_all:", *args)
        assert threading.current_thread() is threading.main_thread()
        if qt.sip.isdeleted(self):
            return
        priorities = [v.priority for k, v in self.__keeper_cache.items()]
        if len(priorities) > 0:
            if not self.isVisible():
                self.show()

            # This next code block needs to be called with a timer,
            # as the above line 'self.show()' needs time to repaint correctly.
            def update(*args):
                top_priority = max(priorities)
                for k, v in self.__keeper_cache.items():
                    if v.priority == top_priority:
                        self.__progress_bar.setFormat(v.text)
                        self.__progress_bar.setTextVisible(True)
                        self.__progress_bar.setMinimum(v.minimum)
                        self.__progress_bar.setMaximum(v.maximum)
                        self.__progress_bar.setValue(v.value)
                        break

            qt.QTimer.singleShot(0, update)
        else:
            # Nothing to show!
            if self.isVisible():
                self.hide()
        return

    #! ========================================================================== !#
    #!                                    MISC                                    !#
    #! ========================================================================== !#

    def update_style(self) -> None:
        """"""
        self.echo("update_style")
        assert threading.current_thread() is threading.main_thread()
        if qt.sip.isdeleted(self):
            return
        self.__progress_bar.setFont(data.get_general_font())
        self.setStyleSheet(
            _stylesheet_groupbox_.get_noborder_style(
                background_color="transparent",
                additional_properties=("max-width: 400px;"),
            )
        )
        return


class ProgressKeeper:
    name: Optional[str] = None
    priority: Optional[int] = None
    text: Optional[str] = None
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    value: Optional[int] = None
    step: Optional[int] = None

    def __init__(
        self,
        name: str,
        priority: int,
        text: str,
        minimum: int,
        maximum: int,
        value: int,
    ) -> None:
        """"""
        self.name: Optional[str] = name
        self.priority: Optional[int] = priority
        self.text: Optional[str] = text
        self.minimum: Optional[int] = minimum
        self.maximum: Optional[int] = maximum
        self.value: Optional[int] = value
        self.step: Optional[int] = 1
        return
