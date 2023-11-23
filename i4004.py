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

memory = bytearray(256) # 256 байт памяти

class I4004:
    def __init__(self, program, memory):
        self.program = program
        self.memory = memory

        self.acc = 0 # Аккумулятор
        self.pc = 0 # Счётчик команд

    def run(self):
        while True:
            opcode = self.program[self.pc]

            if opcode == 0x00: # Остановка
                return

            elif opcode == 0xA2: # Загрузка числа в аккумулятор
                self.acc = self.program[self.pc + 1]
                self.pc += 2

            elif opcode == 0xA4: # Загрузка числа в регистр 0
                self.rr0 = self.program[self.pc + 1]
                self.pc += 2

            elif opcode == 0x58: # Сложение
                self.acc += self.rr0
                self.pc += 1
                if self.acc > 15:
                    self.acc = 15
                    print("Вы не можете получить число выше 15!")

            elif opcode == 0x29: # Вычитание
                self.acc -= self.rr0
                self.pc += 1
                if self.acc < 0:
                    self.acc = 0
                    print("Вы не можете получить число ниже 0!")

            elif opcode == 0x16: # Логическая операция И
                self.acc &= self.rr0
                self.pc += 1

            elif opcode == 0x08: # Логическая операция ИЛИ
                self.acc | self.rr0
                self.pc += 1

            elif opcode == 0xD0: # Сохранение результата в памяти
                address = self.program[self.pc + 1]
                self.memory[address] = self.acc
                self.pc += 2

            else:
                print("Неизвестная инструкция!")
                return