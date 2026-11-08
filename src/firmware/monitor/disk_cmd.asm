// ============================================================
// R (load sector), W (save sector)
// ============================================================

MON_DISK_HOME:
    FIM P0 0x40
    SRC P0
    LDM 3
    WMP
MON_DISK_HOME_L:
    FIM P0 0x40
    SRC P0
    RDM
    RAR
    JCN C MON_DISK_HOME_D
    LDM 1
    WMP
    JUN MON_DISK_HOME_L
MON_DISK_HOME_D:
    BBL 0

// 'R' - load 128-byte sector into RAM 0x00-0xFF
MON_CMD_LOAD:
    JMS MON_PUT_CRLF
    FIM P0 0x40
    SRC P0
    LDM 4       // SELECT
    WMP
    LDM 7       // WRITE GATE OFF
    WMP
    JMS MON_DISK_HOME
    
    FIM P0 0x50
    SRC P0
    LDM 0       // Sector 0
    WMP
    
    FIM P0 0x40
    SRC P0
    LDM 8       // READ
    WMP
    
    // Read 128 bytes (256 nibbles) into memory starting at address 0x00
    FIM P3 0x00 // R6=0, R7=0 (RAM address 0x00)
    LDM 8       // Outer loop: 8 iterations (8 * 16 = 128 bytes)
    XCH R8
    
MON_LOAD_OUT:
    LDM 0       // Inner loop: 16 iterations (2 nibbles = 1 byte each)
    XCH R9
    
MON_LOAD_IN:
    // Read the low nibble from the disk
    FIM P0 0x50
    SRC P0
    RDM
    SRC P3
    WRM
    
    // Increment the RAM address
    LD R7
    IAC
    XCH R7
    JCN NZ MON_LOAD_OV1
    LD R6
    IAC
    XCH R6
MON_LOAD_OV1:

    // Read the high nibble from the disk
    FIM P0 0x50
    SRC P0
    RDM
    SRC P3
    WRM
    
    // Increment the RAM address
    LD R7
    IAC
    XCH R7
    JCN NZ MON_LOAD_OV2
    LD R6
    IAC
    XCH R6
MON_LOAD_OV2:

    ISZ R9 MON_LOAD_IN
    NOP
    
    ISZ R8 MON_LOAD_OUT
    NOP

    JMS MON_PUT_CRLF
    BBL 0

// 'W' - save RAM 0x00-0xFF to sector
MON_CMD_SAVE:
    JMS MON_PUT_CRLF
    FIM P0 0x40
    SRC P0
    LDM 4       // SELECT
    WMP
    LDM 7       // WRITE GATE OFF
    WMP
    JMS MON_DISK_HOME
    
    FIM P0 0x50
    SRC P0
    LDM 0       // Sector 0
    WMP
    
    FIM P0 0x40
    SRC P0
    LDM 6       // WRITE GATE ON
    WMP
    LDM 9       // WRITE
    WMP
    
    // Write 128 bytes from memory starting at address 0x00
    FIM P3 0x00 // R6=0, R7=0 (RAM address 0x00)
    LDM 8       // Outer loop: 8 iterations
    XCH R8
    
MON_SAVE_OUT:
    LDM 0       // Inner loop: 16 iterations
    XCH R9
    
MON_SAVE_IN:
    // Write the low nibble to the disk
    SRC P3
    RDM
    FIM P0 0x50
    SRC P0
    WMP
    
    // Increment the RAM address
    LD R7
    IAC
    XCH R7
    JCN NZ MON_SAVE_OV1
    LD R6
    IAC
    XCH R6
MON_SAVE_OV1:

    // Write the high nibble to the disk
    SRC P3
    RDM
    FIM P0 0x50
    SRC P0
    WMP
    
    // Increment the RAM address
    LD R7
    IAC
    XCH R7
    JCN NZ MON_SAVE_OV2
    LD R6
    IAC
    XCH R6
MON_SAVE_OV2:

    ISZ R9 MON_SAVE_IN
    NOP
    
    ISZ R8 MON_SAVE_OUT
    NOP
    
    FIM P0 0x40
    SRC P0
    LDM 7       // WRITE GATE OFF
    WMP
    JMS MON_PUT_CRLF
    BBL 0