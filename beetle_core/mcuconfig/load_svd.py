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
checking and convert to the config data structure.
"""

import cmsis_svd.parser

from .model import Series, Peripheral, Register, Field, ConfigError


def _get_description(svd):
    return svd.description


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


def _assert_unsigned(value, size=None):
    assert isinstance(value, int)
    assert value >= 0
    if size is not None:
        assert value < (1 << size)


# For debugging: print(_json(svd))
def _json(svd):
    import json

    return json.dumps(svd.to_dict(), indent=4)


def load_file(svd_path):
    try:
        svd = cmsis_svd.parser.SVDParser.for_xml_file(
            svd_path, remove_reserved=True
        ).get_device()
    except TypeError as error:
        raise ConfigError(f"{svd_path}: {error}")
    return convert_series(svd)


def convert_series(svd):
    assert svd.name and svd.address_unit_bits and svd.width
    series = Series(
        name=svd.name,
        description=_get_description(svd),
        address_unit_bits=svd.address_unit_bits,
    )
    for svd in svd.peripherals:
        if svd.name:
            convert_peripheral(svd, series)
        else:
            # SVD error: name, addressUnitBits and width are required
            pass
    return series


def convert_peripheral(svd, series):
    # print(f"Convert {svd.name} @ {svd.base_address} {svd.description}")
    assert svd.name and svd.base_address is not None
    peripheral = Peripheral(
        series=series, name=svd.name, description=_get_description(svd)
    )
    # print(f"{peripheral.name}: {peripheral.description}")
    base_address = svd.base_address
    for svd in svd.registers:
        convert_register(svd, peripheral, base_address)
    return peripheral


def convert_register(svd, peripheral, base_address):
    assert svd.name
    _assert_unsigned(svd.address_offset)
    _assert_unsigned(svd.size)
    # Reset value specifies the value after reset. Reset mask defines which bits
    # are affected by a reset.  Note: WCH defines some registers as 16 bit, but
    # still sets a 32 bit reset value or mask.
    _assert_unsigned(svd.reset_value)
    _assert_unsigned(svd.reset_mask)
    register = Register(
        peripheral,
        name=svd.name,
        description=_get_description(svd),
        address=base_address + svd.address_offset,
        width=svd.size,
        reset_value=svd.reset_value,
        reset_mask=svd.reset_mask,
        # access = _get_access(svd),
    )
    # print(f"  {register.name}: {register.description}")
    for svd in svd.fields:
        convert_field(svd, register)
    return register


def convert_field(svd, register):
    # print(f"convert named field: {_json(svd)}")
    assert svd.name
    field = Field(
        register,
        svd.name,
        description=_get_description(svd),
        # access = _get_access(svd),
        offset=svd.bit_offset,
        width=svd.bit_width,
    )
    # print(f"    {field.name}: {field.description}")
    return field
