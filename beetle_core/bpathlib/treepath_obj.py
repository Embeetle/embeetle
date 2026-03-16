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
import dashboard
import bpathlib.path_obj as _po_
import hardware_api.treepath_unicum as _treepath_unicum_

if TYPE_CHECKING:
    import dashboard.items.path_items.treepath_items as _dashboard_treepath_items_
    import dashboard.items.item as _dashboard_items_
    import project.segments.path_seg.treepath_seg as _treepath_seg_
nop = lambda *a, **k: None


class TreepathObj(_po_.PathObj):
    def __init__(
        self,
        unicum: _treepath_unicum_.TREEPATH_UNIC,
        root_id: str,
        relpath: Optional[str],
        fake: bool,
    ) -> None:
        """A TreepathObj() represents one important dirpath/filepath.

        It is bound to a specific TreepathSeg()-instance (there's only one).
        """
        if relpath is not None:
            assert not relpath.startswith("<")
        assert root_id is not None
        assert root_id.startswith("<") and root_id.endswith(">")
        super().__init__(
            unicum=unicum,
            rootpath_or_rootid=root_id,
            relpath=relpath,
        )
        self._fake = fake
        return

    def create_dashboardItem(
        self,
        rootItem: Optional[_dashboard_items_.Root],
        parentItem: Optional[_dashboard_items_.Folder],
        *args,
        treepath_seg: Optional[_treepath_seg_.TreepathSeg] = None,
        **kwargs,
    ) -> _dashboard_treepath_items_.TreepathItem:
        """"""
        assert self._v_dashboardItem is None
        self._v_dashboardItem = (
            dashboard.items.path_items.treepath_items.TreepathItem(
                treepath_obj=self,
                treepath_seg=treepath_seg,
                rootdir=rootItem,
                parent=parentItem,
            )
        )
        assert self._v_dashboardItem.get_projSegment() is self
        return self._v_dashboardItem

    def is_file(self) -> bool:
        return self.get_unicum().get_dict()["is_file"]

    def is_default_fallback(self) -> bool:
        return self.get_unicum().get_dict()["default_fallback"]

    def get_searchpath(self) -> str:
        return self.get_unicum().get_dict()["searchpath"]

    def get_valid_names(self) -> List[str]:
        return self.get_unicum().get_dict()["valid_names"]

    def get_invalid_names(self) -> List[str]:
        return self.get_unicum().get_dict()["invalid_names"]

    def set_doublepath(
        self,
        doublepath: Optional[Tuple[Optional[str], Optional[str]]],
    ) -> None:
        """Check the given 'doublepath' before passing it to the superclass."""
        rootid, relpath = doublepath
        assert rootid.startswith("<") and rootid.endswith(">")
        if relpath is not None:
            assert not relpath.startswith("<")
        super().set_doublepath(doublepath)
        return

    def set_relpath(self, relpath: Optional[str]) -> None:
        raise NotImplementedError()

    def set_abspath(self, abspath: Optional[str]) -> None:
        raise NotImplementedError()

    def is_fake(self) -> bool:
        return self._fake
