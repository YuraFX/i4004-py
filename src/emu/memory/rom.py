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

from emu.pins import SYNC, D0, D1, D2, D3, CM_ROM1


class ROM:
    def __init__(self, pins):
        self.pins = pins
        self.state = 0
        self.address = 0
        
        # Two memory banks (empty by default)
        self.banks = [bytearray(0), bytearray(0)]
        self.selected_bank = 0

    def is_address_valid(self, address):
        # Check whether the address is within the current bank
        return 0 <= address < len(self.banks[self.selected_bank])

    def load_dump(self, banks):
        # Load a memory dump (list of byte arrays)
        self.banks = banks

    # =================================================================
    # METHOD FOR READING DATA FROM ROM (CALLED FROM CPU)
    # =================================================================
    def read(self, address):
        if self.is_address_valid(address):
            return self.banks[self.selected_bank][address]
        return 0

    def tick(self):
        # Main ROM clock cycle, synchronized with SYNC
        if self.pins.get_pin(SYNC):
            self.state = 0
            return

        if self.state == 0:    # A1
            # Low nibble of the address
            self.address = self.pins.get_pins_data([D0, D1, D2, D3])
            
        elif self.state == 1:  # A2
            # Middle nibble of the address
            self.address |= (self.pins.get_pins_data([D0, D1, D2, D3]) << 4)
            
        elif self.state == 2:  # A3
            # High nibble of the address and bank selection
            self.address |= (self.pins.get_pins_data([D0, D1, D2, D3]) << 8)
            self.selected_bank = 1 if self.pins.get_pin(CM_ROM1) == 1 else 0
            
            if not self.is_address_valid(self.address):
                raise ValueError(f"Address {self.address} is not valid")
                
            # Output the high nibble of the instruction onto the data bus
            data = self.banks[self.selected_bank][self.address]
            self.pins.set_pins_data([D0, D1, D2, D3], data >> 4)
            
        elif self.state == 3:  # M1
            # Output the low nibble of the instruction onto the data bus
            data = self.banks[self.selected_bank][self.address]
            self.pins.set_pins_data([D0, D1, D2, D3], data & 0xF)
            
        elif self.state == 4:  # M2
            # Wait for the next cycle
            pass

        self.state += 1