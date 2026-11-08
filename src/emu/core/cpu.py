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

class CPU:
    def __init__(self, pins, ram=None, rom=None):
        self.pins = pins
        self.ram = ram
        self.rom = rom
        self.display = None  
        self.sr4003 = None
        self.tia = None
        self.teletype = None
        self.disk_controller = None
        self.uart = None  
        
        self.display_mode = '4003'
        self.keyboard_buffer = 0

        self.acc = 0
        self.carry = 0
        self.pc = 0

        self.index_banks = [
            [0] * 16,
            [0] * 16
        ]
        self.selected_register_bank = 0

        self.stack = [0, 0, 0]
        self.sp = 0

        self.selected_rom_bank = 0
        self.ram_control = 0b0001
        self.halted = False

    # =================================================================
    # HELPER METHODS
    # =================================================================

    def _add(self, value, ignore_carry=False):
        result = self.acc + value + (0 if ignore_carry else self.carry)
        self.acc = result & 0xF
        self.carry = 1 if result > 0xF else 0

    def _sub(self, value, ignore_carry=False):
        self.carry = 1 if ignore_carry else ((~self.carry) & 0x1)
        self._add((~value) & 0xF)

    def _push(self, address):
        self.stack[self.sp] = address
        self.sp = (self.sp + 1) % 3

    def _pop(self):
        self.sp = (self.sp - 1 + 3) % 3
        return self.stack[self.sp]

    def _read_reg(self, reg_no):
        return self.index_banks[self.selected_register_bank][reg_no]

    def _write_reg(self, reg_no, value):
        if reg_no < 8:
            self.index_banks[self.selected_register_bank][reg_no] = value & 0xF
        else:
            for bank in self.index_banks:
                bank[reg_no] = value & 0xF

    def _get_full_address(self, page_byte):
        ph = (self.pc & 0xF00) + (0x100 if (self.pc & 0xFF) == 0xFF else 0)
        return ph | (page_byte & 0xFF)

    def _fetch_next_byte(self):
        if self.rom:
            return self.rom.read(self.pc + 1)
        return 0

    # =================================================================
    # INSTRUCTIONS
    # =================================================================

    def NOP(self): pass
    def HLT(self): self.halted = True
    def LDM(self, data): self.acc = data & 0xF
    def LD(self, reg): self.acc = self._read_reg(reg)

    def XCH(self, reg):
        temp = self.acc
        self.acc = self._read_reg(reg)
        self._write_reg(reg, temp)

    def ADD(self, reg): self._add(self._read_reg(reg))
    def SUB(self, reg): self._sub(self._read_reg(reg))
    def INC(self, reg): self._write_reg(reg, (self._read_reg(reg) + 1) & 0xF)

    def ISZ(self, reg, page_byte):
        val = (self._read_reg(reg) + 1) & 0xF
        self._write_reg(reg, val)
        if val == 0:
            self.pc += 3
        else:
            self.pc = self._get_full_address(page_byte)

    def JUN(self, high_nibble, low_byte):
        self.pc = (high_nibble << 8) | low_byte

    def JMS(self, high_nibble, low_byte):
        target = (high_nibble << 8) | low_byte
        self._push(self.pc + 2)
        self.pc = target

    def JCN(self, condition, page_byte):
        invert = (condition & 0x8) == 0x8
        acc_zero = (condition & 0x4) == 0x4
        cf_set = (condition & 0x2) == 0x2

        cond = (acc_zero and self.acc == 0) or (cf_set and self.carry == 1)
        final_cond = not cond if invert else cond

        if final_cond:
            self.pc = self._get_full_address(page_byte)
        else:
            self.pc += 2

    def BBL(self, data):
        return_addr = self._pop()
        self.acc = data & 0xF
        self.pc = return_addr

    def FIM(self, reg_pair, data):
        self._write_reg(reg_pair, (data >> 4) & 0xF)
        self._write_reg(reg_pair + 1, data & 0xF)
        self.pc += 2

    def JIN(self, reg_pair):
        addr = (self._read_reg(reg_pair) << 4) | self._read_reg(reg_pair + 1)
        self.pc = addr

    def FIN(self, reg_pair):
        addr = (self._read_reg(reg_pair) << 4) | self._read_reg(reg_pair + 1)
        data = self.rom.read(addr) if self.rom else 0
        self._write_reg(0, (data >> 4) & 0xF)
        self._write_reg(1, data & 0xF)

    def SRC(self, reg_pair):
        high = self._read_reg(reg_pair)
        low = self._read_reg(reg_pair + 1)
        self.pins.set_ram_address(high, low)
        
        if self.ram:
            bank = self.ram.banks[0]
            bank['selected_register'] = high & 0xF
            bank['selected_character'] = low & 0xF

    # =================================================================
    # I/O AND CONTROL INSTRUCTIONS
    # =================================================================

    def _get_ram_target(self):
        if not self.ram:
            return None, None, None
        bank = self.ram.banks[0]
        reg = bank['selected_register']
        char = bank['selected_character']
        return bank, reg, char

    def WRM(self):
        bank, reg, char = self._get_ram_target()
        if bank:
            bank['registers'][reg]['main'][char] = self.acc
        else:
            self.pins.write_ram(self.acc)

    def WMP(self):
        bank, reg, char = self._get_ram_target()
        if bank:
            chip = reg >> 2
            
            # --- UART LOGIC (AY-5-1013) on Chip 3 ---
            if getattr(self, 'uart', None):
                if chip == 3:
                    if reg == 12:
                        self.uart.write_data(self.acc)
                        return
                    elif reg == 13:
                        return # Status is read-only
                    elif reg == 14:
                        self.uart.write_control(self.acc)
                        return

            # Store the value in the port array if the index is within bounds
            if reg < len(bank['outputs']):
                bank['outputs'][reg] = self.acc
                
            if self.ram.output_handler:
                self.ram.output_handler({'chip': chip, 'data': self.acc})

            # --- DISK DRIVE LOGIC ---
            if getattr(self, 'disk_controller', None):
                if reg == 4: # Disk drive commands
                    cmd = self.acc
                    if cmd == 0x1:   self.disk_controller.step()
                    elif cmd == 0x2: self.disk_controller.set_direction(True)
                    elif cmd == 0x3: self.disk_controller.set_direction(False)
                    elif cmd == 0x4: self.disk_controller.select(True)
                    elif cmd == 0x5: self.disk_controller.select(False)
                    elif cmd == 0x6: self.disk_controller.set_write_gate(True)
                    elif cmd == 0x7: self.disk_controller.set_write_gate(False)
                    elif cmd == 0x8: 
                        sector_num = getattr(self.disk_controller, 'target_sector', 0)
                        data = self.disk_controller.read_sector(sector_num)
                        if data:
                            self.disk_controller.read_buffer = data
                            self.disk_controller.read_index = 0
                    elif cmd == 0x9:
                        self.disk_controller.write_buffer = []
                elif reg == 5: # Disk drive data
                    if self.disk_controller.write_gate:
                        if not hasattr(self.disk_controller, 'write_buffer'):
                            self.disk_controller.write_buffer = []
                        if not hasattr(self.disk_controller, 'current_nibble'):
                            self.disk_controller.current_nibble = None

                        if self.disk_controller.current_nibble is None:
                            self.disk_controller.current_nibble = self.acc
                        else:
                            byte_val = self.disk_controller.current_nibble | (self.acc << 4)
                            self.disk_controller.write_buffer.append(byte_val)
                            self.disk_controller.current_nibble = None

                            if len(self.disk_controller.write_buffer) == 128:
                                sector_num = getattr(self.disk_controller, 'target_sector', 0)
                                self.disk_controller.write_sector(sector_num, self.disk_controller.write_buffer)
                                self.disk_controller.write_buffer = []
                    else:
                        self.disk_controller.target_sector = self.acc
                        self.disk_controller.data_register = self.acc

            # --- VIDEO LOGIC (Teletype / TIA / 4003) ---
            mode = getattr(self, 'display_mode', '4003')
            
            if mode == 'TIA' and getattr(self, 'tia', None):
                if self.tia.write_register(reg, self.acc):
                    self.tia.render(self.display)
                    
            elif mode == 'Teletype' and getattr(self, 'teletype', None):
                import time
                if chip == 0:
                    bit = self.acc & 0x1
                    self.teletype.receive_bit(bit, int(time.perf_counter() * 1_000_000))
                    
            else:
                if chip in [0, 1] and getattr(self, 'sr4003', None):
                    for i in range(4):
                        bit = (self.acc >> i) & 0x1
                        self.sr4003.set_data(bit)
                        self.sr4003.clock_pulse()

                if chip == 2 and getattr(self, 'display', None):
                    x = bank['outputs'][0]
                    y = bank['outputs'][1]
                    self.display.set_pixel(x, y, self.acc)

        else:
            self.pins.write_ram_port(self.acc)

    def RDM(self):
        bank, reg, char = self._get_ram_target()
        if bank:
            chip = reg >> 2
            
            # --- UART LOGIC (AY-5-1013) on Chip 3 ---
            if getattr(self, 'uart', None):
                if chip == 3:
                    if reg == 12:
                        self.acc = self.uart.read_data()
                        return
                    elif reg == 13:
                        self.acc = self.uart.read_status()
                        return

            # --- DISK DRIVE LOGIC (priority) ---
            if getattr(self, 'disk_controller', None):
                if reg == 4:
                    status = 0
                    if self.disk_controller.track00: status |= 0x1
                    if self.disk_controller.ready: status |= 0x2
                    self.acc = status
                    return
                elif reg == 5:
                    if hasattr(self.disk_controller, 'read_buffer') and self.disk_controller.read_index < len(self.disk_controller.read_buffer):
                        if not hasattr(self.disk_controller, 'read_nibble_state'):
                            self.disk_controller.read_nibble_state = 0
                            
                        current_byte = self.disk_controller.read_buffer[self.disk_controller.read_index]
                        
                        if self.disk_controller.read_nibble_state == 0:
                            self.acc = current_byte & 0xF
                            self.disk_controller.read_nibble_state = 1
                        else:
                            self.acc = (current_byte >> 4) & 0xF
                            self.disk_controller.read_nibble_state = 0
                            self.disk_controller.read_index += 1
                    else:
                        self.acc = 0
                    return
                    
            # --- KEYBOARD LOGIC ---
            if chip == 3:
                if not hasattr(self, 'kbd_nibble_state'):
                    self.kbd_nibble_state = 0
                
                if bank['outputs'][3] == 0:
                    self.kbd_nibble_state = 0
                    self.acc = 0
                    return

                full_char = bank['outputs'][3]
                if self.kbd_nibble_state == 0:
                    self.acc = full_char & 0xF
                    self.kbd_nibble_state = 1
                else:
                    self.acc = (full_char >> 4) & 0xF
                    self.kbd_nibble_state = 0
                    bank['outputs'][3] = 0
                return

            # --- Standard read ---
            self.acc = bank['registers'][reg]['main'][char]
        else:
            self.acc = self.pins.read_ram()

    def ADM(self):
        bank, reg, char = self._get_ram_target()
        if bank: self._add(bank['registers'][reg]['main'][char])
        else: self._add(self.pins.read_ram())

    def SBM(self):
        bank, reg, char = self._get_ram_target()
        if bank: self._sub(bank['registers'][reg]['main'][char])
        else: self._sub(self.pins.read_ram())

    def WR0(self): 
        bank, reg, char = self._get_ram_target()
        if bank: bank['registers'][reg]['status'][0] = self.acc
        else: self.pins.write_ram_status(0, self.acc)

    def WR1(self): 
        bank, reg, char = self._get_ram_target()
        if bank: bank['registers'][reg]['status'][1] = self.acc
        else: self.pins.write_ram_status(1, self.acc)

    def WR2(self): 
        bank, reg, char = self._get_ram_target()
        if bank: bank['registers'][reg]['status'][2] = self.acc
        else: self.pins.write_ram_status(2, self.acc)

    def WR3(self): 
        bank, reg, char = self._get_ram_target()
        if bank: bank['registers'][reg]['status'][3] = self.acc
        else: self.pins.write_ram_status(3, self.acc)

    def RD0(self): 
        bank, reg, char = self._get_ram_target()
        if bank: self.acc = bank['registers'][reg]['status'][0]
        else: self.acc = self.pins.read_ram_status(0)

    def RD1(self): 
        bank, reg, char = self._get_ram_target()
        if bank: self.acc = bank['registers'][reg]['status'][1]
        else: self.acc = self.pins.read_ram_status(1)

    def RD2(self): 
        bank, reg, char = self._get_ram_target()
        if bank: self.acc = bank['registers'][reg]['status'][2]
        else: self.acc = self.pins.read_ram_status(2)

    def RD3(self): 
        bank, reg, char = self._get_ram_target()
        if bank: self.acc = bank['registers'][reg]['status'][3]
        else: self.acc = self.pins.read_ram_status(3)

    def DCL(self):
        bank = self.acc & 0x7
        self.ram_control = 0b0001 if bank == 0 else (bank << 1)
        self.pins.ram_control = self.ram_control

    def DB0(self): self.pins.set_rom_bank(0)
    def DB1(self): self.pins.set_rom_bank(1)
    def SB0(self): self.selected_register_bank = 0
    def SB1(self): self.selected_register_bank = 1

    # =================================================================
    # ALU AND FLAG OPERATIONS
    # =================================================================

    def CLB(self):
        self.acc = 0
        self.carry = 0

    def CLC(self): self.carry = 0
    def STC(self): self.carry = 1
    def CMC(self): self.carry = (~self.carry) & 0x1
    def CMA(self): self.acc = (~self.acc) & 0xF
    def IAC(self): self._add(1, ignore_carry=True)
    def DAC(self): self._sub(1, ignore_carry=True)

    def RAL(self):
        old_carry = self.carry
        self.carry = (self.acc >> 3) & 0x1
        self.acc = ((self.acc << 1) & 0xF) | old_carry

    def RAR(self):
        old_carry = self.carry
        self.carry = self.acc & 0x1
        self.acc = (self.acc >> 1) | (old_carry << 3)

    def TCC(self):
        self.acc = self.carry
        self.carry = 0

    def TCS(self):
        self.acc = 10 if self.carry == 1 else 9
        self.carry = 0

    def DAA(self):
        if self.carry == 1 or self.acc > 9:
            result = self.acc + 6
            self.acc = result & 0xF
            if result > 0xF:
                self.carry = 1

    def KBP(self):
        mapping = {0x0: 0, 0x1: 1, 0x2: 2, 0x4: 3, 0x8: 4}
        self.acc = mapping.get(self.acc, 0xF)

    # =================================================================
    # MAIN EXECUTION LOOP
    # =================================================================

    def step(self):
        if self.halted or not self.rom:
            return

        opcode = self.rom.read(self.pc)
        opr = opcode >> 4
        opa = opcode & 0xF

        if opr == 0x0:
            if opa == 0x0: self.NOP()
            elif opa == 0x1: self.HLT()
            elif opa == 0x4: self.acc |= self._read_reg(4)
            elif opa == 0x5: self.acc |= self._read_reg(5)
            elif opa == 0x6: self.acc &= self._read_reg(6)
            elif opa == 0x7: self.acc &= self._read_reg(7)
            elif opa == 0x8: self.DB0()
            elif opa == 0x9: self.DB1()
            elif opa == 0xA: self.SB0()
            elif opa == 0xB: self.SB1()
            self.pc += 1
            
        elif opr == 0x1:
            self.JCN(opa, self._fetch_next_byte())
            return
            
        elif opr == 0x2:
            if opa % 2 == 0:
                self.FIM(opa, self._fetch_next_byte())
                return
            else:
                self.SRC(opa & 0xE)
                self.pc += 1
                
        elif opr == 0x3:
            if opa % 2 == 0: 
                self.FIN(opa & 0xE)
                self.pc += 1
            else: 
                self.JIN(opa & 0xE)
                return
                
        elif opr == 0x4:
            self.JUN(opa, self._fetch_next_byte())
            return
            
        elif opr == 0x5:
            self.JMS(opa, self._fetch_next_byte())
            return
            
        elif opr == 0x6:
            self.INC(opa)
            self.pc += 1
            
        elif opr == 0x7:
            self.ISZ(opa, self._fetch_next_byte())
            return
            
        elif opr == 0x8:
            self.ADD(opa)
            self.pc += 1
            
        elif opr == 0x9:
            self.SUB(opa)
            self.pc += 1
            
        elif opr == 0xA:
            self.LD(opa)
            self.pc += 1
            
        elif opr == 0xB:
            self.XCH(opa)
            self.pc += 1
            
        elif opr == 0xC:
            self.BBL(opa)
            return
            
        elif opr == 0xD:
            self.LDM(opa)
            self.pc += 1
            
        elif opr == 0xE:
            if opa == 0x0: self.WRM()
            elif opa == 0x1: self.WMP()
            elif opa == 0x4: self.WR0()
            elif opa == 0x5: self.WR1()
            elif opa == 0x6: self.WR2()
            elif opa == 0x7: self.WR3()
            elif opa == 0x8: self.SBM()
            elif opa == 0x9: self.RDM()
            elif opa == 0xB: self.ADM()
            elif opa == 0xC: self.RD0()
            elif opa == 0xD: self.RD1()
            elif opa == 0xE: self.RD2()
            elif opa == 0xF: self.RD3()
            self.pc += 1
            
        elif opr == 0xF:
            if opa == 0x0: self.CLB()
            elif opa == 0x1: self.CLC()
            elif opa == 0x2: self.IAC()
            elif opa == 0x3: self.CMC()
            elif opa == 0x4: self.CMA()
            elif opa == 0x5: self.RAL()
            elif opa == 0x6: self.RAR()
            elif opa == 0x7: self.TCC()
            elif opa == 0x8: self.DAC()
            elif opa == 0x9: self.TCS()
            elif opa == 0xA: self.STC()
            elif opa == 0xB: self.DAA()
            elif opa == 0xC: self.KBP()
            elif opa == 0xD: self.DCL()
            self.pc += 1