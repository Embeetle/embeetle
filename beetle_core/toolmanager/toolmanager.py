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
from components.singleton import Singleton
import os, sys, pprint, threading, copy, traceback
import qt, data, purefunctions, functions, serverfunctions, gui
import bpathlib.path_power as _pp_
import bpathlib.file_power as _fp_
import hardware_api.toolcat_unicum as _toolcat_unicum_
import bpathlib.tool_obj as _tool_obj_
import home_toolbox.chassis.home_toolbox as _toolbox_widg_
import home_toolbox.items.toolchain_items.toolchain_items as _toolchain_i_
import home_toolbox.items.build_automation_items.build_automation_items as _buildauto_i_
import home_toolbox.items.flash_tool_items.flash_tool_items as _probemid_i_
import home_toolbox.items.info_items as _info_i_
import home_toolbox.items.add_item as _add_i_
import toolmanager.version_extractor as _v_
import fnmatch as _fn_
import components.thread_switcher as _sw_
import toolmanager_downloader.downloader as _downloader_
import hardware_api.hardware_api as _hardware_api_
import os_checker

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
    import wizards.tool_wizard.new_tool_wizard as _wiz_
    import project.segments.chip_seg.chip as _chip_
    import tree_widget.widgets.item_btn as _item_btn_
    import tree_widget.widgets.item_lbl as _item_lbl_
    import tree_widget.widgets.item_action_btn as _item_action_btn_
from various.kristofstuff import *


class Toolmanager(metaclass=Singleton):
    """
    ============================================================================
    |                                 DATABASE                                 |
    ============================================================================
    The Toolmanager()-singleton keeps a ToolmanObj() per tool it finds. If run-
    ning in the Home Window, each ToolmanObj() generates a displayable
    ToolmanItem() for the TOOLBOX tab.

    The ToolmanObj()s are kept in a nested dictionary:
    ┌───────────────────────────────────────────────────────────────────────────────────┐
    │ self._tp_nesteddict_ =                                                            │
    │ {        ╭--------------------------------------------------------> tool category │
    │          |                 ╭--------------------------------------> unique id     │
    │     'COMPILER_TOOLCHAIN':  |                                   ╭--> ToolmanObj()  │
    │     {                      |                                   |                  │
    │         'gnu_arm_toolchain_9.2.1_9-2019-q4-major_32b'    : <ToolmanObj()>,        │
    │         'gnu_riscv_sifive_toolchain_8.3.0_2019.08.0_64b' : <ToolmanObj()>,        │
    │     },                                                                            │
    │                                                                                   │
    │     'FLASHTOOL':                                                                  │
    │     {                                                                             │
    │         'openocd_0.10.0_dev00973_32b': <ToolmanObj()>,                            │
    │         'openocd_0.10.0_dev01138_64b': <ToolmanObj()>,                            │
    │         'pyocd_0.23.1_dev10_64b'     : <ToolmanObj()>,                            │
    │     },                                                                            │
    │                                                                                   │
    │     'BUILD_AUTOMATION':                                                           │
    │     {                                                                             │
    │         'gnu_make_4.2.1_32b': <ToolmanObj()>                                      │
    │     },                                                                            │
    │ }                                                                                 │
    └───────────────────────────────────────────────────────────────────────────────────┘

    NOTE: This Singleton gets saved to data.toolman

    ============================================================================
    |                           VISUAL REPRESENTATION                          |
    ============================================================================
    This Toolmanager()-singleton also directs the visual representation in the
    Home Windows' TOOLBOX tab. It holds three Root()-items for that purpose:
        - self._v_rootItem_toolchain
        - self._v_rootItem_buildauto
        - self._v_rootItem_probemid

    The TOOLBOX Chassis is defined in 'home_toolbox/chassis/home_toolbox.py' and
    the shown Items in 'home_toolbox/items/...'. Very much like the dashboard
    chassis and items.
    The dashboard items are *directed* by the project segments. In the same way,
    the toolbox items are *directed* by this Toolmanager()-singleton.
    """

    def __init__(self, mode: Optional[str] = None) -> None:
        """"""
        super().__init__()
        if data.startup_log_toolmanager:
            print(
                f"[startup] toolmanager.py -> Toolmanager.__init__({q}{mode}{q})"
            )

        # * General variables
        self.__mode = mode
        self._tp_nesteddict_: Dict[str, Dict[str, _tool_obj_.ToolmanObj]] = {}
        self.__cached_remote_beetle_toollist: Optional[List] = None

        # * Home Window TOOLBOX tab
        self._v_rootItem_buildauto: Optional[
            _buildauto_i_.BuildAutomationRootItem
        ] = None
        self._v_rootItem_toolchain: Optional[
            _toolchain_i_.ToolchainRootItem
        ] = None
        self._v_rootItem_probemid: Optional[_probemid_i_.FlashToolRootItem] = (
            None
        )
        if self.__mode == "home":
            assert isinstance(data.toolbox_widg, _toolbox_widg_.Toolbox)
            self._v_rootItem_buildauto = _buildauto_i_.BuildAutomationRootItem()
            self._v_rootItem_toolchain = _toolchain_i_.ToolchainRootItem()
            self._v_rootItem_probemid = _probemid_i_.FlashToolRootItem()
            data.toolbox_widg.add_root(self._v_rootItem_buildauto)
            data.toolbox_widg.add_root(self._v_rootItem_toolchain)
            data.toolbox_widg.add_root(self._v_rootItem_probemid)
        elif self.__mode == "project":
            pass
        else:
            assert False
        return

    def init_all(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """The Toolmanager() object must be initialized before use!

        This Toolmanager()-instance keeps a ToolmanObj() per tool it finds. If this code is running
        in the Home Window, the ToolmanObj() will generate a displayable ToolmanItem() - shown in
        the TOOLBOX tab.
        """
        if data.startup_log_toolmanager:
            print("[startup] toolmanager.py -> init_all()")
        origthread: qt.QThread = qt.QThread.currentThread()

        def parse_path(*args):
            if data.startup_log_toolmanager:
                print("[startup] toolmanager.py -> init_all().parse_path()")
            assert qt.QThread.currentThread() is origthread
            parse_saved()
            # self.parse_path_tools(
            #     callback    = parse_saved,
            #     callbackArg = None,
            # )
            return

        def parse_saved(*args):
            if data.startup_log_toolmanager:
                print("[startup] toolmanager.py -> init_all().parse_saved()")
            assert qt.QThread.currentThread() is origthread
            self.parse_saved_tools(
                callback=refresh_compiler_toolchain,
                callbackArg=None,
            )

        def refresh_compiler_toolchain(*args):
            if data.startup_log_toolmanager:
                print(
                    "[startup] toolmanager.py -> init_all().refresh_compiler_toolchain()"
                )
            assert qt.QThread.currentThread() is origthread
            if self._v_rootItem_toolchain is None:
                assert self._v_rootItem_buildauto is None
                assert self._v_rootItem_probemid is None
                finish()
                return
            self._v_rootItem_toolchain._v_emitter.refresh_recursive_later_sig.emit(
                True,
                False,
                refresh_build_automation,
                None,
            )
            return

        def refresh_build_automation(*args):
            if data.startup_log_toolmanager:
                print(
                    "[startup] toolmanager.py -> init_all().refresh_build_automation()"
                )
            assert threading.current_thread() is threading.main_thread()
            self._v_rootItem_buildauto._v_emitter.refresh_recursive_later_sig.emit(
                True,
                False,
                refresh_flash_tool,
                None,
            )
            return

        def refresh_flash_tool(*args):
            if data.startup_log_toolmanager:
                print(
                    "[startup] toolmanager.py -> init_all().refresh_flash_tool()"
                )
            assert threading.current_thread() is threading.main_thread()
            self._v_rootItem_probemid._v_emitter.refresh_recursive_later_sig.emit(
                True,
                False,
                switch,
                None,
            )
            return

        def switch(*args):
            if data.startup_log_toolmanager:
                print("[startup] toolmanager.py -> init_all().switch()")
            _sw_.switch_thread_new(
                qthread=origthread,
                callback=finish,
                args=None,
            )
            return

        def finish(*args):
            if data.startup_log_toolmanager:
                print("[startup] toolmanager.py -> init_all().finish()")
            assert qt.QThread.currentThread() is origthread
            if self.__mode == "home":
                assert threading.current_thread() is threading.main_thread()
                for rootItem in (
                    self._v_rootItem_toolchain,
                    self._v_rootItem_probemid,
                    self._v_rootItem_buildauto,
                ):
                    addItem = _add_i_.AddItem(rootdir=rootItem)
                    rootItem.add_child(
                        addItem,
                        alpha_order=False,
                        show=False,
                        callback=None,
                        callbackArg=None,
                    )
            callback(callbackArg)
            return

        assert qt.QThread.currentThread() is origthread
        self.parse_beetle_tools(
            callback=parse_path,
            callbackArg=None,
        )
        return

    def parse_beetle_tools(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Parse the 'beetle_tools' folder for tools."""
        if data.startup_log_toolmanager:
            print("[startup] toolmanager.py -> parse_beetle_tools()")

        def analyze_next(
            _toolmanObj: Optional[_tool_obj_.ToolmanObj],
            _dirpathIter: Iterator[str],
        ) -> None:
            # Note: param toolmanObj is from previous analysis
            try:
                _dirpath = next(_dirpathIter)
            except StopIteration:
                # Finish
                if callback is not None:
                    callback(callbackArg)
                return
            if data.startup_log_toolmanager:
                path_msg = _dirpath
                if "beetle_tools/" in path_msg:
                    path_msg = path_msg.split("/")[-1]
                print(
                    f"[startup] toolmanager.py -> parse_beetle_tools().analyze_next({q}{path_msg}{q})"
                )
            self.add_tool(
                dirpath_or_exepath=_dirpath,
                wiz=None,
                callback=analyze_next,
                callbackArg=_dirpathIter,
            )
            return

        # * Start
        if not os.path.isdir(data.beetle_tools_directory):
            _fp_.make_dir(
                dir_abspath=data.beetle_tools_directory,
                printfunc=nop,
                catch_err=True,
                overwr=False,
            )
        rootpath = data.beetle_tools_directory
        if not os.path.isdir(rootpath):
            _fp_.make_dir(
                dir_abspath=rootpath,
                printfunc=nop,
                catch_err=True,
                overwr=False,
            )
            # Finish
            if callback is not None:
                callback(callbackArg)
            return

        # First check out all the subdirectories of 'beetle_tools/'
        dirnames = os.listdir(rootpath)
        dirpaths = []
        for name in dirnames:
            if name == "windows" or name == "linux":
                continue
            dirpath = _pp_.rel_to_abs(rootpath=rootpath, relpath=name)
            if os.path.isfile(dirpath):
                continue
            dirpaths.append(dirpath)
            continue

        # In the newest code, we no longer make the 'windows/' and 'linux/'
        # subdirectories under 'beetle_tools/', but they might still exist from
        # old code.
        if os.path.exists(f"{data.beetle_tools_directory}/windows"):
            rootpath = f"{data.beetle_tools_directory}/windows"
        elif os.path.exists(f"{data.beetle_tools_directory}/linux"):
            rootpath = f"{data.beetle_tools_directory}/linux"
        else:
            rootpath = None
        if rootpath:
            dirnames = os.listdir(rootpath)
            for name in dirnames:
                dirpath = _pp_.rel_to_abs(rootpath=rootpath, relpath=name)
                if os.path.isfile(dirpath):
                    continue
                dirpaths.append(dirpath)
                continue

        # Iterate over all found directories (they probably represent a tool
        # each)
        dirpathIter = iter(dirpaths)
        analyze_next(None, dirpathIter)
        return

    def parse_path_tools(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:

        callback(callbackArg)
        return
        """
        Parse the tools present on your PATH.
        """
        if data.startup_log_toolmanager:
            print(f"[startup] toolmanager.py -> parse_path_tools()")
        known_exes = []

        def analyze_next_dirpath(_dirpathIter: Iterator[str]) -> None:
            try:
                _dirpath = next(_dirpathIter)
            except StopIteration:
                # * Finish
                if data.startup_log_toolmanager:
                    print(
                        f"[startup] toolmanager.py -> parse_path_tools().finish()"
                    )
                callback(callbackArg)
                return
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> parse_path_tools().analyze_next_dirpath({q}{_dirpath}{q})"
                )
            analyze_dirpath(None, (_dirpath, _dirpathIter))
            return

        def analyze_dirpath(
            _toolmanObj: Optional[_tool_obj_.ToolmanObj],
            arg: Tuple[str, Iterator[str]],
        ) -> None:
            # Note: param _toolmanObj is from previous analysis
            nonlocal known_exes
            _dirpath, _dirpathIter = arg
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> parse_path_tools().analyze_dirpath({q}{_dirpath}{q})"
                )
            exekind, exepath = _v_.VersionExtractor().extract_executable(
                dirpath=_dirpath,
                exename=None,
                known_exes=known_exes,
            )

            # $ If nothing found => move on to next
            if (exekind is None) or (exekind.lower() == "none"):
                analyze_next_dirpath(_dirpathIter)
                return
            if (exepath is None) or (exepath.lower() == "none"):
                analyze_next_dirpath(_dirpathIter)
                return

            # $ Something found => add it
            known_exes.append(exepath)
            self.add_tool(
                dirpath_or_exepath=exepath,
                wiz=None,
                callback=analyze_dirpath,
                callbackArg=(_dirpath, _dirpathIter),
            )
            return

        # * Start
        dirpaths: List[str] = []
        path_list: Optional[List[str]] = None
        if os_checker.is_os("windows"):
            path_list = os.environ["PATH"].split(";")
        else:
            path_list = os.environ["PATH"].split(":")
        for path in path_list:
            path = path.replace("\\", "/")
            path = path.replace("//", "/")
            if path.endswith("/"):
                path = path[0:-1]
            if os.path.isdir(path):
                if data.beetle_tools_directory in path:
                    # beetle tools get discovered in other function
                    # -> ignore
                    pass
                else:
                    dirpaths.append(path)
            else:
                # It's a file
                # -> ignore
                pass
        dirpathIter = iter(dirpaths)
        analyze_next_dirpath(dirpathIter)
        return

    def parse_saved_tools(
        self, callback: Optional[Callable], callbackArg: Any
    ) -> None:
        """Parse the saved tools."""
        if data.startup_log_toolmanager:
            print(f"[startup] toolmanager.py -> parse_saved_tools()")

        def analyze_next(
            _toolmanObj: Optional[_tool_obj_.ToolmanObj],
            _dirpathIter: Iterator[str],
        ) -> None:
            # Note: param toolmanObj is from previous analysis
            try:
                _dirpath = next(_dirpathIter)
            except StopIteration:
                # * Finish
                if data.startup_log_toolmanager:
                    print(
                        f"[startup] toolmanager.py -> parse_saved_tools().finish()"
                    )
                callback(callbackArg)
                return

            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> parse_saved_tools().analyze_next({q}{_dirpath}{q})"
                )
            self.add_tool(
                dirpath_or_exepath=_dirpath,
                wiz=None,
                callback=analyze_next,
                callbackArg=_dirpathIter,
            )
            return

        # * Start
        filepath: Optional[str] = None
        filepath_1: str = _pp_.rel_to_abs(
            rootpath=data.settings_directory, relpath="embeetle_tools.btl"
        )
        filepath_2: str = _pp_.rel_to_abs(
            rootpath=data.settings_directory, relpath="beetle_tools.btl"
        )
        filepath_3: str = _pp_.rel_to_abs(
            rootpath=data.settings_directory, relpath="tools.btl"
        )
        if os.path.isfile(filepath_1):
            filepath = filepath_1
        elif os.path.isfile(filepath_2):
            filepath = filepath_2
        elif os.path.isfile(filepath_3):
            filepath = filepath_3
        else:
            # * Finish
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> parse_saved_tools().finish()"
                )
            callback(callbackArg)
            return
        pathlist: List[str] = []
        with open(filepath, "r", encoding="utf-8", newline="\n") as f:
            text = f.readlines()
        assert isinstance(text, list)
        for line in text:
            assert isinstance(line, str)
            line = line.strip()
            if line == "":
                pass
            elif line.startswith("#"):
                pass
            else:
                line = _pp_.standardize_abspath(line)
                pathlist.append(line)
        if len(pathlist) == 0:
            # * Finish
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> parse_saved_tools().finish()"
                )
            callback(callbackArg)
            return
        dirpathIter = iter(pathlist)
        analyze_next(None, dirpathIter)
        return

    def save_tools(self) -> None:
        """Save all external tools that are not on the PATH."""
        filepath: Optional[str] = None
        filepath_1: str = _pp_.rel_to_abs(
            rootpath=data.settings_directory,
            relpath="embeetle_tools.btl",
        )
        filepath_2: str = _pp_.rel_to_abs(
            rootpath=data.settings_directory,
            relpath="beetle_tools.btl",
        )
        filepath_3: str = _pp_.rel_to_abs(
            rootpath=data.settings_directory,
            relpath="tools.btl",
        )
        if os.path.isfile(filepath_1):
            filepath = filepath_1
        elif os.path.isfile(filepath_2):
            filepath = filepath_2
        elif os.path.isfile(filepath_3):
            filepath = filepath_3
        else:
            filepath = filepath_1
            try:
                _fp_.make_file(filepath, print, catch_err=False, overwr=False)
            except Exception as e:
                purefunctions.printc(
                    f"ERROR: Cannot create file\n{q}{filepath}{q}",
                    color="error",
                )
                return
        pathlist: List[str] = []
        for _catname_, _tooldict_ in self._tp_nesteddict_.items():
            for _id, toolmanObj in _tooldict_.items():
                if toolmanObj.is_saved():
                    abspath = toolmanObj.get_abspath()
                    if os.path.isfile(abspath):
                        abspath = os.path.dirname(abspath)
                        abspath = _pp_.standardize_abspath(abspath)
                    pathlist.append(abspath + "\n")
        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            f.writelines(
                [
                    f"# EXTERNAL TOOLS\n",
                    f"# Tools that are not in the <beetle-tools> folder,\n",
                    f"# nor on the PATH env variable:\n",
                ]
            )
            f.writelines(pathlist)
        return

    def sort_toollist(
        self,
        toollist: List[Dict],
    ) -> List[Dict]:
        """Sort the given toollist, like:

        toollist = [
            {
                'name'     : 'gnu_arm_toolchain',
                'kind'     : 'COMPILER_TOOLCHAIN',
                'version'  : '9.2.1_9-2019-q4-major',
                'bitness'  : '32b',
                'unique_id': 'gnu_arm_toolchain_9.2.1_9-2019-q4-major_32b',
                'iconpath' : 'icons/tools/gnu_arm.png',
            },

            {
                'name'     : 'gnu_make',
                'kind'     : 'BUILD_AUTOMATION',
                'version'  : '4.2.0',
                'bitness'  : '32b',
                'unique_id': 'gnu_make_4.2.0_32b',
                'iconpath' : 'icons/tools/gnu_arm.png',
            },
            ...
        ]
        """
        # Make sure the original list is not affected
        copied_toollist = copy.deepcopy(toollist)
        # Split the toollist according to the categories
        build_automation_toollist = []
        compiler_toolchain_toollist = []
        flashtool_toollist = []
        for tooldict in copied_toollist:
            if tooldict["kind"].lower() == "build_automation":
                build_automation_toollist.append(tooldict)
                continue
            if tooldict["kind"].lower() == "compiler_toolchain":
                compiler_toolchain_toollist.append(tooldict)
                continue
            if tooldict["kind"].lower() == "flashtool":
                flashtool_toollist.append(tooldict)
                continue
            raise RuntimeError(
                f'tooldict[{q}kind{q}] = {q}{tooldict["kind"]}{q} not recognized!'
            )

        def give_sort_nr(_toollist: List[Dict[str, str]]) -> None:
            for d1 in _toollist:
                if "nr" not in d1.keys():
                    d1["nr"] = "0"
                for d2 in _toollist:
                    if "nr" not in d2.keys():
                        d2["nr"] = "0"
                    if d1 is d2:
                        continue
                    assert "nr" in d1.keys()
                    assert "nr" in d2.keys()
                    try:
                        # $ Same version
                        if d1["version"] == d2["version"]:
                            if d1["bitness"] == d2["bitness"]:
                                pass
                            elif d1["bitness"] > d2["bitness"]:
                                d1["nr"] = str(int(d1["nr"]) + 1)
                                d2["nr"] = str(int(d2["nr"]) + 0)
                            else:
                                d1["nr"] = str(int(d1["nr"]) + 0)
                                d2["nr"] = str(int(d2["nr"]) + 1)
                        # $ d1 > d2
                        elif functions.is_larger_than(
                            d1["version"], d2["version"]
                        ):
                            d1["nr"] = str(int(d1["nr"]) + 1)
                            d2["nr"] = str(int(d2["nr"]) + 0)
                        # $ d1 < d2
                        else:
                            d1["nr"] = str(int(d1["nr"]) + 0)
                            d2["nr"] = str(int(d2["nr"]) + 1)
                    except:
                        pass
                    continue
                continue

        give_sort_nr(build_automation_toollist)
        give_sort_nr(compiler_toolchain_toollist)
        give_sort_nr(flashtool_toollist)

        def sort_key(d: Dict[str, str]) -> int:
            return int(d["nr"])

        build_automation_toollist.sort(key=sort_key, reverse=True)
        compiler_toolchain_toollist.sort(key=sort_key, reverse=True)
        flashtool_toollist.sort(key=sort_key, reverse=True)
        return (
            build_automation_toollist
            + compiler_toolchain_toollist
            + flashtool_toollist
        )

    def get_remote_beetle_toollist(
        self,
        toolcat: Optional[str] = None,
        callback: Optional[Callable] = None,
    ) -> None:
        """
        Request the list of all tools available on the server. The list is returned through the
        provided callback:
        > callback(toollist)

        if toolcat is not None, the list is filtered first on the given tool category before being
        passed to the callback.

        Example of returned toollist:
        toollist = [
            {
                'name'     : 'gnu_arm_toolchain',
                'kind'     : 'COMPILER_TOOLCHAIN',
                'version'  : '9.2.1_9-2019-q4-major',
                'bitness'  : '32b',
                'unique_id': 'gnu_arm_toolchain_9.2.1_9-2019-q4-major_32b',
                'iconpath' : 'icons/tools/gnu_arm.png',
            },

            {
                'name'     : 'gnu_make',
                'kind'     : 'BUILD_AUTOMATION',
                'version'  : '4.2.0',
                'bitness'  : '32b',
                'unique_id': 'gnu_make_4.2.0_32b',
                'iconpath' : 'icons/tools/gnu_arm.png',
            },
            ...
        ]

        NOTE: If connection error, returned toollist is None
        NOTE: If no tools on server for given category, toollist = []
        """
        if data.startup_log_toolmanager:
            print(
                f"[startup] toolmanager.py -> get_remote_beetle_toollist({q}{toolcat}{q})"
            )
        if callback is None:
            callback = pprint.pprint

        def finish(toollist: Optional[List[Dict[str, str]]]) -> None:
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> get_remote_beetle_toollist().finish()"
                )
            if self.__cached_remote_beetle_toollist is None:
                self.__cached_remote_beetle_toollist = toollist
            if toollist is None:
                callback(None)
                return
            if not isinstance(toollist, list):
                callback(None)
                return
            try:
                assert isinstance(toollist, list)
                # $ Icons
                # Stuff an iconpath in each tool dictionary
                new_toollist = []
                for _tooldict_ in toollist:
                    if (toolcat is None) or (
                        _tooldict_["kind"].lower() == toolcat.lower()
                    ):
                        _tooldict_["iconpath"] = self.get_matching_iconpath(
                            _tooldict_["name"]
                        )
                        new_toollist.append(_tooldict_)
                if len(new_toollist) == 0:
                    callback(new_toollist)
                    return

                # $ Sort and return the toollist
                callback(self.sort_toollist(new_toollist))
                return
            except:
                callback(None)
                return
            assert False
            return

        # * Start
        if self.__cached_remote_beetle_toollist is None:
            serverfunctions.get_remote_beetle_toollist(finish)
            return
        finish(self.__cached_remote_beetle_toollist)
        return

    def get_local_beetle_toollist(
        self,
        toolcat: Optional[str] = None,
        callback: Optional[Callable] = None,
    ) -> None:
        """Same as previous, but for local tools."""
        if callback is None:
            callback = pprint.pprint
        if data.startup_log_toolmanager:
            print(
                f"[startup] toolmanager.py -> get_local_beetle_toollist({q}{toolcat}{q})"
            )

        def finish(toollist):
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> get_local_beetle_toollist().finish()"
                )
            if toolcat == "FLASHTOOL":
                toollist.append(
                    {
                        "name": "built_in",
                        "kind": "FLASHTOOL",
                        "version": "None",
                        "bitness": "None",
                        "unique_id": "built_in",
                        "iconpath": self.get_matching_iconpath("built_in"),
                    }
                )
            callback(self.sort_toollist(toollist))
            return

        # * Start
        new_toollist = []
        for _catname_, _tooldict_ in self._tp_nesteddict_.items():
            if (toolcat is not None) and (toolcat.lower() != _catname_.lower()):
                continue
            for unique_id, toolmanObj in _tooldict_.items():
                version = toolmanObj.get_version_info("version")
                suffix = toolmanObj.get_version_info("suffix")
                if (suffix is None) or (suffix.lower() == "none"):
                    pass
                else:
                    version += suffix
                new_toollist.append(
                    {
                        "name": toolmanObj.get_version_info("name"),
                        "kind": toolmanObj.get_category(),
                        "version": version,
                        "bitness": toolmanObj.get_version_info("bitness"),
                        "unique_id": unique_id,
                        "iconpath": self.get_matching_iconpath(unique_id),
                    }
                )
        finish(new_toollist)
        return

    def delete_tool_light(
        self,
        unique_id: str,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Delete the tool from the dictionary, but not from harddrive!

        > callback(success, callbackArg)
        """

        def kill_toolmanItem(_toolmanObj: _tool_obj_.ToolmanObj) -> None:
            assert threading.current_thread() is threading.main_thread()
            _toolmanObj.delete_toolmanItem(
                callback=update_nesteddict, callbackArg=None
            )
            return

        def update_nesteddict(*args) -> None:
            assert threading.current_thread() is threading.main_thread()
            for _catname_, _tooldict_ in self._tp_nesteddict_.items():
                for _id, _ in _tooldict_.items():
                    if _id.lower() == unique_id.lower():
                        del _tooldict_[_id]
                        finish()
                        return
            raise RuntimeError(f"ERROR: unique_id {q}{unique_id}{q} not found!")

        def abort(*args) -> None:
            assert threading.current_thread() is threading.main_thread()
            if callback is not None:
                callback(False, callbackArg)
            return

        def finish(*args) -> None:
            assert threading.current_thread() is threading.main_thread()
            if callback is not None:
                callback(True, callbackArg)
            return

        # * Start
        assert threading.current_thread() is threading.main_thread()
        if unique_id is None:
            abort()
            return
        toolmanObj: _tool_obj_.ToolmanObj = self.get_toolmanobj(unique_id)
        if toolmanObj is None:
            abort()
            return
        if self.__mode == "home":
            kill_toolmanItem(toolmanObj)
        else:
            update_nesteddict()
        return

    def delete_tool(
        self,
        toolmanObj: _tool_obj_.ToolmanObj,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Delete the tool corresponding to the given ToolmanObj()

        > callback(success, callbackArg)
        """

        def delete_from_hdd(_toolfolder: str) -> None:
            assert threading.current_thread() is threading.main_thread()
            success = _fp_.delete_dir(
                dir_abspath=_toolfolder,
                catch_err=True,
            )
            print(f"\nDelete folder {q}{_toolfolder}{q}\nSuccess = {success}\n")
            if not success:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    title_text="Cannot delete folder",
                    icon_path="icons/dialog/warning.png",
                    text=f"Embeetle failed to delete the folder:<br>"
                    f'<span style="color:#3465a4">&nbsp;&nbsp;&nbsp;&nbsp;'
                    f"{q}{_toolfolder}{q}</span><br>"
                    f"Make sure the folder is not open in another program and<br>"
                    f"try again.",
                )
                abort()
                return
            self.delete_tool_light(
                unique_id=toolmanObj.get_unique_id(),
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(success: bool, *args) -> None:
            assert threading.current_thread() is threading.main_thread()
            if not success:
                abort()
                return
            if callback is not None:
                callback(True, callbackArg)
            return

        def abort(*args) -> None:
            assert threading.current_thread() is threading.main_thread()
            if callback is not None:
                callback(False, callbackArg)
            return

        # * Start
        assert threading.current_thread() is threading.main_thread()
        assert self.__mode == "home"
        if (toolmanObj.get_unique_id() is None) or (
            toolmanObj.get_unique_id().lower() == "none"
        ):
            purefunctions.printc(f"ERROR: Cannot delete {q}None{q} tool!")
            abort()
            return
        toolfolder = toolmanObj.get_toolfolder()
        if not functions.allowed_to_delete_folder(
            abspath=toolfolder,
            allow_rootpath_deletion=False,
        ):
            gui.dialogs.popupdialog.PopupDialog.ok(
                title_text=f"Delete tool?",
                icon_path=f"icons/gen/trash.png",
                text=str(
                    f"Embeetle cannot delete this tool:<br>"
                    f'<span style="color:#3465a4">&nbsp;&nbsp;&nbsp;&nbsp;'
                    f"{toolmanObj.get_unique_id()}</span><br>"
                    f"<br>"
                ),
            )
            abort()
            return
        reply = gui.dialogs.popupdialog.PopupDialog.question(
            title_text=f"Delete tool?",
            icon_path=f"icons/gen/trash.png",
            text=str(
                f"Are you sure you want to delete tool<br>"
                f'<span style="color:#3465a4">&nbsp;&nbsp;&nbsp;&nbsp;'
                f"{toolmanObj.get_unique_id()}</span><br>"
                f"from your harddrive?<br>"
                f"The following folder will be deleted:<br>"
                f'<span style="color#3465a4">&nbsp;&nbsp;&nbsp;&nbsp;'
                f"{q}{toolfolder}{q}</span><br>"
                f"This action cannot be undone.<br>"
            ),
        )
        if reply != qt.QMessageBox.StandardButton.Yes:
            abort()
            return
        delete_from_hdd(toolfolder)
        return

    def add_tool(
        self,
        dirpath_or_exepath: str,
        wiz: Optional[_wiz_.NewToolWizard],
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Analyze the given tool on the harddrive and create a matching
        ToolmanObj().

        Proceed as follows:
            1. wiz is not None
                Don't add the ToolmanObj() to the nested dictionary. Don't add
                it to the TOOLBOX tab either!
                Instead, apply the ToolmanObj() on the given wizard-object and
                return the ToolmanObj() in the end.

            2. wiz is None
                Add the ToolmanObj() to the nested dictionary. Add it also to
                the TOOLBOX tab if self.__mode == 'home'.
                Return the ToolmanObj() in the end (although nothing really
                happens to the return-value).

        NOTE: I used to take the foldername as unique_id, but stopped doing
              that. Now, the unique_id is always computed (run tool with
              --version flag).

        NOTE: If the computed 'unique_id' already exists in the nested dict,
              the addition operation is aborted (unless wiz is not None, in which
              case this doesn't matter).

        NOTE: If the '--version' run fails, then unique_id = None. Adding the
              tool fails.

        :param dirpath_or_exepath:  Tool location (directory or executable)
        :param wiz:                 [Optional] NewToolWizard() object.

        > callback(ToolmanObj(), callbackArg)
        """
        if data.startup_log_toolmanager:
            path_msg = dirpath_or_exepath
            if "beetle_tools/" in path_msg:
                path_msg = path_msg.split("/")[-1]
            print(
                f"[startup] toolmanager.py -> add_tool({q}{path_msg}{q}, {wiz is None})"
            )

        dirpath: Optional[str] = None  # Toplevel directory from tool.
        exepath: Optional[str] = (
            None  # Path to tool executable. For compiler, path to 'gcc.exe'.
        )
        exekind: Optional[str] = (
            None  # 'COMPILER_TOOLCHAIN', 'BUILD_AUTOMATION' or 'FLASHTOOL'
        )
        dirpath_or_exepath = _pp_.standardize_abspath(dirpath_or_exepath)

        def check_tool_version(_toolmanObj: _tool_obj_.ToolmanObj) -> None:
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> add_tool().check_tool_version()"
                )
            unique_id = _toolmanObj.get_unique_id()
            #! Abort if unique_id is None !#
            if (unique_id is None) or (unique_id.lower() == "none"):
                abort(
                    show_error=True,
                    reason=str(
                        f"        The parameter given to add_tool() is:\n"
                        f"        {dirpath_or_exepath}\n"
                        f"        The unique_id extracted from running the\n"
                        f"        tool with the {q}--version{q} flag is:\n"
                        f"        {q}{unique_id}{q}"
                    ),
                )
                return
            if wiz is not None:
                apply_on_wiz(_toolmanObj)
                return
            apply_on_nesteddict(_toolmanObj)
            return

        def apply_on_wiz(_toolmanObj: _tool_obj_.ToolmanObj) -> None:
            # & Add the toolmanObj to the given wizard
            if data.startup_log_toolmanager:
                print(f"[startup] toolmanager.py -> add_tool().apply_on_wiz()")
            assert threading.current_thread() is threading.main_thread()
            # $ name
            wiz._widgets_p2r1["name_lineedit"].setText(
                _toolmanObj.get_version_info("name")
            )
            wiz._widgets_p2r1["name_lineedit"].update()
            # $ unique_id
            wiz._widgets_p2r1["unique_id_lineedit"].setText(
                str(_toolmanObj.get_unique_id())
            )
            # $ version
            version = _toolmanObj.get_version_info("version")
            suffix = _toolmanObj.get_version_info("suffix")
            if suffix is not None:
                wiz._widgets_p2r1["version_lineedit"].setText(
                    f"{version} ({suffix})"
                )
            else:
                wiz._widgets_p2r1["version_lineedit"].setText(version)
            # $ build_date
            date = _toolmanObj.get_version_info("date")
            if date is None:
                wiz._widgets_p2r1["build_date_lineedit"].setText("none")
            else:
                wiz._widgets_p2r1["build_date_lineedit"].setText(
                    f'{date.strftime("%d %b %Y")}'
                )
            # $ bitness
            bitness = _toolmanObj.get_version_info("bitness")
            if bitness is None:
                wiz._widgets_p2r1["bitness_lineedit"].setText("none")
            else:
                wiz._widgets_p2r1["bitness_lineedit"].setText(bitness)
            # $ location
            location = _toolmanObj.get_abspath()
            if (location is None) or (location.lower() == "none"):
                wiz._widgets_p2r1["location_lineedit"].setText("none")
            else:
                if data.beetle_tools_directory in location:
                    location = location.replace(
                        data.beetle_tools_directory,
                        "<beetle-tools>",
                        1,
                    )
                wiz._widgets_p2r1["location_lineedit"].setText(
                    f"{q}{location}{q}"
                )
            # $ toolprefix
            toolprefix_lineedit = wiz._widgets_p2r1["toolprefix_lineedit"]
            if toolprefix_lineedit is not None:
                toolprefix = _toolmanObj.get_toolprefix()
                if (toolprefix is None) or (toolprefix.lower() == "none"):
                    toolprefix_lineedit.setText("none")
                elif data.beetle_tools_directory in toolprefix:
                    toolprefix = toolprefix.replace(
                        data.beetle_tools_directory,
                        "<beetle-tools>",
                        1,
                    )
                    toolprefix_lineedit.setText(f"{q}{toolprefix}{q}")
                else:
                    tool_abspath = _toolmanObj.get_abspath()
                    if os.path.isfile(tool_abspath):
                        tool_abspath = os.path.dirname(tool_abspath).replace(
                            "\\", "/"
                        )
                    toolprefix = toolprefix.replace(
                        tool_abspath,
                        "<tool-folder>",
                        1,
                    )
                    toolprefix_lineedit.setText(f"{q}{toolprefix}{q}")
            finish(_toolmanObj)
            return

        def apply_on_nesteddict(_toolmanObj: _tool_obj_.ToolmanObj) -> None:
            # & Add the toolmanObj to the nested dictionary
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> add_tool().apply_on_nesteddict()"
                )
            assert wiz is None
            unique_id = _toolmanObj.get_unique_id()
            if any(unique_id == _id for _id in self.list_unique_ids(exekind)):
                print(
                    f"INFO: Tool with unique_id = {q}{unique_id}{q} already added."
                )
                print(f"location 1: {q}{_toolmanObj.get_abspath()}{q}")
                print(f"location 2: {q}{dirpath_or_exepath}{q}")
                abort(False)
                return
            if _toolmanObj.get_category() not in self._tp_nesteddict_:
                self._tp_nesteddict_[_toolmanObj.get_category()] = {}
            self._tp_nesteddict_[_toolmanObj.get_category()][
                unique_id
            ] = _toolmanObj
            if self.is_external(_toolmanObj):
                if not self.is_onpath(_toolmanObj):
                    _toolmanObj.set_saved(True)
            if self.__mode == "home":
                apply_on_toolbox_tab_a(_toolmanObj)
                return
            finish(_toolmanObj)
            return

        def apply_on_toolbox_tab_a(_toolmanObj: _tool_obj_.ToolmanObj) -> None:
            # & Add the toolmanObj visually to the TOOLBOX tab
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> add_tool().apply_on_toolbox_tab_a()"
                )
            assert threading.current_thread() is threading.main_thread()
            assert self.__mode == "home"
            assert wiz is None
            rootItem: Union[
                _toolchain_i_.ToolchainRootItem,
                _buildauto_i_.BuildAutomationRootItem,
                _probemid_i_.FlashToolRootItem,
                None,
            ] = None
            if exekind == "COMPILER_TOOLCHAIN":
                rootItem = self._v_rootItem_toolchain
            if exekind == "BUILD_AUTOMATION":
                rootItem = self._v_rootItem_buildauto
            if exekind == "FLASHTOOL":
                rootItem = self._v_rootItem_probemid
            assert rootItem is not None
            addItem: _add_i_.AddItem = cast(
                _add_i_.AddItem,
                rootItem.get_child_byName("AddItem"),
            )
            if addItem is not None:
                addItem.self_destruct(
                    killParentLink=True,
                    callback=apply_on_toolbox_tab_b,
                    callbackArg=(_toolmanObj, rootItem, True),
                )
                return
            apply_on_toolbox_tab_b((_toolmanObj, rootItem, False))
            return

        def apply_on_toolbox_tab_b(
            arg: Tuple[
                _tool_obj_.ToolmanObj,
                Union[
                    _buildauto_i_.BuildAutomationRootItem,
                    _toolchain_i_.ToolchainRootItem,
                    _probemid_i_.FlashToolRootItem,
                ],
                bool,
            ],
        ) -> None:
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> add_tool().apply_on_toolbox_tab_b()"
                )
            assert threading.current_thread() is threading.main_thread()
            _toolmanObj, rootItem, add_item_deleted = arg
            _toolmanObj.create_toolmanItem(
                rootItem=rootItem, parentItem=rootItem
            )
            rootItem.add_child(
                child=_toolmanObj.get_toolmanItem(),
                alpha_order=False,
                show=False,
                callback=apply_on_toolbox_tab_c,
                callbackArg=(_toolmanObj, rootItem, add_item_deleted),
            )
            return

        def apply_on_toolbox_tab_c(
            arg: Tuple[
                _tool_obj_.ToolmanObj,
                Union[
                    _buildauto_i_.BuildAutomationRootItem,
                    _toolchain_i_.ToolchainRootItem,
                    _probemid_i_.FlashToolRootItem,
                ],
                bool,
            ],
        ) -> None:
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> add_tool().apply_on_toolbox_tab_c()"
                )
            assert threading.current_thread() is threading.main_thread()
            _toolmanObj, rootItem, add_item_deleted = arg
            uniqueIDNameItem = _info_i_.UniqueIDNameItem(
                toolObj=_toolmanObj,
                rootdir=rootItem,
                parent=_toolmanObj.get_toolmanItem(),
            )
            uniqueIDItem = _info_i_.UniqueIDItem(
                toolObj=_toolmanObj,
                rootdir=rootItem,
                parent=_toolmanObj.get_toolmanItem(),
            )
            versionItem = _info_i_.VersionItem(
                toolObj=_toolmanObj,
                rootdir=rootItem,
                parent=_toolmanObj.get_toolmanItem(),
            )
            builddateItem = _info_i_.BuilddateItem(
                toolObj=_toolmanObj,
                rootdir=rootItem,
                parent=_toolmanObj.get_toolmanItem(),
            )
            bitnessItem = _info_i_.BitnessItem(
                toolObj=_toolmanObj,
                rootdir=rootItem,
                parent=_toolmanObj.get_toolmanItem(),
            )
            locationItem = _info_i_.LocationItem(
                toolObj=_toolmanObj,
                rootdir=rootItem,
                parent=_toolmanObj.get_toolmanItem(),
            )
            toolprefixItem = None
            if exekind == "COMPILER_TOOLCHAIN":
                toolprefixItem = _info_i_.ToolprefixItem(
                    toolObj=_toolmanObj,
                    rootdir=rootItem,
                    parent=_toolmanObj.get_toolmanItem(),
                )
            _toolmanObj.get_toolmanItem().add_child(
                uniqueIDNameItem,
                alpha_order=False,
                show=False,
                callback=None,
                callbackArg=None,
            )
            _toolmanObj.get_toolmanItem().add_child(
                uniqueIDItem,
                alpha_order=False,
                show=False,
                callback=None,
                callbackArg=None,
            )
            _toolmanObj.get_toolmanItem().add_child(
                versionItem,
                alpha_order=False,
                show=False,
                callback=None,
                callbackArg=None,
            )
            _toolmanObj.get_toolmanItem().add_child(
                builddateItem,
                alpha_order=False,
                show=False,
                callback=None,
                callbackArg=None,
            )
            _toolmanObj.get_toolmanItem().add_child(
                bitnessItem,
                alpha_order=False,
                show=False,
                callback=None,
                callbackArg=None,
            )
            _toolmanObj.get_toolmanItem().add_child(
                locationItem,
                alpha_order=False,
                show=False,
                callback=None,
                callbackArg=None,
            )
            if exekind == "COMPILER_TOOLCHAIN":
                _toolmanObj.get_toolmanItem().add_child(
                    toolprefixItem,
                    alpha_order=False,
                    show=False,
                    callback=None,
                    callbackArg=None,
                )
            # $ Phase = post-startup
            if add_item_deleted:

                def close_root(*args) -> None:
                    if rootItem.get_state().open:
                        rootItem.close_later(
                            click=False,
                            callback=open_root,
                            callbackArg=None,
                        )
                        return
                    open_root()
                    return

                def open_root(*args) -> None:
                    if not rootItem.get_state().open:
                        rootItem.open_later(
                            click=False,
                            callback=finish_open,
                            callbackArg=None,
                        )
                        return
                    finish_open()
                    return

                def finish_open(*args) -> None:
                    finish(_toolmanObj)
                    return

                addItem = _add_i_.AddItem(rootdir=rootItem)
                rootItem.add_child(
                    addItem,
                    alpha_order=False,
                    show=False,
                    callback=close_root,
                    callbackArg=None,
                )
                return

            # $ Phase = startup
            assert not add_item_deleted
            finish(_toolmanObj)
            return

        def finish(_toolmanObj: _tool_obj_.ToolmanObj) -> None:
            if data.startup_log_toolmanager:
                print(f"[startup] toolmanager.py -> add_tool().finish()")
            if callback is not None:
                callback(_toolmanObj, callbackArg)
            return

        def abort(
            show_error: bool = True,
            reason: Optional[str] = None,
            *args,
        ) -> None:
            if data.startup_log_toolmanager:
                print(f"[startup] toolmanager.py -> add_tool().abort()")
            if wiz is not None:
                # clean info lines
                #   -> happens externally based on callback value!
                pass
            elif show_error:
                purefunctions.printc(
                    f"\nWARNING: Cannot add tool with \n"
                    f"    exekind = {exekind}\n"
                    f"    dirpath = {dirpath}\n"
                    f"    exepath = {exepath}\n",
                    color="warning",
                )
                if reason is not None:
                    print(f"    For the following reason:\n" f"{reason}")
            if callback is not None:
                callback(None, callbackArg)
            return

        # * ----------------------------[ Start ]----------------------------- *#
        # Analyze parameter 'dirpath_or_exepath'
        if (dirpath_or_exepath is None) or (
            dirpath_or_exepath.lower() == "none"
        ):
            abort(
                show_error=True,
                reason=f"        The parameter given to add_tool() is:\n"
                f"        {dirpath_or_exepath}\n",
            )
            return

        # & Directory
        if os.path.isdir(dirpath_or_exepath):
            dirpath = dirpath_or_exepath
            exekind, exepath = _v_.VersionExtractor().extract_executable(
                dirpath
            )
            if (exekind is None) or (exekind.lower() == "none"):
                abort(
                    show_error=True,
                    reason=str(
                        f"        The parameter given to add_tool() is:\n"
                        f"        {dirpath_or_exepath}\n"
                        f"        and is recognized as a directory.\n"
                        f"        extract_executable({dirpath}) returns:\n"
                        f"        exekind = {exekind}\n"
                        f"        exepath = {exepath}\n"
                    ),
                )
                return
            if (exepath is None) or (exepath.lower() == "none"):
                abort(
                    show_error=True,
                    reason=str(
                        f"        The parameter given to add_tool() is:\n"
                        f"        {dirpath_or_exepath}\n"
                        f"        and is recognized as a directory.\n"
                        f"        extract_executable({dirpath}) returns:\n"
                        f"        exekind = {exekind}\n"
                        f"        exepath = {exepath}\n"
                    ),
                )
                return

        # & File
        elif os.path.isfile(dirpath_or_exepath):
            exepath = dirpath_or_exepath
            exename = exepath.split("/")[-1]
            dirpath = os.path.dirname(exepath).replace("\\", "/")
            if dirpath.endswith("/"):
                dirpath = dirpath[0:-1]
            if dirpath.endswith("/bin"):
                dirpath = dirpath[0:-4]
            p_toolchain = _v_.VersionExtractor().get_patterns(
                "COMPILER_TOOLCHAIN"
            )
            p_fdserver = _v_.VersionExtractor().get_patterns("FLASHTOOL")
            p_buildauto = _v_.VersionExtractor().get_patterns(
                "BUILD_AUTOMATION"
            )
            for p in p_fdserver:
                if _fn_.fnmatch(name=exename, pat=p):
                    exekind = "FLASHTOOL"
            for p in p_buildauto:
                if _fn_.fnmatch(name=exename, pat=p):
                    exekind = "BUILD_AUTOMATION"
            for p in p_toolchain:
                if _fn_.fnmatch(name=exename, pat=p):
                    exekind = "COMPILER_TOOLCHAIN"
            if exekind is None:
                for p in p_fdserver:
                    if _fn_.fnmatch(name=exepath, pat=p):
                        exekind = "FLASHTOOL"
                for p in p_buildauto:
                    if _fn_.fnmatch(name=exepath, pat=p):
                        exekind = "BUILD_AUTOMATION"
                for p in p_toolchain:
                    if _fn_.fnmatch(name=exepath, pat=p):
                        exekind = "COMPILER_TOOLCHAIN"
            if exekind is None:
                abort(
                    show_error=True,
                    reason=str(
                        f"        The parameter given to add_tool() is:\n"
                        f"        {dirpath_or_exepath}\n"
                        f"        and is recognized as a file.\n"
                        f"        the filename and filepath don{q}t match"
                        f"        with any of the known patterns."
                    ),
                )
                return

        # & No file or directory
        else:
            abort(
                show_error=True,
                reason=str(
                    f"        The parameter given to add_tool() is:\n"
                    f"        {dirpath_or_exepath}\n"
                    f"        and is not a directory, nor a file."
                ),
            )
            return
        assert dirpath is not None
        assert exepath is not None
        assert exekind is not None

        # * ---------------------[ Create ToolmanObj() ]---------------------- *#
        if data.startup_log_toolmanager:
            print(f"[startup] toolmanager.py -> add_tool().create_toolmanObj()")

        toolmanObj: Optional[_tool_obj_.ToolmanObj] = None
        if exekind == "FLASHTOOL":
            toolmanObj = _tool_obj_.ToolmanObj(
                cat_unic=_toolcat_unicum_.TOOLCAT_UNIC("FLASHTOOL"),
                abspath=exepath,
            )
        if exekind == "COMPILER_TOOLCHAIN":
            toolmanObj = _tool_obj_.ToolmanObj(
                cat_unic=_toolcat_unicum_.TOOLCAT_UNIC("COMPILER_TOOLCHAIN"),
                abspath=exepath,  #!!
            )
        if exekind == "BUILD_AUTOMATION":
            toolmanObj = _tool_obj_.ToolmanObj(
                cat_unic=_toolcat_unicum_.TOOLCAT_UNIC("BUILD_AUTOMATION"),
                abspath=exepath,
            )
        if toolmanObj is None:
            abort(
                show_error=True,
                reason=str(
                    f"        The parameter given to add_tool() is:\n"
                    f"        {dirpath_or_exepath}\n"
                    f"        The tool category is: {exekind}, which\n"
                    f"        was not recognized.\n"
                ),
            )
            return

        toolmanObj.refresh_version_info(
            callback=check_tool_version,
            callbackArg=toolmanObj,
        )
        return

    def list_unique_ids(self, cat_name: str) -> List[str]:
        """List all local unique_ids (eg.

        ['openocd_0.10.0_dev00973_32b', 'openocd_0.10.0_dev01138_64b'] ) from
        the given tool category (eg. 'FLASHTOOL')
        """
        unique_id_list = []
        for _catname_, _tooldict_ in self._tp_nesteddict_.items():
            if _catname_.lower() == cat_name.lower():
                for unique_id, toolmanObj in _tooldict_.items():
                    unique_id_list.append(unique_id)
        if cat_name == "FLASHTOOL":
            unique_id_list.append("built_in")
            unique_id_list.append("avrdude")
        return unique_id_list

    def get_toolmanobj(self, unique_id: str) -> Optional[_tool_obj_.ToolmanObj]:
        """Get ToolmanObj() matching the given unique_id."""
        if unique_id is None:
            return None
        for _catname_, _tooldict_ in self._tp_nesteddict_.items():
            for uid, toolmanObj in _tooldict_.items():
                if uid.lower() == unique_id.lower():
                    return toolmanObj
        return None

    def get_abspath(self, unique_id: str) -> Optional[str]:
        """Get abspath from the given unique_id."""
        if unique_id is None:
            return None
        for _catname_, _tooldict_ in self._tp_nesteddict_.items():
            for uid, toolmanObj in _tooldict_.items():
                if uid.lower() == unique_id.lower():
                    return toolmanObj.get_abspath()
        return None

    def get_toolfolder(self, unique_id: str) -> Optional[str]:
        """Get tool folder from the given unique_id."""
        if unique_id is None:
            return None
        for _catname_, _tooldict_ in self._tp_nesteddict_.items():
            for uid, toolmanObj in _tooldict_.items():
                if uid.lower() == unique_id.lower():
                    return toolmanObj.get_toolfolder()
        return None

    def get_toolprefix(self, unique_id: str) -> Optional[str]:
        """Get toolprefix from the given unique_id."""
        if unique_id is None:
            return None
        for _catname_, _tooldict_ in self._tp_nesteddict_.items():
            for _id, toolmanObj in _tooldict_.items():
                if _id.lower() == unique_id.lower():
                    assert _catname_.lower() == "compiler_toolchain"
                    return toolmanObj.get_toolprefix()
        return None

    def is_external(
        self,
        unique_id: Union[str, _tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
    ) -> bool:
        """Is abspath from given unique_id external to 'beetle_tools'?"""
        if unique_id is None:
            return True
        if isinstance(unique_id, str):
            for _catname_, _tooldict_ in self._tp_nesteddict_.items():
                for uid, toolmanObj in _tooldict_.items():
                    if (
                        (uid is not None)
                        and (uid.lower() != "none")
                        and (unique_id is not None)
                        and (unique_id.lower() != "none")
                        and (uid.lower() == unique_id.lower())
                    ):
                        if (toolmanObj.get_abspath() is None) or (
                            toolmanObj.get_abspath().lower() == "none"
                        ):
                            return True
                        return (
                            data.beetle_tools_directory
                            not in toolmanObj.get_abspath()
                        )
            # not found
            return True
        elif isinstance(unique_id, _tool_obj_.ToolmanObj) or isinstance(
            unique_id, _tool_obj_.ToolpathObj
        ):
            toolObj = unique_id
            if (toolObj.get_abspath() is None) or (
                toolObj.get_abspath().lower() == "none"
            ):
                return True
            return data.beetle_tools_directory not in toolObj.get_abspath()
        else:
            assert False
        return True

    def is_onpath(
        self,
        unique_id: Union[str, _tool_obj_.ToolmanObj],
    ) -> bool:
        """Is abspath from given unique_id external to 'beetle_tools'?"""
        path_list: List[str] = []
        temp_list: Optional[List[str]] = None
        if os_checker.is_os("windows"):
            temp_list = os.environ["PATH"].split(";")
        else:
            temp_list = os.environ["PATH"].split(":")
        for path in temp_list:
            path = path.replace("\\", "/")
            path = path.replace("//", "/")
            path_list.append(path)

        def onpath(_abspath: str) -> bool:
            for p in path_list:
                if not _abspath.startswith(p):
                    continue
                relpath: str = ""
                try:
                    relpath = _pp_.abs_to_rel(
                        rootpath=p,
                        abspath=_abspath,
                    )
                except:
                    traceback.print_exc()
                    continue
                if "/" in relpath:
                    continue
                return True
            return False

        if isinstance(unique_id, str):
            for _catname_, _tooldict_ in self._tp_nesteddict_.items():
                for uid, toolmanObj in _tooldict_.items():
                    if (
                        (uid is not None)
                        and (uid.lower() != "none")
                        and (unique_id is not None)
                        and (unique_id.lower() != "none")
                        and (uid.lower() == unique_id.lower())
                    ):
                        abspath = toolmanObj.get_abspath()
                        exepath = None
                        if (abspath is None) or (abspath.lower() == "none"):
                            return False
                        if not os.path.isfile(abspath):
                            (
                                exekind,
                                exepath,
                            ) = _v_.VersionExtractor().extract_executable(
                                dirpath=abspath
                            )
                        else:
                            exepath = abspath
                        return onpath(exepath)
            # not found
            return False

        elif isinstance(unique_id, _tool_obj_.ToolmanObj):
            toolmanObj = unique_id
            abspath = toolmanObj.get_abspath()
            exepath = None
            if (abspath is None) or (abspath.lower() == "none"):
                return False
            if not os.path.isfile(abspath):
                exekind, exepath = _v_.VersionExtractor().extract_executable(
                    dirpath=abspath
                )
            else:
                exepath = abspath
            return onpath(exepath)
        raise RuntimeError(
            f"did not recognize parameter for is_onpath({unique_id})"
        )

    def get_matching_iconpath(self, unique_id: str) -> str:
        """Get icon that matches the given 'unique_id'.

        If not a 'unique_id', a name is also sufficient.
        """
        if unique_id is None:
            return "icons/dialog/help.png"

        # $ Check for a match in the nested dictionary
        for _catname_, _tooldict_ in self._tp_nesteddict_.items():
            for uid, toolmanObj in _tooldict_.items():
                if (
                    (uid is not None)
                    and (uid.lower() != "none")
                    and (unique_id is not None)
                    and (unique_id.lower() != "none")
                    and (uid.lower() == unique_id.lower())
                ):
                    return toolmanObj.get_unique_id_iconpath()

        # $ Check for a match in the 'uid_pattern' from the tool categories
        for toolcat_name in _hardware_api_.HardwareDB().list_toolcat_unicums():
            toolcat_dict = _hardware_api_.HardwareDB().get_toolcat_dict(
                toolcat_name
            )
            for p in toolcat_dict["uid_pattern"].keys():
                if _fn_.fnmatch(name=unique_id.lower(), pat=p):
                    return toolcat_dict["uid_pattern"][p]["icon"]

        # $ No match
        purefunctions.printc(
            f"WARNING: Toolmanager().get_matching_iconpath({q}{unique_id}{q}) failed!",
            color="warning",
        )
        return "icons/dialog/help.png"

    def unique_id_exists(
        self,
        unique_id: str,
        bitness_matters: bool = True,
    ) -> bool:
        """Check if unique_id exists in the nested dictionary."""
        if unique_id is None:
            return False
        for _catname_, _tooldict_ in self._tp_nesteddict_.items():
            for uid, toolmanObj in _tooldict_.items():
                if uid.lower() == unique_id.lower():
                    return True
                if not bitness_matters:
                    _id_ = ""
                    if uid.endswith("_32b"):
                        _id_ = uid[0:-4] + "_64b"
                    elif uid.endswith("_64b"):
                        _id_ = uid[0:-4] + "_32b"
                    if _id_.lower() == unique_id.lower():
                        return True
        return False

    def get_matching_unique_id(self, unique_id: str) -> Optional[str]:
        """Get matching unique_id, ignoring the bitness."""
        if unique_id is None:
            return None
        for _catname_, _tooldict_ in self._tp_nesteddict_.items():
            for uid, toolmanObj in _tooldict_.items():
                if uid.lower() == unique_id.lower():
                    return uid
        for _catname_, _tooldict_ in self._tp_nesteddict_.items():
            for uid, toolmanObj in _tooldict_.items():
                assert uid.lower() != unique_id.lower()
                _id_ = ""
                if uid.endswith("_32b"):
                    _id_ = uid[0:-4] + "_64b"
                elif uid.endswith("_64b"):
                    _id_ = uid[0:-4] + "_32b"
                if _id_.lower() == unique_id.lower():
                    return uid
        return None

    def unique_id_exists_in_beetle_tools_folder(self, unique_id: str) -> bool:
        """Check if the tool with given 'unique_id' exists in the 'beetle_tools'
        folder."""
        if unique_id is None:
            return False
        abspath = self.get_abspath(unique_id)
        if (abspath is None) or (abspath.lower() == "none"):
            return False
        if data.beetle_tools_directory in abspath:
            return True
        return False

    def send_add_tool_blink_msg(self, category: str) -> None:
        """Push the Home Window on top, switch to the TOOLS tab and make the
        'Add tool' button blink."""
        if self.__mode != "project":
            raise RuntimeError()

        def switch_tab(*args) -> None:
            data.main_form.send("switch-tab tools")
            qt.QTimer.singleShot(150, blink)
            return

        def blink(*args) -> None:
            data.main_form.send(f"add_tool_blink({category})")
            return

        cast(
            "gui.forms.mainwindow.MainWindow", data.main_form
        ).open_home_window()
        qt.QTimer.singleShot(150, switch_tab)
        return

    def receive_add_tool_blink_msg(self, category: str) -> None:
        """Make the 'Add tool' button blink."""
        print(f"receive_add_tool_blink_msg({category})")
        if self.__mode != "home":
            raise RuntimeError()
        rootItem: Optional[
            Union[
                _toolchain_i_.ToolchainRootItem,
                _buildauto_i_.BuildAutomationRootItem,
                _probemid_i_.FlashToolRootItem,
            ]
        ] = None
        if category.upper() == "COMPILER_TOOLCHAIN":
            rootItem = self._v_rootItem_toolchain
        elif category.upper() == "BUILD_AUTOMATION":
            rootItem = self._v_rootItem_buildauto
        elif category.upper() == "FLASHTOOL":
            rootItem = self._v_rootItem_probemid
        else:
            raise RuntimeError()

        def open_rootItem(*args) -> None:
            if not rootItem.get_state().open:
                rootItem.open_later(
                    click=False,
                    callback=blink_addItem,
                    callbackArg=None,
                )
                return
            blink_addItem()
            return

        def blink_addItem(*args) -> None:
            addItem = rootItem.get_child_byName("AddItem")
            assert addItem is not None
            action_btn: _item_action_btn_.ItemActionBtn = cast(
                "_item_action_btn_.ItemActionBtn",
                addItem.get_widget(
                    key="itemActionBtn",
                ),
            )
            action_btn.blink(
                callback=nop,
                callbackArg=None,
            )
            return

        # * blink_rootItem
        btn: _item_btn_.ItemBtn = cast(
            "_item_btn_.ItemBtn",
            rootItem.get_widget(key="itemBtn"),
        )
        lbl: _item_lbl_.ItemLbl = cast(
            "_item_lbl_.ItemLbl",
            rootItem.get_widget(key="itemLbl"),
        )
        btn.blink(
            itemlbl=lbl,
            callback=open_rootItem,
            callbackArg=None,
        )
        return

    def send_add_tool_msg(self, dirpath_or_exepath: str) -> None:
        """Notify Project Window that a new tool has been added."""
        if not os.path.exists(dirpath_or_exepath):
            raise RuntimeError()
        data.main_form.send(f"add_tool({dirpath_or_exepath})")
        return

    def receive_add_tool_msg(self, dirpath_or_exepath: str) -> None:
        """Receive notification from Home Window that a new tool has been
        added."""
        if not os.path.exists(dirpath_or_exepath):
            raise RuntimeError()
        self.add_tool(
            dirpath_or_exepath=dirpath_or_exepath,
            wiz=None,
            callback=None,
            callbackArg=None,
        )
        return

    def send_delete_tool_msg(self, unique_id: str) -> None:
        """Notify Project Window that a tool has been deleted."""
        data.main_form.send(f"delete_tool({unique_id})")
        return

    def receive_delete_tool_msg(self, unique_id: str) -> None:
        """Receive notification from Home Window that a tool has been
        deleted."""
        print(f"{self.__mode}.receive_delete_tool_msg({unique_id})")
        toolmanObj = self.get_toolmanobj(unique_id)
        if toolmanObj is not None:
            if self.__mode == "home":
                self.delete_tool(
                    toolmanObj=toolmanObj,
                    callback=None,
                    callbackArg=None,
                )
            else:
                self.delete_tool_light(
                    unique_id=unique_id,
                    callback=None,
                    callbackArg=None,
                )
        return

    def filter_toollist(
        self,
        toolcat: str,
        toollist: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        """Filter toollist for a specific tool category."""
        if toolcat is None:
            purefunctions.printc(
                "ERROR: function filter_toollist() called with\n"
                "       None argument!\n",
                color="error",
            )
            return []
        resultlist = []
        if (toollist is None) or (not isinstance(toollist, list)):
            return []
        for tooldict in toollist:
            if (tooldict["kind"] is not None) and (
                tooldict["kind"].lower().replace(" ", "_")
                == toolcat.lower().replace(" ", "_")
            ):
                resultlist.append(copy.deepcopy(tooldict))
        return resultlist

    def filter_overlap(
        self, toollist1: List[Dict[str, str]], toollist2: List[Dict[str, str]]
    ) -> Tuple[
        List[Dict[str, str]],
        List[Dict[str, str]],
        List[Dict[str, str]],
    ]:
        """
        Start from two toollists and return three:
            > toollist1 - overlap
            > overlap
            > toollist2 - overlap
        """
        t1: List[Dict[str, str]] = []
        t2: List[Dict[str, str]] = []
        t3: List[Dict[str, str]] = []
        if (toollist1 is None) and (toollist2 is None):
            return [], [], []
        if toollist1 is None:
            return [], [], toollist2
        if toollist2 is None:
            return toollist1, [], []

        def has_overlap(unique_id):
            found1 = False
            found2 = False
            for _tooldict in toollist1:
                if _tooldict["unique_id"].lower() == unique_id:
                    found1 = True
                    break
            for _tooldict in toollist2:
                if _tooldict["unique_id"].lower() == unique_id:
                    found2 = True
                    break
            if found1 and found2:
                return True
            return False

        for tooldict in toollist1:
            if has_overlap(tooldict["unique_id"]):
                t2.append(copy.deepcopy(tooldict))
            else:
                t1.append(copy.deepcopy(tooldict))
        for tooldict in toollist2:
            if has_overlap(tooldict["unique_id"]):
                pass
            else:
                t3.append(copy.deepcopy(tooldict))
        return t1, t2, t3

    def idmatch(
        self,
        id1: Optional[str],
        id2: Optional[str],
    ) -> bool:
        """"""
        if (id1 is None) or (id2 is None):
            return False
        if (id1.lower() == "none") or (id2.lower() == "none"):
            return False
        if id1.lower() == id2.lower():
            return True
        if id1.lower()[0:-4] + "_32b" == id2.lower():
            return True
        if id1.lower()[0:-4] + "_64b" == id2.lower():
            return True
        return False

    def wizard_download_tool(
        self,
        remote_uid: str,
        parent_folder: str,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Download remote tool and add it to the Toolmanager().

        This function is intended to run at the end of a wizard.     >
        callback(success, callbackArg)
        """
        if data.startup_log_toolmanager:
            print(f"[startup] toolmanager.py -> wizard_download_tool()")

        tool_folder: Optional[str] = None  # directory where tool ends up, eg.
        # 'beetle_tools/gnu_make_4.2.0_32b'
        tool_url: str = serverfunctions.get_github_tool_url(remote_uid)
        is_replacement: bool = False

        def start_hdd_tool_replacement(*args) -> None:
            # & Start to download + replace the existing tool on the harddrive
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> wizard_download_tool().start_hdd_tool_replacement()"
                )
            assert threading.current_thread() is threading.main_thread()
            assert is_replacement == True
            nonlocal tool_folder
            abspath = self.get_abspath(remote_uid)
            if (abspath is None) or (abspath.lower() == "none"):
                abort(
                    f"wizard_download_tool().start_hdd_tool_replacement(1)<br>"
                    f"<br>"
                    f"The tool you{q}re trying to replace no longer exists:<br>"
                    f"<span style={dq}color:{q}#3465a4{q}{dq}>{q}{abspath}{q}</span><br>"
                )
                return
            if os.path.isfile(abspath):
                tool_folder = self.get_toolfolder(remote_uid)
            elif os.path.isdir(abspath):
                tool_folder = abspath
            else:
                abort(
                    f"wizard_download_tool().start_hdd_tool_replacement(2)<br>"
                    f"<br>"
                    f"The tool you{q}re trying to replace no longer exists:<br>"
                    f"<span style={dq}color:{q}#3465a4{q}{dq}>{q}{abspath}{q}</span><br>"
                )
                return
            if (tool_folder is None) or (tool_folder.lower() == "none"):
                abort(
                    f"wizard_download_tool().start_hdd_tool_replacement(3)<br>"
                    f"<br>"
                    f"Cannot replace the tool at:<br>"
                    f"<span style={dq}color:{q}#3465a4{q}{dq}>{q}{abspath}{q}</span><br>"
                )
                return
            _downloader_.Downloader().download_beetle_tool(
                tool_url=tool_url,
                tool_folder=tool_folder,
                is_replacement=True,
                callback=finish_download,
                callbackArg=None,
            )
            return

        def start_hdd_tool_addition(*args) -> None:
            # & Start to download + add the new tool to the harddrive
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> wizard_download_tool().start_hdd_tool_addition()"
                )
            assert threading.current_thread() is threading.main_thread()
            assert is_replacement == False
            nonlocal tool_folder
            if not os.path.isdir(parent_folder):
                abort(
                    f"wizard_download_tool().start_hdd_tool_addition()<br>"
                    f"<br>"
                    f"The target directory you selected doesn{q}t exist:<br>"
                    f"<span style={dq}color:{q}#3465a4{q}{dq}>&nbsp;&nbsp;&nbsp;&nbsp;"
                    f"{q}{parent_folder}{q}</span><br>"
                )
                return
            tool_folder = _pp_.rel_to_abs(
                rootpath=parent_folder, relpath=remote_uid
            )
            _downloader_.Downloader().download_beetle_tool(
                tool_url=tool_url,
                tool_folder=tool_folder,
                is_replacement=False,
                callback=finish_download,
                callbackArg=None,
            )
            return

        def finish_download(success: bool, *args) -> None:
            # & Finish the (clean and) download
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> wizard_download_tool().finish_download()"
                )
            assert threading.current_thread() is threading.main_thread()
            if not success:
                abort(f"wizard_download_tool().finish_download()<br>")
                return
            if self.unique_id_exists(remote_uid):
                assert is_replacement == True
                self.delete_tool_light(
                    unique_id=remote_uid,
                    callback=start_dict_tool_addition,
                    callbackArg=None,
                )
                return
            assert is_replacement == False
            start_dict_tool_addition(True)
            return

        def start_dict_tool_addition(success: bool, *args) -> None:
            # & Start to add the tool to the nested dictionary in toolman
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> wizard_download_tool().start_dict_tool_addition()"
                )
            assert threading.current_thread() is threading.main_thread()
            if not success:
                abort(f"wizard_download_tool().start_dict_tool_addition(1)<br>")
                return
            if (tool_folder is None) or (tool_folder.lower() == "none"):
                abort(f"wizard_download_tool().start_dict_tool_addition(2)<br>")
                return
            self.add_tool(
                dirpath_or_exepath=tool_folder,
                wiz=None,
                callback=finish,
                callbackArg=None,
            )
            return

        def abort(reason="", *args) -> None:
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> wizard_download_tool().abort()"
                )
            assert threading.current_thread() is threading.main_thread()
            gui.dialogs.popupdialog.PopupDialog.ok(
                title_text="ERROR",
                icon_path="icons/dialog/warning.png",
                text=str(
                    f"ERROR:<br>"
                    f"Adding tool failed:<br>"
                    f'<span style="color:#3465a4">{q}{remote_uid}{q}</span><br>'
                    f"<br>"
                    f"{reason}"
                ),
            )
            if callback is not None:
                callback(False, callbackArg)
            return

        def finish(toolmanObj: _tool_obj_.ToolmanObj, *args) -> None:
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> wizard_download_tool().finish()"
                )
            assert threading.current_thread() is threading.main_thread()
            if toolmanObj is None:
                abort(f"wizard_download_tool().finish(1)<br>")
                return
            try:
                self.send_add_tool_msg(tool_folder)
            except:
                traceback.print_exc()
                abort(
                    f"wizard_download_tool().finish(2)<br>"
                    + traceback.format_exc().replace("\n", "<br>")
                )
                return
            if toolmanObj.is_saved():
                try:
                    self.save_tools()
                except:
                    traceback.print_exc()
                    abort(
                        f"wizard_download_tool().finish(3)<br>"
                        + traceback.format_exc().replace("\n", "<br>")
                    )
                    return
            if callback is not None:
                callback(True, callbackArg)
            return

        # * Start
        assert threading.current_thread() is threading.main_thread()
        if self.unique_id_exists(remote_uid):
            is_replacement = True
            start_hdd_tool_replacement()
            return
        start_hdd_tool_addition()
        return

    def wizard_add_local_tool(
        self,
        dirpath_or_exepath: str,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Add local tool to the toolman.

        Function intended to run at the end of a wizard. > callback(success,
        unique_id, callbackArg)
        """
        if data.startup_log_toolmanager:
            print(f"[startup] toolmanager.py -> wizard_add_local_tool()")
        assert threading.current_thread() is threading.main_thread()

        def abort(reason="", *args) -> None:
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> wizard_add_local_tool().abort()"
                )
            assert threading.current_thread() is threading.main_thread()
            gui.dialogs.popupdialog.PopupDialog.ok(
                title_text="ERROR",
                icon_path="icons/dialog/warning.png",
                text=str(
                    f"ERROR:<br>"
                    f"Adding tool failed:<br>"
                    f'<span style="color:#3465a4">{q}{dirpath_or_exepath}{q}</span><br>'
                    f"<br>"
                    f"{reason}"
                ),
            )
            callback(False, None, callbackArg)
            return

        def finish(toolmanObj: Optional[_tool_obj_.ToolmanObj], *args) -> None:
            if data.startup_log_toolmanager:
                print(
                    f"[startup] toolmanager.py -> wizard_add_local_tool().finish()"
                )
            assert threading.current_thread() is threading.main_thread()
            if toolmanObj is None:
                print(">>> adding toolmanObj failed")
                abort(f"wizard_add_local_tool().finish(1)<br>")
                return
            try:
                self.send_add_tool_msg(dirpath_or_exepath)
            except:
                traceback.print_exc()
                abort(
                    f"wizard_add_local_tool().finish(2)<br>"
                    + traceback.format_exc().replace("\n", "<br>")
                )
                return
            try:
                self.save_tools()
            except:
                traceback.print_exc()
                abort(
                    f"wizard_add_local_tool().finish(3)<br>"
                    + traceback.format_exc().replace("\n", "<br>")
                )
                return
            gui.dialogs.popupdialog.PopupDialog.ok(
                title_text="FINISH",
                icon_path="icons/dialog/add.png",
                text=f"FINISH:<br>"
                f"Adding tool successful:<br>"
                f'<span style="color:#3465a4">&nbsp;&nbsp;&nbsp;&nbsp;'
                f"{q}{dirpath_or_exepath}{q}</span><br>",
            )
            callback(True, toolmanObj.get_unique_id(), callbackArg)
            return

        # * Start
        self.add_tool(
            dirpath_or_exepath=dirpath_or_exepath,
            wiz=None,
            callback=finish,
            callbackArg=None,
        )
        return
