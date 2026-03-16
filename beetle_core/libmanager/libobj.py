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
import functions, functools, purefunctions
import qt, data, traceback
import dashboard.items.lib_items.lib_item as _da_lib_items_
import project.segments.project_segment as _ps_
import bpathlib.path_power as _pp_
import home_libraries.items.lib_item as _home_lib_items_

if TYPE_CHECKING:
    import project.segments.lib_seg.lib_seg as _lib_seg_
    import home_libraries.items.lib_root_item as _lib_root_item_
from various.kristofstuff import *


class LibObj(_ps_.ProjectSubsegment):
    """A LibObj()-instance represents A SPECIFIC LIBRARY IN A SPECIFIC LOCATION.

    In other words, it
    should NOT be shared between two libraries in different locations - even if they have the same
    name and are of the same version!
    """

    __slots__ = (
        "__name",
        "__version",
        "__author",
        "__sentence",
        "__paragraph",
        "__mod_name",
        "__mod_author",
        "__mod_sentence",
        "__mod_paragraph",
        "__depends",
        "__category",
        "__web_url",
        "__architectures",
        "__proj_relpath",
        "__local_abspath",
        "__zip_url",
        "__origin",
        "_v_dashboard_item",
        "_v_home_item",
    )

    def __init__(
        self,
        name: str,  # original name
        version: str,  # original version
        author: str,  # original author
        sentence: str,  # original sentence
        paragraph: str,  # original paragraph
        mod_name: Optional[str],  # modified name
        mod_author: Optional[str],  # modified author
        mod_sentence: Optional[str],  # modified sentence
        mod_paragraph: Optional[str],  # modified paragraph
        depends: Optional[List[str]],  # list of dependencies
        category: str,  # category
        web_url: Optional[str],  # website url
        architectures: Optional[List[str]],  # architectures
        proj_relpath: Optional[
            str
        ],  # relative path in current project, including '<project>'
        local_abspath: Optional[str],  # absolute path to local storage
        zip_url: Optional[str],  # url to online zipfile
        origin: str,  # 'proj_relpath', 'local_abspath' or 'zip_url'
    ) -> None:
        """Create LibObj()-instance.

        NOTE:
        Several locations can be given, eg. proj_relpath, local_abspath and zip_url. However, only
        one of them acts as the representative location for this LibObj()-instance. Which one is
        given by the 'origin' attribute.
        """
        super().__init__()
        self.__name = name
        self.__version = version
        self.__author = author
        self.__sentence = sentence
        self.__paragraph = paragraph
        self.__mod_name = mod_name
        self.__mod_author = mod_author
        self.__mod_sentence = mod_sentence
        self.__mod_paragraph = mod_paragraph
        self.__depends = depends
        self.__category = category
        self.__web_url = web_url
        self.__architectures = architectures
        self.__proj_relpath = proj_relpath
        self.__local_abspath = local_abspath
        self.__zip_url = zip_url
        self.__origin = origin
        self._v_dashboard_item: Optional[_da_lib_items_.LibItem] = None
        self._v_home_item: Optional[_home_lib_items_.LibItem] = None
        assert (
            origin == "proj_relpath"
            or origin == "local_abspath"
            or origin == "zip_url"
        ), f"origin = {origin}"
        if (proj_relpath is not None) and (proj_relpath.lower() != "none"):
            assert proj_relpath.startswith("<")
        if depends is not None:
            assert isinstance(depends, list)
            for t in depends:
                assert isinstance(t, str)
        return

    def modify(
        self,
        name: str,  # original name
        version: str,  # original version
        author: str,  # original author
        sentence: str,  # original sentence
        paragraph: str,  # original paragraph
        mod_name: Optional[str],  # modified name
        mod_author: Optional[str],  # modified author
        mod_sentence: Optional[str],  # modified sentence
        mod_paragraph: Optional[str],  # modified paragraph
        depends: Optional[List[str]],  # list of dependencies
        category: str,  # category
        web_url: Optional[str],  # website url
        architectures: Optional[List[str]],  # architectures
        proj_relpath: Optional[
            str
        ],  # relative path in current project, including '<project>'
        local_abspath: Optional[str],  # absolute path to local storage
        zip_url: Optional[str],  # url to online zipfile
        origin: str,  # 'proj_relpath', 'local_abspath' or 'zip_url'
    ) -> None:
        """Modify this LibObj()"""
        # * Sanitize input
        if name != self.__name:
            purefunctions.printc(
                f"WARNING: attempt to change name of LibObj() {self.__name}",
                color="warning",
            )
        self.__name = name
        self.__version = version
        self.__author = author
        self.__sentence = sentence
        self.__paragraph = paragraph
        self.__mod_name = mod_name
        self.__mod_author = mod_author
        self.__mod_sentence = mod_sentence
        self.__mod_paragraph = mod_paragraph
        self.__depends = depends
        self.__category = category
        self.__web_url = web_url
        self.__architectures = architectures
        self.__proj_relpath = proj_relpath
        self.__local_abspath = local_abspath
        self.__zip_url = zip_url
        self.__origin = origin
        assert (
            origin == "proj_relpath"
            or origin == "local_abspath"
            or origin == "zip_url"
        ), f"origin = {origin}"
        if (proj_relpath is not None) and (proj_relpath.lower() != "none"):
            assert proj_relpath.startswith("<")
        if depends is not None:
            assert isinstance(depends, list)
            for t in depends:
                assert isinstance(t, str)
        return

    def modify_from_propdict(self, propdict: Dict) -> None:
        """Modify this LibObj() according to the given properties dictionary.

        WARNING ======= If you change anything here, also change the function
        '__create_libobj_from_propdict()' in 'libmanager.py'.
        """
        self.modify(
            name=propdict["name"] if "name" in propdict else "None",
            version=propdict["version"] if "version" in propdict else "None",
            author=propdict["author"] if "author" in propdict else "None",
            sentence=propdict["sentence"] if "sentence" in propdict else "None",
            paragraph=(
                propdict["paragraph"] if "paragraph" in propdict else "None"
            ),
            mod_name=None,
            mod_author=None,
            mod_sentence=None,
            mod_paragraph=None,
            depends=propdict["depends"] if "depends" in propdict else None,
            category=propdict["category"] if "category" in propdict else None,
            web_url=propdict["web_url"] if "web_url" in propdict else None,
            architectures=(
                propdict["architectures"]
                if "architectures" in propdict
                else None
            ),
            proj_relpath=(
                propdict["proj_relpath"]
                if "architectures" in propdict
                else None
            ),
            local_abspath=(
                propdict["local_abspath"]
                if "proj_relpath" in propdict
                else None
            ),
            zip_url=propdict["zip_url"] if "zip_url" in propdict else None,
            origin=propdict["origin"],
        )
        return

    def get_name(self) -> str:
        return self.__name

    def get_version(self) -> str:
        return self.__version

    def get_author(self) -> str:
        return self.__author

    def get_sentence(self) -> str:
        return self.__sentence

    def get_paragraph(self) -> str:
        return self.__paragraph

    def get_mod_name(self) -> Optional[str]:
        return self.__mod_name

    def get_mod_author(self) -> Optional[str]:
        return self.__mod_author

    def get_mod_sentence(self) -> Optional[str]:
        return self.__mod_sentence

    def get_mod_paragraph(self) -> Optional[str]:
        return self.__mod_paragraph

    def get_depends(self) -> Optional[List[str]]:
        return self.__depends

    def get_category(self) -> str:
        return self.__category

    def get_web_url(self) -> Optional[str]:
        return self.__web_url

    def get_architectures(self) -> Optional[List[str]]:
        return self.__architectures

    def get_zip_url(self) -> Optional[str]:
        return self.__zip_url

    def get_proj_relpath(self) -> Optional[str]:
        return self.__proj_relpath

    def get_proj_abspath(self) -> Optional[str]:
        if self.__proj_relpath is None:
            return None
        if data.is_home:
            return None
        assert self.__proj_relpath.startswith("<")
        rootid, relpath = purefunctions.strip_rootid(
            prefixed_relpath=self.__proj_relpath,
        )
        # Obtain the rootpath belonging to this LibObj().
        rootpath = data.current_project.get_rootpath_from_rootid(
            rootid=rootid,
            suppress_warnings=False,
        )
        if rootpath is None:
            return None
        return _pp_.rel_to_abs(
            rootpath=rootpath,
            relpath=relpath,
        )

    def get_proj_rootpath(self) -> Optional[str]:
        if self.__proj_relpath is None:
            return None
        if data.is_home:
            return None
        assert self.__proj_relpath.startswith("<")
        rootid, relpath = purefunctions.strip_rootid(
            prefixed_relpath=self.__proj_relpath,
        )
        rootpath = data.current_project.get_rootpath_from_rootid(
            rootid=rootid,
            suppress_warnings=True,
        )
        return rootpath

    def get_local_abspath(self) -> Optional[str]:
        return self.__local_abspath

    def get_origin(self) -> str:
        return self.__origin

    def set_mod_name(self, mod_name: Optional[str]) -> None:
        self.__mod_name = mod_name

    def set_mod_author(self, mod_author: Optional[str]) -> None:
        self.__mod_author = mod_author

    def set_mod_sentence(self, mod_sentence: Optional[str]) -> None:
        self.__mod_sentence = mod_sentence

    def set_mod_paragraph(self, mod_paragraph: Optional[str]) -> None:
        self.__mod_paragraph = mod_paragraph

    def get_dashboard_item(
        self,
        parent_seg: _lib_seg_.LibSeg,
    ) -> _da_lib_items_.LibItem:
        """Return the corresponding Dashboard LibItem()-instance."""
        assert not data.is_home
        if self._v_dashboard_item is None:
            self._v_dashboard_item = _da_lib_items_.LibItem(
                libobj=self,
                rootdir=parent_seg._v_rootItem,
                parent=parent_seg._v_rootItem,
            )
        return self._v_dashboard_item

    def get_hometab_item(
        self,
        parent_root_item: _lib_root_item_.LibCategoryRootItem,
    ) -> _home_lib_items_.LibItem:
        """Return the corresponding Home Window LibItem()-instance."""
        assert data.is_home
        if self._v_home_item is None:
            self._v_home_item = _home_lib_items_.LibItem(
                libobj=self,
                rootdir=parent_root_item,
                parent=parent_root_item,
            )
        return self._v_home_item

    def go_to_website(self) -> None:
        """"""
        try:
            functions.open_url(self.get_web_url())
        except Exception as e:
            traceback.print_exc()
        return

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """Destroy this LibObj()-instance and its LibItem()(s) in the Dashboard
        or Home Window.

        > callback(callbackArg)
        """
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill LibObj() {q}{self.__name}{q} twice!"
                )
            self.dead = True

        # Supercall not needed. Nothing really happens there.
        # super().self_destruct(...)

        def finish(*args) -> None:
            "Kill all attributes"
            self._v_dashboard_item = None
            self._v_home_item = None
            self.__name = None
            self.__version = None
            self.__author = None
            self.__sentence = None
            self.__paragraph = None
            self.__mod_name = None
            self.__mod_author = None
            self.__mod_sentence = None
            self.__mod_paragraph = None
            self.__depends = None
            self.__category = None
            self.__web_url = None
            self.__architectures = None
            self.__proj_relpath = None
            self.__local_abspath = None
            self.__zip_url = None
            self.__origin = None
            if callback is not None:
                qt.QTimer.singleShot(
                    10,
                    functools.partial(
                        callback,
                        callbackArg,
                    ),
                )
            return

        # * Start
        # & -----------------[ PROJECT MODE ]------------------ *#
        # Kill the Dashboard LibItem() belonging to this LibObj().
        if not data.is_home:
            assert self._v_home_item is None
            # Take shortcut if there are no dashboard items for this library.
            if self._v_dashboard_item is None:
                finish()
                return
            self._v_dashboard_item.self_destruct(
                killParentLink=True,
                callback=finish,
                callbackArg=None,
            )
            return

        # & ----------------[ HOME MODE ]---------------- *#
        # Kill the Home LibItem(). See 'home_libraries/items/lib_item.py'.
        assert self._v_dashboard_item is None
        assert data.is_home
        self._v_home_item.self_destruct(
            killParentLink=True,
            callback=finish,
            callbackArg=None,
        )
        return

    def printout(self) -> None:
        """Print info about this LibObj()."""
        print(self.get_name())
        return
