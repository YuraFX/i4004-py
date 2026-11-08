# Peripherals and I/O Reference

[← Previous: Architecture and Emulation Reference](./06-architecture-and-emulation-reference.md) | [Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md) | [Next: System Monitor and Disk Operations →](./08-system-monitor-and-disk-operations.md)

---

This document is for readers who want to understand how the emulator reproduces external devices: memory, UART, disk drive, video chips, and teletype. It does not teach you to write programs (for that, see the [Assembly Programming Guide](./03-assembly-programming-guide.md) and the [BASIC Programming Guide](./04-basic-programming-guide.md)) and it does not describe the CPU core (that is in the [Architecture and Emulation Reference](./06-architecture-and-emulation-reference.md)). Here we focus on how the 4-bit CPU talks to an 8-bit world and which devices are connected to its ports.

The document is organized as a reference: sections are grouped by device, each with the operating principle, data structures, and implementation details. If you want to look up how a specific command works or which port serves which device, open the relevant section.

---

## 1. The core problem: 4 bits against 8 bits

The Intel 4004 is a 4-bit processor. Its accumulator holds 4 bits, its registers hold 4 bits, and its data bus is 4 bits wide. But almost every peripheral we want to emulate works with 8-bit values: ASCII characters, disk bytes, screen pixels.

There are two ways to solve this.

**Nibble transmission.** An 8-bit value is split into two 4-bit halves (nibbles) that travel one after the other. Usually the low nibble goes first, then the high nibble. This is how the UART, the keyboard, and the disk drive work.

**Dedicated chips.** Some devices (for example, the 4003 shift register) take over part of the work: the CPU sends data one bit at a time, and the chip assembles the bits into a parallel value. This lets the design bypass the 4-bit bus limit.

Understanding these two mechanisms is the key to understanding the entire peripheral layer.

---

## 2. Ports and chips: how the CPU addresses devices

The 4004 has no dedicated "read from disk" or "print to screen" instructions. Instead, it provides `WRM` (write), `RDM` (read), and `WMP` (write to port), which operate on **memory registers**. Each register belongs to a particular "chip", and different chips serve different devices.

### Chip partitioning

In the emulator, the 16 RAM registers are split into 4 chips of 4 registers each:

| Chip | Registers | Purpose in the emulator |
|------|-----------|------------------------|
| Chip 0 | `R0`–`R3` | 4003 shift register, teletype (in direct bit-banging mode) |
| Chip 1 | `R4`–`R7` | 4003 shift register (continued) |
| Chip 2 | `R8`–`R11` | Display (pixels) |
| Chip 3 | `R12`–`R15` | UART, keyboard |

This partition is not part of the 4004 architecture — it is a choice made in the emulator so that different devices do not conflict over the same registers. On a real 4004, each 4002 chip had its own ports, and the engineer decided which chip to wire to which device.

### Selecting register and cell: SRC

Before reading or writing, a program must specify which register and which cell it wants to work with. This is done with the `SRC` instruction:

```asm
FIM P0, 0x40    // Load pair P0 (R0:R1) with 0x40
SRC P0          // Select register 4, cell 0
```

After that, `WRM` or `RDM` operates on register 4, cell 0. `SRC` is the "key" that opens the right door.

### Output handler

When a program executes `WMP` (write to port), the emulator calls `output_handler` — a function that decides what to do with the data. In `System.__init__()` this handler is connected to `RAM`, and `cpu.py` then decides which device the write belongs to:

- If `chip == 3` and `reg == 12`, it is the UART (data write).
- If `chip == 3` and `reg == 14`, it is the UART (control register write).
- If `chip == 4` and `reg == 4`, it is the disk drive (commands).
- If `chip == 4` and `reg == 5`, it is the disk drive (data).
- If `chip == 2`, it is the display (pixels).
- If `chip == 0` or `chip == 1`, it is the 4003 shift register.
- If `chip == 0` and the mode is Teletype, it is the teletype (direct bit-banging).

This scheme lets the emulator support several devices at once without mixing their data.

---

## 3. RAM as a peripheral: the 4002 chip

On a real 4004, data memory was not a separate chip but a set of 4002 chips. Each 4002 held 40 bytes of memory (80 nibbles) and a built-in 4-bit output port. The `ram.py` module reproduces this structure.

### Bank structure

Each RAM bank is a dictionary with four keys:

| Key | Contents |
|-----|----------|
| `registers` | List of 16 registers. Each register is a dict with `main` (16 cells of 4 bits) and `status` (4 cells). |
| `outputs` | List of 8 output ports. A real 4002 had 4 ports; the emulator extends this to 8 to connect additional devices. |
| `selected_register` | Selected register number (set via `SRC`). |
| `selected_character` | Selected cell number (set via `SRC`). |

### Main and status memory

**Main memory (`main`)** is 16 cells of 4 bits. Instructions `WRM`, `RDM`, `ADM`, and `SBM` work with it. These are the values a program stores and processes.

**Status memory (`status`)** is 4 cells. They are accessible through `WR0`–`WR3` and `RD0`–`RD3`. On a real 4002, status registers held flags and peripheral state; in the emulator they are available to programs for their own use.

### Output ports

`outputs` is an array of 8 values. When a program executes `WMP`, the value is written to `outputs[reg]`, where `reg` is the selected register number. This lets a program "expose" data on ports that peripherals then read.

### The _execute method

The `_execute()` method is called from `tick()` and performs the operation on the selected bank. It handles all memory-access instructions:

| Instruction | What it does |
|-------------|--------------|
| `RDM` | Reads main memory and places the value on lines D0–D3. |
| `RD0`–`RD3` | Reads a status register and places the value on lines D0–D3. |
| `WRM` | Writes the value on lines D0–D3 into main memory. |
| `WMP` | Writes the value to an output port and invokes `output_handler`. |
| `WR0`–`WR3` | Writes the value into a status register. |
| `ADM` | Adds the accumulator to the memory value. |
| `SBM` | Subtracts the memory value from the accumulator. |

### Clock cycle

The `tick()` method emulates the 8 phases of a machine cycle (A1, A2, A3, M1, M2, X1, X2). At phase M2 memory records the operation code, and at phase X2 it executes it. This reproduces real chip behavior, where command and data travel in different clock cycles.

---

## 4. UART AY-5-1013: serial communication

UART (Universal Asynchronous Receiver/Transmitter) converts parallel data (bytes) into a serial bit stream and back. The emulator uses a model of the General Instrument AY-5-1013 — one of the first single-chip UARTs, introduced around 1971.

### Why a UART is needed

The 4004 could not provide software bit-banging at 110 baud without data loss: the CPU is too slow and the teletype is too picky. The UART takes over all timing routine, freeing the CPU for computation. The CPU simply writes a byte to the UART register and forgets about it; the UART itself "fires" bits at the right intervals.

### UART registers

The UART communicates with the CPU through four registers of chip 3:

| Register | Purpose |
|----------|---------|
| `R12` | Transmit data (write) or received data (read). |
| `R13` | Status (read-only). |
| `R14` | Control register (write). |
| `R15` | Unused (in the current version). |

### Control register

The value written to `R14` determines the frame format:

| Bit | Meaning |
|-----|---------|
| 0–1 | Data bits: `00` = 5, `01` = 6, `10` = 7, `11` = 8. |
| 2 | Stop bits: `0` = 1, `1` = 2. |
| 3 | Parity: `0` = none, `1` = enabled. |

### Status register

The value read from `R13` contains flags:

| Bit | Flag | Meaning |
|-----|------|---------|
| 0 | `TBMT` | Transmit buffer empty (a new byte can be written). |
| 1 | `DAV` | Data available (a received byte can be read). |
| 2 | `OR` | Overrun (data arrived before the previous byte was read). |
| 3 | `FE` | Framing error (no stop bit detected). |

### Transmission: the tx_process state machine

The `tx_process()` method implements a state machine that "fires" bits into the teletype:

| State | What happens |
|-------|--------------|
| `IDLE` | Wait until the CPU writes a byte to `tx_buffer` and clears `TBMT`. |
| `PREP_TIME` | One preparation tick. |
| `START_BIT` | Send `0` (start bit). |
| `PROCESSING` | Shift out data bits (LSB first). |
| `FIRST_STOP_BIT` | Send `1` (stop bit) and restore the `TBMT` flag. |

After transmission completes, the UART returns to `IDLE` and waits for the next byte.

### Reception: the rx_process state machine

The `rx_process()` method works in the opposite direction:

| State | What happens |
|-------|--------------|
| `IDLE` | Wait for the line to fall to `0` (start bit). |
| `DATA` | Read data bits, assemble them into a byte. |
| `STOP` | Check the stop bit. If `1`, data is ready and `DAV` is set. If `0`, a framing error occurs. |

### Byte assembly and disassembly

Because the 4004 is 4-bit, the UART cannot transmit or receive a byte in one operation. The `write_data()` and `read_data()` methods act as "assemblers":

- **On write:** the first `write_data()` call stores the low nibble in `data_in_low`; the second combines it with the high nibble and sends it to `tx_buffer`.
- **On read:** the first `read_data()` call returns the low nibble of the received byte; the second returns the high nibble and clears `DAV`.

### Synchronization with the CPU

The UART runs at its own frequency, independent of the 4004. The emulator models this via the `tick()` method, which is called from `System.instruction()` several times per CPU step (usually 10). This compensates for the frequency gap: while the CPU executes one instruction, the UART processes several bits.

> [!TIP]
> The UART emits characters at 110 baud, which is roughly 10 characters per second. If a program produces faster output, characters may be lost. The emulator does not model back-pressure; it relies on the program checking the `TBMT` flag before writing.

---

## 5. Disk drive: IBM 3740 format and the Shugart SA 800-1

The disk drive is one of the most complex devices in the emulator. It consists of two parts: `disk_image.py` (the logical disk structure) and `shugart.py` (the mechanics and control).

### disk_image.py: a digital disk model

The `DiskImage` class is the "paper" we write on. It stores data in IBM 3740 format.

**Format parameters:**

| Parameter | Value | Description |
|-----------|-------|-------------|
| `tracks` | 77 | Tracks (concentric circles). Track 0 is outermost, 76 is innermost. |
| `sectors_per_track` | 26 | Sectors per track. |
| `sector_size` | 128 | Bytes per sector. |
| `total_size` | 256,256 | Total image size (77 × 26 × 128). |

**Data structure.** Data is stored in a single flat `bytearray` of 256,256 bytes. The `_offset(track, sector, skew)` method computes the position in this array from track and sector numbers.

**Skew table.** This is the most interesting part of the code. CP/M 1.4/2.2 used software interleaving: physical sectors were read out of order (0, 6, 12, 18, 24, 4, 10, ...) instead of sequentially (0, 1, 2, ...). Why? A disk rotates at 360 RPM (one revolution every 166 ms). When the controller reads sector 0, the CPU needs time to process 128 bytes. If the next physical sector were sector 1, the disk would "move on" and the controller would miss it. The solution is to read with a skip, so the CPU has time to process data.

**Methods:**

| Method | Purpose |
|--------|---------|
| `load(path)` | Load an image from a file (verifies size). |
| `save(path)` | Save an image to a file. |
| `read_sector(track, sector, skew)` | Return the 128 bytes of a sector. |
| `write_sector(track, sector, data, skew)` | Write 128 bytes into a sector. |
| `clear()` | Clear the image (all zeros). |

### shugart.py: the virtual controller

If `disk_image.py` is paper, then `shugart.py` is the printing press that moves the head and presses it against the paper. The 4004 could not drive the disk directly (it lacked the speed), so in reality a separate controller stood beside it. The `ShugartSA800` class emulates that controller in software.

**Mechanical parameters:**

| Parameter | Value | Description |
|-----------|-------|-------------|
| `rpm` | 360 | Rotation speed, RPM. |
| `step_time_ms` | 8 | Head step time, ms. |
| `tracks` | 77 | Number of tracks. |
| `sectors_per_track` | 26 | Sectors per track. |
| `bytes_per_sector` | 128 | Bytes per sector. |

**Controller state:**

| Field | Purpose |
|-------|---------|
| `current_track` | Current track (0–76). |
| `direction` | Head direction: `1` — inward, `0` — outward. |
| `head_loaded` | Head pressed against the disk. |
| `write_gate` | Write enable. |
| `selected` | Device selected. |
| `track00` | "Head on track 0" flag. |
| `ready` | Drive ready. |

**Control methods:**

| Method | Purpose |
|--------|---------|
| `step()` | Move the head one track in the current direction. |
| `set_direction(inward)` | Set the direction (`True` — inward). |
| `select(enable)` | Select or deselect the device. |
| `set_write_gate(enable)` | Enable or disable write permission. |
| `read_sector(sector_num)` | Return 128 bytes from the current track. |
| `write_sector(sector_num, data)` | Write 128 bytes to the current track. |

### How the CPU talks to the drive

The CPU knows nothing about Python classes. It communicates with the drive through ports:

1. An assembly program sends a command to port 4 (for example, `0x1` — STEP).
2. `cpu.py` catches the value and calls `self.disk_controller.step()`.
3. `shugart.py` moves the head (`current_track += 1`).
4. If the program sends a READ command (`0x8`), `cpu.py` calls `read_sector()`, and data flows into port 5, where the CPU reads it nibble by nibble.

**Drive commands:**

| Code | Command | Action |
|------|---------|--------|
| `0x1` | STEP | Move the head one track. |
| `0x2` | INWARD | Move toward the center. |
| `0x3` | OUTWARD | Move toward the edge. |
| `0x4` | SELECT | Select the device. |
| `0x5` | DESELECT | Deselect the device. |
| `0x6` | WRITE GATE ON | Enable writing. |
| `0x7` | WRITE GATE OFF | Disable writing. |
| `0x8` | READ | Read a sector. |
| `0x9` | WRITE | Write a sector. |

### Reading and writing a sector

**Reading.** When a program sends a READ command, `cpu.py` calls `read_sector(sector_num)` and stores the data in the controller buffer. The program then reads the data nibble by nibble through port 5. Each `RDM` call returns the low or high nibble of the current byte, depending on the state of `read_nibble_state`.

**Writing.** When a program sends a WRITE command, `cpu.py` assembles bytes from nibbles arriving at port 5. Each `WMP` call adds a nibble to the buffer; when two nibbles accumulate, they are joined into a byte and appended to `write_buffer`. When the buffer fills (128 bytes), `write_sector()` is called and the data is written to the disk.

---

## 6. Video: four ways to draw an image

The emulator has four video devices, each working differently. The mode is selected via the dropdown on the **IO** tab.

### display.py: abstract framebuffer

The `Display` class is not an emulation of a specific chip but a simple framebuffer. A 16×16 matrix where `0` means the pixel is off and `1` means it is on.

**Methods:**

| Method | Purpose |
|--------|---------|
| `set_pixel(x, y, value)` | Turn a pixel on or off. Bounds-checked. |
| `clear()` | Clear the entire screen. |

**Why it exists.** The real 4004 had no video output. The screen is an overlay that visualizes the output of `sr4003.py` or `tia.py`. It is a utility class for the interface.

### sr4003.py: Intel 4003 shift register

The Intel 4003 is a 10-bit static shift register with serial input and parallel output. In the MCS-4 system it was used as a port expander: the CPU could not drive many devices directly, so data was shifted into the 4003 one bit at a time and then read out in parallel.

**Structure:**

| Field | Purpose |
|-------|---------|
| `bits` | Array of 10 bits. Index 0 is the input (LSB), index 9 is the output (MSB). |
| `enable` | `1` — outputs disabled (High-Z), `0` — outputs active. |

**Methods:**

| Method | Purpose |
|--------|---------|
| `set_data(bit)` | Set the bit at the input. |
| `clock_pulse()` | Shift all bits to the right (toward the high end) and feed `data_in` into the input. |
| `set_enable(value)` | Control the output buffers. |
| `get_parallel_out()` | Return the 10-bit value if outputs are active. |

**How it works.** The CPU writes bits to port 0 or port 1, and each bit is shifted into the register. Once 10 bits accumulate, they can be read in parallel. This is a simplified but functionally correct model.

### teletype.py: Teletype Model 33 ASR

The Teletype Model 33 ASR is an electromechanical terminal from the 1960s. It ran at 110 baud (about 10 characters per second), used a 20 mA current loop and ASCII encoding. Transmission used frames: start bit, 7 or 8 data bits, optional parity bit, and one or two stop bits.

**Structure:**

| Field | Purpose |
|-------|---------|
| `state` | Current state of the state machine. |
| `bit_count` | Number of received bits. |
| `current_byte` | Byte being assembled. |
| `parity_bit` | Parity bit. |
| `buffer` | Buffer of received characters. |
| `tx_buffer` | Buffer for transmission. |

**Reception: receive_bit**

The `receive_bit()` method implements a state machine:

| State | What happens |
|-------|--------------|
| `0` | Wait for the start bit (`0`). |
| `1` | Receive data bits (7 or 8, depending on parity). |
| `2` | Check stop bits. |

When a frame is complete, `_finish_char()` is called; it checks parity and adds the character to the buffer.

**Transmission: type_char**

The `type_char()` method generates a bit sequence for sending a character: start bit, data bits (LSB first), parity bit (if enabled), and stop bits. These bits are then read by `get_tx_bit()`.

**Simplifications.** A real teletype had no buffer: the CPU had to wait while the mechanics "chewed" each character. The emulator ignores timing entirely (`time_us` is not used) so the emulator runs fast. This is a conscious simplification that does not affect program logic.

### tia.py: Atari TIA (Television Interface Adaptor)

The TIA is a chip from the Atari 2600 (1977). Its key feature: no framebuffer. The console had only 128 bytes of RAM, so a program had to write to TIA registers in sync with the TV's electron beam — a process called "racing the beam".

**TIA registers:**

| Register | Purpose |
|----------|---------|
| `0`–`2` | Playfield (background). |
| `3`, `4` | Sprites (`grp0`, `grp1`). |
| `5`, `6` | Sprite X positions. |
| `7`, `8` | Sprite Y positions. |
| `9` | Redraw flag (`dirty`). |
| `10`, `11` | Sprite heights. |
| `12`, `13` | Ball position (`ball_x`, `ball_y`). |
| `14` | Ball enable. |
| `15` | Set a pixel in video memory (X, then Y). |

**The render method.** Redraws the frame based on current register values. First the playfield (`pf`) is drawn, then sprites (`grp0`, `grp1`) and the ball (`ball`) are overlaid.

**Why buffering.** The real TIA had no buffer — a program had to change registers while the beam was drawing. The emulator uses a buffered model: a program writes registers, then `render()` draws the whole frame. This is the only viable path for a 4004, which cannot "race the beam" at 740 kHz.

---

## 7. Keyboard: how a 4-bit CPU reads 8-bit ASCII

The keyboard is another example of nibble transmission. When the user presses a key, the interface writes the character's ASCII code to port 3 (register 15). The CPU reads that code in pieces.

### How it works

1. The user presses a key. The interface (`ui.py`) catches the event and writes the ASCII code to `outputs[3]` of bank 0.
2. A program executes `RDM` for register 15. The emulator checks `kbd_nibble_state`:
   - If `0`, it returns the low nibble and switches state to `1`.
   - If `1`, it returns the high nibble and resets state to `0`.
3. The program assembles the full byte from the two nibbles.

### Input queue

To prevent programs from losing keystrokes (for example, if a program does not read the port in time), the interface uses a `key_queue`. When the CPU reads port 3, it first takes a character from the queue and then clears it, freeing the port for the next one.

### Arrow keys

Arrow keys are written to port 3 as codes `1`, `2`, `3`, and `4`. This is convenient for games and navigation. The interface distinguishes arrows from regular keys: for arrows it writes the code directly; for others it appends the ASCII code to the queue.

---

## 8. How everything connects in System

The `System` class is the emulator's "motherboard". It creates all components and wires them together.

### Initialization

```python
self.pins = CPUPins()
self.rom = ROM(self.pins)
self.ram = RAM(self.pins, ram_dump, ram_output_handler)
self.display = Display()
self.sr4003 = ShiftRegister4003()
self.tia = TIA16x16()
self.teletype = Teletype(...)
self.disk_controller = ShugartSA800()
self.uart = AY51013UART(self.teletype)
self.cpu = CPU(self.pins)
self.cpu.rom = self.rom
self.cpu.ram = self.ram
self.cpu.display = self.display
self.cpu.sr4003 = self.sr4003
self.cpu.tia = self.tia
self.cpu.teletype = self.teletype
self.cpu.disk_controller = self.disk_controller
self.cpu.uart = self.uart
```

Each component receives a reference to `pins` (the shared bus) and to other components it must interact with. This mirrors how an engineer inserts chips into sockets and connects them with wires.

### Display mode selection

The `cpu.display_mode` field determines how writes to the ports are interpreted:

| Mode | What happens on `WMP` |
|------|------------------------|
| `4003` | Bits are shifted into the shift register; pixels are drawn on the screen. |
| `TIA` | Values are written to TIA registers; the screen is redrawn. |
| `Teletype` | The bit is sent to the teletype (direct bit-banging). |

### Completion check

The system is considered finished when:

1. Someone called `terminate()`.
2. `pc` left the ROM range.
3. The CPU executed `HLT`.

This prevents infinite loops and lets the interface stop execution cleanly.

---

## 9. Accuracy and simplifications

Here is a summary of what is emulated accurately and what is simplified. This will help you understand where the emulator's behavior may differ from real hardware.

### Emulated accurately

- **IBM 3740 format.** 77 tracks, 26 sectors, 128 bytes — all match the standard.
- **Skew table.** CP/M 1.4/2.2 used exactly this sequence.
- **Drive mechanics.** Head stepping, direction, `Track00`, `Write Gate` — all behave like a real Shugart SA 800-1.
- **UART protocol.** Frame format, flags, nibble transmission — all match the AY-5-1013.
- **4003 shift register.** 10 bits, serial input, parallel output.
- **Teletype protocol.** Start bit, data, parity, stop bits.

### Simplified

- **Timing.** Real hardware devices run at different frequencies; in the emulator they are synchronized through `System.instruction()`.
- **Physical delays.** Head step time, character print time, bit transmission time — all ignored for speed.
- **TIA without "racing the beam".** A real TIA required the program to change registers while the beam was drawing; the emulator uses buffering.
- **Keyboard without debounce.** Real hardware had key bounce; in the emulator every press is one event.

### What this means for you

If you write a program that depends on precise timing (for example, bit-banging on the teletype), the emulator may behave differently from real hardware. But for most programs (memory access, disk operations, text output), the emulator produces the correct result.

---

## 10. Extending the peripheral layer

If you want to add a new device (for example, a printer or a second drive), here is what to do.

### Adding a device

1. **Create a class.** It must have a `write_register(reg, value)` method (for writes) and/or `read_register(reg)` (for reads).
2. **Choose a port.** Decide which chip and register will serve the device. Make sure the port is not already used by another device.
3. **Wire it in cpu.py.** In the `WMP` or `RDM` method, add a branch for your device.
4. **Wire it in System.** Create an instance of the device in `System.__init__()` and pass it to `cpu`.
5. **Update the UI.** Add a tab or a control for the new device.

### Example: a second drive

If you want to add a second drive, create a second `ShugartSA800` instance, connect it to another chip (for example, chip 5), and add commands to switch between drives. In `cpu.py`, check which chip the write is for and call the appropriate controller.

---

## Conclusion

This reference covers the emulator's entire peripheral layer: memory, UART, disk drive, video, teletype, and keyboard. If you want to understand how the CPU and instruction cycle work, see the [Architecture and Emulation Reference](./06-architecture-and-emulation-reference.md). If you are interested in the monitor and disk operations, see the [System Monitor and Disk Operations guide](./08-system-monitor-and-disk-operations.md).

Peripherals are what make the emulator tangible. You can watch pixels light up, text print, and the disk head move across tracks. Understanding how this works under the hood helps both when writing programs and when reading the emulator's source code.

---

[← Previous: Architecture and Emulation Reference](./06-architecture-and-emulation-reference.md) | [Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md) | [Next: System Monitor and Disk Operations →](./08-system-monitor-and-disk-operations.md)
