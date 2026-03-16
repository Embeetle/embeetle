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


def extract_register_snippet(
    svd_file: str, peripheral_name: str, register_name: str
) -> str:
    """Extract the <register>...</register> snippet for a register with the
    given 'register_name' from the specified SVD file. The register must belong
    to the given peripheral.

    :param svd_file: Path to the SVD (XML) file.
    :param peripheral_name: Look into this peripheral for the requested
        register.
    :param register_name: The <name> value of the register you want to extract.
    :return: A string containing the entire <register> element and its contents.
        Returns an empty string if no matching register is found.
    """
    import xml.etree.ElementTree as ET

    tree = ET.parse(svd_file)
    root = tree.getroot()

    # Find the <peripheral> element with the given name
    for peripheral in root.findall(".//peripheral"):
        p_name_element = peripheral.find("name")
        if (
            p_name_element is not None
            and p_name_element.text == peripheral_name
        ):
            # Found the correct peripheral, now look for the register
            for reg in peripheral.findall(".//register"):
                reg_name_element = reg.find("name")
                if (
                    reg_name_element is not None
                    and reg_name_element.text == register_name
                ):
                    # Return the entire <register> as a string
                    return ET.tostring(reg, encoding="unicode")

    # If no match is found, return an empty string
    return ""


def count_bitfields(register_snippet: str) -> int:
    """Count the nr of bitfields in the given register snippet."""
    import xml.etree.ElementTree as ET

    root = ET.fromstring(register_snippet)
    n = len(root.findall(".//field"))
    return n


print(
    count_bitfields(
        extract_register_snippet(
            svd_file="APM32F411.svd",
            peripheral_name="USART1",
            register_name="CTRL3",
        )
    )
)


# # Load the SVD file for parsing
# # svd_file_path = "/mnt/data/APM32F411.svd"
# svd_file_path = "APM32F411.svd"
# # Parse the SVD file
# tree = ET.parse(svd_file_path)
# root = tree.getroot()
# # Locate the <register> block for CTRL3 in USART1
# ctrl3_register = None
# for peripheral in root.findall(".//peripheral"):
#     if peripheral.find("name").text == "USART1":
#         for register in peripheral.findall(".//register"):
#             if register.find("name").text == "CTRL3":
#                 ctrl3_register = register
#                 break
# # Check if CTRL3 register was found
# if ctrl3_register is not None:
#     # Count the bitfields under <fields>
#     fields = ctrl3_register.find("fields")
#     if fields is not None:
#         n_bitfields = len(fields.findall("field"))
#         print(n_bitfields)
#     else:
#         "No fields found under CTRL3 register."
# else:
#     "CTRL3 register not found in USART1."
