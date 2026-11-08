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

class Display:
    def __init__(self, width=16, height=16):
        self.width = width
        self.height = height
        # 0 = off, 1 = on
        self.pixels = [[0] * width for _ in range(height)]

    def set_pixel(self, x, y, value):
        # Guard against going outside the screen bounds
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = 1 if value else 0

    def clear(self):
        for y in range(self.height):
            for x in range(self.width):
                self.pixels[y][x] = 0