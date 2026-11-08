// ============================================================
// X (examine), G (go)
// ============================================================

MON_CMD_X:
    JMS MON_PUT_CRLF
    LD R0
    JMS MON_PUT_HEX_NIB
    LD R1
    JMS MON_PUT_HEX_NIB
    LD R2
    JMS MON_PUT_HEX_NIB
    LD R3
    JMS MON_PUT_HEX_NIB
    JMS MON_PUT_CRLF
    LD R4
    JMS MON_PUT_HEX_NIB
    LD R5
    JMS MON_PUT_HEX_NIB
    LD R6
    JMS MON_PUT_HEX_NIB
    LD R7
    JMS MON_PUT_HEX_NIB
    JMS MON_PUT_CRLF
    LD R8
    JMS MON_PUT_HEX_NIB
    LD R9
    JMS MON_PUT_HEX_NIB
    LD R10
    JMS MON_PUT_HEX_NIB
    LD R11
    JMS MON_PUT_HEX_NIB
    JMS MON_PUT_CRLF
    LD R12
    JMS MON_PUT_HEX_NIB
    LD R13
    JMS MON_PUT_HEX_NIB
    LD R14
    JMS MON_PUT_HEX_NIB
    LD R15
    JMS MON_PUT_HEX_NIB
    JMS MON_PUT_CRLF
    BBL 0

// 'G' - jump to 8-bit address (via JIN)
MON_CMD_GO:
    JMS MON_PARSE_ADDR
    LD R6
    XCH R0
    LD R7
    XCH R1
    JIN P0
    BBL 0