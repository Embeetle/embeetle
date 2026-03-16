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
import os, difflib, math, functools, weakref
import qt, data, purefunctions, functions, gui, project
import gui.helpers.various
import bpathlib.path_power as _pp_
import bpathlib.treepath_obj as _treepath_obj_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_arrow as _cm_arrow_
import tree_widget.widgets.item_lbl as _cm_lbl_
import tree_widget.widgets.item_lineedit as _cm_lineedit_
import tree_widget.widgets.item_img as _cm_img_
import dashboard.items.item as _da_
import dashboard.contextmenus.toplvl_contextmenu as _da_toplvl_popup_
import dashboard.contextmenus.treepath_contextmenu as _da_treepath_popup_
import hardware_api.file_generator as _file_generator_
import project_generator.generator.file_changer as _fc_
import helpdocs.help_texts as _ht_
import dashboard.items.path_items.treepath_item_helper as _treepath_item_helper_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_
import components.newfiletreehandler as _newfiletreehandler_
import hardware_api.toolcat_unicum as _toolcat_unicum_

TYPE_CHECKING = False
if TYPE_CHECKING:
    import project.segments.path_seg.treepath_seg as _treepath_seg_
    import gui.dialogs
    import gui.dialogs.popupdialog
from various.kristofstuff import *


class TreepathRootItem(_da_.Root):
    """Belongs to TreepathSeg()"""

    class Status(_da_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: TreepathRootItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = f"icons/folder/closed/tree.png"
            self.openIconpath = f"icons/folder/open/tree.png"
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
            treepath_rootitem: TreepathRootItem = self.get_item()
            treepath_seg: _treepath_seg_.TreepathSeg = (
                treepath_rootitem.get_projSegment()
            )
            if self.has_asterisk():
                self.lblTxt = "*Project Layout"
            else:
                self.lblTxt = "Project Layout "
            functions.assign_icon_err_warn_suffix(itemstatus=self)

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(self, treepath_seg: _treepath_seg_.TreepathSeg) -> None:
        """Create a TreepathRootItem() to represent the given TreepathSeg() in
        the Dashboard."""
        assert isinstance(
            treepath_seg,
            project.segments.path_seg.treepath_seg.TreepathSeg,
        )
        super().__init__(
            projSegment=treepath_seg,
            name="TreepathRootItem",
            state=TreepathRootItem.Status(item=self),
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

    def show_contextmenu_itemBtn(
        self, event: Union[qt.QMouseEvent, qt.QEvent]
    ) -> None:
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

        def _help(_key: str) -> None:
            _ht_.treepaths_help()
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


class TreepathItem(_da_.Folder):
    """Belongs to a single TreepathObj()"""

    class Status(_da_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: TreepathItem) -> None:
            """"""
            super().__init__(item=item)
            return

        # def __get_dropdown_elements(self,
        #                             treepath_obj:_treepath_obj_.TreepathObj,
        #                             treepath_seg:_treepath_seg_.TreepathSeg,
        #                             callback:Callable,
        #                             ) -> None:
        #     '''
        #     > callback(dropdown_elements, dropdown_selection)
        #     '''
        #     # Figure out current selection
        #     # TODO: Figure out
        #     dropdown_selection:Optional[str] = '<project>'
        #     # Fill dropdown elements
        #     dropdown_elements:List[Dict] = []
        #     color = 'default'
        #     if (treepath_obj.get_name() == 'DASHBOARD_MK') or \
        #             (treepath_obj.get_name() == 'FILETREE_MK'):
        #         color = 'green'
        #     for rootid in data.current_project.get_all_rootids(True, False):
        #         dropdown_elements.append(
        #             {
        #                 'name' : rootid,
        #                 'widgets' : [
        #                     {
        #                         'type'  : 'text',
        #                         'text'  : rootid,
        #                         'color' : color,
        #                     },
        #                 ]
        #             }
        #         )
        #     # Finish
        #     callback(dropdown_elements, dropdown_selection)
        #     return

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
            item: TreepathItem = self.get_item()

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

            # def finish(dropdown_elements, dropdown_selection):
            #     self.dropdownElements  = dropdown_elements
            #     self.dropdownSelection = dropdown_selection
            #     if refreshlock:
            #         item.release_refresh_mutex()
            #     if callback is not None:
            #         callback(callbackArg)
            #     return

            def finish(*args) -> None:
                if refreshlock:
                    item.release_refresh_mutex()
                if callback is not None:
                    callback(callbackArg)
                return

            # * Sync self
            treepath_obj = item.get_treepath_obj()
            treepath_seg = item.get_treepath_seg()
            self.set_asterisk(treepath_obj.has_asterisk())
            self.set_relevant(treepath_obj.is_relevant())
            self.set_readonly(treepath_obj.is_readonly())
            self.set_warning(treepath_obj.has_warning())
            self.set_error(treepath_obj.has_error())
            self.set_info_purple(treepath_obj.has_info_purple())
            self.set_info_blue(treepath_obj.has_info_blue())
            assert self.has_info_purple() == False
            assert self.has_info_blue() == False
            self.closedIconpath = treepath_obj.get_closedIconpath()
            self.openIconpath = treepath_obj.get_openIconpath()
            functions.assign_icon_err_warn_suffix(itemstatus=self)
            max_len = 0
            for _treepath_obj in treepath_seg.get_treepath_obj_list():
                if not _treepath_obj.is_relevant():
                    continue
                if len(_treepath_obj.get_name()) > max_len:
                    max_len = len(_treepath_obj.get_name())
                continue
            name = treepath_obj.get_name().ljust(max_len)
            if self.has_asterisk():
                self.lblTxt = str("*" + name)
            else:
                self.lblTxt = str(name + " ")

            # $ Set textfield
            abspath = treepath_obj.get_abspath()
            relpath = treepath_obj.get_relpath()
            rootid = treepath_obj.get_rootid()
            rootid_stripped = rootid.replace("<", "").replace(">", "")
            if (relpath is None) or (relpath.lower() == "none"):
                self.lineeditTxt = "None"
            elif relpath == ".":
                self.lineeditTxt = "."
            else:
                self.lineeditTxt = relpath
            # self.richLblTxt = '/'
            self.imgpath = "icons/gen/gear.png"

            # $ Set tooltip
            is_file = treepath_obj.is_file()
            if (relpath is None) or (relpath.lower() == "none"):
                self.tooltip = f"Click to select a "
                if is_file:
                    self.tooltip += "file"
                else:
                    self.tooltip += "folder"
            else:
                self.tooltip = f"{q}{abspath}{q}"

            # * Finish
            # self.__get_dropdown_elements(
            #     treepath_obj = treepath_obj,
            #     treepath_seg = treepath_seg,
            #     callback     = finish,
            # )
            finish()
            return

    __slots__ = (
        "__treepath_seg_ref",
        "__enter_pressed_mutex",
    )

    def __init__(
        self,
        treepath_obj: _treepath_obj_.TreepathObj,
        treepath_seg: _treepath_seg_.TreepathSeg,
        rootdir: Optional[_da_.Root],
        parent: Optional[_da_.Folder],
    ) -> None:
        """Create a TreepathItem() to represent a single TreepathObj() in the
        Dashboard.

        NOTE:
        The TreepathObj() belongs to a specific TreepathSeg() and therefore also to a specific en-
        vironment!
        """
        assert isinstance(treepath_obj, _treepath_obj_.TreepathObj)
        self.__treepath_seg_ref = weakref.ref(treepath_seg)
        super().__init__(
            projSegment=treepath_obj,
            rootdir=rootdir,
            parent=parent,
            name=treepath_obj.get_name(),
            state=TreepathItem.Status(item=self),
        )
        self.__enter_pressed_mutex = threading.Lock()
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
        itemArrow = None
        if (self.get_childlist() is not None) and (
            len(self.get_childlist()) > 0
        ):
            itemArrow = _cm_arrow_.ItemArrow(owner=self)
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemArrow=itemArrow,
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
            # itemDropdown = _cm_dropdown_.ItemDropdown(owner=self),
            # itemRichLbl  = _cm_item_richlbl_.ItemRichLbl(owner=self),
            itemLineedit=_cm_lineedit_.ItemLineedit(owner=self),
            itemImg=_cm_img_.ItemImg(owner=self),
        )
        # dropdown:_cm_dropdown_.ItemDropdown = self.get_widget('itemDropdown')
        # richlbl:_cm_item_richlbl_.ItemRichLbl = self.get_widget('itemRichLbl')
        lineedit: _cm_lineedit_.ItemLineedit = self.get_widget("itemLineedit")
        img: _cm_img_.ItemImg = self.get_widget("itemImg")
        # dropdown.selection_changed_from_to.connect(
        #     self.selection_changed_from_to,
        # )
        if hasattr(self, "get_childlist"):
            if (self.get_childlist() is None) or (
                len(self.get_childlist()) == 0
            ):
                pass
            else:
                # dropdown.hide()
                # richlbl.hide()
                lineedit.hide()
                img.hide()
        lineedit.enter_pressed_signal.connect(self.enter_pressed_itemLineedit)
        lineedit.key_pressed_signal.connect(self.key_pressed_itemLineedit)

        # Set QLineEdit() readonly and disable dropdown for 'dashboard.mk' and 'filetree.mk'
        treepath_obj = self.get_treepath_obj()
        self.get_state().lineeditReadOnly = False
        if (treepath_obj.get_name() == "DASHBOARD_MK") or (
            treepath_obj.get_name() == "FILETREE_MK"
        ):
            self.get_state().lineeditReadOnly = True
            lineedit.setProperty("gray", True)
            # dropdown.setEnabled(False)
            # dropdown.clicked.connect(_ht_.makefiles_together)
        return

    def __get_current_abspath(self) -> Optional[str]:
        """Get the abspath pointed to by the current text in the lineedit along
        with the current selection in the dropdown."""
        lineedit: _cm_lineedit_.ItemLineedit = self.get_widget("itemLineedit")
        # dropdown:_cm_dropdown_.ItemDropdown = self.get_widget('itemDropdown')
        # return _pp_.rel_to_abs(
        #     rootpath = data.current_project.get_rootpath_from_rootid(
        #         dropdown.get_selected_item_name()
        #     ),
        #     relpath = lineedit.text(),
        # )
        return _pp_.rel_to_abs(
            rootpath=data.current_project.get_proj_rootpath(),
            relpath=lineedit.text(),
        )

    def toggle_open(self) -> None:
        """"""
        # dropdown:_cm_dropdown_.ItemDropdown = self.get_widget('itemDropdown')
        # richlbl:_cm_item_richlbl_.ItemRichLbl = self.get_widget('itemRichLbl')
        lineedit: _cm_lineedit_.ItemLineedit = self.get_widget("itemLineedit")
        img: _cm_img_.ItemImg = self.get_widget("itemImg")
        if self.get_state().open:
            # Will be closed
            # dropdown.hide()
            # richlbl.hide()
            lineedit.hide()
            img.hide()
        else:
            # Will be opened
            # dropdown.show()
            # richlbl.show()
            lineedit.show()
            img.show()
        super().toggle_open()
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        self.__navigate_to()
        return

    def rightclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu(
            functions.get_position(event),
        )
        return

    def leftclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        self.__navigate_to()
        return

    def rightclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu(
            functions.get_position(event),
        )
        return

    def leftclick_itemLineedit(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemLineedit(event)
        treepath_obj = self.get_treepath_obj()
        if (treepath_obj.get_name() == "DASHBOARD_MK") or (
            treepath_obj.get_name() == "FILETREE_MK"
        ):
            _ht_.makefiles_together()
        return

    def rightclick_itemLineedit(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemLineedit(event)
        self.show_contextmenu(
            functions.get_position(event),
        )
        return

    def enter_pressed_itemLineedit(self, event: qt.QEvent) -> None:
        """User pressed enter."""
        abspath = self.__get_current_abspath()
        treepath_obj = self.get_treepath_obj()
        if abspath == treepath_obj.get_abspath():
            # Nothing to do.
            return

        def finish(success: bool = True, *args) -> None:
            # Change should have been completed.
            if not success:
                abort()
                return
            # Turn off the 'red' property which was potentially applied directly on the lineedit
            # during keystrokes. The text can still be displayed red through other means (if the
            # Status()-instance of this TreepathItem() registered an error).
            lineedit: _cm_lineedit_.ItemLineedit = self.get_widget(
                "itemLineedit"
            )
            if lineedit.property("red"):
                lineedit.setProperty("red", False)
                lineedit.style().unpolish(lineedit)
                lineedit.style().polish(lineedit)
            unlock()
            return

        def abort(*args) -> None:
            # Refresh to make sure both the dropdown and lineedit get reset to their original val-
            # ues. Turn off the 'red' property which was potentially applied directly on the line-
            # edit during keystrokes. The text can still be displayed red through other means (if
            # the Status()-instance of this TreepathItem() registered an error).
            lineedit: _cm_lineedit_.ItemLineedit = self.get_widget(
                "itemLineedit"
            )
            if lineedit.property("red"):
                lineedit.setProperty("red", False)
                lineedit.style().unpolish(lineedit)
                lineedit.style().polish(lineedit)
            self.refresh_later(
                refreshlock=True,
                force_stylesheet=False,
                callback=unlock,
                callbackArg=None,
            )
            return

        def unlock(*args) -> None:
            self.__enter_pressed_mutex.release()
            return

        if not self.__enter_pressed_mutex.acquire(blocking=False):
            return

        if abspath is None:
            # Something went wrong. Reset the values.
            abort()
            return
        if treepath_obj.is_default_fallback():
            # For the build artefacts, it doesn't matter if the file exists or
            # not. No need to check.
            pass
        elif not os.path.exists(abspath):
            # For other files, a warning must be shown if the file doesn't
            # exist.
            css = purefunctions.get_css_tags()
            blue = css["blue"]
            end = css["end"]
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/dialog/stop.png",
                title_text=f"File doesn{q}t exist",
                text=str(
                    f"what you entered:<br>"
                    f"{blue}{q}{abspath}{q}{end}<br>"
                    f"doesn{q}t exist!"
                ),
            )
            abort()
            return
        self.__select_location(
            autolocate=False,
            given_abspath=abspath,
            callback=finish,
        )
        return

    def focusout_itemLineedit(self, event: qt.QEvent) -> None:
        """User clicks somewhere else.

        If the text has been edited, this should count as if user pressed enter.
        """
        self.enter_pressed_itemLineedit(event)
        return

    def key_pressed_itemLineedit(self, event: qt.QEvent) -> None:
        """User pressed enter."""
        abspath = self.__get_current_abspath()
        lineedit: _cm_lineedit_.ItemLineedit = self.get_widget("itemLineedit")
        treepath_obj = self.get_treepath_obj()
        if os.path.exists(abspath) or treepath_obj.is_default_fallback():
            if lineedit.property("red"):
                lineedit.setProperty("red", False)
                lineedit.style().unpolish(lineedit)
                lineedit.style().polish(lineedit)
        else:
            if not lineedit.property("red"):
                lineedit.setProperty("red", True)
                lineedit.style().unpolish(lineedit)
                lineedit.style().polish(lineedit)
        return

    def leftclick_itemImg(self, event: qt.QMouseEvent) -> None:
        """"""
        img: _cm_img_.ItemImg = self.get_widget("itemImg")
        self.show_contextmenu(position=img.mapToGlobal(img.rect().bottomLeft()))
        return

    def rightclick_itemImg(self, event: qt.QMouseEvent) -> None:
        """"""
        img: _cm_img_.ItemImg = self.get_widget("itemImg")
        self.show_contextmenu(position=img.mapToGlobal(img.rect().bottomLeft()))
        return

    def get_treepath_obj(self) -> _treepath_obj_.TreepathObj:
        """"""
        treepath_obj = cast(
            _treepath_obj_.TreepathObj,
            self.get_projSegment(),
        )
        treepath_seg = self.get_treepath_seg()
        assert treepath_obj.is_fake() == treepath_seg.is_fake()
        return treepath_obj

    def get_treepath_seg(self) -> _treepath_seg_.TreepathSeg:
        """Return the TreepathSeg()-instance from the Dashboard in which this
        TreepathItem() lives."""
        if self.get_rootdir() is not None:
            treepath_root_item = cast(
                TreepathRootItem,
                self.get_rootdir(),
            )
            treepath_seg: _treepath_seg_.TreepathSeg = (
                treepath_root_item.get_projSegment()
            )
            assert treepath_seg == self.__treepath_seg_ref()
        else:
            treepath_seg = self.__treepath_seg_ref()
        return treepath_seg

    def __navigate_to(self) -> None:
        """Navigate in the Filetree to the file or folder represented by this
        TreepathItem() and open it in the editor.

        NOTE:
        This also works for external folders.
        """
        treepath_obj = self.get_treepath_obj()
        abspath = treepath_obj.get_abspath()
        if (abspath is None) or (abspath.lower() == "none"):
            return
        data.dashboard.dashboard_open_file(self)
        return

    def __select_location(
        self,
        autolocate: bool,
        given_abspath: Optional[str],
        callback: Optional[Callable],
    ) -> None:
        """Select the location of the represented PROJECT_LAYOUT item.

        The selected location is applied on the treepathObj and on the whole
        project as well (because from_intro_wiz == False)!
        """
        _treepath_item_helper_.select_location(
            self=self,
            autolocate=autolocate,
            given_abspath=given_abspath,
            callback=callback,
        )
        return

    def __create_build_folder(self) -> None:
        """Ask user what kind of build procedure he has (inline or shadow). In
        case of inline building, there is no point in making a new directory, so
        the BUILD_DIR entry will simply point to the toplevel project folder!

        In case of shadow, a new 'build/' subfolder will be created (if it not
        already existed).
        """
        _treepath_item_helper_.create_build_folder(
            self=self,
            callback=None,
            callbackArg=None,
        )
        return

    # def selection_changed_from_to(self,
    #                               from_rootid:str,
    #                               to_rootid:str,
    #                               ) -> None:
    #     '''
    #     Invoked when user changes selection in the ItemDropdown()-widget.
    #     :param from_rootid:    Original board name
    #     :param to_rootid:      New board name
    #     '''
    #     print(f'from_rootid: {from_rootid}, to_rootid: {to_rootid}')
    #     return

    def show_contextmenu(
        self,
        position: Optional[qt.QPoint] = None,
    ) -> None:
        """"""
        if position is None:
            position = functions.get_position(None)
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _da_treepath_popup_.TreepathContextMenu(
            widg=itemBtn,
            item=self,
            toplvl_key="itemBtn",
            clickfunc=self.contextmenuclick_itemBtn,
            treepathObj=self.get_treepath_obj(),
        )
        _contextmenu_launcher_.ContextMenuLauncher().launch_contextmenu(
            contextmenu=contextmenu,
            point=position,
            callback=None,
            callbackArg=None,
        )
        return

    def contextmenuclick_itemBtn(self, key, *args):
        """Context Menu click."""
        key = functions.strip_toplvl_key(key)
        treepath_obj = self.get_treepath_obj()
        if not treepath_obj.is_fake():
            super().contextmenuclick_itemBtn(key)

        def navigate(_key: str) -> None:
            self.__navigate_to()
            return

        def select_man(_key: str) -> None:
            self.__select_location(
                autolocate=False,
                given_abspath=None,
                callback=None,
            )
            return

        def autolocate(_key: str) -> None:
            self.__select_location(
                autolocate=True,
                given_abspath=None,
                callback=None,
            )
            return

        def new_build_folder(_key: str) -> None:
            self.__create_build_folder()
            return

        def path(_key: str) -> None:
            # Taken care of locally.
            pass

        def _help(_key: str) -> None:
            _ht_.show_treepathobj_info(treepath_obj)
            return

        def _reset(_key: str) -> None:
            self.__reset(
                callback=None,
                callbackArg=None,
            )
            return

        funcs = {
            "navigate": navigate,
            "path": path,
            "select_man": select_man,
            "select_auto": autolocate,
            "create_build_folder": new_build_folder,
            "reset": _reset,
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return

    def blink_everywhere(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Let this entry blink in the dashboard and the corresponding one in
        the filetree as well.

        Then open the file in the editor.
        """
        treepath_obj = self.get_treepath_obj()
        treepath_root_item: TreepathRootItem = cast(
            TreepathRootItem,
            self.get_rootdir(),
        )
        treepath_seg: _treepath_seg_.TreepathSeg = (
            treepath_root_item.get_projSegment()
        )
        name_unicum = treepath_obj.get_unicum()

        def blink_in_dashboard(*args) -> None:
            data.dashboard.go_to_item(
                abspath=f"TreepathRootItem/{name_unicum.get_name()}",
                callback1=None,
                callbackArg1=None,
                callback2=blink_in_filetree,
                callbackArg2=None,
            )
            return

        def blink_in_filetree(*args) -> None:
            abspath = treepath_obj.get_abspath()
            if (abspath is None) or (abspath.lower() == "none"):
                abort()
                return
            data.filetree.goto_path(abspath)
            finish()
            return

        def finish(*args) -> None:
            if callback is not None:
                callback(callbackArg)
            return

        def abort(*args) -> None:
            if callback is not None:
                callback(callbackArg)
            return

        blink_in_dashboard()
        return

    def __reset(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Reset the content of the corresponding TreepathObj() file to a fresh
        generated content."""
        treepath_obj = self.get_treepath_obj()
        treepath_unicum = treepath_obj.get_unicum()
        new_content: str = ""
        cur_content: str = ""
        diff = 0.0

        def acquire_new_content(*args) -> None:
            nonlocal new_content
            try:
                # $ makefile
                if treepath_unicum.get_name().upper() == "MAKEFILE":
                    new_content = _file_generator_.get_new_makefile(
                        boardname=data.current_project.get_board().get_name(),
                        chipname=data.current_project.get_chip().get_name(),
                        version=data.current_project.get_version_seg().get_version_nr(),
                    )
                # $ dashboard.mk
                elif treepath_unicum.get_name().upper() == "DASHBOARD_MK":
                    new_content = _file_generator_.get_new_dashboard_mk(
                        proj_rootpath=data.current_project.get_proj_rootpath(),
                        boardname=data.current_project.get_board().get_name(),
                        chipname=data.current_project.get_chip().get_name(),
                        probename=data.current_project.get_probe().get_name(),
                        toolprefix=data.current_project.get_toolpath_seg().get_compiler_toolchain_prefix(
                            absolute=False
                        ),
                        flashtool_exename=_toolcat_unicum_.TOOLCAT_UNIC(
                            "FLASHTOOL"
                        ).get_flashtool_exename(
                            unique_id=data.current_project.get_toolpath_seg().get_unique_id(
                                "FLASHTOOL"
                            )
                        ),
                        filepaths={
                            u: (
                                data.current_project.get_treepath_seg().get_abspath(
                                    u
                                )
                                if data.current_project.get_treepath_seg().is_relevant(
                                    u
                                )
                                else None
                            )
                            for u in data.current_project.get_treepath_seg().get_treepath_unicum_names()
                            if u
                            not in (
                                "BUTTONS_BTL",
                                "MAKEFILE",
                                "DASHBOARD_MK",
                                "FILETREE_MK",
                            )
                        },
                        repoints=None,
                        version=data.current_project.get_version_seg().get_version_nr(),
                    )
                # $ filetree.mk
                elif treepath_unicum.get_name().upper() == "FILETREE_MK":
                    try:
                        new_content = data.filetree.api.generate_filetree_mk(
                            template_only=False,
                            version=data.current_project.get_version_seg().get_version_nr(),
                        )
                    except:
                        new_content = _newfiletreehandler_.generate_makefile(
                            flat_tree_structure_copy={},
                            project_path=data.current_project.get_proj_rootpath(),
                            external_version=data.current_project.get_version_seg().get_version_nr(),
                            template_only=True,
                        )
                # $ openocd_chip.cfg
                elif treepath_unicum.get_name().upper() == "OPENOCD_CHIPFILE":
                    new_content = _file_generator_.get_new_openocd_chipcfg_file(
                        boardname=data.current_project.get_board().get_name(),
                        chipname=data.current_project.get_chip().get_name(),
                    )
                # $ openocd_probe.cfg
                elif treepath_unicum.get_name().upper() == "OPENOCD_PROBEFILE":
                    new_content = _file_generator_.get_new_openocd_probecfg_file(
                        boardname=data.current_project.get_board().get_name(),
                        chipname=data.current_project.get_chip().get_name(),
                        probename=data.current_project.get_probe().get_name(),
                        transport_protocol_name=data.current_project.get_probe().get_transport_protocol_name(),
                    )
                # $ linkerscript.ld
                elif treepath_unicum.get_name().upper() == "LINKERSCRIPT":
                    linkerscript_dict = _file_generator_.get_new_linkerscripts(
                        boardname=data.current_project.get_board().get_name(),
                        chipname=data.current_project.get_chip().get_name(),
                    )
                    new_content = linkerscript_dict[
                        list(linkerscript_dict.keys())[0]
                    ]
                # $ .gdbinit
                elif treepath_unicum.get_name().upper() == "GDB_FLASHFILE":
                    new_content = _file_generator_.get_new_gdbinit(
                        boardname=data.current_project.get_board().get_name(),
                        chipname=data.current_project.get_chip().get_name(),
                        probename=data.current_project.get_probe().get_name(),
                    )
                # $ buttons.btl
                elif treepath_unicum.get_name().upper() == "BUTTONS_BTL":
                    new_content = _file_generator_.get_new_buttonsbtl_file(
                        probename=data.current_project.get_probe().get_name(),
                    )
                # $ other files
                else:
                    raise RuntimeError()
            except:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    title_text="Reset config file",
                    icon_path="icons/dialog/info.png",
                    text=str(
                        f"Embeetle cannot generate content for the<br>"
                        f"{treepath_unicum.get_name()}<br>"
                    ),
                )
                abort()
                return
            acquire_cur_content()
            return

        def acquire_cur_content(*args) -> None:
            nonlocal cur_content
            abspath = treepath_obj.get_abspath()
            if (
                (abspath is None)
                or (abspath.lower() == "none")
                or (not os.path.isfile(abspath))
            ):
                gui.dialogs.popupdialog.PopupDialog.ok(
                    title_text="Reset config file",
                    icon_path="icons/dialog/info.png",
                    text=str(
                        f"You did not yet select a file to serve as your {treepath_unicum.get_name()}.<br>"
                        f"Click again on {treepath_unicum.get_name()} in the dashboard and choose<br>"
                        f"{q}Select{q} or {q}Autodetect{q}<br>"
                    ),
                )
                abort()
                return
            with open(
                abspath, "r", encoding="utf-8", newline="\n", errors="replace"
            ) as f:
                cur_content = f.read()
            cur_content = cur_content.replace("\r\n", "\n")
            compare_contents()
            return

        def compare_contents(*args) -> None:
            # & Compare 'cur_content' with 'new_content'
            nonlocal diff
            eq = difflib.SequenceMatcher(
                None,
                cur_content,
                new_content,
            ).ratio()
            if eq == 1.0:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    title_text="Reset config file",
                    icon_path="icons/dialog/info.png",
                    text=str(
                        f"Embeetle did not detect any changes in this config file,<br>"
                        f"so there is nothing to reset<br>"
                    ),
                )
                abort()
                return
            assert eq != 1.0
            diff = math.ceil(100000 * (1.0 - eq)) / 1000
            ask_permission()
            return

        def ask_permission(*args) -> None:
            modperm_dict = {
                treepath_unicum.get_name(): [
                    treepath_obj.get_abspath(),  # file abspath
                    f"{diff}%",  # diff
                    False,  # chbx state
                    False,  # conflicts
                    cur_content,  # current content
                    new_content,  # resulting content
                    False,  # manual mods
                ],
            }
            _ht_.ask_dashboard_permission(
                addperm_dict={},
                delperm_dict={},
                modperm_dict=modperm_dict,
                repperm_dict={},
                title_text=None,
                callback=apply,
            )
            return

        def apply(
            _addperm_dict_: Dict,
            _delperm_dict_: Dict,
            _modperm_dict_: Dict,
            _repperm_dict_: Dict,
            _diff_dialog_: Optional[gui.helpers.various.DiffDialog],
        ) -> None:
            # & Apply permitted changes
            if _diff_dialog_ is not None:
                _diff_dialog_.close()
            # $ User closed dialog with 'X' button
            if (
                (_addperm_dict_ is None)
                or (_delperm_dict_ is None)
                or (_modperm_dict_ is None)
                or (_repperm_dict_ is None)
            ):
                abort()
                return
            # $ User gave no permission
            perm = _modperm_dict_[treepath_unicum.get_name()][2]
            if not perm:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    title_text="Reset config file",
                    icon_path="icons/dialog/info.png",
                    text=str(
                        f"Embeetle did not touch your config file {treepath_unicum.get_name()}"
                    ),
                )
                abort()
                return
            # $ Apply new content
            abspath = treepath_obj.get_abspath()
            assert os.path.isfile(abspath)
            with open(abspath, "w", encoding="utf-8", newline="\n") as f:
                f.write(new_content)
            # Delete corresponding files in cache
            _fc_.FileChanger().delete_corresponding_original(abspath)
            self.blink_everywhere(
                callback=finish,
                callbackArg=None,
            )
            return

        def abort(*args) -> None:
            if callback is not None:
                callback(callbackArg)
            return

        def finish(*args) -> None:
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        # Do some basic checks
        if not treepath_obj.is_relevant():
            gui.dialogs.popupdialog.PopupDialog.ok(
                title_text="Reset config file",
                icon_path="icons/dialog/info.png",
                text=str(
                    f"The file {q}{treepath_unicum.get_name()}{q} is irrelevant in the<br>"
                    f"current configuration of your project. In other words,<br>"
                    f"the file is not being used - so there is no point in<br>"
                    f"generating content for it.<br>"
                ),
            )
            abort()
            return
        acquire_new_content()
        return
