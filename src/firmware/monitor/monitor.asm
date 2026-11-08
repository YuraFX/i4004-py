// ============================================================
// Entry point + command dispatch
// ============================================================
ORG 0x000

MON_START:
    JMS MON_TTY_INIT
    JMS MON_PUT_WELCOME

MON_LOOP:
    JMS MON_PUT_PROMPT
    JMS MON_GET_CHAR
    
    // Dispatch: check high nibble (R3) first
    LD R3
    XCH R4
    LDM 4
    XCH R5
    LD R4
    CLC
    SUB R5
    JCN Z MON_DISP_4
    LDM 5
    XCH R5
    LD R4
    CLC
    SUB R5
    JCN Z MON_DISP_5
    JUN MON_BAD

MON_DISP_4:
    // D (0x44), G (0x47)
    LD R2
    XCH R4
    LDM 4
    XCH R5
    LD R4
    CLC
    SUB R5
    JCN Z MON_GO_D
    LDM 7
    XCH R5
    LD R4
    CLC
    SUB R5
    JCN Z MON_GO_G
    JUN MON_BAD

MON_DISP_5:
    // S (0x53), X (0x58), R (0x52), W (0x57)
    LD R2
    XCH R4
    LDM 3
    XCH R5
    LD R4
    CLC
    SUB R5
    JCN Z MON_GO_S
    LDM 8
    XCH R5
    LD R4
    CLC
    SUB R5
    JCN Z MON_GO_X
    LDM 2
    XCH R5
    LD R4
    CLC
    SUB R5
    JCN Z MON_GO_R
    LDM 7
    XCH R5
    LD R4
    CLC
    SUB R5
    JCN Z MON_GO_W
    JUN MON_BAD

MON_GO_D:
    JMS MON_CMD_DUMP
    JUN MON_LOOP
MON_GO_S:
    JMS MON_CMD_EDIT
    JUN MON_LOOP
MON_GO_X:
    JMS MON_CMD_X
    JUN MON_LOOP
MON_GO_R:
    JMS MON_CMD_LOAD
    JUN MON_LOOP
MON_GO_W:
    JMS MON_CMD_SAVE
    JUN MON_LOOP
MON_GO_G:
    JMS MON_CMD_GO
    JUN MON_LOOP

MON_BAD:
    LDM 10
    XCH R2
    LDM 2
    XCH R3
    JMS MON_SEND_CHAR
    JMS MON_PUT_CRLF
    JUN MON_LOOP