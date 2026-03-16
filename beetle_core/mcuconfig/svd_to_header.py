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
svd_to_header.py
================
This script parses an SVD (System View Description) XML file and produces C bitfield
definitions for each register found in the device. It identifies whether a register
is a single register or an array (via <dim>), generates a packed C struct (with unions
to handle overlapping fields), and emits preprocessor macros for convenient access to
the register's address. Specifically:

- `list_registers()`: Iterates over each <peripheral> in the SVD, printing out all
  generated type definitions and macros for its registers.
- `extract_typedef()`: Decides whether a register is single or array, then calls the
  appropriate function.
- `extract_typedef_normal_register()`: Creates a struct with bitfields, placing
  overlapping fields in a union.
- `extract_typedef_array_register()`: Similar to the above, but handles a <dim>
  attribute, meaning the register appears multiple times. Generates both a struct
  for one "slot" and macros to index array elements.
- `generate_bitfield_struct_code()`: (in the refactored version) Common helper that
  sorts fields by offset, groups overlapping fields, and emits a struct with unions
  and gap placeholders.

Run the script directly to parse an SVD file. For example:
python svd_to_header.py my_mcu.svd > registers.h

The name of the SVD file to be parsed is hard coded (see below). I'll update the
script later to make it more flexible.
"""

import sys
import xml.etree.ElementTree as ET
from typing import *

# tree: ET.ElementTree = ET.parse('APM32F00x.svd')
tree: Optional[ET.ElementTree] = None
root: Optional[ET.Element] = None
tab = "    "


def main():
    if len(sys.argv) < 2:
        print("Usage: svd_to_header.py my_mcu.svd > registers.h")
        sys.exit(1)
    input_path = sys.argv[1]
    global tree
    global root
    tree = ET.parse(input_path)
    root = tree.getroot()
    list_interrupts()
    list_registers()
    return


def list_interrupts() -> None:
    """Write out all interrupt definitions."""
    print(f"#include <stdint.h>")
    print("")
    print("typedef enum IRQn")
    print("{")

    def write_interrupts(_interrupts: List[Tuple[str, int, str]]) -> None:
        _interrupts.sort(key=lambda x: x[1])
        iname_longest: int = max(len(iname) for iname, _, _ in _interrupts)
        for iname, ival, idesc in _interrupts:
            print(
                f"{tab}{iname.ljust(iname_longest)} = {str(str(ival)+',').ljust(4)} /*!< {idesc} */"
            )
            # print(f"{tab}{iname.ljust(iname_longest)} = {str(str(ival)+',')}")
            continue
        return

    # Processor Exceptions
    # --------------------
    interrupts: List[Tuple[str, int, str]] = [
        ("NonMaskableInt_IRQn", -14, "2 Non Maskable Interrupt"),
        (
            "MemoryManagement_IRQn",
            -12,
            "4 Cortex-M4 Memory Management Interrupt",
        ),
        ("BusFault_IRQn", -11, "5 Cortex-M4 Bus Fault Interrupt"),
        ("UsageFault_IRQn", -10, "6 Cortex-M4 Usage Fault Interrupt"),
        ("SVCall_IRQn", -5, "11 Cortex-M4 SV Call Interrupt"),
        ("DebugMonitor_IRQn", -4, "12 Cortex-M4 Debug Monitor Interrupt"),
        ("PendSV_IRQn", -2, "14 Cortex-M4 Pend SV Interrupt"),
        ("SysTick_IRQn", -1, "15 Cortex-M4 System Tick Interrupt"),
    ]
    title = f"{tab}/****** Processor Exceptions"
    title = f"{title} {'*'*(97-len(title))}*/"
    print(title)
    write_interrupts(interrupts)

    # Device Interrupts
    # -----------------
    interrupts = []
    iname_longest: int = 1
    for interrupt in root.findall(".//interrupt"):
        iname: str = interrupt.find("name").text
        iname = f"{iname}_IRQn"
        if iname in [_iname for _iname, _, _ in interrupts]:
            continue
        ival: int = int(interrupt.find("value").text)
        idesc: str = (
            interrupt.find("description")
            .text.replace("\r", "")
            .replace("\n", "")
        )
        interrupts.append((iname, ival, idesc))
        if len(iname) > iname_longest:
            iname_longest = len(iname)
        continue
    print("")
    title = f"{tab}/****** Device Interrupts"
    title = f"{title} {'*'*(97-len(title))}*/"
    print(title)
    write_interrupts(interrupts)

    # Finish
    print("} IRQn_Type;")
    print("")
    return


def list_registers() -> None:
    """Write out all register definitions."""
    # Peripheral
    for peripheral in root.findall(".//peripheral"):
        peripheral_name: str = peripheral.find("name").text
        peripheral_base_address: str = peripheral.find("baseAddress").text
        peripheral_desc: str = (
            peripheral.find("description")
            .text.replace("\r", "")
            .replace("\n", "")
        )
        print(create_c_title(peripheral_name))

        # Check for 'derivedFrom' attribute
        derived_from: Optional[str] = peripheral.get("derivedFrom")
        if derived_from:
            print(f"// {peripheral_name} is derived from {derived_from}")
            original_peripheral = root.find(
                f".//peripheral[name='{derived_from}']"
            )
            peripheral = original_peripheral

        # Write description
        print(f"// {capitalize_first_letter(peripheral_desc)}")
        print("")

        # Register
        for register in peripheral.findall(".//register"):
            print(
                extract_typedef(
                    register, peripheral_name, peripheral_base_address
                )
            )
            print("")
            continue
        print("")
        continue
    return


def get_register_type(size: int) -> str:
    if size == 8:
        return "uint8_t"
    elif size == 16:
        return "uint16_t"
    elif size == 32:
        return "uint32_t"
    elif size == 64:
        return "uint64_t"
    return f"uint{size}_t"  # For other sizes


def generate_bitfield_struct_code(
    struct_typename: str,
    register_type: str,
    total_bits: int,
    fields: List[Tuple[str, int, int, str]],
) -> List[str]:
    """Generate the lines of code that define a packed C struct with overlapping
    fields using unions, plus the final typedef line.

    Returns a list of strings (one per line) that you can later join or append
    to.
    """
    longest_fname = 1
    if len(fields) > 0:
        longest_fname = max(len(fname) for fname, _, _, _ in fields)

    lines: List[str] = []
    lines.append(f"typedef struct __attribute__((__packed__)) {{")

    # --- STEP A: Group Overlapping Fields ---
    # Sort by starting bit
    fields.sort(key=lambda x: x[1])

    unions: List[List[Tuple[str, int, int, str]]] = []
    current_union: List[Tuple[str, int, int, str]] = []
    current_union_end = -1

    for fname, fstart, fwidth, fdesc in fields:
        fend = fstart + fwidth - 1
        if fstart <= current_union_end:
            # Overlap => same union
            current_union.append((fname, fstart, fwidth, fdesc))
            current_union_end = max(current_union_end, fend)
        else:
            # No overlap => close previous union (if any) and start a new one
            if current_union:
                unions.append(current_union)
            current_union = [(fname, fstart, fwidth, fdesc)]
            current_union_end = fend
    # Add the final union group
    if current_union:
        unions.append(current_union)

    # --- STEP B: Emit the struct with unions ---
    prev_end_bit = -1
    for group in unions:
        group_start = min(f[1] for f in group)
        group_end = max(f[1] + f[2] - 1 for f in group)

        # Gap before this group?
        if group_start > (prev_end_bit + 1):
            gap_size = group_start - (prev_end_bit + 1)
            lines.append(f"{tab}{register_type} : {gap_size};")

        if len(group) == 1:
            # Single field => no union needed
            fname, fstart, fwidth, fdesc = group[0]
            lines.append(
                f"{tab}{register_type} {fname.ljust(longest_fname)}: {fwidth}; // {fdesc}"
            )
        else:
            # Multiple fields => union
            # Pick the field with largest coverage as the 'main' one
            main_field = max(group, key=lambda x: (x[1] + x[2], x[1]))
            main_name, main_start, main_width, main_desc = main_field
            subfields = [f for f in group if f != main_field]
            subfields.sort(key=lambda x: x[1])  # Sort by bit offset

            lines.append(f"{tab}union {{")
            # 1) Main field
            lines.append(
                f"{tab*2}{register_type} {main_name.ljust(longest_fname)}: {main_width}; // {main_desc}"
            )

            # 2) Sub-struct
            lines.append(f"{tab*2}struct {{")
            sub_prev_end = main_start - 1
            for sname, sstart, swidth, sdesc in subfields:
                if sstart > (sub_prev_end + 1):
                    gap_size = sstart - (sub_prev_end + 1)
                    lines.append(f"{tab*3}{register_type} : {gap_size};")
                lines.append(
                    f"{tab*3}{register_type} {sname.ljust(longest_fname)}: {swidth}; // {sdesc}"
                )
                sub_prev_end = sstart + swidth - 1

            # Gap in sub-struct if needed
            if sub_prev_end < group_end:
                gap_size = group_end - sub_prev_end
                lines.append(f"{tab*3}{register_type} : {gap_size};")

            lines.append(f"{tab*2}}};")
            lines.append(f"{tab}}};")

        prev_end_bit = group_end

    # Fill up any remaining bits at the end
    if prev_end_bit < (total_bits - 1):
        gap_size = total_bits - (prev_end_bit + 1)
        lines.append(f"{tab}{register_type} : {gap_size};")

    # Close struct
    lines.append(f"}} {struct_typename};")
    return lines


def extract_typedef_normal_register(
    register: ET.Element,
    peripheral_name: str,
    peripheral_base_address: str,
) -> str:
    register_name = register.find("name").text
    register_size = int(register.find("size").text)
    register_type = get_register_type(register_size)

    reg_address = int(peripheral_base_address, 16) + int(
        register.find("addressOffset").text, 16
    )
    total_bits = register_size

    # Collect fields
    fields: List[Tuple[str, int, int, str]] = []
    for field in register.findall(".//field"):
        fname: str = field.find("name").text
        fstart: int = int(field.find("bitOffset").text)
        fwidth: int = int(field.find("bitWidth").text)
        fdesc: Optional[str] = capitalize_first_letter(
            field.find("description").text.replace("\r", "").replace("\n", "")
        )
        fields.append((fname, fstart, fwidth, fdesc))

    struct_typename = f"{peripheral_name}_{register_name}bits_t"

    # Generate the struct code using our helper
    lines = generate_bitfield_struct_code(
        struct_typename=struct_typename,
        register_type=register_type,
        total_bits=total_bits,
        fields=fields,
    )

    # Add macros
    hex_address = hex(reg_address)
    lines.append(
        f"#define {peripheral_name}_{register_name} (*(volatile {register_type} *){hex_address})"
    )
    lines.append(
        f"#define {peripheral_name}_{register_name}bits (*(volatile {struct_typename} *){hex_address})"
    )

    return "\n".join(lines)


def extract_typedef_array_register(
    register: ET.Element,
    peripheral_name: str,
    peripheral_base_address: str,
) -> str:
    # Make sure <dim> is present
    dim_element = register.find("dim")
    if dim_element is None:
        raise ValueError(
            "This function should only be called on a <register> with <dim>"
        )

    register_name = register.find("name").text
    # E.g. "IPR%s" => "IPR"
    if "%s" in register_name:
        register_name = register_name.replace("%s", "")

    register_size = int(register.find("size").text)
    register_type = get_register_type(register_size)

    dim_count = int(register.find("dim").text)
    dim_increment = int(register.find("dimIncrement").text, 0)

    reg_address_offset = int(register.find("addressOffset").text, 16)
    reg_base_address = int(peripheral_base_address, 16) + reg_address_offset
    total_bits = register_size

    # Collect fields
    fields: List[Tuple[str, int, int]] = []
    for field in register.findall(".//field"):
        fname: str = field.find("name").text
        fstart: int = int(field.find("bitOffset").text)
        fwidth: int = int(field.find("bitWidth").text)
        fdesc: Optional[str] = capitalize_first_letter(
            field.find("description").text.replace("\r", "").replace("\n", "")
        )
        fields.append((fname, fstart, fwidth, fdesc))

    struct_typename = f"{peripheral_name}_{register_name}bits_t"

    # Generate the struct definition
    lines = generate_bitfield_struct_code(
        struct_typename=struct_typename,
        register_type=register_type,
        total_bits=total_bits,
        fields=fields,
    )

    # Emit array macros
    hex_base = hex(reg_base_address)
    lines.append(
        f"#define {peripheral_name}_{register_name} ((volatile {register_type} *){hex_base})"
    )
    lines.append(
        f"#define {peripheral_name}_{register_name}bits ((volatile {struct_typename} *){hex_base})"
    )

    # Optional convenience macros for indexing
    lines.append(
        f"#define {peripheral_name}_{register_name}n(n) "
        f"(*((volatile {register_type} *)({hex_base} + (n)*{dim_increment})))"
    )
    lines.append(
        f"#define {peripheral_name}_{register_name}bitsn(n) "
        f"(*((volatile {struct_typename} *)({hex_base} + (n)*{dim_increment})))"
    )
    return "\n".join(lines)


def extract_typedef(
    register: ET.Element,
    peripheral_name: str,
    peripheral_base_address: str,
) -> str:
    """Extract the typedef for the register, as well as the #define macros."""
    register_name = register.find("name").text
    register_desc = (
        register.find("description").text.replace("\r", "").replace("\n", "")
    )
    print(f"// {register_name}")
    print(f"// {'-'*len(register_name)}")
    print(f"// {capitalize_first_letter(register_desc)}")
    if register.find("dim") is not None:
        return extract_typedef_array_register(
            register, peripheral_name, peripheral_base_address
        )
    return extract_typedef_normal_register(
        register, peripheral_name, peripheral_base_address
    )


def capitalize_first_letter(s: Optional[str]) -> Optional[str]:
    """Capitalize only first letter."""
    if (s is None) or (len(s) == 0):  # Check for an empty string
        return s
    return s[0].upper() + s[1:]


def create_c_title(s):
    """Create a C-style title."""
    total_width = 80
    border = "// " + "=" * (total_width - 6) + " //"

    # Center the title text
    title = s.upper()
    padding_length = (total_width - 6 - len(title)) // 2
    title_line = (
        "// "
        + " " * padding_length
        + title
        + " " * (total_width - 6 - len(title) - padding_length)
        + " //"
    )

    # Combine the border and title lines
    return f"{border}\n{title_line}\n{border}"


if __name__ == "__main__":
    main()

# REFACTORING THE CODE TO HANDLE REGISTER ARRAYS
# ==============================================
# Before the latest change, where the code was refactored to handle register arrays, the output for
# the NVIC_IP register from the Cortex-M0+ was as follows:
#     typedef struct __attribute__((__packed__)) {
#         uint32_t : 32;
#     } NVIC_IPbits_t;
#     #define NVIC_IP (*(volatile uint32_t *)0xe000e400)
#     #define NVIC_IPbits (*(volatile NVIC_IPbits_t *)0xe000e400)
# Notice that NVIC_IP is dereferenced here. So you can write something directly to the register.
# After the change, the output for the NVIC_IP register is as follows:
#     typedef struct __attribute__((__packed__)) {
#         uint8_t : 8;
#     } NVIC_IPbits_t;
#     #define NVIC_IP ((volatile uint8_t *)0xe000e400)
#     #define NVIC_IPbits ((volatile NVIC_IPbits_t *)0xe000e400)
# Notice that NVIC_IP is not dereferenced here. So you first need to dereference it before writing
# something. However, that's exactly what we need, because that's what the array syntax does for us.
# Remember:
#     x[n] == *(x + n)
# So:
#     NVIC_IP[0] == *(NVIC_IP + 0)
#     NVIC_IP[1] == *(NVIC_IP + 1)
#     ...
# The NVIC_IP register had no fields. Its SVD snippet was:
#     <register>
#         <name>IP</name>
#         <description>Interrupt Priority Register</description>
#         <addressOffset>0x300</addressOffset>
#         <size>8</size>
#         <access>read-write</access>
#         <dim>32</dim>
#         <dimIncrement>0x1</dimIncrement>
#         <dimIndex>0-31</dimIndex>
#     </register>
# After an SVD update, it now has fields:
#     <register>
#         <name>IP</name>
#         <description>Interrupt Priority Register</description>
#         <addressOffset>0x300</addressOffset>
#         <size>8</size>
#         <access>read-write</access>
#         <dim>32</dim>
#         <dimIncrement>0x1</dimIncrement>
#         <dimIndex>0-31</dimIndex>
#         <fields>
#             <field>
#                 <name>RESERVED</name>
#                 <description>Reserved</description>
#                 <bitOffset>0</bitOffset>
#                 <bitWidth>6</bitWidth>
#             </field>
#             <field>
#                 <name>PRI</name>
#                 <description>Priority Bits</description>
#                 <bitOffset>6</bitOffset>
#                 <bitWidth>2</bitWidth>
#             </field>
#         </fields>
#     </register>
# The output for this is:
#     typedef struct __attribute__((__packed__)) {
#         uint8_t RESERVED: 6;
#         uint8_t PRI: 2;
#     } NVIC_IPbits_t;
#     #define NVIC_IP ((volatile uint8_t *)0xe000e400)
#     #define NVIC_IPbits ((volatile NVIC_IPbits_t *)0xe000e400)
# Again, notice that the NVIC_IP is not dereferenced. You can use the array syntax to do that:
#     NVIC_IPbits[9].PRI = 0b10;
# Or:
#     NVIC_IPbits_t ip_bits;
#     ip_bits.PRI = 0b10;
#     NVIC_IPbits[9] = ip_bits;
