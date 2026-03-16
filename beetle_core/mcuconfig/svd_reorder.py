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

"""svd_reorder.py.

Reorders <field> elements under <register>/<fields> by ascending <bitOffset>,
while preserving comments and the XML declaration.

Usage:
  python svd_reorder.py input.svd > output.svd

Requires:
  pip install lxml
"""

import sys
from lxml import etree


def main():
    if len(sys.argv) < 2:
        print("Usage: python svd_reorder.py input.svd > output.svd")
        sys.exit(1)

    input_path = sys.argv[1]

    # Parser that preserves comments and whitespace text.
    parser = etree.XMLParser(remove_comments=False, remove_blank_text=False)
    tree = etree.parse(input_path, parser)
    root = tree.getroot()

    # For each <register> in the SVD, reorder the <field> elements under <fields>.
    for register in root.xpath(".//register"):
        fields_elem = register.find("fields")
        if fields_elem is None:
            continue

        # Collect all children (which may include comments, text nodes, etc.).
        all_children = list(fields_elem)
        if not all_children:
            continue

        # We'll build a structure of ( [comments_above], field_element ) pairs.
        field_pairs = []
        comment_buffer = []

        # We'll also keep track of nodes that are neither comments nor <field>.
        leftover_nodes = []

        for node in all_children:
            if is_comment_node(node):
                # Accumulate in buffer for the *next* field that appears.
                comment_buffer.append(node)
            elif node.tag == "field":
                # Attach the current comment buffer to this field, then clear the buffer.
                field_pairs.append((comment_buffer, node))
                comment_buffer = []
            else:
                # Some other element or text node.
                leftover_nodes.append(node)

        # Any leftover comments after the last field go into leftover_nodes.
        if comment_buffer:
            leftover_nodes.extend(comment_buffer)

        # Sort fields by <bitOffset>
        def get_bit_offset(field_elem):
            bit_offset_elem = field_elem.find("bitOffset")
            return (
                int(bit_offset_elem.text) if bit_offset_elem is not None else 0
            )

        field_pairs.sort(key=lambda pair: get_bit_offset(pair[1]))

        # Clear out the <fields> element's children.
        for child in all_children:
            fields_elem.remove(child)

        # Re-insert sorted fields, each preceded by its associated comment nodes.
        for comments_list, field_elem in field_pairs:
            for cnode in comments_list:
                fields_elem.append(cnode)
            fields_elem.append(field_elem)

        # Finally, append leftover nodes (e.g. trailing comments, text).
        for leftover in leftover_nodes:
            fields_elem.append(leftover)

    # Write the modified XML to stdout as bytes, ensuring the XML declaration is included.
    output_bytes = etree.tostring(
        tree,
        encoding="utf-8",
        xml_declaration=True,  # <-- Ensures <?xml version="1.0" encoding="utf-8"?>
        pretty_print=True,
    )
    sys.stdout.buffer.write(output_bytes)


def is_comment_node(node):
    """Utility to check if an lxml node is a comment."""
    return isinstance(node, etree._Comment)


if __name__ == "__main__":
    main()
