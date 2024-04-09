# Foobar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

class CPU:
    def __init__(self):

        # 256 bytes of memory
        self.memory = bytearray(256)

        # accumulator
        self.acc = 0

        # program counter
        self.pc = 0

        # carry flag
        self.carry = 0

    # NOP instruction (No Operation)
    def NOP(self):
        self.pc += 1

    # JCN instruction (Jump conditional)
    def JCN(self, address):
        if self.acc != 0:
            self.pc = address
        else:
            self.pc += 2

    # FIM instruction (Fetched immediate from ROM)
    def FIM(self, data):
        self.acc = data
        self.pc += 2

    # JUN instruction (Jump unconditional)
    def JUN(self, address):
        self.pc = address

    # JMS instruction (Jump to Subroutine)
    def JMS(self, address):
        self.memory[self.memory[255]] = self.pc + 2
        self.memory[255] = (self.memory[255] - 1) % 256
        self.pc = address

    # INC instruction (Increment index register)
    def INC(self):
        self.acc = (self.acc + 1) % 256
        self.pc += 1

    # ISZ instruction (Increment index register skip if zero)
    def ISZ(self, address):
        self.memory[address] = (self.memory[address] + 1) % 256

        if self.memory[address] == 0:
            self.pc += 2
        else:
            self.pc += 1

    # ADD instruction (Add index register to accumulator with carry)
    def ADD(self, address):
        self.acc = (self.acc + self.memory[address]) % 256
        self.pc += 2

    # SUB instruction (Subtract index register to accumulator with borrow)
    def SUB(self, address):
        self.acc = (self.acc - self.memory[address]) % 256
        self.pc += 2

    # LD instruction (Load index register to Accumulator)
    def LD(self, address):
        self.acc = self.memory[address]
        self.pc += 2

    # XCH instruction (Exchange index register and accumulator)
    def XCH(self, address):
        temp = self.acc
        self.acc = self.memory[address]
        self.memory[address] = temp
        self.pc += 2

    # BBL instruction (Branch back and load data to the accumulator)
    def BBL(self):
        self.pc = self.memory[self.memory[255]]
        self.acc = self.memory[self.memory[255] + 1]
        self.memory[255] = (self.memory[255] + 2) % 256

    # LDM instruction (Load Data to Accumulator)
    def LDM(self, data):
        self.acc = data
        self.pc += 2

    # CLB instruction (Clear both)
    def CLB(self):
        self.acc = 0
        self.carry = 0
        self.pc += 1

    # CLC instruction (Clear carry)
    def CLC(self):
        self.carry = 0
        self.pc += 1

    # IAC instruction (Increment accumulator)
    def IAC(self):
        self.acc = (self.acc + 1) & 0xFF
        self.pc += 1

    # CMC instruction (Complement carry)
    def CMC(self):
        self.carry = 1 if self.carry == 0 else 0
        self.pc += 1

    # CMA instruction (Complement Accumulator)
    def CMA(self):
        self.acc = ~self.acc & 0xFF
        self.pc += 1

    # RAL instruction (Rotate left)
    def RAL(self):
        temp = (self.acc << 1) + self.carry
        self.carry = (self.acc & 0x80) >> 7
        self.acc = temp & 0xFF
        self.pc += 1

    def run(self):
        while self.pc < len(self.memory):
            opcode = self.memory[self.pc]

            # NOP instruction opcode
            if opcode == 0x0:
                self.NOP()

            # JCN instruction opcode
            elif opcode == 0x1:
                self.JCN(self.memory[self.pc + 1])

            # FIM instruction opcode
            elif opcode == 0x2:
                self.FIM(self.memory[self.pc + 1])

            # JUN instruction opcode
            elif opcode == 0x4:
                self.JUN(self.memory[self.pc + 1])

            # JMS instruction opcode
            elif opcode == 0x5:
                self.JMS(self.memory[self.pc + 1])

            # INC instruction opcode
            elif opcode == 0x6:
                self.INC()

            # ISZ instruction opcode
            elif opcode == 0x7:
                self.ISZ(self.memory[self.pc + 1])

            # ADD instruction opcode
            elif opcode == 0x8:
                self.ADD(self.memory[self.pc + 1])

            # SUB instruction opcode
            elif opcode == 0x9:
                self.SUB(self.memory[self.pc + 1])

            # LD instruction opcode
            elif opcode == 0xA:
                self.LD(self.memory[self.pc + 1])

            # XCH instruction opcode
            elif opcode == 0xB:
                self.XCH(self.memory[self.pc + 1])

            # BBL instruction opcode
            elif opcode == 0xC:
                self.BBL()

            # LDM instruction opcode
            elif opcode == 0xD:
                self.LDM(self.memory[self.pc + 1])

            elif opcode == 0xF:

                # CLB instruction opcode
                if opcode == 0x0:
                    self.CLB()

                # CLC instruction opcode
                elif opcode == 0x1:
                    self.CLC()

                # IAC instruction opcode
                elif opcode == 0x2:
                    self.IAC()

                # CMC instruction opcode
                elif opcode == 0x3:
                    self.CMC()

                # CMA instruction opcode
                elif opcode == 0x4:
                    self.CMA()

                # RAL instruction opcode
                elif opcode == 0x5:
                    self.RAL()

            else:
                print('Unknown opcode!!!')
                return

            self.pc += 1