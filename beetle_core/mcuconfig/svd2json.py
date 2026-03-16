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

"""
The CMSIS-SVD format is described at
https://arm-software.github.io/CMSIS_5/SVD/html/svd_Format_pg.html

The cmsis_svd Python package does most of the heavy lifting, such as handling
derived_from attributes and default values.  Here, we do limited additional
checking and convert to json.
"""

import cmsis_svd.parser
import json


def load_file(svd_path):
    try:
        svd = cmsis_svd.parser.SVDParser.for_xml_file(
            svd_path, remove_reserved=True
        ).get_device()
    except TypeError as error:
        raise ConfigError(f"{svd_path}: {error}")
    return svd


def svd2json(svd_path: str):
    print(f"convert {svd_path} to json")
    svd = load_file(svd_path)
    return {
        "series": svd.name,
        "vendor": svd.vendor,
        "parts": [],
        "pads": {},
        "pad_types": {},
        "pad_config": {},
        "clocks": {},
        "peripherals": {},
        "svd_data": {
            "filename": svd_path,
            "version": svd.version,
            "address_unit_bits": svd.address_unit_bits,
            "peripherals": {
                peripheral_svd.name: peripheral_data(peripheral_svd)
                for peripheral_svd in svd.peripherals
            },
        },
    }


def peripheral_data(svd):
    assert type(svd.base_address) is int
    try:
        return {
            "description": svd.description,
            "registers": {
                register.name: register_data(register, svd.base_address)
                for register in svd.registers
            },
        }
    except TypeError as error:
        for register in svd.registers:
            print(f"register {register.name}")
            print(f"description: {register.description}")
            print(f"address: {register.base_address + register.address_offset}")
            print(f"width: {register.size}")
            print(f"reset_value: {register.reset_value}")
            print(f"reset_mask: {register.reset_mask}")
            for field in register.fields:
                print(f"  field {field.name}: {field_data(field)}")
        raise error from None


def register_data(svd, base_address):
    return {
        "description": svd.description,
        "address": base_address + svd.address_offset,
        "width": svd.size,
        # Reset value specifies the value after reset. Reset mask defines which
        # bits are affected by a reset.  Note: WCH defines some registers as 16
        # bit, but still sets a 32 bit reset value or mask.
        "reset_value": svd.reset_value,
        "reset_mask": svd.reset_mask,
        "fields": {field.name: field_data(field) for field in svd.fields},
    }


def field_data(svd):
    return {
        "description": svd.description,
        "offset": svd.bit_offset,
        "width": svd.bit_width,
        # access = _get_access(svd),
    }


def _get_access(svd):
    access = svd.access or "read-write"

    # CMSIS-SVD standardises the access field to the values listed below,
    # but the CHv003 SVD also uses 'read/clear'.
    assert access in [
        "read-only",
        "write-only",
        "read-write",
        "writeOnce",
        "read-writeOnce",
    ]
    return access


def print_json(data):
    json.dump(data, sys.stdout, indent=2)


if __name__ == "__main__":
    print_json(svd2json(*sys.argv[1:]))
