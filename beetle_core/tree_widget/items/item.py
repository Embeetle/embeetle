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
import pprint, weakref, functools, threading, copy, re, traceback, sys
import qt, data, purefunctions
import bpathlib.path_power as _pp_
import tree_widget.helpers.item_emitter as _cm_emitter_
import tree_widget.helpers.item_layout as _cm_layout_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_

if TYPE_CHECKING:
    import tree_widget.chassis.chassis as _chassis_
    import tree_widget.chassis.chassis_body as _chassis_body_
    import tree_widget.widgets.item_widget as _iw_
    import tree_widget.widgets.item_arrow as _item_arrow_
    import tree_widget.widgets.item_btn as _item_btn_
    import tree_widget.widgets.item_action_btn as _item_action_btn_
    import tree_widget.widgets.item_chbx as _item_chbx_
    import tree_widget.widgets.item_img as _item_img_
    import tree_widget.widgets.item_lbl as _item_lbl_
    import tree_widget.widgets.item_lineedit as _item_lineedit_
    import tree_widget.widgets.item_progbar as _item_progbar_
    import tree_widget.widgets.item_richlbl as _item_richlbl_
    import tree_widget.widgets.item_dropdown as _item_dropdown_
    import dashboard.items.item as _dashboard_items_
    import dashboard.items.lib_items.lib_item_shared as _lib_item_shared_
    import sa_tab.items.item as _sa_tab_item_
    import gui.helpers.advancedcombobox as _advancedcombobox_
from components.decorators import ref
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    pass

from various.kristofstuff import *

# ^                                              ITEM                                              ^#
# % ============================================================================================== %#
# % Item is superclass for Folder() and File().                                                    %#
# %                                                                                                %#


class Item(object):
    class Status(object):
        __slots__ = (
            "dead",
            "itemRef",
            "showChbx",
            "closedIconpath",  # ItemBtn()      -> icon when closed
            "openIconpath",  # ItemBtn()      -> icon when open
            "action_iconpath",
            "action_txt",
            "action_icon_suffixes",
            "open",  # ItemBtn()      -> open directory OR file open in editor
            "busyBtn",  # ItemBtn()      -> busy button
            "richLblTxt",  # ItemRichLbl()  -> text
            "lblTxt",  # ItemLbl()      -> text
            "imgpath",  # ItemImg()      -> icon for image
            "lineeditTxt",  # ItemLineedit() -> text
            "lineeditReadOnly",  # ItemLineedit() -> read only
            "progbarMax",  # ItemProgbar()  -> maximum
            "progbarForm",  # ItemProgbar()  -> format
            "progbarVal",  # ItemProgbar()  -> value
            "progbarCol",  # ItemProgbar()  -> color
            "dropdownElements",  # ItemDropdown() -> elements
            "dropdownSelection",  # ItemDropdown() -> selected element
            "forcePolish",
            "asterisk",  # Put an asterisk.
            "error",  # Make red.
            "warning",  # Make orange.
            "info_purple",  # Make purple.
            "info_blue",  # Make blue.
            "relevant",  # Make gray if irrelevant.
            "readonly",  # Other icon if readonly.
            "tooltip",
            "icon_suffixes",
        )

        def __init__(
            self,
            item: Union[Item, _lib_item_shared_.LibItemShared],
        ) -> None:
            """"""
            assert isinstance(item, Item)
            self.dead: bool = False
            self.itemRef = weakref.ref(item)
            self.showChbx: bool = True
            self.closedIconpath: str = ""
            self.openIconpath: str = ""
            self.action_iconpath: str = ""
            self.action_txt: str = ""
            self.action_icon_suffixes: Set[str] = set()
            self.open: bool = False
            self.busyBtn: bool = False
            self.lblTxt: str = ""
            self.richLblTxt: str = ""
            self.imgpath: str = ""
            self.lineeditTxt: str = ""
            self.lineeditReadOnly: bool = True
            self.progbarMax: int = 100
            self.progbarForm: str = "%v"
            self.progbarVal: int = 0
            self.progbarCol: str = "blue"
            self.dropdownElements: List[Dict] = []
            self.dropdownSelection = None
            self.forcePolish: bool = False
            self.asterisk: bool = False
            self.error: bool = False
            self.warning: bool = False
            self.info_purple: bool = False
            self.info_blue: bool = False
            self.relevant: bool = True
            self.readonly: bool = False
            self.tooltip: Optional[str] = None
            self.icon_suffixes: Set[str] = set()
            return

        @ref
        def get_item(self) -> Union[
            Item,
            Folder,
            File,
            _dashboard_items_.Folder,
            _dashboard_items_.File,
            Any,
        ]:
            return self.itemRef  # noqa

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            WARNING:
            As this method doesn't do anything, I have omitted its invocation
            in the following spots:
             - 'filetree/items/item.py' -> Folder.Status.sync_state()
             - 'filetree/items/item.py' -> File.Status.sync_state()
             - 'filetree/items/item.py' -> Root.Status.sync_state()
             - 'dashboard/items/probe_items/probe_items.py' -> ...
             - 'dashboard/items/probe_items/probe_comportitem.py' -> ...
             - 'dashboard/items/chip_items/chip_items.py' -> ...
             - 'dashboard/items/board_items/board_items.py' -> ...
             - 'dashboard/items/path_items/treepath_items.py' -> ...
             - 'dashboard/items/path_items/toolpath_items.py' -> ...
             - 'home_toolbox/items/add_item.py' -> ...
            """
            assert refreshlock is False
            if callback is not None:
                callback(callbackArg)
            return

        def printout(self) -> Dict[str, Any]:
            """Return a dictionary representing this Status()-instance. The dict
            will be stringified and saved to 'filetree_config.btl' eventually.

            NOTE:
            Everything that shouldn't be saved must be eliminated first! Some elimination steps take
            place here, other refinements are done in the subclasses.

            NOTE:
            This 'printout()' method gets only invoked if needed. So only when the Item()-instance
            has anything worthwhile to save. The returned dict gets stringified as one line, and is
            put next to the relpath of the Item() in the 'filetree_config.btl' file.
            """
            originaldict = {
                k: getattr(self, k)
                for k in [
                    a
                    for a in dir(self)
                    if not a.startswith("__") and not callable(getattr(self, a))
                ]
            }
            mydict = copy.deepcopy(originaldict)
            del mydict["dead"]
            del mydict["showChbx"]
            del mydict["open"]
            del mydict["busyBtn"]
            del mydict["lblTxt"]
            del mydict["richLblTxt"]
            del mydict["imgpath"]
            del mydict["lineeditTxt"]
            del mydict["lineeditReadOnly"]
            del mydict["progbarMax"]
            del mydict["progbarForm"]
            del mydict["progbarVal"]
            del mydict["progbarCol"]
            del mydict["dropdownElements"]
            del mydict["dropdownSelection"]
            del mydict["forcePolish"]
            del mydict["asterisk"]
            del mydict["error"]
            del mydict["warning"]
            del mydict["info_purple"]
            del mydict["info_blue"]
            del mydict["relevant"]
            del mydict["active"]
            del mydict["readonly"]
            del mydict["tooltip"]
            del mydict["icon_suffixes"]
            del mydict["action_iconpath"]
            del mydict["action_txt"]
            del mydict["action_icon_suffixes"]
            return mydict

        def print_state(self) -> None:
            """"""
            originaldict = {
                k: getattr(self, k)
                for k in [
                    a
                    for a in dir(self)
                    if not a.startswith("__") and not callable(getattr(self, a))
                ]
            }
            pprint.pprint(originaldict)
            return

        def load(self, mydict: Dict) -> None:
            """"""
            for k in mydict:
                if hasattr(self, k):
                    value = copy.deepcopy(mydict[k])
                    try:
                        setattr(self, k, value)
                    except Exception as e:
                        print(e)
            return

        def self_destruct(self, death_already_checked: bool = False) -> None:
            """"""
            if not death_already_checked:
                if self.dead:
                    raise RuntimeError(f"Trying to kill Item().Status() twice!")
                self.dead = True

            self.showChbx = None
            self.closedIconpath = None
            self.openIconpath = None
            self.action_iconpath = None
            self.action_icon_suffixes = None
            self.action_txt = None
            self.open = None
            self.busyBtn = None
            self.lblTxt = None
            self.richLblTxt = None
            self.imgpath = None
            self.lineeditTxt = None
            self.lineeditReadOnly = None
            self.progbarMax = None
            self.progbarVal = None
            self.progbarCol = None
            self.dropdownElements = None
            self.dropdownSelection = None
            self.asterisk = None
            self.relevant = None
            self.readonly = None
            self.warning = None
            self.error = None
            self.info_purple = None
            self.info_blue = None
            self.tooltip = None
            return

        #! ------------ asterisk ------------ !#
        def set_asterisk(self, a: bool) -> None:
            assert isinstance(a, bool)
            self.asterisk = a
            return

        def has_asterisk(self) -> bool:
            "Propagates"
            if self.asterisk:
                return True
            myItem = self.get_item()
            if hasattr(myItem, "get_childlist"):
                if myItem.get_childlist() is not None:
                    for item in myItem.get_childlist():
                        if (
                            hasattr(item.get_state(), "has_asterisk")
                            and item.get_state().has_asterisk()
                        ):
                            return True
            return False

        #! ------------ relevant ------------ !#
        def set_relevant(self, r: bool) -> None:
            assert isinstance(r, bool)
            self.relevant = r
            return

        def is_relevant(self) -> bool:
            "Propagates"
            if self.relevant:
                return True
            myItem = self.get_item()
            if hasattr(myItem, "get_childlist"):
                if myItem.get_childlist() is not None:
                    for item in myItem.get_childlist():
                        if (
                            hasattr(item.get_state(), "is_relevant")
                            and item.get_state().is_relevant()
                        ):
                            return True
            return False

        #! ------------ readonly ------------ !#
        def set_readonly(self, r: bool) -> None:
            assert isinstance(r, bool)
            self.readonly = r
            return

        def is_readonly(self) -> bool:
            "Does not propagate"
            return self.readonly

        #! ------------- warning ------------ !#
        def set_warning(self, w: bool) -> None:
            assert isinstance(w, bool)
            self.warning = w
            return

        def has_warning(self) -> bool:
            "Propagates"
            if self.warning:
                return True
            myItem = self.get_item()
            if hasattr(myItem, "get_childlist"):
                if myItem.get_childlist() is not None:
                    for item in myItem.get_childlist():
                        if (
                            hasattr(item.get_state(), "has_warning")
                            and item.get_state().has_warning()
                        ):
                            return True
            return False

        #! ------------- error -------------- !#
        def set_error(self, e: bool) -> None:
            assert isinstance(e, bool)
            self.error = e
            return

        def has_error(self) -> bool:
            "Propagates"
            if self.error:
                return True
            myItem = self.get_item()
            if hasattr(myItem, "get_childlist"):
                if myItem.get_childlist() is not None:
                    for item in myItem.get_childlist():
                        if (
                            hasattr(item.get_state(), "has_error")
                            and item.get_state().has_error()
                        ):
                            return True
            return False

        #! ----------- info_purple ----------- !#
        def set_info_purple(self, i: bool) -> None:
            assert isinstance(i, bool)
            self.info_purple = i
            return

        def has_info_purple(self) -> bool:
            "Propagates"
            if self.info_purple:
                return True
            myItem = self.get_item()
            if hasattr(myItem, "get_childlist"):
                if myItem.get_childlist() is not None:
                    for item in myItem.get_childlist():
                        if (
                            hasattr(item.get_state(), "has_info_purple")
                            and item.get_state().has_info_purple()
                        ):
                            return True
            return False

        #! ------------ info_blue ------------ !#
        def set_info_blue(self, i: bool) -> None:
            assert isinstance(i, bool)
            self.info_blue = i
            return

        def has_info_blue(self) -> bool:
            "Propagates"
            if self.info_blue:
                return True
            myItem = self.get_item()
            if hasattr(myItem, "get_childlist"):
                if myItem.get_childlist() is not None:
                    for item in myItem.get_childlist():
                        if (
                            hasattr(item.get_state(), "has_info_blue")
                            and item.get_state().has_info_blue()
                        ):
                            return True
            return False

    __slots__ = (
        "dead",
        "_rootRef",  # Weak reference to Root()-instance.
        "_parentRef",  # Weak reference to parent Item()-object.
        "_name",
        "_state",
        "_v_layout",
        "_v_widgets",
        "_v_emitter",
        "_v_refreshMutex",
        "__weakref__",
        "_cntr",
    )

    def __init__(
        self,
        rootdir: Optional[Root],
        parent: Optional[Folder],
        name: str,
        state: Status,
    ) -> None:
        """
        The Item class is the superclass for: Dir, Root and File.

        An Item()-object itself can exist without GUI elements. All GUI elements are considered "volatile"
        attributes in the sense that:
            > They are stored in attributes starting with '_v_'.
            > They can be created on the fly when needed, just call item.init_guiVars() (*Note*).
            > You can delete them safely without affecting the Item()-object.

        An Item()-object without GUI elements cannot send signals, but it can receive them. A QObject can connect its
        signal to a non-QObject using a proxy object to pass on the signal. It actually does that by default.
        To send signals from an Item()-instance, you need to instantiate the ItemEmitter() and assign it to the
        _v_emitter attribute.

        *Note: The init_guiVars() method not only creates the GUI elements, but also pushes them to the main
               thread. This way, you can safely call this function from any thread without nasty surprises!

        :param rootdir: The Root()-instance at the top.       (*Note*)
        :param parent:  The parent directory.                 (*Note*)
        :param name:    The Item's name.
        :param state:   A Status()-instance to start from.

        *Note: Only a weak reference to these parameters get stored.

        """
        self.dead = False
        self._rootRef = weakref.ref(rootdir) if rootdir is not None else None
        self._parentRef = weakref.ref(parent) if parent is not None else None
        self._name: str = name
        self._state: Union[
            Item.Status,
            Folder.Status,
            File.Status,
            _dashboard_items_.Folder.Status,
            _dashboard_items_.File.Status,
            _sa_tab_item_.Folder.Status,
            _sa_tab_item_.File.Status,
        ] = state

        self._v_layout: Optional[
            Union[
                _cm_layout_.FolderLayout,
                _cm_layout_.FileLayout,
            ]
        ] = None
        self._v_widgets: Dict[
            str,
            Optional[
                Union[
                    _iw_.ItemWidget,
                    _item_btn_.ItemBtn,
                    _item_action_btn_.ItemActionBtn,
                    _item_arrow_.ItemArrow,
                    _item_chbx_.ItemChbx,
                    _item_dropdown_.ItemDropdown,
                    _item_img_.ItemImg,
                    _item_lbl_.ItemLbl,
                    _item_lineedit_.ItemLineedit,
                    _item_progbar_.ItemProgbar,
                    _item_richlbl_.ItemRichLbl,
                ]
            ],
        ] = {
            "itemBtn": None,
            "itemActionBtn": None,
            "itemArrow": None,
            "itemChbx": None,
            "cchbx": None,
            "hchbx": None,
            "hglass": None,
            "cfgchbx": None,
            "itemLbl": None,
            "itemDropdown": None,
            "itemRichLbl": None,
            "itemLineedit": None,
            "itemImg": None,
            "itemProgbar": None,
        }
        self._cntr: int = 0
        self._v_emitter: Optional[_cm_emitter_.ItemEmitter] = None
        self._v_refreshMutex: threading.Lock = threading.Lock()
        return

    def acquire_refresh_mutex(self) -> bool:
        # purefunctions.printc(f'Item({q}{self._name}{q}).acquire_refresh_mutex()', color='cyan')
        return self._v_refreshMutex.acquire(blocking=False)

    def release_refresh_mutex(self) -> None:
        # purefunctions.printc(f'Item({q}{self._name}{q}).release_refresh_mutex()', color='cyan')
        self._v_refreshMutex.release()
        return

    def get_state(self) -> Union[
        Item.Status,
        Folder.Status,
        File.Status,
        _dashboard_items_.Folder.Status,
        _dashboard_items_.File.Status,
    ]:
        return self._state

    """----------------------------------------------------------------------------"""
    """ 1. INITIALIZATIONS                                                         """
    """----------------------------------------------------------------------------"""

    def init_emitter(self) -> None:
        """Initialize the ItemEmitter()-instance, and push it to the main
        thread."""
        if self._v_emitter is not None:
            return
        try:
            self._v_emitter = _cm_emitter_.ItemEmitter(
                parent=self.get_rootdir().get_chassis_body(),
            )
        except Exception as e:
            self._v_emitter = _cm_emitter_.ItemEmitter(parent=None)
        if threading.current_thread() is not threading.main_thread():
            self._v_emitter.moveToThread(threading.main_thread())  # noqa

        self._v_emitter.refresh_connect.connect(
            self._v_emitter._refresh_connect_
        )
        self._v_emitter.refresh_connect.emit(self.refresh)
        self._v_emitter.refresh_later_connect.connect(
            self._v_emitter._refresh_later_connect_
        )
        self._v_emitter.refresh_later_connect.emit(self.refresh_later)
        self._v_emitter.refresh_recursive_later_connect.connect(
            self._v_emitter._refresh_recursive_later_connect_
        )
        self._v_emitter.refresh_recursive_later_connect.emit(
            self.refresh_recursive_later
        )

        self._v_emitter.rescale_connect.connect(
            self._v_emitter._rescale_connect_
        )
        self._v_emitter.rescale_connect.emit(self.rescale)
        self._v_emitter.rescale_later_connect.connect(
            self._v_emitter._rescale_later_connect_
        )
        self._v_emitter.rescale_later_connect.emit(self.rescale_later)
        self._v_emitter.rescale_recursive_later_connect.connect(
            self._v_emitter._rescale_recursive_later_connect_
        )
        self._v_emitter.rescale_recursive_later_connect.emit(
            self.rescale_recursive_later
        )

        self._v_emitter.self_destruct_connect.connect(
            self._v_emitter._self_destruct_connect_
        )
        self._v_emitter.self_destruct_connect.emit(self.self_destruct)
        return

    def init_guiVars(self, **kwargs) -> None:
        """"""
        purefunctions.printc(
            f"ERROR: item with name {self.get_name()} and "
            f"lblText {self.get_state().lblTxt} did not "
            f"implement init_guiVars()",
            color="error",
        )
        raise NotImplementedError()

    def bind_guiVars(self, **kwargs) -> None:
        """Initialize all GUI elements (including the ItemEmitter()!) and push
        them to the main thread.

        Unlike the Filetree case, the Dashboard Item()-instance cannot init-
        ialize its GUI elements alone. It needs help from the subclass.
        """
        assert threading.current_thread() is threading.main_thread()
        self.init_emitter()
        parent = self.get_parent()
        if parent is not None:
            self.get_state().showChbx = parent.get_state().showChbx
        for key, value in kwargs.items():
            assert key in self._v_widgets
            self._v_widgets[key] = value
            if value is None:
                continue
            # self._v_widgets[key].moveToThread(data.application.thread())
            self._v_widgets[key].leftclick_signal.connect(self.leftclick)
            self._v_widgets[key].ctrl_leftclick_signal.connect(
                self.ctrl_leftclick
            )
            self._v_widgets[key].rightclick_signal.connect(self.rightclick)
            self._v_widgets[key].dragstart_signal.connect(self.dragstart)
            self._v_widgets[key].dragenter_signal.connect(self.dragenter)
            self._v_widgets[key].dragleave_signal.connect(self.dragleave)
            self._v_widgets[key].dragdrop_signal.connect(self.dragdrop)
            self._v_widgets[key].keypress_signal.connect(self.keypress)
            self._v_widgets[key].keyrelease_signal.connect(self.keyrelease)
            self._v_widgets[key].focusin_signal.connect(self.focusin)
            self._v_widgets[key].focusout_signal.connect(self.focusout)
            continue
        self.rescale(refreshlock=False)
        return

    def get_layout(
        self,
    ) -> Union[_cm_layout_.FolderLayout, _cm_layout_.FileLayout]:
        """"""
        if self._v_layout is None:
            self.init_guiVars()
        return self._v_layout

    def kill_guiVars_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Done immediately if no context menu is running.

        CAREFUL:
        This function only deals with the own ItemLayout(). It doesn't touch the left SpacerLayout()
        or the encapsulating hlyt. So you should only call this function after you've dealt with
        those!
        """

        def kill_next(
            _widget_gen: Iterator[
                ItemsView[
                    str,
                    Optional[
                        Union[
                            _iw_.ItemWidget,
                            _item_arrow_.ItemArrow,
                            _item_btn_.ItemBtn,
                            _item_chbx_.ItemChbx,
                            _item_dropdown_.ItemDropdown,
                            _item_img_.ItemImg,
                            _item_lbl_.ItemLbl,
                            _item_lineedit_.ItemLineedit,
                            _item_progbar_.ItemProgbar,
                            _item_richlbl_.ItemRichLbl,
                        ]
                    ],
                ]
            ],
        ) -> None:
            try:
                _key, temp = next(_widget_gen)
                _widg: Optional[
                    Union[
                        _iw_.ItemWidget,
                        _item_arrow_.ItemArrow,
                        _item_btn_.ItemBtn,
                        _item_chbx_.ItemChbx,
                        _item_dropdown_.ItemDropdown,
                        _item_img_.ItemImg,
                        _item_lbl_.ItemLbl,
                        _item_lineedit_.ItemLineedit,
                        _item_progbar_.ItemProgbar,
                        _item_richlbl_.ItemRichLbl,
                    ]
                ] = temp
            except StopIteration:
                try:
                    finish()
                except RecursionError:
                    purefunctions.printc(
                        f"\n"
                        f"WARNING: Function {q}kill_guiVars_later(){q} in item.py went \n"
                        f"         very deep into recursion. Increase recursion \n"
                        f"         limit to:",
                        color="warning",
                    )
                    sys.setrecursionlimit(sys.getrecursionlimit() + 1000)
                    print(f"         {sys.getrecursionlimit()}")
                    finish()
                return
            if _widg is None:
                kill_next(_widget_gen)
                return
            self._v_widgets[_key] = None
            try:
                _widg.self_destruct(
                    callback=kill_next,
                    callbackArg=_widget_gen,
                )
            except RecursionError:
                purefunctions.printc(
                    f"\n"
                    f"WARNING: Function {q}kill_guiVars_later(){q} in item.py went \n"
                    f"         very deep into recursion. Increase recursion \n"
                    f"         limit to:",
                    color="warning",
                )
                sys.setrecursionlimit(sys.getrecursionlimit() + 1000)
                print(f"         {sys.getrecursionlimit()}")
                _widg.self_destruct(
                    callback=kill_next,
                    callbackArg=_widget_gen,
                )
            return

        def finish(*args) -> None:
            # $ Clean and kill one's own layout.
            self._v_layout.clean()
            self._v_layout.setParent(None)  # noqa
            self._v_layout.deleteLater()
            self._v_layout = None
            self._v_emitter.disconnect_signals()
            self._v_emitter.setParent(None)  # noqa
            self._v_emitter.deleteLater()
            self._v_emitter = None
            self.release_refresh_mutex()
            try:
                if callback is not None:
                    callback(callbackArg)
            except RecursionError as e:
                purefunctions.printc(
                    f"\n"
                    f"WARNING: Function {q}kill_guiVars_later(){q} in item.py went \n"
                    f"         very deep into recursion. Increase recursion \n"
                    f"         limit to:",
                    color="warning",
                )
                sys.setrecursionlimit(sys.getrecursionlimit() + 1000)
                print(f"         {sys.getrecursionlimit()}")
                if callback is not None:
                    callback(callbackArg)
            return

        # * Start
        assert threading.current_thread() is threading.main_thread()
        if self._v_layout is None:
            if callback is not None:
                callback(callbackArg)
            return
        for key, widg in self._v_widgets.items():
            if (
                widg is not None
            ) and _contextmenu_launcher_.ContextMenuLauncher().is_busy():
                qt.QTimer.singleShot(
                    60,
                    functools.partial(
                        self.kill_guiVars_later,
                        callback,
                        callbackArg,
                    ),
                )
                return
        if not self.acquire_refresh_mutex():
            qt.QTimer.singleShot(
                60,
                functools.partial(
                    self.kill_guiVars_later,
                    callback,
                    callbackArg,
                ),
            )
            return

        # $ Start killing the widgets one-by-one.
        widget_gen: Iterator[
            ItemsView[
                str,
                Optional[
                    Union[
                        _iw_.ItemWidget,
                        _item_arrow_.ItemArrow,
                        _item_btn_.ItemBtn,
                        _item_chbx_.ItemChbx,
                        _item_dropdown_.ItemDropdown,
                        _item_img_.ItemImg,
                        _item_lbl_.ItemLbl,
                        _item_lineedit_.ItemLineedit,
                        _item_progbar_.ItemProgbar,
                        _item_richlbl_.ItemRichLbl,
                    ]
                ],
            ]
        ] = iter(
            self._v_widgets.items()
        )  # noqa
        try:
            kill_next(widget_gen)
        except RecursionError:
            purefunctions.printc(
                f"\n"
                f"WARNING: Function {q}kill_guiVars_later(){q} in item.py went \n"
                f"         very deep into recursion. Increase recursion \n"
                f"         limit to:",
                color="warning",
            )
            sys.setrecursionlimit(sys.getrecursionlimit() + 1000)
            print(f"         {sys.getrecursionlimit()}")
            kill_next(widget_gen)
        return

    """----------------------------------------------------------------------------"""
    """ 2. GETTERS AND SETTERS                                                     """
    """----------------------------------------------------------------------------"""

    def get_relpath(self) -> Optional[str]:
        "Rootfolder overrides this function to return a dot"
        if self.get_parent() is None:
            # Only happens if parent has died. Shouldn't happen in fact.
            purefunctions.printc(
                f"\n\nERROR: get_relpath() called on item {q}{self._name}{q} "
                f"whose parent has died.",
                color="error",
            )
            print(traceback.print_stack())
            print("\n\n")
            return None
        if self.get_parent().get_relpath() == ".":
            return self._name
        return f"{self.get_parent().get_relpath()}/{self._name}"

    def get_abspath(self) -> Optional[str]:
        "Rootfolder overrides this function to return the abspath"
        relpath = self.get_relpath()
        if relpath is None:
            return None
        abspath = _pp_.rel_to_abs(
            rootpath=self.get_rootdir().get_abspath(),
            relpath=relpath,
        )
        return abspath

    def get_name(self) -> str:
        """"""
        return self._name

    def get_name_suffix_replaced(
        self,
        new_suffix: str,
        name: Optional[str] = None,
    ) -> str:
        """"""
        if name is None:
            name = self.get_name()
        p = re.compile(r"(.*[.])([^.]*)")
        try:
            new_suffix = new_suffix.replace(".", "")
            new_name = p.sub(r"\1" + new_suffix, name)
            return new_name
        except Exception as e:
            pass
        return name + new_suffix

    def set_name(self, name: str) -> None:
        """"""
        self._name = name
        return

    @ref
    def get_parent(self) -> Folder:
        """"""
        return self._parentRef  # noqa

    def set_parent(self, parent: Folder) -> None:
        """"""
        if self._parentRef is not None:
            if self._parentRef() is parent:
                return
            assert self not in self._parentRef().get_childlist(), str(
                f"self = [{self.get_name()}, {self}]\n"
                f"old_parent = [{self._parentRef().get_name()}, {self._parentRef()}]\n"
                f"new_parent = [{parent.get_name()}, {parent}]\n"
            )
            self._parentRef = None
        self._parentRef = weakref.ref(parent)
        assert self in self._parentRef().get_childlist()
        name = self.get_name()
        return

    def get_depth(self) -> int:
        """"""
        raise NotImplementedError()

    @ref
    def get_rootdir(self) -> Union[Root, Any]:
        """"""
        return self._rootRef  # noqa

    def get_ancestorList(self) -> List[Item]:
        """"""
        ancestorList = []
        if self.get_parent() is None:
            return ancestorList
        ancestor = self.get_parent()
        while True:
            ancestorList.append(ancestor)
            ancestor = ancestor.get_parent()
            if ancestor is None:
                break
        return ancestorList

    def get_widget(self, key: str) -> Union[
        _iw_.ItemWidget,
        qt.QWidget,
        _advancedcombobox_.AdvancedComboBox,
        Any,
    ]:
        """"""
        return self._v_widgets[key]

    def get_widgetIter(self) -> Iterator[_iw_.ItemWidget]:
        """"""
        return iter(self._v_widgets.values())

    def get_reversedWidgetIter(self) -> Iterator[_iw_.ItemWidget]:
        """"""
        return reversed([value for key, value in self._v_widgets.items()])

    """----------------------------------------------------------------------------"""
    """ 3. CLICKS                                                                  """
    """----------------------------------------------------------------------------"""

    def printclicks(self, txt: str) -> None:
        """"""
        # print(txt)
        return

    """
    3.1 LEFTCLICK
    """

    def leftclick(self, key: str, event: qt.QEvent) -> None:
        """"""
        funcs = {
            "itemBtn": self.leftclick_itemBtn,
            "itemActionBtn": self.leftclick_itemActionBtn,
            "itemArrow": self.leftclick_itemBtn,
            "itemLbl": self.leftclick_itemLbl,
            "itemChbx": self.leftclick_itemChbx,
            "cchbx": self.leftclick_cchbx,
            "hchbx": self.leftclick_hchbx,
            "hglass": self.leftclick_hglass,
            "cfgchbx": self.leftclick_cfgchbx,
            "itemImg": self.leftclick_itemImg,
            "itemLineedit": self.leftclick_itemLineedit,
            "itemProgbar": self.leftclick_itemProgbar,
            "itemRichLbl": self.leftclick_itemRichLbl,
            "itemDropdown": self.leftclick_itemDropdown,
        }
        # noinspection PyArgumentList
        funcs[key](event)
        return

    def leftclick_itemBtn(self, event: Optional[qt.QMouseEvent]) -> None:
        self.printclicks("leftclick on itemBtn")

    def leftclick_itemActionBtn(self, event: Optional[qt.QMouseEvent]) -> None:
        self.printclicks("leftclick on itemActionBtn")

    def leftclick_itemLbl(self, event: Optional[qt.QMouseEvent]) -> None:
        self.printclicks("leftclick on itemLbl")

    def leftclick_itemChbx(self, event: Optional[qt.QMouseEvent]) -> None:
        self.printclicks("leftclick on itemChbx")

    def leftclick_cchbx(self, event: Optional[qt.QMouseEvent]) -> None:
        self.printclicks("leftclick on cchbx")

    def leftclick_hchbx(self, event: Optional[qt.QMouseEvent]) -> None:
        self.printclicks("leftclick on hchbx")

    def leftclick_hglass(self, event: Optional[qt.QMouseEvent]) -> None:
        self.printclicks("leftclick on hglass")

    def leftclick_cfgchbx(self, event: Optional[qt.QMouseEvent]) -> None:
        self.printclicks("leftclick on cfgchbx")

    def leftclick_itemImg(self, event: Optional[qt.QMouseEvent]) -> None:
        self.printclicks("leftclick on itemImg")

    def leftclick_itemLineedit(self, event: Optional[qt.QMouseEvent]) -> None:
        self.printclicks("leftclick on itemLineedit")

    def leftclick_itemProgbar(self, event: Optional[qt.QMouseEvent]) -> None:
        self.printclicks("leftclick on itemProgbar")

    def leftclick_itemRichLbl(self, event: Optional[qt.QMouseEvent]) -> None:
        self.printclicks("leftclick on itemRichLbl")

    def leftclick_itemDropdown(self, event: Optional[qt.QMouseEvent]) -> None:
        self.printclicks("leftclick on itemDropdown")

    """
    3.2 CTRL_LEFTCLICK
    """

    def ctrl_leftclick(self, key: str, event: qt.QEvent) -> None:
        """"""
        funcs = {
            "itemBtn": self.ctrl_leftclick_itemBtn,
            "itemActionBtn": self.ctrl_leftclick_itemActionBtn,
            "itemArrow": self.ctrl_leftclick_itemBtn,
            "itemLbl": self.ctrl_leftclick_itemLbl,
            "itemChbx": self.ctrl_leftclick_itemChbx,
            "cchbx": self.ctrl_leftclick_cchbx,
            "hchbx": self.ctrl_leftclick_hchbx,
            "hglass": self.ctrl_leftclick_hglass,
            "cfgchbx": self.ctrl_leftclick_cfgchbx,
            "itemImg": self.ctrl_leftclick_itemImg,
            "itemLineedit": self.ctrl_leftclick_itemLineedit,
            "itemProgbar": self.ctrl_leftclick_itemProgbar,
            "itemRichLbl": self.ctrl_leftclick_itemRichLbl,
            "itemDropdown": self.ctrl_leftclick_itemDropdown,
        }
        # noinspection PyArgumentList
        funcs[key](event)
        return

    def ctrl_leftclick_itemBtn(self, event: qt.QEvent) -> None:
        self.printclicks("ctrl_leftclick on itemBtn")

    def ctrl_leftclick_itemActionBtn(self, event: qt.QEvent) -> None:
        self.printclicks("ctrl_leftclick on itemActionBtn")

    def ctrl_leftclick_itemLbl(self, event: qt.QEvent) -> None:
        self.printclicks("ctrl_leftclick on itemLbl")

    def ctrl_leftclick_itemChbx(self, event: qt.QEvent) -> None:
        self.printclicks("ctrl_leftclick on itemChbx")

    def ctrl_leftclick_cchbx(self, event: qt.QEvent) -> None:
        self.printclicks("ctrl_leftclick on cchbx")

    def ctrl_leftclick_hchbx(self, event: qt.QEvent) -> None:
        self.printclicks("ctrl_leftclick on hchbx")

    def ctrl_leftclick_hglass(self, event: qt.QEvent) -> None:
        self.printclicks("ctrl_leftclick on hglass")

    def ctrl_leftclick_cfgchbx(self, event: qt.QEvent) -> None:
        self.printclicks("ctrl_leftclick on cfgchbx")

    def ctrl_leftclick_itemImg(self, event: qt.QEvent) -> None:
        self.printclicks("ctrl_leftclick on itemImg")

    def ctrl_leftclick_itemLineedit(self, event: qt.QEvent) -> None:
        self.printclicks("ctrl_leftclick on itemLineedit")

    def ctrl_leftclick_itemProgbar(self, event: qt.QEvent) -> None:
        self.printclicks("ctrl_leftclick on itemProgbar")

    def ctrl_leftclick_itemRichLbl(self, event: qt.QEvent) -> None:
        self.printclicks("leftclick on itemRichLbl")

    def ctrl_leftclick_itemDropdown(self, event: qt.QEvent) -> None:
        self.printclicks("leftclick on itemDropdown")

    """
    3.3 RIGHTCLICK
    """

    def rightclick(self, key: str, event: qt.QEvent) -> None:
        """"""
        funcs = {
            "itemBtn": self.rightclick_itemBtn,
            "itemActionBtn": self.rightclick_itemActionBtn,
            "itemArrow": self.rightclick_itemBtn,
            "itemLbl": self.rightclick_itemLbl,
            "itemChbx": self.rightclick_itemChbx,
            "cchbx": self.rightclick_cchbx,
            "hchbx": self.rightclick_hchbx,
            "hglass": self.rightclick_hglass,
            "cfgchbx": self.rightclick_cfgchbx,
            "itemImg": self.leftclick_itemImg,
            "itemLineedit": self.rightclick_itemLineedit,
            "itemProgbar": self.rightclick_itemProgbar,
            "itemRichLbl": self.rightclick_itemRichLbl,
            "itemDropdown": self.rightclick_itemDropdown,
        }
        # noinspection PyArgumentList
        funcs[key](event)
        return

    def rightclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        self.printclicks("rightclick on itemBtn")

    def rightclick_itemActionBtn(self, event: qt.QMouseEvent) -> None:
        self.printclicks("rightclick on itemActionBtn")

    def rightclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        self.printclicks("rightclick on itemLbl")

    def rightclick_itemChbx(self, event: qt.QMouseEvent) -> None:
        self.printclicks("rightclick on itemChbx")

    def rightclick_cchbx(self, event: qt.QMouseEvent) -> None:
        self.printclicks("leftclick on cchbx")

    def rightclick_hchbx(self, event: qt.QMouseEvent) -> None:
        self.printclicks("leftclick on hchbx")

    def rightclick_hglass(self, event: qt.QMouseEvent) -> None:
        self.printclicks("rightclick on hglass")

    def rightclick_cfgchbx(self, event: qt.QMouseEvent) -> None:
        self.printclicks("leftclick on cfgchbx")

    def rightclick_itemImg(self, event: qt.QMouseEvent) -> None:
        self.printclicks("rightclick on itemImg")

    def rightclick_itemLineedit(self, event: qt.QMouseEvent) -> None:
        self.printclicks("rightclick on itemLineedit")

    def rightclick_itemProgbar(self, event: qt.QMouseEvent) -> None:
        self.printclicks("rightclick on itemProgbar")

    def rightclick_itemRichLbl(self, event: qt.QMouseEvent) -> None:
        self.printclicks("rightclick on itemRichLbl")

    def rightclick_itemDropdown(self, event: qt.QMouseEvent) -> None:
        self.printclicks("rightclick on itemDropdown")

    """
    3.4 CTRL_RIGHTCLICK
    """
    # NOT
    # IMPLEMENTED
    """
    3.5 DRAGSTART
    """

    def dragstart(self, key: str, event: qt.QEvent, mimetxt: str) -> None:
        """"""
        funcs = {
            "itemBtn": self.dragstart_itemBtn,
            "itemActionBtn": self.dragstart_itemActionBtn,
            "itemArrow": self.dragstart_itemBtn,
            "itemLbl": self.dragstart_itemLbl,
            "itemChbx": self.dragstart_itemChbx,
            "cchbx": self.dragstart_cchbx,
            "hchbx": self.dragstart_hchbx,
            "hglass": self.dragstart_hglass,
            "cfgchbx": self.dragstart_cfgchbx,
            "itemImg": self.dragstart_itemImg,
            "itemLineedit": self.dragstart_itemLineedit,
            "itemProgbar": self.dragstart_itemProgbar,
            "itemRichLbl": self.dragstart_itemRichLbl,
            "itemDropdown": self.dragstart_itemDropdown,
        }
        # noinspection PyArgumentList
        funcs[key](event, mimetxt)
        return

    def dragstart_itemBtn(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragstart on itemBtn")

    def dragstart_itemActionBtn(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragstart on itemActionBtn")

    def dragstart_itemLbl(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragstart on itemLbl")

    def dragstart_itemChbx(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragstart on itemChbx")

    def dragstart_cchbx(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragstart on cchbx")

    def dragstart_hchbx(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragstart on hchbx")

    def dragstart_hglass(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragstart on hglass")

    def dragstart_cfgchbx(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragstart on cfgchbx")

    def dragstart_itemImg(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragstart on itemImg")

    def dragstart_itemLineedit(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragstart on itemLineedit")

    def dragstart_itemProgbar(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragstart on itemProgbar")

    def dragstart_itemRichLbl(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragstart on itemRichLbl")

    def dragstart_itemDropdown(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragstart on itemDropdown")

    """
    3.6 DRAGENTER
    """

    def dragenter(self, key: str, event: qt.QEvent, mimetxt: str) -> None:
        """"""
        funcs = {
            "itemBtn": self.dragenter_itemBtn,
            "itemActionBtn": self.dragenter_itemActionBtn,
            "itemArrow": self.dragenter_itemBtn,
            "itemLbl": self.dragenter_itemLbl,
            "itemChbx": self.dragenter_itemChbx,
            "cchbx": self.dragenter_cchbx,
            "hchbx": self.dragenter_hchbx,
            "hglass": self.dragenter_hglass,
            "cfgchbx": self.dragenter_cfgchbx,
            "itemImg": self.dragenter_itemImg,
            "itemLineedit": self.dragenter_itemLineedit,
            "itemProgbar": self.dragenter_itemProgbar,
            "itemRichLbl": self.dragenter_itemRichLbl,
            "itemDropdown": self.dragenter_itemDropdown,
        }
        # noinspection PyArgumentList
        funcs[key](event, mimetxt)
        return

    def dragenter_itemBtn(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragenter on itemBtn")

    def dragenter_itemActionBtn(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragenter on itemActionBtn")

    def dragenter_itemLbl(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragenter on itemLbl")

    def dragenter_itemChbx(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragenter on itemChbx")

    def dragenter_cchbx(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragenter on cchbx")

    def dragenter_hchbx(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragenter on hchbx")

    def dragenter_hglass(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragenter on hglass")

    def dragenter_cfgchbx(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragenter on cfgchbx")

    def dragenter_itemImg(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragenter on itemImg")

    def dragenter_itemLineedit(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragenter on itemLineedit")

    def dragenter_itemProgbar(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragenter on itemProgbar")

    def dragenter_itemRichLbl(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragenter on itemRichLbl")

    def dragenter_itemDropdown(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragenter on itemDropdown")

    """
    3.7 DRAGLEAVE
    """

    def dragleave(self, key: str, event: qt.QEvent) -> None:
        """"""
        funcs = {
            "itemBtn": self.dragleave_itemBtn,
            "itemActionBtn": self.dragleave_itemActionBtn,
            "itemArrow": self.dragleave_itemBtn,
            "itemLbl": self.dragleave_itemLbl,
            "itemChbx": self.dragleave_itemChbx,
            "cchbx": self.dragleave_cchbx,
            "hchbx": self.dragleave_hchbx,
            "hglass": self.dragleave_hglass,
            "cfgchbx": self.dragleave_cfgchbx,
            "itemImg": self.dragleave_itemImg,
            "itemLineedit": self.dragleave_itemLineedit,
            "itemProgbar": self.dragleave_itemProgbar,
            "itemRichLbl": self.dragleave_itemRichLbl,
            "itemDropdown": self.dragleave_itemDropdown,
        }
        # noinspection PyArgumentList
        funcs[key](event)
        return

    def dragleave_itemBtn(self, event: qt.QEvent) -> None:
        self.printclicks("dragleave on itemBtn")

    def dragleave_itemActionBtn(self, event: qt.QEvent) -> None:
        self.printclicks("dragleave on itemActionBtn")

    def dragleave_itemLbl(self, event: qt.QEvent) -> None:
        self.printclicks("dragleave on itemLbl")

    def dragleave_itemChbx(self, event: qt.QEvent) -> None:
        self.printclicks("dragleave on itemChbx")

    def dragleave_cchbx(self, event: qt.QEvent) -> None:
        self.printclicks("dragleave on cchbx")

    def dragleave_hchbx(self, event: qt.QEvent) -> None:
        self.printclicks("dragleave on hchbx")

    def dragleave_hglass(self, event: qt.QEvent) -> None:
        self.printclicks("dragleave on hglass")

    def dragleave_cfgchbx(self, event: qt.QEvent) -> None:
        self.printclicks("dragleave on cfgchbx")

    def dragleave_itemImg(self, event: qt.QEvent) -> None:
        self.printclicks("dragleave on itemImg")

    def dragleave_itemLineedit(self, event: qt.QEvent) -> None:
        self.printclicks("dragleave on itemLineedit")

    def dragleave_itemProgbar(self, event: qt.QEvent) -> None:
        self.printclicks("dragleave on itemProgbar")

    def dragleave_itemRichLbl(self, event: qt.QEvent) -> None:
        self.printclicks("dragleave on itemRichLbl")

    def dragleave_itemDropdown(self, event: qt.QEvent) -> None:
        self.printclicks("dragleave on itemDropdown")

    """
    3.8 DRAGDROP
    """

    def dragdrop(self, key: str, event: qt.QEvent, mimetxt: str) -> None:
        """"""
        funcs = {
            "itemBtn": self.dragdrop_itemBtn,
            "itemActionBtn": self.dragdrop_itemActionBtn,
            "itemArrow": self.dragdrop_itemBtn,
            "itemLbl": self.dragdrop_itemLbl,
            "itemChbx": self.dragdrop_itemChbx,
            "cchbx": self.dragdrop_cchbx,
            "hchbx": self.dragdrop_hchbx,
            "hglass": self.dragdrop_hglass,
            "cfgchbx": self.dragdrop_cfgchbx,
            "itemImg": self.dragdrop_itemImg,
            "itemLineedit": self.dragdrop_itemLineedit,
            "itemProgbar": self.dragdrop_itemProgbar,
            "itemRichLbl": self.dragdrop_itemRichLbl,
            "itemDropdown": self.dragdrop_itemDropdown,
        }
        # noinspection PyArgumentList
        funcs[key](event, mimetxt)
        return

    def dragdrop_itemBtn(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragdrop on itemBtn")

    def dragdrop_itemActionBtn(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragdrop on itemActionBtn")

    def dragdrop_itemLbl(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragdrop on itemLbl")

    def dragdrop_itemChbx(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragdrop on itemChbx")

    def dragdrop_cchbx(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragdrop on cchbx")

    def dragdrop_hchbx(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragdrop on hchbx")

    def dragdrop_hglass(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragdrop on hglass")

    def dragdrop_cfgchbx(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragdrop on cfgchbx")

    def dragdrop_itemImg(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragdrop on itemImg")

    def dragdrop_itemLineedit(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragdrop on itemLineedit")

    def dragdrop_itemProgbar(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragdrop on itemProgbar")

    def dragdrop_itemRichLbl(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragdrop on itemRichLbl")

    def dragdrop_itemDropdown(self, event: qt.QEvent, mimetxt: str) -> None:
        self.printclicks("dragdrop on itemDropdown")

    """
    3.9 CONTEXT MENU CLICK (! click in context menu itself !)
    """

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        self.printclicks(
            f"you clicked on {self.get_relpath()} -> itemBtn -> {key}"
        )

    def contextmenuclick_itemActionBtn(self, key: str, *args) -> None:
        self.printclicks(
            f"you clicked on {self.get_relpath()} -> itemActionBtn -> {key}"
        )

    def contextmenuclick_itemLbl(self, key: str, *args) -> None:
        self.printclicks(
            f"you clicked on {self.get_relpath()} -> itemLbl -> {key}"
        )

    def contextmenuclick_itemChbx(self, key: str, *args) -> None:
        self.printclicks(
            f"you clicked on {self.get_relpath()} -> itemChbx -> {key}"
        )

    def contextmenuclick_cchbx(self, key: str, *args) -> None:
        self.printclicks(
            f"you clicked on {self.get_relpath()} -> cchbx -> {key}"
        )

    def contextmenuclick_hchbx(self, key: str, *args) -> None:
        self.printclicks(
            f"you clicked on {self.get_relpath()} -> hchbx -> {key}"
        )

    def contextmenuclick_hglass(self, key: str, *args) -> None:
        self.printclicks(
            f"you clicked on {self.get_relpath()} -> hglass -> {key}"
        )

    def contextmenuclick_cfgchbx(self, key: str, *args) -> None:
        self.printclicks(
            f"you clicked on {self.get_relpath()} -> cfgchbx -> {key}"
        )

    def contextmenuclick_itemImg(self, key: str, *args) -> None:
        self.printclicks(
            f"you clicked on {self.get_relpath()} -> itemImg -> {key}"
        )

    def contextmenuclick_itemLineedit(self, key: str, *args) -> None:
        self.printclicks(
            f"you clicked on {self.get_relpath()} -> itemLineedit -> {key}"
        )

    def contextmenuclick_itemProgbar(self, key: str, *args) -> None:
        self.printclicks(
            f"you clicked on {self.get_relpath()} -> itemProgbar -> {key}"
        )

    def contextmenuclick_itemRichLbl(self, key: str, *args) -> None:
        self.printclicks(
            f"you clicked on {self.get_relpath()} -> itemProgbar -> {key}"
        )

    def contextmenuclick_itemDropdown(self, key: str, *args) -> None:
        self.printclicks(
            f"you clicked on {self.get_relpath()} -> itemDropdown -> {key}"
        )

    """
    3.10 KEYPRESS
    """

    def keypress(self, key: str, event: qt.QEvent) -> None:
        """"""
        funcs = {
            "itemBtn": self.keypress_itemBtn,
            "itemActionBtn": self.keypress_itemActionBtn,
            "itemArrow": self.keypress_itemBtn,
            "itemLbl": self.keypress_itemLbl,
            "itemChbx": self.keypress_itemChbx,
            "cchbx": self.keypress_cchbx,
            "hchbx": self.keypress_hchbx,
            "hglass": self.keypress_hglass,
            "cfgchbx": self.keypress_cfgchbx,
            "itemImg": self.keypress_itemImg,
            "itemLineedit": self.keypress_itemLineedit,
            "itemProgbar": self.keypress_itemProgbar,
            "itemRichLbl": self.keypress_itemRichLbl,
            "itemDropdown": self.keypress_itemDropdown,
        }
        # noinspection PyArgumentList
        funcs[key](event)
        return

    def keypress_itemBtn(self, event: qt.QEvent) -> None:
        self.printclicks("keypress on itemBtn")

    def keypress_itemActionBtn(self, event: qt.QEvent) -> None:
        self.printclicks("keypress on itemActionBtn")

    def keypress_itemLbl(self, event: qt.QEvent) -> None:
        self.printclicks("keypress on itemLbl")

    def keypress_itemChbx(self, event: qt.QEvent) -> None:
        self.printclicks("keypress on itemChbx")

    def keypress_cchbx(self, event: qt.QEvent) -> None:
        self.printclicks("keypress on cchbx")

    def keypress_hchbx(self, event: qt.QEvent) -> None:
        self.printclicks("keypress on hchbx")

    def keypress_hglass(self, event: qt.QEvent) -> None:
        self.printclicks("keypress on hglass")

    def keypress_cfgchbx(self, event: qt.QEvent) -> None:
        self.printclicks("keypress on cfgchbx")

    def keypress_itemImg(self, event: qt.QEvent) -> None:
        self.printclicks("keypress on ItemImg")

    def keypress_itemLineedit(self, event: qt.QEvent) -> None:
        self.printclicks("keypress on itemLineedit")

    def keypress_itemProgbar(self, event: qt.QEvent) -> None:
        self.printclicks("keypress on itemProgbar")

    def keypress_itemRichLbl(self, event: qt.QEvent) -> None:
        self.printclicks("keypress on itemRichLbl")

    def keypress_itemDropdown(self, event: qt.QEvent) -> None:
        self.printclicks("keypress on itemDropdown")

    """
    3.11 KEYRELEASE
    """

    def keyrelease(self, key: str, event: qt.QEvent) -> None:
        """"""
        funcs = {
            "itemBtn": self.keyrelease_itemBtn,
            "itemActionBtn": self.keyrelease_itemActionBtn,
            "itemArrow": self.keyrelease_itemBtn,
            "itemLbl": self.keyrelease_itemLbl,
            "itemChbx": self.keyrelease_itemChbx,
            "cchbx": self.keyrelease_cchbx,
            "hchbx": self.keyrelease_hchbx,
            "hglass": self.keyrelease_hglass,
            "cfgchbx": self.keyrelease_cfgchbx,
            "itemImg": self.keyrelease_itemImg,
            "itemLineedit": self.keyrelease_itemLineedit,
            "itemProgbar": self.keyrelease_itemProgbar,
            "itemRichLbl": self.keyrelease_itemRichLbl,
            "itemDropdown": self.keyrelease_itemDropdown,
        }
        # noinspection PyArgumentList
        funcs[key](event)
        return

    def keyrelease_itemBtn(self, event: qt.QEvent) -> None:
        self.printclicks("keyrelease on itemBtn")

    def keyrelease_itemActionBtn(self, event: qt.QEvent) -> None:
        self.printclicks("keyrelease on itemActionBtn")

    def keyrelease_itemLbl(self, event: qt.QEvent) -> None:
        self.printclicks("keyrelease on itemLbl")

    def keyrelease_itemChbx(self, event: qt.QEvent) -> None:
        self.printclicks("keyrelease on itemChbx")

    def keyrelease_cchbx(self, event: qt.QEvent) -> None:
        self.printclicks("keyrelease on cchbx")

    def keyrelease_hchbx(self, event: qt.QEvent) -> None:
        self.printclicks("keyrelease on hchbx")

    def keyrelease_hglass(self, event: qt.QEvent) -> None:
        self.printclicks("keyrelease on hglass")

    def keyrelease_cfgchbx(self, event: qt.QEvent) -> None:
        self.printclicks("keyrelease on cfgchbx")

    def keyrelease_itemImg(self, event: qt.QEvent) -> None:
        self.printclicks("keyrelease on itemImg")

    def keyrelease_itemLineedit(self, event: qt.QEvent) -> None:
        self.printclicks("keyrelease on itemLineedit")

    def keyrelease_itemProgbar(self, event: qt.QEvent) -> None:
        self.printclicks("keyrelease on itemProgbar")

    def keyrelease_itemRichLbl(self, event: qt.QEvent) -> None:
        self.printclicks("keyrelease on itemRichLbl")

    def keyrelease_itemDropdown(self, event: qt.QEvent) -> None:
        self.printclicks("keyrelease on itemDropdown")

    """
    3.12 FOCUSIN
    """

    def focusin(self, key: str, event: qt.QEvent) -> None:
        """"""
        funcs = {
            "itemBtn": self.focusin_itemBtn,
            "itemActionBtn": self.focusin_itemActionBtn,
            "itemArrow": self.focusin_itemBtn,
            "itemLbl": self.focusin_itemLbl,
            "itemChbx": self.focusin_itemChbx,
            "cchbx": self.focusin_cchbx,
            "hchbx": self.focusin_hchbx,
            "hglass": self.focusin_hglass,
            "cfgchbx": self.focusin_cfgchbx,
            "itemImg": self.focusin_itemImg,
            "itemLineedit": self.focusin_itemLineedit,
            "itemProgbar": self.focusin_itemProgbar,
            "itemRichLbl": self.focusin_itemRichLbl,
            "itemDropdown": self.focusin_itemDropdown,
        }
        # noinspection PyArgumentList
        funcs[key](event)
        return

    def focusin_itemBtn(self, event: qt.QEvent) -> None:
        self.printclicks("focusin on itemBtn")

    def focusin_itemActionBtn(self, event: qt.QEvent) -> None:
        self.printclicks("focusin on itemActionBtn")

    def focusin_itemLbl(self, event: qt.QEvent) -> None:
        self.printclicks("focusin on itemLbl")

    def focusin_itemChbx(self, event: qt.QEvent) -> None:
        self.printclicks("focusin on itemChbx")

    def focusin_cchbx(self, event: qt.QEvent) -> None:
        self.printclicks("focusin on cchbx")

    def focusin_hchbx(self, event: qt.QEvent) -> None:
        self.printclicks("focusin on hchbx")

    def focusin_hglass(self, event: qt.QEvent) -> None:
        self.printclicks("focusin on hglass")

    def focusin_cfgchbx(self, event: qt.QEvent) -> None:
        self.printclicks("focusin on cfgchbx")

    def focusin_itemImg(self, event: qt.QEvent) -> None:
        self.printclicks("focusin on itemImg")

    def focusin_itemLineedit(self, event: qt.QEvent) -> None:
        self.printclicks("focusin on itemLineedit")

    def focusin_itemProgbar(self, event: qt.QEvent) -> None:
        self.printclicks("focusin on itemProgbar")

    def focusin_itemRichLbl(self, event: qt.QEvent) -> None:
        self.printclicks("focusin on itemRichLbl")

    def focusin_itemDropdown(self, event: qt.QEvent) -> None:
        self.printclicks("focusin on itemDropdown")

    """
    3.13 FOCUSOUT
    """

    def focusout(self, key: str, event: qt.QEvent) -> None:
        """"""
        funcs = {
            "itemBtn": self.focusout_itemBtn,
            "itemActionBtn": self.focusout_itemActionBtn,
            "itemArrow": self.focusout_itemBtn,
            "itemLbl": self.focusout_itemLbl,
            "itemChbx": self.focusout_itemChbx,
            "cchbx": self.focusout_cchbx,
            "hchbx": self.focusout_hchbx,
            "hglass": self.focusout_hglass,
            "cfgchbx": self.focusout_cfgchbx,
            "itemImg": self.focusout_itemImg,
            "itemLineedit": self.focusout_itemLineedit,
            "itemProgbar": self.focusout_itemProgbar,
            "itemRichLbl": self.focusout_itemRichLbl,
            "itemDropdown": self.focusout_itemDropdown,
        }
        # noinspection PyArgumentList
        funcs[key](event)
        return

    def focusout_itemBtn(self, event: qt.QEvent) -> None:
        self.printclicks("focusout on itemBtn")

    def focusout_itemActionBtn(self, event: qt.QEvent) -> None:
        self.printclicks("focusout on itemActionBtn")

    def focusout_itemLbl(self, event: qt.QEvent) -> None:
        self.printclicks("focusout on itemLbl")

    def focusout_itemChbx(self, event: qt.QEvent) -> None:
        self.printclicks("focusout on itemChbx")

    def focusout_cchbx(self, event: qt.QEvent) -> None:
        self.printclicks("focusout on cchbx")

    def focusout_hchbx(self, event: qt.QEvent) -> None:
        self.printclicks("focusout on hchbx")

    def focusout_hglass(self, event: qt.QEvent) -> None:
        self.printclicks("focusout on hglass")

    def focusout_cfgchbx(self, event: qt.QEvent) -> None:
        self.printclicks("focusout on cfgchbx")

    def focusout_itemImg(self, event: qt.QEvent) -> None:
        self.printclicks("focusout on itemImg")

    def focusout_itemLineedit(self, event: qt.QEvent) -> None:
        self.printclicks("focusout on itemLineedit")

    def focusout_itemProgbar(self, event: qt.QEvent) -> None:
        self.printclicks("focusout on itemProgbar")

    def focusout_itemRichLbl(self, event: qt.QEvent) -> None:
        self.printclicks("focusout on itemRichLbl")

    def focusout_itemDropdown(self, event: qt.QEvent) -> None:
        self.printclicks("focusout on itemDropdown")

    """----------------------------------------------------------------------------"""
    """ 4. SYNCHRONIZATIONS                                                        """
    """----------------------------------------------------------------------------"""

    def refresh(self, refreshlock: bool) -> None:
        """"""
        self.refresh_later(
            refreshlock=refreshlock,
            force_stylesheet=False,
            callback=None,
            callbackArg=None,
        )
        return

    def refresh_later(
        self,
        refreshlock: bool,
        force_stylesheet: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Synchronize the state and all the widgets from this Item():

            - self.get_state().sync_state(...)
            - widg.sync_widg(...) for all widgets

        > RECENT CHANGE (20 JULY 2020):
          If self._v_layout is None
              -> Abort refreshing immediately if it's a Filetree item.
              -> For other items, just complete the state syncing.
        """
        if self.dead:
            purefunctions.printc(
                "WARNING: refresh_later() invoked on dead Item()",
                color="warning",
            )
            if callback is not None:
                callback(callbackArg)
            return
        recursion_cntr: int = 0

        # * Start
        assert threading.current_thread() is threading.main_thread()
        if refreshlock:
            if not self.acquire_refresh_mutex():
                self._cntr += 1
                if self._cntr > 5:
                    print(
                        f"{self.get_name()}.refresh_later() could not "
                        f"acquire _v_refreshMutex!"
                    )
                    self._cntr = 0
                qt.QTimer.singleShot(
                    150,
                    functools.partial(
                        self.refresh_later,
                        refreshlock,
                        force_stylesheet,
                        callback,
                        callbackArg,
                    ),
                )
                return
            assert self._v_refreshMutex.locked()
            self._cntr = 0

        def sync_widgets_start(*args) -> None:
            "Start iteration process"
            if self._v_layout is None:
                finish()
                return
            sync_next_widget(self.get_widgetIter())
            return

        def sync_next_widget(widg_iter: Iterator[_iw_.ItemWidget]) -> None:
            "Sync next widget"
            nonlocal recursion_cntr
            try:
                widg: _iw_.ItemWidget = next(widg_iter)
                recursion_cntr += 1
            except StopIteration:
                finish()
                return
            # Should also sync their contextmenus (if exists already).
            if widg is None:
                sync_next_widget(widg_iter)
                return
            if qt.sip.isdeleted(widg):
                finish()
                return
            # Avoid going too deep into recursion. Use a timer
            # from time to time.
            if recursion_cntr > 10:
                recursion_cntr = 0
                qt.QTimer.singleShot(
                    10,
                    functools.partial(
                        widg.sync_widg,
                        False,
                        force_stylesheet,
                        sync_next_widget,
                        widg_iter,
                    ),
                )
                return
            widg.sync_widg(
                refreshlock=False,
                force_stylesheet=force_stylesheet,
                callback=sync_next_widget,
                callbackArg=widg_iter,
            )
            return

        def finish(*args) -> None:
            self._state.forcePolish = False
            if refreshlock:
                self.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

        # * Sync state
        self._state.sync_state(
            refreshlock=False,
            callback=sync_widgets_start,
            callbackArg=None,
        )
        return

    def refresh_recursive_later(
        self,
        refreshlock: bool,
        force_stylesheet: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        # For children, see override in Folder()!
        self.refresh_later(refreshlock, force_stylesheet, callback, callbackArg)
        return

    def rescale(self, refreshlock: bool) -> None:
        """"""
        self.rescale_later(
            refreshlock=refreshlock,
            callback=None,
            callbackArg=None,
        )
        return

    def rescale_later(
        self,
        refreshlock: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        if self.dead:
            purefunctions.printc(
                "WARNING: rescale_later() invoked on dead Item()",
                color="warning",
            )
            if callback is not None:
                callback(callbackArg)
            return

        def set_scale():
            refresh_self()
            return

        def refresh_self():
            self.refresh_later(
                refreshlock=False,
                force_stylesheet=False,
                callback=refresh_leftlyt,
                callbackArg=None,
            )
            return

        def refresh_leftlyt(arg):
            leftlyt = self.get_layout().get_leftSpacerLyt()
            if leftlyt is None:
                # leftlyt should only exist if this Item() is shown.
                finish()
                return
            leftlyt.rescale_later(
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args):
            self.release_refresh_mutex() if refreshlock else nop()
            (
                qt.QTimer.singleShot(
                    10,
                    functools.partial(callback, callbackArg),
                )
                if callback is not None
                else nop()
            )
            return

        # * Start
        assert threading.current_thread() is threading.main_thread()
        if self._v_layout is None:
            if callback is not None:
                callback(callbackArg)
            return
        if refreshlock:
            if not self.acquire_refresh_mutex():
                self._cntr += 1
                if self._cntr > 5:
                    print(
                        f"{self.get_name()}.rescale_later() could not "
                        f"acquire _v_refreshMutex!"
                    )
                    self._cntr = 0
                qt.QTimer.singleShot(
                    100,
                    functools.partial(
                        self.rescale_later,
                        refreshlock,
                        callback,
                        callbackArg,
                    ),
                )
                return
            assert self._v_refreshMutex.locked()
            self._cntr = 0
        set_scale()
        return

    def rescale_recursive_later(
        self,
        refreshlock: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        # For children, see override in Dir()!
        self.rescale_later(
            refreshlock=refreshlock,
            callback=callback,
            callbackArg=callbackArg,
        )
        return

    """----------------------------------------------------------------------------"""
    """ 5. DEATH                                                                   """
    """----------------------------------------------------------------------------"""

    def is_dead(self) -> bool:
        return self.dead

    def self_destruct(
        self,
        killParentLink: bool = True,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """Kill this Item()-instance: > Remove this Item() from the parental
        layout, so it's no longer visible. > The previous action automatically
        kills all the guiVars of this Item(). > If 'killParentLink', remove
        oneself from the parental childlist. > Set all attributes of this object
        to None.

        :param killParentLink: Remove this Item()-instance from its parental
            childlist.
        """
        if self._v_refreshMutex.locked():
            purefunctions.printc(
                f"WARNING: Trying to kill Item({q}{self._name}{q}) while refresh mutex is locked!",
                color="warning",
            )
        assert threading.current_thread() is threading.main_thread()
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill Item() {q}{self._name}{q} twice!"
                )
            self.dead = True

        my_name = self.get_name()
        my_parent = self.get_parent()
        if my_parent is not None:
            assert self in my_parent.get_childlist()

        def delete_root_guiVars(*args) -> None:
            assert threading.current_thread() is threading.main_thread()
            # I removed this assertion for those elements in the intro wizard that have no parent
            # but are no root either:
            # assert self is self.get_rootdir(), str(
            #     f'{my_relpath} is not the root dir, but has no parent'
            # )
            self.kill_guiVars_later(
                callback=kill_attributes,
                callbackArg=None,
            )
            return

        def remove_from_parentLayout(*args) -> None:
            assert threading.current_thread() is threading.main_thread()
            assert my_parent is not None
            if self._v_layout is None:
                for key in self._v_widgets:
                    assert self._v_widgets[key] is None
                kill_parent_link()
                return
            my_parent.get_layout().remove_one_item(
                child=self,
                callback=kill_parent_link,
                callbackArg=None,
            )
            return

        def kill_parent_link(*args) -> None:
            assert threading.current_thread() is threading.main_thread()
            if my_parent:
                assert self in my_parent.get_childlist()
            if not killParentLink:
                kill_attributes()
                return
            if my_parent:
                my_parent.get_childlist().remove(self)
            kill_attributes()
            return

        def kill_attributes(*args) -> None:
            assert threading.current_thread() is threading.main_thread()
            self._rootRef = None
            self._parentRef = None
            self._state.self_destruct()
            self._state = None
            self._v_widgets = None
            qt.QTimer.singleShot(1, finish)
            return

        def finish(*args) -> None:
            assert threading.current_thread() is threading.main_thread()
            if (not killParentLink) and (my_parent is not None):
                assert self in my_parent.get_childlist(), str(
                    f"{my_name} was accidentally removed from the parent list"
                )
            if callback is not None:
                callback(callbackArg)
            return

        if my_parent is None:
            delete_root_guiVars()
        else:
            remove_from_parentLayout()
        return


# ^                                             FOLDER                                             ^#
# % ============================================================================================== %#
# % Folder()-instance represents one folder in the Filetree/Dashboard/...                          %#
# %                                                                                                %#


class Folder(Item):
    __slots__ = (
        "_childlist",
        "_depth",
    )

    def __init__(
        self,
        rootdir: Optional[Root],
        parent: Optional[Folder],
        name: str,
        depth: int,
        state: Item.Status,
    ) -> None:
        """The Dir()-instance holds two extra attributes in addition to those
        from its superclass Item: > self._childlist: An ordinary Python list
        with child items. > self._depth:    The nesting depth. Root directory
        has depth 0.

        :param rootdir: The Root()-instance at the top.       (*Note*)
        :param parent: The parent directory.                 (*Note*)
        :param name: The name.
        :param depth: The nested depth. Root directory has depth 0.
        :param state: A Status()-instance to start from. *Note: Only a weak
            reference to these parameters get stored.
        """
        super().__init__(rootdir, parent, name, state)
        self._childlist: List[
            Union[
                Item,
                Folder,
                File,
            ]
        ] = []
        self._depth: int = depth

    """----------------------------------------------------------------------------"""
    """ 1. INITIALIZATIONS                                                         """
    """----------------------------------------------------------------------------"""

    def init_layout(self) -> None:
        """"""
        assert self._v_layout is None
        self._v_layout = _cm_layout_.FolderLayout(self)
        return

    """----------------------------------------------------------------------------"""
    """ 2. GETTERS AND SETTERS                                                     """
    """----------------------------------------------------------------------------"""

    def get_childlist(self) -> Optional[List[Union[Folder, File, Item]]]:
        """"""
        return self._childlist

    def add_child(
        self,
        child: Union[Folder, File, Item],
        alpha_order: Union[bool, List[str]],
        show: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Add the given child to 'self._childlist'.

        If this Folder()-instance is shown and open, this function takes a
        while.
        """
        if threading.current_thread() is not threading.main_thread():
            assert show == False

        def show_child(*args):
            self._v_layout.insert_one_item(
                child=child,
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args):
            if callback is not None:
                callback(callbackArg)
            return

        # $ Add to childlist
        self._childlist.append(child)
        child.set_parent(parent=self)
        # $ Not showing now => finish()
        if (
            (show == False)
            or (self._v_layout is None)
            or (self.get_state().open == False)
        ):
            if alpha_order:
                self.order_childlist(
                    order_list=alpha_order,
                    callback=finish,
                    callbackArg=None,
                )
                return
            finish()
            return
        # $ Showing now => show_child()
        if alpha_order:
            self.order_childlist(
                order_list=alpha_order,
                callback=show_child,
                callbackArg=None,
            )
            return
        show_child()
        return

    def remove_child(self, child: Item) -> None:
        """
        Note: This function is redundant. You can reach the same with the
        self_destruct() method.

        """
        raise RuntimeError(
            f"To remove the child, simply call its "
            f"{q}self_destruct(){q} method."
        )

    def replace_child(
        self,
        child1: Item,
        child2: Item,
        show: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Replace child1 by child2 in the 'self._childlist'. The original
        child1 gets destroyed. :param child1       Item() to replace.

        :param child2       Replacement.
        :param show:        Show the inserted child - if this directory itself is open of course.
        """

        def start():
            assert child1 in self._childlist
            i = self._childlist.index(child1)
            child1.self_destruct(
                killParentLink=True,
                callback=replace,
                callbackArg=i,
            )
            return

        def replace(i):
            self._childlist.insert(i, child2)
            child2.set_parent(parent=self)
            if (
                (show is False)
                or (self._v_layout is None)
                or (self.get_state().open is False)
            ):
                finish()
            else:
                show_child()
            return

        def show_child():
            self._v_layout.insert_one_item(
                child=child2,
                callback=callback,
                callbackArg=callbackArg,
            )
            return

        def finish():
            if callback is not None:
                callback(callbackArg)
            return

        start()
        return

    def order_childlist(
        self,
        order_list: Optional[List[str]],
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Order the self._childlist alphabetically."""

        def start_sorting(*args):
            if (order_list is None) or isinstance(order_list, bool):
                # Sort alphabetically
                def sort_key(child):
                    return child.get_name()

            else:
                # Sort according to given list
                def sort_key(child):
                    return order_list.index(child.get_name())

            file_list = [
                item for item in self._childlist if isinstance(item, File)
            ]
            folder_list = [
                item for item in self._childlist if isinstance(item, Folder)
            ]
            file_list.sort(key=sort_key)
            folder_list.sort(key=sort_key)
            self._childlist = folder_list + file_list  # noqa
            callback(callbackArg)
            return

        start_sorting()
        return

    def get_child_byName(
        self,
        name: str,
    ) -> Optional[
        Union[
            Item,
            _dashboard_items_.File,
            _dashboard_items_.Folder,
            Any,
        ]
    ]:
        """Get the requested child Item() from this Folder()-instance."""
        if self._childlist is None:
            purefunctions.printc(
                f"WARNING: self._childlist of dir {self.get_name()} was None",
                color="warning",
            )
            return None
        for item in self._childlist:
            if item.get_name() == name:
                return item
        return None

    def get_child_byRelpath(self, relpath: str) -> Optional[Item]:
        """"""
        if self._childlist is None:
            purefunctions.printc(
                f"WARNING: self._childlist of dir {self.get_name()} was None",
                color="warning",
            )
            return None
        for item in self._childlist:
            if item.get_relpath() == relpath:
                return item
        return None

    def get_depth(self) -> int:
        """"""
        return self._depth

    """----------------------------------------------------------------------------"""
    """ 3. CLICKS                                                                  """
    """----------------------------------------------------------------------------"""

    def toggle_open(self) -> None:
        """Open this Folder() if closed and vice versa.

        WARNING:
        The 'data.user_lock' gets locked during the act of opening/closing, so
        this method must only be invoked through direct user interaction!
        """
        if self.get_state().open:
            self.close_later(
                click=True,
                callback=None,
                callbackArg=None,
            )
            return
        self.open_later(
            click=True,
            callback=None,
            callbackArg=None,
        )
        return

    def open_all(
        self,
        click: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """TEST FUNCTION."""
        if click:
            if not data.user_lock.acquire(blocking=False):
                print("open_all() cannot acquire mutex")
                return

        def open_next(child_iter: Iterator[Item]) -> None:
            try:
                child = next(child_iter)
            except StopIteration:
                if click:
                    data.user_lock.release()
                if callback is not None:
                    callback(callbackArg)
                return
            if isinstance(child, Folder):
                child.open_all(
                    click=False,
                    callback=open_next,
                    callbackArg=child_iter,
                )
                return
            open_next(child_iter)
            return

        # * Start
        self.open_later(
            click=False,
            callback=open_next,
            callbackArg=iter(self.get_childlist()),
        )
        return

    def confirm_childlist(self) -> bool:
        """Confirm if childlist is okay.

        Only relevant for the Filetree.
        """
        return True

    def repair_childlist(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
        *args,
        **kwargs,
    ) -> None:
        """Repair one's childlist.

        Only relevant for the Filetree.
        """
        callback(callbackArg)
        return

    def open_later(
        self,
        click: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Open directory.

        :param click: Function initiated by user click.
        """
        if click:
            if not data.user_lock.acquire(blocking=False):
                if callback is not None:
                    callback(callbackArg)
                return
        if self._state.open:
            # -> oneself is already open.
            if click:
                data.user_lock.release()
            if callback is not None:
                callback(callbackArg)
            return
        if (self.get_parent() is not None) and (
            self.get_parent().get_state().open is False
        ):
            # -> parent already closed.
            if click:
                data.user_lock.release()
            if callback is not None:
                callback(callbackArg)
            return
        assert self._state.busyBtn is False

        def repair_start(*args) -> None:
            if not self.confirm_childlist():
                self.repair_childlist(
                    show=False,
                    recurse=False,
                    recurse_first_run=False,
                    update_libraries=True,
                    callback=open_lyt,
                    callbackArg=None,
                )
                return
            open_lyt()
            return

        def open_lyt(*args) -> None:
            # No need to run the init_guiVars() function before opening the lay-
            # out. Each child has its 'get_layout()' function called, which al-
            # ready initializes the GUI elements as needed.
            if len(self._childlist) > 0:
                self.get_layout().open_lyt_later(
                    callback=finish_a,
                    callbackArg=None,
                )
            else:
                finish_a()
            return

        def finish_a(*args) -> None:
            self._state.busyBtn = False
            self._state.forcePolish = True
            self._v_emitter.refresh_later_sig.emit(
                True,
                False,
                finish_b,
                None,
            )
            return

        def finish_b(*args):
            if click:
                data.user_lock.release()
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        self._state.open = True
        if len(self._childlist) > 20:
            self._state.busyBtn = True
        self._state.forcePolish = True
        self._v_emitter.refresh_later_sig.emit(
            True,
            False,
            repair_start,
            None,
        )
        return

    def close_later(
        self,
        click: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Close directory.

        :param click: Function initiated by user click.
        """
        if click:
            if not data.user_lock.acquire(blocking=False):
                if callback is not None:
                    callback(callbackArg)
                return
        if not self._state.open:
            # -> parent closure already closed this one.
            if click:
                data.user_lock.release()
            if callback is not None:
                callback(callbackArg)
            return
        assert self._state.busyBtn is False
        open_children = [
            folder
            for folder in self._childlist
            if isinstance(folder, Folder) and folder._state.open
        ]

        def close_next(folder_iter: Iterator[Folder]) -> None:
            try:
                open_folder = next(folder_iter)
            except StopIteration:
                self.get_layout().close_lyt_later(
                    callback=finish_a,
                    callbackArg=None,
                )
                return
            open_folder.close_later(
                click=False,
                callback=close_next,
                callbackArg=folder_iter,
            )
            return

        def finish_a(*args) -> None:
            self._state.open = False
            self._state.busyBtn = False
            self._state.forcePolish = True
            self._v_emitter.refresh_later_sig.emit(
                True,
                False,
                finish_b,
                None,
            )
            return

        def finish_b(*args) -> None:
            if click:
                data.user_lock.release()
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        if (len(open_children) > 0) or (len(self._childlist) > 20):
            self._state.busyBtn = True
        self._state.forcePolish = True
        self._v_emitter.refresh_later_sig.emit(
            True,
            False,
            close_next,
            iter(open_children),
        )
        return

    """----------------------------------------------------------------------------"""
    """ 4. SYNCHRONIZATIONS                                                        """
    """----------------------------------------------------------------------------"""

    def refresh_recursive_later(
        self,
        refreshlock: bool,
        force_stylesheet: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Refresh this Folder() and all children.

        > RECENT CHANGE (20 JULY 2020): REFRESH CHILDREN FIRST, THEN ONESELF
        This change whas needed for the dashboard, where parents sometimes
        depend their state on the children (eg. asterisk).
        """
        assert threading.current_thread() is threading.main_thread()
        if self.dead:
            purefunctions.printc(
                "WARNING: refresh_recursive_later() invoked on dead Folder()",
                color="warning",
            )
            callback(callbackArg)
            return

        # * Start
        if refreshlock:
            if not self.acquire_refresh_mutex():
                self._cntr += 1
                if self._cntr > 10:
                    print(
                        f"refresh_recursive_later() Folder({self.get_name()}) "
                        f"-> misses mutex"
                    )
                    self._cntr = 0
                qt.QTimer.singleShot(
                    150,
                    functools.partial(
                        self.refresh_recursive_later,
                        refreshlock,
                        force_stylesheet,
                        callback,
                        callbackArg,
                    ),
                )
                return

        def refresh_next(child_iter: Iterator[Union[Folder, File]]) -> None:
            try:
                child = next(child_iter)
            except StopIteration:
                super(Folder, self).refresh_later(
                    refreshlock=False,
                    force_stylesheet=force_stylesheet,
                    callback=finish,
                    callbackArg=None,
                )
                return
            child.refresh_recursive_later(
                refreshlock=False,
                force_stylesheet=force_stylesheet,
                callback=refresh_next,
                callbackArg=child_iter,
            )
            return

        def finish(*args) -> None:
            if refreshlock:
                self.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

        # * Start refresh cycle
        self._cntr = 0
        qt.QTimer.singleShot(
            5,
            functools.partial(
                refresh_next,
                iter(self._childlist),
            ),
        )
        return

    def rescale_recursive_later(
        self,
        refreshlock: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Rescale this Folder() and all VISIBLE(*) children.

        (*) When invisible children get visible (through opening their parent
        directory), they inherit scaling factors from the parent anyhow before
        being shown.
        """
        assert threading.current_thread() is threading.main_thread()
        if self.dead:
            purefunctions.printc(
                "WARNING: rescale_recursive_later() invoked on dead Folder()",
                color="warning",
            )
            callback(callbackArg)
            return

        # * Start
        if self._v_layout is None:
            if callback is not None:
                callback(callbackArg)
            return

        if refreshlock:
            if not self.acquire_refresh_mutex():
                self._cntr += 1
                if self._cntr > 10:
                    print(
                        f"rescale_recursive_later() Folder({self.get_name()}) "
                        f"-> misses mutex"
                    )
                    self._cntr = 0
                qt.QTimer.singleShot(
                    150,
                    functools.partial(
                        self.rescale_recursive_later,
                        refreshlock,
                        callback,
                        callbackArg,
                    ),
                )
                return

        def rescale_next(child_iter: Iterator[Union[Folder, File]]) -> None:
            try:
                child = next(child_iter)
            except StopIteration:
                super(Folder, self).rescale_later(
                    refreshlock=False,
                    callback=finish,
                    callbackArg=None,
                )
                return
            child.rescale_recursive_later(
                refreshlock=False,
                callback=rescale_next,
                callbackArg=child_iter,
            )
            return

        def finish(*args) -> None:
            if refreshlock:
                self.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

        # * Start rescale cycle
        self._cntr = 0
        qt.QTimer.singleShot(
            5,
            functools.partial(
                rescale_next,
                iter(self._childlist),
            ),
        )
        return

    """-------------------------------------------------------------------"""
    """ 5. DEATH  (ALWAYS RECURSIVE!)                                     """
    """-------------------------------------------------------------------"""

    def self_destruct(
        self,
        killParentLink: bool = True,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """
        Extension to the superclass function:
            > Close oneself if opened.
            > Kill all children recursively (call 'self_destruct()' on them).
            > Kill oneself (call 'self_destruct()' from the superclass on oneself).

        :param killParentLink: Remove this Folder()-instance from the parental childlist.
        :param callback:       Call at finish.
        :param callbackArg:    Argument to the callback.
        """
        if self._v_refreshMutex.locked():
            purefunctions.printc(
                f"WARNING: Trying to kill Folder({q}{self._name}{q}) while refresh mutex is locked!",
                color="warning",
            )
        assert threading.current_thread() is threading.main_thread()
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill Folder() {q}{self._name}{q} twice!"
                )
            self.dead = True
        assert self.get_state() is not None

        def try_closing(*args) -> None:
            assert threading.current_thread() is threading.main_thread()
            if self.get_state().open:
                self.close_later(
                    click=False,
                    callback=try_closing,
                    callbackArg=None,
                )
                return
            qt.QTimer.singleShot(
                10,
                functools.partial(kill_next, iter(reversed(self._childlist))),
            )
            return

        def kill_next(child_iter: Iterator[Union[Folder, File]]) -> None:
            assert threading.current_thread() is threading.main_thread()
            try:
                child = next(child_iter)
            except StopIteration:
                # Did 'killParentLink' work properly?
                assert self._childlist is not None
                assert len(self._childlist) == 0
                self._depth = None
                self._childlist = None
                super(Folder, self).self_destruct(
                    killParentLink=killParentLink,
                    callback=finish,
                    callbackArg=None,
                    death_already_checked=True,
                )
                return
            child.self_destruct(
                killParentLink=True,
                callback=kill_next,
                callbackArg=child_iter,
            )
            return

        def finish(*args) -> None:
            assert threading.current_thread() is threading.main_thread()
            if callback is not None:
                callback(callbackArg)
            return

        try_closing()
        return

    def kill_children_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Kill all children recursively."""
        cntr = 0

        def kill_next(child_iter: Iterator[Union[Folder, File]]) -> None:
            # Once in a while, a timer should be used to re-invoke this sub-
            # function. This avoids stack overflows.
            nonlocal cntr
            cntr += 1
            if cntr > 20:
                cntr = 0
                qt.QTimer.singleShot(
                    20,
                    functools.partial(
                        kill_next,
                        child_iter,
                    ),
                )
                return

            # Obtain the next child and kill it.
            try:
                child = next(child_iter)
            except StopIteration:
                # Make sure all children have been killed. Then invoke the call-
                # back and quit.
                assert len(self._childlist) == 0
                if callback is not None:
                    callback(callbackArg)
                return
            child.self_destruct(
                killParentLink=True,
                callback=kill_next,
                callbackArg=child_iter,
            )
            return

        self.close_later(
            click=False,
            callback=kill_next,
            callbackArg=iter(reversed(self._childlist)),
        )
        return

    def printFiles(self, spacer: str) -> None:
        """"""
        for item in self._childlist:
            if isinstance(item, Folder):
                print(spacer + "> " + item.get_relpath())
                item.printFiles(spacer + "    ")
            else:
                print(spacer + "- " + item.get_relpath())
        return


# ^                                              FILE                                              ^#
# % ============================================================================================== %#
# % File()-instance represents one file in the Filetree/Dashboard/...                              %#
# %                                                                                                %#


class File(Item):
    __slots__ = ()

    def __init__(
        self,
        rootdir: Root,
        parent: Folder,
        name: str,
        state: Item.Status,
    ) -> None:
        """The Dir()-instance holds two extra attributes in addition to those
        from its superclass Item: > self._childlist: An ordinary Python list
        with child items. > self._depth:    The nesting depth. Root directory
        has depth 0.

        :param rootdir: The Root()-instance at the top.       (*Note*)
        :param parent: The parent directory.                 (*Note*)
        :param state: A Status()-instance to start from. *Note: Only a weak
            reference to these parameters get stored.
        """
        super().__init__(rootdir, parent, name, state)
        return

    def init_layout(self) -> None:
        assert self._v_layout is None
        self._v_layout = _cm_layout_.FileLayout(file=self)
        return

    def get_depth(self):
        return self._parentRef().get_depth() + 1


# ^                                              ROOT                                              ^#
# % ============================================================================================== %#
# % Root()-instance represents a toplevel Folder() in Filetree/Dashboard/...                       %#
# %                                                                                                %#


class Root(ABC):
    @classmethod
    def get_slots(cls):
        return (
            "_abspath",  # Absolute path, other Item()-instances just
            # keep a relpath.
            "_v_chassisBody",  # The only reference to the chassis shell.
        )

    def __init__(self, abspath: str) -> None:
        """Root()-instance."""
        self._abspath = abspath
        self._v_chassisBody: Optional[
            weakref.ReferenceType[_chassis_body_.ChassisBody]
        ] = None
        return

    #! ==========[ ABSTRACT METHODS ]========== !#
    @abstractmethod
    def get_relpath(self) -> str:
        return "."

    @abstractmethod
    def get_abspath(self) -> str:
        return self._abspath

    @abstractmethod
    def set_abspath(self, abspath: str) -> None:
        self._abspath = abspath
        return

    @abstractmethod
    def get_parent(self) -> None:
        return None

    @abstractmethod
    def set_parent(self, parent: Folder) -> None:
        if parent is not None:
            raise RuntimeError()
        return

    @abstractmethod
    def get_rootdir(self) -> Root:
        return self

    @abstractmethod
    def get_chassis(self) -> _chassis_.Chassis:
        return self._v_chassisBody()._chassisRef()

    @abstractmethod
    def get_chassis_body(self) -> _chassis_body_.ChassisBody:
        return self._v_chassisBody()

    @abstractmethod
    def get_nr_visible_items(self) -> int:
        return self.get_layout().calc_nr_items()  # noqa

    @abstractmethod
    def self_destruct(
        self,
        killParentLink: bool = True,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        hdd_and_sa_op: bool = False,
        delete_from_hdd: bool = False,
        notify_project: bool = False,
        superfunc: Optional[Callable] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:  # noqa
                raise RuntimeError(
                    f"Trying to kill Root() {q}{self._name}{q} twice!"
                )  # noqa
            self.dead = True  # noqa

        def finish(arg):
            self._abspath = None
            self._v_chassisBody().body_remove_root(self)
            self._v_chassisBody = None
            if callback is not None:
                callback(callbackArg)
            return

        assert killParentLink is False
        superfunc(
            self,
            killParentLink=False,
            callback=finish,
            callbackArg=None,
            death_already_checked=True,
        )
        return

    #! ==========[ NORMAL METHODS ]========== !#
    def connect_chassis_body(self, chassis_body) -> None:
        # Gets called by the Chassis itself (in the add_root() function).
        self._v_chassisBody = weakref.ref(chassis_body)
        return

    def find_item(
        self,
        abspath: str,
        check: bool,
        update_libraries: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Find item, put it as first argument in the callback.

        :param abspath:          Absolute path to the item.
        :param check:            Check each item's childlist while browsing,
                                 do repairs when needed.
        :param update_libraries: While doing repairs, also update the libraries.

        Note: if this is called from a non-main thread, any reparation in the
        childlist won't be shown in the GUI immediately.

            > callback(found_item, callbackArg)
        """
        assert callback is not None

        def finish(chain, *args) -> None:
            if chain is None:
                callback(None, callbackArg)
                return
            if len(chain) > 0:
                callback(chain[-1], callbackArg)
                return
            callback(None, callbackArg)
            return

        self.get_item_chain(
            relpath=None,
            abspath=abspath,
            check=check,
            update_libraries=update_libraries,
            callback=finish,
            callbackArg=None,
        )
        return

    def get_item_chain(
        self,
        relpath: Optional[str],
        abspath: Optional[str],
        check: bool,
        update_libraries: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Find chain of items.

        :param relpath:     [Optional] Relative path to the item.
        :param abspath:     [Optional] Absolute path to the item.
        :param check:       Check each item's childlist while browsing, do
                            repairs when needed.
        :param update_libraries:  While checking, also update libraries.

        Note: if this is called from a non-main thread, any reparation in the
        childlist won't be shown in the GUI immediately.

            > callback(chain, callbackArg)
        """

        def chain_next(arg):
            _chain, _name_iter = arg
            try:
                name = next(_name_iter)
                item = _chain[-1].get_child_byName(name)
            except StopIteration:
                finish(_chain)
                return
            if item is None:
                abort()
                return
            _chain.append(item)

            # $ FOLDER
            if isinstance(item, Folder):
                if check:
                    if item.confirm_childlist():
                        chain_next((_chain, _name_iter))
                        return
                    item.repair_childlist(
                        show=threading.current_thread()
                        is threading.main_thread(),
                        recurse=False,
                        recurse_first_run=False,
                        update_libraries=update_libraries,
                        callback=chain_next,
                        callbackArg=(_chain, _name_iter),
                    )
                    return
                chain_next((_chain, _name_iter))
                return

            # $ FILE
            finish(_chain)
            return

        def abort(*args):
            callback(None, callbackArg)
            return

        def finish(_chain):
            callback(_chain, callbackArg)
            return

        # * ----[ START ]---- *#
        # * 1. Check input arguments
        # Only one of the two parameters can be provided.
        assert not ((relpath is None) is (abspath is None))
        if relpath is None:
            if not abspath.startswith(self._abspath):
                abort()
                return
            # Don't use '_pp_.abs_to_rel()' here, because that would invoke
            # 'os.path.realpath()' on the given 'abspath' parameter. That is
            # okay if we're dealing with Filetree-items, but not for Dashboard-
            # items!
            relpath = abspath.replace(self._abspath, "", 1)
            if relpath.startswith("/"):
                relpath = relpath[1:]

        # * 2. Convert 'relpath' into a 'list of item names'.
        item_names = []
        assert not relpath.startswith("/")
        assert not relpath.endswith("/")
        if relpath == ".":
            finish(
                [
                    self,
                ]
            )
            return
        item_names = relpath.split("/")

        # * 3. Start the sequence.
        chain = [
            self,
        ]
        name_iter = iter(item_names)
        if check:
            assert isinstance(self, Folder)
            if self.confirm_childlist():
                chain_next((chain, name_iter))
                return
            self.repair_childlist(
                show=threading.current_thread() is threading.main_thread(),
                recurse=False,
                recurse_first_run=False,
                update_libraries=update_libraries,
                callback=chain_next,
                callbackArg=(chain, name_iter),
            )
            return
        chain_next((chain, name_iter))
        return
