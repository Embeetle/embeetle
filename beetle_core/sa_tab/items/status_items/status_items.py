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
import functools
import qt, data, functions
import helpdocs.help_texts as _ht_
import sa_tab.items.item as _sa_tab_items_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_arrow as _cm_arrow_
import tree_widget.widgets.item_lbl as _cm_lbl_
import tree_widget.widgets.item_lineedit as _cm_lineedit_
import tree_widget.widgets.item_img as _cm_item_img_
import dashboard.contextmenus.toplvl_contextmenu as _toplvl_contextmenu_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_
import components.sourceanalyzerinterface as _sai_


class StatusRootItem(_sa_tab_items_.Root):
    class Status(_sa_tab_items_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: StatusRootItem) -> None:
            """"""
            super().__init__(item=item)
            self.imgpath = "icons/dialog/help.png"
            self.closedIconpath = "icons/gen/stethoscope.png"
            self.openIconpath = "icons/gen/stethoscope.png"
            self.lblTxt = " status "
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            ATTENTION: Used to run only if self.get_item()._v_layout is not None, but now it runs
            always!
            """
            item = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
                    qt.QTimer.singleShot(
                        10,
                        functools.partial(
                            self.sync_state,
                            refreshlock,
                            callback,
                            callbackArg,
                        ),
                    )
                    return

            # * Sync self
            if self.has_asterisk():
                self.lblTxt = " *status"
            else:
                self.lblTxt = " status "
            project_status = (
                _sai_.SourceAnalysisCommunicator().get_project_status()
            )
            linker_status = (
                _sai_.SourceAnalysisCommunicator().get_linker_status()
            )
            launch_issues = (
                _sai_.SourceAnalysisCommunicator().get_sa_launch_issues()
            )
            internal_err = (
                _sai_.SourceAnalysisCommunicator().has_internal_error()
            )
            lineedit: _cm_lineedit_.ItemLineedit = item.get_widget(
                "itemLineedit"
            )

            # $ ERROR
            # For now we ignore the 'linker_status'.
            if (
                (project_status == 2)
                or (launch_issues is not None)
                or internal_err
            ):
                self.lineeditTxt = "error"
                if lineedit is not None:
                    lineedit.setProperty("green", False)
                    lineedit.setProperty("red", True)
                self.set_error(True)

            # $ BUSY
            elif (
                (project_status == 1)
                or (linker_status == 0)
                or (linker_status == 1)
            ):
                self.lineeditTxt = "busy"
                if lineedit is not None:
                    lineedit.setProperty("green", False)
                    lineedit.setProperty("red", False)
                self.set_error(False)

            # $ DONE
            else:
                self.lineeditTxt = "done"
                if lineedit is not None:
                    lineedit.setProperty("green", True)
                    lineedit.setProperty("red", False)
                self.set_error(False)
            self.lineeditReadOnly = True
            functions.assign_icon_err_warn_suffix(itemstatus=self)

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(self) -> None:
        """"""
        super().__init__(
            name="status",
            state=StatusRootItem.Status(item=self),
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def init_guiVars(self) -> None:
        """"""
        if self._v_layout is not None:
            return
        super().init_layout()
        arrow: Optional[_cm_arrow_.ItemArrow] = None
        if data.debug_mode:
            arrow = _cm_arrow_.ItemArrow(owner=self)
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemArrow=arrow,
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
            itemLineedit=_cm_lineedit_.ItemLineedit(owner=self),
            itemImg=_cm_item_img_.ItemImg(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        return

    def rightclick_itemBtn(
        self, event: Union[qt.QMouseEvent, qt.QEvent]
    ) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(
        self, event: Union[qt.QMouseEvent, qt.QEvent]
    ) -> None:
        """"""
        super().leftclick_itemLbl(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        return

    def rightclick_itemLbl(
        self, event: Union[qt.QMouseEvent, qt.QEvent]
    ) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLineedit(
        self, event: Union[qt.QMouseEvent, qt.QEvent]
    ) -> None:
        """"""
        super().leftclick_itemLineedit(event)
        return

    def rightclick_itemLineedit(
        self, event: Union[qt.QMouseEvent, qt.QEvent]
    ) -> None:
        """"""
        super().rightclick_itemLineedit(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemImg(
        self, event: Optional[Union[qt.QMouseEvent, qt.QEvent]]
    ) -> None:
        """"""
        super().leftclick_itemImg(event)
        project_status = _sai_.SourceAnalysisCommunicator().get_project_status()
        linker_status = _sai_.SourceAnalysisCommunicator().get_linker_status()
        launch_issues = (
            _sai_.SourceAnalysisCommunicator().get_sa_launch_issues()
        )
        internal_err = _sai_.SourceAnalysisCommunicator().has_internal_error()
        feeder_busy = False
        digester_busy = False
        if internal_err:
            _ht_.sa_internal_problem()
            return
        if launch_issues:
            _ht_.sa_launch_problem()
            return
        if project_status == 2:
            _ht_.sa_project_err()
            return
        if (
            (project_status == 1)
            or (linker_status == 0)
            or (linker_status == 1)
            or feeder_busy
            or digester_busy
        ):
            _ht_.sa_busy()
            return
        _ht_.sa_status_ok()
        return

    def show_contextmenu_itemBtn(
        self, event: Union[qt.QMouseEvent, qt.QEvent]
    ) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _toplvl_contextmenu_.ToplvlContextMenu(
            widg=itemBtn,
            item=self,
            toplvl_key="itemBtn",
            clickfunc=self.contextmenuclick_itemBtn,
        )
        _contextmenu_launcher_.ContextMenuLauncher().launch_contextmenu(
            contextmenu=contextmenu,
            point=functions.get_position(event),
            callback=None,
            callbackArg=None,
        )
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def _help(_key):
            self.leftclick_itemImg(None)
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


class LaunchStatusItem(_sa_tab_items_.File):
    class Status(_sa_tab_items_.File.Status):
        __slots__ = ()

        def __init__(self, item: LaunchStatusItem) -> None:
            super().__init__(item=item)
            self.closedIconpath = "icons/gen/stethoscope.png"
            self.openIconpath = "icons/gen/stethoscope.png"
            self.lblTxt = "launch issues ".ljust(23)
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            ATTENTION: Used to run only if self.get_item()._v_layout is not None, but now it runs
            always!
            """
            item = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
                    qt.QTimer.singleShot(
                        10,
                        functools.partial(
                            self.sync_state,
                            refreshlock,
                            callback,
                            callbackArg,
                        ),
                    )
                    return

            # * Sync self
            if self.has_asterisk():
                self.lblTxt = "*launch issues".ljust(23)
            else:
                self.lblTxt = "launch issues ".ljust(23)
            launch_issues = (
                _sai_.SourceAnalysisCommunicator().get_sa_launch_issues()
            )
            lineedit: _cm_lineedit_.ItemLineedit = item.get_widget(
                "itemLineedit"
            )
            if launch_issues is None:
                self.lineeditTxt = str("no")
                if lineedit is not None:
                    lineedit.setProperty("green", True)
                    lineedit.setProperty("red", False)
                self.set_error(False)
            else:
                self.lineeditTxt = launch_issues
                if lineedit is not None:
                    lineedit.setProperty("green", False)
                    lineedit.setProperty("red", True)
                self.set_error(True)
            functions.assign_icon_err_warn_suffix(itemstatus=self)

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(
        self,
        rootdir: Optional[StatusRootItem],
        parent: Optional[_sa_tab_items_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="launch_status",
            state=LaunchStatusItem.Status(item=self),
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def init_guiVars(self) -> None:
        """"""
        if self._v_layout is not None:
            return
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
            itemLineedit=_cm_lineedit_.ItemLineedit(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def _help(_key):
            print("HELP")
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


class InternalErrorItem(_sa_tab_items_.File):
    class Status(_sa_tab_items_.File.Status):
        __slots__ = ()

        def __init__(self, item: InternalErrorItem) -> None:
            super().__init__(item=item)
            self.closedIconpath = "icons/gen/stethoscope.png"
            self.openIconpath = "icons/gen/stethoscope.png"
            self.lblTxt = "internal error ".ljust(23)
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            ATTENTION: Used to run only if self.get_item()._v_layout is not None, but now it runs
            always!
            """
            item = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
                    qt.QTimer.singleShot(
                        10,
                        functools.partial(
                            self.sync_state,
                            refreshlock,
                            callback,
                            callbackArg,
                        ),
                    )
                    return

            # * Sync self
            if self.has_asterisk():
                self.lblTxt = "*internal error".ljust(23)
            else:
                self.lblTxt = "internal error ".ljust(23)
            lineedit: _cm_lineedit_.ItemLineedit = item.get_widget(
                "itemLineedit"
            )
            if _sai_.SourceAnalysisCommunicator().has_internal_error():
                self.lineeditTxt = str("error")
                if lineedit is not None:
                    lineedit.setProperty("green", False)
                    lineedit.setProperty("red", True)
                self.set_error(True)
            else:
                self.lineeditTxt = str("no")
                if lineedit is not None:
                    lineedit.setProperty("green", True)
                    lineedit.setProperty("red", False)
                self.set_error(False)
            functions.assign_icon_err_warn_suffix(itemstatus=self)

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(
        self,
        rootdir: Optional[StatusRootItem],
        parent: Optional[_sa_tab_items_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="digester_status",
            state=InternalErrorItem.Status(item=self),
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def init_guiVars(self) -> None:
        """"""
        if self._v_layout is not None:
            return
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
            itemLineedit=_cm_lineedit_.ItemLineedit(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def _help(_key):
            print("HELP")
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


class SAStatusItem(_sa_tab_items_.File):
    class Status(_sa_tab_items_.File.Status):
        __slots__ = ()

        def __init__(self, item: SAStatusItem) -> None:
            super().__init__(item=item)
            self.closedIconpath = "icons/gen/stethoscope.png"
            self.openIconpath = "icons/gen/stethoscope.png"
            self.lblTxt = "project status ".ljust(23)
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            ATTENTION: Used to run only if self.get_item()._v_layout is not None, but now it runs
            always!
            """
            item = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
                    qt.QTimer.singleShot(
                        10,
                        functools.partial(
                            self.sync_state,
                            refreshlock,
                            callback,
                            callbackArg,
                        ),
                    )
                    return

            # * Sync self
            if self.has_asterisk():
                self.lblTxt = "*project status".ljust(23)
            else:
                self.lblTxt = "project status ".ljust(23)
            project_status = (
                _sai_.SourceAnalysisCommunicator().get_project_status()
            )
            lineedit: _cm_lineedit_.ItemLineedit = item.get_widget(
                "itemLineedit"
            )
            if project_status == 0:
                self.lineeditTxt = str("0 [ready]")
                if lineedit is not None:
                    lineedit.setProperty("green", True)
                    lineedit.setProperty("red", False)
                self.set_error(False)
            elif project_status == 1:
                self.lineeditTxt = str("1 [busy]")
                if lineedit is not None:
                    lineedit.setProperty("green", False)
                    lineedit.setProperty("red", False)
                self.set_error(False)
            elif project_status == 2:
                self.lineeditTxt = str("2 [error]")
                if lineedit is not None:
                    lineedit.setProperty("green", False)
                    lineedit.setProperty("red", True)
                self.set_error(True)
            else:
                self.lineeditTxt = str(f"{project_status} [???]")
                if lineedit is not None:
                    lineedit.setProperty("green", False)
                    lineedit.setProperty("red", True)
                self.set_error(True)
            functions.assign_icon_err_warn_suffix(itemstatus=self)

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(
        self,
        rootdir: Optional[StatusRootItem],
        parent: Optional[_sa_tab_items_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="source_analyzer_status",
            state=SAStatusItem.Status(item=self),
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def init_guiVars(self) -> None:
        """"""
        if self._v_layout is not None:
            return
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
            itemLineedit=_cm_lineedit_.ItemLineedit(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def _help(_key):
            print("HELP")
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


class LinkerStatusItem(_sa_tab_items_.File):
    class Status(_sa_tab_items_.File.Status):
        __slots__ = ()

        def __init__(self, item: LinkerStatusItem) -> None:
            super().__init__(item=item)
            self.closedIconpath = "icons/gen/stethoscope.png"
            self.openIconpath = "icons/gen/stethoscope.png"
            self.lblTxt = "linker status ".ljust(23)
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            ATTENTION: Used to run only if self.get_item()._v_layout is not None, but now it runs
            always!
            """
            item = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
                    qt.QTimer.singleShot(
                        10,
                        functools.partial(
                            self.sync_state,
                            refreshlock,
                            callback,
                            callbackArg,
                        ),
                    )
                    return

            # * Sync self
            if self.has_asterisk():
                self.lblTxt = "*linker status".ljust(23)
            else:
                self.lblTxt = "linker status ".ljust(23)
            linker_status = (
                _sai_.SourceAnalysisCommunicator().get_linker_status()
            )
            lineedit: _cm_lineedit_.ItemLineedit = item.get_widget(
                "itemLineedit"
            )
            # Don't set an actual error status, because that would propagate
            # upwards. We don't want that for now.
            if linker_status == 0:
                self.lineeditTxt = str("0 [waiting]")
                if lineedit is not None:
                    lineedit.setProperty("green", False)
                    lineedit.setProperty("red", False)
            elif linker_status == 1:
                self.lineeditTxt = str("1 [busy]")
                if lineedit is not None:
                    lineedit.setProperty("green", False)
                    lineedit.setProperty("red", False)
            elif linker_status == 2:
                self.lineeditTxt = str("2 [done]")
                if lineedit is not None:
                    lineedit.setProperty("green", True)
                    lineedit.setProperty("red", False)
            elif linker_status == 3:
                self.lineeditTxt = str("3 [error]")
                if lineedit is not None:
                    lineedit.setProperty("green", False)
                    lineedit.setProperty("red", True)
            else:
                self.lineeditTxt = str(f"{linker_status} [???]")
                if lineedit is not None:
                    lineedit.setProperty("green", False)
                    lineedit.setProperty("red", True)
            functions.assign_icon_err_warn_suffix(itemstatus=self)

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(
        self,
        rootdir: Optional[StatusRootItem],
        parent: Optional[_sa_tab_items_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="source_analyzer_status",
            state=LinkerStatusItem.Status(item=self),
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def init_guiVars(self) -> None:
        """"""
        if self._v_layout is not None:
            return
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
            itemLineedit=_cm_lineedit_.ItemLineedit(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def _help(_key):
            print("HELP")
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


class FeederStatusItem(_sa_tab_items_.File):
    class Status(_sa_tab_items_.File.Status):
        __slots__ = ()

        def __init__(self, item: FeederStatusItem) -> None:
            super().__init__(item=item)
            self.closedIconpath = "icons/gen/stethoscope.png"
            self.openIconpath = "icons/gen/stethoscope.png"
            self.lblTxt = "feeder status ".ljust(23)
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            ATTENTION: Used to run only if self.get_item()._v_layout is not None, but now it runs
            always!
            """
            item = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
                    qt.QTimer.singleShot(
                        10,
                        functools.partial(
                            self.sync_state,
                            refreshlock,
                            callback,
                            callbackArg,
                        ),
                    )
                    return

            # * Sync self
            if self.has_asterisk():
                self.lblTxt = "*feeder status".ljust(23)
            else:
                self.lblTxt = "feeder status ".ljust(23)
            lineedit: _cm_lineedit_.ItemLineedit = item.get_widget(
                "itemLineedit"
            )
            self.lineeditTxt = str("done")
            if lineedit is not None:
                lineedit.setProperty("green", True)
                lineedit.setProperty("red", False)
            functions.assign_icon_err_warn_suffix(itemstatus=self)

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(
        self,
        rootdir: Optional[StatusRootItem],
        parent: Optional[_sa_tab_items_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="feeder_status",
            state=FeederStatusItem.Status(item=self),
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def init_guiVars(self) -> None:
        """"""
        if self._v_layout is not None:
            return
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
            itemLineedit=_cm_lineedit_.ItemLineedit(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def _help(_key):
            print("HELP")
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


class DigesterStatusItem(_sa_tab_items_.File):
    class Status(_sa_tab_items_.File.Status):
        __slots__ = ()

        def __init__(self, item: DigesterStatusItem) -> None:
            super().__init__(item=item)
            self.closedIconpath = "icons/gen/stethoscope.png"
            self.openIconpath = "icons/gen/stethoscope.png"
            self.lblTxt = "digester status ".ljust(23)
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            ATTENTION: Used to run only if self.get_item()._v_layout is not None, but now it runs
            always!
            """
            item = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
                    qt.QTimer.singleShot(
                        10,
                        functools.partial(
                            self.sync_state,
                            refreshlock,
                            callback,
                            callbackArg,
                        ),
                    )
                    return

            # * Sync self
            if self.has_asterisk():
                self.lblTxt = "*digester status".ljust(23)
            else:
                self.lblTxt = "digester status ".ljust(23)
            lineedit: _cm_lineedit_.ItemLineedit = item.get_widget(
                "itemLineedit"
            )
            self.lineeditTxt = str("done")
            if lineedit is not None:
                lineedit.setProperty("green", True)
                lineedit.setProperty("red", False)
            functions.assign_icon_err_warn_suffix(itemstatus=self)

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(
        self,
        rootdir: Optional[StatusRootItem],
        parent: Optional[_sa_tab_items_.Folder],
    ) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=parent,
            name="digester_status",
            state=DigesterStatusItem.Status(item=self),
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def init_guiVars(self) -> None:
        """"""
        if self._v_layout is not None:
            return
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
            itemLineedit=_cm_lineedit_.ItemLineedit(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def _help(_key):
            print("HELP")
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return
