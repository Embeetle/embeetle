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

"""svd_compare.py.

Compares two SVD (XML) files while:
  - Ignoring XML comment nodes
  - Ignoring the order of child elements in most cases
  - BUT for <field> elements, we match them by their <name> sub-element.
    If <name> differs, we consider them unmatched (i.e., "missing" or "extra").

This avoids "partial mismatch spam" when a <field> is missing from one file
and the script tries to pair it with a different <field> in the other file.

Usage:
  python svd_compare.py file1.svd file2.svd

Author: ChatGPT
"""

import sys
import xml.etree.ElementTree as ET
from collections import defaultdict


def main():
    if len(sys.argv) != 3:
        print("Usage: python svd_compare.py file1.svd file2.svd")
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    # Parse both XMLs
    try:
        tree1 = ET.parse(file1)
        tree2 = ET.parse(file2)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        sys.exit(1)

    root1 = tree1.getroot()
    root2 = tree2.getroot()

    differences = []
    reorder_notes = []

    compare_elements(root1, root2, "/", differences, reorder_notes)

    if differences:
        print("SVD files are different")
        print("Differences found:")
        for diff in differences:
            print(f"  - {diff}")
    else:
        print("SVD files are the same")

    if reorder_notes:
        print("")
        for note in reorder_notes:
            print(f"[NOTE] {note}")


def compare_elements(e1, e2, path, differences, reorder_notes):
    """Compare e1 vs.

    e2 in a hierarchical manner.
    """
    # 1) Compare tag
    if e1.tag != e2.tag:
        differences.append(f"{path}: Different tags: '{e1.tag}' vs '{e2.tag}'")
        return

    current_path = f"{path}/{e1.tag}"

    # 2) Compare attributes
    if e1.attrib != e2.attrib:
        differences.append(
            f"{current_path}: Different attributes: {e1.attrib} vs {e2.attrib}"
        )

    # 3) Compare text
    text1 = (e1.text or "").strip()
    text2 = (e2.text or "").strip()
    if text1 != text2:
        differences.append(
            f"{current_path}: Different text: '{text1}' vs '{text2}'"
        )

    # 4) Compare tail text
    tail1 = (e1.tail or "").strip()
    tail2 = (e2.tail or "").strip()
    if tail1 != tail2:
        differences.append(
            f"{current_path}: Different tail text: '{tail1}' vs '{tail2}'"
        )

    # 5) Collect children (ignore comment nodes)
    children1 = [c for c in e1 if c.tag is not None]
    children2 = [c for c in e2 if c.tag is not None]

    # 6) If the sequence of tags differs, note reorder
    if len(children1) == len(children2):
        tags_in_seq1 = [c.tag for c in children1]
        tags_in_seq2 = [c.tag for c in children2]
        if tags_in_seq1 != tags_in_seq2 and len(children1) > 1:
            reorder_notes.append(
                f"{current_path}: child elements are reordered"
            )

    # 7) We do different matching strategies for <field> vs. other tags
    if e1.tag == "fields":
        # We'll match <field> by <name>.
        # But note <fields> could have other children (rare?), so let's do a fallback for those.
        fields1 = [c for c in children1 if c.tag == "field"]
        fields2 = [c for c in children2 if c.tag == "field"]
        # Any child that is not <field> we handle in a generic "best match" approach
        other1 = [c for c in children1 if c.tag != "field"]
        other2 = [c for c in children2 if c.tag != "field"]

        # Compare <field> specifically by name
        compare_fields_by_name(fields1, fields2, current_path, differences)

        # Compare other children (like <dim>, <reserved>, etc.) with a best-match or old approach
        compare_children_best_match(
            other1, other2, current_path, differences, reorder_notes
        )
    else:
        # For non-<fields> nodes, do a best-match approach ignoring child order
        compare_children_best_match(
            children1, children2, current_path, differences, reorder_notes
        )


def compare_fields_by_name(fields1, fields2, current_path, differences):
    """For <field> elements, match them by the text inside <name>. If there's no
    <name>, we skip it in the matching logic and treat it as unmatched.

    For each match, recursively compare them (which will in turn compare their
    children).
    """
    # Build dict by field_name -> list of elements
    # (In some SVDs, you might have multiple <field> with the same name. Rare, but possible.)
    map1 = group_fields_by_name(fields1)
    map2 = group_fields_by_name(fields2)

    all_names = set(map1.keys()) | set(map2.keys())
    for fname in all_names:
        group1 = map1.get(fname, [])
        group2 = map2.get(fname, [])

        if len(group1) != len(group2):
            differences.append(
                f"{current_path}: Different number of <field name='{fname}'> elements ({len(group1)} vs {len(group2)})"
            )

        # Pair them 1-to-1 in order
        used2 = set()
        for f1 in group1:
            best2_idx = None
            best_subdiff = None

            # We search for a 0-diff match if possible. If not found, we take the minimal diff match.
            best_diff_count = None
            for i, f2 in enumerate(group2):
                if i in used2:
                    continue
                subdiff = []
                # Recursively compare
                compare_elements(
                    f1, f2, current_path, subdiff, reorder_notes=[]
                )
                dcount = len(subdiff)
                if best_diff_count is None or dcount < best_diff_count:
                    best_diff_count = dcount
                    best_subdiff = subdiff
                    best2_idx = i
                if dcount == 0:
                    break

            if best2_idx is not None:
                used2.add(best2_idx)
                # Add subdiff from best match
                differences.extend(best_subdiff)
            else:
                # No match for f1
                fname_text = get_field_name_text(f1)
                differences.append(
                    f"{current_path}: No matching <field name='{fname_text}'> found in file2"
                )

        # leftover in group2
        leftover = len(group2) - len(used2)
        if leftover > 0:
            # For each leftover
            leftover_indices = [i for i in range(len(group2)) if i not in used2]
            for idx in leftover_indices:
                f2 = group2[idx]
                fname_text = get_field_name_text(f2)
                differences.append(
                    f"{current_path}: Extra <field name='{fname_text}'> in file2 not matched"
                )


def compare_children_best_match(
    ch1, ch2, current_path, differences, reorder_notes
):
    """Generic "best match" approach for child elements ignoring order and tag
    sequence.

    Steps:
      - Group children by tag
      - For each child in file1, find best match in file2 of same tag
      - If no match found => unmatched
      - leftover children => extra in file2
    """
    grouped1 = group_by_tag(ch1)
    grouped2 = group_by_tag(ch2)
    all_tags = set(grouped1.keys()) | set(grouped2.keys())

    for tag in all_tags:
        list1 = grouped1.get(tag, [])
        list2 = grouped2.get(tag, [])

        if len(list1) != len(list2):
            differences.append(
                f"{current_path}: Different number of <{tag}> children ({len(list1)} vs {len(list2)})"
            )

        used2 = set()
        for c1 in list1:
            best_idx = None
            best_diff_count = None
            best_subdiff = None
            best_subreorder = None
            for i, c2 in enumerate(list2):
                if i in used2:
                    continue
                subdiff = []
                subreorder = []
                compare_elements(c1, c2, current_path, subdiff, subreorder)
                dcount = len(subdiff)
                if best_diff_count is None or dcount < best_diff_count:
                    best_diff_count = dcount
                    best_subdiff = subdiff
                    best_subreorder = subreorder
                    best_idx = i
                if dcount == 0:
                    break

            if best_idx is not None:
                used2.add(best_idx)
                differences.extend(best_subdiff)
                reorder_notes.extend(best_subreorder)
            else:
                differences.append(
                    f"{current_path}: No matching <{c1.tag}> found in file2"
                )

        # leftover children in list2
        leftover = len(list2) - len(used2)
        if leftover > 0:
            leftover_indices = [i for i in range(len(list2)) if i not in used2]
            for idx in leftover_indices:
                c2 = list2[idx]
                differences.append(
                    f"{current_path}: Extra <{c2.tag}> in file2 not matched"
                )


def group_by_tag(children):
    """Group elements by their tag name."""
    dd = defaultdict(list)
    for c in children:
        dd[c.tag].append(c)
    return dd


def group_fields_by_name(fields):
    """
    Return a dict:
      { field_name_string : [field_element, field_element, ...], ... }

    If <name> is missing, use None as the key.
    """
    dd = defaultdict(list)
    for f in fields:
        fname = get_field_name_text(f)
        dd[fname].append(f)
    return dd


def get_field_name_text(field_elem):
    """Extract the text inside <name> for this <field>.

    If none, return None.
    """
    name_elem = field_elem.find("name")
    if name_elem is not None and name_elem.text:
        return name_elem.text.strip()
    else:
        return None


if __name__ == "__main__":
    main()
