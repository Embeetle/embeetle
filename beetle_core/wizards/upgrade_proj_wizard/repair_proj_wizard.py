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
import wizards.upgrade_proj_wizard.upgrade_or_repair_wizard as _upgrade_or_repair_wizard_

if TYPE_CHECKING:
    import qt


class RepairProjWizard(_upgrade_or_repair_wizard_.UpgradeOrRepairWizard):
    """"""

    def __init__(
        self,
        parent: Optional[qt.QWidget],
        cur_version: int,
        new_version: int,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Create RepairProjWizard()."""
        super().__init__(
            parent=parent,
            cur_version=cur_version,
            new_version=new_version,
            role="repair",
            callback=callback,
            callbackArg=callbackArg,
        )
        return
