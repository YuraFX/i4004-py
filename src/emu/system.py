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

from emu.core.cpu import CPU
from emu.pins import CPUPins, CM_RAM0, CM_RAM1, CM_RAM2, CM_RAM3
from emu.memory.ram import RAM
from emu.memory.rom import ROM
from emu.video.display import Display
from emu.video.sr4003 import ShiftRegister4003
from emu.video.tia import TIA16x16
from emu.video.teletype import Teletype
from emu.storage.shugart import ShugartSA800
from emu.io.uart_ay import AY51013UART


class System:
    def __init__(self, rom_dump, ram_dump=None, ram_output_handler=None):
        self.terminated = False
        self.instruction_cycles = 0

        self.pins = CPUPins()

        # Initialize peripherals
        self.rom = ROM(self.pins)
        self.ram = RAM(self.pins, ram_dump, ram_output_handler)
        self.display = Display()
        self.sr4003 = ShiftRegister4003()
        self.tia = TIA16x16()
        
        # Disable parity and timing delays for fast operation
        self.teletype = Teletype(enable_parity=False, emulate_timing=False, stop_bits=1)
        
        # Create a Shugart SA 800-1 disk drive instance
        self.disk_controller = ShugartSA800()

        # Create a virtual UART instance and bind it to the Teletype
        self.uart = AY51013UART(self.teletype)

        # Create the CPU and bind it to all peripherals
        self.cpu = CPU(self.pins)
        self.cpu.rom = self.rom
        self.cpu.ram = self.ram
        self.cpu.display = self.display
        self.cpu.sr4003 = self.sr4003
        self.cpu.tia = self.tia
        self.cpu.teletype = self.teletype
        self.cpu.disk_controller = self.disk_controller
        self.cpu.uart = self.uart  # <--- Pass UART to CPU
        
        self.cpu.display_mode = '4003'

        self.rom.load_dump(rom_dump)

    def instruction(self):
        if self.is_finished():
            return
        self.cpu.step()
        # Spin the UART several times per one CPU step,
        # so it can process its timings while the CPU is spinning in a wait loop
        for _ in range(10): 
            self.uart.tick()
        self.instruction_cycles += 1

    def is_finished(self):
        return (
            self.terminated or
            not self.rom.is_address_valid(self.cpu.pc) or
            self.cpu.halted
        )

    def terminate(self):
        self.terminated = True

    @property
    def registers(self):
        return self.cpu

    @property
    def memory(self):
        return self.ram.banks

    @property
    def selected_ram_bank(self):
        cm_ram = self.pins.get_pins_data([CM_RAM0, CM_RAM1, CM_RAM2, CM_RAM3])
        return self.ram.get_bank_no_from_pins_data(cm_ram) if cm_ram else 0