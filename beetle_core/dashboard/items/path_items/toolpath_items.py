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
import traceback
import qt, data, functions, functools, project, weakref, purefunctions
import bpathlib.tool_obj as _tool_obj_
import project.segments.path_seg.toolpath_seg as _toolpath_seg_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_arrow as _cm_arrow_
import tree_widget.widgets.item_lbl as _cm_lbl_
import tree_widget.widgets.item_img as _cm_img_
import tree_widget.widgets.item_dropdown as _cm_dropdown_
import home_toolbox.items.info_items as _info_i_
import dashboard.items.item as _da_
import dashboard.contextmenus.toplvl_contextmenu as _da_toplvl_popup_
import dashboard.contextmenus.tool_contextmenu as _da_toolpath_popup_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_
import helpdocs.help_texts as _ht_
import fnmatch as _fn_
import bpathlib.path_power as _pp_
import hardware_api.toolcat_unicum as _toolcat_unicum_
import os_checker

if TYPE_CHECKING:
    import tree_widget.items.item as _item_
    import project.segments.chip_seg.chip as _chip_
    import project.segments.probe_seg.probe as _probe_
from various.kristofstuff import *

# ^                                         TOOL ROOT ITEM                                         ^#
# % ============================================================================================== %#
# % ToolRootItem()                                                                                 %#
# %                                                                                                %#


class ToolRootItem(_da_.Root):
    """Belongs to ToolpathSeg()"""

    class Status(_da_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: ToolRootItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = f"icons/folder/closed/laptop.png"
            self.openIconpath = f"icons/folder/open/laptop.png"
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

            def sync_self(*args) -> None:
                tool_rootitem: ToolRootItem = self.get_item()
                toolpath_seg: _toolpath_seg_.ToolpathSeg = (
                    tool_rootitem.get_projSegment()
                )
                self.lblTxt = "*Tools" if self.has_asterisk() else "Tools "
                self.closedIconpath = f"icons/folder/closed/tools.png"
                self.openIconpath = f"icons/folder/open/tools.png"
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

            # * Start
            if self.get_item() is None:
                callback(callbackArg) if callback is not None else nop()
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
            _da_.Folder.Status.sync_state(
                self,
                refreshlock=False,
                callback=sync_self,
                callbackArg=None,
            )
            return

    __slots__ = ()

    def __init__(
        self,
        toolpath_seg: _toolpath_seg_.ToolpathSeg,
    ) -> None:
        """"""
        assert isinstance(
            toolpath_seg,
            project.segments.path_seg.toolpath_seg.ToolpathSeg,
        )
        super().__init__(
            projSegment=toolpath_seg,
            name="ToolRootItem",
            state=ToolRootItem.Status(item=self),
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

    def rightclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _da_toplvl_popup_.ToplvlContextMenu(
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
            _ht_.tools_help()
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


# ^                                         TOOLPATH ITEM                                          ^#
# % ============================================================================================== %#
# % ToolpathItem()                                                                                 %#
# %                                                                                                %#


class ToolpathItem(_da_.Folder):
    """Belongs to a single ToolpathObj()"""

    class Status(_da_.Folder.Status):
        __slots__ = ("_first_run",)

        def __init__(self, item: ToolpathItem, name: str) -> None:
            """"""
            self._first_run = True
            super().__init__(item=item)
            return

        def __get_dropdown_elements(
            self,
            toolpath_obj: _tool_obj_.ToolpathObj,
            is_fake: bool,
            callback: Optional[Callable],
        ) -> None:
            """> callback( dropdown_elements, dropdown_selection,

            remote_toollist, )
            """
            probe: Optional[_probe_.Probe] = None
            chip: Optional[_chip_.Chip] = None
            if is_fake:
                probe = data.current_project.intro_wiz.get_fake_probe()
                chip = data.current_project.intro_wiz.get_fake_chip()
            else:
                probe = data.current_project.get_probe()
                chip = data.current_project.get_chip()
            dropdown_elements: List[Dict[str, Any]] = []

            # & Dropdown selection
            # The dropdown selection is normally the unique id as registered in the ToolpathObj() -
            # remember, the ToolpathSeg() stores one ToolpathObj() per category.
            # However, if this ToolpathItem() is being shown in the Intro Wizard (instead of the
            # Dashboard), it could be that the ToolpathObj() has no unique id stored. That's typi-
            # cally the case when you open a project for which you don't have the required tools
            # locally. The load() method from the ToolpathSeg() then clears the corresponding Tool-
            # pathObj() but stores the unique id in the project report!
            # For that reason, it's not sufficient to just rely on what is in the ToolpathObj() to
            # set the dropdown preselection of the Intro Wizard (because it can be cleared by that
            # ToolpathSeg().load() function). We need the project report here to do a proper pre-
            # selection.
            # Note: later on, in the acquire_remote_toollist() subfunction, we'll check if the uid
            # chosen for the dropdown_selection corresponds to any known tool - either local or
            # remote. If not, the dropdown selection will be cleared.
            dropdown_selection = toolpath_obj.get_unique_id()
            if (
                dropdown_selection is None
            ) or dropdown_selection.lower() == "none":
                try:
                    item: ToolpathItem = self.get_item()
                    if item._report is not None:
                        toolpath_obj: _tool_obj_.ToolpathObj = (
                            item.get_projSegment()
                        )
                        category: str = toolpath_obj.get_category().upper()
                        dropdown_selection = item._report["toolpath_report"][
                            category
                        ]["proj_uid"]
                except:
                    purefunctions.printc(
                        f"ERROR: Cannot properly preselect the dropdown widget for the tools in "
                        f"the Intro Wizard.",
                        color="error",
                    )
                    traceback.print_exc()

            local_toollist: Optional[List[Dict[str, str]]] = None
            local_toollist_filtered: Optional[List[Dict[str, str]]] = None

            def acquire_local_toollist(
                _local_toollist: List[Dict[str, str]], *args
            ) -> None:
                # Acquire the local toollist and store it in the nonlocal variable.
                nonlocal local_toollist
                local_toollist = _local_toollist
                data.toolman.get_remote_beetle_toollist(
                    toolcat=toolpath_obj.get_category(),
                    callback=acquire_remote_toollist,
                )
                return

            def acquire_remote_toollist(
                remote_toollist: List[Dict[str, str]], *args
            ) -> None:
                # Acquire the remote toollist and merge it with the local one.
                nonlocal local_toollist, local_toollist_filtered
                (
                    local_toollist_filtered,
                    overlap_toollist,
                    remote_toollist_filtered,
                ) = data.toolman.filter_overlap(
                    toollist1=local_toollist,
                    toollist2=remote_toollist,
                )
                for tooldict in remote_toollist_filtered:
                    tooldict["cloud_icon"] = "icons/gen/download.png"
                total_toollist = data.toolman.sort_toollist(
                    local_toollist_filtered
                    + overlap_toollist
                    + remote_toollist_filtered
                )

                # $ Check if dropdown selection is possible
                # Check if the dropdown selection (taken from the project report) corresponds to one
                # of the uids available locally and/or remotely. If that's the case, then the drop-
                # down selection variable can be kept (best to make it identical to the uid it cor-
                # responds to, because that's what the actual dropdown elements will be named like).
                nonlocal dropdown_selection
                for tooldict in total_toollist:
                    uid = tooldict.get("unique_id")
                    if (
                        (uid is not None)
                        and (dropdown_selection is not None)
                        and (uid.lower() == dropdown_selection.lower())
                    ):
                        dropdown_selection = uid
                        break
                    continue
                else:
                    # Try again, but without looking at bitness
                    for tooldict in total_toollist:
                        uid = tooldict.get("unique_id")
                        if (
                            (uid is not None)
                            and (dropdown_selection is not None)
                            and (
                                uid.lower()
                                .replace("-", "_")
                                .replace("_32b", "_64b")
                                == dropdown_selection.lower()
                                .replace("-", "_")
                                .replace("_32b", "_64b")
                            )
                        ):
                            dropdown_selection = uid
                            break
                        continue
                    else:
                        # No match found
                        dropdown_selection = None
                toolpath_obj.set_unique_id(dropdown_selection)

                # For each tooldict in the merged toollist, create and add a dropdown element.
                for tooldict in total_toollist:
                    dropdown_elements.append(
                        self.__get_dropdown_entry(
                            tooldict=tooldict,
                            toolpath_obj=toolpath_obj,
                            probe=probe,
                            chip=chip,
                        )
                    )

                # Create and add the final dropdown element.
                text_color = "default"
                dropdown_elements.append(
                    {
                        "name": "add_new_tool",
                        "widgets": [
                            {
                                "type": "image",
                                "icon-path": "icons/dialog/add.png",
                            },
                            {
                                "type": "text",
                                "text": "add new tool",
                                "color": text_color,
                            },
                        ],
                    }
                )

                # * Finish
                callback(
                    dropdown_elements,
                    dropdown_selection,
                )
                return

            # & Start
            data.toolman.get_local_beetle_toollist(
                toolcat=toolpath_obj.get_category(),
                callback=acquire_local_toollist,
            )
            return

        def __get_dropdown_entry(
            self,
            tooldict: Dict[str, str],
            toolpath_obj: _tool_obj_.ToolpathObj,
            probe: _probe_.Probe,
            chip: _chip_.Chip,
        ) -> Dict[str, Any]:
            """Get a dropdown entry for the given tooldict."""
            # $ Start creating dropdown entry
            uid = tooldict["unique_id"]
            iconpath = toolpath_obj.get_other_unique_id_iconpath(uid)

            default_color: str = "default"
            red_color: str = "red"
            text_color: str = default_color

            # $ Check compatibility
            if not self.__is_compatible(
                toolcat=toolpath_obj.get_category(),
                uid=uid,
                probe=probe,
                chip=chip,
                is_fake=None,
            ):
                iconpath = iconpath.replace(".png", "(err).png")
                text_color = red_color

            # $ Create dropdown entry
            icon_widget = {
                "type": "image",
                "icon-path": iconpath,
            }
            text_widget = {
                "type": "text",
                "text": uid,
                "color": text_color,
            }
            if "cloud_icon" in tooldict.keys():
                cloud_widget = {
                    "type": "image",
                    "icon-path": tooldict["cloud_icon"],
                }
                new_item = {
                    "name": uid,
                    "widgets": [icon_widget, text_widget, cloud_widget],
                }
            else:
                new_item = {
                    "name": uid,
                    "widgets": [icon_widget, text_widget],
                }
            return new_item

        def __is_compatible(
            self,
            toolcat: str,
            uid: str,
            probe: Optional[_probe_.Probe],
            chip: Optional[_chip_.Chip],
            is_fake: Optional[bool],
        ) -> bool:
            """Check compatibility of the tool represented by 'uid' with the
            given probe and chip.

            The probe and chip are either given directly, or they are derived
            from the 'is_fake' parameters.
            """
            toolcat = toolcat.upper()
            assert toolcat in (
                "FLASHTOOL",
                "COMPILER_TOOLCHAIN",
                "BUILD_AUTOMATION",
            ), f"toolcat = {toolcat}"

            # OPTION 1: 'probe' and 'chip' parameters are given directly. No need to derive them.
            if (probe is not None) and (chip is not None) and (is_fake is None):
                pass
            # OPTION 2: Derive the 'probe' and 'chip' parameters from 'is_fake'.
            elif (is_fake is not None) and (probe is None) and (chip is None):
                if is_fake:
                    probe = data.current_project.intro_wiz.get_fake_probe()
                    chip = data.current_project.intro_wiz.get_fake_chip()
                else:
                    probe = data.current_project.get_probe()
                    chip = data.current_project.get_chip()
            else:
                assert False

            # $ FLASHTOOL
            if toolcat == "FLASHTOOL":
                if not probe.is_compatible(uid):
                    return False
                if not chip.is_compatible_with_flashtool(uid):
                    return False
                return True

            # $ COMPILER TOOLCHAIN
            if toolcat == "COMPILER_TOOLCHAIN":
                if not chip.is_compatible_with_compiler_uid(uid):
                    return False
                return True

            # $ BUILD AUTOMATION
            assert toolcat == "BUILD_AUTOMATION"
            return True

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
            item: ToolpathItem = self.get_item()

            def finish(
                dropdown_elements: List[Dict[str, Any]],
                dropdown_selection: str,
            ) -> None:
                "Finish this function with a dropdown"
                self.dropdownElements = dropdown_elements
                self.dropdownSelection = dropdown_selection
                if refreshlock:
                    item.release_refresh_mutex()

                # & Intro Wizard
                # For the Intro Wizard, preselect the default tool if the current selection is None
                # or incompatible. However, this must *only* happen for the first run!
                if toolpath_seg.is_fake():
                    if self._first_run:
                        self._first_run = False
                        make_new_selection: bool = False
                        # $ Nothing selected
                        if (dropdown_selection is None) or (
                            dropdown_selection.lower() == "none"
                        ):
                            make_new_selection = True
                        # $ Something wrong selected
                        elif not self.__is_compatible(
                            toolcat=toolpath_obj.get_category(),
                            uid=dropdown_selection,
                            probe=None,
                            chip=None,
                            is_fake=True,
                        ):
                            make_new_selection = True
                        # $ Something good selected
                        else:
                            pass
                        # Preselect the default tool if needed. Then quit with a callback.
                        if make_new_selection:
                            cat_unic: _toolcat_unicum_.TOOLCAT_UNIC = (
                                _toolcat_unicum_.TOOLCAT_UNIC(
                                    toolpath_obj.get_category()
                                )
                            )
                            boardname: Optional[str] = None
                            chipname: Optional[str] = None
                            probename: Optional[str] = None
                            try:
                                boardname = (
                                    data.current_project.intro_wiz.get_fake_board().get_name()
                                )
                            except:
                                pass
                            try:
                                chipname = (
                                    data.current_project.intro_wiz.get_fake_chip().get_name()
                                )
                            except:
                                pass
                            try:
                                probename = (
                                    data.current_project.intro_wiz.get_fake_probe().get_name()
                                )
                            except:
                                pass
                            to_uid = cat_unic.get_default_unique_id(
                                boardname=boardname,
                                chipname=chipname,
                                probename=probename,
                            )
                            item.selection_changed_from_to(
                                from_uid=dropdown_selection,
                                to_uid=to_uid,
                                callback=callback,
                                callbackArg=callbackArg,
                            )
                            return
                    if callback is not None:
                        callback(callbackArg)
                    return

                # & Dashboard
                # No need to preselect anything.
                if callback is not None:
                    callback(callbackArg)
                return

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
            # $ ToolpathSeg()
            # A segment of the Project()-instance. The ToolpathSeg() keeps track of the tools. It is
            # represented in the dashboard through the ToolRootItem().
            toolpath_seg: _toolpath_seg_.ToolpathSeg = item.get_toolpath_seg()

            # $ ToolpathObj()
            # The ToolpathSeg() keeps one ToolpathObj() per category. Each of them is represented in
            # the dashboard by a ToolpathItem(). Remember: The ToolpathObj() is just a shell. It
            # only stores the 'unique_id' and the 'cat_unicum'. It will always look for the matching
            # ToolmanObj() to return vital info.
            toolpath_obj: _tool_obj_.ToolpathObj = item.get_projSegment()
            assert isinstance(toolpath_obj, _tool_obj_.ToolpathObj)

            # $ ToolmanObj()
            # The Toolmanager()-singleton keeps a ToolmanObj() per tool it
            # finds.
            toolman_obj: _tool_obj_.ToolmanObj = (
                toolpath_obj.get_matching_toolmanObj()
            )
            if toolman_obj is not None:
                assert isinstance(toolman_obj, _tool_obj_.ToolmanObj)
                if data.toolman.is_external(toolman_obj):
                    if data.toolman.is_onpath(toolman_obj):
                        toolman_obj.set_info_purple(True)
                        toolman_obj.set_info_blue(False)
                    else:
                        toolman_obj.set_info_purple(False)
                        toolman_obj.set_info_blue(True)
                else:
                    toolman_obj.set_info_purple(False)
                    toolman_obj.set_info_blue(False)

            # & Set status stuff
            self.set_asterisk(toolpath_obj.has_asterisk())
            self.set_relevant(toolpath_obj.is_relevant())
            self.set_readonly(toolpath_obj.is_readonly())
            self.set_warning(toolpath_obj.has_warning())
            self.set_error(toolpath_obj.has_error())
            self.set_info_purple(toolpath_obj.has_info_purple())
            self.set_info_blue(toolpath_obj.has_info_blue())
            if toolpath_seg.is_fake():
                self.set_warning(False)
                self.set_error(False)
            assert self.is_relevant() == True
            assert self.is_readonly() == False
            category = toolpath_obj.get_category().replace("_", " ").ljust(16)
            category_title = category.lower().title()

            # & Button
            self.closedIconpath = toolpath_obj.get_closedIconpath()
            self.openIconpath = toolpath_obj.get_openIconpath()

            # & Label
            if self.has_asterisk():
                self.lblTxt = str("*" + category_title + " ")
            else:
                self.lblTxt = str(category_title + "  ")
            self.lblTxt = self.lblTxt.ljust(20)

            # & Item image
            if self.has_info_purple():
                self.imgpath = "icons/dialog/info.png"
            else:
                self.imgpath = "icons/dialog/info.png"
            if self.get_item()._v_layout is not None:
                itemImg = self.get_item().get_widget(key="itemImg")
                if self.has_info_purple() or self.has_info_blue():
                    itemImg.show()
                else:
                    itemImg.hide()
            functions.assign_icon_err_warn_suffix(itemstatus=self)
            self.__get_dropdown_elements(
                toolpath_obj=toolpath_obj,
                is_fake=toolpath_seg.is_fake(),
                callback=finish,
            )
            return

    __slots__ = ("__toolpath_seg_ref", "_report")

    def __init__(
        self,
        toolpath_obj: _tool_obj_.ToolpathObj,
        toolpath_seg: _toolpath_seg_.ToolpathSeg,
        rootdir: Optional[_da_.Root],
        parent: Optional[_da_.Folder],
        report: Optional[Dict] = None,
    ) -> None:
        """This ToolpathItem() represents the given ToolpathObj() on the
        dashboard or Intro Wizard.

        The ToolpathSeg() is only kept as a weak reference. A project report is
        required if this ToolpathItem() represents a ToolpathObj() on the Intro
        Wizard (instead of the Dashboard). In that case, the unique id from the
        project report might be needed to prefill the dropdown menu.
        """
        assert isinstance(toolpath_obj, _tool_obj_.ToolpathObj)
        self.__toolpath_seg_ref = weakref.ref(toolpath_seg)
        self._report = report
        super().__init__(
            projSegment=toolpath_obj,
            rootdir=rootdir,
            parent=parent,
            name=toolpath_obj.get_category(),
            state=ToolpathItem.Status(
                item=self,
                name=toolpath_obj.get_category(),
            ),
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
        toolpath_obj: _tool_obj_.ToolpathObj = cast(
            _tool_obj_.ToolpathObj,
            self.get_projSegment(),
        )
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemArrow=_cm_arrow_.ItemArrow(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
            itemImg=_cm_img_.ItemImg(owner=self),
            itemDropdown=_cm_dropdown_.ItemDropdown(owner=self),
        )
        dropdown: _cm_dropdown_.ItemDropdown = self.get_widget("itemDropdown")
        dropdown.selection_changed_from_to.connect(
            self.selection_changed_from_to,
        )
        return

    def get_toolpath_seg(self) -> _toolpath_seg_.ToolpathSeg:
        """Return the ToolpathSeg()-instance from the Dashboard in which this
        ToolpathItem() lives."""
        if self.get_rootdir() is not None:
            tool_root_item = cast(
                ToolRootItem,
                self.get_rootdir(),
            )
            toolpath_seg = cast(
                _toolpath_seg_.ToolpathSeg,
                tool_root_item.get_projSegment(),
            )
            assert toolpath_seg == self.__toolpath_seg_ref()
        else:
            toolpath_seg = self.__toolpath_seg_ref()
        return toolpath_seg

    def selection_changed_from_to(
        self,
        from_uid: Optional[str],
        to_uid: Optional[str],
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Invoked when user changes selection in the ItemDropdown()-widget.

        :param from_uid: Unique ID of original tool
        :param to_uid: Unique ID of new tool
        """
        toolpath_seg: _toolpath_seg_.ToolpathSeg = self.get_toolpath_seg()
        toolpath_obj: _tool_obj_.ToolpathObj = cast(
            _tool_obj_.ToolpathObj,
            self.get_projSegment(),
        )
        category: str = toolpath_obj.get_category()

        def download_if_needed(*args) -> None:
            # $ Tool exists
            if data.toolman.unique_id_exists(
                unique_id=to_uid,
                bitness_matters=True,
            ):
                # No need to download
                switch_to_new_tool()
                return

            # $ Edge cases
            if (
                "built_in" in to_uid.lower()
                or "add local tool" in to_uid.lower()
                or "cannot connect" in to_uid.lower()
                or "select tool" in to_uid.lower()
                or to_uid.lower() == "empty"
            ):
                # No need to download
                switch_to_new_tool()
                return

            # $ Intro Wizard
            # For the intro wizard, do not download immediately! The tool will be downloaded at the
            # end.
            if toolpath_seg.is_fake():
                switch_to_new_tool()
                return

            # $ Download
            parent_folder = _pp_.rel_to_abs(
                rootpath=data.beetle_tools_directory,
                relpath=os_checker.get_os(),
            )
            if _ht_.ask_to_download_tool(
                uid=to_uid,
                beetle_tools_folder=parent_folder,
            ):
                data.toolman.wizard_download_tool(
                    remote_uid=to_uid,
                    parent_folder=parent_folder,
                    callback=download_finished,
                    callbackArg=None,
                )
                return
            download_finished(False)
            return

        def download_finished(success: bool, *args) -> None:
            if not success:
                # Refresh oneself such that the selection returns to what it
                # was before. No change of 'uid' has been given to the Tool-
                # pathSeg() anyhow.
                if self._v_emitter is not None:
                    self._v_emitter.refresh_sig.emit(False)
                finish()
                return
            switch_to_new_tool()
            return

        def switch_to_new_tool(*args) -> None:
            # Let the ToolpathSeg() take care of the switch. At some point, it gets back to this
            # ToolpathItem()-object to refresh it.
            self.get_toolpath_seg().change_unique_id(
                cat_name=category,
                unique_id=to_uid,
                history=True,
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args) -> None:
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        # $ Deal with 'to_uid' being None
        if (to_uid is None) or (to_uid.lower() == "none"):
            # Refresh oneself such that the selection returns to what it was before. No change of
            # 'uid' has been given to the ToolpathSeg() anyhow.
            if self._v_emitter is not None:
                self._v_emitter.refresh_sig.emit(False)
            finish()
            return

        # $ Deal with 'add new tool'
        if to_uid == "add_new_tool":
            data.toolman.send_add_tool_blink_msg(
                category,
            )
            # Refresh oneself such that the selection returns to what it was before. No change of
            # 'uid' has been given to the ToolpathSeg() anyhow.
            if self._v_emitter is not None:
                self._v_emitter.refresh_sig.emit(False)
            finish()
            return

        # $ Download if needed and then switch to the new tool
        download_if_needed()
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)

        def finish(*args):
            if len(self.get_childlist()) > 0:
                # 'toggle_open()' will lock the 'data.user_lock'. That's okay
                # because this is a direct user click.
                self.toggle_open()
                return
            self.show_contextmenu_itemBtn(event)
            return

        if len(self.get_childlist()) == 0:
            self.refill_children_later(
                callback=finish,
                callbackArg=None,
            )
            return
        finish()
        return

    def rightclick_itemBtn(
        self, event: qt.QMouseEvent, force: bool = False
    ) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)

        def finish(*args):
            if len(self.get_childlist()) > 0:
                # 'toggle_open()' will lock the 'data.user_lock'. That's okay
                # because this is a direct user click.
                self.toggle_open()
            else:
                self.show_contextmenu_itemBtn(event)
            return

        if len(self.get_childlist()) == 0:
            self.refill_children_later(
                callback=finish,
                callbackArg=None,
            )
            return
        finish()
        return

    def rightclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLineedit(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemLineedit(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLineedit(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemLineedit(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemImg(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemImg(event)
        toolpath_obj: _tool_obj_.ToolpathObj = cast(
            _tool_obj_.ToolpathObj,
            self.get_projSegment(),
        )
        unique_id: Optional[str] = toolpath_obj.get_unique_id()
        abspath: Optional[str] = toolpath_obj.get_abspath()
        if unique_id is None:
            return
        if data.toolman.is_external(unique_id):
            if data.toolman.is_onpath(unique_id):
                _ht_.tool_on_path(
                    toolpath_obj,
                )
            else:
                _ht_.tool_external(
                    toolpath_obj,
                )
        return

    def rightclick_itemImg(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemImg(event)
        toolpath_obj: _tool_obj_.ToolpathObj = cast(
            _tool_obj_.ToolpathObj,
            self.get_projSegment(),
        )
        unique_id: Optional[str] = toolpath_obj.get_unique_id()
        abspath: Optional[str] = toolpath_obj.get_abspath()
        if unique_id is None:
            return
        if data.toolman.is_external(unique_id):
            if data.toolman.is_onpath(unique_id):
                _ht_.tool_on_path(
                    toolpath_obj,
                )
            else:
                _ht_.tool_external(
                    toolpath_obj,
                )
        return

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        toolpath_obj: _tool_obj_.ToolpathObj = cast(
            _tool_obj_.ToolpathObj,
            self.get_projSegment(),
        )
        contextmenu = _da_toolpath_popup_.ToolContextMenu(
            widg=itemBtn,
            item=self,
            toplvl_key="itemBtn",
            clickfunc=self.contextmenuclick_itemBtn,
            toolpathObj=toolpath_obj,
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
        toolpath_obj: _tool_obj_.ToolpathObj = cast(
            _tool_obj_.ToolpathObj,
            self.get_projSegment(),
        )

        def navigate(_key: str) -> None:
            "Navigate to current tool"
            abspath: str = toolpath_obj.get_abspath()
            if (abspath is None) or (abspath.lower() == "none"):
                return
            data.dashboard.dashboard_open_file(self)
            return

        def path(_key: str) -> None:
            "Show path of current tool"
            # Path already copied by the PopupcompPath()-instance itself.
            pass

        def _help(_key: str) -> None:
            "Show helptext"
            if toolpath_obj.get_category() == "COMPILER_TOOLCHAIN":
                _ht_.toolchain_help()
            if toolpath_obj.get_category() == "BUILD_AUTOMATION":
                _ht_.buildautomation_help()
            if toolpath_obj.get_category() == "FLASHTOOL":
                _ht_.flashtool_help()
            return

        funcs = {
            "navigate": navigate,
            "path": path,
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return

    def kill_children_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Kill all children recursively."""
        super().kill_children_later(callback, callbackArg)
        return

    def refill_children_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Add the info-children."""
        toolpath_obj: _tool_obj_.ToolpathObj = cast(
            _tool_obj_.ToolpathObj,
            self.get_projSegment(),
        )
        rootItem = self.get_rootdir()

        def add_children(
            childiter: Iterator[Union[_item_.Folder, _item_.File]],
        ) -> None:
            try:
                child: Union[_item_.Folder, _item_.File] = next(childiter)
            except StopIteration:
                if callback is not None:
                    callback(callbackArg)
                return
            self.add_child(
                child=child,
                alpha_order=False,
                show=True,
                callback=add_children,
                callbackArg=childiter,
            )
            return

        # * Start
        childlist = []
        if toolpath_obj.get_unique_id() is None:
            pass
        elif (toolpath_obj.get_category() == "FLASHTOOL") and _fn_.fnmatch(
            name=toolpath_obj.get_unique_id().lower(), pat="*built*in*"
        ):
            # special case: blackmagic probe
            childlist.append(
                _info_i_.UniqueIDNameItem(
                    toolObj=toolpath_obj, rootdir=rootItem, parent=self
                )
            )
            childlist.append(
                _info_i_.UniqueIDItem(
                    toolObj=toolpath_obj, rootdir=rootItem, parent=self
                )
            )
        else:
            # all other tools
            childlist.append(
                _info_i_.UniqueIDNameItem(
                    toolObj=toolpath_obj, rootdir=rootItem, parent=self
                )
            )
            childlist.append(
                _info_i_.UniqueIDItem(
                    toolObj=toolpath_obj, rootdir=rootItem, parent=self
                )
            )
            childlist.append(
                _info_i_.VersionItem(
                    toolObj=toolpath_obj, rootdir=rootItem, parent=self
                )
            )
            childlist.append(
                _info_i_.BuilddateItem(
                    toolObj=toolpath_obj, rootdir=rootItem, parent=self
                )
            )
            childlist.append(
                _info_i_.BitnessItem(
                    toolObj=toolpath_obj, rootdir=rootItem, parent=self
                )
            )
            childlist.append(
                _info_i_.LocationItem(
                    toolObj=toolpath_obj, rootdir=rootItem, parent=self
                )
            )
            if toolpath_obj.get_category() == "COMPILER_TOOLCHAIN":
                # extra field for toolchain
                childlist.append(
                    _info_i_.ToolprefixItem(
                        toolObj=toolpath_obj,
                        rootdir=rootItem,
                        parent=toolpath_obj.get_toolmanItem(),
                    ),
                )
        add_children(iter(childlist))
        return
