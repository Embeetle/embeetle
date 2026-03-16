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

# Standard library
import os
import sys
import pathlib

# Local imports
import qt
import data
import themes
import iconfunctions
import chipconfigurator.widgets
import gui.stylesheets.tooltip
import gui.stylesheets.mainwindow


class Window(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("Form")
        self.setWindowTitle("Chip-Configurator testing window")
        self.resize(1300, 800)

        layout = qt.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.chip_configurator_window = (
            chipconfigurator.widgets.ChipConfiguratorWindow(
                parent=self,
                main_form=None,
                project_path="",
            )
        )
        # Select series and chip
        series_json_file = os.path.join(
            data.beetle_core_directory,
            "mcuconfig/resources/series/APM32F411/chip_config.json5",
        )
        self.chip_configurator_window.load(
            series_json_file,
            "APM32F411VCT6",
        )

        self.layout().addWidget(self.chip_configurator_window)

        self.setStyleSheet(gui.stylesheets.mainwindow.get_default())


def main():
    print("Testing Embeetle Chip-Configurator tool ...")

    data.theme = themes.get("air")
    iconfunctions.update_style()

    app = qt.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
