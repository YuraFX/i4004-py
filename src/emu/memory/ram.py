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

from emu.pins import SYNC, CM_RAM0, CM_RAM1, CM_RAM2, CM_RAM3, D0, D1, D2, D3


class RAM:
    def __init__(self, pins, ram_dump=None, output_handler=None):
        self.pins = pins
        self.output_handler = output_handler
        
        # Build the memory structure (8 banks of 16 registers each)
        if ram_dump:
            self.banks = self._construct_ram_banks(ram_dump)
        else:
            self.banks = self._get_empty_ram()
            
        self.state = 0
        self.bank_for_execution = None
        self.bank_to_set_offset = None
        self.opa = 0

    @staticmethod
    def _construct_ram_banks(dump):
        # Convert a memory dump into the working structure
        banks = []
        for registers in dump:
            bank = {
                'registers': registers,
                'outputs': [0] * 8,  # <--- FIXED: was [0, 0, 0, 0]
                'selected_register': 0,
                'selected_character': 0
            }
            banks.append(bank)
        return banks

    @staticmethod
    def _get_empty_ram():
        # Initialize 8 empty RAM banks
        banks = []
        for _ in range(8):
            registers = []
            for _ in range(16):
                registers.append({
                    'main': [0] * 16,
                    'status': [0] * 4
                })
            bank = {
                'registers': registers,
                'outputs': [0] * 8,  # <--- FIXED: was [0, 0, 0, 0]
                'selected_register': 0,
                'selected_character': 0
            }
            banks.append(bank)
        return banks

    @staticmethod
    def get_bank_no_from_pins_data(pins_data):
        # Determine the bank number from the CM-RAM line combination
        if (pins_data & 0x1) == 0x1:
            return 0
            
        pins_data >>= 1
        bank_mapping = {
            0b001: 1,
            0b010: 2,
            0b100: 3,
            0b011: 4,
            0b101: 5,
            0b110: 6,
            0b111: 7
        }
        if pins_data in bank_mapping:
            return bank_mapping[pins_data]
        else:
            raise ValueError('Unknown value for CMRAM!')

    def _selected_bank(self):
        # Get the currently selected bank based on the pin state
        cm_ram = self.pins.get_pins_data([CM_RAM0, CM_RAM1, CM_RAM2, CM_RAM3])
        if cm_ram:
            return self.banks[self.get_bank_no_from_pins_data(cm_ram)]
        return None

    def _execute(self, bank, opa, data):
        # Execute a RAM instruction
        reg = bank['selected_register']
        char = bank['selected_character']
        
        if opa == 0x9:    # RDM (Read RAM character)
            self.pins.set_pins_data([D0, D1, D2, D3], bank['registers'][reg]['main'][char])
        elif opa == 0xC:  # RD0 (Read RAM status character 0)
            self.pins.set_pins_data([D0, D1, D2, D3], bank['registers'][reg]['status'][0])
        elif opa == 0xD:  # RD1
            self.pins.set_pins_data([D0, D1, D2, D3], bank['registers'][reg]['status'][1])
        elif opa == 0xE:  # RD2
            self.pins.set_pins_data([D0, D1, D2, D3], bank['registers'][reg]['status'][2])
        elif opa == 0xF:  # RD3
            self.pins.set_pins_data([D0, D1, D2, D3], bank['registers'][reg]['status'][3])
            
        elif opa == 0x0:  # WRM (Write accumulator into RAM character)
            bank['registers'][reg]['main'][char] = data
        elif opa == 0x1:  # WMP (Write RAM port)
            chip_index = reg >> 2
            if self.output_handler:
                self.output_handler({'chip': chip_index, 'data': data})
            bank['outputs'][chip_index] = data
        elif opa == 0x4:  # WR0
            bank['registers'][reg]['status'][0] = data
        elif opa == 0x5:  # WR1
            bank['registers'][reg]['status'][1] = data
        elif opa == 0x6:  # WR2
            bank['registers'][reg]['status'][2] = data
        elif opa == 0x7:  # WR3
            bank['registers'][reg]['status'][3] = data
            
        elif opa == 0xB:  # ADM (Add from memory with carry)
            self.pins.set_pins_data([D0, D1, D2, D3], bank['registers'][reg]['main'][char])
        elif opa == 0x8:  # SBM (Subtract from memory with borrow)
            self.pins.set_pins_data([D0, D1, D2, D3], bank['registers'][reg]['main'][char])

    def tick(self):
        # Main RAM clock cycle, synchronized with SYNC
        if self.pins.get_pin(SYNC) or self.state == 7:
            # Handle the SRC command (store the character index)
            if self.bank_to_set_offset:
                self.bank_to_set_offset['selected_character'] = self.pins.get_pins_data([D0, D1, D2, D3])
                self.bank_to_set_offset = None
            self.state = 0
            return

        if self.state == 0:    # A1
            pass
        elif self.state == 1:  # A2
            pass
        elif self.state == 2:  # A3
            pass
        elif self.state == 3:  # M1
            pass
        elif self.state == 4:  # M2
            self.bank_for_execution = self._selected_bank()
            if self.bank_for_execution:
                self.opa = self.pins.get_pins_data([D0, D1, D2, D3])
        elif self.state == 5:  # X1
            pass
        elif self.state == 6:  # X2
            data = self.pins.get_pins_data([D0, D1, D2, D3])
            
            # Handle the SRC command (store the register and chip index)
            self.bank_to_set_offset = self._selected_bank()
            if self.bank_to_set_offset:
                self.bank_to_set_offset['selected_register'] = data
                
            # Execute the operation captured during the M2 stage
            if self.bank_for_execution:
                self._execute(self.bank_for_execution, self.opa, data)
                self.bank_for_execution = None

        self.state += 1