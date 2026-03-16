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
import qt, data, functions, gui
import dashboard.items.item as _da_
import project.segments.version_seg.version_seg as _version_seg_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_arrow as _cm_arrow_
import tree_widget.widgets.item_lbl as _cm_lbl_
import tree_widget.widgets.item_lineedit as _cm_lineedit_
import dashboard.contextmenus.toplvl_contextmenu as _toplvl_contextmenu_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_
import wizards.upgrade_proj_wizard.repair_proj_wizard as _repair_proj_wizard_
import wizards.upgrade_proj_wizard.upgrade_proj_wizard as _upgrade_proj_wizard_

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
from various.kristofstuff import *

# ^                             VERSION ROOT ITEM                              ^#
# % ========================================================================== %#
# % VersionRootItem()                                                          %#
# %                                                                            %#


class VersionRootItem(_da_.Root):
    class Status(_da_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: VersionRootItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/gen/certificate.png"
            self.openIconpath = "icons/gen/certificate.png"
            self.lblTxt = "Version "
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
            if self.get_item() is None:
                if callback is not None:
                    callback(callbackArg)
                return
            if refreshlock:
                if not self.get_item().acquire_refresh_mutex():
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

            def sync_self(*args) -> None:
                if self.has_asterisk():
                    self.lblTxt = "*Version"
                else:
                    self.lblTxt = "Version "
                version_seg: _version_seg_.VersionSeg = (
                    self.get_item().get_projSegment()
                )
                functions.assign_icon_err_warn_suffix(itemstatus=self)
                finish()
                return

            def finish(*args) -> None:
                (
                    self.get_item().release_refresh_mutex()
                    if refreshlock
                    else nop()
                )
                callback(callbackArg) if callback is not None else nop()
                return

            _da_.Folder.Status.sync_state(
                self,
                refreshlock=False,
                callback=sync_self,
                callbackArg=None,
            )
            return

    __slots__ = ()

    def __init__(self, version: _version_seg_.VersionSeg) -> None:
        """"""
        super().__init__(
            projSegment=version,
            name="version",
            state=VersionRootItem.Status(item=self),
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
            itemArrow=_cm_arrow_.ItemArrow(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
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
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
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
        version: _version_seg_.VersionSeg = self.get_projSegment()

        def _help(_key):
            # _ht_.version_help(version)
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


# ^                                       PROJECT TYPE ITEM                                        ^#
# % ============================================================================================== %#
# % ProjectTypeItem()                                                                              %#
# %                                                                                                %#


class ProjectTypeItem(_da_.File):
    class Status(_da_.File.Status):
        __slots__ = ()

        def __init__(self, item: ProjectTypeItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/logo/gnu.png"
            self.openIconpath = "icons/logo/gnu.png"
            self.lblTxt = "Project Type ".ljust(17)
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
            if self.get_item() is None:
                if callback is not None:
                    callback(callbackArg)
                return
            if refreshlock:
                if not self.get_item().acquire_refresh_mutex():
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

            def sync_self(*args) -> None:
                if self.has_asterisk():
                    self.lblTxt = "*Project Type".ljust(17)
                else:
                    self.lblTxt = "Project Type ".ljust(17)
                version_seg: _version_seg_.VersionSeg = (
                    self.get_item().get_projSegment()
                )
                self.lineeditTxt = "makefile-based"
                functions.assign_icon_err_warn_suffix(itemstatus=self)
                finish()
                return

            def finish(*args) -> None:
                if refreshlock:
                    self.get_item().release_refresh_mutex()
                if callback is not None:
                    callback(callbackArg)
                return

            _da_.File.Status.sync_state(
                self,
                refreshlock=False,
                callback=sync_self,
                callbackArg=None,
            )
            return

    __slots__ = ()

    def __init__(
        self,
        version: _version_seg_.VersionSeg,
        rootdir: Optional[VersionRootItem],
        parent: Optional[_da_.Folder],
    ) -> None:
        """"""
        super().__init__(
            projSegment=version,
            rootdir=rootdir,
            parent=parent,
            name="project_type",
            state=ProjectTypeItem.Status(item=self),
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
        super().leftclick_itemBtn(event)
        self.show_project_type_info(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        self.show_project_type_info(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        self.show_project_type_info(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        self.show_project_type_info(event)
        return

    def leftclick_itemLineedit(self, event: qt.QEvent) -> None:
        super().leftclick_itemLineedit(event)
        self.show_project_type_info(event)
        return

    def rightclick_itemLineedit(self, event: qt.QEvent) -> None:
        super().rightclick_itemLineedit(event)
        self.show_project_type_info(event)
        return

    def show_project_type_info(self, *args) -> None:
        """Show a popup with more information about the project type."""
        version_seg: _version_seg_.VersionSeg = self.get_projSegment()
        version_seg.show_project_type_info()
        return

    def show_contextmenu_itemBtn(self, event: qt.QEvent) -> None:
        itemBtn = self.get_widget(key="itemBtn")
        return

    def contextmenuclick_itemBtn(self, key: str, *args):
        key = functions.strip_toplvl_key(key)
        return


# ^                                        VERSION NR ITEM                                         ^#
# % ============================================================================================== %#
# % VersionNrItem()                                                                                %#
# %                                                                                                %#


class VersionNrItem(_da_.File):
    class Status(_da_.File.Status):
        __slots__ = ()

        def __init__(self, item: VersionNrItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/gen/certificate.png"
            self.openIconpath = "icons/gen/certificate.png"
            self.lblTxt = "Project Version ".ljust(17)
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
            if self.get_item() is None:
                if callback is not None:
                    callback(callbackArg)
                return
            if refreshlock:
                if not self.get_item().acquire_refresh_mutex():
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

            def sync_self(*args) -> None:
                if self.has_asterisk():
                    self.lblTxt = "*Project Version".ljust(17)
                else:
                    self.lblTxt = "Project Version ".ljust(17)
                version_seg: _version_seg_.VersionSeg = (
                    self.get_item().get_projSegment()
                )
                self.lineeditTxt = str(version_seg.get_version_nr())
                functions.assign_icon_err_warn_suffix(itemstatus=self)
                finish()
                return

            def finish(*args) -> None:
                if refreshlock:
                    self.get_item().release_refresh_mutex()
                if callback is not None:
                    callback(callbackArg)
                return

            _da_.File.Status.sync_state(
                self,
                refreshlock=False,
                callback=sync_self,
                callbackArg=None,
            )
            return

    __slots__ = ()

    def __init__(
        self,
        version: _version_seg_.VersionSeg,
        rootdir: Optional[VersionRootItem],
        parent: Optional[_da_.Folder],
    ) -> None:
        """"""
        super().__init__(
            projSegment=version,
            rootdir=rootdir,
            parent=parent,
            name="version_nr",
            state=VersionNrItem.Status(item=self),
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
        super().leftclick_itemBtn(event)
        self.show_version_info(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        self.show_version_info(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        self.show_version_info(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        self.show_version_info(event)
        return

    def leftclick_itemLineedit(self, event: qt.QEvent) -> None:
        super().leftclick_itemLineedit(event)
        self.show_version_info(event)
        return

    def rightclick_itemLineedit(self, event: qt.QEvent) -> None:
        super().rightclick_itemLineedit(event)
        self.show_version_info(event)
        return

    def show_version_info(self, *args) -> None:
        """Show a popup with all the extracted version nrs."""
        version_seg: _version_seg_.VersionSeg = self.get_projSegment()
        version_seg.show_extracted_version_nrs()
        return

    def show_contextmenu_itemBtn(self, event: qt.QEvent) -> None:
        itemBtn = self.get_widget(key="itemBtn")
        return

    def contextmenuclick_itemBtn(self, key: str, *args):
        key = functions.strip_toplvl_key(key)
        return


# ^                                          REPAIR ITEM                                           ^#
# % ============================================================================================== %#
# % RepairItem()                                                                                   %#
# %                                                                                                %#


class RepairItem(_da_.File):
    class Status(_da_.File.Status):
        __slots__ = ()

        def __init__(self, item: RepairItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/gen/certificate_repair.png"
            self.openIconpath = "icons/gen/certificate_repair.png"
            self.lblTxt = "Repair Project ..."
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
            if self.get_item() is None:
                if callback is not None:
                    callback(callbackArg)
                return
            if refreshlock:
                if not self.get_item().acquire_refresh_mutex():
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

            def sync_self(*args) -> None:
                if self.has_asterisk():
                    self.lblTxt = "*Repair Project ..."
                else:
                    self.lblTxt = "Repair Project ..."
                version_seg: _version_seg_.VersionSeg = (
                    self.get_item().get_projSegment()
                )
                functions.assign_icon_err_warn_suffix(itemstatus=self)
                finish()
                return

            def finish(*args) -> None:
                if refreshlock:
                    self.get_item().release_refresh_mutex()
                if callback is not None:
                    callback(callbackArg)
                return

            _da_.File.Status.sync_state(
                self,
                refreshlock=False,
                callback=sync_self,
                callbackArg=None,
            )
            return

    __slots__ = ("__repair_proj_wizard",)

    def __init__(
        self,
        version: _version_seg_.VersionSeg,
        rootdir: Optional[VersionRootItem],
        parent: Optional[_da_.Folder],
    ) -> None:
        """"""
        super().__init__(
            projSegment=version,
            rootdir=rootdir,
            parent=parent,
            name="repair_item",
            state=RepairItem.Status(item=self),
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        self.__repair_proj_wizard: Optional[
            _repair_proj_wizard_.RepairProjWizard
        ] = None
        return

    def init_guiVars(self) -> None:
        """"""
        if self._v_layout is not None:
            return
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QEvent) -> None:
        super().leftclick_itemBtn(event)
        self.__show_repair_wizard(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        self.__show_repair_wizard(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        self.__show_repair_wizard(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        self.__show_repair_wizard(event)
        return

    def __show_repair_wizard(self, *args) -> None:
        """Show the wizard to upgrade the project.

        This instance is designed in such a way that it will always completely
        destroy itself, regardless of how you close it.
        """
        projObj = data.current_project
        highest_v = 0
        version_seg: _version_seg_.VersionSeg = projObj.get_version_seg()
        v = version_seg.get_version_nr()
        if v > highest_v:
            highest_v = v

        self.__repair_proj_wizard = _repair_proj_wizard_.RepairProjWizard(
            parent=data.main_form,
            cur_version=highest_v,
            new_version=highest_v,
            callback=self.__finish_repair_wizard,
            callbackArg=None,
        )
        self.__repair_proj_wizard.show()
        return

    def __finish_repair_wizard(
        self,
        success: bool,
        *args,
    ) -> None:
        """User finishes the wizard."""
        self.__repair_proj_wizard = None
        version_seg: _version_seg_.VersionSeg = self.get_projSegment()
        cur_version = version_seg.get_version_nr()
        if success:
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/gen/certificate.png",
                title_text="Project repaired",
                text=str(
                    f"Your project has been repaired according to <b>Embeetle Makefile<br>"
                    f"Interface Version {cur_version}</b>"
                ),
            )
        return

    def show_contextmenu_itemBtn(self, event: qt.QEvent) -> None:
        itemBtn = self.get_widget(key="itemBtn")
        return

    def contextmenuclick_itemBtn(self, key: str, *args):
        key = functions.strip_toplvl_key(key)
        return


# ^                                      VERSION UPGRADE ITEM                                      ^#
# % ============================================================================================== %#
# % VersionUpgradeItem()                                                                           %#
# %                                                                                                %#


class VersionUpgradeItem(_da_.File):
    class Status(_da_.File.Status):
        __slots__ = ()

        def __init__(self, item: VersionUpgradeItem) -> None:
            super().__init__(item=item)
            self.closedIconpath = "icons/gen/certificate_upgrade.png"
            self.openIconpath = "icons/gen/certificate_upgrade.png"
            self.lblTxt = "Upgrade "
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
            if self.get_item() is None:
                if callback is not None:
                    callback(callbackArg)
                return
            if refreshlock:
                if not self.get_item().acquire_refresh_mutex():
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

            def sync_self(*args):
                if self.has_asterisk():
                    self.lblTxt = "*Upgrade"
                else:
                    self.lblTxt = "Upgrade "
                version_seg: _version_seg_.VersionSeg = (
                    self.get_item().get_projSegment()
                )
                latest_version = (
                    functions.get_latest_makefile_interface_version()
                )
                current_version = version_seg.get_version_nr()
                self.lblTxt += f"({current_version} > {latest_version}) ..."
                if latest_version != current_version:
                    self.set_warning(True)
                else:
                    self.set_warning(False)
                functions.assign_icon_err_warn_suffix(itemstatus=self)
                finish()
                return

            def finish(*args):
                if refreshlock:
                    self.get_item().release_refresh_mutex()
                if callback is not None:
                    callback(callbackArg)
                return

            _da_.File.Status.sync_state(
                self,
                refreshlock=False,
                callback=sync_self,
                callbackArg=None,
            )
            return

    __slots__ = ("__upgrade_proj_wizard",)

    def __init__(
        self,
        version: _version_seg_.VersionSeg,
        rootdir: Optional[VersionRootItem],
        parent: Optional[_da_.Folder],
    ) -> None:
        """"""
        super().__init__(
            projSegment=version,
            rootdir=rootdir,
            parent=parent,
            name="version_nr",
            state=VersionUpgradeItem.Status(item=self),
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        self.__upgrade_proj_wizard: Optional[
            _upgrade_proj_wizard_.UpgradeProjWizard
        ] = None
        return

    def init_guiVars(self) -> None:
        if self._v_layout is not None:
            return
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QEvent) -> None:
        super().leftclick_itemBtn(event)
        self.__show_upgrade_wizard(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        self.__show_upgrade_wizard(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        self.__show_upgrade_wizard(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        self.__show_upgrade_wizard(event)
        return

    def __show_upgrade_wizard(self, *args) -> None:
        """Show the wizard to upgrade the project.

        This instance is designed in such a way that it will always completely
        destroy itself, regardless of how you close it.
        """
        version_seg: _version_seg_.VersionSeg = self.get_projSegment()
        self.__upgrade_proj_wizard = _upgrade_proj_wizard_.UpgradeProjWizard(
            parent=data.main_form,
            cur_version=version_seg.get_version_nr(),
            new_version=functions.get_latest_makefile_interface_version(),
            callback=self.__finish_upgrade_wizard,
            callbackArg=None,
        )
        self.__upgrade_proj_wizard.show()
        return

    def __finish_upgrade_wizard(
        self,
        success: bool,
        *args,
    ) -> None:
        """User finishes the wizard."""
        self.__upgrade_proj_wizard = None
        version_seg: _version_seg_.VersionSeg = self.get_projSegment()
        cur_version = version_seg.get_version_nr()
        new_version = functions.get_latest_makefile_interface_version()
        if success and (cur_version == new_version):
            # The upgrade succeeded
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/gen/certificate.png",
                title_text="Upgrade succeeded",
                text=str(
                    f"Your project has been upgraded to <b>Embeetle Makefile<br>"
                    f"Interface Version {new_version}</b>."
                ),
            )
        elif success:
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/gen/certificate.png",
                title_text="Upgrade failed",
                text=str(
                    f"Embeetle failed to upgrade your project to <b>Embeetle Makefile<br>"
                    f"Interface Version {new_version}</b>."
                ),
            )
        return

    def show_contextmenu_itemBtn(self, event: qt.QEvent) -> None:
        itemBtn = self.get_widget(key="itemBtn")
        return

    def contextmenuclick_itemBtn(self, key: str, *args):
        key = functions.strip_toplvl_key(key)
        return
