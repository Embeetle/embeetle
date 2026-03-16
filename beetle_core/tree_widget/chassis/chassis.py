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
import threading, traceback
import qt, purefunctions, iconfunctions
import gui.templates.baseobject as _baseobject_
import gui.stylesheets.tree_chassis as _chassis_style_
import gui.stylesheets.scrollbar as _scrollbar_style_
import tree_widget.items.item as _cm_
import components.decorators as _dec_

if TYPE_CHECKING:
    import tree_widget.chassis.chassis_body as _chassis_body_
    import home_toolbox.chassis.home_toolbox as _toolmanager_
    import dashboard.chassis.dashboard_head as _dashboard_head_
    import home_libraries.chassis.home_libraries as _chassis_home_libraries_
    import sa_tab.chassis.sa_tab as _chassis_sa_tab_


class Chassis(qt.QFrame, _baseobject_.BaseObject):
    show_tab_savebutton_sig = qt.pyqtSignal()
    hide_tab_savebutton_sig = qt.pyqtSignal()
    enable_tab_optionundo_signal = qt.pyqtSignal(bool)

    def __init__(
        self,
        mainwindow,
        basicwidget,
        name: str,
        iconpath: str,
        head: Optional[qt.QFrame],
        body: Optional[_chassis_body_.ChassisBody],
    ) -> None:
        """┌── self.__lyt ───────────────────────────────────────────┐ │  ┌
        ChassisHead() (QFrame) ───────────────────────────┐  │ │  │ │  │ │
        └───────────────────────────────────────────────────┘  │ │ ┌────
        QScrollArea() ────────────────────────────────┐  │ │  │ ┌────── QFrame()
        ('main frame') ────────────────┐ │  │ │  │ │┌───────── ChassisBody()
        (QFrame) ────────────┐│ │  │ │  │ ││ ││ │  │ │  │ ││
        ││ │  │ │  │ ││                                             ││ │  │ │  │
        │└─────────────────────────────────────────────┘│ │  │ │  │ │ <stretch>
        │ │  │ │  │ └───────────────────────────────────────────────┘ │  │ │
        └───────────────────────────────────────────────────┘  │ │ │
        └─────────────────────────────────────────────────────────┘

        NOTE:
        ChassisHead() and QScrollArea() are encapsulated together inside an anonymous QFrame(), with
        an anonymous QVBoxLayout(), which is then passed to the vertical tabwidget as the 'page'.

        :param mainwindow:  MainWindow().
        :param basicwidget: The basic widget (upper, lower or main).
        :param name:        Name for this Chassis()-widget, to be displayed in its tab.
        :param iconpath:    Relative path to the icon, to be displayed in the tab.
        """
        assert threading.current_thread() is threading.main_thread()
        qt.QFrame.__init__(self)
        _baseobject_.BaseObject.__init__(
            self,
            parent=basicwidget,
            main_form=mainwindow,
            name=name,
            icon=iconfunctions.get_qicon(iconpath),
        )
        self.__mainwindow = mainwindow
        self.__basicwidget = basicwidget
        self.setContentsMargins(0, 0, 0, 0)

        # * ==========[ OVERALL STRUCTURE ]========== *#
        self.__lyt = qt.QVBoxLayout()
        self.__lyt.setSpacing(0)
        self.__lyt.setContentsMargins(0, 0, 0, 0)
        self.__lyt.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.__lyt)
        self.__lyt_struct = {}

        # * ==========[ INIT SELF ]========== *#
        # Note:
        # these signals are also connected to functions in 'mainwindow.py'!
        self.update_style()
        if body:
            self.set_page(
                head=head,
                body=body,
            )
        return

    def contextmenu_requested(self, *args) -> None:
        """User right-clicked somewhere in the 'scroll_mainfrm' which
        encapsulates the body."""
        # Invoke the same method that runs when the user right-clicks in the tab
        # header from this Chassis().
        self.leftclick_tab_settingsbtn()
        return

    def get_current_tabname(self) -> str:
        """Get the name of the currently visible tab.

        Return 'default' if there are none.
        """
        return "default"

    def set_page(
        self,
        head: Optional[qt.QFrame],
        body: Union[_chassis_body_.ChassisBody, qt.QFrame],
        add_stretch: bool = True,
    ) -> None:
        """
        :param head:    Any qt.QFrame() is good
        :param body:    Must be a (subclassed) ChassisBody()
        """
        # This method should only be invoked once!
        assert len(list(self.__lyt_struct.keys())) == 0
        self.__lyt_struct = {
            "chassis_head": head,
            "chassis_body": body,
            "scroll_area": qt.QScrollArea(),
            "scroll_mainfrm": qt.QFrame(),
            "scroll_mainlyt": qt.QVBoxLayout(),
            "has_unsaved_changes": False,
        }

        # * SCROLL MAIN FRAME
        # The 'scroll_mainfrm' has layout 'scroll_mainlyt' and envelopes the
        # body.
        self.__lyt_struct["scroll_mainfrm"].setLayout(
            self.__lyt_struct["scroll_mainlyt"]
        )
        self.__lyt_struct["scroll_mainlyt"].addWidget(body)
        self.__lyt_struct["scroll_mainfrm"].setStyleSheet(
            _chassis_style_.get_transparent()
        )
        self.__lyt_struct["scroll_mainfrm"].setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.CustomContextMenu,
        )
        self.__lyt_struct["scroll_mainfrm"].customContextMenuRequested.connect(
            self.contextmenu_requested,
        )
        self.__lyt_struct["scroll_mainlyt"].setSpacing(0)
        self.__lyt_struct["scroll_mainlyt"].setContentsMargins(0, 0, 0, 0)
        self.__lyt_struct["scroll_mainlyt"].setAlignment(
            qt.Qt.AlignmentFlag.AlignTop
        )
        if add_stretch:
            self.__lyt_struct["scroll_mainlyt"].addStretch()

        # * SCROLL AREA
        # Envelopes the main frame
        self.__lyt_struct["scroll_area"].setWidget(
            self.__lyt_struct["scroll_mainfrm"]
        )
        self.__lyt_struct["scroll_area"].setWidgetResizable(True)
        self.__lyt_struct["scroll_area"].setVerticalScrollBarPolicy(
            qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.__lyt_struct["scroll_area"].setHorizontalScrollBarPolicy(
            qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.__lyt_struct["scroll_area"].setStyleSheet(
            _chassis_style_.get_transparent()
        )
        self.__lyt_struct["scroll_area"].verticalScrollBar().setStyleSheet(
            _scrollbar_style_.get_vertical()
        )
        self.__lyt_struct["scroll_area"].horizontalScrollBar().setStyleSheet(
            _scrollbar_style_.get_horizontal()
        )
        self.__lyt_struct[
            "scroll_area"
        ].verticalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.__lyt_struct[
            "scroll_area"
        ].horizontalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )

        # Add the new scroll area directly to the layout because there are no vertical tabs.
        # $ With head
        if head:
            self.__lyt.addWidget(head)
            self.__lyt.addWidget(self.__lyt_struct["scroll_area"])
        # $ Without head
        else:
            self.__lyt.addWidget(self.__lyt_struct["scroll_area"])
        return

    def has_unsaved_changes(self) -> bool:
        """"""
        return self.__lyt_struct["has_unsaved_changes"]

    def set_unsaved_changes(self) -> None:
        """
        ATTENTION: This method is no longer connected to 'self.show_tab_savebutton_sig'
        """
        self.__lyt_struct["has_unsaved_changes"] = True
        return

    def clear_unsaved_changes(self) -> None:
        """
        ATTENTION: This method is no longer connected to 'self.hide_tab_savebutton_sig'
        """
        self.__lyt_struct["has_unsaved_changes"] = False
        return

    def add_root(self, rootdir) -> None:
        """"""
        self.__lyt_struct["chassis_body"].body_add_root(rootdir)
        return

    def get_chassis_head(
        self,
    ) -> Union[qt.QFrame, _dashboard_head_.DashboardHead]:
        """"""
        return self.__lyt_struct["chassis_head"]

    def get_chassis_body(self) -> Union[
        _chassis_body_.ChassisBody,
        _toolmanager_.ToolboxBody,
        _chassis_home_libraries_.LibManagerBody,
        _chassis_sa_tab_.SATabBody,
    ]:
        """Get the chassis body.

        NOTE: The Root() item instance has a similar method to access the
        chassis body.
        """
        return self.__lyt_struct["chassis_body"]

    def get_rightclick_menu_function(self) -> Callable:
        """Return a list to initialize the tab buttons.

        Each element of this list is a tuple that initializes ONE tab button.
        """
        return self.leftclick_tab_settingsbtn

    def leftclick_tab_settingsbtn(self, *args) -> None:
        """The user right-clicked on the tab header from this Chassis()."""
        print("SHOW CONTEXTMENU FOR TAB HEAD FROM THE CHASSIS()")
        return

    def contextmenuclick_tab_settingsbtn(self, key: str) -> None:
        """React on a click in the tab-contextmenu.

        Should be implemented in the subclass.
        """
        raise NotImplementedError()
        return

    def leftclick_tab_savebtn(self) -> None:
        """The user clicked the save button in the tab header."""
        raise NotImplementedError()
        return

    def mousePressEvent(self, event: qt.QMouseEvent) -> None:
        """"""
        event.accept()
        return

    def go_to_item(
        self,
        abspath: str,
        callback1: Optional[Callable],
        callbackArg1: Any,
        callback2: Optional[Callable],
        callbackArg2: Any,
    ) -> None:
        """"""
        body: _chassis_body_.ChassisBody = self.__lyt_struct["chassis_body"]
        body.body_go_to_item(
            abspath=abspath,
            callback1=callback1,
            callbackArg1=callbackArg1,
            callback2=callback2,
            callbackArg2=callbackArg2,
        )
        return

    def find_item(
        self,
        abspath: Optional[str],
        check: bool,
        update_libraries: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        body: _chassis_body_.ChassisBody = self.__lyt_struct["chassis_body"]
        body.body_find_item(
            abspath=abspath,
            check=check,
            update_libraries=update_libraries,
            callback=callback,
            callbackArg=callbackArg,
        )
        return

    def ensure_item_visible(self, item: _cm_.Item) -> None:
        """Ensure the given widget to be visible in the given tab."""
        try:
            self.__lyt_struct["scroll_area"].ensureWidgetVisible(
                item.get_widget("itemBtn")
            )
        except:
            try:
                self.__lyt_struct["scroll_area"].ensureWidgetVisible(item)
            except:
                purefunctions.printc(
                    f"\nERROR: Cannot make item visible: {item}\n",
                    color="error",
                )
                traceback.print_exc()
        return

    def chassis_rescale_or_refresh_recursive(
        self,
        action: str,
        force_stylesheet: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        :param action:  Choose between 'rescale' and 'refresh':
                            'rescale': resize all widgets
                            'refresh': refresh widget colors (theme change)
        """

        def apply_body_recursive(*args) -> None:
            body: Union[_chassis_body_.ChassisBody] = self.__lyt_struct[
                "chassis_body"
            ]
            body.body_rescale_or_refresh_recursive(
                action=action,
                force_stylesheet=force_stylesheet,
                callback=apply_scrollbars,
                callbackArg=None,
            )
            return

        def apply_scrollbars(*args) -> None:
            v_scrollbar: qt.QScrollBar = self.__lyt_struct[
                "scroll_area"
            ].verticalScrollBar()
            h_scrollbar: qt.QScrollBar = self.__lyt_struct[
                "scroll_area"
            ].horizontalScrollBar()
            v_scrollbar.setStyleSheet(_scrollbar_style_.get_vertical())
            h_scrollbar.setStyleSheet(_scrollbar_style_.get_horizontal())
            v_scrollbar.setContextMenuPolicy(
                qt.Qt.ContextMenuPolicy.NoContextMenu
            )
            h_scrollbar.setContextMenuPolicy(
                qt.Qt.ContextMenuPolicy.NoContextMenu
            )
            v_scrollbar.style().unpolish(v_scrollbar)
            v_scrollbar.style().polish(v_scrollbar)
            v_scrollbar.update()
            h_scrollbar.style().unpolish(v_scrollbar)
            h_scrollbar.style().polish(v_scrollbar)
            h_scrollbar.update()
            qt.QTimer.singleShot(20, finish)
            return

        def finish(*args) -> None:
            if callback is not None:
                callback(callbackArg)
            return

        head: Optional[_dashboard_head_.DashboardHead] = self.__lyt_struct[
            "chassis_head"
        ]
        if head is None:
            apply_body_recursive()
            return
        head.head_rescale_recursive(
            callback=apply_body_recursive,
            callbackArg=None,
        )
        return

    @qt.pyqtSlot(object)
    def receive(self, message) -> None:
        """Slot for receiving messages throught the window communication system.

        This slot will receive ALL messages, manual filtering of the sender is
        needed!
        """
        # Overload to use
        sender, _data = message
        print("Dashboard got message:", _data)
        return

    @_dec_.sip_check_method
    def show_home_window_tools(self):
        """Move home window to the foreground and focus the 'Tools' tab."""
        self.show_home_window()
        self.send("switch-tabs tools")
        return

    def update_style(self):
        """"""
        self.setStyleSheet(_chassis_style_.get_default())
        return
