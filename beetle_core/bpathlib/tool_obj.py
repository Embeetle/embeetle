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
import os, data, purefunctions, datetime
import dashboard
import home_toolbox
import bpathlib.path_obj as _po_
import fnmatch as _fn_
import hardware_api.toolcat_unicum as _toolcat_unicum_

if TYPE_CHECKING:
    import dashboard.items.item as _da_
    import dashboard.items.path_items.toolpath_items as _da_topi_
    import home_toolbox.items.item as _tm_
    import home_toolbox.items.toolchain_items.toolchain_items as _tm_tci_
    import home_toolbox.items.flash_tool_items.flash_tool_items as _tm_fdsi_
    import home_toolbox.items.build_automation_items.build_automation_items as _tm_bai_
    import project.segments.path_seg.toolpath_seg as _toolpath_seg_
nop = lambda *a, **k: None
q = "'"
dq = '"'


class ToolpathObj(_po_.PathObj):
    """The ToolpathObj() is just a shell. It only stores:

        - unique_id
        - cat_unicum
    and will always look for the matching ToolmanObj() to return vital info.
    """

    def __init__(
        self,
        cat_unic: _toolcat_unicum_.TOOLCAT_UNIC,
        unique_id: str,
        is_fake: bool = False,
    ) -> None:
        """
        :param cat_unic:
        :param unique_id:
        """
        # Given this ToolpathObj() to be a shell, providing a rootpath or relpath wouldn't make
        # sense!
        super().__init__(
            unicum=cat_unic,
            rootpath_or_rootid=None,
            relpath=None,
        )
        self.__unique_id = unique_id
        self.__is_fake = is_fake
        return

    def get_matching_toolmanObj(self) -> Optional[ToolmanObj]:
        """"""
        unique_id = self.__unique_id
        if (unique_id is None) or (unique_id.lower() == "none"):
            return None
        toolmanObj = data.toolman.get_toolmanobj(unique_id=unique_id)
        if toolmanObj is not None:
            assert isinstance(toolmanObj, ToolmanObj)
            assert (
                toolmanObj.get_category().lower() == self.get_category().lower()
            )
        return toolmanObj

    def has_matching_toolmanObj(self) -> bool:
        """"""
        toolmanObj = self.get_matching_toolmanObj()
        if toolmanObj is None:
            return False
        return True

    def get_name(self) -> Optional[str]:
        """Right term is 'category', not 'name'!"""
        raise NotImplementedError()

    def get_category(self) -> Optional[str]:
        """"""
        return super().get_name()

    def create_dashboardItem(
        self,
        rootItem: Optional[_da_.Root],
        parentItem: Optional[_da_.Folder],
        *args,
        toolpath_seg: Optional[_toolpath_seg_.ToolpathSeg] = None,
        report: Optional[Dict[Any, Any]] = None,
        **kwargs,
    ) -> _da_topi_.ToolpathItem:
        """Create item to be shown in the dashboard."""
        if rootItem is not None:
            assert isinstance(
                rootItem, dashboard.items.path_items.toolpath_items.ToolRootItem
            )
            assert (
                isinstance(
                    parentItem,
                    dashboard.items.path_items.toolpath_items.ToolRootItem,
                )
                or isinstance(
                    parentItem,
                    dashboard.items.path_items.toolpath_items.ToolpathItem,
                )
                or isinstance(parentItem, dashboard.items.item.Folder)
            )
        assert self._v_dashboardItem is None
        assert self._v_toolmanItem is None
        self._v_dashboardItem = (
            dashboard.items.path_items.toolpath_items.ToolpathItem(
                toolpath_obj=self,
                toolpath_seg=toolpath_seg,
                rootdir=rootItem,
                parent=parentItem,
                report=report,
            )
        )
        assert self._v_dashboardItem.get_projSegment() is self
        return self._v_dashboardItem

    def set_unique_id(self, unique_id: Optional[str]) -> None:
        """"""
        self.__unique_id = unique_id
        # Notify the Filetree if possible.
        if (
            self.__is_fake
            or (data.signal_dispatcher is None)
            or (data.current_project is None)
            or (data.current_project.get_toolpath_seg() is None)
        ):
            return
        if self.get_category() == "BUILD_AUTOMATION":
            data.signal_dispatcher.build_automation_changed_sig.emit(
                self.get_abspath()
            )
            return
        if self.get_category() == "COMPILER_TOOLCHAIN":
            data.signal_dispatcher.compiler_toolchain_changed_sig.emit(
                data.current_project.get_toolpath_seg().get_compiler_folderpath()
            )
            return
        if self.get_category() == "FLASHTOOL":
            data.signal_dispatcher.flashtool_changed_sig.emit(
                self.get_abspath()
            )
            return
        return

    def get_unique_id(self) -> Optional[str]:
        """"""
        return self.__unique_id

    def get_unique_id_iconpath(self) -> Optional[str]:
        """"""
        return self.get_unicum().get_unique_id_iconpath(
            unique_id=self.__unique_id
        )

    def get_other_unique_id_iconpath(
        self, other_unique_id: str
    ) -> Optional[str]:
        """"""
        return self.get_unicum().get_unique_id_iconpath(
            unique_id=other_unique_id
        )

    def get_relevant_treepaths(self) -> List[str]:
        """"""
        return self.get_unicum().get_relevant_treepaths(
            unique_id=self.get_unique_id()
        )

    def set_relpath(self, relpath: str) -> None:
        """"""
        raise RuntimeError()

    def set_abspath(self, abspath: str) -> None:
        """"""
        raise RuntimeError()

    def get_relpath(self) -> Optional[str]:
        """"""
        raise RuntimeError()

    def get_abspath(self) -> Optional[str]:
        """"""
        toolmanObj = self.get_matching_toolmanObj()
        if toolmanObj is None:
            return None
        return toolmanObj.get_abspath()

    def get_rootpath(self) -> Optional[str]:
        """"""
        toolmanObj = self.get_matching_toolmanObj()
        if toolmanObj is None:
            return None
        return toolmanObj.get_rootpath()

    def get_toolprefix(self, absolute: bool = True) -> Optional[str]:
        """"""
        toolmanObj = self.get_matching_toolmanObj()
        if toolmanObj is None:
            return None
        return toolmanObj.get_toolprefix(absolute)

    def refresh_version_info(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        toolmanObj = self.get_matching_toolmanObj()
        if toolmanObj is None:
            if callback is not None:
                callback(callbackArg)
            return
        toolmanObj.refresh_version_info(callback, callbackArg)
        return

    def has_version_info(self) -> bool:
        """"""
        toolmanObj = self.get_matching_toolmanObj()
        if toolmanObj is None:
            return False
        return toolmanObj.has_version_info()

    def get_version_info(
        self, key: str
    ) -> Optional[Union[str, datetime.datetime]]:
        """"""
        toolmanObj = self.get_matching_toolmanObj()
        if toolmanObj is None:
            return None
        # Ensure we return only str or None to match the return type
        result = toolmanObj.get_version_info(key)
        if key == "date":
            if result is None:
                return None
            assert isinstance(result, datetime.datetime)
            return result
        return str(result) if result is not None else None

    def has_info_purple(self) -> bool:
        """"""
        toolmanObj = self.get_matching_toolmanObj()
        if toolmanObj is None:
            return False
        return toolmanObj.has_info_purple()

    def has_info_blue(self) -> bool:
        """"""
        toolmanObj = self.get_matching_toolmanObj()
        if toolmanObj is None:
            return False
        return toolmanObj.has_info_blue()

    def set_info_purple(self, i: bool) -> None:
        """"""
        raise RuntimeError()

    def set_info_blue(self, i: bool) -> None:
        """"""
        raise RuntimeError()


class ToolmanObj(_po_.PathObj):
    """Based on the given abspath, this ToolmanObj() calculates its own
    'unique_id' and other version info."""

    def __init__(
        self,
        cat_unic: _toolcat_unicum_.TOOLCAT_UNIC,
        abspath: str,
    ) -> None:
        """"""
        if (abspath is None) or (abspath.lower() == "none"):
            super().__init__(
                unicum=cat_unic,
                rootpath_or_rootid=None,
                relpath=None,
            )
        else:
            super().__init__(
                unicum=cat_unic,
                rootpath_or_rootid=abspath,
                relpath=".",
            )
        self._version_info = {
            "name": None,
            "unique_id": None,
            "version": None,
            "suffix": None,
            "bitness": None,
            "date": None,
        }
        self.__saved = False
        return

    def set_saved(self, saved: bool) -> None:
        """"""
        self.__saved = saved
        return

    def is_saved(self) -> bool:
        """"""
        return self.__saved

    def get_name(self) -> Optional[str]:
        """Right term is 'category', not 'name'!"""
        raise NotImplementedError()

    def get_category(self) -> Optional[str]:
        """"""
        return super().get_name()

    def create_toolmanItem(
        self, rootItem: _tm_.Root, parentItem: _tm_.Folder
    ) -> Union[
        _tm_tci_.ToolchainItem,
        _tm_fdsi_.FlashToolItem,
        _tm_bai_.BuildAutomationItem,
    ]:
        """Create item to be shown in the Home Toolmanager."""
        assert (
            isinstance(
                rootItem,
                home_toolbox.items.toolchain_items.toolchain_items.ToolchainRootItem,
            )
            or isinstance(
                rootItem,
                home_toolbox.items.flash_tool_items.flash_tool_items.FlashToolRootItem,
            )
            or isinstance(
                rootItem,
                home_toolbox.items.build_automation_items.build_automation_items.BuildAutomationRootItem,
            )
        )
        assert (
            isinstance(
                parentItem,
                home_toolbox.items.toolchain_items.toolchain_items.ToolchainRootItem,
            )
            or isinstance(
                parentItem,
                home_toolbox.items.flash_tool_items.flash_tool_items.FlashToolRootItem,
            )
            or isinstance(
                parentItem,
                home_toolbox.items.build_automation_items.build_automation_items.BuildAutomationRootItem,
            )
        )
        assert self._v_toolmanItem is None
        assert self._v_dashboardItem is None
        if isinstance(
            rootItem,
            home_toolbox.items.toolchain_items.toolchain_items.ToolchainRootItem,
        ):
            self._v_toolmanItem = home_toolbox.items.toolchain_items.toolchain_items.ToolchainItem(
                toolmanObj=self,
                rootdir=rootItem,
            )
        if isinstance(
            rootItem,
            home_toolbox.items.flash_tool_items.flash_tool_items.FlashToolRootItem,
        ):
            self._v_toolmanItem = home_toolbox.items.flash_tool_items.flash_tool_items.FlashToolItem(
                toolmanObj=self,
                rootdir=rootItem,
            )
        if isinstance(
            rootItem,
            home_toolbox.items.build_automation_items.build_automation_items.BuildAutomationRootItem,
        ):
            self._v_toolmanItem = home_toolbox.items.build_automation_items.build_automation_items.BuildAutomationItem(
                toolmanObj=self,
                rootdir=rootItem,
            )
        assert self._v_toolmanItem.get_toolObj() is self
        return self._v_toolmanItem

    def set_unique_id(self, unique_id: str) -> None:
        """"""
        purefunctions.printc(
            "ERROR: Cannot change unique_id from a ToolmanObj()",
            color="error",
        )
        raise RuntimeError()

    def get_unique_id(self) -> Optional[str]:
        """"""
        return self._version_info["unique_id"]

    def get_unique_id_iconpath(self) -> Optional[str]:
        """"""
        return self.get_unicum().get_unique_id_iconpath(
            unique_id=self.get_unique_id()
        )

    def get_other_unique_id_iconpath(
        self, other_unique_id: str
    ) -> Optional[str]:
        """"""
        return self.get_unicum().get_unique_id_iconpath(
            unique_id=other_unique_id
        )

    def get_relevant_treepaths(self) -> List[str]:
        """"""
        return self.get_unicum().get_relevant_treepaths(
            unique_id=self.get_unique_id()
        )

    def set_relpath(self, relpath: str) -> None:
        """"""
        raise RuntimeError()

    def set_abspath(self, abspath: str) -> None:
        """"""
        if (abspath is None) or (abspath.lower() == "none"):
            self.set_doublepath((None, None))
            return
        self.set_doublepath((abspath, "."))
        return

    def get_relpath(self) -> Optional[str]:
        """"""
        raise RuntimeError()

    def get_abspath(self) -> Optional[str]:
        """"""
        return super().get_abspath()

    def get_toolfolder(self) -> Optional[str]:
        """
        Return folder such as:
            - 'C:/.../krist/.embeetle/beetle_tools/gnu_make_4.2.0_32b'
            - 'C:/.../krist/.embeetle/beetle_tools/openocd_0.10.0_dev00973_32b'
        """
        abspath = self.get_abspath()
        if not os.path.exists(abspath):
            return None
        # $ It's a directory
        if os.path.isdir(abspath):
            return abspath
        # $ It's a file
        assert os.path.isfile(abspath)
        tool_dirpath = os.path.dirname(abspath).replace("\\", "/")
        if tool_dirpath.endswith("/"):
            tool_dirpath = tool_dirpath[0:-1]
        assert os.path.isdir(tool_dirpath)
        if tool_dirpath.endswith("/bin"):
            tool_dirpath = tool_dirpath[0:-4]
        return tool_dirpath

    def get_toolprefix(self, absolute: bool = True) -> Optional[str]:
        """"""
        exepath = None
        abspath = self.get_abspath()
        unique_id = self.get_unique_id()
        if (
            (abspath is None)
            or (unique_id is None)
            or (abspath.lower() == "none")
            or (unique_id.lower() == "none")
        ):
            return None
        if not os.path.isfile(abspath):
            exekind, exepath = data.toolversion_extractor.extract_executable(
                dirpath=abspath
            )
        else:
            exepath = abspath
        toolprefix = data.toolversion_extractor.extract_toolprefix(exepath)
        if toolprefix is None:
            return None
        if absolute:
            return toolprefix
        return toolprefix.split("/")[-1]

    def refresh_version_info(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Run the tool with '--version' flag."""

        def finish(vdict: Dict[str, Any]) -> None:
            # Example vdict:
            # vdict = {
            #     'name'      : 'openocd_nuvoton',
            #     'unique_id' : 'openocd_0.10.0_dev00973_32b'
            #     'version'   : '0.10.0',
            #     'suffix'    : '00973',
            #     'bitness'   : '32b',
            #     'date'      : datetime.datetime(2018, 11, 27, 0, 0),
            # }
            if vdict is None:
                abort(
                    kill_unique_id=True,
                    reason=str(f"Could not acquire version."),
                )
                return
            self._version_info = vdict
            if callback is not None:
                callback(callbackArg)
            return

        def abort(kill_unique_id: bool, reason: Optional[str]) -> None:
            for k, v in self._version_info.items():
                if k != "unique_id":
                    self._version_info[k] = None
                elif kill_unique_id:
                    self._version_info[k] = None
            if reason is not None:
                print(
                    f"{self.get_category()}.refresh_version_info() failed:\n"
                    f"{reason}"
                )
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        # & Exception: built-in flash_tool
        if self._version_info["unique_id"] is not None:
            if _fn_.fnmatch(
                name=str(self._version_info["unique_id"]),
                pat="*built*in*",
            ):
                abort(
                    kill_unique_id=False,
                    reason=None,
                ),
                return
        exepath = None
        abspath = self.get_abspath()

        # & Exception: abspath is None
        if (abspath is None) or (abspath.lower() == "none"):
            abort(
                kill_unique_id=True,
                reason=str(f"    Stored abspath = {self.get_abspath()}\n"),
            )
            return

        # & Find executable that matches this tool
        if not os.path.isfile(abspath):
            exekind, exepath = data.toolversion_extractor.extract_executable(
                dirpath=abspath,
            )
        else:
            exepath = abspath

        # & Extract version info
        version_info = None
        if (exepath is not None) and (os.path.isfile(exepath)):
            data.toolversion_extractor.extract_toolversion(
                exepath=exepath,
                callback=finish,
            )
            return
        abort(
            kill_unique_id=True,
            reason=str(
                f"    Stored abspath = {self.get_abspath()}\n"
                f"    Executable = {exepath}\n"
            ),
        )
        return

    def has_version_info(self) -> bool:
        """"""
        if self._version_info["name"] is None:
            return False
        return True

    def get_version_info(self, key) -> Optional[Union[str, datetime.datetime]]:
        """"""
        if key == "date":
            if self._version_info["date"] is None:
                return None
            assert isinstance(self._version_info["date"], datetime.datetime)
            return self._version_info["date"]
        return self._version_info[key]
