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

# The CMSIS-SVD format is described at
# https://arm-software.github.io/CMSIS_5/SVD/html/svd_Format_pg.html
# The cmsis_svd Python package does most of the heavy lifting, such as handling
# derived_from attributes and default values.  Here, we do limited additional
# checking and convert to the config data structure.

import cmsis_svd.parser
import sys

check_desc = False
check_defaults = False


def load_file(svd_path):
    return cmsis_svd.parser.SVDParser.for_xml_file(
        svd_path, remove_reserved=True
    ).get_device()


# For debugging: print(_json(svd))
def _json(svd):
    import json

    return json.dumps(svd.to_dict(), indent=4)


def compare(path1, path2):
    svd1 = load_file(path1)
    svd2 = load_file(path2)

    if svd1.name != svd2.name:
        print(f"different names '{svd1.name}' and '{svd2.name}'")

    if svd1.description != svd2.description:
        print(
            f"different descriptions '{svd1.description}' and "
            f"'{svd2.description}'"
        )
    if svd1.address_unit_bits != svd2.address_unit_bits:
        print(
            f"different address_unit_bits '{svd1.address_unit_bits}' and "
            f"'{svd2.address_unit_bits}'"
        )
    if check_defaults and svd1.width != svd2.width:
        print(f"different width '{svd1.width}' and " f"'{svd2.width}'")
    if check_defaults and svd1.reset_value != svd2.reset_value:
        print(
            f"different reset_value '{svd1.reset_value}' and "
            f"'{svd2.reset_value}'"
        )
    if check_defaults and svd1.reset_mask != svd2.reset_mask:
        print(
            f"different reset_mask '{svd1.reset_mask}' and "
            f"'{svd2.reset_mask}'"
        )

    peris1 = {peri.name: peri for peri in svd1.peripherals}
    peris2 = {peri.name: peri for peri in svd2.peripherals}
    for name in peris1:
        if name not in peris2:
            print(f"peripheral '{name}' missing in '{path2}'")
    for name in peris2:
        if name not in peris1:
            print(f"peripheral '{name}' missing in '{path1}'")
    for peri_name, peri1 in peris1.items():
        peri2 = peris2.get(peri_name)
        if peri2 is None:
            continue
        if check_desc and peri1.description != peri2.description:
            print(
                f"different descriptions for '{peri_name}': "
                f"'{peri1.description}' and '{peri2.description}'"
            )
        if peri1.base_address != peri2.base_address:
            print(
                f"different base_addresss for '{peri_name}': "
                f"'{peri1.base_address}' and '{peri2.base_address}'"
            )

        regs1 = {reg.name: reg for reg in peri1.registers}
        regs2 = {reg.name: reg for reg in peri2.registers}
        for name in regs1:
            if name not in regs2:
                print(f"register '{peri_name}.{name}' missing in '{path2}'")
        for name in regs2:
            if name not in regs1:
                print(f"register '{peri_name}.{name}' missing in '{path1}'")
        for reg_name, reg1 in regs1.items():
            reg2 = regs2.get(reg_name)
            if reg2 is None:
                continue
            if check_desc and reg1.description != reg2.description:
                print(
                    f"different descriptions for '{peri_name}.{reg_name}': "
                    f"'{reg1.description}' and '{reg2.description}'"
                )
            if reg1.address_offset != reg2.address_offset:
                print(
                    f"different address_offsets for '{peri_name}.{reg_name}': "
                    f"'{reg1.address_offset}' and '{reg2.address_offset}'"
                )
            if reg1.size != reg2.size:
                print(
                    f"different sizes for '{peri_name}.{reg_name}': "
                    f"'{reg1.size:x}' and '{reg2.size:x}'"
                )
            if reg1.reset_value != reg2.reset_value:
                print(
                    f"different reset_values for '{peri_name}.{reg_name}': "
                    f"'{reg1.reset_value:x}' and '{reg2.reset_value:x}'"
                )
            if reg1.reset_mask != reg2.reset_mask:
                print(
                    f"different reset_masks for '{peri_name}.{reg_name}': "
                    f"'{reg1.reset_mask:x}' and '{reg2.reset_mask:x}'"
                )

            fields1 = {field.name: field for field in reg1.fields}
            fields2 = {field.name: field for field in reg2.fields}
            for name in fields1:
                if name not in fields2:
                    print(
                        f"field '{peri_name}.{reg_name}.{name}' missing in "
                        f"'{path2}'"
                    )
            for name in fields2:
                if name not in fields1:
                    print(
                        f"field '{peri_name}.{reg_name}.{name}' missing in "
                        f"'{path1}'"
                    )
            for field_name, field1 in fields1.items():
                field2 = fields2.get(field_name)
                if field2 is None:
                    continue
                assert field2, "'{peri_name}.{reg_name}.{field_name}'"
                if check_desc and field1.description != field2.description:
                    print(
                        f"different descriptions for "
                        f"'{peri_name}.{reg_name}.{field_name}': "
                        f"'{field1.description}' and '{field2.description}'"
                    )
                if field1.bit_offset != field2.bit_offset:
                    print(
                        f"different bit_offsets for '{peri_name}.{field_name}': "
                        f"'{field1.bit_offset:x}' and '{field2.bit_offset:x}'"
                    )
                if field1.bit_width != field2.bit_width:
                    print(
                        f"different bit_widths for '{peri_name}.{field_name}': "
                        f"'{field1.bit_width:x}' and '{field2.bit_width:x}'"
                    )


if __name__ == "__main__":
    compare(sys.argv[1], sys.argv[2])
