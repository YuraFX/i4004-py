# Copyright (C) 2026 Yuriy Konyshev
#
# This file is part of i4004-py.
#
# i4004-py is free software: you can redistribute it and/or modify it under the terms of the GNU General 
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your 
# option) any later version.
#
# i4004-py is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even 
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with i4004-py. If not, see 
# <https://www.gnu.org/licenses/>.

class Linker:
    def __init__(self, base_address=0x0000, map_file=False):
        self.base_address = base_address
        self.map_file_enabled = map_file
        
        self.total_code = bytearray()
        self.global_symbols = {}       # Global symbols (PUBLIC)
        self.external_symbols = {}     # External references (EXTRN)
        self.module_data = []          # Module placement data
        self.occupied_ranges = []      # Occupied memory ranges
        self.map_entries = []          # Map entries for output

    def link(self, object_modules):
        self._pass1(object_modules)
        self._pass2(object_modules)
        
        if self.external_symbols:
            missing = ', '.join(self.external_symbols.keys())
            raise ValueError(f"LINK-80 Error: Unresolved external symbols: {missing}")
            
        if self.map_file_enabled:
            self._print_map()
            
        return self.total_code

    def _pass1(self, object_modules):
        """Pass 1: Place modules and collect global symbols (analogous to LNAMES, SEGDEF, PUBDEF)."""
        current_address = self.base_address

        # 1. Place modules with overlap checking
        for mod in object_modules:
            base = current_address
            size = len(mod['code'])
            
            # Check for address overlap (LINK-80 style)
            for (start, end) in self.occupied_ranges:
                if not (base + size <= start or base >= end):
                    raise ValueError(f"LINK-80 Error: Address overlap for module '{mod.get('name', '?')}' at 0x{base:04X}")
            
            self.occupied_ranges.append((base, base + size))
            self.module_data.append({
                'name': mod.get('name', '?'),
                'base': base,
                'size': size
            })
            
            self.total_code.extend(mod['code'])
            current_address += size

        # 2. Collect global symbols and external references (analogous to EXTDEF and PUBDEF)
        for idx, mod in enumerate(object_modules):
            base = self.module_data[idx]['base']
            
            # Register the module's public symbols
            for name, offset in mod.get('symbols', {}).items():
                absolute_addr = base + offset
                if name in self.global_symbols:
                    # In LINK-80, duplicate PUBLIC symbols cause an error
                    raise ValueError(f"LINK-80 Error: Duplicate public symbol '{name}'")
                self.global_symbols[name] = absolute_addr
                self.map_entries.append((mod.get('name', '?'), name, absolute_addr, 'PUBLIC'))
            
            # Register the module's external references
            for reloc_offset, label_name, fmt in mod.get('relocations', []):
                if label_name not in self.external_symbols:
                    self.external_symbols[label_name] = []
                self.external_symbols[label_name].append((base + reloc_offset, fmt))

        # 3. External Reference Resolution
        # If a referenced symbol exists in the global table, it is resolved.
        # Otherwise it remains in external_symbols and will trigger an error.
        for name in list(self.external_symbols.keys()):
            if name in self.global_symbols:
                del self.external_symbols[name]

    def _pass2(self, object_modules):
        """Pass 2: Patch relocations (analogous to FIXUPP)."""
        for idx, mod in enumerate(object_modules):
            base = self.module_data[idx]['base']
            
            for reloc_offset, label_name, fmt in mod.get('relocations', []):
                if label_name in self.global_symbols:
                    absolute_addr = self.global_symbols[label_name]
                    self._patch_relocation(base + reloc_offset, absolute_addr, fmt)
                else:
                    # Symbol not found, leave it for error reporting
                    pass

    def _patch_relocation(self, address, value, fmt):
        """Write the address into the code according to the relocation format (Intel 4004)."""
        if fmt == 'A12':
            # For the 4004: the high nibble (12-bit) is written into the low half-byte of the previous byte (opcode)
            # The low byte is written into the current byte
            if value > 0xFFF:
                raise ValueError(f"LINK-80 Error: Address 0x{value:X} exceeds 12-bit limit for 4004")
            
            self.total_code[address - 1] = (self.total_code[address - 1] & 0xF0) | ((value >> 8) & 0x0F)
            self.total_code[address] = value & 0xFF
            
        elif fmt in ('ISZ', 'COND'):
            self.total_code[address] = value & 0xFF
            
        else:
            raise ValueError(f"LINK-80 Error: Unknown relocation format: {fmt}")

    def _print_map(self):
        """Print the memory map (analogous to /MAP in LINK-80)."""
        print("=== LINK-80 MAP FILE ===")
        print("Module       | Symbol         | Address | Type")
        print("-" * 50)
        for entry in self.map_entries:
            mod_name, sym_name, addr, sym_type = entry
            print(f"{mod_name:<12} | {sym_name:<14} | 0x{addr:04X}  | {sym_type}")
        print("-" * 50)
        print(f"Total code size: {len(self.total_code)} bytes")
        print(f"Start address: 0x{self.base_address:04X}")