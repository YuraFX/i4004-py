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

import tkinter as tk
from gui.ui import EmulatorUI

def main():
    # Create the main application window
    root = tk.Tk()
    
    # Initialize the emulator UI, passing it the main window
    app = EmulatorUI(root)
    
    # Start the infinite Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()