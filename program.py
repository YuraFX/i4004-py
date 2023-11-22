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

print("Эмулятор Intel 4004 с очень урезанным функционалом")
print("Автор эмулятора: Конышев Юрий aka Yura_FX (2023 г.)")

from i4004 import memory
from i4004 import I4004

program = [         # Программа сложения чисел 5 и 3
    0xA2, 0x05,
    0xA4, 0x03,
    0x58,
    0xD0, 0x10,
    0x00,
]

cpu = I4004(program, memory)
cpu.run()

print(f"Результат: {memory[0x10]}")