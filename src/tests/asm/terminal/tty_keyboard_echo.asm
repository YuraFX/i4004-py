// =================================================================
// Terminal Echo: Read from keyboard and output to UART
// =================================================================
ORG 0x000

    // 1. UART initialization (8 bits, 1 stop bit, no parity)
    FIM P0 0xE0       // R14 = 14 (Chip 3, Control)
    SRC P0
    LDM 13            // 0x0D
    WMP

MAIN_LOOP:
    // 2. Read the keyboard (Register 15, Port 3)
    FIM P0 0xF0       // R15 = 15 (Chip 3, Keyboard data)
    SRC P0
    RDM               // Read into ACC (the emulator itself puts the low nibble here)
    JCN Z MAIN_LOOP   // If 0 (no key pressed), keep waiting

    // 3. Save the low nibble
    XCH R2            // R2 = low nibble (Low Nibble)

    // 4. Wait for UART readiness (Register 13)
WAIT_TX1:
    FIM P0 0xD0       // R13 = 13 (Status)
    SRC P0
    RDM
    JCN Z WAIT_TX1    // Wait for TBMT=1

    // 5. Send the low nibble to UART (Register 12)
    FIM P0 0xC0       // R12 = 12 (UART data)
    SRC P0
    LD R2
    WMP

    // 6. Read the second half of the character (high nibble)
    FIM P0 0xF0       // Register 15 again
    SRC P0
    RDM               // The emulator itself returns the high nibble and clears the keyboard
    XCH R2            // R2 = high nibble (High Nibble)

    // 7. Wait for UART readiness before sending the second nibble
WAIT_TX2:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_TX2

    // 8. Send the high nibble to UART
    FIM P0 0xC0
    SRC P0
    LD R2
    WMP

    JUN MAIN_LOOP     // Return to waiting for the next key