// ============================================================
// UART I/O utilities (Combined Best Version)
// ============================================================

MON_TTY_INIT:
    FIM P0 0xE0
    SRC P0
    LDM 13          // 8N1
    WMP
    BBL 0

MON_SEND_CHAR:
MON_SEND_WAIT:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z MON_SEND_WAIT
    FIM P0 0xC0
    SRC P0
    LD R2
    WMP
    LD R3
    WMP
    BBL 0

// Read character (use only R2 and R3 so as not to break the monitor)
MON_GET_CHAR:
MON_WAIT_KEY:
    FIM P0 0xF0
    SRC P0
    RDM
    XCH R2          
    RDM
    XCH R3          

    LD R2
    JCN NZ MON_GOT_KEY
    LD R3
    JCN Z MON_WAIT_KEY

MON_GOT_KEY:
    // INLINE ECHO
MON_ECHO_WAIT:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z MON_ECHO_WAIT
    FIM P0 0xC0
    SRC P0
    LD R2
    WMP
    LD R3
    WMP
    BBL 0

MON_PUT_HEX_NIB:
    XCH R2
    LDM 10
    XCH R5
    LD R2
    CLC
    SUB R5
    JCN C MON_HEX_AF
    // Digit (0-9)
    LDM 3
    XCH R3
    JUN MON_PUT_NIB_TX
MON_HEX_AF:
    // Letter (A-F)
    IAC
    XCH R2
    LDM 4
    XCH R3

MON_PUT_NIB_TX:
MON_PUT_NIB_WAIT:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z MON_PUT_NIB_WAIT
    FIM P0 0xC0
    SRC P0
    LD R2
    WMP
    LD R3
    WMP
    BBL 0

MON_PUT_CRLF:
    LDM 13
    XCH R2
    LDM 0
    XCH R3
    JMS MON_SEND_CHAR
    LDM 10
    XCH R2
    LDM 0
    XCH R3
    JMS MON_SEND_CHAR
    BBL 0

MON_PUT_PROMPT:
    LDM 14
    XCH R2
    LDM 3
    XCH R3
    JMS MON_SEND_CHAR
    LDM 0
    XCH R2
    LDM 2
    XCH R3
    JMS MON_SEND_CHAR
    BBL 0

// Long string "MCS-4 SYSTEM MONITOR"
MON_PUT_WELCOME:
    // "M"
    LDM 13
    XCH R2
    LDM 4
    XCH R3
    JMS MON_SEND_CHAR
    // "C"
    LDM 3
    XCH R2
    LDM 4
    XCH R3
    JMS MON_SEND_CHAR
    // "S"
    LDM 3
    XCH R2
    LDM 5
    XCH R3
    JMS MON_SEND_CHAR
    // "-"
    LDM 13
    XCH R2
    LDM 2
    XCH R3
    JMS MON_SEND_CHAR
    // "4"
    LDM 4
    XCH R2
    LDM 3
    XCH R3
    JMS MON_SEND_CHAR
    // " " (space)
    LDM 0
    XCH R2
    LDM 2
    XCH R3
    JMS MON_SEND_CHAR
    // "S"
    LDM 3
    XCH R2
    LDM 5
    XCH R3
    JMS MON_SEND_CHAR
    // "Y"
    LDM 9
    XCH R2
    LDM 5
    XCH R3
    JMS MON_SEND_CHAR
    // "S"
    LDM 3
    XCH R2
    LDM 5
    XCH R3
    JMS MON_SEND_CHAR
    // "T"
    LDM 4
    XCH R2
    LDM 5
    XCH R3
    JMS MON_SEND_CHAR
    // "E"
    LDM 5
    XCH R2
    LDM 4
    XCH R3
    JMS MON_SEND_CHAR
    // "M"
    LDM 13
    XCH R2
    LDM 4
    XCH R3
    JMS MON_SEND_CHAR
    // " " (space)
    LDM 0
    XCH R2
    LDM 2
    XCH R3
    JMS MON_SEND_CHAR
    // "M"
    LDM 13
    XCH R2
    LDM 4
    XCH R3
    JMS MON_SEND_CHAR
    // "O"
    LDM 15
    XCH R2
    LDM 4
    XCH R3
    JMS MON_SEND_CHAR
    // "N"
    LDM 14
    XCH R2
    LDM 4
    XCH R3
    JMS MON_SEND_CHAR
    // "I"
    LDM 9
    XCH R2
    LDM 4
    XCH R3
    JMS MON_SEND_CHAR
    // "T"
    LDM 4
    XCH R2
    LDM 5
    XCH R3
    JMS MON_SEND_CHAR
    // "O"
    LDM 15
    XCH R2
    LDM 4
    XCH R3
    JMS MON_SEND_CHAR
    // "R"
    LDM 2
    XCH R2
    LDM 5
    XCH R3
    JMS MON_SEND_CHAR
    
    JMS MON_PUT_CRLF
    BBL 0