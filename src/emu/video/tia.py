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

class TIA16x16:
    def __init__(self):
        self.pf = 0
        self.grp0 = 0
        self.grp1 = 0
        self.pos0 = 0
        self.pos1 = 0
        self.y0 = 0
        self.y1 = 0
        self.height0 = 1
        self.height1 = 1
        self.ball_x = 0
        self.ball_y = 0
        self.ball_en = 0
        
        # NEW: Video memory for fixed blocks (16x16)
        self.board = [[0] * 16 for _ in range(16)]
        self.dirty = True

    def write_register(self, reg, value):
        if reg == 0: self.pf = (self.pf & 0xFFF0) | (value & 0xF)
        elif reg == 1: self.pf = (self.pf & 0xF00F) | ((value & 0xFF) << 4)
        elif reg == 2: self.pf = (self.pf & 0x0FFF) | ((value & 0xF) << 12)
        elif reg == 3: self.grp0 = value & 0xFF
        elif reg == 4: self.grp1 = value & 0xFF
        elif reg == 5: self.pos0 = value & 0xF
        elif reg == 6: self.pos1 = value & 0xF
        elif reg == 7: self.y0 = value & 0xF
        elif reg == 8: self.y1 = value & 0xF
        elif reg == 9: 
            self.dirty = True
            return True
        elif reg == 10: self.height0 = (value & 0x7) + 1
        elif reg == 11: self.height1 = (value & 0x7) + 1
        elif reg == 12: self.ball_x = value & 0xF
        elif reg == 13: self.ball_y = value & 0xF
        elif reg == 14: self.ball_en = value & 0x1
        # NEW REGISTER 15: Set a pixel in video memory (X, Y)
        elif reg == 15:
            # NEW LOGIC: Accept X and Y in turn
            if not hasattr(self, 'pixel_x'):
                self.pixel_x = None
                
            if self.pixel_x is None:
                self.pixel_x = value & 0xF  # Save X
            else:
                y = value & 0xF            # Get Y
                x = self.pixel_x
                if 0 <= x < 16 and 0 <= y < 16:
                    self.board[y][x] = 1
                    self.dirty = True      # Force TIA to redraw the frame
                self.pixel_x = None        # Reset for the next point

    def render(self, display):
        if not self.dirty: return
        self.dirty = False
        pixels = display.pixels
        
        # 1. Draw the background (Playfield)
        for y in range(16):
            for x in range(16):
                pixels[y][x] = (self.pf >> (15 - x)) & 1
        
        # 2. Overlay fixed blocks from video memory
        for y in range(16):
            for x in range(16):
                if self.board[y][x]:
                    pixels[y][x] = 1

        # 3. Draw the current shape (sprites)
        self._blit_sprite(pixels, self.grp0, self.pos0, self.y0, self.height0)
        self._blit_sprite(pixels, self.grp1, self.pos1, self.y1, self.height1)
        
        if self.ball_en:
            if 0 <= self.ball_x < 16 and 0 <= self.ball_y < 16:
                pixels[self.ball_y][self.ball_x] = 1

    def _blit_sprite(self, pixels, grp, pos_x, pos_y, height):
        for h in range(height):
            y = pos_y + h
            if y < 0 or y >= 16: continue
            for i in range(8):
                x = pos_x + i
                if 0 <= x < 16:
                    bit = (grp >> i) & 1
                    if bit: pixels[y][x] = 1