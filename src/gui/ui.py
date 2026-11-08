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
from tkinter import ttk, scrolledtext, messagebox, filedialog
import re
import os
import glob

from emu.system import System
from comp.assembler import Assembler
from comp.basic_lexer import BasicLexer
from comp.basic_parser import BasicParser
from comp.basic_codegen import BasicCodeGen
from comp.linker import Linker
from emu.storage.disk_image import DiskImage


class EmulatorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("i4004-py 1.0 — 4-bit MCS-4 Emulator (x64)")
        self.root.configure(bg="#f0f4f8")
        
        # Set the icon (replace icon.png with your actual file name)
        try:
            self.icon_img = tk.PhotoImage(file="assets/icons/icon.png")
            self.root.iconphoto(True, self.icon_img)
        except Exception:
            pass

        self._center_window(1100, 650)

        dummy_rom = [bytearray([0x00] * 256)]
        self.system = System(rom_dump=dummy_rom)
        
        self.current_filepath = None

        self.reg_labels = {}
        self.io_labels = []
        self.sr4003_labels = []
        self.disk_labels = {}
        self.mem_text = None
        self.tty_text = None
        self.disk_hex_text = None
        self.display_canvas = None
        self.display_rects = []

        self.is_running = False
        self.line_map = {}
        self._last_highlighted_line = None
        self.key_queue = []

        self.status_var = tk.StringVar()
        self.status_var.set("Ready.") 
        self.status_bar = tk.Label(
            self.root, 
            textvariable=self.status_var, 
            bg="#e0e0e0", fg="#333", anchor="w", padx=10, pady=5, 
            font=("Consolas", 10), bd=1, relief=tk.SUNKEN
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#f0f4f8", sashwidth=5)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_frame = tk.Frame(self.paned_window, bg="#1e1e1e", bd=2, relief=tk.RIDGE)
        self.paned_window.add(self.left_frame, minsize=400, width=650)
        self._setup_editor()

        self.right_frame = tk.Frame(self.paned_window, bg="#f0f4f8")
        self.paned_window.add(self.right_frame, minsize=450)
        self._setup_right_panel()

        self.root.bind('<KeyPress>', self._on_key_press)
        self.root.bind('<KeyRelease>', self._on_key_release)

        self.update_ui()

    def _center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _on_key_press(self, event):
        if self.root.focus_get() == self.code_editor:
            return
        
        key = event.keysym.lower()
        bank = self.system.ram.banks[0]
        
        if key == 'left': 
            bank['outputs'][3] = 1
            return
        elif key == 'right': 
            bank['outputs'][3] = 2
            return
        elif key == 'up': 
            bank['outputs'][3] = 3
            return
        elif key == 'down': 
            bank['outputs'][3] = 4
            return
            
        if event.char:
            code = ord(event.char)
            if 97 <= code <= 122:
                code = code - 32
            
            if 32 <= code <= 126 or code == 13:
                self.key_queue.append(code)

    def _on_key_release(self, event):
        if self.root.focus_get() == self.code_editor:
            return
        
        key = event.keysym.lower()
        bank = self.system.ram.banks[0]
        if key in ['left', 'right', 'up', 'down']:
            bank['outputs'][3] = 0

    def _setup_editor(self):
        editor_container = tk.Frame(self.left_frame, bg="#1e1e1e")
        editor_container.pack(fill=tk.BOTH, expand=True)

        # Line numbers
        self.line_numbers = tk.Text(editor_container, width=3, padx=4, takefocus=0, border=0,
                                    background="#2d2d2d", foreground="#858585", state='disabled', font=("Consolas", 11))
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Text
        self.code_editor = tk.Text(editor_container, wrap=tk.NONE,
                                    bg="#1e1e1e", fg="#d4d4d4", insertbackground="white", 
                                    font=("Consolas", 11), bd=0, padx=10, pady=5, undo=True, maxundo=-1)
        self.code_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        self.scrollbar = tk.Scrollbar(editor_container, command=self._on_scrollbar)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.code_editor.config(yscrollcommand=self._on_text_scroll)

        self.code_editor.tag_config("comment", foreground="#6a9955")
        self.code_editor.tag_config("current_line", background="#5a5a00")

        self.code_editor.bind("<KeyRelease>", self._highlight_syntax)
        self.code_editor.bind('<MouseWheel>', self._on_scroll)
        self.code_editor.bind('<KeyRelease>', self._update_line_numbers)
        self.code_editor.bind("<Button-3>", self._show_context_menu)
        self.code_editor.bind("<Key>", self._universal_hotkeys)

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.code_editor.edit_undo)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Cut", accelerator="Ctrl+X", command=lambda: self.code_editor.event_generate("<<Cut>>"))
        self.context_menu.add_command(label="Copy", accelerator="Ctrl+C", command=lambda: self.code_editor.event_generate("<<Copy>>"))
        self.context_menu.add_command(label="Paste", accelerator="Ctrl+V", command=lambda: self.code_editor.event_generate("<<Paste>>"))

        bottom_frame = tk.Frame(self.left_frame, bg="#1e1e1e")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        open_btn = tk.Button(bottom_frame, text="Open", bg="#2196F3", fg="white", font=("Arial", 10, "bold"), relief=tk.FLAT, command=self.open_file)
        open_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=10, ipady=5)

        save_btn = tk.Button(bottom_frame, text="Save", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), relief=tk.FLAT, command=self.save_code)
        save_btn.pack(side=tk.LEFT, ipadx=10, ipady=5)

        self._update_line_numbers()

    def _on_text_scroll(self, first, last):
        self.scrollbar.set(first, last)
        self.line_numbers.yview_moveto(first)

    def _on_scrollbar(self, *args):
        self.code_editor.yview(*args)
        self.line_numbers.yview(*args)

    def _show_context_menu(self, event):
        try: self.context_menu.tk_popup(event.x_root, event.y_root)
        finally: self.context_menu.grab_release()

    def _universal_hotkeys(self, event):
        if event.state & 4:
            key = event.keycode
            if key == 65:
                self.code_editor.tag_add(tk.SEL, "1.0", tk.END)
                self.code_editor.mark_set(tk.INSERT, "1.0")
                self.code_editor.see(tk.INSERT)
                return "break"
            elif key == 67:
                self.code_editor.event_generate("<<Copy>>")
                return "break"
            elif key == 88:
                self.code_editor.event_generate("<<Cut>>")
                return "break"
            elif key == 86:
                self.code_editor.event_generate("<<Paste>>")
                return "break"
            elif key == 90:
                self.code_editor.edit_undo()
                return "break"

    def _update_line_numbers(self, event=None):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        line_count = int(self.code_editor.index('end-1c').split('.')[0])
        numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert(1.0, numbers)
        self.line_numbers.config(state='disabled')

    def _on_scroll(self, event):
        self.line_numbers.yview_scroll(int(-1*(event.delta/120)), "units")
        self.code_editor.yview_scroll(int(-1*(event.delta/120)), "units")

    def _highlight_syntax(self, event=None):
        content = self.code_editor.get("1.0", tk.END)
        self.code_editor.tag_remove("comment", "1.0", tk.END)
        for match in re.finditer(r"//.*", content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.code_editor.tag_add("comment", start, end)

    def _detect_language(self, source):
        lines = source.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if line.startswith(';'):
                continue
                
            cleaned_lines.append(line.upper())
            if len(cleaned_lines) >= 5: break

        if not cleaned_lines: return "unknown"
        first_code_line = cleaned_lines[0]
        
        if first_code_line and first_code_line[0].isdigit(): 
            return "basic"
            
        return "asm"

    def open_file(self):
        self.status_var.set("Opening file...")
        filepath = filedialog.askopenfilename(
            title="Open file",
            filetypes=[("All Files", "*.*"), ("Assembly", "*.asm"), ("BASIC", "*.bas"), ("Text", "*.txt")]
        )
        if not filepath: 
            self.status_var.set("Open cancelled.")
            return
        if not filepath.lower().endswith(('.asm', '.bas', '.txt')):
            self.status_var.set("Error: Unsupported format.")
            messagebox.showwarning("Format error", "Please select a file with .asm, .bas, or .txt extension.")
            return
        try:
            self.status_var.set(f"Loading: {filepath}...")
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.code_editor.delete("1.0", tk.END)
            self.code_editor.insert("1.0", content)
            self.code_editor.edit_reset()
            self._update_line_numbers()
            self.current_filepath = os.path.abspath(filepath)
            self.status_var.set(f"Loaded: {filepath}")
        except Exception as e:
            self.status_var.set("Error loading file.")
            messagebox.showerror("Error", f"Failed to open file: {e}")

    def save_code(self):
        source = self.code_editor.get("1.0", tk.END).strip()
        if not source: return
        lang = self._detect_language(source)
        
        if lang == "basic":
            default_ext, file_types = ".bas", [("BASIC File", "*.bas"), ("All Files", "*.*")]
        else:
            default_ext, file_types = ".asm", [("Assembly File", "*.asm"), ("All Files", "*.*")]
        
        self.status_var.set("Saving file...")
        filepath = filedialog.asksaveasfilename(defaultextension=default_ext, filetypes=file_types)
        if filepath:
            try:
                self.status_var.set(f"Saving: {filepath}...")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(source)
                self.current_filepath = os.path.abspath(filepath)
                self.status_var.set(f"Saved: {filepath}")
            except Exception as e:
                self.status_var.set("Error saving file.")
                messagebox.showerror("Error", f"Failed to save file: {e}")
        else:
            self.status_var.set("Save cancelled.")

    def _setup_right_panel(self):
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.tab_general = tk.Frame(self.notebook, bg="#f0f4f8")
        self.tab_io = tk.Frame(self.notebook, bg="#f0f4f8")
        self.tab_memory = tk.Frame(self.notebook, bg="#f0f4f8")
        self.tab_disk = tk.Frame(self.notebook, bg="#f0f4f8")

        self.notebook.add(self.tab_general, text=" General ")
        self.notebook.add(self.tab_io, text=" IO ")
        self.notebook.add(self.tab_memory, text=" Memory ")
        self.notebook.add(self.tab_disk, text=" Disk ")

        self._setup_general_tab()
        self._setup_io_tab()
        self._setup_memory_tab()
        self._setup_disk_tab()

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        self.update_ui()

    def _create_control_buttons(self, parent):
        """Create a universal button block for all tabs"""
        btn_frame = tk.Frame(parent, bg="#f0f4f8")
        btn_frame.pack(fill=tk.X, pady=10, padx=20)

        tk.Button(btn_frame, text="Build", bg="#81c784", fg="white", relief=tk.FLAT, width=8, font=("Arial", 10), command=self.build_run).pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        tk.Button(btn_frame, text="Stop", bg="#e57373", fg="white", relief=tk.FLAT, width=8, font=("Arial", 10), command=self.stop).pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        tk.Button(btn_frame, text="Run", bg="white", fg="black", relief=tk.GROOVE, width=8, font=("Arial", 10), command=self.continue_run).pack(side=tk.LEFT, ipady=3)
        
        return btn_frame

    def _setup_general_tab(self):
        # 1. Control buttons
        self._create_control_buttons(self.tab_general)

        # 2. Debug buttons
        step_frame = tk.Frame(self.tab_general, bg="#f0f4f8")
        step_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Button(step_frame, text="Step over", bg="white", fg="black", relief=tk.GROOVE, width=10, command=self.step).pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        tk.Button(step_frame, text="Step into", bg="white", fg="black", relief=tk.GROOVE, width=10, command=self.step).pack(side=tk.LEFT, ipady=3)

        # 3. Registers
        reg_container = tk.Frame(self.tab_general, bg="#f0f4f8")
        reg_container.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        self._build_misc_registers(reg_container)
        self._build_main_registers(reg_container)
        self._build_pairs_registers(reg_container)

    def _setup_io_tab(self):
        # 1. Control buttons (top)
        self._create_control_buttons(self.tab_io)
        
        # 2. Ports (shifted to the right via padx)
        frame_ports = tk.LabelFrame(self.tab_io, text="RAM Output Ports (WMP/RDM)", bg="#f0f4f8", font=("Arial", 10))
        frame_ports.pack(fill=tk.X, padx=20, pady=(0, 5))

        for i in range(6):
            row = i % 3
            col = i // 3
            
            container = tk.Frame(frame_ports, bg="#f0f4f8")
            container.grid(row=row, column=col, padx=15, pady=4, sticky="w")
            
            tk.Label(container, text=f"Port {i} (Chip {i}):", bg="#f0f4f8", font=("Consolas", 11)).pack(side=tk.LEFT)
            lbl = tk.Label(container, text="00", bg="#e0e0e0", width=4, font=("Consolas", 11))
            lbl.pack(side=tk.LEFT, padx=10)
            self.io_labels.append(lbl)

        # 3. Switcher (Display + Monitor)
        frame_mode = tk.LabelFrame(self.tab_io, text="Display & System Mode", bg="#f0f4f8", font=("Arial", 10))
        frame_mode.pack(fill=tk.X, padx=20, pady=5)

        # Select video controller
        tk.Label(frame_mode, text="Controller:", bg="#f0f4f8", font=("Consolas", 11)).pack(side=tk.LEFT, padx=10)
        self.display_mode_combo = ttk.Combobox(
            frame_mode, 
            values=["4003 Shift Register", "TIA (Television Interface Adaptor, buffered 16x16)", "Teletype Model 33 ASR (110 baud, 20mA loop)"], 
            state="readonly", width=42
        )
        self.display_mode_combo.set("4003 Shift Register")
        self.display_mode_combo.pack(side=tk.LEFT, padx=5, pady=5)
        self.display_mode_combo.bind("<<ComboboxSelected>>", self._on_display_mode_changed)

        # NEW: System monitor selection
        tk.Label(frame_mode, text="| Monitor:", bg="#f0f4f8", font=("Consolas", 11)).pack(side=tk.LEFT, padx=(10, 5))
        self.monitor_combo = ttk.Combobox(
            frame_mode, 
            values=["None", "System Monitor"], 
            state="readonly", width=22
        )
        self.monitor_combo.set("None")
        self.monitor_combo.pack(side=tk.LEFT, padx=5, pady=5)
        self.monitor_combo.bind("<<ComboboxSelected>>", self._on_monitor_changed)

        # 4. Output blocks
        self.frame_4003 = tk.LabelFrame(self.tab_io, text="Intel 4003 Shift Register (10-bit)", bg="#f0f4f8", font=("Arial", 10))
        sr_row = tk.Frame(self.frame_4003, bg="#f0f4f8")
        sr_row.pack(pady=5)
        self.sr4003_labels = [None] * 10
        for i in range(9, -1, -1):
            lbl = tk.Label(sr_row, text="0", bg="#e0e0e0", width=2, font=("Consolas", 12, "bold"))
            lbl.pack(side=tk.LEFT, padx=2)
            self.sr4003_labels[i] = lbl

        self.frame_display = tk.LabelFrame(self.tab_io, text="Monochrome Display (16x16)", bg="#f0f4f8", font=("Arial", 10))
        self.display_canvas = tk.Canvas(self.frame_display, width=256, height=256, bg="black", highlightthickness=1, highlightbackground="#ccc")
        self.display_canvas.pack(pady=10, expand=True)
        self.display_canvas.bind("<Button-1>", lambda e: self.root.focus_set())

        self.display_rects = []
        for y in range(16):
            row = []
            for x in range(16):
                rect = self.display_canvas.create_rectangle(
                    x * 16, y * 16, (x + 1) * 16, (y + 1) * 16, fill="black", outline=""
                )
                row.append(rect)
            self.display_rects.append(row)

        self.frame_tty = tk.LabelFrame(self.tab_io, text="Teletype Model 33 ASR", bg="#f0f4f8", font=("Arial", 10))
        self.tty_text = scrolledtext.ScrolledText(self.frame_tty, bg="#f4f4f4", fg="#111", font=("Courier", 12), state='disabled')
        self.tty_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tty_text.bind("<Button-1>", lambda e: self.root.focus_set())

        self._update_io_visibility()

    def _setup_disk_tab(self):
        # 1. Control buttons
        self._create_control_buttons(self.tab_disk)

        # 2. Status
        frame_status = tk.LabelFrame(self.tab_disk, text="Shugart SA 800-1 Status", bg="#f0f4f8", font=("Arial", 10))
        frame_status.pack(fill=tk.X, padx=20, pady=(5, 5))

        self.disk_labels = {}
        labels = [("Track", "00"), ("Direction", "Outward"), ("Track 00", "Yes"), ("Ready", "Yes"), ("Write Gate", "Off")]
        
        for i, (name, val) in enumerate(labels):
            row = tk.Frame(frame_status, bg="#f0f4f8")
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=f"{name}:", bg="#f0f4f8", font=("Consolas", 11), width=12, anchor="w").pack(side=tk.LEFT, padx=10)
            lbl = tk.Label(row, text=val, bg="#e0e0e0", width=10, font=("Consolas", 11), anchor="w")
            lbl.pack(side=tk.LEFT, padx=5)
            self.disk_labels[name] = lbl

        # 3. Image management
        frame_ctrl = tk.LabelFrame(self.tab_disk, text="Disk Image", bg="#f0f4f8", font=("Arial", 10))
        frame_ctrl.pack(fill=tk.X, padx=20, pady=5)

        tk.Button(frame_ctrl, text="Load .dsk Image", bg="#2196F3", fg="white", relief=tk.FLAT, command=self.load_disk_image).pack(side=tk.LEFT, padx=10, pady=5, ipadx=10)
        tk.Button(frame_ctrl, text="Save .dsk Image", bg="#4CAF50", fg="white", relief=tk.FLAT, command=self.save_disk_image).pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)
        self.disk_path_label = tk.Label(frame_ctrl, text="No disk inserted", bg="#f0f4f8", font=("Arial", 9), fg="#666")
        self.disk_path_label.pack(side=tk.LEFT, padx=10)

        # 4. Dump
        frame_dump = tk.LabelFrame(self.tab_disk, text="Sector Dump (Current Track, Target Sector)", bg="#f0f4f8", font=("Arial", 10))
        frame_dump.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 20))

        self.disk_hex_text = scrolledtext.ScrolledText(frame_dump, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10), state='disabled')
        self.disk_hex_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_disk_image(self):
        filepath = filedialog.askopenfilename(
            title="Load disk image (IBM 3740)",
            filetypes=[("Disk Image", "*.dsk *.img"), ("All Files", "*.*")]
        )
        if not filepath: return

        try:
            self.status_var.set(f"Loading disk: {filepath}...")
            img = DiskImage(filepath)
            if hasattr(self.system, 'disk_controller'):
                disk = self.system.disk_controller
                flat_data = img.data
                idx = 0
                for t in range(disk.tracks):
                    for s in range(disk.sectors_per_track):
                        disk.disk_image[t][s] = bytearray(flat_data[idx : idx + disk.bytes_per_sector])
                        idx += disk.bytes_per_sector
                
                self.status_var.set(f"Disk loaded: {os.path.basename(filepath)}")
                self.disk_path_label.config(text=os.path.basename(filepath))
                self.update_ui()
            else:
                messagebox.showerror("Error", "Disk drive controller is not initialized.")
        except Exception as e:
            self.status_var.set("Error loading disk.")
            messagebox.showerror("Image error", str(e))

    def save_disk_image(self):
        if not hasattr(self.system, 'disk_controller'): return
        filepath = filedialog.asksaveasfilename(
            title="Save disk image",
            defaultextension=".dsk",
            filetypes=[("Disk Image", "*.dsk *.img"), ("All Files", "*.*")]
        )
        if not filepath: return
        
        try:
            disk = self.system.disk_controller
            flat_data = bytearray()
            for t in range(disk.tracks):
                for s in range(disk.sectors_per_track):
                    flat_data.extend(disk.disk_image[t][s])
            
            with open(filepath, "wb") as f:
                f.write(flat_data)
            self.status_var.set(f"Disk saved: {os.path.basename(filepath)}")
            self.disk_path_label.config(text=os.path.basename(filepath))
        except Exception as e:
            self.status_var.set("Error saving disk.")
            messagebox.showerror("Save error", str(e))

    def _update_io_visibility(self):
        self.frame_4003.pack_forget()
        self.frame_display.pack_forget()
        self.frame_tty.pack_forget()

        mode_str = self.display_mode_combo.get()
        if "4003" in mode_str:
            self.frame_4003.pack(fill=tk.X, padx=20, pady=5)
            self.frame_display.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 10))
        elif "TIA" in mode_str:
            self.frame_display.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 10))
        elif "Teletype" in mode_str:
            self.frame_tty.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 15))

    def _on_display_mode_changed(self, event):
        mode_str = self.display_mode_combo.get()
        if "TIA" in mode_str: mode = "TIA"
        elif "Teletype" in mode_str: mode = "Teletype"
        else: mode = "4003"

        if hasattr(self.system, 'cpu'):
            self.system.cpu.display_mode = mode
            if hasattr(self.system, 'display'):
                for y in range(16):
                    for x in range(16):
                        self.system.display.pixels[y][x] = 0
            self._draw_display()
        self._update_io_visibility()

    def _on_monitor_changed(self, event):
        mode = self.monitor_combo.get()
        
        if mode == "System Monitor":
            # Search for the monitor file in possible paths
            possible_paths = [
                os.path.join('firmware', 'monitor', 'monitor.asm'),
                os.path.join('firmware', 'monitor.asm'),
                os.path.join('monitor', 'monitor.asm')
            ]
            
            filepath = None
            for p in possible_paths:
                if os.path.exists(p):
                    filepath = p
                    break
            
            if filepath:
                try:
                    # 1. Load the code into the editor
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    self.code_editor.delete("1.0", tk.END)
                    self.code_editor.insert("1.0", content)
                    self.current_filepath = os.path.abspath(filepath)
                    self._update_line_numbers()
                    
                    # 2. Automatically do Build and Run
                    self.build_run()
                    self.continue_run()
                    
                except Exception as e:
                    self.status_var.set("Error loading monitor.")
                    messagebox.showerror("Error", f"Failed to load the Monitor:\n{e}")
            else:
                self.status_var.set("Monitor file not found.")
                messagebox.showerror("Error", "File monitor.asm not found in the firmware/monitor/ folder")

    def _setup_memory_tab(self):
        self.mem_text = scrolledtext.ScrolledText(self.tab_memory, bg="#ffffff", font=("Consolas", 10), state='disabled')
        self.mem_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _create_reg_label(self, parent, row, col, name, initial_val="0"):
        frame = tk.Frame(parent, bg="#f0f4f8")
        frame.grid(row=row, column=col, padx=5, pady=2, sticky="w")
        tk.Label(frame, text=name, bg="#f0f4f8", fg="#666", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))
        lbl_val = tk.Label(frame, text=initial_val, bg="#e0e0e0", width=4, font=("Consolas", 10), relief=tk.FLAT)
        lbl_val.pack(side=tk.LEFT)
        self.reg_labels[name] = lbl_val
        return frame

    def _build_misc_registers(self, parent):
        frame = tk.LabelFrame(parent, text="Miscellaneous", bg="#f0f4f8", fg="#333", font=("Arial", 10))
        frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, expand=True)
        regs = ["ACC", "CY", "Bank", "PC", "SP", "S0", "S1", "S2"]
        for i, reg in enumerate(regs):
            self._create_reg_label(frame, i, 0, reg)

    def _build_main_registers(self, parent):
        frame = tk.LabelFrame(parent, text="Registers", bg="#f0f4f8", fg="#333", font=("Arial", 10))
        frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, expand=True)
        for i in range(16):
            name = f"RR{i:02d}"
            self._create_reg_label(frame, i // 2, i % 2, name)

    def _build_pairs_registers(self, parent):
        frame = tk.LabelFrame(parent, text="Register pairs", bg="#f0f4f8", fg="#333", font=("Arial", 10))
        frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, expand=True)
        for i in range(8):
            name = f"R{i}"
            self._create_reg_label(frame, i, 0, name, initial_val="00")

    def update_ui(self):
        if not hasattr(self.system, 'cpu'): return
        current_tab = self.notebook.index(self.notebook.select())

        if current_tab == 0:
            cpu = self.system.cpu
            self.reg_labels["ACC"].config(text=f"{cpu.acc:02X}")
            self.reg_labels["CY"].config(text=f"{cpu.carry:02X}")
            self.reg_labels["Bank"].config(text=f"{cpu.selected_register_bank:02X}")
            self.reg_labels["PC"].config(text=f"{cpu.pc:03X}")
            self.reg_labels["SP"].config(text=f"{cpu.sp:02X}")

            for i in range(16):
                val = cpu.index_banks[cpu.selected_register_bank][i]
                self.reg_labels[f"RR{i:02d}"].config(text=f"{val:02X}")

            for i in range(8):
                high = cpu.index_banks[cpu.selected_register_bank][i * 2]
                low = cpu.index_banks[cpu.selected_register_bank][i * 2 + 1]
                self.reg_labels[f"R{i}"].config(text=f"{(high << 4) | low:02X}")

        elif current_tab == 1:
            bank_no = self.system.selected_ram_bank
            bank_data = self.system.memory[bank_no]
            for i in range(6):
                self.io_labels[i].config(text=f"{bank_data['outputs'][i]:02X}")
            
            if hasattr(self.system, 'sr4003'):
                for i in range(10):
                    bit = self.system.sr4003.bits[i]
                    color = "#4CAF50" if bit else "#e0e0e0"
                    self.sr4003_labels[i].config(text=str(bit), bg=color)
                    
            self._draw_display()

            if hasattr(self.system, 'teletype') and self.tty_text:
                self.tty_text.config(state='normal')
                self.tty_text.delete("1.0", tk.END)
                self.tty_text.insert(tk.END, self.system.teletype.get_text())
                self.tty_text.see(tk.END)
                self.tty_text.config(state='disabled')

        elif current_tab == 2:
            bank_no = self.system.selected_ram_bank
            bank_data = self.system.memory[bank_no]
            self.mem_text.config(state='normal')
            self.mem_text.delete(1.0, tk.END)
            self.mem_text.insert(tk.END, f"--- RAM BANK {bank_no} (Selected) ---\n\n")
            for reg_idx in range(16):
                reg = bank_data['registers'][reg_idx]
                main_str = " ".join(f"{x:X}" for x in reg['main'])
                status_str = " ".join(f"{x:X}" for x in reg['status'])
                self.mem_text.insert(tk.END, f"R{reg_idx:02X}: [{main_str}] | [{status_str}]\n")
            self.mem_text.config(state='disabled')

        elif current_tab == 3:
            if hasattr(self.system, 'disk_controller'):
                disk = self.system.disk_controller
                self.disk_labels["Track"].config(text=f"{disk.current_track:02X} ({disk.current_track})")
                self.disk_labels["Direction"].config(text="Inward" if disk.direction == 1 else "Outward")
                self.disk_labels["Track 00"].config(text="Yes" if disk.track00 else "No")
                self.disk_labels["Ready"].config(text="Yes" if disk.ready else "No")
                self.disk_labels["Write Gate"].config(text="On" if disk.write_gate else "Off")

                if hasattr(disk, 'disk_image') and len(disk.disk_image) > disk.current_track:
                    sector_num = getattr(disk, 'target_sector', 0)
                    if sector_num < disk.sectors_per_track:
                        sector_data = disk.disk_image[disk.current_track][sector_num]
                        self.disk_hex_text.config(state='normal')
                        self.disk_hex_text.delete("1.0", tk.END)
                        
                        for i in range(0, 128, 16):
                            chunk = sector_data[i:i+16]
                            hex_str = " ".join(f"{b:02X}" for b in chunk)
                            ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
                            self.disk_hex_text.insert(tk.END, f"{i:04X}: {hex_str.ljust(47)} | {ascii_str}\n")
                            
                        self.disk_hex_text.config(state='disabled')

    def _draw_display(self):
        if not hasattr(self.system, 'display') or not self.display_canvas: return
        pixels = self.system.display.pixels
        for y in range(16):
            for x in range(16):
                color = "white" if pixels[y][x] else "black"
                self.display_canvas.itemconfig(self.display_rects[y][x], fill=color)

    def _update_highlight(self):
        pc = self.system.cpu.pc
        target_line = None
        if self.line_map:
            basic_line = None
            for addr in sorted(self.line_map.keys()):
                if addr <= pc: basic_line = self.line_map[addr]
            if basic_line is not None:
                content = self.code_editor.get("1.0", tk.END)
                for idx, line in enumerate(content.split('\n'), 1):
                    parts = line.strip().split()
                    if parts and parts[0] == str(basic_line):
                        target_line = idx
                        break
        else:
            target_line = pc + 1

        if target_line and target_line > 0:
            if self._last_highlighted_line != target_line:
                self.code_editor.tag_remove("current_line", "1.0", tk.END)
                self.code_editor.tag_add("current_line", f"{target_line}.0", f"{target_line}.end")
                self.code_editor.see(f"{target_line}.0")
                self._last_highlighted_line = target_line

    def step(self):
        try:
            if self.system.is_finished():
                self.stop()
                self.update_ui()
                self._update_highlight()
                return
            self.system.instruction()
            self.update_ui()
            self._update_highlight()
        except Exception as e:
            self.stop()
            messagebox.showerror("Execution error", str(e))

    def continue_run(self):
        self.status_var.set("Running...")
        self.is_running = True
        self._auto_step()

    def _auto_step(self):
        if self.is_running:
            bank = self.system.ram.banks[0]
            if bank['outputs'][3] == 0 and self.key_queue:
                bank['outputs'][3] = self.key_queue.pop(0)
                if hasattr(self.system.cpu, 'kbd_nibble_state'):
                    self.system.cpu.kbd_nibble_state = 0

            for _ in range(10):
                if self.system.is_finished():
                    self.stop()
                    self.update_ui()
                    self._update_highlight()
                    return
                self.system.instruction()
            self.update_ui()
            self._update_highlight()
            self.root.after(10, self._auto_step)

    def stop(self):
        if self.is_running:
            self.status_var.set("Stopped.")
        self.is_running = False
        self.system.terminate()

    def build_run(self):
        self.stop()
        source = self.code_editor.get("1.0", tk.END).strip()
        if not source: return

        try:
            self.line_map = {}
            self._last_highlighted_line = None
            
            lang = self._detect_language(source)
            self.status_var.set("Building...")
            
            main_obj = None
            msg = ""
            
            if lang == "basic":
                lexer = BasicLexer()
                tokens = lexer.tokenize(source)
                parser = BasicParser()
                ast = parser.parse(tokens)
                codegen = BasicCodeGen()
                asm_source = codegen.generate(ast)
                self.line_map = codegen.line_map
                asm_source = asm_source.replace("NZ, ", "NZ ").replace("Z, ", "Z ")
                assembler = Assembler()
                main_obj = assembler.assemble(asm_source)
                msg = f"BASIC compiled."
                
            else:
                assembler = Assembler()
                main_obj = assembler.assemble(source)
                msg = f"ASM compiled."

            object_modules = [main_obj]
            
            search_paths = [
                os.path.join('firmware', '*.asm'), 
                os.path.join('firmware', 'monitor', '*.asm'), 
                os.path.join('monitor', '*.asm'),       
            ]
            
            for path in search_paths:
                for dep in glob.glob(path):
                    dep_abs = os.path.abspath(dep)
                    if self.current_filepath and dep_abs == self.current_filepath:
                        continue
                    
                    try:
                        with open(dep, 'r', encoding='utf-8') as f:
                            dep_src = f.read()
                        
                        dep_src_clean = re.sub(r'ORG\s+0x[0-9A-Fa-f]+', '', dep_src)
                        dep_assembler = Assembler()
                        dep_obj = dep_assembler.assemble(dep_src_clean)
                        object_modules.append(dep_obj)
                    except Exception as e:
                        print(f"!!! Error in file {dep}: {e}")

            linker = Linker()
            rom_bytes = linker.link(object_modules)
            
            msg += f" Linked: {len(rom_bytes)} bytes."

            current_mode_str = self.display_mode_combo.get()
            if "TIA" in current_mode_str: current_mode = "TIA"
            elif "Teletype" in current_mode_str: current_mode = "Teletype"
            else: current_mode = "4003"

            saved_disk_image = None
            if hasattr(self.system, 'disk_controller'):
                saved_disk_image = self.system.disk_controller.disk_image

            self.system = System(rom_dump=[rom_bytes])
            self.system.cpu.ram = self.system.ram
            self.system.cpu.display = self.system.display
            self.system.cpu.sr4003 = self.system.sr4003
            self.system.cpu.tia = self.system.tia
            self.system.cpu.teletype = self.system.teletype 
            self.system.cpu.disk_controller = self.system.disk_controller
            self.system.cpu.display_mode = current_mode
            
            if saved_disk_image is not None:
                self.system.disk_controller.disk_image = saved_disk_image

            if hasattr(self.system, 'teletype'):
                self.system.teletype.clear()

            self.update_ui()
            self._update_highlight()
            self.status_var.set(f"{msg} Ready for debugging.")

        except Exception as e:
            self.status_var.set("Build failed.")
            messagebox.showerror("Build error", str(e))