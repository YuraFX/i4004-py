# System Monitor and Disk Operations

[← Previous: Peripherals and I/O Reference](./07-peripherals-and-io-reference.md) | [Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md)

---

This guide is a practical walkthrough of the monitor built into the emulator and of working with the virtual disk drive. The monitor is a small "operating system" written in 4004 assembly: it prints a prompt, accepts commands, shows memory and registers, and loads and saves disk sectors.

The document assumes you are already familiar with the basics of 4004 assembly (otherwise read the [Assembly Programming Guide](./03-assembly-programming-guide.md)) and know how the emulator interface works (see the [User Guide](./02-user-guide.md)). If you want to understand the disk drive and IBM 3740 format in depth, see the [Peripherals and I/O Reference](./07-peripherals-and-io-reference.md).

---

## 1. What the monitor is and why it exists

The monitor is a program that loads into the emulator's memory and provides a simple command-line interface. You type commands on the teletype, the monitor executes them and prints the result. This resembles the first monitors of the 1970s: no graphics, only text and hexadecimal digits.

The monitor serves several purposes:

- **Memory inspection.** The `D` (Dump) command shows memory contents at a given address.
- **Memory modification.** The `S` (Substitute) command writes a new value to a memory cell.
- **Register inspection.** The `X` (Examine) command prints the contents of all 16 CPU registers.
- **Program launch.** The `G` (Go) command transfers control to a given address.
- **Disk operations.** The `R` (Read) and `W` (Write) commands read and write disk sectors.

The monitor is not a full operating system: it has no file system, no directories, and no input validation beyond the basics. But for learning and for running small programs, it is sufficient.

---

## 2. Starting the monitor

You can start the monitor in two ways.

**Option 1: from the dropdown.** On the **IO** tab in the right panel, find the **Monitor** dropdown and select **System Monitor**. The emulator automatically finds `monitor.asm` in the `firmware/` folder, loads it into the editor, builds it, and runs it. A welcome message and a `>` prompt appear on the teletype within a moment.

**Option 2: manually.** Open `monitor.asm` via the **Open** button, click **Build**, then **Run**. Make sure **Teletype Model 33 ASR** is selected on the **IO** tab — otherwise you will not see the text.

After starting, the monitor prints `MCS-4 SYSTEM MONITOR` and the prompt `> `. It now waits for a command.

> [!NOTE]
> The monitor expects commands in uppercase. The emulator interface automatically converts lowercase letters to uppercase, so you can type `d` or `D` and get the same result. If you connect the monitor through another terminal, use uppercase letters.

---

## 3. Monitor commands

The monitor supports six commands. Each command is a single letter that may be followed by parameters.

| Command | Name | Purpose |
|---------|------|---------|
| `D` | Dump | Print 16 nibbles from memory at the specified address. |
| `S` | Substitute | Write a new nibble to memory at the specified address. |
| `X` | Examine | Print the contents of all registers. |
| `G` | Go | Transfer control to the specified address. |
| `R` | Read | Read a disk sector into memory. |
| `W` | Write | Write memory contents to a disk sector. |

If you enter an unknown command, the monitor prints `*` and returns to the prompt.

### 3.1 D — Dump (memory dump)

**Syntax:** `D <address>`

**Example:** `D 00`

The monitor asks for two hexadecimal digits of the address. Once entered, it prints 16 consecutive nibbles starting at the specified address. Each nibble appears as one hexadecimal digit separated by spaces. The line ends with carriage return and line feed.

**What happens inside.** The monitor stores the address in pair `R6:R7` (pair `P3`). It then loops: executes `SRC P3`, `RDM` (reads a nibble from memory), and `MON_PUT_HEX_NIB` (converts the nibble to ASCII and prints it). After each nibble the address increments by 1 with a carry from `R7` to `R6`. The loop repeats 16 times (counter in `R8`).

**Example output:**

```text
> D 00
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
```

This means memory from `0x00` to `0x0F` is filled with zeros.

### 3.2 S — Substitute (edit memory)

**Syntax:** `S <address>`, then one hexadecimal digit.

**Example:** `S 10`, then `A`.

The monitor asks for an address, then waits for one hexadecimal digit. Once entered, it writes the nibble to memory at the specified address, prints the value back as confirmation, and returns to the prompt.

**What happens inside.** The monitor uses the same address-parsing routine as `D`. It then reads a character from the teletype, converts it to a number (subtracts `'0'` for digits `0`–`9`; subtracts `'A'` and adds 10 for letters `A`–`F`), and writes it to memory via `SRC P3` and `WRM`. After the write it prints the value back so you can confirm the operation.

> [!WARNING]
> `S` writes only one nibble at a time. To write a byte, call `S` twice.

### 3.3 X — Examine (register inspection)

**Syntax:** `X`

**Example:** `X`

The monitor prints the contents of all 16 registers (`R0`–`R15`) in hexadecimal. Registers are printed four per line, four lines total.

**What happens inside.** The monitor loads each register into the accumulator (`LD R0`, `LD R1`, ...), calls `MON_PUT_HEX_NIB` to print it, and prints `CRLF` after every four registers.

**Example output:**

```text
> X
0 0 0 0
0 0 0 0
0 0 0 0
0 0 0 0
```

This means all registers are zero.

### 3.4 G — Go (launch a program)

**Syntax:** `G <address>`

**Example:** `G 00`

The monitor asks for an address and transfers control there. It does not return to the prompt unless the program returns through `BBL` or jumps back to the monitor.

**What happens inside.** The monitor parses the address, stores it in `R6:R7`, then copies `R6` into `R0` and `R7` into `R1`. Pair `R0:R1` is `P0`. It then executes `JIN P0` — an indirect jump to the address stored in the pair. This is the standard way to transfer control on the 4004.

> [!WARNING]
> If a program does not return control, the monitor cannot continue. To get back, press **Stop** and then **Run** again — the monitor restarts from the beginning.

### 3.5 R — Read (read a sector)

**Syntax:** `R`

**Example:** `R`

The monitor reads sector 0 from the current track and loads 128 bytes into memory starting at `0x00`. When finished, it prints `CRLF` and returns to the prompt.

**What happens inside.** The monitor performs the following sequence:

1. Selects the drive (`SELECT`).
2. Disables writing (`WRITE GATE OFF`).
3. Homes the head to track 0 (`HOME`).
4. Sets sector number 0 in the data port.
5. Sends the `READ` command.
6. Loops 8 × 16 = 128 times, reading two nibbles from the data port, joining them into a byte, and writing it to memory.

The destination address lives in pair `R6:R7` (initially `0x00`). After each write the address increments with carry propagation.

> [!NOTE]
> The monitor always reads sector 0 of the current track. If you need a different sector or track, use `disk_driver.asm` in your own program (see section 5).

### 3.6 W — Write (write a sector)

**Syntax:** `W`

**Example:** `W`

The monitor writes 128 bytes from memory (starting at `0x00`) to sector 0 of the current track. When finished, it prints `CRLF` and returns to the prompt.

**What happens inside.** The sequence mirrors `R`, but in reverse order:

1. Selects the drive.
2. Homes the head.
3. Sets sector number 0.
4. Enables writing (`WRITE GATE ON`).
5. Sends the `WRITE` command.
6. Loops 8 × 16 = 128 times, reading a byte from memory, splitting it into two nibbles, and sending them to the data port.
7. Disables writing (`WRITE GATE OFF`).

> [!WARNING]
> `W` overwrites sector 0 of the current track. Make sure you are not erasing data you need. If you are working with a disk image you want to preserve, make a copy before writing.

---

## 4. How the monitor is organized

The monitor is built from several modules, each with its own role. Understanding the structure helps you read the code and extend the monitor.

### 4.1 The main loop (monitor.asm)

The main loop is the heart of the monitor. It prints the `> ` prompt, reads a character from the teletype, and dispatches to the appropriate command.

**Dispatch.** Instead of comparing the character against every command (which would require a lot of code), the monitor uses cascaded comparison of high nibbles. First it checks which group the command belongs to: `D`/`G` (high nibble 4) or `S`/`X`/`R`/`W` (high nibble 5). Then, within a group, it checks the low nibble. This is a classic branching pattern that suits 4-bit data.

**Error handling.** If a command is not recognized, the monitor prints `*` and returns to the prompt.

### 4.2 I/O (console_io.asm)

This module handles communication with the teletype.

| Routine | Purpose |
|---------|---------|
| `MON_TTY_INIT` | Initializes the UART: 8N1 format, port `0xE0`. |
| `MON_SEND_CHAR` | Sends the character whose low nibble is in `R2` and high nibble in `R3`. Waits for UART readiness. |
| `MON_GET_CHAR` | Reads a character from the teletype. Returns the low nibble in `R2` and the high nibble in `R3`. Echoes the character back. |
| `MON_PUT_HEX_NIB` | Converts a nibble to ASCII (`0`–`9`, `A`–`F`) and prints it. |
| `MON_PUT_CRLF` | Prints carriage return (13) and line feed (10). |
| `MON_PUT_PROMPT` | Prints the `> ` prompt. |
| `MON_PUT_WELCOME` | Prints the `MCS-4 SYSTEM MONITOR` welcome message. |

**The key idea.** The 4004 is 4-bit, but an ASCII character is 8-bit, so every routine works with two nibbles: low and high. `MON_SEND_CHAR` expects them in `R2` and `R3`; `MON_GET_CHAR` returns them in the same registers. This single exchange format is used across all commands.

### 4.3 Memory commands (memory_cmd.asm)

This module implements `D` and `S`.

**`MON_PARSE_ADDR`** is the key subroutine. It reads two hexadecimal characters from the teletype and converts them into an 8-bit address, storing the result in `R6` (high nibble) and `R7` (low nibble). The process checks whether each character is a digit or a letter and converts accordingly. Invalid characters are ignored until a valid one arrives.

**`MON_CMD_DUMP`** uses `MON_PARSE_ADDR` to get the starting address, then loops to print 16 nibbles. **`MON_CMD_EDIT`** parses the address, waits for a new value, converts it to a number, and writes it to memory via `WRM`.

### 4.4 System commands (system_cmd.asm)

This module implements `X` and `G`.

**`MON_CMD_X`** prints the contents of all 16 registers in sequence. **`MON_CMD_GO`** parses the address, copies it into pair `P0` (`R0:R1`), and executes `JIN P0`.

### 4.5 Disk commands (disk_cmd.asm)

This module implements `R` and `W`. It uses the same ports as the disk driver (registers 4 and 5) but has its own positioning and read/write logic.

**`MON_DISK_HOME`** is a helper that homes the head to track 0. It sends `OUTWARD`, then loops checking `Track00` and sending `STEP` until the head reaches the edge.

**`MON_CMD_LOAD`** and **`MON_CMD_SAVE`** are simplified disk operations. They always use sector 0 of the current track and always use memory starting at `0x00`. This is enough for small programs, but for anything more complex use `disk_driver.asm`.

---

## 5. Disk operations: the disk_driver.asm module

The monitor has built-in `R` and `W` commands, but they are limited: always sector 0, always current track, always memory from `0x00`. If you need finer control, use `disk_driver.asm`. It is a set of subroutines you can call from your own program.

### 5.1 Driver routines

| Routine | Purpose |
|---------|---------|
| `DISK_INIT` | Select the drive and home the head to track 0. |
| `DISK_SEEK` | Move the head to the track specified in `R2`. |
| `DISK_READ_SECTOR` | Read a sector: `R2` — track, `R3` — sector, `R6:R7` — destination memory address. |
| `DISK_WRITE_SECTOR` | Write a sector: same parameters. |
| `DISK_FORMAT_TRACK` | Fill all 26 sectors of the current track with zeros. |

### 5.2 How DISK_INIT works

`DISK_INIT` does three things:

1. Sends `SELECT` to the command port (register 4).
2. Sends `OUTWARD` (move toward the edge).
3. Loops checking `Track00`. If the head is not on track 0, it sends `STEP` and repeats.

When the head reaches the edge, `Track00` is set, and the routine returns.

### 5.3 How DISK_SEEK works

`DISK_SEEK` first calls `DISK_INIT` to home the head. Then it changes the direction to `INWARD` and steps in a loop until the counter in `R2` reaches zero. Each step decrements `R2` by 1. When `R2` is zero, the head is at the target track.

### 5.4 How DISK_READ_SECTOR works

`DISK_READ_SECTOR` performs the following sequence:

1. Calls `DISK_SEEK` to move the head to track `R2`.
2. Sets the sector number `R3` in the data port (register 5).
3. Sends `READ` (0x8) to the command port.
4. Waits for the controller to set the `Ready` flag.
5. Loops 8 × 16 = 128 times, reading two nibbles from the data port, joining them into a byte, and writing it to memory at `R6:R7`. After each write the address increments by 1.

### 5.5 How DISK_WRITE_SECTOR works

`DISK_WRITE_SECTOR` performs the reverse sequence:

1. Calls `DISK_SEEK`.
2. Enables `WRITE GATE`.
3. Sets the sector number.
4. Sends `WRITE` (0x9).
5. Loops 8 × 16, reading a byte from memory, splitting it into two nibbles, and sending them to the data port.
6. Disables `WRITE GATE`.

### 5.6 How DISK_FORMAT_TRACK works

`DISK_FORMAT_TRACK` fills all 26 sectors of the current track with zeros. It calls `DISK_SEEK`, then loops over 26 sectors writing 128 zero bytes to each. This is a simplified formatting model: real IBM 3740 formatting writes special address marks, but for a teaching model, zeroing is enough.

---

## 6. Worked examples

### Example 1: dump memory and edit a cell

Suppose you want to look at memory from `0x10` and change the first cell to `A`.

```text
> D 10
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
> S 10
> A
A
> D 10
A 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
```

### Example 2: load a sector from disk and run a program

Suppose you wrote a program into sector 0 of a disk image and want to run it.

1. Insert the disk image: on the **Disk** tab, click **Load .dsk Image** and choose a file.
2. In the monitor, run `R`. The monitor reads sector 0 into memory starting at `0x00`.
3. Run `G 00`. The monitor transfers control to address `0x00` and the program begins executing.

### Example 3: save a program to disk

Suppose you entered a small program into memory starting at `0x00` and want to save it to disk.

1. Make sure a disk image is loaded on the **Disk** tab (or create a new one).
2. In the monitor, run `W`. The monitor writes 128 bytes from memory starting at `0x00` to sector 0 of the current track.
3. On the **Disk** tab, click **Save .dsk Image** to save the image to a file.

---

## 7. Limitations and caveats

The monitor is a teaching tool, not a full operating system. Here is what to know.

**Sector 0 only.** The `R` and `W` commands always use sector 0 of the current track. For other sectors, use `disk_driver.asm` in your own program.

**No file system.** The disk is treated as a sequence of raw sectors. There are no directories, no file names, and no protection against overwriting. You work with raw data.

**Uppercase only.** The monitor expects uppercase commands. The emulator interface converts lowercase automatically, but if you use a different terminal, type uppercase.

**Small stack.** The 4004 stack holds three levels. The monitor uses `JMS` for subroutine calls, so deep nesting is not possible. If your program calls many subroutines, the stack can overflow.

**No input validation beyond basics.** If you enter an invalid character, the monitor may ignore it or print `*`. It does not tell you what specifically went wrong.

**Registers are not preserved.** The monitor uses `R0`–`R15` for its own purposes. If you call the monitor from your program, save the registers you care about beforehand.

> [!NOTE]
> The monitor lives in `firmware/monitor/`. If you want to modify it, keep a backup of the original `monitor.asm` so you can compare against the working version.

---

## 8. Extending the monitor

If you want to add a new command, here is the procedure.

1. **Add a check in the dispatcher.** In `monitor.asm`, find `MON_DISP_4` or `MON_DISP_5` and add a comparison with the new character.
2. **Implement the routine.** Write the code that performs the command, for example `MON_CMD_MYCMD`.
3. **Add the call.** In the dispatcher, add `JMS MON_CMD_MYCMD` followed by `JUN MON_LOOP`.
4. **Update the welcome or documentation.** If the command adds new functionality, mention it in `MON_PUT_WELCOME` or in this guide.

**Example:** to add a `Z` command that prints `HELLO`, you would add a check for `Z` (0x5A) in the dispatcher and a routine that loads character codes into `R2`/`R3` and calls `MON_SEND_CHAR` for each character.

---

## 9. Debugging the monitor

If the monitor is not working, several things are worth checking.

**The monitor does not start.** Make sure `monitor.asm` is in `firmware/` (or `firmware/monitor/`). Verify that the build succeeded: the status bar should report success. If there is an error, read it carefully — most often it is a misspelled mnemonic or an undefined label.

**The command does not execute.** Make sure you are typing an uppercase letter. Check that the monitor is at the `> ` prompt. If you entered `G` and the program did not return control, press **Stop** and then **Run** again.

**The disk does not read.** Verify that a disk image of the correct size (256,256 bytes) is loaded on the **Disk** tab. Check that the current track and sector exist. If you use `R` or `W`, remember they only work with sector 0.

**The monitor prints `*`.** This means the command was not recognized. Check that you typed one of the supported letters: `D`, `S`, `X`, `G`, `R`, `W`.

---

## 10. Conclusion

The monitor is a small but complete tool for working with the emulator. It lets you load programs, inspect memory, edit data, and work with the disk. It does not replace a full OS, but it provides enough control for learning and experimentation.

If you want to understand the disk drive and IBM 3740 format in depth, read the [Peripherals and I/O Reference](./07-peripherals-and-io-reference.md). If you want to see how the monitor uses the assembler and linker, return to the [Assembly Programming Guide](./03-assembly-programming-guide.md) and the [Toolchain Reference](./05-toolchain-reference.md). And if you want to extend the monitor or add your own commands, use section 8 as a starting point.

The monitor is your control panel for the emulator. Experiment, make mistakes, try again. No virtual hardware will be harmed.

---

[← Previous: Peripherals and I/O Reference](./07-peripherals-and-io-reference.md) | [Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md)
