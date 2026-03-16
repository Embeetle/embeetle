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

from __future__ import annotations
from typing import *
from components.decorators import ref
import weakref, os, threading, functools
import qt, data, purefunctions
import fnmatch as _fn_
import project.elf_reader as _er_
import dashboard.items.chip_items.chip_items as _da_chip_items_
import project.segments.project_segment as _ps_
import hardware_api.chip_unicum as _chip_unicum_
import hardware_api.hardware_api as _hardware_api_

if TYPE_CHECKING:
    import project.segments.board_seg.board as _board_
    import project.segments.path_seg.treepath_seg as _treepath_seg_
    import project.segments.path_seg.toolpath_seg as _toolpath_seg_
from various.kristofstuff import *

# ^                                           MEMSECTION                                           ^#
# % ============================================================================================== %#
# % MemSection()                                                                                   %#
# %                                                                                                %#


class MemSection(_ps_.ProjectSubsegment):
    """One unit in the SECTIONS{..} part of the linkerscript."""

    def __init__(
        self,
        name: str,  # Example: '.isr_vector'.
        usage: int,  # Current usage [nr of bytes] -> get from elffile!
    ) -> None:
        """"""
        super().__init__()
        self.__name: str = name
        self.__usage: int = usage
        self.__memregion_storage_ref: Optional[
            weakref.ReferenceType[MemRegion]
        ] = None
        self.__memregion_runtime_ref: Optional[
            weakref.ReferenceType[MemRegion]
        ] = None
        return

    def get_name(self) -> str:
        """"""
        return self.__name

    def in_region(self, memregion: MemRegion) -> bool:
        """"""
        if memregion is self.get_memregion_storage():
            return True
        if memregion is self.get_memregion_runtime():
            return True
        return False

    def calc_usage(self) -> None:
        """
        WARNING:
        The call get_memsection_usage() used to print warnings about sections not being present in
        the final .elf file. I have commented out that print statement.
        """
        if _er_.ElfReader().is_open():
            self.__usage = _er_.ElfReader().get_memsection_usage(
                name=self.get_name()
            )
            return
        if _er_.ElfReader().open():
            # Read elf file successfull
            self.__usage = _er_.ElfReader().get_memsection_usage(
                name=self.get_name()
            )
            _er_.ElfReader().close()
        else:
            self.__usage = 0
        return

    def get_usage(self, _format: Optional[str] = None) -> Union[int, str]:
        """"""
        if _format is None:
            return self.__usage
        if _format.lower() == "hex":
            return hex(self.__usage)
        if _format.lower() == "kb":
            return int(self.__usage / 1024)
        assert False

    @ref
    def get_memregion_storage(self) -> Optional[MemRegion]:
        """"""
        return self.__memregion_storage_ref  # type: ignore

    @ref
    def get_memregion_runtime(self) -> Optional[MemRegion]:
        """"""
        return self.__memregion_runtime_ref  # type: ignore

    def set_memregion_storage(self, memregion: MemRegion) -> None:
        """"""
        self.__memregion_storage_ref = (
            weakref.ref(memregion) if memregion is not None else None
        )
        return

    def set_memregion_runtime(self, memregion: MemRegion) -> None:
        """"""
        self.__memregion_runtime_ref = (
            weakref.ref(memregion) if memregion is not None else None
        )
        return

    def check(self) -> None:
        """"""
        memregion_storage = self.get_memregion_storage()
        if memregion_storage is not None:
            assert memregion_storage.has_memsection(self)
        memregion_runtime = self.get_memregion_runtime()
        if memregion_runtime is not None:
            assert memregion_runtime.has_memsection(self)
        return


# ^                                           MEMREGION                                            ^#
# % ============================================================================================== %#
# % MemRegion()                                                                                    %#
# %                                                                                                %#


class MemRegion(_ps_.ProjectSubsegment):
    """One line in the MEMORY{..} part of the linkerscript."""

    def __init__(
        self,
        name: str,  # Example 'DTCMRAM'.
        memtype: _chip_unicum_.MEMTYPE,  # MEMTYPE.RAM or MEMTYPE.FLASH
        rights: str,  # Example 'xrw'.
        origin: int,  # Start address [nr of bytes].
        length: int,  # Memory region length [nr of bytes].
        usage: int,  # Current usage [nr of bytes]. -> get from elffile!
    ) -> None:
        """"""
        super().__init__()
        # $ 1. Assign variables.
        self.__name: str = name
        self.__memtype: _chip_unicum_.MEMTYPE = memtype
        self.__rights: str = rights
        self.__origin: int = origin
        self.__length: int = length
        self.__usage: int = usage

        # List of memory sections is a list of tuples: [ (MemSection(), 'sr'), ... ]
        self.__memsectionList: List[Tuple[MemSection, str]] = []
        self.__v_memItem_ref: Optional[
            weakref.ReferenceType[_da_chip_items_.ChipMemoryItem]
        ] = None

        # $ 2. Check variables.
        assert isinstance(self.__name, str)
        assert isinstance(self.__memtype, _chip_unicum_.MEMTYPE)
        assert isinstance(self.__rights, str)
        assert isinstance(self.__origin, int)
        assert isinstance(self.__length, int)
        assert isinstance(self.__usage, int)
        return

    def set_v_memItem(self, _v_memItem: _da_chip_items_.ChipMemoryItem) -> None:
        """"""
        if not isinstance(_v_memItem, _da_chip_items_.ChipMemoryItem):
            purefunctions.printc(
                f"\n\nERROR: _v_memItem = {_v_memItem.__class__}()\n\n",
                color="error",
            )
            raise Exception()
        self.__v_memItem_ref = weakref.ref(_v_memItem)
        return

    @ref
    def get_v_memItem(self) -> _da_chip_items_.ChipMemoryItem:
        """"""
        return self.__v_memItem_ref  # type: ignore

    def get_name(self) -> str:
        """"""
        return self.__name

    def get_origin(self, _format: Optional[str] = None) -> Union[int, str]:
        """"""
        if _format is None:
            return self.__origin
        if _format.lower() == "hex":
            return hex(self.__origin)
        if _format.lower() == "kb":
            return int(self.__origin / 1024)
        assert False

    def set_origin(self, origin: int) -> None:
        """"""
        self.__origin = origin
        return

    def get_length(self, _format: Optional[str] = None) -> Union[int, str]:
        """"""
        if _format is None:
            return self.__length
        if _format.lower() == "hex":
            return hex(self.__length)
        if _format.lower() == "kb":
            return int(self.__length / 1024)
        assert False

    def set_length(self, length: int) -> None:
        """"""
        self.__length = length
        return

    def has_memsection(self, memsection: MemSection) -> bool:
        """"""
        for e in self.__memsectionList:
            if e[0] is memsection:
                return True
        return False

    def get_memsection(self, name: str) -> Optional[MemSection]:
        """"""
        for e in self.__memsectionList:
            if e[0].get_name() == name:
                return e[0]
        return None

    def get_memsection_list(
        self, form: Optional[str] = None
    ) -> List[MemSection]:
        """"""
        if form is None:
            return [e[0] for e in self.__memsectionList]
        assert form == "sr" or form == "s" or form == "r"
        return [e[0] for e in self.__memsectionList if form in e[1]]

    def add_memsection(self, memsection: MemSection, form: str) -> None:
        """"""
        assert isinstance(memsection, MemSection)
        assert memsection not in self.get_memsection_list()
        assert form == "sr" or form == "s" or form == "r"
        self.__memsectionList.append((memsection, form))
        if "s" in form:
            memsection.set_memregion_storage(memregion=self)
        if "r" in form:
            memsection.set_memregion_runtime(memregion=self)
        return

    def remove_memsection(self, memsection: MemSection) -> None:
        """"""
        assert isinstance(memsection, MemSection)
        assert memsection in self.get_memsection_list()
        for i in range(len(self.__memsectionList)):
            if self.__memsectionList[i][0] is memsection:
                del self.__memsectionList[i]
                return
        assert False

    def check(self) -> None:
        """"""
        for memsection in self.get_memsection_list():
            assert memsection.in_region(memregion=self)
        for memsection in self.get_memsection_list(form="sr"):
            assert memsection.get_memregion_storage() is self
            assert memsection.get_memregion_runtime() is self
        for memsection in self.get_memsection_list(form="s"):
            assert memsection.get_memregion_storage() is self
        for memsection in self.get_memsection_list(form="r"):
            assert memsection.get_memregion_runtime() is self
        for memsection in [
            mem
            for mem in self.get_memsection_list()
            if mem not in self.get_memsection_list(form="s")
        ]:
            assert memsection.get_memregion_storage() is not self
        for memsection in [
            mem
            for mem in self.get_memsection_list()
            if mem not in self.get_memsection_list(form="r")
        ]:
            assert memsection.get_memregion_runtime() is not self
        for memsection in self.get_memsection_list():
            memsection.check()
        if self.get_v_memItem() is not None:
            assert self.get_v_memItem().get_projSegment() is self
        return

    def get_usage(self, _format: Optional[str] = None) -> Union[int, str]:
        """"""
        if _format is None:
            return self.__usage
        if _format.lower() == "hex":
            return hex(self.__usage)
        if _format.lower() == "kb":
            return int(self.__usage / 1024)
        assert False

    def set_usage(self, usage: int) -> None:
        """"""
        assert isinstance(usage, int)
        if usage > self.__length:
            purefunctions.printc(
                f"WARNING: Attempt to set memory usage to {usage} while "
                f"total length is {self.__length}",
                color="warning",
            )
            usage = self.__length
        self.__usage = usage
        return

    def calc_usage(self) -> None:
        """Loop over all the MemSection()s in this MemRegion().

        For each of them, extract the usage from the elf file. Add it all up and
        set the usage of this MemRegion() eventually.
        """
        if data.current_project is None:
            self.set_usage(usage=0)
            return
        try:
            if data.source_analysis_only:
                self.set_usage(usage=0)
                return
        except:
            pass
        treepath_seg: Optional[_treepath_seg_.TreepathSeg] = (
            data.current_project.get_treepath_seg()
        )
        elf_abspath = treepath_seg.get_abspath("ELF_FILE")
        if (elf_abspath is None) or (not os.path.isfile(elf_abspath)):
            self.set_usage(usage=0)
            return
        assert os.path.isfile(elf_abspath)
        size = 0
        if _er_.ElfReader().open(elf_abspath):
            # Opened successful
            for memsection in self.get_memsection_list():
                memsection.calc_usage()
                size += cast(int, memsection.get_usage())
            _er_.ElfReader().close()
            self.set_usage(usage=size)
        else:
            # Cannot read elf file
            purefunctions.printc(
                f"WARNING: Embeetle cannot parse elf-file {q}{elf_abspath}{q}",
                color="warning",
            )
            self.set_usage(usage=0)
        return

    def get_rights(self) -> str:
        """"""
        return self.__rights

    def set_rights(self, rights: str) -> None:
        """"""
        self.__rights = rights
        return

    def get_memtype(self) -> _chip_unicum_.MEMTYPE:
        """"""
        return self.__memtype

    def set_memtype(self, memtype: _chip_unicum_.MEMTYPE) -> None:
        """"""
        assert isinstance(memtype, _chip_unicum_.MEMTYPE)
        self.__memtype = memtype
        return

    def get_linkerscript_line(self) -> str:
        """'DTCMRAM (xrw) : ORIGIN = 0x20000000, LENGTH = 128K'."""
        line = self.get_name() + " "
        line += f"({self.get_rights()}) : "
        line += f'ORIGIN = {self.get_origin("hex")}, '
        line += f'LENGTH = {self.get_length("kb")}K'
        return line

    def print_all(self) -> None:
        """"""
        print("")
        print(f"MEMORY REGION")
        print(f"    name:   {self.get_name()}")
        print(f"    type:   {self.get_memtype()}")
        print(f"    rights: {self.get_rights()}")
        print(f'    origin: {self.get_origin("hex")}')
        print(f'    length: {self.get_length("kb")}Kb')
        print(f'    usage:  {self.get_usage("kb")}Kb')
        print(f"    sections: ")
        for e in self.__memsectionList:
            memsection = e[0]
            form = e[1]
            assert isinstance(memsection, MemSection)
            assert isinstance(form, str)
            line = f"        {memsection.get_name()} "
            line = line.ljust(28)
            print(
                f"{line}["
                f"storage: {memsection.get_memregion_storage().get_name()}, "
                f"runtime: {memsection.get_memregion_runtime().get_name()}"
                f"] -> usage: "
                f'{memsection.get_usage("kb")}Kb, '
                f"{memsection.get_usage()}bytes"
            )
        print("")
        return

    def get_datastruct(
        self,
    ) -> Dict[str, Union[str, Dict[str, Dict[str, str]]]]:
        """Return a datastruct for Matic."""
        memregion_struct: Dict[str, Union[str, Dict[str, Dict[str, str]]]] = {
            "type": str(self.get_memtype()),
            "rights": self.get_rights(),
            "origin": cast(str, self.get_origin("hex")),
            "length": cast(str, self.get_length("hex")),
            "sections": cast("Dict[str, Dict[str, str]]", {}),
        }
        for e in self.__memsectionList:
            memsection = e[0]
            form = e[1]
            assert isinstance(memsection, MemSection)
            assert isinstance(form, str)
            cast("Dict[str, Dict[str, str]]", memregion_struct["sections"])[
                memsection.get_name()
            ] = {
                "usage": cast(str, memsection.get_usage("hex")),
            }
        return memregion_struct


# ^                                              CHIP                                              ^#
# % ============================================================================================== %#
# % Chip()                                                                                         %#
# %                                                                                                %#


class Chip(_ps_.ProjectSegment):
    @classmethod
    def create_default_Chip(cls, chip_unicum: _chip_unicum_.CHIP) -> Chip:
        """Create a default Chip()-object for the given 'chip_unicum'."""
        assert chip_unicum is not None
        return cls(is_fake=False, chip_unicum=chip_unicum)

    @classmethod
    def create_empty_Chip(cls) -> Chip:
        """Create an empty Chip()-object."""
        return cls.create_default_Chip(_chip_unicum_.CHIP("NONE"))

    @classmethod
    def load(
        cls,
        configcode: Optional[Dict[str, Optional[str]]],
        rootpath: str,
        project_report: Dict,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Load Chip()-object from the config file (already loaded into a
        dictionary).

        Note: The project_report is not returned, but simply modified here.
        """
        # $ Figure out chip name
        chip_name: Optional[str] = None
        if configcode is None:
            chip_name = "none"
            purefunctions.printc(
                f"WARNING: Chip().load() got configcode parameter None\n",
                color="warning",
            )
        else:
            try:
                chip_name = configcode["chip_name"]
            except:
                try:
                    chip_name = configcode["chip"]
                except:
                    chip_name = "none"
                    purefunctions.printc(
                        f"WARNING: The {q}dashboard_config.btl{q} file does not define a chip\n",
                        color="warning",
                    )
        if (chip_name is None) or (chip_name.lower() in ("none", "null")):
            chip_name = "none"

        # $ Construct chip unicum
        chip_unicum = None
        try:
            chip_unicum = _chip_unicum_.CHIP(chip_name)
        except KeyError:
            chip_unicum = _chip_unicum_.CHIP("none")
            purefunctions.printc(
                f"WARNING: Embeetle does not recognize chip {q}{chip_name}{q}\n",
                color="warning",
            )
        chip: Chip = cls(
            is_fake=False,
            chip_unicum=chip_unicum,
        )
        callback(chip, callbackArg)
        return

    __slots__ = (
        "__chip_unicum",
        "__memregion_list",
        "__memory_regions_raw_data",
        "__memory_sections_raw_data",
        "__state_dict",
        "_v_rootItem",
        "_v_deviceItem",
        "__trigger_dashboard_refresh_mutex",
        "__linkerscript_signals_bound",
        "__trigger_memory_repair_mutex",
        "__memory_repair_reentered",
    )

    def __init__(
        self,
        is_fake: bool,
        chip_unicum: _chip_unicum_.CHIP,
    ) -> None:
        """Create Chip()-instance."""
        super().__init__(is_fake)
        assert isinstance(chip_unicum, _chip_unicum_.CHIP)

        # Use a mutex to protect the dashboard refreshing from re-entring.
        self.__trigger_dashboard_refresh_mutex = threading.Lock()
        self.__trigger_memory_repair_mutex = threading.Lock()
        self.__memory_repair_reentered = False

        # & Variables
        self.__chip_unicum = chip_unicum
        self.__memregion_list: List[MemRegion] = []
        self.__memory_regions_raw_data = {}
        self.__memory_sections_raw_data = {}
        self.__state_dict = {
            "DEVICE": {"error": False, "warning": False, "asterisk": False},
        }

        # & History
        if not is_fake:
            self.get_history().register_getters(
                chip_unicum=self.get_chip_unicum,
            )
            self.get_history().register_setters(
                chip_unicum=self.set_chip_unicum,
            )
            self.get_history().register_asterisk_setters(
                chip_unicum=self.set_chip_asterisk,
            )
            self.get_history().register_refreshfunc(
                self.trigger_dashboard_refresh,
            )

        # & Dashboard
        self._v_rootItem: Optional[_da_chip_items_.ChipRootItem] = None
        self._v_deviceItem: Optional[_da_chip_items_.ChipDeviceItem] = None

        # & Linkerscript signal dispatcher
        self.__linkerscript_signals_bound: bool = False
        return

    def get_chipfam_unicum(self) -> _chip_unicum_.CHIPFAMILY:
        """Access the CHIPFAMILY()-Unicum."""
        return _chip_unicum_.CHIPFAMILY(
            self.__chip_unicum.get_chip_dict(board=None)["chipfamily"]
        )

    def get_chip_unicum(self) -> _chip_unicum_.CHIP:
        """Access the CHIP()-Unicum."""
        return self.__chip_unicum

    def set_chip_unicum(self, chip_unicum: _chip_unicum_.CHIP) -> None:
        """Swap the CHIP()-Unicum."""
        assert isinstance(chip_unicum, _chip_unicum_.CHIP)
        self.__chip_unicum = chip_unicum

    def get_name(self) -> str:
        """Get the name of the CHIP()-Unicum."""
        return self.__chip_unicum.get_name()

    def get_chip_dict(self, board: Optional[str]) -> Dict[str, Any]:
        """Access the json-dictionary from the CHIP()-Unicum."""
        return self.__chip_unicum.get_chip_dict(board)

    def clone(self, is_fake: bool = True) -> Chip:
        """Clone this object.

        Method used by Intro Wizard to populate itself with fake objects.
        """
        cloned_chip = Chip(
            is_fake=is_fake,
            chip_unicum=self.__chip_unicum,
        )
        return cloned_chip

    def get_complete_memory_structure(self) -> Union[Dict, None]:
        """
        Return the complete memory structure as laid out in the linkerscript. The returned dict-
        ionary can look like this:

        ┌────────────────────────────────────────────────────────┐
        │   returned_dict = {                                    │
        │       'FLASH':                                         │
        │       {                                                │
        │           'type'    : 'MEMTYPE.FLASH',                 │
        │           'length'  : '0x200000',                      │
        │           'origin'  : '0x8000000',                     │
        │           'rights'  : 'rx',                            │
        │           'sections':                                  │
        │           {                                            │
        │               '.ARM'          : {'usage': '0x8'},      │
        │               '.ARM.extab'    : {'usage': '0x0'},      │
        │               '.data'         : {'usage': '0x10'},     │
        │               '.fini_array'   : {'usage': '0x8'},      │
        │               '.init_array'   : {'usage': '0x8'},      │
        │               '.isr_vector'   : {'usage': '0x1f8'},    │
        │               '.preinit_array': {'usage': '0x0'},      │
        │               '.rodata'       : {'usage': '0x18'},     │
        │               '.text'         : {'usage': '0x1e98'}    │
        │           },                                           │
        │                                                        │
        │       },                                               │
        │                                                        │
        │       'RAM':                                           │
        │       {                                                │
        │           'type'    : 'MEMTYPE.RAM',                   │
        │           'length'  : '0x80000',                       │
        │           'origin'  : '0x20000000',                    │
        │           'rights'  : 'xrw',                           │
        │           'sections':                                  │
        │           {                                            │
        │               '._user_heap_stack': {'usage': '0x600'}, │
        │               '.bss':              {'usage': '0xe8'},  │
        │               '.data':             {'usage': '0x10'}   │
        │           },                                           │
        │       }                                                │
        │   }                                                    │
        └────────────────────────────────────────────────────────┘

        The toplevel 'keys' in this dictionary are the memory regions - typically FLASH and RAM, but
        can also have special ones like TCMRAM, ...

        Each memory region has a few memory sections, like .rodata, .text, .bss, .data, ... For each
        of these memory sections, I give the usage. This usage is zero before the build took place.
        Only after a build - when I can get hold of the .elf file - the usages are filled in.

        WARNING:
        This function returns None if the linkerscript has errors and cannot be parsed properly. It
        also returns None if you call the function too early - while Embeetle is still populating
        the dashboard - so the linkerscript hasn't been parsed yet.
        """
        assert not self.is_fake()
        if self.__memregion_list is None:
            return None
        if len(self.__memregion_list) == 0:
            return None
        mem_datastruct: Dict[
            str, Dict[str, Union[str, Dict[str, Dict[str, str]]]]
        ] = {}
        for memregion in self.__memregion_list:
            mem_datastruct[memregion.get_name()] = memregion.get_datastruct()
        return mem_datastruct

    def show_on_dashboard(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Show this Chip()-instance on the dashboard.

        Only the toplevel item is shown, but the child
        items are instantiated and added to the toplevel item. They get shown when the user clicks
        on the toplevel item.
        NOTE:
        Call to 'repair_memregion_list()' initiates the first linkerscript parsing!
        """
        assert not self.is_fake()
        self._v_rootItem = _da_chip_items_.ChipRootItem(chip=self)
        self._v_deviceItem = _da_chip_items_.ChipDeviceItem(
            chip=self,
            rootdir=self._v_rootItem,
            parent=self._v_rootItem,
        )
        self._v_rootItem.add_child(
            self._v_deviceItem,
            alpha_order=False,
            show=False,
            callback=None,
            callbackArg=None,
        )
        data.dashboard.add_root(self._v_rootItem)
        self.__try_to_connect_linkerscript_signals()
        if callback is not None:
            callback(callbackArg)
        return

    def __try_to_connect_linkerscript_signals(self) -> None:
        """"""
        if self.is_fake():
            return
        if self.__linkerscript_signals_bound:
            return
        if data.signal_dispatcher is None:
            return
        if data.signal_dispatcher.source_analyzer is None:
            return
        self.__linkerscript_signals_bound = True
        data.signal_dispatcher.source_analyzer.memory_regions_update.connect(
            self.memory_regions_update_slot,
        )
        data.signal_dispatcher.source_analyzer.memory_sections_update.connect(
            self.memory_sections_update_slot,
        )
        return

    def memory_regions_update_slot(
        self,
        memory_regions_johan: Dict[str, Dict[str, Union[int, str]]],
    ) -> None:
        """
        memory_regions_johan = {
            'DTCMRAM': {
                'origin'        : 536870912,
                'size'          : 131072,
                'access_rights' : 'xrw',
            },
            'RAM_D1': {
                'origin'        : 603979776,
                'size'          : 524288,
                'access_rights' : 'xrw',
            },
            ...
        }
        """
        self.__memory_regions_raw_data = memory_regions_johan
        self.repair_memregion_list()
        return

    def memory_sections_update_slot(
        self,
        memory_sections_johan: Dict[str, Dict[str, str]],
    ) -> None:
        """
        memory_sections_johan = {
            '.isr_vector': {
                'runtime_region' : 'FLASH',
                'load_region'    : 'FLASH',
            },
            '.text': {
                'runtime_region' : 'FLASH',
                'load_region'    : 'FLASH',
            },
            ...
        }
        """
        self.__memory_sections_raw_data = memory_sections_johan
        self.repair_memregion_list()
        return

    def show_on_intro_wizard(
        self,
        vlyt: qt.QVBoxLayout,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Display the MICROCONTROLLER on the Intro Wizard, inside the given
        vlyt."""
        assert self.is_fake()
        self._v_deviceItem = _da_chip_items_.ChipDeviceItem(
            chip=self,
            rootdir=None,
            parent=None,
        )
        self._v_deviceItem.get_layout().initialize()
        vlyt.addLayout(self._v_deviceItem.get_layout())
        return

    def get_impacted_files(self) -> List[str]:
        """"""
        impacted_files = []
        if self.__state_dict["DEVICE"]["asterisk"]:
            impacted_files.append("DASHBOARD_MK")
            impacted_files.append("OPENOCD_CHIPFILE")
            impacted_files.append("GDB_FLASHFILE")
            impacted_files.append("LINKERSCRIPT")
        return impacted_files

    def get_state(self, obj: str, errtype: str) -> bool:
        """"""
        return self.__state_dict[obj][errtype]

    def update_states(
        self,
        board: Optional[_board_.Board] = None,
        project_report: Optional[Dict] = None,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """The states no longer get pushed directly to the GUI elements.

        Instead, I store them locally in the Chip()-instance. The GUI elements
        pull them when syncing.
        """
        projObj = data.current_project
        is_fake: bool = self.is_fake()
        if board is None:
            if is_fake:
                board = data.current_project.intro_wiz.get_fake_board()
            else:
                board = data.current_project.get_board()
        selected_name: Optional[str] = self.get_name()
        err_state: bool = False

        # * Nothing selected
        # Always report an error.
        if (selected_name is None) or (selected_name.lower() == "none"):
            err_state = True

        # * Something selected
        # Check if the selected chip is compatible with the board.
        else:
            if board.get_name().lower() == "custom":
                err_state = False
            elif board.get_board_dict()["chip"] == self.get_name():
                err_state = False
            else:
                err_state = True

        # * Apply state
        self.__state_dict["DEVICE"]["error"] = err_state
        if project_report is not None:
            project_report["chip_report"]["DEVICE"]["error"] = err_state

        if callback is not None:
            callback(callbackArg)
        return

    def trigger_dashboard_refresh(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Applies both on Dashboard and Intro Wizard. It will do:

          - update own states
          - update states of related segments (toolpath_seg)
          - refresh own's widgets

        Note: This function does not repair the memory!
        """
        if not self.__trigger_dashboard_refresh_mutex.acquire(blocking=False):
            qt.QTimer.singleShot(
                100,
                functools.partial(
                    self.trigger_dashboard_refresh,
                    callback,
                    callbackArg,
                ),
            )
            return
        is_fake = self.is_fake()
        toolpath_seg: Optional[_toolpath_seg_.ToolpathSeg] = None
        if is_fake:
            toolpath_seg = (
                data.current_project.intro_wiz.get_fake_toolpath_seg()
            )
        else:
            toolpath_seg = data.current_project.get_toolpath_seg()

        def update_toolpath_states(*args) -> None:
            # Update states of the ToolpathSeg(), then go to the next function
            # depending on some factors.
            next_func: Optional[Callable] = None
            next_arg: Optional[bool] = None

            # & Dashboard
            if not is_fake:
                if self._v_rootItem is None:
                    next_func = finish
                else:
                    next_func = start_refresh

            # & Intro Wizard
            else:
                next_func = start_refresh
                next_arg = False

            # & Both
            toolpath_seg.update_states(
                callback=next_func,
                callbackArg=next_arg,
            )
            return

        def start_refresh(*args) -> None:
            # & Dashboard
            # Refresh the root item recursively.
            if not is_fake:
                if (self._v_rootItem is None) or (
                    self._v_rootItem._v_emitter is None
                ):
                    finish()
                    return
                self._v_rootItem._v_emitter.refresh_recursive_later_sig.emit(
                    True,
                    False,
                    finish,
                    None,
                )
                return

            # & Intro Wizard
            # Just refresh the device item, but it's not sure it exists.
            assert is_fake
            if (self._v_deviceItem is None) or (
                self._v_deviceItem._v_emitter is None
            ):
                finish()
                return
            self._v_deviceItem._v_emitter.refresh_later_sig.emit(
                True,
                False,
                finish,
                None,
            )
            return

        def finish(*args) -> None:
            # & Intro Wizard
            if is_fake:
                self.__trigger_dashboard_refresh_mutex.release()
                if callback is not None:
                    callback(callbackArg)
                return

            # & Dashboard
            if data.dashboard is not None:
                data.dashboard.check_unsaved_changes()
            self.__trigger_dashboard_refresh_mutex.release()
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        # First update states of this Chip()-instance.
        self.update_states(
            callback=update_toolpath_states,
            callbackArg=None,
        )
        return

    def set_chip_asterisk(self, on: bool) -> None:
        """"""
        self.__state_dict["DEVICE"]["asterisk"] = on

    def get_memregion(self, name: str) -> Optional[MemRegion]:
        """"""
        assert not self.is_fake()
        for memregion in self.__memregion_list:
            if memregion.get_name() == name:
                return memregion
        return None

    def get_incompatible_familynames(self) -> List[str]:
        """Get all the other chipfamily names from the same manufacturer."""
        assert not self.is_fake()
        if self.get_name().lower() == "custom":
            return []
        incompatible_familynames: List[str] = []
        myfamilyname: str = self.__chip_unicum.get_chip_dict(board=None)[
            "chipfamily"
        ]
        for chipfam_name in _hardware_api_.HardwareDB().list_chipfamilies(
            manufacturer_list=[
                self.__chip_unicum.get_chip_dict(board=None)["manufacturer"],
            ],
        ):
            if chipfam_name != myfamilyname:
                incompatible_familynames.append(chipfam_name)
            continue
        return incompatible_familynames

    def get_memregion_list(self) -> List[MemRegion]:
        """"""
        assert not self.is_fake()
        return self.__memregion_list

    def get_v_memregion_list(self) -> List[_da_chip_items_.ChipMemoryItem]:
        """"""
        assert not self.is_fake()
        return [
            item
            for item in self._v_rootItem.get_childlist()
            if isinstance(item, _da_chip_items_.ChipMemoryItem)
        ]

    def is_compatible_with_flashtool(self, uid: str) -> bool:
        """Check if this particular instance is compatible with the given
        flashtool unique id.

        Let the custom-chip always be compatible (otherwise all flashtools get
        colored red in the dropdown if you have no chip selected).
        """
        if (self.get_name().lower() == "custom") or (
            self.get_name().lower() == "none"
        ):
            return True
        if (
            (uid is None)
            or (uid.lower() == "none")
            or (uid.lower() == "custom")
        ):
            return False
        assert isinstance(uid, str)
        if uid.lower().replace("-", "_") == "built_in":
            return True
        patterns = self.__chip_unicum.get_chip_dict(board=None).get(
            "flashtool_patterns"
        )
        if patterns is None:
            _hardware_api_.HardwareDB().reset()
            return self.is_compatible_with_flashtool(uid)
        for p in patterns:
            if _fn_.fnmatch(name=uid, pat=p):
                return True
        return False

    def is_compatible_with_compiler_uid(self, uid: str) -> bool:
        """Check if this particular chip is compatible with the given compiler
        unique_id.

        Let the custom-chip always be compatible (otherwise all compilers get
        colored red in the dropdown if you have no chip selected).
        """
        if self.get_name().lower() == "custom":
            return True
        if (
            (uid is None)
            or (uid.lower() == "none")
            or (uid.lower() == "custom")
        ):
            return False
        assert isinstance(uid, str)
        patterns = self.__chip_unicum.get_chip_dict(board=None)[
            "compiler_patterns"
        ]
        if patterns is None:
            _hardware_api_.HardwareDB().reset()
            return self.is_compatible_with_compiler_uid(uid)
        for p in patterns:
            if _fn_.fnmatch(name=uid, pat=p):
                return True
        return False

    def change_chip(
        self,
        chip_unicum: _chip_unicum_.CHIP,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Change chip and trigger a dashboard refresh.

        Also the corresponding ToolpathSeg() gets re- freshed. Works for both
        the Dashboard and Intro Wizard.
        """
        is_fake = self.is_fake()
        toolpath_seg: Optional[_toolpath_seg_.ToolpathSeg] = None
        if is_fake:
            toolpath_seg = (
                data.current_project.intro_wiz.get_fake_toolpath_seg()
            )
        else:
            toolpath_seg = data.current_project.get_toolpath_seg()

        def refresh_self(*args) -> None:
            self.trigger_dashboard_refresh(
                callback=refresh_toolpath,
                callbackArg=None,
            )
            return

        def refresh_toolpath(*args) -> None:
            toolpath_seg.trigger_dashboard_refresh(
                callback=notify_engine_feeder,
                callbackArg=None,
            )
            return

        def notify_engine_feeder(*args) -> None:
            "[dashboard only]"
            if is_fake:
                finish()
                return
            # Notify the Source Analyzer about the new chip. That's important for the heuristics!
            print("TODO: Warn the Source Analyzer about the new chip!!")
            finish()
            return

        def finish(*args) -> None:
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        assert isinstance(chip_unicum, _chip_unicum_.CHIP)
        if self.__chip_unicum == chip_unicum:
            finish()
            return
        if not is_fake:
            self.get_history().push()
        self.__chip_unicum = chip_unicum
        if not is_fake:
            self.get_history().compare_to_baseline(
                refresh=False,
                callback=refresh_self,
                callbackArg=None,
            )
            return
        refresh_self()
        return

    def repair_memregion_list(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """
        Repair the memregion list:
        ==========================
        This function replaces the underlying MemRegion()-objects completely and consequently their
        underlying MemSection()-objects as well, but it keeps the corresponding Dashboard()-items
        intact. They simply are rebound to the new MemRegion()-objects.
        Upon the next dashboard synchronization, they adapt immediately to the new MemRegion()s they
        are bound to.

        Alternatives:
        =============
        - Replace the MemRegion()-objects and their corresponding dashboard-items alltogether. This
          works, but causes flickering.
        - Do not replace anything, but attempt to adapt the existing MemRegion()-objects. That's a
          tedious task, because each MemRegion()-object owns several MemSection()-objects. The
          ownership is labelled with a 's' for 'storage' or 'r' for 'runtime' or 'sr' for both. In
          turn, the MemSection()-objects have backreferences to their MemSection()'s, distinguishing
          between the one for storage and the one for runtime. Fixing this datastructure can easily
          go wrong.
        """
        assert not self.is_fake()

        if not self.__trigger_memory_repair_mutex.acquire(blocking=False):
            self.__memory_repair_reentered = True
            qt.QTimer.singleShot(
                300,
                functools.partial(
                    self.repair_memregion_list,
                    callback,
                    callbackArg,
                ),
            )
            return
        self.__memory_repair_reentered = False

        new_memregion_list = self.__get_new_memregion_list()
        for memregion in new_memregion_list:
            memregion.calc_usage()

        def fix_next_memregion(i: int) -> None:
            if self.__memory_repair_reentered:
                # No need to continue. Everything will be redone anyway.
                finish()
                return
            # Go over the existing memregions in this Chip()-instance, in index-order.
            # $ Replace memregion
            # Replace each memregion by the same-indexed memregion from the new list, but keep the
            # _v_memItem intact. Bind that existing _v_memItem to the new memregion. It will auto-
            # matically adapt all visible stuff upon the next sync().
            if (i < len(self.__memregion_list)) and (
                i < len(new_memregion_list)
            ):
                _memregion1 = self.__memregion_list[i]
                _memregion2 = new_memregion_list[i]
                self.replace_memregion(
                    i=i,
                    memregion1=_memregion1,
                    memregion2=_memregion2,
                    callback=fix_next_memregion,
                    callbackArg=i + 1,
                )
                return
            # $ Add memregion
            # If the end of the Chip()'s memregions list is met first, just add the new memregions
            # and create a new _v_memItem for each.
            if (i >= len(self.__memregion_list)) and (
                i < len(new_memregion_list)
            ):
                _memregion2 = new_memregion_list[i]
                self.add_memregion(
                    memregion=_memregion2,
                    callback=fix_next_memregion,
                    callbackArg=i + 1,
                )
                return
            # $ Delete memregion
            # If the end of the new memregions list is met first, delete all higher indexed mem-
            # regions (including their _v_memItem) from this Chip().
            if (i < len(self.__memregion_list)) and (
                i >= len(new_memregion_list)
            ):
                _memregion1 = self.__memregion_list[i]
                self.remove_memregion(
                    memregion=_memregion1,
                    callback=fix_next_memregion,
                    callbackArg=i,  # don't increment !
                )
                return
            # $ Finish
            if (i >= len(self.__memregion_list)) and (
                i >= len(new_memregion_list)
            ):
                for _memregion in self.__memregion_list:
                    _memregion.check()
                self.trigger_dashboard_refresh(
                    callback=finish,
                    callbackArg=None,
                )
                return
            assert False

        def finish(*args) -> None:
            self.__trigger_memory_repair_mutex.release()
            if callback is not None:
                callback(callbackArg)
            return

        fix_next_memregion(0)
        return

    def __get_new_memregion_list(self) -> List[MemRegion]:
        """Return a new list of MemRegion()-objects based on the raw data from
        the SA.

        These objects contain MemSection()s inside. No visible _v_memItem's are
        bound yet.
        """
        memregion_list = []

        # $ 1. Loop over memory regions
        for memreg_name in self.__memory_regions_raw_data.keys():
            memreg_type = (
                _chip_unicum_.MEMTYPE.RAM
                if "RAM" in memreg_name
                else _chip_unicum_.MEMTYPE.FLASH
            )
            memreg_rights = self.__memory_regions_raw_data[memreg_name][
                "access_rights"
            ]
            memreg_orig = self.__memory_regions_raw_data[memreg_name]["origin"]
            memreg_len = self.__memory_regions_raw_data[memreg_name]["size"]
            memregion_list.append(
                MemRegion(
                    name=memreg_name,
                    memtype=memreg_type,
                    rights=memreg_rights,
                    origin=memreg_orig,
                    length=memreg_len,
                    usage=0,
                ),
            )

        # $ 2. Loop over memory sections
        for memsec_name in self.__memory_sections_raw_data.keys():
            assigned = ""
            memsection = MemSection(
                name=memsec_name,
                usage=0,
            )  # Every MemSection() is created only once!!

            # Add MemSection()-instance to MemRegion()-instance(s)
            if (
                self.__memory_sections_raw_data[memsec_name]["load_region"]
                is None
            ) or (
                self.__memory_sections_raw_data[memsec_name]["runtime_region"]
                == self.__memory_sections_raw_data[memsec_name]["load_region"]
            ):
                for memregion in memregion_list:
                    if (
                        memregion.get_name()
                        == self.__memory_sections_raw_data[memsec_name][
                            "runtime_region"
                        ]
                    ):
                        assert assigned == ""
                        memregion.add_memsection(
                            memsection=memsection,
                            form="sr",
                        )
                        assigned += "sr"
            else:
                for memregion in memregion_list:
                    if (
                        memregion.get_name()
                        == self.__memory_sections_raw_data[memsec_name][
                            "runtime_region"
                        ]
                    ):
                        assert "r" not in assigned
                        memregion.add_memsection(
                            memsection=memsection,
                            form="r",
                        )
                        assigned += "r"
                    if (
                        memregion.get_name()
                        == self.__memory_sections_raw_data[memsec_name][
                            "load_region"
                        ]
                    ):
                        assert "s" not in assigned
                        memregion.add_memsection(
                            memsection=memsection,
                            form="s",
                        )
                        assigned += "s"
            if not ("r" in assigned) and ("s" in assigned):
                purefunctions.printc(
                    f"WARNING: 'assigned' var is '{assigned}'",
                    color="warning",
                )

        # $ 3. Check
        for memregion in memregion_list:
            memregion.check()
        return memregion_list

    def add_memregion(
        self,
        memregion: MemRegion,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        Add the given MemRegion()-instance to this Chip()-object, and create a new _v_memItem -
        instance from ChipMemoryItem() - for its representation in the dashboard.
        """
        assert not self.is_fake()
        assert isinstance(memregion, MemRegion)
        assert memregion not in self.__memregion_list
        self.__memregion_list.append(memregion)
        if self._v_rootItem is not None:
            _v_memItem = _da_chip_items_.ChipMemoryItem(
                memregion=memregion,
                rootdir=self._v_rootItem,
                parent=self._v_rootItem,
            )
            memregion.set_v_memItem(_v_memItem)
            self._v_rootItem.add_child(
                _v_memItem,
                alpha_order=False,
                show=True,
                callback=callback,
                callbackArg=callbackArg,
            )
            return
        if callback is not None:
            callback(callbackArg)
        return

    def remove_memregion(
        self,
        memregion: MemRegion,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        Remove the given MemRegion()-instance from this Chip()-object, and destroy the corresponding
        _v_memItem - instance from ChipMemoryItem() - in the dashboard.
        """
        assert not self.is_fake()
        assert isinstance(memregion, MemRegion)
        assert memregion in self.__memregion_list
        self.__memregion_list.remove(memregion)
        if self._v_rootItem is not None:
            for _v_memItem in self.get_v_memregion_list():
                assert isinstance(
                    _v_memItem, _da_chip_items_.ChipMemoryItem
                ), f"_v_memItem is {_v_memItem}"
                if _v_memItem.get_projSegment() is memregion:
                    _v_memItem.self_destruct(
                        killParentLink=True,
                        callback=callback,
                        callbackArg=callbackArg,
                    )
                    return
            assert False
        if callback is not None:
            callback(callbackArg)
        return

    def replace_memregion(
        self,
        i: int,
        memregion1: MemRegion,
        memregion2: MemRegion,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        Remove 'memregion1' - must be at index i in self.__memregionList - and replace it by
        'memregion2'. While removing 'memregion1', do not kill its _v_memItem in the dashboard.
        Instead, bind it to the replacing 'memregion2'.

        Upon the next dashboard synchronization, this _v_memItem will automatically adapt to the
        data in 'memregion2'.
        """
        assert not self.is_fake()

        # & 1. Replace 'memregion1' by 'memregion2' in the self.__memregionList.
        assert isinstance(memregion1, MemRegion)
        assert memregion1 in self.__memregion_list
        assert memregion2 not in self.__memregion_list
        j = self.__memregion_list.index(memregion1)
        assert i == j
        self.__memregion_list.remove(memregion1)
        self.__memregion_list.insert(i, memregion2)

        # & 2. Attach the '_v_memItem1' from 'memregion1' to 'memregion2'
        if self._v_rootItem is None:
            callback(callbackArg) if callback is not None else nop()
            return
        _v_memItem1 = memregion1.get_v_memItem()
        if _v_memItem1 is not None:
            memregion2.set_v_memItem(_v_memItem1)
            _v_memItem1.set_projSegment(projSegment=memregion2)
            callback(callbackArg) if callback is not None else nop()
            return
        _v_memItem2 = _da_chip_items_.ChipMemoryItem(
            memregion=memregion2,
            rootdir=self._v_rootItem,
            parent=self._v_rootItem,
        )
        memregion2.set_v_memItem(_v_memItem2)
        self._v_rootItem.add_child(
            _v_memItem2,
            alpha_order=False,
            show=True,
            callback=callback,
            callbackArg=callbackArg,
        )
        return

    def printout(self, nr: int, *args, **kwargs) -> str:
        """"""
        assert not self.is_fake()
        super().printout(nr)
        lines = [
            f"# {nr}. Chip ",
            f"chip_name = {q}{self.get_name()}{q}",
            f"",
        ]
        return "\n".join(lines)

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """Kill this Chip()-instance and *all* its representations in the
        Dashboard or Intro Wizard."""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError("Trying to kill Chip() twice!")
            self.dead = True

        def start(*args) -> None:
            # $ Dashboard
            if not self.is_fake():
                if self._v_rootItem:
                    self._v_rootItem.self_destruct(
                        killParentLink=False,
                        callback=finish,
                        callbackArg=None,
                    )
                    return
                finish()
                return
            # $ Intro Wizard
            if self._v_deviceItem:
                self._v_deviceItem.self_destruct(
                    killParentLink=False,
                    callback=finish,
                    callbackArg=None,
                )
                return
            finish()
            return

        def finish(*args) -> None:
            self._v_rootItem = None
            self._v_deviceItem = None
            if callback is not None:
                callback(callbackArg)
            return

        super().self_destruct(
            callback=start,
            callbackArg=None,
            death_already_checked=True,
        )
        return
