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
from components.decorators import ref
import functools, threading, weakref
import qt, data, purefunctions, functions, iconfunctions
import gui.templates.basemenu
import gui.stylesheets.menu as _popstyle_

if TYPE_CHECKING:
    import tree_widget.items.item as _cm_item_
from various.kristofstuff import *

# ^                                       CONTEXT_MENU_COMP                                        ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class ContextMenuComp(object):
    def __init__(
        self,
        contextmenu_root: ContextMenuRoot,
        parent: ContextMenuNode,
        text: str,
        key: str,
    ) -> None:
        """"""
        self.__rootRef = weakref.ref(contextmenu_root)
        self.__parentRef = weakref.ref(parent) if parent is not None else None
        self.__text = text
        self.__key = key
        self.dead = False
        self.triggered.connect(self.leftclick)  # noqa
        self._childkill_mutex = threading.Lock()
        return

    @ref
    def get_parent(self) -> Optional[ContextMenuNode]:
        return self.__parentRef  # noqa

    @ref
    def get_contextmenu_root(self) -> ContextMenuRoot:
        return self.__rootRef  # noqa

    def get_key(self) -> str:
        return self.__key

    def set_key(self, key: str) -> None:
        self.__key = key
        return

    def get_text(self) -> str:
        return self.__text

    def set_text(self, text: str) -> None:
        self.__text = text
        return

    """
    1. ITEM AND OWNER API
    """

    def get_item(self) -> _cm_item_.Item:
        return self.get_contextmenu_root().get_item()

    def is_item_visible(self) -> bool:
        return self.get_contextmenu_root().is_item_visible()

    def get_itemRefreshMutex(self) -> threading.Lock:
        return self.get_contextmenu_root().get_itemRefreshMutex()

    """
    2. CLICKS (inside popup)
    """

    def leftclick(self, *args, **kwargs) -> None:
        """"""
        key = (
            f"{self.get_key()}/{kwargs['key']}"
            if "key" in kwargs
            else self.get_key()
        )
        self.get_parent().leftclick(key=key)
        return

    """
    4. DEATH
    """

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill ContextMenuComp() {q}{self.__key}{q} twice!"
                )
            self.dead = True

        # * Start
        my_parent = self.get_parent()
        assert threading.current_thread() is threading.main_thread()
        if isinstance(self, ContextMenuNode):
            assert len(self.get_childlist()) == 0
            assert len(self.actions()) == 0
        assert (
            (self in my_parent.get_childlist())
            if (my_parent is not None)
            else True
        )
        try:
            self.triggered.disconnect()
        except:
            pass

        # * Kill parent link
        if my_parent is None:
            assert isinstance(self, ContextMenuRoot)
            assert self.get_contextmenu_root() is self
            # * Finish
            self.__rootRef = None
            self.__parentRef = None
            self.__text = None
            self.__key = None
            self.deleteLater()
            if callback is not None:
                callback(callbackArg)
            return

        i1 = len(my_parent.actions())
        i2 = len(my_parent.get_childlist())
        if i1 > i2:
            # Possibly a separater was added, which is not really a child
            for _a in my_parent.actions():
                if _a.isSeparator():
                    my_parent.removeAction(_a)
                    _a.deleteLater()
        i1 = len(my_parent.actions())
        i2 = len(my_parent.get_childlist())
        assert i1 == i2
        i = i1
        my_parent.remove_child(self)
        j1 = len(my_parent.actions())
        j2 = len(my_parent.get_childlist())
        assert j1 == j2
        j = j1
        assert j == (i - 1)

        # * Finish
        self.__rootRef = None
        self.__parentRef = None
        self.__text = None
        self.__key = None
        self.deleteLater()
        if callback is not None:
            callback(callbackArg)
        return


# ^                                       CONTEXT_MENU_NODE                                        ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class ContextMenuNode(ContextMenuComp, gui.templates.basemenu.BaseMenu):
    def __init__(
        self,
        contextmenu_root: ContextMenuRoot,
        parent: Optional[ContextMenuNode],
        text: Optional[str],
        key: str,
        iconpath: Optional[str],
    ) -> None:
        """A ContextMenuNode()-instance has a childlist to hold other menu
        instances.

        :param contextmenu_root: The ContextMenuRoot()-instance at the top.
            (*Note*)
        :param parent: The parent ContextMenuNode()-instance.     (*Note*)
        :param text: The text string to show.
        :param key: The identifier for click signals.
        :param iconpath: Relative path to icon. *Note: Only a weak reference to
            these parameters gets stored.
        """
        # Super() constructors
        # QMenu.__init__(self, title='{0}'.format(text), parent=parent)   if ((text is not None) and (parent is not None) and (iconpath is None)) else nop()
        (
            gui.templates.basemenu.BaseMenu.__init__(
                self, title="{0}".format(text), parent=parent
            )
            if ((text is not None) and (parent is not None))
            else nop()
        )
        (
            gui.templates.basemenu.BaseMenu.__init__(
                self, title="{0}".format(text)
            )
            if ((text is not None) and (parent is None))
            else nop()
        )
        (
            gui.templates.basemenu.BaseMenu.__init__(self, parent=parent)
            if ((text is None) and (parent is not None))
            else nop()
        )
        (
            gui.templates.basemenu.BaseMenu.__init__(self)
            if ((text is None) and (parent is None))
            else nop()
        )
        (
            self.setIcon(iconfunctions.get_qicon(iconpath))
            if iconpath is not None
            else nop()
        )
        ContextMenuComp.__init__(
            self,
            contextmenu_root,
            parent,
            text,
            key,
        )
        self._childlist: List[
            Union[
                ContextMenuComp,
                ContextMenuNode,
                ContextMenuLeaf,
                ContextMenuTopleaf,
            ]
        ] = []
        return

    def set_icon(self, iconpath: str) -> None:
        """"""
        if iconpath is not None:
            self.setIcon(iconfunctions.get_qicon(iconpath))
        return

    def set_text(self, text: str) -> None:
        """"""
        ContextMenuComp.set_text(self, text)
        gui.templates.basemenu.BaseMenu.setTitle(self, text)
        return

    def add_child(
        self,
        menuItem: Union[
            ContextMenuComp,
            ContextMenuNode,
            ContextMenuLeaf,
            ContextMenuTopleaf,
        ],
    ) -> None:
        """"""
        if isinstance(menuItem, qt.QMenu):
            self.addMenu(menuItem)
        elif isinstance(menuItem, qt.QWidgetAction) or isinstance(
            menuItem, qt.QAction
        ):
            if isinstance(menuItem, ContextMenuLeaf):
                # I put this inner if-statement here to let PyCharm know that a QWidgetAction() can
                # be also a ContextMenuLeaf()-object.
                pass
            self.addAction(menuItem)
        else:
            raise RuntimeError(f"ERROR: added item is {q}{menuItem}{q}")
        self._childlist.append(menuItem)
        if menuItem.get_parent() is not None:
            assert menuItem.get_parent() is self
        return

    def remove_child(
        self,
        menuItem: Union[
            ContextMenuComp,
            ContextMenuNode,
            ContextMenuLeaf,
            ContextMenuTopleaf,
        ],
    ) -> None:
        """"""
        if isinstance(menuItem, qt.QMenu):
            self.removeAction(menuItem.menuAction())
            assert menuItem.menuAction() not in self.actions()
        elif isinstance(menuItem, qt.QWidgetAction) or isinstance(
            menuItem, qt.QAction
        ):
            if isinstance(menuItem, ContextMenuLeaf):
                # I put this inner if-statement here to let PyCharm know that a QWidgetAction() can
                # be also a ContextMenuLeaf()-object.
                pass
            self.removeAction(menuItem)
            assert menuItem not in self.actions()
        else:
            assert False
        self._childlist.remove(menuItem)
        menuItem.setParent(None)  # noqa
        # menuItem.deleteLater() -> happens in the menuItem's self_destruct function!
        return

    def has_child(
        self,
        menuItem: Union[
            ContextMenuComp,
            ContextMenuNode,
            ContextMenuLeaf,
            ContextMenuTopleaf,
        ],
    ) -> bool:
        """"""
        return menuItem in self._childlist

    def get_child(
        self,
        key: str,
    ) -> Union[
        ContextMenuComp,
        ContextMenuNode,
        ContextMenuLeaf,
        ContextMenuTopleaf,
        None,
    ]:
        """"""
        for child in self._childlist:
            if child.get_key() == key:
                return child
        return None

    def get_childIter(
        self,
    ) -> Iterator[
        ContextMenuComp, ContextMenuNode, ContextMenuLeaf, ContextMenuTopleaf
    ]:
        return iter(self._childlist)

    def get_childlist(
        self,
    ) -> List[
        ContextMenuComp, ContextMenuNode, ContextMenuLeaf, ContextMenuTopleaf
    ]:
        return self._childlist

    def kill_children(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        if not self._childkill_mutex.acquire(blocking=False):
            return

        def kill_next(menuItem_iter: Iterator[ContextMenuComp]) -> None:
            try:
                menuItem = next(menuItem_iter)
                assert menuItem in self._childlist
            except StopIteration:
                # * Finish
                assert len(self._childlist) == 0
                assert len(self.actions()) == 0
                self._childkill_mutex.release()
                if callback is not None:
                    callback(callbackArg)
                return

            # Also child's link to the parent (oneself) is destroyed.
            menuItem.self_destruct(
                callback=kill_next,
                callbackArg=menuItem_iter,
            )
            return

        # * Start
        qt.QTimer.singleShot(
            10,
            functools.partial(kill_next, iter(reversed(self._childlist))),
        )
        return

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill ContextMenuNode() {q}{self.get_key()}{q} twice!"
                )
            self.dead = True
        my_parent = self.get_parent()

        def finish_kill(*args) -> None:
            assert len(self._childlist) == 0
            assert len(self.actions()) == 0
            assert (
                self in my_parent.get_childlist()
                if my_parent is not None
                else True
            )
            super(ContextMenuNode, self).self_destruct(
                callback=finish,
                callbackArg=None,
                death_already_checked=True,
            )
            return

        def finish(*args) -> None:
            assert (
                self not in my_parent.get_childlist()
                if my_parent is not None
                else True
            )
            self._childlist = None
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        self.kill_children(
            callback=finish_kill,
            callbackArg=None,
        )
        return


# ^                                       CONTEXT_MENU_LEAF                                        ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class ContextMenuLeaf(ContextMenuComp, qt.QWidgetAction):
    def __init__(
        self,
        contextmenu_root: ContextMenuRoot,
        parent: ContextMenuNode,
        text: str,
        key: str,
        iconpath: Optional[str],
    ) -> None:
        """A ContextMenuLeaf()-instance is a leaf, it cannot hold other menu
        instances.

        :param contextmenu_root: The ContextMenuRoot()-instance at the top.
            (*Note*)
        :param parent: The parent ContextMenuNode()-instance. (*Note*)
        :param text: The text string to show.
        :param key: The identifier for click signals.
        :param iconpath: Relative path to icon. *Note: Only a weak reference to
            these parameters gets stored.
        """
        qt.QWidgetAction.__init__(self, parent)
        self._frm = qt.QFrame()
        self._lyt = qt.QHBoxLayout()
        self._frm.setLayout(self._lyt)
        self._frm.setStyleSheet(_popstyle_.get_menuFileFrm_stylesheet())
        self._lyt.setSpacing(0)
        self._lyt.setContentsMargins(0, 0, 0, 0)
        self._lyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        if iconpath is not None:
            self._btn = qt.QPushButton()
            self._btn.setStyleSheet(_popstyle_.get_menuFileBtn_stylesheet())
            self._btn.setIcon(iconfunctions.get_qicon(iconpath))
            # Catching clicks in the button and relaying them to
            # self.leftclick() also works, but it causes the popup
            # to reappear after a short blink.
            self._btn.setAttribute(
                qt.Qt.WidgetAttribute.WA_TransparentForMouseEvents
            )
            self._btnIcon = iconpath
        else:
            self._btn = None
            self._btnIcon = None
        if text is not None:
            self._lbl = qt.QLabel(text)
            text_color = data.theme["fonts"]["default"]["color"]
            self._lbl.setStyleSheet(
                _popstyle_.get_menuFileLbl_stylesheet(color=text_color)
            )
        else:
            self._lbl = None
        self._lyt.addWidget(self._btn) if self._btn is not None else nop()
        self._lyt.addWidget(self._lbl) if self._lbl is not None else nop()
        self.setDefaultWidget(self._frm)
        ContextMenuComp.__init__(
            self,
            contextmenu_root,
            parent,
            text,
            key,
        )
        return

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill ContextMenuLeaf() {q}{self.get_key()}{q} twice!"
                )
            self.dead = True
        my_parent = self.get_parent()

        def finish(*args) -> None:
            assert self not in my_parent.get_childlist()
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        if self._btn is not None:
            self._btn.setParent(None)
            self._btn.deleteLater()
            self._btn = None
        if self._lbl is not None:
            self._lbl.setParent(None)
            self._lbl.deleteLater()
        self._frm.setParent(None)  # noqa
        self._frm.deleteLater()

        # * Finish kill
        if not self in my_parent.get_childlist():
            assert False
        super(ContextMenuLeaf, self).self_destruct(
            callback=finish,
            callbackArg=None,
            death_already_checked=True,
        )
        return


# ^                                      CONTEXT_MENU_TOPLEAF                                      ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class ContextMenuTopleaf(ContextMenuComp, qt.QAction):
    def __init__(
        self,
        contextmenu_root: ContextMenuRoot,
        parent: ContextMenuNode,
        text: str,
        key: str,
        iconpath: str,
    ) -> None:
        """A ContextMenuTopleaf()-instance is a leaf, it cannot hold other menu
        instances.

        :param contextmenu_root: The ContextMenuRoot()-instance at the top.
            (*Note*)
        :param parent: The parent ContextMenuNode()-instance.     (*Note*)
        :param text: The text string to show.
        :param key: The identifier for click signals.
        :param iconpath: Relative path to icon. *Note: Only a weak reference to
            these parameters gets stored.
        """
        qt.QAction.__init__(
            self,
            iconfunctions.get_qicon(iconpath),
            f"{text}",
            parent,
        )
        ContextMenuComp.__init__(
            self,
            contextmenu_root,
            parent,
            text,
            key,
        )
        return

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill ContextMenuTopleaf() {q}{self.get_key()}{q} twice!"
                )
            self.dead = True
        my_parent = self.get_parent()

        def finish(*args) -> None:
            assert self not in my_parent.get_childlist()
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        assert self in my_parent.get_childlist()
        super(ContextMenuTopleaf, self).self_destruct(
            callback=finish,
            callbackArg=None,
            death_already_checked=True,
        )
        return


# ^                                       CONTEXT_MENU_ROOT                                        ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class ContextMenuRoot(ContextMenuNode):
    contextmenuclick_signal = qt.pyqtSignal(str)

    def __init__(
        self,
        widg: Optional[qt.QWidget],
        item: Optional[_cm_item_.Item],
        toplvl_key: str,
        clickfunc: Callable,
    ) -> None:
        """The ContextMenuRoot()-instance is the actual popup. Subclass this
        class to create a popup.

        :param widg: [Optional] Widget launching this context menu. Some context
            menus like to know that when they form themselves.
        :param item: [Optional] Item owning the widget that launches this
            context menu. Some context menus like to know when forming
            themselves.
        :param toplvl_key: The launched context menu invokes the given
            'clickfunc' and passes it a chain of keys. The toplevel key is the
            one given here.
        :param clickfunc: Function to be called when the user clicks an entry in
            this context menu. The function must accept a chain of keys (string
            with '/' between keys).
        """
        super().__init__(
            contextmenu_root=self,
            parent=None,
            text=None,
            key=toplvl_key,
            iconpath=None,
        )
        self.__widget_ref = weakref.ref(widg) if widg is not None else None
        self.__item_ref = weakref.ref(item) if item is not None else None
        self.contextmenuclick_signal.connect(clickfunc)
        return

    def get_parent(self) -> Optional[ContextMenuNode]:
        """"""
        return None

    def get_contextmenu_root(self) -> ContextMenuRoot:
        """"""
        return self

    def show_popup(self) -> None:
        """"""
        self.exec(qt.QCursor.pos())
        return

    def get_item(self) -> Optional[_cm_item_.Item]:
        """Access the Item() behind the ItemWidget() owning this popup."""
        if self.__item_ref is None:
            return None
        return self.__item_ref()

    def is_item_visible(self) -> bool:
        """"""
        if self.get_item() is None:
            return False
        if hasattr(self.get_item(), "_v_layout") and (
            self.get_item()._v_layout is None
        ):
            return False
        return True

    def get_itemRefreshMutex(self) -> threading.Lock:
        """"""
        return self.get_item()._v_refreshMutex

    """
    2. CLICKS (inside popup)
    """

    def leftclick(self, *args, **kwargs) -> None:
        """"""
        key = (
            "{0}/{1}".format(self.get_key(), kwargs["key"])
            if "key" in kwargs
            else None
        )
        if key is None:
            return
        self.contextmenuclick_signal.emit(key)
        return

    """
    4. DEATH
    """

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """Used to disconnect signals in a loop.

        Not needed anymore.
        """
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill ContextMenuRoot() {q}{self.get_key()}{q} twice!"
                )
            self.dead = True

        def finish(*args) -> None:
            self.__widget_ref = None
            self.__item_ref = None
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        try:
            self.contextmenuclick_signal.disconnect()
        except TypeError as e:
            purefunctions.printc(
                "ERROR: Could not disconnect self.contextmenuclick_signal",
                color="error",
            )
        super(ContextMenuRoot, self).self_destruct(
            callback=finish,
            callbackArg=None,
            death_already_checked=True,
        )
        return
