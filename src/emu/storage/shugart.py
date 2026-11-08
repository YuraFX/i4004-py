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

class ShugartSA800:
    def __init__(self):
        # --- Mechanical parameters (from the documentation) ---
        self.rpm = 360                     # Rotation speed, RPM
        self.revolution_time_ms = 166.667  # Time of one revolution, ms (60 / 360 * 1000)
        self.step_time_ms = 8              # Time of one head step, ms
        self.tracks = 77                   # Number of tracks (0..76)
        self.sectors_per_track = 26        # Sectors per track (IBM 3740)
        self.bytes_per_sector = 128        # Bytes per sector

        # --- Controller state ---
        self.current_track = 0             # Current track (0..76)
        self.direction = 1                 # 1 = inward (forward), 0 = outward (backward)
        self.head_loaded = False           # Head pressed against the disk
        self.write_gate = False            # Write enable
        self.selected = False              # Device selected

        # --- Disk buffer (image emulation) ---
        # Stored as a list of tracks, each track is a list of sectors (byte arrays)
        self.disk_image = self._create_empty_disk()

        # --- Flags for the processor (interface line emulation) ---
        self.track00 = True                # Head is on track 00
        self.index = False                 # Index signal (once per revolution)
        self.ready = True                  # Drive is ready

    def _create_empty_disk(self):
        # Create an empty image: 77 tracks × 26 sectors × 128 bytes
        disk = []
        for t in range(self.tracks):
            track = []
            for s in range(self.sectors_per_track):
                track.append(bytearray(self.bytes_per_sector))
            disk.append(track)
        return disk

    # =================================================================
    # HEAD CONTROL (STEP / DIRECTION)
    # =================================================================
    def step(self):
        # Emulate a head step (on the STEP signal edge)
        if not self.selected:
            return
        # Move the head depending on the direction
        if self.direction == 1:
            if self.current_track < self.tracks - 1:
                self.current_track += 1
        else:
            if self.current_track > 0:
                self.current_track -= 1

        # Update the Track00 signal
        self.track00 = (self.current_track == 0)

    def set_direction(self, inward):
        # inward = True -> inward (increasing track number)
        self.direction = 1 if inward else 0

    # =================================================================
    # SECTOR READ / WRITE (CONTROLLER EMULATION)
    # =================================================================
    def read_sector(self, sector_num):
        # Return 128 bytes from the given sector of the current track
        if not self.selected or sector_num >= self.sectors_per_track:
            return None
        # Real hardware would wait for the Index signal and count bits.
        # Here we simply return the data from the image.
        return self.disk_image[self.current_track][sector_num]

    def write_sector(self, sector_num, data):
        # Write 128 bytes into the given sector (if the write gate is active)
        if not self.selected or not self.write_gate or sector_num >= self.sectors_per_track:
            return False
        if len(data) != self.bytes_per_sector:
            return False
        self.disk_image[self.current_track][sector_num] = bytearray(data)
        return True

    # =================================================================
    # INTERFACE CONTROL (SIGNALS)
    # =================================================================
    def select(self, enable=True):
        self.selected = enable

    def load_head(self, enable=True):
        self.head_loaded = enable

    def set_write_gate(self, enable=True):
        self.write_gate = enable

    # =================================================================
    # INDEX SIGNAL (GENERATED DURING OPERATION)
    # =================================================================
    def tick_index(self, elapsed_ms):
        # On a real drive, the Index signal appears once per revolution.
        # We could emulate it, but for simplicity we just return False for now.
        # A time counter can be added later.
        pass