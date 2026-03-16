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

import hardware_api.hardware_api as _hardware_api_
import hardware_api.chip_unicum as _chip_unicum_
import hardware_api.board_unicum as _board_unicum_
from typing import Dict, List, Tuple, Optional


def get_vendor_chip_board_dict() -> Dict[str, Dict[str, List[str]]]:
    """
    Returns a dictionary like:
    {
        'arduino':
        {
            'atmega328p-mu': ['custom', 'ARDUINO_UNO_SMD_R3', 'ARDUINO_NANO'],
            'atmega328p-pu': ['custom', 'ARDUINO_UNO_R3']
        },

        'embeetle':
        {
            'stm32f767zi': ['custom', 'NUCLEO_F767ZI', 'BEETLE_F767ZI'],
            'stm32l412kb': ['custom', 'NUCLEO_L412KB', 'BEETLE_L412KB']
        },

        'giga':
        {
            'gd32e230c8t6' : ['custom', 'GD32E230C_EVAL'],
            'gd32e231c8t6' : ['custom', 'GD32E231C_START'],
            'gd32e232k8q7' : ['custom', 'GD32E232K_START'],
            'gd32vf103cbt6': ['custom', 'GD32VF103C_START']
        },

        'microchip-atmel':
        {
            'atmega328p-mu': ['custom', 'ARDUINO_UNO_SMD_R3', 'ARDUINO_NANO'],
            'atmega328p-pu': ['custom', 'ARDUINO_UNO_R3']
        },

        'nordic':
        {
            'nrf52833': ['custom', 'PCA10100'],
            'nrf52840': ['custom', 'PCA10056']
        },

        'nuvoton':
        {
            'm031sd2ae'  : ['custom', 'NUMAKER_M031SD_V1_2'],
            'm031se3ae'  : ['custom', 'NUMAKER_M031SE_V1_1'],
            'm031tb0ae'  : ['custom', 'NUMAKER_M031TB_V1_1'],
            'm031tc1ae'  : ['custom', 'NUMAKER_M031TC_V1_1'],
            'm032se3ae'  : ['custom', 'NUMAKER_M032SE_V1_3'],
            'm263kiaae'  : ['custom', 'NUMAKER_M263KI_V1_2'],
            'm483kgcae2a': ['custom', 'NUMAKER_M483KG_V1_1'],
            'nuc029sde'  : ['custom', 'NUTINY_NUC029SDE_V1_0'],
        },

        'stmicro':
        {
            'stm32f303k8': ['custom', 'NUCLEO_F303K8'],
            'stm32f303vc': ['custom', 'STM32F3_DISCO'],
            'stm32f401re': ['custom', 'NUCLEO_F401RE'],
            'stm32f407vg': ['custom', 'STM32F4_DISCO'],
            'stm32f429zi': ['custom', 'STM32F429I_DISCO'],
            'stm32f722ze': ['custom', 'NUCLEO_F722ZE'],
            'stm32f746ng': ['custom', 'STM32F746G_DISCO'],
            'stm32f746zg': ['custom', 'NUCLEO_F746ZG'],
            'stm32f767zi': ['custom', 'NUCLEO_F767ZI', 'BEETLE_F767ZI'],
            'stm32h743zi': ['custom', 'NUCLEO_H743ZI'],
            'stm32l053r8': ['custom', 'NUCLEO_L053R8'],
            'stm32l412kb': ['custom', 'NUCLEO_L412KB', 'BEETLE_L412KB'],
            'stm32l476rg': ['custom', 'NUCLEO_L476RG'],
        },
    }

    """
    result = {}

    mf_list = _hardware_api_.HardwareDB().list_manufacturers(
        for_boards=True,
        for_chips=True,
        for_probes=False,
    )
    for mf in mf_list:
        result[mf.lower()] = {}
        # List all chips that are produced by this manufacturer or that appear on one of its boards
        # (eg. Arduino).
        chip_listing: List[str] = []
        for chipname in _hardware_api_.HardwareDB().list_chips(
            chipmf_list=[
                mf.lower(),
            ]
        ):
            chip_listing.append(chipname)
            continue
        for board_unicum in _hardware_api_.HardwareDB().list_boards(
            boardmf_list=[
                mf.lower(),
            ],
            return_unicums=True,
        ):
            assert isinstance(board_unicum, _board_unicum_.BOARD)
            if board_unicum.get_name().lower() == "custom":
                continue
            chip_listing.append(board_unicum.get_board_dict()["chip"])
            continue
        # Per chip that can be associated with this manufacturer,
        # list all the boards that have this chip on them.
        for chip_name in list(set(chip_listing)):
            chip_unicum = _chip_unicum_.CHIP(chip_name)
            result[mf.lower()][chip_name] = [
                board
                for board in _hardware_api_.HardwareDB().list_boards(
                    boardfam_list=None,
                    boardmf_list=None,
                    chip_list=[
                        chip_unicum.get_name(),
                    ],
                    return_unicums=False,
                )
            ]
            continue
        continue
    return result


def vendor_board_chip_filter(
    selected_vendor: Optional[str] = None,
    selected_board: Optional[str] = None,
    selected_chip: Optional[str] = None,
) -> Tuple[List[str], List[str], List[str]]:
    """Based on the given selections, return a list of valid vendors, valid
    boards and valid chips.

    :param selected_vendor: [Optional] Selected vendor. None if no selection.
    :param selected_board: [Optional] Selected board. None if no selection.
    :param selected_chip: [Optional] Selected chip. None if no selection.
    :return: valid_vendors, valid_boards, valid_chips
    """

    def pure_filter(_selected_vendor, _selected_board, _selected_chip):
        if _selected_vendor is not None:
            _selected_vendor = (
                _selected_vendor.lower().replace(" ", "_").replace("-", "_")
            )
        if _selected_board is not None:
            _selected_board = (
                _selected_board.lower().replace(" ", "_").replace("-", "_")
            )
        if _selected_chip is not None:
            _selected_chip = (
                _selected_chip.lower().replace(" ", "_").replace("-", "_")
            )
        _valid_vendors = []
        _valid_boards = []
        _valid_chips = []
        for mf_name, mf_dict in get_vendor_chip_board_dict().items():
            if (_selected_vendor is not None) and (
                mf_name.lower().replace(" ", "_").replace("-", "_")
                != _selected_vendor
            ):
                # Ignore this vendor
                continue
            for chip_name, board_list in mf_dict.items():
                if (_selected_chip is not None) and (
                    chip_name.lower().replace(" ", "_").replace("-", "_")
                    != _selected_chip
                ):
                    # Ignore this chip
                    continue
                for board_name in board_list:
                    if (_selected_board is not None) and (
                        board_name.lower().replace(" ", "_").replace("-", "_")
                        != _selected_board
                    ):
                        # Ignore this board
                        continue
                    # All filters passed!
                    _valid_vendors.append(mf_name)
                    _valid_boards.append(board_name)
                    _valid_chips.append(chip_name)
        return (
            list(set(_valid_vendors)),
            list(set(_valid_boards)),
            list(set(_valid_chips)),
        )

    valid_vendors, _, _ = pure_filter(None, selected_board, selected_chip)
    _, valid_boards, _ = pure_filter(selected_vendor, None, selected_chip)
    _, _, valid_chips = pure_filter(selected_vendor, selected_board, None)
    return (
        valid_vendors,
        valid_boards,
        valid_chips,
    )
