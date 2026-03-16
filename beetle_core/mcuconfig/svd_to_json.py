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

import xml.etree.ElementTree as ET
import json
import argparse
import sys
import re
from typing import Dict, List, Any, Union, Optional

multi_space_p = re.compile(r"\s{2,}")


def parse_hex_or_dec(s: str) -> int:
    """Parse a string as either hexadecimal or decimal and return its integer
    value.

    :param s: String representing the number, possibly in '0x..' format or
        decimal.
    :return: Integer value of the parsed string.
    """
    s_lower: str = s.strip().lower()
    if s_lower.startswith("0x"):
        parsed_value: int = int(s_lower, 16)
    else:
        parsed_value = int(s_lower, 10)
    return parsed_value


def strip_text(txt: Optional[str]) -> Optional[str]:
    """Strip text and replace multiple spaces with a single space."""
    if txt is None:
        return None
    txt = txt.strip()
    txt = multi_space_p.sub(" ", txt)
    return txt


def get_text_or_none(parent: ET.Element, tag: str) -> Optional[str]:
    """Return the stripped text of a child element <tag> of 'parent', or None if
    not present.

    :param parent: The XML element to search within.
    :param tag: The sub-element tag to find.
    :return: The .text (stripped) of the sub-element, or None if not found or
        empty.
    """
    el: Optional[ET.Element] = parent.find(tag)
    if el is not None and el.text is not None:
        return strip_text(el.text)
    return None


def parse_vendor_extensions(vendor_ext_el: ET.Element) -> Dict[str, str]:
    """Parse all children of <vendorExtensions> into a dictionary where the key
    is the tag (including namespace) and the value is the child's text.

    Additionally, if the tag name contains "fieldkind", we rename it to
    "fieldKind".

    :param vendor_ext_el: The <vendorExtensions> element.
    :return: Dictionary mapping tag (or "fieldKind") -> text.
    """
    result: Dict[str, str] = {}
    for child in vendor_ext_el:
        key: str = (
            child.tag
        )  # Keeping the entire tag (with namespace if present)
        if "fieldkindcmt" in key.lower():
            key = "fieldKindCmt"
        elif "fieldkind" in key.lower():
            key = "fieldKind"
        elif "registerkindcmt" in key.lower():
            key = "registerKindCmt"
        elif "registerkind" in key.lower():
            key = "registerKind"
        text_val: str = strip_text(child.text) if child.text else ""
        result[key] = text_val
    return result


def parse_enumerated_values(
    field_el: ET.Element,
) -> List[List[Dict[str, Union[str, int, None]]]]:
    """Parse zero or more <enumeratedValues> sections under a <field> into a
    list-of-lists. Each <enumeratedValues> block becomes one list element. Each
    <enumeratedValue> is parsed into a dict with "name", "description", and
    "value".

    :param field_el: The <field> element potentially containing
        <enumeratedValues>.
    :return: A list of enumerated-values blocks, each block is a list of
        enumerated values.
    """
    enum_values_data: List[List[Dict[str, Union[str, int, None]]]] = []
    enumerated_values_elements: List[ET.Element] = field_el.findall(
        "enumeratedValues"
    )
    for enum_values_el in enumerated_values_elements:
        tmp_list: List[Dict[str, Union[str, int, None]]] = []
        enumerated_value_elements: List[ET.Element] = enum_values_el.findall(
            "enumeratedValue"
        )
        for enum_el in enumerated_value_elements:
            en_name: Optional[str] = get_text_or_none(enum_el, "name")
            en_desc: Optional[str] = get_text_or_none(enum_el, "description")
            en_value_text: Optional[str] = get_text_or_none(enum_el, "value")
            en_value: Optional[int] = (
                parse_hex_or_dec(en_value_text) if en_value_text else None
            )
            tmp_list.append(
                {"name": en_name, "description": en_desc, "value": en_value}
            )
        enum_values_data.append(tmp_list)
    return enum_values_data


def parse_bitfield(field_el: ET.Element) -> Dict[str, Any]:
    """Parse a single <field> element into a dictionary containing its various
    attributes: name, display_name, description, bit_offset, bit_width, access,
    enumerated_values, etc.

    If <vendorExtensions> is present, we parse those too (e.g., fieldKind).

    :param field_el: The <field> element from the SVD.
    :return: A dictionary describing this field.
    """
    field_dict: Dict[str, Any] = {}

    name_text: Optional[str] = get_text_or_none(field_el, "name")
    display_name_text: Optional[str] = get_text_or_none(field_el, "displayName")
    description_text: Optional[str] = get_text_or_none(field_el, "description")

    bit_offset_text: Optional[str] = get_text_or_none(field_el, "bitOffset")
    bit_width_text: Optional[str] = get_text_or_none(field_el, "bitWidth")

    field_dict["name"] = name_text
    field_dict["display_name"] = display_name_text
    field_dict["description"] = description_text
    field_dict["bit_offset"] = int(bit_offset_text) if bit_offset_text else None
    field_dict["bit_width"] = int(bit_width_text) if bit_width_text else None
    field_dict["access"] = get_text_or_none(field_el, "access")

    # enumeratedValues
    ev: List[List[Dict[str, Union[str, int, None]]]] = parse_enumerated_values(
        field_el
    )
    if ev:
        field_dict["enumerated_values"] = ev

    # vendorExtensions
    vendor_ext_el: Optional[ET.Element] = field_el.find("vendorExtensions")
    if vendor_ext_el is not None:
        for k, v in parse_vendor_extensions(vendor_ext_el).items():
            field_dict[k] = v

    return field_dict


def parse_dim_index(dim_index_str: str, dim_val: int) -> List[str]:
    """Parse the <dimIndex> string, which might be:

      - "0-79"
      - "0,1,2,..."
      - or other variations

    If we see "0-79", we expand to ["0","1","2",...,"79"].
    If it's comma-separated, we split on commas.
    Otherwise, we return [dim_index_str].
    If no <dimIndex> is given, we typically fallback to range(dim_val).

    :param dim_index_str: The raw string from <dimIndex>.
    :param dim_val: The <dim> value, i.e. how many items to expand.
    :return: A list of index strings for each expanded element.
    """
    dim_index_str = dim_index_str.strip()
    # If there's a '-' pattern like "0-79":
    if "-" in dim_index_str:
        parts = dim_index_str.split("-")
        if len(parts) == 2:
            start_str, end_str = parts
            start_i = int(start_str)
            end_i = int(end_str)
            return [str(i) for i in range(start_i, end_i + 1)]
        # if more than one dash or weird format, fallback
        return [dim_index_str]
    elif "," in dim_index_str:
        splitted = [chunk.strip() for chunk in dim_index_str.split(",")]
        return splitted
    else:
        # single value or empty
        return [dim_index_str]


def parse_register(
    reg_el: ET.Element, peripheral_base: int
) -> List[Dict[str, Any]]:
    """Parse a single <register> element. If <dim> > 1, expand it into multiple
    registers.

    NOTE: This function returns a list of register dicts (may be length 1 or many).

    :param reg_el: The <register> element from the SVD.
    :param peripheral_base: Base address of the peripheral, used to compute absolute register address.
    :return: A list of register dictionaries, each with "name" and "fields" and so forth.
    """
    r_name: Optional[str] = get_text_or_none(reg_el, "name")
    r_display_name: Optional[str] = get_text_or_none(reg_el, "displayName")
    r_desc: Optional[str] = get_text_or_none(reg_el, "description")
    offset_text: Optional[str] = get_text_or_none(reg_el, "addressOffset")
    size_text: Optional[str] = get_text_or_none(reg_el, "size")
    reset_val_text: Optional[str] = get_text_or_none(reg_el, "resetValue")
    reset_mask_text: Optional[str] = get_text_or_none(reg_el, "resetMask")
    access_text: Optional[str] = get_text_or_none(reg_el, "access")
    protection_text: Optional[str] = get_text_or_none(reg_el, "protection")

    # Potential array/dim fields
    dim_text: Optional[str] = get_text_or_none(reg_el, "dim")
    dim_increment_text: Optional[str] = get_text_or_none(reg_el, "dimIncrement")
    dim_index_text: Optional[str] = get_text_or_none(reg_el, "dimIndex")

    offset_val: int = parse_hex_or_dec(offset_text) if offset_text else 0
    size_val: Optional[int] = int(size_text) if size_text else None
    reset_val: Optional[int] = (
        parse_hex_or_dec(reset_val_text) if reset_val_text else None
    )
    reset_mask: Optional[int] = (
        parse_hex_or_dec(reset_mask_text) if reset_mask_text else None
    )

    # Print warning if reset_val or reset_mask is None!
    if (reset_val is None) or (reset_mask is None):
        print(f"WARNING: reset undefined for '{r_name}'")

    # Parse fields, storing in a dict keyed by field name
    fields_el: Optional[ET.Element] = reg_el.find("fields")
    fields_dict: Dict[str, Dict[str, Any]] = {}
    if fields_el is not None:
        field_elements: List[ET.Element] = fields_el.findall("field")
        for f_el in field_elements:
            field_info: Dict[str, Any] = parse_bitfield(f_el)
            field_name = field_info.pop("name")
            if field_name is not None:
                fields_dict[field_name] = field_info

    # vendorExtensions
    registerKind: Optional[str] = None
    registerKindCmt: Optional[str] = None
    vendor_ext_el: Optional[ET.Element] = reg_el.find("vendorExtensions")
    if vendor_ext_el is not None:
        for k, v in parse_vendor_extensions(vendor_ext_el).items():
            if "registerkindcmt" in k.lower():
                registerKindCmt = v
            elif "registerkind" in k.lower():
                registerKind = v
            continue

    # If <dim> is missing or <= 1, return a single register dictionary
    if not dim_text or int(dim_text) <= 1:
        single_reg: Dict[str, Any] = {
            "name": r_name,
            "display_name": r_display_name,
            "description": r_desc,
            "address_offset": offset_val,
            "address": peripheral_base + offset_val,
            "size": size_val,
            "reset_value": reset_val,
            "reset_mask": reset_mask,
            "access": access_text,
            "protection": protection_text,
            "fields": fields_dict,
        }
        if registerKind is not None:
            single_reg["registerKind"] = registerKind
            single_reg["registerKindCmt"] = registerKindCmt
        return [single_reg]

    # Otherwise, expand
    dim_val = int(dim_text)
    dim_increment = (
        parse_hex_or_dec(dim_increment_text) if dim_increment_text else 0
    )

    # parse dimIndex if present; fallback to numeric range if mismatched
    if dim_index_text:
        indices = parse_dim_index(dim_index_text, dim_val)
        # if the parsed indices don't match dim_val in length, fallback
        if len(indices) != dim_val:
            indices = [str(i) for i in range(dim_val)]
    else:
        indices = [str(i) for i in range(dim_val)]

    expanded_list: List[Dict[str, Any]] = []

    for i, idx_str in enumerate(indices):
        # Construct name for each instance
        if r_name and "%s" in r_name:
            inst_name = r_name.replace("%s", idx_str)
        else:
            # fallback: just append index to the base name
            inst_name = f"{r_name}{idx_str}" if r_name else idx_str

        offset_i = offset_val + i * dim_increment
        reg_inst: Dict[str, Any] = {
            "name": inst_name,
            "display_name": r_display_name,
            "description": r_desc,
            "address_offset": offset_i,
            "address": peripheral_base + offset_i,
            "size": size_val,
            "reset_value": reset_val,
            "reset_mask": reset_mask,
            "access": access_text,
            "protection": protection_text,
            "fields": fields_dict,
        }
        if registerKind is not None:
            reg_inst["registerKind"] = registerKind
            reg_inst["registerKindCmt"] = registerKindCmt
        expanded_list.append(reg_inst)

    return expanded_list


def parse_address_block(
    block_el: ET.Element,
) -> Dict[str, Union[str, int, None]]:
    """Parse a single <addressBlock> element into a dictionary.

    :param block_el: The <addressBlock> element from the SVD.
    :return: A dictionary describing the address block (offset, size, usage,
        protection).
    """
    ab_dict: Dict[str, Union[str, int, None]] = {}
    offset_str: Optional[str] = get_text_or_none(block_el, "offset")
    size_str: Optional[str] = get_text_or_none(block_el, "size")

    ab_dict["offset"] = parse_hex_or_dec(offset_str) if offset_str else 0
    ab_dict["size"] = parse_hex_or_dec(size_str) if size_str else 0
    ab_dict["usage"] = get_text_or_none(block_el, "usage")
    ab_dict["protection"] = get_text_or_none(block_el, "protection")
    return ab_dict


def parse_interrupt(
    interrupt_el: ET.Element,
) -> Dict[str, Union[str, int, None]]:
    """Parse a single <interrupt> element into a dictionary.

    :param interrupt_el: The <interrupt> element from the SVD.
    :return: A dictionary describing the interrupt (name, description, value).
    """
    intr_dict: Dict[str, Union[str, int, None]] = {}
    intr_name: Optional[str] = get_text_or_none(interrupt_el, "name")
    intr_desc: Optional[str] = get_text_or_none(interrupt_el, "description")
    intr_value_text: Optional[str] = get_text_or_none(interrupt_el, "value")

    intr_dict["name"] = intr_name
    intr_dict["description"] = intr_desc
    if intr_value_text is not None:
        intr_dict["value"] = parse_hex_or_dec(intr_value_text)
    else:
        intr_dict["value"] = None

    return intr_dict


def parse_peripheral(periph_el: ET.Element) -> Dict[str, Any]:
    """Parse a single <peripheral> element into a dictionary:

      - name, description, groupName
      - baseAddress
      - addressBlock (if exactly one) or raise RuntimeError if more than one
      - interrupt(s)
      - registers (expanding any <dim> registers)

    :param periph_el: The <peripheral> element from the SVD.
    :return: A dictionary describing this peripheral.
    """
    p_dict: Dict[str, Any] = {}

    p_name: Optional[str] = get_text_or_none(periph_el, "name")
    p_desc: Optional[str] = get_text_or_none(periph_el, "description")
    p_group: Optional[str] = get_text_or_none(periph_el, "groupName")
    base_text: Optional[str] = get_text_or_none(periph_el, "baseAddress")

    base_val: int = parse_hex_or_dec(base_text) if base_text else 0

    p_dict["name"] = p_name
    p_dict["description"] = p_desc
    p_dict["group_name"] = p_group
    p_dict["base_address"] = base_val

    # addressBlock(s)
    block_elements: List[ET.Element] = periph_el.findall("addressBlock")
    num_blocks: int = len(block_elements)
    if num_blocks > 1:
        raise RuntimeError(
            f"Peripheral '{p_name}' has {num_blocks} addressBlock entries. "
            "Expected at most one."
        )
    elif num_blocks == 1:
        ab_info: Dict[str, Union[str, int, None]] = parse_address_block(
            block_elements[0]
        )
        p_dict["address_block"] = ab_info

    # interrupt(s)
    interrupts: List[Dict[str, Union[str, int, None]]] = []
    interrupt_elements: List[ET.Element] = periph_el.findall("interrupt")
    for intr_el in interrupt_elements:
        intr_info: Dict[str, Union[str, int, None]] = parse_interrupt(intr_el)
        interrupts.append(intr_info)
    if interrupts:
        p_dict["interrupts"] = interrupts

    # registers
    registers_dict: Dict[str, Any] = {}
    registers_el: Optional[ET.Element] = periph_el.find("registers")
    if registers_el is not None:
        register_elements: List[ET.Element] = registers_el.findall("register")
        for reg_el in register_elements:
            # parse_register now returns a list (could be >1 if <dim> >1)
            expanded_registers: List[Dict[str, Any]] = parse_register(
                reg_el, base_val
            )
            for reg_info in expanded_registers:
                reg_name: Optional[str] = reg_info.pop("name", None)
                if reg_name is not None:
                    registers_dict[reg_name] = reg_info

    p_dict["registers"] = registers_dict

    return p_dict


def parse_cpu(cpu_el: ET.Element) -> Dict[str, Optional[str]]:
    """Parse <cpu> node into a dictionary containing: name, revision, endian,
    nvicPrioBits, vendorSystickConfig.

    :param cpu_el: The <cpu> element from the SVD.
    :return: A dictionary describing the CPU configuration.
    """
    cpu_dict: Dict[str, Optional[str]] = {}
    cpu_dict["name"] = get_text_or_none(cpu_el, "name")
    cpu_dict["revision"] = get_text_or_none(cpu_el, "revision")
    cpu_dict["endian"] = get_text_or_none(cpu_el, "endian")
    cpu_dict["nvicPrioBits"] = get_text_or_none(cpu_el, "nvicPrioBits")
    cpu_dict["vendorSystickConfig"] = get_text_or_none(
        cpu_el, "vendorSystickConfig"
    )
    return cpu_dict


def svd_to_json(svd_filename: str) -> Dict[str, Any]:
    """Parse the given SVD XML file and return a dictionary that includes all
    device info (vendor, name, version, description, CPU, peripherals, etc.),
    preserving all known fields. It also expands any registers that have <dim> >
    1 (like NVIC IPR).

    :param svd_filename: Path to the SVD file.
    :return: A dictionary containing the parsed SVD content in JSON-friendly
        format.
    """
    tree: ET.ElementTree = ET.parse(svd_filename)
    root: ET.Element = tree.getroot()

    svd_dict: Dict[str, Any] = {}

    vendor_el: Optional[ET.Element] = root.find("vendor")
    name_el: Optional[ET.Element] = root.find("name")
    version_el: Optional[ET.Element] = root.find("version")
    desc_el: Optional[ET.Element] = root.find("description")

    if vendor_el is not None and vendor_el.text is not None:
        svd_dict["vendor"] = strip_text(vendor_el.text)
    if name_el is not None and name_el.text is not None:
        svd_dict["name"] = strip_text(name_el.text)
    if version_el is not None and version_el.text is not None:
        svd_dict["version"] = strip_text(version_el.text)
    if desc_el is not None and desc_el.text is not None:
        svd_dict["description"] = strip_text(desc_el.text)

    address_unit_bits_el: Optional[ET.Element] = root.find("addressUnitBits")
    if (
        address_unit_bits_el is not None
        and address_unit_bits_el.text is not None
    ):
        svd_dict["address_unit_bits"] = int(
            strip_text(address_unit_bits_el.text)
        )

    cpu_el: Optional[ET.Element] = root.find("cpu")
    if cpu_el is not None:
        svd_dict["cpu"] = parse_cpu(cpu_el)

    peripherals_el: Optional[ET.Element] = root.find("peripherals")
    if peripherals_el is not None:
        peripheral_dict: Dict[str, Any] = {}
        peripheral_elements: List[ET.Element] = peripherals_el.findall(
            "peripheral"
        )
        for p_el in peripheral_elements:
            p_info: Dict[str, Any] = parse_peripheral(p_el)
            p_name: Optional[str] = p_info["name"]
            if p_name is not None:
                peripheral_dict[p_name] = p_info
        svd_dict["peripherals"] = peripheral_dict

    return svd_dict


def main() -> None:
    """
    Main entry point: parse command-line arguments, convert SVD to JSON, and write/print the result.

    :return: None
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Convert a CMSIS-SVD XML file to JSON (preserving all data, including array expansions)."
    )
    parser.add_argument("svd_file", help="Path to the input SVD file (XML).")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Path to the output JSON file. If not provided, prints to stdout.",
    )
    args: argparse.Namespace = parser.parse_args()

    svd_json_data: Dict[str, Any] = svd_to_json(args.svd_file)
    svd_json_str: str = json.dumps(svd_json_data, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(svd_json_str)
    else:
        print(svd_json_str)


if __name__ == "__main__":
    main()
