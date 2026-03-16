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

"""New Dashboard module for the Embeetle IDE.

This package contains the new dashboard implementation along with the tile
widget system.

The dashboard implementation follows the Model-View separation principle:

- data.dashboard_data: Stores the dashboard data. The format is defined in
                       `dashboard_data.py`.

- data.new_dashboard:  The `NewDashboard()`-widget serves as the View that
                       displays the data.
"""
