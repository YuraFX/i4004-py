# User Guide

[← Previous: Introduction and Overview](./01-introduction-and-overview.md) | [Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md) | [Next: Assembly Programming Guide →](./03-assembly-programming-guide.md)

---

This document is a practical guide to the emulator interface. It assumes you have completed the setup steps in `README.md` and read the [Introduction and Overview](./01-introduction-and-overview.md), which explains the basic ideas behind the 4004 architecture. Here we focus on using the interface: opening files, building programs, running them, observing registers, and working with memory and disk images.

If you want to start writing code right away, the [Assembly Programming Guide](./03-assembly-programming-guide.md) and the [BASIC Programming Guide](./04-basic-programming-guide.md) are better starting points. This document covers the "control panel" of the emulator.

---

## 1. Window layout

The interface follows a classic IDE layout: the code editor is on the left, and the debugging panel is on the right. You can drag the divider between them to change the width of each panel. A status bar at the bottom displays messages about builds, file loading, and errors.

The right panel is divided into four tabs:

- **General** — CPU registers and debugging controls.
- **IO** — output ports, display mode selection, and virtual peripherals (the 4003 shift register, the screen, and the teletype).
- **Memory** — a dump of the selected RAM bank.
- **Disk** — the state of the virtual disk drive and disk image handling.

Switching tabs does not stop a running program — you can watch changes in real time.

---

## 2. Code editor (left panel)

The editor is more than a text field. It includes several features that make working with code easier.

**Line numbers.** Line numbers appear to the left of the code and stay in sync with scrolling. When you scroll through the code, the numbers move with it.

**Comment highlighting.** Everything after `//` is colored green. This helps you distinguish comments from code at a glance.

**Automatic language detection.** The emulator decides which language your program is written in. If the first non-empty line begins with a digit, it is BASIC. If it begins with a letter or a mnemonic, it is assembly. This determines which tool the build step uses. You do not need to select a language manually.

**Keyboard shortcuts.** The standard combinations `Ctrl+C`, `Ctrl+V`, `Ctrl+X`, `Ctrl+Z`, and `Ctrl+A` work. They are captured at the physical keycode level, so they work even when a non-Latin keyboard layout is active. This is intentional: you do not need to switch layouts every time you copy a code fragment.

**Context menu.** Right-click opens a menu with **Undo**, **Cut**, **Copy**, and **Paste**.

**Open and Save buttons.** **Open** loads a file with an `.asm`, `.bas`, or `.txt` extension. **Save** writes the current text; the default extension depends on the detected language (`.asm` for assembly, `.bas` for BASIC).

---

## 3. General tab: registers and debugging

The **General** tab is where you observe the CPU state. The execution controls are also located here.

**Execution controls.** The buttons at the top of the tab are **Build**, **Stop**, and **Run**.

- **Build** assembles the current code: the assembler turns text into machine bytes, and the linker places modules at addresses and resolves external references.
- **Stop** halts a running program.
- **Run** starts the program from its current state.

Below them are the step-debugging buttons: **Step over** and **Step into**. In the current version, both perform the same action — a single CPU step. The distinction will appear in a future release. One step executes exactly one 4004 instruction, which lets you watch register changes after each command.

**Miscellaneous block.** This block displays the key CPU registers:

| Register | Description |
|----------|-------------|
| `ACC` | Accumulator, a 4-bit value. |
| `CY` | Carry flag. |
| `Bank` | Selected register bank (0 or 1). |
| `PC` | Program counter, a 12-bit address. |
| `SP` | Stack pointer (0 to 2, because the stack is circular and three levels deep). |
| `S0`, `S1`, `S2` | The contents of the three stack cells. |

**Registers block.** Shows the 16 registers of the current bank as `RR00`–`RR15`. Values update after each step. Registers `R8`–`R15` are shared between banks, so their values do not change when you switch banks.

**Register pairs block.** Shows the same registers combined into pairs: `R0`–`R7`. Each pair is an 8-bit value assembled from two 4-bit registers. Pairs are used by instructions that need a full byte: `FIM`, `SRC`, `FIN`, and `JIN`.

---

## 4. IO tab: ports, display, and teletype

The **IO** tab is the busiest one. Here you control how the CPU communicates with the outside world.

**Output ports (RAM Output Ports).** The top of the tab shows the values written to ports via the `WMP` instruction. Each port corresponds to a virtual RAM "chip". For example, `Port 0` is chip 0 and `Port 1` is chip 1. Values update when a program executes `WMP`.

**Display mode selection.** The **Controller** dropdown lets you choose which output device to observe:

- **4003 Shift Register** — the default mode. Shows the 10-bit shift register and the 16×16 screen.
- **TIA (Television Interface Adaptor, buffered 16x16)** — emulates the Atari TIA video controller. Shows only the screen, without the shift register.
- **Teletype Model 33 ASR (110 baud, 20mA loop)** — teletype mode. Shows the "paper" on which text is printed.

When you switch modes, the emulator changes how it interprets writes to the ports. In teletype mode, data written to port 0 is treated as bits of a serial protocol. In 4003 mode, the same data is shifted into the register.

**4003 shift register.** In **4003** mode, a row of ten squares appears below the dropdown. Each square is one bit of the register. Green means `1`, gray means `0`. You can watch bits shift as instructions write to the ports.

**16×16 screen.** In **4003** and **TIA** modes, a monochrome screen is displayed. Each pixel is a 16×16 square on the canvas. White means the pixel is on, black means it is off. The screen updates in real time.

**Teletype.** In **Teletype** mode, a text area replaces the screen. This is the virtual "paper" of the teletype. Everything your program sends through the UART or directly through port 0 appears here. The text scrolls automatically so you can see the latest characters.

**Monitor selection.** The **Monitor** dropdown lets you choose **None** (normal mode) or **System Monitor**. When you select the monitor, the emulator automatically finds `monitor.asm` in the `firmware/` folder, loads it into the editor, builds it, and runs it. This is the fastest way to start working with the emulator's "operating system".

---

## 5. Memory tab: RAM dump

The **Memory** tab shows the contents of the selected RAM bank. The header line indicates which bank is active (`RAM BANK 0`, `RAM BANK 1`, and so on).

For each of the 16 registers, two rows of values are displayed:

- **Main memory (`main`)** — 16 cells of 4 bits each. These are the values manipulated by `WRM`, `RDM`, `ADM`, and `SBM`.
- **Status memory (`status`)** — 4 cells. These are accessible through `WR0`–`WR3` and `RD0`–`RD3`. In the real 4002, status registers held flags and peripheral state; in the emulator they are available to programs for their own use.

The dump refreshes when you switch tabs or after a step. If a program has modified memory, you see the new values.

---

## 6. Disk tab: the drive and disk images

The **Disk** tab controls the virtual Shugart SA 800-1 drive.

**Status block.** Shows the current state of the drive:

| Field | Description |
|-------|-------------|
| **Track** | Current track number (`00` to `76`). |
| **Direction** | Head movement direction: **Inward** (toward the center) or **Outward** (toward the edge). |
| **Track 00** | Whether the head is on track zero. This is the "limit switch" a program uses as a reference point. |
| **Ready** | Drive readiness. |
| **Write Gate** | Whether writing is enabled. |

**Load and Save buttons.** **Load .dsk Image** loads a disk image in IBM 3740 format (77 tracks, 26 sectors, 128 bytes per sector). **Save .dsk Image** saves the current disk state to a file. You can load an image, work with it, and save the result.

**Sector dump.** The bottom of the tab shows a hexadecimal dump of the current sector. Rows are split into 16 bytes; an ASCII rendering appears on the right. This dump helps you understand what a program reads from or writes to the disk.

---

## 7. Execution mechanics: Build, Run, and Stop

Understanding what happens when you press a button helps you avoid confusion.

**Build.** The build runs in several stages. First, the emulator detects the language. If it is BASIC, the lexer → parser → code generator chain turns the BASIC program into assembly text. Then the assembler converts the text into machine bytes. After that, the linker scans the `firmware/` folder for other `.asm` files: if the current program references external symbols (for example, monitor subroutines), the linker automatically includes those files and patches the addresses. The result is a single ROM image that is loaded into the emulator.

**Run.** Starts cyclic execution. The emulator does not execute one instruction at a time; it executes a batch of ten instructions, then refreshes the interface and waits for the next tick. This is a trade-off: on the one hand you see changes in real time, on the other hand the interface does not freeze on slow programs. If the program finishes (`HLT` executes or the program counter leaves the ROM), execution stops automatically.

**Stop.** Halts execution immediately. After that you can inspect registers and memory.

**Step over / Step into.** Execute exactly one instruction. This is useful when you want to see what a specific command does, or when a program is stuck in a loop and you want to find the cause.

**Input queue.** When you press a key (and the focus is not in the code editor), the character goes into a queue. A program reading port 3 takes characters from this queue one at a time. This prevents lost keystrokes when a program does not read the port quickly enough. Arrow keys are written to port 3 as codes `1`, `2`, `3`, and `4` — useful for games and navigation.

> [!NOTE]
> Keystrokes are ignored while the focus is inside the code editor. This lets you type code without accidentally feeding characters to a running program.

---

## 8. Working with the monitor

The monitor is the emulator's "operating system", written in 4004 assembly. It supports several commands that you enter from the teletype.

**Starting the monitor.** Select **System Monitor** in the **Monitor** dropdown on the **IO** tab. The emulator loads `monitor.asm`, builds it, and runs it. A welcome message and a `>` prompt appear on the teletype.

**Commands.** At the prompt, enter one of the following commands:

| Command | Name | Purpose |
|---------|------|---------|
| `D` | Dump | Print 16 consecutive nibbles from memory, starting at the specified address. |
| `S` | Substitute / Edit | Change the value of a memory cell at the specified address. |
| `X` | Examine | Print the contents of all 16 CPU registers in hexadecimal. |
| `G` | Go | Transfer control to the specified address. Used to start a loaded program. |
| `R` | Read | Read a sector from disk into RAM. |
| `W` | Write | Write RAM contents to a disk sector. |

For commands that need an address (`D`, `S`, `G`), the monitor asks for two hexadecimal characters. For `R` and `W`, the monitor uses the current track and sector 0. See the [System Monitor and Disk Operations guide](./08-system-monitor-and-disk-operations.md) for details.

---

## 9. Keyboard shortcuts and small conveniences

Here is a short list of things that save time.

- `Ctrl+C`, `Ctrl+V`, `Ctrl+X`, `Ctrl+Z`, `Ctrl+A` — work in the editor even with a non-Latin keyboard layout active.
- **Arrow keys** — written to port 3 as codes `1`–`4` when focus is not in the editor. This lets you control programs that read port 3.
- **Regular keys** — enter the input queue and are read by programs through port 3. Character case is automatically converted to uppercase.
- **Dragging the divider** between the editor and the debug panel changes the panel widths.
- **Right-click in the editor** opens the context menu with editing commands.

---

## 10. When something goes wrong

**The program does not start.** Verify that you pressed **Build** and then **Run**. If the build failed, the status bar or a dialog box reports the error. The most common cause is a typo in a mnemonic or an undefined label.

**Nothing appears on the screen.** Make sure the correct display mode is selected. If a program prints text through the UART, you need **Teletype** mode. If a program draws pixels through port 2, you need **4003** or **TIA** mode. Check the **General** tab: if `PC` has stopped changing, the program may have finished or become stuck.

**The monitor does not start.** Make sure `monitor.asm` is in the `firmware/` folder (or `firmware/monitor/`). If the file is elsewhere, the emulator will not find it automatically.

**The disk image does not load.** Verify that the image has the correct size: 77 × 26 × 128 = 256,256 bytes. Files of other sizes will not load. Also confirm that the program performs the correct sequence of `DISK_INIT` → `DISK_SEEK` → `DISK_READ_SECTOR`; the monitor does this automatically.

---

## Conclusion

The emulator interface is designed to be transparent glass: you press buttons and immediately see what happens inside the CPU and its peripherals. Do not be afraid to experiment — **Stop** is always available, and the state can be rebuilt from scratch. If you want to understand the individual parts in more depth (the assembler, the linker, the monitor, the disk drive), see the corresponding documents:

- [Assembly Programming Guide](./03-assembly-programming-guide.md) — if you want to write assembly.
- [BASIC Programming Guide](./04-basic-programming-guide.md) — if you want to write BASIC.
- [Toolchain Reference](./05-toolchain-reference.md) — assembler and linker reference.
- [Architecture and Emulation Reference](./06-architecture-and-emulation-reference.md) — CPU internals and the instruction cycle.
- [Peripherals and I/O Reference](./07-peripherals-and-io-reference.md) — UART, disk drive, and video peripherals.
- [System Monitor and Disk Operations](./08-system-monitor-and-disk-operations.md) — monitor commands and disk operations.

---

[← Previous: Introduction and Overview](./01-introduction-and-overview.md) | [Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md) | [Next: Assembly Programming Guide →](./03-assembly-programming-guide.md)
