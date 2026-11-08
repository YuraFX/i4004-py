// ============================================================
// D (dump), S (edit)
// ============================================================

MON_PARSE_ADDR:
    LDM 0
    XCH R2
    LDM 2
    XCH R3
    JMS MON_SEND_CHAR

    // --- Read the first character ---
MON_PARSE_1_LOOP:
    JMS MON_GET_CHAR
    LD R3
    XCH R4
    LDM 3
    XCH R5
    LD R4
    CLC
    SUB R5
    JCN Z MON_PARSE_1_DIG
    LDM 4
    XCH R5
    LD R4
    CLC
    SUB R5
    JCN Z MON_PARSE_1_HEX
    JUN MON_PARSE_1_LOOP
MON_PARSE_1_DIG:
    LD R2
    JUN MON_PARSE_1_DONE
MON_PARSE_1_HEX:
    LD R2
    XCH R4
    LDM 9
    XCH R5
    LD R4
    CLC
    ADD R5
MON_PARSE_1_DONE:
    XCH R6

    // --- Read the second character ---
MON_PARSE_2_LOOP:
    JMS MON_GET_CHAR
    LD R3
    XCH R4
    LDM 3
    XCH R5
    LD R4
    CLC
    SUB R5
    JCN Z MON_PARSE_2_DIG
    LDM 4
    XCH R5
    LD R4
    CLC
    SUB R5
    JCN Z MON_PARSE_2_HEX
    JUN MON_PARSE_2_LOOP
MON_PARSE_2_DIG:
    LD R2
    JUN MON_PARSE_2_DONE
MON_PARSE_2_HEX:
    LD R2
    XCH R4
    LDM 9
    XCH R5
    LD R4
    CLC
    ADD R5
MON_PARSE_2_DONE:
    XCH R7
    BBL 0

// 'D' - dump 16 nibbles
MON_CMD_DUMP:
    JMS MON_PARSE_ADDR
    JMS MON_PUT_CRLF
    
    LDM 16
    XCH R8
    
MON_DUMP_LOOP:
    SRC P3
    RDM
    JMS MON_PUT_HEX_NIB
    
    LDM 0
    XCH R2
    LDM 2
    XCH R3
    JMS MON_SEND_CHAR
    
    LD R7
    IAC
    XCH R7
    JCN NZ MON_DUMP_NOR6
    LD R6
    IAC
    XCH R6
MON_DUMP_NOR6:
    ISZ R8 MON_DUMP_LOOP
    NOP
    JMS MON_PUT_CRLF
    BBL 0

// 'S' - set nibble
MON_CMD_EDIT:
    JMS MON_PARSE_ADDR
    
    LDM 0
    XCH R2
    LDM 2
    XCH R3
    JMS MON_SEND_CHAR
    
MON_EDIT_LOOP:
    JMS MON_GET_CHAR
    LD R3
    XCH R4
    LDM 3
    XCH R5
    LD R4
    CLC
    SUB R5
    JCN Z MON_EDIT_DIG
    LDM 4
    XCH R5
    LD R4
    CLC
    SUB R5
    JCN Z MON_EDIT_HEX
    JUN MON_EDIT_LOOP
MON_EDIT_DIG:
    LD R2
    JUN MON_EDIT_DONE
MON_EDIT_HEX:
    LD R2
    XCH R4
    LDM 9
    XCH R5
    LD R4
    CLC
    ADD R5
MON_EDIT_DONE:
    // Hide our value F (15) in register R9
    XCH R9          // R9 = value (F), ACC = garbage
    
    SRC P3          // Set up the RAM address (R6, R7)
    LD R9           // Retrieve the value back into ACC
    WRM             // Write it into memory
    
    // --- VISUAL CONFIRMATION ---
    JMS MON_PUT_CRLF // Move to the next line (this command clobbers ACC, but we no longer care)
    
    LD R9           // Retrieve the value from R9 back into ACC
    JMS MON_PUT_HEX_NIB  // Print it (F)
    
    JMS MON_PUT_CRLF
    BBL 0