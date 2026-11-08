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

class DiskImage:
    def __init__(self, path=None):
        # IBM 3740 / Shugart SA 800-1 format parameters
        self.tracks = 77               # Tracks
        self.sectors_per_track = 26    # Sectors per track
        self.sector_size = 128         # Bytes per sector
        self.total_size = self.tracks * self.sectors_per_track * self.sector_size  # 256256 bytes

        # Interleave (software skew) table for CP/M 1.4/2.2 on 8-inch disks.
        # Physical sector -> logical (0-based).
        # In CP/M 1.4: [1,7,13,19,25,5,11,17,23,3,9,15,21,2,8,14,20,26,6,12,18,24,4,10,16,22]
        # Stored 0-based here for convenience.
        self.skew_table = [
            0, 6, 12, 18, 24, 4, 10, 16, 22, 2, 8, 14, 20,
            1, 7, 13, 19, 25, 5, 11, 17, 23, 3, 9, 15, 21
        ]

        # Image data: flat bytearray
        self.data = bytearray(self.total_size)

        # If a path is given, load it
        if path:
            self.load(path)

    def load(self, path):
        # Load a raw image (exactly 256256 bytes)
        with open(path, "rb") as f:
            raw = f.read()
        if len(raw) != self.total_size:
            raise ValueError(
                f"Invalid image size: {len(raw)} bytes, expected {self.total_size}"
            )
        self.data = bytearray(raw)

    def save(self, path):
        # Save a raw image
        with open(path, "wb") as f:
            f.write(self.data)

    def _offset(self, track, sector, skew=False):
        # Compute the offset in the flat array.
        # If skew=True, apply the CP/M interleave table.
        if track < 0 or track >= self.tracks:
            raise ValueError(f"Track out of range: {track}")
        if sector < 0 or sector >= self.sectors_per_track:
            raise ValueError(f"Sector out of range: {sector}")

        physical_sector = sector
        if skew:
            # skew_table[logical] = physical
            physical_sector = self.skew_table[sector]

        return (track * self.sectors_per_track + physical_sector) * self.sector_size

    def read_sector(self, track, sector, skew=False):
        # Return the 128 bytes of the sector
        off = self._offset(track, sector, skew)
        return self.data[off:off + self.sector_size]

    def write_sector(self, track, sector, data, skew=False):
        # Write 128 bytes into the sector
        if len(data) != self.sector_size:
            raise ValueError(f"Invalid data size: {len(data)}, expected {self.sector_size}")
        off = self._offset(track, sector, skew)
        self.data[off:off + self.sector_size] = data

    def clear(self):
        # Clear the image (all zeros)
        self.data = bytearray(self.total_size)