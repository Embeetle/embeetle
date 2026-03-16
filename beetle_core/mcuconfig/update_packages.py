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

import json
import os
import shutil


def update_packages(path):
    package_dir = f"{path}/packages"
    shutil.rmtree(package_dir, ignore_errors=True)
    os.makedirs(package_dir, exist_ok=True)
    with open(f"{path}/packages.json") as file:
        data = json.load(file)
    for package_name, package_data in data.get("packages").items():
        package_data["name"] = package_name
        print(f"{package_name} {package_data}")
        with open(f"{package_dir}/{package_name}.json", "w") as file:
            json.dump(package_data, file)


if __name__ == "__main__":
    update_packages(f"{os.path.dirname(__file__)}/resources")
